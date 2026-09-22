#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: add_messages 深度演示 —— 追加/同 id 替换/删除/合并 chunk/自定义字段
# 说明: 不调用 LLM,直接调用 add_messages 展示各类行为,再用一个图演示节点消息有序累积。
# 运行: python 02_add_messages_depth.py
# 依赖: pip install langgraph langchain python-dotenv pydantic

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, RemoveMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]


class AddMessagesDepth:
    """深度演示 add_messages 的各种行为。"""

    @staticmethod
    def demo_append():
        """新 id 消息 -> 追加到尾部。"""
        base = [HumanMessage(content="你好", id="h1")]
        out = add_messages(base, [AIMessage(content="你好,我是助手", id="a1")])
        print("append        :", [m.content for m in out])

    @staticmethod
    def demo_replace():
        """同 id 消息 -> 原地替换旧消息。"""
        base = [HumanMessage(content="v1", id="m1")]
        out = add_messages(base, [HumanMessage(content="v2", id="m1")])
        print("replace       :", [m.content for m in out])

    @staticmethod
    def demo_delete():
        """RemoveMessage(id) -> 删除指定消息。"""
        base = [HumanMessage(content="要被删掉", id="m1"),
                HumanMessage(content="保留", id="m2")]
        out = add_messages(base, [RemoveMessage(id="m1")])
        print("delete        :", [m.id for m in out])

    @staticmethod
    def demo_chunk():
        """AIMessageChunk 合并为一条完整 AIMessage。"""
        chunk1 = AIMessageChunk(content="审核结果", id="chunk-a")
        chunk2 = AIMessageChunk(content="：无风险", id="chunk-a")
        merged = add_messages([], [chunk1])
        merged = add_messages(merged, [chunk2])
        print("chunk 合并    :", type(merged[0]).__name__, '| content =', merged[0].content)

    @staticmethod
    def demo_custom_field():
        """消息携带自定义字段(additional_kwargs),合并时保留。"""
        a = AIMessage(content="结果", id="c1", additional_kwargs={"risk": "low"})
        out = add_messages([], [a])
        print("自定义字段    :", out[0].additional_kwargs)

    def demo_graph(self):
        """用图演示多节点消息按 add_messages 有序累积。"""
        def node_b(state: State) -> dict:
            return {"messages": [AIMessage(content="第二步:情绪分析中", id="b1")]}

        def node_c(state: State) -> dict:
            return {"messages": [AIMessage(content="第三步:主题归类中", id="c1")]}

        def node_d(state: State) -> dict:
            return {"messages": [AIMessage(content="第四步:汇总报告", id="d1")]}

        builder = StateGraph(State)
        builder.add_node("b", node_b)
        builder.add_node("c", node_c)
        builder.add_node("d", node_d)
        builder.add_edge(START, "b")
        builder.add_edge("b", "c")
        builder.add_edge("c", "d")
        builder.add_edge("d", END)
        graph = builder.compile()

        out = graph.invoke({"messages": [HumanMessage(content="审核这篇文章", id="u1")]})
        print("\n[图执行] 消息按 add_messages 有序累积:")
        for m in out["messages"]:
            print("   -", m.content)


def main():
    print("=" * 60)
    print("GraphFlow - add_messages 深度演示")
    print("=" * 60)
    demo = AddMessagesDepth()
    demo.demo_append()
    demo.demo_replace()
    demo.demo_delete()
    demo.demo_chunk()
    demo.demo_custom_field()
    demo.demo_graph()


if __name__ == "__main__":
    main()