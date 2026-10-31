# Day02 - 基础RAG流程（朴素 RAG）

> 这是 RAG 的"Hello World"。今天我们亲手跑通一条**完整的朴素 RAG 管道**：加载文档 → 切块 → 嵌入 → 入库 → 检索 → 生成。先在 LangChain 与 LlamaIndex 双框架下各实现一遍，把整体骨架刻进脑子里，后面每天的优化都是在替换其中某一环。

## 学习目标

完成本章后，你将能够：

- 说出朴素 RAG 的完整三步流程（Indexing / Retrieval / Generation）
- 用 LangChain 实现一条可运行的朴素 RAG
- 用 LlamaIndex 实现等价流程，并对照理解通用本质
- 查看检索返回的"上下文"，理解 Top-K 与相似度
- 理解检索结果如何被"注入 Prompt"再生成

---

## 一、朴素 RAG 的三步流程

朴素 RAG（Naive RAG）是 RAG 最基础的形态，分三步：

```
① Indexing（索引）                ② Retrieval（检索）       ③ Generation（生成）
加载文档 ─▶ 切块 ─▶ 嵌入 ─▶ 入库    查询嵌入 → 相似度检索 TopK   上下文 + 问题 → LLM
(Load)  (Chunk) (Embed)(Store)    (Query-Embed)(Search)      (Augment)(Generate)
```

| 步骤 | 动作 | 输入 | 输出 |
|------|------|------|------|
| **Indexing** | 离线准备 | 原始文档 | 可检索的向量索引 |
| **Retrieval** | 在线查询 | 用户问题 | 相关文档块 Top-K |
| **Generation** | 在线生成 | 问题+上下文 | 最终回答 |

关键点：**Indexing 是离线的（跑一次），Retrieval+Generation 是在线的（每次问答都触发）**。

---

## 二、用 LangChain 实现朴素 RAG

LangChain 把 RAG 拆成可组合的组件。核心链路：

```
Loader(加载) → Splitter(切块) → Embeddings(嵌入) → VectorStore(入库)
                ↑                                              ↓
              QA Chain(生成)  ←  Prompt(注入) ← Retriever(检索) ← 客户端查询
```

最小实现骨架：

```python
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

# ① 加载 + 切块
docs = TextLoader("data.txt").load()
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
chunks = splitter.split_documents(docs)

# ② 嵌入 + 入库
vectorstore = FAISS.from_documents(chunks, OpenAIEmbeddings())

# ③ 检索 + 生成
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
prompt = ChatPromptTemplate.from_template("依据以下资料：{context}\n回答：{question}")
# ...用 LCEL 把 retriever + prompt + model 串成链
```

> 每个组件都可以独立替换——这正是"组件化"的意义，也是后续每天优化的入口。

---

## 三、用 LlamaIndex 实现朴素 RAG

LlamaIndex 同样强调"数据管道"，但 API 更"一站式"：

```python
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex

# 加载文档（自动切块 + 嵌入 + 入库一步到位）
documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)

# 直接得到查询引擎（检索 + 生成封装）
query_engine = index.as_query_engine()
answer = query_engine.query("我们的报销标准是什么？")
```

LlamaIndex 把很多默认行为内置（默认切块器、默认嵌入），上手更快；LangChain 组件更"显式可组合"。**两者背后是同一套 RAG 思想**，搞清楚通用本质比记 API 更重要。

---

## 四、检索返回的是什么 -- 理解 Top-K 与来源

无论哪个框架，检索都返回 **Top-K 个相关文档块**，每个块带一个**相似度得分（score）**。理解这点至关重要：

```python
# LangChain
hits = retriever.invoke("报销标准")
for hit in hits:
    print(hit.page_content)      # 命中的文本
    print(hit.metadata)         # 来源元数据（文件名等）

# LlamaIndex
retriever = index.as_retriever(similarity_top_k=3)
for nw in retriever.retrieve("报销标准"):
    print(nw.node.text, nw.score)
```

**为什么检索结果重要**：RAG 的答案质量天花板 = 召回质量 × 生成质量。**如果检索返回的上下文不对，再强的模型也答不对。** 所以排障时先看检索结果（Day10 会系统讲评估）。

---

## 五、上下文如何"注入"Prompt

检索到上下文后，要把它拼进 Prompt 再交还给 LLM。典型的生成 Prompt 设计：

```
你是 DataIQ 企业知识库助手。请**只依据**下面的资料回答问题，
资料中没有的内容请如实说不知道。回答时标注出处。

=== 检索到的资料 ===
[来自《报销制度》] 差旅报销需在出差结束后5个工作日内提交…
[来自《差旅标准》] 住宿每天上限500元…

=== 问题 ===
我出差住四星级酒店一天800，能报销吗？
```

关键约束：**"只依据资料""不编造""说出处"** 三条指令能大幅降低幻觉（Day10 会用指标验证）。

---

## 六、朴素 RAG 的局限（为后续铺垫）

朴素 RAG 虽能跑通，但质量不稳，常见局限与对应优化：

| 局限 | 表现 | 后续优化 Day |
|------|------|-------------|
| 切块策略粗糙 | 语义被切碎 | Day03 多样切块策略 |
| 嵌入选择随意 | 相似度不准 | Day04 嵌入模型选择 |
| TopK 固定 | 召回过度/不足 | Day05 参数与过滤 |
| 召回质量不稳 | Top1 不精准 | Day06 重排 |
| 口语化查询 | 检索不到 | Day07 查询改写 |
| 单一向量召回 | 关键词场景漏检 | Day08 混合检索 |

> 记住一句话：**朴素 RAG 是"能用"，但不是"好用"**。今天先跑通骨架，接下来逐环优化。

---

## 场景：DataIQ 第一步朴素 RAG

为 DataIQ 写几份 Markdown 制度文档放入 `data/`，用朴素 RAG 让员工能提问并得到带依据的回答。今天的目标是"能答"，从 Day03 起追求"答得好"。

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_naive_rag_langchain.py` | LangChain 朴素 RAG 完整实现 | 是（嵌入+LLM，可降级） |
| `Code/02_naive_rag_llama.py` | LlamaIndex 朴素 RAG 完整实现 | 是（可降级） |
| `Code/03_retrieval_inspect.py` | 查看检索返回的 TopK 与来源 | 是（仅嵌入） |
| `Code/README.md` | 运行说明 | - |

---

## 关键知识点总结

1. **三步流程**：Indexing → Retrieval → Generation。
2. **离线 vs 在线**：索引离线跑一次，检索+生成在线每次触发。
3. **双框架同源**：LangChain 组件式、LlamaIndex 一站式，思想一致。
4. **Top-K + score**：检索返回带得分的文档块。
5. **答案质量 = 召回 × 生成**：先看检索，再优化生成。

---

## 实战练习

### 练习 1：搭建迷你知识库

在 `data/` 建 3 份制度文档（如《报销规则》《年假规则》《支付规则》），运行朴素 RAG，让员工用自然语言提问至少 5 个问题。

### 练习 2：观察检索结果

运行 `03_retrieval_inspect.py`，对同一个问题把 `k` 分别设为 1 / 3 / 5，观察召回内容与得分变化，思考：什么情况下 k 太小会漏信息？k 太大会引入噪音？

### 练习 3：约束 Prompt 对比

用同一个问题，分别用"严格只依据资料 + 说出处"和"自由发挥"两版 Prompt 提问，比较回答的事实性与幻觉程度，记录差异。

### 练习 4：双框架对照

同时运行 LangChain 与 LlamaIndex 两个版本，用同一文档同一问题，对比回答质量与代码结构，体会两种框架的设计理念差异。

---

## 下一步

跑通朴素 RAG 后，你会发现**切块是影响质量的第一道关口**。Day03 专门攻克文本切块——这是"一块内容切坏了，后面全废"的关键环节。