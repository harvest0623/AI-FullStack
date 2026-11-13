# Day05 - Action 执行与工具调用

> 本章节闭合 ReAct 的最后一环：把 Thought 解析出的 **Action 真正执行**，并把结果以 **Observation** 喂回循环。基于 Day03 的注册表做 Action 执行，并演示**原生 `tool_calls`** 这种更稳健、结构化程度更高的落地方式。

---

## 目录

- [一、学习目标](#一学习目标）
- [二、理论知识](#二理论知识）
  - [2.1 从 Thought 到 Action](#21-从-thought-到-action）
  - [2.2 用注册表执行 Action](#22-用注册表执行-action）
  - [2.3 Observation 回填协议](#23-observation-回填协议）
  - [2.4 原生 tool_calls 方式](#24-原生-tool_calls-方式）
  - [2.5 两种实现对比](#25-两种实现对比）
- [三、核心概念解析](#三核心概念解析）
  - [3.1 执行边界与异常](#31-执行边界与异常）
  - [3.2 tool message 的 role 约定](#32-tool-message-的-role-约定）
  - [3.3 何时只用文本协议](#33-何时只用文本协议）
- [四、关键知识点总结](#四关键知识点总结）
- [五、实战练习](#五实战练习）

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **把 Action 翻译成注册表执行调用**。
2. **把工具结果正确地以 Observation/tool 回填**。
3. **用原生 `tool_calls` 实现更稳的 ReAct**。
4. **区分文本协议与 tool_calls 的取舍**。
5. **跑通一个完整闭环并对最终答案收尾**。

---

## 二、理论知识

### 2.1 从 Thought 到 Action

在 Day04 我们解析出 `Action: name` 和 `Action Input: {...}`。这一步只是「意图」，**执行**要交给注册表：

```
Action  name = square, args = {"x": 12}
   ↓
reg.execute("square", x=12)   →  144
   ↓
Observation: 144  (回填历史)
```

### 2.2 用注册表执行 Action

```python
tool = reg.get(action_name)          # 找到 Tool
if tool is None:
    obs = f"错误: 没有名为 {action_name} 的工具"   # 反馈给模型自纠
else:
    obs = tool.run(**args)
history.append({"role": "tool", "content": str(obs)})
```

找不到工具时，把错误也作为 Observation 喂回，模型会修正再试。

### 2.3 Observation 回填协议

在文本协议里，Observation 是程序追加的一条消息，下一轮模型能读到：

```
user: 计算 12 的平方
...assistant: Thought / Action...
tool: square(12) = 144
...assistant: Thought / Final Answer...
```

### 2.4 原生 tool_calls 方式

现代模型（GPT/Claude/DeepSeek 等）能**原生返回结构化工具调用**，无需解析文本：

```python
resp = llm.chat(messages, tools=reg.openai_tools())
for tc in resp["tool_calls"]:
    result = reg.execute(tc["name"], **tc["arguments"])
    messages.append({"role": "tool", "tool_call_id": ..., "content": str(result)})
```

模型端到端地输出 `name + arguments(JSON)`，比正则解析文本可靠得多。

### 2.5 两种实现对比

| | 文本协议 | 原生 tool_calls |
| --- | --- | --- |
| 兼容模型 | 几乎全部 | 需支持 tool 的模型 |
| 解析稳定性 | 用正则, 较弱 | 结构化, 强 |
| 并行调用 | 需自写规则 | 原生支持(tool_calls 数组) |
| 维护成本 | 高 | 低 |

**结论**：能用 tool_calls 就用 tool_calls；文本协议适合不支持该能力的大模型/教学理解。

---

## 三、核心概念解析

### 3.1 执行边界与异常

工具执行要包 `try/except`：参数错、超时、权限异常都应作为 Observation 回传（Day07 完善），而不是让循环崩溃。

### 3.2 tool message 的 role 约定

真实 OpenAI 每次 tool_calls 要带 `tool_call_id` 关联；文本协议可用一个累积 `tool_calls_map` 管理。Mock 场景用 `role="tool"` + content 即可。

### 3.3 何时只用文本协议

- 无法访问原生 tool 能力（某些本地/自托管模型）。
- 需要最大兼容、或不希望依赖厂商扩展。
- 仅作学习/调试：把协议打出来看。

---

## 四、关键知识点总结

- **Action → `reg.execute(name, **args)`** 执行工具。
- **Observation/tool** 回填历史，驱动下一轮 Thought。
- **找不到工具** 时反馈错误让模型自纠。
- **原生 tool_calls** 更结构化、更稳，优先使用。
- **工具执行要包异常边界**。

---

## 五、实战练习

### 练习一：01-action-execute.py —— 文本协议执行

**任务描述**：用 Day03 注册表执行 Action，把 result 回填 Observation，完成一个「计算+换算」闭环。

**运行方式**

```bash
python "Day05 - Action 执行与工具调用/Code/01-action-execute.py"
```

### 练习二：02-native-toolcalls.py —— 原生 tool_calls

**任务描述**：用 llm.chat(..., tools=...) 走原生 tool_calls 循环（Mock 演示 + 真实可选）。

**运行方式**

```bash
python "Day05 - Action 执行与工具调用/Code/02-native-toolcalls.py"
```

### 练习三：尝试

给 Agent 加一个 `unknown` 工具的输入，观察它如何通过错误 Observation 自纠，并把该逻辑固化为 `retry(n)`。

---

## 下节预告

下一节 **Day06** 进入 **记忆与上下文管理**：对话历史、记忆装箱、token 预算与窗口截断，解决长任务的上下文爆炸。