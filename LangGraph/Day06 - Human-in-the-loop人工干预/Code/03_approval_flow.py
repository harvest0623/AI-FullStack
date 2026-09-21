# -*- coding: utf-8 -*-
"""
文件用途：Day06 - 人工审批工作流（可复用模式）
特点：
  1. 完整审批流程：内容分析 -> 是否需要人工审计 -> interrupt 暂停 -> 批准/拒绝 -> 放行/拦截
  2. 用 get_state 获取待审内容与提问
  3. 用 Command(resume= {"approved": bool, "comment": str}) 传入审批结果
  4. 封装成 ApprovalWorkflow 类，便于在多个业务中复用
场景：GraphFlow 内容发布前的"人工审批门"
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
    doc: str
    risk: str            # low / medium / high
    decision: str        # pending / approved / rejected
    comment: str         # 审批意见
    report: str


def analyze_doc(state: ReviewState) -> dict:
    """风险分析节点"""
    doc = state["doc"]
    hits = [w for w in ["赌博", "诈骗", "成人", "暴力"] if w in doc]
    if len(hits) == 0:
        risk = "low"
    elif len(hits) == 1:
        risk = "medium"
    else:
        risk = "high"
    return {"risk": risk, "report": f"命中关键词: {hits}"}


def approver(state: ReviewState) -> dict:
    """
    审批主体：medium/high 风险必须人工审批。
    interrupt 抛出的 payload 可携带待审内容与理由。
    """
    if state["risk"] == "low":
        return {"decision": "approved", "comment": "低风险自动通过"}

    payload = interrupt(
        {"prompt": "该内容需人工审批", "doc": state["doc"], "risk": state["risk"]}
    )
    approved = bool(payload.get("approved"))
    comment = payload.get("comment", "无意见")
    return {"decision": "approved" if approved else "rejected", "comment": comment}


def gate_outcome(state: ReviewState) -> dict:
    """根据审批结果决定放行还是拦截"""
    if state["decision"] == "approved":
        return {"report": "已放行发布 | " + state["report"]}
    return {"report": "已拦截: " + state["comment"] + " | " + state["report"]}


def build_graph():
    b = StateGraph(ReviewState)
    b.add_node("analyze", analyze_doc)
    b.add_node("approver", approver)
    b.add_node("gate", gate_outcome)
    b.add_edge(START, "analyze")
    b.add_edge("analyze", "approver")
    b.add_edge("approver", "gate")
    b.add_edge("gate", END)
    return b.compile(checkpointer=MemorySaver())


class ApprovalWorkflow:
    """
    可复用的审批流程封装：
      submit -> 图跑到 approver 处 interrupt（若需人工）
      fetch_pending -> 取待审内容
      decide(approved, comment) -> 提交人工决策并恢复
    """

    def __init__(self):
        self.graph = build_graph()
        self._tick = 0

    def new_thread(self) -> dict:
        self._tick += 1
        return {"configurable": {"thread_id": f"wf-{self._tick}"}}

    def submit(self, doc: str):
        cfg = self.new_thread()
        self.graph.invoke({"doc": doc}, config=cfg)
        return self.pending(cfg)

    def pending(self, cfg):
        s = self.graph.get_state(cfg)
        # 若停在 approver，next 会包含 'approver'
        return {"next": s.next, "values": s.values, "cfg": cfg}

    def decide(self, cfg, approved: bool, comment: str):
        return self.graph.invoke(
            Command(resume={"approved": approved, "comment": comment}),
            config=cfg,
        )


def main():
    print("=" * 60)
    print("GraphFlow 人工审批工作流（ApprovalWorkflow）")
    print("=" * 60)
    aw = ApprovalWorkflow()

    # 案例1：低风险，自动通过
    print("\n[案例1] 低风险文档 -------------------")
    info = aw.submit("今天天气很好")
    print(" 一步到位 decision =", info["values"].get("decision"))

    # 案例2：中风险，人工审批后批准
    print("\n[案例2] 中风险文档（人工批准） ---------")
    info = aw.submit("这篇文章提到了'赌博'一词做新闻报道")
    print(" 等待审批，待审 payload =", info["values"].get("report"))
    res = aw.decide(info["cfg"], True, "内容合规，同意发布")
    print(" 恢复后 report =", res["report"], "| decision =", res["decision"])

    # 案例3：高风险，人工拒绝
    print("\n[案例3] 高风险文档（人工拒绝） ---------")
    info = aw.submit("赌博 诈骗 广告 高利贷 全套")
    res = aw.decide(info["cfg"], False, "疑似违规，禁止发布")
    print(" 恢复后 report =", res["report"])


if __name__ == "__main__":
    main()