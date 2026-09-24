# 文件用途：Transformer 概念演示
# 用 Python + numpy 演示 Self-Attention（自注意力）的计算过程：
#   Q/K/V 矩阵乘法 -> 缩放点积 -> softmax -> 加权求和
# 同时演示多头注意力（Multi-Head Attention）的概念拆分，
# 以及 Transformer 中的正弦/余弦位置编码生成。
# 本文件不依赖任何 LLM API，纯数学演示，可直接运行（需 numpy）。

import numpy as np


# ============================================================
# 一、Self-Attention 自注意力计算
# ============================================================
def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """数值稳定的 softmax 实现。"""
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def self_attention(Q: np.ndarray, K: np.ndarray, V: np.ndarray,
                   mask: np.ndarray | None = None) -> np.ndarray:
    """
    计算 Scaled Dot-Product Attention。
    公式: Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V

    参数:
        Q: (seq_len, d_k) 查询矩阵
        K: (seq_len, d_k) 键矩阵
        V: (seq_len, d_v) 值矩阵
        mask: 可选掩码，用于屏蔽某些位置（如 Decoder 的因果掩码）
    返回:
        加权求和后的输出矩阵 (seq_len, d_v)
    """
    d_k = Q.shape[-1]
    # 1) Q 与 K 的转置做点积，得到注意力分数 (seq_len, seq_len)
    scores = Q @ K.T
    # 2) 缩放：除以 sqrt(d_k)，防止点积过大导致 softmax 梯度消失
    scaled_scores = scores / np.sqrt(d_k)
    # 3) 应用掩码（若提供），被掩码位置设为 -inf，softmax 后变为 0
    if mask is not None:
        scaled_scores = np.where(mask == 0, -np.inf, scaled_scores)
    # 4) softmax 归一化，得到注意力权重
    attention_weights = softmax(scaled_scores, axis=-1)
    # 5) 注意力权重对 V 加权求和，得到最终输出
    output = attention_weights @ V
    return output, attention_weights


def demo_self_attention() -> None:
    """演示一个 3 个 Token、4 维向量的自注意力计算。"""
    print("=" * 60)
    print("一、Self-Attention 自注意力计算演示")
    print("=" * 60)
    np.random.seed(42)
    seq_len, d_model = 3, 4

    # 模拟 3 个 Token 的嵌入向量（实际中由词向量 + 位置编码得到）
    x = np.random.randn(seq_len, d_model)
    print(f"\n输入序列 X (shape={x.shape}):\n{x}\n")

    # 通过三个不同的线性变换矩阵得到 Q / K / V
    W_Q = np.random.randn(d_model, d_model)
    W_K = np.random.randn(d_model, d_model)
    W_V = np.random.randn(d_model, d_model)
    Q, K, V = x @ W_Q, x @ W_K, x @ W_V
    print(f"Q (Query) shape={Q.shape}\n{Q}\n")
    print(f"K (Key)   shape={K.shape}\n{K}\n")
    print(f"V (Value) shape={V.shape}\n{V}\n")

    output, weights = self_attention(Q, K, V)
    print(f"注意力权重矩阵 (每行加和为 1):\n{np.round(weights, 4)}\n")
    print(f"Self-Attention 输出 shape={output.shape}:\n{np.round(output, 4)}\n")


# ============================================================
# 二、Multi-Head Attention 多头注意力概念演示
# ============================================================
def multi_head_attention(x: np.ndarray, num_heads: int) -> np.ndarray:
    """
    多头注意力概念演示：将 d_model 维向量拆分为 num_heads 个子空间，
    每个头独立做 Self-Attention，最后拼接并做线性变换。
    不同的头可以捕捉不同维度的语义关系。
    """
    seq_len, d_model = x.shape
    head_dim = d_model // num_heads

    # 初始化每头各自的 Q/K/V 变换矩阵
    W_Q = np.random.randn(d_model, d_model)
    W_K = np.random.randn(d_model, d_model)
    W_V = np.random.randn(d_model, d_model)
    Q, K, V = x @ W_Q, x @ W_K, x @ W_V

    head_outputs = []
    for h in range(num_heads):
        # 切分出当前头的 Q/K/V 子空间
        start, end = h * head_dim, (h + 1) * head_dim
        Q_h = Q[:, start:end]
        K_h = K[:, start:end]
        V_h = V[:, start:end]
        out_h, _ = self_attention(Q_h, K_h, V_h)
        head_outputs.append(out_h)
        print(f"  Head {h + 1}: 捕捉一种语义关系，输出 shape={out_h.shape}")

    # 拼接所有头的输出
    concat = np.concatenate(head_outputs, axis=-1)
    # 最后通过一个线性变换融合各头信息
    W_O = np.random.randn(d_model, d_model)
    return concat @ W_O


def demo_multi_head_attention() -> None:
    print("\n" + "=" * 60)
    print("二、Multi-Head Attention 多头注意力演示")
    print("=" * 60)
    np.random.seed(7)
    x = np.random.randn(4, 8)  # 4 个 Token，8 维向量
    print(f"\n输入 shape={x.shape}，使用 4 个注意力头（每个头 2 维）\n")
    output = multi_head_attention(x, num_heads=4)
    print(f"\n多头注意力最终输出 shape={output.shape}\n")


# ============================================================
# 三、Positional Encoding 位置编码生成
# ============================================================
def sinusoidal_positional_encoding(seq_len: int, d_model: int) -> np.ndarray:
    """
    Transformer 原论文中的正弦/余弦位置编码：
      PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
      PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
    位置编码与词向量相加，使模型能感知 Token 的顺序。
    """
    pe = np.zeros((seq_len, d_model))
    position = np.arange(seq_len)[:, np.newaxis]          # (seq_len, 1)
    div_term = np.exp(np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model))
    pe[:, 0::2] = np.sin(position * div_term)             # 偶数维用 sin
    pe[:, 1::2] = np.cos(position * div_term)             # 奇数维用 cos
    return pe


def demo_positional_encoding() -> None:
    print("=" * 60)
    print("三、Positional Encoding 正弦/余弦位置编码")
    print("=" * 60)
    pe = sinusoidal_positional_encoding(seq_len=6, d_model=8)
    print(f"\n位置编码矩阵 shape={pe.shape}（6 个位置，8 维）:")
    print(np.round(pe, 4))
    print("\n说明：")
    print("- 偶数维(0,2,4,6)使用 sin 函数")
    print("- 奇数维(1,3,5,7)使用 cos 函数")
    print("- 不同位置拥有不同的编码模式，使模型能区分词序")
    print("- 现代模型（如 Llama）多采用 RoPE 旋转位置编码，原理不同但目的一致\n")


if __name__ == "__main__":
    demo_self_attention()
    demo_multi_head_attention()
    demo_positional_encoding()
    print("演示完成。本文件展示了 Transformer 三大核心组件的数学原理。")
