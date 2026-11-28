# Day05 代码 - 索引与向量存储指南

> 运行本章代码前，请先安装依赖：
> ```
> pip install llama-index llama-index-embeddings-openai python-dotenv
> pip install llama-index-vector-stores-chroma chromadb   # 03 号脚本用到
> ```

## 各文件说明

| 文件 | 说明 | 关键 API |
|------|------|---------|
| `01_vector_index.py` | 向量索引构建（from_documents / from_nodes） | `VectorStoreIndex.from_documents` / `.from_nodes` / `Settings.embed_model` |
| `02_storage_context.py` | StorageContext + persist + 重新加载 | `storage_context.persist` / `StorageContext.from_defaults(persist_dir=...)` / `load_index_from_storage` |
| `03_vector_stores.py` | 多种向量存储切换 | `SimpleVectorStore` / `ChromaVectorStore` |
| `04_index_update.py` | 增量更新 | `index.insert` / `index.refresh` / `index.delete_ref_doc` |

## 运行与数据目录

- `02`/`04` 会分别在 `./storage_dataiq`、`./storage_update` 生成持久化数据；
- `03` 会在 `./chroma_db` 生成 Chroma 本地库。再次运行会清理同名集合并重建（幂等）。

## 无 Key 降级说明

所有脚本在未检测到 `OPENAI_API_KEY` 时，用内置 `HashEmbedding`（文本哈希 → 固定维向量）代替真实嵌入模型，确保离线可运行。生产环境请替换为：

```python
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
```

---

## Index 类型选择决策表

| 需求 | 推荐索引 |
|------|---------|
| 通用语义检索 / 问答 | `VectorStoreIndex` ✅ |
| 全文/整体总结 | `SummaryIndex` |
| 精确关键词命中 | `KeywordTableIndex` |
| 超长文档层级摘要 | `TreeIndex` |
| 关系推理（三元组） | `KnowledgeGraphIndex` |
| 海量多文档检索 | `DocumentSummaryIndex`（先摘要后检索） |

> **95% 的场景用 `VectorStoreIndex` 就够了**，除非业务明确需要关键词或图谱能力。

## VectorStoreIndex 完整教程

```python
from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

index = VectorStoreIndex.from_documents(docs)          # 语义索引
retriever = index.as_retriever(similarity_top_k=3)     # → 检索（Day06）
query_engine = index.as_query_engine()                 # → 问答（Day07）
```

**持久化最佳实践**：
```python
index.storage_context.persist(persist_dir="./storage")                     # 保存
from llama_index.core import StorageContext, load_index_from_storage
sc = StorageContext.from_defaults(persist_dir="./storage")                 # 加载
index = load_index_from_storage(sc)
```
- 每次业务改动（增删改）后及时 persist；
- 将 persist_dir 作为配置项管理，便于多环境复用；
- 大文档建议先持久化 node 再复用，避免重复 embedding 成本。

## 向量存储选择对比

| 存储 | 持久化 | 外部依赖 | 规模 | 推荐场景 |
|------|--------|---------|------|---------|
| `SimpleVectorStore` | 随 persist 暂存 | 无 | 小 | 教学/原型（默认） |
| `ChromaVectorStore` | 是 | chromadb | 中 | 本地生产 |
| `FaissVectorStore` | 是 | faiss-cpu | 大 | 高性能检索 |
| `MilvusVectorStore` | 是 | Milvus 服务 | 海量 | 企业生产 |
| `PineconeVectorStore` | 是 | 云服务 | 海量 | 云托管 |

## 增量更新策略

- 新增文件 → `index.insert(doc)`；
- 覆盖更新 → 构造相同 `doc_id` 的 Document 后 `index.refresh(doc)`，返回被更新的 doc_id 列表；
- 删除文件 → `index.delete_ref_doc(doc_id)`，可删同源全部 Node；
- 每次变更后执行 `persist` 确保持久化。

## embedding 配置建议

- 在线 `OpenAIEmbedding`：效果好、按 Token 计费，适合大多数场景；
- 本地 `HuggingFaceEmbedding("BAAI/bge-small-zh-v1.5")`：零成本、离线、中文友好；
- **维度一致性**：切换 embed_model 时，已持久化的向量维度不匹配会导致检索异常，需重建索引；
- 中文场景优先选用对中文友好的嵌入模型或与业务语料贴近的模型。

> **版本提示**：旧版用 `ServiceContext.from_defaults(embed_model=...)`，新版统一使用全局 `Settings.embed_model`。代码均基于新版写法，兼容 `pip install llama-index`（当前稳定版）。