# 文件用途：注意力机制可视化演示
# 构造一个简单中文句子，计算每个词对其他词的注意力权重，
# 打印注意力矩阵，展示语义关联（如"猫吃鱼"中"猫"对"吃"的注意力较高）。
# 纯 numpy 实现，不依赖任何外部 LLM API。

import numpy as np


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """数值稳定的 softmax。"""
    x_max = np.max(x, axis=axis, keepdims=True)
    return np.exp(x - x_max) / np.sum(np.exp(x - x_max), axis=axis, keepdims=True)


def build_token_vectors(tokens: list[str], dim: int = 16, seed: int = 0) -> np.ndarray:
    """
    为每个 Token 生成一个固定随机向量（模拟词嵌入）。
    实际应用中这些向量由预训练 Embedding 模型产生，这里用随机向量演示计算流程。
    """
    rng = np.random.default_rng(seed)
    return rng.standard_normal((len(tokens), dim))


def compute_attention_weights(x: np.ndarray) -> np.ndarray:
    """
    计算自注意力权重矩阵。
    返回 (seq_len, seq_len) 矩阵，第 i 行 j 列表示第 i 个词对第 j 个词的注意力权重。
    """
    d_k = x.shape[-1]
    # 这里为演示清晰，直接用 x 同时充当 Q/K（实际中会有独立线性变换）
    Q, K = x, x
    scores = Q @ K.T / np.sqrt(d_k)        # 缩放点积
    weights = softmax(scores, axis=-1)     # 每行归一化
    return weights


def print_attention_matrix(tokens: list[str], weights: np.ndarray) -> None:
    """以表格形式打印注意力矩阵。"""
    n = len(tokens)
    # 表头
    header = "来源\\目标".ljust(6) + "".join(t.ljust(8) for t in tokens)
    print(header)
    print("-" * len(header))
    for i in range(n):
        row = tokens[i].ljust(6) + "".join(f"{weights[i][j]:.3f}".ljust(8) for j in range(n))
        print(row)


def analyze_strong_attention(tokens: list[str], weights: np.ndarray) -> None:
    """分析每个词对其他词的注意力排序，找出强关联。"""
    print("\n各词的注意力排序（从高到低，排除自身）:")
    for i, token in enumerate(tokens):
        # 排除自身后排序
        order = sorted(
            [(j, weights[i][j]) for j in range(len(tokens)) if j != i],
            key=lambda x: -x[1],
        )
        top = order[0]
        print(f"  「{token}」 最关注 -> 「{tokens[top[0]]}」 (权重 {top[1]:.3f})")


def demo_sentence(sentence: list[str], label: str, seed: int = 0) -> None:
    print("=" * 60)
    print(f"注意力可视化演示：{label}")
    print(f"句子：{''.join(sentence)}")
    print("=" * 60)
    x = build_token_vectors(sentence, dim=16, seed=seed)
    weights = compute_attention_weights(x)
    print("\n注意力权重矩阵（行=查询词，列=被关注词）:")
    print_attention_matrix(sentence, weights)
    analyze_strong_attention(sentence, weights)
    print()


def main() -> None:
    # 注意：由于使用随机词向量，此演示主要展示「注意力机制的计算流程与可视化方式」。
    # 真实语义关联需要预训练词向量才能体现（如"猫"真正关注"吃"）。
    demo_sentence(["猫", "吃", "鱼"], "短句示例", seed=1)
    demo_sentence(["我", "爱", "自然", "语言", "处理"], "稍长句子", seed=2)

    print("=" * 60)
    print("说明：")
    print("- 上述演示使用随机词向量，注意力权重反映的是向量相似度。")
    print("- 在真实模型中，词向量经过预训练编码语义，注意力能体现「猫」关注「吃」这类语法/语义关系。")
    print("- 可将 build_token_vectors 替换为真实 Embedding（如 Word2Vec/OpenAI Embedding）以观察语义注意力。")
    print("=" * 60)


if __name__ == "__main__":
    main()
