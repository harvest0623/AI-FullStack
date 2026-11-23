"""
Day05 错误处理与重试
===================
真实世界: 函数会抛错(网络失败/参数不对/未知函数)。关键设计是——
  出错后不是崩掉, 而是把错误作为 tool 结果喂回模型, 让模型"重试/纠错/妥协"。

演示:
  1. 函数内部抛异常 -> 框架捕获并转为 [error] 消息
  2. 模型(planner)读到错误 -> 修正参数重试
  3. 调未知函数 -> 反馈错误
  4. 连续重试仍失败 -> 最终友好回答

运行:
  python "Day05 - 错误处理与重试/Code/05-errors.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec,
)


def risky_divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b


def make_reg():
    reg = FunctionRegistry()
    reg.add(FunctionSpec("divide", "a 除以 b",
                         {"properties": {"a": {"type": "number"},
                                         "b": {"type": "number"}},
                          "required": ["a", "b"]}, risky_divide))
    return reg


def main() -> None:
    reg = make_reg()

    # ---------- 0. 直接用 execute 抛错 ----------
    print("0) execute 遇到函数异常:")
    from framework_function_calling import FunctionCallError
    try:
        reg.execute("divide", {"a": 1, "b": 0})
    except FunctionCallError as e:
        print(f"   -> 捕获 FunctionCallError: {e}")

    # ---------- 1. 模型读到错误后重试 ----------
    # 策略: 第一次传 b=0(会报"除数不能为0"), 模型读到 [error] 后改用 b=2 重试
    def planner2(messages, tools):
        # 只看最近一条工具结果(错误的 vs 成功的)
        tool_msgs = [m for m in messages if m["role"] == "tool"]
        if tool_msgs:
            last = tool_msgs[-1]
            if last["content"].startswith("[error]"):
                # 上一步因 b=0 报错 -> 改成 b=2 重试
                return ("call", [{"name": "divide", "args": {"a": 10, "b": 2}}])
            return ("text", f"最终: {last['content']}")
        return ("call", [{"name": "divide", "args": {"a": 10, "b": 0}}])

    llm = FunctionCallingLLM(plan=planner2)
    print("\n1) 读到错误 -> 修正参数重试:")
    ans = llm.chat_with_tools("10 除以 0", reg)
    print("  答:", ans)
    assert "5.0" in ans

    # ---------- 2. 调未知函数 -> 驳回 ----------
    def planner_unknown(messages, tools):
        if any(m["role"] == "tool" for m in messages):
            for m in messages:
                if m["role"] == "tool":
                    return ("text", f"该工具不可用: {m['content']}")
        return ("call", [{"name": "hack_something", "args": {}}])

    llm2 = FunctionCallingLLM(plan=planner_unknown)
    print("\n2) 模型请求未知函数:")
    ans2 = llm2.chat_with_tools("帮我黑一下", make_reg())
    print("  答:", ans2)
    assert "未知函数" in ans2

    print("\n错误处理与重试断言通过 ✓")


if __name__ == "__main__":
    main()