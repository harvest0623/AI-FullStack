#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 失败降级 fallback 演示 —— 主分析节点失败,走规则降级节点
# 说明: 用条件边 + 异常捕获设计 fallback;主节点(LLM)失败后,降级为关键词规则分析。
# 运行: python 02_fallback.py
# 依赖: pip install langgraph langchain python-dotenv pydantic（可配 KEY 调真实模型,不配则模拟失败降级）

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

# 可控开关: 是否模拟主 LLM 节点失败(便于观察降级,不耗费 API 配额)
SIMULATE_FAILURE = True


class State(TypedDict):
    input_text: str
    result: str
    used_fallback: str     # 记录是否使用了降级


# ---------------- 节点 ----------------
def primary_analysis(state: State) -> dict:
    """主分析节点:模拟 LLM 分析,可能抛异常。"""
    if SIMULATE_FAILURE:
        raise ValueError("LLM 调用超时/失败")
    # 正常路径(未启用模拟):规则即简单返回
    return {"result": "主链路分析完成", "used_fallback": "no"}


def rule_based(state: State) -> dict:
    """降级节点:关键词规则分析,保证最低可用性。"""
    text = state["input_text"]
    risk_words = ["稳赚", "诱导", "链接", "涨幅"]
    hits = [w for w in risk_words if w in text]
    level = "高风险" if len(hits) >= 2 else ("中风险" if hits else "低风险/合规")
    return {"result": f"[规则降级] 命中关键词 {hits} => {level}", "used_fallback": "yes"}


def route_after_primary(state: State) -> str:
    """条件边路径:主节点异常时由外层捕获并通过异常流程进入降级。

    实际上 langgraph 节点异常会直接中断,这里采用"try/except 返回 + 条件边"模式,
    让主节点失败时优雅地进入降级节点而不是中断整图。
    """
    # 主节点内部已捕获异常;这里始终走向返回,仅当状态标记 fallback 时进降级
    return "fallback" if state.get("used_fallback") == "yes" else "end"


# ---------------- 封装容错的主节点(捕获异常 + 标记降级) ----------------
def safe_primary(state: State) -> dict:
    """包装主节点:尝试主分析,失败则标记 used_fallback,交由条件边路由到降级。"""
    try:
        return primary_analysis(state)
    except Exception as e:
        print(f"  [主节点异常] {type(e).__name__}: {e}")
        # 不抛,标记需要降级
        return {"result": "", "used_fallback": "yes"}


class FallbackDemo:
    """演示 fallback:主节点失败时降级到规则引擎。"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(State)
        builder.add_node("primary", safe_primary)
        builder.add_node("fallback", rule_based)
        builder.add_edge(START, "primary")
        # 条件边: 根据 used_fallback 分流
        builder.add_conditional_edges("primary", route_after_primary,
                                      {"fallback": "fallback", "end": END})
        builder.add_edge("fallback", END)
        return builder.compile()

    def run(self, text: str) -> dict:
        return self.graph.invoke({"input_text": text})


def main():
    print("=" * 60)
    print("GraphFlow - 失败降级 fallback（LLM -> 规则）")
    print("=" * 60)
    demo = FallbackDemo()
    res = demo.run("稳赚不赔,点击链接立即领取高额涨幅!")
    print(f"审核结论   : {res['result']}")
    print(f"是否降级   : {res['used_fallback']} (yes 表示走了规则兜底)")


if __name__ == "__main__":
    main()