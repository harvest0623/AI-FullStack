# -*- coding: utf-8 -*-
"""
Day05 - 02 top_p（核采样）与 top_k

演示：
1. top_p：只保留累积概率达 p 的 token 池
2. top_k：只从概率最高的 k 个中选
3. 可视化候选池的收缩
"""

PROBS = [0.4, 0.25, 0.15, 0.08, 0.06, 0.03, 0.02, 0.01]  # 从高到低


def top_p_pool(p: float) -> list[float]:
    """返回累积概率达到 p 的前缀子集"""
    pool, acc = [], 0.0
    for prob in PROBS:
        acc += prob
        pool.append(prob)
        if acc >= p:
            break
    return pool


def top_k_pool(k: int) -> list[float]:
    return PROBS[:k]


def render(pool: list, title: str):
    print(f"  {title}: 候选 = {len(pool)} 个, 概率 = "
          + " ".join(f"{x:.2f}" for x in pool))


def main():
    print(">> top_p / top_k 候选池演示（初始 8 个 token 概率从高到低）\n")
    print("  初始概率分布：", " ".join(f"{p:.2f}" for p in PROBS), "\n")

    print("【top_p】按累积概率裁剪：")
    render(top_p_pool(0.9), "top_p=0.9")
    render(top_p_pool(0.7), "top_p=0.7")
    render(top_p_pool(0.5), "top_p=0.5")

    print("\n【top_k】只留概率最高的 k 个：")
    render(top_k_pool(3), "top_k=3")
    render(top_k_pool(5), "top_k=5")
    render(top_k_pool(1), "top_k=1 (greedy)")

    print("\n" + "-" * 60)
    print("配合理解：")
    print("  - top_p 越大越是完整分布（多样），越小越保守（只留高概率头部）")
    print("  - top_k=1 等价于始终选概率最高 -> 完全确定")
    print("  - 三者叠加时：先 top_k 后 top_p 再 temperature 共同决定")
    print("  - 结构化输出(JSON/抽取) 常把 top_p 调低以稳定")


if __name__ == "__main__":
    main()