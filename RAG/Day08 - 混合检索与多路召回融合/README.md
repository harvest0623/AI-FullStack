# Day08 - 混合检索与多路召回融合

> 稠密（向量）检索擅长"语义相关"但可能漏掉"精确关键词"，稀疏检索（BM25）擅长"精确匹配"但对"同义改写"无能为力。**混合检索 = 稀疏 + 稠密多路召回，再融合排序**，是提升 RAG 召回鲁棒性的有效手段。

## 学习目标

完成本章后，你将能够：

- 解释稠密检索与稀疏检索（BM25）的原理与优缺点
- 用 BM25 做关键词检索、用嵌入做稠密检索
- 用加权融合与 RRF 融合多路召回结果
- 对比混合检索与单一检索在不同场景下的表现
- 在 LangChain / LlamaIndex 中落地混合检索

---

## 一、两种检索范式

| 维度 | 稠密检索（Dense） | 稀疏检索（BM25 / Sparse） |
|------|------------------|---------------------------|
| 表示 | 语义向量 | 词频/逆文档频率向量 |
| 原理 | 相似度（语义） | 关键词精确/加权匹配 |
| 优点 | 捕捉同义改写、语义接近 | 精确术语、稀有词命中强 |
| 缺点 | 对精确词/专业术语麻木 | 对同义改写、词序不敏感 |
| 典型 | OpenSearch/向量库 | Elasticsearch/Lucene |

**结论**：两者互补。语义检索抓"意思像"，稀疏检索抓"字符合"，混合应对真实多样的查询。

---

## 二、稠密检索（向量）快速回顾

Day04/05 已实现：查询向量 vs 文档向量做相似度 Top-K。擅长"这句和那句意思接近"。

```python
hits = vectorstore.similarity_search(query, k=10)   # 稠密召回
```

---

## 三、稀疏检索 BM25

BM25 基于词频（TF）与逆文档频率（IDF）打分的经典词法检索：

```python
from rank_bm25 import BM25Okapi
corpus = [doc.split() for doc in docs_text]
bm25 = BM25Okapi(corpus)
scores = bm25.get_scores(query.split())
```

优点：
- 对**专有名词、产品型号、编号**（如 "DATA-PRO-2024"）极其有效；
- 无需嵌入、可离线、可解释。

---

## 四、多路召回融合（Fusion）

把稠密 + 稀疏两路各自的 Top-K 合并成一个最终列表，常见两种：

### 4.1 加权融合（Weighted Sum）

把两路分数归一化后加权求和。需处理两路分数不同量纲。

### 4.2 RRF（Reciprocal Rank Fusion）⭐ 推荐

**RRF 不看分数，只看排名**，稳定且无需归一化：

```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```
其中 `k` 为常数（通常 60），`rank_i(d)` 是文档在第 i 路检索中的排名。

```python
def rrf(rankings_per_source, k=60):
    scores = {}
    for rankings in rankings_per_source:
        for rank, doc in enumerate(rankings):
            scores[doc] = scores.get(doc, 0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

- 优点：不依赖分数量纲，对多路稳定。
- 是所有多路召回融合的主流默认。

---

## 五、融合后的一体化管道

```
查询
 ├── ① 稠密检索  Top-10  ├┐
 └── ② BM25检索  Top-10  ├┴─▶ RRF 融合 ──▶ 取 Top-5 ──▶ (重排) ──▶ 生成
```

LangChain 的融合检索器 `EnsembleRetriever` 内置了 RRF：

```python
from langchain.retrievers import EnsembleRetriever
ensemble = EnsembleRetriever(retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5])
hits = ensemble.invoke(query)
```

LlamaIndex 类似可用 `QueryFusionRetriever` 实现 RRF 融合多路。

---

## 六、混合 vs 单一，何时值得

| 场景 | 结论 |
|------|------|
| 含大量专有名词/编号/精确条款 | 强烈建议混合（稀疏补上稠密的盲区） |
| 语义型问答（同义改写多） | 混合仍稳健，略有开销 |
| 极简原型、无杂词 | 单稠密即可 |
| 有 Elasticsearch/结构库 | 天然适合稀疏一路参与混合 |

原则：**混合检索提升"召回鲁棒性"**，配合重排进一步精排；用指标（Day10）确认要不要上。

---

## 场景：DataIQ 的混合检索

DataIQ 制度里满是专有名词（"DATA-PRO-2024"、"云闪付"）与精确条款号，单靠向量常漏检。方案：
- 稠密：Chroma 向量库（语义）；
- 稀疏：对制度全文跑 BM25；
- 融合：`EnsembleRetriever` + RRF；
- 再加重排，取 Top-3 进生成。

用 Day10 的 Recall/MRR 对比"单稠密 vs 混合"以验证收益。

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_bm25_retrieval.py` | 用 rank_bm25 做关键词检索 | 否 |
| `Code/02_dense_retrieval.py` | 稠密向量检索 | 是（可降级） |
| `Code/03_hybrid_fusion.py` | 稠密+BM25 多路 RRF 融合 | 是（可降级） |
| `Code/04_hybrid_compare.py` | 单一 vs 混合检索对比 | 否 |
| `Code/README.md` | 运行说明 | - |

---

## 关键知识点总结

1. **稠密管语义、稀疏管关键词**，二者互补。
2. **BM25** 基于 TF-IDF，对专业术语/编号高效。
3. **RRF 融合**：按排名求和 `1/(k+rank)`，稳定不依赖分数。
4. **EnsembleRetriever / QueryFusionRetriever** 可快速落地。
5. **混合提升召回鲁棒性**，用指标决定是否值得。

---

## 实战练习

### 练习 1：体验 BM25

运行 `01_bm25_retrieval.py`，用含产品编号的查询验证 BM25 对精确匹配的高分。

### 练习 2：RRF 手推

给定"稠密路：[A,B,C]、稀疏路：[B,C,A]"，手写 RRF 求和，验证 B 排第一、A/C 次之，最终排序。

### 练习 3：混合 vs 单一

运行 `04_hybrid_compare.py`，构造"语义相关但无精确词"和"精确词但语义远"两类查询，观察何者混合更优。

### 练习 4：DataIQ 落地

用 LangChain `EnsembleRetriever` 为 DataIQ 组装"BM25 + Chroma"融合检索，设定权重，对比纯向量检索在专有名词查询上的提升。

---

## 下一步

解决了"召回"，还有"架构"。Day09 处理多文档与知识库架构——多索引、元数据路由、先摘要再检索，让 RAG 面对海量多源数据时依然又快又准。