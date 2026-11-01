# -*- coding: utf-8 -*-
"""
文件用途：Day06 - 01 Bi-Encoder 与 CrossEncoder 概念模拟
用简化的数值模拟解释两种编码器为何在"相关性判断"上精度不同：
  - Bi-Encoder：把 查询、文档 各自编码成向量，用点积近似相关。
  - CrossEncoder：把 [查询, 文档] 拼接送入能给"深层交互"的打分器。

运行：python 01_rerank_concept.py（无需联网）
"""

import math


def bag_vec(text: str) -> dict[str, int]:
    d = {}
    for tok in text.replace("，", " ").replace("。", " ").split():
        d[tok] = d.get(tok, 0) + 1
    return d


def cos_bag(a: dict, b: dict) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb or 1)


def crossencoder_score(query: str, doc: str) -> float:
    """把 [查询, 文档] 作为一个整体打分（简化：词袋 + 交互项奖励共现）。"""
    q = set(query.replace("，", " ").replace("。", " ").split())
    d = set(doc.replace("，", " ").replace("。", " ").split())
    overlap = len(q & d)
    # 基础相似 + 共现奖励，模拟 CrossEncoder 能看到"查询与文档的交互"
    return cos_bag(bag_vec(query), bag_vec(doc)) + 0.3 * overlap


def main() -> None:
    query = "报销住宿每天上限多少"
    docs = {
        "A": "差旅报销需提交申请并附发票",
        "B": "年假每年15天需提前申请",
        "C": "住宿每天上限500元，超出部分自理",
    }

    print("问题：", query, "\n")
    print("Bi-Encoder（词袋余弦，模拟双塔只比较低层表示）：")
    for name, d in docs.items():
        print(f"   {name}: cos={cos_bag(bag_vec(query), bag_vec(d)):+.3f}")
    print("\nCrossEncoder（拼接后加共现交互，能看到深层语义）：")
    for name, d in docs.items():
        print(f"   {name}: score={crossencoder_score(query, d):+.3f}")

    print("\n结论：Bi-Encoder 可能把'A提交/发票'误判较近，")
    print("      CrossEncoder 因看到查询与文档的共现细节，能把真正相关的 C 排到最前。")


if __name__ == "__main__":
    main()