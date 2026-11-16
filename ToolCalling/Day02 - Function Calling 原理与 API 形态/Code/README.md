# Day02 - Code 代码目录说明

本目录提供 Day02（Function Calling 原理与 API 形态）的代码。所有脚本**离线可运行**。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_how_model_decides.py` | 讲解+演示 | 模型如何感知工具并决策 |
| `02_api_shapes.py` | 讲解+演示 | OpenAI / Anthropic 返回形态对比 |
| `03_tool_calls_struct.py` | 讲解+演示 | tool_calls 解析与 arguments 反序列化 |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_how_model_decides.py
python 02_api_shapes.py
python 03_tool_calls_struct.py
```

## 说明

- 本日聚焦 API 形态与解析；真正的执行闭环从 Day04 开始
- `03_tool_calls_struct.py` 的 `parse_arguments` 是后续所有调用都会复用的关键函数