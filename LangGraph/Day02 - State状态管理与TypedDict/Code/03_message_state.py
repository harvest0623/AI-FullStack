# 文件用途：消息列表状态（Annotated[list, add_messages] 累积）
# 对比两种行为：
#   1) 默认覆盖：messages 字段被整体覆盖，只留下最后一个节点写入的消息
#   2) 使用 add_messages：messages 字段自动「追加」，累积全部节点写入的消息
# 场景：GraphFlow 各分析步骤都要在 messages 里追加一条记录，最终汇总查看全部历史。

from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages  # LangGraph 内置 reducer


# ---- 默认行为：messages 被覆盖 ----
class OverrideState(TypedDict):
    messages: list[str]          # 纯 list，默认覆盖语义


# ---- 使用 add_messages reducer 累积 ----
class MessageState(TypedDict):
    messages: Annotated[list[str], add_messages]   # 追加语义
    record: str


def detect_node(state: MessageState) -> dict:
    """安全检测步骤：追加一条消息。"""
    return {"messages": ["[安全检测] 未检出异常"], "record": "detect"}


def analyze_node(state: MessageState) -> dict:
    """情感分析步骤：再追加一条消息。"""
    return {"messages": ["[情感分析] 整体偏正面"], "record": "analyze"}


def report_node(state: MessageState) -> dict:
    """生成报告步骤：追加最后一条消息。"""
    return {"messages": ["[报告] 可自动通过"], "record": "report"}


def build_override_app():
    b = StateGraph(OverrideState)
    b.add_node("d", lambda s: {"messages": ["[安全检测] 一条"]})
    b.add_node("a", lambda s: {"messages": ["[情感分析] 另一条"]})
    b.add_edge(START, "d")
    b.add_edge("d", "a")
    b.add_edge("a", END)
    return b.compile()


def build_message_app():
    b = StateGraph(MessageState)
    b.add_node("detect", detect_node)
    b.add_node("analyze", analyze_node)
    b.add_node("report", report_node)
    b.add_edge(START, "detect")
    b.add_edge("detect", "analyze")
    b.add_edge("analyze", "report")
    b.add_edge("report", END)
    return b.compile()


def main() -> None:
    print("=" * 60)
    print("对比1：默认覆盖 — messages 被整体覆盖")
    print("=" * 60)
    app = build_override_app()
    out = app.invoke({"messages": []})
    print("  messages =", out["messages"])
    print("  （只剩最后一个节点写入的 1 条）")

    print("=" * 60)
    print("对比2：Annotated[list, add_messages] — 消息累积")
    print("=" * 60)
    app = build_message_app()
    out = app.invoke({"messages": [], "record": ""})
    print("  messages：")
    for m in out["messages"]:
        print("   -", m)
    print("  record  =", out["record"], "（标量字段仍由 report 覆盖）")


if __name__ == "__main__":
    main()