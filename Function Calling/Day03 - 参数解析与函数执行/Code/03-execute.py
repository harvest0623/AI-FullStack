"""
Day03 参数解析与函数执行
=======================
聚焦循环里的"执行"环节: 模型给出 {name, args} 后,
如何解析出参数、调用真实函数、拿到可读结果。

演示(用 registry.execute 这一核心方法):
  1. 直接用 execute() 执行一个函数, 观察参数如何被接收
  2. 完整 chat 循环里: 模型解析自然语言 -> 提取参数 -> 执行 -> 结果
  3. 展示 add 工具: 模型从文本里提取两个数字调用

运行:
  python "Day03 - 参数解析与函数执行/Code/03-execute.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec, tool_add,
    tool_get_weather,
)


def main() -> None:
    reg = FunctionRegistry()
    reg.add(FunctionSpec("add", "两个数相加",
                         {"properties": {"a": {"type": "number"},
                                         "b": {"type": "number"}},
                          "required": ["a", "b"]}, tool_add))
    reg.add(FunctionSpec("get_weather", "查天气",
                         {"properties": {"city": {"type": "string"}},
                          "required": ["city"]}, tool_get_weather))

    # ---------- 1. 直接用 execute(): 参数 -> 函数 -> 结果 ----------
    print("1) registry.execute 直接执行")
    out = reg.execute("add", {"a": 3, "b": 4})
    print("   execute('add', {a:3, b:4}) =", out)
    assert float(out) == 7

    out = reg.execute("get_weather", {"city": "北京"})
    print("   execute('get_weather', {city:北京}) =", out)
    assert "北京" in out

    # ---------- 2. 自定义 planner: 从文本提取参数 ----------
    def planner(messages, tools):
        if any(m["role"] == "tool" for m in messages):
            for m in messages:
                if m["role"] == "tool":
                    return ("text", f"计算完成: {m['content']}")
        text = messages[-1]["content"]
        # 简单提取 "12 和 5" 这种两个数
        nums = [int(x) for x in text.replace("和", " ").split() if x.isdigit()]
        if "天气" in text:
            city = "北京" if "北京" in text else "上海"
            return ("call", [{"name": "get_weather", "args": {"city": city}}])
        if len(nums) >= 2:
            return ("call", [{"name": "add", "args": {"a": nums[0], "b": nums[1]}}])
        return ("text", "我没找到要加的两个数。")

    llm = FunctionCallingLLM(plan=planner)

    print("\n" + "=" * 60)
    print("2) 从自然语言提取参数执行")
    print("问: '计算 12 和 5'")
    ans = llm.chat_with_tools("计算 12 和 5", reg)
    print("答:", ans)
    assert "17" in ans

    print("\n" + "=" * 60)
    print("问: '北京天气怎么样'")
    ans2 = llm.chat_with_tools("北京天气怎么样", reg)
    print("答:", ans2)
    assert "北京" in ans2

    print("\n参数解析与执行断言通过 ✓")


if __name__ == "__main__":
    main()