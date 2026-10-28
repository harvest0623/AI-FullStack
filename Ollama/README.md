# Ollama 学习指南

> 系统化掌握 Ollama：从本地部署、模型管理、HTTP API、Python SDK，到推理参数调优、上下文管理、嵌入与向量、工具调用，再到与 LangChain/LlamaIndex 集成和综合实战，构建完全本地的 AI 应用

> 共 10 天，聚焦 Ollama 本身的安装、使用、编程与调优，是"在本地跑 LLM/嵌入模型"的工程层基础

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [为什么用 Ollama](#为什么用-ollama)
- [学习路线图](#学习路线图)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

**Ollama** 是一个本地运行大语言模型（LLM）和嵌入模型（Embedding）的工具，一条命令即可把开源模型跑在自己的电脑上，并提供兼容 OpenAI 的 REST API。

**与 LLM 板块的关系**：此前学习的是"调用云 LLM API"（如 OpenAI），需联网、按量付费。Ollama 让同样的能力**离线、免费、数据不出本地**。

**与 Agent / RAG / LangChain 板块的关系**：Ollama 模型是这些上层框架的**底座模型提供者**——Lagent 里的 LLM、RAG 里的嵌入模型都可由 Ollama 提供，接口（`/api/chat`、`/api/embed`）与 OpenAI 兼容，可无缝替换。

**学习目标**：完成本板块后，你应能：
- 在本地安装并部署 Ollama，拉取并管理模型
- 通过 REST API 与 Python SDK 调用聊天/文本/嵌入/视觉模型
- 理解并调整 temperature、top_p、num_ctx 等关键推理参数
- 管理上下文窗口，进行多轮对话与会话隔离
- 使用嵌入模型做语义检索，为 RAG 打底
- 让本地模型支持工具调用（Function Calling）
- 将 Ollama 模型接入 LangChain / LlamaIndex
- 完成一个基于本地模型 + 本地嵌入的应用

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 Python 代码 + 实战练习
- 代码优先兼容离线运行：**当本机未安装 Ollama 或未拉取模型时，自动退化到模拟层**，保证"照搬就能跑"
- 有 Ollama 环境时，代码自动走真实调用，看到真实模型输出
- 紧扣 Ollama 本身，不堆砌框架内容（框架集成单列一天）

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| Python | 必须 | 基础语法、`requests`、`json` |
| 计算机基础 | 了解 | 终端命令、环境变量、端口 |
| LLM 基础 | 了解 | Chat 消息结构（LLM 板块） |
| 可选 | 有帮助 | LangChain / LlamaIndex 概念 |

**环境准备**（可选，但强烈建议用于真实体验）：
- 安装 Ollama：[https://ollama.com](https://ollama.com)
- 拉起服务：`ollama serve`
- 拉取模型（任选）：
  ```bash
  ollama pull llama3.1        # 对话模型（约 4.7GB）
  ollama pull qwen2.5:7b       # 中文友好的对话模型
  ollama pull nomic-embed-text # 嵌入模型（约 274MB）
  ollama pull llava            # 视觉模型（可选）
  ```
- 拉取后验证：`ollama run llama3.1 "你好"`

> **重要**：本板块所有代码都做了**双模式**兼容——检测不到 Ollama 环境或模型时，使用内置 `SimOllama` 模拟 API 响应，确保无环境也能运行；有环境时则走真实 API。切到真实模式只需启动 Ollama 并 pull 对应模型。

---

## 为什么用 Ollama

| 对比项 | 云端 API（如 OpenAI） | Ollama（本地） |
|--------|---------------------|---------------|
| 联网 | 必须 | 不需要（离线） |
| 费用 | 按 token 计费 | 免费（自耗算力） |
| 数据隐私 | 数据出本地 | 数据不出本地 ★ |
| 延迟 | 受网络影响 | 本地更可控 |
| 模型选择 | 供应商限定 | 开源模型自由切换 |
| 硬件要求 | 低（服务端跑） | 需较好 GPU/内存 |
| 适合 | 高并发生产 | 开发、隐私、离线场景 |

---

## 学习路线图

```
┌──────────────────────────────────────────────────────────────────┐
│             Ollama 学习路线（10天，从本地跑起来到集成上线）        │
└──────────────────────────────────────────────────────────────────┘

阶段一：基础入门（Day01-Day02）
┌──────────────┬──────────────┐
│ Day01        │ Day02        │
│ 概述与       │ 模型管理     │
│ 快速体验     │ 与拉取       │
└──────┬───────┴──────┬───────┘
       │              │
       ▼              ▼
阶段二：编程调用（Day03-Day04）
┌──────────────┬──────────────┐
│ Day03        │ Day04        │
│ HTTP API     │ Python SDK   │
│ 编程调用     │ 编程         │
└──────┬───────┴──────┬───────┘
       │              │
       ▼              ▼
阶段三：高级能力（Day05-Day08）
┌─────────┬─────────┬─────────┬─────────┐
│ Day05   │ Day06   │ Day07   │ Day08   │
│ 推理参数 │ 上下文与 │ 嵌入与   │ 工具调用 │
│ 调优     │ 对话管理 │ 向量     │         │
└─────────┴─────────┴─────────┴─────────┘
       │              │
       ▼              ▼
阶段四：集成与实战（Day09-Day10）
┌──────────────┬──────────────┐
│ Day09        │ Day10        │
│ LangChain/   │ 综合实战     │
│ LlamaIndex   │ 与部署       │
└──────────────┴──────────────┘
```

---

## 每日内容详表

### Day01 - Ollama概述与快速体验
- **核心**：Ollama 是什么、本地跑 LLM 的意义、架构（Client ↔ Server ↔ 模型仓库）、安装方式（Win/macOS/Linux）、`ollama run` 交互体验、模型选择思路
- **代码**：`01_what_is_ollama.py`（架构与托管模型清单）/`02_install_check.py`（环境检测与版本检查）/`03_quick_chat.py`（第一条对话：真实/模拟双模式）/`README.md`
- **重点**：环境就绪、双模式代码骨架

### Day02 - 模型管理与拉取
- **核心**：`ollama pull/push/rm/list/cp/show` 命令、模型仓库（仓库:标签）、从 OpenAI 仓库导入 GGUF、查看模型详情与参数量、磁盘占用与清理、管理器封装
- **代码**：`01_pull_list.py`（拉取与管理命令演示）/`02_model_detail.py`（模型元信息与参数量）/`03_model_manager.py`（管理器：列表/搜索/删除/磁盘汇总）/`README.md`
- **重点**：模型生命周期管理、命令与 API 对应

### Day03 - Ollama HTTP API 编程调用
- **核心**：REST API 全览（chat/embed/generate/list/show）、`/api/generate` 流式/非流式、请求体构造、响应解析、流式逐 token 输出、错误处理与重试
- **代码**：`01_rest_overview.py`（API 端点总览）/`02_chat_api.py`（chat 接口：消息/参数/响应解析）/`03_streaming.py`（流式逐 token 生成）/`04_generate_api.py`（generate 与多模态 raw）/`README.md`
- **重点**：chat/generate/embed 三大核心端点与流式

### Day04 - Python SDK 编程
- **核心**：`ollama` Python 客户端、同步与异步调用、`.chat()/.generate()/.embed()`、简化请求、stream 参数、原生客户端 vs HTTP 客户端、封装会话管理
- **代码**：`01_sdk_chat.py`（.chat 快捷调用）/`02_sdk_stream.py`（流式与非流式对比）/`03_sdk_embed.py`（嵌入调用）/`04_async_client.py`（异步并发）/`README.md`
- **重点**：SDK Pythonic 调用、流式、异步

### Day05 - 推理参数调优
- **核心**：temperature/top_p/top_k 采样、num_predict/max_tokens、stop 序列、seed 复现、repeat_penalty、参数对输出的影响、调试工具、组合示例
- **代码**：`01_temperature.py`（温度对创造力的影响）/`02_top_p.py`（top_p 采样）/`03_seed_repeat.py`（随机种子与重复惩罚）/`04_all_params.py`（综合参数调优演示）/`README.md`
- **重点**：采样参数、随机性控制、输出约束

### Day06 - 上下文长度与对话管理
- **核心**：num_ctx 上下文窗口、默认 2048 的限制、长上下文处理、多轮对话历史管理、会话隔离、历史裁剪、与记忆系统（Agent 板块）衔接
- **代码**：`01_context_window.py`（num_ctx 效果与 token 统计）/`02_multi_turn.py`(多轮对话历史构建）/`03_session_isolation.py`（多会话隔离）/`04_history_trim.py`（历史裁剪与摘要）/`README.md`
- **重点**：num_ctx、多轮对话、会话管理

### Day07 - 嵌入模型与向量检索
- **核心**：嵌入 Embedding 概念、语言嵌入 vs 通用嵌入、`/api/embed` 与 SDK、nomic-embed-text 等模型、为 RAG 准备向量库、余弦相似度检索（结合 VectorDB 板块）
- **代码**：`01_embedding_intro.py`（嵌入与相似度）/`02_semantic_search.py`（本地语义搜索）/`03_doc_chunk.py`（文档切块与入库）/`04_rag_embed.py`（嵌入驱动的简单检索）/`README.md`
- **重点**：嵌入、语义相似度、检索基础

### Day08 - 工具调用（Function Calling）
- **核心**：让本地模型调用工具、Ollama 的 tools 参数、Function Calling 协议、注册工具、多工具调度、与 Agent 板块（Day03）衔接、封装一个工具型 Agent
- **代码**：`01_tool_schema.py`（工具定义）/`02_function_calling.py`（Ollama 工具调用往返）/`03_multi_tool.py`（多工具调度）/`04_tool_agent.py`（工具型 Agent，真实/模拟双模式）/`README.md`
- **重点**：tools 协议、调用往返、工具 Agent

### Day09 - 与LangChain/LlamaIndex集成
- **核心**：Ollama 作为 LangChain 的模型提供者（ChatOllama/OllamaEmbeddings）、作为 LlamaIndex 的 LLM/Embedding、在框架内完成一次 RAG、prompt 模板结合、替代云端 API 的做法
- **代码**：`01_langchain_llm.py`(LangChain 对话)/`02_langchain_rag.py`(LangChain 本地 RAG)/`03_llamaindex_llm.py`（LlamaIndex 集成）/`04_multi_framework.py`（框架对比与选择）/`README.md`
- **重点**：框架接入、本地 RAG

### Day10 - 综合实战与部署
- **核心**：组装一个完整应用：本地模型客服助手（对话+内存+RAG+工具）、服务化部署、并发与性能、GPU 检测与加速、生产注意事项、总结与学习路径
- **代码**：`01_gpu_check.py`（硬件检测）/`02_full_agent.py`（本地客服助手整合）/`03_service.py`（REST 服务化演示）/`04_perf_bench.py`（性能基准）/`README.md`
- **重点**：整合、服务化、性能

---

## 目录结构

```
Ollama/
├── README.md                          ← 本文件（板块总入口）
├── Day01 - Ollama概述与快速体验/
│   ├── README.md
│   └── Code/
│       ├── 01_what_is_ollama.py
│       ├── 02_install_check.py
│       ├── 03_quick_chat.py
│       └── README.md
├── Day02 - 模型管理与拉取/
│   ├── README.md
│   └── Code/...
├── ...（Day03-Day09 同构）...
└── Day10 - 综合实战与部署/
    ├── README.md
    └── Code/
        ├── 01_gpu_check.py
        ├── 02_full_agent.py
        ├── 03_service.py
        ├── 04_perf_bench.py
        └── README.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，均为 `.py` 文件（可直接 `python file.py` 运行）
- 所有代码**优先离线可跑**：本机有 Ollama 走真实 API，无则自动退化到 `SimOllama` 模拟

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-6 小时 | 约 1.5-2 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 3-4 周 |
| 保守 | 碎片时间 | 1 小时 | 约 1.5 月 |

### 学习方法论

1. **先装环境**：Day01 就安装 Ollama 并 pull 一个模型，后续所有真实输出都依赖它
2. **跑通再深入**：先让代码"能跑"，再逐字段改参数看变化
3. **双模式对照**：模拟模式看代码逻辑，真实模式看模型行为，二者对比理解框架
4. **接口先行**：先掌握 REST API（Day03），SDK（Day04）只是其 Pythonic 封装
5. **结合上层**：学完 Day07/08 后，去对照 RAG、Agent 板块，看 Ollama 如何当底座
6. **本地优先**：理解"数据不出本地 + 免费"的独特价值，思考适合本地跑的场景

### 阶段性检查点

- **阶段一完成后**：能否拉取并运行一个模型？（`ollama run`）
- **阶段二完成后**：能否用 HTTP API 和 SDK 完成一次流式对话？
- **阶段三完成后**：能否调采样参数、管理上下文、做嵌入检索、让模型调工具？
- **阶段四完成后**：能否把 Ollama 接入 LangChain 并完成一个本地 RAG / Agent？

---

## 如何运行代码

### 环境准备

```bash
# 1. 安装 Ollama（Windows/macOS 装桌面版，Linux 用脚本）
# 官方: https://ollama.com/download
# Linux:
curl -fsSL https://ollama.com/install.sh | sh

# 2. 启动服务
ollama serve              # 默认监听 127.0.0.1:11434

# 3. 拉取模型（任选）
ollama pull llama3.1
ollama pull nomic-embed-text

# 4. Python 依赖（可选，只有真实调用模式需要）
pip install ollama requests  # requests 为极简多语言环境兜底
```

### 运行示例

```bash
# Day01：快速体验
python "Day01 - Ollama概述与快速体验/Code/03_quick_chat.py"

# Day03：HTTP API
python "Day03 - Ollama HTTP API 编程调用/Code/02_chat_api.py"

# Day07：嵌入与语义检索
python "Day07 - 嵌入模型与向量检索/Code/02_semantic_search.py"

# Day10：综合实战
python "Day10 - 综合实战与部署/Code/02_full_agent.py"
```

> 所有代码均可**无 Ollama、无网络**运行：检测不到服务时自动使用内置 `SimOllama` 模拟响应。

---

## 知识点速查

### 三大核心端点速查

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/chat` | POST | 多轮 Chat 对话（messages） |
| `/api/generate` | POST | 单次文本生成（prompt + prompt 历史） |
| `/api/embed` | POST | 文本 -> 向量嵌入 |
| `/api/list` | GET | 列出本地模型 |
| `/api/show` | POST | 查看模型详情/参数 |
| `/api/pull` | POST | 拉取模型 |

### 关键推理参数速查

| 参数 | 作用 | 典型值 |
|------|------|--------|
| `temperature` | 随机性（低=稳定，高=多样） | 0.1~1.0 |
| `top_p` | 核采样（累积概率阈值） | 0.9 |
| `top_k` | 只从概率前 k 个中选 | 40 |
| `num_predict` | 最大输出 token 数 | 128~4096 |
| `num_ctx` | 上下文窗口大小 | 2048~128000 |
| `seed` | 固定随机种子复现结果 | 42 |
| `stop` | 停止序列 | ["\n\n"] |

### 常见场景模型推荐速查

| 场景 | 推荐模型 | 大小 |
|------|---------|------|
| 通用对话 | llama3.1、qwen2.5 | 4.7~7GB |
| 代码 | codellama、qwen2.5-coder | 3.8~7GB |
| 嵌入 | nomic-embed-text | 274MB |
| 视觉 | llava、minicpm-v | 4.7~9GB |
| 中文 | qwen2.5、glm4 | 4~9GB |

### 与 OpenAI 兼容性速查

| 能力 | OpenAI | Ollama |
|------|--------|--------|
| 消息结构 | messages[role/content] | 兼容 |
| 函数调用 | tools | 兼容（tools 参数） |
| 流式 | stream=true | 兼容 |
| 端点 | /v1/chat/completions | /v1/chat/completions（兼容端点） |

---

## 后续板块

本板块完成后，可自然衔接：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **LangChain / LlamaIndex** | 用 Ollama 当底座模型做完整框架应用 |
| **RAG / VectorDB** | 用 Ollama 嵌入模型 + 向量库做本地知识问答 |
| **Agent** | 用 Ollama 模型驱动工具调用 Agent |
| **微调** | 本地模型微调与私有化部署 |
| **部署运维** | 本机多模型、多服务的生产化 |

---

## 学习资源补充

> 遇到疑问时优先查阅官方文档

- [Ollama 官方文档](https://docs.ollama.com) - 安装/命令/API 权威参考
- [Ollama GitHub](https://github.com/ollama/ollama) - 开源仓库
- [Ollama Model Library](https://ollama.com/library) - 模型仓库
- [Ollama Python SDK](https://github.com/ollama/ollama-python) - 官方客户端

---

## 贡献与反馈

本学习手册为原创内容，参考 Ollama 官方文档的组织思想但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，让大模型跑在你的电脑上！**