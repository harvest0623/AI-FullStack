# Day10 - 实战整合与评估

> 最后一节：把 9 天学到的所有能力拼成一个**多功能小助手**，跑真实场景并断言，
> 再用能力自检清单复盘整条知识线。

---

## 1. 小助手：ToolAssistant

注册 5 个工具，一站式处理多种请求：

| 工具 | 场景 | 用到的能力 |
|------|------|-----------|
| `get_weather` | 查天气 | 多工具选择、参数解析 |
| `add` | 算数 | 参数解析、Agent 封装 |
| `search_book` | 搜书 | 多工具选择 |
| `joke` | 讲笑话 | 空参工具 |
| `tax` | 算含税价 | 可选参数、校验 |

统一决策器依用户问题分流、有结果就总结，做成一个调用方只 `run()` 的助手。

---

## 2. 贯穿全模块的十条能力

| Day | 能力 | 落地点 |
|-----|------|--------|
| 1 | Function Calling 范式 | 问→调→喂回→答 循环 |
| 2 | 工具定义 schema | name/description/parameters |
| 3 | 参数解析与执行 | executor 拿 args 调函数 |
| 4 | 多工具选择与循环 | 按描述分流 |
| 5 | 错误处理与重试 | 错误喂回 + 修正重试 |
| 6 | 参数校验与类型 | required/type 拦截 |
| 7 | 多轮上下文 | 历史结果驱动下一步 |
| 8 | 并行调用 | 一次发多个 call |
| 9 | Agent 封装 | 统一 run() |
| 10 | 实战整合 | 多功能助手 |

---

## 3. 迁移到真实 LLM

全程用模拟框架。接真实 API 只需把 `FunctionCallingLLM` 的 `plan` 替换为真实模型：
- 把 `reg.explain_tools()` 作为 `tools` 入参发给模型；
- 模型返回 `tool_calls` → 你执行 `reg.execute` → 结果作为 `role="tool"` 追加；
- 循环直到模型不再要调用。

消息形态、schema、校验、错误重试逻辑**全部复用**，仅"谁能生成 tool_calls"换掉。

---

## 4. 本节练习

[10-assistant.py](Code/10-assistant.py) 跑通笑话/算数/搜书/含税/天气五个场景，
断言关键结果，并打印能力自检清单。

```bash
python "Day10 - 实战整合与评估/Code/10-assistant.py"
```

---

## 5. 评估清单

- [ ] 明白 Function Calling 的循环范式
- [ ] 会用 JSON Schema 定义工具参数
- [ ] 能解析模型输出并执行函数
- [ ] 会让模型在多个工具间做选择
- [ ] 会处理错误并让模型重试
- [ ] 会用必填/类型校验挡坏参数
- [ ] 会用历史上下文推进多步工作流
- [ ] 会一次并行调用多个工具
- [ ] 会封装成统一 Agent 接口
- [ ] 能独立拼出完整工具箱应用

---

## 6. 下一站

Function Calling 是 Agent 基础设施。继续可以：

- 用它复盘/深化 **ToolCalling**、**ReAct**、**AutoGen** 模块的思路；
- 在 **LangChain/LangGraph** 里直接使用内置工具调用；
- 接入真实 OpenAI / 通义等 API，把 `planner` 换成真实模型跑生产。

恭喜你完成 Function Calling 模块！