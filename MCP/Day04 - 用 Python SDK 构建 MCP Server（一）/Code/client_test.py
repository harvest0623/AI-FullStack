# -*- coding: utf-8 -*-
"""
Day04 - client_test.py  连接测试 client 模板

以子进程方式启动 server_hello.py，完成能力发现并调用工具。

运行（需安装 mcp，且 server_hello.py 同目录）：
    python client_test.py

说明：本文件需要 `mcp` 包。
"""

import asyncio

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("未检测到 mcp SDK，请先运行: pip install mcp")
    raise SystemExit(1)


async def main():
    # 以子进程方式启动 server
    params = StdioServerParameters(command="python", args=["server_hello.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            # 握手初始化
            await session.initialize()

            # 能力发现：列出所有工具
            tools = await session.list_tools()
            print("发现工具:", [t.name for t in tools.tools])

            # 调用工具
            res = await session.call_tool("echo", {"text": "hello mcp"})
            print("echo 结果:", res.content)

            res2 = await session.call_tool("add", {"a": 3, "b": 4})
            print("add 结果:", res2.content)


if __name__ == "__main__":
    asyncio.run(main())