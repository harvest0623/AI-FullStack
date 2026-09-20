# Day03 Code - Node 节点与 Edge 边

本目录包含 Day03「Node 节点与 Edge 边」的配套脚本：多种节点定义、普通边与入口/出口、扇入扇出行为。

## 环境准备

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic
```

> `01_node_basics.py` 中情感分析调用 LLM，需要 `.env` 配 `OPENAI_API_KEY`；未配置时会安全降级继续演示。

## 文件说明

| 文件 | 用途 | 关键概念 |
| --- | --- | --- |
| `01_node_basics.py` | 多种节点定义 | 纯函数节点、调 LLM 节点、async 节点、返回部分字段 |
| `02_edge_types.py` | 边与入口出口 | add_edge、set_entry_point/set_finish_point、START/END |
| `03_fan_out_in.py` | 扇入扇出 | fan-out 并行、fan-in 汇集、stream 观测 |

## 运行方式

```bash
python 01_node_basics.py
python 02_edge_types.py
python 03_fan_out_in.py
```

## 核心代码速览

### 1. 普通边声明（两写法等价）

```python
g.set_entry_point("a")          # = g.add_edge(START, "a")
g.add_edge("a", "b")
g.set_finish_point("b")         # = g.add_edge("b", END)
```

### 2. 扇出并行 + 扇入汇集

```python
g.add_edge("classify", "safety")      # 源节点同出两条边 → 并行
g.add_edge("classify", "sentiment")
g.add_edge("safety", "report")        # 多上游汇入同节点 → 汇集
g.add_edge("sentiment", "report")
```

## 常见问题

- **fan-in 节点执行了几次？** 一次。LangGraph 等待所有上游就绪后仅执行一次。
- **async 节点如何运行？** 用 `await app.ainvoke(...)`；节点内部 `await`。
- **节点返回的字段没生效？** 确认字段在 State 中、且返回 dict 而非直接改动 state。

## 下一步

会用普通边与节点后，进入 Day04 学习条件边，让图具备**动态路由**能力。