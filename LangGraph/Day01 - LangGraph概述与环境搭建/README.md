# Day01 - LangGraph 概述与环境搭建

LangGraph 是 LangChain 生态中用于构建**有状态、可恢复、多步骤 LLM 应用**的状态图框架。它以「图」为抽象——节点执行操作、边定义流转、状态在节点间共享——天然支持循环、分支、人工干预和状态持久化。本章作为阶段一「图基础」的开篇，带你建立 LangGraph 的整体认知：它解决了什么问题、它和 LCEL 以及 Agent 的关系、核心概念有哪些，并动手搭建环境跑通第一个图。全程围绕统一的示例项目 **GraphFlow**（内容审核与智能问答工作流）展开。

## 学习目标

- 理解 LangGraph 的定义、要解决的问题及其在 LangChain 生态中的位置
- 掌握状态图模型的四大核心概念：`State` / `Node` / `Edge` / `Conditional Edge`
- 明晰 LangGraph 与 LCEL 的差异及各自的适用场景
- 理解 LangGraph 与 Agent（智能体）的关系
- 完成 Python 3.10+ 环境搭建与 API Key 配置
- 能编写、编译并执行第一个两节点图，并观察状态流转

---

## 一、LangGraph 是什么

**LangGraph 是一个以图（graph）为抽象的有状态 LLM 工作流编排框架。** 它把一次复杂的 LLM 处理流程建模成一张**有向图**：

- **节点（Node）** 负责执行具体操作（调用 LLM、处理逻辑、路由决策）
- **边（Edge）** 定义节点之间的流转关系
- **状态（State）** 是整个流程中节点共享的数据容器

与「线性管道」不同，图结构可以表达**循环、分支、回退、并行、人工干预**等任意复杂的控制流。这正是构建 Agent 的根本能力。

---

## 二、LangGraph 解决了什么问题

### 2.1 LCEL 的局限

LangChain 的 LCEL（LangChain Expression Language）用管道符串联组件，非常简洁：

```python
chain = prompt | model | output_parser
```

但它本质是**线性管道**，处理以下场景会非常别扭甚至无法表达：

| 能力 | LCEL 表现 |
| --- | --- |
| 循环（loop） | 不支持，无法「反复思考直到收敛」 |
| 条件分支（if/else） | 仅靠 `RunnableBranch`，表达能力弱 |
| 递归 / 动态流程 | 困难 |
| 状态持久化 | 不内置，跨步骤保存需自行实现 |
| 人工中断与恢复 | 不内置 |
| 运行历史 / 时间旅行 | 不提供 |

### 2.2 Agent 需要的能力

构建真正的 Agent（能自主推理、调用工具、动态决策的程序）需要：

- **循环（往返思考/行动）**：Agent 要反复「思考→执行→再看结果→再思考」，这是循环而非直线
- **动态路由**：根据当前状态决定下一步做什么
- **可中断 / 可恢复**：长时间运行的流程要能暂停（例如等待人工批准）、在崩溃后恢复
- **状态持久化**：每一步的状态要被记录，供回放与审查

LCEL 表达不了这些；而 LangGraph 的图模型正是为此而生的。

---

## 三、设计思想：把工作流建模为有向图

LangGraph 的核心思想非常朴素：**把工作流画成一张有向图**。

```
┌────────┐    ┌────────┐    ┌────────┐
│ Node A │───▶│ Node B │───▶│ Node C │   Node：执行操作（函数）
└────────┘    └───┬────┘    └────────┘
                  │ 条件       ▲
                  ▼            │
               ┌────────┐      │
               │ Node D │──────┘
               └────────┘
State（数据容器）在节点间传递，边决定流向。
```

把原来「写一段线性脚本」的思维，换成「先画清流程图，再让框架来执行」。你只负责定义**节点干什么**和**边怎么走**，剩下的执行顺序、状态合并、并行调度都由框架处理。

---

## 四、核心概念

### 4.1 State（状态）

节点之间共享的数据容器，通常用 `TypedDict` 定义：

```python
class State(TypedDict):
    input_text: str
    risk_level: str
```

每个节点**读取** State 中的字段作为输入，**返回**对 State 的部分更新（一个 dict），框架负责把更新合并进全局 State。

### 4.2 Node（节点）

一个执行操作的**函数**：接收 `state`，返回 `dict`（State 的部分更新）。

```python
def node(state: State) -> dict:
    return {"risk_level": "low"}   # 返回部分字段
```

节点里可以调用 LLM、调用工具、做任意处理、做路由决策。

### 4.3 Edge（边）

节点之间的**连接**，决定流转方向。普通边 `add_edge(a, b)` 表示无条件从 a 流到 b。

### 4.4 Conditional Edge（条件边）

**根据状态动态选择下一个节点**。这是实现路由和循环的基础（Day04 详讲）。

### 4.5 Compile（编译）

通过 `graph.compile()` 把图编译为一个**可执行对象** `CompiledGraph`，之后才能 `invoke` / `stream`。

### 4.6 Checkpointer（检查点/状态持久化）

一个可选组件，用于**跨 step 保存中间状态**，支持断点恢复、时间旅行与人工干预（Day05 详讲）。

---

## 五、与 LCEL 对比

| 维度 | LCEL | LangGraph |
| --- | --- | --- |
| 抽象模型 | 线性管道 `a \| b \| c` | 有向图（节点 + 边） |
| 循环 | 不支持 | 支持（条件边回环） |
| 条件分支 | `RunnableBranch`，能力有限 | `add_conditional_edges`，灵活 |
| 并行 | 需手动组织 | fan-out 天然并行 |
| 人工干预 | 不内置 | 基于 Checkpointer + interrupt |
| 状态持久化 | 手动 | 内置 Checkpointer |
| 调试/可视化 | 有限 | `get_graph()` 可视化 / 流式观测 |
| 适用场景 | 简单顺序流程 | 复杂控制流 / Agent |

**选择原则**：简单顺序管道用 LCEL，复杂控制流（循环、分支、持久化、多 Agent）用 LangGraph。二者互补，LangGraph 内部仍可复用 LangChain 的模型、Prompt、工具。

---

## 六、与 Agent 的关系

- **LangGraph 是构建 Agent 的底层图框架**
- 一个 Agent 本质上就是一张**状态图**：内含一个**推理循环**（思考→决定→调用工具→看结果→再思考），外加工具调用节点
- LangGraph 提供循环、条件路由、记忆、人工反馈等 Agent 需要的所有图能力

```
Agent ≈ 状态图（推理循环 + 工具调用）
```

> **本板块边界**：Day01-Day12 聚焦 LangGraph 框架本身（状态图、节点边、Checkpointer、流式、记忆、子图、错误处理）。基于它构建的完整 Agent 应用（ReAct/Tool/多智能体）会在后续独立的 **Agent 板块**深入讲解。

---

## 七、安装配置

### 7.1 系统要求

- Python 3.10+
- 至少一个 LLM API Key

### 7.2 安装依赖

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic
```

完整清单
| 包 | 作用 |
| --- | --- |
| `langgraph` | 状态图框架核心 |
| `langgraph-checkpoint` | 状态持久化（Checkpointer） |
| `langchain` | LangChain 核心 |
| `langchain-openai` | OpenAI/兼容接口 ChatModel |
| `python-dotenv` | 从 `.env` 读取 API Key |
| `pydantic` | 结构化数据校验 |

### 7.3 配置 API Key

在项目根目录创建 `.env`：

```
OPENAI_API_KEY=sk-xxxxxxxx
```

代码中用 `python-dotenv` 加载：

```python
from dotenv import load_dotenv
load_dotenv()   # 读取 .env
```

---

## 八、第一个图程序流程

任何 LangGraph 程序都遵循同样的六步：

```
① 定义 State(TypedDict)   →  ② 定义 Node 函数  →  ③ 创建 StateGraph
④ 添加节点与边           →  ⑤ compile() 编译   →  ⑥ invoke(input) 执行
```

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    msg: str

def node_a(state: State) -> dict:
    return {"msg": state["msg"] + " → A"}

def node_b(state: State) -> dict:
    return {"msg": state["msg"] + " → B"}

g = StateGraph(State)
g.add_node("a", node_a)
g.add_node("b", node_b)
g.set_entry_point("a")
g.add_edge("a", "b")
g.set_finish_point("b")

app = g.compile()                 # ⑤ 编译
print(app.invoke({"msg": "start"}))  # ⑥ 执行 → {'msg': 'start → A → B'}
```

---

## 关键知识点总结

### 1. 核心概念速查表

| 概念 | 作用 | 关键 API |
| --- | --- | --- |
| State | 节点间共享数据 | `TypedDict` 定义 |
| Node | 执行操作 | `node(state) -> dict` |
| Edge | 定义流转 | `add_edge(a, b)` |
| Conditional Edge | 动态路由 | `add_conditional_edges(...)` |
| Compile | 编译为可执行图 | `graph.compile()` |
| Checkpointer | 状态持久化 | `compile(checkpointer=...)` |
| START / END | 入口/出口特殊节点 | `START`、`END` |

### 2. LCEL vs LangGraph 对比表

见上文第五章的完整对比表，一句话记忆：**LCEL 走直线，LangGraph 走地图**。

### 3. 图编译执行流程图

```
源码图(StateGraph)
  │ compile()
  ▼
CompiledGraph (可执行)
  │ invoke(initial_state)
  ▼
START → node_a → node_b → END
        └────── State 逐节点合并 ──────┘
```

### 4. 环境安装清单

```bash
python -m venv .venv
# 激活（Windows）
.venv\Scripts\activate
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic
# 配置 .env 后再运行
python "Day01 - LangGraph概述与环境搭建/Code/01_hello_graph.py"
```

---

## 代码文件说明

| 文件 | 内容 |
| --- | --- |
| `01_hello_graph.py` | 第一个两节点图（接收→处理），完整演示创建/编译/执行 |
| `02_environment_setup.py` | 环境检查工具（Python 版本、依赖、Key、生成配置） |
| `03_graph_visualization.py` | 三节点图的结构可视化（get_graph 输出） |

---

## 常见问题排查

| 现象 | 原因与解决 |
| --- | --- |
| `ModuleNotFoundError: langgraph` | 未安装，执行 `pip install langgraph` |
| `API key 不生效` | 未加载 `.env`，或在代码顶部未调用 `load_dotenv()` |
| `TypedDict` 报错 | 用 Python 3.10+，或改从 `typing_extensions` 导入 |
| `invoke` 返回不是预期 | 检查节点函数是否全部返回 dict，且字段名与 State 一致 |

---

## 推荐学习资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/) - 权威参考
- [LangGraph How-to Guides](https://langchain-ai.github.io/langgraph/how-tos/) - 操作指南
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph) - 源码

---

## 实战练习

### 练习 1：观察状态流转
运行 `01_hello_graph.py`，用 `stream_mode="updates"` 观察每个节点的增量输出，回答：`process_note` 字段为什么在两个节点中被拼接而不是被覆盖？

### 练习 2：扩展为三节点图
在 `03_graph_visualization.py` 的三步图基础上，新增第四个节点「存档 node」，插在「报告」之后，重新编译并观察 `get_graph()` 的结构变化。

### 练习 3：环境自检
运行 `02_environment_setup.py`，确认依赖与 API Key 状态。若 `langchain_openai` 未安装，`pip install langchain-openai` 后重跑，观察输出变化。

---

## 下一步

完成 Day01，你就搭建好了 LangGraph 的「骨架」。Day02 深入整个框架的**灵魂**——`State` 状态管理与 `TypedDict`，理解状态如何在节点间流转与合并。