# Day01 - 认识 Function Calling 范式

> 本节目标：理解 Function Calling（函数调用）到底是什么、解决什么问题，并建立起
> "**模型不只是输出文字，还会输出结构化指令去调函数**" 的核心直觉。

---

## 1. 什么是 Function Calling

常规 LLM 只会"说"。但很多任务需要 LLM 去调用真实代码才靠谱：

- 查天气 → 调用 `get_weather(city)`
- 查库存/数据库 → 调用 `query_db(sql)`
- 算数、发信、检索 → 调用各自函数

**Function Calling** 让模型在回答时，**不是直接给最终文字**，而是输出像这样的结构化
调用指令：

```json
{"name": "get_weather", "args": {"city": "上海"}}
```

然后由**你的程序**真正执行这个函数，把结果（如"晴，26°C"）作为一条 `tool` 消息
喂回模型，模型再最终回答。

---

## 2. 核心循环（画重点）

```
用户提问
  → 模型决定: 直接答 还是 需要调函数?
  → 若调函数: 模型输出 tool_calls(名字+参数)   ← Function Calling 的关键
  → 程序执行函数, 得到结果
  → 结果作为 role="tool" 的消息加回对话
  → 再次给模型, 模型基于结果给出最终回答
```

这条"**问 → 调 → 喂回 → 答**"的循环是后面所有 Day 的母题。

---

## 3. 两种角色消息

| role | 含义 |
|------|------|
| `assistant` | 模型的输出；可含 `tool_calls` 字段 |
| `tool` | 程序执行函数后的**结果**，回传给模型 |

只有模型看到 `tool` 结果，才能在下一步回答里"参考"它。

---

## 4. 模型"决定是否调用"要看你给的工具

调用什么、传什么参数，模型会根据你提供的 **tools 定义**（函数名、描述、参数 schema）
来判断。所以**工具怎么定义，决定了模型能不能用对**（下一节展开）。

---

## 5. 本节练习

[01-intro.py](Code/01-intro.py) 复用 [framework_function_calling.py](Code/framework_function_calling.py)：
注册一个 `get_weather` 工具，用规则式 planner 模拟"模型决定调用函数"，观察
`tool_calls → 执行 → tool 消息 → 最终回答` 的完整流转。

```bash
python "Day01 - 认识 Function Calling 范式/Code/01-intro.py"
```

---

## 6. 你要记住的三句话

1. Function Calling = 模型说"**我想调这个函数，参数是…**"，你替它执行。
2. 核心循环：问 → 调 → 结果喂回 → 答。
3. `assistant` 带 `tool_calls`，`tool` 带回结果，两者配合驱动循环。

下一节：深入**工具/函数定义 schema**——怎么把函数"说明"给模型。