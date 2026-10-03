# -*- coding: utf-8 -*-
"""
Day08 - 03 调试手段（mcp dev / Inspector）

介绍官方 CLI 的调试流程：用内置 Inspector 可视化查看并调用 Server。

离线可运行（纯讲解；命令需真实环境执行）。
"""


def debug_tools():
    print("官方 CLI 调试利器：\n")
    print("  · mcp dev <server.py>  启动内置测试客户端（Inspector）")
    print("  · uv run mcp dev ...     配合 uv 自动管理依赖\n")


def steps():
    print("调试步骤：\n")
    steps = [
        "写一个 Server（如 server_resources.py）",
        "在 Server 目录执行调试命令",
        "浏览器打开 Inspector 面板",
        "左侧：查看 tools / resources / prompts 清单",
        "右侧：选择工具 → 填参数 → 调用 → 看结果与日志",
    ]
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s}")


def commands():
    print("\n常用命令示例：\n")
    print("  uv run mcp dev server_resources.py")
    print("  uv run mcp dev server_bank.py")
    print("\n  等价于：python -m mcp.server.cli run ... 的调试包装")


def why():
    print("\n为什么要用 Inspector？\n")
    print("  - 不需要写 Client 代码即可验证 Server 是否正确")
    print("  - 能直观看到每个工具的 inputSchema")
    print("  - 观察调用返回与日志，定位问题更快")


def main():
    print(">> 调试手段\n")
    debug_tools()
    steps()
    commands()
    why()
    print("\n  tips: 先 `pip install mcp`；Inspector 是最快验证 Server 是否健壮的方式。")


if __name__ == "__main__":
    main()