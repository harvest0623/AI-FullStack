# Day08 Code - 并行执行与子图示例

> 本目录是 Day08 的可运行 Python 示例，建议按顺序运行了解三种组合方式。

## 依赖安装

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv
```

本目录示例均为**纯逻辑演示**，**无需 API Key** 即可直接运行。

## 文件清单

| 文件 | 运行方式 | 演示重点 |
|------|----------|----------|
| `01_parallel_nodes.py` | `python 01_parallel_nodes.py` | 固定数量并行（fan-out/fan-in）、`stream_mode` 观察每步 |
| `02_send_batch.py` | `python 02_send_batch.py` | `Send` 动态并行、map-reduce、reducer 累积结果 |
| `03_subgraph.py` | `python 03_subgraph.py` | 子图编译复用、顶层图字段映射 |

## 运行建议

- 先跑 `01` 理解"固定并行"，再跑 `02` 体会"动态并行（数据决定 worker 数）"。
- `03` 展示了"子图复用"，可当作把 `02` 的 worker 替换为完整子流程的过渡练习。
- 想要观察并行效果，可在各节点内加 `time.sleep` 再看耗时对比。