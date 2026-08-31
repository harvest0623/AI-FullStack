# Day10 Code - Callbacks 与 Streaming 代码示例

> 本目录包含 Day10 全部可运行 Python 代码，演示 Callback 回调机制与流式输出

## 文件清单

| 文件 | 内容 | 是否需要 API Key | 场景 |
|------|------|-----------------|------|
| `01_callback_handler.py` | 自定义 LoggingCallbackHandler | 是 | ChainQA 执行过程日志 |
| `02_streaming_output.py` | 流式输出（stream/astream/chunk拼接） | 是 | ChainQA 流式问答 |
| `03_logging_callback.py` | MetricsCallbackHandler 指标采集 | 是 | ChainQA 生产监控 |
| `04_langsmith_trace.py` | LangSmith 追踪集成 | 是（可选 LangSmith） | ChainQA 追踪评估 |

## 运行顺序建议

```
01_callback_handler.py  ← 先理解 Callback 基础
      │
      ▼
02_streaming_output.py  ← 再学流式输出（与 Callback 配合）
      │
      ▼
03_logging_callback.py  ← 然后做生产级指标采集
      │
      ▼
04_langsmith_trace.py   ← 最后集成 LangSmith 平台
```

## 环境准备

```bash
# 核心依赖
pip install langchain langchain-openai python-dotenv

# 配置 API Key（.env 文件）
# OPENAI_API_KEY=sk-xxxxxxxx
# 可选：LangSmith 追踪
# LANGCHAIN_API_KEY=ls_xxxxxxxx
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_PROJECT=chainqa
```

## 运行示例

```bash
cd "d:\Coding\AI-FullStack\LangChain\Day10 - Callbacks与Streaming回调流式\Code"

python 01_callback_handler.py
python 02_streaming_output.py
python 03_logging_callback.py
python 04_langsmith_trace.py
```

## Callbacks 与 Streaming 指南

### Callback 方法速查表

| 方法 | 触发时机 | 关键参数 |
|------|---------|---------|
| `on_llm_start` | LLM 调用开始 | serialized, prompts |
| `on_chat_model_start` | ChatModel 调用开始 | serialized, messages |
| `on_llm_new_token` | 生成新 Token（流式） | token |
| `on_llm_end` | LLM 调用结束 | response |
| `on_chain_start` | Chain 开始 | serialized, inputs |
| `on_chain_end` | Chain 结束 | outputs |
| `on_tool_start` | 工具开始 | serialized, input_str |
| `on_tool_end` | 工具结束 | output |
| `on_text` | 文本输出 | text |
| `on_error` | 错误发生 | error |

### 自定义 Handler 模板

```python
from langchain_core.callbacks import BaseCallbackHandler

class MyHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, *, run_id, **kwargs):
        # 记录开始时间、输入
        pass

    def on_llm_new_token(self, token, **kwargs):
        # 流式时逐 Token 处理（打字机效果）
        print(token, end="", flush=True)

    def on_llm_end(self, response, *, run_id, **kwargs):
        # 记录耗时、输出
        pass

    def on_error(self, error, *, run_id, **kwargs):
        # 错误处理
        pass
```

### 流式输出实现步骤

```python
# 1. 模型开启 streaming
model = ChatOpenAI(model="gpt-4o-mini", streaming=True)

# 2. 同步流式
for chunk in chain.stream({"question": "..."}):
    print(chunk, end="", flush=True)

# 3. 异步流式
async for chunk in chain.astream({"question": "..."}):
    print(chunk, end="", flush=True)

# 4. AIMessageChunk 拼接
full = None
for chunk in model.stream("..."):
    full = chunk if full is None else full + chunk
```

### LangSmith 集成教程

1. **注册账号**：访问 https://smith.langchain.com
2. **获取 API Key**：Settings → API Keys → Create
3. **配置 .env**：
   ```
   LANGCHAIN_API_KEY=ls_xxxxxxxx
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=chainqa
   ```
4. **运行代码**：无需改代码，自动上报
5. **查看 Trace**：在 LangSmith 界面查看执行链路

### 生产监控最佳实践

| 监控项 | 实现方式 | 告警阈值 |
|--------|---------|---------|
| 延迟 P95 | MetricsCallbackHandler | > 5s |
| 错误率 | on_error 计数 | > 5% |
| Token 消耗 | on_llm_new_token 计数 | 日预算上限 |
| 成本 | 按模型定价计算 | 日/月预算上限 |
| 缓存命中率 | 对比 invoke 次数 | < 30% 需优化 |

## 常见问题

**Q1：on_llm_new_token 不触发？**
- 检查模型是否设置 `streaming=True`
- 确认用的是 `.stream()` 或 `.invoke()`（invoke 也会触发回调）

**Q2：流式输出有延迟？**
- 网络问题：检查到 API 的连接
- 模型问题：某些模型首 Token 延迟较高
- 未开启 streaming：确认 `streaming=True`

**Q3：LangSmith 看不到 trace？**
- 检查 `LANGCHAIN_TRACING_V2=true`
- 确认 `LANGCHAIN_API_KEY` 正确
- 检查项目名是否正确

## 学习产出

完成本目录代码后，你应能：
- [ ] 继承 BaseCallbackHandler 实现自定义回调
- [ ] 用 .stream() 实现流式输出和打字机效果
- [ ] 拼接 AIMessageChunk 处理流式数据
- [ ] 实现 MetricsCallbackHandler 采集生产指标
- [ ] 配置 LangSmith 追踪并查看可视化链路
