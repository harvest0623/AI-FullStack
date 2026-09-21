# -*- coding: utf-8 -*-
"""
文件用途：Day07 - 打字机效果实现
特点：
  1. 为节点打 tags 标注
  2. 用 astream_events 过滤出指定 tag 的 on_chat_model_stream
  3. 从 data["chunk"].content 逐 token 取出文本
  4. 逐个 print(flush=True) 实现实时"打字机"展示
场景：GraphFlow 审核结论逐字实时流式输出到前端/终端
"""

import os, asyncio, time
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
    """结论节点：LLM 生成报告"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
    msg = llm.invoke(f"请用一句话给出这篇内容的审核结论：{state['content']}")
    return {"conclusion": msg.content}


def build_graph():
    b = StateGraph(ReviewState)
    b.add_node("conclusion", analyze_node, tags=["graphflow_conclusion"])
    b.add_edge(START, "conclusion")
    b.add_edge("conclusion", END)
    return b.compile()


class TypingEffectDemo:
    def __init__(self, graph):
        self.graph = graph

    async def stream_with_typing(self):
        print("实时审核结论（打字机效果）：\n")
        async for event in self.graph.astream_events(
            {"content": "AI 在内容安全审核中的应用"}, version="v2"
        ):
            if event.get("event") != "on_chat_model_stream":
                continue
            # 只保留我们打了 tag 的哪个节点产生的 token
            if "graphflow_conclusion" not in (event.get("tags") or []):
                continue
            token = (event.get("data") or {}).get("chunk")
            text = getattr(token, "content", "") or ""
            if text:
                print(text, end="", flush=True)      # flush 立即输出，形成打字机感
                await asyncio.sleep(0.02)            # 人为放慢，便于观察
        print("\n\n[完成] 审核结论已流式输出完毕。")


async def main_async():
    print("=" * 60)
    print("GraphFlow 打字机流式效果演示")
    print("=" * 60)
    demo = create_demo()
    await demo.stream_with_typing()


def create_demo():
    return TypingEffectDemo(build_graph())


if __name__ == "__main__":
    asyncio.run(main_async())