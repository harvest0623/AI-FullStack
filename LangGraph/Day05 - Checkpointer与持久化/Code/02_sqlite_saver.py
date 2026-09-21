# -*- coding: utf-8 -*-
"""
文件用途：Day05 - SQLite 持久化（SqliteSaver）演示
特点：
  1. 使用 SqliteSaver 把状态保存到 SQLite 文件（跨进程持久）
  2. 重启/重新运行本脚本后，历史状态仍在
  3. 用 get_state() 从磁盘恢复某个会话的当前状态
  4. 展示 from_connstring 的用法（文件路径 / :memory:）
场景：GraphFlow 进程崩溃后，从断点恢复此前未完成的审核会话
"""

import os
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv(find_dotenv())

# SQLite 持久化文件（放在本脚本同目录）
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graphflow.db")
THREAD_ID = "review-session-0001"


class ReviewState(TypedDict):
    content: str
    score: int
    risks: list
    approved: bool
    note: str


def safety_check(state: ReviewState) -> dict:
    """检查节点：内容是否含违规词"""
    bad = ["赌博", "诈骗"]
    risks = [f"命中: {w}" for w in bad if w in state["content"]]
    score = max(0, 100 - len(risks) * 50)
    return {"risks": risks, "score": score, "note": "safety_check"}


def finalize(state: ReviewState) -> dict:
    """汇总节点：得出最终结论"""
    ok = state["score"] >= 50
    return {"approved": ok, "note": "finalized:" + str(ok)}


def build_graph():
    builder = StateGraph(ReviewState)
    builder.add_node("safety_check", safety_check)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "safety_check")
    builder.add_edge("safety_check", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile()


class SqlitePersistence:
    """
    封装 SQLite 持久化的读写。
    使用 SqliteSaver.from_connstring() 既可以连文件，也可以连内存。
    """

    def __init__(self, db_path: str):
        # 关键：from_connstring 解析连接串；文件路径会被 `check_str` 保存到磁盘
        self.db_path = db_path

    def run(self):
        # 注意：SqliteSaver 需要作为上下文管理器，结束后才有完整的 db 连接
        with SqliteSaver.from_connstring(self.db_path) as saver:
            graph = build_graph()
            graph = graph.with_config({"configurable": {"thread_id": THREAD_ID}})

            current = graph.get_state(graph.config)   # 查询当前(可能为空)状态
            print(f"当前会话初始状态: values={current.values}")

            # 若尚未审核过该会话，则执行一次审核
            if not current.values.get("content"):
                result = graph.invoke({"content": "这篇文章了赌博相关的内容"})
                print("执行一次审核，结果 approve =", result["approved"])

            # 从磁盘再次读取当前状态（已验证持久化可恢复）
            restored = graph.get_state(graph.config)
            print("\n从 SQLite 恢复出的状态：")
            print("  content =", restored.values.get("content"))
            print("  score   =", restored.values.get("score"))
            print("  risks   =", restored.values.get("risks"))
            print("  approved=", restored.values.get("approved"))


def main():
    print("=" * 60)
    print("GraphFlow SQLite 持久化演示（SqliteSaver）")
    print("=" * 60)
    obj = SqlitePersistence(DB_PATH)
    obj.run()

    print("\n[演示] from_connstring 还支持内存库 :memory: 的用法：")
    mem_saver = SqliteSaver.from_connstring(":memory:")
    print("  内存版 SqliteSaver 已创建，注意它不能跨进程持久化。")


if __name__ == "__main__":
    main()