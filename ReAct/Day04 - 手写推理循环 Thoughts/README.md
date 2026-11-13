# Day04 - 手写推理循环 Thoughts

> 本章节进入 ReAct 的心脏：**Thought 推理循环**。我们用「纯文本协议」手写一个最小 ReAct **循环机械**——每一次迭代都让 LLM 生成思考，解析它下一步要做什么，并在循环里维护历史、做终止判断与最大轮次保护。

---

## 目录

- [一、学习目标](#一学习目标）
- [二、理论知识](#二理论知识）
  - [2.1 循环机械长什么样](#21-循环机械长什么样）
  - [2.2 纯文本 ReAct 协议](#22-纯文本-react-协议）
  - [2.3 解析 LLM 输出](#23-解析-llm-输出）
  - [2.4 维护轨迹(历史)](#24-维护轨迹历史)
  - [2.5 终止条件与最大轮次](#25-终止条件与最大轮次）
- [三、核心概念解析](#三核心概念解析）
  - [3.1 Thought 的作用](#31-thought-的作用）
  - [3.2 为什么需要解析协议](#32-为什么需要解析协议）
  - [3.3 最大轮次是成本闸门](#33-最大轮次是成本闸门）
- [四、关键知识点总结](#四关键知识点总结）
- [五、实战练习](#五实战练习）

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **写出 ReAct 的最小 while 循环**。
2. **定义四种解析 Token（Thought/Action/Action Input）。**
3. **用 MockLLM 推动循环并把轨迹喂回历史**。
4. **实现最大轮次与终止判定**。
5. **体会到「思考」如何驱动下一步**。

---

## 二、理论知识

### 2.1 循环机械长什么样

如果没有模型内部的 tool-calling，最朴素的做法是**纯文本协议**：让模型按固定格式 `Thought:/Action:/Action Input:` 输出，程序解析，执行后把结果以 `Observation:` 追加回去，再让模型继续。

```
while steps < max_steps:
    reply = llm.chat(history)        # 生成 Thought(+可选的 Action)
    history.append(reply)
    if reply 含 Action:
        obs = execute(action)        # （Day05 完整实现）
        history.append({"role": tool/obs})
        continue
    else:
        return reply.text            # 终止
```

### 2.2 纯文本 ReAct 协议

在系统提示里规定固定格式，让模型「结构化地思考」：

```
Thought: <你的推理>
Action: 要调用的工具
Action Input: {"key": "val"}
Observation: <工具返回>          (程序追加)
Thought: <继续...>
...
Thought: 任务完成
Final Answer: <最终回答>           (终止)
```

### 2.3 解析 LLM 输出

直接把模型文本拆成片段：

```python
for line in reply.splitlines():
    if line.startswith("Thought:")   : thought.append(line)
    elif line.startswith("Action:")  : action = ...
    elif line.startswith("Action Input:"): args = json.loads(...)
    elif line.startswith("Final Answer:"): final = ...
```

稳妥起见用**逐行扫描**，容忍多余换行。解析后把「Observation」追加到历史里，循环继续。

### 2.4 维护轨迹(历史)

每次迭代的 `Thought`/`Action` 都要**追加回历史**，模型下一轮才能看到自己上一步说了什么、观察到了什么。这就是 ReAct 的记忆来源。

### 2.5 终止条件与最大轮次

- 出现 `Final Answer:` → 返回并结束。
- 达到 **max_steps**（如 8）→ 强制终止，提示"已达最大轮次"。
- 两者缺一，模型可能死循环 → 最大轮次是**成本和稳定性闸门**，工程上必加。

```python
for _ in range(max_steps):
    ...
    if final: return final
return "(Agent 达到最大轮次, 未完成)"
```

---

## 三、核心概念解析

### 3.1 Thought 的作用

Thought 让模型「先想后做」：总结已有 Observation、判断缺口、定下一步。它是 CoT 在 ReAct 里的体现，也让轨迹可审计。

### 3.2 为什么需要解析协议

机器要能**可靠地把模型自由文本变成可执行的结构**。纯文本协议在非 tool-calling 模型（本地/开源）上通用；有 tool-calling 的模型可用原生结构（Day05），更稳。

### 3.3 最大轮次是成本闸门

每多一轮 = 多一次模型调用 = 多花 token。ReAct 必须限制步数，兼顾完成率与成本/时延。

---

## 四、关键知识点总结

- **ReAct 循环 = 生成 Thought → 解析 Action → (执行) → 观察 → 再循环**。
- **纯文本协议**用 `Thought/Action/Action Input/Observation/Final Answer` 标记。
- **历史必须回填**，模型才能推进。
- **max_steps 是防死循环的必要闸门**。

---

## 五、实战练习

### 练习一：01-thought-loop.py —— 手写 Thought 循环

**任务描述**：用文本协议让 MockLLM 逐步生成 Thought/Action，并在循环里维护历史与观察。无 Key 离线可跑。

**运行方式**

```bash
python "Day04 - 手写推理循环 Thoughts/Code/01-thought-loop.py"
```

### 练习二：02-max-steps.py —— 终止与最大轮次

**任务描述**：故意让模型「不停调用工具」，演示 max_steps 兜底并给出提示。

**运行方式**

```bash
python "Day04 - 手写推理循环 Thoughts/Code/02-max-steps.py"
```

### 练习三：尝试

把「多个 Action 合并成一次并行调用」或「加入 Final Answer 检测正则」，改造成你自己的循环。

---

## 下节预告

下一节 **Day05** 进入 **Action 执行与工具调用**：把 Thought 解析出的 Action 真正执行（复用 Day03 注册表），再把 Observation 完美衔接——形成完整 ReAct 闭环，并对比原生 `tool_calls` 实现。