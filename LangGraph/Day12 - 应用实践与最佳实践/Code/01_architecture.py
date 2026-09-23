#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 完整项目架构实现 —— 分层清晰的小型 LangGraph 项目 (GraphFlow 生产化)
# 说明: 在单文件内以模块化小节组织: ①状态模型 ②节点集 ③配置管理 ④图工厂 build_graph(cfg)。
#      实际大型项目中可拆分为 state.py / nodes.py / config.py / factory.py 等多个文件。
# 运行: python 01_architecture.py
# 依赖: pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.graph import END, START, StateGraph

load_dotenv()


# ============ ① 状态模型 (state.py) ============
class GraphFlowState(TypedDict):
    input_text: str
    messages: Annotated[list, add_messages]   # 短时记忆:会话消息累积
    risk_level: str                            # 审核结论
    status: str                                # ok / degraded / error


# ============ ② 节点集 (nodes.py) ============
def analyze_node(state: GraphFlowState) -> dict:
    """按关键词规则分析风险(重规则、轻依赖,便于演示与测试;生产可换 LLM)。"""
    risk_words = ["稳赚", "诱导", "链接", "涨幅"]
    hits = [w for w in risk_words if w in state["input_text"]]
    if len(hits) >= 2:
        level = "high"
    elif hits:
        level = "medium"
    else:
        level = "low"
    return {"risk_level": level, "status": "ok"}


# ============ ③ 配置管理 (config.py) ============
def default_config() -> dict:
    """集中管理可配置项:模型、风险词、重试等。可按环境覆盖。"""
    return {
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "risk_words": ["稳赚", "诱导", "链接", "涨幅"],
        # 注释: 生产建议使用 SqliteSaver / PostgresSaver 持久化 Checkpointer
        "use_checkpointer": True,
    }


# ============ ④ 图工厂 (factory.py) ============
def build_graph(cfg: dict) -> object:
    """图工厂:把配置注入图构造,返回已编译的 CompiledGraph。

    好处:同一份图定义,可通过不同 cfg 产出不同行为(模型/持久化开关)。
    """
    builder = StateGraph(GraphFlowState)
    builder.add_node("analyze", analyze_node)
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", END)

    if cfg.get("use_checkpointer", True):
        checkpointer = MemorySaver()
    else:
        checkpointer = None
    return builder.compile(checkpointer=checkpointer)


class ArchitectureDemo:
    """展示分层架构下的使用方式。"""

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or default_config()
        self.graph = build_graph(self.cfg)

    def run(self, text: str, thread_id: str = "t1") -> dict:
        config = {"configurable": {"thread_id": thread_id, "user_id": "demo"}}
        return self.graph.invoke({"input_text": text}, config=config)


def main():
    print("=" * 60)
    print("GraphFlow - 分层架构(状态/节点/配置/图工厂)")
    print("=" * 60)
    demo = ArchitectureDemo()
    for text in ["今天天气很好", "稳赚不赔点击链接领取涨幅"]:
        res = demo.run(text)
        print(f"输入: {text}")
        print(f"  -> 风险等级={res['risk_level']:>6}  状态={res['status']}")


if __name__ == "__main__":
    main()