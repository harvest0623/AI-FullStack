# llm-gateway - 可运行的 LLM 网关

> Day13 实战项目：用 Go 标准库把上游大模型能力包装为受控的内部 API

## 项目简介

`llm-gateway` 是一个兼容 OpenAI Chat Completions 协议的轻量网关。业务方只需把请求发到本服务，由网关统一追加 API Key、控制超时、执行重试与限流，再把上游结果原样返回。它不依赖任何第三方库，可直接用 `go run .` 启动。

适合作为以下场景的起点：

- 为前端或内部系统提供统一的模型调用入口
- 在网关层集中管理密钥、超时、重试与限流
- 后续扩展 SSE 流式输出、鉴权、计费与多模型路由

## 架构

```
客户端（前端 / 内部服务）
        │  POST /v1/chat
        ▼
┌───────────────────────────────────────────────┐
│ llm-gateway                                   │
│                                               │
│  RequestID → Recover → Logging → CORS         │
│      → RateLimit → ServeMux                   │
│                       ├── GET  /healthz        │
│                       └── POST /v1/chat        │
│                              │                │
│                     Handler 校验与错误映射     │
│                              ▼                │
│                     Client（超时 + 重试）      │
└──────────────────────────────┬────────────────┘
                               │ HTTPS + Bearer API Key
                               ▼
                  上游 OpenAI 兼容 /chat/completions
```

请求处理流程：

1. `requestIDMiddleware` 生成 `X-Request-ID`，写入 context 与响应头。
2. `recoverMiddleware` 兜底 panic，避免单个请求拖垮进程。
3. `loggingMiddleware` 记录方法、路径、状态码、耗时与请求 ID。
4. `corsMiddleware` 处理跨域与 OPTIONS 预检。
5. `rateLimitMiddleware` 按分钟固定窗口计数，超限返回 429。
6. `handleChat` 校验请求体，调用 `Client.Chat`，把上游错误映射为网关状态码。

## 文件说明

| 文件 | 职责 |
| --- | --- |
| `main.go` | 配置加载、slog 初始化、HTTP 服务启动与优雅关闭 |
| `config.go` | 环境变量解析、默认值与必填项校验 |
| `client.go` | 上游请求结构、HTTP 调用、指数退避重试、`UpstreamError` |
| `handler.go` | 路由注册、请求校验、上游错误映射、统一 JSON 错误结构 |
| `middleware.go` | 请求 ID、日志、恢复、CORS、限流与中间件链 |
| `handler_test.go` | 基于 `httptest` 的单元测试，不依赖真实网络 |

## 环境变量

| 变量 | 默认值 | 必填 | 说明 |
| --- | --- | --- | --- |
| `PORT` | `8080` | 否 | 监听端口，范围 1-65535 |
| `UPSTREAM_URL` | `https://api.openai.com/v1/chat/completions` | 否 | 上游 Chat Completions 地址 |
| `API_KEY` | 无 | 是 | 上游 API Key，启动时校验非空 |
| `MODEL` | `gpt-4o-mini` | 否 | 请求未指定 `model` 时使用的默认模型 |
| `TIMEOUT` | `30s` | 否 | 单次上游调用超时，Go 时长格式 |
| `MAX_BODY_BYTES` | `1048576`（1MB） | 否 | 请求体最大字节数 |
| `RATE_LIMIT_PER_MINUTE` | `60` | 否 | 每分钟允许的请求数，`0` 表示不限流 |
| `LOG_LEVEL` | `info` | 否 | `debug` / `info` / `warn` / `error` |

> 使用本地模拟上游（如 Ollama、Mock Server）时，`API_KEY` 仍需设置为任意非空字符串，以满足启动校验。

## 运行步骤

```bash
cd "Go/Day13 - 实战：构建AI应用后端/Code/llm-gateway"

# 1. 整理依赖（本项目仅使用标准库，执行后不会新增第三方依赖）
go mod tidy

# 2. 设置上游密钥（PowerShell）
$env:API_KEY="sk-your-key"
# macOS / Linux: export API_KEY=sk-your-key

# 3. 启动
go run .
# 输出：{"time":"...","level":"INFO","msg":"llm-gateway 启动","addr":":8080",...}
```

### 健康检查

```bash
curl http://localhost:8080/healthz
# {"model":"gpt-4o-mini","service":"llm-gateway","status":"ok"}
```

### 发起对话

```bash
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "你是一个简洁的助手"},
      {"role": "user", "content": "用一句话介绍 Go 语言"}
    ],
    "temperature": 0.7
  }'
```

响应沿用 OpenAI 结构：

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Go 是一门语法简洁、原生支持并发、适合构建云原生服务的静态编译语言。"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 24,
    "completion_tokens": 28,
    "total_tokens": 52
  }
}
```

## 测试

```bash
go test ./...
go test -v ./...
go test -race ./...
```

测试使用 `httptest.NewServer` 构造假上游，通过 `NewServer(Config{...})` 注入地址，不访问真实网络。覆盖场景：

- `/healthz` 返回 200 与模型信息
- `/v1/chat` 正常转发并返回上游内容
- 非法 JSON 返回 400
- `messages` 为空返回 400
- 上游 500 映射为 502
- 错误方法返回 405

## 错误码说明

| HTTP 状态 | `error.code` | 触发场景 |
| --- | --- | --- |
| `400` | `invalid_json` | 请求体不是合法 JSON，或包含未知字段 |
| `400` | `invalid_messages` | `messages` 为空，或某条消息缺少 `role` / `content` |
| `400` | `upstream_bad_request` | 上游返回 4xx（鉴权类除外），通常由参数导致 |
| `413` | `request_too_large` | 请求体超过 `MAX_BODY_BYTES` |
| `429` | `rate_limited` | 触发网关本地限流，响应带 `Retry-After` |
| `429` | `upstream_rate_limited` | 上游返回 429，响应带 `Retry-After` |
| `500` | `internal_error` | 处理器 panic，被恢复中间件捕获 |
| `502` | `upstream_error` / `upstream_auth_failed` / `upstream_unavailable` | 上游 5xx、鉴权失败或网络不可达 |
| `504` | `upstream_timeout` | 上游调用超时或 context 被取消 |

统一错误结构：

```json
{
  "error": {
    "code": "upstream_error",
    "message": "上游返回的具体错误信息"
  }
}
```

## 扩展方向

1. **SSE 流式输出**：在 `ChatRequest.Stream` 为 `true` 时，把上游 `text/event-stream` 逐块刷新给客户端，需要设置 `Content-Type: text/event-stream` 并处理 `http.Flusher`。
2. **鉴权与配额**：为业务方签发内部 API Key，按 Key 维度限流与计量；可结合 `Day11` 的鉴权中间件思路。
3. **真实计费**：解析上游 `usage`，按模型单价累计 token 成本，写入数据库或消息队列。
4. **多模型路由**：根据请求头、租户或提示词长度选择不同上游模型，并维护模型白名单。
5. **可观测性**：暴露 `/metrics` 供 Prometheus 抓取，记录请求数、延迟直方图、上游错误率。
6. **分布式限流**：将固定窗口计数替换为 Redis 原子计数，支持多实例部署。