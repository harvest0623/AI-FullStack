# -*- coding: utf-8 -*-
"""
Day04 - 02 SDK 流式对话（stream=True）

对比：
  - 非流式：等全部生成好，一次返回
  - 流式：  chunk 生成器，逐 token 增量返回
"""

import time
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ollama_util import is_ollama_available

try:
    import ollama as _ollama
    SDK_AVAILABLE = True
except ImportError:
    _ollama = None
    SDK_AVAILABLE = False


def stream_real(model: str = "llama3.1"):
    messages = [{"role": "user", "content": "用三句话讲讲流式输出的好处。"}]
    print("  [流式] 逐 token 输出：", end="", flush=True)
    full = ""
    for chunk in _ollama.chat(model=model, messages=messages, stream=True):
        content = chunk.get("message", {}).get("content", "")
        if content:
            full += content
            print(content, end="", flush=True)
            time.sleep(0.02)
        if chunk.get("done"):
            stats = chunk
            break
    print(f"\n  [统计] 完成，生成 {stats.get('eval_count', '?')} tokens")
    return full


def stream_sim(model: str = "llama3.1"):
    demo = "[SimOllama:llama3.1] 流式好处：1) 首字节快 2) 体验好 3) 可早停。"
    print("  [模拟流式] 逐 token 输出：", end="", flush=True)
    for ch in demo:
        print(ch, end="", flush=True)
        time.sleep(0.015)
    print("\n  [模拟] 完成")


def main():
    print(">>> SDK 流式输出\n")
    if SDK_AVAILABLE and is_ollama_available("llama3.1"):
        stream_real()
    else:
        stream_sim()

    print("\n" + "=" * 60)
    print("流式 vs 非流式")
    print("=" * 60)
    print("  非流式：stream=False -> 一次返回完整 message.content")
    print("  流式  ：stream=True  -> 返回生成器，逐 chunk 增量")
    print("  体验上流式让用户立即看到内容，长文本尤其明显。")


if __name__ == "__main__":
    main()