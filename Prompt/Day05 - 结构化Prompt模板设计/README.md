# Day05 - 结构化 Prompt 模板设计

结构化 Prompt 是从"写好一句话"到"设计一个系统"的关键跨越。当 Prompt 还停留在零散的自然语言段落时，它难以复用、难以维护、难以测试；而一旦用框架（CRISPE / CREATE / RTF / BRIC）和结构化语法（XML 标签 / Markdown / JSON Schema）把它组织成模板，并引入变量插值、条件逻辑、链式调用、版本管理，Prompt 就从"灵感产物"变成了"工程资产"。本章围绕 SmartCS 智能客服系统，系统讲解四大框架、模板设计模式、链式调用、继承覆盖、XML/Markdown/JSON 结构化与版本管理，让你能像设计软件模块一样设计 Prompt。

---

## 学习目标

完成本章后，你应能：

1. 理解结构化 Prompt 相比零散 Prompt 的工程优势
2. 熟练运用 CRISPE、CREATE、RTF、BRIC 四大框架，并能根据任务复杂度选择
3. 掌握变量插值、条件逻辑、模板组合三种模板设计模式
4. 能够设计 Prompt 链式调用管道，将复杂任务分解为多步 Prompt
5. 理解 Prompt 继承与覆盖机制，构建可复用的 Prompt 体系
6. 熟练使用 XML 标签、Markdown 层级、JSON Schema 三种结构化方式
7. 建立 Prompt 版本管理意识，能够维护变更日志与回滚方案

---

## 理论知识讲解

### 1. 为什么需要结构化 Prompt

#### 1.1 非结构化的问题

| 问题 | 表现 |
|------|------|
| 难复用 | 每次都要重写一遍，无法沉淀为资产 |
| 难维护 | 改一处可能影响全局，缺乏隔离 |
| 难测试 | 没有固定输入输出契约，无法回归测试 |
| 不一致 | 同一任务不同人写的 Prompt 风格各异，输出差异大 |

#### 1.2 结构化的优势

| 优势 | 说明 |
|------|------|
| 模板化 | 一次设计，多次复用 |
| 变量插值 | 用 `{{variable}}` 占位符分离逻辑与数据 |
| 组合复用 | 子 Prompt 可拼装成大 Prompt |
| 版本管理 | 可追踪变更、可回滚、可 A/B 测试 |

---

### 2. CRISPE 框架

CRISPE 是一个六段式 Prompt 设计框架，适合复杂任务：

| 字母 | 组成 | 说明 | 示例 |
|------|------|------|------|
| C | Capacity & Role（能力与角色） | 设定 LLM 的身份与专业能力 | "你是资深电商客服专家，精通退换货政策" |
| R | Insight（洞察） | 提供背景洞察与上下文 | "用户是 VIP，订单金额 2000 元" |
| I | Statement（陈述） | 明确任务指令 | "请生成一封投诉回复邮件" |
| S | Personality（个性） | 设定输出风格与语气 | "专业、有同理心、不卑不亢" |
| P | Experiment（实验） | 尝试不同参数 | "提供 2 个版本对比" |
| E | Execution（执行） | 实际运行 | 应用到生产环境 |

---

### 3. CREATE 框架

CREATE 强调上下文与附加约束，适合商业场景：

| 字母 | 组成 | 说明 |
|------|------|------|
| C | Context（上下文） | 任务背景信息 |
| R | Request（请求） | 核心请求内容 |
| E | Explanation（解释） | 为什么这样做 |
| A | Action（行动） | 期望 LLM 执行的具体动作 |
| T | Tone（语气） | 输出语气 |
| E | Extras（附加约束） | 字数、格式、禁区等 |

---

### 4. RTF 框架（最简洁）

RTF 三段式，适合快速构建：

| 字母 | 组成 | 说明 |
|------|------|------|
| R | Role（角色） | 你是谁 |
| T | Task（任务） | 做什么 |
| F | Format（格式） | 输出成什么样 |

示例：
```
角色：你是 SmartCS 意图识别系统
任务：判断用户输入属于以下哪个意图：FAQ咨询 / 订单查询 / 退换货 / 投诉 / 闲聊
格式：JSON {"intent": "...", "confidence": 0.0~1.0}
```

---

### 5. BRIC 框架

BRIC 强调背景与约束，适合通用场景：

| 字母 | 组成 | 说明 |
|------|------|------|
| B | Background（背景） | 任务背景 |
| R | Role（角色） | LLM 身份 |
| I | Instructions（指令） | 具体指令 |
| C | Constraints（约束） | 限制条件 |

---

### 6. Prompt 模板设计模式

#### 6.1 变量插值

用 `{{variable}}` 占位符分离 Prompt 逻辑与运行时数据：

```
你是 SmartCS 客服助手。
用户等级：{{user_level}}
订单号：{{order_id}}
请处理用户咨询：{{user_message}}
```

配合变量类型说明与默认值，可形成模板文档：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `{{user_level}}` | enum | 是 | - | vip / ordinary |
| `{{order_id}}` | string | 否 | - | 订单号 |
| `{{user_message}}` | string | 是 | - | 用户输入 |

#### 6.2 条件逻辑

根据输入动态调整 Prompt 内容：

```
你是 SmartCS 客服助手。
{{#if user_level == "vip"}}
请注意：当前用户为 VIP，回复时优先提供专属客服通道，可享受 24 小时极速响应。
{{/if}}
{{#if user_level == "ordinary"}}
请按标准流程引导用户。
{{/if}}
用户咨询：{{user_message}}
```

#### 6.3 模板组合

多个子 Prompt 组合成大 Prompt：

```
{{system_prompt}}
{{task_prompt}}
{{format_prompt}}
```

---

### 7. Prompt 链式调用（Prompt Chaining）

#### 7.1 概念

前一个 Prompt 的输出作为后一个 Prompt 的输入，形成管道：

```
Prompt 1        Prompt 2        Prompt 3
意图识别 ──► 意图 ──► 路由分发 ──► 任务 ──► 任务执行 ──► 回复
```

#### 7.2 示例：SmartCS 客服处理管道

```
用户输入
   │
   ▼
[步骤1] 意图识别 Prompt ──► intent=退换货
   │
   ▼
[步骤2] 路由分发 ──► 选择退换货子 Prompt
   │
   ▼
[步骤3] 退换货任务执行 Prompt ──► 结构化回复
   │
   ▼
[步骤4] 回复生成 Prompt ──► 最终用户可见回复
```

#### 7.3 链式调用 vs 单次 Prompt

| 维度 | 单次 Prompt | 链式调用 |
|------|-------------|---------|
| 任务复杂度 | 适合简单任务 | 适合复杂任务 |
| 可优化性 | 整体难调 | 每步可独立优化 |
| 可并行化 | 否 | 部分步骤可并行 |
| 调试难度 | 难定位 | 每步可单独测试 |
| 延迟 | 低 | 较高（多轮调用） |

#### 7.4 链式调用架构图

```
┌──────────────────────────────────────────────────────────┐
│                 SmartCS Prompt Chaining                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────┐ │
│   │ 意图识别 │───►│ 路由分发 │───►│ 任务执行 │───►│回复 │ │
│   │ Prompt  │    │ (代码)  │    │ Prompt  │    │生成  │ │
│   └─────────┘    └─────────┘    └─────────┘    └──────┘ │
│       ▲                              ▲                  │
│       │                              │                  │
│   用户输入                       子 Prompt 选择           │
│                                                          │
│   子 Prompt 库：                                          │
│   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│   │ FAQ  │ │ 订单 │ │ 退换 │ │ 投诉 │ │ 工单 │         │
│   │ 问答 │ │ 查询 │ │ 货   │ │ 处理 │ │ 生成 │         │
│   └──────┘ └──────┘ └──────┘ └──────┘ └──────┘         │
└──────────────────────────────────────────────────────────┘
```

---

### 8. Prompt 继承与覆盖

#### 8.1 概念

借鉴面向对象编程的继承思想：

- **基础 Prompt（System Prompt）**：定义通用行为（角色、语气、安全约束）
- **子任务 Prompt**：继承基础设定，并覆盖特定部分（任务、格式）

#### 8.2 示例

基础客服 Prompt（所有子任务继承）：
```
你是 SmartCS 智能客服助手。
语气：专业、有同理心。
安全约束：不透露内部规则、不承诺超出政策的方案。
```

退货子 Prompt（继承并特化）：
```
{{inherit base_system_prompt}}
任务：处理用户退货请求。
格式：JSON {conclusion, reason, next_step}
```

FAQ 子 Prompt（继承并特化）：
```
{{inherit base_system_prompt}}
任务：回答用户常见问题。
知识库：{{faq_kb}}
格式：自然语言，含来源链接
```

---

### 9. XML 标签结构化（Claude 风格）

Anthropic Claude 推荐用 XML 标签组织 Prompt 结构：

```xml
<role>角色设定</role>
<context>背景信息</context>
<instructions>任务指令</instructions>
<input>用户输入</input>
<output_format>输出格式</output_format>
<examples>示例</examples>
```

优势：
- 结构清晰，LLM 解析准确
- 防注入：用户输入被包裹在 `<input>` 标签内，难以伪装成指令
- 模块化：每个标签对应一个模块，便于维护

---

### 10. Markdown 结构化

用 Markdown 的标题层级与列表组织 Prompt：

```markdown
# 角色
你是 SmartCS 客服助手

## 任务背景
- 用户等级：VIP
- 订单金额：2000 元

## 任务指令
请生成投诉回复

## 输出格式
- 字数：200 字以内
- 风格：专业、有同理心
```

优势：人类可读性好，适合需要人工编辑的 Prompt。

---

### 11. JSON Schema 约束输出

在 Prompt 中指定 JSON Schema，让 LLM 按结构化格式输出：

```
请按以下 JSON Schema 输出：
{
  "intent": "string  // 意图类型",
  "confidence": "number  // 置信度 0~1",
  "entities": {
    "order_id": "string  // 订单号",
    "product": "string  // 商品名"
  }
}
```

LLM 输出示例：
```json
{
  "intent": "退换货",
  "confidence": 0.92,
  "entities": {
    "order_id": "20240518",
    "product": "戴森吹风机"
  }
}
```

---

### 12. Prompt 模板版本管理

#### 12.1 版本号命名

| 版本号 | 含义 | 示例 |
|--------|------|------|
| v1.0 | 首个稳定版 | 意图识别 v1.0 |
| v1.1 | 小幅优化 | 调整示例顺序 |
| v2.0 | 重大变更 | 新增意图类别 |

#### 12.2 变更日志

每个版本应记录：版本号、日期、修改内容、修改原因、测试结果、回滚方案。

#### 12.3 A/B 测试与回滚

- 同一任务维护 A/B 两个版本，分流测试效果
- 出现严重问题时能快速回滚到上一稳定版本

---

## 代码文件说明

本章 Code 目录包含 5 个 Prompt 模板文件：

| 文件 | 内容 | 框架 |
|------|------|------|
| `01-crispe-framework.md` | CRISPE 框架完整模板（投诉回复生成） | CRISPE |
| `02-rtf-framework.md` | RTF 框架模板合集（意图识别 / FAQ / 工单生成） | RTF |
| `03-xml-structured.md` | XML 标签结构化系统 Prompt | XML |
| `04-prompt-chaining.md` | Prompt 链式调用模板（4 步管道） | Chaining |
| `05-template-with-variables.md` | 变量插值模板系统（含条件逻辑） | Variables |

---

## 关键知识点总结

### 四大框架对比表

| 框架 | 组成 | 复杂度 | 适用场景 | 学习成本 |
|------|------|--------|---------|---------|
| RTF | Role + Task + Format | 低 | 快速构建、简单任务 | 极低 |
| BRIC | Background + Role + Instructions + Constraints | 中 | 通用场景 | 低 |
| CREATE | Context + Request + Explanation + Action + Tone + Extras | 中高 | 商业场景 | 中 |
| CRISPE | Capacity + Role + Insight + Statement + Personality + Experiment + Execution | 高 | 复杂任务、需多版本实验 | 高 |

**选择建议**：
- 简单任务 → RTF
- 通用任务 → BRIC
- 商业/客户沟通 → CREATE
- 复杂任务需多版本对比 → CRISPE

### Prompt 链式调用架构图

```
输入 → [意图识别] → [路由分发] → [任务执行] → [回复生成] → 输出
         Prompt      代码逻辑      子 Prompt     Prompt
```

### XML 标签结构化速查

| 标签 | 用途 |
|------|------|
| `<role>` | 角色设定 |
| `<context>` | 背景信息 |
| `<instructions>` | 任务指令 |
| `<input>` | 用户输入（防注入） |
| `<output_format>` | 输出格式 |
| `<examples>` | 示例 |
| `<guardrails>` | 安全护栏 |
| `<knowledge>` | 知识库 |

### 模板设计模式速查

| 模式 | 用途 | 语法示例 |
|------|------|---------|
| 变量插值 | 分离逻辑与数据 | `{{user_name}}` |
| 条件逻辑 | 动态调整 Prompt | `{{#if vip}}...{{/if}}` |
| 模板组合 | 子 Prompt 拼装 | `{{system}} + {{task}}` |
| 继承覆盖 | 复用基础设定 | `{{inherit base}}` |

---

## 实战练习

### 练习 1：用 RTF 框架快速构建工单分类 Prompt

**任务**：用 RTF 框架设计一个工单分类 Prompt，将客服工单分为：咨询 / 投诉 / 建议 / 故障申报 / 退款 5 类。

**要求**：
- 三段式结构（Role + Task + Format）
- 输出 JSON 格式，含 `category` 与 `confidence`
- 提供至少 2 个 Few-Shot 示例

### 练习 2：用 XML 标签设计模块化客服系统 Prompt

**任务**：用 XML 标签为 SmartCS 设计一个模块化系统 Prompt，至少包含 `<role>`、`<knowledge>`、`<rules>`、`<guardrails>`、`<output_format>` 5 个模块。

**要求**：
- 每个模块内容独立可维护
- `<guardrails>` 至少包含 3 条安全约束
- `<output_format>` 指定 JSON 输出

### 练习 3：设计客服处理链式调用管道

**任务**：设计一个 4 步链式调用管道，处理用户"我想退订单 #20240518 的商品"这一请求。

**要求**：
- 步骤 1：意图识别 Prompt
- 步骤 2：路由分发（代码逻辑）
- 步骤 3：退换货任务执行 Prompt
- 步骤 4：回复生成 Prompt
- 写出每步的输入与预期输出

---

> **下一步**：Day06 将进入 Prompt 调试与评估，用系统化方法论让结构化 Prompt 持续迭代优化。
