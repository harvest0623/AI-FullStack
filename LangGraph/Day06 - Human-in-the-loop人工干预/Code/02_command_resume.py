# -*- coding: utf-8 -*-
"""
文件用途：Day06 - Command 恢复执行（进阶）
特点：
  1. 深入使用 Command(resume=...) 提供每次 interrupt 的答案
  2. 一个图内可有多处 interrupt，靠 resume 依次恢复
  3. 展示"先检查被中断状态再决定如何恢复"的模式
  4. 不同线程互不干扰地各自恢复
场景：GraphFlow 在多环节（初审 -> 终审）各暂停一次，逐步人工放行
"""

import os
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

load_dotenv(find_dotenv())


class ReviewState(TypedDict):
    content: str
    stage: str          # 当前所处阶段
    flag: str           # 由 interrupt 返回值累积而来
    history: list       # 记录各阶段人工决策
    done: bool


# 阶段一：初审，确定风险
def stage_inspect(state: ReviewState) -> dict:
    # 抛给外部：是否需要进入人工初审
    answer = interrupt("进入人工初审 (approve?)")
    return {"history": state["history"] + [("初审", answer)]}


# 阶段二：终审，二次确认
def stage_review(state: ReviewState) -> dict:
    answer = interrupt("进入人工终审 (approve?)")
    return {"history": state["history"] + [("终审", answer)]}


# 阶段三：完成
def stage_done(state: ReviewState) -> dict:
    return {"done": True, "flag": "completed"}


def build_graph():
    b = StateGraph(ReviewState)
    b.add_node("inspect", stage_inspect)
    b.add_node("review", stage_review)
    b.add_node("done", stage_done)
    b.set_entry_point("inspect")
    b.add_edge("inspect", "review")
    b.add_edge("review", "done")
    b.add_edge("done", END)
    return b.compile(checkpointer=MemorySaver())


class ResumeFlow:
    """封装一次多中断流程的查看与恢复决策"""

    def __init__(self, graph, thread: str):
        self.graph = graph
        self.config = {"configurable": {"thread_id": thread}}

    def inspect(self) -> dict:
        """查看当前被中断位置"""
        s = self.graph.get_state(self.config)
        return {"next": s.next, "values": s.values}

    def provide_answer(self, answer) -> dict:
        """向当前 interrupt 提供答案并恢复"""
        # Command(resume=answer)：answer 会成为对应 interrupt() 的返回值
        return self.graph.invoke(Command(resume=answer), config=self.config)


def main():
    print("=" * 60)
    print("GraphFlow Command(resume) 多中断恢复演示")
    print("=" * 60)
    graph = build_graph()

    a = ResumeFlow(graph, "multi-a")
    # 第一次 invoke：会停在第 1 个 interrupt（初审）
    graph.invoke({"content": "多环节审核样本"}, config=a.config)

    print("\n[第1次] 初始 invoke，待审位于：", a.inspect()["next"])
    # 审阅后提供答案 True
    a.provide_answer(True)
    print("[第2次] resume=True 后待审位于:", a.inspect()["next"])
    # 第二个 interrupt（终审）给 False
    res = a.provide_answer(False)
    print("[第3次] resume=False 后 done =", res["done"])
    print("这条线程的历史 =", a.inspect()["values"]["history"])

    # 另一个线程并行地走完全程
    b = ResumeFlow(graph, "multi-b")
    graph.invoke({"content": "样本B"}, config=b.config)
    b.provide_answer(True)
    b.provide_answer(True)
    print("\n[线程B] 历史 =", b.inspect()["values"]["history"])
    print("[线程A仍在] 历史（不受B影响）=", a.inspect()["values"]["history"])


if __name__ == "__main__":
    main()