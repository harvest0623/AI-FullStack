# Code 说明

本目录为「Day08 - 工具调用（Function Calling）」的可执行代码。

- 01_tool_schema.py       工具 Schema 拆解
- 02_function_calling.py  一次工具调用往返
- 03_multi_tool.py        多工具调度
- 04_tool_agent.py        工具型 Agent（循环）
- ollama_util.py          双模式共用（含 tools 调用）

运行方式：

```bash
python 01_tool_schema.py
python 02_function_calling.py
python 03_multi_tool.py
python 04_tool_agent.py
```

> 有支持 tools 的模型走真实往返；无则用规则模拟"模型要调工具"的意图，流程可观察。