# Day06 - Code 代码目录说明

本目录提供 Day06（工具调用循环与错误处理）的代码。所有脚本**离线可运行**。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_tool_loop.py` | 讲解+演示 | 工具调用循环（Agent 雏形）+ 最大迭代保护 |
| `02_error_handling.py` | 讲解+演示 | 各类错误的捕获与回填 |
| `03_max_iterations.py` | 讲解+演示 | 防死循环强制终止 |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_tool_loop.py
python 02_error_handling.py
python 03_max_iterations.py
```

## 说明

- `01_tool_loop.py` 是理解 Agent 的关键：决策→执行→回填循环，直到模型作答
- 三个脚本都体现了"错误/边界要收敛为可控结果"，这是工程化工具调用的要点