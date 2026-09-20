# 文件用途：普通边与入口/出口
# 演示 Edge 的几种声明方式及其等价关系：
#   set_entry_point(node)  ≡ add_edge(START, node)
#   set_finish_point(node) ≡ add_edge(node, END)
#   add_edge(a, b)         普通定向边，无条件流转
# 完整展示 GraphFlow 基础流程图并打印执行路径（用 updates 模式逐步打印）。

from typing import TypedDict

from langgraph.graph import StateGraph, END, START


class State(TypedDict):
    """GraphFlow 的基础流转状态。"""
    input_text: str
    log: list[str]


def step_node(tag: str):
    """工厂函数：生成一个把 tag 记录到 log 并返回的节点函数。"""
    def node(state: State) -> dict:
        return {"log": state.get("log", []) + [tag]}
    return node


def build_via_set_points() -> "CompiledGraph":
    """方式1：用 set_entry_point / set_finish_point 声明入口与出口。"""
    b = StateGraph(State)
    b.add_node("receive", step_node("接收"))
    b.add_node("detect", step_node("安全检测"))
    b.add_node("report", step_node("生成报告"))
    b.set_entry_point("receive")      # 入口：receive
    b.add_edge("receive", "detect")   # 普通边
    b.add_edge("detect", "report")
    b.set_finish_point("report")      # 出口：report
    return b.compile()


def build_via_start_end() -> "CompiledGraph":
    """方式2：直接用 START / END 常量，等价于方式1。"""
    b = StateGraph(State)
    b.add_node("receive", step_node("接收"))
    b.add_node("detect", step_node("安全检测"))
    b.add_node("report", step_node("生成报告"))
    b.add_edge(START, "receive")     # 等价 set_entry_point("receive")
    b.add_edge("receive", "detect")
    b.add_edge("detect", "report")
    b.add_edge("report", END)        # 等价 set_finish_point("report")
    return b.compile()


def main() -> None:
    print("=" * 60)
    print("方式1：set_entry_point / set_finish_point")
    print("=" * 60)
    app = build_via_set_points()
    app.get_graph().print_ascii()
    print("执行路径（log）：", app.invoke({"input_text": "hi", "log": []})["log"])

    print("=" * 60)
    print("方式2：START / END 常量（等价，推荐）")
    print("=" * 60)
    app = build_via_start_end()
    steps = []
    for ev in app.stream({"input_text": "hi", "log": []}, stream_mode="updates"):
        steps.append(list(ev.keys())[0])
    print("执行的节点顺序：", " -> ".join(steps))


if __name__ == "__main__":
    main()