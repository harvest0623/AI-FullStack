"""
Day04 多工具选择与循环
=====================
场景: 模型注册了多个工具, 一次请求里"根据描述选对工具, 连续调不同的函数",
      形成一段多步流水线(哪怕没有并行, 也按顺序一次次来)。

演示:
  - 注册 4 个工具: get_weather / add / search_book / convert_c2f
  - planner 依据用户意图分别选择合适工具
  - 展示"连续调用"在两次请求里分别命中不同工具

运行:
  python "Day04 - 多工具选择与循环/Code/04-multi.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec, tool_add,
    tool_get_weather, tool_search_book,
)


def convert_c2f(c: float) -> float:
    return c * 9 / 5 + 32


def make_reg():
    reg = FunctionRegistry()
    reg.add(FunctionSpec("get_weather", "查天气",
                         {"properties": {"city": {"type": "string"}},
                          "required": ["city"]}, tool_get_weather))
    reg.add(FunctionSpec("add", "两个数相加",
                         {"properties": {"a": {"type": "number"},
                                         "b": {"type": "number"}},
                          "required": ["a", "b"]}, tool_add))
    reg.add(FunctionSpec("search_book", "检索书库里的书",
                         {"properties": {"keyword": {"type": "string"}},
                          "required": ["keyword"]}, tool_search_book))
    reg.add(FunctionSpec("convert_c2f", "摄氏转华氏",
                         {"properties": {"c": {"type": "number"}},
                          "required": ["c"]}, convert_c2f))
    return reg


def planner(messages, tools):
    # 已有工具结果: 直接汇报
    if any(m["role"] == "tool" for m in messages):
        for m in messages:
            if m["role"] == "tool":
                return ("text", f"结果: {m['content']}")
    text = messages[-1]["content"]
    # 多工具分流
    if "天气" in text:
        city = next((c for c in ("上海", "北京", "广州", "深圳") if c in text), "上海")
        return ("call", [{"name": "get_weather", "args": {"city": city}}])
    if any(w in text for w in ("书", "收藏", "检索")):
        kw = "mongo" if "mongo" in text.lower() else "ai"
        return ("call", [{"name": "search_book", "args": {"keyword": kw}}])
    if "华氏" in text and ("度" in text):
        import re
        m = re.search(r"(\d+)", text)
        c = float(m.group(1))
        return ("call", [{"name": "convert_c2f", "args": {"c": c}}])
    if "和" in text or "+" in text:
        nums = [int(x) for x in text.replace("和", " ").replace("+", " ").split() if x.isdigit()]
        if len(nums) >= 2:
            return ("call", [{"name": "add", "args": {"a": nums[0], "b": nums[1]}}])
    return ("text", "我可以查天气、加数、搜书、转温度。你想用哪个?")


def main() -> None:
    reg = make_reg()
    llm = FunctionCallingLLM(plan=planner)
    print("可用工具:", reg.names())

    cases = [
        "查询书架上的 mongo 书籍",
        "计算 20 和 7",
        "25 摄氏度等于多少华氏度",
        "上海天气",
    ]
    for q in cases:
        print("\n" + "=" * 60)
        print("问:", q)
        print("答:", llm.chat_with_tools(q, reg))

    # ---------- 验证: 工具选择正确 ----------
    # 用 generate_call 单次决策校验"选中哪个工具"
    llm2 = FunctionCallingLLM(plan=planner)
    assert llm2.generate_call("计算 20 和 7", reg)[1][0]["name"] == "add"
    assert llm2.generate_call("上海天气", reg)[1][0]["name"] == "get_weather"
    assert llm2.generate_call("书架上的 mongo 书", reg)[1][0]["name"] == "search_book"
    assert llm2.generate_call("25 度转华氏", reg)[1][0]["name"] == "convert_c2f"
    print("\n多工具选择断言通过 ✓")


if __name__ == "__main__":
    main()