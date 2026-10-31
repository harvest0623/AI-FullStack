# Day02 - 基础RAG流程（朴素RAG）· 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_naive_rag_langchain.py` | LangChain 朴素 RAG 全流程 | 是（可降级） |
| `02_naive_rag_llama.py` | LlamaIndex 朴素 RAG 全流程 | 是（可降级） |
| `03_retrieval_inspect.py` | 查看检索 TopK 与分数 | 是（嵌入） |

## 运行

```bash
# LangChain 版朴素 RAG
python 01_naive_rag_langchain.py

# LlamaIndex 版朴素 RAG
python 02_naive_rag_llama.py

# 查看检索结果（可设 TOP_K=5 调整召回数）
python 03_retrieval_inspect.py
```

> `01`/`02` 会自动生成示例文档 `dataiq.md`；配置了 `OPENAI_API_KEY` 才真正调用嵌入与生成，否则降级为演示链路。

## 依赖

```bash
# LangChain 路线
pip install langchain-core langchain-community langchain-openai faiss-cpu

# LlamaIndex 路线
pip install llama-index llama-index-embeddings-openai llama-index-llms-openai
```

## 环境变量

在项目根目录 `.env` 中配置：

```ini
OPENAI_API_KEY=sk-xxxx
OPENAI_MODEL=gpt-4o-mini   # 可选，默认
```