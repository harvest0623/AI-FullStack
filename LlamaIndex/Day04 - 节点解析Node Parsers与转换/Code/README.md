# Day04 - 节点解析 Node Parsers 与转换 / 代码说明

本章代码位于 `Code/` 目录。切分与自定义 Parser 可离线运行；语义切分与内置元数据提取需联网（无 Key 时已做降级）。

## 环境准备

```bash
pip install llama-index llama-index-embeddings-openai llama-index-readers-file python-dotenv
```

> 语义切分脚本（`02`）和内置元数据提取（`03` 在线分支）需要 OPENAI_API_KEY；无 Key 时程序会自动降级为规则演示，不会崩溃。

## 文件说明

| 文件 | 说明 | 是否需联网 |
|------|------|-----------|
| `01_sentence_splitter.py` | SentenceSplitter：chunk_size / chunk_overlap，对比不同切块大小 | 否 |
| `02_semantic_splitter.py` | SemanticSplitterNodeParser 语义切分；无 Key 降级为规则分组演示 | 需 Key（可降级） |
| `03_metadata_extractor.py` | MetadataExtractor（Title/Keyword/Summary）+ IngestionPipeline；离线用规则元数据注入降级 | 需 Key（可降级） |
| `04_custom_parser.py` | 继承 NodeParser 实现"按段落+标题"切分，并接入 IngestionPipeline | 否 |

## 运行方式

```bash
python 01_sentence_splitter.py     # 离线可跑
python 04_custom_parser.py         # 离线可跑
python 02_semantic_splitter.py     # 有 Key 体验语义切分，无 Key 自动降级
python 03_metadata_extractor.py    # 有 Key 体验真实元数据提取，无 Key 规则演示
```

## 输出概览

- `01`：不同 chunk_size 下的 Node 数量与各块长度对比
- `02`：语义分组结果（按语义边界而非固定长度）
- `03`：每个 Node 被补上的关键词/标题等元数据
- `04`：按 `## 标题` 结构切出的节点及其 section_title 元数据