# Day05 - Code 代码目录说明

本目录提供 Day05（多工具调用与并行）的代码。所有脚本**离线可运行**。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_multi_tool.py` | 讲解+演示 | 多工具遍历执行 + 按 id 回填 |
| `02_parallel.py` | 讲解+演示 | 独立工具的并行执行（体现耗时差异） |
| `03_dependencies.py` | 讲解+演示 | 有依赖的顺序处理 |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_multi_tool.py
python 02_parallel.py
python 03_dependencies.py
```

## 说明

- `02_parallel.py` 用 `ThreadPoolExecutor` + `time.sleep` 演示并行与串行的耗时区别
- `03_dependencies.py` 说明为何有依赖时不能并行；复杂多步交给 Agent 循环更合适