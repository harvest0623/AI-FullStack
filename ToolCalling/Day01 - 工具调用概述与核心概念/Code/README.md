# Day01 - Code 代码目录说明

本目录提供 Day01（工具调用概述与核心概念）的全部代码。所有讲解脚本**离线可运行**，无需真实模型 key。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_what_is_tool_calling.py` | 讲解脚本 | 本质：模型只提议、应用才执行 |
| `02_lifecycle.py` | 讲解+演示 | 一次调用的生命周期四步 |
| `03_scenarios.py` | 讲解脚本 | 典型场景与能力边界 |
| `toolcall_check.py` | 工具脚本 | 探测可选模型 SDK（信息展示） |

## 运行方式

```bash
python 01_what_is_tool_calling.py
python 02_lifecycle.py
python 03_scenarios.py
python toolcall_check.py
```

## 说明

- 讲解脚本输出均为中文，控制台请用 UTF-8
- 本日纯概念；后续用"模拟模型"逐步实现真实闭环（Day04 起）