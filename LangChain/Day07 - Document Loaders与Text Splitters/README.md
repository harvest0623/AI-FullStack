# Day07 - Document Loaders 与 Text Splitters

要让 ChainQA 真正回答"你的文档"里的问题，第一步是让 LLM 能"读"这些文档。现实中的知识以各种形态存在：PDF、Word、网页、CSV、Markdown……它们长短不一、格式各异，而 LLM 的上下文窗口有限，不可能一次性塞进一本 500 页的书。Document Loaders 负责把不同来源的内容统一加载为 LangChain 的 `Document` 对象，Text Splitters 则负责把这些长文档切分成大小合适、语义完整的块。这两者是非结构化数据处理的基础工具，也是后续检索增强（RAG）的入口环节。本章带你掌握从加载到分割的完整文档处理流程。

---

## 学习目标

- 理解 `Document` 对象的结构（page_content + metadata）
- 掌握常用 Document Loaders（Text/CSV/JSON/PDF/Web/Directory）
- 理解为什么需要 Text Splitters 及其目标
- 熟练使用 RecursiveCharacterTextSplitter（最常用分割器）
- 掌握分割参数（chunk_size / chunk_overlap）的调优方法
- 了解代码分割器、Markdown/HTML 结构化分割器
- 理解完整的文档处理流程：Load → Split → Transform → Store → Retrieve

---

## 理论知识讲解

### 1. Document 概念

`Document` 是 LangChain 中文档的基本单位。

```python
from langchain_core.documents import Document

doc = Document(
    page_content="这是文档的文本内容。",
    metadata={"source": "readme.md", "page": 1, "author": "张三"},
)
```

| 字段 | 说明 |
|------|------|
| `page_content` | 文档的文本内容（字符串） |
| `metadata` | 文档元数据（来源、页码、作者等），字典类型 |

一份长文档通常会被分割为多个 `Document`，每个块保留各自的 metadata（如页码），便于追溯来源。

### 2. Document Loaders 分类

Document Loaders 负责把不同来源的数据加载为 `Document` 列表。

| 类别 | 常用 Loader | 说明 |
|------|------------|------|
| 文件类 | TextLoader / CSVLoader / JSONLoader / PyPDFLoader / UnstructuredMarkdownLoader | 加载本地文件 |
| 网页类 | WebBaseLoader / ArxivLoader / GitLoader | 抓取在线内容 |
| 数据库类 | SQLDatabaseLoader / MongoDBLoader | 从数据库读取 |
| 云存储类 | S3DirectoryLoader / GoogleDriveLoader | 加载云端文件 |

### 3. 常用 Loader 详解

#### 3.1 TextLoader

加载 `.txt` 文件，最简单的 Loader。

```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("readme.txt", encoding="utf-8")
docs = loader.load()  # 返回 List[Document]，通常 1 个 Document
```

#### 3.2 CSVLoader

加载 CSV，**每行一个 Document**，列名作为 metadata。

```python
from langchain_community.document_loaders import CSVLoader

loader = CSVLoader("data.csv", encoding="utf-8")
docs = loader.load()  # 100 行 CSV → 100 个 Document
# 每个 Document 的 page_content 是该行内容，metadata 含行号
```

#### 3.3 JSONLoader

加载 JSON，支持 `jq` 语法提取字段。

```python
from langchain_community.document_loaders import JSONLoader

loader = JSONLoader(
    file_path="data.json",
    jq_schema=".messages[]",  # 提取 messages 数组的每个元素
    text_content=False,
)
docs = loader.load()
```

#### 3.4 PyPDFLoader

加载 PDF，**每页一个 Document**。

```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("doc.pdf")  # 需 pip install pypdf
docs = loader.load()  # 10 页 PDF → 10 个 Document，metadata 含 page
```

#### 3.5 WebBaseLoader

加载网页内容（需 `beautifulsoup4`）。

```python
from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://example.com/article")
docs = loader.load()
```

#### 3.6 DirectoryLoader

批量加载目录下所有文件。

```python
from langchain_community.document_loaders import DirectoryLoader

loader = DirectoryLoader(
    "./docs",
    glob="**/*.txt",            # 文件匹配模式
    loader_cls=TextLoader,      # 用哪个 Loader 加载
)
docs = loader.load()
```

### 4. Text Splitters 概念

#### 4.1 为什么需要分割

- LLM 上下文窗口有限（4K-200K Token），长文档无法整体塞入
- 检索时需要小而精的块，整篇文档检索不精确
- 分块策略直接影响后续检索质量

#### 4.2 分割目标

- **控制块大小**：每块不超过模型上下文限制
- **保持语义完整性**：尽量在自然边界处切分，不在句子中间断开
- **保留上下文关联**：块之间适当重叠，避免信息断裂

#### 4.3 分块策略影响检索

| 策略 | 检索效果 |
|------|---------|
| 块太大 | 检索不精确、Token 浪费 |
| 块太小 | 语义不完整、块数过多 |
| 无重叠 | 跨块信息断裂 |
| 重叠太多 | 冗余、存储浪费 |

### 5. 常用 Text Splitter 详解

#### 5.1 RecursiveCharacterTextSplitter（最常用）

递归按分隔符分割：先按段落，再按句子，最后按字符。**通用首选**。

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,           # 每块最大字符数
    chunk_overlap=50,         # 块之间重叠字符数
    separators=["\n\n", "\n", "。", " ", ""],  # 分隔符优先级
)
chunks = splitter.split_documents(docs)
```

工作原理：依次尝试每个分隔符，优先用大粒度（段落）切分，切不开再用小粒度（句子、字符）。

#### 5.2 CharacterTextSplitter

按固定分隔符分割，简单直接。

```python
from langchain_text_splitters import CharacterTextSplitter

splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=500,
    chunk_overlap=50,
)
```

#### 5.3 TokenTextSplitter

按 Token 数分割，精确控制 Token。

```python
from langchain_text_splitters import TokenTextSplitter

splitter = TokenTextSplitter(
    chunk_size=200,        # 每块最大 Token 数
    chunk_overlap=20,
)
```

#### 5.4 MarkdownHeaderTextSplitter

按 Markdown 标题层级分割，保留结构信息。

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
)
```

#### 5.5 HTMLHeaderTextSplitter

按 HTML 标签分割。

```python
from langchain_text_splitters import HTMLHeaderTextSplitter

splitter = HTMLHeaderTextSplitter(
    headers_to_split_on=[("h1", "Header 1"), ("h2", "Header 2")]
)
```

#### 5.6 代码分割器

按代码语法分割，避免在语句中间断开。

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=500,
    chunk_overlap=50,
)
```

### 6. 分割参数调优

#### 6.1 chunk_size（块大小）

| 取值 | 检索效果 | 适用场景 |
|------|---------|---------|
| 300 | 精确但可能语义不全 | 问答型检索 |
| 500 | 平衡（推荐起点） | 通用场景 |
| 1000 | 语义完整但不够精确 | 摘要型任务 |
| 2000 | 信息丰富但 Token 浪费 | 长上下文分析 |

#### 6.2 chunk_overlap（重叠）

| 取值 | 效果 |
|------|------|
| 0 | 无重叠，跨块信息可能断裂 |
| 50-100 | 适度重叠（推荐，约 chunk_size 的 10-20%） |
| 200+ | 重叠多，冗余增加 |

#### 6.3 调优原则

- **chunk_size**：通常 500-1000 字符（或 200-500 Token）
- **chunk_overlap**：通常为 chunk_size 的 10-20%
- **实验对比**：用不同参数对比检索效果，选择最优

### 7. Document Transformer

分割后可对文档做进一步转换：

| Transformer | 作用 |
|-------------|------|
| 重排器（Reorder） | 重新排序文档 |
| 过滤器（Filter） | 过滤无关文档 |
| 翻译器 | 翻译文档内容 |
| EmbeddingsRedundantFilter | 去除语义重复文档 |

```python
from langchain_community.document_transformers import EmbeddingsRedundantFilter

redundant_filter = EmbeddingsRedundantFilter(embeddings=embeddings)
docs = redundant_filter.transform_documents(docs)
```

### 8. 完整文档处理流程

```
Load（加载）→ Split（分割）→ Transform（转换）→ Store（存储）→ Retrieve（检索）
```

```python
# 1. Load
docs = TextLoader("doc.txt").load()

# 2. Split
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# 3. Transform（可选）
# chunks = some_transformer.transform_documents(chunks)

# 4. Store（下一章讲解）
# vectorstore = Chroma.from_documents(chunks, embedding=...)

# 5. Retrieve（下一章讲解）
# results = retriever.invoke("query")
```

---

## 代码文件说明

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_document_loaders.py` | 多种格式文档加载 | Text/CSV/JSON/PDF 加载与 Document 结构 |
| `02_web_loaders.py` | 网页与在线文档加载 | WebBaseLoader/ArxivLoader/DirectoryLoader |
| `03_text_splitters.py` | 多种分割器对比 | Recursive/Character/Token/Markdown/代码分割器 |
| `04_splitter_tuning.py` | 分割参数调优 | chunk_size/overlap 对比实验与调优报告 |

运行方式：

```bash
cd "Day07 - Document Loaders与Text Splitters/Code"
python 01_document_loaders.py
```

> 部分示例会自动生成测试数据文件，无需手动准备。

---

## 关键知识点总结

### Document Loaders 速查表

| Loader | 格式 | 安装依赖 | 输出粒度 |
|--------|------|---------|---------|
| TextLoader | .txt | 无 | 整文件一个 |
| CSVLoader | .csv | 无 | 每行一个 |
| JSONLoader | .json | 无 | 按 jq_schema |
| PyPDFLoader | .pdf | pypdf | 每页一个 |
| UnstructuredMarkdownLoader | .md | unstructured | 整文件一个 |
| WebBaseLoader | 网页 | beautifulsoup4 | 整页一个 |
| ArxivLoader | 论文 | arxiv | 每篇一个 |
| DirectoryLoader | 目录 | 取决于文件 | 批量加载 |

### Text Splitters 对比表

| Splitter | 分割方式 | 适用场景 | 关键参数 |
|----------|---------|---------|---------|
| RecursiveCharacterTextSplitter | 递归字符 | 通用首选 | chunk_size / chunk_overlap / separators |
| CharacterTextSplitter | 固定字符 | 简单文本 | separator / chunk_size |
| TokenTextSplitter | 按 Token | 精确 Token 控制 | chunk_size / chunk_overlap |
| MarkdownHeaderTextSplitter | 按 Markdown 标题 | Markdown 文档 | headers_to_split_on |
| HTMLHeaderTextSplitter | 按 HTML 标签 | 网页内容 | headers_to_split_on |
| Language 代码分割器 | 按代码语法 | 代码文档 | language / chunk_size |

### 分割参数建议表

| 参数 | 推荐范围 | 调优建议 |
|------|---------|---------|
| chunk_size | 500-1000 字符 | 问答用小，摘要用大 |
| chunk_overlap | chunk_size 的 10-20% | 避免信息断裂 |
| separators | 优先段落→句子→字符 | 中文加 "。" |

### Document 处理流程

```
Load → Split → Transform → Store → Retrieve
加载    分割    转换        存储     检索
```

---

## 实战练习

### 练习 1：加载并分割一份 Markdown 文档

- 用 `UnstructuredMarkdownLoader` 加载一份 `.md` 文件
- 用 `MarkdownHeaderTextSplitter` 按标题分割
- 再用 `RecursiveCharacterTextSplitter` 控制块大小
- 观察 metadata 中保留的标题层级信息

### 练习 2：对比不同 chunk_size 的分割效果

- 准备一份 3000 字的长文本
- 分别用 chunk_size = 300 / 500 / 1000 / 2000 分割
- 统计每种参数下的块数、平均块长度
- 评估哪种参数最适合问答检索

### 练习 3：构建文档处理流水线

- 用 `DirectoryLoader` 批量加载一个目录下的多个 txt 文件
- 用 `RecursiveCharacterTextSplitter` 分割
- 用 `EmbeddingsRedundantFilter` 去重
- 输出处理后的文档总数和去重数量

---

## 小结

Document Loaders 和 Text Splitters 是非结构化数据处理的两大基础工具：Loaders 把各种格式统一为 `Document`，Splitters 把长文档切成可检索的小块。`RecursiveCharacterTextSplitter` 是通用首选，参数调优的核心是平衡块大小与语义完整性。完成 Load → Split 后，下一章我们将把这些块存入向量库，让 ChainQA 具备语义检索能力。
