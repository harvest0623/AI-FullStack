# ReAct 全栈学习指南

> 系统化掌握 **ReAct（Reasoning + Acting）**——2022 年被提出的 AI Agent 核心范式。本板块带你从零手写一个可运行的 ReAct 推理循环，逐步加入工具、记忆、错误处理、流式与多工具，最终落地一个能检索/计算的实用 AI 助手 Agent，并接入 OpenAI 兼容接口。
>
> 共 10 天，覆盖 ReAct 原理与工程化实践；全部脚本**无需 API Key** 也能离线跑通（内置 Mock LLM 模拟）。

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是 AI 全栈系列的**智能体（Agent）核心**。ReAct 让大模型不再只是「一问一答」，而是能**推理（Thought）→ 行动（Action）→ 观察（Observation）**，反复迭代直到完成任务。

对 AI 全栈工程师，ReAct 是理解一切 Agent（AutoGPT、LangGraph、Manus、CrewAI 等）的地基：

- 让 LLM 决定「何时调用工具、调哪个工具、传什么参数」
- 用环境反馈（Observation）驱动多步推理
- 把外部能力（搜索、计算、数据库、Web）接进对话
- 是 Tool Calling、Function Call、Agentic Loop 的底层模型

**学习目标**：完成本板块后，你应能：
- 说清 ReAct 的 Thought/Action/Observation 循环
- 手写一个最小 ReAct 代理循环
- 定义并注册工具（参数 schema、执行、错误兜底）
- 用 OpenAI 兼容接口（原生 tool calling）实现 ReAct
- 加入记忆、重试、流式、并行工具调用
- 组装一个多工具实用 Agent 并做简单评估

**设计原则**：
- 从**手写循环**开始，避免「黑盒一行代码」，理解本质
- 每章理论 + 可运行脚本 + 实战练习
- 提供 `MockLLM`，**无 API Key 也能跑**；有 KEY 时自动切真模型
- 紧扣生产：工具异常、上下文、最大轮次、成本控制

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| Python | 熟练 | 类型注解、装饰器、面向对象 |
| LLM 基础 | 了解 | prompt、system/user 消息、温度 |
| HTTP | 了解 | `httpx` / `requests` 调用 API |

**环境准备**：

```bash
pip install openai httpx
# 可选真实模型(需 KEY): export OPENAI_API_KEY=sk-...
```

---代码仅依赖 `openai` 与 `httpx`；不装 langgraph/langchain，避免黑盒。

---

## 学习路线图

```markdown
阶段一：理解与最小循环（Day01-05）
  Day01 什么是 ReAct → Day02 LLM 封装 → Day03 工具定义
      → Day04 Thought 推理 → Day05 Action 执行循环

阶段二：进化与工程（Day06-08）
  Day06 记忆/上下文 → Day07 错误与重试 → Day08 流式与并行

阶段三：实战（Day09-10）
  Day09 多工具 Agent → Day10 实用助手 + 评估
```

---

## 每日内容详表

#### Day01 - 认识 ReAct 与 Agent 范式
- **核心**：Agent 概念、ReAct 论文思想、Thought/Action/Observation、与 Chain/COT 的区别
- **代码**：模拟一次 ReAct 的文字版交互

#### Day02 - 环境与 LLM 调用封装
- **核心**：openai 兼容接口、`chat.completions`、消息结构、MockLLM 与真实 LLM 切换
- **代码**：`llm.py` 统一封装 + 测试

#### Day03 - 工具定义与注册
- **核心**：工具 schema、`tools` 参数、JSON 参数校验、工具注册表
- **代码**：定义计算/查找工具并注册，`model_json_schema` 生成参数

#### Day04 - 手写推理循环 Thought
- **核心**：从零手写 `think`，让 LLM 决定下一步；终止条件、最大轮次
- **代码**：纯 prompt 的文本 ReAct（无 tool schema）

#### Day05 - 行动执行 Action 与工具调用
- **核心**：将 Thought 转为 Action，执行工具，把 Observation 喂回循环
- **代码**：完整「推理→行动→观察」循环（文本协议 + tool calling 两版）

#### Day06 - 记忆与上下文管理
- **核心**：对话历史、`ConversationBufferMemory`、窗口截断、总结压缩
- **代码**：记忆装箱、token 预算、长对话压缩

#### Day07 - 错误处理与重试
- **核心**：工具抛错、非法 JSON、调用次数限制、优雅降级
- **代码**：把异常塞回 Observation 让 LLM 自纠，+ 重试策略

#### Day08 - 流式输出与并行工具调用
- **核心**：SSE 流式 token、并行 `tool_calls`、合并多工具结果
- **代码**：流式输出助手 + 并行调两个工具

#### Day09 - 多工具复杂 Agent
- **核心**：搜索/计算/数据库/Web 等多工具编排、工具冲突与优先级
- **代码**：三工具 Agent 完成任务

#### Day10 - 实战 AI 助手与评估
- **核心**：组装可用助手，加日志、成本统计；正确率/轮次等简单评估
- **代码**：`agent.py` 完整助手 + 评测脚本

---

## 目录结构

```markdown
ReAct/
├── README.md                    # 本板块总纲
├── Day01 - 认识 ReAct 与 Agent 范式/
│   ├── README.md
│   └── Code/
│       ├── 01-narrate-react.py
│       └── ...
├── Day02 - 环境与 LLM 调用封装/
│   └── ...
└── Day10 - AI 助手与评估/
    └── ...
```

每个 `DayXX` 含 **README.md**（当天讲解）与 **Code/**（可运行脚本）。

---

## 学习建议

1. **先把 Day04 手写循环跑通**，理解「LLM 决策 + 环境反馈」这一动力学。
2. **本地用 MockLLM**：`MOCK=true` 或未设 KEY 时脚本自动走模拟，便于观察轨迹。
3. **开 trace**：打印每一步 Thought/Action/Observation，看 ReAct 如何收敛。
4. **有 KEY 时**：脚本会自动用真实模型，对比真实效果。
5. **多动手改工具**：加一个自己的工具，观察 Agent 决策变化。

---

## 如何运行代码

```bash
cd ReAct
python "Day01 - 认识 ReAct 与 Agent 范式/Code/01-narrate-react.py"
```

脚本默认离线运行；设置 `OPENAI_API_KEY` 或显式传 LLM 实例即可切换到真实模型。

---

## 知识点速查

| 主题 | 一句话速记 |
|------|-----------|
| ReAct | Reasoning + Acting，推理与行动交替 |
| Thought | LLM 的思考步骤，决定下一步 |
| Action | 调用某个工具/动作 |
| Observation | 工具/环境返回的结果，喂回 LLM |
| Tool | 具名 + 参数 schema + 执行函数的集合 |
| tool_calling | 模型原生输出结构化工具调用 |
| 最大轮次 | 防止死循环的成本闸门 |
| Memory | 对话历史/记忆装箱/窗口截断 |
| Streaming | SSE 逐 token 输出 |
| 并行工具 | 一次返回多个 tool_calls 并行执行 |

---

## 后续板块

- **LangGraph**：用图状态机编排 ReAct Agent（可在学习本板块后接入）
- **FastAPI + Agent**：把 ReAct 封装成可调用的 API
- **多 Agent 协作**：规划者/执行者分工
- **RAG + ReAct**：给 Agent 接检索增强

各板块相互独立，可按需跳读。