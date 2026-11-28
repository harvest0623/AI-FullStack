# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 01 向量索引构建
演示 VectorStoreIndex 的完整构建流程：
  1. from_documents 从 Document 构建向量索引
  2. 通过 Settings 配置 embed_model（无 Key 时降级为 HashEmbedding）
  3. from_nodes 从已切分的 Node 构建索引
  4. 用 as_retriever() 检索验证索引可用

场景：DataIQ 企业知识库基础索引搭建。
运行：python 01_vector_index.py
依赖：llama-index llama-index-embeddings-openai python-dotenv
"""

import os
from dotenv import load_dotenv

# 尽量加载 .env 中的 API Key
load_dotenv()

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import BaseEmbedding


class HashEmbedding(BaseEmbedding):
    """无 Key 时的降级嵌入模型：基于文本哈希生成固定维向量。

    仅用于离线演示流程，不具备真实语义。生产环境请替换为
    OpenAIEmbedding / HuggingFaceEmbedding 等真实模型。
    """

    def __init__(self, *args, dim: int = 16, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dim = dim

    def _get_text_embedding(self, text: str) -> list:
        import hashlib

        vec = []
        for i in range(self.dim):
            # 用 text 与序号复合做 md5 哈希，映射到 [0,1)
            h = hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8]
            vec.append(int(h, 16) / (16**8))
        return vec

    def _get_query_embedding(self, query: str) -> list:
        return self._get_text_embedding(query)


def load_embed_model():
    """根据是否存在 API Key，选择真实/降级嵌入模型。"""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        from llama_index.embeddings.openai import OpenAIEmbedding

        print("[embed] 使用 OpenAIEmbedding（在线）")
        return OpenAIEmbedding(model="text-embedding-3-small", api_key=api_key)
    print("[embed] 未检测到 OPENAI_API_KEY，降级使用 HashEmbedding（仅演示）")
    return HashEmbedding()


def build_demo_documents() -> list[Document]:
    """生成 DataIQ 企业知识库示例文档。"""
    docs_data = [
        ("dataiq_policy_001", "远程办公政策",
         "DataIQ 公司实行每周最多三天的远程办公制度。员工可在家办公，"
         "但需保证上午 10 点到下午 4 点保持在线，并定期参加团队周会。"),
        ("dataiq_policy_002", "出差报销制度",
         "差旅报销需在出差结束后 5 个工作日内提交。住宿每天上限 500 元，"
         "交通如需升级舱位须提前向直属经理邮件申请获准。"),
        ("dataiq_policy_003", "年假制度",
         "DataIQ 提供每年 15 天带薪年假，入职满 1 年即可全部领取。"
         "年假需提前 3 天在 HR 系统提交，不允许跨年累计。"),
    ]
    docs = []
    for doc_id, title, text in docs_data:
        docs.append(Document(
            text=text,
            metadata={"doc_id": doc_id, "title": title},
        ))
    return docs


class VectorIndexDemo:
    """向量索引构建演示类。"""

    def __init__(self) -> None:
        # 全局配置：嵌入模型（真实 or 降级）
        Settings.embed_model = load_embed_model()

    def build_by_documents(self) -> VectorStoreIndex:
        """方式一：from_documents 一键构建。"""
        print("\n===== 1) from_documents 构建向量索引 =====")
        docs = build_demo_documents()
        # 内部会先用默认 NodeParser 把 Document 切成 Node，再向量化
        index = VectorStoreIndex.from_documents(docs)
        print(f"索引类型：{type(index).__name__}")
        print(f"已嵌入 Node 数：{len(index.ref_doc_info)} 篇文档")
        return index

    def build_by_nodes(self) -> VectorStoreIndex:
        """方式二：先手动手动切分 Node，再 from_nodes 构建。"""
        print("\n===== 2) from_nodes 手动切分后构建 =====")
        docs = build_demo_documents()
        parser = SentenceSplitter(chunk_size=64, chunk_overlap=8)
        nodes = parser.get_nodes_from_documents(docs)
        print(f"切分得到 {len(nodes)} 个 Node")
        # 手动切分后从 Nodes 构建（更精细控制 chunk 大小）
        index = VectorStoreIndex.from_nodes(nodes)
        print(f"从 {len(nodes)} 个 Node 构建索引成功")
        return index

    def verify_retrieval(self, index: VectorStoreIndex) -> None:
        """用 as_retriever() 检索验证索引可用。"""
        print("\n===== 3) as_retriever() 检索验证 =====")
        retriever = index.as_retriever(similarity_top_k=2)
        nodes = retriever.retrieve("我们每年可以休假多少天？")
        print(f"检索到 {len(nodes)} 个相关节点，按相似度排序：")
        for i, node_with_score in enumerate(nodes, 1):
            print(f"  #{i} score={node_with_score.score:.4f} "
                  f"title={node_with_score.node.metadata.get('title')}")
            print(f"     文本：{node_with_score.node.text[:40]}...")

    def run(self) -> None:
        index_docs = self.build_by_documents()
        self.verify_retrieval(index_docs)

        index_nodes = self.build_by_nodes()
        self.verify_retrieval(index_nodes)


if __name__ == "__main__":
    VectorIndexDemo().run()