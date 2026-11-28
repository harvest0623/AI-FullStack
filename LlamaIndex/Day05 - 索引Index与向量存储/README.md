# Day05 - 索引 Index 与向量存储

> 把解析好的 Node 组织成「可检索」的结构，让语义搜索成为可能。

经过 Day01-Day04，我们已经完成了数据管道的前两阶段 **Load（加载）** 与 **Parse（解析）**，把原始文档变成了一个个带 metadata 的 Node。从今天开始进入 **Index（索引）** 阶段—— 这一阶段的核心问题是：

**如何把一堆 Node 组织起来，使得后续能高效地「根据用户问题找到最相关的片段」？**

答案就是 `Index`。它是 LlamaIndex 数据管道的中枢，是一切 `Retriever` 与 `Query Engine` 的载体。

---

## 本章简介

**Index（索引）** 是 LlamaIndex 中用来**组织 Node、便于高效检索**的数据结构。它把切分后的 Node 以某种方式「存放」起来，并对外提供两个标准接口：

- `as_retriever()` → 返回一个 `Retriever`，用于**检索**（Day06）
- `as_query_engine()` → 返回一个 `Query Engine`，用于**问答**（Day07）

无论你在 LlamaIndex 里用什么索引类型，最后一定跑不出这两个出口。而索引长期演进、最常见、也最值得重点掌握的，就是**向量索引 `VectorStoreIndex`**。

为了支撑向量索引，我们需要一个能存放向量并做相似度计算的**向量存储 VectorStore**，以及负责把文本转成向量的**嵌入模型 embed_model**。同时，为了让索引在多次运行之间不丢失，还需要理解**存储上下文 StorageContext** 与**持久化（persist / load）**。

本章以 **DataIQ 企业知识库** 为场景，一步步搭建、持久化、切换向量存储，并演示文档的增量更新。

---

## 学习目标

完成本章后，你应该能够：

1. 说清 Index 在数据管道中的定位，以及 `as_retriever()` / `as_query_engine()` 两个出口的作用。
2. 列举 LlamaIndex 的常见索引类型（VectorStoreIndex / SummaryIndex / KeywordTableIndex / TreeIndex / KnowledgeGraphIndex / DocumentSummaryIndex）并说出各自适用场景。
3. 用 `VectorStoreIndex.from_documents()` / `from_nodes()` 构建向量索引，并通过 `Settings` 配置嵌入模型。
4. 理解 `StorageContext` 的作用，配置不同的底部向量存储。
5. 掌握索引的**持久化**与**重新加载**完整流程。
6. 学会用 `insert` / `refresh` / `delete_ref_doc` 对索引做**增量更新**。
7. 明白检索与查询的衔接：`index → retriever → query engine`。

---

## 理论知识

### 一、Index 概念

`Index`（索引）是 **Node 在内存/存储中的一种组织和存放方式**。它接收一批 `Node`（或直接把 `Document` 解析成 Node），经过索引构建逻辑，产生一个可以被检索的数据结构。

核心要点：

- 是数据管道 **Index 阶段** 的核心抽象；
- 存放的是「可检索的中间表示」（向量、关键词表、树、知识图谱等）；
- 通常不直接回答用户问题，而是交给下游的 Retriever / Query Engine 使用。

索引对外暴露的两个方法：

| 方法 | 返回 | 用途 | 对应章节 |
|------|------|------|---------|
| `index.as_retriever()` | `Retriever` | 按查询检索相关 Node | Day06 |
| `index.as_query_engine()` | `QueryEngine` | 检索 + 合成，直接得到回答 | Day07 |

> 无论底层是什么存储，`as_retriever()` 与 `as_query_engine()` 是统一出口，这也是为什么构建索引时不需要关心上层如何消费。

### 二、Index 类型概览

LlamaIndex 内置多种索引，对应不同的组织方式与检索策略：

| 索引类型 | 数据结构 | 检索方式 | 适用场景 |
|---------|---------|---------|---------|
| **`VectorStoreIndex`** | 向量（embedding 相似度） | 语义相似度 | 语义检索、通用问答（**最常用**） |
| `SummaryIndex` | 顺序列表 | 全量顺读 | 小型文档整体总结 |
| `KeywordTableIndex` | 关键词 → Node 映射表 | 关键词精确匹配 | 关键词检索 |
| `TreeIndex` | 树形层级 | 自顶向下遍历 | 大文档层级摘要 |
| `KnowledgeGraphIndex` | 知识图谱（三元组） | 关系遍历推理 | 需要关系推理的场景 |
| `DocumentSummaryIndex` | 文档级摘要 | 先检索文档摘要再查 | 超长文档、多文档问答 |

> 绝大多数实际项目只用到 `VectorStoreIndex`。其余类型在特定需求（如关键词命中、关系推理）下才需要。索引类型的选择决策表见 Code/README.md。

### 三、VectorStoreIndex（重点）

**向量索引**是所有索引中最通用、最推荐的选择。其原理是：

1. **建索引时**：用 `embed_model` 把每个 Node 的文本向量化，得到一个 `node_id → vector` 的映射，存进底部向量存储；
2. **检索时**：把查询也向量化，在向量存储中做相似度（余弦/内积）计算，返回最相似的 Top-N 节点。

创建方式：

```python
from llama_index.core import VectorStoreIndex

# 方式一：从 Documents 构建（内部先解析成 Node 再向量化）
index = VectorStoreIndex.from_documents(docs)

# 方式二：从已有 Nodes 构建（适合你已经手动解析好了 Node）
index = VectorStoreIndex.from_nodes(nodes)
```

构建向量索引必须有一个**嵌入模型 `embed_model`**（本例通过 `Settings.embed_model` 全局配置）:

```python
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
```

> **注意版本差异**：早期版本用 `ServiceContext.from_defaults(embed_model=...)` 注入 embedding；新版本已统一改为全局 `Settings`。`VectorStoreIndex.from_documents(..., embed_model=...)` 仍可局部覆盖，但推荐用 `Settings` 统一管理。

### 四、StorageContext 存储上下文

`StorageContext` 是 LlamaIndex 用来**管理「索引数据存在哪里」**的对象。它内部聚合了几个存储：

| 存储 | 作用 |
|------|------|
| `docstore` | 存放 Document 与 Node（文本与元数据） |
| `vector_store` | 存放向量与相似度检索所需索引 |
| `image_store` / `index_store` | 图片 / 索引级元信息 |

默认情况下，所有存储都在**内存**中：

```python
from llama_index.core import StorageContext
sc = StorageContext.from_defaults()   # 全部默认内存存储，程序退出即消失
```

若要持久化，需要**配置底部向量存储**并把 `storage_context` 传给索引构建：

```python
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("dataiq")
vector_store = ChromaVectorStore(chroma_collection=collection)

storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)
```

### 五、向量存储 VectorStore

向量存储负责把「向量 + 相似度检索」落地。LlamaIndex 内置与支持多种：

| 向量存储 | 位置 | 特性 | 适用 |
|---------|------|------|------|
| `SimpleVectorStore` | 内存（默认） | 简单、无需外部服务 | 原型、教学 |
| `ChromaVectorStore` | 本地 Chroma | 本地持久化、API 友好 | 中小型本地应用 |
| `FaissVectorStore` | 本地 FAISS | 高性能近似最近邻（ANN） | 大规模向量检索 |
| `MilvusVectorStore` | 独立服务 | 分布式、海量 | 生产级 |
| `PineconeVectorStore` | 云托管 | 托管、免运维 | 生产级 |

**选择依据**：数据量（内存能否放下）、是否需要持久化（重启后保留）、并发/分布式（单机 or 服务）。

> `SimpleVectorStore` 虽在内存，但配合索引持久化（`persist`）也能把向量写到磁盘，适合教学与中小场景。生产大规模场景建议直接用 Chroma / FAISS / Milvus / Pinecone。

### 六、持久化

LlamaIndex 通过 `storage_context.persist()` 把整个索引（docstore + vector_store + index_store）写到磁盘目录，之后再从目录**重新加载**。

```python
import os
from llama_index.core import StorageContext, load_index_from_storage

PERSIST_DIR = "./storage"

# 保存
storage_context = index.storage_context
storage_context.persist(persist_dir=PERSIST_DIR)

# 重新加载
storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
index = load_index_from_storage(storage_context)
```

加载完成后，即可照常重建 QueryEngine / Retriever：

```python
query_engine = index.as_query_engine()
```

> **注意版本差异**：新版本推荐用 `load_index_from_storage(storage_context)`；更旧的 API 是 `index.load_from_disk(persist_dir)`，现已废弃。

### 七、文档增量更新

索引构建好之后，不可能每次都全量重建。LlamaIndex 提供增量 API：

```python
# 1. 增量加入新文档（追加，不改变已有）
index.insert(new_doc)

# 2. 依据 metadata 刷新（doc_id 相同的旧版会被替换，返回被更新的 doc_id 列表）
refreshed_docs = index.refresh(refreshed_doc)

# 3. 删除某来源文档（ref_doc_id 关联的所有 Node 被移除）
index.delete_ref_doc(doc_id, delete_from_docstore=True)
```

| 方法 | 行为 | 适用 |
|------|------|------|
| `insert(doc)` | 追加新文档，不触碰已有 | 新增文件入库 |
| `refresh(doc)` | 按 `doc_id` 检测版本次更新替换 | 文档更新覆盖 |
| `delete_ref_doc(doc_id)` | 删除该来源的全部相关 Node | 删除文件 |

> `insert` / `refresh` 对内存型 `SimpleVectorStore` 生效；对接外部向量库时，取决于该库是否支持增量写入与删除（Chroma、FAISS 均支持）。

### 八、embedding 配置

嵌入模型决定语义检索的「语义」好坏与成本：

- `OpenAIEmbedding`（在线，效果佳，按 token 计费）
- `HuggingFaceEmbedding`（本地，无成本，需下载模型）
- `SentenceTransformerEmbedding`（本地 sentence-transformers）

统一通过 `Settings.embed_model` 配置：

```python
from llama_index.core import Settings

# 在线
from llama_index.embeddings.openai import OpenAIEmbedding
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# 本地（需 pip install llama-index-embeddings-huggingface）
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5")
```

> **无 Key 降级方案**：本系列代码在没有 API Key 时，内置了一个 `HashEmbedding`（基于文本哈希生成固定维向量）作为 embed_model 降级，保证流程可离线跑通，但语义效果仅用于演示。生产中务必替换为真实验嵌入模型。

### 九、检索与查询衔接

索引本身不做问答，它向下游提供出口：

```
index.as_retriever()  →  Retriever（检索 Node）        →  Day06
index.as_query_engine() →  QueryEngine（问答）          →  Day07
```

它们的关系可以概括为：

```
用户问题
   │
   ▼
QueryEngine（Day07）
   ├── Retriever（Day06）   ← 从 index 取相关 Node
   ├── NodePostprocessor     ← 可选后处理过滤
   └── ResponseSynthesizer   ← 合成回答（Day08）
   │
   ▼
回答 + 来源节点
```

---

## 代码文件说明

本章代码位于 `Code/` 目录：

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_vector_index.py` | 向量索引完整构建（from_documents / from_nodes / embedding 配置 / 检索验证） | DataIQ 基础索引搭建 |
| `02_storage_context.py` | StorageContext 配置、persist 保存、从目录重新加载并验证 | 索引持久化与恢复 |
| `03_vector_stores.py` | 多种向量存储对比（内存 Simple / 本地 Chroma） | 切换底层向量库 |
| `README.md` | 索引与向量存储指南（Index 类型决策表 / 持久化 / 增量更新 / embedding） | 参考文档 |

> 运行顺序建议：`01 → 02 → 03 → 04`。均为独立脚本，可直接 `python 文件.py` 运行。请先 `pip install llama-index llama-index-embeddings-openai llama-index-vector-stores-chroma python-dotenv`。

---

## 关键知识点总结

### Index 类型对比表

| 类型 | 结构 | 优点 | 缺点 | 适用 |
|------|------|------|------|------|
| `VectorStoreIndex` | 向量 | 语义检索、通用 | 需 embedding、成本 | 通用问答（首选） |
| `SummaryIndex` | 顺序 | 覆盖全部内容 | 大文档费 token | 全文总结 |
| `KeywordTableIndex` | 关键词映射 | 精确命中快速 | 无语义理解 | 关键词查询 |
| `TreeIndex` | 树形 | 层级摘要 | 复杂 | 大文档层级 |
| `KnowledgeGraphIndex` | 知识图谱 | 关系推理 | 构建成本高 | 关系问答 |
| `DocumentSummaryIndex` | 文档摘要 | 超长文档高效 | 摘要可能丢细节 | 多文档 |

### VectorStoreIndex 创建流程

```
加载文档(docs) ──► (可选 NodeParser 切分 Node) ──► embed_model 向量化 ──► VectorStore 存储 ──► Index
        │                                                        │
        └──── from_documents(docs)                                └── from_nodes(nodes)
```

### VectorStore 对比表

| 存储 | 是否持久化 | 是否外部依赖 | 规模 | 生产可用 |
|------|-----------|-------------|------|---------|
| `SimpleVectorStore` | 否（随 persist 可暂存） | 无 | 小 | 教学 |
| `ChromaVectorStore` | 是 | Chroma（本地库） | 中 | 是 |
| `FaissVectorStore` | 是（存盘） | FAISS | 大 | 是 |
| `MilvusVectorStore` | 是 | Milvus 服务 | 海量 | 是 |
| `PineconeVectorStore` | 是 | 云服务 | 海量 | 是 |

### 持久化步骤

1. `storage_context = index.storage_context`
2. `storage_context.persist(persist_dir=PERSIST_DIR)`
3. 加载：`sc2 = StorageContext.from_defaults(persist_dir=PERSIST_DIR)`
4. `index = load_index_from_storage(sc2)`
5. 重建 `query_engine = index.as_query_engine()`

### 增量更新 API

| API | 作用 | 说明 |
|-----|------|------|
| `index.insert(doc)` | 追加 | 不影响已有 |
| `index.refresh(doc)` | 按 doc_id 更新替换 | 返回被更新的 id |
| `index.delete_ref_doc(doc_id)` | 删除整篇 | 删除该源全部节点 |

---

## 实战练习

1. **搭建 DataIQ 基础索引**：用 3-5 条自制企业政策文本（如《远程办公政策》《出差报销制度》《年假制度》），用 `VectorStoreIndex.from_documents()` 构建索引，`as_retriever()` 检索「年假有几天」，观察命中的节点与分数。
2. **实现索引持久化 + 恢复**：把上题索引 `persist` 到 `./storage_dataiq`，写第二个脚本用 `load_index_from_storage` 重新加载，用 `as_query_engine()` 问同一个问题，验证恢复后能力不变。
3. **索引增量更新**：构建索引后，依次体验 `insert`（新增《加班制度》）、`refresh`（更新某篇，返回被更新的 doc_id）、`delete_ref_doc`（删除某篇），每次操作后检索验证索引确实反映了最新数据。
4. **进阶（可选）**：切换到 Chroma 作为底部向量存储，观察持久化目录、验证重启加载，并比较 `SimpleVectorStore` 与 `Chroma` 的使用差异（API 层几乎无感，仅创建方式不同）。

> **检查点**：能否不看文档独立完成「建索引 → 持久化 → 加载 → 检索」闭环？能否说清 `docstore`、`vector_store`、`index_store` 各自存什么？