# Prompt Engineering 学习指南

> 系统化掌握 Prompt 工程核心能力，为 AI 应用开发与 LLM 集成奠定提示词设计基础
>
> 共 10 天，覆盖从基础概念、设计原则、高级技巧到 Agent 应用与安全防护的完整知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [示例场景](#示例场景)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何使用代码](#如何使用代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是全栈学习系列的 **AI 交互能力基石**。Prompt Engineering 是与大语言模型（LLM）高效沟通的核心技能——同样一个 LLM，优秀的 Prompt 能让输出质量提升数倍，而糟糕的 Prompt 则可能得到完全无关的结果。随着 ChatGPT、Claude、GPT-4 等 LLM 的普及，Prompt Engineering 已成为开发者、产品经理、数据分析师的必备技能。

**与 Python 板块的关系**：Python 是调用 LLM API 的编程语言，Prompt Engineering 则决定你传给 API 的指令质量。两者结合——用 Python 调用 LLM API、用精心设计的 Prompt 获取高质量输出——构成了 AI 应用开发的基础。

**学习目标**：完成本板块后，你应能：
- 理解 LLM 工作原理与 Prompt 的本质
- 掌握 Prompt 设计的六大原则（清晰、具体、上下文、角色、格式、约束）
- 熟练运用零样本、少样本、思维链等核心技术
- 设计结构化、可复用的 Prompt 模板
- 调试和评估 Prompt 质量
- 针对代码生成、文本处理、内容创作等场景编写专业 Prompt
- 设计 Agent 与工具调用的 Prompt
- 识别 Prompt 注入等安全风险并采取防护措施

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + Prompt 模板 + 实战练习
- 全程围绕一个**智能客服助手开发**场景展开，前后连贯
- 所有 Prompt 模板可直接用于 ChatGPT / Claude / 文心一言 / 通义千问等主流 LLM
- 紧扣工程化视角，多处铺垫 RAG / Agent / AI 应用开发场景

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| LLM 使用经验 | 基础 | 用过 ChatGPT / Claude 等对话工具 |
| 编程基础 | 有更好 | Python 基础有助于理解 API 调用示例 |
| 逻辑思维 | 重要 | Prompt 设计需要清晰的逻辑表达 |

**环境准备**：
- 一个 LLM 账号：ChatGPT / Claude / 国内大模型（文心一言 / 通义千问 / 智谱清言）
- 代码编辑器：VS Code（用于编辑 Prompt 模板和 Python 调用脚本）
- 可选：Python 3.10+ + openai 库（用于 API 调用示例）

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                  Prompt Engineering 学习路线（10天）            │
└─────────────────────────────────────────────────────────────────┘

阶段一：基础与原则（Day01-Day03）
┌──────────────┬──────────────┬──────────────┐
│  Day01 概述  │  Day02 设计  │  Day03 零样本│
│  与基础      │  原则与技巧  │  与少样本    │
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       ▼              ▼              ▼
阶段二：高级技巧（Day04-Day06）
┌──────────────┬──────────────┬──────────────┐
│  Day04 思维链│  Day05 结构化│  Day06 调试  │
│  与推理优化  │  模板设计    │  与评估      │
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       ▼              ▼              ▼
阶段三：实战应用（Day07-Day09）
┌──────────────┬──────────────┬──────────────┐
│  Day07 代码  │  Day08 文本  │  Day09 Agent│
│  生成实战    │  处理创作    │  与工具调用  │
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       ▼              ▼              ▼
阶段四：安全与进阶（Day10）
┌──────────────┐
│  Day10 安全  │
│  与最佳实践  │
└──────────────┘
```

---

## 示例场景

本板块全程围绕一个**智能客服助手 `SmartCS`** 的 Prompt 开发展开，模拟从零构建 AI 客服系统的全过程。

### 项目背景

```
项目：SmartCS - 智能客服助手
目标：用 LLM 构建电商平台的智能客服系统

功能模块：
┌──────────────────────────────────────────────────┐
│               SmartCS 智能客服系统                │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ 意图识别 │  │ FAQ 问答 │  │ 订单查询      │  │
│  │ Prompt   │  │ Prompt   │  │ Prompt        │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  | 退换货   │  │ 情感分析 │  │ 工单生成      │  │
│  │ 流程引导 │  │ 与安抚   │  │ 与分派        │  │
│  │ Prompt   │  │ Prompt   │  │ Prompt        │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │          Agent 工具调用层                │    │
│  │  查询订单 → 查询库存 → 生成回复          │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

### Prompt 模板组织

```
prompts/
├── system/                    ← 系统级 Prompt
│   ├── role_customer_service.md   ← 客服角色设定
│   └── guardrails.md              ← 安全护栏
├── tasks/                     ← 任务级 Prompt
│   ├── intent_classification.md   ← 意图识别
│   ├── faq_answer.md              ← FAQ 问答
│   ├── order_query.md             ← 订单查询
│   ├── refund_guide.md            ← 退换货引导
│   ├── sentiment_analysis.md      ← 情感分析
│   └── ticket_generation.md       ← 工单生成
├── agents/                    ← Agent Prompt
│   ├── tool_use.md                ← 工具调用
│   └── multi_step.md              ← 多步推理
└── templates/                 ← 通用模板
    ├── few_shot.md                ← 少样本模板
    ├── cot.md                     ← 思维链模板
    └── structured_output.md      ← 结构化输出模板
```

> 各天的 Prompt 模板围绕这个客服系统展开，逐步完成从基础对话到 Agent 工具调用的完整体系。

---

## 每日内容详表

### 阶段一：基础与原则

#### Day01 - Prompt工程概述与基础
- **核心**：LLM 工作原理（Token、上下文窗口、温度）、Prompt 本质（指令而非查询）、Prompt Engineering 定义与发展历程、为什么需要 Prompt Engineering、Prompt 的基本结构（指令+上下文+输入+输出格式）、System Prompt vs User Prompt vs Assistant Prompt、多轮对话机制、主流 LLM 对比（GPT-4/Claude/Gemini/国内模型）、Prompt 调试工具介绍
- **代码**：`01-basic-prompt.md`（基础 Prompt 示例）/ `02-token-and-context.md`（Token 与上下文窗口演示）/ `03-chat-roles.md`（三种角色对话演示）/ `README.md`（LLM 基础概念指南）
- **重点**：理解 Prompt 是"指令"而非"搜索查询"，Token 与上下文窗口概念

#### Day02 - Prompt设计原则与技巧
- **核心**：六大设计原则（清晰明确、具体详尽、提供上下文、角色设定、指定格式、设定约束）、"Be Specific" 原则、分隔符使用（```/###/---/XML 标签）、指令的优先级（开头/结尾效果更好）、正面指令 vs 负面指令（"做什么"优于"不做什么"）、限制输出长度、指定输出格式（JSON/Markdown/表格/列表）、温度（Temperature）与 Top-p 调参、Prompt 长度与信息密度的平衡
- **代码**：`01-six-principles.md`（六大原则示例对比）/ `02-delimiters.md`（分隔符使用示例）/ `03-output-format.md`（输出格式控制）/ `04-temperature-tuning.md`（温度调参指南）
- **重点**：六大原则的实际应用、分隔符隔离输入与指令

#### Day03 - 零样本与少样本学习
- **核心**：零样本（Zero-Shot）概念与适用场景、少样本（Few-Shot）概念与原理、Few-Shot 示例选择策略（数量/顺序/多样性/代表性）、示例格式（输入-输出对）、Few-Shot 的边界（何时无效）、One-Shot 单样本、Few-Shot 与微调的区别、In-Context Learning（上下文学习）原理、示例质量 > 数量、示例偏差对输出的影响
- **代码**：`01-zero-shot.md`（零样本 Prompt 模板）/ `02-few-shot.md`（少样本 Prompt 模板）/ `03-example-selection.md`（示例选择策略对比）/ `04-few-shot-patterns.md`（少样本常见模式合集）
- **重点**：Few-Shot 示例的质量与选择策略

---

### 阶段二：高级技巧

#### Day04 - 思维链与推理优化
- **核心**：思维链（Chain-of-Thought, CoT）原理、CoT 触发方式（"Let's think step by step"）、Zero-Shot CoT vs Few-Shot CoT、CoT 适用场景（数学/逻辑/推理）、Self-Consistency（自洽性：多次采样取多数）、Tree-of-Thoughts（ToT，思维树）、ReAct 推理模式（Reason+Act）、分步推理的 Prompt 结构、推理过程可见性、CoT 的局限与失败模式
- **代码**：`01-cot-basic.md`（CoT 基础模板）/ `02-cot-advanced.md`（高级 CoT 模式）/ `03-react-pattern.md`（ReAct 推理模板）/ `04-self-consistency.md`（自洽性策略模板）
- **重点**：CoT 触发技巧、ReAct 推理模式

#### Day05 - 结构化Prompt模板设计
- **核心**：为什么需要结构化 Prompt、CRISPE 框架（Capacity/Role/Insight/Statement/Personality/Experiment）、CREATE 框架、RTF 框架（Role/Task/Format）、Prompt 模板设计模式、变量插值（{{variable}} 占位符）、条件逻辑（根据输入动态调整）、Prompt 组合与链式调用（Prompt Chaining）、Prompt 继承与覆盖、XML 标签结构化（Anthropic Claude 风格）、Markdown 结构化、JSON Schema 约束输出、Prompt 模板版本管理
- **代码**：`01-crispe-framework.md`（CRISPE 框架模板）/ `02-rtf-framework.md`（RTF 框架模板）/ `03-xml-structured.md`（XML 标签结构化模板）/ `04-prompt-chaining.md`（Prompt 链式调用模板）/ `05-template-with-variables.md`（变量插值模板）
- **重点**：结构化框架的实际应用、Prompt 链式调用

#### Day06 - Prompt调试与评估
- **核心**：Prompt 常见问题（幻觉/格式错/逻辑错/拒绝回答/过度安全）、调试方法论（A/B 测试/边界测试/对抗测试）、评估指标（准确性/相关性/流畅性/一致性/安全性）、人工评估 vs 自动评估、LLM-as-a-Judge（用 LLM 评估 LLM 输出）、评估数据集构建、Prompt 回归测试、迭代优化流程（诊断→假设→修改→验证）、Prompt 版本管理与变更日志、常见反模式（过度指令/矛盾指令/模糊指令）
- **代码**：`01-debugging-checklist.md`（调试清单）/ `02-evaluation-rubric.md`（评估标准模板）/ `03-llm-as-judge.md`（LLM 自动评估模板）/ `04-ab-test-template.md`（A/B 测试模板）/ `05-iteration-workflow.md`（迭代优化流程指南）
- **重点**：调试方法论、LLM-as-a-Judge 评估模式

---

### 阶段三：实战应用

#### Day07 - 代码生成与开发实战
- **核心**：代码生成 Prompt 结构（语言+框架+需求+约束+风格）、指定技术栈与版本、函数级代码生成、类设计生成、API 接口设计生成、SQL 生成、正则表达式生成、单元测试生成、代码审查 Prompt、代码重构 Prompt、代码解释 Prompt、Bug 修复 Prompt、文档注释生成、README 生成、多文件项目生成、代码风格规范约束、安全编码约束、Prompt 工程：用 Prompt 生成 Prompt（Meta-Prompting）
- **代码**：`01-code-generation.md`（代码生成模板合集）/ `02-code-review.md`（代码审查模板）/ `03-test-generation.md`（测试生成模板）/ `04-refactor-and-debug.md`（重构与调试模板）/ `05-meta-prompting.md`（元 Prompt 模板）
- **重点**：代码生成的结构化 Prompt、Meta-Prompting

#### Day08 - 文本处理与内容创作
- **核心**：文本摘要（单文档/多文档/分块摘要）、文本分类（情感/主题/意图）、信息抽取（实体/关系/事件）、文本翻译（多语言/风格化翻译）、文本改写（润色/简化/扩写/续写）、内容创作（文章/文案/邮件/报告/故事）、风格迁移、格式转换（文本→表格/文本→JSON/文本→Markdown大纲）、数据清洗与标准化、关键词提取与主题建模、问答系统 Prompt 设计（FAQ/RAG 预览）
- **代码**：`01-summarization.md`（摘要模板合集）/ `02-classification-extraction.md`（分类与抽取模板）/ `03-translation-rewrite.md`（翻译与改写模板）/ `04-content-creation.md`（内容创作模板合集）/ `05-format-conversion.md`（格式转换模板）
- **重点**：摘要的分块策略、信息抽取的 Schema 约束

#### Day09 - Agent与工具调用Prompt
- **核心**：Agent 概念（LLM 作为推理引擎）、ReAct Agent 模式（Thought→Action→Observation→Thought）、工具描述格式（function calling schema）、工具选择 Prompt 设计、多步规划与任务分解、Agent 记忆管理（短期/长期）、多 Agent 协作 Prompt、自我反思与修正（Reflection）、Agent 循环控制（何时终止/何时重试）、Function Calling / Tool Use Prompt 完整设计、OpenAI Function Calling 格式、Claude Tool Use 格式、Agent 应用场景（自动编程/数据分析/客服/搜索）
- **代码**：`01-react-agent.md`（ReAct Agent 完整模板）/ `02-tool-use-prompt.md`（工具调用 Prompt 模板）/ `03-multi-step-planning.md`（多步规划模板）/ `04-multi-agent-collaboration.md`（多 Agent 协作模板）/ `05-reflection-pattern.md`（自我反思模板）/ `06-customer-service-agent.md`（客服 Agent 完整案例）
- **重点**：ReAct 模式、Function Calling 工具描述格式

---

### 阶段四：安全与进阶

#### Day10 - Prompt安全与最佳实践
- **核心**：Prompt 注入攻击（直接注入/间接注入）、注入攻击案例分析、防护策略（输入过滤/指令分层/输出检查/权限隔离）、Jailbreak 越狱攻击与防护、信息泄露风险、Prompt 泄露防护（防止 System Prompt 被套出）、安全护栏（Guardrails）设计、内容安全（ toxicity/bias/harmful content）、Prompt 安全审计清单、Prompt 工程最佳实践总结（六大原则/结构化/可测试/可维护/可复用）、Prompt 工程未来展望（多模态/自动优化/Prompt 编译器）
- **代码**：`01-prompt-injection-defense.md`（注入防护模板）/ `02-jailbreak-defense.md`（越狱防护模板）/ `03-guardrails.md`（安全护栏配置）/ `04-security-audit-checklist.md`（安全审计清单）/ `05-best-practices-summary.md`（最佳实践总结文档）
- **重点**：Prompt 注入防护、安全护栏设计、最佳实践总结

---

## 目录结构

```
Prompt/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - Prompt工程概述与基础/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天 Prompt 模板
│       ├── 01-basic-prompt.md
│       ├── 02-token-and-context.md
│       ├── 03-chat-roles.md
│       └── README.md
├── Day02 - Prompt设计原则与技巧/
│   ├── README.md
│   └── Code/
│       ├── 01-six-principles.md
│       ├── 02-delimiters.md
│       ├── 03-output-format.md
│       └── 04-temperature-tuning.md
├── ...（Day03-Day09 同构）...
└── Day10 - Prompt安全与最佳实践/
    ├── README.md
    └── Code/
        ├── 01-prompt-injection-defense.md
        ├── 02-jailbreak-defense.md
        ├── 03-guardrails.md
        ├── 04-security-audit-checklist.md
        └── 05-best-practices-summary.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，以 `.md`（Prompt 模板）为主
- Prompt 模板使用 Markdown 格式，包含：模板说明、变量说明、完整模板、使用示例、预期输出
- 部分天数含 `.py` 文件（API 调用示例）和 `.json` 文件（配置）

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 3-4 小时 | 约 1-2 周 |
| 标准 | 业余学习 | 1-2 小时 | 约 2-3 周 |
| 保守 | 碎片时间 | 30 分钟 | 约 1 月 |

### 学习方法论

1. **边学边练**：每个 Prompt 模板都要在真实 LLM 中测试一遍
2. **对比实验**：修改 Prompt 中的措辞、结构、示例，对比输出差异
3. **记录发现**：建立自己的 Prompt 笔记，记录什么有效、什么无效
4. **场景代入**：将每天的 Prompt 模板应用到自己的工作场景中
5. **迭代优化**：好 Prompt 是改出来的，不要期望一次就完美
6. **关注社区**：Prompt Engineering 是快速发展的领域，关注最新研究

### 阶段性检查点

完成每个阶段后，应能回答以下问题：

- **阶段一完成后**：能否按照六大原则设计一个结构清晰、输出可控的 Prompt？
- **阶段二完成后**：能否用 CoT、结构化模板、链式调用解决复杂推理任务？
- **阶段三完成后**：能否针对代码生成、文本处理、Agent 等场景编写专业级 Prompt？
- **阶段四完成后**：能否识别 Prompt 安全风险并设计防护措施？

---

## 如何使用代码

### 方式一：直接复制到 LLM 对话框

最简单的使用方式——打开 ChatGPT / Claude / 文心一言 / 通义千问，将 `.md` 文件中的 Prompt 模板复制粘贴到对话框中，替换其中的 `{{变量}}` 占位符即可。

```markdown
# 示例：使用意图识别 Prompt 模板

1. 打开 prompts/tasks/intent_classification.md
2. 复制完整 Prompt 模板
3. 将 {{user_message}} 替换为实际用户输入
4. 粘贴到 LLM 对话框
5. 获取分类结果
```

### 方式二：用 Python 调用 LLM API

```python
# 安装 OpenAI 库
# pip install openai

from openai import OpenAI

client = OpenAI(api_key="your-api-key")

# 读取 Prompt 模板
with open("prompts/tasks/intent_classification.md", "r", encoding="utf-8") as f:
    prompt_template = f.read()

# 替换变量
user_message = "我想退货，订单号是 12345"
prompt = prompt_template.replace("{{user_message}}", user_message)

# 调用 API
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "你是一个意图识别系统。"},
        {"role": "user", "content": prompt}
    ],
    temperature=0
)

print(response.choices[0].message.content)
```

### 方式三：使用 LangChain / LlamaIndex

```python
# pip install langchain

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# 加载 Prompt 模板
prompt = PromptTemplate.from_file("prompts/tasks/intent_classification.md")

# 创建 LLM 链
llm = ChatOpenAI(model="gpt-4", temperature=0)
chain = prompt | llm

# 执行
result = chain.invoke({"user_message": "我想退货，订单号是 12345"})
print(result)
```

### Prompt 模板格式约定

本板块的 Prompt 模板统一使用以下格式：

```markdown
# [模板名称]

## 模板说明
- 用途：[一句话描述]
- 适用模型：[GPT-4 / Claude / 通用]
- 变量：[列出所有 {{变量}}]

## 完整模板

[实际 Prompt 内容，含 {{变量}} 占位符]

## 使用示例

### 输入
[替换变量后的完整 Prompt]

### 预期输出
[期望的 LLM 输出]

## 调优建议
[温度建议、注意事项等]
```

---

## 知识点速查

### Prompt 六大设计原则速查

| 原则 | 核心要点 | 示例 |
|------|---------|------|
| 清晰明确 | 用明确的语言描述任务 | "总结以下文章的核心观点" 而非 "看看这个" |
| 具体详尽 | 提供足够的细节和约束 | 指定字数、格式、风格、受众 |
| 提供上下文 | 给出背景信息和相关知识 | "你是一位电商客服专家，处理退换货问题" |
| 角色设定 | 为 LLM 赋予专业身份 | "你是一位资深 Python 开发者" |
| 指定格式 | 明确输出格式 | "以 JSON 格式输出，包含 intent 和 confidence 字段" |
| 设定约束 | 限制范围和边界 | "只从给定选项中选择，不要编造新选项" |

### Prompt 核心技术速查

| 技术 | 全称 | 触发方式 | 适用场景 | 对应天数 |
|------|------|---------|---------|---------|
| Zero-Shot | 零样本 | 直接给出指令 | 简单任务、通用知识 | Day03 |
| Few-Shot | 少样本 | 提供示例（Input→Output） | 分类、格式控制、风格模仿 | Day03 |
| CoT | 思维链 | "Let's think step by step" | 数学、逻辑、推理 | Day04 |
| ReAct | 推理+行动 | Thought→Action→Observation | 工具调用、多步任务 | Day04/Day09 |
| Self-Consistency | 自洽性 | 多次采样取多数 | 高精度推理 | Day04 |
| Prompt Chaining | 链式调用 | 前一步输出→后一步输入 | 复杂任务分解 | Day05 |
| Reflection | 自我反思 | 评估→修正→再生成 | 质量提升 | Day09 |

### Prompt 结构框架速查

| 框架 | 组成 | 适用场景 | 对应天数 |
|------|------|---------|---------|
| RTF | Role + Task + Format | 快速构建 | Day05 |
| CRISPE | Capacity+Role+Insight+Statement+Personality+Experiment | 复杂任务 | Day05 |
| CREATE | Context+Request+Explanation+Action+Tone+Extras | 商业场景 | Day05 |
| BRIC | Background+Role+Instructions+Constraints | 通用 | Day05 |

### 温度参数速查

| Temperature | 行为 | 适用场景 |
|-------------|------|---------|
| 0.0 | 确定性输出（每次相同） | 分类、抽取、代码生成 |
| 0.1-0.3 | 低随机性 | 事实问答、摘要、翻译 |
| 0.4-0.7 | 适中随机性 | 创意写作、对话、建议 |
| 0.8-1.0 | 高随机性 | 头脑风暴、创意故事 |
| >1.0 | 极高随机性（不推荐） | 实验用途 |

### 分隔符使用速查

| 分隔符 | 示例 | 适用场景 |
|--------|------|---------|
| 三重引号 | """text""" | 通用文本隔离 |
| 三重反引号 | \`\`\`text\`\`\` | 代码块隔离 |
| XML 标签 | `<input>text</input>` | 结构化输入（Claude 推荐） |
| 井号分隔 | ### text ### | 简单分隔 |
| 自定义标记 | [START] text [END] | 防止注入 |

### LLM 角色体系速查

| 角色 | 作用 | 示例 |
|------|------|------|
| System | 设定 LLM 身份和行为规范 | "你是一个电商客服助手" |
| User | 用户输入 | "我想退货" |
| Assistant | LLM 回复（可作为上下文） | "好的，请提供订单号" |
| Tool | 工具调用结果（Function Calling） | {"order_status": "已发货"} |

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **LLM / RAG / Agent** | Prompt 是 RAG 和 Agent 的基础，检索增强生成和工具调用都依赖 Prompt 设计 |
| **Python** | 用 Python 调用 LLM API、构建 Prompt 管道 |
| **FastAPI / Flask** | 将 Prompt 工程封装为 API 服务 |
| **Docker** | AI 应用容器化部署 |
| **数据分析** | 用 Prompt 辅助数据分析和报告生成 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering) - OpenAI 官方指南
- [Anthropic Prompt Engineering](https://docs.anthropic.com/claude/docs/prompt-engineering) - Claude 官方指南
- [Prompt Engineering Guide (DAIR.AI)](https://www.promptingguide.ai/) - 开源 Prompt 教程
- [Learn Prompting](https://learnprompting.org/) - 系统化 Prompt 课程
- [Awesome ChatGPT Prompts](https://github.com/f/awesome-chatgpt-prompts) - Prompt 集合
- [LangChain Docs](https://python.langchain.com/docs/) - LangChain 文档

---

## 贡献与反馈

本学习手册为原创内容，参考 GitHub 优质仓库的文档风格但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用精准的 Prompt 解锁 LLM 的全部潜力！**
