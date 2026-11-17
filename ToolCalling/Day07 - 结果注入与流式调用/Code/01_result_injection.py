# -*- coding: utf-8 -*-
"""
Day07 - 01 结果注入

展示工具结果如何以 role=tool + tool_call_id 回填给模型。

离线可运行（纯演示）。
"""

import json


def build_tool_message(tool_call_id, content):
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}


def main():
    print(">> 结果注入\n")
    # 一次工具调用产生的回填
    msg = build_tool_message("call_abc123", "北京 晴 22°C")
    print("回填消息形态：\n")
    print(json.dumps(msg, ensure_ascii=False, indent=2))

    print("\n要点：")
    print("  · role 必须是 'tool'")
    print("  · tool_call_id 必须对应原 assistant 消息里的 id")
    print("  · content 通常为字符串；多结果可一次性塞（会渲染为内容列表）")

    print("\n一条消息同时带多个工具结果（常见做法：每个结果一条 tool 消息）：")
    multi = [
        build_tool_message("c1", "北京 22°C"),
        build_tool_message("c2", "上海 30°C"),
    ]
    print(json.dumps(multi, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()