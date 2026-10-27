# -*- coding: utf-8 -*-
"""
Day08 - 02 Function Calling 往返

完整演示一次工具调用的"往返"：
1. 把工具 Schema 随 messages 发给 /api/chat
2. 模型返回 tool_calls（说"我要调用 get_weather(city=北京)"）
3. 我方真正执行工具，得到结果（25℃）
4. 把结果作为 tool 消息拼回历史
5. 再让模型基于结果给出最终答复

双模式：有支持 tools 的模型 -> 真实往返；无 -> 按规则模拟模型意图。
"""

import json
from ollama_util import (
    is_ollama_available, real_chat_with_tools, WEATHER_TOOL,
)

MODEL = "qwen2.5"


def get_weather(city: str) -> str:
    """真实执行层——模拟查天气（离线写死，教学用）"""
    data = {"北京": "晴, 25℃", "上海": "小雨, 22℃", "广州": "多云, 28℃"}
    return data.get(city, f"{city}: 暂无数据")


def execute(tool_calls) -> list[dict]:
    """执行工具，返回 tool 结果消息"""
    results = []
    for call in tool_calls:
        fn = call["function"]
        name = fn["name"]
        args = json.loads(fn.get("arguments") or "{}")
        print(f"  [执行] {name}({args})")
        out = get_weather(args.get("city", ""))
        print(f"  [结果] {out}")
        results.append({
            "role": "tool",
            "content": out,
        })
    return results


def main():
    print(">> Function Calling 往返\n")
    messages = [
        {"role": "user", "content": "北京今天天气怎么样？"},
    ]
    tools = [WEATHER_TOOL]

    if is_ollama_available(MODEL):
        print("[真实模式]\n")
        resp = real_chat_with_tools(MODEL, messages, tools)
        msg = resp.get("message", {})
        print(f"模型原始回复：msg={json.dumps(msg, ensure_ascii=False)}")
        tool_calls = msg.get("tool_calls", [])
        if tool_calls:
            messages.append(msg)
            messages.extend(execute(tool_calls))
            final = real_chat_with_tools(MODEL, messages, tools)
            print(f"\n最终答复：{final.get('message', {}).get('content','')}")
        else:
            print(f"模型直接回答：{msg.get('content')}")
        return

    # ---- 模拟模式 ----
    print("[模拟模式：规则模拟模型想要调工具]")
    print("  用户：北京今天天气怎么样？")
    print("  → 模型判定需要调用 get_weather(city=北京)")
    simulated = {"role": "assistant",
                 "content": "",
                 "tool_calls": [{"function": {
                     "name": "get_weather",
                     "arguments": json.dumps({"city": "北京"})}}]}
    messages.append(simulated)
    messages.extend(execute(simulated["tool_calls"]))
    print("\n  把工具结果回传给模型 → 模型基于结果给最终答复：")
    print("  → 北京今天晴，气温 25℃，适合出行。")
    print("\n  tips: 安装 qwen2.5 后自动切真实往返")


if __name__ == "__main__":
    main()