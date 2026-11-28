# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 04 索引增量更新
演示文档入库后的增量更新：
  1. insert(new_doc)：追加新文档
  2. refresh(doc)：按 doc_id 检测版本并更新替换
  3. delete_ref_doc(doc_id)：删除某来源文档
  4. 每次操作后检索验证索引反映最新数据

场景：DataIQ 新文档入库、政策更新、政策删除。
运行：python 04_index_update.py
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
    print("[embed] 未检测到 API Key，降级使用 HashEmbedding（仅演示）")
    return HashEmbedding()


def build_docs() -> list[Document]:
    return [
        Document(
            text="DataIQ 提供每年 15 天带薪年假，入职满一年即可全额领取。",
            metadata={"doc_id": "policy_annual", "title": "年假制度-旧版"},
        ),
        Document(
            text="DataIQ 支持员工远程办公，每周最多三天在家里办公。",
            metadata={"doc_id": "policy_remote", "title": "远程办公政策"},
        ),
    ]


class IndexUpdateDemo:
    """索引增量更新演示类。"""

    def __init__(self) -> None:
        Settings.embed_model = load_embed_model()
        self.index = VectorStoreIndex.from_documents(build_docs())
        print("初始索引（2 篇文档）构建完成")

    def search(self, question: str) -> None:
        """检索并打印命中的文档标题。"""
        nodes = self.index.as_retriever(similarity_top_k=3).retrieve(question)
        titles = [n.node.metadata.get("title") for n in nodes]
        print(f"  检索「{question}」命中：{titles}")

    def step_insert(self) -> None:
        print("\n===== 1) insert：新增《加班制度》=====")
        new_doc = Document(
            text="DataIQ 工作日加班可申请调休，法定节假日加班按 3 倍工资计发。",
            metadata={"doc_id": "policy_overtime", "title": "加班制度"},
        )
        self.index.insert(new_doc)
        self.index.storage_context.persist(persist_dir="./storage_update")
        print("  已 insert 并持久化（追加，不影响已有文档）")
        self.search("加班怎么算？")

    def step_refresh(self) -> None:
        print("\n===== 2) refresh：更新《年假制度》=====")
        updated_doc = Document(
            text="DataIQ 将年假额度提升至每年 20 天，入职满六个月即可领取。",
            metadata={"doc_id": "policy_annual", "title": "年假制度-新版"},
        )
        # 依据 doc_id 刷新：旧版 policy_annual 的 Node 会被替换
        refreshed = self.index.refresh(updated_doc)
        print(f"  被更新的 doc_id 列表：{refreshed}")
        self.search("每年可以休多少天假？")

    def step_delete(self) -> None:
        print("\n===== 3) delete_ref_doc：删除《远程办公政策》=====")
        self.index.delete_ref_doc("policy_remote", delete_from_docstore=True)
        print("  已删除 policy_remote 及其全部相关 Node")
        self.search("可以远程办公吗？")

    def run(self) -> None:
        self.step_insert()
        self.step_refresh()
        self.step_delete()
        print("\n最终索引中的文档篇数：", len(self.index.ref_doc_info))


if __name__ == "__main__":
    IndexUpdateDemo().run()