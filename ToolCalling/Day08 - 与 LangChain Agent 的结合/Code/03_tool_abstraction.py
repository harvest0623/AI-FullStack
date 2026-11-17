# -*- coding: utf-8 -*-
"""
Day08 - 03 统一工具抽象（Tool / ToolRegistry）

把函数与工具描述统一封装，一处定义、统一 schema 生成与安全调用。

离线可运行（纯演示）。
"""

import inspect
import json


class Tool:
    def __init__(self, fn, description=None):
        self.fn = fn
        self.name = fn.__name__
        self.description = description or inspect.getdoc(fn) or ""

    def to_schema(self):
        """从签名生成工具 schema（复用 Day03 思路，简化）。"""
        sig = inspect.signature(self.fn)
        props, required = {}, []
        for pname, p in sig.parameters.items():
            ptype = str(p.annotation)[1:-1] if p.annotation is not inspect.Parameter.empty else "object"
            ptype = ptype if ptype in ("string", "integer", "number", "array", "boolean") else "string"
            props[pname] = {"type": ptype, "description": f"参数 {pname}"}
            if p.default is inspect.Parameter.empty:
                required.append(pname)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": props, "required": required},
            },
        }

    def run(self, **kwargs):
        return self.fn(**kwargs)


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def add(self, tool: Tool):
        self._tools[tool.name] = tool

    def list_schemas(self):
        return [t.to_schema() for t in self._tools.values()]

    def call(self, name, args):
        try:
            return self._tools[name].run(**args)
        except KeyError:
            return {"error": f"未知工具 {name}"}
        except Exception as e:
            return {"error": str(e)}


# —— 使用 ——
def get_weather(city: str) -> str:
    """查询指定城市天气。"""
    return f"{city}: 晴"


def get_time(city: str) -> str:
    """查询指定城市时间。"""
    return f"{city}: 14:00"


def main():
    print(">> 统一工具抽象\n")
    reg = ToolRegistry()
    reg.add(Tool(get_weather))
    reg.add(Tool(get_time))

    print("自动生成的 schema 列表：\n")
    print(json.dumps(reg.list_schemas(), ensure_ascii=False, indent=2))

    print("\n统一调用：")
    print("  reg.call('get_weather', {'city':'北京'}) →", reg.call("get_weather", {"city": "北京"}))
    print("  reg.call('get_time', {'city':'上海'})   →", reg.call("get_time", {"city": "上海"}))
    print("  reg.call('none', {})                  →", reg.call("none", {}))


if __name__ == "__main__":
    main()