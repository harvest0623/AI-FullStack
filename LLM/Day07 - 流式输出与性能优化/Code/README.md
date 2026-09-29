# Day07 Code - 流式输出与性能优化代码

本目录提供 4 个 Python 脚本，覆盖流式输出、异步并发、响应缓存、重试限流四大性能优化主题。所有脚本围绕 `AISearch` 项目的"性能优化"环节展开。

---

## 环境准备

```bash
pip install openai anthropic python-dotenv
```

`.env` 配置：

```
OPENAI_API_KEY=sk-xxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
```

---

## 文件清单

### `01_streaming_output.py` — 流式输出实现

**核心类**：`StreamingClient`

**能力**：
- OpenAI 同步流式（含打字机效果）
- OpenAI 异步流式（`AsyncOpenAI` + `async for`）
- Anthropic 流式（`messages.stream` + `text_stream`）
- 流式迭代器（生成器形式，供上层自定义消费）
- 流中断处理（`try/except` 捕获并提示）

**示例**：

```python
client = StreamingClient()
# 打字机效果
client.stream_openai_sync("讲个笑话", typewriter=True)
# 异步
asyncio.run(client.stream_openai_async("讲个笑话"))
# Claude
client.stream_anthropic("讲个笑话")
```

直接运行：`python 01_streaming_output.py`

---

### `02_async_batch.py` — 异步批量调用

**核心类**：`AsyncBatchProcessor`、`BatchReport`、`BatchResult`

**能力**：
- 串行执行（`run_serial`）
- 并发执行（`run_concurrent`，用 `asyncio.gather` + `Semaphore`）
- 自动统计总耗时、平均延迟、成功率
- 输出加速比对比

**示例**：

```python
processor = AsyncBatchProcessor(model="gpt-4o-mini")
prompts = [f"翻译：Hello {i}" for i in range(20)]
report_s = processor.run_serial(prompts)
report_c = asyncio.run(processor.run_concurrent(prompts, concurrency=5))
print(report_s.summary())
print(report_c.summary())
```

**典型结果**：20 条请求，串行约 30s，并发(5) 约 7s，加速 4x 左右。

直接运行：`python 02_async_batch.py`

---

### `03_response_cache.py` — 响应缓存

**核心类**：`ResponseCache`、`CacheEntry`、`CacheStats`

**能力**：
- 内存 LRU 缓存（`OrderedDict` 实现，超容量淘汰最久未用）
- 文件持久化缓存（JSON 落盘，跨进程复用）
- 内容哈希 key（prompt + model + 参数 → sha256）
- TTL 过期（`ttl_sec` 控制）
- 缓存命中率统计（hits / misses / hit_rate）
- `get_or_fetch()` 一站式：命中返回，未命中调 fetch_fn 并写入
- 手动清除（`clear()`）

**示例**：

```python
cache = ResponseCache(max_size=1000, ttl_sec=3600, cache_dir=".cache")
def my_llm_call(prompt, model):
    # ... 真实调用
    return output, prompt_tokens, completion_tokens
out = cache.get_or_fetch("解释 RAG", "gpt-4o-mini", my_llm_call)
print(cache.stats)  # hits=0 misses=1 sets=1 hit_rate=0.0%
```

直接运行：`python 03_response_cache.py`（含 mock 与真实两种演示）

---

### `04_retry_rate_limit.py` — 重试与限流

**核心类**：`TokenBucket`、`RateLimitHandler`；装饰器 `@retry` / `@async_retry`

**重试能力**：
- 指数退避：`base * 2^n`，加上限 `max_delay`
- 抖动 Jitter：`+ random.uniform(0, 1)`，避免雪崩
- 可重试判断：`is_retryable()` 按异常类名 + status_code 双重判断
- 不可重试错误（400/401/404）立即抛出
- 同步 `@retry` 与异步 `@async_retry` 两版

**限流能力**：
- Token Bucket 算法：`capacity`（容量）+ `refill_rate`（每秒补令牌）
- 支持阻塞等待（`timeout`）或立即返回
- 线程安全（`threading.Lock`）

**一体化封装**：

```python
handler = RateLimitHandler(rpm=60, max_attempts=3, timeout=30.0)
out = handler.call_llm("讲个笑话", model="gpt-4o-mini")
# 内部流程：限流(取令牌) → 调用 → 失败则重试(指数退避) → 超时抛出
```

直接运行：`python 04_retry_rate_limit.py`（重试与限流演示无需 API Key）

---

## 性能优化指南

### 流式输出实现步骤

1. **客户端**：同步用 `OpenAI`，异步用 `AsyncOpenAI`
2. **参数**：`stream=True`，OpenAI 加 `stream_options={"include_usage": True}` 取 Token 数
3. **迭代**：`for chunk in stream` 或 `async for chunk in stream`
4. **取内容**：`chunk.choices[0].delta.content`
5. **异常**：`try/except` 包住迭代，捕获中断
6. **前端**：逐字 `print(c, end="", flush=True)` 或 SSE 转发到浏览器

### 异步并发最佳实践

| 实践 | 说明 |
|------|------|
| 用 `AsyncOpenAI` | 同步客户端在 asyncio 里会阻塞事件循环 |
| `Semaphore` 限并发 | 默认不超过 API 的 RPM 限制的 80% |
| `gather` 保序 | 返回顺序与输入顺序一致 |
| 错误隔离 | 单个失败不阻断其他，用 `return_exceptions=True` 或 try/except |
| 批量大小 | 单批建议 10-50，过大易触发限流 |

### 缓存策略选择决策表

| 场景 | 推荐策略 | 理由 |
|------|---------|------|
| 单进程高频重复 | 内存 LRU | 速度最快，零网络 |
| 跨进程 / 跨重启 | 文件 / Redis | 持久化复用 |
| 同义不同表述 | 语义缓存 | Embedding 相似度匹配 |
| 实时性要求高 | 不缓存 / 短 TTL | 避免脏数据 |
| 温度 > 0 | 不缓存 | 输出不确定 |

### 重试配置建议

| 参数 | 建议值 | 说明 |
|------|--------|------|
| `max_attempts` | 3-5 | 过多会放大延迟 |
| `base_delay` | 1.0s | 起始等待 |
| `max_delay` | 30s | 上限，避免长尾 |
| `jitter` | True | 必开，防雪崩 |
| 可重试错误 | 429/5xx/408/网络 | 4xx 立即失败 |

### 限流参数设置指南

| API 档位 | RPM | 建议 capacity | 建议 refill_rate |
|---------|-----|--------------|------------------|
| Tier 1 | 60 | 60 | 1.0/s |
| Tier 2 | 500 | 400 | 8.0/s |
| Tier 3 | 5000 | 4000 | 80.0/s |

> 实际 capacity 设为 RPM 的 80%，留余量应对突发。

### 延迟优化清单

1. **小模型替代**：简单任务用 `gpt-4o-mini`，速度 2-5x
2. **限制 max_tokens**：避免冗长输出
3. **降低 temperature**：减少采样开销（小幅）
4. **预热连接池**：复用 client 实例，避免每次新建 TCP
5. **就近部署**：选最近 API 区域（如 `api.openai.com` vs 代理）
6. **缓存命中**：重复请求直接返回
7. **并发处理**：独立请求用 `asyncio.gather`
8. **Batch API**：非实时任务用 Batch，单价降 50%

### Batch API 使用示例

```python
from openai import OpenAI
client = OpenAI()

# 1. 准备 JSONL
import json
lines = [json.dumps({
    "custom_id": f"req-{i}",
    "method": "post",
    "url": "/v1/chat/completions",
    "body": {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": p}]}
}) for i, p in enumerate(prompts)]
Path("batch.jsonl").write_text("\n".join(lines), encoding="utf-8")

# 2. 上传 + 创建 batch
file = client.files.create(file=open("batch.jsonl", "rb"), purpose="batch")
batch = client.batches.create(
    input_file_id=file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
)

# 3. 轮询状态
import time
while batch.status not in ("completed", "failed", "expired"):
    time.sleep(60)
    batch = client.batches.retrieve(batch.id)

# 4. 下载结果
content = client.files.content(batch.output_file_id).text
```

---

## 常见问题

**Q1：异步流式报 `RuntimeError: asyncio.run() cannot be called from a running event loop`？**
A：在 Jupyter 等已有事件循环的环境里，用 `await client.stream_openai_async(...)` 而非 `asyncio.run()`。

**Q2：并发太多被 429？**
A：调小 `Semaphore`，或用 `RateLimitHandler` 的限流器；并开启 `@retry` 自动退避。

**Q3：缓存命中但内容过期？**
A：调短 `ttl_sec`，或在 Prompt 模板变更时调 `cache.clear()`。

**Q4：重试时延迟过长？**
A：减小 `max_attempts` 或 `max_delay`；对用户体验敏感的场景，失败比长时间等待更好。
