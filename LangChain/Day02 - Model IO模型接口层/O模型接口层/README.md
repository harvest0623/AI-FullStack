# Day02 - Model I/O 模型接口层

Model I/O 是 LangChain 与 LLM 交互的入口，所有 LLM 应用的第一步都是调用模型。掌握 Model I/O 层——理解 LLM 与 ChatModel 的差异、熟练实例化各类模型、掌握 invoke/batch/stream 三种调用方式、配置模型参数与回退机制——是构建 LLM 应用的起点。本章深入 LangChain 的模型接口层，对比不同 ChatModel 的实例化方式，演示统一 Runnable 接口的四种调用方法，并介绍模型绑定、结构化输出与回退策略，为后续 Prompt 管理和输出解析打下基础。

## 学习目标

- 理解 Model I/O 的概念与三步流程
- 区分 LLM 与 ChatModel，理解为何现代开发以 ChatModel 为主
- 掌握 ChatOpenAI / ChatAnthropic / ChatOllama 的实例化与配置
- 掌握模型参数：temperature / max_tokens / streaming / timeout / max_retries 等
- 熟练使用 invoke / batch / stream / ainvoke 四种调用方式
- 理解流式输出 AIMessageChunk 的拼接机制
- 掌握 `.bind()` / `.with_structured_output()` / `.with_fallbacks()` 系列方法
- 理解多模型统一接口设计与无缝切换

---

## 一、Model I/O 概念

Model I/O 是 LangChain 与 LLM 交互的抽象层，它将「输入 Prompt → 调用模型 → 输出结果」这一核心流程封装为统一的 Runnable 接口。

**三步流程**：

```
1. 输入：构造 Prompt（字符串 / 消息列表 / PromptValue）
       ↓
2. 调用：模型接收输入，调用 LLM API
       ↓
3. 输出：返回结果（AIMessage / AIMessageChunk / str）
```

在 LangChain 中，Model I/O 层的核心是 `BaseChatModel` 和 `BaseLLM` 两个抽象基类，所有具体模型都继承自它们。

---

## 二、LLM vs ChatModel

LangChain 提供两种模型接口：

| 维度 | LLM（旧式） | ChatModel（现代） |
|------|------------|------------------|
| 基类 | `BaseLLM` | `BaseChatModel` |
| 输入 | 纯文本字符串 | 消息列表（带角色） |
| 输出 | 字符串 | AIMessage 对象 |
| 角色支持 | ❌ 无 | ✅ System/Human/AI |
| 代表类 | OpenAI（已废弃） | ChatOpenAI |
| 推荐度 | ⚠️ 不推荐 | ✅ 推荐 |

### 2.1 LLM（BaseLLM）

LLM 是旧式的纯文本接口，对应 OpenAI 早期的 completions API。输入一个字符串，输出一个字符串：

```python
from langchain_community.llms import OpenAI   # 已废弃
llm = OpenAI(model="gpt-3.5-turbo-instruct")
result = llm.invoke("解释什么是机器学习")
# result 是字符串
```

> ⚠️ **注意**：LLM 类已不推荐使用，现代模型（GPT-4o、Claude 3.5）都只提供 Chat 接口。本手册仅作了解，实际开发请用 ChatModel。

### 2.2 ChatModel（BaseChatModel）

ChatModel 是现代的对话接口，支持消息角色体系（System / Human / AI），对应 OpenAI 的 chat completions API：

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

model = ChatOpenAI(model="gpt-4o-mini")
result = model.invoke([
    SystemMessage(content="你是一个翻译助手"),
    HumanMessage(content="把'你好'翻译成英文")
])
# result 是 AIMessage 对象，含 content / usage_metadata 等
print(result.content)
```

**为什么现代开发以 ChatModel 为主？**
- 主流模型（GPT-4o、Claude 3.5、Gemini）只提供 Chat 接口
- 角色体系（System 设定行为、Human 用户输入、AI 回复）更清晰
- 支持多轮对话历史
- AIMessage 提供丰富的元数据（Token 用量、模型信息、停止原因等）

---

## 三、ChatModel 模型实例化

所有 ChatModel 都继承 `BaseChatModel`，实例化方式高度统一：

### 3.1 ChatOpenAI（OpenAI 系列）

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-4o-mini",       # 模型名称
    temperature=0.7,            # 随机性
    max_tokens=1000,             # 最大输出 Token
    timeout=30,                 # 超时秒数
    max_retries=2,              # 最大重试次数
)
```

### 3.2 ChatAnthropic（Claude 系列）

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0.7,
    max_tokens=1000,
    timeout=30,
)
# 需安装：pip install langchain-anthropic
# 需配置：ANTHROPIC_API_KEY
```

### 3.3 ChatOllama（本地模型，无需 API Key）

```python
from langchain_community.chat_models import ChatOllama

model = ChatOllama(
    model="qwen2.5:7b",                          # 本地模型名
    base_url="http://localhost:11434/v1",        # Ollama 服务地址
    temperature=0.7,
)
# 需先安装 Ollama 并拉取模型：ollama pull qwen2.5:7b
```

### 3.4 ChatTongyi（通义千问）

```python
from langchain_community.chat_models.tongyi import ChatTongyi

model = ChatTongyi(model="qwen-max")
# 需安装：pip install dashscope
# 需配置：DASHSCOPE_API_KEY
```

### 3.5 实例化差异对比

| 模型类 | 必装包 | 环境变量 | 特有参数 |
|--------|--------|---------|---------|
| ChatOpenAI | langchain-openai | OPENAI_API_KEY | — |
| ChatAnthropic | langchain-anthropic | ANTHROPIC_API_KEY | — |
| ChatOllama | langchain-community | 无（本地） | base_url |
| ChatTongyi | dashscope | DASHSCOPE_API_KEY | — |

> **核心要点**：所有 ChatModel 都实现 Runnable 接口，实例化后调用方式完全一致，可以无缝切换。

---

## 四、模型参数配置

| 参数 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `model` | str | 模型名称 | `"gpt-4o-mini"` |
| `temperature` | float | 随机性（0=确定，1=高随机，2=极高） | `0.7` |
| `max_tokens` | int | 最大输出 Token 数 | `1000` |
| `streaming` | bool | 是否流式输出 | `True` |
| `timeout` | int | 请求超时（秒） | `30` |
| `max_retries` | int | 最大重试次数 | `2` |
| `stop` | list[str] | 停止序列 | `["\n\n"]` |
| `seed` | int | 随机种子（确定性输出） | `42` |

### temperature 详解

```
temperature = 0    → 完全确定，每次输出相同（适合分类、抽取）
temperature = 0.3  → 低随机，稳定且有少量变化（适合问答）
temperature = 0.7  → 中等随机，平衡创意与稳定（默认值，适合对话）
temperature = 1.0  → 高随机，富有创意（适合创作）
temperature = 2.0  → 极高随机，可能不连贯（不推荐）
```

---

## 五、三种调用方式

所有 ChatModel（及所有 Runnable 组件）都支持以下四种调用方式：

| 方法 | 说明 | 同步/异步 | 适用场景 |
|------|------|----------|---------|
| `.invoke(input)` | 单次调用 | 同步 | 单个请求 |
| `.batch(inputs)` | 批量调用 | 同步 | 多个输入并行 |
| `.stream(input)` | 流式输出 | 同步 | 实时显示 |
| `.ainvoke(input)` | 单次调用 | 异步 | 高并发场景 |
| `.abatch(inputs)` | 批量调用 | 异步 | 大批量并发 |

### 5.1 invoke（单次调用）

```python
result = model.invoke("什么是 LangChain？")
# 输入可以是字符串、消息列表、PromptValue
# 返回 AIMessage
print(result.content)
```

### 5.2 batch（批量调用）

```python
results = model.batch([
    "什么是 LangChain？",
    "什么是 RAG？",
    "什么是 Agent？",
])
# 并行处理多个输入，返回 AIMessage 列表
for r in results:
    print(r.content)
```

### 5.3 stream（流式输出）

```python
for chunk in model.stream("讲一个长故事"):
    # chunk 是 AIMessageChunk
    print(chunk.content, end="", flush=True)
```

### 5.4 ainvoke（异步调用）

```python
import asyncio

async def main():
    result = await model.ainvoke("什么是 LangChain？")
    print(result.content)

asyncio.run(main())
```

---

## 六、stream 流式输出详解

流式输出是提升用户体验的关键能力，让用户看到「正在生成」的效果而非等待完整结果。

### 6.1 AIMessageChunk

`.stream()` 返回的不是完整 AIMessage，而是多个 `AIMessageChunk` 分片：

```python
for chunk in model.stream("讲一个故事"):
    print(type(chunk))  # <class 'AIMessageChunk'>
    print(chunk.content)  # 当前分片的文本
```

### 6.2 Chunk 拼接

AIMessageChunk 支持 `+` 运算符拼接，可以把所有 chunk 合并成完整结果：

```python
full = None
for chunk in model.stream("讲一个故事"):
    if full is None:
        full = chunk
    else:
        full = full + chunk   # AIMessageChunk.__add__

print(full.content)  # 完整文本
```

### 6.3 流式 vs 非流式对比

| 维度 | 非流式（invoke） | 流式（stream） |
|------|----------------|---------------|
| 用户体验 | 等待全部生成后一次性显示 | 逐字显示，即时反馈 |
| 首字延迟 | 等于总生成时间 | 接近 0（生成第一个 token 即返回） |
| 总耗时 | 略快 | 略慢（分片传输开销） |
| 适用场景 | 后台处理、批量任务 | 聊天界面、实时交互 |
| 内存占用 | 一次返回完整结果 | 增量返回，峰值低 |

---

## 七、模型绑定参数 .bind() 系列

### 7.1 .bind() 绑定固定参数

`.bind()` 用于创建一个绑定了固定参数的新模型实例，常用于绑定 stop 序列：

```python
# 绑定 stop 序列，遇到 "\n\n" 停止生成
model_with_stop = model.bind(stop=["\n\n"])
result = model_with_stop.invoke("写一段文字")
```

### 7.2 .with_structured_output() 结构化输出

绑定 Pydantic 模型，让 LLM 直接输出结构化数据（Day04 详讲）：

```python
from pydantic import BaseModel, Field

class PersonInfo(BaseModel):
    name: str = Field(description="人名")
    age: int = Field(description="年龄")

structured_model = model.with_structured_output(PersonInfo)
result = structured_model.invoke("张三今年 25 岁")
# result 是 PersonInfo 实例，不是 AIMessage
print(result.name, result.age)  # 张三 25
```

### 7.3 .with_fallbacks() 模型回退

主模型故障时自动切换备用模型，提升可用性：

```python
primary = ChatOpenAI(model="gpt-4o")           # 主模型
fallback1 = ChatOpenAI(model="gpt-4o-mini")     # 备用1
fallback2 = ChatOllama(model="qwen2.5:7b")      # 备用2（本地）

model = primary.with_fallbacks([fallback1, fallback2])
# gpt-4o 失败 → gpt-4o-mini → 本地模型
```

### 7.4 .bind_tools() 绑定工具

绑定工具让 LLM 可以调用外部函数（Day09 详讲）：

```python
from langchain_core.tools import tool

@tool
def search_weather(city: str) -> str:
    """查询天气"""
    return f"{city} 今天晴"

model_with_tools = model.bind_tools([search_weather])
```

---

## 八、多模型统一接口设计

LangChain 的核心优势之一：所有 ChatModel 继承 `BaseChatModel`，接口完全统一，可以无缝切换。

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# 两个不同厂商的模型，接口完全一致
models = {
    "openai": ChatOpenAI(model="gpt-4o-mini"),
    "anthropic": ChatAnthropic(model="claude-3-5-sonnet-20241022"),
}

# 同一套代码，切换模型只需改 key
for name, model in models.items():
    result = model.invoke("你好")
    print(f"{name}: {result.content}")
```

---

## 九、速率限制与重试

### 9.1 max_retries 参数

实例化时设置最大重试次数，遇到限流/网络错误自动重试：

```python
model = ChatOpenAI(model="gpt-4o-mini", max_retries=3)
```

### 9.2 with_retry() 方法

更灵活的重试配置，可自定义重试逻辑：

```python
from langchain_core.runnables import RunnableConfig

model = ChatOpenAI(model="gpt-4o-mini")
# 配置重试：最多 3 次，指数退避
retry_model = model.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True,
)
```

---

## 十、代码文件说明

| 文件 | 用途 | 关键内容 |
|------|------|---------|
| `Code/01_chat_models.py` | ChatModel 实例化与调用 | ChatOpenAI/Anthropic/Ollama 实例化 / invoke 调用 / AIMessage 结构分析 |
| `Code/02_llm_models.py` | LLM 与 ChatModel 对比 | 旧式 LLM / 消息类型 / 字符串转消息列表 |
| `Code/03_invoke_batch_async.py` | 三种调用方式对比 | invoke/batch/stream/ainvoke / 性能计时 |
| `Code/04_model_config.py` | 模型配置与回退 | 参数对比 / .bind() / 结构化输出 / with_fallbacks |
| `Code/README.md` | Model I/O 指南 | 参数表 / 调用决策表 / 错误排查 / 迁移指南 |

运行方式：

```bash
cd "Day02 - Model I/O模型接口层/Code"
python 01_chat_models.py
python 02_llm_models.py
python 03_invoke_batch_async.py
python 04_model_config.py
```

---

## 关键知识点总结

### ChatModel 速查表

| 模型类 | 包名 | 环境变量 | 特点 |
|--------|------|---------|------|
| ChatOpenAI | langchain-openai | OPENAI_API_KEY | 最通用 |
| ChatAnthropic | langchain-anthropic | ANTHROPIC_API_KEY | Claude 系列 |
| ChatOllama | langchain-community | 无（本地） | 无需 Key |
| ChatTongyi | langchain-community | DASHSCOPE_API_KEY | 通义千问 |
| ChatGoogleGenerativeAI | langchain-google-genai | GOOGLE_API_KEY | Gemini |

### 模型参数速查

| 参数 | 作用 | 默认值 | 推荐场景 |
|------|------|--------|---------|
| model | 模型名称 | — | 必填 |
| temperature | 随机性 | 0.7 | 0=确定, 1=创意 |
| max_tokens | 最大输出 | 无限 | 控制成本 |
| streaming | 流式输出 | False | 聊天界面 |
| timeout | 超时 | None | 30 秒 |
| max_retries | 重试次数 | 2 | 生产环境 |
| stop | 停止序列 | None | 控制输出 |
| seed | 随机种子 | None | 可复现 |

### 调用方式对比表

| 方法 | 同步/异步 | 输入 | 输出 | 适用场景 |
|------|----------|------|------|---------|
| invoke | 同步 | 单个 | AIMessage | 单次请求 |
| batch | 同步 | 列表 | AIMessage 列表 | 批量处理 |
| stream | 同步 | 单个 | AIMessageChunk 迭代器 | 实时显示 |
| ainvoke | 异步 | 单个 | AIMessage | 高并发 |
| abatch | 异步 | 列表 | AIMessage 列表 | 大批量 |
| astream | 异步 | 单个 | AIMessageChunk 迭代器 | 异步流式 |

### .bind() 系列方法速查

| 方法 | 作用 | 返回值 | 对应天数 |
|------|------|--------|---------|
| `.bind(**kwargs)` | 绑定固定参数 | 新模型实例 | Day02 |
| `.with_structured_output(schema)` | 结构化输出 | 直接输出 Pydantic 对象 | Day04 |
| `.with_fallbacks(models)` | 模型回退 | 带回退的模型 | Day02 |
| `.bind_tools(tools)` | 绑定工具 | 带工具的模型 | Day09 |

### 模型回退配置

```
主模型（gpt-4o）
    ↓ 失败
备用1（gpt-4o-mini）    ← 降级到更便宜模型
    ↓ 失败
备用2（本地 Ollama）     ← 本地兜底
```

---

## 实战练习

### 练习 1：多模型输出对比

使用 `Code/01_chat_models.py` 的方式，同时调用 ChatOpenAI 和 ChatAnthropic：
- 用相同的 Prompt：「用三句话解释量子计算」
- 对比两个模型的输出风格、Token 用量、响应速度
- 思考：什么场景下应该选哪个模型？

### 练习 2：批量处理优化

基于 `Code/03_invoke_batch_async.py`：
- 准备 10 个不同的翻译任务
- 分别用 `for + invoke` 和 `batch` 两种方式处理
- 对比两种方式的总耗时，思考 batch 的并行优势

### 练习 3：构建带回退的健壮模型

基于 `Code/04_model_config.py`：
- 配置一个三级回退链：gpt-4o → gpt-4o-mini → 本地 Ollama
- 故意触发一个错误（如使用无效模型名），观察回退机制是否生效
- 思考：在生产环境中，回退策略应该考虑哪些因素？

---

> **下一步**：Day03 将学习 Prompt 管理，掌握 PromptTemplate 和 ChatPromptTemplate 的模板化与变量插值。
