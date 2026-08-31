# Day11 Code - LangServe 与 LangGraph 代码示例

> 本目录包含 Day11 全部可运行代码，演示 LangServe API 部署与 LangGraph 状态图编排

## 文件清单

| 文件 | 内容 | 运行方式 | 场景 |
|------|------|---------|------|
| `01_langserve_basic.py` | LangServe 基础 API 部署 | `uvicorn 01_langserve_basic:app --reload` | ChainQA API 基础版 |
| `02_langserve_playground.py` | Playground + 自定义端点 + CORS + 认证 | `uvicorn 02_langserve_playground:app --reload --port 8001` | ChainQA API 增强版 |
| `03_langgraph_basics.py` | LangGraph StateGraph 基础（线性图） | `python 03_langgraph_basics.py` | 分析→检索→生成 |
| `04_langgraph_advanced.py` | 条件分支 + 循环 + 质量自检 | `python 04_langgraph_advanced.py` | 复杂度路由 |

## 运行顺序建议

```
01_langserve_basic.py     ← 先把 Chain 部署为 API
      │
      ▼
02_langserve_playground.py ← 再增强 API（认证/CORS/自定义端点）
      │
      ▼
03_langgraph_basics.py    ← 然后学 LangGraph 基础（线性图）
      │
      ▼
04_langgraph_advanced.py  ← 最后学条件分支与循环
```

## 环境准备

```bash
# 核心依赖
pip install langchain langchain-openai langgraph langserve fastapi uvicorn python-dotenv

# 配置 API Key（.env 文件）
# OPENAI_API_KEY=sk-xxxxxxxx
```

## 运行示例

### LangServe 服务

```bash
cd "d:\Coding\AI-FullStack\LangChain\Day11 - LangServe与LangGraph基础\Code"

# 基础版（端口 8000）
uvicorn 01_langserve_basic:app --reload --port 8000

# 增强版（端口 8001，需认证）
uvicorn 02_langserve_playground:app --reload --port 8001
```

### 测试 LangServe 端点

```bash
# 健康检查
curl http://localhost:8000/health

# 调用问答（invoke 端点）
curl -X POST http://localhost:8000/chainqa/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"question": "什么是 LangChain？"}}'

# 批量调用（batch 端点）
curl -X POST http://localhost:8000/chainqa/batch \
  -H "Content-Type: application/json" \
  -d '{"inputs": [{"question": "什么是 LCEL？"}, {"question": "什么是 Memory？"}]}'

# 浏览器访问 Playground
# http://localhost:8000/chainqa/playground
```

### LangGraph

```bash
python 03_langgraph_basics.py
python 04_langgraph_advanced.py
```

## LangServe/LangGraph 指南

### LangServe 部署步骤

```python
# 1. 创建 Chain
chain = prompt | model | parser

# 2. 创建 FastAPI app
app = FastAPI()

# 3. add_routes 注册
add_routes(app, chain, path="/chainqa")

# 4. 启动：uvicorn file:app --reload
```

### LangServe 自动生成的端点

| 端点 | 方法 | 用途 |
|------|------|------|
| `/path/invoke` | POST | 单次调用 |
| `/path/batch` | POST | 批量调用 |
| `/path/stream` | POST | 流式调用 |
| `/path/ainvoke` | POST | 异步单次调用 |
| `/path/input_schema` | GET | 输入 Schema |
| `/path/output_schema` | GET | 输出 Schema |
| `/path/playground` | GET | 在线调试 |

### LangGraph 核心概念图解

```
┌─────────────────────────────────────────────────┐
│  State（状态）：TypedDict 定义，在节点间流转      │
│  ┌──────────────────────────────────────────┐   │
│  │ question: str                            │   │
│  │ analysis: str                            │   │
│  │ answer: str                              │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘

    START ──→ [classify] ──→ ┌─→ [simple]  ──→ [check] ──→ END
                              │                              │
                              └─→ [complex] ──→ [check] ──→ ┐│
                                                              │
                              ┌──── retry ←───────────────────┘
                              │       │
                              └─→ [check] (循环) ──→ END
```

### LangGraph vs LCEL 选择决策表

| 场景 | 选 LCEL | 选 LangGraph |
|------|:------:|:------------:|
| 简单 Q&A 链 | ✅ | |
| 多步检索→生成 | ✅ | |
| 循环直到满足条件 | | ✅ |
| 条件分支选不同链 | | ✅ |
| 多轮工具调用 | | ✅ |
| 人工审批环节 | | ✅ |
| 并行多路径 | | ✅ |

### LangGraph 基础模式速查

```python
# 1. 线性图
graph.add_edge(START, "node1")
graph.add_edge("node1", "node2")
graph.add_edge("node2", END)

# 2. 条件分支
graph.add_conditional_edges(
    "node",
    route_func,           # 返回下一节点名
    {"path_a": "nodeA", "path_b": "nodeB"},
)

# 3. 循环（带终止）
graph.add_edge("retry", "check")           # 形成环
graph.add_conditional_edges(
    "check",
    lambda s: END if s["ok"] or s["count"] >= 3 else "retry",
)
```

### 与后续 Agent 板块衔接说明

本天的 LangGraph 基础是 Agent 板块的核心工具：

| 本天学到的 | Agent 板块如何用 |
|-----------|-----------------|
| State 定义 | Agent 的对话历史、工具调用记录 |
| Node 函数 | LLM 决策节点、工具执行节点 |
| 条件边 | Agent 判断是否继续调用工具 |
| 循环 | Agent 的多轮工具调用循环 |
| 终止条件 | Agent 的最大步数、目标达成判断 |

> Agent 本质上就是一个带循环的 LangGraph：决策→执行工具→观察→再决策，直到达成目标或达到步数上限。

## 常见问题

**Q1：uvicorn 启动报 ModuleNotFoundError: langserve？**
- 安装：`pip install langserve[all]`
- 确认在 Code 目录下运行

**Q2：LangGraph 报 ImportError？**
- LangGraph 是独立包：`pip install langgraph`
- 注意不是 `langchain-graph`

**Q3：Playground 打不开？**
- 确认服务已启动
- 检查端口是否正确（默认 8000）
- 查看 `/docs` 是否可访问

**Q4：条件边路由不生效？**
- 路由函数返回的字符串必须与节点名完全一致
- 检查 `add_conditional_edges` 的第三个参数（路由映射）

## 学习产出

完成本目录代码后，你应能：
- [ ] 用 LangServe 把 Chain 部署为 REST API
- [ ] 访问 Playground 在线调试 Chain
- [ ] 添加自定义端点、CORS、认证中间件
- [ ] 用 LangGraph StateGraph 构建线性工作流
- [ ] 用 add_conditional_edges 实现条件分支
- [ ] 实现带终止条件的循环图
