# -*- coding: utf-8 -*-
"""
Day02 - 模型管理与拉取

复用 Day01 的 ollama_util.py。该工具包含：
  - is_ollama_available / list_local_models  环境与列表
这些命令式操作（pull/push/rm）在教学里主要走 CLI，这里用"模拟输出"演示流程逻辑；
有真实环境时，同样代码逻辑可直接调用真实 API。
"""

# 为保持知识点自洽，本文件演示"命令层的逻辑"，不强依赖真实环境。

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ollama_util import is_ollama_available, list_local_models


# ============================================================
# 1. 本地模型列表（真实或模拟）
# ============================================================

def show_list():
    print("=" * 60)
    print("01 查看本地模型 ollama list")
    print("=" * 60)
    if is_ollama_available("llama3.1"):
        models = list_local_models()
        print(f" 真实环境，发现 {len(models)} 个模型：")
        for m in models:
            print(f"   - {m}")
    else:
        # 模拟展示（教学预设数据）
        demo = [
            {"name": "llama3.1:latest", "size": "4.7GB", "modified": "2026-09-10"},
            {"name": "nomic-embed-text:latest", "size": "274MB", "modified": "2026-09-10"},
            {"name": "qwen2.5:latest", "size": "4.7GB", "modified": "2026-09-09"},
            {"name": "tinyllama:latest", "size": "637MB", "modified": "2026-09-08"},
        ]
        print(" [模拟数据] 本机模型存放（/api/tags 返回的结构）：")
        for m in demo:
            print(f"   - {m['name']:<22} size={m['size']:<8} modified={m['modified']}")


# ============================================================
# 2. pull 流程（含模拟进度）
# ============================================================

def show_pull_flow():
    print("\n" + "=" * 60)
    print("02 拉取流程 ollama pull（模拟进度条）")
    print("=" * 60)
    progress_stages = [
        ("pulling manifest", ""),
        ("pulling xxx/base layer", "10%"),
        ("downloading", "25%"),
        ("downloading", "60%"),
        ("downloading", "100%"),
        ("verifying sha256 digest", ""),
        ("writing manifest", ""),
        ("success", "✔"),
    ]
    model = "qwen2.5:3b"
    print(f"  执行：ollama pull {model}\n")
    for msg, pct in progress_stages:
        bar = "█" * int((int(pct.rstrip('%')) / 10) if pct.endswith('%') and pct[:-1].isdigit() else 0)
        print(f"   {msg:<24} {bar} {pct}")
    print("\n  完成。模型已就绪 —— 提示：真实环境下 O 分片下载、可断点续传。")


# ============================================================
# 3. 命名规则
# ============================================================

def show_naming():
    print("\n" + "=" * 60)
    print("03 模型命名：仓库:标签")
    print("=" * 60)
    examples = [
        ("llama3.1", "默认 latest"),
        ("llama3.1:8b-instruct", "8B 指令版本"),
        ("qwen2.5:7b-q4_0", "7B + 4bit 量化"),
        ("ollama.com/library/llama3.1", "完整仓库路径"),
        ("myuser/mymodel:v1", "自定义（推送到你的模型库）"),
    ]
    for name, desc in examples:
        print(f"   {name:<38} {desc}")


# ============================================================
# 4. 主入口
# ============================================================

def main():
    print(">>> Day02 模型管理（真实/模拟双模式）\n")
    show_list()
    show_pull_flow()
    show_naming()


if __name__ == "__main__":
    main()