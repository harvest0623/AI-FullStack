"""
Day05 练习二：原生 tool_calls 循环
====================================
用 llm.chat(messages, tools=...) 走原生工具调用循环:
  - 模型返回结构化的 tool_calls(name + arguments)
  - 执行后用 role="tool" 回填, 再继续, 直到模型不再要工具
本脚本用 MockLLM 模拟 "原生 tool_calls", 有真实 KEY 时可切真实模型。

运行:
  python "Day05 - Action 执行与工具调用/Code/02-native-toolcalls.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import auto_llm, tool_call, text     # noqa: E402
from tools import tool, ToolRegistry          # noqa: E402


# ---------- 工具 ----------
@tool
def multiply(a: float, b: float) -> str:
    """两数相乘"""
    return str(a * b)


@tool
def square(x: float) -> str:
    """求平方"""
    return str(x ** 2)


# ---------- 模拟"原生 tool_calls"的 decider ----------
def native_decider(messages, tools=None):
    """返回统一格式 {content, tool_calls}, 模拟模型原生决策。"""
    obs = [m["content"] for m in messages if m.get("role") == "tool"]
    if not obs:
        return tool_call("multiply", {"a": 3, "b": 4})
    if obs[-1] in ("12", "12.0"):
        return tool_call("square", {"x": 12})
    if obs[-1] in ("144", "144.0"):
        return text("(3*4)^2 = 144")
    return text("我不知道怎么继续")


def main() -> None:
    reg = ToolRegistry([multiply, square])   # 已是 @tool 装饰的 Tool

    # 无 KEY 走 Mock, 有 KEY 走真实模型
    try:
        llm = auto_llm(mock_decider=native_decider)
    except RuntimeError as e:  # 未装 openai 时兜底用 mock
        from llm import MockLLM
        llm = MockLLM(native_decider)

    messages = [{"role": "user", "content": "计算 (3*4) 的平方。"}]
    print("原生 tool_calls 循环:\n")

    for step in range(6):
        resp = llm.chat(messages, tools=reg.openai_tools())
        # 1) 先追加 assistant 的回复(含 tool_calls)
        messages.append({"role": "assistant",
                         "content": resp.get("content") or "",
                         "tool_calls": resp["tool_calls"]})
        print(f"── 第 {step+1} 轮 ──")
        print("  模型:", resp.get("content") or "(要调用工具)")

        for tc in resp["tool_calls"]:
            result = reg.execute(tc["name"], **tc["arguments"])
            print(f"  调用 {tc['name']}({tc['arguments']}) -> {result}")
            messages.append({"role": "tool", "content": str(result)})

        if not resp["tool_calls"]:
            print("\n✅ 无更多工具调用, 模型输出:", resp.get("content"))
            return

    print("\n⚠️ 达到最大轮次未完成")


if __name__ == "__main__":
    main()