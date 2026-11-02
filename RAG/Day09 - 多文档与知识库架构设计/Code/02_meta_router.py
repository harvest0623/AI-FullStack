# -*- coding: utf-8 -*-
"""
文件用途：Day09 - 02 元数据过滤路由
用 metadata 过滤实现"按部门/类型/密级"精准检索，作为单大库 + 强过滤的架构演示。

运行：python 02_meta_router.py
依赖：langchain-community chromadb langchain-openai（可降级）
"""

import os
import hashlib
from dotenv import load_dotenv

load_dotenv()


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


ITEMS = [
    ("报销需5个工作日内提交发票", {"dept": "财务", "doc_type": "制度", "level": "内部"}),
    ("住宿每日上限500元", {"dept": "财务", "doc_type": "制度", "level": "内部"}),
    ("年假15天需提前3天申请", {"dept": "人事", "doc_type": "制度", "level": "内部"}),
    ("产品支持云闪付支付", {"dept": "产品", "doc_type": "手册", "level": "公开"}),
    ("产品为云原生架构", {"dept": "产品", "doc_type": "手册", "level": "公开"}),
]


def main() -> None:
    from langchain_community.vectorstores import Chroma
    emb = get_emb()
    vs = Chroma.from_texts([t for t, _ in ITEMS], emb, metadatas=[m for _, m in ITEMS], persist_directory="./chroma_filt")

    scenarios = [
        ("只看财务部制度", {"dept": "财务", "doc_type": "制度"}),
        ("只看公开的手册", {"level": "公开", "doc_type": "手册"}),
        ("只看人事（模拟权限）", {"dept": "人事"}),
    ]
    for label, flt in scenarios:
        print(f"\n[{label}] filter={flt}")
        hits = vs.similarity_search("报销 or 产品 或 年假", k=3, filter=flt)
        for d in hits:
            print("   -", d.page_content[:26], "|", d.metadata)


if __name__ == "__main__":
    main()