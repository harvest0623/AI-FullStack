# -*- coding: utf-8 -*-
"""
文件用途：Day08 - 并行节点（fan-out / fan-in）
特点：
  1. 一个起始节点 fan-out 到多个并行分析节点（安全检测 / 情感分析 / 主题分类）
  2. 并行节点 fan-in 汇集到聚合节点
  3. 观察并行执行中每步状态（用 stream_mode 追踪）
  4. 需节点间无依赖，LangGraph 自动并发执行
场景：GraphFlow 对同一篇内容同时做安全检测 + 情感分析 + 主题分类
"""

import os
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from typing import TypedDict

load_dotenv(find_dotenv())


class ReviewState(TypedDict):
    content: str
    safety: str
    sentiment: str
    topic: str
    summary: str


def entry(state: ReviewState) -> dict:
    """入口节点：截断一下内容，作为三个并行分析的统一输入"""
    content = state["content"][:50]
    return {"content": content}


# ---- 三个可并行的独立分析节点（彼此无依赖） ----
def analyze_safety(state: ReviewState) -> dict:
    risk = "风险" if any(w in state["content"] for w in ["赌博", "诈骗"]) else "安全"
    return {"safety": f"安全检测:{risk}"}


def analyze_sentiment(state: ReviewState) -> dict:
    s = "正面" if "开心" in state["content"] else "中性"
    return {"sentiment": f"情感:{s}"}


def analyze_topic(state: ReviewState) -> dict:
    return {"topic": "主题:科技"}


# ---- 聚合节点：收集并行结果 ----
def aggregate(state: ReviewState) -> dict:
    merged = f"{state['safety']} | {state['sentiment']} | {state['topic']}"
    return {"summary": "综合结论 -> " + merged}


class ParallelNodes:
    def __init__(self, graph):
        self.graph = graph
        self.cfg = {"configurable": {"thread_id": "par-1"}}

    def run(self):
        print("[结果] 综合结论：")
        final = self.graph.invoke({"content": "开心的AI科技文章（无违规）"}, config=self.cfg)
        print(" ", final["summary"])

        print("\n[执行过程] 用 stream_mode='values' 观察每个节点后的状态：")
        seen = 0
        for chunk in self.graph.stream(
            {"content": "开心的AI科技文章（无违规）"}, config=self.cfg, stream_mode="values"
        ):
            changed = {k: v for k, v in chunk.items() if k in ("safety", "sentiment", "topic")}
            if changed:
                seen += 1
                print(f"   已就绪 {seen}/3 个分支: {list(changed.keys())}")


def build_graph():
    b = StateGraph(ReviewState)
    b.add_node("entry", entry)
    b.add_node("safety", analyze_safety)
    b.add_node("sentiment", analyze_sentiment)
    b.add_node("topic", analyze_topic)
    b.add_node("aggregate", aggregate)

    b.add_edge(START, "entry")
    # fan-out：entry 分发给三个并行节点
    b.add_edge("entry", "safety")
    b.add_edge("entry", "sentiment")
    b.add_edge("entry", "topic")
    # fan-in：三个并行节点汇入 aggregate
    b.add_edge("safety", "aggregate")
    b.add_edge("sentiment", "aggregate")
    b.add_edge("topic", "aggregate")
    b.add_edge("aggregate", END)
    return b.compile()


def main():
    print("=" * 60)
    print("GraphFlow 并行节点（安全检测+情感+主题）演示")
    print("=" * 60)
    demo = ParallelNodes(build_graph())
    demo.run()


if __name__ == "__main__":
    main()