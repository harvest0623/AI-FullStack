# -*- coding: utf-8 -*-
"""
Day03 - 04 /api/generate：单次文本生成（补全）

对比 /api/chat 与 /api/generate：
  chat     -> messages 多轮
  generate -> prompt 单次，可带 system 与 history
适合：代码补全、续写、一次性指令。
"""

import json
import urllib.request
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ollama_util import is_ollama_available

HOST = "http://127.0.0.1:11434"


def real_generate(prompt: str, model: str = "llama3.1", options: dict | None = None):
    body = {"model": model, "prompt": prompt, "stream": False, "options": options or {}}
    req = urllib.request.Request(
        f"{HOST}/api/generate",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def compare_chat_vs_generate():
    print("=" * 60)
    print("/api/chat 与 /api/generate 对比")
    print("=" * 60)
    print("\n【/api/chat】")
    print("  请求：messages=[system,user,assistant,user...]  多轮上下文")
    print("  响应：message.content")
    print("  适合：对话、有 system 角色、多轮记忆")
    print("\n【/api/generate】")
    print("  请求：prompt='...'  单次文本，可选 system/history")
    print("  响应：response 字段")
    print("  适合：补全、续写，一次性指令（不适合维护多轮）")


def generate_demo():
    print("\n" + "=" * 60)
    print("生成示例（代码续写场景）")
    print("=" * 60)
    prompt = "补全这个 Python 函数：\ndef add(a, b):"
    if is_ollama_available("llama3.1"):
        resp = real_generate(prompt, options={"num_predict": 64})
        out = resp.get("response", "")
        print(f"  输入 prompt：{prompt}")
        print(f"\n  生成结果：\n{out}")
    else:
        print(f"  输入 prompt：{prompt}")
        print("\n  [模拟] 生成结果：\n    return a + b   # （模拟 return 提示）")


def main():
    print(">>> /api/generate 演示\n")
    compare_chat_vs_generate()
    generate_demo()


if __name__ == "__main__":
    main()