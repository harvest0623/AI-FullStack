# -*- coding: utf-8 -*-
"""
Day04 - 03 SDK 嵌入 ollama.embed()

演示：
1. 生成文本向量
2. 计算余弦相似度做语义排序
3. 说明 nomic-embed-text 等嵌入模型
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ollama_util import is_ollama_available, SimOllama

EMBED_MODEL = "nomic-embed-text"

try:
    import ollama as _ollama
    SDK_AVAILABLE = True
except ImportError:
    _ollama = None
    SDK_AVAILABLE = False


def cos_sim(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = (sum(x * x for x in a) ** 0.5) or 1.0
    nb = (sum(x * x for x in b) ** 0.5) or 1.0
    return dot / (na * nb)


def embed_and_search():
    print("=" * 60)
    print("嵌入 + 余弦相似度示例")
    print("=" * 60)

    question = "如何退换货？"
    candidates = [
        "退货流程说明",
        "如何申请退款",
        "今天天气怎么样",
        "衬衫的尺码表",
        "订单取消操作",
    ]

    print(f"\n  查询：{question}")
    print("  候选文档：")
    for i, c in enumerate(candidates, 1):
        print(f"    {i}. {c}")

    if SDK_AVAILABLE and is_ollama_available(EMBED_MODEL):
        q_vec = _ollama.embed(model=EMBED_MODEL, input=question)["embeddings"][0]
        c_vecs = _ollama.embed(model=EMBED_MODEL, input=candidates)["embeddings"]
        sims = [(c, cos_sim(q_vec, v)) for c, v in zip(candidates, c_vecs)]
    else:
        q_vec = SimOllama.embed(EMBED_MODEL, question)
        c_vecs = [SimOllama.embed(EMBED_MODEL, c) for c in candidates]
        sims = [(c, cos_sim(q_vec, v)) for c, v in zip(candidates, c_vecs)]

    print("\n  按相似度排序：")
    for rank, (c, s) in enumerate(sorted(sims, key=lambda x: -x[1]), 1):
        flag = " ★" if rank <= 2 else ""
        print(f"    {rank}. {c:<16} 相似度 {s:.3f}{flag}")

    print("\n  tips: 嵌入用于语义检索（RAG 的基础），Day07 深入。")


def main():
    embed_and_search()


if __name__ == "__main__":
    main()