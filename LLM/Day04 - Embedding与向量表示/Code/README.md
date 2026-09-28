# Day04 Code - Embedding 与向量表示示例

本目录包含 Day04「Embedding 与向量表示」的配套代码，覆盖文本向量化、相似度计算、语义搜索、多模型对比与向量降维可视化，对应 AISearch 项目 `embedding/` 模块（向量编码 / 相似度计算）。

## 环境准备

```bash
# 基础依赖
pip install openai python-dotenv numpy scikit-learn

# 可选：本地 Embedding 模型（用于 03 对比）
pip install sentence-transformers
```

### 配置 .env

```dotenv
OPENAI_API_KEY=sk-你的密钥
# 可选代理
# OPENAI_BASE_URL=https://your-proxy.com/v1
```

> `03_embedding_comparison.py` 的本地模型部分无需 Key；其余脚本需 OpenAI Key。

## 文件说明

| 文件 | 核心类/函数 | 内容 | 依赖 |
| --- | --- | --- | --- |
| `01_embedding_basics.py` | `EmbeddingClient` | 文本转向量、余弦/欧氏/点积三种相似度、降维演示 | openai, numpy |
| `02_similarity_search.py` | `SemanticSearch` | 文档索引构建 + Top-K 语义搜索 + 批量搜索 | openai, numpy |
| `03_embedding_comparison.py` | `compare_models` | OpenAI small/large vs 本地 bge：维度/准确率/速度/成本对比 | openai, numpy, (sentence-transformers) |
| `04_vector_visualization.py` | `reduce_pca/reduce_tsne` | 高维向量降到 2D/3D，打印可视化数据，展示聚类 | openai, numpy, scikit-learn |

## 运行方式

```bash
python 01_embedding_basics.py        # Embedding 基础与相似度
python 02_similarity_search.py        # 语义搜索
python 03_embedding_comparison.py     # 多模型对比
python 04_vector_visualization.py     # 向量降维可视化
```

## 各 Embedding 模型选择决策表

| 场景 | 推荐模型 | 理由 |
| --- | --- | --- |
| 通用英文/多语言、追求简单 | `text-embedding-3-small` | 性价比高，1536 维，$0.02/1M |
| 追求最高精度 | `text-embedding-3-large` | 3072 维，精度高，$0.13/1M |
| 中文为主、追求效果 | `BAAI/bge-large-zh-v1.5`（本地） | 中文开源最佳之一 |
| 多语言 | `bge-m3` / Cohere embed-v3 | 多语言对齐好 |
| 隐私/离线/成本敏感 | `sentence-transformers` 本地模型 | 免费、数据不出域 |
| 长文本 | `Jina Embeddings v3` | 支持超长文本（8K） |
| 需要降维省存储 | `text-embedding-3-*` + `dimensions` 参数 | Matryoshka 降维 |

## 相似度计算方法对比

| 方法 | 公式 | 范围 | 特点 | 适用 |
| --- | --- | --- | --- | --- |
| 余弦相似度 | `A·B/(|A||B|)` | [-1,1] | 对向量长度不敏感，最常用 | 通用语义相似 |
| 欧氏距离 | `‖A-B‖` | [0,∞) | 关注绝对距离，越小越相似 | 几何聚类 |
| 点积 | `A·B` | (-∞,∞) | 简洁快，但受长度影响 | 归一化后≈余弦 |

> **工程技巧**：把向量预先归一化（L2 norm），则点积 = 余弦相似度，可用更快的点积运算。

## 语义搜索实现步骤

```
1. 准备文档库
2. 用 Embedding 模型把每篇文档编码为向量（建索引）
3. 把查询文本编码为向量
4. 计算查询向量与所有文档向量的相似度
5. 取 Top-K 最相似的文档返回
6. （进阶）把 Top-K 文档作为上下文交给 LLM 生成答案 → 这就是 RAG
```

大规模场景需用专业向量数据库（FAISS / Milvus / Qdrant / pgvector）做近似最近邻（ANN）搜索，本目录 `02` 用 numpy 演示原理，适合中小规模。

## 向量可视化工具推荐

| 工具 | 特点 |
| --- | --- |
| TensorFlow Embedding Projector | 在线交互式，支持 PCA/t-SNE/UMAP，上传即用 |
| matplotlib + seaborn | Python 本地绘制散点图，灵活 |
| Plotly | 交互式 3D 散点图 |
| UMAP-learn | 比 t-SNE 更兼顾局部与全局结构 |

## Embedding 质量评估方法

1. **相关性测试**：构造相似/不相似文本对，看相似度是否能区分（见 `03` 评测集）
2. **聚类测试**：同类文本应聚在一起（见 `04` 可视化）
3. **检索质量**：对已知答案的查询，看 Top-K 命中率（Recall@K / MRR）
4. **对比基线**：与 BM25 关键词搜索对比，语义搜索应在同义/近义场景占优

## 下一步

完成 Day04 后，你已掌握 LLM 阶段一（原理与基础）的全部内容：
- Day01 架构原理 → Day02 API 调用 → Day03 Token/上下文管理 → Day04 Embedding/语义搜索

这四块组合起来，你已经具备搭建一个**智能问答服务 AISearch** 的全部基础：
- `clients/` ← Day02 多模型统一客户端
- `core/` ← Day03 对话管理 / Token 计数 / 上下文管理
- `embedding/` ← Day04 向量编码 / 相似度计算

下一步可进入**阶段二（应用与工程）**，学习 RAG、Prompt 工程、Agent、函数调用等进阶主题，把这些基础组件组装成完整应用。
