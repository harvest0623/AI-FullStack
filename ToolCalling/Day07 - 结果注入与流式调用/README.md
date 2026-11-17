# Day07 - 结果注入与流式调用

> 学会把工具返回结果正确地"塞回"上下文，处理超大结果，以及在流式输出场景下解析带增量拼装的工具调用。

---

## 1. 结果注入

工具结果要作为一条 **`role: "tool"`** 的消息回填，且必须带上**对应的 `tool_call_id`**：

```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "北京 晴 22°C"
}
```

- `content` 是给模型"读"的内容，通常为字符串（JSON 文本亦可）
- 会随整个对话历史一并发给模型
- 模型据此生成最终回答，或发起下一轮工具调用

---

## 2. 超大结果怎么处理

工具返回可能很大（整篇文档、整表数据）。可选策略：

- **截断**：按 token/字符数裁剪，保留开头/关键部分
- **摘要**：先在应用侧把结果压缩（如取前 N 行）
- **结构化引用**：只给"已存到文件 X"这类引用，需要时再读

> 原则：**上下文里只放模型"当下需要"的信息**，避免撑爆上下文或稀释注意力。

---

## 3. 流式输出时的工具调用

使用流式（streaming）时，模型输出是一段段增量到达。工具调用同样可能是**分片拼接**的：

```
第1段: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"c1","type":"function",
        "function":{"name":"get_we"}]}}}]}
第2段: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\"cit"}}}]}}]}
第3段: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"y\":\"北"}}}]}}]}
... 增量继续，直到 arguments 收尾
```

应用需按 **index** 分类，把每一段的 name / arguments **逐步拼接**，等流结束后得到完整 tool_call 再执行。

---

## 4. 流式多段拼接（要点）

```python
tool_calls_accum = {}   # index -> {"id","name","arguments"} 
for chunk in stream:
    for delta_tc in chunk["choices"][0]["delta"].get("tool_calls", []):
        i = delta_tc["index"]
        acc = tool_calls_accum.setdefault(i, {"arguments": ""})
        if "id" in delta_tc: acc["id"] = delta_tc["id"]
        if "function" in delta_tc:
            if "name" in delta_tc["function"]: acc["name"] = delta_tc["function"]["name"]
            acc["arguments"] += delta_tc["function"].get("arguments", "")
# 流结束后，accum 里就是完整的 tool_calls
```

---

## 5. 本节小结

- 结果注入 = 一条 `role:tool` + `tool_call_id` + `content`
- 超大结果务必截断/摘要/结构化引用
- 流式工具调用：按 index 增量拼接 name 与 arguments，流结束后再执行

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_result_injection.py` | 结果注入的正确形态 |
| `02_stream_partial.py` | 流式 tool_calls 增量拼接演示 |
| `03_truncation.py` | 大结果截断/摘要策略 |
| `README.md` | 本目录说明 |

均**离线可运行**。