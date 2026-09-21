# -*- coding: utf-8 -*-
"""
文件用途：Day07 - astream_events 事件流订阅
特点：
  1. 用 astream_events() 订阅 on_chat_model_stream 等模型级事件
  2. 观察事件结构中 event / name / run_id / tags 等字段
  3. 演示按 event 类型或 tags 过滤事件
  4. async 迭代器用法
场景：订阅 GraphFlow 各分析节点的 LLM 调用，细粒度观察 token 生成
"""

import os, asyncio
from dotenv import find_dotenv, load_dotenv

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from typing import TypedDict

load_dotenv(find_dotenv())
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise SystemExit("本示例需要真实 LLM 调用，请在 .env 配置 OPENAI_API_KEY")


class ReviewState(TypedDict):
    content: str
    conclusion: str


def analyze_node(state: ReviewState) -> dict:
    """分析节点：让 LLM 生成审核结论"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
    msg = llm.invoke(f"请审核以下内容并给出结论：{state['content']}")
    return {"conclusion": msg.content}


def build_graph():
    b = StateGraph(ReviewState)
    # 用 tags 标注这个节点，便于在事件流中精确过滤
    b.add_node("analyze", analyze_node, tags=["graphflow_analyze"])
    b.add_edge(START, "analyze")
    b.add_edge("analyze", END)
    return b.compile()


class EventStreamDemo:
    def __init__(self, graph):
        self.graph = graph

    async def run(self):
        print("订阅 astream_events，等待 on_chat_model_stream 事件…")
        async for event in self.graph.astream_events(
            {"content": "这是一篇关于AI的科技文章"},
            version="v2",
        ):
            kind = event.get("event")
            # 只打印部分我们感兴趣的事件类型
            if kind in ("on_chat_model_stream", "on_chain_start", "on_chat_model_end"):
                print(f"[{kind}] name={event['name']} run_id={str(event.get('run_id'))[:8]} tags={event.get('tags')}")

        print("\n[tips] event 结构包含：event / name / data / tags / metadata / run_id 等字段")
        print("[tips] 通过 tags 过滤可只看某个节点的调用，见 03_typing_effect.py")


async def main_async():
    print("=" * 60)
    print("GraphFlow astream_events 事件流订阅")
    print("=" * 60)
    demo = EventStreamDemo(build_graph())
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main_async())