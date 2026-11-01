# Day05 - 向量存储与检索召回 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_chroma_store.py` | Chroma 建库/检索/增删改/持久化 | 是（可降级） |
| `02_faiss_store.py` | FAISS 构建/检索/保存加载 | 是（可降级） |
| `03_metadata_filter.py` | 元数据过滤检索对比 | 是（可降级） |
| `04_index_metrics.py` | Flat vs HNSW 速度/召回模拟 | 否 |

## 运行

```bash
python 01_chroma_store.py
python 02_faiss_store.py
python 03_metadata_filter.py
python 04_index_metrics.py
```

> 01/02/03 配置 `OPENAI_API_KEY` 走真实嵌入，否则降级为本地哈希向量（仅演示流程）。

## 依赖

```bash
pip install langchain-community chromadb faiss-cpu langchain-openai python-dotenv
```