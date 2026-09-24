# Day03 - Token 管理与上下文工程

Token 是 LLM 的计量单位——计费、限流、上下文窗口都以它为单位。上下文窗口是有限资源：每轮对话都要把历史发回去，对话越长 Token 越多、越贵、越慢，还可能触发「Lost in the Middle」。所以**管理 Token 就是管理成本和质量**。本章从 Token 概念与计数工具出发，深入上下文窗口管理策略、对话历史压缩、成本估算、分块与长文本处理，帮你把 LLM 用得又省又稳，这是把 Demo 变成生产级应用的关键一跃。

## 学习目标

- 深入理解 Token 概念，掌握不同语言/模型的 Token 效率差异
- 熟练使用 tiktoken 进行 Token 计数（文本与对话消息）
- 掌握四种上下文管理策略：截断、摘要、滑动窗口、选择性保留
- 能实现对话历史管理器，对比三种策略的 Token 消耗与信息保留
- 掌握 Token 成本计算与月度预算告警
- 理解 Lost in the Middle 问题与上下文工程最佳实践
- 掌握分块策略与长文本处理三种模式（Map-Reduce / Refine / Map-Rerank）

---

## 一、Token 概念深入

### Token ≠ 字符 ≠ 单词

LLM 用 **BPE（Byte Pair Encoding）** 把文本切成子词（subword）单元，Token 就是这些子词。一个 Token 可能是：

- 一个完整单词（如 `hello`）
- 一个词的一部分（如 `un` + `believe` + `able`）
- 一个汉字（如 `语`）
- 一个字节（罕见字符被拆成多字节）

### 不同语言的 Token 效率

| 语言/类型 | 1 Token ≈ | 说明 |
| --- | --- | --- |
| 英文 | 0.75 个单词（~4 字符） | 效率最高，BPE 对英文优化好 |
| 中文 | 0.5-0.7 个汉字 | 相同语义消耗更多 Token，成本更高 |
| 代码 | 2-4 个字符 | 含符号与缩进，介于英文与中文之间 |

> 这就是为什么中文应用尤其要关注 Token 成本——同样一段意思，中文可能比英文贵 2-3 倍。

### 不同模型 Tokenizer 不同

| 模型 | 分词器 |
| --- | --- |
| GPT-4o / GPT-4o-mini | `o200k_base`（tiktoken） |
| GPT-4 / GPT-3.5 | `cl100k_base`（tiktoken） |
| Llama | SentencePiece |
| Claude | 专有分词器 |

所以「Token 数」依赖具体模型，跨模型不能直接比较。

---

## 二、tiktoken 库详解

`tiktoken` 是 OpenAI 开源的高性能 BPE 分词库（Rust 实现，Python 调用）。

```bash
pip install tiktoken
```

### 核心 API

```python
import tiktoken

# 1. 获取模型对应编码器
enc = tiktoken.encoding_for_model("gpt-4o")  # 自动选 o200k_base

# 2. 文本 -> Token ID 列表
token_ids = enc.encode("Hello 世界")

# 3. Token ID -> 文本
text = enc.decode(token_ids)

# 4. Token 数量
n = len(enc.encode("Hello 世界"))

# 5. 批量编码（比循环 encode 快）
results = enc.encode_batch(["text1", "text2"])
```

### 对话消息 Token 估算

OpenAI 官方给出的近似算法：每条消息 = `3 + content_tokens`（带 `name` 字段再加 1），对话末尾加 3。完整实现见 `Code/01_token_counter.py` 的 `count_messages`。

> 注意：这是**估算**，实际计费以 API 返回的 `usage` 为准。

---

## 三、上下文窗口管理策略

当对话变长，Token 超过预算时，需要主动管理。四种策略：

| 策略 | 做法 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **截断 Truncation** | 丢弃最早的旧消息 | 简单 | 丢失早期信息 |
| **摘要 Summary** | 旧对话压缩成摘要 | 保留关键信息 | 摘要有损、需调 LLM |
| **滑动窗口 Sliding** | 只保留最近 K 轮 | 成本恒定 | 无长期记忆 |
| **选择性保留 Selective** | 保留关键事实/指令 | 信息密度高 | 实现复杂 |

### 截断策略

```python
while total_tokens(messages) > budget:
    messages.pop(0)  # 丢最早的
```

### 摘要压缩

```python
# 旧对话 -> LLM 生成摘要 -> 替换为一条 system 摘要消息
summary = llm("把以下对话压缩成摘要", old_dialog)
messages = [{"role":"system","content":f"[历史摘要]{summary}"}] + recent_messages
```

### 滑动窗口

```python
keep = K * 2  # 每轮 user+assistant
messages = messages[-keep:]
```

### 选择性保留

保留：用户明确指令、关键事实（姓名/偏好/决策）、System Prompt；丢弃：寒暄、重复确认。可结合 Embedding 检索历史相关片段（即 RAG for memory）。

---

## 四、对话历史管理

对应 `Code/03_conversation_memory.py` 的三种实现：

| 策略 | Token 消耗 | 信息保留 | 实现复杂度 | 适用 |
| --- | --- | --- | --- | --- |
| 全量保留 full | 线性增长 O(n) | 100% | 最简单 | 短对话 |
| 滑动窗口 sliding | 恒定 O(1) | 仅近期 | 简单 | 无状态问答 |
| 摘要压缩 summary | 受控 O(√n) | 摘要+近期 | 中等 | 长对话助手 |

**核心权衡**：Token 成本 vs 信息完整性 vs 实现复杂度。生产级长对话助手推荐**摘要压缩**。

---

## 五、Token 成本计算

### 公式

```
单次成本 = (输入Token × 输入单价 + 输出Token × 输出单价) / 1,000,000
月度成本 = 日均调用次数 × 单次成本 × 30
```

### 价格表示例（USD / 1M tokens）

| 模型 | 输入 | 输出 |
| --- | --- | --- |
| gpt-4o | $2.5 | $10 |
| gpt-4o-mini | $0.15 | $0.6 |
| claude-3-5-sonnet | $3 | $15 |
| deepseek-chat | ~$0.14 | ~$0.28 |

> 完整价格表见 `Code/04_cost_calculator.py` 的 `DEFAULT_PRICING`。

### 月度成本估算方法

1. 估算日均调用次数 N
2. 估算平均输入/输出 Token（用 tiktoken 实测）
3. 查模型单价
4. `月度成本 = N × (输入Token×输入价 + 输出Token×输出价) / 1M × 30`

> 实际生产应接入日志统计真实 `usage`，比估算更准。

---

## 六、上下文窗口与性能关系

### Lost in the Middle 问题

研究表明，LLM 对上下文**开头和结尾**的信息关注多，**中间**的信息容易被忽略。当上下文很长时，放在中间的关键信息可能「丢失」。

### 最佳实践

- **重要信息放开头和结尾**：System Prompt 放开头，关键问题放结尾
- **能用短上下文就别用长**：越长越贵越慢，且 Lost in the Middle 风险增加
- **结构化分隔**：用标记（如 `---`、`[文档]`）帮模型定位信息
- **重排序**：检索后把最相关片段放两端

### 上下文越长越贵越慢

- **成本**：Token 线性增长 → 成本线性增长
- **延迟**：Self-Attention 复杂度 O(n²)，长上下文推理更慢
- **所以**：长上下文是「能力」也是「负担」，按需使用

---

## 七、分块策略 Chunking

处理长文档（如 RAG 检索）时需先分块：

| 策略 | 做法 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **固定长度** | 按 Token 数切分 | 简单可控 | 可能切断语义 |
| **语义分块** | 按句子/段落切 | 语义完整 | 块大小不均 |
| **递归分块** | 段落→句子→字符逐级降级 | 灵活适应 | 实现稍复杂 |
| **重叠分块** | 块间留 overlap | 保持上下文连续 | 存储冗余 |

**经验值**：常用块大小 500-1000 Token，重叠 50-200 Token。

### 递归分块示例（LangChain 思路）

```python
def recursive_split(text, chunk_size=500, separators=["\n\n", "\n", "。", " "]):
    # 先用最大分隔符切，块仍太大就降级到更小分隔符
    ...
```

---

## 八、长文本处理模式

文档远超上下文窗口时，三种经典处理模式：

| 模式 | 流程 | 适用场景 | 优点 |
| --- | --- | --- | --- |
| **Map-Reduce** | 分块各自处理 → 合并结果 | 统计、计数、摘要 | 并行快 |
| **Refine** | 前块结果 + 后块 → 逐步精炼 | 连贯长摘要 | 全局连贯 |
| **Map-Rerank** | 分块各自处理 + 评分 → 取最佳 | 问答、抽取 | 选最相关 |

### Map-Reduce 示例

```
文档 → [块1, 块2, 块3]
       ↓ 各自摘要
       [摘1, 摘2, 摘3]
       ↓ 合并再摘要
       最终摘要
```

### Refine 示例

```
块1 → 摘要1
摘要1 + 块2 → 摘要2（更精炼）
摘要2 + 块3 → 摘要3（最终）
```

---

## 关键知识点总结

### 1. Token 消耗估算表

| 类型 | 字符/Token | 1000字约消耗 |
| --- | --- | --- |
| 英文 | ~4 | ~250 Token |
| 中文 | ~1.5-2 | ~500-650 Token |
| 代码 | ~2-4 | ~250-500 Token |

### 2. 上下文管理策略对比表

| 策略 | Token | 信息 | 复杂度 | 适用 |
| --- | --- | --- | --- | --- |
| 截断 | 低 | 差 | 简单 | 临时 |
| 摘要 | 中 | 中 | 中 | 长对话 |
| 滑动窗口 | 恒定 | 仅近期 | 简单 | 无状态 |
| 选择性 | 低 | 高 | 复杂 | 关键事实 |

### 3. 分块策略对比表

| 策略 | 语义完整 | 大小均匀 | 实现难度 |
| --- | --- | --- | --- |
| 固定长度 | 差 | 好 | 低 |
| 语义分块 | 好 | 差 | 中 |
| 递归分块 | 较好 | 中 | 中 |
| 重叠分块 | 中（冗余） | 中 | 低 |

### 4. 成本计算公式

```
单次 = (输入Token×输入价 + 输出Token×输出价) / 1M
月度 = 日均次数 × 单次 × 天数
```

### 5. 长文本处理模式对比

| 模式 | 并行 | 连贯性 | 适用 |
| --- | --- | --- | --- |
| Map-Reduce | 高 | 中 | 统计/摘要 |
| Refine | 低 | 高 | 连贯摘要 |
| Map-Rerank | 高 | - | 问答抽取 |

---

## 代码文件说明

| 文件 | 核心类 | 内容 |
| --- | --- | --- |
| `Code/01_token_counter.py` | `TokenCounter` | 多模型计数、消息计数、效率对比、可视化 |
| `Code/02_context_manager.py` | `ContextManager` | Token 预算 + 三种压缩策略 |
| `Code/03_conversation_memory.py` | `ConversationMemory` | 三种历史策略对比 |
| `Code/04_cost_calculator.py` | `CostCalculator` | 价格表 + 单次/月度估算 + 告警 |
| `Code/README.md` | - | tiktoken 教程、决策表、成本优化、长文本实践 |

> `01` 与 `04` 无需 Key 即可运行；`02`/`03` 的 summary 策略可选调用 LLM，未配置 Key 自动回退。

---

## 实战练习

### 练习 1：估算你的应用成本

假设你做一个客服机器人，日均 2000 次对话，每次平均输入 1200 Token、输出 300 Token。用 `04_cost_calculator.py` 估算：
1. 用 gpt-4o 与 gpt-4o-mini 的月度成本分别是多少？
2. 若改用 DeepSeek-chat，能省多少？
3. 如果把历史用摘要压缩使输入降到 600 Token，月度成本下降多少？

### 练习 2：实现选择性保留策略

在 `03_conversation_memory.py` 基础上实现 `SelectiveMemory`：用规则（或 Embedding 检索）保留「包含用户姓名/偏好的消息」+「最近 K 轮」，其余丢弃。对比它与 summary 策略的 Token 消耗与信息保留。

### 练习 3：长文档 Map-Reduce 摘要

选一篇 5000 字以上的技术文章，用 tiktoken 分成 5 块，对每块调用 LLM 摘要（map），再把 5 份摘要合并成总摘要（reduce）。统计总 Token 消耗，并思考：相比直接塞进长上下文，Map-Reduce 的优劣各是什么？

---

## 下一步

你已经会管理 Token、压缩历史、控制成本了。但要让 LLM「找到」相关信息，还需要**语义搜索**——这就需要把文本变成向量。Day04 学习 **Embedding 与向量表示**：文本如何编码为向量、如何计算相似度、如何实现语义搜索与可视化，这是 RAG 与推荐系统的基础。
