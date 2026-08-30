# Day08 Code - Retrievers 检索器基础代码示例

本目录包含 Day08「Retrievers 检索器基础」的全部可运行 Python 代码，演示从向量存储到检索链集成的完整流程，这是 RAG（检索增强生成）的基础模式。

## 文件说明

| 文件 | 内容 | 核心知识点 |
|------|------|-----------|
| `01_vector_store.py` | 向量存储创建与搜索 | Chroma / FAISS 创建、from_documents、similarity_search、带分数搜索、VectorStoreManager |
| `02_retrievers.py` | 多种 Retriever 对比 | as_retriever、similarity vs mmr、MultiQueryRetriever、ContextualCompressionRetriever、RetrieverComparator |
| `03_mmr_search.py` | MMR 搜索实现 | MMR 原理、lambda_mult 调优、fetch_k 影响、similarity vs mmr 对比 |
| `04_retrieval_chain.py` | 检索器与 Chain 集成 | RunnablePassthrough 传查询、检索注入 Prompt、RAG 基础模式、RetrievalQAChain |

## 运行方式

```bash
# 安装依赖
pip install langchain langchain-openai langchain-community python-dotenv pydantic
pip install chromadb faiss-cpu  # 向量库

# 配置 .env（需 OpenAI API Key，用于 Embedding 和 Model）
# OPENAI_API_KEY=sk-xxxxxxxx
# OPENAI_MODEL=gpt-4o-mini
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small

cd "Day08 - Retrievers检索器基础/Code"
python 01_vector_store.py
python 02_retrievers.py
python 03_mmr_search.py
python 04_retrieval_chain.py
```

> 示例文档数据内置在代码中（无需额外文件）。运行会调用 OpenAI Embedding 和 Chat API，产生少量费用。

## VectorStore 选择决策表

| VectorStore | 部署方式 | 性能 | 适用场景 | 安装 |
|-------------|---------|------|---------|------|
| Chroma | 本地 | 中 | 开发测试、小规模 | `pip install chromadb` |
| FAISS | 本地 | 高 | 高性能本地搜索 | `pip install faiss-cpu` |
| Pinecone | 云端 | 高 | 生产、大规模 | `pip install pinecone-client` |
| Milvus | 自托管 | 高 | 生产、可扩展 | `pip install pymilvus` |

**选择建议**：
- 开发阶段：Chroma（轻量、易调试）
- 本地高性能：FAISS
- 生产环境：Pinecone / Milvus

## Retriever 类型对比表

| Retriever | 原理 | 优点 | 适用场景 |
|-----------|------|------|---------|
| VectorStoreRetriever (similarity) | 纯相似度 | 简单直接 | 精确匹配、默认选择 |
| VectorStoreRetriever (mmr) | 相似度+多样性 | 去重、覆盖广 | 避免冗余、概览问题 |
| MultiQueryRetriever | 多查询合并 | 召回高 | 提高检索覆盖率 |
| ContextualCompressionRetriever | 检索后压缩 | 聚焦相关 | 长文档、噪声多 |

## 检索参数调优建议

| 参数 | 作用 | 推荐值 | 说明 |
|------|------|--------|------|
| `k` | 返回数量 | 3-5 | 问答场景通常 3-4 |
| `fetch_k` | MMR 候选池 | k 的 3-5 倍 | 影响多样性空间 |
| `lambda_mult` | MMR 多样性系数 | 0.5 | 平衡相关性与多样性 |
| `score_threshold` | 相关性阈值 | 0.5-0.8 | 仅 score_threshold 类型 |

### lambda_mult 调优指南

- `lambda_mult=1.0`：纯相似度（无多样性）
- `lambda_mult=0.5`：平衡（默认推荐）
- `lambda_mult=0.0`：纯多样性（可能偏离查询）

## 检索链集成模式说明

### RAG 基础模式（核心）

```python
from langchain_core.runnables import RunnablePassthrough

chain = (
    {
        "context": retriever,             # 检索相关文档
        "question": RunnablePassthrough() # 原样传递问题
    }
    | prompt    # 填充上下文和问题
    | model     # 生成回答
    | parser    # 解析输出
)

result = chain.invoke("用户问题")
```

### 数据流

```
用户问题
    │
    ▼
┌───────────────────────────────┐
│ RunnableParallel              │
│   context = retriever(问题)   │ ← 检索相关文档
│   question = 问题（原样）     │ ← 保留原始问题
└───────────────────────────────┘
    │
    ▼ {context: [...], question: "..."}
┌───────────────────────────────┐
│ Prompt 模板填充               │
└───────────────────────────────┘
    │
    ▼
┌───────────────────────────────┐
│ Model 生成回答                │
└───────────────────────────────┘
    │
    ▼
┌───────────────────────────────┐
│ Parser 解析为字符串           │
└───────────────────────────────┘
```

### 检索结果格式化

```python
from langchain_core.runnables import RunnableLambda

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

chain = (
    {
        "context": retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough(),
    }
    | prompt | model | parser
)
```

## 与后续 RAG 板块的衔接说明

本天覆盖的内容（RAG 入门）：
- 文档到向量库流程（Load → Split → Embed → Store）
- similarity 与 MMR 搜索
- 基础检索链集成模式

后续 RAG 独立板块将深入：
- 检索质量评估与优化（Top-K 准确率、召回率）
- 混合检索（关键词 + 语义）
- 重排序（Re-ranking with Cross-Encoder）
- RAG 系统架构设计（多级检索、缓存）
- 端到端评估与调优
- 生产级 RAG 部署
