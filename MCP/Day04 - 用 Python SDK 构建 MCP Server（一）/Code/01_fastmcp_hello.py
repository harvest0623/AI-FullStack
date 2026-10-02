# -*- coding: utf-8 -*-
"""
Day04 - 01 FastMCP 用法讲解

用『模拟』方式演示 FastMCP 的核心套路：装饰器把函数变工具、
自动生成 JSON Schema、stdio 运行、Client 发现与调用。

离线可运行（无需安装 mcp 包；展示的是逻辑而非真实 SDK 调用）。
"""

import json


# ---------- 离线模拟：模拟 @mcp.tool() 注册 ----------
class _Registry:
    """简易的『工具注册表』，用于离线演示 FastMCP 的注册链路。"""

    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        def deco(fn):
            tname = name or fn.__name__
            # 从函数签名注解推断参数 schema（示意）
            import inspect
            sig = inspect.signature(fn)
            props = {}
            required = []
            for pname, p in sig.parameters.items():
                ptype = p.annotation
                ts = "string" if ptype is str else "number" if ptype is int else "object"
                props[pname] = {"type": ts, "description": f"参数 {pname}"}
                required.append(pname)
            self.tools[tname] = {
                "name": tname,
                "description": (fn.__doc__ or "").strip().split("\n")[0],
                "inputSchema": {"type": "object", "properties": props, "required": required},
                "fn": fn,
            }
            return fn
        return deco


# ---------- 模拟 FastMCP 对象 ----------
class FastMCP:
    def __init__(self, name):
        self.name = name
        self._reg = _Registry()

    def tool(self, name=None):
        return self._reg.tool(name)

    def run(self):
        print(f"  ({self.name}: 以 stdio 方式运行，等待 Client 连接...)")
        print(f"  已注册工具列表：{', '.join(self._reg.tools.keys())}")
        for name, t in self._reg.tools.items():
            print(f"    - {name}（description: {t['description']}）")


# ---------- 用户代码：与真实 FastMCP 完全同形 ----------
mcp = FastMCP("Hello")


@mcp.tool()
def echo(text: str) -> str:
    """原样返回输入的文字。"""
    return f"你说了：{text}"


@mcp.tool()
def add(a: int, b: int) -> int:
    """返回两个整数之和。"""
    return a + b


def explain():
    print("\n" + "=" * 60)
    print("这套代码在真实 SDK 下等价于：")
    print("  from mcp.server.fastmcp import FastMCP")
    print("  mcp = FastMCP(\"Hello\")")
    print("  @mcp.tool()")
    print("  def echo(text: str) -> str: ...")
    print("  mcp.run()   # 默认 stdio 运行\n")
    print("SDK 自动完成：注册工具 → 生成 JSON Schema → 处理握手 → 接收调用。")


def main():
    print(">> FastMCP 用法（离线模拟）\n")
    print("第一步：注册两个工具…\n")
    mcp.run()
    explain()

    print("\n第二步：模拟 Client 能力发现与一次调用")
    import inspect
    echo_fn = mcp._reg.tools["echo"]["fn"]
    print(f"  调用 echo(text='hello') → {echo_fn('hello')}")
    add_fn = mcp._reg.tools["add"]["fn"]
    print(f"  调用 add(a=3, b=4)     → {add_fn(3, 4)}")

    print("\n  tips: 装饰器 + 类型标注 + docstring，就是定义工具的全部三要素。")


if __name__ == "__main__":
    main()