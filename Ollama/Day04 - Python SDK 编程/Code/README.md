# Day04 代码说明

## 运行方式

```bash
cd "Ollama/Day04 - Python SDK 编程/Code"

python 01_sdk_chat.py       # .chat() 基本对话
python 02_sdk_stream.py     # 流式
python 03_sdk_embed.py      # 嵌入
python 04_async_client.py   # 异步并发
```

无 `ollama` SDK 或无 Ollama 环境时自动走 `SimOllama` 模拟；安装 SDK 后走真实调用。

## 环境准备

```bash
pip install ollama          # 官方 SDK
ollama pull llama3.1         # 对话模型
ollama pull nomic-embed-text # 嵌入模型（03 用到）
```

## 文件说明

| 文件 | 内容 | 关键概念 |
|------|------|---------|
| `01_sdk_chat.py` | `.chat(model, messages, options)` 快速对话 + Client(host) | 基础 |
| `02_sdk_stream.py` | `stream=True` 返回生成器，逐 token 打印 | 流式 |
| `03_sdk_embed.py` | `.embed()` 生成向量 + 余弦相似度语义排序 | 嵌入 |
| `04_async_client.py` | `asyncio.gather` + `AsyncClient` 并发，对比串行/并发耗时 | 异步 |

## 观察要点

**01_sdk_chat.py**
- 若安装 SDK 且服务就绪，`ollama.chat(...)` 真实返回；否则走模拟
- 展示 `resp["message"]["content"]` 取值与 `eval_count`

**02_sdk_stream.py**
- 流式生成器遍历 `chunk["message"]["content"]`
- `chunk.get("done")` 在最后一拍为真，可取统计

**03_sdk_embed.py**
- "如何退换货？" 的嵌入与候选文档相似度排序
- 正确匹配 "退货流程说明" / "如何申请退款"（模拟也可能近似）
- 手工 `cos_sim` 验证 `embed()` 是向量化的本质

**04_async_client.py**
- 5 个请求串行 vs 并发，直观看到加速比 ~5x
- 真实用 `await AsyncClient().chat()`，模拟用 `await asyncio.sleep`

## 对照 REST（Day03）

| SDK | 等价 REST |
|-----|-----------|
| `ollama.chat` | `POST /api/chat` |
| `ollama.generate` | `POST /api/generate` |
| `ollama.embed` | `POST /api/embed` |
| `ollama.list` | `GET /api/tags` |