# Day11 Code 说明 —— 错误处理与重试实战

本章用 `GraphFlow` 演示容错三板斧：重试 / 降级 / 兜底。

## 文件导航

| 文件 | 类 | 演示内容 | 运行 |
|------|-----|---------|------|
| `01_retry_policy.py` | `RetryDemo` | RetryPolicy：指数退避+抖动、验证 max_attempts（前2次失败第3次成功） | `python 01_retry_policy.py` |
| `02_fallback.py` | `FallbackDemo` | 失败降级：主节点异常→条件边路由→规则兜底（默认模拟失败） | `python 02_fallback.py` |
| `03_timeout_degrade.py` | `ResilientGraph` | 超时+容错：asyncio 超时控制、超时降级、Callback 上报、兜底 | `python 03_timeout_degrade.py` |

> 三例默认不调用真实 LLM（`02` 用开关`SIMULATE_FAILURE`，`03` 用内置慢调用模拟），零 Key 可运行观察容错行为。

## 核心要点

### 1. RetryPolicy

```python
from langgraph.pregel.retry import RetryPolicy

builder.add_node("model", node, retry=RetryPolicy(
    max_attempts=3, initial_interval=1.0, backoff_factor=2.0, jitter=True))
```

- `max_attempts` 含首次尝试；等待按 `initial_interval * backoff_factor^(n-1)` 递增。
- `jitter=True` 加入随机波动防"惊群"，应对限流更稳。

### 2. fallback（降级）

```
主节点 safe_primary:
  try: llm_analysis
  except: 标记 used_fallback="yes"(不抛异常)
条件边 route_after_primary → used_fallback=="yes" ? "fallback" : "end"
```

- 用 try/except + 条件边实现，主失败不乱中断整图。

### 3. 超时 + Callback

```python
result = await asyncio.wait_for(slow_call(), timeout=TIMEOUT)  # 超时控制
class ErrorLogger(BaseCallbackHandler):
    def on_chain_error(self, error, **kwargs): ...   # 错误上报
```

- 超时捕获 → 走降级；其它异常 → 兜底返回；Callback 记录错误。

## 进阶思考

1. 给 `03` 的节点叠加 `retry=RetryPolicy(...)`，观察"超时→重试→降级"的完整链。
2. 把 `SIMULATED_LATENCY` 调小到 0.2s，正常走 `ok` 分支，对比两次输出的 `status`。
3. 接入 LangSmith：设置 `LANGCHAIN_TRACING_V2` + `LANGCHAIN_API_KEY`，在图执行后到 LangSmith 面板查看错误堆栈。