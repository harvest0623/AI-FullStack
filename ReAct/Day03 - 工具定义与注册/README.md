# Day03 - 工具定义与注册

> 本章节实现「工具」这一 ReAct 的执行载体。理解如何用 JSON Schema 描述工具参数、如何用装饰器把普通函数变成可被 LLM 识别的 `Tool`，以及用注册表（Registry）统一管理和调度工具。

---

## 目录

- [一、学习目标](#一学习目标）
- [二、理论知识](#二理论知识）
  - [2.1 什么是「工具」](#21-什么是工具）
  - [2.2 JSON Schema 描述参数](#22-json-schema-描述参数）
  - [2.3 OpenAI tools 格式](#23-openai-tools-格式）
  - [2.4 用装饰器定义工具](#24-用装饰器定义工具）
  - [2.5 注册表 ToolRegistry](#25-注册表-toolregistry）
- [三、核心概念解析](#三核心概念解析）
  - [3.1 参数类型与 required 推断](#31-参数类型与-required-推断）
  - [3.2 工具执行的安全性](#32-工具执行的安全性）
  - [3.3 工具定义的最佳实践](#33-工具定义的最佳实践）
- [四、关键知识点总结](#四关键知识点总结）
- [五、实战练习](#五实战练习）

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **用 JSON Schema 描述工具的参数**。
2. **用 `@tool` 装饰器把函数注册成工具**。
3. **构造 OpenAI 兼容的 `tools` 参数列表**。
4. **用注册表按名调度执行工具**。
5. **为自定义业务封一个工具**。

---

## 二、理论知识

### 2.1 什么是「工具」

一个工具 = **具名 + 描述 + 参数 Schema + 执行函数**。LLM 通过「名称 + 参数」决定调用，Runtime 负责真正执行。

```
Tool {
  name:        "get_weather"       # 模型选择依据
  description: "返回某城市的天气"    # 指导模型何时用
  params:      {city: str, ...}     # 参数约束
  fn:          python 函数           # 真正执行
}
```

### 2.2 JSON Schema 描述参数

OpenAI 用 JSON Schema 描述工具参数结构：

```python
{
  "type": "object",
  "properties": {
    "city": {"type": "string"}
  },
  "required": ["city"]
}
```

有了它，模型能「知道」该填哪些字段、值是什么类型。

### 2.3 OpenAI tools 格式

```python
tools = [
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "返回城市天气",
      "parameters": {...},
    }
  }
]
client.chat.completions.create(..., tools=tools)
```

传给 `create` 后，模型可能返回 `tool_calls`（Day05 消费）。

### 2.4 用装饰器定义工具

我们提供 `@tool` 装饰器，把普通函数的注解与 docstring 自动转成 Tool：

```python
@tool
def add(a: int, b: int = 0) -> int:
    """两数相加"""
    return a + b

add.name        # 'add'
add.schema()    # 自动生成的参数 schema
```

### 2.5 注册表 ToolRegistry

当工具变多，需要一个 **name → Tool** 的注册表来统一管理：

```python
reg = ToolRegistry()
reg.add(add); reg.add(get_weather)
reg.names()             # ['add', 'get_weather']
reg.execute("add", a=3, b=4)     # 7, 按名调度
reg.openai_tools()      # 一处生成全部 tools 参数
```

---

## 三、核心概念解析

### 3.1 参数类型与 required 推断

- 无默认值的参数 → 加入 `required`。
- 有默认值的参数 → 带上 `default`，可选。
- 类型（int/float/bool/str/list…）映射到 JSON 类型。

本例用轻量推断；生产可用 Pydantic 的 `model_json_schema()` 生成更严谨的 schema（Day10 会引入）。

### 3.2 工具执行的安全性

- 工具是**外部代码**，Agent 会给它喂任意参数 → 需在工具内校验/兜底（Day07）。
- 只应暴露**受控权限**的操作，避免让模型直接执行系统级命令。

### 3.3 工具定义的最佳实践

- `description` 要**写得让模型明白何时该用、能做什么**。
- 参数名清晰、带默认值时给合理默认。
- 单工具做一件事，职责单一，便于模型选择与组合。

---

## 四、关键知识点总结

- **工具 = 名 + 描述 + 参数 Schema + 执行函数**。
- **JSON Schema** 把参数约束告诉模型。
- **OpenAI tools[]** 是标准输入格式。
- **@tool** 装饰器把函数变工具。
- **ToolRegistry** 统一管理与调度。

---

## 五、实战练习

### 练习一：tools.py —— 工具基础设施

**任务描述**：提供 `Tool`、`@tool` 装饰器、`ToolRegistry`，可生成 OpenAI tools 参数并执行。

**运行方式**

```bash
python "Day03 - 工具定义与注册/Code/tools.py"
```

### 练习二：02-custom-tool.py —— 自定义业务工具

**任务描述**：用 `@tool` 定义「订单查询」「汇率换算」，注册并执行。

**运行方式**

```bash
python "Day03 - 工具定义与注册/Code/02-custom-tool.py"
```

### 练习三：尝试

定义三个你自己的工具（如「股票价格」「单位换算」「SQL 查询」），用注册表统一管理并跑一遍执行。

---

## 下节预告

下一节 **Day04** 进入 ReAct 的心脏：**手写 Thought 推理循环**，让 LLM 在真实（或模拟）工具间决策下一步。