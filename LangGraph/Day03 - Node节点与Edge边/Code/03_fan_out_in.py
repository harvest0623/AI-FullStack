# 文件用途：扇入扇出行为
# 演示：
#   fan-out（扇出）：一个节点有多个出边 -> 下一层节点并行执行
#   fan-in（扇入）：多个节点汇集到同一节点 -> 汇集后再执行
# 用 stream_mode 追踪观察并行与汇集的执行次序。
# 场景：GraphFlow 在「规则分类」节点后，并行做「安全检测」和「情感分析」，
#       再「汇集」到报告节点。

import time
from typing import TypedDict

from langgraph.graph import StateGraph, END, START


class State(TypedDict):
    input_text: str
    safety: str
    sentiment: str
    report: str


def classify_node(state: State) -> dict:
    """入口：做一次规则分类。"""
    time.sleep(0.05)
    return {"report": "开始处理"}


def safety_node(state: State) -> dict:
    """安全检测：模拟耗时较快。"""
    time.sleep(0.3)
    return {"safety": "安全 - 未检出异常"}


def sentiment_node(state: State) -> dict:
    """情感分析：模拟耗时较慢。"""
    time.sleep(0.7)
    return {"sentiment": "情感 - 正面"}


def report_node(state: State) -> dict:
    """汇集节点：等两个分支都完成后才执行。"""
    return {"report": f"报告：{state['safety']}；{state['sentiment']}"}


def main() -> None:
    b = StateGraph(State)
    b.add_node("classify", classify_node)
    b.add_node("safety", safety_node)
    b.add_node("sentiment", sentiment_node)
    b.add_node("report", report_node)

    # 入口 -> 分类
    b.add_edge(START, "classify")
    # fan-out：classify 同时指向 safety 和 sentiment（两个子分支并行）
    b.add_edge("classify", "safety")
    b.add_edge("classify", "sentiment")
    # fan-in：safety、sentiment 都汇集到 report
    b.add_edge("safety", "report")
    b.add_edge("sentiment", "report")
    b.add_edge("report", END)

    app = b.compile()
    print("图结构：")
    app.get_graph().print_ascii()

    t0 = time.time()
    print("\n用 stream_mode='updates' 观察执行次序（fan-out 并行）：")
    for ev in app.stream({"input_text": "测试文章"}, stream_mode="updates"):
        print("  ", list(ev.keys())[0], ev)
    print(f"\n总耗时 {time.time() - t0:.2f}s（并行下应接近较慢分支 0.7s，而非 1.0s 串行）")


if __name__ == "__main__":
    main()