# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 04 索引算法对比（Flat vs HNSW）
用纯向量数值模拟"暴力全量比较"与"HNSW 近似近邻"在
延迟与召回率上的差异，帮助理解生产索引选型的权衡。

运行：python 04_index_metrics.py（无需联网）
"""

import random
import math
import time


def gen_vectors(n: int, dim: int = 64) -> list[list[float]]:
    return [[random.uniform(-1, 1) for _ in range(dim)] for _ in range(n)]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def flat_search(query, db):
    """暴力全量比较（精确）。"""
    best = max(range(len(db)), key=lambda i: dot(query, db[i]))
    return best, len(db)


def hnsw_search_approx(query, db, buckets=32):
    """
    极简 HNSW 模拟：先随机把向量分桶，只在与查询最近的桶里比较。
    牺牲一点召回换取更少比较数（真正的 HNSW 用图结构，此处仅演示权衡）。
    """
    bucket_size = max(1, len(db) // buckets)
    buckets_ = [db[i:i + bucket_size] for i in range(0, len(db), bucket_size)]
    # 用桶内首个向量的方向粗筛
    scores = []
    for b in buckets_:
        anchor = b[0]
        scores.append(dot(query, anchor))
    best_bucket_idx = max(range(len(scores)), key=lambda i: scores[i])
    cand = buckets_[best_bucket_idx]
    best = max(range(len(cand)), key=lambda i: dot(query, cand[i]))
    return best, len(cand)


def main() -> None:
    db = gen_vectors(100_000, dim=64)
    queries = gen_vectors(50, dim=64)

    # 基准：用 Flat 每个查询的结果作为"真值"
    flat_tops = []
    t0 = time.perf_counter()
    for q in queries:
        peri, _ = flat_search(q, db)
        flat_tops.append(peri)
    flat_cost = time.perf_counter() - t0

    hnsw_correct = 0
    t0 = time.perf_counter()
    for i, q in enumerate(queries):
        bi, _ = hnsw_search_approx(q, db)
        if bi == flat_tops[i]:
            hnsw_correct += 1
    hnsw_cost = time.perf_counter() - t0

    recall = hnsw_correct / len(queries)

    print(f"向量数：{len(db):,}  维度：64  查询：{len(queries)}\n")
    print(f"[Flat ] 耗时 {flat_cost*1000:8.1f} ms   比较数/查询={len(db)}（精确）")
    print(f"[HNSW] 耗时 {hnsw_cost*1000:8.1f} ms   召回率≈{recall*100:.1f}%（近似）")
    print(f"\n耗时比：{flat_cost/hnsw_cost:.1f}x 更快（近似换性能）")
    print("真实 HNSW 用分层图，召回率可更高；此例仅演示『速度↔召回』的权衡思维。")


if __name__ == "__main__":
    main()