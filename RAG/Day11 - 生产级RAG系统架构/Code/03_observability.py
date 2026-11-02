# -*- coding: utf-8 -*-
"""
文件用途：Day11 - 03 可观测性骨架
展示如何在 RAG 管道埋点记录"检索块、分数、token、延迟"，便于后续接
LangSmith / Langfuse / Phoenix 等追踪与监控。

运行：python 03_observability.py（纯本地，无需联网）
"""

import time
import json
from collections import deque


class Observability:
    """极简可观测性：记录每次 query 的关键维度（真实中对接 Langfuse/Phoenix）。"""
    def __init__(self):
        self.events = deque(maxlen=100)

    def log(self, **kw):
        kw["ts"] = time.strftime("%H:%M:%S")
        self.events.append(kw)
        print("  [OB] " + json.dumps(kw, ensure_ascii=False))

    def summary(self):
        return {
            "total": len(self.events),
            "avg_latency_ms": sum(e["latency_ms"] for e in self.events) / max(len(self.events), 1),
            "avg_tokens": sum(e["tokens"] for e in self.events) / max(len(self.events), 1),
        }


def rag_query(obs: Observability, q: str, retriever, llm_cost_per_call: int = 120, delay: float = 0.1):
    t0 = time.time()
    # 检索（模拟）
    hits = retriever(q)
    retr_ms = (time.time() - t0) * 1000
    # 生成（模拟）— 记 tokens
    time.sleep(delay)
    total_ms = (time.time() - t0) * 1000
    obs.log(question=q, hits=len(hits), retrieved=[h[:12] for h in hits],
            latency_ms=round(total_ms, 1), tokens=llm_cost_per_call)
    return hits[0]


def main() -> None:
    obs = Observability()
    kb = ["报销需5个工作日内提交发票", "住宿每日上限500元", "年假每年15天"]
    retriever = lambda q: sorted(kb, key=lambda t: sum(c in t for c in set(q)), reverse=True)[:2]

    print("=== 带观测的 RAG 请求 ===\n")
    for q in ["住宿报销", "年假几天", "住宿报销", "怎么报销"]:
        rag_query(obs, q, retriever)
    print("\n=== 汇总指标 ===")
    for k, v in obs.summary().items():
        print(f"  {k}: {v}")
    print("\n生产：接入 Langfuse/Phoenix 后，这些事件进入 trace 页可检索/可视化。")


if __name__ == "__main__":
    main()