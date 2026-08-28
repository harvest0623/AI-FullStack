# Day06 - Memory 对话记忆管理

LLM 本身是无状态的——每次调用都是一次全新的开始，它不记得上一句你说了什么。这意味着如果没有记忆机制，多轮对话就无从谈起：用户问"它多少钱"，模型根本不知道"它"指什么。Memory 组件就是为解决这个问题而生：它管理对话历史，在每次调用时把历史消息注入 Prompt，让 LLM "记住"上下文，实现真正的连续对话。本章将带你遍历五种记忆策略，理解它们的取舍，并掌握 LangChain 0.3 推荐的 `RunnableWithMessageHistory` 用法，为 ChainQA 加上多轮对话能力。

---

## 学习目标

- 理解 Memory 的核心问题：LLM 无状态，需要手动管理对话历史
- 掌握五种 Memory 策略的原理与适用场景
- 熟练使用 `RunnableWithMessageHistory` 在 LCEL 链中接入记忆
- 理解 `BaseChatMessageHistory` 及其持久化方案
- 能够管理多会话记忆（session_id 区分用户）
- 学会根据对话长度选择合适的记忆策略

---

## 理论知识讲解

### 1. Memory 概念

#### 1.1 问题：LLM 是无状态的

LLM 的 API 调用是独立的：每次请求都是一个全新的上下文，模型不会保留任何之前调用的信息。

```python
# 第 1 次调用
model.invoke("我叫张三")           # 模型回复：你好，张三

# 第 2 次调用
model.invoke("我叫什么名字？")     # 模型回复：抱歉，我不知道你的名字
```

第 2 次调用时，模型完全不知道第 1 次对话的内容。

#### 1.2 解决：Memory 管理对话历史

Memory 组件的职责：

1. **保存**每次对话的用户消息和 AI 回复
2. **注入**：在下次调用时，把历史消息作为上下文传给模型
3. **管理**：控制历史长度，避免 Token 超限

```
用户：我叫张三        → Memory 保存
AI：你好，张三         → Memory 保存
用户：我叫什么？       → Memory 注入历史 → 模型看到完整上下文 → "张三"
```

#### 1.3 Memory 的本质

Memory 本质上是在调用模型前，把对话历史拼接进 Prompt：

```python
# 无 Memory
prompt = "回答：我叫什么？"

# 有 Memory
prompt = """
之前的对话：
用户：我叫张三
AI：你好，张三

现在回答：我叫什么？
"""
```

### 2. Memory 策略详解

LangChain 提供五种记忆策略，核心区别在于**如何控制历史消息的长度和 Token 消耗**。

#### 2.1 ConversationBufferMemory（全量保留）

保留所有对话历史，不做任何裁剪。

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
memory.save_context({"input": "你好"}, {"output": "你好，有什么可以帮你？"})
memory.save_context({"input": "我叫张三"}, {"output": "你好，张三"})

# 查看历史
print(memory.buffer)  # 完整对话历史
```

| 维度 | 说明 |
|------|------|
| 优点 | 信息完整，不丢失任何细节 |
| 缺点 | Token 消耗线性增长，长对话会超限 |
| 适用 | 短对话（10 轮以内） |

#### 2.2 ConversationBufferWindowMemory（滑动窗口）

只保留最近 K 轮对话，旧消息自动丢弃。

```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(k=3)  # 只保留最近 3 轮
```

| 维度 | 说明 |
|------|------|
| 优点 | Token 消耗可控，有固定上限 |
| 缺点 | 超出窗口的旧对话信息丢失 |
| 适用 | 中等长度对话，只关心近期上下文 |

`k` 参数控制窗口大小（轮数）。`k=3` 表示保留最近 3 组用户-AI 对话。

#### 2.3 ConversationSummaryMemory（自动摘要）

用 LLM 自动把旧对话压缩成摘要，保留要点而非原文。

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(llm=model)  # 需要传入 LLM 用于摘要
```

| 维度 | 说明 |
|------|------|
| 优点 | Token 增长缓慢，可处理很长对话 |
| 缺点 | 摘要可能丢失细节；每次摘要额外消耗 Token |
| 适用 | 长对话，需要保留整体脉络 |

工作原理：随着对话推进，LLM 不断把旧消息合并进一段摘要文本。

#### 2.4 ConversationSummaryBufferMemory（摘要 + 缓冲）

设定 Token 预算，超限时自动把旧消息摘要化，新消息保留原文。

```python
from langchain.memory import ConversationSummaryBufferMemory

memory = ConversationSummaryBufferMemory(
    llm=model,
    max_token_limit=200,  # Token 预算
)
```

| 维度 | 说明 |
|------|------|
| 优点 | 精确控制 Token 预算，平衡信息保留与成本 |
| 缺点 | 实现稍复杂 |
| 适用 | 精确控制成本的长对话场景 |

它结合了 Buffer（保留近期原文）和 Summary（压缩旧消息）两者的优点。

#### 2.5 ConversationTokenBufferMemory（按 Token 管理）

设定 `max_token_limit`，超限时丢弃最早的消息（先进先出）。

```python
from langchain.memory import ConversationTokenBufferMemory

memory = ConversationTokenBufferMemory(
    llm=model,
    max_token_limit=500,  # 最多保留 500 Token 的历史
)
```

| 维度 | 说明 |
|------|------|
| 优点 | Token 精确控制，不超限 |
| 缺点 | 旧消息直接丢弃（无摘要） |
| 适用 | 需要精确 Token 管理的场景 |

### 3. Memory 在 LCEL 中的使用（重点）

LangChain 0.3 推荐用 `RunnableWithMessageHistory` 为 LCEL 链接入记忆。

#### 3.1 基本用法

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# 1. 构建基础链（LCEL）
chain = prompt | model | parser

# 2. 定义 history_factory：返回 BaseChatMessageHistory 实例
def get_session_history(session_id: str) -> ChatMessageHistory:
    return ChatMessageHistory()

# 3. 用 RunnableWithMessageHistory 包装
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",       # 输入中代表用户问题的字段
    history_messages_key="history",      # Prompt 中历史消息的占位符
)

# 4. 调用时指定 session_id
config = {"configurable": {"session_id": "user_001"}}
chain_with_history.invoke({"question": "我叫张三"}, config=config)
chain_with_history.invoke({"question": "我叫什么？"}, config=config)  # 能回答"张三"
```

#### 3.2 关键参数说明

| 参数 | 作用 |
|------|------|
| `runnable` | 被包装的 LCEL 链 |
| `get_session_history` | 工厂函数，根据 session_id 返回历史存储 |
| `input_messages_key` | 输入 dict 中用户消息对应的字段名 |
| `history_messages_key` | ChatPromptTemplate 中 `MessagesPlaceholder` 的变量名 |

#### 3.3 Prompt 中预留历史位置

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是 ChainQA 助手。"),
    MessagesPlaceholder(variable_name="history"),  # 历史消息插入位置
    ("human", "{question}"),
])
```

### 4. BaseChatMessageHistory

`BaseChatMessageHistory` 是历史消息的存储抽象，有多种实现。

| 实现 | 存储位置 | 适用场景 |
|------|---------|---------|
| `ChatMessageHistory` | 内存 | 开发测试、单机短对话 |
| `RedisChatMessageHistory` | Redis | 生产环境、多实例共享 |
| `SQLChatMessageHistory` | SQL 数据库 | 需要持久化查询的场景 |
| `MongoDBChatMessageHistory` | MongoDB | 文档型存储场景 |

```python
# 内存存储
from langchain_community.chat_message_histories import ChatMessageHistory
history = ChatMessageHistory()

# Redis 持久化
from langchain_community.chat_message_histories import RedisChatMessageHistory
history = RedisChatMessageHistory(
    session_id="user_001",
    url="redis://localhost:6379",
)
```

### 5. 多会话记忆管理

#### 5.1 session_id 区分用户

每个用户/会话用唯一的 `session_id`，各自维护独立的历史。

```python
# 不同 session_id 对应不同历史存储
store = {}  # session_id -> ChatMessageHistory

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# 用户 A 和用户 B 互不干扰
chain.invoke({"question": "..."}, config={"configurable": {"session_id": "user_A"}})
chain.invoke({"question": "..."}, config={"configurable": {"session_id": "user_B"}})
```

#### 5.2 会话管理操作

- **创建**：首次使用某 session_id 时自动创建
- **切换**：调用时传入不同的 session_id
- **清除**：调用 `history.clear()` 清空某会话历史
- **过期**：可定时清理长时间未活跃的会话

### 6. 记忆持久化

#### 6.1 持久化方案

- **内存**：进程重启即丢失，仅适合测试
- **文件**：JSON 序列化保存，适合单机小规模
- **Redis**：高性能读写，适合生产
- **SQL/MongoDB**：结构化存储，可查询

#### 6.2 重启后恢复

使用 Redis/SQL 等持久化存储后，应用重启时只要 `session_id` 不变，即可恢复之前的对话历史。

#### 6.3 记忆清理策略

| 策略 | 说明 |
|------|------|
| 定时清理 | 每隔 N 天清除未活跃会话 |
| 容量限制 | 限制总会话数，超出时淘汰最旧 |
| 主动清除 | 用户提供"清空记忆"功能 |

### 7. Memory 策略选择决策表

| 对话场景 | 推荐策略 | 理由 |
|---------|---------|------|
| 短对话（≤10 轮） | BufferMemory | 信息完整，Token 可控 |
| 中等对话（10-30 轮） | BufferWindowMemory(k=5) | 只关心近期，固定上限 |
| 长对话（30+ 轮） | SummaryMemory | 摘要压缩，Token 增长慢 |
| 长对话 + 精确控制 | SummaryBufferMemory | 摘要+缓冲，预算可控 |
| 严格 Token 限制 | TokenBufferMemory | 精确 Token 管理 |

---

## 代码文件说明

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_buffer_memory.py` | 全量与窗口记忆对比 | ChainQA 多轮问答 |
| `02_summary_memory.py` | 摘要记忆策略 | 长对话自动摘要压缩 |
| `03_token_buffer.py` | Token 预算管理 | 精确控制 Token 成本 |
| `04_session_memory.py` | 多会话记忆 + 持久化 | 多用户会话管理 |

运行方式：

```bash
cd "Day06 - Memory对话记忆管理/Code"
python 01_buffer_memory.py
```

---

## 关键知识点总结

### Memory 策略对比表

| 策略 | 原理 | Token 消耗 | 信息保留 | 适用场景 |
|------|------|-----------|---------|---------|
| BufferMemory | 全量保留 | 线性增长 | 最好 | 短对话 |
| BufferWindowMemory | 保留最近 K 轮 | 固定上限 | 近期好/旧丢失 | 中等对话 |
| SummaryMemory | 摘要旧对话 | 增长缓慢 | 压缩摘要 | 长对话 |
| SummaryBufferMemory | 摘要+缓冲 | 预算可控 | 平衡 | 长对话 |
| TokenBufferMemory | 按 Token 管理 | Token 上限 | 平衡 | 精确控制 |

### RunnableWithMessageHistory 使用步骤

1. 构建 LCEL 链（Prompt 中用 `MessagesPlaceholder` 预留历史位置）
2. 定义 `get_session_history` 工厂函数
3. 用 `RunnableWithMessageHistory` 包装链
4. 调用时通过 `config` 传入 `session_id`

### ChatMessageHistory 持久化选项

| 存储 | 安装 | 特点 |
|------|------|------|
| 内存（ChatMessageHistory） | 内置 | 快但易失 |
| Redis | `redis` | 高性能、可共享 |
| SQL | `SQLAlchemy` | 可查询、可迁移 |
| MongoDB | `pymongo` | 文档型、灵活 |

### 策略选择决策表（速查）

```
对话轮数 ≤ 10     → BufferMemory
对话轮数 10-30    → BufferWindowMemory(k=5)
对话轮数 30+      → SummaryMemory 或 SummaryBufferMemory
需要精确 Token   → TokenBufferMemory
```

---

## 实战练习

### 练习 1：构建带记忆的 ChainQA 多轮问答

用 `RunnableWithMessageHistory` 包装一条 LCEL 链，实现：
- 用户可以说"我叫 XX"，后续问"我叫什么"能正确回答
- 用 `ConversationBufferMemory` 策略
- 测试连续 3 轮对话

### 练习 2：对比三种策略的 Token 消耗

准备一段 10 轮的对话，分别用 BufferMemory / BufferWindowMemory(k=3) / TokenBufferMemory(max_token_limit=200) 处理，对比：
- 最终历史消息的 Token 数
- 信息保留情况
- 给出策略选择建议

### 练习 3：实现多用户会话管理

实现一个 `SessionManager` 类：
- 支持创建、切换、清除会话
- 用字典存储多个 session_id 的历史
- 模拟两个用户交替对话，验证互不干扰

---

## 小结

Memory 让 ChainQA 从"金鱼记忆"变为能持续对话的助手。五种策略各有取舍：Buffer 保完整、Window 控上限、Summary 压缩长对话、Token 精确管理。在 LCEL 时代，`RunnableWithMessageHistory` 是接入记忆的标准方式，配合 `session_id` 可管理多用户会话。下一章我们将让 ChainQA 能"阅读"文档，为检索增强做准备。
