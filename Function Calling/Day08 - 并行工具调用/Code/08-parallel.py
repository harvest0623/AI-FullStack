"""
Day08 并行工具调用
=================
模型在*同一次*决策里发出多个独立函数调用(一个 calls 列表), 框架逐个执行,
把多个 tool 结果一起喂回, 模型据此综合回答。它和"多轮串行"不同——
并行是一次发起, 串行是多轮发起。

演示:
  1. 一次同时查三座城市的天气(一个决策发 3 个 call)
  2. 综合结果最终回答

运行:
  python "Day08 - 并行工具调用/Code/08-parallel.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec, tool_get_weather,
)


def make_reg():
    reg = FunctionRegistry()
    reg.add(FunctionSpec("get_weather", "查天气",
                         {"properties": {"city": {"type": "string"}},
                          "required": ["city"]}, tool_get_weather))
    return reg


def main() -> None:
    reg = make_reg()

    # planner: 对"三座城市天气" -> 一次发 3 个并行调用
    def planner(messages, tools):
        tool_msgs = [m for m in messages if m["role"] == "tool"]
        if tool_msgs:
            # 已有全部结果, 综合
            lines = [m["content"] for m in tool_msgs]
            return ("text", "并行拿到: " + " | ".join(lines))
        # 一次返回多个 call = 并行
        calls = [{"name": "get_weather", "args": {"city": c}}
                 for c in ("上海", "北京", "广州")]
        return ("call", calls)

    llm = FunctionCallingLLM(plan=planner)
    print("=" * 60)
    print("用户: '上海、北京、广州天气? [并行]'")
    final = llm.chat_with_tools("上海、北京、广州天气?", reg)

    # 断言: 三个城市都出现在结果里
    print("\n最终回答:", final)
    assert "上海" in final and "北京" in final and "广州" in final
    assert "并行拿到" in final
    print("\n并行调用断言通过 ✓")


if __name__ == "__main__":
    main()