# Day09 - 记忆管理（短时与长时）

> 真正的对话是连续的：用户上次说过的偏好、聊到一半的任务，都应该是下一次对话的“起点”。本章带你拆解 LangGraph 的两层记忆体系。

## 本章简介

一个成熟的 AI 工作流，不能像“金鱼”一样每次对话都从零开始。用户期望它记得当前会话里说过什么（**短时记忆**），也记得自己上星期的偏好和历史事实（**长时记忆**）。

LangGraph 把这两类记忆用两个核心组件清晰地分开：
- **短时记忆（Short-term Memory）**：限定在**单次会话（thread）** 内的上下文，通过 **Checkpointer + `thread_id`** 实现。同一个 `thread_id` 多次 `invoke`，状态会持续累积。
- **长时记忆（Long-term Memory）**：跨会话、跨线程的长期数据（用户画像、历史事实、业务知识），通过 **Store** 实现，用命名空间（namespace）按用户/应用分层持久化。

本章围绕 `GraphFlow` 内容审核与智能问答工作流，先用 Checkpointer 让多轮审核对话“记住前文”，再用 Store 让工作流“记住用户偏好”，最后组合两者生成个性化审核报告。

---

## 学习目标

学完本章，你应该能：

- [ ] 区分短时记忆与长时记忆，并说明各自适用的场景
- [ ] 用 `Checkpointer + thread_id` 实现会话内的多轮消息累积
- [ ] 从 `state` 读取历史消息并注入 Prompt，实现上下文理解
- [ ] 理解 `InMemoryStore` 的配置与 `BaseStore` 接口
- [ ] 用 `store.put / store.get / store.search / store.delete` 读写跨会话数据
- [ ] 理解 namespace 命名空间的层级设计与 key 的唯一性
- [ ] 在节点中通过 `config`（`RunnableConfig`）访问 Store
- [ ] 组合短时 + 长时记忆，实现基于用户画像的个性化输出

---

## 理论知识讲解

### 一、记忆概念

记忆是让工作流“记得住”的能力，LangGraph 将其划分成两个粒度：

| 记忆类型 | 作用周期 | 典型内容 | 实现组件 |
|---------|---------|---------|---------|
| **短时记忆** | 会话内 | 当前对话的历史消息、上一步的分析中间结果 | Checkpointer + `thread_id` |
| **长时记忆** | 跨会话 | 用户画像、偏好、历史事实、业务知识 | Store |

**为什么需要记忆？**
1. **多轮对话理解**：第二轮说“刚才那篇也查一下”，必须知道“刚才那篇”是什么。
2. **个性化**：不同用户喜欢不同的语气、语言、详细程度。
3. **长期连续性**：上次没聊完的任务，今天接着做。

---

### 二、短时记忆（重点）

短时记忆的本质是：**同一个 `thread_id` 下，状态跨多次 `invoke` 持续累积**。

#### 1. 通过 Checkpointer + thread_id 实现

图的执行状态由 Checkpointer 保存。指定相同的 `thread_id`，就相当于“回到上次的话题继续聊”。

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# 两次调用，共用同一个 thread，状态累积
config = {"configurable": {"thread_id": "session-001"}}
graph.invoke({"messages": []}, config=config)
graph.invoke({"messages": []}, config=config)   # 能看到上次的消息
```

> 不同 `thread_id` 彼此隔离，互不干扰 —— 这就是**会话线程（thread）**：一次会话的短时记忆边界。

#### 2. 消息列表用 add_messages 累积

要让消息“追加”而不是“覆盖”，状态里的消息字段必须配置 `add_messages` reducer：

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]   # 追加消息，而不是覆盖
```

#### 3. 从 state 读取历史消息注入 prompt

节点里把累积的消息拼进系统提示，模型就能“看到”上下文：

```python
def chat_node(state: State) -> dict:
    history = "\n".join(m.content for m in state["messages"])
    # 用 history 构造 prompt 调用 LLM ...
    return {"messages": [ai_message]}
```

> 这是所有“多轮问答 / 审核对话”的语言模型应用的底层机制。

---

### 三、长时记忆 Store（重点）

Store 是跨会话的**持久化键值存储**，解决“换了一个 thread、甚至过了几天，还想记得用户”的问题。

#### 1. Store 概念

- **跨线程 / 跨会话**：Store 独立于任何一次执行，属于“全局共享”。
- **用途**：用户画像、历史偏好、需要长期引用的业务事实。

#### 2. 接口

```python
from langgraph.store.memory import InMemoryStore
from langchain_core.runnables import RunnableConfig

store = InMemoryStore()   # 内存实现（开发用）；生产可用 PostgresStore 等

# 写入 / 读取 / 搜索 / 删除
store.put(("users", "u-123"), "profile", {"bio": "..."})
data = store.get(("users", "u-123"), "profile").value
items = store.search(("users", "u-123"))
store.delete(("users", "u-123"), "profile")
```

通过在 `compile(store=store)` 注入的 Store，会被 LangGraph 自动绑定到接受 `store` 参数的节点。

#### 3. namespace 命名空间

- **namespace（命名空间）**：一串字符串元组，用来给数据**按层级分区**，如 `("users", "u-123")`。
- **key**：命名空间内条目的唯一标识，如 `"profile"`、`"pref"`。
- **value**：任意 `dict`。

```python
store.put(("users", "u-123"), "profile", {"name": "Alice"})          # 用户资料
store.put(("users", "u-123"), "pref", {"lang": "zh", "style": "brief"})  # 用户偏好
store.put(("org", "app-a"), "config", {"max_retry": 3})              # 业务配置
```

> 命名空间的职责是**隔离**：按用户、按应用、按业务域分层，避免 Key 冲突。

#### 4. 图通过 config 访问 store

`RunnableConfig` 里携带了注入的 store，同时可在 `configurable` 中放业务上下文（如 `user_id`）：

```python
def node(state: State, *, store):
    cfg = from config?   # 节点拿不到 config ... 见下方签名
```

在 LangGraph 中，`store` 是**关键字参数被框架注入**的；而 `user_id` 这类业务字段要从传入的 config 里取。三种取用姿势：

```python
# 方式一：节点直接声明 store 参数（框架自动注入）
def node(state, *, store):
    profile = store.get(("users", "u-123"), "profile")

# 方式二：节点再声明 config 参数，从 configurable 取业务字段
def node(state, *, store, config: RunnableConfig):
    user_id = config["configurable"].get("user_id", "anonymous")
    pendings = [x for x in store.search(("tasks", user_id))]

# 方式三：把 config drilled 到子调用（如工具/回调）
```

> 记住规律：**`store` 由 LangGraph 注入，`thread_id/user_id` 等业务字段放在 `config["configurable"]` 中读取**。

---

### 四、在图中使用 Store

```python
def audit_node(state, *, store, config: RunnableConfig):
    # 1. 从 config 取当前用户身份
    user_id = config["configurable"].get("user_id", "anonymous")
    # 2. 用当前用户 namespace 读取历史资料
    profile = store.get(("users", user_id), "profile")
    # 3. 写入/更新跨会话共享的信息
    store.put(("users", user_id), "pref", {"lang": "zh"})
    # 4. 返回业务结果
    return {"summary": ...}
```

要点：
- 节点**签名接收 `store` 参数**，由 LangGraph 自动注入，无需手动传递。
- 读/写的是**跨会话共享的数据**。
- 用户身份 `user_id` 从 `config` 获取，保证数据按用户隔离。

---

### 五、记忆应用

| 应用 | 说明 | 用的记忆 |
|------|------|---------|
| **个性化** | 记住用户偏好 / 风格 / 历史 | 长时（Store） |
| **连续性** | 跨会话记住未完成任务 | 长时（Store）+ 短时（thread） |
| **RAG 类** | 存储文档切片，作为 Retriever 的数据源 | 长时（Store） |

以 `GraphFlow` 为例：记住某用户习惯用简洁中文、偏好高风险内容单独提示 —— 下次任何时候审核，输出都自动贴合这位用户。

---

### 六、记忆管理最佳实践

- **短时**：会话消息累积交给 `add_messages` + Checkpointer，无需手动处理。
- **长时**：关键事实抽象提取后写入 Store；例如每次审核后把“用户偏好”增量更新进 Store。
- **定期清理过期记忆**：设定 TTL / 上限；Store 里若存了业务数据，要按策略删除或归档（示例：`store.delete`）。

---

## 代码文件说明

| 文件 | 类 | 说明 |
|------|-----|------|
| `Code/01_short_term_memory.py` | `ShortTermMemory` | 短时记忆：Checkpointer + thread_id 实现会话内消息累积 / 从 state 读历史注入 prompt / 多轮审核对话理解上下文 |
| `Code/02_long_term_store.py` | `StoreDemo` | 长时记忆：InMemoryStore 配置 / store.put 写入 / store.get 读取 / namespace 分层 / 跨会话读取个人偏好 |
| `Code/03_personalized.py` | `PersonalizedGraph` | 组合短时 + 长时：会话内上下文 + 跨会话用户画像 / 从 config 取 user_id 读写 store / 生成个性化审核报告 |
| `Code/README.md` | - | 记忆管理指南：短时/长时选择决策表、Store 完整教程、namespace 设计、记忆清理策略、生产记忆架构 |

---

## 关键知识点总结

### 短时 vs 长时对比表

| 维度 | 短时记忆 | 长时记忆 |
|------|---------|---------|
| 周期 | 会话内（同一 thread） | 跨会话（所有 thread 共享） |
| 组件 | Checkpointer + `thread_id` | Store |
| 数据形态 | 会话消息、中间状态 | 用户画像、偏好、事实 |
| 读取方式 | `state["messages"]` | `store.get(("users", uid), key)` |
| 隔离粒度 | thread | namespace |
| 典型场景 | 多轮对话 | 个性化、连续性 |

### Store API 速查

| 方法 | 作用 |
|------|------|
| `store.get(namespace, key)` | 读取单条记录，返回 `Item`（`.value` 为数据）或 `None` |
| `store.put(namespace, key, value)` | 写入/更新单条记录 |
| `store.search(namespace)` | 列出该命名空间下的所有 key |
| `store.delete(namespace, key)` | 删除单条记录 |

### namespace 设计规范

- 第一层通常是域：`"users"` / `"org"` / `"tasks"` / `"docs"`。
- 第二层是按主体隔离：`"u-abc123"`（用户 id）。
- 后续层放细分维度，如 `"stats"`、`"pref"`。
- 规范形如 `("users", user_id)`，保证每个用户数据互为独立。

### 在节点中使用 store 的签名

```python
def node(state, *, store, config: RunnableConfig):
    user_id = config["configurable"].get("user_id", "anonymous")
    record = store.get(("users", user_id), "pref")
    ...
```

### 记忆应用场景

- 个性化：按用户偏好组织输出语言/风格。
- 连续性：记住未完成任务，下次续做。
- RAG：把切片长期存放，作为检索数据源。

---

## 实战练习

1. **实现“记住上次任务”**：扩展 `GraphFlow`，让用户在对话里说“上次那个高风险客户”，第二次会话（新 thread 但同 user_id）能从 Store 找到并关联上一篇审核记录。
2. **偏好动态更新**：每次审核后解析用户对输出风格的反馈，写入 `store.put(("users", uid), "pref", new_style)`，并让下一次输出自动适配。
3. **为分片建索引**：把文档切片写入 `store.put(("docs", doc_id), f"chunk-{i}", {...})`，用 `store.search` 实现一个极简检索节点（贴近 RAG 的雏形）。

---

## 参考阅读

- [LangGraph 官方文档 - 记忆](https://langchain-ai.github.io/langgraph/concepts/memory/)
- [LangGraph 官方文档 - 持久化与 Store](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [LangChain 官方文档 - RunnableConfig](https://python.langchain.com/docs/concepts/runnables/)