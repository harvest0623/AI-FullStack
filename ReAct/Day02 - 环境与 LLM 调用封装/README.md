# Day02 - 环境与 LLM 调用封装

> 本章节搭建 ReAct 的工程底座：安装依赖、理解 OpenAI 兼容的「消息结构」，并统一封装 LLM 客户端。关键产出是一个可复用的 `llm.py`，同时支持**真实模型**与**离线 MockLLM**，让后续章节不依赖 API Key 也能运行。

---

## 目录

- [一、学习目标](#一学习目标）
- [二、理论知识](#二理论知识）
  - [2.1 依赖与闲聊环境](#21-依赖与闲聊环境）
  - [2.2 OpenAI 兼容的"消息"结构](#22-openai-兼容的消息结构）
  - [2.3 chat.completions 接口](#23-chatcompletions-接口）
  - [2.4 为什么要封装统一 LLM](#24-为什么要封装统一-llm）
  - [2.5 MockLLM：无 Key 也能跑的测试替身](#25-mockllm无-key-也能跑的测试替身）
  - [2.6 统一回复格式设计](#26-统一回复格式设计）
- [三、核心概念解析](#三核心概念解析）
  - [3.1 role 的四种取值](#31-role-的四种取值）
  - [3.2 tools 参数(预告)](#32-tools-参数预告)
  - [3.3 真实/模拟无缝切换](#33-真实模拟无缝切换)
- [四、关键知识点总结](#四关键知识点总结）
- [五、实战练习](#五实战练习）

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **理解 OpenAI 兼容的消息结构（role/content）**。
2. **用 `chat.completions.create` 做一次对话**。
3. **理解为什么要统一封装 LLM**。
4. **编写能给任意脚本复用的 `MockLLM`**。
5. **在真实模型与离线模拟间切换**。

---

## 二、理论知识

### 2.1 依赖与环境

```bash
pip install openai httpx
```

`openai` 官方 SDK 既能连 OpenAI，也能通过 `base_url` 连任何 OpenAI 兼容服务（本地 vLLM、DeepSeek、Ollama 等），一线方案。

### 2.2 OpenAI 兼容的"消息"结构

一次对话是一组 `消息`，每条含 `role` 与 `content`：

```python
messages = [
    {"role": "system",    "content": "你是一个乐于助人的助手。"},
    {"role": "user",      "content": "今天天气怎么样?"},
    {"role": "assistant", "content": "我需要查天气…"},
    {"role": "tool",      "content": "杭州: 25℃ 多云。"},   # 工具返回(后文)
]
```

`system` 设定人格/规则，`user` 是用户输入，`assistant` 是模型回复，`tool` 是工具观察结果。

### 2.3 chat.completions 接口

```python
from openai import OpenAI
client = OpenAI()                       # 读 OPENAI_API_KEY
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    temperature=0.7,
)
print(resp.choices[0].message.content)
```

返回对象中 `choices[0].message` 即本次回复。

### 2.4 为什么要封装统一 LLM

ReAct 会反复、结构化地调用模型。把「连哪个服务、怎么解析、怎么抛错」收进一个类，脚本只需 `llm.chat(messages)`，逻辑与厂商解耦，方便换模型/加 Mock。

### 2.5 MockLLM：无 Key 也能跑的测试替身

写测试/本地演示时，没有 Key 也能跑。做法是给个「决策函数」模拟模型：

```python
def my_decider(messages, tools):
    last = messages[-1]["content"]
    if "天气" in last:
        return tool_call("search_weather", {"city": "成都"})
    return text("我不知道")

llm = MockLLM(my_decider)
```

它不真调网络，但**接口与真实模型一致**，可驱动 ReAct 循环的完整演示与单元测试。

### 2.6 统一回复格式设计

我们把任何后端的回复统一成：

```python
{"content": "文本回复…",                       # 可选
 "tool_calls": [{"name": "search_weather", "arguments": {...}}]}  # 可选
```

这样后续读 Agent 循环时，只认这一种返回，不用区分真实/Mock。

---

## 三、核心概念解析

### 3.1 role 的四种取值

| role | 含义 | 
| --- | --- |
| `system` | 设定行为、规则 |
| `user` | 用户/提问/工具返回前的输入 |
| `assistant` | 模型回复（也可携带 tool_calls） |
| `tool` | 工具执行结果（Observation） |

### 3.2 tools 参数(预告)

真实模型的 `create(..., tools=[...])` 会让模型**原生输出结构化工具调用**（Day03-05 详述）。封装已预留 `tools` 参数。

### 3.3 真实/模拟无缝切换

`auto_llm(mock_decider=...)`：有 `OPENAI_API_KEY` 用真模型，否则用 Mock。脚本既可在 CI 里离线跑，也能在有 Key 的机器上真调。

---

## 四、关键知识点总结

- **消息 = role + content 的列表**。
- **chat.completions** 是统一入口。
- **统一封装** 让厂商与逻辑解耦。
- **MockLLM(decider)** 离线可测。
- **统一回复 `{content, tool_calls}`** 供循环消费。

---

## 五、实战练习

### 练习一：llm.py —— 统一封装库

**任务描述**：提供了 `OpenAILLM`、`MockLLM`、`auto_llm`、`text/tool_call` 等基础设施，后续章节复用。

**运行方式**

```bash
python "Day02 - 环境与 LLM 调用封装/Code/llm.py"
```

### 练习二：02-chat-demo.py —— 用封装做对话

**任务描述**：用 `llm.py` 里的接口完成一次多轮对话，无 Key 走 Mock、有 Key 走真模型。

**运行方式**

```bash
python "Day02 - 环境与 LLM 调用封装/Code/02-chat-demo.py"
```

### 练习三：尝试

- 给 MockLLM 写一个 `decider`：把最后一条用户消息翻译成"查到 xx"。 
- 查看是否有 `OPENAI_API_KEY`，若有试真实模型跑通一次对话。

---

## 下节预告

下一节 **Day03** 进入 **工具定义与注册**：如何用 JSON Schema 描述一个工具、注册表设计，以及如何用 Pydantic 生成工具参数 schema。