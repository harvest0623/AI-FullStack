# -*- coding: utf-8 -*-
"""
文件用途：Day04 - 02 嵌入模型对比
对同一组中文句称，分别用不同嵌入模型计算相似度并展示维度差异。
便于理解"模型选型 × 维度 × 相关性"的权衡。

运行：python 02_model_compare.py
依赖：langchain-openai（OPENAI_API_KEY）与可选 sentence-transformers（本地）
"""

import os
from dotenv import load_dotenv

load_dotenv()

PAIRS = [
    ("报销住宿上限", "出差住宿能报销多少", True),   # 应相似
    ("报销住宿上限", "年假怎么申请", False),        # 应不相关
]


def cos(a, b):
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb or 1)


def run_openai():
    from langchain_openai import OpenAIEmbeddings
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    print("模型：text-embedding-3-small")
    vecs = emb.embed_documents([p[0] for p in PAIRS]*0 or [x[0] for x in PAIRS] + [x[1] for x in PAIRS])
    d = len(vecs[0])
    for (a, b, expect), va, vb in zip(PAIRS, vecs[:2], vecs[2:]):
        print(f"  sim={cos(va, vb):+.4f}  预期{'相似' if expect else '不相关'}  <{a} | {b}>")
    return d


def run_local():
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
        dim = None
        print("模型：BAAI/bge-small-zh-v1.5（本地）")
        for (a, b, expect) in PAIRS:
            # bge 查询侧需加指令前缀以提升检索效果
            q = "为这个句子生成表示以用于检索相关文章：" + a
            va = model.encode(q)
            vb = model.encode(b)
            dim = len(va)
            print(f"  sim={cos(va, vb):+.4f}  预期{'相似' if expect else '不相关'}  <{a} | {b}>")
        return dim
    except Exception as e:
        print(f"  [!] 本地模型不可用：{e}")
        return None


def main() -> None:
    print("===== 嵌入模型对比 =====")
    print("OpenAI API：" if os.getenv("OPENAI_API_KEY") else "OpenAI API（未配置Key，跳过）")
    if os.getenv("OPENAI_API_KEY"):
        d = run_openai()
        print(f"维度：{d}")
    print("\n本地 bge（可选）：")
    d = run_local()
    if d:
        print(f"维度：{d}")
    print("\n注意：不同模型的向量不可互相比较，需统一在检索环境中使用同一模型。")


if __name__ == "__main__":
    main()