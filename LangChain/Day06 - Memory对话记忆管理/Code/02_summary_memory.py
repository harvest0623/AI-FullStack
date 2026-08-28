# 文件用途：摘要记忆策略演示
# 演示 ConversationSummaryMemory（自动摘要）与
# ConversationSummaryBufferMemory（摘要+缓冲），
# 展示摘要生成过程与 Token 消耗对比。
# 场景：长对话自动摘要压缩

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import (
    ConversationSummaryMemory,
    ConversationSummaryBufferMemory,
)

load_dotenv()


def get_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def demo_summary_memory() -> None:
    """ConversationSummaryMemory：用 LLM 自动摘要旧对话。

    每次保存新对话时，LLM 会把旧摘要 + 新对话合并成新摘要。
    """
    print("=" * 60)
    print("【ConversationSummaryMemory 自动摘要】\n")

    model = get_model()
    memory = ConversationSummaryMemory(llm=model, return_messages=True)

    # 初始摘要是空的
    print(f"初始摘要：'{memory.buffer}'\n")

    # 逐轮对话，观察摘要演变
    conversations = [
        ("我叫张三，是北京大学计算机系的学生。", "你好，张三同学！"),
        ("我正在学习 LangChain 框架，主要研究 LCEL 链式调用。", "LCEL 是 LangChain 的核心，加油！"),
        ("我想做一个智能问答助手项目。", "很好的项目，可以用 LangChain 的 Chains 和 Memory 组件。"),
    ]

    for i, (user_input, ai_output) in enumerate(conversations, 1):
        memory.save_context({"input": user_input}, {"output": ai_output})
        print(f"第 {i} 轮对话后摘要：")
        print(f"  {memory.buffer}\n")

    print("说明：三轮对话被压缩成一段摘要，Token 增长缓慢\n")


def demo_summary_buffer_memory() -> None:
    """ConversationSummaryBufferMemory：摘要 + 缓冲。

    设定 Token 预算，超限时自动把旧消息摘要化，新消息保留原文。
    """
    print("=" * 60)
    print("【ConversationSummaryBufferMemory 摘要+缓冲】\n")

    model = get_model()
    # 设定较小的 Token 预算，便于观察摘要触发
    memory = ConversationSummaryBufferMemory(
        llm=model,
        max_token_limit=100,
        return_messages=True,
    )

    conversations = [
        ("我叫张三，是大学生。", "你好，张三同学！"),
        ("我在学 LangChain。", "很棒的选择。"),
        ("LCEL 是什么？", "LangChain Expression Language，用管道符组合组件。"),
        ("它支持流式输出吗？", "支持，所有 Runnable 都有 stream 方法。"),
        ("Memory 有几种策略？", "五种：Buffer/Window/Summary/SummaryBuffer/TokenBuffer。"),
    ]

    for i, (user_input, ai_output) in enumerate(conversations, 1):
        memory.save_context({"input": user_input}, {"output": ai_output})
        messages = memory.chat_memory.messages
        print(f"第 {i} 轮后：")
        print(f"  消息数：{len(messages)}")

        # 检查是否有摘要（前缀消息）
        if messages and "summary" in str(messages[0].content).lower() or memory.moving_summary_buffer:
            print(f"  摘要缓冲：{memory.moving_summary_buffer[:80]}...")
        print()

    print("说明：超过 Token 预算的旧消息被压缩为摘要，新消息保留原文\n")


def compare_token_growth() -> None:
    """对比 Summary 策略与 Buffer 策略的 Token 增长曲线。"""
    print("=" * 60)
    print("【Token 增长对比：Summary vs Buffer】\n")

    model = get_model()
    summary_memory = ConversationSummaryMemory(llm=model, return_messages=True)

    # Buffer 用字符数模拟（不实际调用 LLM 摘要，仅对比）
    buffer_chars = 0
    summary_chars = 0

    print(f"{'轮数':<6}{'Buffer 字符数(模拟)':<22}{'Summary 摘要字符数':<20}")
    print("-" * 48)

    for i in range(1, 6):
        user_msg = f"这是第 {i} 轮对话，包含一些详细信息和背景说明。"
        ai_msg = f"这是第 {i} 轮的回复，内容较为详尽，包含若干要点。"

        # Buffer：线性累加
        buffer_chars += len(user_msg) + len(ai_msg)

        # Summary：实际调用 LLM 摘要（仅演示前几轮，避免过多 API 调用）
        summary_memory.save_context({"input": user_msg}, {"output": ai_msg})
        summary_chars = len(summary_memory.buffer)

        print(f"{i:<6}{buffer_chars:<22}{summary_chars:<20}")

    print("\n结论：Buffer 线性增长，Summary 增长缓慢（被压缩为摘要）\n")


def demo_summary_principle() -> None:
    """演示摘要策略的工作原理。"""
    print("=" * 60)
    print("【摘要策略工作原理】\n")

    print("SummaryMemory 工作流程：")
    print("  1. 新对话产生时，把旧摘要 + 新对话拼接")
    print("  2. 调用 LLM 生成新的合并摘要")
    print("  3. 用新摘要替换旧摘要，丢弃原始消息\n")

    print("SummaryBufferMemory 工作流程：")
    print("  1. 新对话加入缓冲区")
    print("  2. 检查缓冲区总 Token 是否超过 max_token_limit")
    print("  3. 超限时，把最早的几条消息交给 LLM 摘要")
    print("  4. 摘要保存，原消息从缓冲区移除\n")

    print("适用场景对比：")
    print("  - SummaryMemory：超长对话，只关心整体脉络")
    print("  - SummaryBufferMemory：长对话，近期需原文、远期可摘要\n")


def main() -> None:
    demo_summary_memory()
    demo_summary_buffer_memory()
    compare_token_growth()
    demo_summary_principle()
    print("=" * 60)
    print("摘要记忆策略演示完成。")


if __name__ == "__main__":
    main()
