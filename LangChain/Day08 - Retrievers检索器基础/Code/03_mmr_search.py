# 文件用途：MMR 搜索实现演示
# 演示 MMR 搜索原理、lambda_mult 参数调优、similarity vs mmr 结果对比、
# 展示 MMR 如何提升多样性。含参数调优实验。
# 场景：ChainQA 检索多样性优化

import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def prepare_documents_with_redundancy() -> list[Document]:
    """准备含冗余内容的文档，便于展示 MMR 的去重效果。"""
    return [
        Document(page_content="LangChain Memory 管理对话历史，五种策略可选。", metadata={"id": 1}),
        Document(page_content="Memory 组件让 LLM 记住对话历史，提供五种策略。", metadata={"id": 2}),
        Document(page_content="对话记忆管理是 Memory 的核心功能，有五种策略。", metadata={"id": 3}),
        Document(page_content="LCEL 用管道符组合组件，是 LangChain 的核心。", metadata={"id": 4}),
        Document(page_content="Retriever 基于向量相似度检索相关文档。", metadata={"id": 5}),
        Document(page_content="Embedding 模型把文本转为向量，用于语义检索。", metadata={"id": 6}),
    ]


def create_vectorstore() -> Chroma:
    """创建向量库。"""
    docs = prepare_documents_with_redundancy()
    return Chroma.from_documents(docs, embedding=get_embeddings())


def explain_mmr_principle() -> None:
    """解释 MMR（最大边际相关性）原理。"""
    print("=" * 60)
    print("【MMR 原理讲解】\n")

    print("MMR = Maximal Marginal Relevance（最大边际相关性）\n")

    print("目标：在「与查询的相关性」和「结果之间的多样性」之间平衡\n")

    print("算法步骤：")
    print("  1. 先用相似度搜索取 fetch_k 个候选文档")
    print("  2. 选入与查询最相关的第 1 个文档")
    print("  3. 之后每步选：argmax [ λ·sim(query, d) - (1-λ)·max(sim(d, 已选)) ]")
    print("     即：既要与查询相关，又要与已选文档差异大")
    print("  4. 重复直到选满 k 个\n")

    print("lambda_mult 参数（λ）：")
    print("  λ=1.0：退化为纯相似度搜索（不考虑多样性）")
    print("  λ=0.5：平衡相关性与多样性（默认）")
    print("  λ=0.0：只考虑多样性（不考虑相关性）\n")

    print("适用场景：")
    print("  - 文档库中有大量相似内容时，避免返回重复信息")
    print("  - 概览性问题，希望结果覆盖不同方面\n")


def demo_similarity_vs_mmr() -> None:
    """similarity vs mmr 结果对比，展示 MMR 去重效果。"""
    print("=" * 60)
    print("【similarity vs mmr 结果对比】\n")

    vectorstore = create_vectorstore()
    query = "Memory 是什么？"

    print(f"查询：{query}")
    print(f"文档库中 id=1,2,3 是关于 Memory 的相似内容（冗余）\n")

    # similarity 搜索
    sim_results = vectorstore.similarity_search(query, k=3)
    print("--- similarity（可能返回相似的 1,2,3）---")
    for doc in sim_results:
        print(f"  id={doc.metadata['id']}: {doc.page_content}")

    # mmr 搜索
    mmr_results = vectorstore.max_marginal_relevance_search(
        query, k=3, fetch_k=6, lambda_mult=0.5
    )
    print("\n--- mmr（去重，返回更多样化的结果）---")
    for doc in mmr_results:
        print(f"  id={doc.metadata['id']}: {doc.page_content}")

    print("\n说明：similarity 倾向返回相似的 1,2,3；mmr 会加入其他不同内容，提升多样性\n")


def demo_lambda_tuning() -> None:
    """lambda_mult 参数调优实验。"""
    print("=" * 60)
    print("【lambda_mult 参数调优】\n")

    vectorstore = create_vectorstore()
    query = "Memory 是什么？"

    print(f"查询：{query}")
    print(f"对比不同 lambda_mult 值的返回结果（k=3, fetch_k=6）\n")

    lambdas = [1.0, 0.7, 0.5, 0.3, 0.0]
    print(f"{'lambda_mult':<14}{'返回 id':<20}{'说明'}")
    print("-" * 60)

    explanations = {
        1.0: "纯相似度，无多样性",
        0.7: "偏重相关性",
        0.5: "平衡（默认）",
        0.3: "偏重多样性",
        0.0: "纯多样性",
    }

    for lam in lambdas:
        results = vectorstore.max_marginal_relevance_search(
            query, k=3, fetch_k=6, lambda_mult=lam
        )
        ids = [doc.metadata["id"] for doc in results]
        print(f"{lam:<14}{str(ids):<20}{explanations[lam]}")

    print("\n结论：")
    print("  - λ 越大，越偏向相关性（可能返回冗余）")
    print("  - λ 越小，越偏向多样性（可能偏离查询）")
    print("  - 默认 0.5 是良好的平衡点\n")


def demo_fetch_k_effect() -> None:
    """fetch_k 参数对 MMR 效果的影响。"""
    print("=" * 60)
    print("【fetch_k 参数影响】\n")

    vectorstore = create_vectorstore()
    query = "Memory 是什么？"

    print(f"查询：{query}")
    print(f"fetch_k 是 MMR 的候选池大小，影响可选范围\n")

    fetch_ks = [3, 4, 6]
    for fk in fetch_ks:
        results = vectorstore.max_marginal_relevance_search(
            query, k=3, fetch_k=fk, lambda_mult=0.5
        )
        ids = [doc.metadata["id"] for doc in results]
        print(f"  fetch_k={fk}: 返回 id={ids}")

    print("\n说明：fetch_k 越大，候选池越大，MMR 有更多选择空间，多样性可能更好")
    print("  但 fetch_k 过大会增加计算开销，通常设为 k 的 3-5 倍\n")


def demo_mmr_with_retriever() -> None:
    """用 as_retriever 配置 MMR 检索器。"""
    print("=" * 60)
    print("【用 as_retriever 配置 MMR 检索器】\n")

    vectorstore = create_vectorstore()

    # 通过 as_retriever 配置 MMR
    mmr_retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 3,
            "fetch_k": 6,
            "lambda_mult": 0.5,
        },
    )

    query = "Embedding 是什么？"
    print(f"查询：{query}")
    results = mmr_retriever.invoke(query)
    print(f"MMR 检索器返回 {len(results)} 个结果：")
    for doc in results:
        print(f"  id={doc.metadata['id']}: {doc.page_content}")
    print()


def best_practices() -> None:
    """MMR 搜索最佳实践。"""
    print("=" * 60)
    print("【MMR 搜索最佳实践】\n")

    print("1. 何时用 MMR：")
    print("   - 文档库有大量相似/重复内容")
    print("   - 希望检索结果覆盖不同方面")
    print("   - 概览性问题（如'介绍一下 X'）\n")

    print("2. 何时用 similarity：")
    print("   - 精确匹配型问题")
    print("   - 文档库内容差异明显")
    print("   - 需要最相关的单一答案\n")

    print("3. 参数推荐：")
    print("   - k：3-5（返回数量）")
    print("   - fetch_k：k 的 3-5 倍（候选池）")
    print("   - lambda_mult：0.5（默认平衡）\n")


def main() -> None:
    explain_mmr_principle()
    demo_similarity_vs_mmr()
    demo_lambda_tuning()
    demo_fetch_k_effect()
    demo_mmr_with_retriever()
    best_practices()
    print("=" * 60)
    print("MMR 搜索演示完成。")


if __name__ == "__main__":
    main()
