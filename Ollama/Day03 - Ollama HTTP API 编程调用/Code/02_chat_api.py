# -*- coding: utf-8 -*-
"""
Day03 - 02 /api/chat 调用 + 响应元数据解析

演示：
1. 构造多轮对话消息
2. 调用 /api/chat（真实环境）或模拟
3. 解析 message.content 与 token/耗时统计
4. 打印"速度"（token/s）教学指标
"""

import json
import time
import urllib.request
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ollama_util import is_ollama_available, SimOllama

HOST = "http://127.0.0.1:11434"


def real_chat(messages: list[dict], options: dict | None = None, model: str = "llama3.1"):
    """真实调用 /api/chat 并返回完整响应 dict"""
    body = {"model": model, "messages": messages, "stream": False, "options": options or {}}
    req = urllib.request.Request(
        f"{HOST}/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def demo_multi_turn():
    print("=" * 60)
    print("多轮对话 /api/chat（含 system 提示）")
    print("=" * 60)

    messages = [
        {"role": "system", "content": "你是一位数据分析助手，回答简洁，优先给结论。"},
        {"role": "user", "content": "什么是 RAG？一句话解释。"},
        {"role": "assistant", "content": "RAG 是检索增强生成，先检索相关资料再让模型基于资料生成回答。"},
        {"role": "user", "content": "那它的最大好处是什么？"},
    ]

    if is_ollama_available("llama3.1"):
        resp = real_chat(messages, {"temperature": 0.3})
        content = resp["message"]["content"]
        eval_count = resp.get("eval_count", 0)
        eval_dur = resp.get("eval_duration", 0) / 1e9
    else:
        content = SimOllama.chat("llama3.1", messages, {"temperature": 0.3})
        eval_count, eval_dur = 42, 1.2

    print(f"\n  助手回复：{content}")
    if eval_dur and eval_count:
        print(f"\n  [统计] 生成 {eval_count} tokens，耗时 {eval_dur:.2f}s，"
              f"≈ {eval_count / eval_dur:.1f} tokens/s")


def parse_meta(model: str = "qwen2.5"):
    """展示响应中的元数据字段及其含义"""
    print("\n" + "=" * 60)
    print("响应元数据解析（token 与耗时）")
    print("=" * 60)
    fields = [
        ("prompt_eval_count", "输入 token 数"),
        ("prompt_eval_duration", "处理输入耗时(ns)"),
        ("eval_count", "生成的 token 数"),
        ("eval_duration", "生成耗时(ns)"),
        ("total_duration", "总耗时(ns)"),
        ("load_duration", "模型加载耗时(ns)"),
    ]
    for k, meaning in fields:
        print(f"  {k:<22} → {meaning}")

    msgs = [{"role": "user", "content": "写一段示例"}]
    if is_ollama_available(model):
        resp = real_chat(msgs, {}, model=model)
        prompt_t = resp.get("prompt_eval_count", 0)
        gen_t = resp.get("eval_count", 0)
        total_ns = resp.get("total_duration", 0)
        print(f"\n  真实结果：输入 {prompt_t} token，生成 {gen_t} token，"
              f"总耗时 {total_ns / 1e9:.2f}s")
    else:
        print("\n  真实结果：（未检测到环境，使用模拟值）")

    print("\n  tips：eval_count/total_duration 是评估成本与性能的关键。")


def main():
    demo_multi_turn()
    parse_meta()


if __name__ == "__main__":
    main()