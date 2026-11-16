# -*- coding: utf-8 -*-
"""
Day06 - 01 工具调用循环（Agent 雏形）

把"决策→执行→回填"放进循环，直到模型不再调用工具。带最大迭代保护。

离线可运行（模拟模型：第一轮调工具查天气，第二轮根据结果直接作答）。
"""

import json

TOOLS = {
    "get_weather": lambda city: {"北京": "晴 22°C", "上海": "小雨 30°C"}.get(city, "未知"),
}
MAX_ITER = 10


def mock_model(messages, tools):
    """分段模拟模型：先调工具，得到回填后再作答。"""
    if any(m["role"] == "tool" for m in messages):
        # 已有工具回填 → 直接作答
        return {"content": "北京今天晴，22°C，适合出门。"}
    # 首轮 → 发出工具调用
    return {
        "content": None,
        "tool_calls": [{
            "id": "c1", "type": "function",
            "function": {"name": "get_weather", "arguments": json.dumps({"city": "北京"})},
        }],
    }


def execute(tc):
    name = tc["function"]["name"]
    args = json.loads(tc["function"]["arguments"])
    return TOOLS[name](**args)


def run_loop(user_input, tools):
    messages = [{"role": "user", "content": user_input}]
    print(f"  用户：『{user_input}』\n")
    for it in range(MAX_ITER):
        print(f"  —— 第 {it+1} 轮 ——")
        resp = mock_model(messages, tools)
        if not resp.get("tool_calls"):
            print(f"  [模型] 不再调用工具，作答：『{resp['content']}』")
            return resp["content"]

        tool_msgs = []
        for tc in resp["tool_calls"]:
            result = execute(tc)
            print(f"  [执行] {tc['function']['name']} → {result}")
            tool_msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})
        messages.append({"role": "assistant", "tool_calls": resp["tool_calls"]})
        messages.extend(tool_msgs)
    print(f"  ⚠ 已达最大轮数 {MAX_ITER}，强制结束")
    return "已达最大迭代，请人工介入"


def main():
    print(">> 工具调用循环\n")
    run_loop("北京天气怎么样？", list(TOOLS))
    print("\n  tips: 这就是最小 Agent 循环；换真实模型端点即可实跑多步。")


if __name__ == "__main__":
    main()