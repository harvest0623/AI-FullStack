# Day02 - Function Calling 原理与 API 形态

> 深入模型如何"感知工具并决策"，掌握主流 API（尤其 OpenAI 风格）的 tools 参数与 tool_calls 返回结构，理解为什么工具定义和参数都走 JSON。

---

## 1. 模型如何"感知工具"

调用时把工具清单以 `tools` 参数传入。工具本质就是一段文本化的**JSON Schema 描述**，模型把它当作上下文的一部分来"阅读"，从而知道：

- 有哪些可用工具
- 每个工具是干嘛的（description）
- 每个工具需要哪些参数（inputSchema / parameters）

模型不会"看得见"工具的 Python 实现，它只看到**描述文本**。因此**描述写得好不好，直接决定模型用得准不准**。

```
用户对话 ┌──────────────────────────┐
         │ tools: [ get_weather,     │  ← 一并送入模型
         │          get_stock, ... ] │
         └──────────────────────────┘
```

---

## 2. 输出 tool_calls

当模型认为需要外部能力时，输出会附带一个 `tool_calls` 数组。以 OpenAI 风格为例：

```json
{
  "message": {
    "role": "assistant",
    "content": null,
    "tool_calls": [
      {
        "id": "call_abc123",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"city\": \"北京\"}"
        }
      }
    ]
  }
}
```

关键字段：
- **id**：本次调用的唯一标识，回填时要用它对应结果
- **function.name**：要调用的工具名
- **function.arguments**：JSON 编码的字符串——注意它是**字符串**，需要 `json.loads` 解析成对象

---

## 3. 主流 API 形态对比

| 厂商 | tools 参数 | 返回字段 | 备注 |
|------|-----------|---------|------|
| OpenAI | `tools` + `tool_choice` | `message.tool_calls` | 行业事实标准 |
| Anthropic | `tools` | `content` 中的 `tool_use` block | `id/name/input` 结构 |
| Ollama（部分模型） | `tools` | 依模型而定 | 兼容前后者 |

> 名称与细节稍有差异，但**思想一致**：输入带工具描述，输出带结构化调用请求。本板块以 OpenAI 风格为主线，其余可对照。

---

## 4. 为什么是 JSON

- **结构化**：模型输出可解析的字段，而非自然语言
- **标准**：JSON 是数据交换的事实标准，Python/JS 都可解析
- **约束**：借助 JSON Schema 约束参数类型与必填，减少幻觉

---

## 5. tool_choice（可选，控制行为）

可通过 `tool_choice` 影响模型是否调用、调用哪个：

| 值 | 行为 |
|----|------|
| `auto` | 模型自行决定（默认） |
| `none` | 强制不调用工具 |
| `required` | 强制必须调用某个工具 |
| `{"type":"function","function":{"name":"x"}}` | 强制调用指定工具 |

---

## 6. 本节小结

- 工具以 `tools` 参数作为**文本描述**进入模型上下文
- 模型输出 `tool_calls`（id + name + arguments 字符串）
- 各大模型思想一致，OpenAI 风格为主线；`arguments` 需 JSON 解析
- `tool_choice` 可控制是否/强制调用

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_how_model_decides.py` | 模型如何感知工具并决策（离线演示） |
| `02_api_shapes.py` | 主流 API 返回形态对比 |
| `03_tool_calls_struct.py` | tool_calls 结构解析与 arguments 反序列化 |
| `README.md` | 本目录说明 |

均**离线可运行**。