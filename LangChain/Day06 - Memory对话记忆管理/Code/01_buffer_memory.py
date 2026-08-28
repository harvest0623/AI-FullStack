# 文件用途：全量与窗口记忆策略演示
# 对比 ConversationBufferMemory（全量保留）与 ConversationBufferWindowMemory(k=3)（滑动窗口），
# 展示两种策略的 Token 消耗和信息保留差异，用 Memory + ChatModel 实现多轮对话。
# 场景：ChainQA 多轮问答

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
)

load_dotenv()


def get_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def demo_buffer_memory() -> None:
    """ConversationBufferMemory：全量保留所有对话历史。

    信息完整，但 Token 消耗线性增长。
    """
    print("=" * 60)
    print("【ConversationBufferMemory 全量保留】\n")

    memory = ConversationBufferMemory(return_messages=True)

    # 模拟 5 轮对话
    conversation = [
        ("我叫张三，是大学生。", "你好，张三同学！"),
        ("我在学习 LangChain。", "LangChain 是很好的 LLM 框架。"),
        ("它有哪些核心组件？", "包括 Model I/O、Prompts、Chains、Memory 等。"),
        ("Memory 有什么用？", "Memory 让 LLM 记住对话历史。"),
        ("我叫什么名字？", "你叫张三。"),  # 依赖第 1 轮的信息
    ]

    for user_input, ai_output in conversation:
        memory.save_context({"input": user_input}, {"output": ai_output})

    # 查看完整历史
    messages = memory.chat_memory.messages
    print(f"保留的消息总数：{len(messages)} 条")
    print(f"历史消息内容：")
    for msg in messages:
        role = "用户" if msg.type == "human" else "AI"
        print(f"  [{role}] {msg.content}")

    # Token 消耗估算（粗略：中文 1 字 ≈ 1-2 token）
    total_chars = sum(len(m.content) for m in messages)
    print(f"\n历史消息总字符数：{total_chars}（Token 消耗线性增长）")
    print("说明：全量保留，5 轮后仍能回答第 1 轮的姓名问题\n")


def demo_window_memory() -> None:
    """ConversationBufferWindowMemory(k=3)：只保留最近 3 轮。

    Token 消耗可控，但超出窗口的旧信息会丢失。
    """
    print("=" * 60)
    print("【ConversationBufferWindowMemory(k=3) 滑动窗口】\n")

    memory = ConversationBufferWindowMemory(k=3, return_messages=True)

    # 同样 5 轮对话
    conversation = [
        ("我叫张三，是大学生。", "你好，张三同学！"),
        ("我在学习 LangChain。", "LangChain 是很好的 LLM 框架。"),
        ("它有哪些核心组件？", "包括 Model I/O、Prompts、Chains、Memory 等。"),
        ("Memory 有什么用？", "Memory 让 LLM 记住对话历史。"),
        ("我叫什么名字？", "（窗口外，模型不知道）"),
    ]

    for user_input, ai_output in conversation:
        memory.save_context({"input": user_input}, {"output": ai_output})

    messages = memory.chat_memory.messages
    print(f"k=3，实际保留消息数：{len(messages)} 条（最近 3 轮 = 6 条消息）")
    print(f"保留的历史：")
    for msg in messages:
        role = "用户" if msg.type == "human" else "AI"
        print(f"  [{role}] {msg.content}")

    print("\n说明：第 1 轮的姓名信息已被丢弃，模型无法回答'我叫什么'")
    print("优势：Token 消耗有固定上限，不会因对话变长而超限\n")


def demo_memory_with_chat() -> None:
    """用 Memory + ChatModel + LCEL 实现多轮对话。

    展示记忆如何让模型"记住"上下文。
    """
    print("=" * 60)
    print("【Memory + LCEL 多轮对话】\n")

    model = get_model()
    memory = ConversationBufferMemory(return_messages=True)

    # 带历史占位的 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 助手。请根据对话历史回答用户问题。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    parser = StrOutputParser()

    def chat(user_input: str) -> str:
        # 从 memory 加载历史
        history = memory.chat_memory.messages
        # 调用链
        response = (prompt | model | parser).invoke({
            "history": history,
            "input": user_input,
        })
        # 保存到 memory
        memory.save_context({"input": user_input}, {"output": response})
        return response

    # 第 1 轮
    r1 = chat("我叫张三，今年 20 岁。")
    print(f"用户：我叫张三，今年 20 岁。")
    print(f"AI：{r1}\n")

    # 第 2 轮（依赖第 1 轮）
    r2 = chat("我叫什么名字？多大了？")
    print(f"用户：我叫什么名字？多大了？")
    print(f"AI：{r2}\n")

    print("说明：第 2 轮能正确回答，因为 Memory 注入了第 1 轮的历史\n")


def compare_token_consumption() -> None:
    """对比两种策略随对话轮数增长的 Token 消耗。"""
    print("=" * 60)
    print("【Token 消耗对比】\n")

    buffer = ConversationBufferMemory(return_messages=True)
    window = ConversationBufferWindowMemory(k=3, return_messages=True)

    print(f"{'轮数':<6}{'Buffer 字符数':<18}{'Window(k=3) 字符数':<20}")
    print("-" * 44)

    for i in range(1, 9):
        user_msg = f"这是第 {i} 轮对话的用户消息。"
        ai_msg = f"这是第 {i} 轮对话的 AI 回复。"
        buffer.save_context({"input": user_msg}, {"output": ai_msg})
        window.save_context({"input": user_msg}, {"output": ai_msg})

        buffer_chars = sum(len(m.content) for m in buffer.chat_memory.messages)
        window_chars = sum(len(m.content) for m in window.chat_memory.messages)
        print(f"{i:<6}{buffer_chars:<18}{window_chars:<20}")

    print("\n结论：Buffer 线性增长，Window 在 k=3 后趋于稳定\n")


def main() -> None:
    demo_buffer_memory()
    demo_window_memory()
    demo_memory_with_chat()
    compare_token_consumption()
    print("=" * 60)
    print("全量与窗口记忆演示完成。")


if __name__ == "__main__":
    main()
