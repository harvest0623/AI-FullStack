# Day05 - Checkpointer 与持久化

> 让 LangGraph 图"记住自己走到哪了"——在任何一处**暂停**、**恢复**、**回溯**的关键能力。

## 本章简介

在前面四天里，我们构建的图都是一次性的：`invoke()` 一执行到底，状态函数栈里用完即弃，进程一退出就什么都不剩。这在真实业务里远远不够——LLM 应用动辄几十秒、涉及多次模型调用与用户交互，我们常常需要：

- 进程崩溃后从**中断处**继续跑；
- 随时**查询 / 修改**图的中间状态；
- 在关键环节**暂停**等待人工审阅再恢复；
- 区分不同用户的多套并行会话。

这一切都依赖一个核心组件——**Checkpointer（检查点）**。本章将系统讲解 Checkpointer 的概念、内置实现（`MemorySaver` / `SqliteSaver` / `PostgresSaver` / `RedisSaver`）、`thread_id` 会话隔离、状态管理 API，以及基于历史快照的**时间旅行**。它是下一章 Human-in-the-loop（人工干预）的技术底座。

---

## 学习目标

完成本章后，你应能：

- 说清 Checkpointer 是什么、解决什么问题、没有它会怎样
- 记清 `compile(checkpointer=...)` 的正确写法
- 理解 `thread_id` 的会话隔离机制，能用它实现多用户/多会话独立状态
- 熟练使用 `get_state()` / `get_state_history()` / `update_state()`
- 在四类内置 Checkpointer 之间做出正确选型
- 掌握时间旅行：回溯历史步 → 修正 → 重放

---

## 理论知识

### 一、Checkpointer 概念

#### 定义

**Checkpointer** 是一个负责**保存图执行中间状态**的组件，它按**线程（thread）**粒度对状态做细粒度快照。每一次节点执行后，都会把最新的状态写入检查点，从而让图的状态具备**可查询、可恢复**能力。

```python
from langgraph.checkpoint.memory import MemorySaver

graph = builder.compile(checkpointer=MemorySaver())
```

#### 作用

| 能力 | 说明 | 典型场景 |
|------|------|---------|
| 断点恢复 | 崩溃/中断后从最后检查点继续 | 进程重启后续跑 |
| 时间旅行 | 回溯到历史某步查看/修正 | 调试、重放 |
| 人工干预 | 暂停→人工审阅→恢复 | 内容审核、交易确认 |
| 跨请求持久化 | 状态存到外部存储，跨请求/跨进程存活 | 服务端多轮对话 |

#### 没有 Checkpointer 会怎样

- 图是**一次性**执行，`invoke` 结束后状态即丢失；
- 无法在任意位置**暂停**——因为它压根不记得该存哪个断点；
- 无法区分多用户会话（`thread_id` 无从谈起）；
- 无法查询历史，无法回溯。

一句话：**Checkpointer 是"可中断/可恢复工作流"的门票。**

### 二、为什么需要 Checkpointer

1. **进程崩溃后继续**：长任务跑到一半服务器重启，有了检查点就能从断点续跑，不重复前面的昂贵 LLM 调用。
2. **随时查询 / 修改状态**：外部系统可调用 `get_state` 读当前值、`update_state` 改写，实现"外部参与决策"。
3. **人工干预**：这是 Day06 的核心——`interrupt()` 暂停，状态留在检查点，人工批准后 `Command(resume=)` 恢复。**没有 Checkpointer，interrupt 无法工作**。
4. **多用户会话隔离**：按 `thread_id` 隔离，每个用户有自己独立的状态空间。

### 三、内置 Checkpointer

| Checkpointer | 存储位置 | 跨进程 | 适用场景 | 安装 |
|--------------|----------|--------|----------|------|
| `MemorySaver` | 进程内存 | 否 | 开发调试 / 单进程 | 随 langgraph 提供 |
| `SqliteSaver` | SQLite 文件 | 是（单机） | 本地 / 轻量 / 小型应用 | `langgraph-checkpoint-sqlite` |
| `PostgresSaver` | PostgreSQL | 是 | 生产多实例共享 | `langgraph-checkpoint-postgres` |
| `RedisSaver` | Redis | 是 | 高并发 / 分布式 | `redis` |

> 选型原则：开发用 `MemorySaver`；单机小应用用 `SqliteSaver`；多副本生产用 `PostgresSaver`/`RedisSaver`。

### 四、配置 Checkpointer

```python
graph = builder.compile(checkpointer=MemorySaver())
```

只需要在 `compile()` 时传入，之后 `invoke/stream` 就自动写入检查点。

### 五、thread_id 配置（重点）

`thread_id` 用于把状态**分桶**——同 `thread` 内的状态是连续的，不同 `thread` 互不可见。

```python
config = {"configurable": {"thread_id": "user-1"}}
graph.invoke({"content": "..."}, config=config)
```

要点：

- **不同 `thread_id` 隔离不同会话**（A 用户看不到 B 用户状态）；
- **同一 `thread_id` 多次 `invoke` 共享状态** → 天然实现"多轮对话 / 累积记录"；
- **配置了 Checkpointer 却不传 `thread_id`** → 通常报错（无法定位会话），或退化为无持久化。

### 六、状态管理 API（重点）

```python
state  = graph.get_state(config)             # 当前状态（含 next 步骤）
history = graph.get_state_history(config)     # 所有历史快照（每步一个）
graph.update_state(config, {"score": 90})     # 手动改写状态（用于人工介入）
```

### 七、图执行恢复

再次对**同一 `thread_id`** 调用 `invoke`，图会从**最后一个检查点继续**而非重新开始：

```python
graph.invoke({"content": "续跑"}, config=config)   # 上一次可能已中断
```

这是崩溃恢复的实现基础。

### 八、时间旅行（重点）

时间旅行让你**回到过去任意一步**查看状态、改动后重放，是调试与人工修正的利器：

1. `graph.get_state_history(config)` 获取每个历史步的快照；
2. 用某一步快照的 `config` 作为新执行基线，即"回滚到该步"；
3. 必要时用 `update_state(config, values)` 修正该步状态；
4. 重新 `invoke`，从修正后的点**重放**后续流程。

**没有 http 依赖**——读者可以在**当前进程内**用 `MemorySaver` 直接体验回溯与重放。

---

## 代码文件说明

| 文件 | 说明 |
|------|------|
| `Code/01_memory_saver.py` | 内存 Checkpointer：配置 / `thread_id` 会话隔离 / 同 thread 累积 / 异 thread 隔离 / 无 thread 报错处理。封装 `SessionChat` 类演示多用户持久化审核记录 |
| `Code/02_sqlite_saver.py` | SQLite 持久化：`SqliteSaver` 配置 / 持久化文件 / 重启后状态仍在 / `get_state` 查询 / `from_connstring` 用法。封装 `SqlitePersistence` 类，展示"崩溃后恢复会话" |
| `Code/03_time_travel.py` | 时间旅行：`get_state_history` 历史快照 / 回滚 / `update_state` 修正 / 追溯误判。封装 `TimeTravelDemo` 类 |

> 三者都基于同一 `GraphFlow` 审核工作流，随 Day 演进复用同一套状态与节点。

---

## 关键知识点总结

### Checkpointer 对比表

| Checkpointer | 持久化 | 跨进程 | 适用场景 |
|--------------|--------|--------|----------|
| MemorySaver | 内存 | 否 | 开发 / 单进程调试 |
| SqliteSaver | SQLite 文件 | 是(单机) | 本地 / 轻量 |
| PostgresSaver | PostgreSQL | 是 | 生产多实例 |
| RedisSaver | Redis | 是 | 高并发 / 分布式 |

### thread_id 会话隔离说明

- 一个 `thread_id` = 一条连续的会话时间线；
- 同 `thread` `invoke` 多次 → 状态累积（多轮对话）；
- 不同 `thread` 互相隔离 → 多用户并存；
- 配了 Checkpointer 却不给 `thread_id` → 出错或无持久化。

### 状态管理 API 速查

| API | 作用 |
|-----|------|
| `graph.get_state(config)` | 查询当前状态（含下一步 `next`） |
| `graph.get_state_history(config)` | 历史快照列表（每步一条） |
| `graph.update_state(config, values)` | 手动改写某状态 |
| `graph.invoke(input, config)` | 带上会话继续/新起执行 |

### 时间旅行四步

```
get_state_history → 取目标历史步 → update_state 修正 → 重新 invoke 重放
```

---

## 实战练习

### 练习 1：多用户审核隔离

用 `MemorySaver` 构建一个审核图，为 A、B 两个用户分配不同 `thread_id`。各自提交内容，确认：
- A 的 `risks` 不会混入 B 的结果；
- A 连续提交两条，第二条能看到第一条累积的 `risks`（同 thread 累积）。

### 练习 2：SQLite 崩溃恢复

用 `SqliteSaver` 把状态写入 `graphflow.db`，运行一次脚本后不删库、再次运行，用 `get_state` 验证上次会话内容仍在，并能"从断点续跑"。

### 练习 3：时间旅行修误判

构造一个会"产生错误评分"的检查节点，用 `get_state_history` 找到这一步，`update_state` 改成分数后再 `invoke` 重放，观察最终 `approved` 是否被修正为你想要的值。