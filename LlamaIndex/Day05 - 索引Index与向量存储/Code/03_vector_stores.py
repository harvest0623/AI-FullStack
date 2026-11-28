# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 03 多种向量存储
演示如何切换底层向量存储：
  1. SimpleVectorStore（内存，默认）
  2. ChromaVectorStore（本地持久化）
  3. 对比不同向量存储的创建方式与使用差异

场景：DataIQ 从内存向量库平滑迁移到本地 Chroma。
运行：python 03_vector_stores.py
依赖：llama-index llama-index-embeddings-openai llama-index-vector-stores-chroma
      chromadb python-dotenv
"""

import os
from dotenv import load_dotenv

load_dotenv()

from llama_index.core import (
    Document,
    Settings,
    StorageContext,
    VectorStoreIndex,
    vector_stores,
)
from llama_index.core.embeddings import BaseEmbedding

CHROMA_PATH = "./chroma_db"
CHROMA_COLLECTION = "dataiq"


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
    print("[embed] 未检测到 API Key，降级使用 HashEmbedding（仅演示）")
    return HashEmbedding()


def build_docs() -> list[Document]:
    return [
        Document(text=text, metadata={"doc_id": did, "title": title})
        for did, title, text in [
            ("p1", "年假制度", "DataIQ 员工每年拥有 15 天带薪年假，入职满一年即可全额领取。"),
            ("p2", "出差报销", "差旅报销需 5 个工作日内提交，住宿每天上限 500 元。"),
        ]
    ]


class VectorStoreCompare:
    """多种向量存储对比演示类。"""

    def __init__(self) -> None:
        Settings.embed_model = load_embed_model()

    def build_with_simple_vector_store(self) -> VectorStoreIndex:
        """方式一：内存 SimpleVectorStore（默认）。"""
        print("\n===== SimpleVectorStore（内存，默认）=====")
        # 显式指定 vector_store（默认就是 SimpleVectorStore）
        sc = StorageContext.from_defaults(vector_store=vector_stores.SimpleVectorStore())
        index = VectorStoreIndex.from_documents(build_docs(), storage_context=sc)
        print(f"向量存储类型：{type(index.vector_store).__name__}")
        print("说明：数据仅存于内存，进程退出即丢失（除非 persist 到磁盘）")
        return index

    def build_with_chroma(self) -> VectorStoreIndex:
        """方式二：ChromaVectorStore（本地持久化）。"""
        print("\n===== ChromaVectorStore（本地持久化）=====")
        try:
            import chromadb
            from llama_index.vector_stores.chroma import ChromaVectorStore
        except ImportError as e:
            print("[skip] 未安装 chromadb / llama-index-vector-stores-chroma，跳过。")
            print(f"       请执行：pip install chromadb llama-index-vector-stores-chroma")
            return None

        chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        # 删除旧集合同名数据，保证演示幂等（可选）
        try:
            chroma_client.delete_collection(CHROMA_COLLECTION)
        except Exception:
            pass
        collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)
        vector_store = ChromaVectorStore(chroma_collection=collection)

        sc = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_documents(build_docs(), storage_context=sc)
        print(f"向量存储类型：{type(index.vector_store).__name__}")
        print(f"Chroma 持久化目录：{CHROMA_PATH}（数据落盘，可重启恢复）")
        return index

    def query(self, index, question: str) -> None:
        retriever = index.as_retriever(similarity_top_k=2)
        nodes = retriever.retrieve(question)
        print(f"  查询「{question}」→ 命中 {len(nodes)} 个节点："
              f"{[n.node.metadata.get('title') for n in nodes]}")

    def run(self) -> None:
        idx_simple = self.build_with_simple_vector_store()
        self.query(idx_simple, "每年有几天年假？")

        idx_chroma = self.build_with_chroma()
        if idx_chroma is not None:
            self.query(idx_chroma, "每年有几天年假？")
            print("\n结论：底层向量存储可无缝切换，上层 retriever/query 代码完全不变。")


if __name__ == "__main__":
    VectorStoreCompare().run()