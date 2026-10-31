# Day03 - 文本切块 Chunking 策略

> 切块（Chunking）是 RAG 质量的第一道关口：**一块内容切得好，语义完整且可定位；切得差，语义断裂、噪声满屏。** 上游一切优化都建立在一个合理的"切片粒度"之上。今天我们系统吃透各种切块策略与调优方法。

## 学习目标

完成本章后，你将能够：

- 理解切块对检索质量的直接影响
- 掌握固定大小 / 递归字符 / Token / 语义 / 父子五种切块策略
- 针对不同文档类型选择合适的切块策略
- 理解并调优 chunk_size 与 chunk_overlap
- 掌握切块时保留元数据与结构化信息的方法

---

## 一、为什么切块很关键

- LLM 无法一次处理整个大文档（窗口有限、成本高）。
- 检索需要**细粒度**——整篇文档一次召回既不准又费 Token。
- **切块的粒度决定召回单元的语义完整度**：太细丢上下文，太粗混进噪声。

> 一句话：**切块错误是"一错百错"**——切错了，后面嵌入、检索、生成全部受影响。

---

## 二、主流切块策略对比

| 策略 | 原理 | 优点 | 缺点 | 适用 |
|------|------|------|------|------|
| **固定大小** | 按字符数硬切 | 简单可控 | 可能切断句子/语义 | 均匀短文本 |
| **递归字符** | 按符号层级递归切 | 语义较完整、主流 | 依赖分隔符 | 大多数通用文档 |
| **Token 切块** | 按 Token 长度切 | 与模型窗口精确对齐 | 中文分字丢失语义 | 控制上下文窗口 |
| **语义切块** | 按语义边界切 | 语义最完整 | 计算开销大、需嵌入 | 语义强相关文档 |
| **父子切块** | 大块(parent)+小块(child) | 兼顾细节与上下文 | 存储量增大 | 长文、跨块引用 |

---

## 三、五种策略详解与选型

### 3.1 固定大小切块（Fixed-size Chunking）

```python
# 用 langchain 的按字符长度切（代固定切块演示）
from langchain_text_splitters import CharacterTextSplitter
splitter = CharacterTextSplitter(separator="\n", chunk_size=100, chunk_overlap=10)
chunks = splitter.split_text(long_text)
```
- 优点：实现最简单、运行最快。
- 缺点：可能从句子中间切开，语义断裂。
- 适合：文本均匀、对语义完整性要求不高的场景。

### 3.2 递归字符切块（RecursiveCharacterTextSplitter）⭐ 最常用

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50,
    separators=["\n\n", "\n", "。", "；", "，", " ", ""],
)
```
- 原理：从分隔符优先级最高的开始递归切，尽力不割断语义单元。
- 是 LangChain 默认、工程上最稳的通用选择。

### 3.3 Token 切块（TokenTextSplitter）

```python
from langchain_text_splitters import TokenTextSplitter
splitter = TokenTextSplitter(chunk_size=300, chunk_overlap=30)
```
- 按 Token（而非字符）计数，与模型上下文窗口精确对齐。
- 对中文：字符与 Token 不成比例，通常 Token 更省 Local。

### 3.4 语义切块（Semantic Chunking）⭐ 高质量追求

```python
# langchain-experimental 提供 SemanticChunker
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
splitter = SemanticChunker(OpenAIEmbeddings(), breakpoint_threshold_type="percentile")
chunks = splitter.split_text(long_text)
```
- 用嵌入相似度找到"语义边界"，在意思明显变化的点切分。
- 语义最完整，但需嵌入模型、开销较大。

### 3.5 父子切块（Parent-Child）⭐ 兼顾上下文

```python
# LlamaIndex 提供 HierarchicalNodeParser + AutoMergingRetriever（Day05/09 深入）
from llama_index.core.node_parser import (
    SentenceSplitter, HierarchicalNodeParser,
    get_leaf_nodes, get_root_nodes,
)
node_parser = HierarchicalNodeParser.from_defaults()
nodes = node_parser.get_nodes_from_documents(docs)
leaf_nodes = get_leaf_nodes(nodes)   # 小块，用于精准检索
root_nodes = get_root_nodes(nodes)   # 大块，用于补全上下文
```
- 检索用小块（child）提高精度，回答时回填父块（parent）补全上下文。
- 是解决"上下文漂移"的经典方案。

---

## 四、关键参数：chunk_size 与 chunk_overlap

| 参数 | 含义 | 影响 |
|------|------|------|
| `chunk_size` | 每块的目标大小 | 太小→语义碎；太大→噪声多、成本高 |
| `chunk_overlap` | 相邻块重叠长度 | 防止关键句恰被切断丢失 |

调优经验：
- **chunk_size 参考区间** 200-800 Token 或 300-1500 字符，视文档与问题粒度而定。
- overlap 常设为 size 的 10%-20%。
- 短问短答（条款、数值）适合小 chunk；长文总结适合大 chunk。
- **没有万能参数**，需结合 Day10 的评估指标实测调优。

---

## 五、不同文档类型的切块策略

| 文档类型 | 推荐策略 |
|---------|---------|
| 通用长文（制度/文章） | 递归字符 / 父子切块 |
| 代码仓库 | 按函数/类切（尊重语法） |
| 表格 | 按行/按语义块，勿硬切单元格 |
| Markdown | 按标题层级(HeadingSplitter)切 |
| PDF 多栏 | 按段落 + 元数据保留页号 |
| 对话/多轮 | 按轮次切块 |

> 原则：**切块边界尽量落在"语义自然边界"**（段落、章节、句子），并保留结构信息（标题、页号）到元数据，供检索/引用。

---

## 六、切块与元数据的配合

切块后每个 chunk 是独立检索单元，**务必带上结构元数据**：

```python
for i, chunk in enumerate(chunks):
    chunk.metadata["title"] = "报销规则"     # 来源标题（供引用/过滤）
    chunk.metadata["page"] = i // 3 + 1      # 页码（供定位）
    chunk.metadata["section"] = "差旅"        # 章节（供路由）
```

有了元数据，Day05 的元数据过滤、Day09 的文档路由才成为可能。

---

## 场景：DataIQ 的切块实践

员工制度文档往往很长，且条款之间互相引用。我们采用**递归字符切块（chunk_size=500, overlap=50）**作为基线，章节目录用 `##` 标题保持层级。后续根据 Day10 评估决定是否升级为父子切块。

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_fixed_splitter.py` | 固定大小切块 | 否 |
| `Code/02_recursive_splitter.py` | 递归字符切块（多分隔符） | 否 |
| `Code/03_semantic_splitter.py` | 语义切块（需嵌入） | 是（可降级） |
| `Code/04_chunking_tune.py` | chunk_size/overlap 参数量化对比 | 否 |
| `Code/README.md` | 运行说明 | - |

---

## 关键知识点总结

1. **切块是质量第一道关口**，影响检索与生成。
2. **五种策略**：固定 / 递归 / Token / 语义 / 父子。
3. **递归字符最常用**，语义与父子追求高质量。
4. **chunk_size + overlap 是关键参数**，需实测调优。
5. **保留元数据**：标题/页码/章节 供检索与路由。

---

## 实战练习

### 练习 1：对比三种切块

取一段 1000+ 字制度文档，分别用固定 / 递归 / Token 切块，打印每个块的边界，观察哪种切割最不破坏语义。

### 练习 2：chunk_size 扫描

运行 `04_chunking_tune.py`，对 size ∈ [100, 300, 500, 800] 分别统计块数、平均块长、overlap 覆盖率，分析成本与粒度的权衡。

### 练习 3：父子切块设计

思考 DataIQ 的年假制度：员工问"年假能累计吗"，正确答案散在"领取规则"和"结转规则"两块。设计一个父子切块方案让检索能命中并补全。

### 练习 4：为文档选策略

判断以下各适合哪种切块：①一份 200 页合规手册；②一个 Python 项目库；③一张带标题的销售表格；④一段英文论文。并说明理由。

---

## 下一步

切好的块需要**变成向量**才能被检索。Day04 学习嵌入模型：文本如何变向量、选哪个模型、如何评估嵌入质量。