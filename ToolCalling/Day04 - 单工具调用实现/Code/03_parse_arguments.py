# -*- coding: utf-8 -*-
"""
Day04 - 03 参数安全解析与校验

提供可复用的参数处理工具：解析 arguments（JSON 字符串）→ 校验必填与类型。

离线可运行（讲解 + 工具函数）。
"""

import json


def parse_arguments(raw: str):
    """把 arguments 字符串解析为 dict；非法则返回 None。"""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def validate_required(args, required):
    """校验必填字段，返回缺失列表。"""
    return [f for f in required if f not in args]


def validate_types(args, types):
    """按 {字段: 类型名} 校验，返回类型不符列表（简化：返回第一个冲突描述）。"""
    problems = []
    for field, tname in types.items():
        if field not in args:
            continue
        v = args[field]
        ok = (
            (tname == "string" and isinstance(v, str))
            or (tname == "integer" and isinstance(v, int) and not isinstance(v, bool))
            or (tname == "number" and isinstance(v, (int, float)) and not isinstance(v, bool))
            or (tname == "boolean" and isinstance(v, bool))
        )
        if not ok:
            problems.append(f"字段[{field}]应为 {tname}，实际 {type(v).__name__}")
    return problems


def get_weather(city: str) -> str:
    return f"{city}: 晴 25°C"


def main():
    print(">> 参数安全解析与校验\n")

    # 合法参数
    raw = json.dumps({"city": "北京"})
    args = parse_arguments(raw)
    print(f"  解析 {raw!r} → {args}")

    # 非法 JSON
    bad = parse_arguments("not json")
    print(f"  解析 'not json' → {bad}")

    # 空
    print(f"  解析 None → {parse_arguments(None)}")

    print("\n校验：")
    missing = validate_required(args, ["city"])
    print(f"  必填 city 缺失？ → {missing if missing else '无，通过'}")
    type_issues = validate_types(args, {"city": "string"})
    print(f"  类型校验 city=string？ → {type_issues if type_issues else '通过'}")

    print("\n（参数合法才执行）")
    if not missing and not type_issues:
        print(f"  执行 get_weather → {get_weather(args['city'])}")
    else:
        print("  拒绝执行，向模型回传错误")


if __name__ == "__main__":
    main()