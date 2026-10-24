# -*- coding: utf-8 -*-
"""
Day05 - 03 随机种子（seed）与重复惩罚（repeat_penalty）

演示：
1. seed：固定种子让采样结果"可复现"，同参数同 seed 输出稳定
2. repeat_penalty：抑制重复 token，避免模型原地打转/啰嗦循环
3. 无环境用规则演示，真实环境走真实模型

双模式：有 Ollama -> 真实 API（含 options）；无 -> 规则模拟。
"""

import random
from ollama_util import is_ollama_available, chat_wrapper, real_chat, SimOllama

TOKENS = ["我", "你", "他", "我们", "今天", "天气", "很好", "不错", "啊", "的"]


def shell_sampling(seed: int, temperature: float) -> str:
    """用固定 random seed 模拟一次采样路径（核心：seed 决定随机序列）"""
    rng = random.Random(seed)
    pick = rng.choice(TOKENS)
    return pick


def repeat_penalty_sim(repeat: float) -> list[str]:
    """
    模拟 repeat_penalty 对"已输出 token"概率的压制。
    原理：每出现一次 token，下一次再被选中的概率按 repeat 倍衰减。
    repeat=1 不去重（易循环），repeat>1 压制重复（更流畅）。
    """
    counts: dict[str, int] = {}
    seq: list[str] = []
    base = {t: 1.0 for t in TOKENS}
    rng = random.Random(7)
    for _ in range(20):
        # 对已出现 token 的权重打折
        probs = {}
        for t in TOKENS:
            w = base[t]
            c = counts.get(t, 0)
            if c:
                w *= repeat ** (-c)  # 每次出现衰减 repeat 倍
            probs[t] = max(w, 1e-3)
        total = sum(probs.values())
        r = rng.random() * total
        acc = 0.0
        chosen = TOKENS[-1]
        for t, p in probs.items():
            acc += p
            if r <= acc:
                chosen = t
                break
        seq.append(chosen)
        counts[chosen] = counts.get(chosen, 0) + 1

    unique = len(set(seq))
    return seq, unique, len(seq)


def main():
    print(">> seed 与 repeat_penalty 演示\n")

    # ---- seed 复现 ----
    print("一、seed 可复现性（同 seed 同输出）")
    print("  seed=42 连续两次：", shell_sampling(42, 0.7), "|", shell_sampling(42, 0.7))
    print("  seed=99 连续两次：", shell_sampling(99, 0.7), "|", shell_sampling(99, 0.7))

    print("\n  真实模型验证（有环境时）：")
    if is_ollama_available("llama3.1"):
        msgs = [{"role": "user", "content": "随机写 3 个互不相关的词语："}]
        a = real_chat("llama3.1", msgs, {"temperature": 0.8, "seed": 42})
        b = real_chat("llama3.1", msgs, {"temperature": 0.8, "seed": 42})
        same = "相同（已复现）" if a == b else "不同（仍有其它随机源）"
        print(f"  seed=42 第1次：{a}")
        print(f"  seed=42 第2次：{b}")
        print(f"  → {same}")
    else:
        print("  本机无 Ollama，跳过真实验证。")

    # ---- repeat_penalty ----
    print("\n二、repeat_penalty 抑制重复")
    for rp in [1.0, 1.1, 1.5]:
        seq, unique, total = repeat_penalty_sim(rp)
        print(f"  repeat_penalty={rp}: 去重词数 {unique}/{total} →  {' '.join(seq[:10])}...")

    print("\n  真实模型验证（有环境时）：")
    if is_ollama_available("llama3.1"):
        msgs = [{"role": "user", "content": "请用『今天天气很好』续写一句话，不要重复："}]
        for rp in [1.0, 1.5]:
            out = real_chat("llama3.1", msgs, {"repeat_penalty": rp})
            print(f"  repeat_penalty={rp}: {out}")
    else:
        print("  本机无 Ollama，跳过真实验证。")

    print("\n  tips: 长文生成发现啰嗦/循环 → 调大 repeat_penalty（1.1~1.3）")


if __name__ == "__main__":
    main()