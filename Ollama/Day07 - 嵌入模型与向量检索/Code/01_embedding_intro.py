# -*- coding: utf-8 -*-
"""
Day07 - 01 嵌入与余弦相似度

展示嵌入最核心的一步：
1. 文本 → 向量（用 embed 接口）
2. 手写余弦相似度
3. 语义 vs 关键词：相近意思也能算出高分

双模式：有嵌入模型 -> 真实向量；无 -> SimOllama 伪向量兜底（逻辑一致）。
"""

import math
from ollama_util import embed_wrapper

EMBED_MODEL = "nomic-embed-text"


def cos_sim(a, b):
    """余弦相似度：向量夹角，越接近1越相似"""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


def show_vec(v, name):
    print(f"  {name}（维度 {len(v)}）前6维: "
          + " ".join(f"{x:.3f}" for x in v[:6]) + " ...")


def main():
    print(">> 嵌入与余弦相似度\n")

    texts = [
        "如何申请退款",
        "被扣了钱想退回",
        "今天的天气真好",
    ]
    vecs = [embed_wrapper(EMBED_MODEL, t) for t in texts]
    for t, v in zip(texts, vecs):
        show_vec(v, f"「{t}」")

    print("\n两两相似度（语义相关度）:")
    pairs = [(0, 1), (0, 2), (1, 2)]
    for i, j in pairs:
        sim = cos_sim(vecs[i], vecs[j])
        print(f"  sim(「{texts[i][:8]}…」, 「{texts[j][:8]}」) = {sim:.3f}")

    print("\n→ 观察：语义相近的两句（退款/退回）得分通常更高，"
          "这就是「语义检索」的基础。")
    print("  注：真实嵌入更精确；伪向量仅提供示例顺序。")


if __name__ == "__main__":
    main()