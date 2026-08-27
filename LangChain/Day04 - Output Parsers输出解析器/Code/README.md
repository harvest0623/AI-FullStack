# Day04 Code - Output Parsers 指南

本目录包含 Day04「Output Parsers 输出解析器」的全部代码文件，演示将 LLM 自由文本输出转化为结构化数据的完整能力。

## 文件清单

| 文件 | 用途 | 是否需要 API Key |
|------|------|-----------------|
| `01_str_json_parser.py` | 字符串与 JSON 解析 | 部分需要 |
| `02_pydantic_parser.py` | Pydantic 模型解析（重点） | 部分需要 |
| `03_list_parser.py` | 列表与枚举解析 | 部分需要 |
| `04_custom_parser.py` | 自定义解析器与错误重试 | 部分需要 |

---

## 各 Parser 对比表

| Parser | 输出类型 | 格式指令 | 适用场景 | 难度 |
|--------|---------|---------|---------|------|
| StrOutputParser | str | 无 | 纯文本输出 | ⭐ |
| JsonOutputParser | dict | ✅ | JSON 数据 | ⭐⭐ |
| PydanticOutputParser | Pydantic 实例 | ✅ | 信息抽取 | ⭐⭐⭐ |
| CommaSeparatedListOutputParser | list[str] | ✅ | 关键词列表 | ⭐ |
| EnumOutputParser | Enum | ✅ | 分类任务 | ⭐⭐ |
| DatetimeOutputParser | datetime | ✅ | 日期解析 | ⭐⭐ |
| 自定义 Parser | Any | 可选 | 特殊格式 | ⭐⭐⭐⭐ |

---

## PydanticOutputParser 最佳实践

### 1. 模型设计原则

```python
from pydantic import BaseModel, Field

# ✅ 好的设计
class ProductInfo(BaseModel):
    name: str = Field(description="产品名称")
    price: float = Field(description="产品价格（元）", ge=0)  # 加约束
    category: str = Field(description="产品类别")
    in_stock: bool = Field(description="是否有库存")

# ❌ 差的设计
class ProductInfo(BaseModel):
    name: str              # 缺少 description
    price: float           # 缺少约束和说明
    category: str
```

### 2. Field description 要清晰

description 是 LLM 理解字段的关键，要写清楚：
- 字段含义
- 取值范围
- 格式要求

```python
# ✅ 清晰的 description
age: int = Field(description="年龄，范围 0-150", ge=0, le=150)
status: str = Field(description="订单状态：待付款/已付款/已发货/已完成")
```

### 3. 使用 get_format_instructions()

```python
parser = PydanticOutputParser(pydantic_object=ProductInfo)

# 自动生成格式指令，注入 Prompt
prompt = ChatPromptTemplate.from_template(
    "提取信息：{text}\n\n{format_instructions}"
).partial(format_instructions=parser.get_format_instructions())
```

---

## 错误处理策略选择

| 策略 | 实现 | 适用场景 | 代码示例 |
|------|------|---------|---------|
| 直接捕获 | try/except | 简单场景 | `except OutputParserException` |
| 自动重试 | RetryOutputParser | 生产环境 | `retry_parser.parse_with_prompt()` |
| 降级处理 | 默认值 | 容错要求高 | `result = fallback_value` |
| 模型回退 | with_fallbacks | 高可用 | 主模型失败切备用 |
| 手动修复 | parse_with_prompt | 精细控制 | 附加错误信息重试 |

### 错误处理代码模板

```python
from langchain_core.exceptions import OutputParserException

try:
    result = chain.invoke({"text": "..."})
except OutputParserException as e:
    print(f"解析失败：{e}")
    # 策略 1：降级
    result = default_value
    # 策略 2：重试（需要 RetryOutputParser）
    # result = retry_parser.parse_with_prompt(llm_output, prompt_value)
```

---

## with_structured_output 替代方案说明

### 两种方式对比

```python
# 方式 A：PydanticOutputParser（传统，代码多）
parser = PydanticOutputParser(pydantic_object=ProductInfo)
prompt = ChatPromptTemplate.from_template(
    "提取：{text}\n\n{format_instructions}"
).partial(format_instructions=parser.get_format_instructions())
chain = prompt | model | parser

# 方式 B：with_structured_output（简洁，推荐）
structured_model = model.with_structured_output(ProductInfo)
prompt = ChatPromptTemplate.from_template("提取：{text}")
chain = prompt | structured_model
```

### 选择建议

| 场景 | 推荐 | 原因 |
|------|------|------|
| 日常开发 | with_structured_output | 代码简洁 |
| 需要精细控制格式 | PydanticOutputParser | 可定制格式指令 |
| 需要错误重试 | PydanticOutputParser + RetryOutputParser | 重试机制更完善 |
| 模型不支持 Function Calling | PydanticOutputParser | 兼容性更好 |

---

## Parser 与 Chain 集成模式

### 标准模式

```python
chain = prompt | model | parser
```

### 带格式指令注入

```python
parser = PydanticOutputParser(pydantic_object=Schema)
prompt = ChatPromptTemplate.from_template(
    "...{format_instructions}"
).partial(format_instructions=parser.get_format_instructions())
chain = prompt | model | parser
```

### 带错误重试

```python
from langchain.output_parsers import RetryOutputParser

parser = PydanticOutputParser(pydantic_object=Schema)
retry_parser = RetryOutputParser.from_llm(parser=parser, llm=model)

# 在 Chain 中使用时需手动处理
try:
    result = (prompt | model | parser).invoke(input)
except OutputParserException:
    # 重试逻辑
    llm_output = (prompt | model).invoke(input)
    result = retry_parser.parse_with_prompt(llm_output, prompt.invoke(input))
```

---

## 常见问题

### 问题 1：`OutputParserException: Failed to parse`

**原因**：LLM 输出不符合预期格式。

**解决**：
- 检查 Field description 是否清晰
- 降低 temperature（设为 0）
- 使用 RetryOutputParser 自动重试

### 问题 2：JSON 解析中字段缺失

**原因**：LLM 漏输出某些字段。

**解决**：
- 将字段设为 Optional：`field: str | None = None`
- 在 description 中强调必填

### 问题 3：Enum 解析失败

**原因**：LLM 输出了枚举外的值。

**解决**：
- 在 format_instructions 中明确列出可选值
- 降低 temperature

### 问题 4：自定义 Parser 不工作

**原因**：未正确实现 `parse()` 方法或 `_type` 属性。

**解决**：
```python
class MyParser(BaseOutputParser):
    def parse(self, text: str) -> Any:
        # 实现解析逻辑
        ...

    @property
    def _type(self) -> str:
        return "my_parser"  # 必须实现
```

---

## 运行指南

```bash
cd "Day04 - Output Parsers输出解析器/Code"

python 01_str_json_parser.py      # 字符串与 JSON
python 02_pydantic_parser.py       # Pydantic 模型（重点）
python 03_list_parser.py           # 列表与枚举
python 04_custom_parser.py         # 自定义与重试
```

---

## 阶段一完成检查

完成 Day04 后，确认你能：

- [ ] 用 ChatModel 调用 LLM（invoke/batch/stream）
- [ ] 用 ChatPromptTemplate 管理多角色 Prompt
- [ ] 用 MessagesPlaceholder 管理对话历史
- [ ] 用 PydanticOutputParser 解析结构化输出
- [ ] 用 with_structured_output 快速实现结构化输出
- [ ] 实现自定义 Output Parser
- [ ] 处理解析错误与自动重试
- [ ] 组合 prompt | model | parser 构建完整 Chain

---

> 阶段一（基础与核心）完成！进入 Day05 学习 LCEL 链式调用，开始组合这些组件。
