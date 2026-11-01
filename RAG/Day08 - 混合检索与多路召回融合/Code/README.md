# Day08 - 混合检索与多路召回融合 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_bm25_retrieval.py` | BM25 稀疏（关键词）检索 | 否 |
| `02_dense_retrieval.py` | 稠密（向量）检索 | 是（可降级） |
| `03_hybrid_fusion.py` | 稠密+BM25 多路 RRF 融合 | 是（可降级） |
| `04_hybrid_compare.py` | 混合 vs 单一检索对比 | 否 |

## 运行

```bash
pip install rank_bm25   # 01/03 用到
python 01_bm25_retrieval.py
python 02_dense_retrieval.py
python 03_hybrid_fusion.py
python 04_hybrid_compare.py
```

> `02`/`03` 的稠密部分配置 `OPENAI_API_KEY` 走真实嵌入，否则降级为哈希向量（仅演示流程）。
> `04` 纯本地模拟，无依赖要求。

## 依赖

```bash
pip install rank_bm25 langchain-community faiss-cpu langchain-openai python-dotenv
```