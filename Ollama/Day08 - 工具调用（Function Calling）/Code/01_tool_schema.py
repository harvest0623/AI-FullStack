# -*- coding: utf-8 -*-
"""
Day08 - 01 工具 Schema 拆解

工具调用第一步：用 JSON Schema 完整描述一个"可调用函数"。
模型根据 Schema 决定要不要调用、怎么填参数。

离线演示——不调模型，只看 Schema 该怎么写。
"""

from ollama_util import WEATHER_TOOL


def explain_schema():
    print("一个 function 工具的 Schema：\n")
    for key, val in WEATHER_TOOL.items():
        if key == "function":
            f = val
            print(f"  type: {WEATHER_TOOL['type']}")
            for k, v in f.items():
                if k == "parameters":
                    print(f"  parameters: {json_d(v)}")
                else:
                    print(f"  function.{k}: {v}")
        else:
            print(f"  {key}: {val}")


def json_d(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


def good_vs_bad_descriptions():
    print("\n为什么 description 重要：")
    print("  好：'查询指定城市的实时天气'（模型能判断何时该用）")
    print("  差：'the function to get weather'（语义不够明确）\n")

    print("parameters 约定：")
    print("  - properties.city: 参数名 + 类型 + 含义")
    print("  - required: ['city']  哪些参数必须")


def main():
    print(">> 工具 Schema 拆解\n")
    explain_schema()
    good_vs_bad_descriptions()
    print("\n→ 一个 Schema 就是一份『工具说明书』，模型照着它调用你。")


if __name__ == "__main__":
    main()