# -*- coding: utf-8 -*-
"""
Day07 - 04 嵌入驱动的简单检索（迷你 RAG 前奏）

完整链路：文档切块 → 入库 → 查询 embed → 取最相似块 → 拼接回答
这几乎是 RAG 检索层的雏形，Day09/10 会叠加框架与对话模型。

双模式：有嵌入模型 -> 真实向量；无 -> 伪向量兜底。
"""

import math
from ollama_util import embed_wrapper

EMBED_MODEL = "nomic-embed-text"

FAQ = [
    ("退款到账时间", "退款在原路退回，3-5 个工作日到账。"),
    ("退货期限", "签收 7 天内可无理由退货。"),
    ("发票申请", "确认收货后 30 天内可申请发票。"),
    ("优惠券退款", "退款按实付金额计算，优惠券不退。"),
]


def cos_sim(a, b):
    if not a or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


def build_index():
    """入库：答案文本转向量"""
    idx = []
    for topic, ans in FAQ:
        idx.append((topic, ans, embed_wrapper(EMBED_MODEL, ans)))
    return idx


def retrieve(index, query, top_k=1):
    qv = embed_wrapper(EMBED_MODEL, query)
    scored = [(cos_sim(qv, v), topic, ans) for topic, ans, v in index]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def main():
    print(">> 嵌入驱动的简单检索（迷你 RAG）\n")
    index = build_index()
    print(f"已入库 {len(index)} 条知识。\n")

    for query in ["我退货了多久能收到退款", "怎么开发票"]:
        score, topic, ans = retrieve(index, query)[0]
        print(f"查询：{query}")
        print(f"  命中「{topic}」（相似度 {score:.3f}）")
        print(f"  检索到答案：{ans}\n")

    print("→ 检索到最相关片段 = RAG 的『检索(retrieval)』步骤")


if __name__ == "__main__":
    main()