# 文件用途：LangGraph 条件分支与循环
# 条件边 add_conditional_edges / 根据条件选择路径 / 循环执行（带终止条件）/ 并行节点
# 场景：根据问题复杂度路由到不同处理链
# 运行：python 04_langgraph_advanced.py
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
# State 定义
# ============================================================

class RouterState(TypedDict):
    """路由工作流的状态"""
    question: str           # 用户问题
    complexity: str         # 问题复杂度：simple / complex
    answer: str             # 最终回答
    retry_count: int        # 重试次数（循环用）
    quality_ok: bool        # 质量是否合格


# ============================================================
# 辅助：获取 LLM
# ============================================================

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ============================================================
# 节点1：分析问题复杂度
# ============================================================

def classify_node(state: RouterState) -> dict:
    """分析问题复杂度，决定路由方向"""
    print(f"\n📍 [classify] 分析问题复杂度：{state['question']}")
    llm = get_llm()
    # 让 LLM 判断问题复杂度
    result = llm.invoke(
        f"判断以下问题的复杂度，只回答 'simple' 或 'complex'：\n{state['question']}"
    ).content.strip().lower()

    complexity = "complex"
    if "simple" in result:
        complexity = "simple"

    print(f"   → 复杂度：{complexity}")
    return {"complexity": complexity}


# ============================================================
# 节点2a：简单问题处理（直接回答）
# ============================================================

def simple_answer_node(state: RouterState) -> dict:
    """处理简单问题"""
    print(f"\n📍 [simple_answer] 直接回答简单问题")
    llm = get_llm()
    answer = llm.invoke(f"简洁回答：{state['question']}").content
    print(f"   → 回答：{answer[:80]}...")
    return {"answer": answer}


# ============================================================
# 节点2b：复杂问题处理（深度回答）
# ============================================================

def complex_answer_node(state: RouterState) -> dict:
    """处理复杂问题（深度分析后回答）"""
    print(f"\n📍 [complex_answer] 深度处理复杂问题")
    llm = get_llm()
    prompt = f"""这是一个复杂问题，请分步骤深度分析后给出详细回答：

问题：{state['question']}

要求：
1. 先分析问题的关键点
2. 逐点解释
3. 给出总结"""
    answer = llm.invoke(prompt).content
    print(f"   → 回答：{answer[:80]}...")
    return {"answer": answer}


# ============================================================
# 节点3：质量检查（用于循环演示）
# ============================================================

def quality_check_node(state: RouterState) -> dict:
    """检查回答质量"""
    print(f"\n📍 [quality_check] 检查回答质量（第 {state['retry_count'] + 1} 次）")
    llm = get_llm()
    result = llm.invoke(
        f"判断以下回答质量是否合格（只回答'合格'或'不合格'）：\n"
        f"问题：{state['question']}\n回答：{state['answer'][:200]}"
    ).content.strip()

    quality_ok = "合格" in result
    retry_count = state["retry_count"] + 1
    print(f"   → 质量评估：{'✅ 合格' if quality_ok else '❌ 不合格'}（第 {retry_count} 次）")
    return {"quality_ok": quality_ok, "retry_count": retry_count}


# ============================================================
# 条件路由函数
# ============================================================

def route_by_complexity(state: RouterState) -> str:
    """根据复杂度路由到不同节点"""
    if state["complexity"] == "simple":
        return "simple_answer"
    return "complex_answer"


def route_after_check(state: RouterState) -> str:
    """质量检查后的路由：合格→END，不合格且未超次数→重新生成"""
    if state["quality_ok"]:
        return END
    if state["retry_count"] >= 3:
        print(f"   ⚠️  达到最大重试次数 3，结束循环")
        return END
    return "retry_generate"


# ============================================================
# 重试生成节点（循环用）
# ============================================================

def retry_generate_node(state: RouterState) -> dict:
    """质量不合格时重新生成回答"""
    print(f"\n📍 [retry_generate] 质量不合格，重新生成回答...")
    llm = get_llm()
    # 让模型改进回答
    answer = llm.invoke(
        f"请改进以下回答，使其更准确完整：\n"
        f"问题：{state['question']}\n原回答：{state['answer']}"
    ).content
    print(f"   → 改进后回答：{answer[:80]}...")
    return {"answer": answer}


# ============================================================
# 构建图1：条件分支图
# ============================================================

def build_conditional_graph():
    """构建条件分支图

    流程：
        START → classify → ┬→ simple_answer  → quality_check → END
                           └→ complex_answer → quality_check → END
    """
    graph = StateGraph(RouterState)

    # 添加节点
    graph.add_node("classify", classify_node)
    graph.add_node("simple_answer", simple_answer_node)
    graph.add_node("complex_answer", complex_answer_node)
    graph.add_node("quality_check", quality_check_node)

    # 入口
    graph.add_edge(START, "classify")

    # 条件边：根据复杂度路由
    graph.add_conditional_edges(
        "classify",
        route_by_complexity,
        {
            "simple_answer": "simple_answer",
            "complex_answer": "complex_answer",
        },
    )

    # 两个回答节点都汇入质量检查
    graph.add_edge("simple_answer", "quality_check")
    graph.add_edge("complex_answer", "quality_check")

    # 质量检查 → END
    graph.add_edge("quality_check", END)

    return graph.compile()


# ============================================================
# 构建图2：带循环的图（质量自检循环）
# ============================================================

def build_loop_graph():
    """构建带循环的图

    流程：
        START → classify → ┬→ simple_answer  → quality_check → ┬→ END (合格)
                           └→ complex_answer → quality_check → └→ retry_generate → quality_check (循环)
                                                                  (达到3次则 END)
    """
    graph = StateGraph(RouterState)

    # 添加节点
    graph.add_node("classify", classify_node)
    graph.add_node("simple_answer", simple_answer_node)
    graph.add_node("complex_answer", complex_answer_node)
    graph.add_node("quality_check", quality_check_node)
    graph.add_node("retry_generate", retry_generate_node)

    # 入口
    graph.add_edge(START, "classify")

    # 条件边：根据复杂度路由
    graph.add_conditional_edges(
        "classify",
        route_by_complexity,
        {
            "simple_answer": "simple_answer",
            "complex_answer": "complex_answer",
        },
    )

    # 两个回答节点都汇入质量检查
    graph.add_edge("simple_answer", "quality_check")
    graph.add_edge("complex_answer", "quality_check")

    # 条件边：质量检查后路由（合格→END，不合格→重试）
    graph.add_conditional_edges(
        "quality_check",
        route_after_check,
        {
            END: END,
            "retry_generate": "retry_generate",
        },
    )

    # 重试后回到质量检查（形成循环）
    graph.add_edge("retry_generate", "quality_check")

    return graph.compile()


# ============================================================
# 主流程
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day11 - 04 LangGraph 条件分支与循环")
    print("场景：根据问题复杂度路由 + 质量自检循环")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置后运行。")
        return

    # ── 演示1：条件分支图 ──
    print("\n" + "=" * 60)
    print("演示1：条件分支图（根据复杂度路由）")
    print("=" * 60)

    conditional_app = build_conditional_graph()
    print("✅ 条件分支图编译完成")

    # 测试简单问题
    print("\n--- 测试简单问题 ---")
    state1: RouterState = {
        "question": "Python 是什么？",
        "complexity": "",
        "answer": "",
        "retry_count": 0,
        "quality_ok": False,
    }
    result1 = conditional_app.invoke(state1)
    print(f"\n💬 最终回答：{result1['answer']}")

    # 测试复杂问题
    print("\n\n--- 测试复杂问题 ---")
    state2: RouterState = {
        "question": "请深入分析 LangChain 的 LCEL、LangGraph、LangServe 三个组件的架构设计理念、适用场景和它们之间的协作关系",
        "complexity": "",
        "answer": "",
        "retry_count": 0,
        "quality_ok": False,
    }
    result2 = conditional_app.invoke(state2)
    print(f"\n💬 最终回答：{result2['answer'][:200]}...")

    # ── 演示2：带循环的图 ──
    print("\n\n" + "=" * 60)
    print("演示2：带循环的图（质量自检，最多重试3次）")
    print("=" * 60)

    loop_app = build_loop_graph()
    print("✅ 循环图编译完成")

    state3: RouterState = {
        "question": "解释什么是 RAG 以及它的核心流程",
        "complexity": "",
        "answer": "",
        "retry_count": 0,
        "quality_ok": False,
    }
    result3 = loop_app.invoke(state3)
    print(f"\n💬 最终回答：{result3['answer'][:200]}...")
    print(f"📊 重试次数：{result3['retry_count']}，质量合格：{result3['quality_ok']}")

    print("\n" + "=" * 60)
    print("✅ LangGraph 条件分支与循环演示完成")
    print("要点：")
    print("  1. add_conditional_edges 实现条件分支")
    print("  2. 路由函数返回下一节点名（或 END）")
    print("  3. 节点间形成环路即实现循环（retry → quality_check → retry）")
    print("  4. 循环必须带终止条件（retry_count >= 3 → END）")
    print("  5. 这是 Agent 多轮决策的基础——后续 Agent 板块深入")
    print("=" * 60)


if __name__ == "__main__":
    main()
