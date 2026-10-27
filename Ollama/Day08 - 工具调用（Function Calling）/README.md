# Day08 - 工具调用（Function Calling）

> 让本地模型"不只是说话，还能动手"：给它定义工具（函数），模型在需要时生成"我要调用 get_weather(city=北京)"这样的结构化指令，你执行后把结果喂回模型，完成封闭循环。这就是 Agent 的核心一环。

---

## 目录

- [为什么需要工具调用](#为什么需要工具调用)
- [核心概念](#核心概念)
- [今日学习目标](#今日学习目标)
- [示例项目演进](#示例项目演进)
- [每日内容详解](#每日内容详解)
- [练习与挑战](#练习与挑战)
- [运行代码](#运行代码)
- [知识点速查](#知识点速查)

---

## 为什么需要工具调用

纯 LLM 只能"生成文本"，无法查实时天气、查订单库、算数字。工具调用（Function Calling / Tool Use）让模型**声明它需要调用哪个函数、传什么参数**，由你的代码真正执行，再把结果拼回对话。于是模型**能做事了**。

| 没有工具 | 有工具 |
|---------|--------|
| 只会"回答" | 会"查/算/执行" |
| 数据过时 | 实时读取 |
| 无法接入系统 | 调用内部 API |
| Agent 无从谈起 | Agent 的"手" ★ |

---

## 核心概念

- **tools 参数**：把工具 JSON Schema（type/function/name/description/parameters）随请求传给 `/api/chat`。
- **tool_calls**：模型返回的"调用意图"，含 `function.name` 和 `function.arguments`（JSON 字符串）。
- **执行层**：你的代码按 name 调用真实函数，得到结果。
- **回合追加**：把"用户请求 + 模型tool_calls + 工具结果"追加回 messages，再让模型总结。
- **多工具**：注册多个工具，由模型按需挑选。
- **工具型 Agent**：循环「模型要工具→执行→结果回传→模型再决策」直到完成。

---

## 今日学习目标

- 写出符合 Ollama/OpenAI 范式的工具 Schema
- 完成一次「模型请求工具 → 我方执行 → 结果回传」往返
- 注册并调度多个工具
- 封装一个最小可用的**工具型 Agent**（真实/模拟双模式）

---

## 示例项目演进

为客服 AgentLee 加"双手"：能查天气、能查订单、能算数，从而真正处理用户诉求。

| 阶段 | Day08 体现 |
|------|-----------|
| 定义工具 | `01_tool_schema.py` 写 Schema |
| 一次往返 | `02_function_calling.py` 请求→执行→回传 |
| 多工具 | `03_multi_tool.py` 按需调度 |
| 工具 Agent | `04_tool_agent.py` 循环直到完成 |

---

## 每日内容详解

### 01 - 工具 Schema
拆解一个 function 需要哪些字段（name/description/parameters/required），以及为什么 description 要写清。

### 02 - Function Calling 往返
完整演示：发带 tools 的请求 → 模型说"我要调 get_weather(北京)" → 我方查得 25℃ → 拼回 messages → 模型给最终答复。

### 03 - 多工具调度
注册 get_weather / get_order / add 三个工具，模型依据用户意图挑选对应工具。

### 04 - 工具型 Agent
封装成循环：解析 tool_calls、执行、回传、直到模型不再要工具。真实环境走真实模型，无环境用规则模拟"想调工具"的意图。

---

## 练习与挑战

1. **新增工具**：定义 `get_stock_price(code)` 并接入多工具调度。
2. **参数校验**：模型给的 arguments 非法时如何处理（重试/报错）。
3. **链式调用**：让模型"先查订单，再根据结果申请退款"两步工具。
4. **真实验证**：用 `qwen2.5:7b`（支持 tools）拉真实 Oracle 往返。

---

## 运行代码

```bash
python "Day08 - 工具调用（Function Calling）/Code/01_tool_schema.py"
python "Day08 - 工具调用（Function Calling）/Code/02_function_calling.py"
python "Day08 - 工具调用（Function Calling）/Code/03_multi_tool.py"
python "Day08 - 工具调用（Function Calling）/Code/04_tool_agent.py"
```

> 无支持 tools 的模型时，用规则模拟"模型想调工具"的意图，结构和流程照常演示。

---

## 知识点速查

| 项 | 说明 |
|----|------|
| tools 字段 | 传递给模型的函数 JSON Schema |
| tool_calls | 模型返回的调用意图（name + arguments） |
| 支持 tools 的模型 | qwen2.5、llama3.1、mistral 等 |
| 往返步骤 | 请求→tool_calls→执行→结果回传→总结 |
| 多工具 | 一个 tools 数组里注册多个函数 |
| 工具 Agent | 循环执行，直到模型不再调用工具 |
| 与 Agent 板块 | 本日内容对应 Agent Day03 的 Tool Calling |