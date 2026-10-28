# Code 说明

本目录为「Day09 - 与LangChain/LlamaIndex集成」的代码。

- 01_langchain_llm.py     ChatOllama 接入（讲解版，可跑）
- 02_langchain_rag.py     LangChain 本地 RAG（需 langchain-ollama）
- 03_llamaindex_llm.py    LlamaIndex 集成（需 llama-index）
- 04_multi_framework.py   框架对比与选择（讲解版，可跑）
- ollama_util.py          双模式共用（本日用于 04 的状态检测）

运行：
```bash
python 01_langchain_llm.py        # 无需额外依赖
python 04_multi_framework.py       # 无需额外依赖
# 02/03 需先：pip install langchain-ollama  或  llama-index-llms-ollama
```

> 01/04 侧重"理解接入方式"，离线即可运行；02/03 开放可选的真实接入，未装依赖时打印指引。