# 文件用途：Runnable 核心组件详解
# 演示 RunnablePassthrough 传递输入、RunnableParallel 并行执行、
# RunnableLambda 包装函数、RunnablePassthrough.assign() 添加字段。
# 场景：ChainQA 并行问答 + 检索链

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


def get_model() -> ChatOpenAI:
    """获取 ChatModel 实例。"""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def demo_passthrough() -> None:
    """RunnablePassthrough：将输入原样传递，常用于并行管道中保留原始输入。"""
    print("=" * 60)
    print("【RunnablePassthrough 原样传递】")

    # 单独使用：输入即输出
    passthrough = RunnablePassthrough()
    result = passthrough.invoke({"question": "什么是 LangChain？"})
    print(f"输入：{{'question': '什么是 LangChain？'}}")
    print(f"输出：{result}")  # 原样返回

    # 在并行管道中保留原始问题
    print("\n在并行管道中保留原始输入：")
    chain = RunnableParallel({
        "original": RunnablePassthrough(),  # 原样保留
        "length": RunnableLambda(lambda x: len(x["question"])),  # 计算长度
    })
    result = chain.invoke({"question": "什么是 LangChain？"})
    print(f"输出：{result}\n")


def demo_passthrough_assign() -> None:
    """RunnablePassthrough.assign()：在输入上添加额外字段，不覆盖原输入。"""
    print("=" * 60)
    print("【RunnablePassthrough.assign() 添加字段】")

    # 模拟检索函数
    def mock_retrieve(question: str) -> str:
        return f"关于「{question}」的模拟检索结果"

    # 输入是 dict，添加 context 字段
    chain = RunnablePassthrough().assign(
        context=lambda x: mock_retrieve(x["question"])
    )
    result = chain.invoke({"question": "什么是 LCEL？"})
    print(f"输入：{{'question': '什么是 LCEL？'}}")
    print(f"输出：{result}")  # question 保留，新增 context
    print("说明：assign 保留了原始 question，同时新增了 context 字段\n")


def demo_parallel() -> None:
    """RunnableParallel：并行执行多个 Runnable，输出为字典。"""
    print("=" * 60)
    print("【RunnableParallel 并行执行】")

    model = get_model()

    # 两个不同的 Prompt 链
    answer_prompt = ChatPromptTemplate.from_template(
        "用一句话回答：{question}"
    )
    summary_prompt = ChatPromptTemplate.from_template(
        "把这个问题压缩成关键词（不超过 5 个字）：{question}"
    )
    parser = StrOutputParser()

    answer_chain = answer_prompt | model | parser
    summary_chain = summary_prompt | model | parser

    # 并行执行两条链
    parallel = RunnableParallel({
        "answer": answer_chain,
        "keywords": summary_chain,
    })

    result = parallel.invoke({"question": "什么是 Python？"})
    print(f"问题：什么是 Python？")
    print(f"answer 分支：{result['answer']}")
    print(f"keywords 分支：{result['keywords']}\n")


def demo_lambda() -> None:
    """RunnableLambda：将普通 Python 函数包装为 Runnable，支持 invoke/batch/stream。"""
    print("=" * 60)
    print("【RunnableLambda 包装自定义函数】")

    # 自定义函数：统计字数
    def word_count(text: dict) -> int:
        return len(text["question"].split()) if "question" in text else len(text.split())

    # 包装为 Runnable
    count_runnable = RunnableLambda(word_count)

    # 支持 invoke
    print(f"invoke：{count_runnable.invoke({'question': 'what is langchain'})}")
    # 支持 batch
    print(f"batch：{count_runnable.batch([{'question': 'a b c'}, {'question': 'x y'}])}")

    # 在链中使用 RunnableLambda
    model = get_model()
    prompt = ChatPromptTemplate.from_template("回答：{question}")
    parser = StrOutputParser()

    chain = (
        RunnablePassthrough.assign(
            word_count=RunnableLambda(lambda x: len(x["question"]))
        )
        | prompt
        | model
        | parser
    )
    result = chain.invoke({"question": "什么是 LangChain？"})
    print(f"链输出（assign 添加 word_count 后调用模型）：{result[:60]}...\n")


def demo_combined() -> None:
    """综合示例：并行问答 + 检索链，组合多种 Runnable 组件。"""
    print("=" * 60)
    print("【综合：并行问答 + 检索链】")

    model = get_model()
    parser = StrOutputParser()

    # 模拟检索
    def retrieve(question: str) -> str:
        return "LangChain 是一个 LLM 应用开发框架，支持链式调用、记忆管理、检索增强等。"

    # 并行：同时检索 + 重写问题
    parallel_preprocess = RunnableParallel({
        "context": RunnableLambda(lambda x: retrieve(x["question"])),
        "question": RunnablePassthrough(),  # 原样保留输入 dict
    })

    # 问答 Prompt
    qa_prompt = ChatPromptTemplate.from_template(
        "根据以下上下文回答问题。\n上下文：{context}\n问题：{question}\n回答："
    )

    # 组合：并行预处理 -> 问答 -> 解析
    chain = parallel_preprocess | qa_prompt | model | parser

    result = chain.invoke({"question": "LangChain 是什么？"})
    print(f"回答：{result}\n")


def main() -> None:
    """主函数：依次演示 Runnable 核心组件。"""
    demo_passthrough()
    demo_passthrough_assign()
    demo_parallel()
    demo_lambda()
    demo_combined()
    print("=" * 60)
    print("Runnable 核心组件演示完成。")


if __name__ == "__main__":
    main()
