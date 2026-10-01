# -*- coding: utf-8 -*-
"""
Day01 - 03 MCP vs 其他方案

横向对比普通 API、Function Calling、Agent 与 MCP，
理解『MCP 是 Agent 的外部能力接入层』这一关键定位。

离线可运行（纯讲解）。
"""


def compare_table():
    print("四方案横向对比：\n")
    rows = [
        ("普通 API", "直接叫/程序调", "无统一标准；模型也不知道何时调；每个服务一套接口"),
        ("Function Calling", "单个 LLM", "模型『知道要调某工具』；但工具定义与特定模型绑定，难复用"),
        ("Agent", "应用架构", "让模型自主规划+调工具；但工具『怎么接入』仍是各自为政"),
        ("MCP", "整个 AI 生态", "标准化工具/资源接入层；Server 与 Host 解耦，可复用、可移植"),
    ]
    for name, audience, feature in rows:
        print(f"  ■ {name:<18} 面向：{audience}")
        print(f"       {feature}\n")


def mcp_vs_function():
    print("MCP 与 Function Calling 的关系：\n")
    print("  它们不是二选一，而是『不同层次』：")
    print("    Function Calling：是『模型侧』决定调用哪个函数的能力")
    print("    MCP           ：是『应用侧』如何发现并调用外部工具的协议")
    print("  常见组合：Host 用 MCP 拿到工具清单 → 转成模型认识的 tool schema")
    print("            → 模型决策调用 → 通过 MCP 真正执行\n")


def mcp_vs_agent():
    print("MCP 与 Agent 的关系：\n")
    print("   Agent = 规划 + 记忆 + 工具使用")
    print("   MCP   = 其中『工具使用』的标准化接入层")
    print("  结论：MCP 让 Agent 的外部能力接入更规范、更可复用，但 Agent 本身")
    print("         的规划/记忆逻辑仍由你自己实现。二者互补，不冲突。")


def main():
    print(">> MCP vs 其他方案\n")
    compare_table()
    mcp_vs_function()
    mcp_vs_agent()
    print("\n  tips: 市面上 Agent 框架（如 LangChain）也都在拥抱 MCP 标准。")


if __name__ == "__main__":
    main()