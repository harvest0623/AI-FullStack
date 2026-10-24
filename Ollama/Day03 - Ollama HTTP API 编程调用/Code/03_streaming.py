# -*- coding: utf-8 -*-
"""
Day03 - 03 流式生成（stream:true）逐 token 输出

演示：
1. 构建流式请求
2. 用 iter_lines 逐行读取 NDJSON
3. 实时拼接增量内容，模拟"打字机效果"
4. 结束时读取统计字段
5. 非流式 vs 流式对比说明
"""

import json
import time
import urllib.request
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ollama_util import is_ollama_available

HOST = "http://127.0.0.1:11434"


def streaming_chat(model: str, messages: list[dict], options: dict | None = None) -> str:
    """
    流式调用 /api/chat。
    返回拼接的完整文本，并打印逐 token 输出效果。
    """
    body = {"model": model, "messages": messages, "stream": True, "options": options or {}}
    full = ""
    done_stats = {}
    print("  [" + "流式输出开始".center(38) + "]")

    req = urllib.request.Request(
        f"{HOST}/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        for raw in r:
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("done"):
                done_stats = obj
                break
            chunk = obj.get("message", {}).get("content", "")
            full += chunk
            print(chunk, end="", flush=True)
            time.sleep(0.02)  # 模拟打字速度，便于观察增量

    print("\n  [" + "流式输出结束".center(38) + "]")
    if done_stats:
        print(f"  [统计] 生成 {done_stats.get('eval_count', '?')} tokens，"
              f"耗时 {done_stats.get('eval_duration', 0)/1e9:.2f}s")
    return full


def fake_stream(model: str, prompt: str) -> str:
    """无环境时模拟逐字输出（模拟打字机教学）"""
    demo = f"[SimOllama:{model}] 针对「{prompt[:12]}...」的模拟流式回答，逐 token 显示。"
    print("  [" + "模拟流式输出开始".center(38) + "]")
    for ch in demo:
        print(ch, end="", flush=True)
        time.sleep(0.01)
    print("\n  [" + "模拟流式输出结束".center(38) + "]")
    return demo


def explain_tradeoff():
    print("\n" + "=" * 60)
    print("流式 vs 非流式")
    print("=" * 60)
    print("  非流式(stream:false)：等服务端生成完整才返回，首字节延迟 = 全量时间")
    print("  流式(stream:true)  ：每生成一个 token 立即下发，首字节延迟 ≈ 首 token 时间")
    print("  场景：")
    print("     - 流式：聊天、长文本生成（用户等着看打字效果）")
    print("     - 非流式：批处理、后台任务、对结果不敏感的下游管道")
    print("  实现差异：主要是 iter_lines/逐行 与 一次 read 的差别。")


def main():
    print(">>> 流式生成演示\n")
    model = "llama3.1"
    if is_ollama_available(model):
        streaming_chat(model, [{"role": "user", "content": "用三句话介绍流式输出的好处"}])
    else:
        fake_stream(model, "流式输出的好处")

    explain_tradeoff()


if __name__ == "__main__":
    main()