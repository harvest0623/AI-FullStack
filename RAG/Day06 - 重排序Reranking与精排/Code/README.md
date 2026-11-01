# Day06 - 重排序 Reranking 与精排 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_rerank_concept.py` | Bi-Encoder vs CrossEncoder 概念模拟 | 否 |
| `02_rerank_pipeline.py` | 粗召回→重排→生成完整管道 | 可选 |
| `03_rerank_metrics.py` | MRR / nDCG 量化重排收益 | 否 |

## 运行

```bash
python 01_rerank_concept.py
python 02_rerank_pipeline.py
python 03_rerank_metrics.py
```

> `02` 的重排器优先级：Cohere（`COHERE_API_KEY`）→ 本地 bge（`pip install FlagEmbedding`）→ 词重叠降级。不配置则走降级演示，仍能看清管道结构。

## 依赖

```bash
# 本地 bge 重排（可选，体积较大）
pip install FlagEmbedding
# Cohere（可选）
pip install cohere
```