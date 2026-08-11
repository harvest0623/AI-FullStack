# 文件用途：LLM（旧式文本模型）实例化与 ChatModel 对比
# 展示 LLM vs ChatModel 的差异、消息类型、字符串转消息列表
# 标注 LLM 已不推荐使用，现代开发请用 ChatModel

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 1. 消息类型详解
# ============================================================
def demo_message_types():
    """展示 LangChain 的消息类型体系"""
    print("=" * 60)
    print("【1】消息类型详解")
    print("=" * 60)

    from langchain_core.messages import (
        SystemMessage,
        HumanMessage,
        AIMessage,
        ChatMessage,
    )

    # SystemMessage：系统设定（角色/规范/护栏）
    sys_msg = SystemMessage(content="你是一个翻译助手，只输出翻译结果。")
    print(f"SystemMessage  | type={sys_msg.type} | content={sys_msg.content}")

    # HumanMessage：用户输入
    human_msg = HumanMessage(content="把'你好世界'翻译成英文")
    print(f"HumanMessage   | type={human_msg.type} | content={human_msg.content}")

    # AIMessage：LLM 回复（用于对话历史）
    ai_msg = AIMessage(content="Hello World")
    print(f"AIMessage      | type={ai_msg.type} | content={ai_msg.content}")

    # ChatMessage：自定义角色消息
    custom_msg = ChatMessage(role="translator", content="Hola Mundo")
    print(f"ChatMessage    | type={custom_msg.type} | role={custom_msg.role} | content={custom_msg.content}")

    print("\n消息类型对比：")
    print("┌──────────────┬──────────────┬──────────────────────────┐")
    print("│ 类型         │ role         │ 用途                     │")
    print("├──────────────┼──────────────┼──────────────────────────┤")
    print("│ SystemMessage│ system       │ 设定角色/规范/护栏        │")
    print("│ HumanMessage │ human        │ 用户输入                  │")
    print("│ AIMessage    │ ai           │ LLM 回复（对话历史）     │")
    print("│ ChatMessage  │ 自定义       │ 特殊角色消息             │")
    print("└──────────────┴──────────────┴──────────────────────────┘\n")


# ============================================================
# 2. 字符串转消息列表
# ============================================================
def demo_string_to_messages():
    """字符串与消息列表的转换"""
    print("=" * 60)
    print("【2】字符串转消息列表")
    print("=" * 60)

    from langchain_core.messages import HumanMessage

    # ChatModel 接受多种输入格式
    # 方式 1：直接字符串（自动转为 HumanMessage）
    text_input = "什么是 LangChain？"
    print(f"输入 1（字符串）：{text_input}")

    # 方式 2：单条 HumanMessage
    msg_input = HumanMessage(content="什么是 LangChain？")
    print(f"输入 2（HumanMessage）：{msg_input}")

    # 方式 3：消息列表（推荐，支持多角色）
    list_input = [
        HumanMessage(content="什么是 LangChain？"),
    ]
    print(f"输入 3（消息列表）：{list_input}")

    print("\n推荐使用消息列表，可灵活组合多角色消息。\n")


# ============================================================
# 3. ChatModel 调用（推荐方式）
# ============================================================
def demo_chat_model():
    """ChatModel 调用演示（推荐方式）"""
    print("=" * 60)
    print("【3】ChatModel 调用（推荐）")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 使用消息列表（支持 System 设定）
    messages = [
        SystemMessage(content="你是一个翻译助手，只输出翻译结果，不加任何解释。"),
        HumanMessage(content="把'你好，世界'翻译成英文"),
    ]

    result = model.invoke(messages)
    print(f"输入：你好，世界")
    print(f"输出：{result.content}")
    print(f"返回类型：{type(result).__name__}（含 content / usage_metadata 等元数据）\n")


# ============================================================
# 4. LLM 旧式调用（已废弃，仅作了解）
# ============================================================
def demo_legacy_llm():
    """LLM 旧式调用（已废弃，仅作了解）"""
    print("=" * 60)
    print("【4】LLM 旧式调用（⚠️ 已废弃，仅作了解）")
    print("=" * 60)

    print("⚠️  警告：LLM 类已不推荐使用！")
    print("   原因：")
    print("   1. 现代模型（GPT-4o / Claude 3.5）只提供 Chat 接口")
    print("   2. LLM 不支持 System 角色设定")
    print("   3. 返回纯字符串，缺少 usage_metadata 等元数据")
    print("   4. LangChain 官方推荐使用 ChatModel\n")

    print("LLM vs ChatModel 对比：")
    print("┌────────────┬─────────────────────┬────────────────────────────┐")
    print("│ 维度       │ LLM（旧）           │ ChatModel（新）            │")
    print("├────────────┼─────────────────────┼────────────────────────────┤")
    print("│ 基类       │ BaseLLM             │ BaseChatModel              │")
    print("│ 输入       │ 纯字符串            │ 消息列表（带角色）          │")
    print("│ 输出       │ 字符串              │ AIMessage（含元数据）       │")
    print("│ 角色支持   │ ❌ 无               │ ✅ System/Human/AI         │")
    print("│ 多轮对话   │ ❌ 不支持           │ ✅ 原生支持                │")
    print("│ Token 用量 │ ❌ 需手动计算       │ ✅ usage_metadata 自带     │")
    print("│ 推荐度     │ ⚠️ 不推荐           │ ✅ 推荐                    │")
    print("└────────────┴─────────────────────┴────────────────────────────┘\n")

    # 展示 LLM 的调用方式（注释掉，因为需要旧版模型）
    print("LLM 旧式调用示例（仅供参考，不实际运行）：")
    print("""
    # from langchain_community.llms import OpenAI
    # llm = OpenAI(model="gpt-3.5-turbo-instruct")  # 旧模型
    # result = llm.invoke("解释什么是机器学习")
    # # result 是纯字符串，不含元数据
    """)
    print("✅ 请始终使用 ChatModel（如 ChatOpenAI）替代 LLM。\n")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day02 - LLM 与 ChatModel 对比\n")

    demo_message_types()
    demo_string_to_messages()
    demo_chat_model()
    demo_legacy_llm()

    print("=" * 60)
    print("✅ 对比演示完成")
    print("总结：")
    print("  - LLM 已废弃，现代开发请用 ChatModel")
    print("  - ChatModel 支持多角色消息（System/Human/AI）")
    print("  - AIMessage 包含丰富的元数据（usage/response_metadata）")
    print("=" * 60)
