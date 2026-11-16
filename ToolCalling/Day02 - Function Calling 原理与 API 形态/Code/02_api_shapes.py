# -*- coding: utf-8 -*-
"""
Day02 - 02 主流 API 形态对比

对比 OpenAI / Anthropic 两条主流 tool calling 的返回形状，
理解"思想一致、细节有差"。

离线可运行（纯讲解 + 结构演示）。
"""

import json


def openai_shape():
    print("OpenAI 风格（主线）：\n")
    sample = {
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
    print(json.dumps(sample, ensure_ascii=False, indent=2))
    print("\n  字段：message.tool_calls[]  id / type / function.name / function.arguments(字符串)")


def anthropic_shape():
    print("\nAnthropic 风格：\n")
    sample = {
        "content": [
            {"type": "text", "text": "我来查天气"},
            {"type": "tool_use",
             "id": "toolu_1",
             "name": "get_weather",
             "input": {"city": "北京"}},   # input 已是对象
        ],
        "stop_reason": "tool_use",
    }
    print(json.dumps(sample, ensure_ascii=False, indent=2))
    print("\n  字段：content[] 中的 tool_use block：id / name / input(对象)")


def compare():
    print("\n" + "=" * 60)
    print("对比要点：\n")
    rows = [
        ("入口", "tools", "tools"),
        ("返回位置", "message.tool_calls", "content[] 内 tool_use"),
        ("参数形态", "arguments 为字符串", "input 为对象"),
        ("结构示例", "通用惯例", "多格式支持"),
    ]
    for k, oa, an in rows:
        print(f"  · {k:<8}{oa:<22}{an}")


def main():
    print(">> 主流 API 形态\n")
    openai_shape()
    anthropic_shape()
    compare()
    print("\n  tips: 用哪个厂商就按哪个 SDK 解析；思想完全一致——输入带工具、输出带调用请求。")


if __name__ == "__main__":
    main()