# Day04 - 构建 MCP Server（一）：工具

> 从本日开始真正动手：安装 MCP Python SDK，用 FastMCP 创建一个暴露工具的 Server，并用 Client 连通自测。这是『我的第一个 MCP 能力』。

---

## 1. 环境准备

安装官方 Python SDK：

```bash
pip install mcp
```

> 本日所有讲解脚本**可离线运行**（检测到 SDK 再演示真实写法）。真实 `server_*.py` / `client_*.py` 模板需已安装 SDK。

---

## 2. 认识 FastMCP

官方 Python SDK 提供了 `FastMCP`，它用装饰器把普通 Python 函数暴露为 MCP 能力，**自动处理握手、消息、生命周期**，让你聚焦业务。

看一下最小 Server：

```python
from mcp.server.fastmcp import FastMCP

# 创建 Server，名字会出现在客户端
mcp = FastMCP("Hello")

# 把一个函数暴露成工具
@mcp.tool()
def echo(text: str) -> str:
    """原样返回输入的文字（函数 docstring 会成为工具的 description）"""
    return f"你说了：{text}"

# 在 stdio 模式运行
if __name__ == "__main__":
    mcp.run()
```

### 干了什么？
- `@mcp.tool()` 把 `echo` 注册成一个 **Tools**
- 参数类型 `str`、返回值 `str` 会被自动转成 **JSON Schema**
- `docstring` 自动变成工具的 **description**
- `mcp.run()` 默认走 **stdio** 传输

---

## 3. 工具定义要点

| 关注点 | 说明 |
|--------|------|
| 函数签名 | 参数即工具的 inputSchema，类型标注越清晰越好 |
| 返回值 | 返回 `str` 或任意可序列化对象 |
| docstring | 一定要写清楚『何时用、怎么用』 |
| 装饰器 | `@mcp.tool()` 支持传 `name` 覆盖工具名 |

---

## 4. 用 Client 自测

写一个简单 Client 连接这个 Server，列出工具并调用：

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python", args=["server_hello.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("发现工具:", [t.name for t in tools.tools])
            res = await session.call_tool("echo", {"text": "hello"})
            print("调用结果:", res.content)

if __name__ == "__main__":
    asyncio.run(main())
```

要点：
- `stdio_client` 以子进程方式启动 `server_hello.py`
- `ClientSession` 封装握手与消息
- `session.list_tools()` → 能力发现；`session.call_tool()` → 调用

---

## 5. 本节小结

- `pip install mcp`；核心 API 是 **FastMCP**
- `@mcp.tool()` 把函数变成工具；签名 / 返回值 / docstring 自动转成协议定义
- `mcp.run()` 默认 stdio 运行
- Client 用 `list_tools` 发现、`call_tool` 调用

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_fastmcp_hello.py` | 讲解 FastMCP 用法 + 简易流程演示（离线，无需 SDK） |
| `server_hello.py` | 可直接运行的 Server 模板（需 SDK） |
| `client_test.py` | 连接测试的 Client 模板（需 SDK） |
| `README.md` | 本目录说明 |

`01_fastmcp_hello.py` 离线可运行；其余需安装 `mcp`。