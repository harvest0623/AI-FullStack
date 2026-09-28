# Day06 - Prompt 工程化集成

Prompt 不只是写好一段文字，更是将其作为**代码资产**来管理——模板化、变量化、版本化、测试化。当应用里只有 3 条 Prompt 时，散落在代码里尚可维护；一旦 Prompt 数量上百、需要多人协作、需要 A/B 测试、需要回滚，没有工程化管理就会变成灾难。本章把 Prompt 当作"特殊代码"来对待：用模板引擎实现变量插值与条件逻辑，用 YAML 集中存储多版本模板，用语义化版本号管理变更，用断言式测试框架保证质量，用缓存策略降低成本。这是从"Prompt 工程"走向"Prompt 工程化"的关键一跃，也是 `AISearch` 项目从 demo 走向生产的基础。

---

## 学习目标

完成本章后，你应能：

1. 说出 Prompt 散落管理的四大痛点，并解释工程化管理的五个目标。
2. 用 Jinja2 实现变量插值、条件逻辑、循环、模板继承与组合。
3. 对比字符串模板、文件加载、Jinja2 三种管理方式的优劣并合理选型。
4. 设计 Markdown / YAML / JSON 三种 Prompt 模板格式并说明适用场景。
5. 用语义版本号管理 Prompt 变更，实现版本对比与回滚。
6. 搭建 Prompt 测试框架，编写包含 / 格式（JSON Schema）/ 正则 / 不包含四类断言。
7. 根据用户类型、对话历史、任务复杂度动态构建 Prompt。
8. 实现内容哈希缓存与语义缓存，并说明缓存失效策略。
9. 阐述 "Prompt as Code" 理念，把 Prompt 文件与 Python 代码解耦。

---

## 理论知识讲解

### 6.1 Prompt 工程化需求

#### 6.1.1 问题：Prompt 散落的四大痛点

| 痛点 | 表现 | 后果 |
|------|------|------|
| 散落各处 | Prompt 写死在 `.py` 各函数里 | 改一处要搜全代码 |
| 难以复用 | 同样的 system prompt 复制多份 | 改一处要改多处 |
| 无法版本管理 | 改了 Prompt 不知道改了什么、何时改的 | 出问题无法回滚 |
| 无法测试 | 改完 Prompt 直接上线 | 线上回归靠运气 |

#### 6.1.2 目标：工程化管理的五个目标

1. **模板化**：变量与正文分离，正文写一次、变量传多次。
2. **变量化**：用占位符 `{{var}}` 标注变量，支持默认值与类型说明。
3. **可测试**：每条 Prompt 都能用一组输入→断言验证。
4. **可版本管理**：语义版本号 + 变更日志，可回滚。
5. **可组合**：多个子模板组合成完整 Prompt，支持继承。

### 6.2 Prompt 模板系统设计

#### 6.2.1 变量插值

用 `{{variable}}` 占位符标注变量，渲染时替换为实际值。

```text
模板：你是{{role}}，请用{{tone}}的语气回答用户问题：{{question}}
渲染：你是客服专家，请用专业的语气回答用户问题：怎么退款？
```

支持**默认值**：`{{name | default("用户")}}`，未传值时使用默认。

支持**变量类型说明**：在元数据中标注 `question: string, required: true`。

#### 6.2.2 条件逻辑

用 `{% if condition %}...{% endif %}` 实现分支，典型场景：VIP 与普通用户不同话术。

```text
{% if is_vip %}
您是 VIP 用户，享受 7x24 专属服务。
{% else %}
您好，请描述您的问题。
{% endif %}
```

#### 6.2.3 模板继承

基础模板定义骨架，子模板覆盖特定部分（块）。

```text
基础模板 base.j2：
你是 AISearch 助手。
{% block rules %}默认规则{% endblock %}
请回答：{{question}}

子模板 vip.j2：
{% extends "base.j2" %}
{% block rules %}VIP 规则：优先响应{% endblock %}
```

#### 6.2.4 模板组合

多个子模板拼接成完整 Prompt：`system_prompt = role_block + rules_block + few_shot_block`。

### 6.3 Python 中管理 Prompt 模板

#### 方式一：字符串模板

```python
# str.format
template = "你是{role}，回答：{question}"
prompt = template.format(role="客服", question="怎么退款？")

# f-string（不推荐存模板，变量需硬编码在代码里）
prompt = f"你是{role}，回答：{question}"
```

**优点**：零依赖。
**缺点**：不支持条件 / 循环 / 继承；变量多了难维护。

#### 方式二：文件加载

把模板存成 Markdown / YAML / JSON 文件，运行时读取。

```python
from pathlib import Path
template = Path("prompts/qa.md").read_text(encoding="utf-8")
prompt = template.replace("{{question}}", "怎么退款？")
```

**优点**：与代码解耦，非工程师可编辑。
**缺点**：仍需自己实现变量替换与条件逻辑。

#### 方式三：Jinja2 模板引擎

```bash
pip install jinja2
```

```python
from jinja2 import Template
t = Template("你是 {{role}}，{% if vip %}VIP{% endif %}回答：{{question}}")
prompt = t.render(role="客服", vip=True, question="怎么退款？")
```

**优点**：变量 / 条件 / 循环 / 继承 / 过滤器全支持，生态成熟。
**缺点**：多一个依赖；模板语法有学习成本。

#### 三种方式对比

| 方式 | 依赖 | 变量 | 条件 | 继承 | 适用 |
|------|------|------|------|------|------|
| 字符串模板 | 无 | ✓ | ✗ | ✗ | 极简单场景 |
| 文件加载 | 无 | 需自实现 | 需自实现 | ✗ | 与代码解耦 |
| Jinja2 | jinja2 | ✓ | ✓ | ✓ | 生产首选 |

### 6.4 模板格式设计

#### 6.4.1 Markdown 格式（含元数据）

```markdown
---
model: gpt-4o-mini
temperature: 0.3
variables:
  - name: question
    type: string
    required: true
  - name: tone
    type: string
    default: 专业
---

你是 AISearch 客服，请用 {{tone}} 的语气回答：{{question}}
```

**优点**：人类可读，方便非工程师编辑。

#### 6.4.2 YAML 格式

```yaml
qa:
  version: "1.2.0"
  model: gpt-4o-mini
  template: |
    你是客服，回答：{{question}}
summarize:
  version: "1.0.0"
  model: gpt-4o
  template: |
    总结以下文本：{{text}}
```

**优点**：结构化存储多个模板，便于批量管理。

#### 6.4.3 JSON 格式

```json
{
  "qa": {"version": "1.2.0", "template": "你是客服，回答：{{question}}"}
}
```

**优点**：程序友好，支持复杂嵌套结构；适合 API 传输。

### 6.5 Prompt 版本管理

#### 6.5.1 语义版本号

`v主.次.修`（Major.Minor.Patch）：

| 变更类型 | 版本位 | 示例 |
|---------|--------|------|
| 不兼容变更（输出格式变了） | 主版本 | 1.0.0 → 2.0.0 |
| 兼容新增（加变量、加示例） | 次版本 | 1.0.0 → 1.1.0 |
| Bug 修复（错别字、调措辞） | 修订号 | 1.0.0 → 1.0.1 |

#### 6.5.2 变更日志

```yaml
changelog:
  - version: "1.2.0"
    date: "2025-03-15"
    change: "增加 few-shot 示例"
    reason: "提升分类准确率 8%"
  - version: "1.1.0"
    date: "2025-03-01"
    change: "新增 tone 变量"
    reason: "支持多语气切换"
  - version: "1.0.0"
    date: "2025-02-01"
    change: "初始版本"
    reason: "首次上线"
```

#### 6.5.3 版本对比与回滚

- **diff**：对比两个版本模板正文，定位改动点。
- **回滚**：发现新版本线上回归，立即切回上一版本。

### 6.6 Prompt 测试框架

#### 6.6.1 测试类型

| 类型 | 含义 | 触发时机 |
|------|------|---------|
| 单元测试 | 给定输入 → 验证输出格式 / 内容 | 每次提交 |
| 回归测试 | 改 Prompt 后重跑所有测试 | 每次改 Prompt |

#### 6.6.2 断言类型

| 断言 | 含义 | 示例 |
|------|------|------|
| 包含断言 | 输出包含某关键词 | `assert "退款" in output` |
| 格式断言 | 输出符合 JSON Schema | `validate(output, schema)` |
| 正则断言 | 输出匹配正则 | `re.match(r"\d{4}-\d{2}-\d{2}", output)` |
| 不包含断言 | 输出不包含某词 | `assert "抱歉" not in output` |

#### 6.6.3 测试用例设计

- **正常用例**：典型输入，期望正常输出。
- **边界用例**：空输入、超长输入、特殊字符。
- **异常用例**：变量缺失、类型错误。

### 6.7 动态 Prompt 构建

根据上下文动态选择模板与参数：

| 维度 | 影响 | 示例 |
|------|------|------|
| 用户类型 | 选不同模板 | VIP 用 vip.j2，普通用 base.j2 |
| 对话历史 | 决定是否带历史 | 多轮对话拼接历史消息 |
| 任务复杂度 | 调整参数 | 复杂任务 temperature=0.2，创作 temperature=0.9 |
| Few-Shot | 动态拼示例 | 按相似度检索 3 个示例拼到 prompt |

### 6.8 Prompt 缓存策略

#### 6.8.1 内容哈希缓存

相同输入 → 命中缓存直接返回输出。

```python
import hashlib
key = hashlib.sha256(f"{prompt}|{model}|{temp}".encode()).hexdigest()
if key in cache: return cache[key]
```

#### 6.8.2 语义缓存

语义相似输入 → 复用输出（需 Embedding + 相似度阈值）。

```text
新输入 → Embedding → 与缓存向量比对 → 余弦相似度 > 0.95 → 命中
```

#### 6.8.3 缓存失效

- Prompt 模板变更 → 清空该模板的所有缓存。
- 模型升级 → 清空该模型缓存。
- TTL 过期 → 自动失效。

### 6.9 Prompt 与代码解耦

#### 6.9.1 分离原则

- **Prompt 文件**：存放在 `prompts/` 目录，按业务分文件。
- **Python 代码**：只负责加载、渲染、调用 LLM。
- **变量**：通过参数传入，不在 Prompt 文件里硬编码。

#### 6.9.2 Prompt 即代码（Prompt as Code）

把 Prompt 当作"特殊代码"来对待：

1. **版本控制**：Prompt 文件入 Git，每次改动有 commit。
2. **代码评审**：Prompt 改动走 PR 评审。
3. **CI 测试**：Prompt 改动自动跑测试。
4. **环境隔离**：dev/staging/prod 用不同版本。
5. **可视化编辑**：用 Prompt 编辑器（如 Promptfoo / LangSmith）管理。

---

## 代码文件说明

| 文件 | 用途 | 核心类 |
|------|------|--------|
| `01_prompt_template.py` | Prompt 模板系统 | `PromptTemplate` |
| `02_prompt_manager.py` | Prompt 管理器 | `PromptManager` |
| `03_dynamic_prompt.py` | 动态 Prompt 构建 | `DynamicPromptBuilder` |
| `04_prompt_testing.py` | Prompt 测试框架 | `PromptTestRunner` |

详细使用方式见 `Code/README.md`。

---

## 关键知识点总结

### 模板管理方式对比表

| 方式 | 依赖 | 条件 | 继承 | 测试友好 | 推荐 |
|------|------|------|------|---------|------|
| 字符串模板 | 无 | ✗ | ✗ | 一般 | 仅极简场景 |
| 文件加载 | 无 | 需自实现 | ✗ | 一般 | 解耦首选 |
| Jinja2 | jinja2 | ✓ | ✓ | 优秀 | 生产首选 |

### Jinja2 语法速查

| 语法 | 含义 | 示例 |
|------|------|------|
| `{{var}}` | 变量插值 | `{{name}}` |
| `{% if %}` | 条件 | `{% if x %}A{% endif %}` |
| `{% for %}` | 循环 | `{% for i in items %}{{i}}{% endfor %}` |
| `{% extends %}` | 继承 | `{% extends "base" %}` |
| `{% block %}` | 块 | `{% block name %}默认{% endblock %}` |
| `\|default` | 默认值 | `{{name|default("匿名")}}` |
| `\|upper` | 过滤器 | `{{name|upper}}` |
| `{# comment #}` | 注释 | `{# 仅说明 #}` |

### Prompt 版本管理规范

| 变更类型 | 版本位 | 是否兼容 | 是否需测试 |
|---------|--------|---------|-----------|
| 主版本（Major） | 1.0.0→2.0.0 | 否 | 必须 |
| 次版本（Minor） | 1.0.0→1.1.0 | 是 | 必须 |
| 修订（Patch） | 1.0.0→1.0.1 | 是 | 建议 |

### 测试框架断言类型速查

| 断言 | 用途 | 示例 |
|------|------|------|
| contains | 含关键词 | `"退款" in output` |
| not_contains | 不含 | `"抱歉" not in output` |
| regex | 正则 | `r"\d{4}"` |
| json_schema | JSON 格式 | `{"type":"object"}` |
| exact | 完全匹配 | `output == "正面"` |

### 缓存策略对比

| 策略 | 实现 | 命中条件 | 适用 |
|------|------|---------|------|
| 内容哈希 | hash(prompt+model) | 完全相同 | 重复请求多 |
| 语义缓存 | Embedding+相似度 | 相似度>阈值 | 同义不同表述 |
| 持久化 | Redis/文件 | 跨进程 | 长期复用 |

---

## 实战练习

### 练习 1：为 AISearch 设计 3 个 Prompt 模板

用 YAML 格式设计 3 个模板：客服问答、文档摘要、代码 review。每个含元数据（model / temperature / variables）和变更日志。用 `02_prompt_manager.py` 的 `PromptManager` 加载并渲染。

**提示**：参考 `Code/README.md` 的 YAML 示例。

### 练习 2：编写 Prompt 测试用例

为练习 1 的"客服问答"模板编写 5 条测试用例：3 条正常 + 1 条边界（空输入）+ 1 条异常（变量缺失）。断言类型至少用到 contains 和 json_schema 两种。运行 `04_prompt_testing.py` 验证通过。

**提示**：用 mock LLM 返回固定字符串测试，避免真实调用成本。

### 练习 3：实现 VIP 与普通用户差异化 Prompt

基于 `03_dynamic_prompt.py`，扩展：VIP 用户模板带专属问候与优先规则，普通用户用标准模板。再实现"对话历史超 5 轮自动启用摘要压缩"的逻辑。展示同一问题在两种用户下的 Prompt 差异。

**提示**：用 Jinja2 的 `{% extends %}` 实现模板继承。
