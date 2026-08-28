# 文件用途：复杂多步链
# 演示多步骤管道（问题分析→检索→回答生成）、链的组合与嵌套、
# 错误处理 with_retry + with_fallbacks、链可视化 get_graph。
# 场景：ChainQA 复杂问答链，展示完整的多步推理链。

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    RunnableLambda,
)

load_dotenv()


def get_model(model_name: str = "gpt-4o-mini") -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", model_name),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def demo_multi_step_chain() -> None:
    """多步骤管道：问题分析 → 检索 → 回答生成。

    展示如何把一条复杂链拆分为多个子步骤，每步职责单一。
    """
    print("=" * 60)
    print("【多步骤管道：分析 → 检索 → 生成】\n")

    model = get_model()
    parser = StrOutputParser()

    # 第 1 步：分析问题，提取关键词
    analyze_prompt = ChatPromptTemplate.from_template(
        "分析以下问题，提取 3 个关键词，用逗号分隔：\n问题：{question}\n关键词："
    )
    analyze_chain = analyze_prompt | model | parser

    # 第 2 步：根据关键词检索（这里用模拟函数）
    def retrieve_by_keywords(input_dict: dict) -> dict:
        keywords = input_dict["keywords"]
        # 模拟检索结果
        context = f"基于关键词「{keywords}」检索到的相关资料：LangChain 支持 LCEL 链式调用。"
        return {**input_dict, "context": context}

    # 第 3 步：根据上下文生成回答
    answer_prompt = ChatPromptTemplate.from_template(
        "根据上下文回答问题。\n上下文：{context}\n问题：{question}\n回答："
    )
    answer_chain = answer_prompt | model | parser

    # 组合多步链：分析 -> 添加关键词 -> 检索 -> 生成
    full_chain = (
        RunnablePassthrough.assign(keywords=analyze_chain)  # 添加 keywords 字段
        | RunnableLambda(retrieve_by_keywords)              # 添加 context 字段
        | answer_chain                                       # 生成回答
    )

    result = full_chain.invoke({"question": "LangChain 的核心特性是什么？"})
    print(f"最终回答：{result}\n")


def demo_chain_nesting() -> None:
    """链的组合与嵌套：子链作为父链的组件。

    展示链本身是 Runnable，可以嵌套进更大的链。
    """
    print("=" * 60)
    print("【链的组合与嵌套】\n")

    model = get_model()
    parser = StrOutputParser()

    # 子链 1：生成初版答案
    draft_prompt = ChatPromptTemplate.from_template("简要回答：{question}")
    draft_chain = draft_prompt | model | parser

    # 子链 2：润色答案
    refine_prompt = ChatPromptTemplate.from_template(
        "请润色以下回答，使其更专业、更详细（不超过 100 字）：\n{draft}"
    )
    refine_chain = refine_prompt | model | parser

    # 父链：先生成初稿，再润色
    parent_chain = (
        RunnablePassthrough.assign(draft=draft_chain)  # 子链嵌套
        | refine_chain
    )

    result = parent_chain.invoke({"question": "什么是向量数据库？"})
    print(f"润色后回答：{result}\n")


def demo_retry_and_fallback() -> None:
    """错误处理：with_retry 重试 + with_fallbacks 回退。

    展示如何让链具备容错能力。
    """
    print("=" * 60)
    print("【错误处理 with_retry + with_fallbacks】\n")

    parser = StrOutputParser()
    prompt = ChatPromptTemplate.from_template("回答：{question}")

    # 主模型（可能会失败，例如额度不足）
    primary_model = ChatOpenAI(
        model="gpt-4o",  # 高级模型
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # 备用模型
    fallback_model = ChatOpenAI(
        model="gpt-4o-mini",  # 降级模型
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # 1. with_retry：失败自动重试（最多 3 次）
    robust_model = primary_model.with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,
    )

    # 2. with_fallbacks：主模型重试仍失败时，回退到备用模型
    model_with_fallback = robust_model.with_fallbacks([fallback_model])

    # 构建健壮的链
    chain = prompt | model_with_fallback | parser

    try:
        result = chain.invoke({"question": "什么是重试机制？"})
        print(f"回答：{result[:80]}...\n")
    except Exception as e:
        print(f"链执行失败（所有重试和回退均失败）：{e}\n")


def demo_chain_visualization() -> None:
    """链可视化：get_graph 获取结构，input_schema/output_schema 查看类型。

    展示 LCEL 链自带的可观测能力。
    """
    print("=" * 60)
    print("【链可视化 get_graph】\n")

    model = get_model()
    parser = StrOutputParser()

    prompt = ChatPromptTemplate.from_template("回答：{question}")
    chain = prompt | model | parser

    # 获取链结构图
    graph = chain.get_graph()
    print("链的节点（nodes）：")
    for node_id, node in graph.nodes.items():
        # 跳过图自身的起止节点
        name = node.data.get("name") or node.data.get("__type__", "Unknown")
        print(f"  - {node_id}: {name}")

    print("\n链的边（edges）：")
    for edge in graph.edges:
        print(f"  - {edge.source} -> {edge.target}")

    # 输入输出 Schema
    print(f"\n输入 Schema 字段：{list(chain.input_schema.model_json_schema().get('properties', {}).keys())}")
    print(f"输出 Schema 类型：{chain.output_schema.model_json_schema()}\n")


def demo_chainqa_complex_chain() -> None:
    """ChainQA 复杂问答链：综合多步推理。

    完整流程：问题分类 → 并行（检索 + 问题重写） → 综合回答 → 格式化输出
    """
    print("=" * 60)
    print("【ChainQA 复杂问答链（综合示例）】\n")

    model = get_model()
    parser = StrOutputParser()

    # 子链：问题重写（优化检索效果）
    rewrite_prompt = ChatPromptTemplate.from_template(
        "把以下问题改写为更适合检索的查询语句（直接输出改写结果）：\n{question}"
    )
    rewrite_chain = rewrite_prompt | model | parser

    # 模拟检索
    def retrieve(question: str) -> str:
        return "LangChain 是 LLM 应用开发框架，核心包括 LCEL、Memory、Retrievers、Tools。"

    # 第 1 阶段：并行执行检索 + 问题重写
    parallel_stage = RunnableParallel({
        "context": RunnableLambda(lambda x: retrieve(x["question"])),
        "rewritten": rewrite_chain,
        "question": RunnablePassthrough(),
    })

    # 第 2 阶段：综合上下文生成回答
    answer_prompt = ChatPromptTemplate.from_template(
        "你是 ChainQA 助手。综合以下信息回答用户问题。\n"
        "原始问题：{question}\n"
        "改写问题：{rewritten}\n"
        "检索上下文：{context}\n"
        "回答（专业、简洁）："
    )
    answer_chain = answer_prompt | model | parser

    # 第 3 阶段：格式化输出
    def format_output(answer: str) -> str:
        return f"【ChainQA 回答】\n{answer}\n{'—' * 30}"

    format_chain = RunnableLambda(format_output)

    # 完整链：并行预处理 -> 生成回答 -> 格式化
    full_chain = parallel_stage | answer_chain | format_chain

    result = full_chain.invoke({"question": "LangChain 有哪些核心组件？"})
    print(result)


def main() -> None:
    """主函数：依次演示复杂链的各种技巧。"""
    demo_multi_step_chain()
    demo_chain_nesting()
    demo_retry_and_fallback()
    demo_chain_visualization()
    demo_chainqa_complex_chain()
    print("=" * 60)
    print("复杂多步链演示完成。")


if __name__ == "__main__":
    main()
