# -*- coding: utf-8 -*-
"""
文件用途：Day06 - 03 混合检索
演示 向量检索 + BM25 关键词检索 的混合检索（QueryFusionRetriever）：
  1. 分别构造向量检索器、BM25 检索器
  2. QueryFusionRetriever 用 Reciprocal Rank Fusion 融合排序
  3. 对比 单一检索 vs 混合检索的效果

场景：DataIQ 检索同时需要语义理解与精确词命中。
运行：python 03_hybrid_retriever.py
依赖：
  pip install llama-index llama-index-embeddings-openai python-dotenv rank_bm25
  pip install llama-index-retrievers-bm25   # BM25Retriever 若不在 core
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
            ("c1", "合同 CON-2024-007", "合同 CON-2024-007 服务期为一年，总金额 50 万元，含月度维护。"),
            ("c2", "合同续签流程", "合同到期前 30 天应由商务部门发起续签评审，法务审核后签署。"),
            ("c3", "供应商准入", "新供应商需提交资质与报价，经采购委员会评审通过方可合作。"),
            ("c4", "付款条款", "合同款项分三笔支付：签约 30%、验收 40%、维保到期后 30%。"),
        ]
    ]


class HybridRetrieverDemo:
    """混合检索演示类。"""

    def __init__(self) -> None:
        Settings.embed_model = load_embed_model()
        self.index = VectorStoreIndex.from_documents(build_docs())

    def make_bm25(self):
        try:
            from llama_index.retrievers.bm25 import BM25Retriever
            return BM25Retriever.from_defaults(index=self.index, similarity_top_k=2)
        except Exception:
            try:
                from llama_index_retrievers_bm25 import BM25Retriever
                return BM25Retriever.from_defaults(index=self.index, similarity_top_k=2)
            except Exception as e:
                print(f"[skip] 未安装 BM25 相关依赖：{e}")
                return None

    def demo(self) -> None:
        from llama_index.core.retrievers import QueryFusionRetriever

        vector_r = self.index.as_retriever(similarity_top_k=2)
        bm25_r = self.make_bm25()

        if bm25_r is None:
            hybrid = QueryFusionRetriever(
                [vector_r], similarity_top_k=2,
                mode=QueryFusionRetriever.Mode.RECIPROCAL_RANK,
            )
            print("[warn] 因缺少 BM25 依赖，混合检索退化为单路向量。\n")
        else:
            hybrid = QueryFusionRetriever(
                [vector_r, bm25_r], similarity_top_k=2,
                mode=QueryFusionRetriever.Mode.RECIPROCAL_RANK,
            )

        query = "合同 CON-2024-007 多少钱？"
        print(f"===== 查询：{query} =====\n")
        print("[单一·向量] 命中：",
              [n.node.metadata['title'] for n in vector_r.retrieve(query)])
        if bm25_r is not None:
            print("[单一·BM25] 命中：",
                  [n.node.metadata['title'] for n in bm25_r.retrieve(query)])
        print("[混合·融合] 命中：",
              [n.node.metadata['title'] for n in hybrid.retrieve(query)])

        print("""
结论观察：
  - 向量负责「语义近义」召回，BM25 负责「精确词（编号）」召回；
  - 混合检索把两边结果用 RRF 融合，避免单一策略漏召回关键片段，
    尤其适合同时包含专有编号 + 口语表述的企业查询。""")


if __name__ == "__main__":
    HybridRetrieverDemo().demo()