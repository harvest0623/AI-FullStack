# -*- coding: utf-8 -*-
"""
文件用途：Day12 - 03 检索与生成整合
把"混合检索 + 重排 + 生成"整合为 DataIQ 的查询引擎。
无 LLM/K 时演示"检索上下文"构建；配置 Key 时真实回答。

运行：python 03_retriever_engine.py
"""

import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

DOCS = [
    "报销需在出差结束后5个工作日内提交申请，附有效发票。",
    "住宿每日上限500元，超出部分自理。",
    "住宿如需升级需提前向经理申请获批。",
    "年假每年15天，需提前3天在HR系统提交，不允许跨年结转。",
    "DATA-PRO-2024 产品支持支付宝与云闪付支付。",
]


def hash_vec(text: str, dim: int = 16):
    return [(int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16) % 2000)/1000.0 - 1.0 for i in range(dim)]


def get_emb():
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")
    class H:
        def embed_documents(self, texts): return [hash_vec(t) for t in texts]
        def embed_query(self, text): return hash_vec(text)
    return H()


def bm25_rank(query):
    qset = set(query)
    return sorted(range(len(DOCS)), key=lambda i: sum(c in DOCS[i] for c in qset), reverse=True)


def rrf(rankings, k=60):
    sm = {}
    for rk in rankings:
        for rank, d in enumerate(rk):
            sm[d] = sm.get(d, 0) + 1.0/(k + rank + 1)
    return sorted(sm, key=lambda d: sm[d], reverse=True)


def query_engine(question, top=3):
    emb = get_emb()
    from langchain_community.vectorstores import FAISS
    vs = FAISS.from_texts(DOCS, emb)
    dense = [i for i, _ in vs.similarity_search_with_score(question, k=5)]
    sparse = bm25_rank(question)
    fused = rrf([dense, sparse])
    # 简单重排：命中的再提权（真实用 CrossEncoder）
    top_ix = fused[:top]
    return [DOCS[i] for i in top_ix]


def generate(question):
    context = "\n".join(f"- {t}" for t in query_engine(question))
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "你是DataIQ知识库助手，只依据资料回答。"},
                    {"role": "user", "content": f"资料：\n{context}\n问题：{question}"},
                ])
            return resp.choices[0].message.content
        except Exception as e:
            return f"(升降级生成占位: {e})"
    return f"（无Key·仅演示）检索到上下文：\n{context}"


def main() -> None:
    q = "住宿升级要提前申请吗？"
    print("问题：", q)
    print("\n召回（混合检索+重排）：")
    for i, t in enumerate(query_engine(q), 1):
        print(f"  {i}. {t}")
    print("\n生成：")
    print(generate(q))


if __name__ == "__main__":
    main()