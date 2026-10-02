# Day06 - 构建 MCP Client 与应用集成

> 站到链路另一端：用 Client 连接 Server、发现能力并调用；再把它接进含 LLM 的更上层应用，让模型『看得见并用得上』MCP 能力。

---

## 1. Client 连接与能力发现

Client 的核心职责：**连上 Server → 发现能力 → 按需调用**。

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python", args=["server_resources.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()   # 握手

            # 能力发现
            tools = await session.list_tools()          # 工具
            resources = await session.list_resources()   # 资源
            prompts = await session.list_prompts()       # 提示词
            ...
```

### 常用 ClientSession API

| 方法 | 作用 |
|------|------|
| `initialize()` | 握手，建立会话 |
| `list_tools()` / `call_tool(name, args)` | 列工具 / 调工具 |
| `list_resources()` / `read_resource(uri)` | 列资源 / 读资源 |
| `list_prompts()` / `get_prompt(name, args)` | 列提示词 / 取提示词 |
| `read_resource` 返回 `contents` | 读取结果 |

---

## 2. 把 MCP 接进 LLM

单纯调工具意义有限；真正的价值是**让模型根据用户指令自动选择并调用 MCP 工具**。核心思路：

1. 用 `list_tools()` 拿到工具的 `inputSchema`
2. 把它转成模型认识的 **tool schema**（很多 SDK 有现成转换）
3. 模型在对话里返回「要调哪个工具 + 参数」
4. Client 用 `call_tool()` 真实执行
5. 结果回填给模型，模型生成最终回复

```
用户提问 ─▶ LLM 感知工具清单 ─▶ 模型决定调 echo/add
          ◀── tools/call 结果 ── Client 执行 MCP 工具
```

> 这一步把 Day04-05 的 Server 能力，真正变成了 Agent 的「手」。

---

## 3. 分层架构

```
┌────────────────────────────────────────────┐
│ 应用层：用户交互 + 业务逻辑                  │
│ ┌────────────┐  ┌───────────────────────┐  │
│ │ LLM        │  │ Client（MCP）         │  │
│ │ 感知工具    │──│ list/call/read        │  │
│ │ 决策调用    │  └──────────┬────────────┘  │
│ └────────────┘             │               │
└────────────────────────────┼───────────────┘
                             ▼
                      MCP Server（外部能力）
```

---

## 4. 本节小结

- Client = 连接 + 发现 + 调用，`ClientSession` 封装一切
- `list_*` 系列 = 能力发现；`call_tool` / `read_resource` / `get_prompt` = 使用
- 接 LLM 的关键：工具清单 → tool schema → 模型决策 → `call_tool` 执行
- Client 是 Host 与 Server 的桥梁，让顶层应用能调度 MCP 能力

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_client_connect.py` | 讲解 + 离线模拟 Client 连接与能力发现 |
| `client_llm.py` | 含 LLM 决策 + MCP 工具调用的集成演示（离线模拟版） |
| `README.md` | 本目录说明 |

二者均**离线可运行**（不依赖真实 SDK / 真实 LLM）。