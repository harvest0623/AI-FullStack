# Day09 - Tools 与 Tool Calling 工具调用

> 让 LLM 从"只能说"进化为"能做事"：掌握 LangChain 框架层面的 Tool 定义、绑定、调用与集成

## 本章简介

单纯的 LLM 只能基于训练数据"说话"，无法获取实时信息、执行计算、查询数据库或调用外部 API。**Tools（工具）** 的出现，让 LLM 拥有了"动手能力"——它可以根据用户意图选择合适的工具、生成调用参数、执行工具并把结果融入最终回复，从而完成"查询天气""检索文档""执行计算"等真实任务。

本天聚焦 **LangChain 框架层面的 Tool 定义和调用基础**：我们用三种方式定义工具，用 `.bind_tools()` 把工具绑定到模型，完整演示 Tool Calling 的七步流程，并介绍内置工具集和自定义工具与 Chain 的集成方式。**重要提醒**：本天只讲单次工具调用与 Chain 集成，不深入 Agent 系统（Agent = LLM + Tools + 循环多轮调用），Agent 将在后续独立板块深入讲解。

---

## 学习目标

完成本章后，你应能够：

1. 理解 Tool 的概念、原理，以及 Tool 与 Agent 的本质区别
2. 使用三种方式定义工具：`@tool` 装饰器、`Tool` 类、`StructuredTool`
3. 用 Pydantic 模型为工具设计参数 Schema（必需/可选参数、字段描述）
4. 使用 `.bind_tools()` 把工具绑定到 ChatModel
5. 手动实现 Tool Calling 完整七步流程（含 ToolMessage 回传）
6. 使用 LangChain 内置工具集（搜索/Wikipedia/计算器）
7. 把工具调用封装为 Chain，实现 ChainQA 的工具增强问答
8. 处理工具执行错误，并理解 Tool 与后续 Agent 板块的衔接

---

## 理论知识讲解

### 1. Tool 概念与原理

**定义**：Tool（工具）是让 LLM 调用外部函数 / API / 服务以获取信息或执行操作的封装单元。每个 Tool 都有名称、描述、参数 Schema 和执行函数。

**原理（Tool Calling 核心流程）**：

```
用户提问
   │
   ▼
LLM 分析意图 → 决定调用哪个工具
   │
   ▼
LLM 返回 tool_calls（工具名 + 参数 JSON）
   │
   ▼
外部执行工具：tool.invoke(tool_call_args)
   │
   ▼
工具结果包装为 ToolMessage
   │
   ▼
ToolMessage 发回 LLM
   │
   ▼
LLM 基于工具结果生成最终自然语言回复
```

**Tool vs Agent（关键区分）**：

| 维度 | Tool（工具） | Agent（智能体） |
|------|-------------|----------------|
| 角色 | 被调用的函数 | 调用 Tool 的决策者 |
| 决策 | 不做决策，只执行 | 决定调用哪个工具、何时调用 |
| 循环 | 单次执行 | 多轮循环（调用→观察→再调用） |
| 本天范围 | ✅ 重点讲解 | ❌ 后续独立板块 |

> 本天只讲"单次工具调用"：模型决定调用 → 执行 → 返回。Agent 的多轮循环推理将在 Agent 板块深入。

### 2. LangChain Tool 定义方式（三种）

LangChain 0.3 提供三种定义工具的方式，推荐优先使用 `@tool` 装饰器。

#### 方式一：`@tool` 装饰器（最简洁，推荐）

```python
from langchain_core.tools import tool

@tool
def search_weather(city: str) -> str:
    """查询指定城市的天气"""
    return f"{city}今天晴，25度"
```

- 自动从 **docstring** 生成工具描述（LLM 据此选择工具）
- 自动从 **类型注解** 生成参数 Schema
- 复杂参数可用 Pydantic 模型定义：

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class SearchInput(BaseModel):
    query: str = Field(description="搜索关键词")
    top_k: int = Field(default=3, description="返回结果数量")

@tool(args_schema=SearchInput)
def search_docs(query: str, top_k: int = 3) -> str:
    """在知识库中检索文档"""
    return f"已检索关于 {query} 的 {top_k} 条结果"
```

#### 方式二：`Tool` 类（传统方式）

```python
from langchain.tools import Tool

def search_func(query: str) -> str:
    return f"搜索结果：{query}"

search_tool = Tool(
    name="search",
    func=search_func,
    description="用于搜索信息的工具",
)
```

适合把现成函数快速包装为工具，但参数 Schema 不如 `@tool` 精细。

#### 方式三：`StructuredTool`（结构化工具）

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class CalcInput(BaseModel):
    expression: str = Field(description="数学表达式，如 1+2*3")

def calc_func(expression: str) -> str:
    return str(eval(expression))

calc_tool = StructuredTool.from_function(
    func=calc_func,
    name="calculator",
    description="计算数学表达式",
    args_schema=CalcInput,
)
```

显式指定 `args_schema`，参数控制最精细，适合复杂参数场景。

#### 三种方式对比

| 方式 | 简洁性 | 参数 Schema 精细度 | 推荐场景 |
|------|--------|-------------------|---------|
| `@tool` 装饰器 | ⭐⭐⭐ | 高（自动+可定制） | 优先选择 |
| `Tool` 类 | ⭐⭐ | 低（仅字符串描述） | 快速包装现成函数 |
| `StructuredTool` | ⭐ | 最高（显式 Schema） | 复杂参数、需要复用 Schema |

### 3. Tool 参数 Schema 设计

参数 Schema 决定 LLM 能否正确生成调用参数。设计规范：

- **类型注解**：使用 `str` / `int` / `float` / `bool` / `List` / `Dict`，避免 `Any`
- **字段描述**：每个字段都用 `Field(description=...)` 说明含义
- **必需 vs 可选**：必需参数无默认值；可选参数用 `Field(default=...)`
- **枚举约束**：用 `Literal` 或 `Enum` 限制取值范围

```python
from typing import Literal
from pydantic import BaseModel, Field

class QueryInput(BaseModel):
    city: str = Field(description="要查询的城市中文名，如'北京'")
    unit: Literal["celsius", "fahrenheit"] = Field(
        default="celsius", description="温度单位"
    )
    detailed: bool = Field(default=False, description="是否返回详细预报")
```

### 4. `.bind_tools()` 绑定工具到模型

绑定后，模型"知道"有哪些工具可用，并能在回复时返回 `tool_calls`。

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
model_with_tools = model.bind_tools([search_weather, calc_tool])

# 模型现在能根据问题决定调用哪个工具
response = model_with_tools.invoke("北京天气怎么样？")
# response.tool_calls 包含工具调用信息
```

### 5. Tool Calling 完整流程（重点）

完整流程分七步，是本天核心：

```python
from langchain_core.messages import HumanMessage, ToolMessage

# 步骤1：用户提问
messages = [HumanMessage(content="北京今天天气怎么样？")]

# 步骤2-3：模型分析意图，返回 tool_calls
response = model_with_tools.invoke(messages)
# response.tool_calls = [{"name": "search_weather", "args": {"city": "北京"}, "id": "xxx"}]

# 步骤4：执行工具
for tool_call in response.tool_calls:
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    # 根据名字找到对应工具并执行
    result = tool_map[tool_name].invoke(tool_args)

    # 步骤5：包装为 ToolMessage
    messages.append(ToolMessage(
        content=result,
        tool_call_id=tool_call["id"],  # 关联对应的 tool_call
    ))

# 步骤6：把 ToolMessage 发回模型
messages.append(response)  # 先加入模型的 AI 回复（含 tool_calls）
# 注：实际顺序为 [Human, AI(tool_calls), ToolMessage, ...]

# 步骤7：模型基于工具结果生成最终回复
final_response = model_with_tools.invoke(messages)
```

### 6. ToolMessage 消息类型

`ToolMessage` 是专门用于承载工具执行结果的消息类型：

| 字段 | 说明 |
|------|------|
| `content` | 工具执行结果（字符串） |
| `tool_call_id` | 关联模型发起的 `tool_call` 的 id，必须对应 |

> 缺少 `tool_call_id` 会导致模型无法关联结果与请求，调用失败。

### 7. 内置工具集速查

LangChain Community 提供常用内置工具，开箱即用：

| 工具 | 类 | 安装依赖 | 用途 |
|------|----|---------|------|
| DuckDuckGo 搜索 | `DuckDuckGoSearchRun` | `duckduckgo-search` | 免费网页搜索 |
| Tavily 搜索 | `TavilySearchResults` | `tavily-python` | AI 专用搜索（需 Key） |
| Wikipedia 查询 | `WikipediaQueryRun` + `WikipediaAPIWrapper` | `wikipedia` | 百科查询 |
| 计算器 | `Calculator`（LLMMathChain，0.3 已迁移） | - | 数学计算 |
| Python REPL | `PythonREPL` | - | 执行 Python 代码（慎用） |
| Arxiv 查询 | `ArxivQueryRun` + `ArxivAPIWrapper` | `arxiv` | 论文检索 |

### 8. 多工具选择策略

LLM 靠**工具描述**选择工具，因此：

- **描述要清晰**：写清工具能做什么、何时该用
- **命名要语义化**：`search_weather` 优于 `tool1`
- **避免功能重叠**：两个工具描述相似会让模型困惑
- **提供示例**：复杂工具在 docstring 中给出使用示例

### 9. Tool 错误处理

工具执行失败时，应返回错误信息（而非抛异常中断流程），让 LLM 知道失败并决定下一步：

```python
@tool
def query_db(sql: str) -> str:
    """执行 SQL 查询"""
    try:
        return execute_sql(sql)
    except Exception as e:
        return f"工具执行失败：{e}。请检查 SQL 语法后重试。"
```

### 10. Tool 与 Chain 的集成

将工具调用封装为 Chain（`ToolCallingChain` 模式），实现"根据问题选择工具→执行→生成回答"的闭环：

```python
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

def route_and_execute(input_dict):
    question = input_dict["question"]
    response = model_with_tools.invoke([HumanMessage(content=question)])
    # 执行工具并回传...
    return final_answer

chain = RunnablePassthrough() | RunnableLambda(route_and_execute)
```

### 11. 与 Agent 的关系

```
Tool（本天）         Agent（后续板块）
─────────────       ──────────────
单次调用             多轮循环
手动执行工具         框架自动执行
无观察-反思          观察→反思→再调用
```

本天掌握的 Tool 定义和调用基础，是后续 Agent 板块的基石——Agent 只是在此基础上加了"循环决策"。

---

## 代码文件说明

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_define_tools.py` | 三种工具定义方式 + Pydantic 参数 Schema | 天气查询/计算器/文本搜索 |
| `02_tool_calling.py` | Tool Calling 完整七步流程 + 消息流追踪 | 用户问天气→调用工具→返回结果 |
| `03_builtin_tools.py` | 内置工具使用 + BuiltinToolkit 封装 | 搜索/Wikipedia/计算器 |
| `04_custom_tools.py` | 自定义工具 + Chain 集成（ToolCallingChain） | ChainQA 工具增强问答 |

---

## 关键知识点总结

### Tool 定义方式对比表

| 方式 | 关键 API | 参数 Schema | 推荐度 |
|------|---------|------------|--------|
| `@tool` 装饰器 | `from langchain_core.tools import tool` | 自动+可定制 | ⭐⭐⭐ |
| `Tool` 类 | `from langchain.tools import Tool` | 低 | ⭐ |
| `StructuredTool` | `StructuredTool.from_function(...)` | 最高 | ⭐⭐ |

### Tool Calling 流程图

```
[HumanMessage] → [model.bind_tools()] → [AIMessage(tool_calls)]
                                              │
                                              ▼
                                    [tool.invoke(args)]
                                              │
                                              ▼
                                    [ToolMessage(content, tool_call_id)]
                                              │
                                              ▼
                                    [model.invoke(messages)]
                                              │
                                              ▼
                                    [AIMessage(最终回复)]
```

### 内置工具速查表

见上文"内置工具集速查"小节。

### Tool 参数 Schema 设计规范

1. 类型明确，禁用 `Any`
2. 每个字段必须有 `description`
3. 必需参数无默认值，可选参数有默认值
4. 枚举值用 `Literal` 约束
5. 复杂结构用嵌套 Pydantic 模型

### Tool vs Agent 关系说明

| 维度 | Tool | Agent |
|------|------|-------|
| 定位 | 能力单元 | 决策大脑 |
| 调用次数 | 单次 | 多轮 |
| 实现复杂度 | 低 | 高 |
| 本板块 | ✅ Day09 | 后续独立板块 |

---

## 实战练习

### 练习一：定义一个汇率查询工具

用 `@tool` 装饰器定义 `query_exchange_rate` 工具，参数包括 `from_currency`（源货币）、`to_currency`（目标货币）、`amount`（金额，可选默认 1）。要求：用 Pydantic 模型定义参数 Schema，每个字段有描述。绑定到模型并测试"100 美元等于多少人民币"。

### 练习二：实现双工具调用流程

定义"天气查询"和"计算器"两个工具，绑定到模型。实现完整 Tool Calling 流程：当用户问"北京天气温度的两倍是多少"时，模型应先调用天气工具获取温度，再调用计算器计算两倍值。追踪完整消息流。

### 练习三：为 ChainQA 添加工具错误处理

基于 `04_custom_tools.py`，给数据库查询工具添加错误处理：当 SQL 语法错误时，返回友好错误信息，让模型在下一轮中修正 SQL 并重试（提示：可手动实现两轮调用模拟 Agent 行为）。

---

## 与后续板块衔接

本天掌握了 Tool 的定义和**单次调用**。后续 **Agent 板块** 将在此基础上：

- 引入 **循环决策**：模型观察工具结果后决定是否再调用
- 使用 **LangGraph** 或 **AgentExecutor** 实现多轮工具调用
- 处理 **工具选择冲突**、**最大轮数限制**、**人工干预**等复杂场景
- 构建 **ReAct Agent**、**Function Calling Agent** 等完整智能体

打好本天的 Tool 基础，Agent 学习将水到渠成。

---

**下一站**：[Day10 - Callbacks 与 Streaming 回调流式](../Day10%20-%20Callbacks与Streaming回调流式/README.md)
