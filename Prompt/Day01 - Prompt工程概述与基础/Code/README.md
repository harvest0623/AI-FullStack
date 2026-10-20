# LLM 基础概念指南

本文件是 Day01 的代码配套指南，提供主流 LLM 模型清单、Token 计算工具 `tiktoken` 使用方法、上下文窗口管理策略、温度与 Top-p 调参指南，以及各主流模型 API 调用的 Python 基础示例。

---

## 一、主流 LLM 模型清单与特点

### 1. 海外模型

| 模型 | 厂商 | 上下文窗口 | 特长 | 适用场景 |
|------|------|-----------|------|---------|
| GPT-4 Turbo | OpenAI | 128K | 综合能力强、Function Calling 稳定 | 复杂推理、Agent |
| GPT-4o | OpenAI | 128K | 多模态、速度快、价格低 | 实时对话、多模态 |
| GPT-4o mini | OpenAI | 128K | 性价比高 | 高频轻量任务 |
| Claude 3.5 Sonnet | Anthropic | 200K | 长文档、写作、代码、遵循指令 | 长文本、结构化输出 |
| Claude 3 Opus | Anthropic | 200K | 最强推理 | 复杂分析 |
| Gemini 1.5 Pro | Google | 1M-2M | 超长上下文、多模态 | 整书/视频处理 |
| Gemini 1.5 Flash | Google | 1M | 快速、便宜 | 高频任务 |

### 2. 国内模型

| 模型 | 厂商 | 上下文窗口 | 特长 | 适用场景 |
|------|------|-----------|------|---------|
| 文心一言 4.0 | 百度 | 8K-128K | 中文友好、合规 | 中文业务 |
| 通义千问 Max | 阿里 | 32K-128K | 阿里云集成、中文强 | 企业应用 |
| 通义千问 Plus | 阿里 | 131K | 性价比 | 通用 |
| 智谱清言 GLM-4 | 智谱 | 128K | 国产 Agent、长上下文 | Agent、国产化 |
| DeepSeek-V2/V3 | 深度求索 | 128K | 开源、性价比极高、代码强 | 代码、私有部署 |
| Kimi (Moonshot) | 月之暗面 | 200K | 长文本对话 | 长文档问答 |
| 豆包 Doubao | 字节 | 128K | 价格低、火山引擎集成 | 高频业务 |

### 3. 选型决策表

| 需求 | 推荐模型 |
|------|---------|
| 海外复杂推理 / Agent | GPT-4 / Claude 3.5 |
| 海外高频低成本 | GPT-4o mini / Claude Haiku |
| 超长文档（>200K） | Gemini 1.5 Pro / Claude 3.5 |
| 国内合规中文 | 文心 4.0 / 通义 / 智谱 |
| 国内高频低成本 | DeepSeek / 豆包 |
| 代码生成 | GPT-4o / Claude 3.5 / DeepSeek |
| 私有化部署 | DeepSeek / 智谱 GLM 开源版 |

---

## 二、Token 计算工具 tiktoken 使用

`tiktoken` 是 OpenAI 开源的 BPE 分词器，可离线计算 GPT 系列模型的 token 数。

### 1. 安装

```bash
pip install tiktoken
```

### 2. 基础用法：计算 token 数

```python
import tiktoken

# 选择分词器
# - cl100k_base: GPT-4 / GPT-3.5
# - o200k_base: GPT-4o
encoding = tiktoken.get_encoding("cl100k_base")

text = "我想退货，订单号 SO20240501-001"
tokens = encoding.encode(text)
print(f"字符数: {len(text)}")
print(f"Token 数: {len(tokens)}")
print(f"Token 列表: {tokens}")
print(f"解码还原: {encoding.decode(tokens)}")
```

输出示例：
```
字符数: 21
Token 数: 17
Token 列表: [151, 23278, 4517, 11, 42029, 9118, 83, 36111, 83, 50677, 48669, 629, 16, 220, 16, 16, 1]
解码还原: 我想退货，订单号 SO20240501-001
```

### 3. 中英文 token 消耗对比

```python
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

samples = {
    "英文": "I want to return the order SO20240501.",
    "中文": "我想退掉订单 SO20240501。",
    "中英混合": "Order SO20240501 的退款申请已提交，please wait.",
}

for name, text in samples.items():
    tokens = enc.encode(text)
    print(f"{name:8s} | 字符 {len(text):3d} | token {len(tokens):3d} | 比 {len(tokens)/len(text):.2f}")
```

输出示例：
```
英文      | 字符  38 | token  12 | 比 0.32
中文      | 字符  19 | token  18 | 比 0.95
中英混合  | 字符  50 | token  35 | 比 0.70
```

### 4. 使用模型名自动选分词器

```python
import tiktoken

# 根据模型名自动选择
enc_gpt4  = tiktoken.encoding_for_model("gpt-4")
enc_gpt4o = tiktoken.encoding_for_model("gpt-4o")

text = "智能客服 SmartCS 为您服务"
print(f"GPT-4  token: {len(enc_gpt4.encode(text))}")
print(f"GPT-4o token: {len(enc_gpt4o.encode(text))}")
```

### 5. 成本估算函数

```python
import tiktoken

def estimate_cost(text, model="gpt-4o", input_price_per_1k=0.0025):
    """估算单次输入成本"""
    enc = tiktoken.encoding_for_model(model)
    tokens = len(enc.encode(text))
    cost = tokens / 1000 * input_price_per_1k
    return tokens, cost

tokens, cost = estimate_cost("我想退货，订单号 SO20240501-001")
print(f"Token: {tokens}, 估算成本: ${cost:.6f}")
```

> 注意：`tiktoken` 仅适用于 OpenAI 模型。Claude、国内模型需用各自 SDK 的计数接口或估算。

---

## 三、上下文窗口管理策略

### 1. 滑动窗口（最常用）

只保留最近 N 轮对话：

```python
def build_messages(system_prompt, history, user_input, max_turns=6):
    """history: [{"role":"user","content":"..."},{"role":"assistant","content":"..."},...]"""
    recent = history[-max_turns * 2:]  # 每轮含 user + assistant
    messages = [{"role": "system", "content": system_prompt}] + recent + [{"role": "user", "content": user_input}]
    return messages
```

### 2. 摘要压缩

当历史超过阈值时，把早期对话压缩为摘要：

```python
def compress_history(history, llm_client):
    long_history = history[:-6]  # 保留最近 3 轮原文
    recent = history[-6:]

    summary_prompt = "请将以下对话压缩为不超过 150 字的摘要，保留订单号、诉求、进度：\n" + format_history(long_history)
    summary = llm_client.chat(summary_prompt)

    return [
        {"role": "system", "content": f"历史对话摘要：{summary}"},
        *recent
    ]
```

### 3. 分块处理长文档

```python
def chunk_text(text, max_chars=1500):
    """按自然段落分块"""
    paragraphs = text.split("\n\n")
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) > max_chars:
            if current:
                chunks.append(current)
            current = p
        else:
            current = current + "\n\n" + p if current else p
    if current:
        chunks.append(current)
    return chunks

# 逐块处理
for i, chunk in enumerate(chunk_text(long_doc)):
    result = llm_client.chat(f"分析第 {i+1} 块：\n{chunk}")
```

### 4. 策略选择

| 策略 | 适用 | 实现 |
|------|------|------|
| 滑动窗口 | 多轮对话 | 保留最近 N 轮 |
| 摘要压缩 | 长会话 | 早期对话压成摘要 |
| 分块 | 长文档 | 切块逐个处理 |
| RAG 检索 | 知识库 | 向量检索 Top-K 注入 |

---

## 四、温度与 Top-p 调参指南

### 1. Temperature

| Temperature | 行为 | 适用场景 | SmartCS 应用 |
|-------------|------|---------|-------------|
| 0.0 | 确定性，每次相同 | 分类、抽取、代码 | 意图识别、工单分类 |
| 0.1-0.3 | 低随机性 | 事实问答、摘要、翻译 | FAQ 回答、订单查询 |
| 0.4-0.7 | 平衡 | 对话、建议、写作 | 客服对话、商品推荐 |
| 0.8-1.0 | 高随机性 | 头脑风暴、创意 | 营销文案、活动 slogan |
| >1.0 | 极高（不推荐） | 实验用途 | — |

### 2. Top-p（核采样）

只从累积概率达到 p 的候选 token 中采样：

- `top_p=1.0`：不限制，全部候选参与采样
- `top_p=0.9`：忽略概率极低的长尾 token（推荐默认值）
- `top_p=0.1`：只选最高概率的少数 token（接近确定性）

### 3. 调参原则

```python
# 原则：Temperature 与 Top-p 二选一调整，不要同时大幅改动
# 场景 A：需要确定性输出
params_a = {"temperature": 0, "top_p": 1.0}

# 场景 B：平衡对话
params_b = {"temperature": 0.7, "top_p": 1.0}

# 场景 C：用 top_p 控制而非 temperature
params_c = {"temperature": 1.0, "top_p": 0.9}
```

### 4. SmartCS 各模块推荐参数

| 模块 | Temperature | Top-p | 理由 |
|------|-------------|-------|------|
| 意图识别 | 0 | 1.0 | 需确定性分类 |
| FAQ 问答 | 0.2 | 1.0 | 准确为主 |
| 订单查询 | 0 | 1.0 | 事实性输出 |
| 客服对话 | 0.5-0.7 | 1.0 | 需人情味 |
| 商品推荐 | 0.3-0.5 | 1.0 | 稳定但略灵活 |
| 营销文案 | 0.9-1.0 | 0.95 | 创意优先 |

---

## 五、各模型 API 调用基础示例

### 1. OpenAI（GPT-4 / GPT-4o）

```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(api_key="your-openai-api-key")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是 SmartCS 电商客服，专业热情简洁。"},
        {"role": "user", "content": "我想退货，订单号 SO20240501-001"}
    ],
    temperature=0.5,
    top_p=1.0,
    max_tokens=300
)

print(response.choices[0].message.content)
print(f"Token 用量: {response.usage}")
```

### 2. Anthropic Claude

```bash
pip install anthropic
```

```python
import anthropic

client = anthropic.Anthropic(api_key="your-anthropic-api-key")

# Claude 的 system 是独立参数，不在 messages 内
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system="你是 SmartCS 电商客服，专业热情简洁。",
    messages=[
        {"role": "user", "content": "我想退货，订单号 SO20240501-001"}
    ],
    temperature=0.5,
    max_tokens=300
)

print(response.content[0].text)
print(f"输入 token: {response.usage.input_tokens}, 输出 token: {response.usage.output_tokens}")
```

> Claude 的 system 是顶层参数，与 OpenAI 放在 messages 数组首位不同。

### 3. 通义千问（阿里云 DashScope）

```bash
pip install dashscope
```

```python
import dashscope

dashscope.api_key = "your-dashscope-api-key"

response = dashscope.Generation.call(
    model="qwen-max",
    messages=[
        {"role": "system", "content": "你是 SmartCS 电商客服，专业热情简洁。"},
        {"role": "user", "content": "我想退货，订单号 SO20240501-001"}
    ],
    temperature=0.5,
    result_format="message"
)

print(response.output.choices[0].message.content)
```

### 4. 智谱 GLM-4

```bash
pip install zhipuai
```

```python
from zhipuai import ZhipuAI

client = ZhipuAI(api_key="your-zhipu-api-key")

response = client.chat.completions.create(
    model="glm-4",
    messages=[
        {"role": "system", "content": "你是 SmartCS 电商客服，专业热情简洁。"},
        {"role": "user", "content": "我想退货，订单号 SO20240501-001"}
    ],
    temperature=0.5,
    max_tokens=300
)

print(response.choices[0].message.content)
```

### 5. DeepSeek（兼容 OpenAI 接口）

```python
from openai import OpenAI

# DeepSeek 兼容 OpenAI SDK，只需改 base_url
client = OpenAI(api_key="your-deepseek-api-key", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是 SmartCS 电商客服，专业热情简洁。"},
        {"role": "user", "content": "我想退货，订单号 SO20240501-001"}
    ],
    temperature=0.5
)

print(response.choices[0].message.content)
```

### 6. 通用调用封装（支持多模型切换）

```python
from openai import OpenAI
import anthropic

def chat(model, messages, temperature=0.5, system=None):
    """统一调用入口，支持 OpenAI 系 / Claude"""
    if model.startswith("claude"):
        client = anthropic.Anthropic(api_key="your-anthropic-key")
        sys_content = system or ""
        # 从 messages 提取 system
        if not sys_content:
            sys_msgs = [m for m in messages if m["role"] == "system"]
            if sys_msgs:
                sys_content = sys_msgs[0]["content"]
                messages = [m for m in messages if m["role"] != "system"]
        resp = client.messages.create(
            model=model, system=sys_content, messages=messages,
            temperature=temperature, max_tokens=1024
        )
        return resp.content[0].text
    else:
        client = OpenAI(api_key="your-openai-key")
        resp = client.chat.completions.create(
            model=model, messages=messages,
            temperature=temperature, max_tokens=1024
        )
        return resp.choices[0].message.content

# 调用示例
msgs = [
    {"role": "system", "content": "你是 SmartCS 客服。"},
    {"role": "user", "content": "退款流程是什么？"}
]
print(chat("gpt-4o", msgs))
print(chat("claude-3-5-sonnet-20241022", msgs))
```

---

## 六、开发环境检查清单

- [ ] Python 3.10+
- [ ] 安装 `openai`、`anthropic`、`tiktoken`（按需安装对应 SDK）
- [ ] 配置 API Key（建议用环境变量，不要硬编码）
- [ ] 能用 `tiktoken` 计算 token 数
- [ ] 能调用至少一个模型的 chat 接口
- [ ] 理解 temperature / top_p 的取值含义

> 安全提示：API Key 务必通过环境变量或 `.env` 文件加载，不要写入代码仓库。示例中的 `"your-xxx-api-key"` 仅为占位符。
