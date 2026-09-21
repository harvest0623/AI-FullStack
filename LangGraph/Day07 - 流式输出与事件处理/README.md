# Day07 - 流式输出与事件处理

> 让长任务"实时可见"，让执行过程可被逐 token 订阅。交互体验与可观测性的分水岭。

## 本章简介

前几章的 `invoke()` 都是"整体返回"：图从头跑到尾，最后一次性给你结果。对用户体验来说，长任务里用户等待十几秒却毫无反馈是一种灾难；对开发者来说，图内部发生了什么（哪个节点、哪些 token、调了哪些工具）也无法细看。

LangGraph 为此提供两级能力：

- **`stream()` 流式输出**——按 `stream_mode` 逐步产出"状态快照 / 节点增量 / 调试事件"；
- **`astream_events()` 事件流**——以异步迭代器细粒度订阅 `on_chat_model_stream`、`on_tool_start`、`on_chain_start` 等事件，配合 `tags` 精确定位到某个节点。

本章聚焦框架本身的流式与事件机制，并给出可直接套用的**打字机效果**实现，以及前后端集成的思路。基于此构建完整交互式 Agent 界面，留待后续板块。

---

## 学习目标

完成本章后，你应能：

- 用 `graph.stream(input, config)` 迭代产出中间结果
- 分清 `values` / `updates` / `custom` / `debug` 四种 `stream_mode`
- 用 `astream_events()` 订阅模型 / 工具 / 链事件，并看懂事件结构
- 用 `tags` 精确过滤某个节点的流式输出
- 实现逐 token 的打字机效果
- 理解 LangGraph stream 与 LangChain 单链 stream 的差异

---

## 理论知识

### 一、流式输出基础

```python
for chunk in graph.stream(input, config, stream_mode="updates"):
    ...
```

`graph.stream()` 返回一个迭代器，`stream_mode` 决定每一步产出内容的形态。图执行过程中会**持续产生**对应格式的块，直到流程结束。

### 二、stream_mode 详解（重点）

| 模式 | 每步产出 | 典型用途 |
|------|----------|----------|
| `"values"` | 每个节点执行后的**完整状态** | 观察全量状态快照 |
| `"updates"` | 每个节点返回的**增量 dict** | 只关心节点写了哪些字段 |
| `"custom"` | 自定义事件（配合 `streaming` 回调 `get_state()`） | 精细化业务事件 |
| `"debug"` | 详尽的调试事件 | 排查图执行细节 |

```python
# values 形式
{"content": ..., "sentiment": "正面"}
# updates 形式（key 为节点名）
{"sentiment": {"sentiment": "正面"}}
```

### 三、astream_events() 事件流（重点)

```python
async for event in graph.astream_events({"content": ...}, version="v2"):
    kind = event["event"]
```

常见事件类型：

| 事件 | 含义 |
|------|------|
| `on_chain_start / on_chain_end` | 链/节点开始与结束 |
| `on_chat_model_start / on_chat_model_stream` | 模型启动 / 逐 token 流式 |
| `on_tool_start / on_tool_end` | 工具调用开始 / 结束 |

**事件结构**（可用来过滤与定位来源）：

```python
{
  "event": "on_chat_model_stream",
  "name": "ChatOpenAI",
  "run_id": "...",
  "tags": ["graphflow_analyze"],
  "metadata": {...},
  "data": {"chunk": AIMessageChunk(...)}
}
```

### 四、增量 / 打字机效果

- 用 `astream_events` 过滤 `on_chat_model_stream`；
- 从 `data["chunk"].content` 逐 token 取出文本；
- `print(..., end="", flush=True)` 逐字输出，配合 `sleep` 形成打字机动画。

### 五、LangGraph Stream vs LangChain Stream

| 维度 | LangChain `chain.stream` | LangGraph `graph.stream` / `astream_events` |
|------|--------------------------|---------------------------------------------|
| 范围 | 单条 LCEL 链的模型流 | 整张图执行流 + 全局事件 |
| 粒度 | 链级 result 片段 | 状态快照 / 节点增量 / 模型 token / 工具事件 |
| 状态 | 无持久化视角 | 天然结合 Checkpointer |
| 适用 | 简单管道 | 复杂图 / 多节点 / 需要事件定位 |

### 六、流式中的 Checkpointer

`stream` / `astream_events` 在配置了 Checkpointer 的图上同样生效：流式执行同样**可持久化、可中断、可恢复**，与 Day05/Day06 能力无缝衔接。

### 七、事件过滤最佳实践

```python
graph.add_node("analyze", analyze_node, tags=["graphflow_analyze"])

# 过滤：只看该节点的模型流
if event["event"] == "on_chat_model_stream" and "graphflow_analyze" in event["tags"]:
    ...
```

> 用 `tags` 标注节点，事件过滤即可精确到"哪一步在产出什么"。这是生产可观测性的基本功。

---

## 代码文件说明

| 文件 | 说明 |
|------|------|
| `Code/01_stream_modes.py` | `values` / `updates` / `debug` 三种模式对比，观察同一图中各阶段状态流转与输出结构 |
| `Code/02_astream_events.py` | 事件流订阅 `on_chat_model_stream` 等事件，展示事件结构、按 `tags` 过滤 |
| `Code/03_typing_effect.py` | 打字机效果：节点打 `tags` → 过滤 `on_chat_model_stream` → 逐 token 打印实现实时流式展示 |

---

## 关键知识点总结

### stream_mode 使用决策表

| 需求 | 用哪个 |
|------|--------|
| 看每步完整状态 | `values` |
| 看节点写了什么（增量） | `updates` |
| 自定义业务事件 | `custom` |
| 排查执行细节 | `debug` |

### astream_events 事件类型速查

| 事件 | 触发时机 |
|------|----------|
| `on_chat_model_stream` | 模型逐 token 流出 |
| `on_tool_start` | 工具即将执行 |
| `on_chain_start/end` | 节点开始/结束 |

### 打字机效果实现步骤

```
1. 节点 add_node(..., tags=["xxx"])
2. async for event in graph.astream_events(..., version="v2")
3. 过滤 event == on_chat_model_stream 且 tags 命中
4. 取 data["chunk"].content 逐字 print(flush=True)
```

### tag 过滤最佳实践

- 为每个可观测节点打**唯一 tag**；
- 用 `tags` 定位"谁在产出"，避免误收别的节点的 token。

---

## 实战练习

### 练习 1：多模式观察

对 `01_stream_modes.py` 的图分别用 `values` / `updates` 打印，对比每个节点写入的字段差异，体会"增量"与"全量"的区别。

### 练习 2：过滤到自己定义的事件

在 `02` 中新增一个调用工具的节点，订阅 `on_tool_start`，观察工具名与 `run_id` 如何被捕获。

### 练习 3：带进度的打字机

结合 Checkpointer 与 `interrupt`（Day05/06）：让审核结论先流式输出，输出途中可被 `interrupt` 暂停，人工确认后再继续流式到最终——验证"流式 + 可中断"组合。