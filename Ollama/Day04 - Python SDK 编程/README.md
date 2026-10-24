# Day04 - Python SDK 编程

## 今日目标

Day03 用 `requests` 裸调 API，够灵活但繁琐。官方 `ollama` Python SDK 把这些包装成更 Pythonic 的方法，一天搞定 `.chat()/.generate()/.embed()`，连同异步。

学完今天，你将能够：

1. 用 `ollama.chat()` 完成对话（一步到位）
2. 用 `stream=True` 做流式对话
3. 用 `ollama.embed()` 生成嵌入向量
4. 用原生同步 client 与异步 client 处理并发

---

## 一、为什么用 SDK

| 对比 | `requests`(Day03) | `ollama`(SDK) |
|------|-------------------|---------------|
| 对话 | 手动构造 messages + 解析 | `ollama.chat()` 一行 |
| 流式 | 手动 iter_lines + json | 传 `stream=True` 拿生成器 |
| 嵌入 | 手动 POST /api/embed | `ollama.embed()` |
| 类型 | 纯 dict | 有格式，更友好 |

底层 SDK 就是在调同样的 REST API，只是**省去模板代码**。

### 安装

```bash
pip install ollama
```

---

## 二、同步基础用法

### 2.1 对话 `.chat()`

```python
import ollama

resp = ollama.chat(
    model="llama3.1",
    messages=[{"role": "user", "content": "你好！"}],
    stream=False,                 # 默认非流式
    options={"temperature": 0.7},
)
print(resp["message"]["content"])
```

### 2.2 流式 `.chat(stream=True)`

```python
for chunk in ollama.chat(
    model="llama3.1",
    messages=[...],
    stream=True,               # 返回生成器
):
    print(chunk["message"]["content"], end="", flush=True)
```

> 流式时 `chunk["message"]["content"]` 是增量，最后一个 chunk 带 `done:true` 和统计。

### 2.3 一次性 `.generate()`

```python
ollama.generate(model="llama3.1", prompt="补全: def add(a,b):")
# 响应用 resp["response"] 取文本
```

### 2.4 嵌入 `.embed()`

```python
resp = ollama.embed(model="nomic-embed-text", input="你好")
vector = resp["embeddings"][0]   # 512 维 float 列表
```

---

## 三、原生客户端（线程安全 + 异步）

### 3.1 原生 Client

```python
from ollama import Client

client = Client(host="http://127.0.0.1:11434")
resp = client.chat(model="llama3.1", messages=[...])
```

> `Client(host=...)`：指向远程或多实例 Ollama。默认连本机。

### 3.2 异步 AsyncClient

```python
import asyncio
from ollama import AsyncClient

async def main():
    client = AsyncClient()
    resp = await client.chat(model="llama3.1", messages=[...])
    print(resp["message"]["content"])

asyncio.run(main())
```

并发时用 async，能显著提高吞吐（多请求同时进行）。

---

## 四、常用方法与参数速查

| 方法 | 关键参数 | 返回值要点 |
|------|---------|-----------|
| `chat(model, messages, stream, options)` | 多轮 | `message.content` |
| `generate(model, prompt, ...)` | 单次 | `response` |
| `embed(model, input)` | 向量 | `embeddings` |
| `list()` | 模型列表 | `models` |
| `show(model)` | 详情 | `details` |
| `pull(model)` | 拉取 | 进度 |

**options** 直接对应 Day05 的推理参数（temperature/top_p/num_ctx...）。

---

## 五、错误处理与超时

```python
try:
    resp = ollama.chat(model=..., messages=...)
except ollama.ResponseError as e:
    print(f"HTTP {e.status_code}: {e.error}")
# ConnectionError -> 服务没起
# ResponseError   -> 模型不存在/参数错
```

---

## 六、今日核心要点

```
1. SDK 是 REST 的 Pythonic 封装，底层同一套 /api
2. .chat() 对话、.generate() 单次、.embed() 向量、.list() 列表
3. stream=True 返回生成器，逐 token 增量
4. Client(host) 指向多实例；AsyncClient 做并发
5. 错误分两类：ConnectionError(连不上)、ResponseError(4xx/5xx)
```

---

## 七、代码文件说明

| 文件 | 内容 | 关键知识点 |
|------|------|-----------|
| `01_sdk_chat.py` | `.chat()` 快速对话（含 system） | 基础调用 |
| `02_sdk_stream.py` | 流式 + 非流式对比 | 流式生成器 |
| `03_sdk_embed.py` | `.embed()` 生成向量并做相似度 | 嵌入 |
| `04_async_client.py` | async 并发调用 | 异步 |

> 若未安装 `ollama` 库或未启动服务，代码自动退化到 `SimOllama` 模拟，保证离线运行。

---

## 八、延伸思考

1. `Client(host=...)` 能连远程机器吗？有哪些安全考虑？
2. 什么时候必须用 AsyncClient 而不用同步？（并发吞吐）
3. `.chat()` 的 messages 和原生 REST 的 messages 完全等价吗？（基本等价）

---

## 九、明日预告

Day05 学习 **推理参数调优**：temperature / top_p / top_k / num_predict / seed / repeat_penalty 逐个拆解，看它们如何控制输出的确定性、多样性与长度。