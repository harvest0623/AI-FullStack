# -*- coding: utf-8 -*-
"""
Day04 - 04 异步并发（AsyncClient）

演示：
1. asyncio + AsyncClient 并发多个对话请求
2. 对比串行 vs 并发的耗时
3. 无 SDK 或环境时用 asyncio.sleep 模拟延迟演示并发收益
"""

import asyncio
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


def fake_delay_reply(prompt: str) -> str:
    """模拟模型延迟（无环境时用）"""
    # 模拟约 1s 的生成（不同 prompt 长度不同延迟，教学用统一）
    return f"[模拟回答 about {prompt[:8]}]"


async def call_one(prompt: str, delay: float) -> str:
    # 真实：await AsyncClient().chat()；模拟：await sleep
    if SDK_AVAILABLE and is_ollama_available("llama3.1"):
        resp = await _ollama.AsyncClient().chat(
            model="llama3.1",
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )
        return resp["message"]["content"]
    await asyncio.sleep(delay)
    return fake_delay_reply(prompt)


async def run_concurrent(prompts: list[str]) -> list[str]:
    """并发执行"""
    delay = 1.0
    res = await asyncio.gather(*(call_one(p, delay) for p in prompts))
    return res


async def run_serial(prompts: list[str]) -> list[str]:
    """串行执行"""
    delay = 1.0
    res = []
    for p in prompts:
        res.append(await call_one(p, delay))
    return res


async def main_async():
    prompts = [
        "解释并发",
        "什么是 GIL",
        "异步和同步的区别",
        "什么是协程",
        "事件循环是什么",
    ]

    print(">>> 异步并发演示\n")

    t0 = time.time()
    serial = await run_serial(prompts)
    t_serial = time.time() - t0

    t0 = time.time()
    concurrent = await run_concurrent(prompts)
    t_concurrent = time.time() - t0

    print(f"  串行 5 个请求耗时：{t_serial:.2f}s（逐个等待，总时长 ≈ 5x 单请求）")
    print(f"  并发 5 个请求耗时：{t_concurrent:.2f}s（同时进行，≈ 单请求时长）")
    print(f"  加速比：{t_serial / max(t_concurrent, 0.001):.2f}x")

    print("\n  并发随机回看一个：")
    print(f"    {concurrent[0][:40]}...")

    print("\n  tips: 并发大幅提升吞吐，适合批量/多会话场景。真实环境用 AsyncClient。")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()