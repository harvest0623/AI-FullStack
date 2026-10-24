# -*- coding: utf-8 -*-
"""
Day01 - 02 环境检查：探测 Ollama 服务、版本与本地模型

输出一份"环境诊断报告"，告诉你当前是否能走真实模式。
"""

import time
import urllib.request
import json

from ollama_util import _server_alive, list_local_models


def check_version() -> str | None:
    """读取 Ollama 版本（走 / 根路径的响应头或正文）"""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/", timeout=1) as r:
            body = r.read().decode(errors="ignore")
            # 常见格式："Ollama is running" 或带版本
            return body.strip()[:60] or f"HTTP {r.status}"
    except Exception:
        return None


def diagnostic_report():
    """生成环境诊断报告"""
    print("=" * 62)
    print("Ollama 环境诊断报告")
    print("=" * 62)

    # 1. 服务是否存活
    t0 = time.time()
    alive = _server_alive()
    cost = (time.time() - t0) * 1000
    if alive:
        version = check_version()
        print(f"  ✓ Ollama 服务：存活（{cost:.0f}ms）")
        print(f"  ✓ 服务版本/响应：{version}")
    else:
        print(f"  ✗ Ollama 服务：未检测到（{cost:.0f}ms）")
        print("    请执行: ollama serve，或确认桌面版已启动")

    # 2. 本地模型
    models = list_local_models()
    print(f"  {'✓' if models else '✗'} 本地模型：{len(models)} 个")
    if models:
        for m in sorted(models):
            print(f"       - {m}")

    # 3. 结论
    print("-" * 62)
    if alive:
        print("  结论：可走「真实模式」，pull 模型后代码即调真实 API")
    else:
        print("  结论：当前走「SimOllama 模拟」，代码逻辑不变，仅输出为模拟")
    print("  (真实模式安装: https://ollama.com/download)")


def main():
    diagnostic_report()
    print("\n>>> 无论是否有 Ollama，本脚本都能运行并给出诊断。")


if __name__ == "__main__":
    main()