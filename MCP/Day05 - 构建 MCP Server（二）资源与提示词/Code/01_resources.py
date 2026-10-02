# -*- coding: utf-8 -*-
"""
Day05 - 01 资源与提示词的实现（离线模拟）

用简单函数演示 @resource（含动态 URI）与 @prompt 的用法形态，
并展示如何被 Client 通过 resources/read 与 prompts/get 取到。

离线可运行（无需安装 mcp 包）。
"""


# ---------- 真实代码形态（展示，不实际连接） ----------
def real_code():
    print("真实 FastMCP 代码形态（需 SDK）：\n")
    print('''from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Docs")

# 1) 静态资源
@mcp.resource("config://app")
def get_config() -> str:
    """返回应用配置。"""
    return '{"debug": true}'

# 2) 动态 URI 资源：路径段变成参数
@mcp.resource("docs://{topic}")
def get_doc(topic: str) -> str:
    """按主题返回文档。"""
    topics = {"mcp": "MCP 是..."， "agent": "Agent 是..."}
    return topics.get(topic, "未找到")

# 3) 提示词模板
@mcp.prompt()
def review_code(code: str) -> str:
    """生成代码评审提示。"""
    return f"请评审以下代码：\\n```\\n{code}\\n```"

mcp.run()''')
    print("\n  说明：资源用 URI scheme 命名、返回字符串；动态 URI 用 {param} 占位。")


# ---------- 离线模拟：直接演示 '清单 ===> 读取' 流程 ----------
RESOURCES = {
    "config://app": '{"debug": true, "model": "qwen"}',
    "docs://mcp": "MCP（Model Context Protocol）是连接 AI 与外部工具的协议。",
    "docs://agent": "Agent 是能自主规划并调用工具的智能体。",
}

PROMPTS = {
    "review_code": "请评审以下代码，指出 bug 与改进点：\n```\n{code}\n```",
}


def read_resource(uri: str) -> str:
    """模拟 resources/read：直接查表，若符合 docs://:{topic} 则命中动态资源。"""
    if uri in RESOURCES:
        return RESOURCES[uri]
    if uri.startswith("docs://"):
        return RESOURCES.get(uri, "未找到该主题")
    return "未找到该资源"


def get_prompt(name: str, **kwargs) -> str:
    """模拟 prompts/get：替换模板中的 {param}。"""
    tpl = PROMPTS.get(name, "未知提示词")
    return tpl.format(**kwargs)


def demo():
    print("\n" + "=" * 60)
    print("模拟 Client 视角：")
    print("  read_resource('config://app')  →", read_resource("config://app"))
    print("  read_resource('docs://mcp')    →", read_resource("docs://mcp"))
    print("  read_resource('docs://none')   →", read_resource("docs://none"))
    print("  get_prompt('review_code', code='x=1')")
    print("   →", get_prompt("review_code", code="x=1"))


def main():
    print(">> 资源与提示词的实现\n")
    real_code()
    demo()
    print("\n  tips: 动态 URI 把『一类资源』收敛成一个函数，URI 路径段即参数。")


if __name__ == "__main__":
    main()