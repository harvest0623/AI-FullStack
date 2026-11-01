# -*- coding: utf-8 -*-
"""
文件用途：Day08 - 01 BM25 稀疏检索
用 rank_bm25 做基于词频/逆文档频率的关键词检索，验证对精确术语的高命中。

运行：python 01_bm25_retrieval.py
依赖：rank_bm25
"""

from rank_bm25 import BM25Okapi

CORPUS = [
    "报销需在出差结束后五个工作日内提交，附有效发票",
    "住宿每日上限五百元，超出部分自理",
    "年假每年十五天，需提前三天在 HR 系统提交",
    "DATA-PRO-2024 产品支持支付宝与云闪付支付",
    "云原生部署，支持 API 与多方对接",
]


def main() -> None:
    tokenized = [list(doc) for doc in CORPUS]  # 中文按字符简单分词（近似）
    bm25 = BM25Okapi(tokenized)

    print("=== BM25 稀疏检索 ===")
    for query in ["DATA-PRO 支付", "住宿上限", "云闪付怎么用"]:
        q_tokens = list(query)
        scores = bm25.get_scores(q_tokens)
        top = max(range(len(scores)), key=lambda i: scores[i])
        print(f"\n查询『{query}』→ 最佳命中#{top+1} score={scores[top]:.3f}")
        print(f"    {CORPUS[top]}")
    print("\n可见：BM25 对精确专有名词/编号（如 DATA-PRO、云闪付）命中极佳，" 
          "这正是稠密检索常覆盖不到的盲区。")


if __name__ == "__main__":
    main()