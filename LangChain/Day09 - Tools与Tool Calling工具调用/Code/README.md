# Day09 Code - Tools 与 Tool Calling 代码示例

> 本目录包含 Day09 全部可运行 Python 代码，演示 LangChain Tool 定义、绑定、调用与 Chain 集成

## 文件清单

| 文件 | 内容 | 是否需要 API Key | 场景 |
|------|------|-----------------|------|
| `01_define_tools.py` | 三种工具定义方式 + Pydantic 参数 Schema | 否（直接调用工具） | 天气/计算器/文本搜索 |
| `02_tool_calling.py` | Tool Calling 完整七步流程 + 消息流追踪 | 是 | 用户问天气→调用工具→回复 |
| `03_builtin_tools.py` | 内置工具使用 + BuiltinToolkit 封装 | 部分需要 | 搜索/Wikipedia/计算器 |
| `04_custom_tools.py` | 自定义工具 + Chain 集成（ToolCallingChain） | 是 | ChainQA 工具增强问答 |

## 运行顺序建议

```
01_define_tools.py   ← 先理解工具如何定义
      │
      ▼
02_tool_calling.py   ← 再看工具如何被模型调用（核心）
      │
      ▼
03_builtin_tools.py  ← 然后了解开箱即用的内置工具
      │
      ▼
04_custom_tools.py   ← 最后学习工具与 Chain 集成
```

## 环境准备

```bash
# 核心依赖
pip install langchain langchain-openai langchain-community python-dotenv pydantic

# 内置工具可选依赖
pip install duckduckgo-search wikipedia

# 配置 API Key（在项目根目录 .env 文件）
# OPENAI_API_KEY=sk-xxxxxxxx
```

## 运行示例

```bash
# 进入目录
cd "d:\Coding\AI-FullStack\LangChain\Day09 - Tools与Tool Calling工具调用\Code"

# 1. 工具定义演示（无需 API Key）
python 01_define_tools.py

# 2. Tool Calling 完整流程（需要 API Key）
python 02_tool_calling.py

# 3. 内置工具演示
python 03_builtin_tools.py

# 4. 自定义工具 + Chain 集成（需要 API Key）
python 04_custom_tools.py
```

## Tool Calling 指南

### Tool 定义方式选择决策表

| 场景 | 推荐方式 | 理由 |
|------|---------|------|
| 新写工具函数 | `@tool` 装饰器 | 最简洁，自动生成 Schema |
| 包装现成函数 | `Tool` 类 | 无需改动原函数 |
| 复杂参数、需复用 Schema | `StructuredTool` | 显式 Schema 控制最精细 |
| 需要枚举/可选参数 | `@tool(args_schema=...)` | Pydantic 灵活定义 |

### Tool Calling 完整流程图解

```
┌─────────────────────────────────────────────────────┐
│ 1. 用户提问：HumanMessage(content="...")             │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ 2-3. model_with_tools.invoke(messages)              │
│      → AIMessage(tool_calls=[{name, args, id}])     │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ 4. 执行工具：tool_map[name].invoke(args)            │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ 5. 包装结果：ToolMessage(content=result,            │
│             tool_call_id=tc["id"])  ← 必须对应！    │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ 6. 消息流：[Human, AIMessage(tool_calls),           │
│            ToolMessage, ...]                        │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ 7. model_with_tools.invoke(messages)                │
│    → AIMessage(content="最终自然语言回复")           │
└─────────────────────────────────────────────────────┘
```

### 参数 Schema 设计规范

```python
from typing import Literal
from pydantic import BaseModel, Field

class GoodSchema(BaseModel):
    # ✅ 每个字段都有描述
    city: str = Field(description="城市中文名")
    # ✅ 可选参数有默认值
    top_k: int = Field(default=3, description="返回数量")
    # ✅ 枚举值用 Literal 约束
    unit: Literal["celsius", "fahrenheit"] = Field(default="celsius")

class BadSchema(BaseModel):
    # ❌ 无描述，LLM 不知道字段含义
    city: str
    # ❌ 用 Any 类型，无法约束
    data: Any
```

### 错误处理最佳实践

```python
@tool
def safe_tool(query: str) -> str:
    """工具描述"""
    try:
        # 业务逻辑
        return do_something(query)
    except Exception as e:
        # ✅ 返回错误信息，而非抛异常中断流程
        # 让 LLM 知道失败，可决定重试或换工具
        return f"工具执行失败：{e}。建议：检查输入后重试。"
```

### Tool 与 Agent 关系说明

```
本天（Day09）              后续 Agent 板块
─────────────              ──────────────
单次工具调用                多轮循环调用
手动执行工具                框架自动执行
无观察-反思                 观察→反思→再调用
ToolCallingChain           AgentExecutor / LangGraph Agent
```

> 本天掌握的 Tool 定义和单次调用是 Agent 的基础。Agent 只是在此基础上增加"循环决策"——模型观察工具结果后决定是否继续调用其他工具，直到能给出最终答案。

### 与后续 Agent 板块衔接

- **本天学完**：能定义工具、手动实现单次 Tool Calling 流程
- **Agent 板块**：用 `AgentExecutor` 或 `LangGraph` 自动化多轮工具调用循环
- **关键区别**：本天手动写循环（如 `04_custom_tools.py`），Agent 框架帮你自动管理循环、终止条件、错误恢复

## 常见问题

**Q1：模型不调用工具，直接回答怎么办？**
- 检查工具描述是否清晰（描述要说明"何时使用"）
- 确认 `.bind_tools()` 已正确绑定
- 尝试用 `gpt-4o` 等更强模型

**Q2：ToolMessage 报错 "tool_call_id not found"？**
- 检查 `tool_call_id` 是否与 `AIMessage.tool_calls[i]["id"]` 完全一致
- 确认消息顺序：AIMessage(tool_calls) 必须在 ToolMessage 之前

**Q3：多个工具描述相似，模型选错？**
- 在描述中明确区分使用场景
- 命名要语义化（`search_weather` vs `search_news`）
- 必要时在描述中给出"不适用"场景

## 学习产出

完成本目录代码后，你应能：
- [ ] 用三种方式定义 Tool
- [ ] 用 Pydantic 设计工具参数 Schema
- [ ] 手动实现 Tool Calling 七步流程
- [ ] 使用内置工具集
- [ ] 把工具调用封装为 Chain（ToolCallingChain 模式）
- [ ] 处理工具执行错误
