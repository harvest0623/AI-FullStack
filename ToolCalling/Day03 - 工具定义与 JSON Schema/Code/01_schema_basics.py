# -*- coding: utf-8 -*-
"""
Day03 - 01 JSON Schema 基础

展示 tools 的 parameters 常用关键字：type/properties/required/enum/items/description。

离线可运行（纯讲解 + 结构演示）。
"""

import json


def show(tool):
    print(json.dumps(tool, ensure_ascii=False, indent=2))
    print()


def main():
    print(">> JSON Schema 基础\n")

    print("① 简单对象 + 必填：\n")
    show({
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，如 北京"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"],
                             "description": "温度单位"},
                },
                "required": ["city"],
            },
        },
    })

    print("② 数组 + 数字参数：\n")
    show({
        "type": "function",
        "function": {
            "name": "calc_avg",
            "description": "计算一组数字的平均值",
            "parameters": {
                "type": "object",
                "properties": {
                    "nums": {"type": "array", "items": {"type": "number"},
                             "description": "数字列表"},
                },
                "required": ["nums"],
            },
        },
    })

    print("③ 常用关键字速查：")
    for k, v in [
        ("type", "object / string / number / integer / array / boolean"),
        ("properties", "各字段定义（键 → schema）"),
        ("required", "必填字段列表"),
        ("enum", "限定取值范围"),
        ("items", "array 的元素类型"),
        ("description", "字段含义说明"),
    ]:
        print(f"    · {k:<12}{v}")


if __name__ == "__main__":
    main()