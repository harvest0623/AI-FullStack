# -*- coding: utf-8 -*-
"""
Day06 - 02 把 MCP 接进 LLM（集成演示）

演示关键流程：通过 list_tools 拿到工具清单 → 转成模型认识的 schema →
模型『决策调用哪个工具』→ Client 执行 call_tool → 回填给模型生成回复。

离线可运行（用简单的规则函数代替真实 LLM，体现『闭环』逻辑）。

真实落地时，中间那层『决策』会用真实的 LLM（如调用本地/云端模型），
其余结构与这里一致。
"""

# —— 模拟 MCP Server 提供的工具 ——
TOOLS = {
    "echo": lambda text: f"你说了：{text}",
    "add": lambda a, b: a + b,
}


def list_tools():
    """模拟 list_tools：返回工具清单（含 schema）。"""
    return [
        {"name": "echo", "description": "原样返回文字",
         "inputSchema": {"properties": {"text": {"type": "string"}}}},
        {"name": "add", "description": "返回两个整数之和",
         "inputSchema": {"properties": {"a": {"type": "number"}, "b": {"type": "number"}}}},
    ]


def call_tool(name, args):
    """模拟 call_tool：真实执行工具。"""
    fn = TOOLS[name]
    return fn(**args)


def mock_llm_decide(user_input: str):
    """极简『模型决策』：从用户输入里看出要调哪个工具、给什么参数。"""
    if "相加" in user_input or "加起来" in user_input:
        import re
        nums = [int(x) for x in re.findall(r"\d+", user_input)]
        return ("add", {"a": nums[0], "b": nums[-1]})
    return ("echo", {"text": user_input})


def integration_loop(user_query: str):
    """完整闭环：发现 → 决策 → 调用 → 回填。"""
    print(f"  用户提问：『{user_query}』")
    print(f"  [1] LLM 感知工具清单   → {[t['name'] for t in list_tools()]}")
    name, args = mock_llm_decide(user_query)
    print(f"  [2] 模型决策调用工具    → {name}{args}")
    result = call_tool(name, args)
    print(f"  [3] Client 执行 call_tool → {result}")
    print(f"  [4] 模型基于结果回复      → 「结果是 {result} 」\n")


def main():
    print(">> 把 MCP 接进 LLM\n")
    print("流程：list_tools 找工具 → 模型决策 → call_tool 执行 → 回填生成回复\n")
    integration_loop("帮我算一下 12 和 30 相加")
    integration_loop("随便说句话吧")

    print("\n" + "=" * 60)
    print("真实落地说明：")
    print("  用真实 LLM 时，[1] 会把工具 schema 注入系统提示，")
    print("  模型输出结构化的『工具调用』（name + arguments），")
    print("  [3] 用 Client 的 session.call_tool(name, arguments) 真正执行。")
    print("  你可在任何支持 tool calling 的模型上迁移这套骨架。")


if __name__ == "__main__":
    main()