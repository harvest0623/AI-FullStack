# -*- coding: utf-8 -*-
"""
文件用途：Day04 - 03 批量嵌入与简单缓存
演示 embed_documents 批量调用，并用一个内存 dict 做嵌入缓存：
命中缓存的文本不再重复计算，节省成本与时间。

运行：python 03_batch_cache.py
依赖：langchain-openai（OPENAI_API_KEY），无 Key 时降级本地哈希
"""

import os
import math
import hashlib
from dotenv import load_dotenv

load_dotenv()


def hash_vec(text: str, dim: int = 16) -> list[float]:
    out = []
    for i in range(dim):
        h = int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16)
        out.append((h % 2000) / 1000.0 - 1.0)
    return out


def cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb or 1)


class EmbeddingWithCache:
    def __init__(self, backend):
        self.backend = backend
        self.cache: dict[str, list[float]] = {}
        self.hits = 0
        self.misses = 0

    def embed_documents(self, texts):
        result, to_compute = [], []
        for t in texts:
            if t in self.cache:
                result.append(self.cache[t]); self.hits += 1
            else:
                to_compute.append(t)
        if to_compute:
            # 一次批量请求所有未命中文本（后端支持 embed_documents 则批量，否则逐个）
            if hasattr(self.backend, "embed_documents"):
                new_vecs = self.backend.embed_documents(to_compute)
            else:
                new_vecs = [self.backend.embed_query(t) for t in to_compute]
            for t, v in zip(to_compute, new_vecs):
                self.cache[t] = v
                result.append(v)
            self.misses += len(to_compute)
        return result


def build_backend():
    try:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")
    except Exception:
        return type("HashBackend", (), {
            "embed_documents": lambda self, texts: [hash_vec(t) for t in texts],
            "embed_query": lambda self, text: hash_vec(text),
        })()


def main() -> None:
    docs = ["报销住宿上限500元", "年假15天", "报销住宿上限500元", "支付支持支付宝", "年假15天"]
    backend = build_backend()
    emb = EmbeddingWithCache(backend)

    vecs = emb.embed_documents(docs)
    print(f"首次批量：misses={emb.misses} hits={emb.hits}")
    qvec = backend.embed_query("报销住宿标准")
    print(f"向量维度：{len(qvec)}")
    print("\n命中情况（重复文本应走缓存）：")
    for t, v in zip(docs, vecs):
        print(f"  sim={cos(qvec, v):+.4f}  {t}")
    print("\n说明：缓存命中避免重复计算；实际生产可用磁盘/Redis 缓存（Day11）。")


if __name__ == "__main__":
    main()