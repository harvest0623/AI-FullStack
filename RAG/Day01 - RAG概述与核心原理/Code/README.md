# Day01 - RAG 概述与核心原理 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_rag_vs_ft.py` | 对比"模型直答 vs RAG 注入上下文"，直观感受 RAG 价值 | 是（LLM） |
| `02_rag_pipeline_preview.py` | 极简 RAG 三步流程预览（索引/检索/生成） | 可选 |
| `03_failure_modes.py` | RAG 失败模式诊断知识卡片 | 否 |

## 快速运行

```bash
# 1. 对比 RAG 与直答（需 OPENAI_API_KEY）
python 01_rag_vs_ft.py

# 2. 全流程预览（无 Key 会降级为说明文字）
python 02_rag_pipeline_preview.py

# 3. 失败模式诊断卡（纯本地）
python 03_failure_modes.py
```

## 依赖

```bash
pip install python-dotenv openai langchain-core langchain-community langchain-openai faiss-cpu
```

> 本章以概念为主，工程级依赖会在 Day02 起逐步引入。