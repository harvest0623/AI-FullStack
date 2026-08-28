# 文件用途：链式调用模式合集
# 演示顺序模式、并行模式、混合模式、条件分支 RunnableBranch 模式。
# 每种模式含完整代码和适用场景说明。
# 场景：根据问题类型路由到不同处理链（ChainQA 智能路由）

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    RunnableLambda,
    RunnableBranch,
)

load_dotenv()


def get_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def demo_sequential_pattern() -> None:
    """顺序模式：a | b | c，组件依次执行。最基础的流水线。

    适用场景：单一流水线处理，每步依赖上一步输出。
    """
    print("=" * 60)
    print("【顺序模式 a | b | c】")
    print("适用：单一流水线，每步依赖上一步\n")

    model = get_model()
    prompt = ChatPromptTemplate.from_template(
        "你是 ChainQA 助手。用一句话回答：{question}"
    )
    parser = StrOutputParser()

    # 顺序管道
    chain = prompt | model | parser
    result = chain.invoke({"question": "什么是顺序链？"})
    print(f"结果：{result}\n")


def demo_parallel_pattern() -> None:
    """并行模式：RunnableParallel，多个链同时执行，结果合并为字典。

    适用场景：无依赖的多任务，如同时生成答案和摘要。
    """
    print("=" * 60)
    print("【并行模式 RunnableParallel】")
    print("适用：无依赖的多任务并行\n")

    model = get_model()
    parser = StrOutputParser()

    answer_prompt = ChatPromptTemplate.from_template("回答：{question}")
    summary_prompt = ChatPromptTemplate.from_template(
        "用 5 个字总结这个问题：{question}"
    )

    parallel = RunnableParallel({
        "answer": answer_prompt | model | parser,
        "summary": summary_prompt | model | parser,
    })

    result = parallel.invoke({"question": "什么是并行计算？"})
    print(f"answer：{result['answer']}")
    print(f"summary：{result['summary']}\n")


def demo_mixed_pattern() -> None:
    """混合模式：并行 + 顺序组合，先并行收集信息，再顺序处理。

    适用场景：RAG 基础模式——并行收集上下文和问题，再顺序生成回答。
    """
    print("=" * 60)
    print("【混合模式 并行 + 顺序】")
    print("适用：先并行收集，再顺序处理（RAG 基础模式）\n")

    model = get_model()
    parser = StrOutputParser()

    # 模拟检索
    def retrieve(question: str) -> str:
        return "LangChain 提供 LCEL 表达式语言，用管道符组合组件。"

    # 第 1 阶段：并行收集 context 和 question
    collect = RunnableParallel({
        "context": RunnableLambda(lambda x: retrieve(x["question"])),
        "question": RunnablePassthrough(),
    })

    # 第 2 阶段：问答 Prompt
    qa_prompt = ChatPromptTemplate.from_template(
        "根据上下文回答。\n上下文：{context}\n问题：{question}\n回答："
    )

    # 混合组合：并行收集 -> 问答 -> 解析
    chain = collect | qa_prompt | model | parser
    result = chain.invoke({"question": "LCEL 是什么？"})
    print(f"结果：{result}\n")


def demo_branch_pattern() -> None:
    """条件分支模式：RunnableBranch，根据输入选择不同处理链。

    适用场景：根据问题类型路由到不同处理链。
    """
    print("=" * 60)
    print("【条件分支模式 RunnableBranch】")
    print("适用：根据输入类型路由\n")

    model = get_model()
    parser = StrOutputParser()

    # 代码问题链
    code_prompt = ChatPromptTemplate.from_template(
        "你是代码专家。请回答这个代码问题：{question}\n回答："
    )
    code_chain = code_prompt | model | parser

    # 翻译问题链
    translate_prompt = ChatPromptTemplate.from_template(
        "你是翻译专家。请处理这个翻译请求：{question}\n回答："
    )
    translate_chain = translate_prompt | model | parser

    # 默认链
    default_prompt = ChatPromptTemplate.from_template(
        "你是通用助手。回答：{question}\n回答："
    )
    default_chain = default_prompt | model | parser

    # 条件分支：根据问题关键词路由
    branch = RunnableBranch(
        (lambda x: "代码" in x["question"] or "code" in x["question"].lower(), code_chain),
        (lambda x: "翻译" in x["question"] or "translate" in x["question"].lower(), translate_chain),
        default_chain,  # 默认分支
    )

    # 测试三种路由
    test_cases = [
        {"question": "请帮我写一段 Python 代码实现快速排序"},
        {"question": "请把这句话翻译成英文：今天天气很好"},
        {"question": "什么是 LangChain？"},
    ]

    for case in test_cases:
        result = branch.invoke(case)
        print(f"问题：{case['question']}")
        print(f"回答：{result[:80]}...\n")


def demo_dynamic_routing() -> None:
    """动态路由：用 RunnableLambda 先分类，再用 RunnableBranch 路由。

    适用场景：路由逻辑复杂，需要先用 LLM 或规则判断类别。
    """
    print("=" * 60)
    print("【动态路由 Lambda 分类 + Branch 路由】")
    print("适用：复杂路由，先分类再分发\n")

    model = get_model()
    parser = StrOutputParser()

    # 用规则函数分类（实际可用 LLM 分类）
    def classify(question_dict: dict) -> dict:
        q = question_dict["question"].lower()
        if any(kw in q for kw in ["代码", "code", "python", "java"]):
            category = "code"
        elif any(kw in q for kw in ["翻译", "translate", "translate"]):
            category = "translate"
        else:
            category = "general"
        return {**question_dict, "category": category}

    # 三个分支链
    code_prompt = ChatPromptTemplate.from_template("代码专家回答：{question}")
    translate_prompt = ChatPromptTemplate.from_template("翻译专家回答：{question}")
    general_prompt = ChatPromptTemplate.from_template("通用助手回答：{question}")

    chain = (
        RunnableLambda(classify)  # 先分类，添加 category 字段
        | RunnableBranch(
            (lambda x: x["category"] == "code", code_prompt | model | parser),
            (lambda x: x["category"] == "translate", translate_prompt | model | parser),
            general_prompt | model | parser,
        )
    )

    result = chain.invoke({"question": "用 Python 代码读取文件"})
    print(f"问题：用 Python 代码读取文件")
    print(f"回答：{result[:80]}...\n")


def main() -> None:
    """主函数：依次演示四种链式模式 + 动态路由。"""
    demo_sequential_pattern()
    demo_parallel_pattern()
    demo_mixed_pattern()
    demo_branch_pattern()
    demo_dynamic_routing()
    print("=" * 60)
    print("链式调用模式演示完成。")


if __name__ == "__main__":
    main()
