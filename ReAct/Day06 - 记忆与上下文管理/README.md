# Day06 - 记忆与上下文管理

> 本章节解决长任务的上下文爆炸。ReAct 每次调用都要把历史拷给模型，历史越长 token 越贵、效果越差。理解对话历史、`ConversationBufferMemory`、窗口截断与总结压缩，让 Agent 在长对话中稳定工作。

---

## 目录

- [一、学习目标](#一学习目标）
- [二、理论知识](#二理论知识）
  - [2.1 为什么"记忆"重要](#21-为什么记忆重要）
  - [2.2 全量历史的问题](#22-全量历史的问题）
  - [2.3 记忆装箱 ConversationBufferMemory](#23-记忆装箱-conversationbuffermemory）
  - [2.4 Token 预算与窗口截断](#24-token-预算与窗口截断）
  - [2.5 总结压缩 Summarization](#25-总结压缩-summarization）
  - [2.6 结构化记忆(键值/工具结果缓存)](#26-结构化记忆键值工具结果缓存)
- [三、核心概念解析](#三核心概念解析）
  - [3.1 三档记忆策略](#31-三档记忆策略）
  - [3.2 截断 vs 总结的取舍](#32-截断-vs-总结的取舍）
  - [3.3 工具结果也要记忆](#33-工具结果也要记忆）
- [四、关键知识点总结](#四关键知识点总结）
- [五、实战练习](#五实战练习）

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **用记忆装箱管理多轮对话**。
2. **估算 token 并做窗口截断**。
3. **用 LLM 生成摘要来压缩旧上下文**。
4. **缓存工具结果避免重复开销**。
5. **为长任务设计记忆策略**。

---

## 二、理论知识

### 2.1 为什么"记忆"重要

Agent 需要记住用户说过的话、自己做过的行动、工具返回的结果，才能连贯推进。**记忆 = 上下文（messages）**。

### 2.2 全量历史的问题

把所有历史一次全塞给模型：

- **成本**：token 越多越贵，每轮都重复发送。
- **窗口**：超过模型上下文被截断，早期内容丢失。
- **效果**：无关噪音稀释焦点，模型易跑偏。

### 2.3 记忆装箱 ConversationBufferMemory

按「会话」组织历史，并提供交互接口（追加、取回）：

```python
class ConversationBufferMemory:
    def __init__(self): self.messages = []
    def add_user(self, content): self.messages.append({"role": "user", "content": content})
    def add_ai(self, content):   self.messages.append({"role": "assistant", "content": content})
    def add_tool(self, content, id=None): ...
    def as_messages(self): return self.messages
```

### 2.4 Token 预算与窗口截断

给「max_context」设上限，超了就**丢弃最旧的非系统消息**：

```python
def trim(memory, max_tokens, token_counter):
    while estimate(memory.messages) > max_tokens:
        # 从最旧的非 system 消息开始丢
        memory.drop_oldest()
```

用简单 `len(text)/4` 估算 token；工程上可用 `tiktoken`。

### 2.5 总结压缩 Summarization

更高级的压缩：请模型把早前对话**总结成一个摘要**放进 system，然后只剩最近几轮原样保留：

```
system: 以下是此前对话的摘要: …(模型生成)
... 最近 N 条消息原样 ...
```

保留「语义」，丢掉「冗长」，适合超长会话。

### 2.6 结构化记忆（键值/工具结果缓存）

工具结果往往可复用，不必每次重算：

```python
cache = {}                     # key -> tool result
def run_cached(reg, name, **kw):
    key = (name, tuple(sorted(kw.items())))
    cache.setdefault(key, reg.execute(name, **kw))
    return cache[key]
```

同时可存「用户偏好」「当前状态」等键值记忆，喂给 prompt。

---

## 三、核心概念解析

### 3.1 三档记忆策略

| 策略 | 做法 | 场景 |
| --- | --- | --- |
| 全量 | 全部历史 | 短暂对话 |
| 窗口 | 只留最近 N | 中长对话 |
| 总结 | 摘要 + 最近轮 | 超长会话 |

### 3.2 截断 vs 总结的取舍

- **截断**：简单、省成本，但早期信息丢失。
- **总结**：信息保留更全，但多一次模型调用（花钱、时延）。
- 可结合：太老的就总结，近的保留。

### 3.3 工具结果也要记忆

Observation 是 Agent 推进的依据。对昂贵工具（搜索、计费 API）做**结果缓存**，既省 token 又省钱。

---

## 四、关键知识点总结

- **记忆 = messages 上下文**，动态追加。
- **全量 → 窗口截断 → 总结压缩** 为三级策略。
- **token 预算**用估算器约束，超了就丢弃最旧。
- **总结**把旧历史压成摘要，放入 system。
- **工具结果缓存**避免重复开销。

---

## 五、实战练习

### 练习一：01-memory.py —— 记忆装箱与窗口截断

**任务描述**：实现 `ConversationBufferMemory` 与 `trim`，观察超长时只保留最近 N 轮。

**运行方式**

```bash
python "Day06 - 记忆与上下文管理/Code/01-memory.py"
```

### 练习二：02-summary-cache.py —— 摘要压缩与缓存

**任务描述**：模型对太老的历史做摘要；并给工具结果加缓存。

**运行方式**

```bash
python "Day06 - 记忆与上下文管理/Code/02-summary-cache.py"
```

### 练习三：尝试

把 Day05 的 Agent 套上窗口截断 + 工具结果缓存，实测多轮任务不再膨胀。

---

## 下节预告

下一节 **Day07** 进入 **错误处理与重试**：工具抛错、非法 JSON、调用上限，以及如何把异常优雅地喂回模型让其自纠。