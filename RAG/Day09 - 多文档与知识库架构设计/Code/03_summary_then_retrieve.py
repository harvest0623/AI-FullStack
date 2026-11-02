# -*- coding: utf-8 -*-
"""
文件用途：Day09 - 03 先摘要、再检索（Agentic RAG 模式）
演示"两级检索"：先用文档摘要/索引定位"哪几篇"，再深入选中的文档做块级检索。

运行：python 03_summary_then_retrieve.py
依赖：无（含 LLM 占位，无 Key 也走本地演示）
"""

# 模拟"文档库"：每篇文档有 摘要 与 若干正文块
DOCS = {
    "报销合规手册": {
        "summary": "本文档规定报销流程、发票要求与住宿标准。",
        "chunks": [
            "报销需在出差结束后5个工作日内提交，附有效发票",
            "住宿每日上限500元，超出部分自理",
        ],
    },
    "人力资源手册": {
        "summary": "本文档规定年假、病假与考勤制度。",
        "chunks": [
            "年假每年15天，需提前3天在HR系统提交",
            "病假需提供医院证明，不计入年假",
        ],
    },
}


def step1_doc_retrieve(query):
    """文档级检索：用摘要命中，返回最相关的文档名列表。"""
    qset = set(query)
    scored = sorted(
        ((sum(1 for c in qset if c in meta["summary"]), name)
         for name, meta in DOCS.items()), reverse=True)
    return [name for _, name in scored[:1]]


def step2_chunk_retrieve(query, doc_names):
    """块级检索：只在选中文档里精读。"""
    qset = set(query)
    out = []
    for name in doc_names:
        for ch in DOCS[name]["chunks"]:
            score = sum(1 for c in qset if c in ch)
            out.append((name, ch, score))
    out.sort(key=lambda x: x[2], reverse=True)
    return out[:2]


def main() -> None:
    q = "住宿报销上限是多少？"
    print("问题：", q)
    picked = step1_doc_retrieve(q)
    print("① 文档摘要检索 → 选中：", picked)
    chunks = step2_chunk_retrieve(q, picked)
    print("② 仅在选中文档内做块级检索：")
    for name, ch, sc in chunks:
        print(f"   [{name}] {ch}")
    print("\n③ 将上述块作为上下文交给 LLM 生成（此处演示上下文构成）。")
    print("\n价值：先定位文档缩小范围，避免从海量文档直接块检，更省成本更准。")


if __name__ == "__main__":
    main()