# Day02 - Agent核心循环与ReAct模式

> Agent 的心脏：徒手实现「感知-思考-行动-观察」核心循环与 ReAct 三元组，掌握终止条件防失控，并学会用轨迹（Trajectory）记录与回放 Agent 的一举一动。

---

## 一、今日目标

学完本天，你将能够：

- 徒手实现一个**最小 Agent 循环**（不依赖任何框架）
- 理解并实现 **ReAct 三元组**：Thought / Action / Observation
- 设计**终止条件**：完成 / 最大步数 / 重复检测，防止 Agent 失控
- 用**轨迹（Trajectory）** 记录、导出与回放 Agent 运行过程
- 理解循环中的**上下文增长问题**及其对策

---

## 二、核心循环：Agent 的心跳

所有 Agent 框架（LangChain 的 AgentExecutor、LangGraph 的 StateGraph）剥开外壳，都是同一个循环：

```
while not done:
    perception   = 感知（拼接：目标 + 历史 + 最近观察）
    decision     = 思考（LLM 或规则，决定下一步）
    if decision is 最终答案:
        done = True
    else:
        observation = 行动（执行工具）
        记录 (decision, observation) 到轨迹
return 最终答案
```

四个环节：

| 环节 | 输入 | 输出 | 类比 |
|------|------|------|------|
| 感知 Perception | 目标 + 历史轨迹 + 观察结果 | 组装好的上下文 | 眼睛 |
| 思考 Thought | 上下文 | 决策（用工具 or 直答） | 大脑 |
| 行动 Action | 工具名 + 参数 | 执行结果 | 双手 |
| 观察 Observation | 执行结果 | 文本化反馈（回填上下文） | 反馈 |

---

## 三、ReAct：推理与行动协同

### 3.1 三元组

ReAct（Reasoning + Acting）让模型在每一步**显式写下推理**，再行动：

```
Thought: 我需要先知道上周的销量，才能回答涨跌问题。
Action: query_sales
Action Input: {"week": "2024-W02"}
Observation: {"sales": 980, "orders": 290}
Thought: 有本周数据了，但"涨跌"需要基线对比，再查上周。
Action: query_sales
Action Input: {"week": "2024-W01"}
Observation: {"sales": 1200, "orders": 340}
Thought: 980 vs 1200，下跌 18.3%，可以回答了。
Final Answer: 上周销量下跌了 18.3%。
```

### 3.2 为什么显式 Thought 有用

1. **可解释**：人能看懂"为什么走这条路"
2. **可调试**：出错时能定位是哪步推理歪了
3. **更准**：先写推理再选动作，减少冲动型错误（CoT 效应）
4. **可评估**：轨迹成为评估的数据基础

### 3.3 ReAct vs 仅 Acting

| 模式 | 过程 | 问题 |
|------|------|------|
| 仅 Acting | 直接 Action→Observation→Action… | 错误会累积且无人知道为什么 |
| ReAct | Thought→Action→Observation… | 每步有"为什么"，错误可发现可纠正 |

---

## 四、终止条件：给 Agent 上缰绳

Agent 是循环，**循环就必须有出口**，否则就是死循环烧钱。四种出口：

| 条件 | 触发 | 行为 |
|------|------|------|
| **正常完成** | LLM 输出 Final Answer | 返回答案，退出 |
| **最大步数** | step >= max_steps | 截断，返回"已达上限"及当前进展 |
| **重复检测** | 连续相同 Action+参数 | 提示 LLM 换思路，或直接终止 |
| **致命错误** | 工具连续失败 / 预算耗尽 | 快速失败，上报 |

> **工程红线**：`max_steps` 永远要设。一个没上限的 Agent 循环，就是一个可能烧掉预算的 while True。

### 上下文增长问题

每轮循环都往上下文追加 Thought/Action/Observation：
- 步数越多 → 上下文越长 → 响应越慢越贵 → 还可能超出窗口
- 对策：观察结果**截断**（只保留关键部分）、历史**摘要**（Day04 记忆系统）、步数**预算**（Day06 成本控制）

---

## 五、轨迹（Trajectory）

轨迹 = `[(step, thought, action, observation), ...]`，是 Agent 的"黑匣子"：

- **调试**：失败时逐步重放找根因（Day07）
- **评估**：成功率、步数效率、成本的基础数据（Day07）
- **审计**：生产合规必须留存（Day09/10）
- **回放**：离线重现某次运行（可复现性）

工程上建议：轨迹落盘（JSONL），每步含时间戳、耗时、token 数。

---

## 六、代码实战

| 文件 | 内容 | 运行 |
|------|------|------|
| `01_core_loop.py` | 最小 Agent 循环（约 60 行，五脏俱全） | `python 01_core_loop.py` |
| `02_react_pattern.py` | 完整 ReAct：Thought/Action/Observation 三元组 | `python 02_react_pattern.py` |
| `03_stop_conditions.py` | 四种终止条件演示（含失控 Agent 被拦下） | `python 03_stop_conditions.py` |
| `04_trajectory.py` | 轨迹记录、导出 JSONL、结构化回放 | `python 04_trajectory.py` |
| `README.md` | 运行说明与要点回顾 | - |

> 本天"思考"环节用规则模拟（SimBrain）；Day03 将替换为与真实 LLM 对齐的决策接口。

---

## 七、今日思考题

1. 如果去掉循环、只允许 Agent 执行一步，哪些任务还能做？这说明 Agent 的价值本质来自哪里？
2. 重复检测为什么不能只比较"工具名"，必须比较"工具名+参数"？
3. 上下文无限增长时，最先崩的是什么（窗口/成本/延迟）？分别怎么缓解？
4. 轨迹里如果只存 Action 不存 Thought，会损失什么能力？

---

## 八、资源补充

- [ReAct 论文](https://arxiv.org/abs/2210.03629) - 本天核心来源
- [Chain-of-Thought](https://arxiv.org/abs/2201.11903) - Thought 有效性的理论基础
- [LangGraph](https://langchain-ai.github.io/langgraph/) - 对照：框架如何封装这个循环

---

## 九、小结

- **核心循环**是所有 Agent 的心跳：感知→思考→行动→观察，直到达成目标
- **ReAct** 用显式 Thought 把"为什么"写进轨迹：可解释、可调试、可评估
- **终止条件**是缰绳：max_steps 必设，重复检测防打转
- **轨迹**是黑匣子：调试、评估、审计全靠它

**今日金句**：循环给 Agent 生命，终止条件给 Agent 边界，轨迹给 Agent 透明。