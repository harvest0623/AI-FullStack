# 文件用途：多种 Retriever 对比演示
# 演示 VectorStoreRetriever(as_retriever)、similarity vs mmr 搜索对比、
# MultiQueryRetriever 多查询检索、ContextualCompressionRetriever 上下文压缩。
# RetrieverComparator 类对比不同检索器效果。
# 场景：ChainQA 检索策略选型

import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

load_dotenv()


def get_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def prepare_sample_documents() -> list[Document]:
    """准备示例文档（含若干相似内容，便于对比检索策略）。"""
    return [
        Document(page_content="LangChain 的 Memory 组件管理对话历史，五种策略：Buffer、Window、Summary、SummaryBuffer、TokenBuffer。", metadata={"id": 1}),
        Document(page_content="ConversationBufferMemory 全量保留所有对话历史，信息完整但 Token 线性增长。", metadata={"id": 2}),
        Document(page_content="ConversationBufferWindowMemory 只保留最近 K 轮对话，Token 可控但旧信息丢失。", metadata={"id": 3}),
        Document(page_content="LCEL 是 LangChain 0.3 的核心表达式语言，用管道符组合组件。", metadata={"id": 4}),
        Document(page_content="Memory 让 LLM 记住上下文，实现多轮对话，是无状态 LLM 的记忆机制。", metadata={"id": 5}),
        Document(page_content="Retriever 检索器基于向量相似度返回相关文档，支持 similarity 和 mmr 两种搜索。", metadata={"id": 6}),
        Document(page_content="RecursiveCharacterTextSplitter 是最常用的文本分割器，递归按段落、句子、字符切分。", metadata={"id": 7}),
        Document(page_content="对话记忆策略的选择取决于对话长度：短对话用 Buffer，长对话用 Summary。", metadata={"id": 8}),
    ]


def create_vectorstore() -> Chroma:
    """创建向量库。"""
    docs = prepare_sample_documents()
    return Chroma.from_documents(docs, embedding=get_embeddings())


def demo_basic_retriever() -> None:
    """VectorStoreRetriever 基础用法。"""
    print("=" * 60)
    print("【VectorStoreRetriever 基础用法】\n")

    vectorstore = create_vectorstore()

    # as_retriever 创建检索器
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
    )

    query = "Memory 有哪些策略？"
    print(f"查询：{query}")
    print(f"search_type=similarity, k=3\n")

    results = retriever.invoke(query)
    print(f"返回 {len(results)} 个结果：")
    for i, doc in enumerate(results):
        print(f"  [{i}] id={doc.metadata['id']}")
        print(f"      {doc.page_content[:60]}...")
    print()


def demo_similarity_vs_mmr() -> None:
    """similarity vs mmr 搜索对比。"""
    print("=" * 60)
    print("【similarity vs mmr 搜索对比】\n")

    vectorstore = create_vectorstore()

    # similarity 检索器
    sim_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
    )

    # mmr 检索器
    mmr_retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4, "fetch_k": 8, "lambda_mult": 0.5},
    )

    query = "Memory 记忆管理"
    print(f"查询：{query}\n")

    print("--- similarity（纯相似度，可能返回重复内容）---")
    sim_results = sim_retriever.invoke(query)
    for i, doc in enumerate(sim_results):
        print(f"  [{i}] id={doc.metadata['id']}: {doc.page_content[:50]}...")

    print("\n--- mmr（相似度+多样性，去重效果好）---")
    mmr_results = mmr_retriever.invoke(query)
    for i, doc in enumerate(mmr_results):
        print(f"  [{i}] id={doc.metadata['id']}: {doc.page_content[:50]}...")

    print("\n说明：mmr 在相似度和多样性间平衡，避免返回内容高度重复的文档\n")


def demo_multi_query_retriever() -> None:
    """MultiQueryRetriever：用 LLM 生成多个查询变体，提高召回。"""
    print("=" * 60)
    print("【MultiQueryRetriever 多查询检索】\n")

    vectorstore = create_vectorstore()
    model = get_model()

    # 用 LLM 生成多个查询变体
    multi_retriever = MultiQueryRetriever.from_llm(
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        llm=model,
    )

    query = "怎么管理对话历史？"
    print(f"查询：{query}")
    print(f"MultiQueryRetriever 会自动生成多个查询变体，合并结果\n")

    import logging
    logging.basicConfig(level=logging.INFO)  # 开启日志可看到生成的变体

    results = multi_retriever.invoke(query)
    print(f"返回 {len(results)} 个结果（合并去重后）：")
    seen_ids = set()
    for doc in results:
        if doc.metadata["id"] not in seen_ids:
            seen_ids.add(doc.metadata["id"])
            print(f"  id={doc.metadata['id']}: {doc.page_content[:50]}...")
    print()


def demo_contextual_compression() -> None:
    """ContextualCompressionRetriever：检索后压缩，提取相关片段。"""
    print("=" * 60)
    print("【ContextualCompressionRetriever 上下文压缩】\n")

    vectorstore = create_vectorstore()
    model = get_model()

    # 用 LLM 从检索文档中提取与问题相关的片段
    compressor = LLMChainExtractor.from_llm(model)
    compression_retriever = ContextualCompressionRetriever(
        base_retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        base_compressor=compressor,
    )

    query = "BufferWindowMemory 的特点是什么？"
    print(f"查询：{query}")
    print("上下文压缩会从检索结果中提取相关片段\n")

    results = compression_retriever.invoke(query)
    print(f"压缩后返回 {len(results)} 个结果：")
    for i, doc in enumerate(results):
        print(f"  [{i}] {doc.page_content}")
    print()


class RetrieverComparator:
    """检索器对比器：对比不同检索器的效果。"""

    def __init__(self) -> None:
        self.vectorstore = create_vectorstore()
        self.model = get_model()

    def compare(self, query: str, k: int = 3) -> None:
        """对比多种检索器对同一查询的结果。"""
        print("=" * 60)
        print(f"【RetrieverComparator 检索器对比】")
        print(f"查询：{query}\n")

        retrievers = {
            "similarity": self.vectorstore.as_retriever(
                search_type="similarity", search_kwargs={"k": k}
            ),
            "mmr": self.vectorstore.as_retriever(
                search_type="mmr", search_kwargs={"k": k, "fetch_k": 10}
            ),
        }

        for name, retriever in retrievers.items():
            results = retriever.invoke(query)
            ids = [doc.metadata["id"] for doc in results]
            print(f"{name:<14} → 返回 id: {ids}")

        print()


def main() -> None:
    demo_basic_retriever()
    demo_similarity_vs_mmr()
    demo_multi_query_retriever()
    demo_contextual_compression()

    comparator = RetrieverComparator()
    comparator.compare("Memory 策略有哪些？", k=4)
    comparator.compare("文本分割用什么工具？", k=3)

    print("=" * 60)
    print("多种 Retriever 对比演示完成。")


if __name__ == "__main__":
    main()
