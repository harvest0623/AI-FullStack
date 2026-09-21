# Day07 Code - 流式输出与事件处理示例

> 本目录是 Day07 的可运行 Python 示例。

## 依赖安装

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv
```

- `01_stream_modes.py` 是纯逻辑演示，**无需 API Key**。
- `02_astream_events.py`、`03_typing_effect.py` 需要真实 LLM 调用，请在项目根目录 `.env` 配置：

```bash
OPENAI_API_KEY=sk-xxxx
```

## 文件清单

| 文件 | 运行方式 | 演示重点 | 是否需要 Key |
|------|----------|----------|--------------|
| `01_stream_modes.py` | `python 01_stream_modes.py` | `values` / `updates` / `debug` 对比 | 否 |
| `02_astream_events.py` | `python 02_astream_events.py` | `astream_events` 订阅、事件结构、tag 过滤 | 是 |
| `03_typing_effect.py` | `python 03_typing_effect.py` | 逐 token 打字机效果 | 是 |

## 运行建议

- 先跑 `01` 理解 stream_mode 差异，再跑 `02`/`03` 观察 token 级事件。
- 若模型名不适应你的供应商，可在代码中将 `ChatOpenAI(model="gpt-3.5-turbo")` 换成你环境可用的模型。