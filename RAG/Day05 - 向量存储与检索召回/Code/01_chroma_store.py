# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 01 Chroma 向量存储 CRUD
演示用 Chroma 完成建库、检索、增、删、持久化。

运行：python 01_chroma_store.py
依赖：langchain-community chromadb langchain-openai（OPENAI_API_KEY，无 Key 降级）
"""

import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

PERSIST = "./chroma_store"


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


DOCS = [
    ("报销住宿每天上限500元", {"dept": "财务部", "doc": "报销规则"}),
    ("差旅需5个工作日内提交申请", {"dept": "财务部", "doc": "报销规则"}),
    ("年假每年15天，入职满1年可领取", {"dept": "人事部", "doc": "年假制度"}),
    ("支持支付宝、微信、对公转账", {"dept": "财务部", "doc": "支付规则"}),
]


def main() -> None:
    emb, label = build_embeddings()
    print(f"嵌入：{label}\n")

    from langchain_community.vectorstores import Chroma

    # 建库 / 填充
    vs = Chroma.from_texts(
        [t for t, _ in DOCS],
        emb,
        metadatas=[m for _, m in DOCS],
        persist_directory=PERSIST,
    )
    print(f"[建库] 写入 {len(DOCS)} 个块到 {PERSIST}")

    # 查
    hits = vs.similarity_search_with_score("出差住宿能报多少", k=2)
    print("[检索] similarity_search_with_score：")
    for doc, score in hits:
        print(f"   sim≈{score:.4f} {doc.page_content} ({doc.metadata})")

    # 增
    vs.add_texts(["网络安全培训每季度一次"], metadatas=[{"dept": "技术部", "doc": "安全手册"}])
    print("[新增] 加入安全块后总数：", len(vs._collection.get()["ids"]))

    # 删
    vs.add_texts(["待删除临时内容"], metadatas=[{"dept": "临时"}])
    all_ids = vs._collection.get()["ids"]
    vs.delete([all_ids[-1]])
    print("[删除] 已删除末尾临时块，剩余：", len(vs._collection.get()["ids"]))

    vs.persist()
    print("[持久化] 完成，目录已保存")


if __name__ == "__main__":
    main()