# Day13 - 实战：构建 AI 应用后端（LLM 网关）

## 学习目标

- 把零散的语言知识组织为分层清晰、职责单一的服务代码
- 掌握基于环境变量的配置管理与启动校验
- 理解 HTTP 客户端超时、错误分类与指数退避重试
- 编写可组合的中间件链（请求 ID、日志、恢复、CORS、限流）
- 用 `httptest` 对依赖外部 HTTP 服务的代码做可靠测试
- 理解 `http.Server` 超时配置与 `Shutdown` 优雅关闭

## 项目背景与目标

企业内部多个系统都要调用大模型。如果各自持有密钥、各自实现重试与限流，会带来密钥扩散、行为不一致、成本不可控、协议不统一四个问题。解决方式是提供统一的受控入口：对外暴露稳定协议，对内集中管理上游地址、密钥、模型与容错策略。本项目目标：

- 提供 `GET /healthz` 与 `POST /v1/chat`
- 兼容 OpenAI 请求/响应结构，业务方可复用现有 SDK
- 上游故障时返回明确、可重试的状态码，而不是原样透传异常
- 单机可运行，代码可测试、可容器化

## 需求分析

### 功能需求

| 编号 | 需求 | 实现位置 |
| --- | --- | --- |
| F1 | 从环境变量读取端口、上游地址、密钥、模型等配置 | `config.go` |
| F2 | 健康检查返回服务名、状态与默认模型 | `handler.go` |
| F3 | 校验 `messages` 非空及每条消息的 `role` / `content` | `handler.go` |
| F4 | 以 Bearer Token 调用上游 Chat Completions | `client.go` |
| F5 | 429、5xx 与网络错误自动重试，最多 2 次 | `client.go` |
| F6 | 限制请求体大小，拒绝非法 JSON 与未知字段 | `handler.go` |
| F7 | 把上游错误映射为 400 / 429 / 502 / 504 | `handler.go` |
| F8 | 生成请求 ID 并记录结构化访问日志 | `middleware.go` |
| F9 | 捕获 panic，返回 500 而不终止进程 | `middleware.go` |
| F10 | 按分钟限流，超限返回 429 与 `Retry-After` | `middleware.go` |
| F11 | 支持 CORS 预检，便于前端联调 | `middleware.go` |
| F12 | 收到 SIGINT/SIGTERM 后优雅关闭 | `main.go` |

### 非功能需求

| 维度 | 要求 | 设计手段 |
| --- | --- | --- |
| 性能 | 承载常规内部流量 | 标准库 `net/http`、轻量中间件 |
| 可靠性 | 上游短时抖动可恢复 | 分类重试 + 指数退避 + context 取消 |
| 安全 | 密钥不泄露、请求体不无限增长 | 环境变量注入、日志脱敏、`MaxBytesReader` |
| 可观测 | 能按请求追踪问题 | `X-Request-ID` + `slog` 结构化日志 |
| 可测试 | 不依赖真实上游 | 依赖注入 + `httptest` 假上游 |
| 可部署 | 单一静态二进制、镜像小 | 仅标准库、`CGO_ENABLED=0`、多阶段构建 |
| 可维护 | 职责单一、易于扩展 | 按配置/客户端/处理器/中间件拆分文件 |

## 架构设计

```
                 业务方（Web / 内部服务 / SDK）
                           │ POST /v1/chat
                           ▼
┌─────────────────────────────────────────────────────┐
│                   llm-gateway                       │
│                                                     │
│ requestID → recover → logging → CORS → rateLimit    │
│                        │                            │
│                   http.ServeMux                     │
│             ┌──────────┴──────────┐                 │
│       GET /healthz          POST /v1/chat           │
│             │                     │                 │
│             ▼                     ▼                 │
│        健康信息 JSON      handleChat 校验与错误映射   │
│                                   │                 │
│                            Client.Chat              │
│                       （超时 / 重试 / 错误分类）      │
└───────────────────────────────────┬─────────────────┘
                                    │ HTTPS + Bearer Key
                                    ▼
                     上游 OpenAI 兼容 /chat/completions
```

一次对话请求的生命周期：

1. 生成 `X-Request-ID`，注册 `defer recover` 兜住 panic。
2. 日志中间件计时并包装 `ResponseWriter`，记录状态码。
3. CORS 处理跨域与 OPTIONS 预检；限流中间件按分钟计数。
4. `handleChat` 限制请求体、解码 JSON 并校验字段。
5. `Client.Chat` 补默认模型、追加鉴权头并调用上游。
6. 2xx 原样返回；429/5xx/网络错误退避重试；失败则映射错误。

## 接口设计

### GET /healthz

用于存活探针与本地自检，不消耗限流配额。

```json
{"service": "llm-gateway", "status": "ok", "model": "gpt-4o-mini"}
```

### POST /v1/chat

请求头：`Content-Type: application/json`。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `model` | string | 否 | 为空时使用服务端 `MODEL` |
| `messages` | array | 是 | 至少一条消息 |
| `messages[].role` | string | 是 | 常用 `system` / `user` / `assistant` |
| `messages[].content` | string | 是 | 消息正文，不能为空 |
| `temperature` | number | 否 | 采样温度，0 会被 `omitempty` 省略 |
| `stream` | bool | 否 | 字段保留，当前版本不实现流式 |

请求示例：

```json
{"messages":[{"role":"system","content":"你是一个简洁的助手"},{"role":"user","content":"用一句话介绍 Go 语言"}],"temperature":0.7}
```

成功响应沿用 OpenAI 结构：

```json
{
  "id": "chatcmpl-...", "object": "chat.completion", "model": "gpt-4o-mini",
  "choices": [{"index": 0, "message": {"role": "assistant", "content": "Go 是一门语法简洁、原生支持并发的静态编译语言。"}}], "usage": {"prompt_tokens": 24, "completion_tokens": 20, "total_tokens": 44}
}
```

错误响应统一为：

```json
{"error": {"code": "upstream_error", "message": "上游返回的具体错误信息"}}
```

| HTTP | `error.code` | 触发条件 |
| --- | --- | --- |
| 400 | `invalid_json` | JSON 非法、含未知字段或请求体为空 |
| 400 | `invalid_messages` | `messages` 为空，或消息缺少 `role` / `content` |
| 400 | `upstream_bad_request` | 上游返回 4xx（401/403/429 除外） |
| 413 | `request_too_large` | 请求体超过 `MAX_BODY_BYTES` |
| 429 | `rate_limited` | 触发网关本地限流 |
| 429 | `upstream_rate_limited` | 上游返回 429 |
| 500 | `internal_error` | 处理器 panic，被恢复中间件捕获 |
| 502 | `upstream_auth_failed` | 上游 401/403，通常是网关密钥配置错误 |
| 502 | `upstream_error` | 上游 5xx，重试后仍失败 |
| 502 | `upstream_unavailable` | 网络不可达、DNS 失败等 |
| 504 | `upstream_timeout` | 上游超时或客户端取消 |

> 映射原则：调用方的问题返回 4xx，上游的问题返回 5xx，网关限流返回 429；不把上游 401 直接透传。

## 项目结构

```
Day13 - 实战：构建AI应用后端/
├── README.md
└── Code/llm-gateway/
    ├── go.mod              ← module eshop/llm-gateway，go 1.22
    ├── main.go             ← 入口、日志、HTTP 服务、优雅关闭
    ├── config.go           ← 环境变量、默认值、校验
    ├── client.go           ← 数据结构、上游调用、重试
    ├── handler.go          ← 路由、校验、错误映射
    ├── middleware.go       ← 请求 ID、日志、恢复、CORS、限流
    ├── handler_test.go     ← httptest 单元测试
    └── README.md           ← 子项目运行说明
```

| 文件 | 关键类型/函数 | 职责 |
| --- | --- | --- |
| `config.go` | `Config`、`LoadConfig`、`Validate` | 配置来源与合法性 |
| `client.go` | `Client`、`ChatRequest`、`UpstreamError` | 上游协议与容错 |
| `handler.go` | `Server`、`Routes`、`handleChat` | HTTP 适配层 |
| `middleware.go` | `chain`、`rateLimiter` | 横切关注点 |
| `main.go` | `main`、`initLogger` | 进程生命周期 |
| `handler_test.go` | 6 个测试用例 | 行为验证 |

## 核心实现讲解

### 1. 配置管理：config.go

配置全部来自环境变量，按"读取 → 解析 → 校验"三步构造。`envInt` / `envInt64` / `envDuration` 收拢重复逻辑，解析失败用 `%w` 包装原始错误：

```go
port, err := envInt("PORT", 8080)
if err != nil {
    return Config{}, err
}
```

`Validate` 要求上游地址为 http/https、模型非空、API Key 非空。配置错误在启动时立即暴露，而不是等第一个请求才发现。

### 2. 上游客户端与重试：client.go

`Chat` 先补默认模型，再序列化请求。重试循环最多执行 `1 + maxRetries` 次，退避 100ms、200ms：

```go
backoff := baseBackoff << (attempt - 1)
select {
case <-ctx.Done():
    return nil, fmt.Errorf("等待重试时请求已取消: %w", ctx.Err())
case <-time.After(backoff):
}
```

只重试值得重试的错误：

| 情况 | 重试 | 原因 |
| --- | --- | --- |
| 429 | 是 | 上游限流，短暂等待后可能恢复 |
| 5xx | 是 | 上游临时故障 |
| 网络错误 | 是 | 连接失败或被重置 |
| context 取消/超时 | 否 | 调用方已不需要结果 |
| 其它 4xx | 否 | 参数问题，重试无意义 |

非 2xx 响应读取最多 64KB 错误体，优先解析 OpenAI 的 `{"error": {...}}`，再包装为携带 `StatusCode` 的 `UpstreamError`，处理器可用 `errors.As` 提取状态码。

### 3. 中间件链：middleware.go

`chain` 从右向左包装，使声明顺序等于执行顺序：

```go
func chain(h http.Handler, mw ...func(http.Handler) http.Handler) http.Handler {
    for i := len(mw) - 1; i >= 0; i-- {
        h = mw[i](h)
    }
    return h
}
```

- **requestID**：`atomic.Uint64` 生成递增 ID，写入 context 与响应头。
- **logging**：`statusRecorder` 捕获状态码，`slog` 输出方法、路径、状态、耗时。
- **recover**：`defer recover()` 捕获 panic，返回统一 500。
- **CORS**：OPTIONS 直接 204，不进入业务路由。
- **rateLimit**：`sync.Mutex` 保护窗口与计数，跨分钟自动重置；健康检查不占配额。

固定窗口实现简单，但窗口切换瞬间可能放过两倍流量；生产环境可换滑动窗口或 Redis 计数。

### 4. 请求校验与错误映射：handler.go

```go
r.Body = http.MaxBytesReader(w, r.Body, s.cfg.MaxBodyBytes)
dec := json.NewDecoder(r.Body)
dec.DisallowUnknownFields()
```

`MaxBytesReader` 防止超大报文耗尽内存；`DisallowUnknownFields` 让拼写错误立即报错。随后校验 `messages` 非空及每条消息的 `role` / `content`。

错误映射集中在 `writeUpstreamError`：用 `errors.As` 取出 `UpstreamError` 并按状态码映射；用 `errors.Is` 判断 `context.DeadlineExceeded` / `Canceled` 并返回 504。由于客户端用 `%w` 包装错误，跨多层仍能正确识别。

### 5. 优雅关闭：main.go

```go
httpServer := &http.Server{
    Addr:              fmt.Sprintf(":%d", cfg.Port),
    Handler:           server.Routes(),
    ReadHeaderTimeout: 5 * time.Second,
    ReadTimeout:       15 * time.Second,
    WriteTimeout:      60 * time.Second,
    IdleTimeout:       60 * time.Second,
}
```

用 `signal.NotifyContext` 监听 `os.Interrupt` 与 `SIGTERM`。收到信号后调用带 10 秒超时的 `Shutdown`：停止接受新连接，等待在途请求完成。启动日志只打印端口、上游地址与模型，不打印 API Key。

## 运行与测试

```bash
cd "Go/Day13 - 实战：构建AI应用后端/Code/llm-gateway"
go mod tidy

# PowerShell 设置密钥（macOS/Linux 用 export API_KEY=...）
$env:API_KEY="sk-your-key"
go run .
```

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `PORT` | `8080` | 监听端口 |
| `UPSTREAM_URL` | `https://api.openai.com/v1/chat/completions` | 上游地址 |
| `API_KEY` | 无（必填） | 上游密钥 |
| `MODEL` | `gpt-4o-mini` | 默认模型 |
| `TIMEOUT` | `30s` | 上游调用超时 |
| `MAX_BODY_BYTES` | `1048576` | 请求体上限 |
| `RATE_LIMIT_PER_MINUTE` | `60` | 每分钟请求数，0 为不限 |
| `LOG_LEVEL` | `info` | 日志级别 |

验证接口：

```bash
curl http://localhost:8080/healthz

curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"用一句话介绍 Go 语言"}]}'
```

若暂无真实密钥，可把 `UPSTREAM_URL` 指向本地 Mock 服务，`API_KEY` 填任意非空值即可启动。测试命令：

```bash
go test ./...
go test -v ./...
go test -race ./...
```

测试用 `httptest.NewServer` 构造假上游，覆盖健康检查、正常转发、非法 JSON、空消息、上游 500 映射与 405，全程不访问真实网络。

## 部署建议

推荐多阶段构建，产物为静态二进制，最终镜像不含编译工具链：

```dockerfile
FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY *.go ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/llm-gateway .

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/llm-gateway /llm-gateway
EXPOSE 8080
ENTRYPOINT ["/llm-gateway"]
```

```bash
docker build -t eshop/llm-gateway:0.1.0 .
docker run --rm -p 8080:8080 -e API_KEY=sk-your-key eshop/llm-gateway:0.1.0
```

- 密钥通过 Kubernetes Secret、Docker secret 或密钥管理服务注入，不写进镜像、不提交 Git；不同环境使用不同密钥并定期轮换。
- 网关前置于 Nginx / Ingress，由其终止 TLS 并做第一层限流。
- 多实例部署时本地固定窗口失效，需改为 Redis 共享计数；`WriteTimeout` 应大于最长上游耗时。

## 扩展方向

| 方向 | 关键改动 |
| --- | --- |
| SSE 流式输出 | 传递 `stream=true`，设置 `text/event-stream`，用 `http.Flusher` 逐块转发并处理 `[DONE]` |
| 内部鉴权 | 新增 Bearer Key 校验中间件，按调用方限流与统计 |
| 多模型路由 | 维护模型白名单，按租户、请求头或提示词长度选择上游 |
| 真实计费 | 解析 `usage`，按模型单价累计成本并异步落库 |
| Prometheus 指标 | 新增 `/metrics`，记录请求数、延迟直方图、上游错误率 |
| 分布式限流 | 用 Redis `INCR + EXPIRE` 替换本地固定窗口 |
| 请求缓存 | 对相同提示词做短 TTL 缓存，降低重复调用成本 |
| 内容安全 | 转发前后接入敏感词与合规检查 |

## 关键知识点总结

1. **配置外置**：环境变量 + 默认值 + 启动校验，让同一份二进制适配不同环境。
2. **依赖注入**：`NewServer(Config)` 让测试可指向假上游，避免真实网络依赖。
3. **超时分层**：`http.Server` 的四个超时保护服务端，`http.Client.Timeout` 保护上游调用。
4. **分类重试**：只重试 429、5xx 与网络错误，指数退避避免放大故障。
5. **context 传播**：请求取消能穿透到上游调用与重试等待，及时释放资源。
6. **错误包装**：`%w` + `errors.Is/As` 保留错误链，才能在处理器正确映射状态码。
7. **中间件组合**：`chain` 从右向左包装，声明顺序即执行顺序。
8. **统一错误结构**：状态码表达类别，`code` 表达机器可读原因，`message` 提供人类可读信息。
9. **请求体防护**：`MaxBytesReader` 限制大小，`DisallowUnknownFields` 拒绝意外字段。
10. **优雅关闭**：`signal.NotifyContext` + `Shutdown`，让在途请求有完成机会；请求 ID 则贯穿日志便于排查。

## 实战练习

1. **SSE 流式输出**：当 `stream=true` 时以 `text/event-stream` 转发上游数据块，逐块 `Flush`，正确处理 `data: [DONE]`，客户端断开时取消上游请求。
2. **内部鉴权**：新增 `AUTH_TOKENS`（逗号分隔），校验 `Authorization: Bearer <token>`，失败返回 401，并按 token 统计调用次数。
3. **多模型路由**：维护模型白名单，按请求头 `X-Model-Tier`（`fast` / `quality`）选择上游模型，白名单外返回 400。
4. **Prometheus 指标**：新增 `GET /metrics`，输出请求总数、按状态码分类计数与上游耗时直方图，注意并发安全。
5. **表驱动测试**：为 `handleChat` 覆盖缺少 `role`、空 `content`、未知字段、超大请求体、上游 401/429，断言 `error.code` 与 `Retry-After`。

## 与 Day01-Day12 的知识串联

| 天数 | 在本项目中的落点 |
| --- | --- |
| Day01 | `package main`、模块初始化、`go run .`、`gofmt` 风格 |
| Day02 | 类型、零值、`strconv` 解析环境变量 |
| Day03 | 多返回值、闭包（中间件）、`defer`（recover、关闭响应体） |
| Day04 | 切片（`messages`）、Map（健康检查响应） |
| Day05 | 字符串处理、指针接收者、值/指针语义 |
| Day06 | 结构体、JSON 标签、`http.Handler` 的隐式实现 |
| Day07 | `error`、`%w` 包装、`errors.Is/As`、`panic/recover` |
| Day08 | `time`、`slog`、`strings`、`net/url` |
| Day09 | goroutine、`sync.Mutex`、`atomic`、`context`、超时控制 |
| Day10 | `encoding/json`、`net/http` 客户端、状态码处理 |
| Day11 | `ServeMux` 路由、中间件、统一错误、优雅关闭 |
| Day12 | `httptest`、表驱动测试、`-race`、静态编译与容器化 |

至此，Day01-Day12 的知识点都在一个真实服务中找到了位置。建议独立重写一遍，再按练习逐步扩展，完成从"会语法"到"能交付"的转变。