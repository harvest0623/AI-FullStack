# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 02 存储上下文与持久化
演示索引的持久化与恢复：
  1. StorageContext 配置
  2. index.storage_context.persist() 保存到磁盘目录
  3. StorageContext.from_defaults(persist_dir=...) + load_index_from_storage 重新加载
  4. 加载后用 as_query_engine() 查询验证

场景：DataIQ 索引跨进程/重启不丢失。
运行：python 02_storage_context.py
依赖：llama-index llama-index-embeddings-openai python-dotenv
"""

import os
from dotenv import load_dotenv

load_dotenv()

from llama_index.core import (
    Document,
    Settings,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.embeddings import BaseEmbedding

PERSIST_DIR = "./storage_dataiq"


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
        Document(
            text="企业知识库 DataIQ 支持员工自助检索公司制度文档，"
                 "包括远程办公、差旅报销、年假等常见政策，检索结果需附带来源标题。",
            metadata={"doc_id": "intro_001", "title": "DataIQ 简介"},
        ),
        Document(
            text="远程办公政策规定每周最多三天在家办公，"
                 "工作时间内保持在线并在每周一参加团队周会。",
            metadata={"doc_id": "policy_001", "title": "远程办公政策"},
        ),
    ]


class StorageDemo:
    """持久化与恢复演示类。"""

    def __init__(self) -> None:
        Settings.embed_model = load_embed_model()

    def build_and_persist(self) -> None:
        print("\n===== 1) 构建索引并持久化 =====")
        index = VectorStoreIndex.from_documents(build_docs())
        # StorageContext 默认全内存；此处拿到索引自身的 storage_context
        storage_context = index.storage_context
        storage_context.persist(persist_dir=PERSIST_DIR)
        print(f"索引已持久化到目录：{PERSIST_DIR}")
        print(f"持久化子目录：{sorted(os.listdir(PERSIST_DIR))}")

    def load_and_query(self) -> None:
        print("\n===== 2) 从持久化目录重新加载并查询 =====")
        # 从目录恢复 StorageContext，再重建索引
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
        print(f"索引加载成功：{type(index).__name__}, "
              f"包含 {len(index.ref_doc_info)} 篇文档")

        # 加载后照常重建 QueryEngine / Retriever
        query_engine = index.as_query_engine()
        resp = query_engine.query("远程办公要做到什么？")
        print(f"\n回答：{resp.response}")
        print("\n来源节点：")
        for sn in resp.source_nodes:
            print(f"  - {sn.node.metadata.get('title')} (score={sn.score:.4f})")

        query_engine2 = index.as_query_engine()
        resp2 = query_engine2.query("DataIQ 是什么？")
        print(f"\n回答2：{resp2.response}")

    def run(self) -> None:
        # 首次构建并持久化
        self.build_and_persist()
        # 模拟"重启"：仅从磁盘加载，不再重新嵌入
        self.load_and_query()


if __name__ == "__main__":
    StorageDemo().run()