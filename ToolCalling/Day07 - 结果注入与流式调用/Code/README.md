# Day07 - Code 代码目录说明

本目录提供 Day07（结果注入与流式调用）的代码。所有脚本**离线可运行**。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_result_injection.py` | 讲解+演示 | 结果注入形态（role=tool + tool_call_id） |
| `02_stream_partial.py` | 讲解+演示 | 流式 tool_calls 增量拼接 |
| `03_truncation.py` | 讲解+演示 | 大结果截断/摘要策略 |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_result_injection.py
python 02_stream_partial.py
python 03_truncation.py
```

## 说明

- `02_stream_partial.py` 用 OpenAI 的 delta 分片模拟流式，按 index 拼接成完整 tool_call
- 大结果处理是工程关键：用截断/摘要/落盘引用控制上下文占用