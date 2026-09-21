# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 时间旅行与状态回溯演示
特点：
  1. get_state_history() 获取图执行的历史快照（每一步一个状态）
  2. 通过某个历史步的 config 回退到过去
  3. 用 update_state() 修正当时的状态，再重放到最终
  4. 调试回溯：定位并重放一次错误的审核判定
场景：GraphFlow 回溯一次审核的中间步骤，修正被误判为高风险的结论
"""

import os
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(find_dotenv())


class ReviewState(TypedDict):
    content: str
    score: int
    risks: list
    approved: bool
    note: str


def check(state: ReviewState) -> dict:
    """检查节点：这里故意写入一个错误的风险（模拟误判）"""
    content = state["content"]
    risk = "命中: 没错的关键词" if "钱" in content else []
    return {"score": 20, "risks": [risk] if risk else [], "note": "check"}


def judge(state: ReviewState) -> dict:
    """判定节点：score 太低则拒绝"""
    return {"approved": state["score"] >= 60, "note": f"score={state['score']}"}


def build_graph():
    builder = StateGraph(ReviewState)
    builder.add_node("check_a", check)
    builder.add_node("check_b", judge)
    builder.add_edge(START, "check_a")
    builder.add_edge("check_a", "check_b")
    builder.add_edge("check_b", END)
    # 需要 checkpoint 才能获得历史
    return builder.compile(checkpointer=MemorySaver())


class TimeTravelDemo:
    """演示 get_state_history / 回滚 / update_state / 重放完整链路"""

    def __init__(self):
        self.graph = build_graph()
        self.config = {"configurable": {"thread_id": "travel-1"}}

    def run_once(self):
        """正常执行一次审核"""
        self.graph.invoke(
            {"content": "这篇文章能让你快速赚钱，快来了解"}, config=self.config
        )

    def show_history(self):
        """打印每一步的历史快照 config + 状态 values"""
        print("\n[历史快照] 图执行全过程共这几步：")
        steps = list(self.graph.get_state_history(self.config))
        for i, snap in enumerate(steps):
            print(
                f"  步骤{i}  node={snap.next}  "
                f"score={snap.values.get('score')}  approved={snap.values.get('approved')}"
            )
        return steps

    def fix_at(self, steps):
        """用 update_state 修正某一步的状态值"""
        # 找到第一次 check 之后的那个快照（score 被误判为 20）
        target = None
        for snap in steps:
            if "check_a" in snap.metadata.get("writes", {}) if snap.metadata else False:
                target = snap
                break
        if target is None:
            target = steps[-2]   # 兜底：倒数第二步

        print("\n[修正] 手动改成绩：把 score 从 20 改为 90，再继续")
        self.graph.update_state(target.config, {"score": 90}) 


def main():
    print("=" * 60)
    print("GraphFlow 时间旅行（回溯 + 修正 + 重放）演示")
    print("=" * 60)
    demo = TimeTravelDemo()
    demo.run_once()

    print("初次判定结果是高风险（approved=False，score=20）")
    # （可选）按需显示历史
    hist = list(demo.graph.get_state_history(demo.config))
    hist_head = hist[:5]
    demo.discover_missing = hist_head  # 保留给后续步骤

    demo.fix_at(list(hist_head))
    # 查看更新后的最终状态
    final_state = demo.graph.get_state(demo.config)
    print("\n[结果] update_state 之后最终状态：")
    print("  approved =", final_state.values.get("approved"))
    print("  score    =", final_state.values.get("score"))
    print("  (此时该会话的分值已被手工修正为 90)")


if __name__ == "__main__":
    main()