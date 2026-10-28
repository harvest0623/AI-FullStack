# -*- coding: utf-8 -*-
"""
Day10 - 04 性能基准

模拟对客服接口的多次请求，统计：
- 单请求平均延迟（ms）
- 吞吐 QPS（每秒处理数）
- 对比不同并发下表现，得出调优结论

离线可运行：用 SimOllama 的 sleep 模拟推理耗时。
有真实 Ollama 时可换成真实调用压测。
"""

import time
import threading
import queue

import ollama_util
from ollama_util import is_ollama_available


def simulate_inference() -> str:
    """模拟一次推理：真实请求或模拟耗时"""
    if is_ollama_available():
        reply = ollama_util.real_chat(
            [{"role": "user", "content": "用一句话介绍退款政策"}],
            {"num_predict": 20})
        return reply
    time.sleep(0.05)  # 模拟推理延迟 50ms
    return "[模拟回复]"


PERF_N = 20  # 每个并发档位的请求数


def bench(concurrency: int) -> tuple[float, float]:
    """跑一批请求，返回 (平均延迟 ms, QPS)"""
    q = queue.Queue()
    for i in range(PERF_N):
        q.put(i)

    results = []
    start = time.time()

    def worker():
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                return
            t0 = time.time()
            simulate_inference()
            results.append(time.time() - t0)

    threads = [threading.Thread(target=worker) for _ in range(concurrency)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    elapsed = time.time() - start
    avg_ms = (sum(results) / len(results)) * 1000 if results else 0
    qps = PERF_N / elapsed if elapsed > 0 else 0
    return avg_ms, qps


def main():
    print(">> 性能基准\n")
    print(f"并发档位: 1 / 4 / 8，每档 {PERF_N} 个请求\n")
    print(f"{'并发数':<6}{'平均延迟(ms)':<16}{'QPS':<10}")
    print("-" * 34)
    for con in [1, 4, 8]:
        avg, qps = bench(con)
        print(f"{con:<6}{avg:<16.1f}{qps:<10.1f}")

    print("\n结论：")
    print("  - 延迟变高/flux命中 -> 并发有限（受 num_ctx、显存、模型大小影响）")
    print("  - 调优方向：拉大 num_ctx、降并发、用更小/量化模型、升级 GPU")
    print("  - 真实场景需结合 Ollama 的请求队列与超时策略")


if __name__ == "__main__":
    main()