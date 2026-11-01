# -*- coding: utf-8 -*-
"""
文件用途：Day08 - 03 多路召回与 RRF 融合
把"稠密检索"与"BM25 稀疏检索"两路结果用 RRF 融合成统一排序。

运行：python 03_hybrid_fusion.py
依赖：rank_bm25; langchain-community faiss-cpu langchain-openai（可用降级）
"""

import hashlib
from rank_bm25 import BM25Okapi

CORPUS = [
    "报销需在出差结束后五个工作日内提交，附有效发票",
    "住宿每日上限五百元，超出部分自理",
    "年假每年十五天，需提前三天在 HR 系统提交",
    "DATA-PRO-2024 产品支持支付宝与云闪付支付",
    "云原生部署，支持 API 与多方对接",
]


def hash_vec(text: str, dim: int = 16) -> list[float]:
    out = []
    for i in range(dim):
        h = int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16)
        out.append((h % 2000) / 1000.0 - 1.0)
    return out


def get_emb():
    try:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")
    except Exception:
        class H:
            def embed_documents(self, texts): return [hash_vec(t) for t in texts]
            def embed_query(self, text): return hash_vec(text)
        return H()


def dense_rank(query) -> list[int]:
    from langchain_community.vectorstores import FAISS
    vs = FAISS.from_texts(CORPUS, get_emb())
    hits = vs.similarity_search_with_score(query, k=5)
    # 顺序 = 排名：列表头最相关
    return [CORPUS.index(h.page_content) for h, _ in hits]


def bm25_rank(query) -> list[int]:
    bm25 = BM25Okapi([list(d) for d in CORPUS])
    scores = bm25.get_scores(list(query))
    return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)


def rrf(rankings: list[list[int]], k: int = 60) -> list[int]:
    score_map = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            score_map[doc] = score_map.get(doc, 0) + 1.0 / (k + rank + 1)
    return sorted(score_map, key=lambda d: score_map[d], reverse=True)


def main() -> None:
    query = "DATA-PRO2024 产品支持云闪付吗"
    print("查询：", query, "\n")
    dense = dense_rank(query)
    sparse = bm25_rank(query)
    print("稠密路(top5):", [CORPUS[i][:12] for i in dense])
    print("稀疏路(top5):", [CORPUS[i][:12] for i in sparse])
    fused = rrf([dense, sparse], k=60)
    print("\nRRF 融合结果：")
    for i, d in enumerate(fused[:4], 1):
        print(f"  {i}. {CORPUS[d]}")

    print("\n结论：RRF 只看排名，融合两路共识，避免了单路偏科。")


if __name__ == "__main__":
    main()