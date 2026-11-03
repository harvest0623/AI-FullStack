# RAG 学习指南

> 系统化掌握检索增强生成（Retrieval-Augmented Generation, RAG）架构，构建基于私有数据的高质量 LLM 应用

> 共 12 天，覆盖从 RAG 基础原理、完整管道、切块、嵌入、检索、重排序、查询优化、混合检索、知识库架构、质量评估到生产部署的完整知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [示例项目](#示例项目)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是全栈学习系列的 **RAG 架构核心**。前面你已经掌握了 `LLM`（模型能力）、`LangChain`/`LlamaIndex`（框架工具）。**RAG 则是一种架构模式**——它解决 LLM 的"时效性"与"私有知识"两大痛点：让模型在生成前先检索到相关的上下文，再基于这些上下文作答，从而显著减少幻觉、支持实时数据与私有数据问答。

**本板块与框架板块的关系**：RAG 是"蓝图"，LangChain / LlamaIndex 是"实现工具"。本板块聚焦 RAG 架构本身的**设计、流程、进阶模式与评估优化**，会结合 LangChain / LlamaIndex 给出可运行示例，但重点讲解 RAG 架构思想，而非某个框架的 API 细节（那是 LangChain / LlamaIndex 板块的内容）。

**与 Agent 板块的关系**：RAG 提供"检索上下文"能力，Agent 负责"规划与调用工具"。一个 Agent 可以调用 RAG 检索器作为工具。本板块聚焦 RAG 本身，Agent 编排放后续独立板块。

**学习目标**：完成本板块后，你应能：
- 理解 RAG 的核心思想与架构演进（朴素 → 高级 → 模块化）
- 独立实现一条完整的 RAG 管道（切块 → 嵌入 → 检索 → 生成）
- 针对不同类型数据选择与调优切块策略
- 正确选择嵌入模型与向量存储
- 设计并实现召回、精排、重排序、混合检索
- 掌握查询优化、查询路由、多文档知识库架构
- 用评估指标量化 RAG 质量并持续优化
- 搭建生产级 RAG 系统（含缓存、观测、部署）
- 完成一个企业级知识库问答综合项目

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 Python 代码 + 实战练习
- 全程围绕统一的**企业知识库问答系统 `DataIQ`** 项目展开
- 核心示例兼容 LangChain / LlamaIndex 两个框架，便于对照
- 紧扣 RAG 架构视角，为后续 Agent 板块铺垫

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| Python | 必须 | 类型注解、上下文管理器、异步 |
| LLM 基础 | 已完成 | 理解 ChatModel / Embedding / Token |
| Prompt 工程 | 已完成 | 理解检索 Prompt / 生成 Prompt |
| LangChain 或 LlamaIndex | 已完成更佳 | 提供 RAG 常用组件 |
| 向量检索基础 | 了解 | 余弦相似度、Top-K |

**环境准备**：
- Python 3.10+
- 任选一个框架：`pip install langchain` 或 `pip install llama-index`
- 向量库：`chromadb` / `faiss-cpu`
- 至少一个 LLM API Key（OpenAI / Anthropic / 国内模型）
- 本板块默认以 **LangChain** 为主示例，关键处给出 LlamaIndex 对应写法

---

## 学习路线图

```
┌────────────────────────────────────────────────────────────┐
│              RAG 学习路线（12天，架构视角）                  │
└────────────────────────────────────────────────────────────┘

阶段一：基础原理（Day01-Day02）
┌───────────────┬───────────────┐
│ Day01         │ Day02         │
│ RAG概述与      │ 基础RAG流程    │
│ 核心原理       │ (朴素RAG)      │
└───┬───────────┴───┬───────────┘
    │               │
    ▼               ▼
阶段二：核心构建（Day03-Day05）
┌───────────────┬───────────────┬───────────────┐
│ Day03         │ Day04         │ Day05         │
│ 文本切块       │ 嵌入与向量化    │ 向量存储与召回 │
└───┬───────────┴───┬───────────┴───┬───────────┘
    │               │               │
    ▼               ▼               ▼
阶段三：进阶优化（Day06-Day08）
┌───────────────┬───────────────┬───────────────┐
│ Day06         │ Day07         │ Day08         │
│ 重排序精排     │ 查询优化与路由  │ 混合检索融合   │
└───┬───────────┴───┬───────────┴───┬───────────┘
    │               │               │
    ▼               ▼               ▼
阶段四：架构与工程（Day09-Day12）
┌───────────┬───────────┬───────────┬───────────┐
│ Day09     │ Day10     │ Day11     │ Day12     │
│ 多文档知识库│ 质量评估   │ 生产级架构 │ 综合实战   │
└───────────┴───────────┴───────────┴───────────┘
```

---

## 示例项目

本板块全程围绕一个**企业知识库问答系统 `DataIQ`** 展开，逐步从"朴素 RAG"演进为"生产级模块化 RAG"，贯穿 12 天。

### 项目演进路径

| 阶段 | 使用的 Day | 形态 |
|------|-----------|------|
| 朴素 RAG | Day02 | 单文档 → 向量 → 生成 |
| 数据工程 RAG | Day03-05 | 多格式切块 + 嵌入 + 多向量库 |
| 检索优化 RAG | Day06-08 | 重排序 + 查询改写 + 混合检索 |
| 架构级 RAG | Day09-11 | 多库路由 + 评估 + 缓存 + 部署 |
| 生产整合 | Day12 | DataIQ 综合系统 |

### 项目结构（最终形态）

```
dataiq/
├── pyproject.toml
├── config.yaml                ← 配置（模型/切块/检索/存储）
├── data/                      ← 原始文档
├── ingest/                    ← 数据管道（切块/嵌入/入库）
├── retrieval/                 ← 检索（召回/重排/混合）
├── generation/                ← 生成（Prompt/合成）
├── evaluation/                ← 评估（指标/数据集）
├── api/                       ← FastAPI 服务
└── scripts/                   ← 运维脚本
```

> 各天的代码围绕这个项目逐步构建，从基础管道到生产部署完整演进。

---

## 每日内容详表

### 阶段一：基础原理

#### Day01 - RAG概述与核心原理
- **核心**：RAG 定义与动机、为什么需要 RAG（幻觉/时效/私有知识）、RAG 的核心架构（Retrieval + Generation）、与微调 Fine-tuning 对比、与长上下文对比、RAG 演进史（朴素 → 高级 → 模块化）、RAG 适用与不适用场景、常见问题与质量瓶颈
- **代码**：`01_rag_vs_ft.py`（RAG 与微调对比）/`02_rag_pipeline_preview.py`（RAG 全流程预览）/`03_failure_modes.py`（RAG 失败模式演示）/`README.md`
- **重点**：RAG 核心架构与动机、质量瓶颈初识

#### Day02 - 基础RAG流程(朴素RAG)
- **核心**：朴素 RAG 三步流程（Indexing 索引 / Retrieval 检索 / Generation 生成）、文档加载、切块、嵌入、入库、查询嵌入、相似度检索 Top-K、把检索结果注入 Prompt、生成回答、用 LangChain/LlamaIndex 两种实现对照、检索结果的来源引用、一步到位的最小可运行 RAG 系统
- **代码**：`01_naive_rag_langchain.py`（LangChain 朴素 RAG）/`02_naive_rag_llama.py`（LlamaIndex 朴素 RAG）/`03_retrieval_inspect.py`（查看检索上下文）/`README.md`
- **重点**：三步流程、Top-K 注入 Prompt 生成

---

### 阶段二：核心构建

#### Day03 - 文本切块Chunking策略
- **核心**：为什么切块很关键、切块对检索质量的影响、按固定大小切块、按句子/段落切块、递归字符切块 RecursiveCharacterTextSplitter、按 Token 切块、语义切块 SemanticSplitter、父子切块 Parent-Child、切块大小与重叠 chunk_size/chunk_overlap 调优、不同文档类型的切块策略（代码/表格/长文）、切块与元数据保留
- **代码**：`01_fixed_splitter.py`（固定大小切块）/`02_recursive_splitter.py`（递归切块）/`03_semantic_splitter.py`（语义切块）/`04_chunking_tune.py`（切块参数调优）/`README.md`
- **重点**：递归切块、语义切块、参数调优

#### Day04 - 嵌入Embedding与向量化
- **核心**：Embedding 原理（文本→向量）、嵌入模型选择（OpenAI text-embedding / Cohere / BGE / 多语言模型）、嵌入维度与成本、嵌入的相似度计算（余弦）、查询与文档嵌入的一致性、嵌入与切块的关系、批量嵌入、嵌入缓存、嵌入评估与对比、微调嵌入模型（进阶）
- **代码**：`01_embedding_basics.py`（嵌入基础与相似度）/`02_model_compare.py`（嵌入模型对比）/`03_batch_cache.py`（批处理与缓存）/`04_embedding_quality.py`（嵌入质量检验）/`README.md`
- **重点**：余弦相似度、模型选择、质量检验

#### Day05 - 向量存储与检索召回
- **核心**：向量数据库概念、主流向量库对比（Chroma / FAISS / Qdrant / Milvus / Weaviate / pgvector）、内存向量库 vs 专用向量库、元数据过滤 Metadata Filtering、Top-K 召回与相似度阈值、集合/集合划分（多知识库）、向量的增删改管理、Annoy/IVF/HNSW 索引算法概念、检索延迟与召回率权衡
- **代码**：`01_chroma_store.py`（Chroma 增删改查）/`02_faiss_store.py`（FAISS 构建检索）/`03_metadata_filter.py`（元数据过滤）/`04_index_metrics.py`（索引算法与召回）/`README.md`
- **重点**：向量库 CRUD、元数据过滤、Top-K

---

### 阶段三：进阶优化

#### Day06 - 重排序Reranking与精排
- **核心**：为什么需要重排、双阶段检索（粗召回 + 精排）、交叉编码器 CrossEncoder vs 双塔 Bi-Encoder、常用重排模型（Cohere Rerank / BGE-Reranker / bge-reranker-v2-m3）、重排对最终质量的影响、如何把重排嵌入 RAG 管道、重排的评价（MRR/nDCG）、重排阈值过滤、结合重排的多路融合
- **代码**：`01_rerank_concept.py`（重排概念演示）/`02_rerank_cohere.py`（Cohere 重排）/`03_cross_encoder.py`（本地交叉编码器）/`04_rerank_pipeline.py`（重排接入管道）/`README.md`
- **重点**：双阶段检索、交叉编码器、重排接入

#### Day07 - 查询优化与查询路由
- **核心**：查询质量对 RAG 的影响、查询改写 Query Rewriting、多查询 Multi-Query（多视角展开查询）、查询分解 Query Decomposition（复杂问题拆解）、HyDE（假设性文档嵌入）、历史对话压缩、查询路由 Query Routing（按意图分发到不同索引/工具）、LLM 路由 vs 相似度路由、查询优化的成本权衡
- **代码**：`01_query_rewrite.py`（查询改写）/`02_multi_query.py`（多查询检索）/`03_query_decompose.py`（查询分解）/`04_query_router.py`（查询路由）/`README.md`
- **重点**：多查询、查询分解、查询路由

#### Day08 - 混合检索与多路召回融合
- **核心**：为什么需要混合检索、稀疏检索 BM25 原理、稠密检索（向量）原理、混合检索组合（稀疏+稠密）、多路召回融合算法（加权 / RRF 倒数排名融合）、融合排序实现、玻尔兹曼 RRF、混合检索 vs 纯向量检索对比、在不同数据集下的取舍、如何在 LangChain/LlamaIndex 中实现混合检索
- **代码**：`01_bm25_retrieval.py`（BM25 稀疏检索）/`02_dense_retrieval.py`（稠密向量检索）/`03_hybrid_fusion.py`（混合融合 RRF）/`04_hybrid_compare.py`（混合 vs 单一对比）/`README.md`
- **重点**：BM25、RRF 融合、混合检索

---

### 阶段四：架构与工程

#### Day09 - 多文档与知识库架构设计
- **核心**：多文档 RAG 的挑战、文档索引策略（每文档一索引 vs 合并索引）、元数据路由（按文档类型分流）、分文档独立检索再合并、文档级摘要辅助检索、常用 Agentic RAG 模式（先摘要→再检索）、知识库分区与权限控制、表格式 / 结构化数据 RAG、多搜索工具 RAG Router、跨文档引用与冲突处理
- **代码**：`01_multi_index.py`（多索引隔离）/`02_meta_router.py`（元数据路由）/`03_summary_then_retrieve.py`（先摘要再检索）/`04_multi_tool_router.py`（多工具路由）/`README.md`
- **重点**：多索引、路由、摘要辅助检索

#### Day10 - RAG质量评估
- **核心**：为什么要评估 RAG、评估分层（检索层 / 生成层 / 端到端）、检索指标（召回率 Recall / 精确率 / MRR / nDCG）、生成指标（忠实性 Faithfulness / 相关性 Relevancy / 正确性）、上下文相关度 Context Relevance、RAGAS 框架（Faithfulness/Answer Relevance/Context Relevance）、手工评估数据集构建、自动评估 vs 人工评估、LangSmith/RAGAS/DeepEval 工具、评估驱动的优化闭环
- **代码**：`01_retrieval_metrics.py`（检索指标计算）/`02_generation_metrics.py`(生成指标)/`03_ragas_eval.py`（RAGAS 评估）/`04_eval_dataset.py`（构建评估数据集）/`README.md`
- **重点**：检索指标、RAGAS 三角指标、评估闭环

#### Day11 - 生产级RAG系统架构
- **核心**：生产 RAG 架构全景、索引管道与检索管道解耦、缓存策略（LLM 结果缓存 / 嵌入缓存）、异步与并发、增删改的数据同步（增量更新）、权限与数据安全（过滤/隔离）、观测与追踪（LangSmith / Langfuse / Phoenix）、错误处理与降级、监控指标（延迟/成本/召回）、成本优化、LLMOps 最佳实践
- **代码**：`01_arch_design.py`（生产架构骨架）/`02_cache_layer.py`（缓存层）/`03_observability.py`（可观测性配置）/`04_fastapi_rag.py`（FastAPI RAG 服务）/`README.md`
- **重点**：缓存、观测、FastAPI 封装

#### Day12 - 综合实战项目
- **核心**：综合运用全部所学，构建生产可用的 DataIQ 企业知识库问答系统、项目架构设计与按模块拆分、整合切块/嵌入/混合检索/重排/路由/评估、多用户的会话与权限、API 封装与数据管道分离、性能优化、上线运维指南、复盘与进阶方向（Agentic RAG / 图 RAG / 多模态 RAG）
- **代码**：`01_project_structure.py`（项目骨架）/`02_data_pipeline.py`（完整数据管道）/`03_retriever_engine.py`（检索与生成整合）/`04_full_service.py`（完整服务）/`README.md`
- **重点**：全链路整合、工程化落地、Agentic RAG 前瞻

---

## 目录结构

```
RAG/
├── README.md                          ← 本文件（板块总入口）
├── Day01 - RAG概述与核心原理/
│   ├── README.md
│   └── Code/
│       ├── 01_rag_vs_ft.py
│       ├── 02_rag_pipeline_preview.py
│       ├── 03_failure_modes.py
│       └── README.md
├── Day02 - 基础RAG流程(朴素RAG)/
│   ├── README.md
│   └── Code/
│       ├── 01_naive_rag_langchain.py
│       ├── 02_naive_rag_llama.py
│       ├── 03_retrieval_inspect.py
│       └── README.md
├── ...（Day03-Day11 同构）...
└── Day12 - 综合实战项目/
    ├── README.md
    └── Code/
        ├── 01_project_structure.py
        ├── 02_data_pipeline.py
        ├── 03_retriever_engine.py
        ├── 04_full_service.py
        └── README.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，均为 `.py` 文件（可直接 `python file.py` 运行）
- 部分天数含配置文件（`.yaml` / `.json` / `requirements.txt`）

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-6 小时 | 约 2-3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 4-5 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **理解架构思想**：RAG 是"检索 + 生成"的组合，先把握整体再抠细节
2. **动手搭管道**：从 Day02 的朴素 RAG 开始，亲手跑通最小系统
3. **对照两框架**：LangChain 与 LlamaIndex 实现相互对照，理解通用本质
4. **量化质量**：用评估指标代替"感觉"，让优化有据可依
5. **逐步演进项目**：跟随 12 天把 DataIQ 从朴素版演进到生产版
6. **高级模式接 Agent**：理解 Agentic RAG，为 Agent 板块衔接

### 阶段性检查点

- **阶段一完成后**：能否讲清"为什么需要 RAG，如何三步完成朴素 RAG"？
- **阶段二完成后**：能否针对数据类型选择切块与嵌入策略，并建好向量库？
- **阶段三完成后**：能否用重排、查询优化、混合检索显著提升召回质量？
- **阶段四完成后**：能否设计多文档架构、评估系统、部署生产并持续优化？

---

## 如何运行代码

### 环境准备

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 安装核心依赖（LangChain 路线）
pip install langchain langchain-community langchain-openai
pip install chromadb faiss-cpu pypdf

# 或 LlamaIndex 路线
pip install llama-index llama-index-vector-stores-chroma
```

### 配置 API Key

```bash
cat > .env << 'EOF'
OPENAI_API_KEY=sk-xxxxxxxx
EOF
```

### 运行示例

```bash
# 运行朴素 RAG
python "Day02 - 基础RAG流程(朴素RAG)/Code/01_naive_rag_langchain.py"

# 混合检索对比
python "Day08 - 混合检索与多路召回融合/Code/04_hybrid_compare.py"

# 启动综合服务
uvicorn "Day12 - 综合实战项目/Code/04_full_service:app" --reload --port 8000
```

---

## 知识点速查

### RAG 核心管道速查

| 阶段 | 动作 | 关键组件 | 对应天数 |
|------|------|---------|---------|
| Indexing | 切块 | TextSplitter / NodeParser | Day03 |
| Indexing | 嵌入 | Embedding Model | Day04 |
| Indexing | 入库 | Vector Store | Day05 |
| Retrieval | 召回 | Retriever / Vector Search | Day05 |
| Retrieval | 精排 | Reranker / CrossEncoder | Day06 |
| Retrieval | 优化 | 查询改写 / HyDE / 混合 | Day07/08 |
| Generation | 合成 | LLM + Prompt | Day02 |
| Evaluation | 评估 | RAGAS / Metrics | Day10 |

### RAG 演进速查

| 阶段 | 特点 | 不足之处 |
|------|------|---------|
| Naive RAG | 朴素切块+检索+生成 | 召回粗、质量不稳 |
| Advanced RAG | 重排/改写/混合检索 | 架构复杂 |
| Modular RAG | 可插拔模块化 | 依赖编排框架 |

### 检索指标速查

| 指标 | 含义 |
|------|------|
| Recall@K | 召回的相关文档比例 |
| Precision@K | 召回的准确率 |
| MRR | 首个正确结果的倒数排名 |
| nDCG | 考虑排序位置的加权质量 |

### RAGAS 指标速查

| 指标 | 评估对象 | 说明 |
|------|---------|------|
| Context Relevance | 检索上下文 | 上下文是否切题 |
| Answer Relevance | 生成回答 | 回答是否答非所问 |
| Faithfulness | 生成回答 | 回答是否忠实于上下文 |

### 检索技术速查

| 技术 | 类型 | 适用 |
|------|------|------|
| Dense（向量） | 稠密 | 语义相似检索 |
| Sparse（BM25） | 稀疏 | 关键词精确匹配 |
| Hybrid | 稠密+稀疏 | 综合最佳 |
| Reranking | 精排 | 提升 top-1 精度 |
| HyDE | 查询增强 | 查询-文档语义鸿沟 |

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **Agent** | Agent 将 RAG 检索器作为工具，实现更智能的编排 |
| **Fine-tuning** | 微调与 RAG 结合解决领域问题 |
| **Graph RAG** | 用图谱增强检索，处理实体关系 |
| **Multimodal RAG** | 图/表/音视频多模态 RAG |
| **LangChain** | RAG 在该框架下的 Deep Dive |
| **LlamaIndex** | RAG 在该框架下的 Deep Dive |
| **LLM** | 模型调用与 Embedding 基础 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [RAG 综述](https://arxiv.org/abs/2312.10997) - Retrieval-Augmented Generation for Large Language Models: A Survey
- [RAGAS](https://docs.ragas.io/) - 面向 RAG 的评估框架
- [LangChain RAG 文档](https://python.langchain.com/docs/tutorials/rag/) - LangChain RAG 教程
- [LlamaIndex RAG 文档](https://docs.llamaindex.ai/) - LlamaIndex 检索增强
- [Pinecone RAG 指南](https://www.pinecone.io/learn/) - RAG 学习中心
- [arXiv](https://arxiv.org/) - 检索 RAG 相关论文

---

## 贡献与反馈

本学习手册为原创内容，参考 GitHub 优质仓库的文档风格但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用 RAG 让 LLM 真正懂你的数据！**