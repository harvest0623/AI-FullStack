# Code 说明

本目录为「Day06 - 上下文长度与对话管理」的可执行代码。

- 01_context_window.py   num_ctx 与 token 统计（规则演示）
- 02_multi_turn.py       多轮对话历史构建
- 03_session_isolation.py 多会话隔离
- 04_history_trim.py     历史裁剪与摘要
- ollama_util.py         双模式共用工具（含 SimOllama 及真实 API 封装）

运行方式：

```bash
python 01_context_window.py
python 02_multi_turn.py
python 03_session_isolation.py
python 04_history_trim.py
```

> 有真实 Ollama 时走真实对话；无环境时退回规则模拟，逻辑仍可观察。