# Day06 Code - Prompt 工程化集成代码

本目录提供 4 个 Python 脚本，把 Prompt 当作代码资产来管理：模板系统、管理器、动态构建、测试框架。所有脚本围绕 `AISearch` 项目的"Prompt 工程化"环节展开。

---

## 环境准备

```bash
pip install jinja2 pyyaml jsonschema python-dotenv
```

---

## 文件清单

### `01_prompt_template.py` — Prompt 模板系统

**核心类**：`PromptTemplate`

**能力**：
- 基于 Jinja2，支持变量插值 `{{var}}`、条件 `{% if %}`、循环 `{% for %}`、默认值 `|default`
- 从字符串或文件加载（支持 frontmatter 元数据解析）
- 静态分析必需变量、校验缺失变量

**示例**：

```python
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location("pt", "01_prompt_template.py")
pt = module_from_spec(spec); spec.loader.exec_module(pt)

t = pt.PromptTemplate.from_string(
    "你是{{role}}，{% if vip %}VIP{% endif %}回答：{{question}}"
)
print(t.render(role="客服", vip=True, question="退款"))
```

直接运行：`python 01_prompt_template.py`

---

### `02_prompt_manager.py` — Prompt 管理器

**核心类**：`PromptManager`、`ManagedPrompt`、`PromptVersion`

**能力**：
- 从 YAML 批量加载模板（含元数据、版本、变更日志）
- 渲染（内置内容哈希缓存）
- 版本管理：`update()` 升版本 + 记日志；`rollback()` 回滚；`diff()` 对比
- 模板变更自动清缓存

**YAML 结构示例**：

```yaml
qa:
  version: "1.0.0"
  model: gpt-4o-mini
  temperature: 0.3
  template: |
    你是客服，回答：{{question}}
  changelog:
    - version: "1.0.0"
      date: "2025-01-01"
      change: "初始版本"
      reason: "首次上线"
```

**生命周期演示**：加载 → 渲染（命中缓存） → 升版 → diff → 回滚。直接运行 `python 02_prompt_manager.py` 可看完整流程。

---

### `03_dynamic_prompt.py` — 动态 Prompt 构建

**核心类**：`DynamicPromptBuilder`、`BuildContext`、`Complexity`

**动态维度**：

| 维度 | 影响 |
|------|------|
| 用户类型 | VIP 用专属模板（优先响应、深度解答） |
| 对话历史 | >5 轮自动启用摘要压缩 |
| 任务复杂度 | 调整 temperature/max_tokens；复杂任务拼 Few-Shot |
| 问题关键词 | 按关键词选 Few-Shot 示例库 |

**演示**：同一问题在 3 种场景下生成完全不同的 system + user prompt。直接运行 `python 03_dynamic_prompt.py`。

---

### `04_prompt_testing.py` — Prompt 测试框架

**核心类**：`PromptTestRunner`、`TestCase`、`Assertion`、`TestReport`

**断言类型**：

| 类型 | 用途 | 示例 |
|------|------|------|
| `contains` | 含关键词 | `Assertion("contains", "退款")` |
| `not_contains` | 不含 | `Assertion("not_contains", "不知道")` |
| `regex` | 正则 | `Assertion("regex", r"\d{4}")` |
| `json_schema` | JSON Schema | `Assertion("json_schema", {...})` |
| `exact` | 完全匹配 | `Assertion("exact", "正面")` |

**两种模式**：
- `mock=True`（默认）：用 `mock_output` 字段，无需 API，CI 友好
- `mock=False`：真实调 OpenAI，验证实际输出

**pytest 集成**：脚本末尾打印 pytest 代码模板，可直接复制到 `test_prompt.py` 使用。

直接运行：`python 04_prompt_testing.py`

---

## Prompt 工程化指南

### 模板系统设计规范

1. **变量命名**：小写下划线，语义清晰（`question` 而非 `q`）。
2. **默认值**：用 `|default(...)`，避免运行时缺变量报错。
3. **元数据**：必填 `model`、`temperature`、`version`；可选 `variables`（类型说明）。
4. **正文长度**：单模板建议 < 500 字，超过应拆分为子模板组合。
5. **禁止硬编码**：业务变量必须用占位符，不能写死在正文。

### Jinja2 使用教程

**安装**：`pip install jinja2`

**最小示例**：

```python
from jinja2 import Template
t = Template("你好 {{name}}，今天 {{day}}")
print(t.render(name="张三", day="周一"))
```

**条件与循环**：

```python
tpl = """
{% for u in users %}
{{loop.index}}. {{u.name}} - {{u.role}}
{% endfor %}
{% if admin %}管理员可见{% endif %}
"""
```

**模板继承**（需 FileSystemLoader）：

```python
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader("prompts/"))
# base.j2 含 {% block rules %}默认{% endblock %}
# child.j2: {% extends "base.j2" %}{% block rules %}自定义{% endblock %}
print(env.get_template("child.j2").render(question="..."))
```

### 版本管理最佳实践

| 场景 | 操作 | 版本变化 |
|------|------|---------|
| 改了输出格式（不兼容） | 主版本+1，重置次/修 | 1.2.3 → 2.0.0 |
| 新增变量 / 示例（兼容） | 次版本+1 | 1.2.3 → 1.3.0 |
| 修错别字 / 调措辞 | 修订+1 | 1.2.3 → 1.2.4 |

**变更日志必填四要素**：版本号 / 日期 / 变更内容 / 变更原因（含数据支撑，如"准确率+8%"）。

### 测试框架使用指南

**测试分层**：

1. **格式测试**（mock 模式）：只验证输出格式，不调 LLM，CI 必跑。
2. **内容测试**（真实模式）：验证实际输出内容，每天定时跑。
3. **回归测试**：改 Prompt 后立即跑全部用例。

**用例设计原则**：
- 每个模板至少 3 条用例（正常 + 边界 + 异常）
- 异常用例验证变量缺失时的容错
- 关键断言用 `json_schema`，比 `contains` 更严格

### Prompt as Code 理念解读

把 Prompt 当作"特殊代码"：

| 维度 | 普通代码 | Prompt |
|------|---------|--------|
| 版本控制 | Git | Git |
| 评审 | PR | PR |
| 测试 | 单元测试 | Prompt 测试框架 |
| 部署 | CI/CD | Prompt 版本灰度 |
| 监控 | APM | 输出质量监控 |

**落地建议**：
1. 把 `prompts/` 目录纳入 Git，与代码同库管理。
2. Prompt 改动必须走 PR，必须有测试。
3. 线上灰度发布新版本 Prompt，监控指标回归后再全量。
4. 用 LangSmith / Promptfoo 等工具可视化编辑与评估。

---

## 常见问题

**Q1：Jinja2 模板渲染报 `UndefinedError`？**
A：用了 `StrictUndefined`，缺变量会报错。要么补变量，要么用 `|default(...)`，要么改用 `render_safe()`。

**Q2：mock 模式测试都通过，真实调用却失败？**
A：mock 只验证格式逻辑，不验证 LLM 实际输出。需定期跑 `mock=False` 的真实测试。

**Q3：缓存导致改了模板没生效？**
A：`PromptManager` 在 `update()` / `rollback()` 时会自动清缓存；若手动改了文件需调 `clear_cache()`。
