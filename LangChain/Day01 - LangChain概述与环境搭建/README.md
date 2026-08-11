# Day01 - LangChain 概述与环境搭建

LangChain 是当前最流行的 LLM 应用开发框架，它将 LLM 调用、Prompt 管理、输出解析、链式组合、记忆管理等能力封装为可组合的模块化组件，让开发者能像搭积木一样构建复杂的 AI 应用。掌握 LangChain，是从「会调 LLM API」迈向「工程化构建 LLM 应用」的关键一步。本章带你从零开始：理解 LangChain 是什么、它的生态系统与核心概念、0.3 版本的架构特性，并完成环境搭建与第一个 LangChain 程序，为后续学习 Model I/O、Prompt 管理、Output Parsers 打下基础。

## 学习目标

- 理解 LangChain 的定义、发展历程与在 LLM 应用开发中的定位
- 掌握 LangChain 生态系统四大组成（LangChain / LangServe / LangSmith / LangGraph）的职责
- 理解核心概念：Components / Chains / Agents / Memory / Retrievers / Callbacks
- 掌握 LangChain 的架构设计理念：组合性、可扩展性、模块化
- 了解 LangChain 0.3 版本特性：LCEL 核心、Runnable 统一接口、分包结构
- 对比 LangChain 与直接调用 API 的差异，理解框架化开发的价值
- 完成开发环境搭建并运行第一个 LangChain 程序
- 生成 ChainQA 智能问答助手项目脚手架

---

## 一、LangChain 定义

**LangChain** 是一个用于构建 LLM 驱动应用的开源框架，它提供了一套模块化组件，将 LLM 调用、Prompt 管理、输出解析、链式组合、记忆管理、文档检索、工具调用等能力封装为可复用、可组合的单元，让开发者无需从零实现这些繁琐的工程逻辑，就能快速构建复杂的 LLM 应用。

LangChain 解决的核心问题：**直接调用 LLM API 只能完成单轮文本交互，而真实的 AI 应用需要组合「多轮对话记忆 + Prompt 模板 + 输出结构化 + 文档检索 + 工具调用 + 错误重试」等一整套流程**。LangChain 把这些流程封装为标准组件，开发者通过组合组件即可构建应用。

一个典型的 LLM 应用流程：

```
用户输入 → Prompt 模板渲染 → 调用 LLM → 解析输出 → 返回结构化结果
                ↑                              ↓
            记忆管理 ← ← ← ← ← ← ← ← ← ← ← ←
```

直接用 OpenAI SDK 实现这个流程需要手动管理每一步，而 LangChain 把每一步都封装为可组合的组件。

---

## 二、发展历程

| 时间 | 版本 | 关键变化 | 说明 |
|------|------|---------|------|
| 2022.10 | v0.0.1 | 首次发布 | Harrison Chase 创建，初版组件较少 |
| 2023 上半年 | 0.0.x | 快速迭代 | 组件迅速扩展，社区爆发式增长 |
| 2024.01 | 0.1 | Legacy Chains 成熟 | 引入 LCEL，但旧版 Chain 仍为主流 |
| 2024.05 | 0.2 | LCEL 推广 | 标记 Legacy Chains 为弃用，推荐 LCEL |
| 2024.09 | 0.3 | LCEL 为核心 | 正式废弃 LLMChain 等旧 Chain，分包重构 |

**版本演进的核心趋势：**
- 从「面向对象 Chain 类」走向「函数式管道 LCEL」
- 从「单一大包」走向「core / community / partners 分包」
- 从「LLMChain 硬编码」走向「Runnable 统一接口」

> 本手册基于 LangChain 0.3+ 编写，所有示例使用 LCEL 语法，不使用已废弃的 Legacy Chains。

---

## 三、生态系统

LangChain 不只是一个库，而是一个完整的 LLM 应用开发生态：

| 组件 | 职责 | 类比 |
|------|------|------|
| **LangChain** | 核心框架，提供组件 + 链式调用 | 像 Spring 之于 Java |
| **LangServe** | 将 Chain 部署为 REST API | 像 FastAPI 的自动路由 |
| **LangSmith** | 追踪、评估、监控平台 | 像 Datadog 之于后端 |
| **LangGraph** | 状态图编排，构建复杂 Agent 工作流 | 像 Airflow 之于数据管道 |

### 3.1 LangChain（核心框架）

提供构建 LLM 应用的核心组件：
- **Model I/O**：调用 LLM（ChatOpenAI / ChatAnthropic）
- **Prompts**：管理 Prompt 模板（PromptTemplate / ChatPromptTemplate）
- **Output Parsers**：解析 LLM 输出（StrOutputParser / PydanticOutputParser）
- **Chains (LCEL)**：组合组件执行（管道符 `|`）
- **Memory**：对话历史管理
- **Retrievers**：文档检索
- **Tools**：工具调用

### 3.2 LangServe（API 部署）

将 LangChain 应用一键部署为 REST API，自动生成 `/invoke`、`/batch`、`/stream` 端点和 Playground 调试界面。基于 FastAPI，适合快速将 Chain 服务化。

### 3.3 LangSmith（监控评估）

LangSmith 是 LangChain 官方的可观测性平台：
- **追踪**：记录每次 Chain 调用的完整流程（输入/Prompt/输出/耗时/Token）
- **评估**：批量测试 Prompt 和 Chain 的效果
- **监控**：生产环境监控调用质量与成本

### 3.4 LangGraph（状态图编排）

当 Chain 的线性管道不够用时，LangGraph 提供基于状态图（StateGraph）的编排能力，支持循环、分支、人工干预——这是构建复杂 Agent 的核心工具。

---

## 四、核心概念

### 4.1 Components（模块化组件）

LangChain 把 LLM 应用的每个环节都封装为独立组件，每个组件可单独使用、可替换、可组合。

| 组件类别 | 作用 | 关键类 |
|---------|------|--------|
| Model I/O | 调用 LLM | ChatOpenAI / ChatAnthropic |
| Prompts | 管理 Prompt | PromptTemplate / ChatPromptTemplate |
| Parsers | 解析输出 | StrOutputParser / PydanticOutputParser |
| Memory | 对话记忆 | ConversationBufferMemory |
| Retrievers | 文档检索 | VectorStoreRetriever |
| Tools | 工具定义 | @tool / StructuredTool |
| Callbacks | 执行回调 | BaseCallbackHandler |

### 4.2 Chains（链式调用）

将多个组件串联执行。在 0.3 版本中，Chains 通过 LCEL（LangChain Expression Language）的管道符 `|` 实现：

```python
chain = prompt | model | parser
result = chain.invoke({"topic": "LangChain"})
```

### 4.3 Agents（智能体）

Agent = LLM + Tools + 循环决策。LLM 根据用户输入自主决定调用哪个工具、何时调用、如何组合结果。

> **说明**：本板块不深入 Agent 实现，Agent 将在独立板块讲解。Day09 会涉及 Tools 基础为 Agent 铺垫。

### 4.4 Memory（对话记忆）

管理多轮对话的上下文历史，让 LLM 能「记住」之前的对话。包括全量缓冲、滑动窗口、摘要压缩等策略。

### 4.5 Retrievers（检索器）

根据查询从文档库中检索相关内容，是 RAG（检索增强生成）的核心组件。

> **说明**：本板块 Day08 会涉及 Retrievers 基础用法，完整 RAG 系统在独立板块深入。

---

## 五、架构设计理念

### 5.1 组合性（Composability）

组件可像积木一样自由组合。任何一个 Runnable 都可以用 `|` 与其他 Runnable 连接，形成新的 Runnable：

```python
# 三个独立组件组合成一条链
chain = prompt_template | chat_model | output_parser
# 这条链本身也是 Runnable，可以继续组合
super_chain = chain | another_runnable
```

### 5.2 可扩展性

所有组件都基于抽象基类（如 `BaseChatModel`、`BaseOutputParser`），你可以继承基类实现自定义组件，与内置组件无缝配合。

### 5.3 模块化

每个组件独立可替换。例如 ChatModel 可以在 OpenAI 和 Anthropic 之间切换，而不影响 Prompt 和 Parser：

```python
# 切换模型只需改一行，其余代码不变
model = ChatOpenAI(model="gpt-4o-mini")      # 用 OpenAI
model = ChatAnthropic(model="claude-3-5-sonnet-20241022")  # 换成 Claude
```

---

## 六、LangChain 0.3 特性

### 6.1 LCEL 为核心

LCEL（LangChain Expression Language）是 0.3 的核心语法，用管道符 `|` 组合组件：

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("讲一个关于{topic}的笑话")
model = ChatOpenAI(model="gpt-4o-mini")
parser = StrOutputParser()

chain = prompt | model | parser   # ← LCEL 管道
chain.invoke({"topic": "程序员"})
```

### 6.2 Runnable 统一接口

所有组件都实现 Runnable 接口，统一支持四种调用方式：

| 方法 | 说明 | 同步/异步 |
|------|------|----------|
| `.invoke(input)` | 单次调用 | 同步 |
| `.batch(inputs)` | 批量调用 | 同步 |
| `.stream(input)` | 流式输出 | 同步 |
| `.ainvoke(input)` | 单次调用 | 异步 |

### 6.3 废弃 Legacy Chains

0.3 正式废弃旧版 Chain 类（如 `LLMChain`、`SequentialChain`），推荐用 LCEL 替代：

```python
# ❌ 已废弃（Legacy）
from langchain.chains import LLMChain
chain = LLMChain(llm=model, prompt=prompt)

# ✅ 推荐（LCEL）
chain = prompt | model
```

### 6.4 分包结构

| 包名 | 职责 | 安装 |
|------|------|------|
| `langchain-core` | 核心抽象（Runnable / Prompt / Parser 基类） | 随 langchain 安装 |
| `langchain` | 高层组件与 Chains | `pip install langchain` |
| `langchain-community` | 第三方集成（各种 Loader / VectorStore） | `pip install langchain-community` |
| `langchain-openai` | OpenAI 集成 | `pip install langchain-openai` |
| `langchain-anthropic` | Anthropic 集成 | `pip install langchain-anthropic` |

---

## 七、与直接调用 API 的对比

以「带系统提示的问答」为例，对比两种方式：

**直接调用 OpenAI SDK：**

```python
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "你是一个翻译助手"},
        {"role": "user", "content": "把'你好'翻译成英文"}
    ]
)
print(response.choices[0].message.content)
```

**使用 LangChain：**

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
model = ChatOpenAI(model="gpt-4o-mini")
result = model.invoke([
    SystemMessage(content="你是一个翻译助手"),
    HumanMessage(content="把'你好'翻译成英文")
])
print(result.content)
```

简单场景下差异不大，但一旦需要「Prompt 模板化 + 输出解析 + 批量处理 + 流式输出 + 记忆管理」，LangChain 的优势就体现出来了：

| 维度 | 直接调用 API | LangChain |
|------|-------------|-----------|
| Prompt 管理 | 字符串拼接，难复用 | PromptTemplate 模板化，可序列化 |
| 输出解析 | 手动解析字符串 | 内置 Parser，支持 Pydantic |
| 批量处理 | 手动写循环/并发 | `.batch()` 一行搞定 |
| 流式输出 | 手动处理 chunk | `.stream()` 统一接口 |
| 多模型切换 | 改大量代码 | 换一行类名即可 |
| 记忆管理 | 手动维护 messages | Memory 组件自动管理 |
| 错误重试 | 手动实现 | `.with_retry()` 一行配置 |
| 组件组合 | 过程式编程 | LCEL 管道式组合 |
| 可维护性 | 低，逻辑散落 | 高，组件解耦 |

---

## 八、环境搭建

### 8.1 安装 Python

要求 Python 3.10+，推荐 3.11 或 3.12：

```bash
python --version   # 确认版本 ≥ 3.10
```

### 8.2 创建虚拟环境

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 8.3 安装核心依赖

```bash
# 核心包
pip install langchain langchain-openai langchain-community python-dotenv pydantic

# 可选：其他模型 SDK
pip install langchain-anthropic       # Claude
pip install langchain-google-genai    # Gemini
```

### 8.4 配置 API Key

在项目根目录创建 `.env` 文件：

```bash
# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx

# Anthropic（可选）
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# 本地 Ollama（无需 Key，需先启动 ollama serve）
# OLLAMA_BASE_URL=http://localhost:11434/v1
```

用 `python-dotenv` 加载：

```python
from dotenv import load_dotenv
load_dotenv()   # 自动读取 .env 中的环境变量
```

### 8.5 项目结构设计

本板块的示例项目 ChainQA 推荐结构：

```
chainqa/
├── .env                    ← API Key 配置
├── requirements.txt        ← 依赖清单
├── pyproject.toml          ← 项目配置
├── src/
│   └── chainqa/
│       ├── __init__.py
│       ├── config.py       ← 配置管理
│       ├── models.py       ← 模型实例
│       ├── prompts/        ← Prompt 模板
│       ├── parsers/        ← 输出解析器
│       └── chains/         ← 链式调用
└── tests/
```

---

## 九、代码文件说明

| 文件 | 用途 | 关键内容 |
|------|------|---------|
| `Code/01_hello_langchain.py` | 第一个 LangChain 程序 | ChatOpenAI 调用 / invoke / stream / 与 OpenAI SDK 对比 |
| `Code/02_environment_setup.py` | 环境检查与配置工具 | EnvironmentChecker 类 / 检查 Python 版本与依赖 / 生成 requirements.txt 和 .env 模板 |
| `Code/03_project_structure.py` | 项目脚手架生成 | ProjectGenerator 类 / 生成 ChainQA 目录结构与配置文件 |
| `Code/README.md` | 环境搭建指南 | 详细安装步骤 / 常见问题排查 / IDE 配置建议 / 依赖版本兼容性 |

运行方式：

```bash
cd "Day01 - LangChain概述与环境搭建/Code"
python 01_hello_langchain.py
python 02_environment_setup.py
python 03_project_structure.py
```

---

## 关键知识点总结

### LangChain 生态速查

| 组件 | 一句话定位 | 是否本板块覆盖 |
|------|-----------|---------------|
| LangChain | 核心框架（组件 + LCEL） | ✅ 全部 |
| LangServe | 部署 Chain 为 REST API | Day11 基础 |
| LangSmith | 追踪、评估、监控 | Day12 集成 |
| LangGraph | 状态图编排 Agent | Day11 基础 |

### 核心组件速查表

| 组件 | 作用 | 关键类 | 对应天数 |
|------|------|--------|---------|
| Model I/O | 调用 LLM | ChatOpenAI | Day02 |
| Prompts | 管理 Prompt | ChatPromptTemplate | Day03 |
| Output Parsers | 解析输出 | PydanticOutputParser | Day04 |
| Chains (LCEL) | 组合组件 | 管道符 `\|` | Day05 |
| Memory | 对话记忆 | ConversationBufferMemory | Day06 |
| Document Loaders | 加载文档 | TextLoader | Day07 |
| Retrievers | 文档检索 | VectorStoreRetriever | Day08 |
| Tools | 工具调用 | @tool | Day09 |
| Callbacks | 执行回调 | BaseCallbackHandler | Day10 |

### LangChain 0.3 特性速查

| 特性 | 说明 |
|------|------|
| LCEL 核心 | 用 `\|` 组合组件 |
| Runnable 统一接口 | invoke / batch / stream / ainvoke |
| 废弃 Legacy Chains | LLMChain 等已废弃 |
| 分包结构 | core / langchain / community / partners |

### 与直接 API 调用对比

| 维度 | 直接调用 | LangChain |
|------|---------|-----------|
| Prompt | 手动拼接 | 模板化 |
| 解析 | 手动 | Parser 组件 |
| 批量 | 手动循环 | `.batch()` |
| 流式 | 手动 chunk | `.stream()` |
| 模型切换 | 改多处 | 换一行 |
| 组合 | 过程式 | LCEL 管道 |

### 环境配置清单

- [ ] Python 3.10+
- [ ] `pip install langchain langchain-openai langchain-community python-dotenv pydantic`
- [ ] `.env` 配置 `OPENAI_API_KEY`
- [ ] 虚拟环境已激活

---

## 实战练习

### 练习 1：运行并改造第一个程序

运行 `Code/01_hello_langchain.py`，然后改造它：
- 把模型从 `gpt-4o-mini` 换成 `gpt-4o`，对比输出质量与速度差异
- 把 System 提示改成「你是一个资深 Python 工程师」，测试对编程问题回答的影响

### 练习 2：完善环境检查工具

基于 `Code/02_environment_setup.py` 的 `EnvironmentChecker` 类扩展：
- 新增「检查是否安装了 langchain-anthropic」的方法
- 新增「检测 .env 中是否配置了 ANTHROPIC_API_KEY」的方法
- 把检测结果输出为 Markdown 格式的环境报告

### 练习 3：设计自己的项目结构

运行 `Code/03_project_structure.py` 生成 ChainQA 脚手架后：
- 在 `src/chainqa/` 下新增 `utils.py` 工具模块
- 在 `tests/` 下新增一个简单的测试文件
- 思考：为什么要把 prompts、parsers、chains 分目录管理？

---

> **下一步**：Day02 将深入 Model I/O 层，学习 ChatModel 的实例化、三种调用方式、模型参数配置与回退机制。
