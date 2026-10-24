# -*- coding: utf-8 -*-
"""
Day04 - 01 Python SDK 快速对话（.chat()）

演示：
1. 检测是否安装了 ollama SDK
2. 有则用 ollama.chat() 真实调用
3. 无则用 SimOllama 兼容模拟

关键：SDK 是 REST 的 Pythonic 封装。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ollama_util import is_ollama_available

# 尝试导入 ollama SDK；没有则置 None
try:
    import ollama as _ollama
    SDK_AVAILABLE = True
except ImportError:
    _ollama = None
    SDK_AVAILABLE = False


def sdk_chat():
    print("=" * 60)
    print("01 ollama.chat() 基本对话")
    print("=" * 60)
    print(f"  SDK 可用：{SDK_AVAILABLE}")
    print(f"  检测到 Ollama 服务与 llama3.1：{is_ollama_available('llama3.1')}\n")

    messages = [
        {"role": "system", "content": "你是简洁的助手，一句话回答。"},
        {"role": "user", "content": "用一句话介绍 Ollama 是什么。"},
    ]

    if SDK_AVAILABLE and is_ollama_available("llama3.1"):
        resp = _ollama.chat(model="llama3.1", messages=messages, stream=False,
                            options={"temperature": 0.5})
        content = resp["message"]["content"]
        print(f"  助手：{content}")
        if resp.get("eval_count"):
            print(f"  生成了 {resp['eval_count']} tokens")
    else:
        from ollama_util import SimOllama
        content = SimOllama.chat("llama3.1", messages, {"temperature": 0.5})
        print(f"  助手（模拟，未装 SDK 或未启动服务）：{content}")

    print("\n  tips: SDK 内部就是 POST /api/chat，只是把请求/响应包装成方法。")


def client_host():
    print("\n" + "=" * 60)
    print("02 Client(host) 指定服务地址")
    print("=" * 60)
    print("  默认连 127.0.0.1:11434")
    print("  可用 Client(host='http://另一台机器:11434') 连远程/多实例")
    print("  用途：多人共用一台 GPU 机，或把服务部署到容器/集群后统一入口")
    if not SDK_AVAILABLE:
        print("  (未安装 ollama SDK，展示代码示意，不实际连接)")


def main():
    sdk_chat()
    client_host()


if __name__ == "__main__":
    main()