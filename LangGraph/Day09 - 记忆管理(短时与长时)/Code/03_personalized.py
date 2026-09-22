#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 个性化记忆应用 —— 组合短时(thread) + 长时(Store) 生成个性化审核报告
# 说明: 从 config 取 user_id 读写 store；会话内上下文 + 跨会话用户画像，按用户偏好生成输出。
# 运行: python 03_personalized.py
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


class State(TypedDict):
    messages: Annotated[list, add_messages]
    audit_result: str   # 审核结论（覆盖字段）


class PersonalizedGraph:
    """结合短时 + 长时记忆，为 GraphFlow 生成个性化审核报告。"""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        self.store = InMemoryStore()
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        def audit_node(state: State, *, store, config: RunnableConfig) -> dict:
            # 1. 从 config 取当前用户身份
            user_id = config["configurable"].get("user_id", "anonymous")

            # 2. 读跨会话的用户画像/偏好（长时记忆）
            profile_item = store.get(("users", user_id), "profile")
            pref_item = store.get(("users", user_id), "pref")
            profile = profile_item.value if profile_item else {}
            pref = pref_item.value if pref_item else {}

            # 3. 组装提示：短时(历史消息) + 长时(画像/偏好)
            system = SystemMessage(
                content=(
                    "你是内容审核助手 GraphFlow，会结合用户画像给出个性化审核报告。\n"
                    f"用户画像：{profile}\n"
                    f"输出偏好：{pref}\n"
                    "请据此组织报告的篇幅、语气与是否强调风险。"
                )
            )
            resp = self.llm.invoke([system, *state["messages"]])
            return {"messages": [resp], "audit_result": resp.content}

        builder = StateGraph(State)
        builder.add_node("audit", audit_node)
        builder.add_edge(START, "audit")
        builder.add_edge("audit", "__end__")
        return builder.compile(checkpointer=self.checkpointer, store=self.store)

    def set_pref(self, user_id: str, pref: dict) -> None:
        self.store.put(("users", user_id), "pref", pref)

    def set_profile(self, user_id: str, profile: dict) -> None:
        self.store.put(("users", user_id), "profile", profile)

    def analyze(self, text: str, user_id: str, thread_id: str) -> str:
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        result = self.graph.invoke({"messages": [HumanMessage(content=text)]}, config=config)
        return result["audit_result"]


def main():
    print("=" * 60)
    print("GraphFlow - 个性化记忆（短时 + 长时组合）")
    print("=" * 60)

    app = PersonalizedGraph()
    app.set_profile("u-sh", {"name": "王老师", "org": "教育行业"})
    app.set_pref("u-sh", {"lang": "zh", "style": "详细", "educate": True})

    # 同一用户连续两轮 —— thread 内上下文累积
    r1 = app.analyze("请审核：『退学吧，打工也能赚钱』", user_id="u-sh", thread_id="t-sh")
    print(f"[第1轮] {r1}")
    r2 = app.analyze("以上内容如果出现在学生群呢？", user_id="u-sh", thread_id="t-sh")
    print(f"[第2轮] {r2} <- 能记住第1轮的内容，且符合‘详细’风格")


if __name__ == "__main__":
    main()