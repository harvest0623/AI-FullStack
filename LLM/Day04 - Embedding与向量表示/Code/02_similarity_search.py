# 文件用途：语义搜索实现
# SemanticSearch 类：构建文档向量索引 -> 查询向量化 -> Top-K 相似度搜索 -> 返回结果。
# 支持添加文档 / 单条搜索 / 批量搜索。
# 用 numpy 实现向量计算，不依赖外部向量数据库。
# 依赖：pip install openai python-dotenv numpy
# 需在 .env 配置 OPENAI_API_KEY
# 体现 AISearch 项目 embedding/ 中「相似度计算」的封装思想。

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import numpy as np

try:
    from dotenv import load_dotenv
except ImportError:
    print("缺少依赖 python-dotenv，请执行: pip install python-dotenv")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("缺少依赖 openai，请执行: pip install openai")
    sys.exit(1)

load_dotenv()


@dataclass
class SearchResult:
    """单条搜索结果。"""
    doc_id: int
    text: str
    score: float


class SemanticSearch:
    """基于 numpy 的语义搜索引擎（无外部向量库依赖）。"""

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("未配置 OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        self.client = OpenAI(api_key=key, base_url=base_url) if base_url else OpenAI(api_key=key)
        self.documents: list[str] = []
        self.vectors: np.ndarray | None = None  # shape (n, dim)

    # ---- 索引构建 ----
    def add_documents(self, docs: list[str]) -> None:
        """添加文档并批量向量化。"""
        if not docs:
            return
        new_vecs = self._embed_batch(docs)
        if self.vectors is None:
            self.vectors = new_vecs
        else:
            self.vectors = np.vstack([self.vectors, new_vecs])
        start_id = len(self.documents)
        self.documents.extend(docs)
        print(f"  已添加 {len(docs)} 篇文档，当前索引共 {len(self.documents)} 篇")

    # ---- 搜索 ----
    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        """单条查询，返回 Top-K 最相似文档。"""
        if self.vectors is None or len(self.documents) == 0:
            return []
        query_vec = self._embed_batch([query])[0]
        scores = self._cosine_batch(query_vec, self.vectors)
        # 按分数降序取 Top-K
        top_idx = np.argsort(-scores)[:top_k]
        return [
            SearchResult(doc_id=int(i), text=self.documents[i], score=float(scores[i]))
            for i in top_idx
        ]

    def search_batch(self, queries: list[str], top_k: int = 3) -> list[list[SearchResult]]:
        """批量查询。"""
        if self.vectors is None:
            return [[] for _ in queries]
        query_vecs = self._embed_batch(queries)
        results = []
        for qv in query_vecs:
            scores = self._cosine_batch(qv, self.vectors)
            top_idx = np.argsort(-scores)[:top_k]
            results.append([
                SearchResult(doc_id=int(i), text=self.documents[i], score=float(scores[i]))
                for i in top_idx
            ])
        return results

    # ---- 内部工具 ----
    def _embed_batch(self, texts: list[str]) -> np.ndarray:
        resp = self.client.embeddings.create(model=self.model, input=texts)
        data = sorted(resp.data, key=lambda x: x.index)
        return np.array([d.embedding for d in data], dtype=np.float32)

    @staticmethod
    def _cosine_batch(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """计算查询向量与文档矩阵的余弦相似度。"""
        q_norm = query / (np.linalg.norm(query) + 1e-10)
        m_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
        return m_norm @ q_norm  # 归一化后点积 = 余弦相似度


def demo() -> None:
    print("=" * 60)
    print("语义搜索 SemanticSearch 演示")
    print("=" * 60)

    engine = SemanticSearch()
    # 构建一个小型文档库
    docs = [
        "Python 是一种解释型、面向对象的高级编程语言。",
        "机器学习是让计算机从数据中学习规律的人工智能分支。",
        "Transformer 架构是现代大语言模型的核心基础。",
        "向量数据库用于存储和检索高维向量，支持近似最近邻搜索。",
        "RAG 通过检索外部知识增强大模型生成，缓解幻觉问题。",
        "今天天气晴朗，适合户外运动。",
        "推荐系统根据用户兴趣推荐商品或内容。",
        "深度学习使用多层神经网络进行特征学习。",
    ]
    print("\n1. 构建文档索引")
    engine.add_documents(docs)

    print("\n2. 单条查询")
    queries = [
        "什么是大模型的基础架构？",
        "如何用检索增强生成？",
        "今天适合出门吗？",
    ]
    for q in queries:
        print(f"\n  查询: 「{q}」")
        results = engine.search(q, top_k=2)
        for r in results:
            print(f"    [{r.score:.4f}] {r.text}")

    print("\n3. 批量查询（演示批量接口）")
    batch_results = engine.search_batch(queries, top_k=1)
    for q, rs in zip(queries, batch_results):
        best = rs[0] if rs else None
        if best:
            print(f"  「{q}」 -> 最佳: [{best.score:.4f}] {best.text}")

    print("\n说明：")
    print("- 语义搜索能理解「大模型基础架构」对应「Transformer 架构」，而非字面匹配")
    print("- 与关键词搜索（BM25）相比，语义搜索能找到同义/近义表达")
    print("- 本实现用 numpy 存储与计算，适合中小规模；大规模需用专业向量数据库")


if __name__ == "__main__":
    demo()
