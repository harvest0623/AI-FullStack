# Day02 - LLM API 调用与集成

API 是调用 LLM 的最基本方式。无论你用 ChatGPT 还是自建 AI 应用，底层都在调用各家模型的 HTTP API。掌握多模型 API 的集成方式——理解请求参数、消息角色体系、错误处理、同步与异步差异，并能设计统一客户端屏蔽底层差异——是 AI 工程师的核心技能。本章以 OpenAI API 为主线，横向对比 Anthropic Claude 与国内主流模型，最后抽象出「多模型统一客户端」，让你写一次业务代码就能在多家模型间自由切换。

## 学习目标

- 掌握 OpenAI Chat Completions API 的完整参数与响应结构
- 理解 System/User/Assistant/Tool 消息角色体系与多轮对话构造
- 学会调用 Anthropic Claude API，掌握其与 OpenAI 的关键差异
- 掌握国内模型（通义千问 / 智谱 / DeepSeek）的两种调用方式（兼容 OpenAI / 原生 SDK）
- 建立 API Key 安全管理意识，掌握错误处理与重试策略
- 理解同步 vs 异步调用的适用场景
- 能设计多模型统一客户端，实现模型路由

---

## 一、OpenAI API 详解

OpenAI 的 Chat Completions API 是事实上的「行业事实标准」，多数国内模型都兼容其格式。

### 1.1 接口与请求

```
POST https://api.openai.com/v1/chat/completions
Authorization: Bearer $OPENAI_API_KEY
Content-Type: application/json
```

请求体核心参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `model` | string | 模型名，如 `gpt-4o`、`gpt-4o-mini` |
| `messages` | array | 消息列表（角色 + 内容），构成对话上下文 |
| `temperature` | float | 采样温度 0-2，越高越随机，越低越确定 |
| `top_p` | float | 核采样，与 temperature 二选一（一般只调一个） |
| `max_tokens` | int | 最大输出 Token 数 |
| `stop` | array | 停止序列，命中即停止生成 |
| `seed` | int | 随机种子，配合 temperature=0 可尽量复现 |
| `response_format` | object | `{"type":"json_object"}` 启用 JSON Mode |
| `n` | int | 一次生成几条候选回答 |
| `stream` | bool | 是否流式返回 |
| `tools` | array | 定义可调用工具（Function Calling） |
| `tool_choice` | string/object | 工具调用策略（auto/none/指定函数） |

### 1.2 响应结构

```json
{
  "id": "chatcmpl-xxx",
  "model": "gpt-4o-mini-2024-07-18",
  "choices": [
    {
      "message": {"role": "assistant", "content": "..."},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 40,
    "total_tokens": 65
  }
}
```

关键字段：
- `choices[].message`：模型回复内容
- `choices[].finish_reason`：结束原因（`stop` 正常结束 / `length` 达 max_tokens / `tool_calls` 调用工具）
- `usage`：Token 用量（输入/输出/总计），**计费依据**
- `id` / `model`：请求 ID 与实际使用的模型

### 1.3 模型列表

| 模型 | 定位 | 上下文 |
| --- | --- | --- |
| `gpt-4o` | 旗舰多模态 | 128K |
| `gpt-4o-mini` | 高性价比主力 | 128K |
| `gpt-4-turbo` | 上一代旗舰 | 128K |
| `o1` / `o1-mini` | 推理模型（深度思考） | 128K/200K |
| `o3-mini` | 推理模型性价比款 | 200K |

### 1.4 价格体系

- 输入 Token 与输出 Token **分别计价**（输出通常贵 3-4 倍）
- 不同模型价格差异巨大（gpt-4o-mini 比 gpt-4o 便宜约 15 倍）
- 部分模型有**缓存折扣**（命中上下文缓存，输入价大幅下降）
- 详见 `Code/README.md` 价格对比表

---

## 二、消息角色体系详解

`messages` 是 LLM API 的核心，每条消息有 `role` 与 `content`：

| 角色 | 作用 | 优先级 |
| --- | --- | --- |
| `system` | 设定身份、行为规范、输出格式，**全局最高优先级** | 最高 |
| `user` | 用户输入 | - |
| `assistant` | LLM 的历史回复，用于构造多轮对话上下文 | - |
| `tool` | 工具调用返回的结果（Function Calling 场景） | - |

### 多轮对话如何构造

LLM 本身**无状态**，每轮都要把完整历史传回去。多轮对话 = 把历史 user/assistant 消息按序拼接：

```python
messages = [
    {"role": "system", "content": "你是编程助手"},
    {"role": "user", "content": "Python list 和 tuple 区别？"},   # 第1轮用户
    {"role": "assistant", "content": "list 可变，tuple 不可变..."}, # 第1轮回复
    {"role": "user", "content": "那谁更快？"},                     # 第2轮用户
]
```

> 这意味着对话越长，每次请求的 Token 越多、越贵。如何管理历史是 Day03 的主题。

### System Prompt 的重要性

System Prompt 决定了模型的「人设」与边界，是控制输出风格、安全性的第一道防线。优秀实践：
- 明确身份与能力边界（"你是 XX 助手，只回答 XX 领域问题"）
- 规定输出格式（"只返回 JSON"、"不超过 100 字"）
- 给出示例（Few-shot）
- 设定拒绝策略（"不确定时说明，不要编造"）

---

## 三、Anthropic Claude API

Claude 是 OpenAI 之外最重要的闭源模型，长文本、写作、代码能力突出。

### 3.1 接口

```
POST https://api.anthropic.com/v1/messages
x-api-key: $ANTHROPIC_API_KEY
anthropic-version: 2023-06-01
```

Python SDK：`pip install anthropic`

### 3.2 与 OpenAI 的关键差异

| 维度 | OpenAI | Claude |
| --- | --- | --- |
| `system` | messages 内的一条消息 | **顶级参数**，不在 messages 中 |
| `max_tokens` | 可选 | **必填** |
| `temperature` 默认 | 1.0，范围 0-2 | 1.0，范围 0-1 |
| 返回内容 | `choices[0].message.content`（字符串） | `content` 数组（多 block） |
| 消息约束 | 较宽松 | user/assistant **必须严格交替** |
| 流式 | `stream=True` | `stream=True`（事件类型不同） |

### 3.3 模型

| 模型 | 定位 |
| --- | --- |
| `claude-3-5-sonnet` | 综合最强，性价比高 |
| `claude-3-5-haiku` | 轻量快速 |
| `claude-3-opus` | 上一代旗舰 |

### 3.4 示例对比

OpenAI 风格：
```python
client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"},
    ],
)
```

Claude 风格：
```python
client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=512,                       # 必填
    system="你是助手",                     # 顶级参数
    messages=[{"role": "user", "content": "你好"}],
)
```

---

## 四、国内模型 API

国内模型普遍**兼容 OpenAI 格式**，迁移成本极低；同时部分提供原生 SDK。

| 模型 | 厂商 | 兼容 OpenAI | 原生 SDK | base_url（兼容模式） |
| --- | --- | --- | --- | --- |
| 通义千问 Qwen | 阿里 | ✅ | dashscope | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 智谱清言 GLM | 智谱 | ✅ | zhipuai | `https://open.bigmodel.cn/api/paas/v4` |
| 文心一言 | 百度 | ❌（自有） | 百度 SDK | - |
| Kimi | Moonshot | ✅ | - | `https://api.moonshot.cn/v1` |
| DeepSeek | 深度求索 | ✅ | - | `https://api.deepseek.com` |

### 兼容 OpenAI 的调用方式（以 DeepSeek 为例）

只需换 `base_url` 和 Key，其余代码与 OpenAI 完全一致：

```python
from openai import OpenAI
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com")
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "你好"}],
)
```

### 原生 SDK（以智谱为例）

```python
from zhipuai import ZhipuAI
client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))
resp = client.chat.completions.create(
    model="glm-4-flash",
    messages=[{"role": "user", "content": "你好"}],
)
```

> **选型建议**：能用兼容 OpenAI 格式就用，便于统一客户端；只有用到原生特有能力时才用原生 SDK。

---

## 五、API Key 安全管理

**铁律：绝不硬编码 Key 在代码里**（含提交到 Git、写入 Notebook、贴进文档）。

| 方式 | 适用场景 | 示例 |
| --- | --- | --- |
| 环境变量 | 本地开发、CI/CD | `os.getenv("OPENAI_API_KEY")` |
| `.env` 文件 | 本地开发，配合 python-dotenv | `load_dotenv()` 加载，加入 `.gitignore` |
| 密钥管理服务 | 生产环境 | AWS Secrets Manager / HashiCorp Vault / 阿里 KMS |
| 配置中心 | 多服务共享 | 配合权限管控与审计 |

`.env` 示例：
```dotenv
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
```

加载：
```python
from dotenv import load_dotenv
import os
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

---

## 六、错误处理

| 错误类型 | HTTP 状态 | 原因 | 处理策略 |
| --- | --- | --- | --- |
| `AuthenticationError` | 401 | Key 无效/欠费 | 检查 Key 与账户 |
| `RateLimitError` | 429 | 触发限流 | 指数退避重试、降频、升级额度 |
| `InvalidRequestError` | 400 | 参数错误 | 校验 model/messages/参数 |
| `APIConnectionError` | - | 网络/超时 | 重试（设 timeout） |
| `ContextWindowExceededError` | - | Token 超限 | 截断历史或换长窗口模型 |
| `APIStatusError` | 5xx | 服务端错误 | 重试 + 降级 |

### 指数退避重试模板

```python
import time
def call_with_retry(fn, retries=5, base=1.0):
    for i in range(retries):
        try:
            return fn()
        except RateLimitError:
            time.sleep(base * (2 ** i))  # 1, 2, 4, 8, 16 秒
    raise RuntimeError("重试次数耗尽")
```

> 生产环境推荐用 `tenacity` 库，支持更丰富的重试策略。

---

## 七、同步 vs 异步调用

| 维度 | 同步 | 异步 |
| --- | --- | --- |
| 接口 | `OpenAI()` | `AsyncOpenAI()` |
| 调用 | `client.chat.completions.create()` | `await client.chat.completions.create()` |
| 并发 | 串行阻塞 | 高并发（`asyncio.gather`） |
| 适用 | 脚本/单次/调试 | 批量/流式/Web 服务/高并发 |
| 复杂度 | 简单 | 需理解 async/await |

**何时用异步：**
- 批量调用几十上百条请求
- 流式输出（边生成边显示）
- Web 服务中不阻塞主线程（FastAPI + async）

**何时用同步：**
- 脚本、Notebook、调试
- 顺序依赖的调用链

---

## 八、多模型统一客户端设计

为屏蔽不同模型 API 差异，抽象出统一客户端：

```
        LLMClient (ABC)
        - chat(messages) -> ChatResult
            ▲
   ┌──────┴──────┬─────────────┐
OpenAIClient  AnthropicClient  DashScopeClient
```

设计要点：
1. **抽象基类** `LLMClient` 定义统一 `chat()` 接口
2. **统一数据结构** `Message` / `ChatResult` 屏蔽各家差异
3. **子类实现** 各自 SDK 适配（如 Claude 把 system 提到顶级、补 max_tokens）
4. **模型路由** 按任务类型选模型（简单任务用便宜模型，复杂任务用旗舰）

好处：上层业务只依赖 `LLMClient`，切换模型只改配置，符合 AISearch 项目 `clients/` 的封装思想。完整实现见 `Code/04_unified_client.py`。

---

## 关键知识点总结

### 1. OpenAI API 参数速查表

| 参数 | 作用 | 常用值 |
| --- | --- | --- |
| `model` | 模型 | gpt-4o-mini |
| `messages` | 对话上下文 | [{role, content}] |
| `temperature` | 随机性 | 0-0.7 常用 |
| `max_tokens` | 输出上限 | 按需 |
| `response_format` | JSON 输出 | json_object |
| `stream` | 流式 | True/False |
| `tools` | 工具调用 | 函数定义 |

### 2. 响应结构速查

```json
{
  "choices": [{"message": {"content": "..."}, "finish_reason": "stop"}],
  "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
}
```

### 3. 多模型 API 差异对比表

| 维度 | OpenAI | Claude | 国内（兼容） |
| --- | --- | --- | --- |
| system 位置 | messages 内 | 顶级参数 | messages 内 |
| max_tokens | 可选 | 必填 | 可选 |
| 兼容 OpenAI | 自身 | 否 | 多数兼容 |
| 原生 SDK | openai | anthropic | zhipuai/dashscope |

### 4. 错误类型速查表

| 错误 | 状态码 | 处理 |
| --- | --- | --- |
| AuthenticationError | 401 | 查 Key |
| RateLimitError | 429 | 退避重试 |
| InvalidRequestError | 400 | 查参数 |
| APIConnectionError | - | 重试 |

### 5. 同步 vs 异步对比

| | 同步 | 异步 |
| --- | --- | --- |
| 场景 | 单次/调试 | 批量/流式/服务 |
| 客户端 | `OpenAI` | `AsyncOpenAI` |
| 关键字 | - | `await` |

---

## 代码文件说明

| 文件 | 内容 |
| --- | --- |
| `Code/01_openai_chat.py` | OpenAI 完整调用示例（7 个场景 + 错误处理） |
| `Code/02_anthropic_chat.py` | Claude 调用，对比 OpenAI 差异 |
| `Code/03_chinese_models.py` | 国内模型三种调用方式 |
| `Code/04_unified_client.py` | 多模型统一客户端 + 模型路由 |
| `Code/README.md` | 申请步骤、SDK 安装、价格表、错误排查、异步指南 |

> 所有脚本用 `python-dotenv` 加载 `.env`，用 `os.getenv("OPENAI_API_KEY")` 取密钥，**无硬编码**。

---

## 实战练习

### 练习 1：System Prompt 工程实验

用 `01_openai_chat.py` 的结构，设计 3 套不同 System Prompt（如「严谨学者」「段子手」「JSON 接口」），对同一问题「介绍量子计算」生成回答，对比风格差异，总结 System Prompt 对输出的影响规律。

### 练习 2：多模型横向评测

用 `04_unified_client.py` 的统一客户端，向 3 个不同模型（如 gpt-4o-mini、Qwen-plus、DeepSeek-chat）提同一组 5 个问题（含中文理解、代码、推理），从**质量/速度/成本（Token）**三个维度评测，写一份对比报告。

### 练习 3：实现指数退避重试

在统一客户端的 `chat()` 外层包一层「指数退避重试」装饰器，对 `RateLimitError` 与 `APIConnectionError` 自动重试 5 次。提示：可用 `tenacity` 库或手写循环，重试间隔 1/2/4/8/16 秒。

---

## 下一步

你已经能让代码「调用」大模型了。但每轮对话都把全部历史发回去，Token 越来越多、越来越贵——Day03 将解决**Token 管理与上下文工程**：如何计数、如何压缩历史、如何估算成本、如何处理长文本，把 LLM 用得又省又稳。
