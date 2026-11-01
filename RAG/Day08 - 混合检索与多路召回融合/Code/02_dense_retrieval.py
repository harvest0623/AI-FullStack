# -*- coding: utf-8 -*-
"""
文件用途：Day08 - 02 稠密检索（向量）
用 FAISS + 嵌入做语义检索，与 BM25 形成对照。

运行：python 02_dense_retrieval.py
依赖：langchain-community faiss-cpu langchain-openai（无 Key 降级）
"""

import hashlib
from langchain_community.vectorstores import FAISS


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


CORPUS = [
    "报销需在出差结束后五个工作日内提交，附有效发票",
    "住宿每日上限五百元，超出部分自理",
    "年假每年十五天，需提前三天在 HR 系统提交",
    "DATA-PRO-2024 产品支持支付宝与云闪付支付",
    "云原生部署，支持 API 与多方对接",
]


def main() -> None:
    emb = get_emb()
    vs = FAISS.from_texts(CORPUS, emb)
    print("=== 稠密检索（FAISS + 向量嵌入）===")
    for query in ["出差住酒店能报多少钱", "产品支持哪些付款", "云闪付账号"]:
        hits = vs.similarity_search_with_score(query, k=1)
        doc, score = hits[0]
        print(f"\n查询『{query}』→ 最佳命中 score={score:.3f}")
        print(f"    {doc.page_content}")
    print("\n稠密偏语义相似；对精确编号(DATA-PRO)可能不如 BM25，两者互补。")


if __name__ == "__main__":
    main()