# Day03 - Prompt 管理

PromptTemplate 是 LangChain 管理 Prompt 的核心工具，它让 Prompt 从「写死的字符串」变为「可模板化、可复用、可维护」的组件。在真实 LLM 应用中，同一个 Prompt 往往需要在不同场景下复用、动态填充变量、组合多角色消息、序列化到文件。掌握 PromptTemplate 和 ChatPromptTemplate，是构建可维护 LLM 应用的基础。本章深入 LangChain 的 Prompt 管理体系：从基础模板到多角色消息、从动态消息占位到模板序列化，并衔接 Prompt 工程板块的理论知识。

## 学习目标

- 理解 PromptTemplate 的概念与价值
- 掌握 `PromptTemplate.from_template()` 和显式变量两种创建方式
- 掌握 `ChatPromptTemplate` 多角色消息模板（System/Human/AI）
- 理解消息类型体系（SystemMessage / HumanMessage / AIMessage / ChatMessage）
- 掌握 `MessagesPlaceholder` 动态消息列表占位
- 了解模板组合与嵌套
- 掌握模板序列化（JSON/YAML）与文件加载
- 了解 PromptHub 的使用
- 衔接 Prompt 板块的理论知识（CRISPE/RTF 框架）

---

## 一、PromptTemplate 基础

### 1.1 概念

PromptTemplate 将 Prompt 中的变量部分用 `{variable}` 占位，运行时动态填充。

**没有模板时（硬编码字符串）：**

```python
# ❌ 每次都要拼接字符串，难复用、难维护
text = input("请输入要摘要的文本：")
prompt = f"请总结以下文本，不超过 50 字：\n{text}"
```

**使用 PromptTemplate：**

```python
# ✅ 模板化，可复用、可序列化
from langchain_core.prompts import PromptTemplate

template = PromptTemplate.from_template("请总结以下文本，不超过 50 字：\n{text}")
prompt = template.format(text="LangChain 是一个 LLM 应用开发框架...")
```

### 1.2 创建方式

**方式一：`from_template()`（推荐，自动提取变量）**

```python
from langchain_core.prompts import PromptTemplate

# 自动识别 {text} 和 {max_words} 两个变量
template = PromptTemplate.from_template(
    "请总结以下文本，不超过 {max_words} 字：\n{text}"
)
```

**方式二：显式指定变量（更严格）**

```python
from langchain_core.prompts import PromptTemplate

template = PromptTemplate(
    template="请总结以下文本，不超过 {max_words} 字：\n{text}",
    input_variables=["text", "max_words"],
)
```

### 1.3 渲染方法

```python
# .format() → 字符串
prompt_str = template.format(text="...", max_words=50)

# .format_messages() → 消息列表（PromptTemplate 也能用，但通常 ChatPromptTemplate 更合适）
messages = template.format_messages(text="...", max_words=50)

# .invoke() → PromptValue（Runnable 接口，可与模型管道组合）
prompt_value = template.invoke({"text": "...", "max_words": 50})
```

### 1.4 变量验证

PromptTemplate 会自动验证变量，缺少变量会报错：

```python
template = PromptTemplate.from_template("翻译 {text} 成 {language}")
# 缺少 language 会报错
template.format(text="你好")  # ❌ KeyError
template.format(text="你好", language="英文")  # ✅ 正常
```

### 1.5 部分变量填充 `partial()`

当部分变量提前已知、部分变量运行时才有时，用 `partial()` 预填充：

```python
template = PromptTemplate.from_template("你是{role}，请回答：{question}")
# 预填充 role
partial_template = template.partial(role="翻译助手")
# 运行时只需提供 question
prompt = partial_template.format(question="把'你好'翻译成英文")
```

---

## 二、ChatPromptTemplate（重点）

### 2.1 概念

ChatPromptTemplate 是多角色消息模板，支持 System / Human / AI 角色体系，是现代 ChatModel 开发的主要模板工具。

### 2.2 创建方式

**方式一：元组列表（推荐，简洁）**

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，请用{style}的语气回答。"),
    ("human", "{question}"),
])
```

**方式二：消息对象列表（更灵活，可复用消息）**

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="你是一个翻译助手。"),
    HumanMessage(content="把'{text}'翻译成英文"),
])
```

**方式三：单模板（默认 Human 角色）**

```python
prompt = ChatPromptTemplate.from_template("解释什么是 {topic}")
# 等价于 [("human", "解释什么是 {topic}")]
```

### 2.3 渲染方法

```python
# .format_messages() → List[BaseMessage]（推荐，与 ChatModel 配合）
messages = prompt.format_messages(role="助手", style="幽默", question="什么是 AI")

# .format() → 字符串（拼接所有消息）
text = prompt.format(role="助手", style="幽默", question="什么是 AI")

# .invoke() → ChatPromptValue（Runnable 接口）
prompt_value = prompt.invoke({"role": "助手", "style": "幽默", "question": "什么是 AI"})
```

### 2.4 角色体系对输出的影响

```python
# 不同 System 设定，输出风格差异巨大
prompts = {
    "正式": ChatPromptTemplate.from_messages([
        ("system", "你是正式的商务助手，用专业术语回答。"),
        ("human", "{question}"),
    ]),
    "幽默": ChatPromptTemplate.from_messages([
        ("system", "你是幽默的助手，用笑话和比喻回答。"),
        ("human", "{question}"),
    ]),
}
# 同一问题，不同 System → 完全不同的输出风格
```

---

## 三、消息类型详解

| 消息类型 | 对应角色 | 用途 | 示例 |
|---------|---------|------|------|
| SystemMessage | system | 设定角色/规范/护栏 | "你是翻译助手" |
| HumanMessage | human | 用户输入 | "翻译这句话" |
| AIMessage | ai | LLM 回复（对话历史） | "Translation: ..." |
| ChatMessage | 自定义 | 特殊角色 | role="translator" |
| AIMessageChunk | ai | 流式输出分片 | stream 的 chunk |

### 3.1 消息在多轮对话中的作用

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 对话历史由 Human 和 AI 消息交替组成
conversation = [
    SystemMessage(content="你是一个问答助手。"),
    HumanMessage(content="什么是 Python？"),       # 第 1 轮：用户问
    AIMessage(content="Python 是一种编程语言..."),   # 第 1 轮：AI 答
    HumanMessage(content="它有什么优点？"),         # 第 2 轮：用户追问
]
# LLM 能理解上下文，回答第 2 轮的问题
```

---

## 四、MessagesPlaceholder

### 4.1 概念

MessagesPlaceholder 是动态消息列表占位符，用于在模板中插入**可变数量**的消息（如对话历史）。

### 4.2 问题：固定模板无法插入可变消息

```python
# ❌ 问题：对话历史长度不固定，无法在模板中预设
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是助手。"),
    # 这里需要插入 N 条历史消息，N 不固定
    ("human", "{question}"),
])
```

### 4.3 解决：MessagesPlaceholder

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个问答助手，请结合历史对话回答。"),
    MessagesPlaceholder(variable_name="history"),  # 动态插入历史消息
    ("human", "{question}"),
])

# 调用时传入历史消息列表
from langchain_core.messages import HumanMessage, AIMessage

result = prompt.format_messages(
    history=[
        HumanMessage(content="什么是 Python？"),
        AIMessage(content="Python 是一种编程语言。"),
    ],
    question="它有什么优点？",
)
```

### 4.4 Few-Shot 示例的动态插入

MessagesPlaceholder 也用于动态插入 Few-Shot 示例：

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是情感分类器，输出 positive/negative。"),
    MessagesPlaceholder(variable_name="examples"),  # Few-Shot 示例
    ("human", "分类：{input}"),
])
```

---

## 五、模板组合与嵌套

### 5.1 多模板组合

```python
# 基础模板
base = ChatPromptTemplate.from_messages([
    ("system", "你是 ChainQA 助手。"),
])

# 功能模板（继承基础设定）
qa = ChatPromptTemplate.from_messages(base.messages + [
    ("human", "{question}"),
])
```

### 5.2 动态选择模板

```python
# 根据任务类型选择不同模板
templates = {
    "翻译": ChatPromptTemplate.from_template("翻译：{text}"),
    "摘要": ChatPromptTemplate.from_template("摘要：{text}"),
    "分类": ChatPromptTemplate.from_template("分类：{text}"),
}

def select_template(task: str):
    return templates.get(task, templates["翻译"])
```

---

## 六、模板序列化

### 6.1 为什么序列化？

- **Prompt 即代码**：将 Prompt 与代码分离，便于版本管理
- **团队协作**：非开发人员也能编辑 Prompt
- **A/B 测试**：同一应用加载不同 Prompt 文件对比效果

### 6.2 保存为 JSON

```python
import json
from langchain_core.prompts import PromptTemplate

template = PromptTemplate.from_template("总结：{text}")

# 保存
with open("prompt.json", "w") as f:
    json.dump(template.dict(), f, ensure_ascii=False, indent=2)
```

### 6.3 从文件加载

```python
from langchain_core.prompts import load_prompt

# 从 JSON 加载
template = load_prompt("prompt.json")

# 从 YAML 加载
template = load_prompt("prompt.yaml")
```

---

## 七、PromptHub

PromptHub 是 LangChain 官方的 Prompt 共享市场，可以从中加载社区共享的 Prompt。

```python
from langchain import hub

# 从 Hub 拉取 Prompt
prompt = hub.pull("rlm/rag-prompt")

# 推送自己的 Prompt（需登录）
# hub.push("my-username/my-prompt", prompt)
```

---

## 八、与 Prompt 板块的衔接

Prompt 板块讲解的六大原则和结构化框架，可以用 LangChain 的 ChatPromptTemplate 实现：

### 8.1 CRISPE 框架实现

```python
# CRISPE: Capacity / Role / Insight / Statement / Personality / Experiment
prompt = ChatPromptTemplate.from_messages([
    ("system", """
    角色：{role}
    能力：{capacity}
    背景：{insight}
    语气：{personality}
    """),
    ("human", "{statement}"),
])
```

### 8.2 RTF 框架实现

```python
# RTF: Role / Task / Format
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是{role}。"),
    ("human", "任务：{task}。输出格式：{format}。"),
])
```

---

## 九、代码文件说明

| 文件 | 用途 | 关键内容 |
|------|------|---------|
| `Code/01_prompt_template.py` | PromptTemplate 基础 | from_template / 显式变量 / format / partial / 5 种使用模式 |
| `Code/02_chat_prompt_template.py` | ChatPromptTemplate 多角色 | from_messages / System+Human / 角色影响输出 |
| `Code/03_messages_placeholder.py` | MessagesPlaceholder 动态消息 | 对话历史 / Few-Shot 示例 |
| `Code/04_template_serialization.py` | 模板序列化与文件加载 | JSON/YAML / load_prompt / hub.pull |
| `Code/README.md` | Prompt 管理指南 | 选择决策表 / 序列化实践 / 设计规范 |

运行方式：

```bash
cd "Day03 - Prompt管理/Code"
python 01_prompt_template.py
python 02_chat_prompt_template.py
python 03_messages_placeholder.py
python 04_template_serialization.py
```

---

## 关键知识点总结

### PromptTemplate vs ChatPromptTemplate 对比

| 维度 | PromptTemplate | ChatPromptTemplate |
|------|----------------|-------------------|
| 输入类型 | 纯文本 | 多角色消息 |
| 角色支持 | ❌ 无 | ✅ System/Human/AI |
| 适用模型 | LLM（旧） | ChatModel（推荐） |
| format 输出 | 字符串 | 字符串或消息列表 |
| format_messages | 有限支持 | ✅ 原生支持 |
| 推荐度 | 简单场景 | ✅ 现代开发首选 |

### 消息类型速查

| 类型 | role | 用途 |
|------|------|------|
| SystemMessage | system | 设定行为/规范 |
| HumanMessage | human | 用户输入 |
| AIMessage | ai | LLM 回复 |
| ChatMessage | 自定义 | 特殊角色 |
| AIMessageChunk | ai | 流式分片 |

### 模板创建方式对比

| 方式 | 代码 | 特点 |
|------|------|------|
| from_template | `PromptTemplate.from_template("...{var}...")` | 自动提取变量 |
| 显式变量 | `PromptTemplate(template=..., input_variables=[...])` | 严格验证 |
| from_messages（元组） | `ChatPromptTemplate.from_messages([("system","...")])` | 简洁 |
| from_messages（对象） | `ChatPromptTemplate.from_messages([SystemMessage(...)])` | 灵活 |

### 序列化格式对比

| 格式 | 扩展名 | 可读性 | 支持 |
|------|--------|--------|------|
| JSON | .json | 中 | load_prompt |
| YAML | .yaml | 高 | load_prompt |

### MessagesPlaceholder 使用场景

| 场景 | variable_name | 内容 |
|------|--------------|------|
| 对话历史 | "history" | [HumanMessage, AIMessage, ...] |
| Few-Shot 示例 | "examples" | [HumanMessage, AIMessage, ...] |
| 动态系统消息 | "context" | [SystemMessage, ...] |

---

## 实战练习

### 练习 1：构建客服 Prompt 模板

使用 ChatPromptTemplate 设计一个客服系统的 Prompt：
- System：设定客服角色（礼貌、专业、中文回答）
- Human：用户问题
- 测试 3 个不同问题，观察输出是否符合设定

### 练习 2：实现带历史的问答

基于 `Code/03_messages_placeholder.py`：
- 模拟 3 轮对话，用 MessagesPlaceholder 管理历史
- 第 3 轮提问中引用第 1 轮的内容，验证 LLM 能否记住

### 练习 3：Prompt 即代码

基于 `Code/04_template_serialization.py`：
- 将一个 PromptTemplate 序列化为 JSON 文件
- 创建 2 个不同版本的 Prompt 文件
- 加载并对比两个版本的输出效果

---

> **下一步**：Day04 将学习 Output Parsers，将 LLM 的自由文本输出转化为结构化数据。
