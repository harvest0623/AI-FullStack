# -*- coding: utf-8 -*-
"""
Day03 - 03 从函数签名生成 schema

许多框架能从『函数签名 + 类型注解 + docstring』自动生成工具描述。
这里演示这一思路，并用一个示例函数自动产出 JSON。

离线可运行。
"""

import inspect
import json


def _to_schema_type(t):
    name = getattr(t, "__name__", str(t))
    # 处理 Optional / list[int] 等简化
    for src, dst in (("str", "string"), ("int", "integer"),
                     ("float", "number"), ("bool", "boolean")):
        if src in name:
            return {"type": dst}
    return {"type": "string"}


def signature_to_schema(fn) -> dict:
    """从函数签名 + docstring 生成工具描述。"""
    sig = inspect.signature(fn)
    doc = (inspect.getdoc(fn) or "").strip()
    desc = doc.split("\n")[0] if doc else fn.__name__

    properties = {}
    required = []
    for pname, p in sig.parameters.items():
        props = _to_schema_type(p.annotation)
        props["description"] = f"参数 {pname}"
        properties[pname] = props
        if p.default is inspect.Parameter.empty:
            required.append(pname)

    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


# —— 示例：一个带类型注解和 docstring 的函数 ——
def get_weather(city: str, unit: str = "celsius") -> str:
    """查询指定城市的当前天气。"""
    return f"{city}: 晴, 25°C"


def main():
    print(">> 从函数签名生成 schema\n")
    print("  原函数：")
    print("    def get_weather(city: str, unit: str = 'celsius') -> str")
    print("        '''查询指定城市的当前天气。'''\n")
    schema = signature_to_schema(get_weather)
    print("  自动生成的工具描述：\n")
    print(json.dumps(schema, ensure_ascii=False, indent=2))
    print("\n  tips: 有了这个思路，你就能封装属于自己的『工具注册装饰器』（Day09 会进一步应用）。")


if __name__ == "__main__":
    main()