# Day04 - 节点解析 Node Parsers 与转换

> 数据管道的第二步是 **Parse（解析）**。加载进来的 `Document` 往往很长，直接检索既不精确又浪费 Token。**Node Parser 把 Document 切分为适合检索的 Node**——切分策略的好坏，直接决定了检索的精度与成本。本章讲解各种切分器、如何调优切分参数、如何在切分时提取结构化元数据（Metadata Extractor），以及用 IngestionPipeline 串联这些转换。

## 学习目标

完成本章后，你将能够：

- 理解 Node Parser 的作用（控制 Node 大小与边界）
- 熟练使用 `SentenceSplitter` 及其 `chunk_size / chunk_overlap` 参数
- 了解 `TokenTextSplitter` / `SentenceWindowNodeParser` / `SemanticSplitterNodeParser` / `HierarchicalNodeParser`
- 通过对比掌握切分参数调优的原则
- 用 Metadata Extractors（关键词 / 标题 / 实体 / 摘要）为 Node 补元数据以提升检索
- 理解 NodeTransform 与 `IngestionPipeline`，串联多个转换
- 自定义 Parser 满足特殊切分需求
- 根据文档特点选择合适的切分策略

---

## 一、Node Parser 概念

**Node Parser 是把 Document 解析为多个 Node 的组件**，属于 Parse 阶段。

它的核心职责：
- 控制 **Node 的大小**（每块多长）
- 控制 **Node 的边界**（在哪里断开，尽量保持语义完整）
- 在"检索精度"与"Token/成本"之间找平衡

> 一句话：Node Parser 决定"一篇文章被切成几块、每块多大、在哪切开"。

---

## 二、常用 Node Parser

| Parser | 切分依据 | 特点 | 适用 |
|--------|---------|------|------|
| **SentenceSplitter** | 按句子边界，再聚合成 chunk | **最常用**，语义较完整 | 绝大多数文本 |
| **TokenTextSplitter** | 按固定 Token 数 | 简单、可精确控制长度 | 对长度敏感的文本 |
| **SentenceWindowNodeParser** | 句子 + 前后窗口上下文 | 保留跨句上下文 | 需要上下文连续的任务 |
| **SemanticSplitterNodeParser** | 语义相似度（embedding 边界） | 按主题自然分组，需联网 | 主题分明的长文档 |
| **HierarchicalNodeParser** | 层级结构（父/子节点） | 支持"先粗后细"检索 | 超长文档/层级检索 |

### SentenceSplitter（最常用）

```python
from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)
nodes = splitter.get_nodes_from_documents(documents)
```

默认按**句子边界**切分：先按句切，再在不超过 `chunk_size` 的前提下把句子拼成块，必要时用 `chunk_overlap` 让相邻块有重叠，以保持上下文连贯。

---

## 三、切分参数调优

两个最核心的参数：

| 参数 | 含义 | 经验值 |
|------|------|--------|
| `chunk_size` | 每块最大 Token/字符数 | 通常 512-1024 token |
| `chunk_overlap` | 相邻块重叠区 | 通常为 chunk_size 的 10%-20% |

### 太大 vs 太小

| 情形 | 后果 |
|------|------|
| `chunk_size` 太大 | 检索不精确，召回块内混多个主题 |
| `chunk_size` 太小 | 语义不完整，缺乏上下文，检索不到关键信息 |
| `overlap` 太大 | Token 冗余、成本高 |
| `overlap` 太小/无 | 跨块语境断裂 |

> 不同 Parser 的参数名与单位（token 或字符）可能不同，使用前查对应文档。

---

## 四、元数据提取 Metadata Extractor

**Metadata Extractor 在切分时为 Node 提取结构化元数据**，从而提升检索精度与可解释性。

### 常用 Extractors

| Extractor | 提取内容 | 作用 |
|-----------|---------|------|
| `KeywordExtractor` | 关键词 | 关键词匹配检索 |
| `TitleExtractor` | 标题 | 定位主题 |
| `EntityExtractor` | 实体（人名/机构等） | 实体级过滤 |
| `SummaryExtractor` | 摘要 | 快速概括 |

### 用法（配合 IngestionPipeline）

```python
from llama_index.core.extractors import TitleExtractor, KeywordExtractor
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter

extractor = MetadataExtractor(extractors=[TitleExtractor(nodes=1), KeywordExtractor(keywords=3)])
pipeline = IngestionPipeline(transformations=[SentenceSplitter(), extractor])
nodes = pipeline.run(documents=docs)
```

> 多数内置 Extractor 依赖 LLM 生成，需 API Key；本模块为无 Key 场景提供了规则化降级实现。

---

## 五、NodeTransform 与 IngestionPipeline

- **NodeTransform（转换）**：对 Document / Node 进行转换的组件统称，如 Splitter、Extractor、清理/去重等。
- **IngestionPipeline（摄取管道）**：把多个 Transform 按顺序串联，输入 Document、输出 Node，一气呵成。

```
  Document ─▶ [Splitter] ─▶ [Extractor] ─▶ [自定义转换] ─▶ List[Node]
```

`transform_nodes` / `transform_documents` 是 Pipe 内部分组件提供的方法；用 `IngestionPipeline` 组装后就不必手动一个个调用。

---

## 六、自定义 Parser

继承 `NodeParser` 并实现 `_parse_nodes` 即可定制切分逻辑：

```python
from llama_index.core.schema import NodeParser, TextNode

class MyParser(NodeParser):
    def _parse_nodes(self, nodes, show_progress=False, **kwargs):
        result = []
        # 对每个 Document/Node 做自定义切分
        return result  # List[Node]
```

自定义 Parser 与内置 Parser 一样可用于 `get_nodes_from_documents(...)` 或接入 `IngestionPipeline`。

---

## 七、切分策略选择

| 文档特点 | 推荐策略 |
|---------|---------|
| 短文档（< 1 段） | 小 chunk，甚至整篇一个 Node |
| 普通长文档 | SentenceSplitter + 适中 chunk + overlap |
| 超长/层级结构文档 | HierarchicalNodeParser（先粗后细） |
| 结构化文档（有标题/章节） | 按结构切分（如自定义"按段落+标题"） |
| 主题分明、语义聚合 | SemanticSplitterNodeParser |

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_sentence_splitter.py` | SentenceSplitter 参数演示与不同 chunk_size 对比 | 否 |
| `Code/02_semantic_splitter.py` | SemanticSplitter 语义切分；无 Key 降级规则分组 | 需 Key（降级可跑） |
| `Code/03_metadata_extractor.py` | MetadataExtractor + IngestionPipeline；离线规则降级 | 需 Key（降级可跑） |
| `Code/04_custom_parser.py` | 自定义"按段落+标题"Parser | 否 |

---

## 关键知识点总结

### 1. Node Parser 对比表

`SentenceSplitter`(句子) · `TokenTextSplitter`(固定Token) · `SentenceWindow`(句子窗口) · `Semantic`(语义) · `Hierarchical`(层级)

### 2. 切分参数建议表

| 参数 | 建议 |
|------|------|
| chunk_size | 512-1024 token |
| chunk_overlap | chunk_size 的 10%-20% |

### 3. Metadata Extractor 速查

`KeywordExtractor`(关键词) · `TitleExtractor`(标题) · `EntityExtractor`(实体) · `SummaryExtractor`(摘要)

### 4. IngestionPipeline 概念

将 `Splitter + Extractor + 自定义变换` 按序串联，`pipeline.run(documents)` 输出 `List[Node]`。

### 5. 切分策略决策表

短文档小块 · 普通文档句子切分 · 超长文档层级 · 结构文档按标题 · 主题分明语义切分

---

## 实战练习

### 练习 1：chunk_size 影响实验

用 `01_sentence_splitter.py`，把 `chunk_size` 分别设为 50 / 200 / 1000，记录各自的 Node 数量与各块长度。解释为什么过小会"切太碎"、过大会"抓不准"。

### 练习 2：结构文档切分

用 `04_custom_parser.py` 的思路，为一份带 `## 一级标题`、`### 二级标题` 的 Markdown 文档编写自定义 Parser，要求把"一级标题作为 section_title 元数据"，并输出每节的正文文本。体会"按结构切分"相比"固定长度切分"的优势。

### 练习 3：元数据提检索

运行 `03_metadata_extractor.py`，观察每个 Node 补上的关键词/标题。思考：如果要在检索时做"只看财务部文档"的过滤，你希望这些元数据里有哪些字段？写出 3 个你认为最有用的业务元数据字段并说明理由。

---

## 下一步

经过 Load（Day03）与 Parse（Day04），数据已变成"适合检索的 Node"。接下来便是**构建索引**——Day05 开始进入 Index 阶段，学习 `VectorStoreIndex`、向量存储与持久化，把 Node 真正组织起来供检索。