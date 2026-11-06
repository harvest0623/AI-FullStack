# Day09 - 并发编程（goroutine 与 channel）

## 本章简介

Go 最鲜明的语言级特性是原生并发：一个 `go` 关键字就能启动一个 goroutine，一个 `chan` 就能在协程之间传递数据。Go 官方倡导的并发哲学是"不要通过共享内存来通信，而要通过通信来共享内存"，这源自 CSP（Communicating Sequential Processes）模型，也是 channel 设计的理论基础。理解这套模型，比记住几个 API 更重要。

在 eshop-gateway 中，一个商品详情请求往往需要同时获取商品基础信息、库存、价格、评价摘要，并调用上游 LLM 生成导购文案。串行执行会让延迟逐项叠加，并发聚合则能把总耗时压缩到"最慢的那个依赖"附近。但并发不是免费的：没有超时、取消和容量控制，一次上游抖动就可能拖垮整个网关。

本章从 goroutine 的创建与 GMP 调度讲起，逐一拆解 channel 的阻塞语义、`select` 多路复用、`sync` 同步原语、`context` 取消传播，最后落到 worker pool 与常见并发陷阱。所有示例都可以用 `go run -race` 运行，建议每改一处就重新验证一次。

## 学习目标

- 区分并发（concurrency）与并行（parallelism），理解 Go 并发的适用场景
- 理解 goroutine 的轻量本质、初始栈大小与动态扩容机制
- 掌握 GMP 调度模型：G、M、P 的职责，以及 work stealing 与抢占
- 掌握无缓冲与有缓冲 channel 的阻塞条件与容量语义
- 正确使用 `close`、`range`、单向 channel 与 nil channel
- 用 `select` 实现多路复用、非阻塞尝试、超时与退出信号
- 用 `sync.WaitGroup`、`Mutex`、`RWMutex`、`Once` 组织同步逻辑
- 用 `sync/atomic` 完成无锁计数与标志位
- 用 `context` 传播取消、截止时间与请求域数据
- 实现 worker pool、pipeline、fan-out/fan-in 三类并发模式
- 识别数据竞争、goroutine 泄漏、循环变量捕获等陷阱，并能读懂 `go run -race` 的竞争报告

## 理论知识讲解

### 1. 并发与并行

**并发**是程序结构问题：多个任务在时间上重叠地推进，交替使用 CPU；**并行**是执行问题：多个任务在同一时刻真正同时运行，需要多核支持。Go 的 goroutine 让并发写起来像串行代码，而运行时会尽可能把可运行的 goroutine 分配到多个 CPU 核心上。

```
并发（单核交替）              并行（多核同时）
┌───┬───┬───┬───┐            ┌───────┐  ┌───────┐
│G1 │G2 │G1 │G2 │            │  G1   │  │  G2   │
└───┴───┴───┴───┘            └───────┘  └───────┘
  时间 ──────────────────▶      Core0       Core1
```

| 维度 | 并发 | 并行 |
|------|------|------|
| 关注点 | 任务编排与解耦 | 同时执行，提升吞吐 |
| 必要条件 | 多任务可交错推进 | 多核 + 可并行的任务 |
| Go 中的体现 | goroutine + channel | `GOMAXPROCS > 1` 时的 M:P 绑定 |
| 典型收益 | 隐藏 IO 等待、简化结构 | 压缩 CPU 密集任务耗时 |

电商网关的绝大多数场景是 **IO 密集型**：等待数据库、缓存、上游 LLM。并发的主要收益是重叠等待时间，而不是把 CPU 跑满。

### 2. goroutine 与 GMP 调度模型

goroutine 是 Go 运行时管理的用户态协程，初始栈只有约 2KB，按需增长，创建和切换成本远低于操作系统线程。启动方式很简单：

```go
go func(id int) {
    fmt.Println("查询商品", id)
}(1001) // 参数在启动时求值，避免闭包捕获问题
```

Go 调度器采用 **GMP 模型**：

```
        ┌──────────────── 全局可运行队列 ────────────────┐
        │  G  G  G  G                                   │
        └───────────────────┬───────────────────────────┘
                            │ 取任务
        ┌───────────────────▼───────────────────────────┐
        │  P0            P1            P2   （逻辑处理器）│
        │  本地队列      本地队列      本地队列           │
        │  G G G         G G            G                 │
        └───┬─────────────┬─────────────┬───────────────┘
            │ 绑定         │ 绑定         │ 绑定
        ┌───▼───┐     ┌───▼───┐     ┌───▼───┐
        │  M0   │     │  M1   │     │  M2   │  （操作系统线程）
        └───────┘     └───────┘     └───────┘
```

| 角色 | 含义 | 说明 |
|------|------|------|
| G | Goroutine | 待执行的协程任务，保存栈与状态 |
| M | Machine | 操作系统线程，真正执行代码的载体 |
| P | Processor | 逻辑处理器，持有本地运行队列与调度上下文 |
| 数量关系 | M:P 动态绑定 | `GOMAXPROCS` 决定 P 的数量，默认等于 CPU 核数 |

关键机制包括 **work stealing**（P 本地队列为空时从其他 P 或全局队列窃取任务）、**抢占式调度**（Go 1.14 起支持异步抢占，长循环不会永久霸占 P）和**系统调用让出 P**（M 阻塞时把 P 交给其他 M，保证其他 G 继续运行）。

> 不要用 `runtime.NumGoroutine()` 做业务判断，它只适合调试与监控；goroutine 数量持续上涨通常意味着泄漏。

### 3. channel 的语义

channel 是带类型的通信管道，声明为 `chan T`。发送用 `ch <- v`，接收用 `v := <-ch`，方向可以在参数中限制为只写 `chan<- T` 或只读 `<-chan T`。

| 类型 | 创建方式 | 发送阻塞条件 | 接收阻塞条件 |
|------|---------|-------------|-------------|
| 无缓冲 | `make(chan T)` | 没有接收者就绪 | 没有发送者就绪 |
| 有缓冲 | `make(chan T, n)` | 缓冲已满 | 缓冲为空 |
| nil channel | `var ch chan T` | 永久阻塞 | 永久阻塞 |

`close` 的规则必须记牢：

- 只有发送方可以 `close`，重复 close 会 panic
- 向已关闭的 channel 发送会 panic
- 从已关闭的 channel 接收不会阻塞：先取完缓冲区数据，之后返回零值且 `ok == false`
- `for v := range ch` 会在 channel 关闭且数据取完后自动结束

```go
ch := make(chan int, 2)
ch <- 1
ch <- 2
close(ch)
for v := range ch { // 依次输出 1、2 后退出循环
    fmt.Println(v)
}
```

**单向 channel** 常作为函数签名，把"谁能读、谁能写"固化在类型里：

```go
func producer() <-chan int     // 只返回读端
func consumer(in <-chan int)   // 只接收读端
func sender(out chan<- string) // 只接受写端
```

### 4. select 多路复用

`select` 同时等待多个 channel 操作，哪个就绪就执行哪个；多个同时就绪时**随机**选择，因此不能依赖分支顺序。它常与 `default`、`time.After`、`done` channel 组合：

```go
select {
case msg := <-fast:
    fmt.Println("快速通道：", msg)
case msg := <-slow:
    fmt.Println("慢速通道：", msg)
case <-time.After(50 * time.Millisecond):
    fmt.Println("超时，返回降级结果")
case <-ctx.Done():
    return ctx.Err()
default:
    // 所有 case 都未就绪时立即执行，实现非阻塞尝试
}
```

三个容易忽略的点：`time.After` 每次都会创建定时器，高频循环应改用 `time.NewTimer`；`default` 会让 select 变成非阻塞轮询，放在 `for` 里可能空转烧 CPU；超时后发送方若仍向无缓冲 channel 发送会永久阻塞，应留 1 个缓冲或让发送方同时监听 `done`。

### 5. sync 同步原语

channel 适合传递数据与编排流程，而保护共享状态时，`sync` 包往往更直接：

| 原语 | 用途 | 关键约束 |
|------|------|---------|
| `sync.WaitGroup` | 等待一组 goroutine 结束 | `Add` 必须在 `Wait` 之前完成，通常在启动 goroutine 前调用 |
| `sync.Mutex` | 互斥保护临界区 | 锁不可复制；加锁后立即 `defer Unlock()` |
| `sync.RWMutex` | 读多写少场景 | 写锁独占；读锁可并发，但不可嵌套写 |
| `sync.Once` | 全局只执行一次初始化 | `Do` 内部 panic 也会被视为已执行 |
| `sync/atomic` | 计数、标志位 | 只适合简单原子操作，不能替代复杂临界区 |

```go
var (
    mu    sync.Mutex
    count int
)

mu.Lock()
count++
mu.Unlock()

var hits atomic.Int64
hits.Add(1)
fmt.Println(hits.Load())
```

> 经验法则：**能用局部变量和 channel 解决，就不要共享内存**；必须共享时，把锁的粒度压到最小，并保证所有访问路径都加锁。

### 6. context：取消、超时与传值

`context.Context` 是跨 goroutine 传递取消信号的标准机制。它是一棵不可变的树，子 context 被取消时，所有后代都会收到通知：

```
context.Background()
   └── WithTimeout(100ms)          ← HTTP 请求预算
         └── WithCancel()          ← 用户断开连接
               └── WithValue(requestID)
```

| 构造函数 | 用途 |
|---------|------|
| `context.WithCancel(parent)` | 手动取消，返回 cancel 函数 |
| `context.WithTimeout(parent, d)` | 到达相对时间后自动取消 |
| `context.WithDeadline(parent, t)` | 到达绝对时间点后自动取消 |
| `context.WithValue(parent, k, v)` | 携带请求域数据 |

使用约定：

- 作为函数**第一个参数**传入，命名为 `ctx`
- 不要存进结构体，也不要传 `nil`，没有取消需求时用 `context.Background()`
- `cancel` 必须调用（通常 `defer cancel()`），否则会泄漏定时器与子节点
- `WithValue` 只放 requestID、traceID、租户 ID、鉴权主体等**请求域**数据，不要放数据库连接、配置对象等长生命周期依赖
- 区分 `context.DeadlineExceeded`（超时）与 `context.Canceled`（主动取消）

### 7. 常见并发陷阱

**数据竞争**：多个 goroutine 无同步地读写同一变量。`go run -race` 能检测到并打印读写下标；`map` 的并发读写还会直接触发运行时 fatal error。

**goroutine 泄漏**：goroutine 永久阻塞在发送、接收或等待上，无法退出。常见原因是无缓冲 channel 的发送方没有接收者、循环里 `break` 后忘了关闭上游、以及没有监听 `ctx.Done()`。

**循环变量捕获**：Go 1.22 之前，`for` 循环变量在所有迭代间共享，闭包捕获到的是同一个变量，常导致所有 goroutine 打印最后一个值。Go 1.22 起每次迭代都有独立变量，问题已修复；阅读旧代码时仍需留意显式传参的写法。

**WaitGroup 误用**：在 goroutine 内部调用 `wg.Add(1)`，可能与 `wg.Wait()` 并发执行而 panic；正确做法是在启动前 `Add`。

**锁与阻塞混用**：持锁期间做网络调用或向 channel 发送，会让其他协程长时间等待，甚至形成死锁。

### 8. 并发模式

**Worker Pool（工作池）**：固定数量 worker 消费任务队列，控制并发度，避免瞬时打出上千个 goroutine：

```
jobs ──▶ ┌────────┐
         │ worker │ ──▶ results
jobs ──▶ │ worker │ ──▶ results
         │ worker │ ──▶ results
         └────────┘
    close(jobs) 后 worker 的 range 结束
    所有 worker 结束后 close(results)
```

**Pipeline（流水线）**：每一段接收上游 channel、返回下游 channel，用 `close` 串联生命周期。

**Fan-out / Fan-in（扇出/扇入）**：多个 worker 同时消费同一输入（扇出），再把结果汇聚到一个 channel（扇入），适合批量调用上游 LLM 后统一聚合。

### 9. 在 eshop-gateway 中的位置

| 场景 | 使用的原语 | 目标 |
|------|-----------|------|
| 商品详情并发聚合 | `WaitGroup` + 结果 channel + `context` | 总耗时取决于最慢依赖 |
| 商品缓存 | `sync.RWMutex` | 读多写少，避免锁竞争 |
| 配置与客户端初始化 | `sync.Once` | 全局只初始化一次 |
| 请求计数与限流 | `atomic.Int64` | 无锁高频计数 |
| 批量文案生成 | worker pool + `context` | 控制对上游 LLM 的并发压力 |
| 请求取消 | `context.WithTimeout` | 客户端断开即停止下游调用 |

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/goroutines.go` | `go` 启动协程、`WaitGroup` 等待、闭包捕获循环变量（Go 1.22 语义）与显式传参 |
| `Code/channels.go` | 无缓冲/有缓冲 channel、阻塞与容量、`close` + `range`、单向 channel、简单 pipeline |
| `Code/select_timeout.go` | `select` 多路复用、`default` 非阻塞、`time.After` 超时、`done` channel 退出 |
| `Code/sync_demo.go` | `Mutex` 保护计数器、`RWMutex` 商品缓存、`sync.Once` 单例、`atomic.Int64` 计数 |
| `Code/worker_pool.go` | `jobs`/`results` channel、固定 worker 数、`WaitGroup` 收尾与结果汇总 |
| `Code/context_demo.go` | `WithTimeout` 模拟上游调用、`WithCancel` 手动取消、`WithValue` 传 requestID |

执行方式（每个文件独立运行，并发示例务必开启竞争检测）：

```bash
cd "Day09 - 并发编程(goroutine与channel)/Code"
go run -race goroutines.go
go run -race channels.go
go run -race select_timeout.go
go run -race sync_demo.go
go run -race worker_pool.go
go run -race context_demo.go
```

> 同一目录下多个文件都含 `main` 函数，不要执行 `go run .`，请按文件名单独运行。

## 关键知识点总结

1. **并发 ≠ 并行**：并发是任务交错推进的结构，并行是多核同时执行；网关场景主要用并发重叠 IO 等待。
2. **goroutine 很轻**：初始栈约 2KB、按需扩容，创建成本远低于线程，但仍需控制数量与生命周期。
3. **GMP 模型**：G 是协程、M 是线程、P 是逻辑处理器；`GOMAXPROCS` 决定 P 数量，work stealing 负责负载均衡。
4. **channel 阻塞规则**：无缓冲要求收发双方就绪；有缓冲在满/空时阻塞；nil channel 永久阻塞。
5. **close 只由发送方调用**：关闭后不可再发送，接收方会取完缓冲数据并得到 `ok == false`。
6. **单向 channel 是类型约束**：`<-chan T` 只读、`chan<- T` 只写，用于表达数据流向。
7. **select 随机选择就绪分支**：配合 `default` 实现非阻塞，配合 `time.After` / `ctx.Done()` 实现超时与退出。
8. **WaitGroup 的 Add 要在 Wait 前**：推荐在启动 goroutine 之前 `Add`，在 goroutine 内 `defer Done`。
9. **锁保护共享状态**：`Mutex` 用于互斥写，`RWMutex` 适合读多写少；锁不可复制，持锁期间不要做慢操作。
10. **atomic 适合简单计数**：`atomic.Int64` 可避免高频计数时的锁竞争，但不能替代复合逻辑的锁。
11. **context 是取消传播的标准方式**：`cancel` 必须调用，`Value` 只放请求域数据，并区分超时与主动取消。
12. **并发必开 race**：`go run -race` 能把隐蔽的数据竞争暴露为可定位的报告，是并发代码的最低验收标准。

## 实战练习

### 练习 1：商品详情并发聚合（带降级）

实现 `aggregateProduct(ctx, id)`，并发调用三个模拟上游：基础信息（30ms）、库存（60ms）、评价摘要（90ms）。

要求：

- 用 `context.WithTimeout(ctx, 100*time.Millisecond)` 控制总预算
- 三个结果分别写入各自的 channel，主协程用 `select` 逐个收集
- 任一上游超时或报错时，用默认值降级，不影响其他结果
- 打印每个依赖的耗时和总耗时，验证总耗时接近最慢依赖而非三者之和
- 用 `go run -race` 验证无数据竞争

### 练习 2：带 TTL 的并发安全商品缓存

实现 `TTLCache`：

- 内部使用 `map[string]entry` 与 `sync.RWMutex`，`entry` 保存值和过期时间
- `Get` 命中但已过期时删除并返回未命中
- `Set` 写入时记录 `time.Now().Add(ttl)`
- 启动一个后台 goroutine，每 50ms 清理一次过期键，通过 `stop` channel 或 `context` 退出；再用 10 个读 goroutine 和 2 个写 goroutine 压测，确保无 race、无泄漏

### 练习 3：批量 LLM 文案生成 worker pool

给定 20 个商品，为每个商品调用一个模拟 LLM 接口（随机 20-80ms 延迟，部分返回错误）。

要求：

- 启动固定 4 个 worker，从 `jobs` 读取，向 `results` 写入
- 用 `context.WithCancel`：任意任务返回"内容违规"错误时，取消剩余任务
- 用 `WaitGroup` 等待 worker 退出后关闭 `results`，主协程统计成功数、失败数与平均耗时，并打印前 5 条成功文案
- 思考：如果把 worker 数改成 50，会发生什么？为什么网关要限制对上游的并发？

### 练习 4：复现并修复数据竞争

写一个 `race_demo.go`：

- 启动 100 个 goroutine，各自对同一个 `map[string]int` 执行 `counts["p1001"]++`
- 先不加锁运行 `go run -race race_demo.go`，记录 race 报告中的读写位置
- 分别用 `sync.Mutex` 和 `atomic.Int64`（改用计数器而非 map）两种方式修复，并对比适用边界：为什么 `atomic` 不能直接保护 map？
