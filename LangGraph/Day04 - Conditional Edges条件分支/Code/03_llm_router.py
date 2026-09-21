# 文件用途：LLM 语义路由
# 用 LLM 对输入分类 -> 返回类别 -> 条件边路由到对应节点。
# 分类结果写入 state 字段，结合 PydanticOutputParser 做结构化输出。
# 场景：GraphFlow 用 LLM 判断内容是否违规 -> 路由到 通过/复核/拦截。
#
# 注意：本示例会调用 LLM。若未配置 OPENAI_API_KEY，会自动降级为规则判断，以便无 Key 也能演示。

import os
from typing import TypedDict

from dotenv import load_dotenv

load_dotenv()  # 读取 .env 中的 API Key

from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END, START


# 用 Pydantic 定义结构化分类输出
class ContentClassification(BaseModel):
    """LLM 的分类结论。"""
    is_violation: bool = Field(description="是否违规")
    severity: str = Field(description="违规严重度 low/medium/high，不违规则为 low")
    reason: str = Field(description="判断理由")


# State：分类结果作为字段传入 state
class State(TypedDict):
    input_text: str
    classification: dict       # LLM/Pydantic 的字典化输出
    verdict: str               # 路由结论 approved / review / block


parser = PydanticOutputParser(pydantic_object=ContentClassification)


def _llm_classify(text: str) -> ContentClassification:
    """调用 LLM 并解析为 Pydantic 对象。"""
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    prompt = (
        "判断下面内容是否属于违规（如辱骂、色情、暴力、诈骗）。"
        "请按 JSON 输出。\n内容：\n" + text + "\n\n" + parser.get_format_instructions()
    )
    resp = llm.invoke(prompt)
    return parser.invoke(resp.content)


def _rule_fallback(text: str) -> ContentClassification:
    """无 API Key 时的规则降级分类。"""
    if any(k in text for k in ["色情", "暴", "赌", "骂"]):
        return ContentClassification(is_violation=True, severity="high", reason="命中危险词（降级规则）")
    return ContentClassification(is_violation=False, severity="low", reason="未命中（降级规则）")


def classify_node(state: State) -> dict:
    """分类节点：返回分类结果，写回 state。"""
    try:
        clf = _llm_classify(state["input_text"])
        print("  (LLM 分类)", clf.model_dump())
    except Exception as exc:  # noqa: BLE001
        print("  (LLM 调用失败，降级为规则)", type(exc).__name__)
        clf = _rule_fallback(state["input_text"])
    return {
        "classification": clf.model_dump(),
        "verdict": "block" if clf.is_violation and clf.severity == "high"
                   else ("review" if clf.is_violation else "approved"),
    }


def approved_node(state: State) -> dict:
    return {"input_text": state["input_text"] + " | [通过]"}


def review_node(state: State) -> dict:
    return {"input_text": state["input_text"] + " | [转人工复核]"}


def block_node(state: State) -> dict:
    return {"input_text": state["input_text"] + " | [已拦截]"}


def build_graph() -> "CompiledGraph":
    b = StateGraph(State)
    b.add_node("classify", classify_node)
    b.add_node("approved", approved_node)
    b.add_node("review", review_node)
    b.add_node("block", block_node)
    b.add_edge(START, "classify")

    # path_map：根据 verdict 路由；无条件 fallback 到 approved
    def route(state: State) -> str:
        v = state["verdict"]
        return {"approved": "approved", "review": "review", "block": "block"}.get(v, "approved")

    mapping = {"approved": "approved", "review": "review", "block": "block"}
    b.add_conditional_edges("classify", route, mapping)
    for n in ["approved", "review", "block"]:
        b.add_edge(n, END)
    return b.compile()


def main() -> None:
    print("=" * 60)
    print("GraphFlow - LLM 语义路由（违规判定 → 通过/复核/拦截）")
    print("=" * 60)
    app = build_graph()
    app.get_graph().print_ascii()

    samples = [
        "今天推荐一本好书给大家，非常精彩。",
        "你这个人是骗子！滚开！",
        "这里批发各种色情内容，快来买。",
    ]
    for text in samples:
        print("\n输入:", text)
        out = app.invoke({"input_text": text, "classification": {}, "verdict": ""})
        print("  verdict:", out["verdict"], "->", out["input_text"].split(" | ")[1])


if __name__ == "__main__":
    main()