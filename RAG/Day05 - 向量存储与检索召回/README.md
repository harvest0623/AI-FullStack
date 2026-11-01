# Day05 - 向量存储与检索召回

> 文本转成向量后，需要一个"存得下、查得快、还能按元数据过滤"的地方——**向量数据库**。检索质量很大程度取决于：存哪、怎么查、Top-K 取多少、能否按业务元数据过滤。今天把检索召回这一环做扎实。

## 学习目标

完成本章后，你将能够：

- 比较主流向量库，为不同规模选型
- 用 Chroma / FAISS 完成向量的增、删、改、查
- 理解 Top-K 召回与相似度阈值的取舍
- 用元数据过滤实现业务维度的精准检索
- 理解 ANN 索引算法（IVF / HNSW）对延迟与召回的影响

---

## 一、向量数据库是什么

**向量数据库** = 存储向量 + 支持"按相似度快速检索最邻近（ANN）"的引擎。RAG 索引阶段把所有文档块向量批量写入；查询阶段把查询向量拿去查 Top-K 最近邻。

一个 RAG 检索的本质动作就是：

```
doc_vecs ──入库──▶ VectorStore
query_vec ──相似度查找──▶ Top-K 个 doc_vec + 对应原文/元数据
```

---

## 二、主流向量库对比

| 向量库 | 类型 | 元数据过滤 | 扩展性 | 适用 |
|--------|------|-----------|--------|------|
| **Chroma** | 嵌入式 | 好 | 中 | 原型/中小规模，易上手 |
| **FAISS** | 内存库（非独立服务） | 弱（需自建） | 高（单机） | 学术/大向量集 |
| **Qdrant** | 独立服务 | 强 | 高 | 生产、过滤复杂 |
| **Milvus** | 分布式服务 | 强 | 极高 | 海量、集群 |
| **Weaviate** | 独立服务 | 强 | 高 | 混合检索、图关系 |
| **pgvector** | Postgres 插件 | 强 | 中 | 已有 Postgres 沉淀 |

选型口诀：
- 学习/原型 → **Chroma**
- 单机海量、纯检索 → **FAISS**
- 生产需要强过滤/多租户 → **Qdrant / pgvector**
- 超大规模集群 → **Milvus**

---

## 三、向量库核心操作：CRUD

无论选哪个库，都围绕四个动作（以 Chroma 为例，LangChain 封装）：

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

vecs = Chroma.from_documents(docs, embeddings, persist_directory="./chroma") # 建库
# 查
hits = vecs.similarity_search_with_score(q, k=3)     # 检索（带分）
# 增
vecs.add_texts(["新文档..."], metadatas=[{"dept": "技术部"}])
# 改/删
vecs.delete(ids=["chunk_id_xxx"])
```

- **增删改**：文档更新后同步维护索引（Day11 讲增量同步）。
- **持久化**：`persist_directory` 存盘，重启不丢。

---

## 四、Top-K 召回与相似度阈值

检索要回答两个问题：**取多少个（k）？多像才算相关（threshold）？**

| 参数 | 作用 | 调优 |
|------|------|------|
| `k`（Top-K） | 每次召回块数 | 太小漏信息，太大脑噪声+成本；依据问题复杂度与块粒度设 |
| 相似度阈值 | 过滤过相关的结果 | 防止"矮子里拔将军"，低于阈值则"无答案" |

```python
# LangChain 指定 k
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
# Chroma 加相似度阈值过滤（不同库阈值口径不同）
```

> 阈值=0 表示不限制。实际常设为"既能有答案又不引入低质块"，需结合指标实测（Day10）。

---

## 五、元数据过滤：业务维度的"第二把筛子"

向量库常支持对 `metadata` 进行前置过滤（pre-filter）——**先按业务条件缩小候选集，再算相似度**：

```python
# Chroma where 过滤
hits = vectorstore.similarity_search(
    "报销标准", k=3,
    filter={"dept": "财务部"}
)
```

场景举例（DataIQ）：
- 按部门：只搜财务制度 → `{"dept": "财务部"}`
- 按密级：只搜公开文档 → `{"level": "public"}`
- 按来源：只搜"产品手册" → `{"doc_type": "手册"}`

元数据过滤能**同时提升精度与性能**（缩小搜索空间），也支撑多租户/权限隔离（Day09/11）。

---

## 六、ANN 索引算法：性能与召回率的权衡

向量库在"近似最近邻（ANN）"上用了多种索引，理解它们对生产选型重要：

| 索引 | 思路 | 速度 | 内存 | 适用 |
|------|------|------|------|------|
| **Flat（暴力）** | 全量比较 | 慢 | 低 | 小数据、需精确 |
| **IVF** | 聚类分桶，先定桶再比较 | 快 | 中 | 大数据、可接受近似 |
| **HNSW** | 多层图近邻跳转 | 极快 | 高 | 高实时、高质量 |

- 数据小 → Flat 足够且精确
- 数据大 → HNSW / IVF 换取速度（牺牲一点点召回）

> 生产选索引时要观察：延迟、召回率（Recall）、内存占用三者的平衡（Day11 监控）。

---

## 场景：DataIQ 的检索存储选型

- 起步阶段：选用 **Chroma**（内置在本地、易上手），`persist_directory=./storage`。
- 规模上来后：迁移至 **Qdrant** 或 **pgvector**（支持强过滤 + 多租户）。
- 每个文档块 metadata 含 `dept/doc_type/level/file_name`，供按部门/密级过滤。
- Top-K 默认 3，阈值默认关闭，Day10 用指标再调。

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_chroma_store.py` | Chroma 建库/检索/增删改 | 是（嵌入，可降级） |
| `Code/02_faiss_store.py` | FAISS 构建 + 检索 + 保存加载 | 是（嵌入，可降级） |
| `Code/03_metadata_filter.py` | 元数据过滤检索 | 是（嵌入，可降级） |
| `Code/04_index_metrics.py` | Flat vs HNSW 召回/延迟对比 | 否（纯向量模拟） |
| `Code/README.md` | 运行说明 | - |

---

## 关键知识点总结

1. **向量库 = 存向量 + ANN 检索**。
2. **选型**：原型用 Chroma，生产强过滤用 Qdrant/pgvector，海量用 Milvus。
3. **CRUD 四操作**：建、查、增、删改。
4. **Top-K 与阈值**：控制召回数量与下限质量。
5. **元数据过滤**：业务前置过滤，提精度提性能。
6. **ANN（Flat/IVF/HNSW）**：用速度换召回与内存的权衡。

---

## 实战练习

### 练习 1：搭建 Chroma 检索

运行 `01_chroma_store.py`，往库中写入 DataIQ 各制度块，对多个问题做 `similarity_search`，观察召回与分数。

### 练习 2：元数据过滤

运行 `03_metadata_filter.py`，给不同块打上 `dept` 标签，实现"只看财务部文档"的检索，对比加不加过滤的召回差异。

### 练习 3：k 与阈值实验

修改 `01` 中的 `k`，从 1→5 观察召回多样性；再为 Chroma 增加相似度阈值过滤，观察"过低分数被剔除"。

### 练习 4：索引权衡模拟

运行 `04_index_metrics.py`，模拟 Flat 与 HNSW 在 10 万向量上的延迟与召回差异，判断 DataIQ（约 5 万块）该选哪种。

---

## 下一步

向量检索解决了"粗召回"，但相似度最高的不一定是"最相关"的。Day06 引入重排序——用交叉编码器对召回结果精排，显著提升最终质量。