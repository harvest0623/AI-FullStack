# -*- coding: utf-8 -*-
"""
文件用途：Day04 - 01 嵌入基础与余弦相似度
演示嵌入模型调用、embed_documents vs embed_query 的区别、
以及余弦相似度的计算与含义。

运行：python 01_embedding_basics.py
依赖：langchain-openai（配置 OPENAI_API_KEY）或自动降级本地哈希向量
"""

import os
import math
from dotenv import load_dotenv

load_dotenv()


def cos_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb or 1)


def hash_vec(text: str, dim: int = 16) -> list[float]:
    import hashlib
    out = []
    for i in range(dim):
        h = int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16)
        out.append((h % 2000) / 1000.0 - 1.0)
    return out


def main() -> None:
    texts = [
        "报销住宿上限是多少",
        "出差住宿能报销多少钱",
        "年假一共有几天",
        "怎么申请带薪年假",
    ]
    q = "员工出差住宿报销标准"

    try:
        from langchain_openai import OpenAIEmbeddings
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
        vecs = emb.embed_documents(texts)
        qvec = emb.embed_query(q)
        label = "[OpenAIEmbeddings]"
    except Exception:
        emb = None
        vecs = [hash_vec(t) for t in texts]
        qvec = hash_vec(q)
        label = "[降级 HashEmbedding]（仅供参考流程，无真实语义）"

    print(f"{label} 问题向量维度：{len(qvec)}\n")
    print("=" * 55)
    print("查询与各文档的余弦相似度（doc == query 用同模型）：")
    for t, v in zip(texts, vecs):
        print(f"  sim={cos_sim(qvec, v):+.4f}  {t}")
    print("=" * 55)
    if emb is not None:
        print("可见语义相关('报销住宿')比语义无关('年假')得分更高。")
    else:
        print("已降级为哈希向量，仅演示流程；配置 OPENAI_API_KEY 后见真实语义。")


if __name__ == "__main__":
    main()