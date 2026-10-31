# -*- coding: utf-8 -*-
"""
文件用途：Day04 - 04 嵌入质量检验
用"相似问句对 / 不相关问句对"对嵌入模型做 sanity check，
量化判断模型是否适合你的领域与语种。

运行：python 04_embedding_quality.py
依赖：langchain-openai（OPENAI_API_KEY），无 Key 时降级本地哈希
"""

import os
import math
import hashlib
from dotenv import load_dotenv

load_dotenv()

# 每个测试项：(a, b, 期望是否相似, 说明)
CASES = [
    ("报销住宿每天上限多少", "出差住宿能报销多少钱", True, "语义相关·同主题"),
    ("年假有几天", "每年多少天带薪年假", True, "语义相关·同主题"),
    ("怎么申请年假", "在 HR 系统提交年假申请", True, "语义相关·动作"),
    ("报销住宿上限", "今天天气怎么样", False, "语义不相关"),
    ("远程办公定了吗", "年终奖怎么发放", False, "语义不相关·主题相差大"),
]


def cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb or 1)


def hash_vec(text: str, dim: int = 16) -> list[float]:
    out = []
    for i in range(dim):
        h = int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16)
        out.append((h % 2000) / 1000.0 - 1.0)
    return out


def main() -> None:
    try:
        from langchain_openai import OpenAIEmbeddings
        backend = OpenAIEmbeddings(model="text-embedding-3-small")
        enc = backend.embed_query
        enc_docs = backend.embed_documents
        label = "[OpenAIEmbeddings]"
    except Exception:
        enc = hash_vec
        enc_docs = lambda ts: [hash_vec(t) for t in ts]
        label = "[降级 HashEmbedding]"

    print(f"模型：{label}\n")
    vecs = enc_docs([c[0] for c in CASES] + [c[1] for c in CASES])
    half = len(CASES)
    n_correct = 0
    for i, (a, b, expect, desc) in enumerate(CASES):
        va, vb = vecs[i], vecs[half + i]
        s = cos(va, vb)
        verdict = (s > 0.5) if expect else (s < 0.5)
        # 统一方向：期望相似则分越高越好，期望不相关则越低越好
        ok = (expect and s > 0.4) or (not expect and s < 0.6)
        n_correct += bool(ok)
        print(f"  {'✓' if ok else '✗'} sim={s:+.4f}  期望{'相关' if expect else '不相关'} | {a} ✂ {b} | {desc}")
    print("-" * 55)
    if label == "[OpenAIEmbeddings]":
        print(f"sanity check 通过率：{n_correct}/{len(CASES)}")
        print("超过阈值算通过；若明显偏低，需更换多语言/领域模型。")
    else:
        print("当前为降级哈希，仅供参考流程；配置 OPENAI_API_KEY 后可见真实语义区分度。")


if __name__ == "__main__":
    main()