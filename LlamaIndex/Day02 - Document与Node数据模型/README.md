# Day02 - Document 与 Node 数据模型

> LlamaIndex 处理数据时有两级基本单元：**Document（文档）**与 **Node（节点）**。前者是"一块原始数据"，后者是"切分后用来检索的最小单元"。不理解这两个概念，索引、检索、问答全部无从谈起。本章把数据模型彻底讲透。

## 学习目标

完成本章后，你将能够：

- 说出 Document 与 Node 的定义与区别
- 用多种方式创建 Document，并熟练管理其 metadata
- 理解 metadata 在检索中的三大作用（展示 / 过滤 / 注入 Prompt）
- 创建 TextNode，掌握 `node_id / text / metadata / relationships` 属性
- 区分 TextNode / ImageNode / IndexNode 的适用场景
- 理解 Document → Node 的关系与节点关系类型（parent-child / prev-next / source）
- 按生产规范设计自己的数据模型

---

## 一、Document 概念

**Document（文档）是 LlamaIndex 处理数据的最小输入单元**——它可以是一篇文章、一个文件、一段文本。所有 Loader 的结果都是 `List[Document]`，所有 Index 的输入也是 Document（或 Node）。

### Document 的属性

一个 Document 由**两大核心部分**组成：

| 属性 | 含义 |
|------|------|
| `text` | 文档的文本内容（正文） |
| `metadata` | 描述性元数据（来源、属性、业务字段） |
| `doc_id` | 文档唯一标识（自动生成或指定） |

### 创建 Document

```python
from llama_index.core.schema import Document

# 方式一：直接创建
doc = Document(
    text="DataIQ 支持 PDF、Word 等格式。",
    metadata={"file_name": "intro.txt", "department": "技术部"},
)

# 方式二：先创建后追加元数据
doc.metadata["author"] = "Admin"

# 方式三：从 dict 反向创建
doc = Document.from_dict({"text": "...", "metadata": {...}})
```

> `text` 是正文，`metadata` 是"关于这段数据的描述"。二者共同构成一个可用的数据单元。

---

## 二、metadata 元数据

### 2.1 作用

metadata 描述 Document / Node 的**来源与属性**：文件名、路径、标题、创建时间、作者、标签、部门等。

### 2.2 为什么重要

metadata 在检索链路中扮演三个角色：

1. **可展示**：回答时附带来源引用，增强可信度（"来自财务部《报销规则》"）。
2. **可过滤**：在检索前/后可据 metadata 过滤节点（如"只看财务部文档"）。
3. **可注入 Prompt**：把元数据拼进 Prompt，让 LLM 知道内容来源与上下文。

### 2.3 自定义 metadata

除了 Loader 自动写入的字段（文件名等），你可自由添加**业务维度字段**，例如：

```python
doc.metadata = {
    "department": "财务部",    # 部门（权限/过滤）
    "doc_type": "制度文档",    # 文档类型
    "create_time": "2026-01-01",
    "security_level": "内部",  # 密级
}
```

---

## 三、Node 概念

**Node（节点）是切分后的检索单元**，是查询的基础粒度。因为一个 Document 往往太长，直接整篇检索既不精确又浪费 Token，所以要先切成多个 Node。

### 为什么需要 Node

| 场景 | Document | Node |
|------|----------|------|
| 粒度 | 整篇文档 | 一个小文本块 |
| 检索 | 一次召回一篇，粗 | 一次召回相关小块，精准 |
| Token | 大，成本高 | 小，可控 |
| 语义 | 混杂多个主题 | 相对独立完整 |

### Node 的属性

```python
from llama_index.core.schema import TextNode

node = TextNode(
    text="节点文本内容",
    node_id="custom-id",          # 可选，默认自动生成
    metadata={"department": "技术部"},
    # relationships 关系：与源 Document 或其他 Node 的关联
)
```

| 属性 | 含义 |
|------|------|
| `text` | 节点文本 |
| `node_id` | 节点唯一标识 |
| `metadata` | 节点元数据 |
| `relationships` | 节点关系（父子 / 顺序 / 来源） |

---

## 四、Node 的类型

| 类型 | 说明 | 适用 |
|------|------|------|
| **TextNode** | 文本节点（最常用） | 绝大多数文本检索 |
| **ImageNode** | 图像节点 | 多模态 / 图像档案 |
| **IndexNode** | 索引节点（可引用子索引） | 层次结构 / 文档集合的二级索引 |

> 开发中 >95% 的场景用 TextNode 即可。

---

## 五、Document → Node 关系

- **Document 是原始数据，Node 是切分产物。**
- 一个 Document 可切分为**多个 Node**。
- Node 通过 `relationships`（source / parent-child）关联回原始 Document。
- **检索返回的是 Node，而非整个 Document**；通过 Node 的关系可回溯源文档。

```
                    ┌── Node 1 (切块)
  Document ────────▶├── Node 2 (切块)
  (原始整篇)         ├── Node 3 (切块)
                    └── Node N
```

### 节点关系类型（Node Relationships）

| 关系 | 说明 |
|------|------|
| `parent-child` | 父子关系：Node 属于哪个父级（Document 或父节点） |
| `prev-next` | 顺序关系：相邻节点，保持阅读顺序 |
| `source` | 来源关系：指向源 Document |

### 手动派生示例

```python
from llama_index.core.schema import Document, TextNode

doc = Document(text="...", metadata={"file_name": "a.md"})
node = TextNode(text=doc.text, metadata=dict(doc.metadata))
node.relationships = {"source": doc.as_related_node_info()}
# 之后通过 node.relationships["source"] 可回到 doc 来源
```

---

## 数据模型设计规范

1. **metadata 尽量只放"稳定 + 可检索"的字段**（部门、类型、时间），避免放超大文本。
2. **文件来源必放**：`file_name` 或 `file_path`，便于引用与回溯源。
3. **Node 粒度由后续切分策略决定**，本章先掌握数据结构本身。
4. **自定义 node_id** 用于需要稳定引用的场景（如增量更新）。

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_document_basics.py` | Document 三种创建方式 + metadata 遍历 | 否 |
| `Code/02_node_basics.py` | TextNode 属性、node_id、从 Document 派生与 relationships | 否 |
| `Code/03_metadata_management.py` | metadata 增删改、按部门过滤、注入 Prompt | 否 |

> 本章代码全部离线可跑，聚焦数据模型本身。

---

## 关键知识点总结

### 1. Document vs Node 对比表

| 维度 | Document | Node |
|------|----------|------|
| 定位 | 原始数据单元 | 检索单元 |
| 粒度 | 整篇 | 切块 |
| 关系 | 是来源 | 属于 Document |
| 检索 | 不直接返回 | 返回对象 |

### 2. Node 属性速查

`text` / `node_id` / `metadata` / `relationships`

### 3. metadata 三大作用

展示来源 · 过滤节点 · 注入 Prompt

### 4. 节点关系类型

`parent-child` / `prev-next` / `source`

---

## 实战练习

### 练习 1：企业文档建模

用 `01_document_basics.py` 的风格，为你所在公司的 3 个不同部门（如技术部 / 财务部 / 人事部）各创建 1 个 Document，metadata 包含 `department / doc_type / author / create_time`，并遍历打印。

### 练习 2：跟踪父子关系

运行 `02_node_basics.py`，把示例里的 `relationships["source"]` 打印出来。再手动增加一个 `prev/next` 关系（两个节点间建立顺序），说明这样做的用途（例如保留阅读顺序用于长文章检索）。

### 练习 3：元数据过滤检索

用 `03_metadata_management.py` 的思路构造 6 个不同部门的 Document，编写一个函数，输入部门名返回该部门的全部文档，思考：在真实检索中，这个"过滤"动作发生在检索前（metadata filter）还是检索后（过滤结果集）更合适？为什么？

---

## 下一步

理解了 Document 与 Node 后，我们需要**真正拿到各种真实数据**。Day03 将学习数据加载——用各种 Loader / Reader 把文件、网页、API 等外部数据读成 Document。