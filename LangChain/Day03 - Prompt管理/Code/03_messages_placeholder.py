# 文件用途：MessagesPlaceholder 动态消息
# 演示 MessagesPlaceholder 插入对话历史 / 多轮对话模板设计 / 动态拼接 Few-Shot 示例
# 场景：带历史记录的问答链

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 1. MessagesPlaceholder 基础
# ============================================================
def demo_messages_placeholder_basic():
    """MessagesPlaceholder 基础用法"""
    print("=" * 60)
    print("【1】MessagesPlaceholder 基础")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    # 问题：固定模板无法插入可变长度的历史消息
    # 解决：MessagesPlaceholder 动态插入消息列表

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个问答助手，请结合历史对话回答问题。"),
        MessagesPlaceholder(variable_name="history"),  # 动态历史
        ("human", "{question}"),
    ])

    print(f"  输入变量：{prompt.input_variables}")
    print(f"  MessagesPlaceholder 占位：history\n")

    # 渲染：传入历史消息列表
    from langchain_core.messages import HumanMessage, AIMessage

    messages = prompt.format_messages(
        history=[
            HumanMessage(content="什么是 Python？"),
            AIMessage(content="Python 是一种通用编程语言。"),
        ],
        question="它有什么优点？",
    )

    print("  渲染后的消息序列：")
    for msg in messages:
        print(f"    [{msg.type}] {msg.content}")
    print()


# ============================================================
# 2. 空历史处理
# ============================================================
def demo_empty_history():
    """空历史消息的处理"""
    print("=" * 60)
    print("【2】空历史消息处理")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是问答助手。"),
        MessagesPlaceholder(variable_name="history", optional=True),  # optional 允许为空
        ("human", "{question}"),
    ])

    # 不传 history 也能工作（因为 optional=True）
    messages = prompt.format_messages(question="什么是 LangChain？")

    print("  空历史的渲染结果：")
    for msg in messages:
        print(f"    [{msg.type}] {msg.content}")
    print()


# ============================================================
# 3. 多轮对话模板设计
# ============================================================
def demo_multi_turn_conversation():
    """多轮对话模板设计"""
    print("=" * 60)
    print("【3】多轮对话模板设计")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage

    # ChainQA 多轮对话模板
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是 ChainQA 智能问答助手。
规范：
1. 结合历史对话上下文回答
2. 不确定时说明并建议查证
3. 回答简洁专业"""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])

    # 模拟 3 轮对话历史
    history = [
        HumanMessage(content="什么是 LangChain？"),
        AIMessage(content="LangChain 是一个 LLM 应用开发框架。"),
        HumanMessage(content="它有哪些核心组件？"),
        AIMessage(content="核心组件包括 Model I/O、Prompts、Parsers、Chains 等。"),
    ]

    # 第 3 轮提问
    messages = qa_prompt.format_messages(
        history=history,
        question="第一个组件 Model I/O 是什么？",
    )

    print("  3 轮对话的消息序列：")
    for msg in messages:
        content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"    [{msg.type}] {content}")
    print()


# ============================================================
# 4. 动态 Few-Shot 示例
# ============================================================
def demo_few_shot():
    """MessagesPlaceholder 动态拼接 Few-Shot 示例"""
    print("=" * 60)
    print("【4】动态 Few-Shot 示例拼接")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage

    # 情感分类模板（含 Few-Shot 示例）
    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是情感分类器，输出 positive 或 negative。"),
        MessagesPlaceholder(variable_name="examples"),  # Few-Shot 示例
        ("human", "分类：{input}"),
    ])

    # 动态提供不同数量的示例
    examples_full = [
        HumanMessage(content="分类：这部电影太精彩了！"),
        AIMessage(content="positive"),
        HumanMessage(content="分类：服务太差了，很失望。"),
        AIMessage(content="negative"),
    ]

    examples_minimal = [
        HumanMessage(content="分类：很好用"),
        AIMessage(content="positive"),
    ]

    # 使用完整示例
    messages_full = classify_prompt.format_messages(
        examples=examples_full,
        input="味道一般，不会再来。",
    )
    print("  完整 Few-Shot 示例：")
    for msg in messages_full:
        print(f"    [{msg.type}] {msg.content}")

    print("\n  精简 Few-Shot 示例：")
    messages_minimal = classify_prompt.format_messages(
        examples=examples_minimal,
        input="味道一般，不会再来。",
    )
    for msg in messages_minimal:
        print(f"    [{msg.type}] {msg.content}")
    print()


# ============================================================
# 5. 与 ChatModel 配合（带历史的问答）
# ============================================================
def demo_with_model():
    """带历史记录的问答链"""
    print("=" * 60)
    print("【5】带历史记录的问答链")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser

    # 模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 助手，结合历史对话回答。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = StrOutputParser()

    chain = prompt | model | parser

    # 第 1 轮（无历史）
    print("  第 1 轮（无历史）：")
    answer1 = chain.invoke({
        "history": [],
        "question": "什么是 Python？",
    })
    print(f"    用户：什么是 Python？")
    print(f"    助手：{answer1}\n")

    # 第 2 轮（带历史）
    print("  第 2 轮（带历史）：")
    answer2 = chain.invoke({
        "history": [
            HumanMessage(content="什么是 Python？"),
            AIMessage(content=answer1),
        ],
        "question": "它和 Java 相比有什么优势？",
    })
    print(f"    用户：它和 Java 相比有什么优势？")
    print(f"    助手：{answer2}\n")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day03 - MessagesPlaceholder 动态消息\n")

    demo_messages_placeholder_basic()
    demo_empty_history()
    demo_multi_turn_conversation()
    demo_few_shot()
    demo_with_model()

    print("=" * 60)
    print("✅ MessagesPlaceholder 演示完成")
    print("总结：")
    print("  - MessagesPlaceholder 插入可变数量的消息")
    print("  - optional=True 允许历史为空")
    print("  - 适用于多轮对话历史和 Few-Shot 示例")
    print("  - 是构建带记忆问答系统的核心组件")
    print("=" * 60)
