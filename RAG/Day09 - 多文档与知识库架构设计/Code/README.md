# Day09 - 多文档与知识库架构设计 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_multi_index.py` | 按文档类型分索引、独立检索 | 是（可降级） |
| `02_meta_router.py` | 元数据过滤路由 | 是（可降级） |
| `03_summary_then_retrieve.py` | 先摘要再检索（Agentic） | 否 |
| `04_multi_tool_router.py` | 多工具/多库 Router 调度 | LLM/关键词双路 |

## 运行

```bash
python 01_multi_index.py
python 02_meta_router.py
python 03_summary_then_retrieve.py
python 04_multi_tool_router.py
```

> 01/02 配置 `OPENAI_API_KEY` 走真实嵌入，否则降级为哈希向量；03 纯本地；04 无 Key 时用关键词路由器（离线可用）。

## 依赖

```bash
pip install langchain-community chromadb faiss-cpu langchain-openai python-dotenv
```