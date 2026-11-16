# Day03 - 工具定义与 JSON Schema

> 把 Python 函数翻译成模型能读懂的 JSON 描述，是其"用得好不好"的关键。掌握 JSON Schema 基础、参数类型与必填约束、description 的写法。

---

## 1. 工具描述的组成

一份工具描述（OpenAI 风格）通常包含四块：

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "查询指定城市的当前天气",
    "parameters": {
      "type": "object",
      "properties": {
        "city": { "type": "string", "description": "城市名，如 北京" },
        "unit": { "type": "string", "enum": ["celsius", "fahrenheit"],
                  "description": "温度单位" }
      },
      "required": ["city"]
    }
  }
}
```

- **name**：唯一，稳定，不要频繁变
- **description**：告诉模型"何时用、怎么用、给谁用"
- **parameters**：JSON Schema，描述参数结构、类型、必填

---

## 2. JSON Schema 基础

`parameters` 遵循 JSON Schema，最常用关键字：

| 关键字 | 作用 |
|--------|------|
| `type` | 类型：object / string / number / integer / array / boolean |
| `properties` | 各字段的定义（键→schema） |
| `required` | 必填字段列表 |
| `enum` | 限定取值范围 |
| `description` | 字段含义说明 |
| `items` | array 的元素类型 |

### 数组示例

```json
{
  "type": "object",
  "properties": {
    "tags": { "type": "array", "items": { "type": "string" },
              "description": "标签列表" }
  },
  "required": ["tags"]
}
```

---

## 3. description 决定调用准确度

模型靠 description 判断"该不该用它、怎么填参"。写得越具体：

- 用户说"北京天气" → 模型知道该查 `get_weather(city='北京')`
- `city` 描述"城市名"比"一个字符串"更能引导正确填参

**好的 description 特征**：说明目的、参数含义、可能的取值、何时该用。

---

## 4. 从函数签名生成 schema

很多框架能从 Python 函数签名 + 类型注解 + docstring 自动生成工具描述。原理是：
- 参数名 → properties 的键
- 类型注解 → type
- docstring → description

> 手工写 JSON 也是一等公民；自动生成只是提升效率。Day09 会给出封装思路。

---

## 5. 本节小结

- 工具描述 = name + description + parameters(JSON Schema)
- 掌握 type / properties / required / enum / items / description
- description 是模型"正确使用"的关键，务必写具体
- 可从函数签名 + 注解 + docstring 自动生成（简化开发）

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_schema_basics.py` | JSON Schema 基础与关键字示例 |
| `02_description_matters.py` | 描述好坏如何影响调用准确度 |
| `03_signature_to_schema.py` | 从函数签名自动生成 schema |
| `README.md` | 本目录说明 |

均**离线可运行**。