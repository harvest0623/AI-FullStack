# LangGraph 学习指南

> 系统化掌握 LangGraph 状态图框架，构建可控、可恢复、可扩展的复杂工作流与 Agent

> 共 12 天，覆盖从 StateGraph 基础、节点与边、条件路由、Checkpointer 持久化、人工干预、流式输出到记忆管理、子图、错误处理的完整知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [示例项目](#示例项目)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是全栈学习系列的 **LLM 工作流编排核心**。LangGraph 是 LangChain 生态中用于构建**有状态、可恢复、多步骤** LLM 应用的框架。它以"图"为抽象——节点执行操作、边定义流转、状态在节点间传递——天然支持循环、分支、回退和人工干预，是构建 Agent 和复杂自动化工作流的标准工具。

**与 LangChain 板块的关系**：LangChain 的 LCEL 适合线性管道，LangGraph 则解决了 LCEL 无法优雅表达的循环、条件路由、状态持久化和人工干预等需求。两板块互补，LangGraph 建立在 LangChain 的模型/Prompt/工具等组件之上。

**板块边界**：本板块聚焦 LangGraph 框架本身——状态图、节点边、Checkpointer、人工循环、流式、记忆、子图、错误处理。基于 LangGraph 构建的 Agent 应用（ReAct Agent、Tool Agent、多智能体协作），将在后续的 Agent 独立板块中深入。

**学习目标**：完成本板块后，你应能：
- 理解 LangGraph 的状态图模型和核心设计思想
- 用 `TypedDict` 精确建模 `State`
- 创建节点和边，组织状态流转
- 用条件边实现动态路由与循环
- 用 `Checkpointer` 实现状态持久化与断点恢复
- 实现 Human-in-the-loop（人工审阅/中断恢复）
- 流式输出与事件订阅
- 并行执行、子图组合
- 短时记忆（会话内）与长时记忆（跨会话）
- 自定义 Reducer 与消息累积等状态进阶
- 错误处理、重试与容错
- 将 LangGraph 应用部署到生产环境

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 Python 代码 + 实战练习
- 全程围绕统一的**内容审核与智能问答工作流 `GraphFlow`** 项目展开
- 所有代码基于 LangGraph 0.2+（最新稳定版），可在 Python 3.10+ 直接运行
- 紧扣工程化视角，为后续 Agent 板块铺垫

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| Python | 必须 | 类型注解(TypedDict)、异步、装饰器 |
| LangChain | 必须 | 理解 Model/Prompt/工具调用（LangChain 板块知识） |
| LLM | 已完成更佳 | 理解 ChatModel/流式/Token |
| 图论基础 | 了解即可 | 节点、边、有向无环的概念 |

**环境准备**：
- Python 3.10+
- `pip install langgraph langchain langchain-openai`
- 至少一个 LLM API Key（OpenAI / Anthropic / 国内模型）
- 持久化可选：`langgraph-checkpoint-sqlite` / `redis` / `postgres`

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph 学习路线（12天）                     │
└─────────────────────────────────────────────────────────────────┘

阶段一：图基础（Day01-Day04）
┌──────────┬──────────┬──────────┬──────────┐
│ Day01    │ Day02    │ Day03    │ Day04    │
│ 概述与   │ State    │ Node与   │ Conditional│
│ 环境搭建 │ 状态管理 │ Edge边   │ 条件分支 │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
阶段二：生产能力（Day05-Day08）
┌──────────┬──────────┬──────────┬──────────┐
│ Day05    │ Day06    │ Day07    │ Day08    │
│ Checkpoint│ Human-in-│ 流式输出  │ 并行与   │
│ 持久化   │ the-loop │ 事件处理  │ 子图     │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
阶段三：进阶（Day09-Day12）
┌──────────┬──────────┬──────────┬──────────┐
│ Day09    │ Day10    │ Day11    │ Day12    │
│ 记忆管理  │ Reducer  │ 错误处理  │ 应用与   │
│ 短时长时 │ 状态进阶  │ 重试容错  │ 最佳实践 │
└──────────┴──────────┴──────────┴──────────┘
```

---

## 示例项目

本板块全程围绕一个**内容审核与智能问答工作流 `GraphFlow`** 项目展开，逐步用 LangGraph 构建一个可监督、可恢复、可复用的多步骤流程。

### 项目背景

```
GraphFlow：一个"内容智能审核 + 问答"工作流
输入：用户提交的一篇文章/评论
处理：内容安全检测 → 情感/主题分析 → 是否需要人工审核 → 生成审核报告
```

各 Day 逐步为 GraphFlow 增加能力：
- Day01-02：搭建基础图 + 定义状态
- Day03-04：添加分析节点 + 按内容类型路由
- Day05：断点恢复（进程崩溃后继续）
- Day06：敏感内容人工审阅
- Day07：流式展示分析进度
- Day08：多篇并行审核 + 子图复用
- Day09：跨会话记住用户偏好
- Day10：消息列表累积多条分析结果
- Day11：违规内容分析与重试
- Day12：封装为 FastAPI 服务部署

> 各天代码围绕该工作流逐步演进，形成完整项目。

---

## 每日内容详表

### 阶段一：图基础

#### Day01 - LangGraph概述与环境搭建
- **核心**：LangGraph 定义与发展、解决的问题（LCEL 无法处理循环/分支/持久化）、状态图模型（StateGraph/State/Node/Edge）、与 LCEL 对比、与 Agent 的关系、安装配置、第一个图程序（简单两节点图）、图编译与执行（`compile()` + `invoke()`）、图的调试（`get_graph()` / 绘图）
- **代码**：`01_hello_graph.py`（第一个 LangGraph 图）/ `02_environment_setup.py`（环境检查）/ `03_graph_visualization.py`（图结构可视化）/ `README.md`（环境搭建与核心概念）
- **重点**：状态图模型、图编译执行流程

#### Day02 - State状态管理与TypedDict
- **核心**：State 概念（节点间共享的数据）、用 `TypedDict` 定义状态、状态字段（str/int/list/dict/TypedDict 嵌套）、Reducer 概念（如何处理多个节点返回同一字段）、默认 Reducer（`operator.add` 覆盖 vs `Annotated`）、消息累积（`add_messages`）、状态初始化、节点返回 partial state、状态类型检查、可变字段与不可变字段
- **代码**：`01_state_definition.py`（TypedDict 定义状态）/ `02_reducer_basics.py`（Reducer 覆盖与累积）/ `03_message_state.py`（消息列表状态）/ `README.md`（State 深入指南）
- **重点**：`Annotated[list, add_messages]`、Reducer 语义

#### Day03 - Node节点与Edge边
- **核心**：Node 定义（普通函数/async 函数/可绑定 LLM）、签名约定（state → dict，可返回 partial state）、Edge 类型（`add_edge` 普通边 / `add_conditional_edges` 条件边 / `set_entry_point` / `set_finish_point`）、START/END 节点、节点返回值的合并规则、多个入边/出边的行为（fan-in/fan-out）、节点顺序与执行的确定性、分支并行
- **代码**：`01_node_basics.py`（节点定义与返回 / 02_edge_types.py`（普通边与入口出口）/ `03_fan_out_in.py`（扇入扇出行为）/ `README.md`(Node 与 Edge 指南）
- **重点**：普通边 `|` 与条件边、fan-out/fan-in 行为

#### Day04 - Conditional Edges条件分支
- **核心**：条件边概念（根据状态动态选择下一个节点）、`add_conditional_edges` 语法、路径映射函数（返回节点名/节点名列表）、返回多个节点（并行分支）、条件分支 vs 普通分支、路由节点的设计模式（llm 路由 / 规则路由 / 语义路由）、无条件 fallback（默认路径）、常见坑（路径函数放错参数位置）、实战：文本分类路由到不同处理链
- **代码**：`01_conditional_edges.py`（条件边基础）/ `02_router_pattern.py`（路由节点模式）/ `03_llm_router.py`(LLM 语义路由）/ `README.md`（条件分支指南）
- **重点**：`add_conditional_edges` 语法、路由设计模式

---

### 阶段二：生产能力

#### Day05 - Checkpointer与持久化
- **核心**：Checkpointer 概念（保存图执行的中间状态）、为什么需要（断点恢复/时间旅行/人工干预）、内置 Checkpointer（MemorySaver 内存 / SqliteSaver 文件 / PostgresSaver / RedisSaver）、`compile(checkpointer=...)`、thread_id 配置（多会话隔离）、`get_state` / `update_state` / `get_state_history`、图执行恢复（从断点继续）、时间旅行（回溯到历史状态）
- **代码**：`01_memory_saver.py`（内存 Checkpointer）/ `02_sqlite_saver.py`（SQLite 持久化）/ `03_time_travel.py`（时间旅行与状态回溯）/ `README.md`（持久化指南）
- **重点**：MemorySaver 与会话隔离、SqliteSaver 文件持久化

#### Day06 - Human-in-the-loop人工干预
- **核心**：Human-in-the-loop 概念、为什么需要（安全审阅/确认操作/纠错）、基于 Checkpointer 的三种模式（interrupt / wait_user_input / `interrupt()` 函数）、在图中插入 `interrupt()` 暂停、恢复执行（`Command(resume=...)`）、`graph.invoke` 的 `Command`、审阅/编辑工具调用、示例：敏感内容审核需人工通过
- **代码**：`01_interrupt_basics.py`（interrupt 打断与恢复）/ `02_command_resume.py`（Command 恢复执行）/ `03_approval_flow.py`（人工审批工作流）/ `README.md`（人工干预指南）
- **重点**：`interrupt()` 打断、`Command` 恢复、审批流程

#### Day07 - 流式输出与事件处理
- **核心**：LangGraph 流式输出（`stream()` / `astream()`）、`stream_mode` 参数（`values` / `updates` / `custom` / `debug`）、增量输出、`astream_events()` 事件流（on_chat_model_stream 等）、事件过滤（filter）、实现打字机效果、流式输出中的 Checkpointer、vs LangChain stream 的差异
- **代码**：`01_stream_modes.py`（values/updates 模式）/ `02_astream_events.py`（事件流订阅）/ `03_typing_effect.py`（打字机效果实现）/ `README.md`（流式指南）
- **重点**：`stream_mode` 各模式、`astream_events()` 事件过滤

#### Day08 - 并行执行与子图
- **核心**：并行节点（fan-out 后多个节点并发）、`send` API（动态生成节点）/`send` 批量并行、`commands: Send`、子图概念（`CompiledGraph` 嵌套）、子图作节点、`StateGraph` 组合、顶层图与子图的接口对齐、并行度的控制、示例：多篇内容并行审核
- **代码**：`01_parallel_nodes.py`（并行节点）/`02_send_batch.py`（send 动态并行）/ `03_subgraph.py`（子图组合）/`README.md`（并行与子图指南）
- **重点**：`send` 动态并行、子图嵌套组合

---

### 阶段三：进阶

#### Day09 - 记忆管理（短时与长时）
- **核心**：记忆概念（短时/长时）、短时记忆（会话内，通过 Checkpointer + thread_id）、长时记忆（跨会话，Store 接口）、LangGraph Store、`BaseStore` / `InMemoryStore`、`Store` 的写入与读取、记忆的 key/namespace、在图中使用 Store、对话历史管理（持久化消息）、基于记忆的个性化
- **代码**：`01_short_term_memory.py`（短时记忆会话内）/ `02_long_term_store.py`（长时记忆 Store）/ `03_personalized.py`（个性化记忆应用）/`README.md`（记忆管理指南）
- **重点**：Checkpointer+thread 短时记忆、Store 长时记忆

#### Day10 - 自定义Reducer与状态进阶
- **核心**：自定义 Reducer（`Annotated[type, reducer_func]`）、字段级 reducer、reducer 的输入（值列表）、`add_messages` 详解（追加/去重/插入）、自定义累积逻辑（去重、取最新、取最大）、状态嵌套与 `State` 继承、`add_node` 的冗余返回、处理 reducer 与直接赋值的差异、实战：多条分析结果按规则合并
- **代码**：`01_custom_reducer.py`（自定义 Reducer）/`02_add_messages_depth.py`（add_messages 详解）/ `03_state_inheritance.py`（状态继承）/`README.md`（Reducer 进阶指南）
- **重点**：`Annotated` 自定义 reducer、`add_messages` 行为

#### Day11 - 错误处理与重试
- **核心**：图中错误来源（LLM/工具/节点逻辑）、异常传播、`RetryPolicy`（重试策略：`max_attempts`/`wait`）、节点级重试、`graph.retry_policy`、错误上报与记录、fallback 节点（失败走备用）、`timeout` 超时、优雅降级、示例：LLM 调用失败自动重试 + 失败降级
- **代码**：`01_retry_policy.py`（RetryPolicy 重试）/ `02_fallback.py`(失败降级)/`03_timeout_degrade.py`（超时与降级）/`README.md`（错误处理指南）
- **重点**：`RetryPolicy`、fallback、超时容错

#### Day12 - 应用实践与最佳实践
- **核心**：LangGraph 项目架构设计（图/节点/状态分层）、`Command` 语义、事件与回调、`Config` 与 `RunnableConfig`、图复用（工厂函数）、测试（单节点/整图）、`Migration` 与版本、LangSmith 追踪集成、FastAPI 封装 API、Docker 部署、可观测性、最佳实践总结
- **代码**：`01_architecture.py`（分层架构实现）/`02_testing.py`（图测试框架）/`03_fastapi_service.py`（FastAPI 封装）/`04_best_practices.py`（综合最佳实践示例）/`README.md`（应用与最佳实践指南）
- **重点**：项目架构、图测试、FastAPI 封装、最佳实践

---

## 目录结构

```
LangGraph/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - LangGraph概述与环境搭建/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天 Python 代码
│       ├── 01_hello_graph.py
│       ├── 02_environment_setup.py
│       ├── 03_graph_visualization.py
│       └── README.md
├── Day02 - State状态管理与TypedDict/
│   ├── README.md
│   └── Code/
│       ├── 01_state_definition.py
│       ├── 02_reducer_basics.py
│       ├── 03_message_state.py
│       └── README.md
├── ...（Day03-Day11 同构）...
└── Day12 - 应用实践与最佳实践/
    ├── README.md
    └── Code/
        ├── 01_architecture.py
        ├── 02_testing.py
        ├── 03_fastapi_service.py
        ├── 04_best_practices.py
        └── README.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，均为 `.py` 文件（可直接 `python file.py` 运行）
- 部分天数含配置文件（`.yaml` / `.json` / `requirements.txt`）

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-6 小时 | 约 2-3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 4-5 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **先理解状态再画图**：LangGraph 的核心是状态，先读懂每个节点的输入输出
2. **动手跑图**：每个示例都用 `python file.py` 实际运行，观察输出状态
3. **对照状态流转**：用 `stream_mode="updates"` 观察每步状态变化
4. **结合 Checkpointer**：生产必配 Checkpointer，理解持久化与恢复
5. **逐步构建项目**：随学习推进完善 `GraphFlow` 工作流
6. **查阅官方文档**：LangGraph 更新快，以官方文档为准

### 阶段性检查点

- **阶段一完成后**：能否用 StateGraph 构建带条件路由的多节点图？
- **阶段二完成后**：能否用 Checkpointer 做持久化恢复、实现人工干预和流式输出、并行与子图？
- **阶段三完成后**：能否用记忆、自定义 Reducer、错误处理构建健壮的图，并部署为服务？

---

## 如何运行代码

### 环境准备

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 安装核心依赖
pip install langgraph langgraph-checkpoint langchain langchain-openai
# 可选
pip install langgraph-checkpoint-sqlite   # SQLite 持久化
pip install redis fastapi uvicorn         # Redis/API
```

### 配置 API Key

```bash
cat > .env << 'EOF'
OPENAI_API_KEY=sk-xxxxxxxx
EOF
```

### 运行示例

```bash
# 运行指定天数的代码
python "Day01 - LangGraph概述与环境搭建/Code/01_hello_graph.py"

# 演示持久化与恢复
python "Day05 - Checkpointer与持久化/Code/02_sqlite_saver.py"

# 启动 FastAPI 服务
uvicorn "Day12 - 应用实践与最佳实践/Code/03_fastapi_service:app" --reload
```

### 使用 Docker 运行

```bash
docker run -it --rm -v "$(pwd):/workspace" -w /workspace \
  --env-file .env python:3.12-slim \
  sh -c "pip install langgraph langgraph-checkpoint langchain-openai && python 'Day01 - LangGraph概述与环境搭建/Code/01_hello_graph.py'"
```

---

## 知识点速查

### LangGraph 核心概念速查

| 概念 | 作用 | 关键 API | 对应天数 |
|------|------|---------|---------|
| State | 节点间共享数据 | `TypedDict` / `Annotated` | Day02 |
| Node | 执行操作的函数 | `node(state) -> dict` | Day03 |
| Edge | 定义流转 | `add_edge` / `add_conditional_edges` | Day03/04 |
| Conditional Edge | 动态路由 | `add_conditional_edges(map)` | Day04 |
| Checkpointer | 状态持久化 | `compile(checkpointer=...)` | Day05 |
| Human-in-loop | 人工干预 | `interrupt()` / `Command(resume=)` | Day06 |
| Streaming | 流式输出 | `stream` / `astream_events` | Day07 |
| send | 动态并行 | `Command(send=[...])` | Day08 |
| Store | 长时记忆 | `BaseStore` / `InMemoryStore` | Day09 |
| Reducer | 字段合并策略 | `Annotated[type, reducer]` | Day10 |
| RetryPolicy | 节点重试 | `RetryPolicy(max_attempts=...)` | Day11 |

### State 三种典型形态速查

| 形态 | 定义 | 合并行为 | 适用场景 |
|------|------|---------|---------|
| 可覆盖字段 | `field: str` | 后写覆盖先写 | 单值结果（最终回答） |
| 累积列表 | `Annotated[list, add_messages]` | 追加/合并 | 消息、历史 |
| 自定义聚合 | `Annotated[type, func]` | 自定义逻辑 | 去重、取最新、求和 |

### 运行接口速查

| 方法 | 说明 | 同步/异步 |
|------|------|----------|
| `.invoke(input, config)` | 单次执行 | 同步 |
| `.stream(input, config, stream_mode)` | 流式输出 | 同步 |
| `.get_state(config)` | 查询当前状态 | - |
| `.get_state_history(config)` | 状态历史 | - |
| `.update_state(config, values)` | 更新状态 | - |
| `.ainvoke` / `.astream` | 异步 | 异步 |

### Checkpointer 对比速查

| Checkpointer | 持久化 | 是否跨进程 | 适用场景 |
|--------------|--------|-----------|---------|
| MemorySaver | 内存 | 否 | 开发调试/单进程 |
| SqliteSaver | SQLite 文件 | 是(单机) | 本地持久化/轻量 |
| PostgresSaver | PostgreSQL | 是 | 生产多实例 |
| RedisSaver | Redis | 是 | 高并发/分布式 |

### stream_mode 速查

| 模式 | 每步产出 | 适用 |
|------|---------|------|
| `values` | 每个节点后的完整状态 | 观察全状态 |
| `updates` | 每个节点返回的增量 | 追踪增量 |
| `custom` | 自定义事件 | 精细化控制 |
| `debug` | 详尽的调试事件 | 排查问题 |

### 记忆对比速查

| 类型 | 周期 | 实现 | API |
|------|------|------|-----|
| 短时记忆 | 会话内 | Checkpointer + thread_id | 状态消息 |
| 长时记忆 | 跨会话 | Store | `store.put` / `store.get` |

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **Agent** | 基于 LangGraph 的状态图构建完整 Agent（ReAct/Tool/Multi-agent） |
| **RAG** | 将检索节点接入 LangGraph 工作流 |
| **LangChain** | LangGraph 依赖的 LangChain 组件（模型/Prompt/工具） |
| **LLM** | 模型调用与流式/Token 基础 |
| **Python** | 类型注解、异步、装饰器 |
| **Docker** | LangGraph 应用容器化部署 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/) - 官方文档
- [LangGraph Cloud](https://www.langchain.com/langgraph-platform) - 云端部署
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph) - 源码
- [LangGraph Cookbook](https://github.com/langchain-ai/langgraph/tree/main/examples) - 官方示例
- [LangGraph How-to Guides](https://langchain-ai.github.io/langgraph/how-tos/) - 操作指南
- [LangChain 文档](https://python.langchain.com/docs/) - 依赖的组件

---

## 贡献与反馈

本学习手册为原创内容，参考 GitHub 优质仓库的文档风格但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用 LangGraph 编排强大的 AI 工作流！**