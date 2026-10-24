# -*- coding: utf-8 -*-
"""
Day05 - 01 温度（temperature）对输出的影响

演示：
1. 采样机制的概念（概率分布灰-选择）
2. 低温 vs 高温：同样的简单填空题，看确定性差异
3. 无环境用规则演示（真实环境走真实模型）
"""

import random
from ollama_util import is_ollama_available, chat_wrapper

# 一个随机数池：模拟"模型的不同采样结果"
CANDIDATES = ["确定无疑A", "比较可能B", "微弱可能C", "边缘选项D", "冷门E"]


def simulate_sampling(temperature: float, draws: int = 1) -> list[str]:
    """
    模拟温度对"挑选"的影响。
    原理：低温放大概率差（加权后仍偏向头部），高温拉平（更像均匀随机）。
    """
    probs = [0.5, 0.3, 0.12, 0.06, 0.02]  # 初始概率分布
    # 温度 t: 概率放大 1/t 次幂后再归一化；t 越大越平
    if temperature <= 0.01:
        return [CANDIDATES[0]]
    inv = 1.0 / temperature
    weighted = [p ** inv for p in probs]
    total = sum(weighted)
    norm = [w / total for w in weighted]
    # 按归一化概率采样
    result = []
    for _ in range(draws):
        r = random.random()
        acc = 0.0
        picked = norm[-1]
        for cand, p in zip(CANDIDATES, norm):
            acc += p
            if r <= acc:
                picked = cand
                break
        result.append(picked)
    return result


def explain(t: float):
    probs = [0.5, 0.3, 0.12, 0.06, 0.02]
    inv = 1.0 / t if t > 0.01 else 1e9
    weighted = [p ** inv for p in probs]
    total = sum(weighted)
    norm = [w / total for w in weighted]
    print(f"  温度 {t}: 归一化后概率 → "
          + " ".join(f"{p:.3f}" for p in norm)
          + "(越平=越多样)")


def main():
    random.seed(5)
    print(">> temperature 演示：同样的分布，不同温度的选择\n")

    print("初始概率分布（模型给的）：")
    print("   A=0.50  B=0.30  C=0.12  D=0.06  E=0.02\n")

    for t in [0.1, 0.7, 1.2]:
        explain(t)
        picks = simulate_sampling(t, draws=8)
        head = picks[0]
        print(f"     8 次采样结果：{' '.join(picks)}")
        print(f"     → 高频选中: {head}")
        print()

    print("-" * 60)
    print("真实模型验证（有环境时）：")
    print("  低温 vs 高温，让模型续写同一句话，观察差异")
    text = "请用一个词填空：太阳从东方___。"
    for t in [0.1, 1.2]:
        ans = chat_wrapper("llama3.1",
                           [{"role": "user", "content": text}],
                           {"temperature": t}, verbose=True)
        print(f"  temp={t}: {ans}")
    print("\n  tips: 事实场合格用低温（稳定），创意写作用高温（多样）。")


if __name__ == "__main__":
    main()