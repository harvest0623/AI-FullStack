# Day02 - Document 与 Node 数据模型 / 代码说明

本章代码位于 `Code/` 目录，**无需联网**，演示 Document / Node 的数据模型本身。

## 环境准备

```bash
pip install llama-index python-dotenv pydantic
```

> 本章仅涉及数据结构，不需要 API Key 也能完整运行。

## 文件说明

| 文件 | 说明 | 是否需联网 |
|------|------|-----------|
| `01_document_basics.py` | Document 创建与元数据：直接创建 / 追加修改 / from_dict，遍历打印结构 | 否 |
| `02_node_basics.py` | TextNode 创建与属性：自动/手动 node_id、从 Document 派生、relationships 父子关系 | 否 |
| `03_metadata_management.py` | 元数据管理：增删改查、按部门过滤、注入 Prompt 模板 | 否 |

## 运行方式

```bash
python 01_document_basics.py
python 02_node_basics.py
python 03_metadata_management.py
```

## 输出概览

- `01`：展示三种 Document 创建方式及 metadata 的完整结构
- `02`：展示 TextNode 的 `node_id / text / metadata / relationships` 四个核心属性
- `03`：演示 metadata 的编辑、按部门过滤，以及把元数据注入自定义 Prompt