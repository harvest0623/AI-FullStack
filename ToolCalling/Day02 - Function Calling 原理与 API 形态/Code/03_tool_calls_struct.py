# -*- coding: utf-8 -*-
"""
Day02 - 03 tool_calls 结构解析与参数反序列化

重点：arguments 通常是 JSON 字符串，需要安全解析成对象，
并做类型/必填校验后再执行。

离线可运行（讲解 + 演示）。
"""

import json


def parse_arguments(raw: str):
    """把 arguments 字符串安全解析为 dict，失败返回 None。"""
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def demo():
    print("若干 tool_calls 解析演示：\n")
    samples = [
        '{"city": "北京"}',                       # 正常
        '{"city": "上海", "unit": "celsius"}',     # 多参数
        'not a json',                            # 非法
        None,                                     # 空
    ]
    for s in samples:
        parsed = parse_arguments(s)
        print(f"  原始: {s!r}")
        print(f"  解析: {parsed}\n")


def validate(data, required):
    print("执行前的简单校验（必填字段）：\n")
    for field in required:
        ok = bool(data.get(field))
        print(f"  · 字段『{field}』存在: {ok}")
        if not ok:
            print("      → 缺失，应拒绝执行并回传错误提示")


def main():
    print(">> tool_calls 解析与校验\n")
    print("  关键：function.arguments 是『字符串』，必须 json.loads 转成对象\n")
    demo()
    print("-" * 60)
    print("示例：解析 get_weather，校验必填 city\n")
    tool_call = {"name": "get_weather",
                 "arguments": json.dumps({"city": "北京"})}
    args = parse_arguments(tool_call["arguments"])
    print(f"  工具: {tool_call['name']}")
    print(f"  参数对象: {args}")
    validate(args, ["city"])


if __name__ == "__main__":
    main()