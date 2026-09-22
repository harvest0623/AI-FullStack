# -*- coding: utf-8 -*-
"""
文件用途：Day08 - 子图（Subgraph）组合
特点：
  1. 创建一个"单篇审核子流程"子图，编译后作为顶层图的节点复用
  2. 顶层图多次调用子图，每次传入不同 doc
  3. 自定义子图 State 与顶层 State 的字段映射
  4. 子图独立编译、可复用
场景：GraphFlow 的面审核子流程，复用到"内容发布审核"与"举报复核"两个环节
"""

import os
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

load_dotenv(find_dotenv())


# ============================================================
# 一、子图：单篇审核子流程（独立编译）
# ============================================================
class SubState(TypedDict):
    doc: str        # 输入字段
    risk_level: str
    decision: str
    verdict: str    # 输出字段


def sub_analyze(state: SubState) -> dict:
    hits = [w for w in ["赌博", "诈骗", "暴力"] if w in state["doc"]]
    level = "high" if len(hits) >= 2 else ("medium" if hits else "low")
    return {"risk_level": level}


def sub_decide(state: SubState) -> dict:
    lvl = state["risk_level"]
    if lvl == "low":
        decision = "approved"
    elif lvl == "medium":
        decision = "approved"
    else:
        decision = "rejected"
    return {"decision": decision, "verdict": f"[{lvl}]{'通过' if decision == 'approved' else '打回'}"}


def build_subgraph():
    b = StateGraph(SubState)
    b.add_node("sub_analyze", sub_analyze)
    b.add_node("sub_decide", sub_decide)
    b.add_edge(START, "sub_analyze")
    b.add_edge("sub_analyze", "sub_decide")
    b.add_edge("sub_decide", END)
    return b.compile()   # 子图独立编译


# ============================================================
# 二、顶层图：把子图当普通节点使用
# ============================================================
class TopState(TypedDict):
    posts: list[str]        # 待审核内容列表（来源1）
    reports: list[str]      # 待复核的举报（来源2）
    results: list[str]      # 聚合所有子图结果


def review_batch(state: TopState) -> dict:
    """顶层节点：顺序调用子图处理多篇内容（此处演示复用能力）"""
    sub = build_subgraph()
    out = []
    for doc in state["posts"]:
        r = sub.invoke({"doc": doc})
        out.append(doc + " -> " + r["verdict"])
    return {"results": state.get("results", []) + out}


def review_reports(state: TopState) -> dict:
    """另一个环节：同样复用同一个子图"""
    sub = build_subgraph()
    out = []
    for doc in state["reports"]:
        r = sub.invoke({"doc": doc})
        out.append("(举报) " + doc + " -> " + r["verdict"])
    return {"results": state.get("results", []) + out}


def build_top_graph():
    b = StateGraph(TopState)
    b.add_node("review_batch", review_batch)
    b.add_node("review_reports", review_reports)
    b.add_edge(START, "review_batch")
    b.add_edge("review_batch", "review_reports")
    b.add_edge("review_reports", END)
    return b.compile(checkpointer=MemorySaver())   # 顶层图可配 checkpointer


class SubgraphDemo:
    def __init__(self, top):
        self.top = top

    def run(self):
        final = self.top.invoke(
            {"posts": ["普通科技文章", "内容含赌博和诈骗"], "reports": ["被举报的违规贴"]}
        )
        print("两个环节复用同一子图的审核结果：")
        for r in final["results"]:
            print("   ", r)


def main():
    print("=" * 60)
    print("GraphFlow 子图组合演示（审核子流程复用）")
    print("=" * 60)
    demo = SubgraphDemo(build_top_graph())
    demo.run()


if __name__ == "__main__":
    main()