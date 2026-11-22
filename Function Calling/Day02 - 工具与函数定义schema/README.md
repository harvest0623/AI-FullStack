# Day02 - 工具/函数定义 schema

> 本节目标：掌握**如何把一个函数"说明"给模型**——即函数定义 schema。
> 定义越清楚，模型越能选对函数、传对参数。

---

## 1. 一个函数定义需要什么

在 Function Calling 里，每个工具用下面三类信息描述：

| 字段 | 作用 |
|------|------|
| `name` | 函数名，模型用来"选择"调哪个 |
| `description` | 一句话描述，模型用来判断"这个场景该不该用它" |
| `parameters` | 参数结构（JSON Schema），描述每个参数的类型、是否必填、枚举 |

> 这三个字段决定了模型能不能**用对工具**。模糊的名字/描述 → 模型瞎选。

---

## 2. parameters 用 JSON Schema 描述

```python
parameters = {
    "type": "object",
    "properties": {
        "city":  {"type": "string", "description": "城市名, 必需"},
        "unit":  {"type": "string", "enum": ["C", "F"], "description": "温度单位"},
    },
    "required": ["city"],   # 只有 city 必填, unit 可省略
}
```

- `properties`：逐一列出每个参数的类型（string / number / integer / boolean）与说明。
- `required`：数组，列出**必填**参数；没列的可选。
- `enum`：限制取值（如温度单位只能是 C 或 F）。

---

## 3. OpenAI 风格的 tools 结构

真实 OpenAI 里，上面的定义会被包成 `tools` 入参：

```python
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "...",
        "parameters": {...},
    }
}
```

本框架的 `to_openai_tool()` 输出同款结构，方便你对着真实 API 迁移。

---

## 4. 本节练习

[02-schema.py](Code/02-schema.py) 定义一个多参数（`city` 必填 + `unit` 枚举可选）的
天气工具，打印其 OpenAI 结构，并用规则 planner 演示"模型依据 schema 正确传参"
（含解析出可选参数 `unit=F`）。

```bash
python "Day02 - 工具与函数定义schema/Code/02-schema.py"
```

---

## 5. 你要记住的三句话

1. 函数定义三要素：**name / description / parameters**。
2. `parameters` 用 JSON Schema：`properties`(类型) + `required`(必填) + `enum`(枚举)。
3. 定义越清楚，模型越不容易调错——**一个工具可用不可用，一半取决于定义好不好**。

下一节：深入**参数解析与函数执行**——模型输出后怎么落地。