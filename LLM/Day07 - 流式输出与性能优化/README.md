# Day07 - 流式输出与性能优化

流式输出是提升 LLM 应用用户体验的关键。当用户提出一个问题，是非流式"等 5 秒突然全部出现"，还是流式"逐字打字机般涌出"，体感差异巨大——前者让人怀疑系统卡死，后者让用户感觉"AI 在思考、在回答"。但流式只是入口，真正的工程化挑战在性能优化：怎么用 asyncio 并发把串行 30 秒压到 5 秒？怎么用缓存把重复请求成本砍掉 80%？怎么用指数退避把偶发 429 变成对用户透明的自动重试？怎么用限流把突发流量挡在 API 限速之上？本章覆盖流式实现、异步并发、响应缓存、重试限流、延迟优化、Batch API 六大主题，让 `AISearch` 项目更快、更稳、更省。

---

## 学习目标

完成本章后，你应能：

1. 解释 SSE 与 Chunk 传输原理，说出流式 vs 非流式的体验差异。
2. 用 OpenAI / Anthropic SDK 实现同步流式与异步流式调用。
3. 用 `asyncio.gather` + `Semaphore` 实现批量并发，量化串行 vs 并发的性能差异。
4. 实现内存 LRU 缓存与文件缓存，统计命中率。
5. 实现指数退避 + 抖动的重试装饰器，区分可重试 / 不可重试错误。
6. 实现 Token Bucket 限流器，理解 RPM / TPM 限制。
7. 列出至少 5 条延迟优化技巧，并说明各自适用场景。
8. 用 OpenAI Batch API 处理非实时大批量任务，享受 50% 折扣。

---

## 理论知识讲解

### 7.1 流式输出 Streaming 原理

#### 7.1.1 Server-Sent Events (SSE)

SSE 是基于 HTTP 长连接的服务器推送技术：客户端发一次请求，服务器不关闭连接，持续推送 `data: ...` 事件块。LLM API 用 SSE 把生成的 Token 逐块推给客户端。

#### 7.1.2 Chunk 传输

模型逐 Token（或小批量 Token）生成，每生成一块就通过 SSE 推送一个 chunk，客户端逐字渲染。每个 chunk 形如：

```text
data: {"choices":[{"delta":{"content":"你"}}]}

data: {"choices":[{"delta":{"content":"好"}}]}

data: [DONE]
```

#### 7.1.3 流式 vs 非流式对比

| 维度 | 非流式 | 流式 |
|------|--------|------|
| 返回时机 | 全部生成完才返回 | 逐 Token 返回 |
| 首字延迟 | = 总生成时间 | ≈ 模型启动时间（几百 ms） |
| 用户体验 | 等待→突然全部出现 | 打字机效果，渐进显示 |
| 实现复杂度 | 简单 | 略复杂（需处理迭代器） |
| 中断恢复 | 不涉及 | 需考虑流中断处理 |
| 适用场景 | 后台任务、批处理 | 对话、实时交互 |

### 7.2 OpenAI 流式实现

#### 7.2.1 关键参数与字段

- `stream=True`：开启流式。
- `response` 是迭代器，逐 chunk 返回。
- `chunk.choices[0].delta.content`：增量内容。
- `stream_options={"include_usage": True}`：让最后一个 chunk 带 Token 用量。

#### 7.2.2 同步流式

```python
stream = client.chat.completions.create(model="gpt-4o-mini", messages=[...], stream=True)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

#### 7.2.3 异步流式

```python
from openai import AsyncOpenAI
client = AsyncOpenAI()
async for chunk in await client.chat.completions.create(..., stream=True):
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

### 7.3 Anthropic 流式实现

```python
with client.messages.stream(model="claude-3-5-sonnet-20240620", max_tokens=1024, messages=[...]) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

事件类型：`message_start` / `content_block_delta` / `message_stop`，封装在 `text_stream` 迭代器里。

### 7.4 Python 异步流式处理

| 组件 | 作用 |
|------|------|
| `AsyncOpenAI` | 异步客户端 |
| `async for chunk in response` | 异步迭代 chunk |
| `asyncio.run(main())` | 启动事件循环 |
| `asyncio.gather(*tasks)` | 并发多个流式请求 |

### 7.5 流式输出的用户体验优化

| 技巧 | 实现 |
|------|------|
| 打字机效果 | 逐字 / 逐词 `print(c, end="", flush=True)` |
| Markdown 实时渲染 | 边接收边渲染（前端用 `marked.js` 等） |
| 加载状态 | 首字到达前显示"正在思考..." |
| 错误处理 | 流中断时提示"生成中断，请重试" |

### 7.6 并发调用优化

#### 7.6.1 asyncio.gather 批量并发

```python
async def call_one(prompt):
    return await client.chat.completions.create(...)

results = await asyncio.gather(*[call_one(p) for p in prompts])
```

#### 7.6.2 Semaphore 控制并发数

避免瞬间打满 API 限速，用信号量限制同时进行的请求数：

```python
sem = asyncio.Semaphore(5)  # 最多 5 个并发
async def call_one(prompt):
    async with sem:
        return await client.chat.completions.create(...)
```

#### 7.6.3 适用场景

批量翻译、批量分类、批量摘要——多个独立请求可并行。

### 7.7 响应缓存策略

| 策略 | 实现 | 命中条件 | 适用 |
|------|------|---------|------|
| 内存缓存 | LRU dict | 完全相同输入 | 单进程高频重复 |
| 持久化缓存 | Redis / 文件 | 完全相同输入 | 跨进程、跨重启 |
| 语义缓存 | Embedding + 相似度阈值 | 语义相似 | 同义不同表述 |

**缓存命中率** = 命中次数 / 总请求次数。监控命中率可评估缓存效果。

### 7.8 请求重试机制

#### 7.8.1 指数退避 Exponential Backoff

`wait = base * 2^n`（n 为重试次数）：1s → 2s → 4s → 8s。

#### 7.8.2 抖动 Jitter

加入随机偏移，避免多个客户端同时重试引发雪崩：

```python
import random
wait = base * (2 ** n) + random.uniform(0, 1)
```

#### 7.8.3 可重试 vs 不可重试

| 错误类型 | 是否重试 | 示例 |
|---------|---------|------|
| 429 Rate Limit | 是 | 限速，等会儿就好 |
| 500/502/503 | 是 | 服务器临时故障 |
| 408 Timeout | 是 | 网络超时 |
| 400 Invalid Request | 否 | 参数错误，重试无用 |
| 401 Unauthorized | 否 | Key 错误 |
| 404 Not Found | 否 | 模型名错误 |

### 7.9 速率限制处理

| 算法 | 原理 | 特点 |
|------|------|------|
| Token Bucket | 桶里放令牌，请求消耗令牌，定速补令牌 | 允许突发 |
| Leaky Bucket | 请求如水流入桶，定速漏出 | 平滑输出 |
| 固定窗口 | 每窗口计数 | 简单但有边界突发 |
| 滑动窗口 | 加权计数 | 平滑但复杂 |

**RPM**（Requests Per Minute）与 **TPM**（Tokens Per Minute）是 OpenAI 的两类限制，需同时满足。

### 7.10 延迟优化技巧

| 技巧 | 效果 | 实现难度 |
|------|------|---------|
| 用小模型 | 速度提升 2-5x | 低 |
| 限制 max_tokens | 减少输出长度 | 低 |
| 降低 temperature | 减少采样开销 | 低 |
| 预热连接池 | 降低首字延迟 | 中 |
| 就近部署 | 降低网络延迟 | 中 |
| 缓存命中 | 直接返回 | 中 |
| 并发处理 | 多请求并行 | 中 |
| Batch API | 单价降 50% | 中 |

### 7.11 批量处理 Batch API

OpenAI Batch API：把大量请求打包提交，24 小时内异步返回结果，**价格 50% 折扣**。

适用场景：非实时的大批量处理（如每日数据标注、日志分类、历史文档摘要）。

```text
1. 准备 JSONL 文件，每行一个请求
2. 上传文件 → 创建 batch → 等待完成 → 下载结果
3. 适合 >1000 条的非紧急任务
```

---

## 代码文件说明

| 文件 | 用途 | 核心类 |
|------|------|--------|
| `01_streaming_output.py` | 流式输出实现 | `StreamingClient` |
| `02_async_batch.py` | 异步批量调用 | `AsyncBatchProcessor` |
| `03_response_cache.py` | 响应缓存实现 | `ResponseCache` |
| `04_retry_rate_limit.py` | 重试与限流 | `RateLimitHandler` |

详细使用方式见 `Code/README.md`。

---

## 关键知识点总结

### 流式 vs 非流式对比表

| 维度 | 非流式 | 流式 |
|------|--------|------|
| 首字延迟 | 高（=总时间） | 低（几百 ms） |
| 用户体验 | 等待 | 打字机 |
| 实现 | 简单 | 迭代器 |
| 中断恢复 | 无 | 需要 |
| 适用 | 后台 | 交互 |

### 缓存策略对比表

| 策略 | 命中条件 | 成本 | 跨进程 | 适用 |
|------|---------|------|--------|------|
| 内存 LRU | 完全相同 | 低 | 否 | 单进程高频 |
| 文件 | 完全相同 | 中 | 是 | 持久化 |
| Redis | 完全相同 | 中 | 是 | 分布式 |
| 语义缓存 | 相似度>阈值 | 高 | 是 | 同义复用 |

### 重试策略速查

| 错误 | 重试 | 退避 |
|------|------|------|
| 429 | 是 | 指数+抖动 |
| 5xx | 是 | 指数+抖动 |
| 408 | 是 | 指数+抖动 |
| 4xx（除 429/408） | 否 | 立即失败 |
| 网络错误 | 是 | 指数+抖动 |

### 限流算法对比

| 算法 | 突发 | 平滑 | 复杂度 |
|------|------|------|--------|
| Token Bucket | 允许 | 中 | 低 |
| Leaky Bucket | 不允许 | 高 | 中 |
| 滑动窗口 | 部分 | 高 | 高 |

### 延迟优化技巧清单

1. 小模型替代大模型
2. 限制 max_tokens
3. 降低 temperature（减少采样）
4. 预热 HTTP 连接池
5. 就近选择 API 区域
6. 缓存命中
7. 并发处理独立请求
8. Batch API 降本 50%

### Batch API 使用指南

| 步骤 | 操作 |
|------|------|
| 1 | 准备 JSONL（每行一个 chat completion 请求） |
| 2 | 上传文件 `client.files.create()` |
| 3 | 创建 batch `client.batches.create()` |
| 4 | 轮询状态 `client.batches.retrieve()` |
| 5 | 下载结果 `client.files.content()` |
| 折扣 | 50% |
| 时限 | 24h 内完成 |

---

## 实战练习

### 练习 1：实现打字机效果

基于 `01_streaming_output.py`，扩展：每收到一个 chunk，用 `time.sleep(0.05)` 模拟打字机延迟，让输出逐字浮现。再加入"首字到达前显示'正在思考...'"的逻辑。

**提示**：用 `sys.stdout.write` + `flush=True`，首字到达后清除"正在思考"。

### 练习 2：批量翻译性能对比

准备 20 条英文短句，用 `02_async_batch.py` 分别以串行、并发（Semaphore=5）、并发（Semaphore=10）三种方式翻译。记录总耗时，输出对比表。

**提示**：用 `time.perf_counter()` 测量，注意 API 的 RPM 限制。

### 练习 3：缓存 + 重试的完整链路

用 `03_response_cache.py` + `04_retry_rate_limit.py` 组合：对一组 50 条请求（含 10 条重复），先用缓存命中，未命中再走带重试限流的 LLM 调用。统计缓存命中率与总成本节省。

**提示**：在 `RateLimitHandler` 外面包一层 `ResponseCache`，缓存未命中再调用。
