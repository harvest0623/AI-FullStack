# -*- coding: utf-8 -*-
"""
文件用途：Day06 - interrupt 打断与恢复（基础）
特点：
  1. 在节点内调用 interrupt() 让图暂停、返回"待审问题"给外部
  2. 用 get_state() 捕获被 interrupt 打断时的状态
  3. 用 Command(resume=...) 提供人工决策并恢复执行
  4. 演示完整的 中断 -> 查看 -> 恢复 循环
场景：GraphFlow 的审核节点在给出结论前暂停，等待人工确认
"""

import os
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

load_dotenv(find_dotenv())
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("[警告] 未配置 OPENAI_API_KEY，本示例以纯规则逻辑演示。\n")


class ReviewState(TypedDict):
    content: str
    score: int
    risk_level: str
    decision: str   # approve / reject / unknown
    note: str


def analyze(state: ReviewState) -> dict:
    """分析节点：粗判风险等级"""
    content = state["content"]
    if any(w in content for w in ["赌博", "诈骗", "暴力"]):
        level, score = "high", 20
    else:
        level, score = "low", 90
    return {"risk_level": level, "score": score, "note": "analyzed"}


def human_review(state: ReviewState) -> dict:
    """
    人工审核节点：
    - 若为高风险，则 interrupt() 暂停，把问题和 payload 抛给外部；
    - interrupt() 的返回值 = 外部 resume 时传入的决策。
    """
    if state["risk_level"] == "high":
        # 参数：要抛给外部的问题；返回值：恢复时外部提供的答案
        user_input = interrupt(
            {"question": "内容被判为高风险，是否人工复核通过?", "content": state["content"]}
        )
        decision = "approve" if user_input is True else "reject"
    else:
        # 低风险直接放行
        decision = "auto-approve"
    return {"decision": decision, "note": f"reviewed:{decision}"}


def result(state: ReviewState) -> dict:
    """收尾节点"""
    return {"note": state["note"] + " | done"}


def build_graph():
    builder = StateGraph(ReviewState)
    builder.add_node("analyze", analyze)
    builder.add_node("human_review", human_review)
    builder.add_node("result", result)
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "human_review")
    builder.add_edge("human_review", "result")
    builder.add_edge("result", END)
    return builder.compile(checkpointer=MemorySaver())   # interrupt 必须有 checkpoint


def main():
    print("=" * 60)
    print("GraphFlow interrupt 打断与恢复演示")
    print("=" * 60)
    graph = build_graph()
    config = {"configurable": {"thread_id": "human-1"}}

    # 1. 首次 invoke -> 会在 human_review 处遇到 interrupt 而"暂停/未完成"
    out = graph.invoke(
        {"content": "这个群里有赌博和诈骗广告"}, config=config
    )
    # 图未真正结束，返回值里其实没有完整结果，这里展示中断信息
    print("invoke 返回:", out)

    # 2. 捕获被中断时的状态（查看图停在哪、待回答的问题）
    snap = graph.get_state(config)
    print("\n[被打断状态] next =", snap.next)
    print("当前 state.values =", snap.values)

    # 3. 模拟：人工审阅后决定 '批准'，用 Command(resume=True) 恢复
    approved = True
    print("\n[人工决策] 批准 -> Command(resume=True)")
    final = graph.invoke(Command(resume=approved), config=config)
    print("最终 decision  =", final.get("decision"))
    print("最终 note      =", final.get("note"))

    print("\n[对比] 若人工选择'拒绝'，则 decision 会为 reject")
    # 用新 thread 复现一次拒绝分支
    cfg2 = {"configurable": {"thread_id": "human-2"}}
    graph.invoke({"content": "高风险非法内容"}, config=cfg2)
    graph.invoke(Command(resume=False), config=cfg2)
    snap2 = graph.get_state(cfg2)
    print("human-2 decision =", snap2.values.get("decision"))


if __name__ == "__main__":
    main()