# Day11 - 错误处理与重试

> 图在玩具场景里下能跑通容易，在真实网络、真实 API 下依然稳定，才是"生产级"。

## 本章简介

当 `GraphFlow` 接入真实 LLM 与 API 后，任何一次网络抖动、限流、超时都可能让整张图异常中断。本章聚焦**让图在真实环境中健壮运行**：掌握异常在节点间的传播、用 `RetryPolicy` 自动重试、设计 fallback 节点做失败降级、用超时避免卡死，并借助回调与 LangSmith 做错误上报与追踪。最终把 `GraphFlow` 的分析节点从"裸奔"升级为"重试 → 降级 → 兜底"的多级容错结构。

---

## 学习目标

学完本章，你应该能：

- [ ] 识别图中错误的主要来源并分析其影响
- [ ] 理解异常在节点间传播与默认中断的机制
- [ ] 用 `RetryPolicy` 为节点配置指数退避 + 抖动的重试
- [ ] 用条件边 + 异常捕获设计 fallback 降级节点
- [ ] 控制节点超时，避免整图卡死
- [ ] 通过 Callback 捕获错误、记录日志，并接入 LangSmith 追踪
- [ ] 从决策表出发，为不同错误选择合适的容错策略

---

## 理论知识讲解

### 一、图中错误来源

| 错误类型 | 典型表现 | 示例 |
|---------|---------|------|
| LLM 调用失败 | 网络 / 认证错误 | 503、超时、限流(429) |
| 工具 / API 调用错误 | 依赖服务异常 | 数据库连接失败 |
| 节点内部逻辑异常 | 业务 bug | 除零、空指针 |
| 状态不一致 | 字段缺失 / 类型不符 | `KeyError` |

---

### 二、异常传播

- 节点抛出异常 → 沿图**向 `invoke` 调用处传播**。
- 默认行为：**立即中断执行**，不再继续后续节点。

```python
try:
    graph.invoke(inputs)
except Exception as e:
    print("图执行失败:", e)
```

> 由于默认会中断，因此**重试和降级必须在内建机制或外层捕获中处理**。

---

### 三、RetryPolicy 重试（重点）

LangGraph 为节点提供内建的重试策略：

```python
from langgraph.pregel.retry import RetryPolicy

builder.add_node(
    "model",
    node,
    retry=RetryPolicy(
        max_attempts=3,          # 最大尝试次数(含首次)
        initial_interval=1.0,    # 首次重试前等待(秒)
        backoff_factor=2.0,      # 指数退避因子
        jitter=True,             # 随机抖动,避免多个节点同步重试
    ),
)
```

要点：
- `max_attempts`：含首次调用，共允许几次（3 表示首次 + 2 次重试）。
- 指数退避：等待时间按 `initial_interval * backoff_factor^(n-1)` 增长。
- `jitter=True`：在等待基础上加入随机波动，防止"惊群式"同步重试。
- 可通过 `retry_on` 限定只重试特定异常类型（如网络/限流类），对不可重试错误直接失败。

```python
from langchain_core.exceptions import RetryError  # 仅示例,可用自定义异常

RetryPolicy(max_attempts=3, retry_on=(TimeoutError, ConnectionError), jitter=True)
```

---

### 四、fallback（失败降级）

重试耗尽仍失败时，应优雅地"降级"而不是崩掉：

- **思路**：主节点失败 → 走备用节点，用**条件边 + 异常捕获**实现。
- **降级策略**：大模型 → 小模型 / 本地模型 → 规则引擎。

伪代码模式：

```python
def analyze_node(state):
    if state.get("main_failed"):
        return {"result": rule_based_analysis(state)}   # 降级
    try:
        return {"result": llm_analysis(state)}
    except Exception as e:
        return {"result": rule_based_analysis(state), "main_failed": True}
```

配合条件边：根据某失败标记动态路由到 `fallback` 节点。

---

### 五、timeout 超时

- **节点超时**：单次节点执行设限，避免 LLM 长时间无响应拖垮整图。
- **超时降级**：超时视为一次可重试错误，或直接触发 fallback。

```python
import timeout for invoke?  →  由是否 pypeln/signature 决定
```

通常做法：在 `llm.invoke` 外层加 `timeout=...`（部分模型客户端支持），或在节点内部用 `asyncio.wait_for` 包裹，捕获 `asyncio.TimeoutError` 后走降级路径。

> 生产建议：LLM 调用设置合理超时（如 10-30s），并用"重试 → 降级 → 兜底"覆盖超时场景。

---

### 六、错误上报与记录

- **用 Callback 捕获**：`before_callback/after_callback/on_chain_error` 拦截异常。
- **记录错误日志**：包含 state 快照，便于事后排查。
- **LangSmith 追踪**：设置环境变量后，图执行自动上报原始错误与链路。

```python
from langchain_core.callbacks import BaseCallbackHandler

class ErrorLogger(BaseCallbackHandler):
    def on_chain_error(self, error, *, run_id, parent_run_id, **kwargs):
        print(f"[错误] run={run_id} 错误={error}")
```

---

### 七、优雅降级示例

```
LLM 调用失败
   → RetryPolicy 自动重试(退避+抖动)
   → 重试 3 次仍失败
      → 走降级节点(关键词规则回复 / 默认回答)
   → 全部失败
      → 返回错误状态(而非让请求 5xx)
```

---

### 八、最佳实践

| 实践 | 说明 |
|------|------|
| 区分可重试 vs 不可重试 | 网络/限流可重试；认证错误、业务逻辑错误直接失败 |
| 合理退避避免限流 | 指数退避 + 抖动，降低再次触发 429 的概率 |
| fallback 保证可用性 | 永远有一条"最低可用"路径，如规则引擎 |
| 记录并追踪错误 | Callback + LangSmith，让错误可观测、可复盘 |
| 兜底返回 | 最坏情况返回友好错误状态而不是异常崩溃 |

---

## 代码文件说明

| 文件 | 类 | 说明 |
|------|-----|------|
| `Code/01_retry_policy.py` | `RetryDemo` | RetryPolicy 重试：节点配置、模拟首次失败后重试成功、指数退避+抖动、验证 max_attempts |
| `Code/02_fallback.py` | `FallbackDemo` | 失败降级：主分析节点失败走降级节点、条件边+异常捕获、规则回复降级策略 |
| `Code/03_timeout_degrade.py` | `ResilientGraph` | 超时与容错：节点超时、超时降级、错误 Callback、完整"重试→降级→兜底"链 |
| `Code/README.md` | - | 错误处理指南：RetryPolicy 配置建议、fallback 模式、超时实践、错误上报监控、生产容错架构 |

---

## 关键知识点总结

### RetryPolicy 参数速查

| 参数 | 说明 |
|------|------|
| `max_attempts` | 最大尝试次数（含首次） |
| `initial_interval` | 首次重试等待秒数 |
| `backoff_factor` | 指数退避因子 |
| `jitter` | 是否加入随机抖动 |
| `retry_on` | 限定重试的异常类型 |

### fallback 设计模式

```
主节点 → (异常) → 标记失败 → 条件边 → 降级节点(规则/默认) 
```

### 超时配置

- LLM/API 调用设置超时。
- 超时触发降级（视为一次失败）。

### 错误上报

- Callback `on_chain_error` 拦截。
- 记录 state 快照 + 日志。
- LangSmith：`LANGCHAIN_TRACING_V2=true` + API Key 自动上报。

### 容错决策表

| 错误类型 | 可重试? | 处理 |
|---------|--------|------|
| 网络抖动 / 限流 | 是 | RetryPolicy 重试 |
| 超时 | 视情况 | 超时降级 |
| 认证 / 业务逻辑 | 否 | 直接失败 + 记录 |
| 重试耗尽 | - | fallback 降级 |

---

## 实战练习

1. **给打分节点加重试**：让 `GraphFlow` 的分析节点用 `RetryPolicy(max_attempts=4, backoff_factor=2, jitter=True)`，模拟前两次失败后成功。
2. **设计降级路径**：主 LLM 分析失败时，用关键词规则（命中"稳赚/诱导/链接"→高风险）给出兜底审核结论。
3. **超时 + 上报闭环**：给节点加超时，超时后降级，并用自定义 Callback 把错误和 state 快照写入日志文件。

---

## 参考阅读

- [LangGraph 官方文档 - RetryPolicy](https://langchain-ai.github.io/langgraph/how-tos/retries/)
- [LangGraph 官方文档 - Reliability](https://langchain-ai.github.io/langgraph/concepts/reliability/)
- [LangChain 官方文档 - Callbacks](https://python.langchain.com/docs/concepts/callbacks/)