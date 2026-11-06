# Day07 - 错误处理与 defer/panic/recover

## 本章简介

Go 没有异常机制。错误在 Go 里是一个**普通值**，类型为内置的 `error` 接口，由函数显式返回，由调用方显式检查。这套设计初看啰嗦，但它让每一条失败路径都出现在代码里：谁产生错误、谁补充上下文、谁最终处理，一目了然。对于 `eshop-gateway` 这种要同时面对数据库、缓存、支付与 LLM 上游的服务，清晰的错误语义比"少写几行"重要得多。

本章会系统讲清三件事：如何创建与判断错误（`errors.New`、`fmt.Errorf`、哨兵错误）、如何包装与还原错误链（`%w`、`errors.Is`、`errors.As`、`errors.Join`）、以及如何用 `defer` / `panic` / `recover` 管理资源释放与意外崩溃。自定义错误结构体与错误码映射，是把领域错误翻译成 HTTP 状态码的桥梁。

在 `eshop-gateway` 中，这些知识会落到具体位置：仓储层返回 `ErrNotFound`，服务层用 `%w` 补充 SKU 上下文，HTTP 层用 `errors.As` 取出错误码映射为 404/409/500，中间件用 `recover` 兜住 panic 并返回统一错误响应。本章的代码就是这条链路的原型。

## 学习目标

- 理解 `error` 是接口而非异常，掌握"错误是值"的思维方式
- 掌握 `errors.New`、`fmt.Errorf` 与自定义错误类型三种创建方式
- 理解哨兵错误（sentinel error）的设计与命名约定
- 养成早返回（early return）习惯，避免错误处理嵌套地狱
- 掌握用 `%w` 包装错误、保留错误链，理解 `%w` 与 `%v` 的差异
- 熟练使用 `errors.Is` 判断哨兵错误、`errors.As` 提取具体错误类型
- 会用 `errors.Join` 聚合多个错误，并判断聚合结果
- 能设计带错误码的自定义错误，并映射为 HTTP 状态码
- 掌握 `defer` 的 LIFO 顺序、参数求值时机与修改命名返回值的能力
- 理解 `panic` / `recover` 的适用边界，能写出兜底恢复的中间件
- 能识别常见的错误处理反模式：忽略错误、重复记录、字符串比较错误

## 理论知识讲解

### 1. error 是接口，不是异常

标准库对 `error` 的定义只有一行：

```go
type error interface {
	Error() string
}
```

任何实现了 `Error() string` 的类型都是错误。因此错误可以被赋值、返回、存入切片、作为 Map 的值，也可以被包装成另一层错误——它和 `int`、`string` 没有本质区别。

| 维度 | Go | Python | TypeScript |
|------|----|--------|-----------|
| 传递方式 | 返回值 `(T, error)` | `raise` 抛出 | `throw` 抛出 |
| 调用方 | 必须显式检查 | 可省略，异常向上冒泡 | 可省略，异常向上冒泡 |
| 控制流 | 普通返回 | 栈展开 | 栈展开 |
| 清理资源 | `defer` | `finally` / `with` | `finally` |
| 错误上下文 | 包装错误链 | 异常链 `__cause__` | `cause` 选项 |

代价是每处调用都要写 `if err != nil`；收益是**失败路径不会被隐藏**。Go 社区的经验是：把正常路径写在前面，错误分支尽早 `return`，代码依然可读。

### 2. 创建错误的三种方式

```go
// 方式一：固定文案，适合简单场景
err := errors.New("商品不存在")

// 方式二：需要拼接动态上下文
err := fmt.Errorf("商品 %s 库存不足，剩余 %d", sku, stock)

// 方式三：自定义类型，携带结构化字段
type ValidationError struct {
	Field string
	Msg   string
}
func (e ValidationError) Error() string { return e.Field + ": " + e.Msg }
```

| 方式 | 适用场景 | 能否被 `errors.Is` 命中 |
|------|---------|----------------------|
| `errors.New` | 包级哨兵错误 | 可以（同一变量） |
| `fmt.Errorf`（无 `%w`） | 一次性上下文错误 | 否 |
| `fmt.Errorf`（带 `%w`） | 包装底层错误 | 是（沿链查找） |
| 自定义类型 | 需要字段、错误码 | 配合 `errors.As` |

**哨兵错误**是包级导出的固定错误变量，命名以 `Err` 开头：

```go
var (
	ErrNotFound   = errors.New("商品不存在")
	ErrOutOfStock = errors.New("库存不足")
)
```

调用方用 `errors.Is(err, ErrNotFound)` 判断，而不是比较字符串（文案会变）或直接用 `==`（包装后失效）。

### 3. 早返回与错误传播

推荐写法：先处理错误，再走正常逻辑，避免层层缩进。

```go
func (s *Service) Deduct(sku string, n int) error {
	p, err := s.repo.Get(sku)
	if err != nil {
		return fmt.Errorf("扣减库存失败: %w", err)
	}
	if p.Stock < n {
		return fmt.Errorf("%w: 需要 %d，剩余 %d", ErrOutOfStock, n, p.Stock)
	}
	p.Stock -= n
	return s.repo.Save(p)
}
```

三条纪律：

1. **错误只处理一次**：要么在本层处理（降级、重试、返回默认值），要么向上返回，不要既打日志又返回。
2. **包装时补充上下文**：说明"在做什么时失败"，而不是重复底层文案。
3. **不要忽略错误**：确实要忽略时用 `_ = f()` 明确表态，而不是悄悄漏掉。

### 4. 用 `%w` 包装错误链

`fmt.Errorf` 中的 `%w` 不只格式化，还会把被包装的错误挂到新错误上，形成可以逐层解开的链：

```go
base := errors.New("connection refused")
err := fmt.Errorf("查询库存失败: %w", base)

fmt.Println(err)                        // 查询库存失败: connection refused
fmt.Println(errors.Unwrap(err) == base) // true
```

| 动词 | 是否进入错误链 | `errors.Is` 能否命中底层 |
|------|---------------|------------------------|
| `%v` | 否（只拼字符串） | 否 |
| `%w` | 是（实现 `Unwrap()`） | 是 |

注意：

- 一个 `fmt.Errorf` 只能有一个 `%w`（多个错误请用 `errors.Join`）
- 包装层次不宜过深，通常"领域层补一次、接口层补一次"即可
- 底层错误信息已经足够清楚时，不要再机械包装

### 5. `errors.Is` 与 `errors.As`

两者都沿错误链查找，区别在于**找什么**：

| 函数 | 查找目标 | 典型用途 |
|------|---------|---------|
| `errors.Is(err, target)` | 某个**具体的错误值** | 判断 `ErrNotFound`、`context.Canceled` |
| `errors.As(err, &target)` | 某个**错误类型** | 取出 `*AppError`、`*strconv.NumError` |

```go
// Is：逐层比较，命中哨兵错误
if errors.Is(err, ErrOutOfStock) {
	return 409
}

// As：把链上的目标类型写入 target
var appErr *AppError
if errors.As(err, &appErr) {
	fmt.Println(appErr.Code)
}
```

使用要点：

- `errors.As` 的第二个参数必须是**指向错误类型的指针**，否则会 panic
- 自定义类型若实现了 `Is(target error) bool`，可自定义相等语义
- 一个错误若实现了 `Unwrap() []error`，`Is`/`As` 会遍历所有分支（Go 1.20+）

### 6. `errors.Join` 与批量错误

表单校验、批量导入这类场景往往一次性产生多个错误。`errors.Join` 把它们合成一个：

```go
var errs []error
if name == "" {
	errs = append(errs, errors.New("名称不能为空"))
}
if price <= 0 {
	errs = append(errs, ErrInvalidPrice)
}
return errors.Join(errs...) // 全部 nil 时返回 nil
```

```go
err := errors.Join(ErrInvalidPrice, ErrOutOfStock)
fmt.Println(err)
// 两行输出：价格格式非法\n库存不足

errors.Is(err, ErrOutOfStock) // true，任意分支命中即可
```

> `errors.Join` 返回的错误实现了 `Unwrap() []error`，因此 `errors.As` 也能在多分支中找到目标类型。需要自定义文案或统计数量时，也可以像本章示例那样手写 `MultiError`。

### 7. 自定义错误类型与错误码

业务错误通常需要携带**错误码**，供 API 层映射状态码、供前端做差异化提示：

```go
type AppError struct {
	Code    ErrorCode
	Message string
	Err     error
}

func (e *AppError) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("[%d] %s: %v", e.Code, e.Message, e.Err)
	}
	return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}

func (e *AppError) Unwrap() error { return e.Err }
```

| 错误码 | 含义 | HTTP 状态 |
|--------|------|----------|
| `40001` | 参数非法 | 400 |
| `40401` | 资源不存在 | 404 |
| `40901` | 库存冲突 | 409 |
| `50001` | 内部错误 | 500 |

分层职责：

1. **领域层**只关心业务语义，返回 `ErrNotFound` 或 `ValidationError`
2. **应用层**用 `%w` 包装上下文，必要时转成 `AppError`
3. **接口层**用 `errors.As` 提取错误码，映射为 HTTP 状态码，绝不把内部错误原文直接暴露给客户端

### 8. defer 的三条语义

`defer` 把函数调用推迟到当前函数返回时执行，常用于资源释放：

```go
f, err := os.Open(path)
if err != nil {
	return err
}
defer f.Close() // 无论后面从哪返回，都会执行
```

三条必须记住的规则：

| 规则 | 说明 | 示例结果 |
|------|------|---------|
| LIFO 后进先出 | 多个 defer 逆序执行 | 注册 1、2、3，执行 3、2、1 |
| 参数立即求值 | 实参在 defer 语句处就确定 | `defer fmt.Println(i)` 打印当时的值 |
| 可修改命名返回值 | defer 在 return 赋值之后运行 | 命名返回值被改写 |

```go
func total() (sum float64, err error) {
	defer func() {
		if err == nil {
			sum *= 1.01 // 生效：返回前修改命名返回值
		}
	}()
	return 100, nil
}
```

> 常见用途：`defer f.Close()`、`defer mu.Unlock()`、`defer ticker.Stop()`、`defer cancel()`。注意 defer 在循环中会累积到函数结束才执行，循环内要释放资源时应包一层函数。

### 9. panic / recover 的边界

`panic` 表示**程序无法继续**的严重错误：数组越界、nil 解引用、断言失败、初始化配置缺失。业务错误不应该用 panic。

`recover` 只在 `defer` 中调用才有效，用于阻止 panic 继续向上展开：

```go
func safeDivide(a, b float64) (result float64, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("recover 捕获 panic: %v", r)
		}
	}()
	if b == 0 {
		panic("除数为 0")
	}
	return a / b, nil
}
```

关键点：

- `recover()` 捕获后，函数**不会回到 panic 的位置**继续执行，而是从 defer 结束后正常返回
- 命名返回值让 defer 能写入错误，这是把 panic 转成 error 的标准手法
- HTTP 中间件中务必 `recover`，否则一个请求的 panic 会终止整个进程
- 记录 panic 时建议打印 `runtime/debug.Stack()`，保留堆栈便于定位

### 10. 与 Python / TypeScript 的心智对照

| 场景 | Go 写法 | Python / TS 写法 |
|------|---------|------------------|
| 资源释放 | `defer f.Close()` | `with` / `finally` |
| 包装错误 | `fmt.Errorf("...: %w", err)` | `raise X from err` / `cause` |
| 判断错误类型 | `errors.Is` / `errors.As` | `except X` / `instanceof` |
| 兜底崩溃 | `recover` + 中间件 | 全局异常处理器 |
| 多错误 | `errors.Join` | `ExceptionGroup` / `AggregateError` |

理解了这张表，你就掌握了 Go 错误处理 80% 的日常用法；剩下的 20% 是纪律：检查每个错误，补足上下文，不吞掉失败。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/errors_basic.go` | `errors.New`、`fmt.Errorf`、哨兵错误、早返回与 `errors.Is` 判断 |
| `Code/error_wrap.go` | `%w` 包装、`errors.Is`、`errors.As`、`errors.Join`、错误链逐层打印 |
| `Code/custom_error.go` | 自定义 `AppError` / `ValidationError`、错误码到 HTTP 状态映射、批量错误聚合 |
| `Code/defer_panic.go` | defer LIFO、参数求值、修改命名返回值、panic/recover 与继续执行 |

执行方式（每个文件独立运行）：

```bash
cd "Day07 - 错误处理与defer、panic、recover/Code"
go run errors_basic.go
go run error_wrap.go
go run custom_error.go
go run defer_panic.go
```

> 每个文件都自带 `package main` 与 `func main()`，请按文件名单独运行，不要执行 `go run .`。

## 关键知识点总结

1. **错误是值**：`error` 是只有 `Error() string` 的接口，可以返回、包装、比较与聚合。
2. **显式检查**：`if err != nil` 是 Go 的常态，早返回能让正常路径保持扁平。
3. **哨兵错误**：包级 `ErrXxx` 变量配合 `errors.Is` 判断，不要比较错误字符串。
4. **`%w` 包装**：保留错误链与上下文；`%v` 只拼字符串，包装后 `Is/As` 无法命中。
5. **`errors.Is` 找值**：适合判断 `ErrNotFound`、`context.Canceled`、`io.EOF`。
6. **`errors.As` 找类型**：取出 `*AppError` 等自定义错误；目标参数必须是指针。
7. **`errors.Join` 聚合**：表单校验、批量导入一次返回多个错误，任一分支可被 `Is` 命中。
8. **错误码分层**：领域错误 → 应用错误 → HTTP 状态码，接口层不泄露内部细节。
9. **defer 三条语义**：LIFO 执行、参数立即求值、可修改命名返回值。
10. **panic 只用于不可恢复错误**：`recover` 必须写在 defer 中，捕获后函数正常返回而非原地继续。
11. **错误只处理一次**：不要既记录日志又向上返回，避免重复告警与噪音。

## 实战练习

### 练习 1：统一错误码与 HTTP 映射

新建 `error_code_exercise.go`：

1. 定义 `ErrorCode` 与 `AppError`，覆盖参数非法（400）、未找到（404）、库存冲突（409）、上游超时（504）。
2. 写函数 `ToHTTP(err error) (int, string)`，用 `errors.As` 提取错误码，返回状态码与面向用户的提示语；非 `AppError` 一律返回 500 且隐藏内部信息。
3. 构造一条"仓储 NotFound → 服务层 `%w` 包装 → 接口层映射"的调用链，打印每一层的错误文本与最终状态码。

### 练习 2：库存扣减的错误链

在 `errors_basic.go` 基础上：

1. 增加 `ErrConcurrentUpdate` 哨兵错误，模拟乐观锁版本冲突。
2. 让 `Deduct` 在库存不足与版本冲突时返回不同哨兵错误，并各自带上 SKU、请求量、剩余量。
3. 分别用 `errors.Is` 判断两种失败，输出不同的处理策略（提示用户 / 建议重试）。

### 练习 3：用 defer 统计耗时

编写 `elapsed_exercise.go`：

- 写一个 `withTiming(name string, fn func())` 函数，用 `time.Now()` 与 `defer` 打印执行耗时
- 在 `fn` 内部制造 panic，再写一个版本用 `recover` 捕获并保证耗时一定被打印
- 思考：如果 `defer` 的参数写成 `defer log(time.Since(start))`，会发生什么？改成闭包后为什么就正确了？

### 练习 4：HTTP 恢复中间件原型

不引入 `net/http`，仅用函数模拟：

1. 定义 `type Handler func(req string) (string, error)`。
2. 写 `Recover(next Handler) Handler`，内部 `defer recover()`，把 panic 转成 `error` 并打印堆栈长度。
3. 写 `Chain(h Handler, middlewares ...func(Handler) Handler)` 组装中间件，验证 panic 请求之后，后续请求仍能正常处理。
4. 说明为什么生产环境的 recover 中间件必须放在最外层。
