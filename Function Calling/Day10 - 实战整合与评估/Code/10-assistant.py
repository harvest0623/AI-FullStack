"""
Day10 实战整合 + 评估
====================
把全部能力拼成一个"多功能小助手" ToolAssistant:
  工具: 天气、算数、搜书、笑话、税率计算
  能力: schema 定义 / 多工具选择 / 校验 / 错误重试 / 并行 / Agent 封装

演示几个综合场景并断言; 最后打印本模块能力评估自检清单。

运行:
  python "Day10 - 实战整合与评估/Code/10-assistant.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec, tool_get_weather,
    tool_search_book,
)


# ---------- 业务函数 ----------
def tool_add(a: float, b: float) -> float:
    return a + b


def tool_joke() -> str:
    return "程序员为什么分不清万圣节与圣诞节? 因为 Oct 31 == Dec 25。"


def tool_tax(price: float, rate: float = 0.13) -> float:
    return price * (1 + rate)


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def make_reg() -> FunctionRegistry:
    reg = FunctionRegistry()
    reg.add(FunctionSpec("get_weather", "查天气",
                         {"properties": {"city": {"type": "string"}},
                          "required": ["city"]}, tool_get_weather))
    reg.add(FunctionSpec("add", "两个数相加",
                         {"properties": {"a": {"type": "number"},
                                         "b": {"type": "number"}},
                          "required": ["a", "b"]}, tool_add))
    reg.add(FunctionSpec("search_book", "检索书库",
                         {"properties": {"keyword": {"type": "string"}},
                          "required": ["keyword"]}, tool_search_book))
    reg.add(FunctionSpec("joke", "讲个笑话",
                         {"properties": {}}, tool_joke))
    reg.add(FunctionSpec("tax", "计算含税价",
                         {"properties": {"price": {"type": "number"},
                                         "rate": {"type": "number"}},
                          "required": ["price"]}, tool_tax))
    return reg


def make_decider():
    """统一决策器: 多工具选择 + 校验失败重试 + 有结果就总结。"""
    def decide(messages, tools):
        question = next((m["content"] for m in messages if m["role"] == "user"), "")
        done = [m["name"] for m in messages if m["role"] == "tool"]
        last_err = next((m["content"] for m in reversed(messages)
                         if m["role"] == "tool" and m["content"].startswith("[error]")), "")

        if last_err and "tax" in last_err:
            # 税率计算参数错 -> 用默认 0.13 重试
            return ("call", [{"name": "tax", "args": {"price": 100}}])
        if "天气" in question and "get_weather" not in done:
            city = next((c for c in ("上海", "北京", "广州", "深圳") if c in question), "上海")
            return ("call", [{"name": "get_weather", "args": {"city": city}}])
        if ("加" in question or "+" in question) and "add" not in done:
            n = [int(x) for x in question.replace("加", " ").replace("+", " ").split() if x.isdigit()]
            if len(n) >= 2:
                return ("call", [{"name": "add", "args": {"a": n[0], "b": n[1]}}])
        if ("税" in question or "含税" in question) and "tax" not in done:
            import re
            m = re.search(r"(\d+)", question)
            if m:
                return ("call", [{"name": "tax", "args": {"price": int(m.group(1))}}])
        if "书" in question and "search_book" not in done:
            kw = "mongo" if "mongo" in question.lower() else "ai"
            return ("call", [{"name": "search_book", "args": {"keyword": kw}}])
        if "笑" in question and "joke" not in done:
            return ("call", [{"name": "joke", "args": {}}])
        # 已有结果 -> 总结
        tool_msgs = [m for m in messages if m["role"] == "tool"]
        if tool_msgs:
            return ("text", f"助手: {tool_msgs[-1]['content']}")
        return ("text", "我在天气/算数/搜书/讲笑话/算税方面可以帮你。")
    return decide


def main() -> None:
    reg = make_reg()
    llm = FunctionCallingLLM(plan=make_decider())
    calls = ["给我讲个笑话",
             "计算 23 加 98",
             "书架上的 mongo 书有哪些",
             "商品价 200 的含税价是多少",
             "深圳天气",
             "同时问: 100 加 20"]
    results = []
    for q in calls:
        ans = llm.chat_with_tools(q, reg)
        results.append(ans)
        print(f"\n[问] {q}\n[答] {ans}")

    # ---------- 断言关键场景 ----------
    assert any("程序员" in r for r in results)                       # 笑话
    assert any("121" in r for r in results)                          # 23+98
    assert any("MongoDB" in r for r in results)                      # 搜书
    # 200*1.13: 浮点误差(落后一位), 允许接近 226
    assert any(abs(float(r.replace("助手:", "").replace(" ", "")) - 226.0) < 1e-6
               for r in results if _is_float(r.replace("助手:", "").replace(" ", "")))
    assert any("深圳" in r for r in results)                         # 天气
    print("\n" + "=" * 60)
    print("实战场景全部断言通过 ✓")

    # ---------- 评估自检 ----------
    print("\n本模块能力评估与自检:")
    checklist = [
        ("Function Calling 范式", "理解 问->调->喂回->答 循环"),
        ("工具定义 schema", "name/description/parameters(JSON Schema)"),
        ("参数解析与执行", "从模型输出解析 args 并调用"),
        ("多工具选择与循环", "按描述分流、连续调用"),
        ("错误处理与重试", "异常->[error]喂回->修正重试"),
        ("参数校验与类型", "必填/类型拦截"),
        ("多轮上下文", "历史结果驱动下一步"),
        ("并行调用", "一次决策发多个 call"),
        ("Agent/工作流封装", "统一 run() 接口"),
        ("实战整合", "拼成多功能小助手"),
    ]
    for name, desc in checklist:
        print(f"   [✓] {name}: {desc}")
    print("\nFunction Calling 模块通关! 🎉")


if __name__ == "__main__":
    main()