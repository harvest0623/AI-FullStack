"""
Day03 工具定义与注册 tools.py
==============================
把"工具"抽象成可被 LLM 调用、可被 python 执行的统一对象。

关键点:
  - Tool.name      : 模型用于选择工具的标识
  - Tool.schema()  : JSON Schema, 告诉模型参数长什么样(OpenAI tools 格式)
  - Tool.run(**kw) : 真正执行(带 try 兜底)

配套函数:
  - tool(...) 装饰器, 用 Pydantic 推断参数 schema
  - make_tools(...) : 包成 OpenAI tools 参数列表
  - create_registry(...) : 建 name->Tool 的注册表, 供 execute 按名调用

运行自测:
  python "Day03 - 工具定义与注册/Code/tools.py"
"""
from __future__ import annotations

from inspect import signature, Parameter
from typing import Callable, Optional, get_type_hints, get_args, get_origin

try:
    from typing import get_origin, get_args
except ImportError:
    get_origin = get_args = None  # pragma: no cover


class Tool:
    """一个可被 LLM 调用、可被执行的可调用单元。"""

    def __init__(self, name: str, description: str,
                 fn: Callable, param_schema: Optional[dict] = None):
        self.name = name
        self.description = description
        self.fn = fn
        self.param_schema = param_schema or _infer_schema(fn)

    def schema(self) -> dict:
        """返回 OpenAI `tools` 里的单个元素(不含外层 type)。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.param_schema,
            },
        }

    def run(self, **kwargs):
        """执行工具; 调用方负责异常处理(这里只透传异常可读信息)。"""
        return self.fn(**kwargs)

    def __repr__(self):  # pragma: no cover
        return f"<Tool {self.name}>"


# ---------- 参数 schema 推断(极简, 兼容 int/float/str/bool/None 与默认值) ----------
def _infer_schema(fn: Callable) -> dict:
    hints = get_type_hints(fn)
    sig = signature(fn)
    props, required = {}, []
    for pname, p in sig.parameters.items():
        if pname in ("self", "cls"):
            continue
        typ = hints.get(pname, str)
        tname = _py_type_to_js(typ)
        props[pname] = {"type": tname}
        if p.default is not Parameter.empty:
            props[pname]["default"] = p.default
        else:
            required.append(pname)
    return {"type": "object", "properties": props, "required": required}


def _py_type_to_js(typ) -> str:
    base = get_origin(typ) or typ
    if base is int:
        return "integer"
    if base is float:
        return "number"
    if base is bool:
        return "boolean"
    if base in (list, tuple, set):
        return "array"
    if base is dict:
        return "object"
    return "string"


# ---------- 便捷工厂: 用注解 + 函数体定义工具 ----------
def tool(fn: Callable) -> Tool:
    """把普通函数变成 Tool, 描述取函数 docstring 第一行。"""
    doc = (fn.__doc__ or "").strip().splitlines()
    desc = doc[0] if doc else fn.__name__
    return Tool(fn.__name__, desc, fn)


# ---------- 注册表 ----------
class ToolRegistry:
    def __init__(self, tools: Optional[list[Tool]] = None):
        self._tools: dict[str, Tool] = {}
        for t in (tools or []):
            self.add(t)

    def add(self, t: Tool) -> None:
        self._tools[t.name] = t

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools)

    def openai_tools(self) -> list[dict]:
        return [t.schema() for t in self._tools.values()]

    def execute(self, name: str, **kwargs):
        """按名执行, 找不到抛 KeyError。"""
        return self._tools[name].run(**kwargs)


def make_tools(*tools_or_registry) -> list[dict]:
    """拼出可直接传给 OpenAI tools= 的列表。"""
    if len(tools_or_registry) == 1 and isinstance(tools_or_registry[0], ToolRegistry):
        return tools_or_registry[0].openai_tools()
    return [t.schema()
            for t in tools_or_registry if isinstance(t, Tool)]


if __name__ == "__main__":
    # 定义两个示例工具
    def add(a: int, b: int = 0) -> int:
        """两数相加"""
        return a + b

    def get_weather(city: str) -> str:
        """返回城市天气"""
        return f"{city}: 25℃ 多云"

    reg = ToolRegistry()                          # 注册表
    reg.add(tool(add))
    reg.add(tool(get_weather))

    print("注册的工具:", reg.names())
    print("\nopenai tools 参数:")
    import json
    print(json.dumps(reg.openai_tools(), ensure_ascii=False, indent=2))
    print("\n执行 get_weather:", reg.execute("get_weather", city="杭州"))
    print("执行 add:", reg.execute("add", a=3, b=4))