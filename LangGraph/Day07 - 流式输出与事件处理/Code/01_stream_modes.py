# -*- coding: utf-8 -*-
"""
文件用途：Day07 - 流式输出 stream_mode 对比
特点：
  1. 用 graph.stream() 的 stream_mode 在 "values" / "updates" / "debug" 三种模式间切换
  2. values：每个节点执行后的完整状态
  3. updates：每个节点返回的增量（仅本节点写入的字段）
  4. debug：详尽的调试事件
  5. 观察同一张图在不同 stream_mode 下产出的结构差异
场景：GraphFlow 内容审核各阶段（安全->情感->主题->报告）的状态流转
"""

import os
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(find_dotenv())


class ReviewState(TypedDict):
    content: str
    safety_result: str
    sentiment: str
    topic: str
    report: str


def node_safety(state: ReviewState) -> dict:
    return {"safety_result": "安全" if "违规" not in state["content"] else "风险"}


def node_sentiment(state: ReviewState) -> dict:
    return {"sentiment": "正面" if "开心" in state["content"] else "中性"}


def node_topic(state: ReviewState) -> dict:
    return {"topic": "科技"}


def node_report(state: ReviewState) -> dict:
    return {"report": "已生成报告"}


def build_graph():
    b = StateGraph(ReviewState)
    b.add_node("safety", node_safety)
    b.add_node("sentiment", node_sentiment)
    b.add_node("topic", node_topic)
    b.add_node("report", node_report)
    # 两个节点并行（安全 + 情感 + 主题），再汇到 report
    b.add_edge(START, "safety")
    b.add_edge(START, "sentiment")
    b.add_edge(START, "topic")
    b.add_edge("safety", "report")
    b.add_edge("sentiment", "report")
    b.add_edge("topic", "report")
    b.add_edge("report", END)
    # 绑定 Checkpointer，演示流式执行同样可持久化
    return b.compile(checkpointer=MemorySaver())


class StreamModeDemo:
    def __init__(self, graph):
        self.graph = graph
        self.cfg = {"configurable": {"thread_id": "stream-1"}}

    def show_values(self):
        print("\n[stream_mode='values'] 每个节点后的完整状态：")
        for chunk in self.graph.stream({"content": "开心的科技文章"}, config=self.cfg, stream_mode="values"):
            print("  values keys =", list(chunk.keys()))

    def show_updates(self):
        print("\n[stream_mode='updates'] 每个节点的增量(dict)：")
        for _, chunk in self.graph.stream({"content": "开心的科技文章"}, config=self.cfg, stream_mode="updates"):
            print("  update =", chunk)

    def show_debug(self):
        print("\n[stream_mode='debug'] 详尽调试事件（前 5 条）：")
        count = 0
        for chunk in self.graph.stream({"content": "开心的科技文章"}, config=self.cfg, stream_mode="debug"):
            print("  debug event type =", chunk.get("type"))
            count += 1
            if count >= 5:
                break


def main():
    print("=" * 60)
    print("GraphFlow 流式输出 stream_mode 对比")
    print("=" * 60)
    graph = build_graph()
    demo = StreamModeDemo(graph)
    demo.show_updates()
    demo.show_values()
    demo.show_debug()


if __name__ == "__main__":
    main()