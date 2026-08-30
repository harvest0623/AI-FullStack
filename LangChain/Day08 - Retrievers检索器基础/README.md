# Day08 - Retrievers 检索器基础

当用户问"LangChain 的 Memory 有哪几种策略"时，ChainQA 怎么知道答案？它需要先从你提供的文档库中"找出"与问题相关的内容，再交给 LLM 组织回答。这个"找出相关内容"的组件就是 Retriever（检索器）。与传统关键词搜索不同，Retriever 基于**语义相似度**——它理解"记忆策略"和"Memory 策略"说的是同一件事。本章聚焦 LangChain 框架层面的 Retriever 用法：从把文档转化为向量存入 VectorStore，到用相似度/MMR 等策略检索，再到用 LCEL 把检索结果注入问答链。这是 RAG（检索增强生成）的基础模式，深入的 RAG 系统设计将在后续独立板块展开。

---

## 学习目标

- 理解 Retriever 的定义与在 LangChain 中的角色
- 掌握从文档到向量存储的完整流程（Load → Split → Embed → Store）
- 会用 Chroma / FAISS 创建向量库并进行相似度搜索
- 理解 similarity 与 MMR 两种搜索策略的区别
- 了解 MultiQueryRetriever 和 ContextualCompressionRetriever
- 掌握检索器与 LCEL 链的集成模式（RAG 基础）

> **范围说明**：本章只讲 LangChain 框架层面的 Retriever 基础用法，不深入 RAG 系统设计（评估、优化、混合检索等），这些内容在后续 RAG 独立板块深入。

---

## 理论知识讲解

### 1. Retriever 概念

#### 1.1 定义

Retriever（检索器）的核心职责：**给定一个查询，返回最相关的文档列表**。

```python
# 检索器接口
documents = retriever.invoke("什么是 LangChain？")
# 返回 List[Document]，按相关性排序
```

#### 1.2 与搜索引擎的区别

| 维度 | 传统搜索引擎 | LangChain Retriever |
|------|------------|-------------------|
| 匹配方式 | 关键词匹配 | 语义相似度 |
| 理解能力 | 字面匹配 | 理解同义词、近义词 |
| 示例 | "Memory 策略"搜不到"记忆管理" | "Memory 策略"能匹配"记忆管理" |

#### 1.3 在 LangChain 中的角色

Retriever 为 Chain 提供**上下文**：把检索到的文档作为背景知识，注入 Prompt 供 LLM 参考。

```
用户问题 → [Retriever] → 相关文档 → [Prompt + 文档] → [Model] → 回答
```

### 2. VectorStore 向量存储

#### 2.1 概念

VectorStore（向量存储）将文档用 Embedding 模型编码为向量后存储，支持基于向量相似度的搜索。

```
文档 → Embedding 模型 → 向量 → 存入 VectorStore
查询 → Embedding 模型 → 向量 → 与库中向量比对 → 返回最相似的文档
```

#### 2.2 常用 VectorStore

| VectorStore | 特点 | 安装 |
|-------------|------|------|
| Chroma | 轻量级本地向量库，开发首选 | `pip install chromadb` |
| FAISS | Facebook 高性能相似度搜索 | `pip install faiss-cpu` |
| Pinecone | 云端向量数据库，生产可用 | `pip install pinecone-client` |
| Milvus | 开源高性能向量库 | `pip install pymilvus` |

### 3. 从文档到向量存储的流程（重点）

```
Step 1: Load   — 加载文档
Step 2: Split  — 分割文档
Step 3: Embed  — 用 Embedding 模型编码
Step 4: Store  — 存入 VectorStore
```

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Step 1: Load
docs = TextLoader("doc.txt", encoding="utf-8").load()

# Step 2: Split
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# Step 3 & 4: Embed + Store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(chunks, embedding=embeddings)

# 搜索
results = vectorstore.similarity_search("什么是 LangChain？", k=3)
```

### 4. Embedding 模型配置

Embedding 模型把文本转为向量，是语义检索的基础。

```python
# OpenAI Embedding（付费，质量高）
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# HuggingFace Embedding（本地免费）
from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh")
```

| Embedding 模型 | 维度 | 质量 | 成本 | 语言 |
|---------------|------|------|------|------|
| text-embedding-3-small | 1536 | 中 | 低 | 多语言 |
| text-embedding-3-large | 3072 | 高 | 中 | 多语言 |
| BAAI/bge-large-zh | 1024 | 高 | 免费 | 中文优 |

### 5. VectorStoreRetriever

任何 VectorStore 都可以用 `.as_retriever()` 转为 Retriever。

```python
retriever = vectorstore.as_retriever(
    search_type="similarity",  # 搜索类型
    search_kwargs={"k": 4},    # 搜索参数
)
results = retriever.invoke("查询内容")
```

#### 5.1 search_type 参数

| search_type | 说明 | 适用场景 |
|-------------|------|---------|
| `"similarity"` | 纯相似度搜索 | 默认，通用 |
| `"mmr"` | 最大边际相关性（去重+多样性） | 避免结果重复 |
| `"similarity_score_threshold"` | 带阈值过滤 | 只要高相关性结果 |

#### 5.2 search_kwargs 参数

| 参数 | 作用 |
|------|------|
| `k` | 返回文档数量（默认 4） |
| `fetch_k` | MMR 初始候选数（默认 20） |
| `lambda_mult` | MMR 多样性系数（0-1，默认 0.5） |
| `score_threshold` | 相关性阈值（仅 score_threshold 类型） |

### 6. 相似度搜索 vs MMR 搜索

#### 6.1 相似度搜索

返回与查询向量**最相似**的 K 个文档。

```
查询 → 与所有文档算相似度 → 取 Top-K
```

特点：结果可能高度重复（多块内容相似）。

#### 6.2 MMR（Maximal Marginal Relevance）

在相似度和多样性之间平衡：既要相关，又要不重复。

```
1. 先取 fetch_k 个最相似候选
2. 依次选入结果：每步选「与查询相关」且「与已选结果差异大」的文档
3. 直到选满 k 个
```

| 搜索方式 | 结果特点 | 适合场景 |
|---------|---------|---------|
| similarity | 最相关，可能重复 | 精确匹配 |
| mmr | 相关且多样 | 概览性问题、避免冗余 |

### 7. MultiQueryRetriever 多查询检索

自动用 LLM 生成多个查询变体，合并多个查询的检索结果，提高覆盖率。

```python
from langchain.retrievers.multi_query import MultiQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(),
    llm=model,
)
```

适用场景：单个查询可能遗漏相关文档，多查询能扩大召回。

### 8. ContextualCompressionRetriever 上下文压缩检索

检索后压缩/提取相关片段，减少噪声，聚焦相关内容。

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(model)
compression_retriever = ContextualCompressionRetriever(
    base_retriever=vectorstore.as_retriever(),
    base_compressor=compressor,
)
```

适用场景：文档很长，只有一小部分与问题相关，需提取精华。

### 9. 检索器与 Chain 的集成（重点）

这是 **RAG 的基础模式**：用 `RunnablePassthrough` 传递查询同时检索，把检索结果注入 Prompt。

```python
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template(
    "根据以下上下文回答问题。\n上下文：{context}\n问题：{question}\n回答："
)

chain = (
    {
        "context": retriever,             # 检索结果
        "question": RunnablePassthrough() # 原始问题
    }
    | prompt
    | model
    | parser
)

result = chain.invoke("什么是 LangChain 的 Memory？")
```

**数据流**：

1. 输入字符串 `"什么是 LangChain 的 Memory？"`
2. 并行：`retriever` 检索相关文档作为 `context`，`RunnablePassthrough()` 原样传递问题作为 `question`
3. 两路结果合并为 `{"context": [...], "question": "..."}`
4. 传入 Prompt 模板填充
5. 调用 Model 生成回答
6. Parser 解析为字符串

> 这就是 RAG 的基础模式。完整的 RAG 系统设计（评估、混合检索、重排序等）在后续 RAG 独立板块深入。

### 10. 检索质量评估

| 指标 | 说明 |
|------|------|
| Top-K 准确率 | 前 K 个结果中包含正确答案的比例 |
| 相关性 | 返回文档与查询的相关程度 |
| 召回率 | 所有相关文档中被检索出的比例 |
| 精确率 | 检索结果中相关文档的比例 |

---

## 代码文件说明

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_vector_store.py` | 向量存储创建与搜索 | Chroma/FAISS 创建、from_documents、similarity_search |
| `02_retrievers.py` | 多种 Retriever 对比 | VectorStoreRetriever、similarity vs mmr、MultiQuery、Compression |
| `03_mmr_search.py` | MMR 搜索实现 | MMR 原理演示、lambda_mult 调优、similarity vs mmr 对比 |
| `04_retrieval_chain.py` | 检索器与 Chain 集成 | RunnablePassthrough 传查询、检索注入 Prompt、完整问答链 |

运行方式：

```bash
cd "Day08 - Retrievers检索器基础/Code"
python 01_vector_store.py
```

> 示例会自动生成测试文档数据。运行需 OpenAI API Key（用于 Embedding 和 Model）。

---

## 关键知识点总结

### VectorStore 对比表

| VectorStore | 部署 | 性能 | 适用场景 |
|-------------|------|------|---------|
| Chroma | 本地 | 中 | 开发测试、小规模 |
| FAISS | 本地 | 高 | 高性能本地搜索 |
| Pinecone | 云端 | 高 | 生产、大规模 |
| Milvus | 自托管 | 高 | 生产、可扩展 |

### Retriever 类型对比表

| Retriever | 原理 | 适用场景 |
|-----------|------|---------|
| VectorStoreRetriever (similarity) | 纯相似度 | 默认通用 |
| VectorStoreRetriever (mmr) | 相似度+多样性 | 避免重复 |
| MultiQueryRetriever | 多查询合并 | 提高召回 |
| ContextualCompressionRetriever | 检索后压缩 | 聚焦相关片段 |

### 检索参数速查

| 参数 | 作用 | 推荐值 |
|------|------|--------|
| `k` | 返回数量 | 3-5 |
| `fetch_k` | MMR 候选数 | 20 |
| `lambda_mult` | MMR 多样性 | 0.5（平衡） |
| `score_threshold` | 相关性阈值 | 0.5-0.8 |

### 检索链集成模式速查

```python
# RAG 基础模式
chain = (
    {
        "context": retriever,
        "question": RunnablePassthrough()
    }
    | prompt
    | model
    | parser
)
```

---

## 实战练习

### 练习 1：构建自己的知识库检索

- 准备 3-5 段关于不同主题的文本（如 Python、LangChain、数据库）
- 用 RecursiveCharacterTextSplitter 分割
- 存入 Chroma 向量库
- 用 5 个查询测试检索效果

### 练习 2：对比 similarity 和 mmr 搜索

- 构造一个包含若干相似内容的文档库
- 分别用 similarity 和 mmr 检索同一查询
- 对比结果差异，体会 MMR 的去重效果
- 调整 `lambda_mult` 参数观察多样性变化

### 练习 3：构建 ChainQA 检索问答链

- 准备一份 LangChain 文档作为知识库
- 构建检索链：查询 → 检索 → 注入 Prompt → 生成回答
- 测试 3 个问题，检查回答是否基于检索到的上下文
- 尝试不提供知识库的问题，观察模型行为

---

## 与后续 RAG 板块的衔接说明

本章是 RAG（检索增强生成）的入门。本章你掌握了：

- 文档到向量库的流程（Load → Split → Embed → Store）
- 基本的检索链集成模式

后续 RAG 独立板块将深入：

- 检索质量评估与优化
- 混合检索（关键词 + 语义）
- 重排序（Re-ranking）
- RAG 系统架构设计
- 端到端评估与调优

---

## 小结

Retriever 让 ChainQA 具备了"查阅资料再回答"的能力。从文档到向量库的四步流程（Load → Split → Embed → Store）是基础，similarity 与 MMR 是两种核心搜索策略，而 `RunnablePassthrough` + 检索器 + Prompt 的组合就是 RAG 的基础模式。本章只覆盖框架层面的基础用法，更深的 RAG 系统设计在后续独立板块展开。至此，ChainQA 已具备链式调用、记忆、文档处理、检索四大能力，下一章我们将让它学会"使用工具"。
