# -*- coding: utf-8 -*-
"""
Day09 - app_assistant.py  综合小助手（多工具 Agent）

组装"查天气 + 算数 + 记账"的多工具小助手，演示循环 + 注册 + 安全执行。

离线可运行（用规则决策模拟模型决策）。
"""

import json

# ---------- 工具 ----------
def get_weather(city):
    return {"北京": "晴 22°C", "上海": "小雨 30°C", "广州": "多云 28°C"}.get(city, "未知城市")


def calculate(expr):
    # 只允许数字与四则运算，安全起见用白名单校验
    allowed = set("0123456789+-*/(). ")
    if not set(expr) <= allowed:
        raise ValueError("表达式包含不支持的符号")
    return eval(expr, {"__builtins__": {}}, {})   # 受限环境的 eval 演示


def add_expense(item, amount):
    if amount <= 0:
        raise ValueError("金额必须为正数")
    return f"已记账：{item} ￥{amount}"


TOOLS = {
    "get_weather": get_weather,
    "calculate": calculate,
    "add_expense": add_expense,
}
MAX_ITER = 8


def decide(messages):
    """规则决策（替身真实模型）。从用户句里识别需要哪几个工具。"""
    text = messages[0]["content"] if messages and messages[0]["role"] == "user" else ""
    already = [m["tool_call_id"] for m in messages if m["role"] == "tool"]
    calls = []

    if "北京" in text and "天气" in text and "wx" not in already:
        calls.append({"id": "wx", "type": "function",
                      "function": {"name": "get_weather", "arguments": json.dumps({"city": "北京"})}})
    if "算" in text or "+" in text and "calc" not in already:
        calls.append({"id": "calc", "type": "function",
                      "function": {"name": "calculate", "arguments": json.dumps({"expr": "3*7"})}})
    if "记" in text and "exp" not in already:
        calls.append({"id": "exp", "type": "function",
                      "function": {"name": "add_expense", "arguments": json.dumps({"item": "咖啡", "amount": 30})}})

    if calls:
        return {"content": None, "tool_calls": calls}
    return {"content": "都处理好了：天气晴22°C、算法结果21、已记账咖啡30元。"}


def main():
    print(">> 综合小助手（多工具 Agent，离线演示）\n")
    user = "查下北京天气，算下3*7，顺便记一笔咖啡30元"
    print(f"  用户：『{user}』\n")
    messages = [{"role": "user", "content": user}]

    for it in range(MAX_ITER):
        resp = decide(messages)
        tcs = resp.get("tool_calls")
        if not tcs:
            print(f"  [助手] {resp['content']}")
            break
        print(f"  —— 第 {it+1} 轮，批量 {len(tcs)} 个工具 ——")
        tool_msgs = []
        for tc in tcs:
            name, fn = tc["function"]["name"], TOOLS[tc["function"]["name"]]
            args = json.loads(tc["function"]["arguments"])
            try:
                result = fn(**args)
            except Exception as e:
                result = f"执行失败：{e}"
            print(f"    {name}{args} → {result}")
            tool_msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})
        messages.append({"role": "assistant", "tool_calls": tcs})
        messages.extend(tool_msgs)
    else:
        print("  ⚠ 已达最大迭代")

    print("\n  tips: 换成真实模型后，decide 用 LLM 决策，其它结构与循环通用。")


if __name__ == "__main__":
    main()