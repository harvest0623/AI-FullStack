# -*- coding: utf-8 -*-
"""
文件用途：Day10 - 01 检索层指标
实现并演示 Recall@K / Precision@K / MRR / nDCG。

运行：python 01_retrieval_metrics.py（无需联网）
"""

def recall_at_k(hits, relevant, k):
    top = set(hits[:k])
    return len(top & relevant) / len(relevant) if relevant else 1.0


def precision_at_k(hits, relevant, k):
    top = set(hits[:k]) if len(hits) >= k else set(hits)
    return len(top & relevant) / k


def mrr(hits, relevant):
    for i, h in enumerate(hits, 1):
        if h in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(hits, relevant, k):
    def dcg(rel):
        return sum(r / (i + 1) for i, r in enumerate(rel[:k]))
    rel = [1 if h in relevant else 0 for h in hits]
    ideal = sorted(rel, reverse=True)
    return dcg(rel) / (dcg(ideal) or 1)


def main() -> None:
    relevant = {"b", "d"}          # 真相关文档
    hits = ["a", "b", "c", "d", "e"]  # 检索返回顺序
    k = 3

    print(f"真相关: {relevant}")
    print(f"检索返回: {hits}")
    print(f"\nRecall@3   = {recall_at_k(hits, relevant, k):.3f}")
    print(f"Precision@3= {precision_at_k(hits, relevant, k):.3f}")
    print(f"MRR        = {mrr(hits, relevant):.3f}")
    print(f"nDCG@3     = {ndcg_at_k(hits, relevant, k):.3f}")
    print("\n观察：'b'排第2使 MRR=0.5；nDCG 依据排序位置加权，'d'更靠后被适度惩罚。")


if __name__ == "__main__":
    main()