#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 自定义 Reducer 演示 —— 多个打分节点合并出 GraphFlow 的总分与平均分
# 说明: 用 Annotated[type, func] 定义去重/取最大/取平均等聚合 reducer，节点直接返回新值。
# 运行: python 01_custom_reducer.py
# 依赖: pip install langgraph langchain python-dotenv pydantic（本示例不调用真实 LLM）

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


# ---------------- 自定义 reducer ----------------
def merge_unique(left: list, right: list) -> list:
    """合并列表并去重，保持顺序（保序去重）。"""
    seen = set(left)
    out = list(left)
    for x in right:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def merge_max(left: int, right: int) -> int:
    """取最大值（旧的与新的比较）。"""
    return max(left, right)


def merge_sum(left: int, right: int) -> int:
    """累加求和。"""
    return left + right


# 平均分无法仅凭 left/right 算出(需要记录数量),这里用一个复合思路:
# 用两个字段分别累计总和与个数,再在图结束后计算平均分。


# ---------------- 状态定义 ----------------
class State(TypedDict):
    input_text: str
    # 三个打分节点分别输出,用累加 reducer 合并总分
    total_score: Annotated[int, merge_sum]
    count: Annotated[int, merge_sum]          # 记录打分数量,用于算平均
    highest_risk: Annotated[int, merge_max]    # 取最大风险分
    entities: Annotated[list, merge_unique]    # 去重合并实体


class CustomReducer:
    """展示自定义 reducer:多个节点写同一个字段,按规则合并。"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        def safety_node(state: State) -> dict:
            """内容安全打分节点:返回 8 分 + 抽取实体。"""
            return {"total_score": 8, "count": 1, "highest_risk": 8,
                    "entities": ["营销广告", "诱导链接"]}

        def sentiment_node(state: State) -> dict:
            """情绪分析打分节点:返回 6 分。"""
            return {"total_score": 6, "count": 1, "highest_risk": 9,
                    "entities": ["诱导链接", "夸大收益"]}

        def theme_node(state: State) -> dict:
            """主题分析打分节点:返回 7 分。"""
            return {"total_score": 7, "count": 1, "highest_risk": 7,
                    "entities": ["理财", "营销广告"]}

        builder = StateGraph(State)
        builder.add_node("safety", safety_node)
        builder.add_node("sentiment", sentiment_node)
        builder.add_node("theme", theme_node)
        # 三个节点并行(fan-out),随后聚合到 finish
        builder.add_edge(START, "safety")
        builder.add_edge(START, "sentiment")
        builder.add_edge(START, "theme")
        builder.add_edge("safety", END)
        builder.add_edge("sentiment", END)
        builder.add_edge("theme", END)
        return builder.compile()

    def run(self, text: str) -> dict:
        return self.graph.invoke({"input_text": text, "total_score": 0,
                                  "count": 0, "highest_risk": 0, "entities": []})


def main():
    print("=" * 60)
    print("GraphFlow - 自定义 Reducer（多个打分节点合并）")
    print("=" * 60)

    demo = CustomReducer()
    result = demo.run("稳赚不赔的理财计划,点击链接立即领取收益! -> link")

    avg = result["total_score"] / result["count"]
    print(f"输入    : {result['input_text']}")
    print(f"总分    : {result['total_score']}  (三个节点: 8+6+7)")
    print(f"平均分  : {avg:.1f}  (总分/节点数)")
    print(f"最高风险: {result['highest_risk']}  (max reducer 取到 9)")
    print(f"实体(去重): {result['entities']}")


if __name__ == "__main__":
    main()