"""
Day06 参数校验与类型
===================
执行函数前先校验, 挡住坏参数, 降低函数抛错概率。
框架 FunctionRegistry._validate 现在会检查:
  - 必填参数缺失
  - 类型不符(string / number / integer / boolean)
演示直接在 execute 层面看各类非法参数如何被拦截, 再跑一个完整对话。

运行:
  python "Day06 - 参数校验与类型/Code/06-validate.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec, FunctionCallError,
    tool_add, tool_get_weather,
)


def main() -> None:
    reg = FunctionRegistry()
    reg.add(FunctionSpec("add", "两个数相加",
                         {"properties": {"a": {"type": "integer"},
                                         "b": {"type": "integer"}},
                          "required": ["a", "b"]}, tool_add))
    reg.add(FunctionSpec("get_weather", "查天气",
                         {"properties": {"city": {"type": "string"}},
                          "required": ["city"]}, tool_get_weather))

    print("=" * 60)
    print("校验样例(在 execute 层被拦截):")
    cases = [
        ("add", {"a": 1}),                                  # 缺 b
        ("add", {"a": "x", "b": 3}),                        # a 非整数
        ("add", {"a": 1.5, "b": 3}),                        # integer 收到小数
        ("get_weather", {"city": 123}),                     # city 非字符串
        ("get_weather", {"city": "上海", "unit": True}),    # 未知类型参数(宽容)
    ]
    # 前四条会抛错; 第五条 unit 非法 -> 由于框架宽容未知/类型? unit type 未定义 -> 保留
    for name, args in cases[:4]:
        try:
            reg.execute(name, args)
            print(f"   {name} {args} -> 未拦截(!)")
        except FunctionCallError as e:
            print(f"   {name} {args} -> 拦截: {e}")

    # ---------- 完整对话: 模型因校验失败而重试 ----------
    print("\n" + "=" * 60)
    print("完整对话: 第一次传 '二十'(非整数) -> 校验失败 -> 重试成功")
    attempts = {"n": 0}
    def planner(messages, tools):
        tool_msgs = [m for m in messages if m["role"] == "tool"]
        if tool_msgs:
            last = tool_msgs[-1]
            if last["content"].startswith("[error]") and attempts["n"] < 1:
                attempts["n"] += 1
                return ("call", [{"name": "add", "args": {"a": 20, "b": 7}}])
            return ("text", f"结果: {last['content']}")
        return ("call", [{"name": "add", "args": {"a": "二十", "b": 7}}])

    llm = FunctionCallingLLM(plan=planner)
    ans = llm.chat_with_tools("二十 加 7", reg)
    print("  答:", ans)
    assert "27" in ans

    print("\n参数校验与类型断言通过 ✓")


if __name__ == "__main__":
    main()