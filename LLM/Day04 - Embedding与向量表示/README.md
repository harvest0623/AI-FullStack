# Day04 - Embedding 与向量表示

Embedding 是将文本转化为向量的技术——它让计算机「理解」语义。两段话意思相近，向量就相近；意思无关，向量就相远。这个简单而强大的能力，是语义搜索、推荐系统、聚类分类、RAG（检索增强生成）的共同基石。本章从 Embedding 概念出发，对比词嵌入与句嵌入，掌握 OpenAI Embedding API 与开源模型，深入相似度计算、语义搜索实现、向量降维可视化与质量评估，为你搭建一个完整 AISearch 智能问答服务的「检索层」打下基础。

## 学习目标

- 理解 Embedding 的定义与价值，区分它与关键词搜索
- 对比词嵌入（Word2Vec/GloVe）与句嵌入（Sentence-BERT）与 LLM Embedding
- 掌握 OpenAI Embedding API（text-embedding-3-small/large、dimensions 降维）
- 了解其他 Embedding 模型（Cohere / BGE / Jina / sentence-transformers）
- 理解向量维度与性能权衡、Matryoshka 降维
- 掌握三种相似度计算：余弦相似度、欧氏距离、点积
- 能实现语义搜索引擎（建索引→查询→Top-K）
- 掌握向量降维可视化（t-SNE / PCA / UMAP）与 Embedding 质量评估

---

## 一、Embedding 概念

### 定义

**Embedding（嵌入）** 是将文本映射为高维稠密向量（如 1536 维）的技术，使**语义相近的文本在向量空间中也相近**。

```
"猫喜欢吃鱼"   -> [0.12, -0.34, 0.56, ..., 0.78]   (1536维)
"小猫爱吃鱼肉" -> [0.11, -0.32, 0.55, ..., 0.77]   (相似，向量接近)
"今天天气真好" -> [0.91, 0.23, -0.45, ..., -0.12]  (不相关，向量相远)
```

### 为什么需要 Embedding

- 让计算机「理解」语义，而非只看字面
- 支持语义搜索（找意思相近的，而非字面匹配的）
- 支持聚类、分类、推荐、去重
- 是 RAG 的基础：把知识库向量化，按语义检索相关片段

### 与关键词搜索的区别

| 维度 | 关键词搜索（TF-IDF/BM25） | 语义搜索（Embedding） |
| --- | --- | --- |
| 匹配方式 | 字面匹配 | 语义匹配 |
| 同义词 | 找不到 | 能找到 |
| 错别字 | 受影响 | 较鲁棒 |
| 理解上下文 | 否 | 是 |
| 计算成本 | 低 | 高（需向量化） |
| 适用 | 精确关键词、法律条款 | 模糊语义、问答、推荐 |

> 实际系统常**混合**两者：BM25 召回 + Embedding 重排，效果更好。

---

## 二、词嵌入 vs 句嵌入

| 类型 | 代表模型 | 粒度 | 特点 |
| --- | --- | --- | --- |
| **词嵌入 Word Embedding** | Word2Vec / GloVe / FastText | 每个词一个向量 | 静态、不考虑上下文、词义多义无法区分 |
| **句嵌入 Sentence Embedding** | Sentence-BERT / SimCSE | 整句话一个向量 | 考虑上下文、适合检索 |
| **LLM Embedding** | OpenAI / BGE / Jina | 整句话一个向量 | 语义理解最强、效果好 |

**Word2Vec 的局限**：「苹果」在「吃苹果」和「苹果手机」中向量相同（静态），无法区分多义。现代 LLM Embedding 基于上下文，能区分。

---

## 三、OpenAI Embedding API

### 模型

| 模型 | 维度 | 价格 | 定位 |
| --- | --- | --- | --- |
| `text-embedding-3-small` | 1536 | $0.02/1M | 性价比首选 |
| `text-embedding-3-large` | 3072 | $0.13/1M | 精度最高 |
| `text-embedding-ada-002` | 1536 | $0.10/1M | 上一代 |

### dimensions 参数（Matryoshka 降维）

OpenAI 的新模型支持 `dimensions` 参数降维，如 1536→256，牺牲少量精度换取更低存储/计算成本：

```python
resp = client.embeddings.create(
    model="text-embedding-3-small",
    input="hello",
    dimensions=256,   # 从 1536 降到 256
)
```

### 调用方式

```python
from openai import OpenAI
client = OpenAI()
resp = client.embeddings.create(model="text-embedding-3-small", input="要编码的文本")
vector = resp.data[0].embedding   # 1536 维 list
```

批量编码：`input` 传字符串列表，返回 `data` 数组（注意按 `index` 排序）。

---

## 四、其他 Embedding 模型

| 模型 | 出品 | 特点 |
| --- | --- | --- |
| **Cohere embed-v3** | Cohere | 多语言、性能强 |
| **BGE 系列** | 智源 | `bge-large-zh` 中文最佳开源之一；`bge-m3` 多语言 |
| **Jina Embeddings v3** | Jina | 长文本支持好（8K） |
| **sentence-transformers** | 社区 | 本地部署库，含众多模型（MiniLM/bge 等），免费 |

### 本地 Embedding（sentence-transformers）

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
vecs = model.encode(["文本1", "文本2"])
```

> **选型建议**：中文场景优先 BGE；隐私/离线用 sentence-transformers；图省事用 OpenAI。

---

## 五、向量维度与性能权衡

| 维度 | 表达能力 | 存储/计算成本 | 适用 |
| --- | --- | --- | --- |
| 低（256-512） | 弱 | 低 | 海量数据、对延迟敏感 |
| 中（768-1536） | 中 | 中 | 通用平衡 |
| 高（3072+） | 强 | 高 | 追求精度 |

**降维技术**：**Matryoshka Representation**（OpenAI dimensions 参数原理）——训练时让向量的前缀也是有效表示，故可截断降维而不大幅掉点。

---

## 六、相似度计算

### 1. 余弦相似度（最常用）

```
cos(A, B) = A·B / (|A| × |B|)
```
- 范围 [-1, 1]，越接近 1 越相似
- 对向量长度不敏感，只看方向
- **语义搜索首选**

### 2. 欧氏距离

```
d(A, B) = ‖A - B‖
```
- 范围 [0, ∞)，越小越相似
- 关注绝对距离，受向量长度影响
- 适合几何聚类

### 3. 点积

```
dot(A, B) = A·B
```
- 简洁快速
- 受向量长度影响
- **归一化后点积 = 余弦相似度**（工程上常用归一化+点积加速）

### 何时用哪种

| 场景 | 推荐 |
| --- | --- |
| 语义相似度 | 余弦相似度 |
| 聚类（K-Means） | 欧氏距离 |
| 向量数据库加速 | 归一化后点积 |

---

## 七、语义搜索实践

### 流程

```
文档库 ──Embedding──> 文档向量矩阵 (索引)
                            │
查询 ──Embedding──> 查询向量 │
                            ▼
                  计算相似度 (余弦)
                            │
                            ▼
                      Top-K 最相似文档
                            │
                            ▼
              (进阶) 作为上下文交给 LLM 生成 → RAG
```

完整实现见 `Code/02_similarity_search.py` 的 `SemanticSearch` 类。

### 与关键词搜索（TF-IDF/BM25）对比

| 维度 | BM25 | 语义搜索 |
| --- | --- | --- |
| 原理 | 词频+逆文档频率 | 向量相似度 |
| 同义词 | ❌ | ✅ |
| 理解语义 | ❌ | ✅ |
| 精确匹配 | ✅ 强 | 一般 |
| 计算成本 | 低 | 高 |

> 实战常「BM25 召回 + Embedding 重排」混合，兼顾精确与语义。

---

## 八、向量可视化

把高维向量降到 2D/3D 才能画图观察聚类：

| 方法 | 类型 | 特点 |
| --- | --- | --- |
| **t-SNE** | 非线性 | 保留局部结构，可视化效果好，但慢 |
| **PCA** | 线性 | 保留方差最大的方向，快但效果一般 |
| **UMAP** | 非线性 | 兼顾局部与全局，速度比 t-SNE 快 |

> t-SNE 适合「看局部聚类」，PCA 适合「看主成分方差」，UMAP 综合最佳。可视化实现见 `Code/04_vector_visualization.py`。

---

## 九、Embedding 质量评估

| 评估方法 | 做法 | 指标 |
| --- | --- | --- |
| 相关性测试 | 构造相似/不相似文本对 | 相似度区分度 |
| 聚类测试 | 同类文本应聚簇 | 轮廓系数 |
| 检索质量 | 对已知答案查询 | Recall@K / MRR |
| 对比基线 | 与 BM25/其他模型对比 | 相对提升 |

---

## 十、多语言 Embedding

- **中英文跨语言对齐**：好的多语言 Embedding 使「猫」与「cat」向量也接近
- **模型选择**：`bge-m3`、Cohere embed-v3、OpenAI 3 系列均有不错多语言能力
- **注意**：不同语言 Token 效率不同（见 Day03），影响 Embedding 成本

---

## 关键知识点总结

### 1. Embedding 模型对比表

| 模型 | 维度 | 价格 | 中文 | 部署 |
| --- | --- | --- | --- | --- |
| text-embedding-3-small | 1536 | $0.02/1M | 好 | 云端 |
| text-embedding-3-large | 3072 | $0.13/1M | 好 | 云端 |
| bge-large-zh | 1024 | 免费 | 最佳 | 本地 |
| bge-m3 | 1024 | 免费 | 好(多语言) | 本地 |
| Cohere embed-v3 | 1024 | 付费 | 好 | 云端 |

### 2. 相似度计算公式速查

| 方法 | 公式 | 范围 |
| --- | --- | --- |
| 余弦 | `A·B/(|A||B|)` | [-1,1] |
| 欧氏 | `‖A-B‖` | [0,∞) |
| 点积 | `A·B` | (-∞,∞) |

### 3. Embedding 应用场景速查

| 场景 | 用法 |
| --- | --- |
| 语义搜索 | 文档+查询向量化→Top-K |
| RAG | 检索相关片段→喂给 LLM |
| 推荐 | 用户/物品向量相似 |
| 聚类 | 向量聚簇发现分组 |
| 去重 | 相似度高的判为重复 |

### 4. 向量降维方法对比

| 方法 | 类型 | 速度 | 效果 |
| --- | --- | --- | --- |
| PCA | 线性 | 快 | 一般 |
| t-SNE | 非线性 | 慢 | 局部好 |
| UMAP | 非线性 | 中 | 综合好 |

---

## 代码文件说明

| 文件 | 核心类/函数 | 内容 |
| --- | --- | --- |
| `Code/01_embedding_basics.py` | `EmbeddingClient` | 文本转向量、三种相似度、降维 |
| `Code/02_similarity_search.py` | `SemanticSearch` | 文档索引+Top-K 语义搜索+批量搜索 |
| `Code/03_embedding_comparison.py` | `compare_models` | OpenAI vs 本地模型多维对比 |
| `Code/04_vector_visualization.py` | `reduce_pca/reduce_tsne` | 高维降 2D/3D 可视化数据 |
| `Code/README.md` | - | 选型决策表、相似度对比、可视化工具、评估方法 |

> 所有脚本用 `python-dotenv` 加载 `.env`，用 `os.getenv("OPENAI_API_KEY")` 取密钥，**无硬编码**。

---

## 实战练习

### 练习 1：搭建个人知识库语义搜索

收集 20 条你领域的技术笔记/FAQ，用 `02_similarity_search.py` 的 `SemanticSearch` 建索引，设计 5 个查询测试 Top-3 召回效果。思考：哪些查询语义搜索明显优于关键词搜索？为什么？

### 练习 2：Embedding 质量评测集设计

参考 `03_embedding_comparison.py`，设计一个 20 对的中文评测集（10 对相似、10 对不相关，涵盖同义/近义/无关/反义），用余弦相似度计算准确率。尝试调整 `threshold`（0.4/0.5/0.6），观察对准确率的影响，画出 PR 曲线。

### 练习 3：从语义搜索到 RAG

在 `02_similarity_search.py` 基础上扩展：搜索到 Top-3 相关文档后，把它们拼接进 Prompt 作为上下文，调用 LLM（用 Day02 的统一客户端）生成回答。这就是一个最小 RAG 系统。测试一个需要文档知识才能回答的问题，对比「无检索」与「有检索」的回答质量。

---

## 阶段一总结与下一步

恭喜完成 LLM 阶段一（原理与基础）！回顾四天的学习闭环：

| Day | 主题 | 核心能力 | AISearch 对应模块 |
| --- | --- | --- | --- |
| Day01 | 架构原理 | 理解 Transformer/训练流程 | 理论基础 |
| Day02 | API 集成 | 多模型统一调用 | `clients/` |
| Day03 | Token/上下文 | 成本控制、历史管理 | `core/` |
| Day04 | Embedding | 语义搜索、向量表示 | `embedding/` |

这四块已构成一个**智能问答服务 AISearch** 的完整基础。下一步进入**阶段二（应用与工程）**，你将学习：
- **RAG 完整流程**：分块→向量化→检索→重排→生成
- **Prompt 工程**：设计高效提示词、思维链、少样本
- **Function Calling / Agent**：让 LLM 调用工具、自主决策
- **评估与可观测性**：评测集、A/B 测试、链路追踪
- **微调入门**：LoRA/QLoRA 让模型更懂你的领域

把基础打牢，进阶才能走得更远。开始阶段二的旅程吧！
