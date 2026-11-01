# Day06 - 重排序 Reranking 与精排

> 向量检索返回的是"语义相近"的块，但"语义相近 ≠ 与问题最相关"。**重排序（Reranking）**是在粗召回之后加一道精排：用更精准的模型对 Top-K 结果重新打分，把真正相关的顶到最前，是**提升 RAG 质量性价比极高的手段**。

## 学习目标

完成本章后，你将能够：

- 解释为什么"粗召回 + 精排"优于"单一检索"
- 区分交叉编码器（CrossEncoder）与双塔编码器（Bi-Encoder）
- 使用 API 重排（Cohere Rerank）与本地重排（BGE-Reranker）
- 把重排嵌入 RAG 管道，只把精排后的 Top-N 交给 LLM
- 用 MRR / nDCG 评估重排带来的提升

---

## 一、为什么要重排

纯向量检索的问题：
- 查询与文档往往很短，双塔嵌入只捕捉弱关联，**Top-1 未必真相关**。
- 相似度分数不能完全反映"相关性"。

解决思路——**两阶段检索**：

```
粗召回（Retriever）         精排（Reranker）
向量库取 Top-50         →   重排模型 逐对打分   →   取 Top-3
（快，大候选集）               （准，小精排集）        给 LLM 用
```

- **第一阶段**：向量库快速粗召回 20-50 个候选。
- **第二阶段**：重排器只在这几十个里精排，取前 3-5 个进生成。
- 效果：用很小的额外开销换取**显著更准的 Top-K**。

---

## 二、Bi-Encoder（双塔）vs CrossEncoder（交叉编码器）

这是理解重排的关键：

| 维度 | Bi-Encoder（双塔） | CrossEncoder（交叉编码器） |
|------|-------------------|--------------------------|
| 处理方式 | 查询、文档**分别**编码成向量比相似度 | 查询+文档**拼接**送进一个模型打分 |
| 速度 | 快（可预计算文档向量） | 慢（每对都要前向） |
| 精度 | 中（只有低层交互） | **高**（深层交互） |
| 用在哪 | 向量库检索的嵌入 | **重排序** |

> 检索用 Bi-Encoder（快，文档向量可缓存）；重排用 CrossEncoder（准，但只能处理小集合）。两者是 1+1>2 的组合。

---

## 三、常用重排模型

| 模型 | 类型 | 多语言 | 说明 |
|------|------|--------|------|
| `Cohere Rerank` | API CrossEncoder | 好 | 开箱即用、性能强 |
| `bge-reranker-v2-m3` | 本地 CrossEncoder | 优（中英） | 开源免费、热门 |
| `bge-reranker-base` | 本地 CrossEncoder | 好 | 轻量 |
| `FlagEmbedding` | 本地 | 优 | 配套 bge 嵌入 |

选型：生产追求便捷 → API（Cohere）；数据敏感/省成本 → 本地（bge-reranker）。

```python
# 本地 bge-reranker（类似用法）
from FlagEmbedding import FlagReranker
reranker = FlagReranker("BAAI/bge-reranker-base", use_fp16=True)
score = reranker.compute_score(["query", "document"])
```

---

## 四、把重排嵌入 RAG 管道

一个标准的"检索 + 重排 + 生成"管道：

```python
def retrieve_rerank(query, retriever, reranker, recall=30, top=3):
    cands = retriever.invoke(query)          # ① 粗召回 Top-30
    pairs = [[query, c.page_content] for c in cands]
    scores = reranker.compute_score(pairs)    # ② CrossEncoder 精排打分
    top_ix = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top]
    return [cands[i] for i in top_ix]         # ③ 取 Top-3 进生成
```

要点：
- **recall（召回数）**：粗召回多一些（如 30），给重排更多候选。
- **top（精排数）**：最终只给 LLM 3-5 个，控制上下文与成本。
- **阈值过滤**：低于某分数的块直接丢弃，宁可不说也不乱说。

---

## 五、评估重排效果

引入重排后要在指标上看到提升（Day10 详述），这里先给直觉：

| 指标 | 含义 | 重排的预期影响 |
|------|------|--------------|
| **MRR** | 首个正确答案的倒数排名 | Top-1 更准 → MRR 上升 |
| **nDCG** | 按排序位置加权的相关性 | 相关块更靠前 → nDCG 上升 |
| **端到端答案** | 最终回答质量 | 上下文更准 → 回答更准 |

> 判断标准：**同样 k 下，加重排的 Top-K 命中率是否更高**。是，则值得上。

---

## 场景：DataIQ 精排优化

DataIQ 员工制度较多，类似"报销"的块有几十个。我们：
- 向量库粗召回 Top-30；
- 用 `bge-reranker-base`（本地、中文友好）精排取 Top-3；
- 低于相关性阈值（score < 0.5，视模型而定）的丢弃；
- 用 MRR 对比"仅检索"与"检索+重排"的差距，作为上线依据。

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_rerank_concept.py` | Bi-Encoder vs CrossEncoder 概念模拟 | 否 |
| `Code/02_rerank_pipeline.py` | 完整"检索+重排+生成"管道 | 是（可降级） |
| `Code/03_rerank_metrics.py` | MRR/nDCG 对比含重排与否 | 否 |
| `Code/README.md` | 运行说明 | - |

> Cohere / bge 重排为真实选项，本地 bge 为需要热下载的偏好项；先用概念模拟与管道骨架理解全貌。

---

## 关键知识点总结

1. **两阶段检索**：粗召回 (Bi-Encoder) + 精排 (CrossEncoder)。
2. **CrossEncoder 更准但慢**，只适合小集合精排。
3. **recall 要足、top 要精**：粗召 20-50，精排 3-5。
4. **阈值过滤**：低相关直接丢，防止噪声入 Prompt。
5. **用 MRR / nDCG 量化提升**，而非拍脑袋。

---

## 实战练习

### 练习 1：理解双塔 vs 交叉

阅读并运行 `01_rerank_concept.py`，说清为什么 CrossEncoder 在网络结构上能看到"查询与文档的交互"而 Bi-Encoder 看不到。

### 练习 2：改管道

在 `02_rerank_pipeline.py` 中把 recall 从 30 改为 10 和 50，观察精排结果是否变化，体会"召回越足、重排越有材料"。

### 练习 3：MRR 对比

运行 `03_rerank_metrics.py`，构造一个"纯检索会排错、重排纠正"的案例，计算加与不加重排的 MRR。

### 练习 4：选型

为 DataIQ（中文、约 5 万块、数据敏感）在 Cohere Rerank（API）与 bge-reranker（本地）之间选择并说明理由；预算紧张时你会怎么做？

---

## 下一步

除了重排"精排"，我们还能在**查询端**做文章。Day07 学习查询优化与查询路由：改写、多查询、分解、HyDE，以及按意图分流到正确的知识库。