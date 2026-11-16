# Day05 - 多工具调用与并行

> 一次请求如何触发多个工具调用：遍历执行、并行调用、每个结果以各自 id 回填，以及存在相互依赖时的顺序处理。

---

## 1. 一个请求、多个 tool_calls

模型返回的 `tool_calls` 是一个**数组**，可能包含多个调用（每个带独立 `id`）：

```json
"tool_calls": [
  { "id": "c1", "function": { "name": "get_weather", "arguments": "{\"city\":\"北京\"}" } },
  { "id": "c2", "function": { "name": "get_time",   "arguments": "{\"city\":\"北京\"}" } }
]
```

应用需要**遍历执行**每个调用，并对**对应的 id 回填**结果。

---

## 2. 多工具执行与回填

```python
tool_messages = []
for tc in tool_calls:
    args = json.loads(tc["function"]["arguments"])
    result = TOOLS[tc["function"]["name"]]["fn"](**args)
    tool_messages.append({
        "role": "tool",
        "tool_call_id": tc["id"],        # ← 用 id 对应
        "content": str(result),
    })
# 把所有 tool 消息（连同原 assistant 消息）发给模型
```

关键：**必须携带 `tool_call_id` 回填**，模型才能把结果对应到那次调用。

---

## 3. 并行调用

- 相互独立的调用可以**并发执行**（`ThreadPoolExecutor` / asyncio），加快响应
- 模型端 `parallel_tool_calls`（部分 API 支持控制是否允许并行）
- 注意：并发执行的前提是**无依赖**

```python
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor() as pool:
    results = list(pool.map(run_one, tool_calls))
```

---

## 4. 有依赖的顺序处理

有的调用结果会被下一个调用使用。例如：

```
用户："分别查北京和上海的天气，然后告诉我哪个更暖和"
① get_weather(北京) → 22°C
② get_weather(上海) → 30°C
③ compare(a=22, b=30) → 上海更暖和   ← 依赖①②的结果
```

处理方式：**不要并行**，需按阶段执行。

```python
# 阶段1：并行查两城
r1, r2 = 执行(get_weather 北京), 执行(get_weather 上海)
# 阶段2：把 r1/r2 抽成参数再调用 compare
compare(a=解析温度(r1), b=解析温度(r2))
```

> 实践中，**复杂的多步依赖建议交给 Agent（Day08/Day09）**，用"决策→执行→再决策"的循环自然地把前一步结果带进下一步。

---

## 5. 本节小结

- `tool_calls` 是数组，遍历执行、按 `tool_call_id` 回填
- 无依赖 → 可并行（并发执行）；有依赖 → 分阶段顺序处理
- 结果须以各自 id 回填，模型才能正确引用

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_multi_tool.py` | 多工具遍历执行 + 回填 |
| `02_parallel.py` | 独立工具的并行执行 |
| `03_dependencies.py` | 有依赖的顺序处理演示 |
| `README.md` | 本目录说明 |

均**离线可运行**。