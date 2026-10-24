# Day03 - Ollama HTTP API 编程调用

## 今日目标

离开命令行，用程序说话。今天掌握 Ollama 的 REST API——这是它最灵活也是最重要的接口，`/api/chat`、`/api/generate`、`/api/embed` 三大端点全部拿下，并掌握**流式**生成。

学完今天，你将能够：

1. 列出并理解 Ollama 的核心 REST 端点
2. 用 `requests` 调 `/api/chat` 完成多轮对话（构造消息、传参、解析响应）
3. 实现流式逐 token 输出，并理解流式与非流式的取舍
4. 调用 `/api/generate` 处理单次文本生成，理解它和 chat 的区别
5. 正确处理错误、超时与格式非法

---

## 一、REST API 端点总览

| 端点 | 方法 | 请求体关键字段 | 用途 |
|------|------|--------------|------|
| `/api/chat` | POST | `model, messages, stream, options` | 多轮对话 |
| `/api/generate` | POST | `model, prompt, stream, options, system` | 单次生成/补全 |
| `/api/embed` | POST | `model, input` | 文本 -> 向量 |
| `/api/tags` | GET | — | 本地模型列表 |
| `/api/show` | POST | `model` | 模型详情 |
| `/api/pull` | POST | `model, stream` | 拉取模型 |
| `/api/ps` | GET | — | 内存中已加载模型 |

### 1.1 基础 URL

```
BASE_URL = "http://127.0.0.1:11434"
```

### 1.2 统一请求模板

```python
requests.post(
    f"{BASE_URL}/api/chat",
    json={...},      # json= 自动设置 Content-Type
    stream=False,    # 是否流式
    timeout=...,
)
```

---

## 二、/api/chat：多轮对话（最常用）

### 2.1 请求体

```json
{
  "model": "llama3.1",
  "messages": [
    {"role": "system", "content": "你是严谨的助手。"},
    {"role": "user", "content": "解释什么是量子计算"}
  ],
  "stream": false,
  "options": { "temperature": 0.7, "num_predict": 128 }
}
```

### 2.2 响应（非流式，`stream:false`）

```json
{
  "model": "llama3.1",
  "message": { "role": "assistant", "content": "你好！..." },
  "done": true,
  "total_duration": 123456789,     // 总耗时(ns)
  "load_duration": 1000,           // 模型加载耗时(ns)
  "prompt_eval_count": 20,         // 提示 token 数
  "eval_count": 45,                // 生成 token 数
  "eval_duration": 40000000,       // 生成耗时(ns)
  "prompt_eval_duration": ...
}
```

**重要**：`message.content` 就是答案；`eval_count` 等用于统计 token/成本。

---

## 三、流式（stream:true）

### 3.1 为什么流式

长回答如果等全部生成完再返回，用户要干等几十秒。流式让**每生成一个 token 立刻下发**，像打字一样逐字出现（对应 ChatGPT 的流式打字效果）。

### 3.2 流式响应结构（NDJSON）

每行是一个 JSON 对象，`done:false` 时带增量 `message.content`，最后一行 `done:true`：

```json
{"message":{"content":"你"},"done":false}
{"message":{"content":"好"},"done":false}
... 
{"done":true,"eval_count":45,...}
```

### 3.3 代码骨架

```python
resp = requests.post(url, json={**body, "stream": True}, stream=True, timeout=60)
for line in resp.iter_lines(decode_unicode=True):
    if not line:
        continue
    obj = json.loads(line)
    if obj.get("done"):
        stats = obj      # 末行带统计
        break
    print(obj["message"]["content"], end="", flush=True)
```

> 用 `iter_lines()` 逐行读，而不是等整个 body。

---

## 四、/api/generate vs /api/chat

| 维度 | `/api/chat` | `/api/generate` |
|------|-------------|----------------|
| 输入 | `messages`（多轮） | `prompt`（单次，可带前置 history） |
| 适合 | 对话、多轮 | 补全、单次生成 |
| options | 支持 | 支持 |
| system | 通过 messages 传 | 单独 `system` 字段 |

> 底层两者都可能复用同一模型，只是**入参形态**不同。日常对话优先 `chat`；纯文本补全（如代码续写）用 `generate`。

---

## 五、错误处理

| 情形 | 现象 | 处理 |
|------|------|------|
| 服务未启动 | 连接被拒 | 检查 `ollama serve` |
| 模型不存在 | HTTP 404 / "model not found" | 先 `ollama pull` |
| 参数非法 | HTTP 400 | 校验 messages/options |
| 单次流断开 | 读取中断 | 捕获异常并按偏移续传/重试 |

超时设置是重点：非流式 `timeout=60`，流式 `timeout=(5, 300)`（连 5s，读 300s）。

---

## 六、今日核心要点

```
1. 三大端点：/api/chat(对话) /api/generate(补全) /api/embed(向量)
2. chat 用 messages，generate 用 prompt
3. stream:true 开流式，iter_lines 逐行读，done=true 结尾带统计
4. 响应里的 eval_count / durations 用于 token 与性能统计
5. timeout 区别：非流式 vs 流式（连接/读取双超时）
6. 错误四大类：连接/404模型 /400参数 /流中断
```

---

## 七、代码文件说明

| 文件 | 内容 | 关键知识点 |
|------|------|-----------|
| `01_rest_overview.py` | 全部端点一览 + 请求/响应结构速查 | API 图谱 |
| `02_chat_api.py` | `/api/chat` 多轮对话 + 元数据解析（token/耗时） | 对话接口 |
| `03_streaming.py` | 流式逐 token 输出，非流式对比 | 流式 |
| `04_generate_api.py` | `/api/generate` + 与 chat 区别 | 补全接口 |

双模式兼容：`ollama_util.py` 提供检测与真实调用，无环境走模拟。

---

## 八、延伸思考

1. 为什么不直接把整个响应等完再返回？流式对首屏延迟的改善有多大？
2. `messages` 里塞太多历史 token，cost 如何变化？（答案在 Day05/06）
3. `/api/generate` 的 `history` 字段和 chat 的 `messages` 本质差别是什么？
4. 流式下如何做"边生成边停"?（用户按下停止，如何中断服务端）

---

## 九、明日预告

Day04 学习 **Python SDK**：用官方 `ollama` 库把今天的 REST 调用变成更 Pythonic 的一行，含 `.chat()/.generate()/.embed()` 与异步并发。