# -*- coding: utf-8 -*-
"""
Day04 - server_hello.py  真实的 MCP Server 模板

一个最小的 FastMCP Server，暴露两个工具，默认 stdio 运行。

运行（需安装 mcp）：
    python server_hello.py
然后另开终端运行 client_test.py 连接测试。

说明：本文件需要 `mcp` 包；若未安装，
请先执行 `pip install mcp`（讲解版见 01_fastmcp_hello.py，可离线运行）。
"""

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("未检测到 mcp SDK，请先运行: pip install mcp")
    print("或运行讲解版：python 01_fastmcp_hello.py（无需安装）")
    raise SystemExit(1)

# 创建 Server
mcp = FastMCP("Hello")


@mcp.tool()
def echo(text: str) -> str:
    """原样返回输入的文字（docstring 会成为工具的 description）。"""
    return f"你说了：{text}"


@mcp.tool()
def add(a: int, b: int) -> int:
    """返回两个整数之和。"""
    return a + b


if __name__ == "__main__":
    mcp.run()