# 文件用途：Reducer 基础
# 对比两种合并行为：
#   1) 默认覆盖：多个节点写同一字段时，后写的覆盖先写的
#   2) Annotated + operator.add 累积：列表字段自动「拼接」
# StateReducerDemo 类封装两种图，演示 reducer 的合并逻辑。
# 场景：GraphFlow 中多个分析节点都要向 state 写入结果时，如何合并。

from typing import Annotated, TypedDict
from operator import add

from langgraph.graph import StateGraph, START, END


# ---- 方案 A：默认覆盖行为 ----
class OverrideState(TypedDict):
    """默认行为：字段被后写覆盖，列表也被整体覆盖。"""
    analysis: str            # 单一结果
    tags: list[str]          # 列表字段，默认整体覆盖


def writer_first(state: OverrideState) -> dict:
    return {"analysis": "安全检测：通过"}


def writer_second(state: OverrideState) -> dict:
    return {"analysis": "情感分析：正面"}   # 覆盖 writer_first 写入的值


def tagger_first(state: OverrideState) -> dict:
    return {"tags": ["安全"]}


def tagger_second(state: OverrideState) -> dict:
    return {"tags": ["情感"]}   # 覆盖 tagger_first，tags 变成 ["情感"]，而不是 ["安全","情感"]


# ---- 方案 B：Annotated + add 累积 ----
class AccumState(TypedDict):
    """使用 reducer：列表字段用 operator.add 自动拼接。"""
    analysis: str
    tags: Annotated[list[str], add]   # reducer：新列表 + 旧列表


def acc_first(state: AccumState) -> dict:
    return {"analysis": "node1", "tags": ["安全"]}


def acc_second(state: AccumState) -> dict:
    return {"analysis": "node2", "tags": ["情感"]}   # tags 会累积为 ["安全","情感"]


class StateReducerDemo:
    """封装两种合并行为的对比演示。"""

    @staticmethod
    def build_override_app():
        b = StateGraph(OverrideState)
        b.add_node("w1", writer_first)
        b.add_node("w2", writer_second)
        b.add_node("t1", tagger_first)
        b.add_node("t2", tagger_second)
        # 串行：w1 -> w2 -> t1 -> t2
        b.add_edge(START, "w1")
        b.add_edge("w1", "w2")
        b.add_edge("w2", "t1")
        b.add_edge("t1", "t2")
        b.add_edge("t2", END)
        return b.compile()

    @staticmethod
    def build_accum_app():
        b = StateGraph(AccumState)
        b.add_node("a1", acc_first)
        b.add_node("a2", acc_second)
        b.add_edge(START, "a1")
        b.add_edge("a1", "a2")
        b.add_edge("a2", END)
        return b.compile()

    @classmethod
    def run(cls) -> None:
        print("=" * 60)
        print("方案A：默认覆盖行为（后写覆盖先写）")
        print("=" * 60)
        app = cls.build_override_app()
        out = app.invoke({"analysis": "", "tags": []})
        print("  analysis =", repr(out["analysis"]))   # 情感分析：正面（w2 覆盖 w1）
        print("  tags     =", repr(out["tags"]))       # ['情感']（t2 覆盖 t1）

        print("=" * 60)
        print("方案B：Annotated + operator.add 累积")
        print("=" * 60)
        app = cls.build_accum_app()
        out = app.invoke({"analysis": "", "tags": []})
        print("  analysis =", repr(out["analysis"]))   # node2（标量仍覆盖）
        print("  tags     =", repr(out["tags"]))       # ['安全', '情感']（累积）


if __name__ == "__main__":
    StateReducerDemo.run()