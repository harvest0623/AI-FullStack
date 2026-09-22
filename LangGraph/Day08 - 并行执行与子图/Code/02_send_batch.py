# -*- coding: utf-8 -*-
"""
文件用途：Day08 - send 动态并行（map-reduce）
特点：
  1. 用 Send API 在执行期动态决定派发多少个 worker
  2. 每个 Send 携带独立的 item 参数
  3. 聚合节点收集所有 worker 的结果
  4. 实现 map-reduce 模式：批量审核多篇文章
场景：GraphFlow 批量审核 N 篇文章，每篇走独立 worker，最后汇总
"""

import os
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import Annotated, TypedDict

load_dotenv(find_dotenv())


def collect_reducer(left, right):
    """Reducer：累积各 worker 的输出，形成一个列表（map-reduce 的 reduce 侧）"""
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


# 顶层图状态：results 使用 reducer 累积 worker 的每一个结论
class ItemState(TypedDict):
    items: list[str]                      # 待审核文章列表
    results: Annotated[list, collect_reducer]  # worker 结论累积
    note: str                             # 汇总摘要


def planner(state: ItemState) -> list[Send]:
    """
    规划节点：为每个 item 派发一个 Send 到 worker。
    返回 Send 列表 -> LangGraph 动态创建 worker 并行执行（map 侧）。
    """
    return [Send("worker", {"item": item}) for item in state["items"]]


def worker(state: dict) -> dict:
    """
    worker：处理单篇文章。
    注意：返回值必须写入顶层图的字段（这里是 results），
    reducer 会把各 worker 的片段累积进去。
    """
    item = state["item"]
    verdict = "通过" if "违规" not in item else "拦截"
    return {"results": [f"《{item}》-> {verdict}"]}


def aggregator(state: ItemState) -> dict:
    """聚合节点：把累计的 results 整理成统一汇报字符串（reduce 汇总侧）"""
    collected = state.get("results") or []
    joined = "；".join(collected)
    return {"note": f"共审核 {len(collected)} 篇: " + joined} if joined else {"note": "无待审"}


class SendBatchDemo:
    def __init__(self, graph):
        self.graph = graph

    def run(self, articles):
        print(f"\n[批量审核] 共 {len(articles)} 篇文章")
        state = self.graph.invoke({"items": articles})
        note = state.get("note", "")
        print("  摘要 ->", note)


def build_graph():
    b = StateGraph(ItemState)
    b.add_node("planner", planner)
    b.add_node("worker", worker)
    b.add_node("aggregator", aggregator)
    b.add_edge(START, "planner")
    # planner 通过条件边动态分发给任意数量的 worker
    b.add_conditional_edges("planner", lambda s: s.get("items", []), ["worker"])
    b.add_edge("worker", "aggregator")
    b.add_edge("aggregator", END)
    return b.compile()


def main():
    print("=" * 60)
    print("GraphFlow send 动态并行批量审核（map-reduce）")
    print("=" * 60)
    demo = SendBatchDemo(build_graph())
    demo.run(["科技新闻", "违规内容夹杂广告", "娱乐资讯", "健康科普"])
    demo.run(["只用一篇文章也能跑", "含违规的二次示例"])


if __name__ == "__main__":
    main()