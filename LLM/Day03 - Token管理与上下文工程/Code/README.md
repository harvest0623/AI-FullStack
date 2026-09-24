# Day03 Code - Token 管理与上下文工程示例

本目录包含 Day03「Token 管理与上下文工程」的配套代码，涵盖 Token 计数、上下文窗口管理、对话历史策略、成本计算四大核心能力，对应 AISearch 项目 `core/` 模块（对话管理 / Token 计数 / 上下文管理）。

## 环境准备

```bash
pip install tiktoken python-dotenv openai
```

### 配置 .env（可选）

`02_context_manager.py` 与 `03_conversation_memory.py` 的 **summary 摘要策略**会调用 LLM 自动压缩旧对话。未配置 Key 时会自动**回退为截断**，仍可运行：

```dotenv
OPENAI_API_KEY=sk-你的密钥
```

> `01_token_counter.py` 与 `04_cost_calculator.py` 纯本地计算，**无需任何 Key**。

## 文件说明

| 文件 | 核心类 | 功能 | 是否需 Key |
| --- | --- | --- | --- |
| `01_token_counter.py` | `TokenCounter` | 多模型 Token 计数、消息计数、中英代码效率对比、消耗可视化 | 否 |
| `02_context_manager.py` | `ContextManager` | Token 预算管理、自动截断/滑动窗口/摘要三种压缩策略 | summary 策略需要 |
| `03_conversation_memory.py` | `ConversationMemory` | 全量/摘要/滑动窗口三种对话历史策略实现与对比 | summary 策略需要 |
| `04_cost_calculator.py` | `CostCalculator` | 多模型价格表、单次/月度成本估算、预算告警 | 否 |

## 运行方式

```bash
python 01_token_counter.py        # Token 计数与效率对比
python 02_context_manager.py      # 上下文压缩策略演示
python 03_conversation_memory.py  # 对话历史三种策略对比
python 04_cost_calculator.py      # 成本计算与告警
```

## tiktoken 使用教程

```python
import tiktoken

# 1. 获取模型对应编码器
enc = tiktoken.encoding_for_model("gpt-4o")   # -> o200k_base
enc = tiktoken.get_encoding("cl100k_base")    # 显式指定

# 2. 文本 -> Token ID 列表
ids = enc.encode("Hello 世界")                # [9706, 53901, ...]

# 3. Token 数量
n = len(enc.encode("Hello 世界"))             # 3

# 4. Token ID -> 文本
text = enc.decode([9706])                      # 'Hello'

# 5. 批量编码
batch = enc.encode_batch(["a", "b", "c"])
```

## 各模型 Tokenizer 差异

| 模型 | 分词器 | 中文效率 |
| --- | --- | --- |
| GPT-4o / GPT-4o-mini | o200k_base（tiktoken） | 较好，比 cl100k 改进 |
| GPT-4 / GPT-3.5 | cl100k_base（tiktoken） | 一般，中文消耗较大 |
| Llama 系列 | SentencePiece | 视词表而定 |
| Claude | 专有分词器 | 较好 |
| Qwen | tiktoken/BPE 优化 | 中文效率高 |

> 实际计费以各 API 返回的 `usage` 为准，本地 tiktoken 仅为**估算**。

## 上下文窗口管理策略选择决策表

| 场景 | 推荐策略 | 理由 |
| --- | --- | --- |
| 短问答（<10 轮） | 全量保留 | Token 少，信息完整 |
| 客服/无状态问答 | 滑动窗口 | 不依赖历史，恒定成本 |
| 长对话助手 | 摘要压缩 | 保留关键信息，成本可控 |
| 含关键事实的长对话 | 选择性保留 | 保留用户指令/重要事实 |
| 超长文档处理 | 分块 + Map-Reduce | 见下「长文本处理」 |

## 成本优化技巧

1. **选对模型**：简单任务用 gpt-4o-mini / DeepSeek，复杂任务才用旗舰
2. **控制输出**：输出 Token 贵 3-4 倍，用 `max_tokens` 与精简 Prompt 限制
3. **压缩历史**：用摘要/滑动窗口避免重复发送全量历史
4. **复用缓存**：DeepSeek/OpenAI 的上下文缓存命中后输入价大降
5. **批量处理**：异步批量调用提升吞吐，降低单位时间成本
6. **降维 Embedding**：检索用降维后向量（见 Day04），存储与计算更省

## 长文本处理最佳实践

当文档远超上下文窗口时，三种经典模式：

| 模式 | 流程 | 适用 |
| --- | --- | --- |
| **Map-Reduce** | 分块各自处理 → 合并结果 | 摘要、统计 |
| **Refine** | 前块结果 + 后块 → 逐步精炼 | 需要全局连贯的摘要 |
| **Map-Rerank** | 分块各自处理+评分 → 取最佳 | 问答、抽取 |

分块策略：
- **固定长度**：按 Token 数切分，简单但可能切断语义
- **语义分块**：按句子/段落切，保留语义完整
- **递归分块**：段落→句子→字符逐级降级
- **重叠分块**：块间留 overlap（如 100 tokens），保持上下文连续

## 下一步

Token 与上下文管好后，进入 Day04 学习 **Embedding 与向量表示**——把文本变成可计算的向量，实现语义搜索，这是 RAG（检索增强生成）的基础。
