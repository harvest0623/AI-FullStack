# Day10 - Callbacks 与 Streaming 回调流式

> 掌控 Chain 执行全过程，让用户实时看到输出：用 Callbacks 提升可观测性，用 Streaming 提升用户体验

## 本章简介

当 LangChain 应用从"能跑"走向"好用"，两个能力变得至关重要：**可观测性**（知道 Chain 内部发生了什么）和**实时性**（让用户立即看到输出而非长时间等待）。**Callbacks（回调）** 让你在 Chain 执行的各阶段（开始 / Token 生成 / 结束 / 错误）插入自定义逻辑，实现日志记录、指标采集、监控告警；**Streaming（流式输出）** 让 LLM 的回答像打字机一样逐字呈现，大幅改善用户体验。

本天围绕 ChainQA 项目，从 `BaseCallbackHandler` 基类出发，实现自定义日志回调、指标采集回调，演示 `.stream()` / `.astream()` 流式输出，并介绍 LangChain 官方追踪平台 LangSmith 的集成方式。

---

## 学习目标

完成本章后，你应能够：

1. 理解 Callbacks 的设计模式（观察者模式）和作用
2. 继承 `BaseCallbackHandler` 实现自定义回调处理器
3. 重写 `on_llm_start` / `on_llm_new_token` / `on_llm_end` / `on_chain_*` / `on_tool_*` 等方法
4. 使用 `StdOutCallbackHandler` 等内置回调
5. 掌握四种 Callback 配置方式（config / with_config / 全局 / 环境变量）
6. 使用 `.stream()` / `.astream()` 实现流式输出
7. 拼接 `AIMessageChunk` 处理流式 Token
8. 实现 `MetricsCallbackHandler` 采集延迟、Token 数、成本
9. 配置 LangSmith 追踪并理解其可视化能力
10. 理解异步 `AsyncCallbackHandler` 的使用场景

---

## 理论知识讲解

### 1. Callbacks 概念

**定义**：Callbacks 是在 Chain 执行的各阶段（开始 / Token 生成 / 结束 / 错误）插入自定义逻辑的机制。

**作用**：

- 日志记录：记录每个阶段的输入输出
- 指标采集：采集延迟、Token 数、成本
- 监控告警：异常时发送通知
- 调试追踪：打印中间状态，定位问题

**设计模式**：观察者模式（Observer Pattern）。Chain 是被观察者，Callback Handler 是观察者，Chain 执行到特定阶段时通知所有注册的 Handler。

### 2. BaseCallbackHandler 基类

所有 Callback Handler 的基类。继承并重写需要的方法：

```python
from langchain_core.callbacks import BaseCallbackHandler

class MyHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        pass
    # ... 重写其他方法
```

#### Callback 方法速查表

| 方法 | 触发时机 | 关键参数 |
|------|---------|---------|
| `on_llm_start(serialized, prompts, **kwargs)` | LLM 调用开始 | `serialized`（模型信息）、`prompts` |
| `on_chat_model_start(serialized, messages, **kwargs)` | ChatModel 调用开始 | `messages`（消息列表） |
| `on_llm_new_token(token, **kwargs)` | LLM 生成新 Token | `token`（生成的文本片段） |
| `on_llm_end(response, **kwargs)` | LLM 调用结束 | `response`（LLMResult） |
| `on_chain_start(serialized, inputs, **kwargs)` | Chain 开始 | `inputs`（输入数据） |
| `on_chain_end(outputs, **kwargs)` | Chain 结束 | `outputs`（输出数据） |
| `on_tool_start(serialized, input_str, **kwargs)` | 工具开始 | `input_str`（工具输入） |
| `on_tool_end(output, **kwargs)` | 工具结束 | `output`（工具输出） |
| `on_text(text, **kwargs)` | 文本输出 | `text` |
| `on_error(error, **kwargs)` | 错误发生 | `error`（异常对象） |

> `**kwargs` 中常含 `run_id`（本次运行的唯一 ID）、`parent_run_id`（父运行 ID），用于关联父子任务。

### 3. 内置 Callback

| 内置 Callback | 作用 | 使用场景 |
|--------------|------|---------|
| `StdOutCallbackHandler` | 控制台打印执行过程 | 调试（最常用） |
| `FileCallbackHandler` | 写入文件 | 持久化日志 |

```python
from langchain_core.callbacks import StdOutCallbackHandler

handler = StdOutCallbackHandler()
chain.invoke(input, config={"callbacks": [handler]})
```

### 4. 自定义 Callback Handler（重点）

自定义 Handler 是生产环境的核心能力。常见用途：

- **日志记录**：记录每个阶段的输入输出、时间戳
- **指标采集**：记录延迟、Token 数、成本估算
- **通知**：执行完成后发送 webhook / 邮件
- **调试**：打印中间状态

```python
import time
from langchain_core.callbacks import BaseCallbackHandler

class LoggingCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.start_time = None

    def on_chain_start(self, serialized, inputs, **kwargs):
        self.start_time = time.time()
        print(f"[Chain 开始] 输入: {inputs}")

    def on_chain_end(self, outputs, **kwargs):
        elapsed = time.time() - self.start_time
        print(f"[Chain 结束] 耗时: {elapsed:.2f}s 输出: {outputs}")
```

### 5. Streaming 流式输出

流式输出让 LLM 回答逐 Token 呈现，用户体验显著提升（无需等待完整回复）。

| 方法 | 说明 | 同步/异步 |
|------|------|----------|
| `.stream(input)` | 同步流式输出 | 同步 |
| `.astream(input)` | 异步流式输出 | 异步 |

#### Chunk 类型与拼接

流式输出返回的是 `AIMessageChunk`（消息片段），需要拼接：

```python
full = None
for chunk in model.stream("解释什么是 LCEL"):
    # chunk 是 AIMessageChunk
    print(chunk.content, end="", flush=True)
    full = chunk if full is None else full + chunk  # 拼接

# full 是完整的 AIMessage
print(f"\n完整消息: {full.content}")
```

#### 流式与 Callback 配合

启用流式后，`on_llm_new_token` 会在每个 Token 生成时触发：

```python
class StreamingHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token, **kwargs):
        print(token, end="", flush=True)  # 打字机效果
```

### 6. Callback 在 Chain 中的配置（四种方式）

#### 方式一：`config={"callbacks": [...]}`（最常用）

```python
chain.invoke(input, config={"callbacks": [handler1, handler2]})
```

#### 方式二：`.with_config(callbacks=[...])`

```python
chain_with_cb = chain.with_config(callbacks=[handler])
chain_with_cb.invoke(input)  # 自动带上回调
```

#### 方式三：全局默认 Callback

```python
import langchain
langchain.globals.set_debug(True)  # 开启 debug 模式（打印详细执行过程）
# 或设置全局 handler
```

#### 方式四：环境变量

```bash
# .env
LANGCHAIN_CALLBACKS=true
LANGCHAIN_DEBUG=true
```

#### 配置方式对比

| 方式 | 粒度 | 持久性 | 适用场景 |
|------|------|--------|---------|
| `config` | 单次调用 | 临时 | 灵活控制 |
| `with_config` | 绑定到 Runnable | 持久 | 复用配置 |
| 全局 | 所有调用 | 进程级 | 调试 |
| 环境变量 | 所有调用 | 永久 | 部署 |

### 7. LangSmith 追踪集成

**LangSmith** 是 LangChain 官方的追踪、评估、监控平台。

#### 配置

```bash
# .env
LANGCHAIN_API_KEY=ls_xxxxxxxx       # LangSmith API Key
LANGCHAIN_TRACING_V2=true           # 开启 v2 追踪
LANGCHAIN_PROJECT=chainqa           # 项目名（可选）
```

#### 能力

- **自动追踪**：所有 Chain 执行自动上报，无需改代码
- **可视化**：在 LangSmith 界面查看执行链路（每一步的输入输出、耗时、Token）
- **评估**：在 LangSmith 中评估和比较 Chain 质量
- **监控**：长期监控应用的延迟、成本、错误率

### 8. 异步 Callback（AsyncCallbackHandler）

异步 Chain（`ainvoke` / `astream`）需配合异步 Callback：

```python
from langchain_core.callbacks import AsyncCallbackHandler

class AsyncHandler(AsyncCallbackHandler):
    async def on_llm_new_token(self, token, **kwargs):
        # 异步处理 Token（如写入异步队列）
        await async_process(token)
```

---

## 代码文件说明

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_callback_handler.py` | 自定义 LoggingCallbackHandler | ChainQA 执行过程日志记录 |
| `02_streaming_output.py` | 流式输出实现 + 打字机效果 | ChainQA 流式问答 |
| `03_logging_callback.py` | MetricsCallbackHandler 指标采集 | ChainQA 生产监控 |
| `04_langsmith_trace.py` | LangSmith 追踪集成 | ChainQA 追踪与评估 |

---

## 关键知识点总结

### Callback 方法速查表

见上文"Callback 方法速查表"小节。

### Callback 配置方式对比

见上文"配置方式对比"小节。

### Streaming 方法对比

| 方法 | 类型 | 返回 | 适用场景 |
|------|------|------|---------|
| `.stream()` | 同步 | `Iterator[AIMessageChunk]` | 简单脚本 |
| `.astream()` | 异步 | `AsyncIterator[AIMessageChunk]` | 异步应用 |
| `.invoke()` | 同步 | 完整 `AIMessage` | 不需流式 |

### LangSmith 集成配置速查

| 环境变量 | 作用 | 示例 |
|---------|------|------|
| `LANGCHAIN_API_KEY` | LangSmith API Key | `ls_xxx` |
| `LANGCHAIN_TRACING_V2` | 开启 v2 追踪 | `true` |
| `LANGCHAIN_PROJECT` | 项目名 | `chainqa` |
| `LANGCHAIN_ENDPOINT` | 服务地址（默认官方） | `https://api.smith.langchain.com` |

---

## 实战练习

### 练习一：实现一个通知 Callback

继承 `BaseCallbackHandler`，实现 `NotificationCallbackHandler`：在 Chain 执行完成（`on_chain_end`）时，模拟发送通知（打印"✅ 任务完成，耗时 X 秒"）。在发生错误（`on_error`）时，打印"❌ 任务失败：{错误信息}"。应用到 ChainQA 问答链上。

### 练习二：流式输出 + Token 计数

使用 `.stream()` 流式输出一段 LLM 回答，同时用 `on_llm_new_token` 回调统计生成的 Token 数量。最终打印：完整回答 + 总 Token 数 + 总耗时。

### 练习三：配置 LangSmith 追踪

在 `.env` 中配置 LangSmith（若无 Key，则在 LangSmith 官网注册免费账号获取）。运行 ChainQA 问答链，登录 LangSmith 界面查看执行 trace，截图记录 Chain 的执行链路、每步耗时和 Token 消耗。

---

## 与后续板块衔接

本天掌握的 Callbacks 和 Streaming 是生产部署的基础：

- **Day12 生产部署**：用 Callback 采集生产指标、用 LangSmith 监控线上应用
- **Agent 板块**：Agent 的多轮工具调用过程同样通过 Callback 追踪
- **RAG 板块**：检索链的执行过程可通过 Callback 可视化

---

**下一站**：[Day11 - LangServe 与 LangGraph 基础](../Day11%20-%20LangServe与LangGraph基础/README.md)
