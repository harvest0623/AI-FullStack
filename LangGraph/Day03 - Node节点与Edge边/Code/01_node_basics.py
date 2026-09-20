# 文件用途：节点定义与返回
# 展示多种 node 写法：
#   1) 纯函数节点（同步）
#   2) 调用 LLM 的节点（通过 langchain-openai 的 ChatOpenAI）
#   3) async 节点（异步，配合 ainvoke）
#   4) 只返回部分字段的节点
# 场景：GraphFlow 的内容安全检测节点 + 情感分析节点。

import asyncio
import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv

load_dotenv()  # 加载 .env 中的 API Key

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages


# ---- State 定义 ----
class State(TypedDict):
    input_text: str       # 输入文本
    safety_result: str    # 安全检测结果
    sentiment: str        # 情感分析结果
    messages: Annotated[list, add_messages]   # 日志累积


# ---- 1) 纯函数节点：安全检测（模拟规则，不调 LLM，保证无 Key 也能跑）----
SAFETY_BANWORDS = ["赌", "毒", "枪"]


def safety_check_node(state: State) -> dict:
    """纯函数节点：基于简单规则做安全检测，返回部分字段。"""
    text = state["input_text"]
    hits = [w for w in SAFETY_BANWORDS if w in text]
    result = f"触发危险词 {hits}" if hits else "未检出异常"
    return {
        "safety_result": result,
        "messages": [f"[安全检测] {result}"],
    }


# ---- 2) 调用 LLM 的节点：情感分析 ----
def _get_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)


def sentiment_node(state: State) -> dict:
    """调用 LLM 做情感判断。若无 OPENAI_API_KEY 会抛错，见 try/except 降级处理。"""
    llm = _get_llm()
    resp = llm.invoke(f"请判断以下评论的情感倾向（正面/负面/中性），只回答一个词：\n{state['input_text']}")
    return {
        "sentiment": resp.content.strip(),
        "messages": [f"[情感分析] {resp.content.strip()}"],
    }


# ---- 3) async 节点：异步安全复核（示例，实际可多节点并行）----
async def async_recheck_node(state: State) -> dict:
    """async 节点：异步地拼接一句复核说明，返回部分字段。"""
    import asyncio as _a
    await _a.sleep(0.05)  # 模拟 IO
    note = f"异步复核：safety={state.get('safety_result','?')}"
    return {"messages": [f"[async] {note}"]}


def run_sync_demo() -> None:
    """同步图：安全检测 -> 情感分析。情感分析以安全的降级方式运行，无 Key 时也能演示。"""
    builder = StateGraph(State)
    builder.add_node("safety", safety_check_node)
    builder.add_node("sentiment", _sentiment_with_fallback)
    builder.add_edge(START, "safety")
    builder.add_edge("safety", "sentiment")
    builder.add_edge("sentiment", END)
    app = builder.compile()

    print("=" * 60)
    print("GraphFlow - 同步图（安全检测 -> 情感分析）")
    print("=" * 60)
    result = app.invoke({"input_text": "这款产品用起来很舒服，推荐购买。", "messages": []})
    for k, v in result.items():
        print(f"  {k}: {v!r}")


def _sentiment_with_fallback(state: State) -> dict:
    """降级版情感节点：没有 Key 时返回占位结果，保证示例可运行。"""
    try:
        return sentiment_node(state)
    except Exception as exc:  # noqa: BLE001
        return {"sentiment": "（未配置 API Key，跳过真实分析）", "messages": [f"[情感分析] 降级：{exc.__class__.__name__}"]}


async def run_async_demo() -> None:
    """异步图：安全检测 -> async 复核。演示 async 节点与 ainvoke。"""
    builder = StateGraph(State)
    builder.add_node("safety", safety_check_node)
    builder.add_node("recheck", async_recheck_node)
    builder.add_edge(START, "safety")
    builder.add_edge("safety", "recheck")
    builder.add_edge("recheck", END)
    app = builder.compile()

    print("=" * 60)
    print("GraphFlow - 异步图（安全检测 -> 异步复核）")
    print("=" * 60)
    result = await app.ainvoke({"input_text": "这个一点也不赌，买吧。", "messages": []})
    for k, v in result.items():
        print(f"  {k}: {v!r}")


if __name__ == "__main__":
    run_sync_demo()
    asyncio.run(run_async_demo())