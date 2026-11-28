# -*- coding: utf-8 -*-
"""
文件用途：Day06 - 02 BM25 关键词检索
演示 BM25Retriever：
  1. 依赖安装说明（rank_bm25）
  2. BM25 关键词检索 vs 向量检索对比
  3. 各自擅长的场景

场景：DataIQ 精确关键词（如编号）命中。
运行：python 02_bm25_retriever.py
依赖：
  pip install llama-index llama-index-embeddings-openai python-dotenv
  pip install rank_bm25
  pip install llama-index-retrievers-bm25   # 若 BM25Retriever 不在 core 中
"""

import os
from dotenv import load_dotenv

load_dotenv()

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding


class HashEmbedding(BaseEmbedding):
    """无 Key 时的降级嵌入模型。"""

    def __init__(self, *args, dim: int = 16, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dim = dim

    def _get_text_embedding(self, text: str) -> list:
        import hashlib

        return [int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16) / (16**8)
                for i in range(self.dim)]

    def _get_query_embedding(self, query: str) -> list:
        return self._get_text_embedding(query)


def load_embed_model():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        from llama_index.embeddings.openai import OpenAIEmbedding
        return OpenAIEmbedding(model="text-embedding-3-small", api_key=api_key)
    print("[embed] 未检测到 API Key，降级使用 HashEmbedding（仅演示）\n")
    return HashEmbedding()


def build_docs() -> list[Document]:
    return [
        Document(text=text, metadata={"doc_id": did, "title": title})
        for did, title, text in [
            ("t01", "工单 TICKET-1001", "工单 TICKET-1001 关闭原因：用户自助解决，未产生费用。"),
            ("t02", "工单 TICKET-1002", "工单 TICKET-1002 已转交技术部门处理，预计三天内答复。"),
            ("t03", "报销流程", "差旅报销请在 OA 系统提交，附件需包含纸质发票扫描件。"),
            ("t04", "年假制度", "员工每年 15 天带薪年假，需在 HR 系统提前申请。"),
        ]
    ]


class BM25RetrieverDemo:
    """BM25 关键词检索演示类。"""

    def __init__(self) -> None:
        Settings.embed_model = load_embed_model()
        self.index = VectorStoreIndex.from_documents(build_docs())

    def build_bm25(self):
        """创建 BM25 检索器，若未安装依赖则返回 None。"""
        try:
            from llama_index.retrievers.bm25 import BM25Retriever
        except Exception:
            try:
                # 部分版本 BM25 在独立的 retrievers 包
                from llama_index_retrievers_bm25 import BM25Retriever
            except Exception as e:
                print(f"[skip] 未安装 BM25 相关依赖：{e}")
                print("       请执行：pip install rank_bm25 llama-index-retrievers-bm25")
                return None
        return BM25Retriever.from_defaults(index=self.index, similarity_top_k=2)

    def demo(self) -> None:
        bm25 = self.build_bm25()
        vector = self.index.as_retriever(similarity_top_k=2)

        queries = ["TICKET-1001 是什么状态？", "报销在哪里提交？"]
        for q in queries:
            print(f"\n===== 查询：{q} =====")
            if bm25 is not None:
                b_nodes = bm25.retrieve(q)
                print(f"  [BM25]   命中：{[n.node.metadata['title'] for n in b_nodes]}")
            v_nodes = vector.retrieve(q)
            print(f"  [向量]   命中：{[n.node.metadata['title'] for n in v_nodes]}")

        print("""
结论观察：
  - 含精确编号「TICKET-1001」的查询，BM25（关键词共现）往往能精准命中对应工单；
  - 向量检索偏语义，对「在哪儿填报销」这类表达泛化更好。
  → 精确词：BM25 强；语义改写：向量强。两者互补正是混合检索（03 号脚本）的价值。""")


if __name__ == "__main__":
    BM25RetrieverDemo().demo()