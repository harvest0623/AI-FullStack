# Day05 - Chains 链式调用与 LCEL

LCEL（LangChain Expression Language）是 LangChain 0.3 的核心表达力，它用管道符 `|` 将 Prompt、Model、Parser 等组件组合为强大的链式调用。掌握 LCEL，意味着你能像搭积木一样，把零散的能力拼装成一条完整的处理流水线：从接收用户问题，到生成结构化答案，每一步都可组合、可复用、可观测。本章将带你从 Legacy Chain 走到 LCEL，理解 Runnable 接口的统一性，掌握顺序、并行、分支等链式模式，最终为 ChainQA 智能问答助手构建一条完整的多步推理链。

---

## 学习目标

- 理解 Chain 的核心思想：将多个组件按顺序串联，前一步输出作为后一步输入
- 了解 Legacy Chains（LLMChain / SequentialChain / TransformChain）及其被 LCEL 替代的原因
- 掌握 LCEL 管道符语法 `prompt | model | parser` 及其类型匹配规则
- 熟练使用 Runnable 核心组件：Passthrough / Parallel / Lambda / Branch
- 能够构建顺序、并行、混合、条件分支四种链式模式
- 掌握链的错误处理（with_retry / with_fallbacks）与可视化（get_graph）
- 为 ChainQA 构建复杂多步问答链

---

## 理论知识讲解

### 1. Chain 概念

Chain（链）是 LangChain 最早提出的核心抽象：**将多个组件按顺序串联执行**。

最经典的链就是 `Prompt → Model → Parser` 三段式：

- Prompt 模板接收用户输入，组装成完整提示
- Model 接收提示，调用 LLM 生成回复
- Parser 接收回复，解析为结构化数据

```
用户输入 → [Prompt] → [Model] → [Parser] → 结构化输出
```

链式调用的价值在于：

- **可组合**：复杂任务拆解为多个小步骤，每步独立可替换
- **可复用**：一条链可以在不同场景重复使用
- **可维护**：每步职责单一，便于调试和迭代

### 2. Legacy Chains（已废弃但需了解）

在 LangChain 0.3 之前，链通过专门的类实现。这些类在 0.3 中已被 LCEL 替代，但你可能在旧代码或教程中遇到，需要了解。

| Legacy Chain | 作用 | 0.3 中的替代方案 |
|--------------|------|----------------|
| `LLMChain` | 最基本的链（Prompt + Model） | `prompt \| model \| parser` |
| `SequentialChain` | 顺序执行多个链 | `chain_a \| chain_b \| chain_c` |
| `TransformChain` | 自定义转换函数 | `RunnableLambda(func)` |
| `LLMRouterChain` | 根据输入路由到不同链 | `RunnableBranch` |

Legacy 写法示例（了解即可，不推荐使用）：

```python
# 旧写法：LLMChain（已废弃）
from langchain.chains import LLMChain
chain = LLMChain(llm=model, prompt=prompt)
result = chain.run(question="什么是 LangChain？")

# 新写法：LCEL（推荐）
chain = prompt | model | parser
result = chain.invoke({"question": "什么是 LangChain？"})
```

**为什么 LCEL 更好？**

- 统一的 Runnable 接口（invoke / batch / stream / ainvoke）
- 原生支持异步和流式输出
- 更容易组合和调试
- 更好的类型推断和可视化

### 3. LCEL 核心概念（重点）

LCEL（LangChain Expression Language）是 LangChain 0.3 的核心表达力，用管道符 `|` 组合组件。

#### 3.1 管道符组合

LCEL 借鉴 Unix 管道的理念：前一步的输出自动作为后一步的输入。

```python
chain = prompt | model | parser
```

等价于：

```python
# 手动逐步调用
prompt_value = prompt.invoke({"question": "..."})
message = model.invoke(prompt_value)
result = parser.invoke(message)
```

#### 3.2 Runnable 接口

**每个 LCEL 组件都实现了 Runnable 接口**，这是 LCEL 统一性的根基。Runnable 接口提供以下方法：

| 方法 | 说明 | 同步/异步 |
|------|------|----------|
| `.invoke(input)` | 单次调用 | 同步 |
| `.batch(inputs)` | 批量调用 | 同步 |
| `.stream(input)` | 流式输出 | 同步 |
| `.ainvoke(input)` | 单次调用 | 异步 |
| `.abatch(inputs)` | 批量调用 | 异步 |
| `.astream(input)` | 流式输出 | 异步 |

这意味着任何 Runnable（无论是 prompt、model、parser 还是整条链）都支持这 6 种调用方式。

#### 3.3 LCEL 的优势

| 优势 | 说明 |
|------|------|
| 统一接口 | 所有组件支持 invoke/batch/stream |
| 原生异步 | ainvoke/abatch/astream 开箱即用 |
| 流式支持 | `.stream()` 逐 token 返回 |
| 批量支持 | `.batch()` 并行处理多个输入 |
| 可组合 | 管道符任意组合，链可以嵌套 |
| 可观测 | get_graph / input_schema / output_schema |

### 4. LCEL 基本语法

最基础的三步管道：

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. 定义 Prompt 模板
prompt = ChatPromptTemplate.from_template("请用一句话解释：{topic}")

# 2. 创建模型
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 3. 创建解析器
parser = StrOutputParser()

# 4. 用管道符组合
chain = prompt | model | parser

# 5. 调用
result = chain.invoke({"topic": "LangChain"})
```

**类型匹配规则**：每步的输出类型必须能被下一步接收。

```
ChatPromptTemplate → ChatModel → BaseOutputParser
     ↓                  ↓              ↓
  PromptValue       BaseMessage       str/对象
```

- `ChatPromptTemplate.invoke(dict)` 返回 `ChatPromptValue`
- `ChatModel.invoke(ChatPromptValue)` 返回 `BaseMessage`
- `StrOutputParser.invoke(BaseMessage)` 返回 `str`

### 5. Runnable 核心组件

LCEL 提供一组 Runnable 工具组件，用于构建更复杂的链。

| 组件 | 作用 | 典型场景 |
|------|------|---------|
| `RunnablePassthrough` | 将输入原样传递 | 保留原始输入同时并行检索 |
| `RunnableParallel` | 并行执行多个 Runnable | 同时检索 + 重写问题 |
| `RunnableLambda` | 包装普通函数为 Runnable | 自定义处理逻辑 |
| `RunnableBranch` | 条件分支 | 根据问题类型路由 |
| `RunnableEach` | 对列表每个元素执行 | 批量处理 |

#### 5.1 RunnablePassthrough

`RunnablePassthrough()` 将输入原样传递，常用于在并行管道中保留原始输入。

```python
from langchain_core.runnables import RunnablePassthrough

# 同时传递用户问题和检索结果
chain = RunnablePassthrough.assign(
    question=lambda x: x["question"]  # 保留原始问题
)
```

`.assign(**kwargs)` 在输入上添加额外字段，不覆盖原输入：

```python
# 输入: {"question": "..."}
# 输出: {"question": "...", "context": "检索结果"}
chain = RunnablePassthrough.assign(
    context=lambda x: retrieve(x["question"])
)
```

#### 5.2 RunnableParallel

并行执行多个 Runnable，输出为字典（key 对应每个链名）。

```python
from langchain_core.runnables import RunnableParallel

# 同时执行两个链
parallel = RunnableParallel({
    "answer": qa_chain,        # 问答链
    "summary": summary_chain,  # 摘要链
})
result = parallel.invoke({"question": "..."})
# result = {"answer": "...", "summary": "..."}
```

#### 5.3 RunnableLambda

将普通 Python 函数包装为 Runnable，使其支持 invoke/batch/stream。

```python
from langchain_core.runnables import RunnableLambda

def word_count(text: str) -> int:
    return len(text.split())

count_runnable = RunnableLambda(word_count)
count = count_runnable.invoke("hello world")  # 2
```

#### 5.4 RunnableBranch

条件分支，根据条件选择不同 Runnable 执行。

```python
from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda x: "代码" in x["question"], code_chain),
    (lambda x: "翻译" in x["question"], translate_chain),
    default_chain,  # 默认分支
)
```

### 6. 链式调用模式

#### 6.1 顺序模式

最简单的模式，组件依次执行：

```python
chain = a | b | c
```

#### 6.2 并行模式

多个链同时执行，结果合并为字典：

```python
chain = RunnableParallel({"a": chain_a, "b": chain_b})
```

#### 6.3 混合模式

并行 + 顺序组合，先并行收集信息，再顺序处理：

```python
chain = (
    RunnableParallel({
        "context": retriever,
        "question": RunnablePassthrough()
    })
    | prompt
    | model
    | parser
)
```

#### 6.4 条件分支模式

根据输入特征选择不同处理链：

```python
chain = RunnableBranch(
    (condition_1, chain_1),
    (condition_2, chain_2),
    default_chain,
)
```

#### 6.5 传递模式

用 `RunnablePassthrough.assign()` 在输入上添加额外字段，常用于在管道中间补充上下文：

```python
chain = (
    RunnablePassthrough.assign(context=lambda x: retrieve(x["question"]))
    | prompt
    | model
    | parser
)
```

### 7. RunnablePassthrough 详解

`RunnablePassthrough` 在管道中传递原始输入，是构建检索增强链的关键工具。

**典型场景：同时传递用户问题和检索结果**

```python
from langchain_core.runnables import RunnablePassthrough

# 假设 retriever 是一个检索器
chain = (
    {
        "context": retriever,             # 检索结果
        "question": RunnablePassthrough() # 原始问题
    }
    | prompt
    | model
    | parser
)

# 输入是字符串 "什么是 LangChain？"
# 第一步并行：context=检索结果，question="什么是 LangChain？"
# 然后传给 prompt 模板
```

`.assign()` 在不丢失原输入的情况下添加字段：

```python
# 输入: {"question": "..."}
chain = RunnablePassthrough().assign(
    word_count=lambda x: len(x["question"].split())
)
# 输出: {"question": "...", "word_count": 3}
```

### 8. RunnableParallel 详解

并行执行多个链，所有链共享同一输入，输出合并为字典。

```python
from langchain_core.runnables import RunnableParallel

# 同时检索 + 重写问题
chain = RunnableParallel({
    "original_answer": qa_chain,
    "rewritten_question": rewrite_chain,
    "context": retriever,
})
```

**注意**：并行执行的链之间无依赖关系。如果有依赖，请用顺序模式。

### 9. 链的可视化

LCEL 链自带结构描述能力，便于调试和文档化。

```python
# 获取链的结构图
graph = chain.get_graph()
print(graph)

# 链的输入输出 Schema
print(chain.input_schema)   # 输入类型（Pydantic 模型）
print(chain.output_schema)  # 输出类型（Pydantic 模型）
```

`get_graph()` 返回一个图结构对象，包含节点和边，可用于绘制流程图。若需可视化图片，可安装 `pygraphviz` 并调用 `chain.get_graph().draw_png("chain.png")`。

### 10. 错误处理与重试

#### 10.1 with_retry 重试

```python
# 失败时自动重试
robust_model = model.with_retry(
    stop_after_attempt=3,  # 最多重试 3 次
    wait_exponential_jitter=True,  # 指数退避
)

chain = prompt | robust_model | parser
```

#### 10.2 with_fallbacks 回退

当主链失败时，自动切换到备用链：

```python
# 主模型失败时回退到备用模型
primary_model = ChatOpenAI(model="gpt-4o")
fallback_model = ChatOpenAI(model="gpt-4o-mini")
robust_model = primary_model.with_fallbacks([fallback_model])

chain = prompt | robust_model | parser
```

### 11. LCEL 高级技巧

#### 11.1 动态路由

根据输入内容动态选择处理链：

```python
def route(info):
    if "代码" in info["question"]:
        return "code"
    elif "翻译" in info["question"]:
        return "translate"
    return "default"

chain = (
    {"destination": RunnableLambda(route)}
    | RunnableBranch(
        (lambda x: x["destination"] == "code", code_chain),
        (lambda x: x["destination"] == "translate", translate_chain),
        default_chain,
    )
)
```

#### 11.2 链的组合与嵌套

链本身也是 Runnable，可以作为更大链的子组件：

```python
# 子链
sub_chain = prompt | model | parser

# 父链包含子链
parent_chain = (
    RunnablePassthrough.assign(processed=sub_chain)
    | another_prompt
    | another_model
    | another_parser
)
```

#### 11.3 自定义 Runnable

继承 `RunnableBase` 或用 `RunnableLambda` 实现自定义逻辑：

```python
from langchain_core.runnables import RunnableLambda

# 用 RunnableLambda 包装自定义逻辑（推荐，最简单）
def my_logic(x):
    # 自定义处理
    return result

my_runnable = RunnableLambda(my_logic)
```

---

## 代码文件说明

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_lcel_basics.py` | LCEL 基础语法、三步管道、invoke/batch/stream | 基础问答链 |
| `02_runnable_components.py` | Passthrough/Parallel/Lambda 组件详解 | 并行问答+检索链 |
| `03_chain_patterns.py` | 顺序/并行/混合/分支四种模式 | 问题类型路由 |
| `04_advanced_chains.py` | 多步推理链、错误处理、可视化 | ChainQA 复杂问答 |

运行方式：

```bash
cd "Day05 - Chains链式调用与LCEL/Code"
python 01_lcel_basics.py
```

---

## 关键知识点总结

### Legacy vs LCEL 对比

| 维度 | Legacy Chain | LCEL |
|------|-------------|------|
| 语法 | 类实例化（LLMChain(...)） | 管道符（prompt \| model \| parser） |
| 接口 | 各类接口不统一（run/apply/.__call__） | 统一 Runnable 接口 |
| 异步 | 部分支持 | 原生 ainvoke/abatch/astream |
| 流式 | 需额外配置 | `.stream()` 开箱即用 |
| 批量 | 部分支持 | `.batch()` 原生支持 |
| 组合性 | 受限 | 任意嵌套 |
| 可视化 | 无 | get_graph / input_schema |
| 推荐度 | 不推荐（仅维护旧代码） | 强烈推荐 |

### Runnable 组件速查表

| 组件 | 输入 | 输出 | 用途 |
|------|------|------|------|
| `RunnablePassthrough` | x | x（原样） | 传递原始输入 |
| `RunnablePassthrough.assign()` | dict | dict+新字段 | 添加字段保留原输入 |
| `RunnableParallel` | x | dict | 并行执行多链 |
| `RunnableLambda` | 任意 | 函数返回值 | 包装自定义函数 |
| `RunnableBranch` | x | 所选链的输出 | 条件分支 |
| `RunnableEach` | list | list | 批量处理列表 |

### LCEL 模式速查表

| 模式 | 语法 | 适用场景 |
|------|------|---------|
| 顺序 | `a \| b \| c` | 流水线处理 |
| 并行 | `RunnableParallel({...})` | 无依赖的多任务 |
| 混合 | `RunnableParallel({...}) \| prompt \| model` | 先收集再处理 |
| 分支 | `RunnableBranch(...)` | 根据输入路由 |
| 传递 | `RunnablePassthrough.assign(...)` | 补充上下文 |

### 管道符类型匹配规则

| 上一步输出类型 | 可接收的下一步 |
|---------------|---------------|
| `str` | RunnableLambda / 任何接受 str 的组件 |
| `dict` | ChatPromptTemplate / RunnableParallel |
| `ChatPromptValue` | ChatModel |
| `BaseMessage` | OutputParser / 下一个 ChatModel |
| 自定义对象 | RunnableLambda 处理 |

### 错误处理配置

| 方法 | 作用 | 典型用法 |
|------|------|---------|
| `.with_retry(stop_after_attempt=N)` | 失败重试 | 应对网络抖动 |
| `.with_fallbacks([backup])` | 回退备用 | 主模型不可用时降级 |
| `try/except` 包裹 invoke | 手动处理 | 自定义错误逻辑 |

---

## 实战练习

### 练习 1：构建多语言问答链

用 LCEL 构建一条链，根据用户输入的语言（中文/英文）自动选择对应语言回答。

提示：
- 用 `RunnableBranch` 实现语言路由
- 准备中文和英文两个 Prompt 模板
- 测试输入："What is LangChain?" 和 "什么是 LangChain？"

### 练习 2：构建带重试和回退的健壮链

为 ChainQA 的问答链添加容错能力：
- 主模型用 `gpt-4o`，失败时回退到 `gpt-4o-mini`
- 对主模型添加 3 次重试
- 模拟一次失败场景验证回退生效

### 练习 3：构建并行分析链

构建一条链，对同一问题并行执行三个任务：
- 生成答案
- 生成摘要
- 提取关键词

要求：用 `RunnableParallel` 并行执行，最终输出一个包含三个字段的字典。

---

## 小结

LCEL 是 LangChain 0.3 的灵魂。管道符 `|` 让组件组合变得直观，Runnable 接口让所有组件共享 invoke/batch/stream 能力。掌握 Passthrough、Parallel、Lambda、Branch 四大组件后，你能构建从简单问答到复杂多步推理的任意链。下一章我们将为链加上"记忆"，让 ChainQA 能记住对话历史。
