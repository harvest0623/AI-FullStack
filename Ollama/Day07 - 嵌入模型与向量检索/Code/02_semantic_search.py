# -*- coding: utf-8 -*-
"""
Day07 - 02 本地语义搜索

用一个小型 FAQ 库跑 top-k 语义检索：
1. 每条候选文档先嵌入入库
2. 查询文本也嵌入
3. 与所有候选算余弦相似度，按分取 top-k

双模式：有嵌入模型 -> 真实向量；无 -> SimOllama 伪向量兜底。
"""

import math
from ollama_util import embed_wrapper

EMBED_MODEL = "nomic-embed-text"

# 一个小型客服 FAQ 库（候选答案）
FAQ = [
    "退货政策：下单 7 天内可无理由退货。",
    "退款到账：退款一般在 3-5 个工作日原路退回。",
    "订单查询：在个人中心-我的订单可查看物流。",
    "发票开具：请在订单确认后 30 天内申请。",
    "促销活动：满 200 减 30，活动期间有效。",
    "账户安全：请勿向他人透露验证码。",
]


def cos_sim(a, b):
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


# 入库：FAQ 每条转向量
faq_vecs = [embed_wrapper(EMBED_MODEL, faq) for faq in FAQ]


def search(query: str, top_k: int = 2):
    qv = embed_wrapper(EMBED_MODEL, query)
    scored = [(cos_sim(qv, v), faq) for v, faq in zip(faq_vecs, FAQ)]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def main():
    print(">> 本地语义搜索（top-k）\n")
    print("候选 FAQ：")
    for i, faq in enumerate(FAQ):
        print(f"  [{i}] {faq}")

    for query in ["我想要回我的钱", "怎么开发票", "怎么查物流"]:
        print(f"\n查询：{query}")
        for score, faq in search(query):
            print(f"  {score:.3f}  <->  {faq}")

    print("\n→ 语义搜索能跨字面找意图：'要回钱'也能命中'退款''退货'")


if __name__ == "__main__":
    main()