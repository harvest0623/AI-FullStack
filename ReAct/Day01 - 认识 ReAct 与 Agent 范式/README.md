# Day01 - 认识 ReAct 与 Agent 范式

> 本章节建立 ReAct 的整体认知。理解 Agent 是什么、ReAct（Reasoning + Acting）的核心思想，掌握 Thought / Action / Observation 这个最关键的三角循环，并理解它与「一次性指令」「思维链 CoT」的根本区别。

---

## 目录

- [一、学习目标](#一学习目标）
- [二、理论知识](#二理论知识）
  - [2.1 什么是 AI Agent](#21-什么是-ai-agent）
  - [2.2 Who is ReAct](#22-who-is-react）
  - [2.3 Thought / Action / Observation](#23-thought--action--observation）
  - [2.4 ReAct vs Chain vs CoT](#24-react-vs-chain-vs-cot）
  - [2.5 为什么 ReAct 有效](#25-为什么-react-有效）
- [三、核心概念解析](#三核心概念解析）
  - [3.1 一次完整 ReAct 轨迹](#31-一次完整-react-轨迹）
  - [3.2 何时终止](#32-何时终止）
  - [3.3 与 Tool Calling 的关系](#33-与-tool-calling-的关系）
- [四、关键知识点总结](#四关键知识点总结）
- [五、实战练习](#五实战练习）

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **说清 Agent 与普通 LLM 调用的区别**。
2. **画出 ReAct 的三角循环**。
3. **识别一次对话中的 Thought / Action / Observation**。
4. **解释 ReAct 相比一次性指令、CoT 的优势**。

---

## 二、理论知识

### 2.1 什么是 AI Agent

**Agent（智能体）** 是能**自主决策并行动**的程序：它不止回答，还会调用工具、观察结果、调整策略，直到完成目标。

| 普通 LLM 调用 | AI Agent |
| --- | --- |
| 一问一答 | 多步推理与行动 |
| 无外部能力 | 可调工具/API/搜索 |
| 一次性 | 循环迭代直到完成 |
| 无状态 | 有记忆与上下文 |

Agent = **大脑（LLM 决策）+ 手脚（工具）+ 记忆（上下文）**。

### 2.2 ReAct

**ReAct** = **Rea**soning + **A**cting，由 Yao et al.（2022, Princeton & Google）提出。核心主张：**让语言模型「交替进行思考和行动」**，思考指导行动，行动的结果（观察）再喂回思考，形成闭环。

> 一句话：**想一步 → 走一步 → 看一眼 → 再想一步…**直到任务完成。

### 2.3 Thought / Action / Observation

ReAct 把每一步拆成三个片段：

- **Thought（思考）**：模型推理，解释当前理解与下一步计划。例如「我需要先知道今天天气，再决定穿搭」。
- **Action（行动）**：明确要执行的工具与参数。例如 `Action: search_weather(city="杭州")`。
- **Observation（观察）**：工具真实返回的结果，作为下一轮 Thought 的输入。例如 `Observation: 杭州今天 25℃ 多云`。

```
Thought: 用户想知道明天是否下雨, 我需要查天气
Action: search_weather(city="成都", date="2026-09-23")
Observation: 成都 2026-09-23 小雨 18~22℃
Thought: 有雨, 应提醒用户带伞, 问题已解决
Action: finish(answer="明天成都下雨, 建议带伞")
```

### 2.4 ReAct vs Chain vs CoT

- **Chain（管线）**：把过程写成死脚本 `A → B → C`，固定不可变。
- **CoT（思维链）**：让模型「多想几步」再回答，但**没有工具、没有外部反馈**。
- **ReAct**：在 CoT 基础上**加入 Action + Observation**，既能推理又能与环境交互、自我纠错。

| | CoT | ReAct |
| --- | --- | --- |
| 思考 | ✅ | ✅ |
| 行动工具 | ❌ | ✅ |
| 观察反馈 | ❌ | ✅ |
| 自我纠错 | 弱 | 强 |

### 2.5 为什么 ReAct 有效

1. **可交互**：能调用外部工具，突破模型知识截止。
2. **可观察**：Observation 提供事实锚点，减少幻觉。
3. **可纠错**：行动失败可在下一轮 Thought 修正重试。
4. **可解释**：Thought 轨迹可审计，便于调试与审查。

---

## 三、核心概念解析

### 3.1 一次完整 ReAct 轨迹

一次任务通常含多轮 `Thought → Action → Observation`，最后以「明确回答」或「停止调用工具」终止。每条轨迹形成一个可审查的推理痕迹。

### 3.2 何时终止

- 达成目标，输出最终答案。
- 达到**最大轮次**（防死循环，工程上必须）。
- 连续多次行动失败，选择放弃或兜底回答。

### 3.3 与 Tool Calling 的关系

**Tool Calling / Function Calling** 是模型**原生输出结构化工具调用**的接口（如 OpenAI 的 `tool_calls`）。ReAct 是一种「范式/策略」，二者可叠加：用 Tool Calling 承载 Action 的机器可解析表达，是最现代的 ReAct 落地方式（Day03-05 会讲）。

---

## 四、关键知识点总结

- **Agent = 大脑 + 手脚 + 记忆**。
- **ReAct = 推理 + 行动** 的交替闭环。
- **Thought / Action / Observation** 是最小循环单元。
- ReAct 与 CoT 的区别在于**有工具和反馈**。
- 工程上必须有**终止条件（最大轮次）**。

---

## 五、实战练习

### 练习一：01-narrate-react.py —— 文字版 ReAct 演示

**任务描述**：用「旅行规划」示例，把一次 ReAct 轨迹逐步打印并注释，感受循环节拍。无需 API。

**运行方式**

```bash
python "Day01 - 认识 ReAct 与 Agent 范式/Code/01-narrate-react.py"
```

### 练习二：思考题

看下面三段文本，标出哪些是 Thought、Action、Observation，并分析下一轮会怎么做：

```
用户: 帮我比较两款手机的电池容量
A1: 我需要查这两款手机的电池数据
A2: action: phone_spec("X")
A3: X: 4500mAh, Y: 5000mAh
```

### 练习三：尝试

用自己的日常问题（如「今晚吃什么」）手写一个 3 轮的 ReAct 轨迹，标出每一环。

---

## 下节预告

下一节 **Day02** 进入工程实现：安装依赖、封装「统一 LLM 客户端」，并内置 **MockLLM** 让后续章节**无 API Key 也能运行**。