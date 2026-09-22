#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 状态继承与嵌套演示 —— State 继承叠加字段 / 嵌套 TypedDict / BaseState 复用
# 说明: 展示如何使用 BaseState 定义公共字段,再通过继承叠加扩展字段;字段值为嵌套 TypedDict。
# 运行: python 03_state_inheritance.py
# 依赖: pip install langgraph langchain python-dotenv pydantic

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# ---------------- 嵌套 TypedDict ----------------
class RiskInfo(TypedDict):
    level: str        # 高/中/低
    score: int        # 0-100


# ---------------- 基础状态(BaseState 复用) ----------------
class BaseState(TypedDict):
    input_text: str                          # 所有子图共用的输入
    messages: Annotated[list, add_messages]  # 所有子图共用的消息累积


# ---------------- 扩展状态(继承叠加) ----------------
class AuditState(BaseState):
    """在 BaseState 之上叠加审核专用字段。"""
    risk: RiskInfo          # 嵌套结构字段
    tags: list              # 关键词标签


class StateInheritance:
    """演示 State 继承与嵌套字段。"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        def analyze_node(state: AuditState) -> dict:
            # 计算简单规则风险分(演示用),写入嵌套字段
            text = state["input_text"]
            score = min(100, len(state["tags"]) * 20 + 10)
            level = "高" if score >= 70 else ("中" if score >= 40 else "低")
            return {"risk": {"level": level, "score": score}}

        def tag_node(state: AuditState) -> dict:
            return {"tags": ["广告", "诱导", "收益承诺"]}

        builder = StateGraph(AuditState)
        builder.add_node("tag", tag_node)
        builder.add_node("analyze", analyze_node)
        builder.add_edge(START, "tag")
        builder.add_edge("tag", "analyze")
        builder.add_edge("analyze", END)
        return builder.compile()

    def run(self, text: str) -> dict:
        return self.graph.invoke({"input_text": text, "messages": []})


def main():
    print("=" * 60)
    print("GraphFlow - 状态继承与嵌套")
    print("=" * 60)
    demo = StateInheritance()
    result = demo.run("稳赚不赔的理财链接")
    print(f"input_text(继承自 BaseState): {result['input_text']}")
    print(f"tags                       : {result['tags']}")
    print(f"risk(嵌套 TypedDict)      : level={result['risk']['level']}, score={result['risk']['score']}")
    print(f"messages(BaseState 提供)  : {len(result['messages'])} 条")


if __name__ == "__main__":
    main()