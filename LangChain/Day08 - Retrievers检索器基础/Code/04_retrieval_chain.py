# 文件用途：检索器与 Chain 集成演示
# 演示 RunnablePassthrough 传递查询、检索结果注入 Prompt、
# 构建完整问答链：查询→检索→生成回答、展示检索增强效果。
# RetrievalQAChain 类。这是 RAG 的基础模式，后续 RAG 板块深入。
# 场景：ChainQA 检索增强问答

import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

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


def prepare_knowledge_base() -> list[Document]:
    """准备 ChainQA 的知识库文档。"""
    return [
        Document(page_content="ChainQA 是一个基于 LangChain 构建的智能问答助手，支持多轮对话、文档检索和知识问答。", metadata={"source": "intro"}),
        Document(page_content="ChainQA 使用 LCEL 链式调用组合各组件，用 RunnableWithMessageHistory 管理多会话记忆。", metadata={"source": "arch"}),
        Document(page_content="ChainQA 的 Memory 策略默认使用 ConversationBufferWindowMemory(k=5)，平衡上下文保留与 Token 控制。", metadata={"source": "memory"}),
        Document(page_content="ChainQA 通过 Chroma 向量库实现文档检索，用 RecursiveCharacterTextSplitter 分割文档，chunk_size=500。", metadata={"source": "retrieval"}),
        Document(page_content="ChainQA 的检索链模式：查询 → Retriever 检索 → RunnablePassthrough 传问题 → Prompt 注入上下文 → Model 生成回答。", metadata={"source": "chain"}),
        Document(page_content="ChainQA 支持 gpt-4o-mini 作为默认模型，temperature=0 保证回答稳定，主模型失败时回退到 gpt-4o。", metadata={"source": "model"}),
    ]


def create_vectorstore() -> Chroma:
    """创建知识库向量存储。"""
    docs = prepare_knowledge_base()
    return Chroma.from_documents(docs, embedding=get_embeddings())


def demo_runnable_passthrough() -> None:
    """RunnablePassthrough 传递查询：同时检索和保留原始问题。"""
    print("=" * 60)
    print("【RunnablePassthrough 传递查询】\n")

    vectorstore = create_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    # 并行：检索 context + 传递 question
    parallel = {
        "context": retriever,
        "question": RunnablePassthrough(),
    }

    query = "ChainQA 用什么记忆策略？"
    print(f"查询：{query}\n")

    result = RunnablePassthrough()  # 仅演示并行收集阶段
    # 用 invoke 演示并行收集（这里用一个 dict 包装的并行 Runnable）
    from langchain_core.runnables import RunnableParallel
    collect = RunnableParallel(parallel)
    output = collect.invoke(query)

    print("并行收集结果：")
    print(f"  question（原样传递）：{output['question']}")
    print(f"  context（检索结果）：{len(output['context'])} 个文档")
    for i, doc in enumerate(output["context"]):
        print(f"    [{i}] {doc.page_content[:50]}...")
    print()


def demo_retrieval_chain() -> None:
    """完整检索问答链：查询 → 检索 → 注入 Prompt → 生成回答。"""
    print("=" * 60)
    print("【完整检索问答链（RAG 基础模式）】\n")

    vectorstore = create_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    model = get_model()
    parser = StrOutputParser()

    # 带上下文的问答 Prompt
    prompt = ChatPromptTemplate.from_template(
        "你是 ChainQA 智能问答助手。请根据以下上下文回答问题。"
        "如果上下文中没有相关信息，请说明无法从知识库中找到答案。\n\n"
        "上下文：\n{context}\n\n"
        "问题：{question}\n"
        "回答："
    )

    # 检索链：RAG 基础模式
    chain = (
        {
            "context": retriever,             # 检索相关文档
            "question": RunnablePassthrough() # 原样传递问题
        }
        | prompt    # 填充模板
        | model     # 调用模型
        | parser    # 解析输出
    )

    query = "ChainQA 默认用什么模型？"
    print(f"问题：{query}")
    result = chain.invoke(query)
    print(f"回答：{result}\n")

    print("数据流说明：")
    print("  1. 输入字符串问题")
    print("  2. 并行：retriever 检索文档 → context，RunnablePassthrough → question")
    print("  3. context + question 填入 Prompt 模板")
    print("  4. 调用 Model 生成回答")
    print("  5. Parser 解析为字符串\n")


def demo_with_without_retrieval() -> None:
    """对比有无检索增强的效果。"""
    print("=" * 60)
    print("【检索增强效果对比：有 vs 无检索】\n")

    vectorstore = create_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    model = get_model()
    parser = StrOutputParser()

    # 无检索：直接问模型（模型不知道 ChainQA 的内部细节）
    no_retrieval_prompt = ChatPromptTemplate.from_template(
        "回答问题：{question}\n回答："
    )
    no_retrieval_chain = no_retrieval_prompt | model | parser

    # 有检索：先检索再回答
    with_retrieval_prompt = ChatPromptTemplate.from_template(
        "根据上下文回答。\n上下文：{context}\n问题：{question}\n回答："
    )
    with_retrieval_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | with_retrieval_prompt
        | model
        | parser
    )

    query = "ChainQA 的检索链是怎么工作的？"

    print(f"问题：{query}\n")

    print("--- 无检索（模型凭自身知识回答）---")
    r1 = no_retrieval_chain.invoke({"question": query})
    print(f"回答：{r1[:100]}...\n")

    print("--- 有检索（基于知识库回答）---")
    r2 = with_retrieval_chain.invoke(query)
    print(f"回答：{r2[:100]}...\n")

    print("说明：有检索时，模型能基于知识库给出准确答案；无检索时可能瞎编或说不知道\n")


def demo_format_docs() -> None:
    """演示检索结果的格式化处理。"""
    print("=" * 60)
    print("【检索结果格式化处理】\n")

    vectorstore = create_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 把多个 Document 格式化为一个字符串
    def format_docs(docs: list[Document]) -> str:
        return "\n\n".join(f"[来源 {d.metadata['source']}] {d.page_content}" for d in docs)

    model = get_model()
    parser = StrOutputParser()
    prompt = ChatPromptTemplate.from_template(
        "根据以下资料回答。\n资料：\n{context}\n\n问题：{question}\n回答："
    )

    # 用 RunnableLambda 包装格式化函数
    from langchain_core.runnables import RunnableLambda

    chain = (
        {
            "context": retriever | RunnableLambda(format_docs),  # 检索后格式化
            "question": RunnablePassthrough(),
        }
        | prompt
        | model
        | parser
    )

    query = "ChainQA 用什么向量库？"
    print(f"问题：{query}")
    result = chain.invoke(query)
    print(f"回答：{result}\n")


class RetrievalQAChain:
    """检索问答链封装类。

    封装「查询 → 检索 → 生成回答」的完整流程，
    这是 RAG（检索增强生成）的基础模式。
    """

    def __init__(self, retriever=None, model=None) -> None:
        self.retriever = retriever or create_vectorstore().as_retriever(search_kwargs={"k": 3})
        self.model = model or get_model()
        self.parser = StrOutputParser()
        self.chain = self._build_chain()

    def _build_chain(self):
        """构建检索问答链。"""
        prompt = ChatPromptTemplate.from_template(
            "你是 ChainQA 智能问答助手。根据以下上下文回答问题。"
            "若上下文无相关信息，请说明无法从知识库找到答案。\n\n"
            "上下文：\n{context}\n\n问题：{question}\n回答："
        )

        return (
            {
                "context": self.retriever,
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.model
            | self.parser
        )

    def ask(self, question: str) -> str:
        """提问并获取回答。"""
        return self.chain.invoke(question)

    def ask_with_context(self, question: str) -> dict:
        """提问并返回回答 + 检索到的上下文。"""
        # 先检索
        docs = self.retriever.invoke(question)
        # 再生成
        answer = self.chain.invoke(question)
        return {
            "question": question,
            "answer": answer,
            "context_docs": [{"source": d.metadata["source"], "content": d.page_content} for d in docs],
        }


def demo_retrieval_qa_chain_class() -> None:
    """演示 RetrievalQAChain 封装类。"""
    print("=" * 60)
    print("【RetrievalQAChain 封装类（RAG 基础模式）】\n")

    qa_chain = RetrievalQAChain()

    questions = [
        "ChainQA 是什么？",
        "ChainQA 默认用什么记忆策略？",
        "ChainQA 用什么模型？",
    ]

    for q in questions:
        print(f"问题：{q}")
        result = qa_chain.ask_with_context(q)
        print(f"回答：{result['answer'][:80]}...")
        print(f"参考文档数：{len(result['context_docs'])}\n")


def main() -> None:
    demo_runnable_passthrough()
    demo_retrieval_chain()
    demo_with_without_retrieval()
    demo_format_docs()
    demo_retrieval_qa_chain_class()
    print("=" * 60)
    print("检索器与 Chain 集成演示完成。")
    print("注：这是 RAG 的基础模式，深入 RAG 系统设计在后续独立板块。")


if __name__ == "__main__":
    main()
