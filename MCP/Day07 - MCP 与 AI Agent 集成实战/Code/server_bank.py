# -*- coding: utf-8 -*-
"""
Day07 - server_bank.py  业务 Server 模板（银行能力）

一个"业务" MCP Server，暴露查询余额 / 转账等工具，
可被 Agent 或 Client 发现并调用。

运行（需安装 mcp）：
    python server_bank.py

未安装 mcp 时，本文件会提示安装；此时可阅读批注理解 Server 结构，
或运行 01_agent_loop.py 查看 Agent 如何消费它。
"""

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("未检测到 mcp SDK，请先运行: pip install mcp")
    print("或先看讲解版 01_agent_loop.py（无需安装）")
    raise SystemExit(1)

mcp = FastMCP("Bank")

# 离线演示用的"内存账本"
_book = {"10001": 1000.0, "10002": 2500.0}


@mcp.tool()
def get_balance(account: str) -> str:
    """查询指定账户的余额。"""
    bal = _book.get(account, 0.0)
    return f"账户 {account} 余额为 {bal:.2f}"


@mcp.tool()
def transfer(acc_to: str, amount: float) -> str:
    """向指定账户转账金额（演示用，不真实扣款）。"""
    if amount <= 0:
        raise ValueError("转账金额必须为正数")
    return f"已完成向账户 {acc_to} 转账 {amount:.2f}"


if __name__ == "__main__":
    mcp.run()