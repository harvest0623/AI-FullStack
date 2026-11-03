# -*- coding: utf-8 -*-
"""
文件用途：Day12 - 02 数据管道
整合"加载→切块→嵌入→入库"，把 DataIQ 制度文档做成可查询索引。
返回 VectorStore 供 03 检索使用。

运行：python 02_data_pipeline.py
依赖：langchain-community faiss-cpu langchain-openai（可降级）
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


def load_docs():
    # 真实项目用 SimpleDirectoryReader / TextLoader 读 data/；此处内置模拟
    return [
        {"text": "报销需在出差结束后5个工作日内提交申请，附有效发票。", "meta": {"dept": "财务", "doc": "报销"}},
        {"text": "住宿每日上限500元，超出部分自理。", "meta": {"dept": "财务", "doc": "报销"}},
        {"text": "年假每年15天，需提前3天在HR系统提交，不允许跨年结转。", "meta": {"dept": "人事", "doc": "年假"}},
        {"text": "DATA-PRO-2024 产品支持支付宝与云闪付支付。", "meta": {"dept": "产品", "doc": "手册"}},
    ]


def main() -> None:
    docs = load_docs()
    print(f"[load] {len(docs)} 篇文档")

    # 切块（此处每篇一篇小文本不再拆；真实中 RecursiveCharacterTextSplitter）
    texts = [d["text"] for d in docs]
    metadatas = [d["meta"] for d in docs]
    print(f"[chunk] 得到 {len(texts)} 个块")

    emb = get_emb()
    from langchain_community.vectorstores import FAISS
    index = FAISS.from_texts(texts, emb, metadatas=metadatas)
    print(f"[embed+store] 已入库 {len(index.index_to_docstore_id or {}) or len(texts)} 个向量")

    # 冒烟：检索验证
    hits = index.similarity_search("住宿报销", k=2)
    print("\n[smoke] 检索验证：")
    for d in hits:
        print("   -", d.page_content, "|", d.metadata)

    index.save_local("./dataiq_index")
    print("\n已持久化到 ./dataiq_index")


if __name__ == "__main__":
    main()