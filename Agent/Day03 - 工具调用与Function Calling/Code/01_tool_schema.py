"""
01_tool_schema.py
工具定义（Schema）设计：好与坏的定义对比，以及如何把函数自动转成
模型可读的 JSON Schema 工具清单。

运行：python 01_tool_schema.py
"""

import json


# ---------------------------------------------------------------------------
# 反例：一个"烂"的工具定义
# ---------------------------------------------------------------------------
BAD_TOOL = {
    "name": "tool1",
    "description": "查询数据",
    "parameters": {"type": "object", "properties": {"p": {"type": "string"}}},
}

# ---------------------------------------------------------------------------
# 正例：生产级的工具定义
# ---------------------------------------------------------------------------
GOOD_TOOL = {
    "name": "query_sales",
    "description": (
        "查询指定周次的销量数据。"
        "当用户询问某周/上周/本周的销售额、订单量时使用。"
        "输入周次（格式 YYYY-Www，如 2024-W03），返回该周销量与订单数。"
        "注意：仅支持 2024 年数据。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "week": {
                "type": "string",
                "description": "周次，格式 YYYY-Www，例如 2024-W03",
                "pattern": r"^\d{4}-W\d{2}$",
                "examples": ["2024-W01", "2024-W12"],
            },
            "region": {
                "type": "string",
                "description": "地区，默认 all",
                "enum": ["north", "south", "all"],
                "default": "all",
            },
        },
        "required": ["week"],
    },
}


# ---------------------------------------------------------------------------
# 自动从函数生成 Schema 的思路（框架都这么做）
# ---------------------------------------------------------------------------
def query_sales(week: str, region: str = "all") -> dict:
    """查询指定周次的销量数据。"""
    return {"week": week, "region": region, "sales": 1200, "orders": 340}


def auto_schema(func) -> dict:
    """演示：从类型注解 + docstring 自动生成工具 Schema。"""
    import inspect
    sig = inspect.signature(func)
    hints = func.__annotations__

    props = {}
    required = []
    for name, param in sig.parameters.items():
        py_type = hints.get(name, str)
        json_type = {str: "string", int: "integer", float: "number",
                     bool: "boolean", list: "array", dict: "object"}.get(py_type, "string")
        props[name] = {"type": json_type, "description": f"参数 {name}"}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "name": func.__name__,
        "description": (func.__doc__ or "").strip(),
        "parameters": {"type": "object", "properties": props, "required": required},
    }


def main():
    print("=" * 62)
    print("1) 坏定义（模型几乎不可能正确选用）")
    print("=" * 62)
    print(json.dumps(BAD_TOOL, ensure_ascii=False, indent=2))
    print("\n问题：名字无意义；描述没说何时用/输入/输出；参数 p 是什么没人知道。")

    print("\n" + "=" * 62)
    print("2) 好定义（生产级）")
    print("=" * 62)
    print(json.dumps(GOOD_TOOL, ensure_ascii=False, indent=2))
    print("\n优点：动词命名；描述含『何时用+输入+返回+限制』；参数有格式与枚举。")

    print("\n" + "=" * 62)
    print("3) 从函数自动生成 Schema（框架的做法）")
    print("=" * 62)
    print(json.dumps(auto_schema(query_sales), ensure_ascii=False, indent=2))

    print("\n要点：")
    print("  1. 描述是写给模型的 API 文档：何时用/输入什么/返回什么/限制")
    print("  2. 枚举和 pattern 是把『猜』变成『选』，大幅降低参数幻觉")
    print("  3. 自动 Schema 方便起步，但生产建议手写精修 description")


if __name__ == "__main__":
    main()