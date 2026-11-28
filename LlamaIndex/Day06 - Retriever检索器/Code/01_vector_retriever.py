# -*- coding: utf-8 -*-
"""
文件用途：Day06 - 01 向量检索
演示 VectorIndexRetriever 的使用：
  1. index.as_retriever() 创建检索器
  2. retrieve(query) 检索，打印 NodeWithScore(node + score)
  3. similarity_top_k 调参对比（k=2 vs k=5 的召回差异）

场景：DataIQ 语义检索回答不同问题。
运行：python 01_vector_retriever.py
依赖：llama-index llama-index-embeddings-openai python-dotenv
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
            ("a", "年假制度", "DataIQ 员工每年享有 15 天带薪年假，需提前三天在 HR 系统提交申请。"),
            ("b", "远程办公", "员工每周最多可在家办公三天，需保持上午十点至下午四点在线。"),
            ("c", "出差报销", "出差住宿标准每日上限 500 元，报销需出差结束后五个工作日内提交。"),
            ("d", "加班制度", "工作日加班可申请调休，法定节假日加班按三倍工资计发。"),
            ("e", "晋升机制", "员工每年有两次晋升评审窗口，由直属经理提名并进入评审委员会。"),
        ]
    ]


class VectorRetrieverDemo:
    """向量检索演示类。"""

    def __init__(self) -> None:
        Settings.embed_model = load_embed_model()
        self.index = VectorStoreIndex.from_documents(build_docs())
        print(f"索引构建完成，{len(self.index.ref_doc_info)} 篇文档\n")

    def retrieve(self, query: str, top_k: int) -> None:
        """执行检索并打印命中结果。"""
        retriever = self.index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        print(f"  ⇒ 检索「{query}」 top_k={top_k} → 命中 {len(nodes)}")
        for i, nws in enumerate(nodes, 1):
            print(f"     #{i} score={nws.score:.4f} title={nws.node.metadata['title']}")

    def compare_topk(self) -> None:
        print("\n===== similarity_top_k 对比：k=2 vs k=5 =====")
        q = "员工可以休假吗？"
        self.retrieve(q, top_k=2)
        print()
        self.retrieve(q, top_k=5)

    def multi_questions(self) -> None:
        print("\n===== 语义检索回答不同问题 =====")
        for q in ["怎么报销出差费用？", "能否在家办公？", "晋升需要谁提名？"]:
            self.retrieve(q, top_k=2)
            print()

    def run(self) -> None:
        self.compare_topk()
        self.multi_questions()


if __name__ == "__main__":
    VectorRetrieverDemo().run()