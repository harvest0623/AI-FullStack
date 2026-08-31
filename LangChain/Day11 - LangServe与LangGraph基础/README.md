# Day11 - LangServe 与 LangGraph 基础

> LangServe 把 Chain 部署为 API 服务，LangGraph 用状态图编排复杂工作流，让 LangChain 应用走向服务化与工程化

## 本章简介

当 Chain 在本地跑通后，下一步是让它**被外部调用**和**处理复杂流程**。**LangServe** 基于 FastAPI 把任意 Runnable/Chain 一键部署为 REST API，自动生成 `/invoke`、`/batch`、`/stream` 端点和在线调试 Playground；**LangGraph** 用状态图（StateGraph）编排带循环、分支、并行的复杂 LLM 工作流，弥补 LCEL 线性管道的不足。

本天首先用 LangServe 把 ChainQA 部署为可被前端/其他服务调用的 API，然后学习 LangGraph 的核心概念（State/Node/Edge/Conditional Edge），构建简单的线性图和条件分支图。**重要提醒**：本天只讲 LangGraph 基础概念和简单用法，复杂的 Agent 工作流将在后续 Agent 板块深入。

---

## 学习目标

完成本章后，你应能够：

1. 理解 LangServe 的作用和价值
2. 使用 `add_routes()` 把 Chain 注册为 REST API
3. 用 uvicorn 启动 LangServe 服务并访问各端点
4. 使用 Playground 在线调试 Chain
5. 添加自定义端点、认证中间件、CORS 配置
6. 理解 LangGraph 的核心概念：State / Node / Edge / Conditional Edge
7. 用 StateGraph 构建线性工作流（定义状态→节点→边→编译→执行）
8. 用 `add_conditional_edges` 实现条件分支
9. 实现带终止条件的循环图和并行节点
10. 理解 LangGraph vs LCEL 的选择决策

---

## 理论知识讲解

### 1. LangServe 概念

**LangServe** 将 LangChain Runnable/Chain 部署为 REST API，基于 FastAPI 构建，自动生成 API 端点和文档，内置 Playground 在线调试。

**核心价值**：
- 一行代码 `add_routes()` 把 Chain 变成 API
- 自动生成 `/invoke`、`/batch`、`/stream` 等标准端点
- 内置 Playground，浏览器即可调试
- 复用 FastAPI 生态（中间件、认证、CORS）

### 2. LangServe 集成步骤

```python
from fastapi import FastAPI
from langserve import add_routes
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# 1. 创建 Chain
prompt = ChatPromptTemplate.from_messages([("human", "{question}")])
chain = prompt | ChatOpenAI(model="gpt-4o-mini") | StrOutputParser()

# 2. 创建 FastAPI app
app = FastAPI(title="ChainQA API")

# 3. add_routes 注册 Chain
add_routes(app, chain, path="/chainqa")

# 4. 启动：uvicorn 01_langserve_basic:app --reload
```

### 3. 自动生成的 API 端点

注册 `path="/chainqa"` 后自动生成：

| 端点 | 方法 | 用途 |
|------|------|------|
| `/chainqa/invoke` | POST | 单次调用 |
| `/chainqa/batch` | POST | 批量调用 |
| `/chainqa/stream` | POST | 流式调用 |
| `/chainqa/ainvoke` | POST | 异步单次调用 |
| `/chainqa/input_schema` | GET | 输入 Schema |
| `/chainqa/output_schema` | GET | 输出 Schema |
| `/chainqa/config_schema` | GET | 配置 Schema |
| `/chainqa/playground` | GET | 在线调试界面 |

### 4. LangServe Playground

访问 `http://localhost:8000/chainqa/playground` 即可：
- 浏览器中测试 Chain
- 自动渲染输入表单
- 实时查看输出
- 查看请求/响应 JSON

### 5. 自定义 API 端点

除自动生成的端点外，可添加自定义路由、认证、CORS：

```python
from fastapi.middleware.cors import CORSMiddleware

# CORS 配置（允许前端跨域调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义端点
@app.get("/health")
def health():
    return {"status": "ok"}
```

### 6. LangGraph 概念

**LangGraph** 用状态图（StateGraph）编排复杂 LLM 工作流。

**vs LangChain Chains**：

| 维度 | LCEL Chains | LangGraph |
|------|------------|-----------|
| 结构 | 线性管道 | 状态图 |
| 循环 | ❌ 不支持 | ✅ 支持 |
| 分支 | RunnableBranch（有限） | Conditional Edge（灵活） |
| 并行 | RunnableParallel | 节点并行 |
| 人工干预 | ❌ | ✅ 支持 |
| 适用 | 简单线性流程 | 复杂工作流 |

**适用场景**：多步骤 Agent 工作流 / 循环推理 / 人工干预 / 并行处理

> LangGraph 后续 Agent 板块深入使用，本天只讲基础概念和简单图。

### 7. LangGraph 核心概念

| 概念 | 说明 | 示例 |
|------|------|------|
| **State（状态）** | 在图中流转的数据，TypedDict 定义 | `class State(TypedDict): question: str` |
| **Node（节点）** | 执行操作的函数，接收 State 返回更新 | `def analyze(state): return {...}` |
| **Edge（边）** | 连接节点的路径 | `graph.add_edge("a", "b")` |
| **Conditional Edge** | 根据条件选择下一节点 | `graph.add_conditional_edges("a", route_func)` |
| **START / END** | 图的入口和出口 | `graph.add_edge(START, "first")` |

### 8. LangGraph 基础用法（九步）

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. 定义 State
class State(TypedDict):
    question: str
    analysis: str
    answer: str

# 2. 创建 Node 函数（接收 State，返回部分更新）
def analyze(state: State) -> dict:
    return {"analysis": f"分析问题：{state['question']}"}

def generate(state: State) -> dict:
    return {"answer": f"基于 {state['analysis']} 生成回答"}

# 3. 创建 StateGraph
graph = StateGraph(State)

# 4. 添加节点
graph.add_node("analyze", analyze)
graph.add_node("generate", generate)

# 5. 添加边
graph.add_edge("analyze", "generate")

# 6. 设置入口和出口
graph.add_edge(START, "analyze")
graph.add_edge("generate", END)

# 7. 编译
app = graph.compile()

# 8. 执行
result = app.invoke({"question": "什么是 LangChain？"})
# 9. result 包含最终 State
```

### 9. 条件边（Conditional Edge）

```python
def route_by_complexity(state: State) -> str:
    """根据问题复杂度路由到不同节点"""
    if len(state["question"]) < 10:
        return "simple_answer"
    return "complex_answer"

graph.add_conditional_edges(
    "analyze",              # 源节点
    route_by_complexity,    # 路由函数（返回下一节点名）
    {                       # 路由映射（可选，显式声明）
        "simple_answer": "simple_node",
        "complex_answer": "complex_node",
    }
)
```

### 10. LangGraph vs LCEL 选择决策

| 场景 | 推荐 | 理由 |
|------|------|------|
| 简单 Q&A 链 | LCEL | 线性管道足够 |
| 多步检索→生成 | LCEL | 仍是线性 |
| 循环直到满足条件 | LangGraph | LCEL 不支持循环 |
| 根据条件选不同链 | LangGraph | 条件边更灵活 |
| 多轮工具调用 | LangGraph | Agent 核心能力 |
| 人工审批环节 | LangGraph | 支持暂停/恢复 |

---

## 代码文件说明

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_langserve_basic.py` | LangServe 基础 API 部署 | ChainQA API 基础版 |
| `02_langserve_playground.py` | Playground + 自定义端点 + CORS | ChainQA API 增强版 |
| `03_langgraph_basics.py` | LangGraph StateGraph 基础（线性图） | 问题分析→检索→生成 |
| `04_langgraph_advanced.py` | 条件分支 + 循环 + 并行 | 根据复杂度路由 |

---

## 关键知识点总结

### LangServe API 端点速查

见上文"自动生成的 API 端点"小节。

### LangGraph 核心概念速查

见上文"LangGraph 核心概念"小节。

### LangGraph vs LCEL 对比表

见上文"vs LangChain Chains"小节。

### LangGraph 基础流程图

```
START → [node_1] → [node_2] → ┬→ [node_a] → END     (条件分支)
                              └→ [node_b] → END

      ┌←──────────┐
[node] → 检查条件 ─→ 满足 → END                       (循环)
            ↓不满足
         回到 [node]
```

---

## 实战练习

### 练习一：部署 ChainQA API 并测试

运行 `01_langserve_basic.py` 启动服务，用 `curl` 或 Postman 测试以下端点：
- `POST /chainqa/invoke`（单次调用）
- `POST /chainqa/batch`（批量调用）
- `GET /chainqa/playground`（浏览器访问调试）
- `GET /chainqa/input_schema`（查看输入 Schema）

### 练习二：构建三节点 LangGraph

用 LangGraph 构建一个三节点工作流：问题分类→检索相关文档→生成回答。State 包含 `question`、`category`、`docs`、`answer` 四个字段。执行后打印完整 State。

### 练习三：实现循环终止条件

基于 `04_langgraph_advanced.py`，实现一个"自检循环"：生成回答后由一个检查节点判断回答质量，若不合格则回到生成节点重新生成，最多循环 3 次。提示：用条件边 + State 中的 `retry_count` 字段。

---

## 与后续板块衔接

本天的 LangGraph 基础是 Agent 板块的核心：

- **Agent 板块**：用 LangGraph 构建 ReAct Agent、Function Calling Agent
- **循环决策**：Agent 的多轮工具调用就是 LangGraph 的循环
- **状态管理**：Agent 的中间状态用 State 管理
- **人工干预**：复杂 Agent 支持人工审批环节

打好本天的 LangGraph 基础，Agent 学习将事半功倍。

---

**下一站**：[Day12 - 生产部署与最佳实践](../Day12%20-%20生产部署与最佳实践/README.md)
