# Day07 Code - Document Loaders 与 Text Splitters 代码示例

本目录包含 Day07「Document Loaders 与 Text Splitters」的全部可运行 Python 代码，演示从加载到分割的完整文档处理流程。

## 文件说明

| 文件 | 内容 | 核心知识点 |
|------|------|-----------|
| `01_document_loaders.py` | 多种格式文档加载 | TextLoader / CSVLoader / JSONLoader / PyPDFLoader / DocumentLoader 统一封装 |
| `02_web_loaders.py` | 网页与在线文档加载 | WebBaseLoader / ArxivLoader / DirectoryLoader / WebDocumentLoader 封装 / metadata 对比 |
| `03_text_splitters.py` | 多种分割器对比 | RecursiveCharacter / Character / Token / MarkdownHeader / 代码分割器 / SplitterComparator |
| `04_splitter_tuning.py` | 分割参数调优 | chunk_size 对比 / chunk_overlap 对比 / SplitterConfig / 调优报告 / 最佳实践 |

## 运行方式

```bash
# 安装依赖
pip install langchain langchain-openai langchain-community python-dotenv pydantic
pip install pypdf beautifulsoup4 arxiv  # 可选：PDF/网页/论文加载

# 配置 .env
# OPENAI_API_KEY=sk-xxxxxxxx（本天大部分代码不调用 LLM，Key 可选）

cd "Day07 - Document Loaders与Text Splitters/Code"

# 示例数据会自动生成在 sample_data/ 目录
python 01_document_loaders.py
python 02_web_loaders.py
python 03_text_splitters.py
python 04_splitter_tuning.py
```

> 注：`01_document_loaders.py` 会自动生成示例数据文件（txt/csv/json）。`02_web_loaders.py` 的网页和论文加载需网络访问，无网络时会打印用法说明。

## Loader 选择决策表

| 数据来源 | 推荐 Loader | 安装依赖 |
|---------|------------|---------|
| 本地 txt | TextLoader | 无 |
| 表格 CSV | CSVLoader | 无 |
| 结构化 JSON | JSONLoader | 无 |
| PDF 文档 | PyPDFLoader | pypdf |
| Markdown | UnstructuredMarkdownLoader | unstructured |
| 网页 | WebBaseLoader | beautifulsoup4 |
| arXiv 论文 | ArxivLoader | arxiv |
| 目录批量 | DirectoryLoader | 取决于文件类型 |

## Splitter 选择决策表

| 文档类型 | 推荐 Splitter | 关键参数 |
|---------|--------------|---------|
| 通用文本 | RecursiveCharacterTextSplitter | chunk_size=500, overlap=50 |
| 简单文本 | CharacterTextSplitter | separator="\n\n" |
| 精确 Token 控制 | TokenTextSplitter | chunk_size=200 tokens |
| Markdown 文档 | MarkdownHeaderTextSplitter | headers_to_split_on |
| 网页 HTML | HTMLHeaderTextSplitter | headers_to_split_on |
| 代码文档 | RecursiveCharacterTextSplitter.from_language | language=Language.PYTHON |

## 参数调优建议

```
起始参数：chunk_size=500, chunk_overlap=50
问答检索 → chunk_size 偏小（300-500）
摘要任务 → chunk_size 偏大（800-1000）
overlap = chunk_size × 10%~20%
```

## 常见格式处理指南

| 格式 | 注意事项 |
|------|---------|
| 中文文本 | separators 加 "。" "！" "？" |
| PDF | PyPDFLoader 每页一个 Document，注意表格/图片可能丢失 |
| 网页 | WebBaseLoader 可能含导航等噪声，需过滤 |
| CSV | CSVLoader 每行一个 Document，列名进 metadata |
| 代码 | 用 from_language，避免在语句中间断开 |

## Document 处理流程最佳实践

```
1. Load   — 选对 Loader，注意 encoding
2. Split  — 优先 RecursiveCharacterTextSplitter
3. Transform — 可选：去重、过滤、翻译
4. Store  — 存入 VectorStore（Day08 讲解）
5. Retrieve — 用 Retriever 检索（Day08 讲解）
```

### 完整流程代码模板

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Load
docs = TextLoader("doc.txt", encoding="utf-8").load()

# 2. Split
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50,
    separators=["\n\n", "\n", "。", " ", ""],
)
chunks = splitter.split_documents(docs)

# 3. 后续存入向量库（Day08）
# vectorstore = Chroma.from_documents(chunks, embedding=...)
```
