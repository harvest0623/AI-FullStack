# Day09 - 与LangChain / LlamaIndex 集成

> 前面几天我们用 Ollama 的 REST API / SDK 直接操作模型。真实项目更常用**框架**（LangChain、LlamaIndex）来组织应用——Ollama 可作为它们的模型提供者（LLM 与 Embedding），无缝替代云端 API。今天讲清楚怎么接。

---

## 目录

- [为什么需要框架集成](#为什么需要框架集成)
- [核心概念](#核心概念)
- [今日学习目标](#今日学习目标)
- [示例项目演进](#示例项目演进)
- [每日内容详解](#每日内容详解)
- [练习与挑战](#练习与挑战)
- [运行代码](#运行代码)
- [知识点速查](#知识点速查)

---

## 为什么需要框架集成

我们在 Ollama 板块已学会"手动"调用。但要做 RAG、Agent、记忆、检索链，手写太重。LangChain 提供 `ChatOllama`/`OllamaEmbeddings`，LlamaIndex 提供 `Ollama`/`OllamaEmbedding`，一行接入本地底座，然后复用框架的编排能力。

| 能力 | 手动 | 框架集成 |
|------|------|---------|
| 对话 | 手拼 messages | ChatOllama |
| 嵌入 | 手动 embed | OllamaEmbeddings |
| RAG | 自己拼检索 | 框架管道 |
| 与云端切换 | 改代码 | 换 provider |

---

## 核心概念

- **ChatOllama**：LangChain 的 Ollama 对话模型封装，`llm.invoke()` 即可。
- **OllamaEmbeddings**：LangChain 的 Ollama 嵌入封装，`embed_query()`/`embed_documents()`。
- **Ollama pipeline**：LangChain 里靠 `prompt | llm | output_parser`。
- **LlamaIndex Ollama**：作为 LLM 与嵌入模型提供者，配合 VectorStoreIndex 做本地 RAG。
- **provider 模式**：抽象 LLM/Embedding 接口，Ollama 只是其中一个实现——想换云端就换一行。

> 本日代码以**结构讲解 + 可运行模板**为主。若你已安装 `langchain-ollama` / `llamaindex`，把接入行前的 `# [真实]` 注释打开即可走通；否则运行纯讲解文件（无需安装）。

---

## 今日学习目标

- 用 `ChatOllama` 完成一次对话
- 用 `OllamaEmbeddings` 做嵌入
- 用 LangChain 跑一个本地 RAG 最小链路
- 用 LlamaIndex 的 Ollama LLM/Embedding 建索引问答
- 理解"Ollama 当底座、框架当编排"的架构

---

## 每日内容详解

### 01 - LangChain LLM
展示 `ChatOllama` 的接入方式：模型名、`invoke`、stream，以及与 prompt 模板组合。无依赖也能跑的结构讲解版。

### 02 - LangChain 本地 RAG
用 `OllamaEmbeddings` + `Chroma`/内存向量库 + `ChatOllama` 拼一个最小 RAG 管道（文档→切块→入库→检索→生成）。

### 03 - LlamaIndex 集成
用 LlamaIndex 的 `Ollama` + `OllamaEmbedding` 建 `VectorStoreIndex`，`query_engine` 做文档问答。

### 04 - 框架对比与选择
对比 LangChain vs LlamaIndex vs 纯 Ollama，给出选型建议与切换"云端/本地"的做法。

---

## 练习与挑战

1. **接入截图**：安装 langchain-ollama，把 01 的 `[真实]` 放开跑通。
2. **本地 RAG**：用自己的手册文档跑通 02 的问答。
3. **换供应商**：把 Ollama 换成 OpenAI 入口，理解 provider 抽象。
4. **对比选型**：评估同一任务在纯 Ollama 与框架实现的工作量与生态。

---

## 运行代码

```bash
python "Day09 - 与LangChain/LlamaIndex集成/Code/01_langchain_llm.py"
python "Day09 - 与LangChain/LlamaIndex集成/Code/02_langchain_rag.py"
python "Day09 - 与LangChain/LlamaIndex集成/Code/03_llamaindex_llm.py"
python "Day09 - 与LangChain/LlamaIndex集成/Code/04_multi_framework.py"
```

> 01/04 无需额外依赖即可运行讲解；02/03 需要 `pip install langchain-ollama`（或 `llama-index-llms-ollama`），未安装时打印安装指引。

---

## 知识点速查

| 能力 | LangChain | LlamaIndex |
|------|-----------|-----------|
| 对话模型 | `ChatOllama` | `Ollama` |
| 嵌入模型 | `OllamaEmbeddings` | `OllamaEmbedding` |
| 本地 RAG | Chroma + retriever | VectorStoreIndex |
| provider 切换 | 换 `llm` 实例 | 换 `Settings.llm` |
| 生态侧重 | 通用工作流/Agent | 知识库/索引/检索 |