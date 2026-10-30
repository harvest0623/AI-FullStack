# Agent 学习指南

> 系统化掌握 AI Agent（智能体）：从核心循环、工具调用、ReAct 推理、记忆系统、任务规划，到多 Agent 协作、评估调试、安全护栏与生产落地，构建可自主完成任务的智能应用

> 共 12 天，聚焦 Agent 本身的原理与工程，是 LLM 的"行动化"与 RAG/VectorDB/框架等能力的"编排者"层

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

**AI Agent（智能体）** 是以 LLM 为大脑、能**感知环境 → 推理决策 → 调用工具 → 达成目标**的自主系统。如果说 LLM 是"会说"，Agent 就是"会做"；如果说 RAG 给了 LLM 知识，Agent 就给了 LLM **双手**。

**与 LLM 板块的关系**：LLM 板块研究"模型怎么调、Prompt 怎么写"；本板块研究"模型之上如何组织出**自主行动**能力"。

**与 RAG / VectorDB 板块的关系**：RAG 与向量库是 Agent 最常用的**工具之一**（检索工具）；本板块把它们当作可被 Agent 调用的能力。

**与 LangChain / LangGraph 板块的关系**：框架提供了 Agent 的封装（Tool/AgentExecutor/StateGraph）；本板块**徒手实现**核心机制，让你理解框架背后发生了什么，从而能正确设计、调试、定制。

**学习目标**：完成本板块后，你应能：
- 讲清 Agent 的定义、组成（LLM + 工具 + 记忆 + 规划）与核心循环
- 徒手实现工具调用（Function Calling 的原理与工程化）
- 掌握 ReAct 推理模式：思考 → 行动 → 观察
- 设计 Agent 记忆系统：短时上下文 / 长时存储 / 工作记忆
- 实现任务规划与分解：Plan-and-Execute、目标树
- 处理多工具编排、错误重试、并行调用
- 掌握多 Agent 协作模式：主从、流水线、辩论、群聊
- 学会评估与调试 Agent：轨迹分析、成功率、成本控制
- 落地人机协同与安全护栏：审批、权限、输出防护
- 交付一个可运行的 AgentHub 智能体服务

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 Python 代码 + 实战练习
- 全程围绕统一的**企业智能体平台 `AgentHub`** 项目展开
- 代码兼容离线运行（无 API Key 也能跑：内置"模拟 LLM"按规则响应，接口与真实 LLM 对齐，随时可切换）
- 紧扣 Agent 本身，与 LLM/RAG/框架板块互补而非重复

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| Python | 必须 | 面向对象、类型注解、装饰器、`dataclass` |
| LLM 基础 | 必须 | Chat 调用、消息结构（LLM 板块） |
| Prompt 工程 | 了解 | 系统提示、Few-shot（Prompt 板块） |
| RAG 概念 | 了解 | Agent 常用检索工具（RAG 板块更佳） |
| LangGraph | 了解 | 有助于对照框架封装（非必须） |

**环境准备**：
- Python 3.10+
- 基础依赖：`numpy`（部分天数）
- 可选（真实模式）：`openai` 或其他 LLM SDK + API Key
- 本板块**默认离线运行**：内置 `SimLLM` 模拟大脑，接口对齐真实 LLM，随时切换

---

## 学习路线图

```
┌──────────────────────────────────────────────────────────────────┐
│             Agent 学习路线（12天，从会说到会做）                     │
└──────────────────────────────────────────────────────────────────┘

阶段一：Agent 基石（Day01-Day03）
┌──────────────┬──────────────┬──────────────┐
│ Day01        │ Day02        │ Day03        │
│ 概述与       │ 核心循环      │ 工具调用与    │
│ 核心概念     │ 与ReAct      │ Function Call│
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       ▼              ▼              ▼
阶段二：核心能力（Day04-Day06）
┌──────────────┬──────────────┬──────────────┐
│ Day04        │ Day05        │ Day06        │
│ Agent        │ 任务规划      │ 多工具编排    │
│ 记忆系统      │ 与分解        │ 与错误处理    │
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       ▼              ▼              ▼
阶段三：协作与治理（Day07-Day09）
┌──────────────┬──────────────┬──────────────┐
│ Day07        │ Day08        │ Day09        │
│ 评估与调试    │ 多Agent      │ 人机协同与    │
│              │ 协作模式      │ 安全护栏      │
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       ▼              ▼              ▼
阶段四：生产落地（Day10-Day12）
┌──────────────┬──────────────┬──────────────┐
│ Day10        │ Day11        │ Day12        │
│ 服务化与      │ 生产部署与    │ 综合实战      │
│ 可观测        │ 最佳实践      │ AgentHub     │
└──────────────┴──────────────┴──────────────┘
```

---

## 示例项目

本板块全程围绕一个**企业智能体平台 `AgentHub`** 展开：为运营/研发/客服等场景构建能自主查数据、写报告、发通知、走审批的智能体，最终交付可观测、可控、可上线的 Agent 服务。

### 项目演进路径

| 阶段 | 使用的 Day | 形态 |
|------|-----------|------|
| 原理理解 | Day01-03 | Agent 定义、核心循环、工具调用 |
| 单体智能 | Day04-06 | 记忆 + 规划 + 多工具的独立 Agent |
| 协作治理 | Day07-09 | 评估调试、多 Agent、安全护栏 |
| 生产交付 | Day10-12 | 服务化、部署、AgentHub 综合 |

### 项目结构（最终 Service 形态）

```
agenthub/
├── config.yaml            ← 模型/工具/护栏配置
├── llm.py                 ← LLM 访问层（真实/模拟可切换）
├── tools/                 ← 工具注册表与实现
├── memory.py              ← 记忆系统
├── planner.py             ← 任务规划
├── agent.py               ← Agent 核心循环
├── guardrails.py          ← 安全护栏
├── observability.py       ← 轨迹与指标
└── server/                ← FastAPI 服务
```

> 各天围绕此项目逐步搭建，从"理解 Agent"到"上线 AgentHub"。

---

## 每日内容详表

### 阶段一：Agent 基石

#### Day01 - Agent概述与核心概念
- **核心**：什么是 Agent、LLM vs Chatbot vs Agent 的本质差异、Agent 四大组成（LLM 大脑 / 工具 / 记忆 / 规划）、自主性等级（L0 反射式→L4 自治）、典型应用（编程助手/数据分析/客服/办公自动化）、Agent 与 Workflow 的区别、设计范式概览（ReAct/Plan-Execute/Reflection）
- **代码**：`01_agent_intro.py`（Agent 与 Chatbot 对比）/`02_agent_anatomy.py`（四大组件骨架）/`03_autonomy_levels.py`（自主性等级演示）/`README.md`
- **重点**：Agent 定义、四大组成、自主性分级

#### Day02 - Agent核心循环与ReAct模式
- **核心**：感知-思考-行动循环、ReAct（Reasoning + Acting）思想、Thought/Action/Observation 三元组、循环终止条件（完成/最大步数/失败）、Agent Executor 骨架、轨迹（Trajectory）概念、循环中的上下文增长问题
- **代码**：`01_core_loop.py`（最小 Agent 循环）/`02_react_pattern.py`（ReAct 三元组实现）/`03_stop_conditions.py`（终止条件与防失控）/`04_trajectory.py`（轨迹记录与回放）/`README.md`
- **重点**：核心循环、ReAct 三元组、终止条件

#### Day03 - 工具调用与Function Calling
- **核心**：工具是 Agent 的双手、工具定义 Schema（名称/描述/参数 JSON Schema）、模型如何选择工具、函数签名与文档的重要性、工具注册表、参数解析与校验、执行结果回填、无工具调用时的直答、常见工具类型（检索/API/代码/文件）
- **代码**：`01_tool_schema.py`（工具定义与描述）/`02_tool_registry.py`（注册表与路由）/`03_param_validate.py`（参数解析与校验）/`04_tool_roundtrip.py`（完整调用往返）/`README.md`
- **重点**：Schema 设计、注册表、调用往返

---

### 阶段二：核心能力

#### Day04 - Agent记忆系统
- **核心**：为什么 Agent 需要记忆、记忆分层（工作记忆/短时上下文/长时存储）、对话历史管理与裁剪（滑动窗口/摘要）、长时记忆的写入与检索（向量/关键词）、记忆的重要性评分、跨会话记忆、记忆与上下文窗口的取舍
- **代码**：`01_memory_layers.py`（三层记忆骨架）/`02_history_mgmt.py`（历史裁剪与摘要）/`03_longterm_store.py`（长时记忆写入检索）/`04_memory_score.py`（记忆打分与淘汰）/`README.md`
- **重点**：记忆分层、历史管理、长时检索

#### Day05 - 任务规划与分解
- **核心**：规划是 Agent 的"深谋"、Plan-and-Execute 范式（先规划后执行）、任务分解（DAG/清单/树）、规划与反应式的取舍、动态重规划（Replan）、目标管理（子目标完成判定）、TODO 列表驱动、长任务的里程碑设计
- **代码**：`01_plan_execute.py`（先规划后执行）/`02_task_dag.py`（任务依赖图）/`03_replan.py`（动态重规划）/`04_todo_driver.py`（清单驱动执行）/`README.md`
- **重点**：Plan-Execute、任务分解、重规划

#### Day06 - 多工具编排与错误处理
- **核心**：工具越多选择越难（选择准确性）、工具描述优化与分组、并行工具调用、工具结果的聚合、错误处理体系（参数错/执行错/超时）、重试策略（退避/换工具/问用户）、工具链路的超时与取消、成本意识（token/调用次数）
- **代码**：`01_tool_selection.py`（多工具选择准确性）/`02_parallel_tools.py`（并行调用与聚合）/`03_error_retry.py`（错误分类与重试）/`04_cost_control.py`（步数与成本预算）/`README.md`
- **重点**：工具选择、并行执行、重试策略

---

### 阶段三：协作与治理

#### Day07 - Agent评估与调试
- **核心**：Agent 评估的难点（多步/非确定）、评估维度（任务成功率/效率/成本/安全）、轨迹（Trajectory）分析、逐步调试方法（单步/断点/回放）、常见失败模式（死循环/幻觉工具/参数幻觉/过早放弃）、A/B 对比与回归、评估数据集建设
- **代码**：`01_eval_metrics.py`（成功率/效率/成本指标）/`02_trajectory_debug.py`（轨迹分析与失败定位）/`03_failure_modes.py`（典型失败模式复现）/`04_ab_compare.py`（A/B 对比实验）/`README.md`
- **重点**：评估指标、轨迹调试、失败模式

#### Day08 - 多Agent协作模式
- **核心**：为什么需要多 Agent（分工/上下文隔离/专业性）、协作模式（主从 Supervisor / 流水线 Pipeline / 辩论 Debate / 群聊 GroupChat）、消息传递协议、角色定义（角色 Prompt）、任务移交 Handoff、共享状态与黑板模式、协作的成本与复杂度
- **代码**：`01_supervisor.py`（主从编排）/`02_pipeline.py`（流水线协作）/`03_debate.py`（辩论收敛）/`04_group_chat.py`（群聊调度）/`README.md`
- **重点**：Supervisor、Pipeline、Handoff

#### Day09 - 人机协同与安全护栏
- **核心**：Human-in-the-Loop 的价值（关键决策留给人）、审批门（工具执行前拦截）、中断与恢复（中断点/状态保存）、澄清式提问（信息不足时主动问）、输入护栏（注入攻击/越权指令）、工具权限矩阵（最小权限）、输出护栏（敏感信息/合规）、审计日志
- **代码**：`01_approval_gate.py`（工具审批门）/`02_interrupt_resume.py`（中断与恢复）/`03_clarify.py`（澄清式提问）/`04_guardrails.py`（输入输出护栏与权限矩阵）/`README.md`
- **重点**：审批门、中断恢复、护栏

---

### 阶段四：生产落地

#### Day10 - Agent服务化与可观测
- **核心**：从脚本到服务（API 化）、同步与异步任务模式（task_id 轮询）、轨迹日志三层结构（请求级/步骤级/依赖级）、链路追踪（trace_id/span 树）、核心指标（成功率/P99/Token 成本）、告警规则与分级（P0/P1/P2）、限流与熔断
- **代码**：`01_fastapi_service.py`（同步/异步 API 与任务队列）/`02_trajectory_log.py`（三层轨迹日志）/`03_tracing.py`（trace_id 链路追踪与瀑布图）/`04_metrics_alert.py`（指标采集与告警引擎）/`README.md`
- **重点**：异步任务、轨迹日志、链路追踪、指标告警

#### Day11 - 生产部署与最佳实践
- **核心**：LLM 是概率系统必须灰度（5%→20%→50%→100%）、Prompt 即代码（版本化/评审/可回滚）、A/B 测试与 ROI 决策（成功率 vs Token 成本）、回滚三层资源（流量/数据兼容/存量任务）、成本优化三板斧（语义缓存/模型分级/上下文压缩）、PoC→生产检查清单
- **代码**：`01_canary_release.py`（灰度发布与自动回滚）/`02_prompt_versioning.py`（Prompt 版本管理与 A/B）/`03_rollback.py`（回滚策略与演练）/`04_cost_optimization.py`（缓存/分级路由/上下文压缩）/`README.md`
- **重点**：灰度发布、Prompt 版本管理、回滚、成本优化

#### Day12 - 综合实战AgentHub
- **核心**：把 12 天所学组装成完整框架：ToolRegistry + Memory + Planner + Guard + ApprovalGate + TrajectoryLogger + ReActLoop 总装、各模块与 LangGraph/LangChain 的概念对照、扩展方式（自定义工具/注入审批函数/继承改写）
- **代码**：`agenthub.py`（核心框架，7 组件组装）/`01_quickstart.py`（3 步跑通）/`02_tools_memory.py`（自定义工具与长期记忆）/`03_full_pipeline.py`（护栏/审批/脱敏/日志全链路实战）/`README.md`
- **重点**：组装、全链路实战、框架对照

---

## 目录结构

```
Agent/
├── README.md                          ← 本文件（板块总入口）
├── Day01 - Agent概述与核心概念/
│   ├── README.md
│   └── Code/
│       ├── 01_agent_intro.py
│       ├── 02_agent_anatomy.py
│       ├── 03_autonomy_levels.py
│       └── README.md
├── Day02 - Agent核心循环与ReAct模式/
│   ├── README.md
│   └── Code/...
├── ...（Day03-Day11 同构）...
└── Day12 - 综合实战AgentHub/
    ├── README.md
    └── Code/
        ├── agenthub.py          ← 核心框架（7 组件组装）
        ├── 01_quickstart.py
        ├── 02_tools_memory.py
        ├── 03_full_pipeline.py
        └── README.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，均为 `.py` 文件（可直接 `python file.py` 运行）
- 所有代码**离线可跑**：内置 SimLLM 模拟大脑；配置 API Key 后可切换真实 LLM

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-6 小时 | 约 2-3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 4-5 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **先机制后框架**：徒手实现一遍 Agent 循环，再用 LangChain/LangGraph 时才知其所以然。
2. **盯着轨迹看**：Agent 的行为都在轨迹里，调试从"打印每一步 Thought/Action/Observation"开始。
3. **小步快跑**：先让 Agent 会用一个工具，再谈规划、记忆、多 Agent。
4. **成本意识**：每一步都是 token，循环每多跑一轮都是钱；始终关注步数与成本。
5. **安全先行**：能"做"意味着能"闯祸"，工具权限与审批要早于功能上线。
6. **对比框架**：把自己实现的循环对照 LangGraph 的 StateGraph / LangChain 的 AgentExecutor，理解封装价值。

### 阶段性检查点

- **阶段一完成后**：能否徒手写出一个带工具调用的最小 Agent 循环？
- **阶段二完成后**：能否给 Agent 加上记忆与规划，跑通一个多步任务？
- **阶段三完成后**：能否评估与调试 Agent，并搭建多 Agent 协作与安全护栏？
- **阶段四完成后**：能否把 Agent 服务化、可观测化，并交付 AgentHub 综合 Demo？

---

## 如何运行代码

### 环境准备

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 基础依赖
pip install numpy

# 可选：真实 LLM 模式（所有示例默认离线 SimLLM，无需 Key）
# pip install openai
# set OPENAI_API_KEY=sk-xxx        # Windows
# export OPENAI_API_KEY=sk-xxx     # Linux/macOS
```

### 运行示例

```bash
# Day01：Agent 是什么
python "Day01 - Agent概述与核心概念/Code/01_agent_intro.py"

# Day02：最小 Agent 循环 + ReAct
python "Day02 - Agent核心循环与ReAct模式/Code/01_core_loop.py"
python "Day02 - Agent核心循环与ReAct模式/Code/02_react_pattern.py"

# Day03：工具调用
python "Day03 - 工具调用与Function Calling/Code/04_tool_roundtrip.py"

# Day09：安全护栏
python "Day09 - 人机协同与安全护栏/Code/04_guardrails.py"

# Day12：AgentHub 综合实战
python "Day12 - 综合实战AgentHub/Code/03_full_pipeline.py"
```

> 所有脚本均可在**无网络、无 API Key** 环境下直接运行（SimLLM 按规则模拟响应，接口与真实 LLM 对齐）。

---

## 知识点速查

### Chatbot vs Workflow vs Agent 速查

| 维度 | Chatbot | Workflow | Agent |
|------|---------|----------|-------|
| 决策者 | 人 | 开发者预定义 | LLM 自主 |
| 路径 | 单轮问答 | 固定流程图 | 动态规划 |
| 工具 | 无/少 | 固定节点 | 自主选择 |
| 可预测性 | 高 | 高 | 低（需护栏） |
| 适用 | 问答 | 确定任务 | 开放任务 |

### Agent 四大组成速查

| 组件 | 作用 | 类比 |
|------|------|------|
| LLM 大脑 | 推理与决策 | 前额叶 |
| 工具 Tools | 感知与行动能力 | 双手 |
| 记忆 Memory | 上下文与经验 | 海马体 |
| 规划 Planning | 目标分解与路径 | 执行功能 |

### ReAct 三元组速查

| 环节 | 内容 | 说明 |
|------|------|------|
| Thought | 我该做什么、为什么 | 推理 |
| Action | 调用某工具+参数 | 行动 |
| Observation | 工具返回结果 | 感知 |

### 自主性等级速查

| 等级 | 名称 | 特征 |
|------|------|------|
| L0 | 反射式 | 规则触发，无推理 |
| L1 | 辅助式 | 建议+人执行 |
| L2 | 半自治 | 低风险自主，高风险审批 |
| L3 | 受限自治 | 目标内全自主，边界明确 |
| L4 | 全自治 | 长期目标，自我纠偏 |

### 多 Agent 协作模式速查

| 模式 | 结构 | 适用 |
|------|------|------|
| Supervisor | 主 Agent 派活 | 任务路由 |
| Pipeline | 串行流水线 | 阶段加工 |
| Debate | 辩论收敛 | 高质量决策 |
| GroupChat | 群聊调度 | 开放讨论 |

### 失败模式速查

| 模式 | 症状 | 对策 |
|------|------|------|
| 死循环 | 反复同一步 | 最大步数+重复检测 |
| 幻觉工具 | 调不存在的工具 | 工具白名单+Schema 校验 |
| 参数幻觉 | 编造参数值 | 强校验+拒绝执行 |
| 过早放弃 | 浅尝辄止 | Prompt 引导+重试策略 |
| 成本爆炸 | 步数失控 | 预算硬顶+监控告警 |

---

## 后续板块

本板块完成后，可自然衔接：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **多模态** | 多模态工具扩展 Agent 的感知与行动 |
| **LLM 应用架构** | Agent 是应用架构中的执行层 |
| **MCP** | 标准化工具协议，让工具生态复用 |
| **微调/评估** | 针对工具调用场景的模型优化 |
| **工程化部署** | Agent 服务的大规模运维 |

---

## 学习资源补充

> 以下为经典论文与官方资源，遇到疑问时优先查阅

- [ReAct 论文](https://arxiv.org/abs/2210.03629) - Reasoning + Acting 协同范式
- [Toolformer](https://arxiv.org/abs/2302.04761) - 模型自主学习用工具
- [Reflexion](https://arxiv.org/abs/2303.11366) - 自我反思与纠错
- [Plan-and-Solve](https://arxiv.org/abs/2305.04091) - 规划式 Prompt
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/) - Agent 编排框架对照

---

## 贡献与反馈

本学习手册为原创内容，参考公开论文与官方文档的组织思想但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，让你的 Agent 从"会说"进化到"会做"！**
