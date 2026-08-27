# Day03 Code - Prompt 管理指南

本目录包含 Day03「Prompt 管理」的全部代码文件，演示 PromptTemplate 和 ChatPromptTemplate 的模板化管理。

## 文件清单

| 文件 | 用途 | 是否需要 API Key |
|------|------|-----------------|
| `01_prompt_template.py` | PromptTemplate 基础（5 种使用模式） | 第 6 模式需要 |
| `02_chat_prompt_template.py` | ChatPromptTemplate 多角色模板 | 第 6 节需要 |
| `03_messages_placeholder.py` | MessagesPlaceholder 动态消息 | 第 5 节需要 |
| `04_template_serialization.py` | 模板序列化与文件加载 | 第 8 节需要 |

---

## PromptTemplate vs ChatPromptTemplate 选择决策表

| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单单变量 Prompt | PromptTemplate | 轻量简单 |
| 需要 System 设定 | ChatPromptTemplate | 支持角色体系 |
| 多轮对话 | ChatPromptTemplate + MessagesPlaceholder | 管理历史消息 |
| Few-Shot 示例 | ChatPromptTemplate + MessagesPlaceholder | 动态插入示例 |
| 与 ChatModel 配合 | ChatPromptTemplate | 原生支持消息列表 |
| 需要序列化 | 两者都支持 | load_prompt 统一加载 |

> **推荐**：现代开发统一使用 `ChatPromptTemplate`，它功能更全、与 ChatModel 配合更好。

---

## 模板序列化最佳实践

### 1. 文件组织

```
prompts/
├── qa_prompt.json          # 问答模板
├── summary_prompt.yaml     # 摘要模板
├── translate_prompt_v1.json # 翻译模板 v1
├── translate_prompt_v2.json # 翻译模板 v2
└── chat/
    ├── customer_service.json  # 客服模板
    └── few_shot.json          # Few-Shot 模板
```

### 2. 版本管理

- 用版本号命名文件：`prompt_v1.0.json`
- 用 Git 管理变更，记录每次修改
- 重要 Prompt 保留多个版本做 A/B 测试

### 3. JSON 结构

```json
{
  "_type": "prompt",
  "template": "你是{role}，请回答：{question}",
  "input_variables": ["role", "question"]
}
```

### 4. YAML 结构（可读性更好）

```yaml
_type: prompt
template: |
  你是{role}，请回答：
  {question}
input_variables:
  - role
  - question
```

---

## PromptHub 使用指南

### 从 Hub 加载

```python
from langchain import hub

# 拉取官方/社区 Prompt
prompt = hub.pull("rlm/rag-prompt")
```

### 推送到 Hub

```python
from langchain import hub

# 推送自己的 Prompt（需注册账号）
hub.push("your-username/your-prompt-name", prompt)
```

### Hub 使用建议

| 场景 | 建议 |
|------|------|
| 快速原型 | 从 Hub 拉取现成 Prompt |
| 生产环境 | 自定义 Prompt，不依赖 Hub |
| 团队协作 | 建立私有 Hub 或用文件管理 |

---

## 与 Prompt 板块知识衔接

Prompt 板块讲解的理论框架，可用 ChatPromptTemplate 实现：

### CRISPE 框架

| 字母 | 含义 | 模板实现 |
|------|------|---------|
| C | Capacity（能力） | system: "你的能力是{capacity}" |
| R | Role（角色） | system: "你是{role}" |
| I | Insight（背景） | system: "背景：{insight}" |
| S | Statement（任务） | human: "{statement}" |
| P | Personality（风格） | system: "用{personality}语气回答" |
| E | Experiment（实验） | 多版本测试 |

### RTF 框架

```python
rtf_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是{role}。"),
    ("human", "任务：{task}。输出格式：{format}。"),
])
```

### Prompt 板块六大原则对应

| 原则 | LangChain 实现 |
|------|---------------|
| 明确指令 | ChatPromptTemplate + System 设定 |
| 提供参考 | MessagesPlaceholder 插入 Few-Shot |
| 分解任务 | 多步骤 Chain（Day05） |
| 给思考时间 | System 中要求 CoT |
| 使用外部工具 | bind_tools（Day09） |
| 迭代优化 | 序列化 + 版本管理 |

---

## 模板设计规范

### 1. 变量命名

```python
# ✅ 好的命名：清晰有意义
template = "你是{role}，请{style}地回答：{question}"

# ❌ 差的命名：含糊不清
template = "你是{a}，请{b}：{c}"
```

### 2. System 设定规范

```python
# ✅ 好的 System：角色 + 规范 + 限制
("system", """你是 ChainQA 客服助手。
规范：
1. 语气专业亲切
2. 回答不超过 100 字
3. 不确定时建议联系人工客服""")

# ❌ 差的 System：太简单
("system", "你是助手")
```

### 3. 变量隔离

```python
# ✅ 变量用 {} 隔离，避免与 JSON 的 {{}} 冲突
template = "输出 JSON：{{\"name\": \"{name}\"}}"

# 注意：模板中要输出 JSON 大括号时需要双写 {{ }}
```

---

## 常见问题

### 问题 1：`KeyError: 'variable'`

**原因**：format 时缺少变量。

**解决**：检查 `input_variables` 与 format 参数是否一致。

### 问题 2：JSON 大括号冲突

**原因**：模板中要输出 JSON，`{}` 被误认为变量。

**解决**：JSON 大括号双写 `{{` `}}`。

### 问题 3：MessagesPlaceholder 报错

**原因**：未传 history 变量。

**解决**：设置 `optional=True` 或确保传入空列表 `[]`。

---

## 运行指南

```bash
cd "Day03 - Prompt管理/Code"

python 01_prompt_template.py          # 基础模板
python 02_chat_prompt_template.py      # 多角色模板
python 03_messages_placeholder.py      # 动态消息
python 04_template_serialization.py     # 序列化
```

---

> 掌握 Prompt 管理后，进入 Day04 学习 Output Parsers 输出解析器。
