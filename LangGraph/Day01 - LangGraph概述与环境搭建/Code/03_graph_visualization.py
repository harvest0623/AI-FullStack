# 文件用途：图结构可视化
# 场景：GraphFlow 的「接收 - 分析 - 报告」三步图
# 构建一个三节点图，并用 get_graph() 输出图结构：
#   1) print_ascii() 打印 ASCII 节点/边图（无需额外依赖）
#   2) 手动打印节点列表与边列表（便于理解 START/END 的表示）
#   3) mermaid 可视化（可能需要额外库，说明如未安装的处理方式）
# GraphVisualizer 辅助类统一封装这些能力。

from typing import TypedDict

from langgraph.graph import StateGraph, END, START


class State(TypedDict):
    """GraphFlow 三步图的状态。"""
    input_text: str     # 输入
    analysis: str       # 分析结论
    report: str         # 审核报告
    summary: str        # 汇总结果


# ---- 三个节点：接收 / 分析 / 报告 ----
def receive_node(state: State) -> dict:
    return {"analysis": f"接收成功，文本长度 {len(state['input_text'])}"}


def analyze_node(state: State) -> dict:
    return {"report": f"分析[{state['analysis']}] → 结论：内容合规、无敏感词"}


def report_node(state: State) -> dict:
    return {"summary": f"最终报告：{state['report']}"}


class GraphVisualizer:
    """封装常见的图可视化 / 结构查看方式。"""

    def __init__(self, app) -> None:
        self.app = app
        self.graph = app.get_graph()  # 编译后的 CompiledGraph 可通过 get_graph() 拿到图信息

    def print_ascii(self) -> None:
        """用 ASCII 打印节点与边（零额外依赖，最适合快速查看）。"""
        print("\n[方式1] print_ascii()")
        self.graph.print_ascii()

    def print_nodes_and_edges(self) -> None:
        """手动打印图的节点集合与边集合。"""
        print("\n[方式2] 节点列表")
        nodes = self.graph.nodes          # OrderedDict，key 为节点名
        for name in nodes.keys():
            print(f"  节点: {name}")
        print("\n边列表")
        edges = self.graph.edges          # 列表，每项 (source, target)
        for src, tgt in edges:
            print(f"  边: {src} -> {tgt}")

    def mermaid(self, path: str = "graphflow.mmd") -> None:
        """输出 Mermaid 文本到文件（可贴到任意 markdown 渲染器查看）。

        注意：draw_mermaid_png / draw_mermaid 需要额外安装 pygraphviz 或调用在线渲染，
        此处仅导出 .mmd 纯文本，保证零额外依赖即可运行。
        """
        try:
            md = self.graph.draw_mermaid()
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(md)
            print(f"\n[方式3] Mermaid 已导出到 {path}（可用编辑器/在线工具渲染）")
        except Exception as exc:  # noqa: BLE001 - 仅提示
            print(f"\n[方式3] 导出 Mermaid 失败（本示例无需）：{exc}")


def build_app():
    """构建 GraphFlow 三节点图。"""
    builder = StateGraph(State)
    builder.add_node("receive", receive_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("report", report_node)
    builder.add_edge(START, "receive")
    builder.add_edge("receive", "analyze")
    builder.add_edge("analyze", "report")
    builder.add_edge("report", END)
    return builder.compile()


def main() -> None:
    print("=" * 56)
    print("GraphFlow 三步图 - 图结构可视化")
    print("=" * 56)

    app = build_app()
    viz = GraphVisualizer(app)
    viz.print_ascii()
    viz.print_nodes_and_edges()
    viz.mermaid()

    # 说明：若想导出 PNG 图，需要额外库：
    #   pip install pygraphviz（Windows 常见安装困难），LangGraph 内部会调用 Graphviz。
    # 本示例保持零额外依赖，聚焦 get_graph() 文本形式。
    print("\n[提示] 要导出 PNG：pip install pygraphviz 后调用 app.get_graph().draw_mermaid_png()")


if __name__ == "__main__":
    main()