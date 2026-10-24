# Day03 代码说明

## 运行方式

```bash
cd "Ollama/Day03 - Ollama HTTP API 编程调用/Code"

python 01_rest_overview.py    # API 端点图谱
python 02_chat_api.py         # /api/chat 多轮对话
python 03_streaming.py        # 流式生成
python 04_generate_api.py     # /api/generate
```

无 Ollama 环境也运行（走模拟）。

## 文件说明

| 文件 | 内容 | 关键概念 |
|------|------|---------|
| `01_rest_overview.py` | 全部端点 + chat/generate/embed 请求响应契约对照 | API 图谱 |
| `02_chat_api.py` | `/api/chat` 多轮对话，解析 message.content 与 token/耗时 | 对话接口 |
| `03_streaming.py` | `iter_lines` 逐行读 NDJSON，逐 token 实时打印，结尾取统计 | 流式 |
| `04_generate_api.py` | `/api/generate` 补全 + chat vs generate 对比 | 补全接口 |

## 观察要点

**01_rest_overview.py**
- 七个端点的方法/请求体/用途对照表
- chat 的 messages + options 完整请求示例
- 流式 NDJSON 的逐行结构（`done:false` 增量 + `done:true` 统计）

**02_chat_api.py**
- 四段 messages（system + user + assistant + user）演示多轮
- 响应中的 `eval_count` / `eval_duration` 换算成 `tokens/s` 速度指标
- 元数据字段语义表（prompt_eval_count / eval_count / total_duration...）

**03_streaming.py**
- `for raw in r: line = raw.decode()` 逐行解析——核心要点
- `done:true` 行退出并取统计
- 模拟模式用 `time.sleep` 模拟打字机，便于观察"增量"

**04_generate_api.py**
- 明确 chat 与 generate 的本质差异（messages vs prompt）
- 用代码补全示例体现 generate 的用途

## 真实调用前提

```bash
ollama pull llama3.1
# 02/03/04 检测到模型后自动走真实 API
```