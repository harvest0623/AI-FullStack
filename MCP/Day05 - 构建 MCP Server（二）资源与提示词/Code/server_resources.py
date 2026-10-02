# -*- coding: utf-8 -*-
"""
Day05 - server_resources.py  真实 Server：资源 + 提示词 + 工具

一个同时提供资源（静态 + 动态 URI）、提示词与一个示例工具的 FastMCP Server。

运行（需安装 mcp）：
    python server_resources.py

可用官方调试器查看（需 uv + mcp）：
    uv run mcp dev server_resources.py
"""

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("未检测到 mcp SDK，请先运行: pip install mcp")
    raise SystemExit(1)

mcp = FastMCP("Docs")


# ---------- 资源 ----------
@mcp.resource("config://app")
def get_config() -> str:
    """返回应用配置（JSON 字符串）。"""
    return '{"debug": true, "model": "qwen"}'


@mcp.resource("docs://{topic}")
def get_doc(topic: str) -> str:
    """按主题返回文档（动态 URI：docs://{topic}）。"""
    topics = {
        "mcp": "MCP（Model Context Protocol）是连接 AI 与外部工具的开放协议。",
        "agent": "Agent 是能自主规划并调用工具完成目标的智能体。",
        "rag": "RAG 通过检索外部知识增强模型生成。",
    }
    return topics.get(topic, "未找到该主题文档")


# ---------- 提示词 ----------
@mcp.prompt()
def review_code(code: str) -> str:
    """生成一段代码评审提示。"""
    return f"请评审以下代码，指出 bug 与改进点：\n```\n{code}\n```"


# ---------- 一个示例工具，用于演示错误处理 ----------
@mcp.tool()
def divide(a: float, b: float) -> float:
    """返回 a/b；除数不能为 0。"""
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b


if __name__ == "__main__":
    mcp.run()