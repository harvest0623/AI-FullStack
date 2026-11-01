# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 02 FAISS 向量存储
用 FAISS（内存近似最近邻库）构建索引、检索、保存/加载。
FAISS 轻量高效，适合单机大批量向量集。

运行：python 02_faiss_store.py
依赖：langchain-community faiss-cpu langchain-openai（无 Key 降级）
"""

import os
import hashlib
from dotenv import load_dotenv

load_dotenv()


def hash_vec(text: str, dim: int = 16) -> list[float]:
    out = []
    for i in range(dim):
        h = int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16)
        out.append((h % 2000) / 1000.0 - 1.0)
    return out


def build_embeddings():
    try:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small"), "[OpenAI]"
    except Exception:
        class H:
            def embed_documents(self, texts): return [hash_vec(t) for t in texts]
            def embed_query(self, text): return hash_vec(text)
        return H(), "[降级Hash]"


DOCS_TEXT = [
    "报销住宿每天上限500元",
    "差旅需5个工作日内提交申请",
    "年假每年15天，入职满1年可领取",
    "支持支付宝、微信、对公转账",
    "网络安全培训每季度一次",
]


def main() -> None:
    emb, label = build_embeddings()
    print(f"嵌入：{label}\n")

    from langchain_community.vectorstores import FAISS

    # 构建 + 检索
    vs = FAISS.from_texts(DOCS_TEXT, emb)
    print(f"[FAISS] 构建完成，向量集大小={len(DOCS_TEXT)}")

    hits = vs.similarity_search_with_score("年假有几天", k=2)
    print("[检索] 前 2：")
    for doc, score in hits:
        print(f"   dist={score:.4f} {doc.page_content}")
    print("（注：FAISS 默认 L2 距离，越小越相关）")

    # 保存 / 加载
    vs.save_local("./faiss_index")
    loaded = FAISS.load_local("./faiss_index", emb, allow_dangerous_deserialization=True)
    loaded_hits = loaded.similarity_search("怎么报销", k=1)
    print("[保存/加载] 重新加载后检索：", loaded_hits[0].page_content)


if __name__ == "__main__":
    main()