# LangChain 框架学习指南

> 系统化掌握 LangChain 框架核心组件，为构建 LLM 应用打下坚实的工程化基础

> 共 12 天，覆盖从环境搭建、Model I/O、Prompt 管理、Output Parsers、Chains (LCEL)、Memory 到 Document Loaders、Retrievers、Tools、LangServe/LangGraph 的完整框架知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [示例项目](#示例项目)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是全栈学习系列的 **LLM 应用框架核心**。LangChain 是当前最流行的 LLM 应用开发框架——它将 LLM 调用、Prompt 管理、输出解析、链式组合、记忆管理、文档处理、检索增强等能力封装为可组合的模块化组件，让开发者能像搭积木一样构建复杂的 LLM 应用。

**与 LLM 板块的关系**：LLM 板块教你"如何直接调用 LLM API"，本板块教你"如何用 LangChain 框架编排 LLM 应用"——从手动管理 API 调用升级为组件化、可组合、可维护的框架化开发。

**与后续板块的关系**：本板块聚焦 LangChain 框架本身的组件和用法。RAG（检索增强生成）和 Agent（智能体）作为 LangChain 的重要应用场景，将有独立的板块深入讲解其架构设计和完整实现。本板块在 Day07-Day09 会涉及 Retrievers 和 Tools 的基础用法，为后续板块铺垫但不深入。

**学习目标**：完成本板块后，你应能：
- 理解 LangChain 的架构设计和核心概念
- 熟练使用 Model I/O 层（LLM/ChatModel/Embedding 模型接口）
- 掌握 PromptTemplate 和 ChatPromptTemplate 的模板管理
- 使用 Output Parsers 将 LLM 输出解析为结构化数据
- 熟练运用 LCEL (LangChain Expression Language) 构建链式调用
- 管理多轮对话记忆（ConversationBufferMemory / Summary / Window）
- 使用 Document Loaders 加载多种格式文档
- 使用 Text Splitters 进行文档分割
- 构建 Retriever 进行语义检索
- 定义和使用 Tools 实现 Tool Calling
- 使用 Callbacks 和 Streaming 处理流式输出
- 了解 LangServe 和 LangGraph 的基础用法
- 将 LangChain 应用部署到生产环境

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 Python 代码 + 实战练习
- 全程围绕统一的**智能问答助手 `ChainQA`** 项目展开
- 所有 Python 代码基于 LangChain 0.3+ (最新稳定版)，可在 Python 3.10+ 直接运行
- 紧扣框架化视角，为后续 RAG / Agent 板块铺垫

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| Python | 必须 | 异步/类/装饰器/类型注解 |
| LLM 基础 | 已完成 LLM 板块更好 | 理解 API 调用/Token/Embedding |
| Prompt 基础 | 已完成 Prompt 板块更好 | 理解 System/User/Assistant 角色 |
| pip 包管理 | 基础 | 能安装和管理 Python 依赖 |

**环境准备**：
- Python 3.10+
- 至少一个 LLM API Key（OpenAI / Anthropic / 国内模型均可）
- 代码编辑器：VS Code

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                  LangChain 学习路线（12天）                      │
└─────────────────────────────────────────────────────────────────┘

阶段一：基础与核心（Day01-Day04）
┌──────────┬──────────┬──────────┬──────────┐
│ Day01    │ Day02    │ Day03    │ Day04    │
│ 概述与   │ Model I/O│ Prompt   │ Output   │
│ 环境搭建 │ 模型接口  │ 管理     │ Parsers  │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
阶段二：组合与管理（Day05-Day07）
┌──────────┬──────────┬──────────┐
│ Day05    │ Day06    │ Day07    │
│ Chains   │ Memory   │ Document │
│ LCEL链式 │ 记忆管理  │ Loaders  │
└────┬─────┴────┬─────┴────┬─────┘
     │          │          │
     ▼          ▼          ▼
阶段三：检索与工具（Day08-Day10）
┌──────────┬──────────┬──────────┐
│ Day08    │ Day09    │ Day10    │
│ Retriever│ Tools    │ Callbacks│
│ 检索器   │ 工具调用  │ 流式回调  │
└────┬─────┴────┬─────┴────┬─────┘
     │          │          │
     ▼          ▼          ▼
阶段四：服务化与部署（Day11-Day12）
┌──────────────────┬──────────────────┐
│ Day11            │ Day12            │
│ LangServe        │ 生产部署          │
│ LangGraph 基础   │ 最佳实践          │
└──────────────────┴──────────────────┘
```

---

## 示例项目

本板块全程围绕一个**智能问答助手 `ChainQA`** 展开，逐步用 LangChain 组件构建完整的问答系统。

### 项目结构

```
chainqa/
├── pyproject.toml
├── src/
│   └── chainqa/
│       ├── __init__.py
│       ├── config.py                ← 配置管理
│       ├── models.py                ← 模型实例（LLM/ChatModel/Embedding）
│       ├── prompts/                  ← Prompt 模板
│       │   ├── chat_prompt.py        ← 对话模板
│       │   ├── qa_prompt.py          ← 问答模板
│       │   └── summary_prompt.py     ← 摘要模板
│       ├── parsers/                  ← 输出解析器
│       │   ├── json_parser.py        ← JSON 解析
│       │   └── list_parser.py        ← 列表解析
│       ├── chains/                   ← 链式调用
│       │   ├── qa_chain.py           ← 问答链
│       │   ├── summary_chain.py      ← 摘要链
│       │   └── extraction_chain.py   ← 信息抽取链
│       ├── memory/                   ← 记忆管理
│       │   └── conversation.py       ← 对话记忆
│       ├── loaders/                   ← 文档加载
│       │   └── document_loader.py    ← 多格式加载器
│       ├── retrieval/                ← 检索器
│       │   └── vector_store.py       ← 向量存储与检索
│       ├── tools/                    ← 工具定义
│       │   └── search_tools.py       ← 搜索工具
│       └── server/                   ← 服务化
│           └── api.py                ← LangServe API
├── tests/
└── data/                             ← 示例文档数据
```

> 各天的代码围绕这个项目逐步构建，从基础调用到服务化部署完整演进。

---

## 每日内容详表

### 阶段一：基础与核心

#### Day01 - LangChain概述与环境搭建
- **核心**：LangChain 定义与发展历程、LangChain 生态系统（LangChain / LangServe / LangSmith / LangGraph）、核心概念（Components / Chains / Agents / Memory / Retrievers / Callbacks）、架构设计理念（组合性 Composability / 可扩展性 / 模块化）、LangChain 0.3 版本特性、环境搭建（pip install langchain / langchain-openai / langchain-community）、项目结构设计、第一个 LangChain 程序、与直接调用 API 的对比
- **代码**：`01_hello_langchain.py`（第一个 LangChain 程序）/ `02_environment_setup.py`（环境检查与配置）/ `03_project_structure.py`（项目脚手架生成）/ `README.md`（环境搭建指南）
- **重点**：理解 LangChain 的模块化架构、环境搭建

#### Day02 - Model I/O模型接口层
- **核心**：Model I/O 概念（输入 Prompt → 调用模型 → 解析输出）、LLM vs ChatModel 区别（LLM: 纯文本输入输出 / ChatModel: 消息角色体系）、`ChatOpenAI` / `ChatAnthropic` / `ChatOllama` / `ChatTongyi` 模型实例化、模型参数配置（temperature / max_tokens / model / streaming / timeout）、`.invoke()` / `.batch()` / `.async()` 三种调用方式、`.stream()` 流式输出、模型绑定参数（`.bind()` / `.bind_tools()`）、多模型统一接口设计、模型切换与回退（with_fallbacks）、速率限制配置
- **代码**：`01_chat_models.py`（ChatModel 实例化与调用）/ `02_llm_models.py`（LLM 实例化与调用）/ `03_invoke_batch_async.py`（三种调用方式对比）/ `04_model_config.py`（模型配置与回退）/ `README.md`（Model I/O 指南）
- **重点**：ChatModel 的三种调用方式、模型回退机制

#### Day03 - Prompt管理
- **核心**：PromptTemplate 基础（模板字符串 + 变量插值）、`PromptTemplate.from_template()` / `PromptTemplate(template=, input_variables=)`、模板变量验证、ChatPromptTemplate（多角色消息模板）、`ChatPromptTemplate.from_messages()` / `from_template()`、消息类型（SystemMessage / HumanMessage / AIMessage）、`MessagesPlaceholder`（动态消息列表占位）、模板组合与嵌套、模板序列化（JSON/YAML 文件加载）、PromptHub（Prompt 共享市场）、与 LLM 板块 Prompt 工程化的衔接
- **代码**：`01_prompt_template.py`（PromptTemplate 基础）/ `02_chat_prompt_template.py`（ChatPromptTemplate 多角色）/ `03_messages_placeholder.py`（动态消息占位）/ `04_templateSerialization.py`（模板序列化与文件加载）/ `README.md`（Prompt 管理指南）
- **重点**：ChatPromptTemplate 多角色模板、MessagesPlaceholder

#### Day04 - Output Parsers输出解析器
- **核心**：Output Parsers 概念（将 LLM 自由文本输出解析为结构化数据）、StrOutputParser（纯文本输出）、JsonOutputParser（JSON 解析 + Schema 约束）、PydanticOutputParser（Pydantic 模型解析）、CommaSeparatedListOutputParser（逗号分隔列表）、DatetimeOutputParser（日期解析）、EnumOutputParser（枚举解析）、自定义 Output Parser（继承 BaseOutputParser）、解析错误处理（自动重试 + 修复 Prompt）、`get_format_instructions()` 自动生成格式说明、Parser 与 Chain 的配合
- **代码**：`01_str_json_parser.py`（字符串与 JSON 解析）/ `02_pydantic_parser.py`（Pydantic 模型解析）/ `03_list_parser.py`（列表与枚举解析）/ `04_custom_parser.py`（自定义解析器 + 错误重试）/ `README.md`（Output Parsers 指南）
- **重点**：PydanticOutputParser、自定义解析器与错误重试

---

### 阶段二：组合与管理

#### Day05 - Chains链式调用与LCEL
- **核心**：Chain 概念（将多个组件串联执行）、Legacy Chains（LLMChain / SequentialChain / TransformChain，已废弃但需了解）、LCEL (LangChain Expression Language) 核心概念（管道符 `|` 组合组件）、LCEL 基本语法（`prompt | model | parser`）、RunnablePassthrough（传递输入）、RunnableParallel（并行执行）、RunnableLambda（自定义函数包装）、RunnableBranch（条件分支）、RunnableEach（批量处理）、链式调用进阶（多步骤管道 / 并行 + 串行混合）、Runnable 接口统一性（invoke/batch/stream/ainvoke）、链的可视化（get_graph / draw）、错误处理与重试
- **代码**：`01_lcel_basics.py`（LCEL 基础语法）/ `02_runnable_components.py`（RunnablePassthrough/Parallel/Lambda）/ `03_chain_patterns.py`（链式模式：顺序/并行/分支）/ `04_advanced_chains.py`（复杂多步链）/ `README.md`（LCEL 完全指南）
- **重点**：LCEL 管道语法、RunnableParallel、条件分支

#### Day06 - Memory对话记忆管理
- **核心**：Memory 概念（管理多轮对话的上下文历史）、ConversationBufferMemory（全量保留对话历史）、ConversationBufferWindowMemory（滑动窗口，保留最近 K 轮）、ConversationSummaryMemory（摘要压缩旧对话）、ConversationSummaryBufferMemory（摘要 + 缓冲，Token 预算管理）、ConversationTokenBufferMemory（按 Token 数管理）、Memory 与 ChatModel 的配合方式、Memory 在 LCEL 中的使用（RunnableWithMessageHistory）、多会话记忆管理（session_id 区分）、记忆持久化（保存到数据库/文件）、记忆策略对比与选择
- **代码**：`01_buffer_memory.py`（全量与窗口记忆）/ `02_summary_memory.py`（摘要记忆策略）/ `03_token_buffer.py`（Token 预算管理）/ `04_session_memory.py`（多会话记忆 + 持久化）/ `README.md`（Memory 管理指南）
- **重点**：RunnableWithMessageHistory、多会话管理、策略选择

#### Day07 - Document Loaders与Text Splitters
- **核心**：Document 概念（page_content + metadata）、Document Loaders 分类（文件/网页/数据库/云存储）、TextLoader / CSVLoader / JSONLoader / PDFLoader / MarkdownLoader、WebBaseLoader / ArxivLoader / GitLoader、DirectoryLoader（批量加载）、Text Splitters 概念（将长文档分割为可处理的块）、RecursiveCharacterTextSplitter（递归字符分割，最常用）、CharacterTextSplitter（固定字符分割）、TokenTextSplitter（按 Token 分割）、MarkdownHeaderTextSplitter / HTMLHeaderTextSplitter（按结构分割）、分割参数调优（chunk_size / chunk_overlap）、代码分割器（RecursiveCharacterTextSplitter with language）、Document Transformer（重排/过滤/翻译）
- **代码**：`01_document_loaders.py`（多种格式文档加载）/ `02_web_loaders.py`（网页与在线文档加载）/ `03_text_splitters.py`（多种分割器对比）/ `04_splitter_tuning.py`（分割参数调优与对比）/ `README.md`（Document Loaders 指南）
- **重点**：RecursiveCharacterTextSplitter、分割参数调优

---

### 阶段三：检索与工具

#### Day08 - Retrievers检索器基础
- **核心**：Retriever 概念（根据查询返回相关文档）、VectorStore 向量存储（Chroma / FAISS / Pinecone / Milvus）、Embedding 模型配置（OpenAIEmbeddings / HuggingFaceEmbeddings）、从文档到向量存储的流程（Load → Split → Embed → Store）、VectorStoreRetriever（向量检索）、相似度搜索 vs MMR 搜索（最大边际相关性）、多查询检索（MultiQueryRetriever）、上下文压缩检索（ContextualCompressionRetriever）、重排序检索（Re-ranking）、自查询检索（SelfQueryRetriever）、检索器与 Chain 的集成（RunnablePassthrough 传递检索结果）、检索质量评估
- **代码**：`01_vector_store.py`（向量存储创建与搜索）/ `02_retrievers.py`（多种 Retriever 对比）/ `03_mmr_search.py`（MMR 搜索实现）/ `04_retrieval_chain.py`（检索器与 Chain 集成）/ `README.md`（Retrievers 基础指南）
- **重点**：VectorStore 创建流程、MMR 搜索、检索链集成

#### Day09 - Tools与Tool Calling工具调用
- **核心**：Tool 概念（让 LLM 调用外部函数/API）、LangChain Tool 定义方式（@tool 装饰器 / Tool 类 / StructuredTool）、Tool 参数 Schema（Pydantic 模型定义参数）、`.bind_tools()` 绑定工具到模型、Tool Calling 流程（模型决定调用工具 → 执行工具 → 返回结果 → 模型生成最终回复）、ToolMessage 消息类型、内置工具集（搜索/计算器/Python REPL/Wikipedia）、自定义工具实践（天气查询/数据库查询/API调用）、多工具选择策略、Tool 错误处理、工具调用与 Chain 的集成（ToolCallingChain）、与 Agent 的关系（Agent = LLM + Tools + 循环）
- **代码**：`01_define_tools.py`（多种工具定义方式）/ `02_tool_calling.py`（工具调用完整流程）/ `03_builtin_tools.py`（内置工具使用）/ `04_custom_tools.py`（自定义工具 + Chain 集成）/ `README.md`（Tool Calling 指南）
- **重点**：@tool 装饰器、Tool Calling 完整流程、Tool 与 Chain 集成

#### Day10 - Callbacks与Streaming回调流式
- **核心**：Callbacks 概念（在 Chain 执行各阶段插入自定义逻辑）、BaseCallbackHandler 基类、回调方法（on_llm_start / on_llm_new_token / on_llm_end / on_chain_start / on_chain_end / on_tool_start / on_tool_end / on_error）、内置 Callback（StdOutCallbackHandler / FileCallbackHandler）、自定义 Callback Handler（日志记录 / 指标采集 / 通知）、Streaming 流式输出（.stream() / astream()）、流式输出中的 Token 处理、Callback 在 Chain 中的配置方式（config={"callbacks": [...]}）、LangSmith 追踪集成（回调自动上报）、异步 Callback（AsyncCallbackHandler）
- **代码**：`01_callback_handler.py`（自定义 Callback Handler）/ `02_streaming_output.py`（流式输出实现）/ `03_logging_callback.py`（日志与指标采集 Callback）/ `04_langsmith_trace.py`（LangSmith 追踪集成）/ `README.md`（Callbacks 与 Streaming 指南）
- **重点**：自定义 Callback Handler、流式输出、LangSmith 集成

---

### 阶段四：服务化与部署

#### Day11 - LangServe与LangGraph基础
- **核心**：LangServe 概念（将 LangChain 应用部署为 REST API）、FastAPI + LangServe 集成、`add_routes()` 注册 Chain 为 API 端点、API 端点自动生成（/invoke / /batch / /stream / /input_schema / /output_schema）、LangServe Playground（在线调试界面）、自定义 API 端点、LangGraph 概念（状态图 StateGraph）、LangGraph 核心概念（State / Node / Edge / Conditional Edge）、LangGraph vs LangChain Chains（图 vs 链）、简单 StateGraph 构建（定义状态→创建节点→添加边→编译→执行）、LangGraph 基础应用场景预览（循环/分支/人工干预）
- **代码**：`01_langserve_basic.py`（LangServe 基础 API 部署）/ `02_langserve_playground.py`（Playground 与自定义端点）/ `03_langgraph_basics.py`（LangGraph StateGraph 基础）/ `04_langgraph_advanced.py`（LangGraph 条件分支与循环）/ `README.md`（LangServe/LangGraph 指南）
- **重点**：LangServe API 部署、LangGraph StateGraph 基础

#### Day12 - 生产部署与最佳实践
- **核心**：LangChain 生产架构设计（API 层 / Chain 层 / 模型层 / 缓存层 / 监控层）、性能优化（模型缓存 set_llm_cache / 语义缓存 / 批量处理 / 异步并发）、成本控制（模型路由 / Token 优化 / 缓存策略）、错误处理与重试（with_retry / 指数退避 / 降级策略）、配置管理（环境变量 / .env / 配置类）、日志与监控（LangSmith 追踪 / 自定义指标 / 告警）、Docker 容器化部署（Dockerfile / docker-compose）、CI/CD（Prompt 版本管理 / 自动化测试 / 灰度发布）、LangChain 版本升级策略（0.1→0.2→0.3 迁移指南）、最佳实践总结（组件设计 / Prompt 管理 / 错误处理 / 测试 / 部署 / 监控）
- **代码**：`01_production_architecture.py`（生产架构设计与实现）/ `02_caching_retry.py`（缓存与重试机制）/ `03_docker_deploy.py`（Docker 部署配置生成）/ `04_best_practices.py`（最佳实践综合示例）/ `README.md`（生产部署完整指南）
- **重点**：生产架构设计、缓存与重试、LangSmith 监控

---

## 目录结构

```
LangChain/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - LangChain概述与环境搭建/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天 Python 代码
│       ├── 01_hello_langchain.py
│       ├── 02_environment_setup.py
│       ├── 03_project_structure.py
│       └── README.md
├── Day02 - Model I/O模型接口层/
│   ├── README.md
│   └── Code/
│       ├── 01_chat_models.py
│       ├── 02_llm_models.py
│       ├── 03_invoke_batch_async.py
│       ├── 04_model_config.py
│       └── README.md
├── ...（Day03-Day11 同构）...
└── Day12 - 生产部署与最佳实践/
    ├── README.md
    └── Code/
        ├── 01_production_architecture.py
        ├── 02_caching_retry.py
        ├── 03_docker_deploy.py
        ├── 04_best_practices.py
        └── README.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，均为 `.py` 文件（可直接 `python file.py` 运行）
- 部分天数含配置文件（`.yaml` / `.json` / `Dockerfile` / `requirements.txt`）

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-6 小时 | 约 2-3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 4-5 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **先理解组件再组合**：每天先理解单个组件，再思考如何组合
2. **实际运行代码**：所有代码需真实运行，不要只看不动手
3. **对比原生 API**：对比 LangChain 封装 vs 直接调用 API 的差异
4. **关注 LCEL**：LCEL 是 LangChain 0.3 的核心，务必熟练掌握
5. **逐步构建项目**：随学习推进完善 `ChainQA` 智能问答助手
6. **查阅官方文档**：LangChain 更新快，以官方文档为准

### 阶段性检查点

- **阶段一完成后**：能否用 LangChain 完成模型调用→Prompt 管理→输出解析的完整流程？
- **阶段二完成后**：能否用 LCEL 构建复杂链式调用、管理多轮对话记忆、加载和分割文档？
- **阶段三完成后**：能否构建向量检索链、定义和使用工具、处理流式输出和回调？
- **阶段四完成后**：能否用 LangServe 部署 API、用 LangGraph 构建状态图、进行生产部署？

---

## 如何运行代码

### 环境准备

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 安装核心依赖
pip install langchain langchain-openai langchain-community
pip install python-dotenv pydantic

# 可选：其他模型 SDK
pip install langchain-anthropic    # Claude
pip install langchain-google-genai # Gemini
```

### 配置 API Key

```bash
# 创建 .env 文件
cat > .env << 'EOF'
OPENAI_API_KEY=sk-xxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
EOF
```

### 运行示例

```bash
# 运行指定天数的代码
python "Day01 - LangChain概述与环境搭建/Code/01_hello_langchain.py"

# 运行 LCEL 链式调用示例
python "Day05 - Chains链式调用与LCEL/Code/01_lcel_basics.py"

# 启动 LangServe API 服务
pip install fastapi uvicorn
uvicorn "Day11 - LangServe与LangGraph基础/Code/01_langserve_basic:app" --reload
```

### 使用 Docker 运行

```bash
docker run -it --rm \
  -v "$(pwd):/workspace" -w /workspace \
  --env-file .env \
  python:3.12-slim \
  pip install langchain langchain-openai && \
  python "Day02 - Model I/O模型接口层/Code/01_chat_models.py"
```

---

## 知识点速查

### LangChain 核心组件速查

| 组件 | 作用 | 关键类/函数 | 对应天数 |
|------|------|------------|---------|
| Model I/O | 调用 LLM | ChatOpenAI / ChatAnthropic | Day02 |
| Prompts | 管理 Prompt 模板 | PromptTemplate / ChatPromptTemplate | Day03 |
| Output Parsers | 解析 LLM 输出 | StrOutputParser / PydanticOutputParser | Day04 |
| Chains (LCEL) | 组合组件执行 | 管道符 `\|` / RunnablePassthrough | Day05 |
| Memory | 管理对话历史 | ConversationBufferMemory / RunnableWithMessageHistory | Day06 |
| Document Loaders | 加载文档 | TextLoader / PDFLoader / WebBaseLoader | Day07 |
| Text Splitters | 分割文档 | RecursiveCharacterTextSplitter | Day07 |
| Retrievers | 检索相关文档 | VectorStoreRetriever / MultiQueryRetriever | Day08 |
| Tools | 定义可调用工具 | @tool / StructuredTool / .bind_tools() | Day09 |
| Callbacks | 执行过程回调 | BaseCallbackHandler / StdOutCallbackHandler | Day10 |
| LangServe | 部署为 API | add_routes() / FastAPI | Day11 |
| LangGraph | 状态图编排 | StateGraph / Node / Edge | Day11 |

### LCEL Runnable 接口速查

| 方法 | 说明 | 同步/异步 |
|------|------|----------|
| `.invoke(input)` | 单次调用 | 同步 |
| `.batch(inputs)` | 批量调用 | 同步 |
| `.stream(input)` | 流式输出 | 同步 |
| `.ainvoke(input)` | 单次调用 | 异步 |
| `.abatch(inputs)` | 批量调用 | 异步 |
| `.astream(input)` | 流式输出 | 异步 |

### LCEL 核心组件速查

| 组件 | 作用 | 示例 |
|------|------|------|
| `prompt \| model \| parser` | 基本管道 | ChatPrompt → ChatModel → OutputParser |
| `RunnablePassthrough` | 传递原始输入 | 保留查询原文同时检索文档 |
| `RunnableParallel` | 并行执行 | 同时执行检索和问题重写 |
| `RunnableLambda` | 包装自定义函数 | 将普通 Python 函数转为 Runnable |
| `RunnableBranch` | 条件分支 | 根据输入类型选择不同处理链 |
| `RunnableEach` | 批量处理 | 对列表中每个元素执行同一链 |

### Memory 策略对比速查

| 策略 | 原理 | Token 消耗 | 信息保留 | 适用场景 |
|------|------|-----------|---------|---------|
| BufferMemory | 全量保留 | 线性增长 | 最好 | 短对话 |
| BufferWindowMemory | 保留最近 K 轮 | 固定上限 | 最近好/旧丢失 | 中等对话 |
| SummaryMemory | 摘要旧对话 | 增长缓慢 | 压缩摘要 | 长对话 |
| SummaryBufferMemory | 摘要+缓冲 | 预算可控 | 平衡 | 长对话 |
| TokenBufferMemory | 按 Token 管理 | Token 上限 | 平衡 | 精确控制 |

### Document Loaders 速查

| Loader | 格式 | 安装依赖 | 说明 |
|--------|------|---------|------|
| TextLoader | .txt | 无 | 纯文本 |
| CSVLoader | .csv | 无 | CSV 表格 |
| JSONLoader | .json | 无 | JSON 数据 |
| PyPDFLoader | .pdf | pypdf | PDF 文档 |
| UnstructuredMarkdownLoader | .md | unstructured | Markdown |
| WebBaseLoader | 网页 | beautifulsoup4 | 网页内容 |
| ArxivLoader | 论文 | arxiv | arXiv 论文 |
| DirectoryLoader | 目录 | 取决于文件类型 | 批量加载 |

### Text Splitters 速查

| Splitter | 分割方式 | 适用场景 | 参数 |
|----------|---------|---------|------|
| RecursiveCharacterTextSplitter | 递归字符分割 | 通用首选 | chunk_size / chunk_overlap |
| CharacterTextSplitter | 固定字符 | 简单文本 | separator / chunk_size |
| TokenTextSplitter | 按 Token | 精确 Token 控制 | chunk_overlap |
| MarkdownHeaderTextSplitter | 按 Markdown 标题 | Markdown 文档 | 标题层级 |
| HTMLHeaderTextSplitter | 按 HTML 标签 | 网页内容 | 标签选择 |
| Language 代码分割器 | 按代码语法 | 代码文档 | language 参数 |

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **RAG** | 基于 LangChain 的 Retrievers + Document Loaders 构建完整 RAG 系统 |
| **Agent** | 基于 LangChain 的 Tools + LangGraph 构建智能 Agent |
| **LLM** | 本板块的模型调用基础 |
| **Prompt** | 本板块的 Prompt 设计基础 |
| **Python** | 本板块的编程语言基础 |
| **FastAPI / Flask** | LangServe 基于 FastAPI |
| **Docker** | LangChain 应用容器化部署 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [LangChain 官方文档](https://python.langchain.com/docs/) - Python 版官方文档
- [LangChain API 参考](https://api.python.langchain.com/) - 完整 API 参考
- [LangChain GitHub](https://github.com/langchain-ai/langchain) - 源码与 Issues
- [LangSmith 文档](https://docs.smith.langchain.com/) - 追踪与评估平台
- [LangServe 文档](https://github.com/langchain-ai/langserve) - API 部署
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/) - 状态图编排
- [LangChain 示例库](https://github.com/langchain-ai/langchain/tree/master/cookbook) - 官方示例

---

## 贡献与反馈

> 本学习手册为原创内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用 LangChain 构建强大的 LLM 应用！**