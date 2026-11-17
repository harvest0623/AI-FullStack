# -*- coding: utf-8 -*-
"""
Day07 - 02 流式工具调用的增量拼接

模拟流式返回的多段 chunk，按 index 逐步拼接 name 与 arguments，
流结束后得到完整的 tool_calls 再执行。

离线可运行。
"""

import json

# 模拟流式返回的若干 chunk（OpenAI delta 形态，简化为只取相关字段）
STREAM = [
    {"index": 0, "id": "c1", "type": "function",
     "function": {"name": "get_we"}},
    {"index": 0, "function": {"arguments": '{"cit'}},
    {"index": 0, "function": {"arguments": "y\":\""}},
    {"index": 0, "function": {"arguments": "北京"}},
    {"index": 0, "function": {"arguments": '"}'}},
]


def assemble(stream):
    accs = {}
    for chunk in stream:
        i = chunk["index"]
        acc = accs.setdefault(i, {"id": None, "name": None, "arguments": ""})
        if chunk.get("id"):
            acc["id"] = chunk["id"]
        if chunk.get("function") and chunk["function"].get("name"):
            acc["name"] = chunk["function"]["name"]
        args = (chunk.get("function") or {}).get("arguments", "")
        acc["arguments"] += args or ""
    return accs


def main():
    print(">> 流式工具调用（按 index 增量拼接）\n")
    print("流式到达的 chunk：\n")
    for c in STREAM:
        print(json.dumps(c, ensure_ascii=False))

    print("\n拼接过程（只显示每步的 arguments 累计）：")
    buf = ""
    for c in STREAM:
        args = (c.get("function") or {}).get("arguments", "")
        if args:
            buf += args
            print(f"   arguments 累计 → {buf}")

    final = assemble(STREAM)
    print("\n流结束后的完整 tool_call：\n")
    print(json.dumps(list(final.values()), ensure_ascii=False, indent=2))

    args_obj = json.loads(buf)
    print(f"\n解析 arguments → {args_obj}，可据此执行工具。\n")
    print("  tips: 多个并行工具调用会有多个 index，需分别拼接，互不串扰。")


if __name__ == "__main__":
    main()