# Day01 - LlamaIndex 概述与环境搭建

> LlamaIndex 是当下最主流的 LLM 数据框架之一，专注解决一个核心问题：**如何让 LLM 连接、索引并查询你的私有数据**。本文档带你从零认识 LlamaIndex——它是什么、解决什么问题、生态有哪些、核心数据管道怎么走，并完成环境搭建与第一个 "Hello World" 程序。

## 学习目标

完成本章后，你将能够：

- 说出 LlamaIndex 的定义与核心定位（Connecting LLMs with Data）
- 区分 LlamaIndex 与 LangChain 的能力边界，理解二者如何互补
- 认识 LlamaIndex 生态三件套：LlamaHub / LlamaCloud / llama-deploy
- 背诵并理解核心数据管道：**Load → Parse → Index → Query**
- 掌握关键术语：Document、Node、Index、Retriever、Response、Synthesizer
- 完成 Python 环境搭建与 `.env` 的 API Key 配置
- 使用 `Settings` 全局统一配置 LLM / Embedding / 切分器
- 运行第一个 LlamaIndex 程序（数据加载 → 建索引 → 问答）

---

## 一、LlamaIndex 是什么

**LlamaIndex（原名 GPT Index）是一个数据框架（Data Framework）**，它让大语言模型（LLM）能够连接、索引并检索你的私有数据，从而基于这些数据做检索与问答。

想象你有一堆私有的企业文档、代码、数据库记录。直接用 LLM 问答，LLM 并不"知道"这些数据。LlamaIndex 就像一个**数据管道搭建工具**，帮你把数据"喂"给 LLM，并留出"召回 + 生成"的标准接口。

### 核心定位：Connecting LLMs with Data

一句话概括 LlamaIndex 的使命——**连接 LLM 与数据**。它不是一个全能 Agent 框架，而是一套把数据转化为可检索结构、再把检索结果接入 LLM 的工程化工具集。

| 它擅长做的 | 它不擅长/不重点做的 |
|-----------|-------------------|
| 数据加载（几十种格式/来源） | 复杂多步 Agent 编排（那是 LangGraph 的强项） |
| 文档切分与节点化 | 工具链与外部服务编排（LangChain 更擅长） |
| 向量索引构建与持久化 | 通用框架层面的记忆状态机 |
| 检索 + 响应合成的一站式接口 | 多 Agent 协作系统 |

> 更完整的 Agent 实现将放在后续独立板块学习，本板块聚焦 LlamaIndex 数据框架本身。

---

## 二、与 LangChain 的对比

尽管二者都会用到 LLM，但它们的设计重心不同：

| 维度 | LlamaIndex | LangChain |
|------|-----------|-----------|
| **定位** | 数据连接 / 索引 / 检索 | 工具链 / 编排 / Agent |
| **数据加载** | Loader 体系非常全面（LlamaHub 数百种） | 也有 Loaders，但相对基础 |
| **索引** | 内置多种 Index + 与向量库深度集成 | 主要依赖外接向量库，无原生索引概念 |
| **检索** | Retriever + Query Engine 开箱即用 | 需要自行用 LCEL/Chain 组装 |
| **响应合成** | 内置 Synthesizer + 多种 response_mode | 需要借助 Prompt 模板手工拼装 |
| **编排** | Workflows（事件驱动） | LCEL 表达式语言、LangGraph |
| **上手难度** | 数据检索场景极低 | 通用但需更多组装 |

**结论**：二者不是替代关系而是互补关系。做"数据驱动"的检索问答，LlamaIndex 更顺手；做"多工具调用 + 流程编排"的 Agent，LangChain/LangGraph 更合适。实践中也常将它们结合使用：例如用 LlamaIndex 做检索，接入 LangChain 的 Agent。

---

## 三、LlamaIndex 生态

- **LlamaHub**：社区集成的"应用市场"，包含数百种 Loaders（文件、数据库、网页、API 等）、Tools、Data Agent 等，可通过 `pip install llama-index-readers-xxx` 一键安装。
- **LlamaCloud**：LlamaIndex 官方托管的云服务，提供托管索引、解析、检索等服务，免去自建向量库与 API 运维。
- **llama-deploy（原名 agent-server）**：用于把 LlamaIndex 应用（尤其是 Workflows / Agent）部署为可扩展服务的基础设施框架。

---

## 四、核心数据管道（重点）

LlamaIndex 的核心心智模型是一条**四段式数据管道**：

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Load    │──▶│  Parse   │──▶│  Index   │──▶│  Query   │
│ 加载数据  │   │ 解析节点  │   │ 构建索引  │   │ 查询回答  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
  Loader/       Node Parser    VectorStore     Query
  Reader                       Index           Engine
```

| 阶段 | 组件 | 作用 | 对应章 |
|------|------|------|-------|
| **Load** 加载 | Loader / Reader | 把外部数据读为 Document | Day03 |
| **Parse** 解析 | Node Parser | 把 Document 切分为 Node | Day04 |
| **Index** 索引 | Index + VectorStore | 组织 Node，embed 供检索 | Day05 |
| **Query** 查询 | Retriever + Synthesizer | 召回相关节点并生成回答 | Day06/07/08 |

> 本板块（Day01-Day04）聚焦前两阶段的**数据模型 / 加载 / 解析**，索引与检索在后续阶段展开。

---

## 五、关键术语

| 术语 | 含义 |
|------|------|
| **Document** | 一个输入数据单元（一篇文章、一个文件、一段文本） |
| **Node** | Document 切分后的检索单元，查询的最小粒度 |
| **Index** | 组织 Node、便于检索的数据结构（如 VectorStoreIndex） |
| **Retriever** | 根据查询召回相关 Node 的组件 |
| **Response** | 最终的回答（含 answer + source_nodes 来源） |
| **Response Synthesizer** | 用召回的 Node 合成最终响应的组件 |

> 如果你有 LangChain 经验，可对应理解为：Document ≈ 你的数据块，Node ≈ 切分后的 chunk，Index ≈ 向量存储，Retriever ≈ retriever，Synthesizer ≈ 组装回答的环节。

---

## 六、安装与配置

### 6.1 环境要求

- Python 3.10+
- 至少一个 LLM API Key（OpenAI / 国内模型等）

### 6.2 安装核心包

```bash
# 核心 + 基础集成
pip install llama-index

# 常用扩展（按需）
pip install llama-index-readers-file        # 文件类加载器（PDF/Word/CSV 等）
pip install llama-index-readers-web         # 网页类加载器
pip install llama-index-llms-openai         # OpenAI LLM
pip install llama-index-embeddings-openai   # OpenAI Embedding
pip install python-dotenv pydantic           # 环境变量与数据校验
```

> `llama-index` 主包通常已包含 `llama-index-core` 与一批基础集成；额外按需再装等价 reader/llm 包。

### 6.3 配置 API Key

在项目根目录创建 `.env`：

```bash
OPENAI_API_KEY=sk-xxxx
```

代码中通过 `python-dotenv` 加载：

```python
from dotenv import load_dotenv
load_dotenv()  # 自动读取 .env
```

### 6.4 Settings 全局配置

从 LlamaIndex 0.6.x 起引入 `Settings`，集中管理全局默认组件，避免到处传参：

```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter

Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)
Settings.show_progress = True
```

配置后，凡是默认使用这些组件的操作（建索引、查询）都会自动套用，无需重复指定。

---

## 七、第一个程序流程

LlamaIndex 的 Hello World 只用三步：

```python
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex

# 1. Load：读取目录下的文档
documents = SimpleDirectoryReader("data").load_data()

# 2. Index：构建向量索引（内部自动切分 + embedding）
index = VectorStoreIndex.from_documents(documents)

# 3. Query：查询问答
response = index.as_query_engine().query("DataIQ 支持哪些文档格式？")
print(response)
print(response.source_nodes)  # 来源节点
```

对应代码见 `Code/01_hello_llama.py`，完整含自动生成示例数据与无 Key 降级处理。

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_hello_llama.py` | 第一个程序：Load→Index→Query 三步走，自动生成示例文档，无 Key 降级 | 需 Key |
| `Code/02_environment_setup.py` | 环境检查：Python 版本 / llama_index 版本 / 集成包 / API Key，生成 requirements.txt 与 .env 模板 | 否 |
| `Code/03_settings.py` | Settings 全局配置：llm / embed_model / node_parser / show_progress，并离线演示切分 | 部分 |

详细运行说明见 `Code/README.md`。

---

## 关键知识点总结

### 1. 核心数据管道四步流程图

```
Load ─→ Parse ─→ Index ─→ Query
```

### 2. 关键术语速查

| 术语 | 一句话 |
|------|-------|
| Document | 原始数据单元（text + metadata） |
| Node | 切分后的检索单元 |
| Index | 组织 Node 的结构 |
| Retriever | 按查询召回 Node |
| Response | 最终回答 |
| Synthesizer | 合成响应的组件 |

### 3. LangChain vs LlamaIndex 对比表

| 维度 | LlamaIndex | LangChain |
|------|-----------|-----------|
| 定位 | 数据连接/索引 | 工具链/编排 |
| 索引 | 原生 Index | 外接向量库 |
| 检索 | 开箱即用 | 需自行组装 |
| 用途 | 检索问答 | Agent/编排 |

### 4. 安装清单

```bash
pip install llama-index python-dotenv pydantic
```

---

## 实战练习

### 练习 1：跑通环境与 Hello World

1. 运行 `Code/02_environment_setup.py`，检查你的环境是否合格；
2. 配置 `.env` 的 API Key 后，运行 `Code/01_hello_llama.py`，观察 Load / Index / Query 三段输出。
3. 换一个问题（例如"DataIQ 有哪些核心功能？"）再次查询，观察回答是否变化、来源节点是否对应。

### 练习 2：观察 Settings 生效效果

运行 `Code/03_settings.py`，观察配置前（默认类型）与配置后（你指定的模型与切分参数）的差异。尝试把 `chunk_size` 改成 128 再运行切分演示，看切出的 Node 数量与长度如何变化。

### 练习 3：认识生态与对比

- 打开 [LlamaHub](https://llamahub.ai/)，找出 3 个你可能用到的 Loader（如 Notion、Postgres、网页）。
- 用一张表整理"同样的文档问答任务，LlamaIndex 与 LangChain 各自需要的核心组件"，体会二者侧重点的不同。

---

## 下一步

环境已就绪，数据管道心智模型已建立。Day02 将深入数据模型，理解 LlamaIndex 处理数据的**两级基本单元**——`Document` 与 `Node`，这是后续所有操作的地基。