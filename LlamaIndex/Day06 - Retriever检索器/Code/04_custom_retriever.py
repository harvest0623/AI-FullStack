# -*- coding: utf-8 -*-
"""
文件用途：Day06 - 04 自定义 Retriever
演示继承 BaseRetriever 实现自定义检索：
  1. 继承 BaseRetriever，实现 _retrieve(query) 方法
  2. 自定义逻辑：按 metadata 部门过滤 + 向量检索
  3. 注册/使用自定义检索器

场景：DataIQ 只检索特定部门文档的检索器。
运行：python 04_custom_retriever.py
依赖：llama-index llama-index-embeddings-openai python-dotenv
"""

import os
from dotenv import load_dotenv

load_dotenv()

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.base.base_retriever import BaseRetriever


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
        Document(text=text,
                 metadata={"doc_id": did, "title": title, "department": dept})
        for did, title, dept, text in [
            ("p1", "技术部上线规范", "技术部", "上线需提前两天提交变更单，经技术评审后方可发布。"),
            ("p2", "技术部值班表", "技术部", "技术值班按周轮换，值班期间需在群里保持响应。"),
            ("p3", "市场部活动预算", "市场部", "市场活动预算小于一万由市场总监审批，超出走立项流程。"),
            ("p4", "财务部发票规范", "财务部", "报销发票需为增票，抬头必须填写 DataIQ 公司全称。"),
        ]
    ]


class DepartmentRetriever(BaseRetriever):
    """自定义检索器：先按 metadata.department 过滤，再做向量检索。

    通过继承 BaseRetriever 并实现 _retrieve()，我们把业务规则
    （只检索指定部门文档）注入到检索流程中。
    """

    def __init__(self, index: VectorStoreIndex, department: str,
                 similarity_top_k: int = 2) -> None:
        super().__init__()
        self.vector_retriever = index.as_retriever(similarity_top_k=len(index.ref_doc_info))
        self.department = department

    def _retrieve(self, query: str):
        # 1) 先做向量检索（拉全量，便于过滤）
        candidates = self.vector_retriever.retrieve(query)
        # 2) 按部门过滤
        filtered = [
            nws for nws in candidates
            if nws.node.metadata.get("department") == self.department
        ]
        # 3) 按分数降序，返回 top 2
        filtered.sort(key=lambda n: n.score, reverse=True)
        return filtered[:2]


class CustomRetrieverDemo:
    """自定义检索器演示类。"""

    def __init__(self) -> None:
        Settings.embed_model = load_embed_model()
        self.index = VectorStoreIndex.from_documents(build_docs())

    def demo(self) -> None:
        print("===== 通用向量检索（无部门过滤）=====")
        all_nodes = self.index.as_retriever(similarity_top_k=3).retrieve("发票要怎么写")
        print("  命中：", [n.node.metadata['title'] for n in all_nodes])

        print("\n===== 自定义检索：只查「财务部」=====")
        finance_retriever = DepartmentRetriever(self.index, department="财务部")
        f_nodes = finance_retriever.retrieve("发票要怎么写")
        for n in f_nodes:
            print(f"  - [{n.node.metadata['department']}] {n.node.metadata['title']} "
                  f"(score={n.score:.4f})")

        print("\n===== 自定义检索：只查「技术部」=====")
        tech_retriever = DepartmentRetriever(self.index, department="技术部")
        t_nodes = tech_retriever.retrieve("上线怎么操作")
        for n in t_nodes:
            print(f"  - [{n.node.metadata['department']}] {n.node.metadata['title']} "
                  f"(score={n.score:.4f})")

        print("""
小结：
  - 继承 BaseRetriever 实现 _retrieve() 即可注入自定义检索逻辑；
  - 典型组合：metadata 规则 + 向量检索 + 重排/过滤/去重；
  - 自定义 Retriever 可被 QueryEngine 直接使用（Day07：as_query_engine(retriever=...)）。""")


if __name__ == "__main__":
    CustomRetrieverDemo().demo()