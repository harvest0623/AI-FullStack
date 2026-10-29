"""
02_tool_registry.py
工具注册表：注册 / 路由 / 工具清单输出。
注册表是 Agent 的"能力目录"——模型看到的工具列表由它生成，执行也由它路由。

运行：python 02_tool_registry.py
"""

import json
from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict            # JSON Schema
    func: Callable
    risk: str = "low"           # low / medium / high（Day09 权限矩阵用）


class ToolRegistry:
    """工具注册表：注册、查询、生成给模型的清单、安全路由执行。"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"工具重名：{tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_for_model(self) -> list[dict]:
        """生成给模型的工具清单（含 Schema，不含函数体）。"""
        return [{"name": t.name, "description": t.description,
                 "parameters": t.parameters} for t in self._tools.values()]

    def dispatch(self, name: str, args: dict):
        """路由执行：工具不存在时返回可指导的错误。"""
        tool = self._tools.get(name)
        if tool is None:
            return {"error": f"未知工具 '{name}'",
                    "available": list(self._tools)}
        try:
            return tool.func(**args)
        except TypeError as e:
            return {"error": f"参数不匹配：{e}", "hint": "请检查参数名与必填项"}
        except Exception as e:
            return {"error": f"执行失败：{e}"}


# ---------------------------------------------------------------------------
# 一组示例工具
# ---------------------------------------------------------------------------
def query_sales(week: str) -> dict:
    """查询指定周次的销量数据。"""
    return {"week": week, "sales": 980, "orders": 290}


def calc(expression: str) -> dict:
    """计算数学表达式。"""
    return {"result": eval(expression, {"__builtins__": {}}, {})}


def search_kb(keyword: str, top_k: int = 3) -> dict:
    """在知识库中检索文档。"""
    return {"keyword": keyword, "hits": [f"《{keyword} 相关文档 {i}》" for i in range(1, top_k + 1)]}


def send_email(to: str, subject: str, body: str) -> dict:
    """发送邮件（高危操作）。"""
    return {"status": "sent", "to": to, "subject": subject}


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(Tool(
        "query_sales", "查询指定周次(YYYY-Www)的销量数据，返回销量与订单数",
        {"type": "object",
         "properties": {"week": {"type": "string", "pattern": r"^\d{4}-W\d{2}$"}},
         "required": ["week"]},
        query_sales))
    reg.register(Tool(
        "calc", "计算数学表达式，如 (980-1200)/1200*100",
        {"type": "object",
         "properties": {"expression": {"type": "string"}},
         "required": ["expression"]},
        calc))
    reg.register(Tool(
        "search_kb", "在企业知识库中检索文档",
        {"type": "object",
         "properties": {"keyword": {"type": "string"}, "top_k": {"type": "integer", "default": 3}},
         "required": ["keyword"]},
        search_kb))
    reg.register(Tool(
        "send_email", "发送邮件（高危：需要审批）",
        {"type": "object",
         "properties": {"to": {"type": "string"}, "subject": {"type": "string"},
                        "body": {"type": "string"}},
         "required": ["to", "subject", "body"]},
        send_email, risk="high"))
    return reg


def main():
    reg = build_registry()

    print("=" * 62)
    print("1) 注册表生成的工具清单（发给模型的内容）")
    print("=" * 62)
    for t in reg.list_for_model():
        print(f"  - {t['name']:<12} {t['description']}")

    print("\n" + "=" * 62)
    print("2) 路由执行")
    print("=" * 62)
    print("  正常调用:", reg.dispatch("query_sales", {"week": "2024-W02"}))
    print("  正常调用:", reg.dispatch("search_kb", {"keyword": "退款政策"}))

    print("\n" + "=" * 62)
    print("3) 幻觉与错误处理")
    print("=" * 62)
    print("  幻觉工具:", reg.dispatch("query_weather", {"city": "北京"}))
    print("  参数错名:", reg.dispatch("calc", {"expr": "1+1"}))
    print("  缺必填  :", reg.dispatch("calc", {}))

    print("\n要点：")
    print("  1. 注册表是能力目录：模型看到的清单与执行路由都出自它")
    print("  2. 未知工具/参数错误返回『可指导』的错误（含 available/hint），让模型能自我纠正")
    print("  3. 风险分级(risk 字段)已埋点，Day09 权限矩阵与审批门将使用")


if __name__ == "__main__":
    main()