# Function Calling 模块 —— 让模型学会"拿起工具"

> 本模块用 **10 天**，从零到一掌握 **Function/Tool Calling（函数调用）**。
> Function Calling 是所有 Agent / 多智能体 / 工具链的**地基**：让 LLM 不只输出文字，
> 还能输出一个"结构化指令"去调用你提供的函数，把结果喂回模型继续思考。
> 前面学的 AutoGen / ReAct / ToolCalling 内部正是基于这套机制。

## 为什么学 Function Calling

- **连接真实世界**：模型不知道天气/库存/数据库，但可以"请求"去调用你的函数。
- **可验证**：函数是确定性代码，结果可信、可审计。
- **可编排**：一次对话里，模型可连续、甚至并行调用多个工具形成流程。
- **一切 Agent 的地基**：ReAct、ToolCalling、AutoGen、LangGraph 全都靠它。

## 环境说明

本机 **无真实 LLM API Key、也无 openai/其他 SDK 的在线调用能力**。因此与前面
AutoGen 模块一致，自建一个**零依赖的模拟 LLM + Function Calling 框架**
[framework_function_calling.py](framework_function_calling.py)（复制到每个 Day 的
Code/ 目录保证独立可跑）。它复刻真实 OpenAI 风格的 Function Calling 循环：

```python
from framework_function_calling import FunctionCallingLLM, FunctionSpec, FunctionRegistry

llm = FunctionCallingLLM()
reg = FunctionRegistry()
reg.add(FunctionSpec("get_weather", {...}, get_weather_fn))
result = llm.chat_with_tools("上海天气怎么样?", reg)
```

工作原理：由一个 **plain(纯文本) 输入 → normalized 输出（LLM API 对齐）** 的
`planner` 决定"当前是直接回答，还是发起函数调用 + 参数"，形成与真实
`tool_calls` / `role=tool` / 多轮循环完全一致的调用形态。

> 这样你学到的**消息格式、函数 schema、执行循环、错误处理**，在接上真实
> OpenAI / 通义 / 其它兼容 API 后**无缝迁移**，只需替换 `FunctionCallingLLM` 内部
> 那个 `planner` 为真实模型调用即可。

每个 Day 的目录结构：

```
DayXX - 主题/
  README.md       讲解与要点
  Code/
    framework_function_calling.py  共享模拟框架(复制自根目录)
    01-xxx.py     可直接运行的脚本(带断言验证)
    ...
```

## 10 天路线

| 天 | 主题 | 你会做出来 |
|----|------|-----------|
| 01 | 认识 Function Calling 范式 | 模型"想要"调用函数的概念演示 |
| 02 | 工具/函数定义 schema | parameters 结构、JSON Schema |
| 03 | 参数解析与函数执行 | 从 model 输出解析参数并执行返回 |
| 04 | 多工具选择与循环 | 一个循环里连选多个工具 |
| 05 | 错误处理与重试 | 工具抛错、重新让模型决策 |
| 06 | 参数校验与类型 | 必填/类型/缺失默认值 |
| 07 | 多轮工具调用上下文 | 把 tool 结果喂回再追问 |
| 08 | 并行工具调用 | 一次发起多个函数的循环 |
| 09 | 与 Agent/工作流集成 | 简单 ReAct Agent 封装 |
| 10 | 实战整合 + 评估 | 记事本/天气/计算 混合小应用 |

## 怎么开始

```bash
# 推荐从 Day01 逐个阅读, 再看对应脚本并运行
python "Day01 - 认识 Function Calling 范式/Code/01-intro.py"
```

## 速查

```python
from framework_function_calling import FunctionCallingLLM, FunctionSpec, FunctionRegistry

def get_weather(city: str) -> str:
    return f"{city} 天气: 晴, 25℃"

reg = FunctionRegistry()
reg.add(FunctionSpec("get_weather",
        {"properties": {"city": {"type": "string"}}, "required": ["city"]},
        get_weather))

llm = FunctionCallingLLM()
reply = llm.chat_with_tools("上海天气怎么样?", reg)
print(reply)
```

真实部署：接 OpenAI 等配置 `tools` 参数，循环处理 `tool_calls` 与 `role=tool` 消息，
与这里的逻辑保持一致。