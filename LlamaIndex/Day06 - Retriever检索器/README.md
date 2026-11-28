# Day06 - Retriever 检索器

> 检索质量决定了回答质量的天花板——检索不到，再强的 LLM 也答不对。

Day05 我们建立了索引，它有两个出口：`as_retriever()` 与 `as_query_engine()`。今天是第一个出口的深度专题——**Retriever（检索器）**。

如果把检索增强生成（RAG）比作「先查资料再回答」，那 Retriever 就是那个「查资料」的角色。它的输出是 Query Engine 做「回答」的输入，因此**检索质量直接决定了回答质量的上限**。

---

## 本章简介

**Retriever（检索器）** 是 LlamaIndex 中**根据用户查询，从索引里返回最相关 Node 的组件**。它不做生成、不做总结，只做一件事：**找出和查询最相关的几个片段（Node），并附加相似度分数**。

Retriever 的标准输出是 **`List[NodeWithScore]`** —— 每个元素是一个（Node + 分数）的组合，其中 `score` 表示该节点与查询的相似度高低。

创建方式极其简单，从索引直接拿：

```python
retriever = index.as_retriever(similarity_top_k=3)
nodes = retriever.retrieve("查询问题")
```

最常用的是基于向量相似度的 **`VectorIndexRetriever`**。除此之外，LlamaIndex 还提供关键词检索（BM25）、混合检索（向量 + 关键词融合）、查询融合（Query Fusion）等多种策略，还可以手写**自定义 Retriever** 以满足特定规则。

本章以 **DataIQ 企业知识库** 为场景，演示各类型 Retriever 的创建、参数调优与效果对比。

---

## 学习目标

完成本章后，你应该能够：

1. 理解 Retriever 的定位，以及它与索引、Query Engine 的关系。
2. 熟练使用 `index.as_retriever()` 创建 `VectorIndexRetriever`，掌握 `similarity_top_k` 等参数。
3. 理解 `NodeWithScore` 的结构（`node` + `score`）。
4. 学会使用 `BM25Retriever` 做精确关键词检索，并理解它与向量检索的差异。
5. 掌握用 `QueryFusionRetriever` 实现「向量 + 关键词」混合检索。
6. 继承 `BaseRetriever` 编写带元数据过滤等自定义逻辑的 Retriever。
7. 理解检索结果排序、过滤与去重，以及检索质量评估方法。

---

## 理论知识

### 一、Retriever 概念

Retriever 位于索引与合成之间，职责单一而关键：

```
用户查询
   │
   ▼
Retriever ──► List[NodeWithScore]  (Node + 相似度分数)
   │
   ▼
QueryEngine 的合成部分（Day07/Day08）
```

核心特征：

- **输入**：一条字符串查询 `query_str`；
- **输出**：`List[NodeWithScore]`，按相关性降序排列；
- **创建**：`index.as_retriever(...)`，或直接 `VectorIndexRetriever(index=index, ...)`。

> 检索决定「答案的依据是什么」。依据错了，后续合成再精妙也是错的——所以检索质量决定了回答质量的天花板。

### 二、VectorIndexRetriever（最常用）

向量检索器基于 embedding 相似度工作：

1. 把查询用 `embed_model` 向量化；
2. 在向量存储中计算与每个 Node 向量的相似度；
3. 取最相似的 Top-N 个 Node。

```python
from llama_index.core.retrievers import VectorIndexRetriever

retriever = VectorIndexRetriever(index=index, similarity_top_k=3)
# 等价简洁写法
retriever = index.as_retriever(similarity_top_k=3)

nodes = retriever.retrieve("DataIQ 年假制度是什么？")
```

### 三、检索参数

| 参数 | 作用 | 调优建议 |
|------|------|---------|
| `similarity_top_k` | 返回的节点条数 | 越大召回越多但噪声越大，综合所需 token 与精度取 2~10 |
| `similarity_cutoff` | 相似度阈值，过滤低于阈值的节点 | 用于剔除"不太相关"的噪声 |

调优直觉：

- `top_k` 太小 → 可能漏掉关键上下文（召回不足）；
- `top_k` 太大 → 混入无关片段，浪费 token 且引入噪声（精确率下降）；
- 结合 `similarity_cutoff` 可在召回与噪声之间取得平衡。

> `similarity_cutoff` 为可选参数（部分底层存储/版本支持），不兼容时忽略即可。

### 四、多种 Retriever

| Retriever | 检索依据 | 适用场景 |
|-----------|---------|---------|
| `VectorIndexRetriever` | 向量语义相似度 | 语义检索、通用问答（默认首选） |
| `BM25Retriever` | BM25 关键词稀疏匹配 | 精确关键词、编号/缩写命中 |
| `QueryFusionRetriever` | 多路检索结果融合 | 结合语义 + 关键词优势 |
| `SemanticRetriever` | 语义向量（同 Vector 系） | 语义召回 |
| 混合检索（Hybrid） | 向量 ⊕ 关键词 融合排序 | 兼顾语义与精确匹配 |

> **BM25Retriever** 需要额外安装 `rank_bm25`，且是可选的 `llama-index-retrievers-bm25`（部分版本已并入 core）。它做的是「关键词共现」的稀疏匹配，擅长命中专有名词/编号，但无法理解同义改写。

### 五、NodeWithScore

检索结果的核心结构：

```python
@dataclass
class NodeWithScore:
    node: BaseNode      # 检索到的节点（.text / .metadata / .node_id）
    score: float        # 相似度分数（越接近相关越…）
```

```python
for nws in nodes:
    print(nws.node.text[:30])           # 节点文本
    print(nws.node.metadata)            # 节点元数据
    print(nws.score)                    # 相似度分数
```

这个结构会原样传递给 Day08 的响应合成器，作为回答的依据。

### 六、自定义 Retriever

当内置检索器满足不了规则（如"只检索某部门文档再按向量排序"）时，可继承 `BaseRetriever` 实现 `_retrieve`：

```python
from llama_index.core.base.base_retriever import BaseRetriever

class MyRetriever(BaseRetriever):
    def _retrieve(self, query: str):
        nodes = self._base_retriever.retrieve(query)
        # 按 metadata 过滤、去重、限流等自定义逻辑
        return filtered_nodes
```

自定义逻辑常见的组合：metadata 过滤 + 向量检索、多个检索器联合、规则重排等。

### 七、检索结果处理

拿到 `List[NodeWithScore]` 后，常见后处理：
- **排序**：按 `score` 降序（内置检索器默认已排序）；
- **过滤**：按阈值过滤低分项（`SimilarityPostprocessor`，Day08 详解）；
- **去重**：合并相同/重复来源，去除重叠片段。

### 八、Retriever 与 Query Engine

Query Engine 是检索 + 合成的整体对外接口：

```
QueryEngine = Retriever（检索，Day06）
            + Synthesizer（合成，Day08）
            + Postprocessor（后处理，Day08）
```

Retriever 是 Query Engine 的**检索部分**。单独使用 `as_retriever()` 让我们只取「相关片段」而不做回答——这在语义搜索、预检、或构建更复杂管道时非常有用。

### 九、检索质量 vs 回答质量

一句话：**检索不好，回答必然受影响**。评估检索质量可从三方面看：

| 指标 | 含义 |
|------|------|
| 召回率（Recall） | 相关文档被检索到的比例 |
| 精确率（Precision） | 检出的结果里真正相关的比例 |
| 命中分数（score） | 是否把真正相关的排在最前面 |

Day11 会系统讲解用 `ContextRelevancyEvaluator` 等方式做自动评估。

---

## 代码文件说明

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_vector_retriever.py` | 向量检索（as_retriever / retrieve / NodeWithScore / top_k 对比） | DataIQ 语义检索 |
| `02_bm25_retriever.py` | BM25 关键词检索 vs 向量检索对比 | 精确关键词命中 |
| `03_hybrid_retriever.py` | 混合检索（向量 + BM25 融合） | 兼顾语义与关键词 |
| `README.md` | 检索器指南（决策表 / 参数 / 混合 / 自定义模板 / 质量评估） | 参考文档 |

> 运行顺序：`01 → 02 → 03 → 04`。`02`/`03` 需要 `pip install rank_bm25`（以及可能需要的 `llama-index-retrievers-bm25`）。

---

## 关键知识点总结

### Retriever 类型对比表

| 类型 | 机制 | 擅长 | 局限 |
|------|------|------|------|
| `VectorIndexRetriever` | 向量相似度 | 语义、同义改写 | 精确词（编号）易偏 |
| `BM25Retriever` | 关键词稀疏匹配 | 精确词、编号 | 无语义理解 |
| `QueryFusionRetriever` | 多路结果融合 | 兼顾两者 | 稍增开销 |
| 自定义 | 任你设计 | 业务规则 | 需自行实现平衡 |

### VectorIndexRetriever 参数速查

- `similarity_top_k`：返回条数（默认 2），权衡召回与噪声；
- `similarity_cutoff`：相似度门槛，过滤低相关项。

### NodeWithScore 结构

```
NodeWithScore
├── node : BaseNode   →  .text 文本 / .metadata 元数据 / .node_id
└── score: float      →  相似度分数
```

### 混合检索设计

```
QueryFusionRetriever([vector_retriever, bm25_retriever],
                     similarity_top_k=3, num_queries=2,
                     mode=QueryFusionRetriever.Mode.RECIPROCAL_RANK)
```
用 **Reciprocal Rank Fusion（RRF）** 把多路排序结果融合，兼顾语义与关键词。

### 检索质量评估

- 召回率 / 精确率 / 命中位置；
- LlamaIndex 的 `ContextRelevancyEvaluator`（Day11）；
- 手工审查：拉出 top-k 片段人工看相关与否。

---

## 实战练习

1. **DataIQ 语义检索**：用 Day05 构建的索引，分别以 `similarity_top_k=2` 和 `similarity_top_k=5` 检索"员工怎么申请年假"，对比两批命中的差异，感受 top_k 对召回与噪声的影响。
2. **关键词 vs 向量对比**：准备一段含专有名词（如单号 `DATA-2024-001`、系统名 `OA 审批`）的文本，分别用 BM25 与向量检索，观察谁命中得更准。
3. **混合检索**：用 `QueryFusionRetriever` 把向量 + BM25 融合，与单一检索对比，思考混合检索在什么场景下收益最大。
4. **自定义 Retriever**：实现一个"只检索 metadata 中 `department=技术部` 文档"的 Retriever，继承 `BaseRetriever`，验证过滤逻辑生效。

> **检查点**：能否说出 `NodeWithScore` 由什么组成？能否解释为什么"检索质量决定了回答质量的天花板"？