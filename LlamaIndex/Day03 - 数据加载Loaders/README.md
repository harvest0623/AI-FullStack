# Day03 - 数据加载 Loaders

> 数据管道的第一步是 **Load（加载）**。LlamaIndex 用 *Loader / Reader* 把各种格式和来源的数据（文件、网页、API、数据库）统一读取为 `Document` 列表，从而让后续的解析、索引、查询不必关心数据来自哪里。本章系统讲解最常用的加载器，从通用的 `SimpleDirectoryReader` 到各格式专用 Reader，再到 LlamaHub 社区集成与自定义 Loader。

## 学习目标

完成本章后，你将能够：

- 理解 Loader / Reader 的概念与统一输出 `List[Document]`
- 熟练使用 `SimpleDirectoryReader`（基础 / 递归 / 扩展名过滤 / 批量）
- 掌握各格式 Reader（PDF / Docx / CSV / Markdown / PPTX）的用法与专属参数
- 了解 LlamaHub 社区数百种 Loader 及安装方式
- 使用 `WebPageReader` / `StringReader` / `JSONReader` 从不同来源加载
- 知道如何处理加载性能与容错问题
- 自定义 Loader 接入任意数据源

---

## 一、Loader 概念

**Loader（也叫 Reader）是将外部数据加载为 `Document` 列表的工具**，它是 Load 阶段的执行者。

```
外部数据（文件/网页/API/数据库）
        │
        ▼
    Loader  ──▶  List[Document]
```

统一输出 `List[Document]` 是 LlamaIndex 的关键设计：**无论数据源是什么，进入管道后都是统一的 Document**，后续 Parse → Index → Query 无需关心来源差异。

> 在 LlamaIndex 中 `Loader` 与 `Reader` 常可互换使用。

---

## 二、SimpleDirectoryReader（最重要）

`SimpleDirectoryReader` 是使用频率最高的加载器，它能**自动识别目录下多种文件类型**并一次性加载，无需为每种格式单独指定 Reader。

```python
from llama_index.core import SimpleDirectoryReader

# 最简单用法：加载目录下所有支持的文件
documents = SimpleDirectoryReader("data").load_data()
```

### 支持的格式

`pdf / txt / md / docx / pptx / csv / ipynb / html / image` 等。

### 常用参数

| 参数 | 作用 |
|------|------|
| `input_dir` | 目录路径 |
| `input_files` | 指定具体文件列表 |
| `recursive` | 是否递归加载子目录（默认 False） |
| `required_exts` | 只加载指定扩展名（如 `[".txt", ".md"]`） |
| `exclude` | 排除某些文件名/目录 |
| `filename_as_id` | 用文件名作为 Document id |
| `num_files_limit` | 限制最多加载多少个文件（大目录控制） |

### 场景示例

```python
documents = SimpleDirectoryReader(
    input_dir="docs",
    recursive=True,
    required_exts=[".pdf", ".md"],
    filename_as_id=True,
).load_data()
```

---

## 三、文件类型 Reader（llama-index-readers-file）

当需要对特定格式精细控制时，可用专用 Reader（来自 `llama-index-readers-file`）：

| Reader | 用途 | 说明 |
|--------|------|------|
| `PDFReader` | PDF 解析 | 可配置按页/段落，自动拆分 |
| `DocxReader` | Word 文档 | 读取 .docx |
| `CsvReader` | CSV 表格 | 处理表头与行列 |
| `MarkdownReader` | Markdown | 按标题结构切分 |
| `PPTXReader` | PPT 演示 | 读取每页内容 |
| `JSONReader` | JSON | 读取 JSON 结构 |

```python
from llama_index.readers.file import PDFReader

reader = PDFReader()
docs = reader.load_data(file="docs/report.pdf")
```

> 这些高保真解析（尤其 PDF 复杂版式）往往依赖额外库（如 `pypdf`），首次使用需按提示安装。日常多数场景用 `SimpleDirectoryReader` 自动识别即可；需要**精细切分或参数控制**时再单独用专用 Reader。

---

## 四、LlamaHub 社区集成

**LlamaHub**（llamahub.ai）是 LlamaIndex 的社区"应用市场"，提供**数百种 Loader、Tools、Data Agent**，覆盖：

- 数据库：Postgres / MySQL / SQLite / 向量库
- 云服务与 SaaS：Notion / 飞书 / Google Drive / Slack
- 网页：通用网页 / 特定网站
- API：各种公开数据接口
- 其他：文件、消息、音频转写等

```bash
pip install llama-index-readers-notion      # Notion 文档
pip install llama-index-readers-database    # 数据库
```

安装后按模板使用即可。制作面向特定业务的数据管道时，**优先在 LlamaHub 查找是否有现成 Loader**，真正没有再接权写自定义 Loader（见第五节）。

---

## 五、其他常用 Loader

| Loader | 用途 | 示例 |
|--------|------|------|
| `WebPageReader` | 加载网页正文 | `WebPageReader(html_to_text=True).load_data(urls=[url])` |
| `StringReader` | 字符串直接转 Document | `Document(text=...)` 最简形式 |
| `JSONReader` | JSON 数据 | `JSONReader().load_data(input_file=path)` |

网页加载适合抓取在线文档/新闻；字符串加载适合内存中已有的文本（日志、代码片段）。

---

## 六、自定义 Loader

当内置与社区 Loader 都无法满足时，继承 `BaseReader` 实现 `load_data()` 即可接入任意数据源：

```python
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document


class MyReader(BaseReader):
    def load_data(self, *args, **kwargs) -> list[Document]:
        raw = self.fetch_raw()          # 从你的数据源拉取
        return [
            Document(text=item["body"], metadata=item.get("metadata", {}))
            for item in raw
        ]
```

**要点**：输入任意、输出统一 `List[Document]`，这就是它能够无缝接入 LlamaIndex 生态的原因。

---

## 七、加载性能与容错

- **大目录**：用 `num_files_limit` 分批、或 `exclude` 排除无关文件，或按目录/时间段多路加载。
- **并行/异步**：可用 `load_data` 之后自行并发，或在 Workflows 中并行步骤。
- **失败处理**：单个文件解析失败不应中断整批——用 try-except 捕获，记录后跳过；Reader 缺失依赖时报 ImportError，需按提示安装。
- **元数据补齐**：加载后可统一为每个 Document 补上 `source` / `timestamp` 等，便于后续过滤与追溯。

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_simple_reader.py` | SimpleDirectoryReader：基础 / 递归 / required_exts / metadata | 否 |
| `Code/02_file_readers.py` | Markdown / CSV / PDF / Docx 等 Reader | 否（PDF/Docx 视依赖） |
| `Code/03_web_reader.py` | WebPageReader / StringReader / JSONReader | 网页部分需联网 |
| `Code/04_custom_loader.py` | 继承 BaseReader 的自定义 Loader | 否 |

---

## 关键知识点总结

### 1. Loader 类型速查

| 类型 | 代表 | 适用 |
|------|------|------|
| 通用目录 | SimpleDirectoryReader | 绝大多数本地文件 |
| 文件专用 | PDFReader / DocxReader 等 | 精细控制某格式 |
| 网页 | WebPageReader | 在线文档 |
| 内存 | StringReader | 已有文本 |
| 社区 | LlamaHub 数百种 | 第三方服务/数据库 |
| 自定义 | BaseReader 子类 | 任意数据源 |

### 2. SimpleDirectoryReader 参数速查

`input_dir` / `input_files` / `recursive` / `required_exts` / `exclude` / `filename_as_id` / `num_files_limit`

### 3. 各文件 Reader 对比

`PDFReader`(PDF) · `DocxReader`(Word) · `CsvReader`(CSV) · `MarkdownReader`(MD) · `PPTXReader`(PPT) · `JSONReader`(JSON)

### 4. LlamaHub 使用

先搜 → `pip install llama-index-readers-xxx` → 按模板调用

### 5. 自定义 Loader 步骤

继承 `BaseReader` → 实现 `load_data()` 返回 `List[Document]` → 作为普通 Reader 使用

---

## 实战练习

### 练习 1：目录加载实战

准备一个含 `readme.txt`、`guide.md`、`table.csv`、一份 PDF 的目录。用 `Sim明pleDirectoryReader` ：
1. 默认加载全部，打印每个 Document 的文件名与 metadata；
2. 加 `recursive=True` 与 `required_exts=[".txt", ".md"]`，验证过滤效果。

### 练习 2：LlamaHub 探索

进入 [LlamaHub](https://llamahub.ai/)，搜索并安装一个你感兴趣的 Loader（例如 `llama-index-readers-notion` 或某个数据库 reader），阅读它的 README，写出"用你自定义数据源写一个 10 行以内的加载示例"。

### 练习 3：自定义 Loader

仿照 `04_custom_loader.py`，为"读取你的本地 JSON 配置文件目录"编写一个继承 `BaseReader` 的 Loader，使其 `load_data()` 返回包含 `file_name`、`type` 等 metadata 的 Document 列表，并成功打印出来。

---

## 下一步

数据已能加载成 `Document`。但长文档不利于直接检索——Day04 将学习 **Node Parser**：如何把 Document 切分为适合检索的 Node，并控制切分质量。