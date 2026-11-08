# Day11 - Web 服务与 RESTful API

## 本章简介

Go 的标准库 `net/http` 是一个"开箱即用"级别的 HTTP 实现：无需第三方框架，就能写出生产可用的服务。它同时提供客户端与服务端、连接管理、超时控制、路由与中间件所需的全部原语，Kubernetes 的 API Server、Prometheus、etcd 的 HTTP 接口都构建在其上。本章从 `http.Handler` 出发，讲清请求从 TCP 连接到业务函数的完整链路；用 Go 1.22 增强的 `ServeMux` 编写 REST 风格的商品 CRUD 接口，实现日志、异常恢复、CORS、请求 ID 四个中间件；最后补齐上线必备的超时配置与优雅关闭。学完本章，你已能把 Day10 的 JSON 与 HTTP 知识组装成可交付的 API 服务。

## 学习目标

- 理解 `net/http` 服务端的请求生命周期：Listener → Conn → goroutine → Handler
- 掌握 `http.Handler` 接口与 `http.HandlerFunc` 适配器的关系
- 能使用 Go 1.22 的 `ServeMux` 注册"方法 + 路径"路由并读取 `PathValue`
- 理解 RESTful 资源建模、HTTP 方法语义与幂等性，熟练使用 `json.Decoder` / `json.Encoder`
- 掌握 200/201/204/400/404/405/500 等状态码的正确使用场景
- 能设计统一的错误响应结构，避免每个接口各自拼装 JSON
- 理解中间件的函数签名、链式包装与请求/响应两阶段的执行顺序
- 能实现日志、panic 恢复、CORS、请求 ID 四个中间件
- 理解四个超时字段的差异，能用 `signal.NotifyContext` + `Server.Shutdown` 实现优雅关闭
- 能用 `sync.RWMutex` 编写并发安全的内存仓储

## 理论知识讲解

### 1. net/http 服务端架构

```
TCP 连接 → net.Listen → http.Server（Listener + 超时 + Handler）
   ▼ Accept：每连接一个 goroutine，解析请求行/头/体
http.Request + http.ResponseWriter
   ▼ Server.Handler.ServeHTTP → ServeMux 路由 → 业务 Handler
写状态码 → 响应头 → 响应体 → 连接复用或关闭
```

关键事实：

- **每个连接一个 goroutine**：Go 用同步阻塞的写法获得并发能力，业务代码不需要回调。
- **`http.Server` 不是 Handler**：它把请求交给 `Handler` 字段（为 nil 时使用 `http.DefaultServeMux`）。
- **`ServeMux` 是 Handler**：它实现 `ServeHTTP`，职责是按 `r.URL.Path` 找到子 Handler。
- **状态码一旦写出就不可更改**，因此"先判断、后写头"是硬性顺序。

### 2. Handler 与 HandlerFunc

```go
type Handler interface {
	ServeHTTP(ResponseWriter, *Request)
}

type HandlerFunc func(ResponseWriter, *Request)

func (f HandlerFunc) ServeHTTP(w ResponseWriter, r *Request) {
	f(w, r)
}
```

`HandlerFunc` 是**适配器模式**的经典应用：普通函数没有方法，无法满足接口；给它定义 `ServeHTTP`（内部调用自身），函数就变成了 Handler。这与 Day06 的"方法集决定接口实现"完全一致。

```go
mux.HandleFunc("GET /hello", handleHello)             // 内部自动转换
var h http.Handler = http.HandlerFunc(handleHealth)   // 显式转换
mux.Handle("GET /healthz", h)
```

> 自定义 Handler 类型时通常用**指针接收者**实现 `ServeHTTP`，因为处理器往往持有仓储、配置、日志器等状态。

### 3. Go 1.22 增强的 ServeMux

Go 1.22 之前 `ServeMux` 只能按前缀匹配，路径参数必须自己解析；Go 1.22 引入模式语法：

| 模式 | 含义 |
| --- | --- |
| `/api/products` | 精确匹配该路径 |
| `/api/` | 前缀匹配（以 `/` 结尾即子树） |
| `GET /api/products` | 额外限定方法 |
| `GET /api/products/{id}` | 单段通配，值通过 `r.PathValue("id")` 获取 |
| `GET /files/{path...}` | 匹配剩余全部路径段 |
| `GET /{$}` | 仅匹配根路径 `/`，不做前缀兜底 |

- **更具体的模式优先**，与方法无关（`GET /api/products/{id}` 优先于 `/api/`）；同一路径注册了其他方法时，方法不匹配会**自动返回 405** 并带上 `Allow` 头。
- 路径参数是字符串，需要 `strconv.Atoi` 等手动转换与校验；**业务校验仍要自己做**。

```go
mux.HandleFunc("GET /api/products/{id}", func(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.Atoi(r.PathValue("id"))
	// ...
})
```

### 4. RESTful 设计

REST 的核心是"用名词表示资源，用 HTTP 方法表示动作"：

| 方法 | 路径 | 语义 | 成功状态码 | 幂等 |
| --- | --- | --- | --- | --- |
| GET | `/api/products` | 查询列表 | 200 | 是 |
| GET | `/api/products/{id}` | 查询单个 | 200 / 404 | 是 |
| POST | `/api/products` | 创建 | 201 + `Location` | 否 |
| PUT | `/api/products/{id}` | 整体替换 | 200 / 404 | 是 |
| DELETE | `/api/products/{id}` | 删除 | 204 / 404 | 是 |

- 路径用**复数名词**，不要出现动词（`/getProduct` 是反模式）。
- 创建成功返回 **201**，并在 `Location` 头给出新资源地址。
- 删除成功返回 **204 No Content**，响应体必须为空。
- 资源不存在返回 404，而不是 200 + `{"data": null}`；版本号放在路径前缀（`/api/v1/...`）便于演进。

本章 `rest_api.go` 用 `map[int]Product` 加 `sync.RWMutex` 实现内存仓储：读多写少场景下 `RLock` 可并发进入，`Lock` 独占，与 Day09 的并发知识直接衔接。

### 5. JSON 请求与响应

**读取请求体**优先用流式 `json.Decoder`，比 `json.Unmarshal` 更省内存，也便于配合限制器：

```go
dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20)) // 最大 1MB
dec.DisallowUnknownFields()                                   // 拒绝拼错的字段
if err := dec.Decode(&input); err != nil {
	writeError(w, http.StatusBadRequest, "invalid_json", err.Error())
	return
}
```

**写出响应**用 `json.Encoder`：先 `Set("Content-Type", "application/json; charset=utf-8")`，再 `WriteHeader(status)`，最后 `Encode(v)`（会自动追加换行）。`Encode` 的错误发生在写头之后，已无法改状态码，只能记日志。

常见坑：

- 结构体字段必须**首字母大写**才会被 `encoding/json` 处理，小写字段会被静默忽略；`json:"name,omitempty"` 在零值时省略字段。
- 请求体只能读一次；需要重复使用时先 `io.ReadAll` 再解析。

### 6. 状态码与统一错误结构

| 状态码 | 使用场景 |
| --- | --- |
| 200 OK | 查询、更新成功 |
| 201 Created | 创建成功，返回新资源与 `Location` |
| 204 No Content | 删除成功，无响应体 |
| 400 Bad Request | JSON 语法错误、字段校验失败、ID 非法 |
| 404 Not Found | 资源或路由不存在 |
| 405 Method Not Allowed | 路径存在但方法不支持 |
| 500 Internal Server Error | 未预期错误、panic 被恢复后 |

统一错误结构让客户端用同一套逻辑处理失败：

```json
{ "code": "not_found", "message": "商品不存在" }
```

原则是：**`code` 供程序判断，`message` 供人阅读**；生产环境不要把内部堆栈、SQL 语句放进 `message`。

### 7. 中间件原理

中间件本质是"接收一个 Handler，返回一个 Handler 的函数"：

```go
type Middleware func(http.Handler) http.Handler

func Chain(h http.Handler, mws ...Middleware) http.Handler {
	for i := len(mws) - 1; i >= 0; i-- { // 逆序包装，保证第一个参数在最外层
		h = mws[i](h)
	}
	return h
}
```

以 `Chain(mux, RequestID, Logging, Recover, CORS)` 为例：

```
请求 → RequestID → Logging → Recover → CORS → 业务 Handler
响应 ← RequestID ← Logging ← Recover ← CORS ← 业务 Handler
```

**请求阶段**按注册顺序执行，**响应阶段**反向返回，因此 `Logging` 能在 `next.ServeHTTP` 之后拿到耗时与状态码。`Recover` 必须包住可能 panic 的业务代码，`defer recover()` 把 panic 转成 500。`RequestID` 通过 `context.WithValue` 向下传递，业务用 `r.Context().Value(key)` 读取；context 的键要用**自定义类型**，避免不同包使用同名字符串互相覆盖。

记录状态码需要包装 `ResponseWriter`：

```go
type statusRecorder struct {
	http.ResponseWriter
	status int
}
func (r *statusRecorder) WriteHeader(code int) { r.status = code; r.ResponseWriter.WriteHeader(code) }
```

CORS 中间件对 `OPTIONS` 预检直接返回 204；`Access-Control-Allow-Origin: *` 只适合公开 API，带 Cookie 的接口必须回显具体来源。

### 8. http.Server 超时配置

不设超时的服务会被慢连接耗尽资源（Slowloris 攻击）。四个超时的分工：

| 字段 | 约束范围 | 建议 |
| --- | --- | --- |
| `ReadHeaderTimeout` | 从连接建立到读完请求头 | 3-10 秒，必须设置 |
| `ReadTimeout` | 读完请求头 + 请求体的总时长 | 10-30 秒 |
| `WriteTimeout` | 从读完请求头到写完响应的时长 | 10-30 秒；SSE/大文件需放宽或置 0 |
| `IdleTimeout` | keep-alive 连接的空闲等待 | 60-120 秒 |

另有 `MaxHeaderBytes` 限制请求头大小（默认 1MB）。`WriteTimeout` 覆盖整个处理过程，**长耗时任务不能依赖它来保证完成**，应改为异步任务 + 查询接口。

### 9. 优雅关闭

"优雅"的含义是：停止接收新连接，但让已经到达的请求处理完再退出。Kubernetes 滚动更新会向容器发送 SIGTERM，如果服务直接退出，正在处理的请求会失败，用户看到 502。

```go
ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
defer stop()
go func() { errCh <- srv.ListenAndServe() }()

select {
case err := <-errCh:
	// 启动失败（如端口被占用）
case <-ctx.Done():
	stop() // 第二次 Ctrl+C 可强制退出
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		_ = srv.Close() // 超时后强制断开
	}
}
```

`Shutdown` 的行为：关闭 Listener 拒绝新连接 → 关闭所有空闲连接 → 等待在途请求完成，直到传入的 context 超时 → 不等待被劫持的连接（WebSocket、`Hijack`），这类服务需要额外的关闭通知。

实践中把 `shutdownTimeout` 设为小于 Kubernetes 的 `terminationGracePeriodSeconds`，留出清理缓冲。

## 代码文件说明

| 文件 | 监听端口 | 用途 |
| --- | --- | --- |
| `Code/basic_server.go` | `:8081` | 最小服务：`ServeMux`、`HandlerFunc`、查询参数、JSON 响应、404 兜底 |
| `Code/rest_api.go` | `:8082` | 商品 REST API：内存仓储、路径参数、五个 CRUD 接口、统一错误 |
| `Code/middleware.go` | `:8083` | 四个中间件与链式组合，含 panic 演示接口与请求 ID 透传 |
| `Code/graceful_shutdown.go` | `:8084` | 超时配置、信号监听、`Shutdown` 与 10 秒强制退出 |

四个服务**监听不同端口**，请分别开终端运行：

```bash
cd "Day11 - Web服务与RESTful API/Code"
go run basic_server.go        # 终端 1，:8081
go run rest_api.go            # 终端 2，:8082
go run middleware.go          # 终端 3，:8083
go run graceful_shutdown.go   # 终端 4，:8084
```

> 服务启动后会阻塞占住终端，因此**必须在另一个终端执行 curl**，否则看不到响应。PowerShell 中 `curl` 是 `Invoke-WebRequest` 的别名，建议使用 `curl.exe`。

### basic_server.go 验证

```bash
curl.exe -i "http://localhost:8081/hello?name=张三&count=2"
curl.exe -i http://localhost:8081/healthz
curl.exe -i http://localhost:8081/not-exist        # 404 JSON
curl.exe -i -X POST http://localhost:8081/hello    # 405 Method Not Allowed
```

### rest_api.go 验证

```bash
# 列表与单个查询（404 示例：/api/products/99）
curl.exe -i http://localhost:8082/api/products
curl.exe -i http://localhost:8082/api/products/1
# 创建：201 + Location
curl.exe -i -X POST http://localhost:8082/api/products -H "Content-Type: application/json" -d "{\"name\":\"iPad Air\",\"price\":4799,\"stock\":60}"
# 更新：200
curl.exe -i -X PUT http://localhost:8082/api/products/1 -H "Content-Type: application/json" -d "{\"name\":\"iPhone 15 Pro\",\"price\":7999,\"stock\":80}"
# 删除：204 无响应体；校验失败：400
curl.exe -i -X DELETE http://localhost:8082/api/products/2
curl.exe -i -X POST http://localhost:8082/api/products -H "Content-Type: application/json" -d "{\"name\":\"\",\"price\":-1}"
```

### middleware.go 验证

```bash
curl.exe -i http://localhost:8083/api/ping            # 观察 X-Request-ID 响应头
curl.exe -i http://localhost:8083/api/panic           # 500，终端日志含堆栈
curl.exe -i -X OPTIONS http://localhost:8083/api/ping # 204，CORS 预检
```

### graceful_shutdown.go 验证

```bash
# 终端 B 发起 3 秒慢请求；终端 A 在请求进行中按 Ctrl+C，日志显示"开始优雅关闭"
curl.exe -i http://localhost:8084/slow
# 慢请求仍返回 200；再次 Ctrl+C 立即退出
```

## 关键知识点总结

1. **Handler 是唯一抽象**：`ServeMux`、中间件、业务处理器都实现 `ServeHTTP`；`HandlerFunc` 则是把函数适配为 Handler 的适配器。
2. **Go 1.22 路由**：支持 `GET /items/{id}`，`PathValue` 取参数，方法不匹配自动 405。
3. **REST 语义**：名词做路径、方法表动作、201 带 `Location`、204 无响应体、404 不伪装成 200。
4. **JSON 流式处理**：`Decoder` + `MaxBytesReader` + `DisallowUnknownFields` 是接收请求体的标准组合。
5. **错误结构统一**：`code` 给程序、`message` 给人；状态码与业务错误码分层，不泄露内部细节。
6. **中间件签名**：`func(http.Handler) http.Handler`；`Chain` 逆序包装让第一个参数位于最外层，请求正序、响应逆序。
7. **panic 恢复**：`defer recover()` 只能捕获当前 goroutine 的 panic，无法跨 goroutine 兜底。
8. **超时四件套**：`ReadHeaderTimeout` 防慢头攻击，`ReadTimeout` / `WriteTimeout` 约束单次请求，`IdleTimeout` 控制复用连接。
9. **优雅关闭**：`NotifyContext` 收信号 → `Shutdown(ctx)` 等待在途请求 → 超时后 `Close()` 强制断开。
10. **并发安全仓储**：`RWMutex` 的 `RLock` 允许多读并发、`Lock` 独占写；对外返回切片快照而非共享 map。

## 实战练习

### 练习 1：为商品 API 增加分页与过滤

在 `rest_api.go` 基础上扩展 `GET /api/products`：

- 支持 `?page=1&size=10`（默认第 1 页、每页 10 条，`size` 上限 100）与 `?keyword=iphone`（对 `Name` 做不区分大小写的包含匹配）。
- 返回 `{"items": [...], "total": 2, "page": 1, "size": 10}`，非法参数返回 400。提示：用 `strings.Contains(strings.ToLower(name), strings.ToLower(keyword))`，分页计算要防止越界。

### 练习 2：独立实现请求 ID + 访问日志中间件

不参考 `middleware.go`，完成：

- 请求头带 `X-Request-ID` 则复用，否则自行生成（时间戳 + 自增计数）；把 ID 写入响应头并放入 context。
- 日志格式为 `request_id method path status duration`，用 `statusRecorder` 记录状态码，验证未显式调用 `WriteHeader` 时状态码为 200。

### 练习 3：实现简易限流中间件

写一个基于令牌桶的 `RateLimit(limit int, interval time.Duration)`：

- 每个 IP 按固定速率放行，超出返回 429 与 `{"code":"rate_limited"}`；用 `sync.Mutex` + `map[string]time.Time` 记录上次放行时间。
- 思考：进程水平扩展成 3 个副本后，这种内存限流会有什么问题？生产环境应如何改？

### 练习 4：优雅关闭演练

1. 启动 `graceful_shutdown.go`，连续发起 20 个 `/slow` 请求；请求进行中按 Ctrl+C，确认所有在途请求都返回 200。
2. 把 `shutdownTimeout` 改为 `1 * time.Second` 再试，观察哪些请求被强制中断；结合 Docker 解释为什么服务端超时必须小于 `docker stop` 的 10 秒宽限期。