# Day02 Code - LLM API 调用与集成示例

本目录包含 Day02「LLM API 调用与集成」的配套代码，覆盖 OpenAI、Anthropic Claude、国内主流模型（通义千问 / 智谱 / DeepSeek）的调用方式，以及多模型统一客户端的设计实现。

## 环境准备

```bash
# Python 3.10+
pip install openai anthropic zhipuai python-dotenv
```

### 配置 .env

在项目根目录（或本目录）创建 `.env` 文件，按需填入你拥有的模型 Key（**切勿硬编码、切勿提交到 Git**）：

```dotenv
# OpenAI
OPENAI_API_KEY=sk-你的密钥
# 如使用代理/兼容服务，可设置 base_url
# OPENAI_BASE_URL=https://your-proxy.com/v1

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-你的密钥

# 通义千问 DashScope
DASHSCOPE_API_KEY=sk-你的密钥

# 智谱清言
ZHIPUAI_API_KEY=你的密钥

# DeepSeek
DEEPSEEK_API_KEY=sk-你的密钥
```

> 推荐同时把 `.env` 加入 `.gitignore`。

## 文件说明

| 文件 | 内容 | 主要 Key |
| --- | --- | --- |
| `01_openai_chat.py` | OpenAI 完整调用：基础/多轮/System/temperature/max_tokens/JSON Mode/错误处理 | `OPENAI_API_KEY` |
| `02_anthropic_chat.py` | Claude 调用，对比与 OpenAI 的差异（system 顶级参数、max_tokens 必填等） | `ANTHROPIC_API_KEY` |
| `03_chinese_models.py` | 通义千问 / 智谱 / DeepSeek 调用（兼容 OpenAI 格式 + 原生 SDK） | 各自 Key |
| `04_unified_client.py` | 多模型统一客户端：LLMClient 抽象基类 + 三个子类 + 模型路由 | 已配置的任意 Key |

## 运行方式

```bash
python 01_openai_chat.py
python 02_anthropic_chat.py
python 03_chinese_models.py
python 04_unified_client.py
```

> 未配置对应 Key 的示例会自动跳过并给出提示，不会中断整个脚本。

## 各模型 API 申请步骤

| 模型 | 申请入口 | 获取 Key 位置 |
| --- | --- | --- |
| OpenAI | https://platform.openai.com | Dashboard → API Keys |
| Anthropic | https://console.anthropic.com | Settings → API Keys |
| 通义千问 | https://dashscope.console.aliyun.com | API-KEY 管理 |
| 智谱清言 | https://open.bigmodel.cn | API Keys |
| DeepSeek | https://platform.deepseek.com | API Keys |
| Moonshot Kimi | https://platform.moonshot.cn | API Key 管理 |

> 国内模型平台通常需实名认证；OpenAI/Anthropic 需海外网络与支付方式。

## SDK 安装命令

```bash
pip install openai              # OpenAI 及所有兼容服务（Qwen/DeepSeek/Kimi）
pip install anthropic           # Anthropic Claude
pip install zhipuai             # 智谱清言原生 SDK
pip install dashscope           # 通义千问原生 SDK（可选，本目录用兼容接口）
pip install python-dotenv       # 加载 .env
```

## 价格对比表（参考价，单位 $/1M tokens，输入/输出）

| 模型 | 输入价格 | 输出价格 | 备注 |
| --- | --- | --- | --- |
| gpt-4o | $2.5 | $10 | 旗舰，多模态 |
| gpt-4o-mini | $0.15 | $0.6 | 性价比首选 |
| o1 | $15 | $60 | 推理模型，贵 |
| claude-3-5-sonnet | $3 | $15 | 综合强 |
| claude-3-5-haiku | $0.8 | $4 | 轻量快速 |
| qwen-plus | 约 ¥0.8/1M | 约 ¥2/1M | 中文性价比高 |
| deepseek-chat | 约 ¥1/1M(命中缓存¥0.1) | 约 ¥2/1M | 极致性价比 |
| glm-4-flash | 免费 | 免费 | 智谱免费档 |

> 价格随时可能调整，以各平台官网为准。DeepSeek 命中上下文缓存时输入价大幅下降。

## 常见错误排查清单

| 错误/现象 | 原因 | 解决方案 |
| --- | --- | --- |
| `AuthenticationError (401)` | Key 无效/过期 | 检查 Key 拼写、是否欠费、是否用错平台 Key |
| `RateLimitError (429)` | 触发速率/额度限制 | 降低频率、指数退避重试、升级额度 |
| `InvalidRequestError (400)` | 参数错误 | 检查 model 名、messages 格式、max_tokens |
| 连接超时/`APIConnectionError` | 网络问题 | 检查网络/代理，增加 timeout，重试 |
| `context_length_exceeded` | Token 超上下文 | 截断历史、换更长窗口模型（见 Day03） |
| Claude 报 `max_tokens required` | Claude 必填项缺失 | 补上 `max_tokens` 参数 |
| 中文返回乱码 | 编码问题 | 确保终端 UTF-8，Python 文件头部声明编码 |
| `OPENAI_API_KEY` 未加载 | .env 未配置或未调用 load_dotenv | 确认 .env 路径、调用 `load_dotenv()` |

## 异步调用指南

高并发/批量/流式场景推荐异步：

```python
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI()  # 同样从环境变量读 Key
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
    )
    print(resp.choices[0].message.content)

asyncio.run(main())
```

**何时用异步：**
- 批量调用几十上百条请求（配合 `asyncio.gather` 并发）
- 流式输出（`stream=True`，边生成边返回）
- Web 服务中不阻塞主线程

**何时用同步：**
- 脚本/Notebook 单次调用
- 顺序依赖的调用链
- 调试阶段（更易追踪堆栈）

## 下一步

掌握多模型 API 调用后，进入 Day03 学习 **Token 管理与上下文工程**——如何控制成本、管理对话历史、处理长文本，这是把 LLM 用「省」用「稳」的关键。
