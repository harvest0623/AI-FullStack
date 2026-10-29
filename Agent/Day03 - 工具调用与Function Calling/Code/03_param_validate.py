"""
03_param_validate.py
参数校验：五类校验（类型/必填/枚举/格式/范围），
错误信息要『可指导』——告诉模型哪里错了、怎么改。

运行：python 03_param_validate.py
"""

import re


class ParamValidationError(Exception):
    """携带可指导信息的校验异常。"""

    def __init__(self, field: str, message: str, hint: str = ""):
        super().__init__(message)
        self.field = field
        self.message = message
        self.hint = hint


def validate(params: dict, schema: dict) -> list[str]:
    """按 JSON Schema 风格校验参数，返回错误列表（空=通过）。"""
    errors = []
    props = schema.get("properties", {})
    required = schema.get("required", [])

    # 1) 必填检查
    for key in required:
        if key not in params or params.get(key) in (None, ""):
            errors.append(f"缺少必填参数 '{key}'；必须提供 {key}（{props.get(key, {}).get('description', '')}）")

    for key, value in params.items():
        if key not in props:
            errors.append(f"未知参数 '{key}'；合法参数：{list(props)}")
            continue
        rule = props[key]

        # 2) 类型检查
        expected = rule.get("type", "string")
        type_map = {"string": str, "integer": int, "number": (int, float), "boolean": bool}
        if expected in type_map and not isinstance(value, type_map[expected]):
            errors.append(f"参数 '{key}' 类型错误：需要 {expected}，实际 {type(value).__name__}")
            continue

        # 3) 枚举检查
        if "enum" in rule and value not in rule["enum"]:
            errors.append(f"参数 '{key}' 的值 '{value}' 不合法；可选值：{rule['enum']}")

        # 4) 格式检查（pattern）
        if "pattern" in rule and isinstance(value, str):
            if not re.match(rule["pattern"], value):
                examples = rule.get("examples", [])
                ex = f"，示例：{examples}" if examples else ""
                errors.append(f"参数 '{key}' 格式错误：需匹配 {rule['pattern']}{ex}")

        # 5) 范围检查
        if isinstance(value, (int, float)):
            if "minimum" in rule and value < rule["minimum"]:
                errors.append(f"参数 '{key}'={value} 低于最小值 {rule['minimum']}")
            if "maximum" in rule and value > rule["maximum"]:
                errors.append(f"参数 '{key}'={value} 超过最大值 {rule['maximum']}")

    return errors


# ---------------------------------------------------------------------------
# 演示：query_sales 的完整 Schema 与各种"幻觉参数"
# ---------------------------------------------------------------------------
SCHEMA = {
    "type": "object",
    "properties": {
        "week": {"type": "string", "pattern": r"^\d{4}-W\d{2}$",
                 "description": "周次", "examples": ["2024-W03"]},
        "region": {"type": "string", "enum": ["north", "south", "all"]},
        "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
    },
    "required": ["week"],
}

CASES = [
    ("正常", {"week": "2024-W03"}),
    ("缺必填", {"region": "north"}),
    ("类型错误(整数当字符串传)", {"week": "2024-W03", "top_k": "10"}),
    ("枚举外取值", {"week": "2024-W03", "region": "west"}),
    ("格式幻觉(编造周次)", {"week": "上周"}),
    ("范围越界", {"week": "2024-W03", "top_k": 999}),
    ("未知参数", {"week": "2024-W03", "city": "北京"}),
]


def main():
    print("=" * 62)
    print("参数校验：把幻觉拦在执行之前")
    print("=" * 62)
    for name, params in CASES:
        errors = validate(params, SCHEMA)
        status = "✅ 通过" if not errors else "❌ 拒绝"
        print(f"\n[{name}] 输入 {params}")
        print(f"  {status}")
        for e in errors:
            print(f"    - {e}")

    print("\n" + "=" * 62)
    print("错误信息对比：为什么『可指导』很重要")
    print("=" * 62)
    bad = "参数错误"
    good = "参数 'week' 格式错误：需匹配 ^\\d{4}-W\\d{2}$，示例：['2024-W03']"
    print(f"  不可指导: {bad}")
    print(f"    -> 模型只能瞎猜，重试大概率再错")
    print(f"  可指导  : {good}")
    print(f"    -> 模型下一步就能自行修正为 2024-W03")

    print("\n要点：")
    print("  1. 五类校验：必填/类型/枚举/格式(pattern)/范围(min-max)")
    print("  2. 校验失败的错误信息 = 给模型的修正指南")
    print("  3. 校验通过≠参数语义正确（上周≠某周），语义靠工具返回 error 再纠正")


if __name__ == "__main__":
    main()