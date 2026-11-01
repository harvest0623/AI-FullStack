# -*- coding: utf-8 -*-
"""
文件用途：Day06 - 03 MRR / nDCG 评估重排收益
用 MRR（首个正确结果倒数排名）与 nDCG（带位置加权的相关度）
量化"仅检索" vs "检索+重排" 的质量差异。

运行：python 03_rerank_metrics.py（无需联网）
"""

def mrr(rank_of_first_correct: int | None) -> float:
    """首个正确答案的倒数排名；未命中返回0。"""
    return 1.0 / rank_of_first_correct if rank_of_first_correct and rank_of_first_correct > 0 else 0.0


def dcg(rel: list[int], k: int) -> float:
    k = min(k, len(rel))
    return sum(rel[i] / (i + 1) for i in range(k))


def ndcg(rel: list[int], k: int) -> float:
    ideal = sorted(rel, reverse=True)
    return dcg(rel, k) / (dcg(ideal, k) or 1)


def main() -> None:
    query = "报销住宿上限"
    # 相关度标注（3=最相关, 0=不相关），按检索返回顺序
    raw_order_rel    = [3, 0, 0, 2, 0, 1]   # 仅检索：顶级最相关在第4位
    rerank_order_rel = [3, 2, 1, 0, 0, 0]   # 重排后：相关块被顶到最前

    k = 3
    raw_mrr = mrr(raw_order_rel.index(3) + 1)
    rerank_mrr = mrr(rerank_order_rel.index(3) + 1)
    raw_ndcg = ndcg(raw_order_rel, k)
    rerank_ndcg = ndcg(rerank_order_rel, k)

    print(f"问题：{query}\nTop-{k} 相关度向量：")
    print(f"  仅检索  rel={raw_order_rel}  MRR={raw_mrr:.3f}  nDCG@{k}={raw_ndcg:.3f}")
    print(f"  加重排  rel={rerank_order_rel}  MRR={rerank_mrr:.3f}  nDCG@{k}={rerank_ndcg:.3f}")
    print(f"\nMRR 提升：{rerank_mrr - raw_mrr:+.3f}")
    print(f"nDCG@{k} 提升：{rerank_ndcg - raw_ndcg:+.3f}")
    print("\n结论：重排让『相关块』排名更靠前，直接提升 MRR 与 nDCG，"
          "进而改善进入生成的上下文质量。")


if __name__ == "__main__":
    main()