# -*- coding: utf-8 -*-
"""
文件用途：Day09 - 01 多索引隔离
为不同文档类型分别建立索引，独立检索，展示"小而准"的组织方式。

运行：python 01_multi_index.py
依赖：langchain-community faiss-cpu langchain-openai（可降级）
"""

import os
import hashlib
from langchain_community.vectorstores import FAISS

# 三个子文档空间
SPACES = {
    "财务制度": [
        "报销需在出差结束后5个工作日内提交，附发票",
        "住宿每日上限500元，超出部分自理",
    ],
    "人事制度": [
        "年假每年15天，需提前3天在HR系统提交",
        "病假需提供医院证明，不计入年假",
    ],
    "产品资料": [
        "DATA-PRO-2024 支持支付宝与云闪付",
        "产品为云原生架构，支持API对接",
    ],
}


def hash_vec(text: str, dim: int = 16) -> list[float]:
    return [(int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16) % 2000)/1000.0 - 1.0 for i in range(dim)]


def get_emb():
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")
    class H:
        def embed_documents(self, texts): return [hash_vec(t) for t in texts]
        def embed_query(self, text): return hash_vec(text)
    return H()


def main() -> None:
    emb = get_emb()
    indexes = {name: FAISS.from_texts(texts, emb) for name, texts in SPACES.items()}
    print("各子库规模：", {k: len(v) for k, v in SPACES.items()})

    for q in ["住宿报销上限", "年假有几天", "云闪付支付"]:
        print(f"\n问题『{q}』：")
        for name, vs in indexes.items():
            try:
                top = vs.similarity_search(q, k=1)[0]
                print(f"  [{name}] {top.page_content[:30]}")
            except Exception:
                print(f"  [{name}] (空)")
    print("\n提示：多索引让每个库更聚焦；实际中配合 Router（Day09-04）按需调度。")


if __name__ == "__main__":
    main()