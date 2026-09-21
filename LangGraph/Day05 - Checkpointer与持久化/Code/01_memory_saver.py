# -*- coding: utf-8 -*-
"""
文件用途：Day05 - 内存 Checkpointer（MemorySaver）演示
特点：
  1. 使用 MemorySaver 保存每次 invoke 后的中间状态
  2. 通过 thread_id 实现多会话隔离
  3. 同一 thread_id 多次 invoke 共享状态（累积审核记录）
  4. 不同 thread_id 完全隔离
  5. 配置了 Checkpointer 却未提供 thread_id 时的报错处理
场景：GraphFlow 为不同用户持久化各自的审核记录
"""

import os
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from langgraph.checkpoint.memory import MemorySaver


# 加载 .env 中的 API Key（本示例主要演示持久化，LLM 部分为可选展示）
load_dotenv(find_dotenv())
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("[警告] 未在 .env 中配置 OPENAI_API_KEY，示例将以纯逻辑节点运行。\n")


# ---------------------------------------------------------------
# 1. 定义 GraphFlow 审核子流程的状态
# ---------------------------------------------------------------
class ReviewState(TypedDict):
    """一次内容审核的状态"""
    content: str              # 待审核内容
    score: int                # 综合评分
    risks: list               # 检测到的风险点（累积）
    approved: bool            # 是否通过
    note: str                 # 审核备注


# ---------------------------------------------------------------
# 2. 定义节点：执行一次简单的规则审核（无需 LLM 也可运行）
# ---------------------------------------------------------------
def safety_check(state: ReviewState) -> dict:
    """安全检查节点：按敏感词规则打风险分"""
    content = state["content"]
    blocked_words = ["赌博", "诈骗", "暴力", "赌博"]
    risks = []
    for w in set(blocked_words):
        if w in content:
            risks.append(f"命中敏感词: {w}")
    score = 100 - len(risks) * 40          # 每个风险词扣 40 分
    score = max(0, score)
    return {"risks": risks, "score": score, "note": "safety_check 完成"}


def risk_judge(state: ReviewState) -> dict:
    """风险判定节点：根据分数决定是否通过"""
    if state["score"] >= 60:
        return {"approved": True, "note": "低风险，自动通过"}
    return {"approved": False, "note": "高风险，需要人工复核"}


# 组装并编译图（关键：compile 时传入 checkpointer）
def build_graph():
    builder = StateGraph(ReviewState)
    builder.add_node("safety_check", safety_check)
    builder.add_node("risk_judge", risk_judge)
    builder.add_edge(START, "safety_check")
    builder.add_edge("safety_check", "risk_judge")
    builder.add_edge("risk_judge", END)

    # 使用内存 Checkpointer
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    return graph


# ---------------------------------------------------------------
# 3. 会话（Session）类：为不同用户隔离 review 记录
# ---------------------------------------------------------------
class SessionChat:
    """
    用 thread_id 区分不同用户的会话。
    每个用户有独立的审核流，相同内容重复提交会复用状态累积。
    """

    def __init__(self, graph):
        self.graph = graph
        # 为每个用户分配独立的 thread_id
        self._thread_id = {"user-1": "u-1-xxx", "user-2": "u-2-xxx"}

    def config(self, user: str) -> dict:
        # 一个 thread = 一个会话，这里把用户映射为不同的 thread_id
        return {"configurable": {"thread_id": self._thread_id[user]}}

    def submit(self, user: str, content: str) -> dict:
        """用户提交一篇内容进行审核"""
        cfg = self.config(user)
        result = self.graph.invoke({"content": content}, config=cfg)
        return result

    def query(self, user: str) -> dict:
        """查询某用户最后一次审核后的完整状态"""
        cfg = self.config(user)
        return self.graph.get_state(cfg).values


def main():
    graph = build_graph()
    chat = SessionChat(graph)
    print("=" * 60)
    print("GraphFlow 多用户持久化审核记录演示（MemorySaver）")
    print("=" * 60)

    # 4. 同一 thread 多次 invoke 累积状态
    print("\n[场景1] 用户 user-1 连续提交两篇内容，共享同一会话状态")
    r1 = chat.submit("user-1", "今天心情不错（正常内容）")
    print(f"  第1条审核通过: {r1['approved']}  score={r1['score']}")
    r2 = chat.submit("user-1", "教你快速赌博赚大钱（违规内容）")
    print(f"  第2条审核通过: {r2['approved']}  score={r2['score']}  risks={r2['risks']}")
    # 状态里的 risks 是累积的（同一个 thread），能看到两条内容的风险点合并
    print(f"  该用户累积 risks = {chat.query('user-1').get('risks')}")

    # 5. 不同 thread 隔离
    print("\n[场景2] 用户 user-2 的会话与 user-1 隔离")
    r3 = chat.submit("user-2", "欢迎来到我们的平台")
    print(f"  user-2 审核通过: {r3['approved']}  note={r3['note']}")
    print(f"  user-2 的关注内容里没有 user-1 的风险点: risks = {chat.query('user-2').get('risks')}")

    # 6. 无 thread_id 的报错处理
    print("\n[场景3] 配置了 Checkpointer 却不传 thread_id")
    try:
        graph.invoke({"content": "测试"})   # 未提供 config 线程信息
        print("  （未抛错）")
    except Exception as e:
        print(f"  捕获到异常: {type(e).__name__}: {str(e)[:80]}")
        print("  原因：MemorySaver 需要在 config 中指定 thread_id 才能定位会话。")


if __name__ == "__main__":
    main()