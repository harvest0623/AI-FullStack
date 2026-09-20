# Day01 Code - LangGraph 概述与环境搭建

本目录包含 Day01「LangGraph 概述与环境搭建」的配套脚本：构建第一个图、做环境自检、查看图结构。全程围绕 **GraphFlow**（内容审核与智能问答工作流）演示。

## 环境准备

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic
```

> 除 `01_hello_graph.py`、`03_graph_visualization.py` 无需 API Key 外，建议在项目根目录放置 `README.md` 所描述的 `.env`（含 `OPENAI_API_KEY`），方便后续 Days 调用 LLM。

## 文件说明

| 文件 | 用途 | 关键概念 | 是否需要 Key |
| --- | --- | --- | --- |
| `01_hello_graph.py` | 第一个两节点图 | StateGraph、Node、add_edge、set_entry_point/set_finish_point、compile、invoke、stream_mode | 否 |
| `02_environment_setup.py` | 环境检查工具 | Python版本/依赖/Key 校验，生成 requirements.txt 与 .env 模板 | 否（若有 .env 会读取）|
| `03_graph_visualization.py` | 图结构可视化 | get_graph()、print_ascii、节点/边列表、Mermaid 导出 | 否 |

## 运行方式

```bash
python 01_hello_graph.py
python 02_environment_setup.py
python 03_graph_visualization.py
```

## 核心代码速览

### 1. 六步构建一个图

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    msg: str

def node_a(state): return {"msg": state["msg"] + " A"}
def node_b(state): return {"msg": state["msg"] + " B"}

g = StateGraph(State)
g.add_node("a", node_a)
g.add_node("b", node_b)
g.set_entry_point("a")            # = add_edge(START, "a")
g.add_edge("a", "b")
g.set_finish_point("b")           # = add_edge("b", END)
app = g.compile()
print(app.invoke({"msg": "start"}))   # {'msg': 'start A B'}
```

### 2. 观察状态流转

```python
for ev in app.stream({"msg": "start"}, stream_mode="updates"):
    print(ev)   # 每次打印一个节点的增量更新
```

### 3. 查看图结构

```python
app.get_graph().print_ascii()          # ASCII 节点/边图
app.get_graph().nodes                  # 节点集合
app.get_graph().edges                  # 边集合
app.get_graph().draw_mermaid()         # Mermaid 文本
```

## 常见问题

- **`langgraph` 未找到** → `pip install langgraph`
- **`invoke` 结果里字段缺失** → 确认节点返回的 dict key 与 State 字段名一致
- **`.env` Key 不生效** → 代码顶部补 `load_dotenv()`，且确认 `.env` 在运行目录或其上级

## 下一步

理解并跑通第一个图后，进入 Day02 深入学习 `State` 状态管理与 `TypedDict`。