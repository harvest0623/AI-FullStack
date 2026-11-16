# -*- coding: utf-8 -*-
"""
Day06 - 03 防死循环（最大迭代数）

演示当模型反复调用工具时，靠最大迭代数强制终止。

离线可运行。
"""

import json


def always_tool(messages, tools):
    """一个"永远想调工具"的坏模型：每次都返回同一个调用。"""
    return {
        "content": None,
        "tool_calls": [{
            "id": "c-loop", "type": "function",
            "function": {"name": "echo", "arguments": json.dumps({"text": "再来一次"})},
        }],
    }


TOOLS = {"echo": lambda text: text}
MAX_ITER = 3


def main():
    print(">> 防死循环\n")
    messages = [{"role": "user", "content": "一直调用工具"}]
    print(f"  模拟一个『每次都调工具』的坏模型，最大迭代数 = {MAX_ITER}\n")

    for it in range(1, MAX_ITER + 1):
        resp = always_tool(messages, TOOLS)
        print(f"  第 {it} 轮 → 模型又返回 tool_calls: {resp['tool_calls'][0]['function']['name']}")
        if it < MAX_ITER:
            # 正常回填，进入下一轮
            messages.append({"role": "tool", "tool_call_id": "c-loop", "content": "echo:再"})
        else:
            break

    print(f"\n  ⚠ 达到最大迭代数 {MAX_ITER}，强制终止（或转人工）。")
    print("\n  tips: 没有 MAX 保护，这种模型会让你的代理无限空转、还烧钱。")


if __name__ == "__main__":
    main()