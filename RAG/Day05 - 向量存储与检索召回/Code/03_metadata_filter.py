# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 03 元数据过滤检索
对比"不加过滤"与"按部门过滤"的检索结果，理解元数据过滤的作用：
  - 让检索只在业务范围内进行（精度）
  - 缩小候选集（性能）
  - 支撑权限/多租户（安全感）

运行：python 03_metadata_filter.py
依赖：langchain-community chromadb langchain-openai（无 Key 降级）
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
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
        return emb, "[OpenAI]"
    except Exception:
        class H:
            def embed_documents(self, texts): return [hash_vec(t) for t in texts]
            def embed_query(self, text): return hash_vec(text)
        return H(), "[降级Hash]"


ITEMS = [
    ("报销住宿每天上限500元，走财务审批", {"dept": "财务部", "level": "内部"}),
    ("财务报销需附发票，5个工作日内提交", {"dept": "财务部", "level": "内部"}),
    ("年假15天，需提前3天HR系统提交", {"dept": "人事部", "level": "内部"}),
    ("员工体检每年春季统一进行", {"dept": "人事部", "level": "公开"}),
    ("产品采用云原生架构部署", {"dept": "技术部", "level": "公开"}),
]


def main() -> None:
    emb, label = build_embeddings()
    print(f"嵌入：{label}\n")

    from langchain_community.vectorstores import Chroma

    vs = Chroma.from_texts(
        [t for t, _ in ITEMS],
        emb,
        metadatas=[m for _, m in ITEMS],
        persist_directory="./chroma_meta",
    )

    q = "报销审批流程"
    print("a) 不加过滤：")
    for doc, score in vs.similarity_search_with_score(q, k=3):
        print(f"   sim≈{score:.4f} [{doc.metadata['dept']}] {doc.page_content}")

    print("\nb) 只看财务部：")
    for doc, score in vs.similarity_search_with_score(q, k=3, filter={"dept": "财务部"}):
        print(f"   sim≈{score:.4f} {doc.page_content}")

    print("\nc) 只看公开文档：")
    for doc, score in vs.similarity_search_with_score(q, k=3, filter={"level": "公开"}):
        print(f"   sim≈{score:.4f} {doc.page_content}")

    print("\n结论：过滤可剔除跨部门/越权的无关结果，提升精度与合规性。")


if __name__ == "__main__":
    main()