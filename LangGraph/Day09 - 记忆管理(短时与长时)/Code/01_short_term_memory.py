#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 短时记忆（Checkpointer + thread_id）演示 —— 多轮审核对话记住前文
# 说明: 通过 MemorySaver + 相同 thread_id 实现会话内消息累积，从 state 读取历史消息注入 prompt。
# 运行: python 01_short_term_memory.py
# 依赖: pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages

# 加载 .env 中的 API Key
load_dotenv()


# ---------------- 状态定义 ----------------
class State(TypedDict):
    """会话状态。messages 使用 add_messages 累积，实现多轮消息追加而非覆盖。"""
    messages: Annotated[list, add_messages]


# ---------------- 节点 ----------------
def _build_prompt(state: State) -> list:
    """从 state 读取历史消息，注入 SystemMessage，形成有上下文的 Prompt。"""
    history = state["messages"]
    # 取出最后一条用户消息作为本次待分析内容，其余作为上下文
    user_content = ""
    for m in history:
        if isinstance(m, HumanMessage):
            user_content = m.content  # 记录最近一次用户输入
    system = SystemMessage(
        content=(
            "你是一名内容审核助手 GraphFlow，负责对用户提交的内容进行安全性审核。\n"
            f"以下是本次会话的历史对话：\n{history}\n"
            "请结合历史上下文，对最新输入给出审核结论。"
        )
    )
    return [system, HumanMessage(content=user_content)]


class ShortTermMemory:
    """短时记忆演示：同一 thread_id 下，多轮 invoke 状态持续累积。"""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        self.graph = self._build_graph()
        # 生产建议使用 SqliteSaver / PostgresSaver，本示例用内存便于观察
        self.checkpointer = MemorySaver()

    def _build_graph(self):
        def audit_node(state: State) -> dict:
            messages = _build_prompt(state)
            response = self.llm.invoke(messages)
            return {"messages": [response]}

        builder = StateGraph(State)
        builder.add_node("audit", audit_node)
        builder.add_edge(START, "audit")
        builder.add_edge("audit", "__end__")
        return builder.compile(checkpointer=self.checkpointer)

    def chat(self, text: str, thread_id: str = "default") -> str:
        config = {"configurable": {"thread_id": thread_id}}
        # 每次只传最新用户消息，旧消息靠 Checkpointer 自动累积
        result = self.graph.invoke({"messages": [HumanMessage(content=text)]}, config=config)
        ai = result["messages"][-1]
        return ai.content

    def show_history(self, thread_id: str = "default") -> list:
        """用 get_state 查看该会话累积的全部消息。"""
        config = {"configurable": {"thread_id": thread_id}}
        state = self.graph.get_state(config)
        return state.values.get("messages", [])


def main():
    print("=" * 60)
    print("GraphFlow - 短时记忆（会话内上下文累积）")
    print("=" * 60)

    agent = ShortTermMemory()
    tid = "audit-session-001"

    # 第一轮
    print("\n[用户] 请审核这句话是否违规：『今天天气真好』")
    ans1 = agent.chat("请审核这句话是否违规：『今天天气真好』", tid)
    print(f"[助手] {ans1}")

    # 第二轮 —— 引用前一轮,检验记忆是否生效
    print("\n[用户] 那如果加上『滚出去』这个口头禅呢？")
    ans2 = agent.chat("那如果加上『滚出去』这个口头禅呢？", tid)
    print(f"[助手] {ans2}（能理解‘那’指代上一句，说明上下文累积成功）")

    # 展示历史
    print(f"\n[线程 {tid}] 累积的消息数 = {len(agent.show_history(tid))} 条")
    for i, m in enumerate(agent.show_history(tid), 1):
        role = "用户" if m.type == "human" else ("系统" if m.type == "system" else "助手")
        print(f"  {i}. [{role}] {m.content[:40]}")


if __name__ == "__main__":
    main()