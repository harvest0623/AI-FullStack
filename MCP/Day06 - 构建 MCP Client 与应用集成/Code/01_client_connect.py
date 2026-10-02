# -*- coding: utf-8 -*-
"""
Day06 - 01 Client 连接与能力发现（离线模拟）

模拟 ClientSession 的核心流程：握手 → 列工具/资源/提示词 → 调用。
展示『真实写法』并给出等价离线演示。无需 mcp 包。

真实 SDK 写法（需安装 mcp）见 docstring 内的注释。
"""


def real_api():
    print("真实 SDK 的 Client 流程（需安装 mcp）：\n")
    print("""from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python", args=["server_resources.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()          # 列工具
            res   = await session.call_tool("echo", {"text":"hi"})  # 调用
            await session.read_resource("config://app") # 读资源
            await session.get_prompt("review_code", {"code":"x"})   # 取提示词""")
    print()


# ---------- 离线模拟 Server 端返回 ----------
TOOLS = [
    {"name": "echo", "description": "原样返回输入的文字",
     "inputSchema": {"properties": {"text": {"type": "string"}}}},
    {"name": "add", "description": "返回两个整数之和",
     "inputSchema": {"properties": {"a": {"type": "number"}, "b": {"type": "number"}}}},
]
RESOURCES = ["config://app", "docs://mcp", "docs://agent"]
PROMPTS = ["review_code"]


def simulate_capabilities():
    print("Client 能力发现（离线模拟）：\n")
    print("  工具：", ", ".join(t["name"] for t in TOOLS))
    print("  资源：", ", ".join(RESOURCES))
    print("  提示词：", ", ".join(PROMPTS))
    print("\n  调用 echo(text='hello')  → 你说了：hello")
    print("  读取 config://app        → {\"debug\": true, \"model\": \"qwen\"}")
    print("  获取提示词 review_code   → 已生成代码评审模板")


def main():
    print(">> Client 连接与能力发现\n")
    real_api()
    simulate_capabilities()
    print("\n  tips: 握手(initialize)成功后，先做能力发现(list)再做调用(call)。")


if __name__ == "__main__":
    main()