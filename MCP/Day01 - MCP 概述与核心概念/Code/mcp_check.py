# -*- coding: utf-8 -*-
"""
mcp_check.py - MCP 环境探测器（各 Day 通用）

作用：
  1. 检测 Python 版本
  2. 检测是否安装官方 mcp SDK（真实 Server/Client 模板是否可跑）
  3. 检测 uv（官方 CLI 运行器是否可用）
  4. 汇总出一个环境可达状态字串，供讲解脚本控制"讲解模式 / 真实模式"

离线可运行（纯探测，不联网）。
"""

import importlib.util
import platform
import sys


def py_version() -> str:
    return platform.python_version()


def has_mcp() -> bool:
    """mcp 官方 SDK 是否已安装。"""
    return importlib.util.find_spec("mcp") is not None


def has_uv() -> bool:
    return importlib.util.find_spec("uv") is not None


def detect() -> dict:
    return {
        "python": py_version(),
        "mcp_sdk": has_mcp(),
        "uv": has_uv(),
    }


def seen_back(msg: str) -> str:
    """返回离线讲解模式的提示头。"""
    return f"[讲解模式] {msg}"


def main():
    print(">> MCP 环境探测器\n")
    env = detect()
    print(f"  Python 版本 : {env['python']}")
    print(f"  官方 MCP SDK: {'✓ 已安装（真实 Server/Client 模板可运行）' if env['mcp_sdk'] else '✗ 未安装（讲解脚本仍可离线运行）'}")
    print(f"  uv 运行器   : {'✓ 已安装（可用 mcp dev 调试）' if env['uv'] else '✗ 未安装（可选）'}")

    print("\n  环境模式判定：")
    if env["mcp_sdk"]:
        print("    → 真实模式：可直接运行 server_*.py / client_*.py 模板")
    else:
        print("    → 讲解模式：概念脚本离线演示；如需真实运行请先安装：pip install mcp")

    print("\n  检查完成。")


if __name__ == "__main__":
    main()