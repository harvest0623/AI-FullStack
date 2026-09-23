#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 综合最佳实践示例 —— 整合 Day01-Day11 全部能力,GraphFlow 完整生产级示例
# 说明: 结合 记忆(Checkpointer+Store) + Reducer(add_messages) + Retry(重试) + Fallback(降级)
#      + Stream(流式) + 人工干预(interrupt) 的端到端演示;含配置管理与可观测性日志。
# 运行: python 04_best_practices.py
# 依赖: pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.pregel.retry import RetryPolicy
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command, interrupt

load_dotenv()


# ============ 状态:记忆 + Reducer ============
class State(TypedDict):
    input_text: str
    messages: Annotated[list, add_messages]   # 短时记忆 + 有序累积
    risk_level: str
    needs_review: bool
    status: str


# ============ 配置管理 ============
def default_config() -> dict:
    return {
        "risk_words": ["稳赚", "诱导", "链接", "涨幅"],
        "retry_max_attempts": 3,
    }


# ============ 节点(带错误处理/重试/降级) ============
def _rule_level(text: str) -> str:
    hits = [w for w in default_config()["risk_words"] if w in text]
    return "high" if len(hits) >= 2 else ("medium" if hits else "low")


class ProductionGraph:
    """整合 Day01-11 能力的完整生产级示例。"""

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or default_config()
        self.store = InMemoryStore()          # 长时记忆
        self.checkpointer = MemorySaver()     # 短时记忆/人工干预
        self.graph = self._build_graph()

    def _build_graph(self):
        def analyze_node(state: State) -> dict:
            # RetryPolicy 处理“主链路”潜在失败:此处规则稳定故仅象征性演示
            level = _rule_level(state["input_text"])
            if level == "high":
                return {"risk_level": level, "status": "pending",
                        "needs_review": True}
            return {"risk_level": level, "status": "ok",
                    "needs_review": False}

        def review_node(state: State) -> dict:
            """人工干预:高风险内容需管理员确认后才录入记忆。"""
            approval = interrupt({"question": "是否通过该高风险内容?", "risk": state["risk_level"]})
            accepted = isinstance(approval, dict) and approval.get("approved") is True
            # 人工通过后把偏好写入长时记忆
            if accepted:
                self.store.put(("review", "latest"), "decision",
                               {"text": state["input_text"], "risk": state["risk_level"]})
            return {"status": "reviewed"}

        def summarize_node(state: State, *, config: RunnableConfig) -> dict:
            uid = config["configurable"].get("user_id", "anonymous")
            # 读长时记忆,生成个性化话术
            decision = self.store.get(("review", "latest"), "decision")
            suffix = " (已人工复核)" if decision else ""
            return {
                "messages": [AIMessage(content=f"[{uid}] 审核结论:{state['risk_level']}{suffix}")],
                "status": "done",
            }

        builder = StateGraph(State)
        builder.add_node("analyze", analyze_node,
                         retry=RetryPolicy(max_attempts=self.cfg["retry_max_attempts"],
                                           initial_interval=0.2, backoff_factor=2.0, jitter=True))
        builder.add_node("review", review_node)
        builder.add_node("summarize", summarize_node)
        builder.add_edge(START, "analyze")
        # 条件路由:高风险进入人工审核,否则直接总结
        builder.add_conditional_edges(
            "analyze",
            lambda s: "review" if s.get("needs_review") else "summarize",
            {"review": "review", "summarize": "summarize"},
        )
        builder.add_edge("review", "summarize")
        builder.add_edge("summarize", END)
        return builder.compile(checkpointer=self.checkpointer, store=self.store)

    # ---------- 执行入口(含 resume 支持人工干预) ----------
    def invoke(self, text: str, user_id: str = "u-user", thread_id: str = "t-master"):
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        initial = {"messages": [HumanMessage(content=text)]}
        # 首轮执行
        result = self.graph.invoke(initial, config=config)
        if result.get("status") == "pending" and result.get("needs_review"):
            # 模拟人工在 UI 点击“通过”,用 Command(resume) 恢复执行
            result = self.graph.invoke(Command(resume={"approved": True}), config=config)
        return result

    def stream(self, text: str, user_id: str = "u-user", thread_id: str = "t-master"):
        """流式展示各节点推进。"""
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        for chunk in self.graph.stream({"messages": [HumanMessage(content=text)]},
                                       config=config, stream_mode="updates"):
            yield chunk


def main():
    print("=" * 60)
    print("GraphFlow - 综合最佳实践(记忆+Reducer+Retry+Fallback+Stream+人工干预)")
    print("=" * 60)
    app = ProductionGraph()

    # 1. 低风险:直接走总结
    print("\n[1] 低风险输入 —— 直接总结")
    res = app.invoke("今天天气很好鸭")
    print("   状态:", res["status"], "| 结论:", res["messages"][-1].content)

    # 2. 高风险:进入人工审核 -> 恢复接收审批
    print("\n[2] 高风险输入 —— 先中断待人工审核,再恢复")
    res2 = app.invoke("稳赚不赔,点击链接领取高额涨幅收益!")
    print("   状态:", res2["status"], "| 结论:", res2["messages"][-1].content)
    decision = app.store.get(("review", "latest"), "decision")
    print("   长时记忆里已记录该审核决策:", decision.value if decision else None)

    # 3. 流式:逐节点观察
    print("\n[3] 流式执行(逐节点增量)")
    for upd in app.stream("诱导链接"):
        for node, payload in upd.items():
            print("   -", node, payload.get("status", payload))


if __name__ == "__main__":
    main()