#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 长时记忆 Store 演示 —— 跨会话读取个人偏好（不依赖任何一次对话）
# 说明: 使用 InMemoryStore，演示 store.put 写入 / store.get 读取 / namespace 分层 / store.search。
# 运行: python 02_long_term_store.py
# 依赖: pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.store.memory import InMemoryStore

load_dotenv()


# ---------------- 状态定义 ----------------
class State(TypedDict):
    messages: Annotated[list, add_messages]


class StoreDemo:
    """长时记忆演示：Store 独立于 thread，跨会话共享用户偏好。"""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        # Store 与 Checkpointer 独立配置；Store 负责长时跨会话数据
        self.store = InMemoryStore()
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        # 节点通过关键字参数 store 拿到被注入的 Long-term Store
        def pref_node(state: State, *, store) -> dict:
            # 业务上假设当前用户;这里从 config 读取,默认演示用户
            user_id = "u-demo-001"
            profile = store.get(("users", user_id), "profile")
            pref = store.get(("users", user_id), "pref")
            bio = profile.value if profile else {}
            p = pref.value if pref else {}

            system = SystemMessage(
                content=(
                    "你是一名内容审核助手 GraphFlow。\n"
                    f"用户画像：{bio}\n用户偏好：{p}\n"
                    "请按此用户的偏好组织审核回复。"
                )
            )
            resp = self.llm.invoke([system, *state["messages"]])
            return {"messages": [resp]}

        builder = StateGraph(State)
        builder.add_node("pref_node", pref_node)
        builder.add_edge(START, "pref_node")
        builder.add_edge("pref_node", "__end__")
        return builder.compile(checkpointer=self.checkpointer, store=self.store)

    def register_user(self, user_id: str, profile: dict, pref: dict) -> None:
        """把用户画像与偏好写入 Store（一次性，跨会话长期生效）。"""
        self.store.put(("users", user_id), "profile", profile)
        self.store.put(("users", user_id), "pref", pref)

    def read_pref(self, user_id: str) -> dict:
        """从 Store 读取某用户的偏好（跨会话）。"""
        item = self.store.get(("users", user_id), "pref")
        return item.value if item else {}

    def analyze(self, text: str, thread_id: str, user_id: str) -> str:
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        result = self.graph.invoke({"messages": [HumanMessage(content=text)]}, config=config)
        return result["messages"][-1].content


def main():
    print("=" * 60)
    print("GraphFlow - 长时记忆（Store 跨会话偏好）")
    print("=" * 60)

    demo = StoreDemo()

    # 1. 注册一位用户的偏好（模拟第一次会话时沉淀下来的长期数据）
    demo.register_user(
        "u-demo-001",
        {"name": "林先生", "sector": "金融"},
        {"lang": "zh", "style": "简洁", "strict_risk": True},
    )
    print("[Store] 已写入用户 u-demo-001 的 profile 与 pref")

    # 2. 两次使用完全不同的 thread（相当于两场独立会话）
    ans1 = demo.analyze("请审核：『这款理财收益稳赚不亏』", thread_id="t-a", user_id="u-demo-001")
    print(f"[会话A] {ans1}")
    ans2 = demo.analyze("再次提醒我加密风险提示", thread_id="t-b", user_id="u-demo-001")
    print(f"[会话B] {ans2} <- 新会话，仍能读取到用户的 style=简洁/strict_risk 偏好")

    # 3. 直接验证跨会话读取
    print(f"\n[Store 读取] u-demo-001 的 pref = {demo.read_pref('u-demo-001')}")

    # 4. 用 search 查看命名空间下的所有 key
    keys = [it.key for it in demo.store.search(("users", "u-demo-001"))]
    print(f"[Store search] users/u-demo-001 下的 key 集合 = {keys}")


if __name__ == "__main__":
    main()