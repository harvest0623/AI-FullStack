# Day02 Code - Model I/O 指南

本目录包含 Day02「Model I/O 模型接口层」的全部代码文件，演示 ChatModel 的实例化、调用方式、参数配置与回退机制。

## 文件清单

| 文件 | 用途 | 是否需要 API Key |
|------|------|-----------------|
| `01_chat_models.py` | ChatModel 实例化与调用（OpenAI/Anthropic/Ollama） | ✅ 至少一个 |
| `02_llm_models.py` | LLM 与 ChatModel 对比、消息类型 | ✅ 推荐 |
| `03_invoke_batch_async.py` | invoke/batch/stream/ainvoke 四种调用方式对比 | ✅ 需要 |
| `04_model_config.py` | 参数配置、bind、结构化输出、回退 | ✅ 需要 |

---

## 各模型实例化参数表

### ChatOpenAI

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| model | str | "gpt-3.5-turbo" | 模型名称 |
| temperature | float | 0.7 | 随机性 0-2 |
| max_tokens | int | None | 最大输出 Token |
| streaming | bool | False | 流式输出 |
| timeout | int | None | 超时秒数 |
| max_retries | int | 2 | 重试次数 |
| stop | list | None | 停止序列 |
| seed | int | None | 随机种子 |
| base_url | str | None | 自定义 API 地址 |

### ChatAnthropic

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| model | str | — | 如 "claude-3-5-sonnet-20241022" |
| temperature | float | 0.7 | 随机性 0-1 |
| max_tokens | int | 1024 | 最大输出（必填） |
| timeout | int | None | 超时 |
| max_retries | int | 2 | 重试 |

### ChatOllama（本地）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| model | str | — | 如 "qwen2.5:7b" |
| base_url | str | "http://localhost:11434" | Ollama 地址 |
| temperature | float | 0.8 | 随机性 |
| num_ctx | int | 4096 | 上下文长度 |

---

## 调用方式选择决策表

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| 单次问答 | `.invoke()` | 简单直接 |
| 批量翻译 10 条 | `.batch()` | 并行高效 |
| 聊天界面实时显示 | `.stream()` | 逐字输出，体验好 |
| FastAPI 后端 | `.ainvoke()` | 异步不阻塞 |
| 大批量后台处理 | `.abatch()` | 异步并发 |
| 流式 + 异步 | `.astream()` | 异步流式 |

---

## 常见错误排查

### 错误 1：`AuthenticationError`

```
openai.AuthenticationError: Error code: 401 - Incorrect API key
```

**原因**：API Key 无效或未设置。

**解决**：检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确。

### 错误 2：`RateLimitError`

```
openai.RateLimitError: Error code: 429
```

**原因**：调用频率或额度超限。

**解决**：
- 增加 `max_retries` 参数
- 使用 `.with_retry()` 配置重试
- 降低调用频率

### 错误 3：`TimeoutError`

```
httpx.TimeoutException: Request timed out
```

**原因**：请求超时。

**解决**：增加 `timeout` 参数值，如 `timeout=60`。

### 错误 4：`ContextWindowExceededError`

**原因**：输入超过模型上下文窗口。

**解决**：
- 减少输入长度
- 使用更大上下文窗口的模型
- 使用 Text Splitter 分割（Day07）

### 错误 5：结构化输出报错

```
pydantic.ValidationError
```

**原因**：LLM 输出不符合 Pydantic Schema。

**解决**：
- 检查 Field description 是否清晰
- 降低 temperature（设为 0）
- 参考 Day04 的错误重试机制

---

## 模型切换迁移指南

### 从 ChatOpenAI 迁移到 ChatAnthropic

```python
# 之前（OpenAI）
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=500)

# 之后（Anthropic）—— 只需改 import 和 model 名
from langchain_anthropic import ChatAnthropic
model = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.7, max_tokens=500)

# 调用方式完全不变！
result = model.invoke("你好")
```

### 迁移注意事项

| 注意点 | 说明 |
|--------|------|
| 参数名一致 | temperature / max_tokens / timeout 通用 |
| Anthropic max_tokens 必填 | Claude 需要显式指定 max_tokens |
| 角色限制 | Claude 对 System 消息有特殊处理 |
| 环境变量 | 需额外配置 ANTHROPIC_API_KEY |

### 从 API 迁移到本地 Ollama

```python
# 从云端迁移到本地
from langchain_community.chat_models import ChatOllama

model = ChatOllama(
    model="qwen2.5:7b",                          # 本地模型
    base_url="http://localhost:11434/v1",
    temperature=0.7,
)
# 无需 API Key，数据不出本地
```

---

## 结构化输出使用建议

### 何时用 `.with_structured_output()`

| 场景 | 是否推荐 | 原因 |
|------|---------|------|
| 信息抽取（姓名/年龄/地址） | ✅ 推荐 | 结构清晰，类型安全 |
| 分类任务（情感/意图） | ✅ 推荐 | 限制输出范围 |
| 自由创作（写诗/故事） | ❌ 不推荐 | 限制创意 |
| 多轮对话 | ❌ 不推荐 | 用 Memory 管理即可 |

### Pydantic 模型设计建议

```python
from pydantic import BaseModel, Field

class GoodSchema(BaseModel):
    """好的设计：字段名清晰，description 详细"""
    name: str = Field(description="人物的姓名")
    age: int = Field(description="人物的年龄，0-150", ge=0, le=150)
    sentiment: str = Field(description="情感倾向：positive/negative/neutral")
```

> 结构化输出详解见 Day04 - Output Parsers。

---

## 运行指南

```bash
cd "Day02 - Model I/O模型接口层/Code"

# 按顺序运行
python 01_chat_models.py          # 基础实例化
python 02_llm_models.py           # LLM vs ChatModel
python 03_invoke_batch_async.py   # 四种调用方式
python 04_model_config.py         # 配置与回退
```

---

> 掌握 Model I/O 后，进入 Day03 学习 Prompt 管理与模板化。
