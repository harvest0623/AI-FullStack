# Day01 Code - LLM 架构原理代码示例

本目录包含 Day01「LLM 基础与架构原理」配套的代码示例，用纯 Python + numpy + tiktoken 演示 Transformer 的核心数学原理，无需调用任何 LLM API 即可运行，帮助你从「调用者」深入到「理解者」。

## 环境准备

```bash
# 推荐使用 Python 3.10+
pip install numpy tiktoken
```

> 本目录的脚本不调用 LLM API，因此**不需要**配置 `.env` 或 API Key。`03_tokenization_demo.py` 需要联网首次下载 tiktoken 编码表（约几百 KB，缓存到本地）。

## 文件说明

| 文件 | 用途 | 关键概念 | 依赖 |
| --- | --- | --- | --- |
| `01_transformer_concepts.py` | Transformer 核心组件数学演示 | Self-Attention 公式、Q/K/V 矩阵、多头注意力、正弦位置编码 | numpy |
| `02_attention_demo.py` | 注意力权重可视化 | 注意力矩阵、词与词的关注关系 | numpy |
| `03_tokenization_demo.py` | GPT BPE 分词器演示 | Token 切分、Token ID、中英文 Token 效率对比 | tiktoken |

## 运行方式

```bash
# 在本目录下执行
python 01_transformer_concepts.py
python 02_attention_demo.py
python 03_tokenization_demo.py
```

## 核心代码片段速览

### 1. Self-Attention 公式实现

```python
def self_attention(Q, K, V):
    d_k = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)        # 缩放点积
    weights = softmax(scores, axis=-1)     # softmax 归一化
    return weights @ V                      # 对 V 加权求和
```

对应公式：`Attention(Q,K,V) = softmax(QK^T / √d_k) V`

### 2. 多头注意力拆分思路

将 `d_model` 维向量拆成 `num_heads` 个子空间，每个头独立做 Self-Attention，最后拼接 + 线性变换。不同头捕捉不同语义关系（如语法关系、指代关系、长距离依赖等）。

### 3. 正弦位置编码

```python
PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

使无序的 Token 序列获得位置信息。现代模型多改用 **RoPE 旋转位置编码**（相对位置编码），原理不同但目的相同。

## Transformer 论文解读要点

论文：*Attention Is All You Need* (Vaswani et al., 2017)

| 要点 | 说明 |
| --- | --- |
| 核心创新 | 抛弃 RNN/CNN，仅用 Self-Attention 建模序列 |
| 并行优势 | Self-Attention 可对整个序列并行计算，训练效率远高于 RNN |
| 长距离依赖 | 任意两 Token 间路径长度为 O(1)，缓解长依赖问题 |
| 编码器-解码器 | 6 层 Encoder + 6 层 Decoder，每层含多头注意力 + FFN |
| 残差 + LayerNorm | 每个子层包裹 `LayerNorm(x + Sublayer(x))`，稳定训练 |
| 复杂度 | 序列长度 n 的复杂度为 O(n²·d)，长序列开销大（催生 FlashAttention / 稀疏注意力） |

## GPT 模型演进史

| 版本 | 年份 | 参数量 | 关键变化 |
| --- | --- | --- | --- |
| GPT-1 | 2018 | 1.17 亿 | 验证「预训练 + 微调」范式 |
| GPT-2 | 2019 | 15 亿 | Zero-shot，因风险最初不放开完整模型 |
| GPT-3 | 2020 | 1750 亿 | In-context Learning / Few-shot，标志 LLM 时代 |
| InstructGPT | 2022 | 1750 亿 | 引入 RLHF，对齐人类偏好 |
| GPT-3.5 / ChatGPT | 2022 | ~1750 亿 | 对话优化，引爆大众市场 |
| GPT-4 | 2023 | 未公开（推测 MoE） | 多模态、推理能力大幅提升 |
| GPT-4o | 2024 | 未公开 | 原生多模态（文/图/音/视频） |
| o1 / o3 | 2024-2025 | 未公开 | 推理模型，强化思维链 CoT |

## 主流模型参数对比表

| 模型 | 参数量 | 架构 | 上下文窗口 | 特点 |
| --- | --- | --- | --- | --- |
| GPT-4o | 未公开 | Dense | 128K | OpenAI 旗舰，多模态 |
| Claude 3.5 Sonnet | 未公开 | Dense | 200K | Anthropic，长文本强 |
| Llama 3.1 405B | 4050 亿 | Dense | 128K | Meta 开源旗舰 |
| Llama 3.1 8B/70B | 80/700 亿 | Dense | 128K | 开源主力，可本地部署 |
| Qwen 2.5 72B | 720 亿 | Dense | 128K | 中文能力强 |
| Mixtral 8x7B | 467 亿（激活 13B） | MoE | 32K | 欧洲开源 MoE |
| DeepSeek-V3 | 6710 亿（激活 37B） | MoE | 128K | 国产开源，推理/性价比高 |

## 推荐学习资源

- **论文**：*Attention Is All You Need* (2017)、*GPT-3: Language Models are Few-Shot Learners* (2020)、*InstructGPT / RLHF* (2022)
- **可视化**：Jay Alammar《The Illustrated Transformer》（图解 Transformer 必读）
- **3Blue1Brown**：神经网络系列视频，直观理解注意力机制
- **哈佛 NLP**：*The Annotated Transformer*（带代码逐行注释的论文复现）
- **开源仓库**：Hugging Face `transformers`、Meta `llama`、`unsloth`（微调加速）

## 下一步

完成本目录的三个脚本后，建议你：
1. 修改 `01_transformer_concepts.py` 中的 `d_model` 和 `seq_len`，观察注意力权重变化。
2. 在 `02_attention_demo.py` 中替换为更长的句子，思考注意力矩阵的规模增长（O(n²)）。
3. 用 `03_tokenization_demo.py` 测试自己的文档，估算其在 GPT-4o 上的 Token 消耗。

理解了架构原理后，进入 Day02 学习如何通过 API 调用这些大模型。
