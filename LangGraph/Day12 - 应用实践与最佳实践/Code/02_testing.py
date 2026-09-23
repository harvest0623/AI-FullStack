#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 图测试框架 —— 节点级测试 + 图集成测试 + mock LLM 替换真实模型
# 说明: 演示可复用的测试模式;用简单规则节点构造被测图,再编写带断言的测试用例类。
# 运行: python 02_testing.py
# 依赖: pip install langgraph langchain python-dotenv pydantic

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# ---------------- 被测组件:规则审核节点 ----------------
class State(TypedDict):
    input_text: str
    risk_level: str


def analyze_node(state: State) -> dict:
    hits = [w for w in ["稳赚", "诱导", "链接", "涨幅"] if w in state["input_text"]]
    if len(hits) >= 2:
        return {"risk_level": "high"}
    if hits:
        return {"risk_level": "medium"}
    return {"risk_level": "low"}


# ---------------- 仅作演示的 mock LLM ----------------
class MockLLM:
    """测试时替换真实模型:返回固定输出,保证测试稳定、快速、零成本。"""

    def __init__(self, output: str = "low"):
        self.output = output
        self.calls = 0

    def invoke(self, messages, **kwargs):
        self.calls += 1
        # 生产节点若用 llm,测试时传入本对象即可固定返回
        return type("AIMessage", (), {"content": self.output})()


class GraphTester:
    """可复用的测试套件:单节点 / 图集成 / mock LLM。"""

    def build_graph(self):
        builder = StateGraph(State)
        builder.add_node("analyze", analyze_node)
        builder.add_edge(START, "analyze")
        builder.add_edge("analyze", END)
        return builder.compile()

    # --- 1. 单节点测试:直接调用节点函数 ---
    def test_node_high(self):
        res = analyze_node({"input_text": "稳赚不赔点击链接"})
        assert res["risk_level"] == "high", res

    def test_node_low(self):
        res = analyze_node({"input_text": "今天天气不错"})
        assert res["risk_level"] == "low", res

    # --- 2. 图集成测试:invoke + 断言状态 ---
    def test_graph_integration(self):
        graph = self.build_graph()
        out = graph.invoke({"input_text": "稳赚不赔的理财链接"})
        assert out["risk_level"] == "high", out
        print("  [图集成] invoke 返回状态:", out)

    # --- 3. mock LLM:替换真实模型,固定其输出 ---
    def test_mock_llm(self):
        mock = MockLLM(output="medium")
        # 命中两次及以上关键词 -> 但这里演示 mock 覆盖真实模型对最终结论的影响
        # (可把 mock.invoke 注入到生产节点后 assert 命中)
        out = analyze_node({"input_text": "诱导链接稳赚"})
        assert mock.invoke([], ).content == "medium"        # mock 固定返回
        assert mock.calls == 1
        assert out["risk_level"] == "high"                   # 规则节点仍按规则判定
        print("  [mock LLM] 固定返回 medium,调用次数 =", mock.calls)

    def run_all(self):
        print("=" * 60)
        print("GraphFlow - 图测试框架")
        print("=" * 60)
        self.test_node_high()
        print("  [单节点] 高风险用例通过")
        self.test_node_low()
        print("  [单节点] 低风险用例通过")
        self.test_graph_integration()
        self.test_mock_llm()
        print("  => 全部断言通过 ✔")


if __name__ == "__main__":
    GraphTester().run_all()