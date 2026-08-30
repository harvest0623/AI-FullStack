# 文件用途：向量存储创建与搜索演示
# 演示 Chroma 本地向量库创建、FAISS 向量库创建、from_documents 批量入库、
# similarity_search 相似度搜索、展示检索结果和相似度分数。
# VectorStoreManager 类封装。场景：ChainQA 知识库构建

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS

load_dotenv()

# 示例文档数据目录
DATA_DIR = Path(__file__).parent / "retrieval_data"


def get_embeddings() -> OpenAIEmbeddings:
    """获取 Embedding 模型。"""
    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def prepare_sample_documents() -> list[Document]:
    """准备示例文档数据，用于构建向量库。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    docs = [
        Document(
            page_content="LangChain 是一个用于开发 LLM 应用的开源框架，由 Harrison Chase 创建。它提供组件化的方式构建 LLM 应用。",
            metadata={"source": "intro.txt", "topic": "概述"},
        ),
        Document(
            page_content="LCEL（LangChain Expression Language）是 LangChain 0.3 的核心表达式语言，用管道符 | 将 Prompt、Model、Parser 等组件组合为链式调用。",
            metadata={"source": "lcel.txt", "topic": "LCEL"},
        ),
        Document(
            page_content="Memory 组件管理对话历史，让 LLM 记住上下文。五种策略：BufferMemory 全量保留、BufferWindowMemory 滑动窗口、SummaryMemory 摘要、SummaryBufferMemory 摘要+缓冲、TokenBufferMemory 按 Token 管理。",
            metadata={"source": "memory.txt", "topic": "Memory"},
        ),
        Document(
            page_content="Retriever 检索器根据查询返回相关文档，基于向量相似度搜索。支持 similarity 纯相似度和 mmr 最大边际相关性两种搜索策略。",
            metadata={"source": "retriever.txt", "topic": "Retriever"},
        ),
        Document(
            page_content="Document Loaders 加载多种格式文档（txt/csv/json/pdf/web），Text Splitters 将长文档分割为可检索的小块。RecursiveCharacterTextSplitter 是最常用的分割器。",
            metadata={"source": "loader.txt", "topic": "Document"},
        ),
        Document(
            page_content="Chroma 是轻量级本地向量数据库，适合开发测试。FAISS 是 Facebook 开发的高性能相似度搜索库。Pinecone 是云端向量数据库服务。",
            metadata={"source": "vectorstore.txt", "topic": "VectorStore"},
        ),
        Document(
            page_content="Runnable 接口是 LCEL 的根基，所有组件都支持 invoke 单次调用、batch 批量调用、stream 流式输出三种方式，以及对应的异步版本。",
            metadata={"source": "runnable.txt", "topic": "Runnable"},
        ),
        Document(
            page_content="Embedding 模型将文本转化为向量，是语义检索的基础。OpenAIEmbeddings 使用 text-embedding-3-small 模型，HuggingFaceEmbeddings 可免费本地使用 BAAI/bge-large-zh。",
            metadata={"source": "embedding.txt", "topic": "Embedding"},
        ),
    ]

    # 保存到文件（便于了解来源）
    for doc in docs:
        path = DATA_DIR / doc.metadata["source"]
        path.write_text(doc.page_content, encoding="utf-8")

    return docs


def demo_chroma_create() -> None:
    """Chroma 本地向量库创建与搜索。"""
    print("=" * 60)
    print("【Chroma 本地向量库创建】\n")

    docs = prepare_sample_documents()
    embeddings = get_embeddings()

    # from_documents 批量入库
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="chainqa_kb",
        persist_directory=str(DATA_DIR / "chroma_db"),  # 持久化目录
    )

    print(f"向量库创建完成，文档数：{len(docs)}")
    print(f"集合名：chainqa_kb")
    print(f"持久化目录：{DATA_DIR / 'chroma_db'}\n")

    # similarity_search 相似度搜索
    query = "LangChain 的记忆管理有哪些策略？"
    print(f"查询：{query}")
    results = vectorstore.similarity_search(query, k=3)
    print(f"返回 {len(results)} 个结果：\n")
    for i, doc in enumerate(results):
        print(f"  [{i}] source={doc.metadata['source']}")
        print(f"      内容：{doc.page_content[:60]}...")
    print()


def demo_chroma_with_scores() -> None:
    """带相似度分数的搜索。"""
    print("=" * 60)
    print("【带相似度分数的搜索 similarity_search_with_score】\n")

    docs = prepare_sample_documents()
    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(docs, embedding=embeddings)

    query = "什么是 LCEL？"
    print(f"查询：{query}")
    # similarity_search_with_score 返回 (Document, score) 元组列表
    # 注意：Chroma 返回的是距离（越小越相似），不是相似度
    results = vectorstore.similarity_search_with_score(query, k=3)
    print(f"返回 {len(results)} 个结果（按距离升序，越小越相似）：\n")
    for i, (doc, score) in enumerate(results):
        print(f"  [{i}] 距离={score:.4f} source={doc.metadata['source']}")
        print(f"      内容：{doc.page_content[:60]}...")
    print()


def demo_faiss_create() -> None:
    """FAISS 向量库创建与搜索。"""
    print("=" * 60)
    print("【FAISS 向量库创建】\n")

    docs = prepare_sample_documents()
    embeddings = get_embeddings()

    # FAISS 内存创建
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)

    print(f"FAISS 向量库创建完成，文档数：{len(docs)}")

    query = "向量数据库有哪些选择？"
    print(f"查询：{query}")
    results = vectorstore.similarity_search(query, k=3)
    print(f"返回 {len(results)} 个结果：\n")
    for i, doc in enumerate(results):
        print(f"  [{i}] source={doc.metadata['source']}")
        print(f"      内容：{doc.page_content[:60]}...")
    print()

    # FAISS 带分数搜索（返回相似度，越大越相似）
    print("FAISS 带相似度分数搜索：")
    results_with_scores = vectorstore.similarity_search_with_score(query, k=3)
    for i, (doc, score) in enumerate(results_with_scores):
        print(f"  [{i}] 相似度={score:.4f} source={doc.metadata['source']}")
    print()


class VectorStoreManager:
    """向量存储管理器，封装 Chroma 和 FAISS 的常用操作。"""

    def __init__(self, embeddings=None) -> None:
        self.embeddings = embeddings or get_embeddings()

    def create_chroma(self, documents: list[Document], persist_dir: str = None) -> Chroma:
        """创建 Chroma 向量库。"""
        kwargs = {"documents": documents, "embedding": self.embeddings}
        if persist_dir:
            kwargs["persist_directory"] = persist_dir
        return Chroma.from_documents(**kwargs)

    def create_faiss(self, documents: list[Document]) -> FAISS:
        """创建 FAISS 向量库。"""
        return FAISS.from_documents(documents=documents, embedding=self.embeddings)

    def search(self, vectorstore, query: str, k: int = 3, with_score: bool = False) -> list:
        """通用搜索接口。"""
        if with_score:
            return vectorstore.similarity_search_with_score(query, k=k)
        return vectorstore.similarity_search(query, k=k)


def demo_vectorstore_manager() -> None:
    """演示 VectorStoreManager 封装类。"""
    print("=" * 60)
    print("【VectorStoreManager 统一封装】\n")

    docs = prepare_sample_documents()
    manager = VectorStoreManager()

    # 创建 Chroma
    chroma_store = manager.create_chroma(docs)
    # 创建 FAISS
    faiss_store = manager.create_faiss(docs)

    query = "Runnable 接口支持哪些调用方式？"
    print(f"查询：{query}\n")

    print("Chroma 结果：")
    for doc in manager.search(chroma_store, query, k=2):
        print(f"  - {doc.page_content[:50]}...")

    print("\nFAISS 结果：")
    for doc in manager.search(faiss_store, query, k=2):
        print(f"  - {doc.page_content[:50]}...")
    print()


def main() -> None:
    demo_chroma_create()
    demo_chroma_with_scores()
    demo_faiss_create()
    demo_vectorstore_manager()
    print("=" * 60)
    print("向量存储创建与搜索演示完成。")


if __name__ == "__main__":
    main()
