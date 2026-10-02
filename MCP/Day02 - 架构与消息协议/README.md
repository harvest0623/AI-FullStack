# Day02 - 架构与消息协议

> 深入 MCP 的通信骨架：它基于 JSON-RPC 2.0、支持 stdio 与 Streamable HTTP 两种传输、并有一套明确的会话生命周期。理解这些，你就懂了 MCP『背后怎么聊』。

---

## 1. 协议层次总览

MCP 不是一个虚构的『黑盒』，它有清晰的层次：

```
┌─────────────────────────────────────────────┐
│  原语层   Tools / Resources / Prompts / Roots│   ← 业务能力
├─────────────────────────────────────────────┤
│  生命周期  initialize → initialized → 操作     │   ← 会话流程
├─────────────────────────────────────────────┤
│  消息层   JSON-RPC 2.0（request/response/    │   ← 通信会话
│            notification）                     │
├─────────────────────────────────────────────┤
│  传输层   stdio ｜ Streamable HTTP            │   ← 落地管道
└─────────────────────────────────────────────┘
```

- **消息层** 定义了『说什么』的格式
- **生命周期** 定义了『按什么顺序说』
- **传输层** 定义了『用什么管道说』

---

## 2. 基于 JSON-RPC 2.0

MCP 的消息正文采用 **JSON-RPC 2.0** 规范。三种消息类型：

### Request（请求）

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

- `id` 用于关联响应
- 必须有 `method` 和 `params`

### Response（响应）

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { "tools": [ ... ] }
}
```

- 用 `id` 对应请求
- 成功返回 `result`（含 `result` 或 `error` 二选一）

### Notification（通知）

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

- **没有 `id`**，也不需要响应，单向告知

> 记忆：**有 id = 需要应答（request/response）；无 id = 单向通知（notification）**。

---

## 3. 会话生命周期

一次 MCP 会话严格走以下阶段：

```
 Client                          Server
   │  ── initialize(request) ─────▶│
   │  ◀── initialize(result) ──────│    协商版本、capabilities、client/server 信息
   │  ── notifications/initialized▶│    告知『我准备好了』
   │  ── tools/list ──────────────▶│    能力发现（可多次、按需）
   │  ── tools/call ──────────────▶│    实际调工具 / 读资源 / 取提示
   │  ◀── 返回结果 ────────────────│
   │  ...  持续交互 ...            │
   │  ── 关闭连接 ────────────────▶│    会话结束
```

关键点：
- **`initialize` 只能是第一条消息**，也是唯一带真正意义的『握手』
- **`notifications/initialized`** 表示 Client 已就绪
- `initialize` 中会带 `capabilities`，双方协商能做什么（工具/资源/提示词等）
- SDK（如 FastMCP）会自动帮你处理握手，你只需关心业务原语

---

## 4. 两种传输方式

### stdio（标准输入/输出）

- **本地**：Host 以子进程方式启动 Server，通过 stdin/stdout 交换消息
- 零网络依赖，适合本地开发、桌面客户端
- 消息按行分隔（每行一个 JSON 消息）

```
Client 进程 ──stdin──▶ Server 进程
Client 进程 ◀──stdout─ Server 进程
```

### Streamable HTTP（可流式 HTTP）

- **远程**：基于 HTTP，支持 Server-Sent Events（SSE）流式返回
- Client 用 HTTP POST 发请求，Server 可流式下发结果
- 适合把 Server 部署到服务器，多个客户端远程接入
- 结合 OAuth 做认证（Day09 详讲）

| 维度 | stdio | Streamable HTTP |
|------|-------|-----------------|
| 场景 | 本地子进程 | 远程/多客户端 |
| 协议 | stdin/stdout | HTTP + SSE |
| 认证 | 不需要 | 常需 OAuth 等 |
| 部署 | 随宿主进程 | 独立服务 |

---

## 5. 本节小结

- MCP 消息基于 **JSON-RPC 2.0**：request（需应答）/ response / notification（单向）
- **生命周期**：`initialize`（首个握手）→ `notifications/initialized`（就绪）→ 能力发现与操作 → 结束
- **传输**：`stdio`（本地）与 `Streamable HTTP`（远程 + SSE）
- SDK 自动处理握手，开发者聚焦原语与业务即可

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_architecture.py` | 协议层次、生命周期详解 |
| `02_jsonrpc.py` | 三种 JSON-RPC 消息的分类与识别 |
| `03_transport.py` | stdio vs HTTP 传输对比 |
| `README.md` | 本目录说明 |

所有脚本**离线可运行**。