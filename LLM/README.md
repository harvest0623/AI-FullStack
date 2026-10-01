# LLM 大语言模型学习指南

> 系统化掌握大语言模型的核心原理、API 集成、工程优化与生产部署能力

> 共 12 天，覆盖从 Transformer 架构、API 调用、Embedding、模型选型到微调部署的完整工程链路

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

本板块是全栈学习系列的 **AI 工程化核心**。大语言模型（LLM）是当前 AI 浪潮的技术基石——从 ChatGPT 到代码助手，从智能客服到数据分析，LLM 正在重塑软件开发的方方面面。理解 LLM 的工作原理、掌握 API 集成与工程优化、能够进行模型选型与部署，是 AI 全栈工程师的核心竞争力。

**与 Prompt 板块的关系**：Prompt 板块教你"如何与 LLM 沟通"，本板块教你"如何用工程化方式驱动 LLM"——从 API 调用到 Token 管理，从 Embedding 到微调部署，是 Prompt 工程的上层建筑。

**与后续板块的关系**：本板块聚焦 LLM 本身。LangChain、RAG、Agent 等基于 LLM 的应用框架和架构将有独立的板块深入讲解。

**学习目标**：完成本板块后，你应能：
- 理解 Transformer 架构与 LLM 训练流程（预训练→指令微调→RLHF）
- 熟练调用主流 LLM API（OpenAI / Anthropic / 国内模型）
- 管理 Token 消耗与上下文窗口
- 使用 Embedding 进行语义表示与相似度计算
- 进行模型选型与对比评估
- 在 Python 项目中工程化管理 Prompt 模板
- 实现流式输出与性能优化
- 使用多模态 LLM（Vision / 语音）
- 部署本地开源模型（Ollama / vLLM / llama.cpp）
- 了解微调方法（LoRA / QLoRA）
- 评估 LLM 输出质量并建立监控
- 将 LLM 应用部署到生产环境

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 Python 代码 + 实战练习
- 全程围绕统一的**智能问答服务 `AISearch`** 项目展开
- 所有 Python 代码可在 3.10+ 直接运行（需配置 API Key）
- 紧扣工程化视角，为后续 RAG / Agent 板块铺垫

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| Python | 必须 | 能读写 Python 代码、理解异步/类/装饰器 |
| Prompt 基础 | 已完成 Prompt 板块更好 | 理解 System/User/Assistant 角色、Few-Shot、CoT |
| HTTP/API | 基础 | 理解 REST API 调用方式 |
| 命令行 | 基础 | 能安装依赖、运行脚本 |

**环境准备**：
- Python 3.10+
- 至少一个 LLM API Key（OpenAI / Anthropic / 国内模型均可）
- 代码编辑器：VS Code
- 可选：GPU（本地模型部署需要）

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                   LLM 学习路线（12天）                           │
└─────────────────────────────────────────────────────────────────┘

阶段一：原理与基础（Day01-Day04）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Day01 LLM   │  Day02 API   │  Day03 Token │  Day04 Embed │
│  架构原理    │  调用与集成  │  与上下文    │  与向量表示 │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
阶段二：工程化（Day05-Day08）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Day05 模型  │  Day06 Prompt│  Day07 流式  │  Day08 多模 │
│  选型与评估  │  工程化集成  │  与性能优化  │  态LLM应用 │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
阶段三：部署与优化（Day09-Day12）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Day09 本地  │  Day10 微调  │  Day11 评估  │  Day12 生产 │
│  模型部署    │  与模型优化  │  与监控      │  部署实践   │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 示例项目

本板块全程围绕一个**智能问答服务 `AISearch`** 展开，模拟从零构建 LLM 应用的全过程。

### 项目结构

```
aisearch/
├── pyproject.toml
├── src/
│   └── aisearch/
│       ├── __init__.py
│       ├── config.py              ← LLM 配置管理（API Key/模型/参数）
│       ├── clients/               ← LLM 客户端封装
│       │   ├── openai_client.py    ← OpenAI API 封装
│       │   ├── anthropic_client.py ← Anthropic API 封装
│       │   └── local_client.py     ← 本地模型封装
│       ├── core/                   ← 核心功能
│       │   ├── chat.py             ← 对话管理
│       │   ├── token_counter.py    ← Token 计数与管理
│       │   ├── context_manager.py  ← 上下文窗口管理
│       │   └── stream.py           ← 流式输出
│       ├── embedding/              ← Embedding 服务
│       │   ├── encoder.py          ← 向量编码
│       │   └── similarity.py       ← 相似度计算
│       ├── prompts/                ← Prompt 模板管理
│       │   ├── templates/          ← 模板文件
│       │   └── manager.py          ← 模板加载与渲染
│       ├── eval/                   ← 评估模块
│       │   ├── metrics.py          ← 评估指标
│       │   └── judge.py            ← LLM-as-Judge
│       └── utils/                  ← 工具函数
│           ├── cache.py            ← 响应缓存
│           ├── retry.py            ← 重试机制
│           └── cost.py             ← 成本计算
├── tests/
└── scripts/
```

> 各天的代码围绕这个项目逐步构建，从 API 调用到生产部署完整演进。

---

## 每日内容详表

### 阶段一：原理与基础

#### Day01 - LLM基础与架构原理
- **核心**：LLM 定义与发展历程、NLP 发展史（规则→统计→深度学习→Transformer→LLM）、Transformer 架构详解（自注意力 Self-Attention、多头注意力 Multi-Head Attention、位置编码 Positional Encoding、前馈网络 FFN、Layer Normalization）、GPT 架构（Decoder-Only）、BERT 架构（Encoder-Only）、LLM 训练三阶段（预训练 Pre-training → 指令微调 SFT → 人类反馈强化学习 RLHF）、模型参数与能力关系、Scaling Laws、涌现能力（Emergent Abilities）、上下文窗口概念、主流开源模型生态（Llama / Qwen / Mistral / DeepSeek）
- **代码**：`01_transformer_concepts.py`（Transformer 概念演示）/ `02_attention_demo.py`（注意力机制可视化）/ `03_tokenization_demo.py`（分词器演示）/ `README.md`（LLM 架构原理指南）
- **重点**：理解 Transformer 自注意力机制、LLM 训练三阶段

#### Day02 - LLM API调用与集成
- **核心**：OpenAI API 详解（Chat Completions / Completions / Embeddings / Whisper / DALL-E）、消息角色体系（System/User/Assistant/Tool）、请求参数详解（model/messages/temperature/top_p/max_tokens/stop/seed/response_format）、响应结构（choices/usage/finish_reason）、Anthropic Claude API（Messages API / system 参数 / max_tokens 必填）、国内模型 API（通义千问/文心一言/智谱清言/Moonshot）、API Key 安全管理（环境变量/.env/密钥管理服务）、错误处理（Rate Limit/Token Limit/Invalid Request/Timeout）、Python SDK 使用（openai / anthropic / dashscope）、同步 vs 异步调用、多模型统一客户端设计
- **代码**：`01_openai_chat.py`（OpenAI 对话调用）/ `02_anthropic_chat.py`（Claude 对话调用）/ `03_chinese_models.py`（国内模型调用）/ `04_unified_client.py`（多模型统一客户端）/ `README.md`（API 集成指南）
- **重点**：多模型统一客户端设计、API Key 安全管理

#### Day03 - Token管理与上下文工程
- **核心**：Token 概念（Token ≠ 字符 ≠ 单词）、tiktoken 库（编码/解码/计数）、不同模型 Tokenizer 差异（GPT BPE / Llama SentencePiece / Claude）、中文 Token 消耗特点、上下文窗口管理策略（截断/摘要/滑动窗口/选择性保留）、对话历史管理（全量保留 vs 摘要压缩 vs 滑动窗口）、Token 成本计算（输入/输出/总成本）、上下文窗口与性能关系（Lost in the Middle 问题）、分块策略（固定长度/语义分块/递归分块）、长文本处理模式（Map-Reduce/Refine/Map-Rerank）
- **代码**：`01_token_counter.py`（Token 计数工具）/ `02_context_manager.py`（上下文窗口管理器）/ `03_conversation_memory.py`（对话历史管理：全量/摘要/滑动窗口三种策略对比）/ `04_cost_calculator.py`（成本计算器）/ `README.md`（Token 管理指南）
- **重点**：上下文窗口管理策略、对话历史压缩

#### Day04 - Embedding与向量表示
- **核心**：Embedding 概念（文本→高维向量）、为什么需要 Embedding（语义搜索/聚类/分类/推荐）、词嵌入 vs 句嵌入（Word2Vec/GloVe vs Sentence-BERT）、OpenAI Embedding API（text-embedding-3-small/large）、其他 Embedding 模型（Cohere/BGE/E5）、向量维度与性能权衡、余弦相似度/欧氏距离/点积、相似度搜索实践、向量可视化（t-SNE/PCA 降维）、Embedding 质量评估、多语言 Embedding
- **代码**：`01_embedding_basics.py`（Embedding 基础：编码/相似度计算）/ `02_similarity_search.py`（语义搜索实现）/ `03_embedding_comparison.py`（多模型 Embedding 对比）/ `04_vector_visualization.py`（向量降维可视化）/ `README.md`（Embedding 工程指南）
- **重点**：语义搜索实现、相似度计算

---

### 阶段二：工程化

#### Day05 - 模型选择与对比评估
- **核心**：模型能力维度（推理/代码/创作/多语言/多模态）、闭源模型对比（GPT-4o/GPT-4 Turbo/Claude 3.5 Sonnet/Claude 3 Opus/Gemini 1.5 Pro）、开源模型对比（Llama 3/Qwen 2/Mistral/DeepSeek）、模型选型决策框架（任务类型/成本/延迟/隐私/部署方式）、能力评估基准（MMLU/HumanEval/GSM8K/MT-Bench）、输出质量对比方法、成本与延迟对比、模型路由策略（根据任务复杂度选择不同模型）、A/B 测试模型选型
- **代码**：`01_model_comparison.py`（多模型输出对比工具）/ `02_benchmark_runner.py`（基准测试运行器）/ `03_model_router.py`（模型路由器实现）/ `04_cost_latency_analysis.py`（成本与延迟分析）/ `README.md`（模型选型决策指南）
- **重点**：模型选型决策框架、模型路由策略

#### Day06 - Prompt工程化集成
- **核心**：Prompt 工程化需求（模板管理/版本控制/动态渲染/A-B 测试）、Prompt 模板系统设计（变量插值/条件逻辑/继承组合）、Python 中管理 Prompt 模板（文件加载/字符串模板/Jinja2 模板）、Prompt 版本管理、Prompt 测试框架（单元测试/回归测试）、动态 Prompt 构建（根据上下文动态选择模板）、Prompt 缓存策略、Prompt 与代码的解耦设计、Prompt 即代码（Prompt as Code）理念
- **代码**：`01_prompt_template.py`（Prompt 模板系统）/ `02_prompt_manager.py`（Prompt 管理器：加载/渲染/版本管理）/ `03_dynamic_prompt.py`（动态 Prompt 构建）/ `04_prompt_testing.py`（Prompt 测试框架）/ `README.md`（Prompt 工程化指南）
- **重点**：Prompt 模板系统设计、Prompt 测试框架

#### Day07 - 流式输出与性能优化
- **核心**：流式输出（Streaming）原理（SSE/Chunk 传输）、OpenAI stream=True 实现、Anthropic 流式实现、Python 异步流式处理（async/await + async for）、流式输出的用户体验（逐字打印/打字机效果）、并发调用优化（asyncio.gather 批量请求）、响应缓存策略（内容哈希/语义缓存）、请求重试机制（指数退避/抖动）、速率限制处理（Token Bucket/Leaky Bucket）、延迟优化技巧（模型选择/参数调优/预热连接）、批量处理（Batch API）
- **代码**：`01_streaming_output.py`（流式输出实现）/ `02_async_batch.py`（异步批量调用）/ `03_response_cache.py`（响应缓存实现）/ `04_retry_rate_limit.py`（重试与限流）/ `README.md`（性能优化指南）
- **重点**：流式输出实现、异步并发调用

#### Day08 - 多模态LLM应用
- **核心**：多模态 LLM 概念（文本+图像+音频+视频）、GPT-4o/GPT-4 Vision（图像理解：描述/OCR/分析/对比）、Claude 3.5 Vision、Gemini 多模态能力、图像输入方式（URL/Base64/文件上传）、多图像对话、音频处理（Whisper 语音识别/TTS 语音合成）、视频理解（Gemini 视频分析）、多模态应用场景（图文问答/文档解析/表单识别/医疗影像/安防监控）、多模态 Prompt 技巧、多模态成本管理
- **代码**：`01_vision_chat.py`（图像理解对话）/ `02_image_analysis.py`（图像分析工具：OCR/描述/对比）/ `03_whisper_stt.py`（语音转文字）/ `04_tts_demo.py`（文字转语音）/ `README.md`（多模态应用指南）
- **重点**：图像理解 API 调用、多模态应用场景

---

### 阶段三：部署与优化

#### Day09 - 本地模型部署
- **核心**：本地部署的需求场景（隐私/成本/离线/定制化）、Ollama 安装与使用（ollama run/ollama pull/模型管理）、Ollama API 调用（兼容 OpenAI API 格式）、vLLM 部署（高吞吐推理引擎/PagedAttention/连续批处理）、llama.cpp 部署（轻量级/CPU 推理/GPU 加速）、模型量化（GGUF/AWQ/GPTQ/INT4/INT8）、硬件需求（GPU 显存计算/CPU 内存需求）、模型下载与管理（HuggingFace Hub/modelscope）、本地模型 vs API 对比、本地部署安全考量
- **代码**：`01_ollama_demo.py`（Ollama 本地调用）/ `02_vllm_server.py`（vLLM 服务部署脚本）/ `03_local_vs_api.py`（本地模型 vs API 性能对比）/ `04_quantization_guide.py`（模型量化指南）/ `README.md`（本地部署完整指南：含 Docker/裸机部署步骤）
- **重点**：Ollama 快速部署、vLLM 高性能推理

#### Day10 - 微调与模型优化
- **核心**：微调概念与动机（领域适配/风格定制/成本优化）、微调方法分类（全量微调 Full Fine-tuning / 参数高效微调 PEFT）、LoRA 原理（低秩适配矩阵）、QLoRA（量化+LoRA）、微调数据准备（指令格式/数据质量/数据量）、微调流程（数据准备→格式转换→训练→评估→部署）、微调工具（LLaMA-Factory/Unsloth/Axolotl）、微调效果评估、微调 vs Few-Shot vs RAG 选型、微调的坑与注意事项
- **代码**：`01_data_preparation.py`（微调数据准备与格式化）/ `02_lora_config.py`（LoRA 配置示例）/ `03_training_script.py`（微调训练脚本框架）/ `04_eval_finetuned.py`（微调效果评估）/ `README.md`（微调实践指南：含 LLaMA-Factory 使用教程）
- **重点**：LoRA/QLoRA 原理、微调数据准备

#### Day11 - LLM评估与监控
- **核心**：LLM 评估的挑战（开放性/主观性/多维度）、评估指标体系（准确性/相关性/流畅性/安全性/忠实性）、评估基准（MMLU/HumanEval/GSM8K/MT-Bench/AlpacaEval）、LLM-as-a-Judge 实现（用 GPT-4 评估其他模型输出）、人工评估方法论（盲评/多标注者/评分量表）、评估数据集构建、自动化评估管道、生产环境监控（延迟监控/成本监控/质量监控/安全监控）、用户反馈收集、漂移检测（概念漂移/数据漂移）、告警系统设计
- **代码**：`01_eval_metrics.py`（评估指标计算）/ `02_llm_judge.py`（LLM-as-Judge 实现）/ `03_eval_pipeline.py`（自动化评估管道）/ `04_monitoring.py`（生产监控仪表盘数据采集）/ `README.md`（评估与监控指南）
- **重点**：LLM-as-a-Judge、自动化评估管道

#### Day12 - 生产部署与最佳实践
- **核心**：LLM 应用架构设计（API 层/业务层/LLM 层/缓存层/监控层）、成本控制策略（模型路由/缓存/Token 优化/批量处理）、高可用设计（故障转移/降级策略/多模型备份）、安全防护（Prompt 注入防护/输出过滤/PII 脱敏/API 限流）、合规与审计（日志记录/数据留痕/用户同意/数据删除）、CI/CD for LLM（Prompt 版本管理/自动化测试/灰度发布）、Docker 容器化部署（Dockerfile/Compose/K8s）、API 服务封装（FastAPI 实现LLM API 服务）、负载均衡与扩缩容、最佳实践总结
- **代码**：`01_fastapi_service.py`（FastAPI LLM 服务封装）/ `02_docker_deploy.py`（Docker 部署配置生成）/ `03_cost_monitor.py`（成本监控系统）/ `04_health_check.py`（健康检查与告警）/ `README.md`（生产部署完整指南：含架构图/部署清单/最佳实践）
- **重点**：LLM 应用架构设计、FastAPI 服务封装、成本控制

---

## 目录结构

```
LLM/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - LLM基础与架构原理/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天 Python 代码
│       ├── 01_transformer_concepts.py
│       ├── 02_attention_demo.py
│       ├── 03_tokenization_demo.py
│       └── README.md
├── Day02 - LLM API调用与集成/
│   ├── README.md
│   └── Code/
│       ├── 01_openai_chat.py
│       ├── 02_anthropic_chat.py
│       ├── 03_chinese_models.py
│       ├── 04_unified_client.py
│       └── README.md
├── ...（Day03-Day11 同构）...
└── Day12 - 生产部署与最佳实践/
    ├── README.md
    └── Code/
        ├── 01_fastapi_service.py
        ├── 02_docker_deploy.py
        ├── 03_cost_monitor.py
        ├── 04_health_check.py
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

1. **先理解后编码**：每天先通读 README，理解 LLM 原理再动手写代码
2. **实际调用 API**：代码中的 API 调用需要真实 Key 才能运行
3. **对比实验**：不同模型、不同参数、不同策略要实际对比
4. **关注成本**：LLM API 按量计费，注意 Token 消耗和费用
5. **工程化思维**：从"能跑通"到"能上线"，关注错误处理/监控/成本
6. **逐步构建项目**：随学习推进完善 `AISearch` 智能问答服务

### 阶段性检查点

- **阶段一完成后**：能否理解 LLM 工作原理并熟练调用多种 LLM API？
- **阶段二完成后**：能否在 Python 项目中工程化管理 Prompt、实现流式输出和多模态应用？
- **阶段三完成后**：能否部署本地模型、进行微调评估、并将 LLM 应用部署到生产环境？

---

## 如何运行代码

### 环境准备

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 安装核心依赖
pip install openai anthropic tiktoken httpx python-dotenv
```

### 配置 API Key

```bash
# 创建 .env 文件
cat > .env << 'EOF'
OPENAI_API_KEY=sk-xxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
DASHSCOPE_API_KEY=sk-xxxxxxxx
EOF

# 或设置环境变量
export OPENAI_API_KEY="sk-xxxxxxxx"
```

### 运行示例

```bash
# 运行指定天数的代码
python "Day02 - LLM API调用与集成/Code/01_openai_chat.py"

# 运行 Embedding 示例
python "Day04 - Embedding与向量表示/Code/01_embedding_basics.py"

# 启动本地模型（需先安装 Ollama）
ollama pull qwen2.5:7b
python "Day09 - 本地模型部署/Code/01_ollama_demo.py"
```

### 使用 Docker 运行

```bash
# 用 Docker 运行（含所有依赖）
docker run -it --rm \
  -v "$(pwd):/workspace" -w /workspace \
  --env-file .env \
  python:3.12-slim \
  python "Day02 - LLM API调用与集成/Code/01_openai_chat.py"
```

---

## 知识点速查

### LLM 训练三阶段速查

| 阶段 | 名称 | 数据 | 目标 | 产出 |
|------|------|------|------|------|
| 1 | 预训练 Pre-training | 海量无标注文本 | 学习语言和知识 | 基座模型 |
| 2 | 指令微调 SFT | 指令-回答对 | 学会遵循指令 | 对话模型 |
| 3 | RLHF | 人类偏好数据 | 对齐人类偏好 | 对齐模型 |

### 主流 LLM API 对比速查

| 模型 | 提供商 | 上下文窗口 | 多模态 | API 兼容 | 特长 |
|------|--------|-----------|--------|---------|------|
| GPT-4o | OpenAI | 128K | 文本+图像+音频 | OpenAI 格式 | 综合能力最强 |
| Claude 3.5 Sonnet | Anthropic | 200K | 文本+图像 | Anthropic 格式 | 长文本/代码 |
| Gemini 1.5 Pro | Google | 1M+ | 全模态 | Google 格式 | 超长上下文 |
| 通义千问 | 阿里 | 128K | 文本+图像 | OpenAI 兼容 | 中文/国内合规 |
| 文心一言 | 百度 | 128K | 文本+图像 | 百度格式 | 中文/生态 |
| 智谱清言 | 智谱 | 128K | 文本+图像 | OpenAI 兼容 | 中文/开源 |

### Token 消耗估算速查

| 语言 | 1 Token ≈ | 1000 字 ≈ | 说明 |
|------|----------|----------|------|
| 英文 | 0.75 词 | ~1300 Token | 英文 Token 效率高 |
| 中文 | 0.5-0.7 字 | ~1500-2000 Token | 中文 Token 消耗大 |
| 代码 | 2-4 字符 | ~1500-2500 Token | 代码 Token 因语言而异 |

### 模型选型决策速查

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 高质量推理 | GPT-4o / Claude 3.5 | 推理能力最强 |
| 低成本简单任务 | GPT-4o-mini / Qwen-Turbo | 性价比高 |
| 超长文本处理 | Claude 3.5 / Gemini 1.5 | 上下文窗口大 |
| 代码生成 | GPT-4o / Claude 3.5 | 代码能力强 |
| 中文场景 | Qwen / 文心 / 智谱 | 中文优化 |
| 隐私敏感 | Llama 3 / Qwen（本地部署） | 数据不出域 |
| 高吞吐推理 | vLLM + 开源模型 | 吞吐量高 |

### Embedding 模型速查

| 模型 | 提供商 | 维度 | 中文支持 | 特点 |
|------|--------|------|---------|------|
| text-embedding-3-small | OpenAI | 1536 | 支持 | 性价比高 |
| text-embedding-3-large | OpenAI | 3072 | 支持 | 精度高 |
| bge-large-zh | 智源 | 1024 | 优秀 | 中文最佳开源 |
| bge-m3 | 智源 | 1024 | 优秀 | 多语言 |
| Cohere embed-v3 | Cohere | 1024 | 支持 | 多语言强 |

### 微调方法对比速查

| 方法 | 参数量 | 显存需求 | 效果 | 适用场景 |
|------|--------|---------|------|---------|
| 全量微调 | 100% | 极高 | 最好 | 企业级/大量数据 |
| LoRA | 0.1-1% | 中等 | 良好 | 通用首选 |
| QLoRA | 0.1-1% | 低 | 良好 | 消费级 GPU |
| Prefix Tuning | <1% | 低 | 一般 | 轻量适配 |

### 本地部署工具速查

| 工具 | 特点 | GPU 需求 | 吞吐量 | 适用场景 |
|------|------|---------|--------|---------|
| Ollama | 最简单 | 可选 | 中 | 开发/测试 |
| vLLM | 高性能 | 必须 | 高 | 生产环境 |
| llama.cpp | 轻量级 | 可选 | 低 | CPU/边缘 |
| TGI | HuggingFace | 必须 | 高 | 生产环境 |
| SGLang | 高性能 | 必须 | 高 | 生产环境 |

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **RAG** | 基于 LLM + Embedding 构建检索增强生成系统 |
| **LangChain** | 用 LangChain 框架编排 LLM 应用 |
| **Agent** | 基于 LLM 构建 Agent 系统（工具调用/多步推理） |
| **Python** | 本板块的编程语言基础 |
| **Prompt** | 本板块的 Prompt 设计基础 |
| **Docker** | LLM 应用容器化部署 |
| **FastAPI / Flask** | LLM API 服务封装 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [OpenAI API 文档](https://platform.openai.com/docs) - OpenAI 官方 API 文档
- [Anthropic API 文档](https://docs.anthropic.com/) - Claude 官方文档
- [HuggingFace 文档](https://huggingface.co/docs) - 开源模型与工具
- [vLLM 文档](https://docs.vllm.ai/) - 高性能推理引擎
- [Ollama 官网](https://ollama.com/) - 本地模型部署
- [tiktoken 文档](https://github.com/openai/tiktoken) - Token 计数工具
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) - Transformer 可视化教程

---

## 贡献与反馈

本学习手册为原创内容，参考 GitHub 优质仓库的文档风格但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用工程化思维驾驭大语言模型！**
