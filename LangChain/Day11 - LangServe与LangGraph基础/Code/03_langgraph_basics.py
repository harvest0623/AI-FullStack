# 文件用途：LangGraph StateGraph 基础（线性图）
# 定义 State TypedDict / 创建 Node 函数 / 创建 StateGraph / 添加节点和边 / 编译执行
# 场景：问题分析 → 检索 → 生成回答（简单线性图）
# 运行：python 03_langgraph_basics.py
# 依赖：pip install langchain langchain-openai langgraph python-dotenv
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

load_dotenv()


# ============================================================
# 1. 定义 State（在图中流转的数据，用 TypedDict 定义）
# ============================================================

class QAState(TypedDict):
    """ChainQA 问答工作流的状态定义

    State 在各节点间流转，每个节点接收完整 State，返回部分更新。
    """
    question: str           # 用户问题（输入）
    analysis: str           # 问题分析结果
    retrieved_docs: str     # 检索到的文档（模拟）
    answer: str             # 最终回答（输出）


# ============================================================
# 2. 创建 Node 函数（接收 State，返回部分更新）
# ============================================================

def get_llm() -> ChatOpenAI:
    """获取 LLM 实例"""
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def analyze_node(state: QAState) -> dict:
    """节点1：分析用户问题

    接收当前 State，返回要更新的字段。
    """
    print(f"\n📍 [节点 analyze] 分析问题：{state['question']}")
    llm = get_llm()
    # 让 LLM 分析问题的意图和关键词
    analysis = llm.invoke(
        f"请用一句话分析以下问题的意图和关键词：{state['question']}"
    ).content
    print(f"   → 分析结果：{analysis[:80]}...")
    # 返回部分更新（合并到 State）
    return {"analysis": analysis}


def retrieve_node(state: QAState) -> dict:
    """节点2：根据分析结果检索文档（模拟检索）"""
    print(f"\n📍 [节点 retrieve] 基于分析结果检索文档...")
    # 模拟检索（真实场景用 VectorStore + Retriever）
    analysis = state["analysis"]
    docs = f"基于分析'{analysis[:30]}...'检索到 3 条相关文档：\n"
    docs += "- 文档1：LangChain 是 LLM 应用开发框架\n"
    docs += "- 文档2：LCEL 用于组合组件\n"
    docs += "- 文档3：LangGraph 编排复杂工作流"
    print(f"   → 检索结果：{docs[:80]}...")
    return {"retrieved_docs": docs}


def generate_node(state: QAState) -> dict:
    """节点3：基于分析结果和检索文档生成最终回答"""
    print(f"\n📍 [节点 generate] 生成最终回答...")
    llm = get_llm()
    # 组合 State 中的信息生成回答
    prompt = f"""基于以下信息回答用户问题：

用户问题：{state['question']}
问题分析：{state['analysis']}
检索文档：{state['retrieved_docs']}

请综合以上信息，给出准确简洁的回答。"""
    answer = llm.invoke(prompt).content
    print(f"   → 回答：{answer[:80]}...")
    return {"answer": answer}


# ============================================================
# 3. 创建 StateGraph 并构建图
# ============================================================

def build_qa_graph():
    """构建 ChainQA 问答工作流图

    流程：START → analyze → retrieve → generate → END
    """
    # 创建 StateGraph，指定 State 类型
    graph = StateGraph(QAState)

    # 添加节点
    graph.add_node("analyze", analyze_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)

    # 添加边（定义节点间的执行顺序）
    graph.add_edge(START, "analyze")      # 入口 → analyze
    graph.add_edge("analyze", "retrieve") # analyze → retrieve
    graph.add_edge("retrieve", "generate")# retrieve → generate
    graph.add_edge("generate", END)       # generate → 出口

    # 编译图（生成可执行的 Runnable）
    return graph.compile()


# ============================================================
# 4. 主流程
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day11 - 03 LangGraph StateGraph 基础")
    print("场景：问题分析 → 检索 → 生成回答（线性图）")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置后运行。")
        return

    # 构建并编译图
    print("\n构建 LangGraph 工作流图...")
    qa_app = build_qa_graph()
    print("✅ 图编译完成")

    # 执行图
    print("\n" + "=" * 60)
    print("🚀 执行工作流")
    print("=" * 60)

    # 初始 State（只需提供 question，其他字段由节点填充）
    initial_state: QAState = {
        "question": "LangChain 的 LCEL 和 LangGraph 有什么区别？",
        "analysis": "",
        "retrieved_docs": "",
        "answer": "",
    }

    # 执行图
    final_state = qa_app.invoke(initial_state)

    # 打印最终 State
    print("\n" + "=" * 60)
    print("📋 最终 State")
    print("=" * 60)
    for key, value in final_state.items():
        print(f"\n【{key}】")
        print(f"  {value}")

    # 测试第二个问题
    print("\n\n" + "=" * 60)
    print("🚀 执行第二个问题")
    print("=" * 60)
    state2: QAState = {
        "question": "什么是 Tool Calling？",
        "analysis": "",
        "retrieved_docs": "",
        "answer": "",
    }
    final_state2 = qa_app.invoke(state2)
    print(f"\n💬 最终回答：{final_state2['answer']}")

    print("\n" + "=" * 60)
    print("✅ LangGraph 基础演示完成")
    print("要点：")
    print("  1. State 用 TypedDict 定义，在节点间流转")
    print("  2. Node 函数接收 State，返回部分更新")
    print("  3. Edge 定义执行顺序，START/END 是入口出口")
    print("  4. graph.compile() 编译后得到可执行 Runnable")
    print("  5. 调用方式与 LCEL 一致：app.invoke(initial_state)")
    print("=" * 60)


if __name__ == "__main__":
    main()
