# -*- coding: utf-8 -*-
"""
toolcall_check.py - ToolCalling 环境探测器（各 Day 通用）

作用：
  1. 检测 Python 版本
  2. 检测是否安装常用模型 SDK（openai / anthropic / ollama）——仅用于真实 API 形态对照
  3. 给出环境状态字串

讲解脚本本身离线可运行，不依赖这些 SDK；本探测器仅作信息展示。

离线可运行（纯探测，不联网）。
"""

import importlib.util
import sys

SDKS = ["openai", "anthropic", "ollama"]


def py_version() -> str:
    import platform
    return platform.python_version()


def available_sdks() -> list:
    return [s for s in SDKS if importlib.util.find_spec(s) is not None]


def main():
    print(">> ToolCalling 环境探测器\n")
    print(f"  Python 版本 : {py_version()}")
    got = available_sdks()
    if got:
        print(f"  已安装模型 SDK : {', '.join(got)}（可用于真实 API 形态对照）")
    else:
        print("  已安装模型 SDK : 无（讲解脚本仍可离线运行，无需这些）")

    print("\n  说明：")
    print("    · 本模块讲解脚本全部离线，无需真实 key")
    print("    · 想对照真实工具调用，安装 openai / anthropic / ollama 任一即可")


if __name__ == "__main__":
    main()