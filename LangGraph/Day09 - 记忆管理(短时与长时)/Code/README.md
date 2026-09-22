# Day09 Code 说明 —— 记忆管理实战

本章代码围绕 `GraphFlow` 内容审核工作流，演示 LangGraph 的两层记忆体系。

## 文件导航

| 文件 | 类 | 演示内容 | 运行方式 |
|------|-----|---------|---------|
| `01_short_term_memory.py` | `ShortTermMemory` | 短时记忆：Checkpointer + thread_id 累积会话消息、历史注入 prompt | `python 01_short_term_memory.py` |
| `02_long_term_store.py` | `StoreDemo` | 长时记忆：InMemoryStore、put/get/search、namespace 分层、跨会话偏好 | `python 02_long_term_store.py` |
| `03_personalized.py` | `PersonalizedGraph` | 组合短时+长时：config 取 user_id、读写 store、个性化报告 | `python 03_personalized.py` |

## 运行前准备

在 `LangGraph/Day09 .../Code/` 目录放置 `.env`：

```bash
OPENAI_API_KEY=sk-xxxxx
```

安装依赖：

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic
```

## 核心要点

### 1. 短时记忆的关键代码

```python
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]   # 追加而非覆盖

# 编译时注入 checkpointer
graph = builder.compile(checkpointer=MemorySaver())
# 相同 thread_id 多次 invoke，消息持续累积
graph.invoke({"messages": []}, config={"configurable": {"thread_id": "t-1"}})
```

### 2. 长时记忆 Store 的关键代码

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
# 编译时需要同时传 checkpointer 与 store
graph = builder.compile(checkpointer=..., store=store)

def node(state, *, store):          # LangGraph 自动注入 store
    it = store.get(("users", "u-1"), "pref")   # 读取
    store.put(("users", "u-1"), "pref", {...}) # 写入
```

## 运行示例输出示意

```
GraphFlow - 短时记忆（会话内上下文累积）
[用户] 请审核这句话是否违规：『今天天气真好』
[助手] 不违规……
[用户] 那如果加上『滚出去』这个口头禅呢？
[助手] 结合前文历史（了解「那」的指代）……
```

## 进阶思考

1. 把 `MemorySaver` 换成 `SqliteSaver` / `PostgresStore`，短时与长时都向磁盘/数据库持久化。
2. 思考：如何在上一次审核后，把用户对输出风格的评价写回 Store，实现偏好自学习？
3. 为 Store 加 TTL：结合 `store.search` + `store.delete` 做定期清理，避免数据无限膨胀。