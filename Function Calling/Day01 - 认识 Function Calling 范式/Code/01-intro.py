"""
Day01 认识 Function Calling 范式
================================
用模拟框架演示最核心的思想: 模型不只是"说话", 还会"请求调用你给的函数"。

演示:
  1. 给模型提供一个 get_weather 工具
  2. 用规则式 planner 模拟"模型判断该调用天气函数"
  3. 触发 tool_calls -> 执行函数 -> 把结果喂回 -> 模型结合结果回答

观察 assistant/tool 两种消息如何流转(与真实 OpenAI tool_calls 一致)。

运行:
  python "Day01 - 认识 Function Calling 范式/Code/01-intro.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec, tool_get_weather,
)


def main() -> None:
    # ---------- 1. 给模型"装备"一个工具 ----------
    registry = FunctionRegistry()
    registry.add(FunctionSpec(
        name="get_weather",
        description="查询某个城市的天气",
        parameters={"type": "object",
                    "properties": {"city": {"type": "string"},
                                   "unit": {"type": "string"}},
                    "required": ["city"]},
        func=tool_get_weather,
    ))
    print("注册的工具:", registry.names())
    for t in registry.explain_tools():
        print("模型看到的 tools 定义:", t["function"]["name"])

    # ---------- 2. 自定义一个"假模型决策器" ----------
    # plan(对话历史, 可用工具) -> ("text", 直接回答) 或 ("call", [调用列表])
    def planner(messages, tools):
        # 模拟模型: 当用户提到天气且刚问城市, 就去调用 get_weather
        if any(t["role"] == "tool" for t in messages):
            # 已有工具结果, 模型据此给出最终回答
            for m in messages:
                if m["role"] == "tool":
                    return ("text", f"(模型据结果) {m['content']}")
        if "上海" in messages[-1]["content"]:
            return ("call", [{"name": "get_weather", "args": {"city": "上海"}}])
        return ("text", "我不知道天气, 但可以帮你查。")

    llm = FunctionCallingLLM(plan=planner)

    # ---------- 3. 跑一次完整对话循环 ----------
    print("\n" + "=" * 60)
    print("用户: '上海今天天气怎么样?'")
    answer = llm.chat_with_tools("上海今天天气怎么样?", registry)
    print("最终回答:", answer)

    # ---------- 4. 看原始一次决策(模型输出) ----------
    print("\n" + "=" * 60)
    print("观察: 框架内部模型先输出 tool_calls(不是文字), 执行后再转文字。")
    decision = llm.generate_call("上海今天天气怎么样?", registry)
    print("模型的一次决策是:", decision)
    assert decision[0] == "call"

    # ---------- 5. 总结范式 ----------
    print("\n" + "=" * 60)
    print("Function Calling 范式核心循环:")
    print("  用户问 -> 模型判定需调用函数 -> 返回结构化调用指令")
    print("        -> 程序执行函数 -> 结果作为 tool 消息喂回")
    print("        -> 模型基于结果生成最终回答")
    print("范式理解断言通过 ✓")


if __name__ == "__main__":
    main()