# 文件用途：Token 预算管理演示
# 演示 ConversationTokenBufferMemory(max_token_limit=500) 精确 Token 控制，
# Token 超限时自动丢弃最早消息，与 BufferWindowMemory 对比。
# 场景：精确控制 Token 成本

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import (
    ConversationTokenBufferMemory,
    ConversationBufferWindowMemory,
)

load_dotenv()


def get_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def demo_token_buffer() -> None:
    """ConversationTokenBufferMemory：按 Token 数管理历史。

    设定 max_token_limit，超限时丢弃最早的消息（先进先出）。
    """
    print("=" * 60)
    print("【ConversationTokenBufferMemory Token 预算管理】\n")

    model = get_model()
    memory = ConversationTokenBufferMemory(
        llm=model,
        max_token_limit=100,  # 设小一点便于观察丢弃
        return_messages=True,
    )

    conversations = [
        ("我叫张三，是北京大学计算机系大三学生，今年 21 岁。", "你好，张三同学！很高兴认识你。"),
        ("我正在学习 LangChain 框架，重点研究 LCEL 链式调用和 Memory 组件。", "LCEL 和 Memory 都是 LangChain 的核心，加油！"),
        ("LCEL 的管道符语法很优雅，prompt | model | parser 一行搞定。", "是的，LCEL 是 LangChain 0.3 的核心表达力。"),
        ("Memory 有五种策略，各有取舍。", "对，Buffer/Window/Summary/SummaryBuffer/TokenBuffer。"),
    ]

    for i, (user_input, ai_output) in enumerate(conversations, 1):
        memory.save_context({"input": user_input}, {"output": ai_output})
        messages = memory.chat_memory.messages
        # 估算当前 Token（用字符数近似）
        token_est = sum(len(m.content) for m in messages)
        print(f"第 {i} 轮后：保留 {len(messages)} 条消息，约 {token_est} 字符")
        for msg in messages:
            role = "用户" if msg.type == "human" else "AI"
            print(f"  [{role}] {msg.content[:30]}...")
        print()

    print("说明：超过 max_token_limit 的最早消息被自动丢弃，Token 始终可控\n")


def demo_token_limit_behavior() -> None:
    """详细演示 Token 超限时的丢弃行为。"""
    print("=" * 60)
    print("【Token 超限丢弃行为】\n")

    model = get_model()
    memory = ConversationTokenBufferMemory(
        llm=model,
        max_token_limit=50,  # 极小预算
        return_messages=True,
    )

    # 逐条添加，观察哪些被保留
    messages = [
        ("消息1：这是第一条很长的用户消息用于测试。", "回复1：第一条回复。"),
        ("消息2：第二条用户消息。", "回复2：第二条回复。"),
        ("消息3：第三条用户消息。", "回复3：第三条回复。"),
    ]

    for i, (u, a) in enumerate(messages, 1):
        memory.save_context({"input": u}, {"output": a})
        kept = memory.chat_memory.messages
        print(f"添加第 {i} 条后，保留 {len(kept)} 条消息：")
        for m in kept:
            role = "用户" if m.type == "human" else "AI"
            print(f"  [{role}] {m.content}")
        print()

    print("结论：max_token_limit 越小，保留的消息越少（最早被丢弃）\n")


def compare_with_window() -> None:
    """与 BufferWindowMemory 对比：Token 控制 vs 轮数控制。"""
    print("=" * 60)
    print("【TokenBuffer vs Window 对比】\n")

    model = get_model()
    token_memory = ConversationTokenBufferMemory(llm=model, max_token_limit=80, return_messages=True)
    window_memory = ConversationBufferWindowMemory(k=2, return_messages=True)

    conversations = [
        ("短消息", "短回复"),
        ("这是一条比较长的用户消息，包含较多内容用于测试 Token 控制。", "这是一条较长的 AI 回复。"),
        ("又一条消息", "又一回复"),
        ("短", "短"),
    ]

    print(f"{'轮数':<6}{'TokenBuffer 消息数':<22}{'Window(k=2) 消息数':<22}")
    print("-" * 50)

    for i, (u, a) in enumerate(conversations, 1):
        token_memory.save_context({"input": u}, {"output": a})
        window_memory.save_context({"input": u}, {"output": a})

        t_count = len(token_memory.chat_memory.messages)
        w_count = len(window_memory.chat_memory.messages)
        print(f"{i:<6}{t_count:<22}{w_count:<22}")

    print("\n对比说明：")
    print("  - TokenBuffer：按 Token 总量裁剪，长短消息一视同仁")
    print("  - Window：按轮数裁剪，不管消息长短")
    print("  - TokenBuffer 更精确控制成本，Window 更简单直观\n")


def demo_cost_control() -> None:
    """演示 Token 预算管理如何控制 API 成本。"""
    print("=" * 60)
    print("【Token 预算与成本控制】\n")

    print("成本控制逻辑：")
    print("  每次调用 LLM 的 Token 消耗 = 系统 Prompt + 历史消息 + 当前问题 + 输出")
    print("  历史消息越长，单次调用成本越高\n")

    model = get_model()
    # 模拟不同预算下的历史 Token
    budgets = [100, 300, 500, 1000]
    print(f"{'max_token_limit':<18}{'历史 Token 上限':<18}{'适用场景'}")
    print("-" * 56)
    scenarios = {
        100: "极低成本，仅保留最近要点",
        300: "低成本，保留近期对话",
        500: "中等成本，平衡上下文",
        1000: "较高成本，保留较多历史",
    }
    for b in budgets:
        print(f"{b:<18}{b:<18}{scenarios[b]}")

    print("\n建议：根据业务对话长度，选择能覆盖核心上下文的最小预算\n")


def main() -> None:
    demo_token_buffer()
    demo_token_limit_behavior()
    compare_with_window()
    demo_cost_control()
    print("=" * 60)
    print("Token 预算管理演示完成。")


if __name__ == "__main__":
    main()
