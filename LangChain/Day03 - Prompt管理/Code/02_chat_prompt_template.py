# 文件用途：ChatPromptTemplate 多角色模板
# 演示 from_messages 创建（元组方式和消息对象方式）
# System + Human 角色设定 / format_messages 渲染 / 与 ChatModel 配合
# 展示角色体系对输出质量的影响

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 1. from_messages 创建（元组方式）
# ============================================================
def demo_from_messages_tuple():
    """元组列表方式创建 ChatPromptTemplate（推荐）"""
    print("=" * 60)
    print("【1】from_messages 创建（元组方式）")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate

    # 元组列表：(角色, 内容模板)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个{role}，请用{style}的语气回答。"),
        ("human", "{question}"),
    ])

    print(f"  输入变量：{prompt.input_variables}")
    print(f"  消息数量：{len(prompt.messages)}\n")

    # format_messages 渲染为消息列表
    messages = prompt.format_messages(
        role="翻译助手",
        style="简洁",
        question="把'你好世界'翻译成英文",
    )

    print("  渲染后的消息列表：")
    for msg in messages:
        print(f"    {type(msg).__name__}: {msg.content}")
    print()


# ============================================================
# 2. from_messages 创建（消息对象方式）
# ============================================================
def demo_from_messages_objects():
    """消息对象列表方式创建"""
    print("=" * 60)
    print("【2】from_messages 创建（消息对象方式）")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.messages import SystemMessage, HumanMessage

    # 使用消息对象（适合复用已有消息）
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="你是一个专业的技术顾问。"),
        HumanMessage(content="请解释什么是 {technology}。"),
    ])

    print(f"  输入变量：{prompt.input_variables}")

    messages = prompt.format_messages(technology="LCEL")
    print("  渲染结果：")
    for msg in messages:
        print(f"    {type(msg).__name__}: {msg.content}")
    print()


# ============================================================
# 3. from_template 单模板（默认 Human）
# ============================================================
def demo_from_template():
    """单模板方式（默认为 Human 角色）"""
    print("=" * 60)
    print("【3】from_template 单模板")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate

    # 简单场景：只有一个 Human 消息
    prompt = ChatPromptTemplate.from_template("什么是 {topic}？")

    print(f"  输入变量：{prompt.input_variables}")

    messages = prompt.format_messages(topic="LangChain")
    print(f"  消息类型：{type(messages[0]).__name__}")
    print(f"  角色：{messages[0].type}")
    print(f"  内容：{messages[0].content}\n")


# ============================================================
# 4. 多角色对话模板
# ============================================================
def demo_multi_role():
    """多角色对话模板（System + Human + AI + Human）"""
    print("=" * 60)
    print("【4】多角色对话模板")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate

    # 包含对话历史的模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 智能助手，回答专业、简洁。"),
        ("human", "什么是 Python？"),
        ("ai", "Python 是一种通用编程语言。"),
        ("human", "{follow_up}"),  # 用户追问
    ])

    messages = prompt.format_messages(follow_up="它有什么优点？")

    print("  多角色消息：")
    for msg in messages:
        print(f"    [{msg.type}] {msg.content}")
    print()


# ============================================================
# 5. 角色设定对输出的影响
# ============================================================
def demo_role_impact():
    """展示不同 System 设定对输出质量的影响"""
    print("=" * 60)
    print("【5】角色设定对输出的影响")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate

    # 三个不同风格的 System 设定
    prompts = {
        "正式": ChatPromptTemplate.from_messages([
            ("system", "你是正式的商务顾问，用专业术语和严谨的语气回答。"),
            ("human", "{question}"),
        ]),
        "幽默": ChatPromptTemplate.from_messages([
            ("system", "你是幽默的助手，用笑话和比喻来回答问题。"),
            ("human", "{question}"),
        ]),
        "简洁": ChatPromptTemplate.from_messages([
            ("system", "你是一个极简助手，回答不超过 20 字。"),
            ("human", "{question}"),
        ]),
    }

    question = "什么是人工智能？"

    print(f"  同一问题：{question}\n")
    for style, prompt in prompts.items():
        messages = prompt.format_messages(question=question)
        print(f"  [{style}] System 设定：{messages[0].content}")

    print("\n  （运行下方代码可看到实际输出差异）\n")


# ============================================================
# 6. 与 ChatModel 配合使用
# ============================================================
def demo_with_chat_model():
    """ChatPromptTemplate 与 ChatModel 配合"""
    print("=" * 60)
    print("【6】与 ChatModel 配合使用")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser

    # 客服系统模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 客服助手，请专业、亲切地回答用户问题。"),
        ("human", "{question}"),
    ])

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    parser = StrOutputParser()

    # LCEL 管道
    chain = prompt | model | parser

    # 测试不同问题
    questions = [
        "如何注册账号？",
        "支持哪些支付方式？",
    ]

    for q in questions:
        result = chain.invoke({"question": q})
        print(f"  【用户】{q}")
        print(f"  【客服】{result}\n")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day03 - ChatPromptTemplate 多角色模板\n")

    demo_from_messages_tuple()
    demo_from_messages_objects()
    demo_from_template()
    demo_multi_role()
    demo_role_impact()
    demo_with_chat_model()

    print("=" * 60)
    print("✅ ChatPromptTemplate 演示完成")
    print("总结：")
    print("  - from_messages 元组方式：简洁，推荐")
    print("  - from_messages 消息对象方式：灵活，可复用消息")
    print("  - System 角色设定极大影响输出质量")
    print("  - format_messages 生成消息列表，与 ChatModel 完美配合")
    print("=" * 60)
