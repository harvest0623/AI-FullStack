# -*- coding: utf-8 -*-
"""
Day08 - 03 多工具调度

注册多个工具（天气/订单/加法），模型根据用户意图挑选对应工具：
- "查天气" → get_weather
- "查订单" → get_order
- "算一下" → add

双模式：有支持 tools 的模型 -> 真实多工具；无 -> 规则模拟挑选意图。
"""

import json
from ollama_util import is_ollama_available, real_chat_with_tools

MODEL = "qwen2.5"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市天气",
            "parameters": {"type": "object",
                           "properties": {"city": {"type": "string", "description": "城市"}},
                           "required": ["city"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "查询订单状态",
            "parameters": {"type": "object",
                           "properties": {"order_id": {"type": "string"}},
                           "required": ["order_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "计算两个数之和",
            "parameters": {"type": "object",
                           "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                           "required": ["a", "b"]},
        },
    },
]

# 工具执行注册表
REGISTRY = {
    "get_weather": lambda **k: f"【假数据】{k['city']} 晴 24℃",
    "get_order": lambda **k: f"【假数据】订单 {k['order_id']} 已发货",
    "add": lambda **k: k["a"] + k["b"],
}


def run_case(user_text: str):
    print(f"\n用户：{user_text}")
    msgs = [{"role": "user", "content": user_text}]

    if is_ollama_available(MODEL):
        resp = real_chat_with_tools(MODEL, msgs, TOOLS)
        msg = resp.get("message", {})
        calls = msg.get("tool_calls", [])
        if calls:
            for c in calls:
                fn = c["function"]
                args = json.loads(fn.get("arguments") or "{}")
                out = REGISTRY[fn["name"]](**args)
                print(f"  [真实选工具] {fn['name']}({args}) → {out}")
                msgs.append(msg)
                msgs.append({"role": "tool", "content": str(out)})
        else:
            print(f"  [直接回答] {msg.get('content')}")
        return

    # 模拟：按关键词规则"假装模型选了工具"
    text = user_text
    if "天气" in text:
        tool, args = ("get_weather", {"city": "北京"})
    elif "订单" in text:
        tool, args = ("get_order", {"order_id": "A100"})
    elif "加" in text or "算" in text:
        tool, args = ("add", {"a": 3, "b": 4})
    else:
        print("  （模拟）模型直接回答：你好，我能帮你什么？")
        return
    out = REGISTRY[tool](**args)
    print(f"  [模拟选定工具] {tool}({args}) → {out}")


def main():
    print(">> 多工具调度\n")
    for q in ["上海天气怎么样？", "帮我查订单 A100", "帮我算 3 加 4 等于几"]:
        run_case(q)
    print("\n→ 模型按意图挑工具；你的代码用一个注册表统一执行。")


if __name__ == "__main__":
    main()