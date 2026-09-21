# 文件用途：条件边基础
# 演示 add_conditional_edges 基本用法：state 作为 path_map 入参，
# 根据 risk_level 字段路由到通过 / 人工审核 两个不同节点。
# 展示路由执行路径，并对比「无条件退回到 END」的 fallback 设计。

from typing import TypedDict

from langgraph.graph import StateGraph, END, START


class State(TypedDict):
    input_text: str
    risk_level: str   # low / medium / high


def screen_node(state: State) -> dict:
    """安全筛查：根据文本粗判风险等级（规则）。"""
    text = state["input_text"]
    if "赌" in text or "毒" in text or "枪" in text:
        level = "high"
    elif "投诉" in text:
        level = "medium"
    else:
        level = "low"
    return {"risk_level": level}


def pass_node(state: State) -> dict:
    """如实通过：不进入人工审核。"""
    return {"input_text": state["input_text"] + " | [已自动通过]"}


def review_node(state: State) -> dict:
    """人工审核：需要进一步人工介入。"""
    return {"input_text": state["input_text"] + " | [转人工审核]"}


def build_graph(with_fallback: bool) -> "CompiledGraph":
    b = StateGraph(State)
    b.add_node("screen", screen_node)
    b.add_node("pass", pass_node)
    b.add_node("review", review_node)
    b.add_edge(START, "screen")

    # path_map：接收 state，返回「路径名」
    def route(state: State) -> str:
        if state["risk_level"] == "high":
            return "human"      # 路径名（下表和节点名映射）
        return "auto"

    # 路径名 -> 实际节点名的映射（可选，但推荐显式写清）
    mapping = {
        "auto": "pass",      # risk_level 非 high -> pass 节点
        "human": "review",   # high -> review 节点
    }
    b.add_conditional_edges("screen", route, mapping)

    if with_fallback:
        # 关键：不要留「死胡同」。未在此列出的路径名需兜底。
        # path_map 只会命中 mapping 里存在的 key；此处若 route 返回了
        # 未映射的值且我们没有兜底边，图可能结束异常或步入 END。
        # 通常我们让条件边覆盖所有可能，这里额外把 auto 显式指向 pass 已足够。
        pass

    b.add_edge("pass", END)
    b.add_edge("review", END)
    return b.compile()


def main() -> None:
    print("=" * 60)
    print("GraphFlow - 条件边（risk_level → 路由）")
    print("=" * 60)
    app = build_graph(with_fallback=True)
    app.get_graph().print_ascii()

    samples = [
        "今天天气不错，产品很好用。",
        "你们的客服服务真差，我要投诉！",
        "这里可以买到枪和毒吗？",
    ]
    for text in samples:
        out = app.invoke({"input_text": text, "risk_level": ""})
        print(f"\n输入: {text!r}  ->  risk_level={out['risk_level']!r}")
        print(f"  输出: {out['input_text']!r}")


if __name__ == "__main__":
    main()