# Day06 代码 - 检索器指南

> 运行本章代码前，请先安装依赖：
> ```
> pip install llama-index llama-index-embeddings-openai python-dotenv
> pip install rank_bm25                        # 02/03 检索关键词用
> pip install llama-index-retrievers-bm25      # 若 BM25Retriever 不在 core 中
> ```

## 各文件说明

| 文件 | 说明 | 关键 API |
|------|------|---------|
| `01_vector_retriever.py` | 向量检索 + top_k 对比 | `index.as_retriever(similarity_top_k=)` / `.retrieve()` / `NodeWithScore` |
| `02_bm25_retriever.py` | BM25 关键词检索 vs 向量 | `BM25Retriever.from_defaults(index=)` |
| `03_hybrid_retriever.py` | 混合检索（RRF 融合） | `QueryFusionRetriever` + `Mode.RECIPROCAL_RANK` |
| `04_custom_retriever.py` | 自定义部门过滤检索器 | `BaseRetriever._retrieve()` |

## 无 Key 降级说明

未检测到 `OPENAI_API_KEY` 时，脚本用内置 `HashEmbedding` 降级，流程可离线跑通。混合检索若缺少 BM25 依赖，会退化为单路向量并给出提示。

---

## Retriever 类型选择决策表

| 需求 | 推荐 |
|------|------|
| 通用语义问答 | `VectorIndexRetriever` ✅ |
| 含精确词/编号 | `BM25Retriever` 或混合 |
| 兼顾语义 + 精确 | `QueryFusionRetriever` 混合 |
| 带业务规则（按部门/权限） | 自定义 `BaseRetriever` |

## VectorIndexRetriever 参数调优

- `similarity_top_k`：返回条数。**过小漏召回，过大掺噪声**。结合 token 预算取 2~10；
- `similarity_cutoff`：相似度阈值，过滤低分项（可选，看底层存储是否支持）；
- 调优方法：换大/小 top_k 检索同一批问题，对比命中与回答质量。

## 混合检索设计

```python
from llama_index.core.retrievers import QueryFusionRetriever, VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever

hybrid = QueryFusionRetriever(
    [vector_retriever, bm25_retriever],
    similarity_top_k=3,
    num_queries=2,                       # 融合前的改写查询数量（可选）
    mode=QueryFusionRetriever.Mode.RECIPROCAL_RANK,
)
nodes = hybrid.retrieve(query)
```

**推荐顺序**：向量(召回广) + BM25(精确词) → RRF 融合 → top-k。适合企业场景中「口语表述 + 专有编号」混杂的查询。

## BM25 使用

- 依赖：`rank_bm25`（以及可能的 `llama-index-retrievers-bm25`）；
- 创建：`BM25Retriever.from_defaults(index=index, similarity_top_k=2)`；
- 特性：基于文本稀疏共现，**不依赖 embedding**，无 API 成本；
- 局限：无法理解同义改写。

## 自定义 Retriever 模板

```python
from llama_index.core.base.base_retriever import BaseRetriever

class MyRetriever(BaseRetriever):
    def __init__(self, index, ...):
        super().__init__()
        self.vector_retriever = index.as_retriever(similarity_top_k=N)

    def _retrieve(self, query: str):
        nodes = self.vector_retriever.retrieve(query)
        # 你的过滤/重排/去重逻辑
        return nodes[:k]
```

## 检索质量评估

- **召回率**：该找回的是否全找回（看重不漏）；
- **精确率**：找回来的是否都相关（看重不误）；
- **命中分数/顺序**：真实相关的排得是否靠前；
- 手段：人工审查 top-k 片段；或用 LlamaIndex 的 `ContextRelevancyEvaluator`（Day11）。

> **版本提示**：本模块基于 `pip install llama-index`（当前稳定版）；`BaseRetriever` 从 `llama_index.core.base.base_retriever` 导入，`QueryFusionRetriever` 从 `llama_index.core.retrievers` 导入。若所用版本导入路径有变化，以官方文档为准并在 import 处调整。