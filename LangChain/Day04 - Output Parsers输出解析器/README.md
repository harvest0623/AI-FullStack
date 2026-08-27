# Day04 - Output Parsers 输出解析器

LLM 的输出是自由文本，程序难以直接使用——你拿到一段字符串，却不知道哪个是姓名、哪个是年龄、哪个是分类结果。Output Parsers 就是解决这个问题的工具：它将 LLM 的自由文本转化为程序可处理的结构化数据（字符串、列表、字典、Pydantic 模型）。这是 LLM 应用从「能跑」到「工程化」的关键一环。本章深入 LangChain 的输出解析体系：从基础的 StrOutputParser 到强大的 PydanticOutputParser，从列表/枚举/日期解析到自定义解析器与错误重试，让你全面掌握将 LLM 输出结构化的能力。

## 学习目标

- 理解 Output Parsers 的概念与三步流程
- 掌握 StrOutputParser（字符串输出）
- 掌握 JsonOutputParser（JSON 解析与 Schema 约束）
- 掌握 PydanticOutputParser（Pydantic 模型解析，重点）
- 掌握 CommaSeparatedListOutputParser（列表解析）
- 掌握 EnumOutputParser（枚举解析）和 DatetimeOutputParser（日期解析）
- 能够自定义 Output Parser（继承 BaseOutputParser）
- 掌握解析错误处理与 RetryOutputParser 自动重试
- 理解 Parser 与 Chain 的配合（prompt | model | parser）
- 了解 with_structured_output() 替代方案

---

## 一、Output Parsers 概念

### 1.1 问题：LLM 输出是自由文本

```python
# LLM 返回的是 AIMessage，content 是一段自由文本
result = model.invoke("提取张三的信息")
# result.content = "姓名：张三，年龄：28，职业：工程师"
# 程序怎么用？还得手动正则解析...
```

### 1.2 解决：Parser 将文本解析为结构化数据

```python
# 用 PydanticOutputParser，输出直接是结构化对象
parser = PydanticOutputParser(pydantic_object=PersonInfo)
chain = prompt | model | parser
result = chain.invoke({"text": "张三 28 岁 工程师"})
# result 是 PersonInfo 实例，可直接 result.name / result.age
```

### 1.3 三步流程

```
1. 生成格式指令：parser.get_format_instructions() → "请输出 JSON..."
       ↓
2. 注入 Prompt：将格式指令加入 Prompt 模板
       ↓
3. 解析输出：parser.parse(llm_output) → 结构化数据
```

---

## 二、StrOutputParser

最简单的解析器，直接返回字符串。ChatModel 输出 AIMessage，StrOutputParser 提取 `.content`。

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()

# 单独使用：从 AIMessage 提取字符串
from langchain_core.messages import AIMessage
msg = AIMessage(content="你好")
print(parser.invoke(msg))  # "你好"

# 在 Chain 中使用（最常见）
chain = prompt | model | parser
result = chain.invoke({"question": "什么是 Python"})
# result 直接是字符串，不是 AIMessage
```

---

## 三、JsonOutputParser

将 LLM 输出解析为 dict，可指定 JSON Schema 约束输出结构。

```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# 定义数据结构
class Person(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")

parser = JsonOutputParser(pydantic_object=Person)

# 获取格式指令（注入 Prompt）
print(parser.get_format_instructions())
# 输出类似："The output should be formatted as a JSON instance..."

# 在 Chain 中使用
chain = prompt | model | parser
result = chain.invoke({"text": "张三 28 岁"})
# result 是 dict: {"name": "张三", "age": 28}
```

---

## 四、PydanticOutputParser（重点）

将 LLM 输出解析为 Pydantic 模型实例，提供类型安全和 IDE 自动补全。

### 4.1 三步使用

```python
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# 1. 定义 Pydantic 模型
class ProductInfo(BaseModel):
    name: str = Field(description="产品名称")
    price: float = Field(description="产品价格（元）")
    in_stock: bool = Field(description="是否有库存")

# 2. 创建 Parser
parser = PydanticOutputParser(pydantic_object=ProductInfo)

# 3. 获取格式指令并注入 Prompt
format_instructions = parser.get_format_instructions()
prompt = ChatPromptTemplate.from_template(
    "提取产品信息：{text}\n\n{format_instructions}"
).partial(format_instructions=format_instructions)

# 4. 组成 Chain
chain = prompt | model | parser

# 5. 调用，返回 Pydantic 实例
result = chain.invoke({"text": "iPhone 15 售价 5999 元，有货"})
print(result.name)       # "iPhone 15"（有类型提示）
print(result.price)      # 5999.0
print(result.in_stock)   # True
```

### 4.2 优势

- **类型安全**：`result.name` 有类型提示，IDE 自动补全
- **Schema 约束**：Field description 指导 LLM 输出
- **自动生成格式说明**：get_format_instructions() 自动生成
- **验证**：Pydantic 自动验证类型

---

## 五、CommaSeparatedListOutputParser

将逗号分隔的文本解析为列表。

```python
from langchain_core.output_parsers import CommaSeparatedListOutputParser

parser = CommaSeparatedListOutputParser()
print(parser.get_format_instructions())
# "Your response should be a list of comma separated values..."

result = parser.parse("苹果, 香蕉, 橙子")
# result = ["苹果", "香蕉", "橙子"]
```

---

## 六、DatetimeOutputParser

解析日期时间格式。

```python
from langchain_core.output_parsers import DatetimeOutputParser

parser = DatetimeOutputParser()
print(parser.get_format_instructions())
# 指示 LLM 输出 ISO 8601 格式日期

result = parser.parse("2024-01-15T10:30:00")
# result 是 datetime 对象
```

---

## 七、EnumOutputParser

解析为枚举值，限制 LLM 只能输出给定选项之一。

```python
from langchain_core.output_parsers import EnumOutputParser
from enum import Enum

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

parser = EnumOutputParser(enum=Sentiment)
print(parser.get_format_instructions())
# "请只输出以下值之一：positive, negative, neutral"

result = parser.parse("positive")
# result = Sentiment.POSITIVE
```

---

## 八、自定义 Output Parser

继承 `BaseOutputParser`，实现 `parse()` 方法。

```python
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.exceptions import OutputParserException

class MarkdownTableParser(BaseOutputParser):
    """解析 Markdown 表格为列表的列表"""

    def parse(self, text: str) -> list[list[str]]:
        """将 Markdown 表格解析为二维列表"""
        lines = text.strip().split("\n")
        # 过滤分隔行（|---|---|）
        rows = []
        for line in lines:
            if set(line.strip()) <= set("|- "):
                continue  # 跳过分隔行
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cells)
        if not rows:
            raise OutputParserException("未找到有效表格")
        return rows

    @property
    def _type(self) -> str:
        return "markdown_table_parser"
```

---

## 九、解析错误处理

### 9.1 OutputParserException

解析失败时抛出 `OutputParserException`：

```python
from langchain_core.exceptions import OutputParserException

try:
    result = parser.parse("invalid json {{{")
except OutputParserException as e:
    print(f"解析失败：{e}")
```

### 9.2 RetryOutputParser 自动重试

解析失败 → 在 Prompt 中追加错误信息 → 重新调用 LLM：

```python
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import RetryOutputParser

parser = PydanticOutputParser(pydantic_object=ProductInfo)
retry_parser = RetryOutputParser.from_llm(parser=parser, llm=model)

# parse_with_prompt 传入原始 Prompt 用于重试
result = retry_parser.parse_with_prompt(llm_output, prompt_value)
```

---

## 十、Parser 与 Chain 的配合

Parser 作为链的最后一环，`get_format_instructions()` 注入 Prompt：

```python
# 完整模式：prompt | model | parser
parser = PydanticOutputParser(pydantic_object=ProductInfo)

prompt = ChatPromptTemplate.from_template(
    "提取信息：{text}\n\n{format_instructions}"
).partial(format_instructions=parser.get_format_instructions())

chain = prompt | model | parser
# 输入文本，输出直接是 Pydantic 实例
result = chain.invoke({"text": "..."})
```

---

## 十一、with_structured_output() 替代方案

ChatModel 的 `.with_structured_output()` 可替代 PydanticOutputParser：

```python
# 方式 A：PydanticOutputParser（传统）
parser = PydanticOutputParser(pydantic_object=ProductInfo)
chain = prompt.partial(format_instructions=parser.get_format_instructions()) | model | parser

# 方式 B：with_structured_output（更简洁）
structured_model = model.with_structured_output(ProductInfo)
chain = prompt | structured_model
# 不需要手动注入 format_instructions
```

### 两者对比

| 维度 | PydanticOutputParser | with_structured_output |
|------|---------------------|----------------------|
| 代码量 | 较多 | 少 |
| 格式指令 | 手动注入 | 自动处理 |
| 底层机制 | Prompt 指令 + 文本解析 | 模型原生 Function Calling |
| 可控性 | 高 | 中 |
| 推荐度 | 需要精细控制时 | ✅ 大多数场景 |

---

## 十二、代码文件说明

| 文件 | 用途 | 关键内容 |
|------|------|---------|
| `Code/01_str_json_parser.py` | 字符串与 JSON 解析 | StrOutputParser / JsonOutputParser / Schema 约束 |
| `Code/02_pydantic_parser.py` | Pydantic 模型解析 | 模型定义 / Field 描述 / 类型安全访问 |
| `Code/03_list_parser.py` | 列表与枚举解析 | CommaSeparatedList / Enum / Datetime |
| `Code/04_custom_parser.py` | 自定义解析器与错误重试 | BaseOutputParser / RetryOutputParser |
| `Code/README.md` | Output Parsers 指南 | 对比表 / 最佳实践 / 集成模式 |

运行方式：

```bash
cd "Day04 - Output Parsers输出解析器/Code"
python 01_str_json_parser.py
python 02_pydantic_parser.py
python 03_list_parser.py
python 04_custom_parser.py
```

---

## 关键知识点总结

### Output Parsers 对比表

| Parser | 输出类型 | 适用场景 | 难度 |
|--------|---------|---------|------|
| StrOutputParser | str | 纯文本输出 | ⭐ |
| JsonOutputParser | dict | JSON 数据 | ⭐⭐ |
| PydanticOutputParser | Pydantic 实例 | 结构化信息抽取 | ⭐⭐⭐ |
| CommaSeparatedListOutputParser | list | 关键词列表 | ⭐ |
| EnumOutputParser | Enum | 分类任务 | ⭐⭐ |
| DatetimeOutputParser | datetime | 日期解析 | ⭐⭐ |
| 自定义 Parser | Any | 特殊格式 | ⭐⭐⭐⭐ |

### PydanticOutputParser 使用步骤

1. 定义 Pydantic 模型 + Field description
2. 创建 PydanticOutputParser
3. 获取 format_instructions 注入 Prompt
4. 组成 Chain：prompt | model | parser
5. 调用，返回 Pydantic 实例

### 错误处理策略对比

| 策略 | 实现 | 适用场景 |
|------|------|---------|
| 直接抛异常 | try/except | 简单场景 |
| 自动重试 | RetryOutputParser | 生产环境 |
| 降级处理 | with_fallbacks | 容错要求高 |
| 手动修复 | parse_with_prompt | 需要控制 |

### Parser vs with_structured_output 对比

| 维度 | PydanticOutputParser | with_structured_output |
|------|---------------------|----------------------|
| 代码量 | 多 | 少 |
| 底层机制 | Prompt 指令 + 解析 | Function Calling |
| 可控性 | 高 | 中 |
| 推荐 | 精细控制 | ✅ 日常使用 |

---

## 实战练习

### 练习 1：客服意图识别

基于 `Code/01_str_json_parser.py`：
- 设计一个客服意图识别系统
- 用 JsonOutputParser 约束输出为：`{"intent": "...", "confidence": 0.9}`
- 测试 5 条用户消息，验证解析结果

### 练习 2：商品信息抽取

基于 `Code/02_pydantic_parser.py`：
- 定义一个 `OrderDetail` 模型（订单号、商品列表、总价、状态）
- 用 PydanticOutputParser 解析一段订单描述文本
- 验证类型安全访问

### 练习 3：自定义 Markdown 解析器

基于 `Code/04_custom_parser.py`：
- 实现一个 Markdown 代码块解析器（提取 ``` 之间的代码）
- 加入错误重试机制
- 测试解析失败时是否能自动重试

---

> **阶段一完成**：至此，Day01-Day04 基础与核心阶段完成。你已经掌握 LangChain 环境搭建、Model I/O、Prompt 管理、Output Parsers 四大基础。下一步进入 Day05 学习 LCEL 链式调用，开始组合这些组件构建复杂应用。
