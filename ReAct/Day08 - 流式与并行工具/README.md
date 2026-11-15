# Day08 - 流式输出与并行工具

> 本章节提升 ReAct 的「体感」与「效率」。**SSE 流式**让 token 逐字吐给用户，体验更好、首字更快；**并行工具调用**让模型一次返回多个 `tool_calls`，同时执行再合并结果，缩短多步任务耗时。

---

## 目录

- [一、学习目标](#一学习目标）
- [二、理论知识](#二理论知识）
  - [2.1 为什么需要流式](#21-为什么需要流式）
  - [2.2 SSE / stream=True](#22-sse--streamtrue）
  - [2.3 手写一个流式生成器](#23-手写一个流式生成器）
  - [2.4 并行工具调用 tool_calls 数组](#24-并行工具调用-tool_calls-数组）
  - [2.5 并行执行与结果合并](#25-并行执行与结果合并）
  - [2.6 流式 + 工具的混合策略](#26-流式--工具的混合策略）
- [三、核心概念解析](#三核心概念解析）
  - [3.1 流式的收益与成本](#31-流式的收益与成本）
  - [3.2 并行执行线程/异步](#32-并行执行线程异步)
  - [3.3 何时不可并行](#33-何时不可并行）
- [四、关键知识点总结](#四关键知识点总结）
- [五、实战练习](#五实战练习）

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **用生成器逐 token 输出文本**。
2. **理解 `stream=True` 的增量返回**。
3. **消费一次返回的多个 `tool_calls` 并行执行**。
4. **合并多个工具结果再回填**。
5. **在真实/模拟两种后端间取舍流式方案**。

---

## 二、理论知识

### 2.1 为什么需要流式

- **首字时延**：不等整句生成完，先出第一字。
- **体验**：逐字打字更像真人聊天。
- **进度**：长回答尤其明显。

### 2.2 SSE / stream=True

OpenAI 兼容接口支持 `stream=True`，返回逐块（chunk）：

```python
resp = client.chat.completions.create(..., stream=True)
for chunk in resp:
    delta = chunk.choices[0].delta
    if delta.content:
        yield delta.content          # 逐 token
```

### 2.3 手写一个流式生成器

我们提供统一的 `stream_text` 生成器接口：

```python
def stream_text(llm, messages, tools=None, step=0.1):
    full = ""
    for piece in llm.stream(messages, tools):     # 各后端实现
        full += piece
        yield piece
    return full
```

Mock 后端可以按固定节奏吐字，模拟真实流式。

### 2.4 并行工具调用 tool_calls 数组

真实模型一次能返回**多个** tool_calls（OpenAI 等支持）：

```python
resp = llm.chat(messages, tools=...)
for tc in resp["tool_calls"]:        # 可能有多个
    ...
```

我们要能消费数组，而不是只处理第一个。

### 2.5 并行执行与结果合并

多个独立工具可同时跑（`ThreadPoolExecutor`），再把所有 Observation **逐个**回填：

```python
with ThreadPoolExecutor() as ex:
    futures = [ex.submit(reg.execute, tc["name"], **tc["arguments"]) for tc in tool_calls]
results = [f.result() for f in futures]
for tc, r in zip(tool_calls, results):
    history.append({"role": "tool", "content": str(r)})
```

合并后一次性让模型基于所有结果继续。

### 2.6 流式 + 工具的混合策略

实践中常：工具阶段**不流式**（快、结构化），进入最终回答阶段才流式输出给用户：

```
工具调用(快照模型回复, 非流式)
   ↓ 拿到最终要说的内容
流式生成最终回复(逐 token)
```

---

## 三、核心概念解析

### 3.1 流式的收益与成本

- 收益：体验好、首字快。
- 成本：多一次往返、需处理 SSE、与服务端流式配合。

### 3.2 并行执行（线程/异步）

独立工具用 `ThreadPoolExecutor` / `asyncio` 并行，总耗时 ≈ 最慢那个工具，而不是累加。

### 3.3 何时不可并行

- 工具之间有**依赖**（后一个要用前一个结果）。
- 有**副作用顺序要求**（如先扣款再发货）。
- 此时必须串行，模型也应在下一轮再调用。

---

## 四、关键知识点总结

- **stream=True → 逐 chunk 增量 content**。
- **统一 stream_text 生成器**封装流式。
- **并行工具 = 消费 tool_calls 数组 + 线程池执行**。
- **合并 Observation 逐个回填**。
- **有依赖的工具必须串行**。

---

## 五、实战练习

### 练习一：01-streaming.py —— 流式输出

**任务描述**：用生成器逐步 `yield` token 打印，模拟 SSE；认识流式节奏。

**运行方式**

```bash
python "Day08 - 流式与并行工具/Code/01-streaming.py"
```

### 练习二：02-parallel-calls.py —— 并行工具调用

**任务描述**：一次拿多个 tool_calls，用线程池并行执行两个独立计算工具，合并结果。

**运行方式**

```bash
python "Day08 - 流式与并行工具/Code/02-parallel-calls.py"
```

### 练习三：尝试

把 Day05 的 Agent 改为「工具完成后再流式输出最终回答」，体验优化延迟。

---

## 下节预告

下一节 **Day09** 进入 **多工具复杂 Agent**：搜索、计算、数据库、Web 等多工具编排，工具优先级与冲突处理。