# -*- coding: utf-8 -*-
"""
文件用途：Day08 - 04 混合 vs 单一检索对比
在"精确词型"与"语义等价型"两类查询上，对比 单一稠密 / 单一 BM25 / 混合(RRF)
的命中正确性，直观理解为什么混合更鲁棒。

运行：python 04_hybrid_compare.py（纯模拟，无需联网）
"""

CORPUS = [
    "报销需在出差结束后五个工作日内提交，附有效发票",   # 0
    "住宿每日上限五百元，超出部分自理",                 # 1
    "年假每年十五天，需提前三天在 HR 系统提交",          # 2
    "DATA-PRO-2024 产品支持支付宝与云闪付支付",          # 3
    "云原生部署，支持 API 与多方对接",                   # 4
]

# 每个查询的"正确答案"：approximate（语义）或 exact（精确）检索能命中谁
QUERIES = [
    {"q": "产品支持云闪付吗", "answer": 3, "kind": "精确词"},      # 稠密可能抓不住"云闪付"精确词
    {"q": "出差住宿能报销多少", "answer": 1, "kind": "语义等价"},   # BM25 可能抓不住"报销↔住宿"语义
]


def bm25_sim(q, text):
    return sum(1 for c in set(q) if c in text)


def dense_sim(q, text):
    # 简化语义相似：重叠词 + 模糊命中（用同义替换兜底）
    overlap = sum(1 for c in set(q) if c in text)
    hyponyms = {"报销": ["住宿", "出差"], "云闪付": ["支付"]}
    extra = 0
    for hk, hyps in hyponyms.items():
        if hk in q:
            extra += sum(1 for h in hyps if h in text)
    return overlap + 0.5 * extra


def top1(sim_fn, q, exclude=None):
    return max(range(len(CORPUS)), key=lambda i: sim_fn(q, CORPUS[i]) if i != exclude else -1)


def eager_recall_true(ranking, answer, k=3):
    return answer in ranking[:k]


def main() -> None:
    print("=== 混合 vs 单一检索对比（Top-3 命中评估） ===\n")
    for item in QUERIES:
        q, ans, kind = item["q"], item["answer"], item["kind"]
        dense_rank = sorted(range(len(CORPUS)), key=lambda i: dense_sim(q, CORPUS[i]), reverse=True)
        bm25_rank = sorted(range(len(CORPUS)), key=lambda i: bm25_sim(q, CORPUS[i]), reverse=True)
        # 混合：两路共识增强（取两路共同靠前的）
        fused = sorted(range(len(CORPUS)), key=lambda i: dense_sim(q, CORPUS[i]) + bm25_sim(q, CORPUS[i]), reverse=True)

        print(f"[{kind}] {q}  正确: #{ans} {CORPUS[ans][:14]}...")
        print(f"  稠密命中: {eager_recall_true(dense_rank, ans)}   "
              f"BM25命中: {eager_recall_true(bm25_rank, ans)}   "
              f"混合命中: {eager_recall_true(fused, ans)}")
        print("  " + "-" * 40)

    print("\n观察：混合(RRF/加权)通常不会比任一单路更差，且在两类查询上更均衡——")
    print("这正是不容易偏科的工程价值。")


if __name__ == "__main__":
    main()