# -*- coding: utf-8 -*-
"""
Day08 - 01 LangChain bind_tools 思路

说明 LangChain 如何把函数转成工具并调度，理解其与 Day04-06 本质一致。

离线可运行（纯讲解，不依赖真实 langchain）。
"""


def concept():
    print("LangChain 的工具调用桥接：\n")
    print("""  伪代码（示意）:
  model = SomeChatModel(...)
  tools = [get_weather, get_time]     # 直接给 Python 函数
  model_with_tools = model.bind_tools(tools)

  resp = model_with_tools.invoke("北京天气")
  # resp.tool_calls → [{'name':'get_weather','args':{'city':'北京'}}]
  """)
    print("""
  key:
    · bind_tools 读函数签名/docstring 生成工具 schema（= Day03 思路）
    · 返回 resp.tool_calls（= Day02 tool_calls）
    · ToolNode / ToolMessage 把执行结果包成 role=tool 回填（= Day04/07）""")

    print("\n  结论：框架只是把 Day04-06 的『循环 + 规范』封装成 API。"
          "理解本质后可无缝迁移。")


def mapping():
    print("\n映射到本模块：\n")
    rows = [
        ("bind_tools / @tool", "Day03 工具定义 + JSON Schema"),
        ("model.invoke 触发", "Day04 模型决策 + tool_calls"),
        ("ToolNode 执行", "Day05 执行 + 并行"),
        ("ForAgentNode / 循环", "Day06 工具调用循环"),
        ("ToolMessage", "Day07 结果注入"),
    ]
    for lc, ours in rows:
        print(f"  · {lc:<22}←  {ours}")


def main():
    print(">> LangChain 结合\n")
    concept()
    mapping()
    print("\n  tips: 先吃透 04-06 的本体，再用 LangChain 只是『少写样板』。")


if __name__ == "__main__":
    main()