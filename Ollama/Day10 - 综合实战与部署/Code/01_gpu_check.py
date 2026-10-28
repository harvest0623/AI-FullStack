# -*- coding: utf-8 -*-
"""
Day10 - 01 GPU 与硬件检测

判断本机适合跑多大的模型：
1. 探测 nvidia-smi（有 GPU 则打印显存）
2. 探测 CPU 核数
3. 探测 Ollama 是否在跑、有没有已加载模型

离线可运行（未安装 nvidia-smi 不影响，只是打印提示）。
"""

import os
import platform
import subprocess
import urllib.request
import json


def detect_gpu():
    print("一、GPU 检测：")
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader"], timeout=5).decode().strip()
        print(f"  发现 NVIDIA GPU：{out}")
        return True
    except Exception:
        print("  未检测到 NVIDIA GPU（可能 CPU 推理，或未装驱动）")
        return False


def detect_cpu():
    print("\n二、CPU 检测：")
    count = os.cpu_count() or 0
    arch = platform.machine()
    print(f"  CPU 核心数：{count}，架构：{arch}")
    return count


def detect_ollama():
    print("\n三、Ollama 状态：")
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/", timeout=1) as r:
            up = r.status == 200
        print(f"  服务存活：{'是' if up else '否'}")
    except Exception:
        up = False
        print("  服务存活：否（未启动 ollama serve）")
    if up:
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=2) as r:
                data = json.loads(r.read().decode())
            loaded = [m.get("name") for m in data.get("models", [])]
            print(f"  已加载（在内存中的）模型：{loaded if loaded else '无'}")
        except Exception:
            pass


def main():
    print(">> 本机推理能力检测\n")
    has_gpu = detect_gpu()
    cpu = detect_cpu()
    detect_ollama()

    print("\n建议：")
    if has_gpu:
        print("  有 GPU → 可跑 7B/8B 甚至更大模型，速度良好")
    elif cpu and cpu >= 8:
        print("  无 GPU 但多核 → 可跑 3B~7B 小模型，速度可接受")
    else:
        print("  资源有限 → 建议用 1B~3B 轻量模型（如 qwen2.5:1.5b）")


if __name__ == "__main__":
    main()