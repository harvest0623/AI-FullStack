# Day06 Code - Memory 对话记忆管理代码示例

本目录包含 Day06「Memory 对话记忆管理」的全部可运行 Python 代码，围绕 ChainQA 智能问答助手演示五种记忆策略与多会话管理。

## 文件说明

| 文件 | 内容 | 核心知识点 |
|------|------|-----------|
| `01_buffer_memory.py` | 全量与窗口记忆 | ConversationBufferMemory / ConversationBufferWindowMemory(k) / Token 消耗对比 / Memory + LCEL 多轮对话 |
| `02_summary_memory.py` | 摘要记忆策略 | ConversationSummaryMemory / ConversationSummaryBufferMemory / 摘要生成过程 / Token 增长对比 |
| `03_token_buffer.py` | Token 预算管理 | ConversationTokenBufferMemory / max_token_limit / 超限丢弃行为 / 与 Window 对比 |
| `04_session_memory.py` | 多会话 + 持久化 | RunnableWithMessageHistory / SessionManager 类 / session_id 管理 / Redis 持久化 |

## 运行方式

```bash
# 安装依赖
pip install langchain langchain-openai langchain-community python-dotenv pydantic

# 可选：Redis 持久化（04_session_memory.py 中演示）
pip install redis

# 配置 .env
# OPENAI_API_KEY=sk-xxxxxxxx
# OPENAI_MODEL=gpt-4o-mini
# REDIS_URL=redis://localhost:6379  # 可选

cd "Day06 - Memory对话记忆管理/Code"
python 01_buffer_memory.py
python 02_summary_memory.py
python 03_token_buffer.py
python 04_session_memory.py
```

## Memory 策略选择决策表

```
对话轮数 ≤ 10     → ConversationBufferMemory
对话轮数 10-30    → ConversationBufferWindowMemory(k=5)
对话轮数 30+      → ConversationSummaryMemory
长对话 + 精确控制 → ConversationSummaryBufferMemory
严格 Token 限制   → ConversationTokenBufferMemory
```

## RunnableWithMessageHistory 使用教程

### 标准用法

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# 1. 构建 LCEL 链（Prompt 用 MessagesPlaceholder 预留历史位置）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])
chain = prompt | model | parser

# 2. 定义 history_factory
def get_history(session_id: str) -> ChatMessageHistory:
    return ChatMessageHistory()

# 3. 包装
chain_with_history = RunnableWithMessageHistory(
    chain, get_history,
    input_messages_key="question",
    history_messages_key="history",
)

# 4. 调用时传 session_id
config = {"configurable": {"session_id": "user_001"}}
chain_with_history.invoke({"question": "你好"}, config=config)
```

### 关键参数

| 参数 | 作用 |
|------|------|
| `input_messages_key` | 输入 dict 中用户消息字段名 |
| `history_messages_key` | Prompt 中 MessagesPlaceholder 的变量名 |
| `get_session_history` | 工厂函数，返回历史存储 |

## 持久化配置指南

| 方案 | 安装 | 配置示例 |
|------|------|---------|
| 内存 | 内置 | `ChatMessageHistory()` |
| Redis | `redis` | `RedisChatMessageHistory(session_id=..., url="redis://...")` |
| SQL | `SQLAlchemy` | `SQLChatMessageHistory(session_id=..., connection=...)` |
| MongoDB | `pymongo` | `MongoDBChatMessageHistory(session_id=..., connection_string=...)` |

## 多会话管理最佳实践

1. **用 SessionManager 统一管理**：封装会话的增删查改
2. **session_id 设计**：用户ID + 时间戳 或 UUID
3. **会话过期清理**：定期清理长时间未活跃会话
4. **容量限制**：限制总会话数，超出淘汰最旧
5. **提供清除入口**：让用户能主动"清空记忆"

## Token 预算管理技巧

- `max_token_limit` 设为模型上下文窗口的 30-50%（留空间给系统 Prompt 和当前问题）
- 短对话：500-1000 Token 足够
- 中等对话：1000-2000 Token
- 长对话：考虑用 SummaryMemory 而非单纯加大预算
- 监控实际 Token 消耗，动态调整
