# -*- coding: utf-8 -*-
"""
文件用途：Day01 - 02 RAG 完整流程预览（最小可运行骨架）
用极简代码把 RAG 的三步流程（索引 → 检索 → 生成）串起来跑通。
本文件刻意精简，仅用于"看全貌"；后续每天会在一处处替换为工程级实现。

流程：加载文档 → 切块 → 向量库索引 → 查询嵌入 → 相似度检索 TopK → 注入 Prompt → 生成。

运行：python 02_rag_pipeline_preview.py
依赖：langchain-core langchain-community langchain-openai
      faiss-cpu（向量库后端）
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------- 仅离线演示时使用的简易关键词检索 ----------
def simple_keyword_retrieve(question: str, chunks: list[tuple[str, str]], top_k: int = 2) -> list[tuple[str, str]]:
    """无向量库时的降级检索：按关键词共现打分（真实项目请用向量检索，见 Day05）。"""
    q_words = set(question.replace("的", " ").replace("？", " ").split())
    scored: list[tuple[float, str, str]] = []
    for title, text in chunks:
        text_words = set(text.replace("，", " ").replace("。", " ").split())
        score = len(q_words & text_words)
        scored.append((score, title, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(t, x) for _, t, x in scored[:top_k]]


# ---------- 供后续真实演示用的 LLM 调用 ----------
def call_llm(context: str, question: str) -> str:
    try:
        from openai import OpenAI

        client = OpenAI()
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system",
                 "content": "你是企业知识库助手，只依据上下文回答，不编造。"},
                {"role": "user", "content": f"上下文：\n{context}\n\n问题：{question}"},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[!] 未配置有效 OPENAI_API_KEY（{e}）"


# ---------- 数据：DataIQ 知识库的几则"文档块" ----------
KNOWLEDGE_CHUNKS = [
    ("远程办公", "员工每周最多可以远程办公三天，需保证上午 10 点到下午 4 点在线。"),
    ("报销制度", "差旅报销需在出差结束后 5 个工作日内提交，住宿每天上限 500 元。"),
    ("年假制度", "DataIQ 提供每年 15 天带薪年假，需提前 3 天在 HR 系统提交。"),
    ("支付方式", "DataIQ 支持支付宝、微信支付、对公转账与云闪付，不支持货到付款。"),
]


def main() -> None:
    question = "我们每年有几天带薪年假？"

    print("===== Step1·索引（Indexing）：文档入库 =====")
    # 真实项目：切块 → 嵌入 → 写入向量库（此处用内存列表模拟）
    print(f"已索引 {len(KNOWLEDGE_CHUNKS)} 个知识块")

    print("\n===== Step2·检索（Retrieval）：查询太检索 TopK =====")
    hits = simple_keyword_retrieve(question, KNOWLEDGE_CHUNKS, top_k=2)
    for title, text in hits:
        print(f"  - [{title}] {text}")
    context = "\n".join(text for _, text in hits)

    print("\n===== Step3·生成（Generation）：注入 Prompt 并作答 =====")
    answer = call_llm(context, question)
    print(answer)

    print("\n===== 全流程预览完成 =====")
    print("后续优化点预览：")
    print("  · 切块与嵌入（Day03/04）替代关键词检索")
    print("  · 向量库与元数据过滤（Day05）")
    print("  · 重排 + 查询改写 + 混合检索（Day06-08）")


if __name__ == "__main__":
    main()