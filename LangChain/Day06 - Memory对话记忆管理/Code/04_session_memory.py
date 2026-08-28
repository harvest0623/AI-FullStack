# 文件用途：多会话记忆与持久化演示
# 演示 RunnableWithMessageHistory 包装 Chain、多 session_id 管理、
# ChatMessageHistory 内存存储、RedisChatMessageHistory 持久化示例、
# 会话切换和清除。SessionManager 类管理多用户会话。
# 场景：ChainQA 多用户会话管理

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import (
    ChatMessageHistory,
    RedisChatMessageHistory,
)

load_dotenv()


def get_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


class SessionManager:
    """多会话记忆管理器。

    管理多个 session_id 对应的对话历史，支持创建、切换、清除。
    """

    def __init__(self) -> None:
        # session_id -> ChatMessageHistory
        self._store: dict[str, ChatMessageHistory] = {}

    def get_history(self, session_id: str) -> ChatMessageHistory:
        """获取（或创建）指定会话的历史。作为 history_factory 使用。"""
        if session_id not in self._store:
            self._store[session_id] = ChatMessageHistory()
        return self._store[session_id]

    def list_sessions(self) -> list[str]:
        """列出所有会话 ID。"""
        return list(self._store.keys())

    def clear_session(self, session_id: str) -> None:
        """清除指定会话的历史。"""
        if session_id in self._store:
            self._store[session_id].clear()
            print(f"会话 {session_id} 已清空")

    def remove_session(self, session_id: str) -> None:
        """彻底删除指定会话。"""
        if session_id in self._store:
            del self._store[session_id]
            print(f"会话 {session_id} 已删除")

    def session_info(self, session_id: str) -> dict:
        """返回会话信息。"""
        if session_id not in self._store:
            return {"session_id": session_id, "exists": False, "message_count": 0}
        msgs = self._store[session_id].messages
        return {
            "session_id": session_id,
            "exists": True,
            "message_count": len(msgs),
            "last_message": msgs[-1].content[:50] if msgs else None,
        }


def build_chain_with_history(manager: SessionManager) -> RunnableWithMessageHistory:
    """构建带历史记忆的 LCEL 链。"""
    model = get_model()
    parser = StrOutputParser()

    # Prompt 中预留 history 占位
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 智能问答助手。请根据对话历史回答用户问题。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])

    chain = prompt | model | parser

    # 用 RunnableWithMessageHistory 包装
    chain_with_history = RunnableWithMessageHistory(
        chain,
        manager.get_history,           # history_factory
        input_messages_key="question",  # 输入中用户问题字段
        history_messages_key="history", # Prompt 中历史占位符
    )
    return chain_with_history


def demo_multi_session() -> None:
    """多会话管理：两个用户各自独立对话。"""
    print("=" * 60)
    print("【多会话管理：session_id 区分用户】\n")

    manager = SessionManager()
    chain = build_chain_with_history(manager)

    # 用户 A 对话
    config_a = {"configurable": {"session_id": "user_A"}}
    print("—— 用户 A 对话 ——")
    r1 = chain.invoke({"question": "我叫张三，今年 20 岁。"}, config=config_a)
    print(f"用户A：我叫张三，今年 20 岁。")
    print(f"AI：{r1}\n")

    # 用户 B 对话（与 A 独立）
    config_b = {"configurable": {"session_id": "user_B"}}
    print("—— 用户 B 对话 ——")
    r2 = chain.invoke({"question": "我叫李四，喜欢编程。"}, config=config_b)
    print(f"用户B：我叫李四，喜欢编程。")
    print(f"AI：{r2}\n")

    # 用户 A 再次提问（验证记忆只属于 A）
    print("—— 用户 A 再次提问 ——")
    r3 = chain.invoke({"question": "我叫什么名字？多大了？"}, config=config_a)
    print(f"用户A：我叫什么名字？多大了？")
    print(f"AI：{r3}\n")

    # 用户 B 提问（B 不应该知道 A 的信息）
    print("—— 用户 B 提问 ——")
    r4 = chain.invoke({"question": "我叫什么名字？"}, config=config_b)
    print(f"用户B：我叫什么名字？")
    print(f"AI：{r4}\n")

    print("说明：两个会话互不干扰，各自记住各自的信息\n")


def demo_session_management() -> None:
    """会话管理操作：查看、清除、切换。"""
    print("=" * 60)
    print("【会话管理操作】\n")

    manager = SessionManager()
    chain = build_chain_with_history(manager)

    # 创建几个会话
    for sid in ["user_001", "user_002", "user_003"]:
        config = {"configurable": {"session_id": sid}}
        chain.invoke({"question": f"你好，我是 {sid}"}, config=config)

    print(f"当前所有会话：{manager.list_sessions()}")
    for sid in manager.list_sessions():
        info = manager.session_info(sid)
        print(f"  {info}")

    # 清除某个会话
    print("\n清除 user_002 的历史：")
    manager.clear_session("user_002")
    print(f"  清除后：{manager.session_info('user_002')}")

    # 删除某个会话
    print("\n删除 user_003：")
    manager.remove_session("user_003")
    print(f"  剩余会话：{manager.list_sessions()}\n")


def demo_redis_persistence() -> None:
    """RedisChatMessageHistory 持久化示例（需 Redis 服务）。

    展示生产环境持久化配置方式。若无 Redis 服务，会打印提示。
    """
    print("=" * 60)
    print("【RedisChatMessageHistory 持久化示例】\n")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    try:
        history = RedisChatMessageHistory(
            session_id="user_001",
            url=redis_url,
        )
        history.add_user_message("你好")
        history.add_ai_message("你好，有什么可以帮你？")

        msgs = history.messages
        print(f"Redis 中保存了 {len(msgs)} 条消息：")
        for m in msgs:
            print(f"  [{m.type}] {m.content}")
        print("\n说明：Redis 持久化后，应用重启仍可恢复对话\n")

    except Exception as e:
        print(f"未连接 Redis（{e.__class__.__name__}）")
        print("说明：生产环境可用 RedisChatMessageHistory 实现持久化")
        print("配置方式：RedisChatMessageHistory(session_id=..., url='redis://...')")
        print("优势：多实例共享、重启不丢失、高性能读写\n")


def demo_persistence_options() -> None:
    """对比各种持久化方案。"""
    print("=" * 60)
    print("【持久化方案对比】\n")

    print(f"{'方案':<14}{'存储':<10}{'特点':<30}{'适用'}")
    print("-" * 70)
    options = [
        ("ChatMessageHistory", "内存", "最快、易失", "开发测试"),
        ("RedisChatMessageHistory", "Redis", "高性能、可共享", "生产多实例"),
        ("SQLChatMessageHistory", "SQL", "可查询、可迁移", "需查询场景"),
        ("MongoDBChatMessageHistory", "MongoDB", "文档型、灵活", "文档存储"),
    ]
    for name, store, feat, scene in options:
        print(f"{name:<14}{store:<10}{feat:<30}{scene}")

    print("\n选择建议：")
    print("  - 开发阶段：用 ChatMessageHistory（内存），简单直接")
    print("  - 生产单机：用 SQLChatMessageHistory，可持久化查询")
    print("  - 生产集群：用 RedisChatMessageHistory，多实例共享\n")


def main() -> None:
    demo_multi_session()
    demo_session_management()
    demo_redis_persistence()
    demo_persistence_options()
    print("=" * 60)
    print("多会话记忆与持久化演示完成。")


if __name__ == "__main__":
    main()
