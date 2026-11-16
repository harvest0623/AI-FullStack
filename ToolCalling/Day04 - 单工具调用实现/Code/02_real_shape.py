# -*- coding: utf-8 -*-
"""
Day04 - 02 OpenAI 风格真实形态（对照）

展示真实 SDK 请求带 tools、返回含 tool_calls 的样子。
本文件不真实发请求，仅给出结构示意与下一步处理方向。

离线可运行（纯示意）。
"""

import json


def openai_shape():
    print("OpenAI 风格请求（简化）：\n")
    request = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "北京天气如何？"}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询指定城市的天气",
                "parameters": {"type": "object",
                               "properties": {"city": {"type": "string"}},
                               "required": ["city"]},
            },
        }],
        "tool_choice": "auto",
    }
    print(json.dumps(request, ensure_ascii=False, indent=2))


def response_shape():
    print("\n返回（含 tool_calls，OpenAI 命名）：\n")
    resp = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_abc123",
                    "type": "function",
                    "function": {"name": "get_weather",
                                 "arguments": json.dumps({"city": "北京"})},
                }],
            }
        }]
    }
    print(json.dumps(resp, ensure_ascii=False, indent=2))


def how_to_handle():
    print("\n拿到返回后，应用侧处理（与 Day04-01 完全相同）：\n")
    print("  1. 取 resp['choices'][0]['message']['tool_calls']")
    print("  2. 对每个 call：name → 找函数；arguments → json.loads 解析")
    print("  3. 执行函数得 result")
    print("  4. 追加一条 {role:'tool', tool_call_id:id, content:result} 再请求模型")


def main():
    print(">> OpenAI 风格真实形态\n")
    openai_shape()
    response_shape()
    how_to_handle()
    print("\n  tips: 形态不同、逻辑一致——应用侧的执行/回填代码可复用。")


if __name__ == "__main__":
    main()