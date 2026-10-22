# Day07 - 代码生成与开发实战

> LLM 是强大的编程助手，掌握代码生成 Prompt 可以让开发效率成倍提升。从函数实现到接口设计、从单元测试到代码审查、从 Bug 修复到 Meta-Prompting，本章系统讲解面向开发全流程的 Prompt 设计方法，让 LLM 真正成为你团队中的"高资深工程师"。

---

## 本章简介

代码生成是 LLM 落地最成熟、收益最直接的应用场景之一。一个结构良好的代码 Prompt，可以让 GPT-4 / Claude 等模型一次性生成可直接运行的函数、完整的类、规范的 API 接口，甚至配套的单元测试与文档。但同样是"让 AI 写代码"，模糊的 Prompt 只会得到充满想象却跑不通的代码，而专业的 Prompt 则能稳定输出符合工程规范的代码。

本章延续 SmartCS 智能客服助手的开发场景，但所讲的 Prompt 模板可拓展到任意开发场景：电商折扣函数、商品数据类、RESTful CRUD、订单统计 SQL、正则验证、Docker 配置等实战样例覆盖了后端开发的常见任务；代码审查、测试生成、重构与调试模板则覆盖了代码质量保障的全流程；最后的 Meta-Prompting 模板展示"用 AI 增强 AI"的进阶工作流。

---

## 学习目标

完成本章后，你应能：

1. 掌握代码生成 Prompt 的标准结构（语言 + 框架 + 需求 + 约束 + 风格 + 输出格式）
2. 针对函数、类、API 接口、SQL、正则、配置等场景编写专业 Prompt
3. 设计代码审查 Prompt，输出含问题等级与修复建议的结构化报告
4. 生成覆盖率导向的单元测试用例（正常 / 异常 / 边界）
5. 编写代码重构、Bug 修复、性能优化类 Prompt
6. 使用 Meta-Prompting 让 LLM 帮你生成、优化、评估 Prompt

---

## 理论知识讲解

### 1. 代码生成 Prompt 结构

代码生成 Prompt 与普通文本 Prompt 最大的不同在于：代码是"严格结构化"的语言，任何模糊都可能导致编译错误或逻辑漏洞。一个工程级的代码 Prompt 应包含以下五要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| 语言+框架+版本 | 明确技术栈与版本号，避免生成过时 API | Python 3.12 / TypeScript 5.0 / NestJS 10 |
| 需求描述 | 功能 + 输入 + 输出三要素 | "传入订单列表，返回按用户分组的总金额字典" |
| 约束条件 | 性能 / 安全 / 兼容性约束 | "时间复杂度 O(n)；不使用 eval；兼容 Python 3.10+" |
| 代码风格 | 遵循的风格规范 | PEP 8 / ESLint Airbnb / Google Style |
| 输出格式 | 完整代码 / 代码片段 + 解释 | "只输出代码块，不要解释" |

**对比示例**：

```text
❌ 模糊 Prompt：
写一个 Python 函数计算折扣

✅ 专业 Prompt：
请用 Python 3.12 编写一个函数，遵循 PEP 8 规范。

需求：
- 功能：根据用户等级和订单金额计算最终折扣价
- 输入：user_level(str，取值 "bronze"/"silver"/"gold")、order_amount(float，单位元)
- 输出：final_price(float，保留两位小数)

折扣规则：
- bronze：满 200 减 20，否则不打折
- silver：9 折
- gold：满 500 减 80 + 8.5 折

约束：
- 不使用 eval / exec
- 输入非法时抛出 ValueError
- 只输出代码块，不要额外解释
```

### 2. 函数级代码生成

函数是代码复用的最小单元，也是 LLM 最擅长生成的粒度。函数级 Prompt 的核心是"**单一职责 + 明确签名 + 边界处理**"。

要点：
- **单一职责**：一个函数只做一件事，避免生成"上帝函数"
- **明确输入输出类型**：使用类型注解（Python type hints / TypeScript interface）
- **提供函数签名让 LLM 补充实现**：先写签名 + docstring，再让 LLM 填充
- **包含错误处理和边界条件**：在 Prompt 中显式列出边界情况

模板示例：

```text
请补充实现以下 Python 函数，保持签名不变：

```python
def calculate_discount(user_level: str, order_amount: float) -> float:
    """根据用户等级和订单金额计算折扣价。

    Args:
        user_level: 用户等级，取值 bronze/silver/gold
        order_amount: 订单金额（元），必须为正数

    Returns:
        折扣后价格，保留两位小数

    Raises:
        ValueError: 当 user_level 非法或 order_amount <= 0 时
    """
    # TODO: 在此实现
```

约束：
- 严格遵循 PEP 8
- 必须处理所有非法输入
- 不引入额外依赖
```

### 3. 类设计生成

类设计比函数复杂得多，涉及属性、方法、魔术方法、继承关系、接口设计等。Prompt 中需要明确类的"骨架"，让 LLM 沿着骨架填充。

要点：
- **属性 + 方法 + 魔术方法**：明确列出需要实现的成员
- **继承关系设计**：指明父类 / 抽象基类 / 接口
- **接口/抽象类设计**：用 ABC（Python）或 interface（TS）显式约束

模板骨架：

```text
请用 Python 3.12 设计一个 Product 数据类，要求：

1. 继承自 dataclasses.dataclass
2. 字段：
   - product_id: str
   - name: str
   - price: float（必须 > 0）
   - stock: int（必须 >= 0）
   - category: str
3. 方法：
   - to_dict() -> dict：序列化为字典
   - from_dict(cls, data: dict) -> Product：类方法反序列化
   - apply_discount(self, rate: float) -> None：应用折扣
4. 魔术方法：
   - __repr__、__eq__
5. 校验：price <= 0 或 stock < 0 时抛出 ValueError

输出：完整类定义 + 简要使用示例
```

### 4. API 接口设计生成

RESTful API 设计需要遵循统一的资源命名、HTTP 方法语义、状态码、错误码规范。Prompt 中要明确约束这些维度。

要点：
- **RESTful 风格约束**：资源用名词复数、HTTP 方法语义化
- **请求/响应 Schema 定义**：用 JSON Schema 或 Pydantic 描述
- **错误码设计**：统一错误响应结构

模板示例：

```text
请设计一组 RESTful API 接口，用于电商商品 CRUD，技术栈：FastAPI + Pydantic v2。

资源：/api/v1/products

要求：
1. 列出所有接口（method + path + 描述）：
   - GET    /api/v1/products          列表查询（支持分页、筛选）
   - GET    /api/v1/products/{id}     详情查询
   - POST   /api/v1/products          创建商品
   - PUT    /api/v1/products/{id}     全量更新
   - DELETE /api/v1/products/{id}     删除商品

2. 为每个接口定义 Pydantic 模型：
   - ProductCreate、ProductUpdate、ProductResponse、ProductListResponse

3. 错误响应统一格式：
   {"code": "PRODUCT_NOT_FOUND", "message": "...", "details": {}}

4. 状态码：200 / 201 / 204 / 400 / 404 / 422 / 500

输出：完整 FastAPI 路由代码 + Pydantic 模型定义 + 一段 curl 调用示例
```

### 5. SQL 生成

SQL 生成分为两类：表结构设计（DDL）和复杂查询（DQL）。Prompt 中应明确数据库类型、版本、性能约束。

要点：
- **表结构设计 DDL**：字段类型、主键、外键、索引、约束
- **复杂查询 DQL**：JOIN、子查询、窗口函数、聚合
- **优化建议**：要求 LLM 给出索引建议和执行计划分析

模板示例：

```text
数据库：MySQL 8.0

请根据以下需求生成 SQL：

【表结构】
设计 4 张表：users、products、orders、order_items
- users: id, username, email, level, created_at
- products: id, name, price, stock, category, created_at
- orders: id, user_id, total_amount, status, created_at
- order_items: id, order_id, product_id, quantity, unit_price

要求：
1. 合理设置主键、外键、索引
2. 字段类型与约束符合电商场景
3. status 枚举：pending/paid/shipped/delivered/cancelled

【复杂查询】
查询 2025 年 Q4 每个用户的：
- 订单总数
- 总消费金额
- 最常购买的商品类别
- 客单价（总消费 / 订单数）

要求：
- 只统计 status != 'cancelled' 的订单
- 按总消费金额降序排列
- 取 TOP 10

输出：DDL + DQL + 索引优化建议
```

### 6. 单元测试生成

单元测试是保障代码质量的基石。测试 Prompt 的核心是"**覆盖率导向 + 三类用例**"。

要点：
- **测试用例设计**：正常用例 / 异常用例 / 边界用例
- **覆盖率导向**：明确要求覆盖所有分支
- **Mock 设计**：对数据库、外部 API 等依赖进行 Mock

模板示例：

```text
请为以下 Python 函数生成 pytest 单元测试：

```python
def calculate_discount(user_level: str, order_amount: float) -> float:
    ...
```

测试要求：
1. 使用 pytest 框架，遵循 Arrange-Act-Assert 模式
2. 覆盖三类用例：
   - 正常用例：bronze/silver/gold 各 1 个
   - 异常用例：非法等级、负数金额、零金额
   - 边界用例：刚好满 200、刚好满 500、浮点精度
3. 使用 @pytest.mark.parametrize 参数化
4. 每个用例独立，不依赖执行顺序
5. 命名规范：test_<场景>_<预期>

输出：完整测试文件 + 覆盖率分析（哪些分支被覆盖）
```

### 7. 代码审查 Prompt

代码审查（Code Review）是 LLM 擅长的"分析型"任务。关键是定义清晰的审查维度和输出格式。

要点：
- **审查维度**：安全 / 性能 / 可读性 / 最佳实践 / 错误处理
- **输出审查报告格式**：问题等级 + 具体位置 + 修复建议

| 问题等级 | 含义 | 处理方式 |
|---------|------|---------|
| 严重 | 安全漏洞 / 必然崩溃 | 必须修复，阻断合并 |
| 警告 | 潜在 Bug / 性能问题 | 建议修复 |
| 建议 | 可读性 / 风格优化 | 可选改进 |

### 8. 代码重构 Prompt

重构的核心约束是"**保持行为不变**"。Prompt 中必须强调这一点，否则 LLM 可能顺手"修 Bug"导致行为变更。

要点：
- **重构目标**：提取函数 / 简化条件 / 消除重复
- **保持行为不变的约束**：明确要求"不改变外部可观察行为"

模板骨架：

```text
请重构以下代码，目标：提取函数 + 消除重复逻辑。

约束：
1. 保持外部行为完全不变（输入输出一致）
2. 不修改函数签名
3. 提取的子函数命名清晰
4. 解释每一处重构的动机

【待重构代码】
{{code}}

输出：
1. 重构后的代码
2. 重构说明（每处改动的动机）
3. 行为等价性验证思路
```

### 9. Bug 修复 Prompt

Bug 修复的关键是"**让 LLM 先定位再修复**"，避免直接给修复方案而掩盖根因。

要点：
- **提供代码 + 错误信息 + 期望行为**：三要素缺一不可
- **让 LLM 定位 → 分析 → 修复**：强制输出推理过程

模板骨架：

```text
请修复以下代码中的 Bug。

【代码】
{{code}}

【错误信息】
{{error_message}}

【期望行为】
{{expected_behavior}}

请按以下步骤输出：
1. 定位：指出 Bug 所在的行号和代码片段
2. 分析：解释为什么会产生这个 Bug（根因分析）
3. 修复：给出修复后的完整代码
4. 验证：说明如何验证修复有效（测试用例）
```

### 10. 代码解释 Prompt

代码解释适合不同水平的读者，Prompt 中要指定读者画像。

要点：
- **逐行/逐块解释**：选择解释粒度
- **适合不同水平读者**：新手 / 中级 / 资深

### 11. 文档注释生成

要点：
- **docstring / JSDoc / OpenAPI**：明确文档规范
- **README 生成**：项目结构、安装、使用、贡献指南

### 12. Meta-Prompting（用 Prompt 生成 Prompt）

Meta-Prompting 是"**用 AI 增强 AI 工作流**"的核心技巧，包含三种模式：

| 模式 | 输入 | 输出 |
|------|------|------|
| Prompt 生成器 | 任务需求描述 | 完整 Prompt 模板 |
| Prompt 优化器 | 现有 Prompt | 分析问题 + 优化版 |
| Prompt 评估器 | 待评估 Prompt | 评分 + 改进建议 |

Meta-Prompting 流程：

```text
任务需求 ──→ [Prompt 生成器] ──→ 初版 Prompt
                                      │
                                      ▼
                              [Prompt 评估器] ──→ 评分 + 问题
                                      │
                                      ▼
                              [Prompt 优化器] ──→ 优化版 Prompt
                                      │
                                      ▼
                                  迭代直至达标
```

### 13. 代码生成最佳实践

| 实践 | 说明 |
|------|------|
| 提供上下文 | 给出现有代码库结构、技术栈、相关文件 |
| 逐步细化 | 先架构 → 再模块 → 再函数，避免一次性要求太多 |
| 要求解释 | 让 LLM 说明"为什么这样写"，便于审查 |
| 安全约束 | 明确禁止 eval / exec / 硬编码密钥 / SQL 拼接 |
| 验证可运行 | 要求 LLM 自检语法、给出运行命令 |
| 版本固定 | 指定语言/框架/库的版本，避免生成过时 API |

---

## 代码文件说明

| 文件 | 内容 | 模板数 |
|------|------|--------|
| `Code/01-code-generation.md` | 代码生成模板合集（函数/类/API/SQL/正则/配置） | 6 |
| `Code/02-code-review.md` | 代码审查模板（含 Python / TypeScript 示例） | 1 + 2 示例 |
| `Code/03-test-generation.md` | 测试生成模板（pytest / Jest / API 测试） | 1 + 3 示例 |
| `Code/04-refactor-and-debug.md` | 重构 / Bug 修复 / 性能优化模板合集 | 3 |
| `Code/05-meta-prompting.md` | Meta-Prompting 模板合集（生成/优化/评估） | 3 |

---

## 关键知识点总结

### 代码生成 Prompt 结构速查

```text
┌─────────────────────────────────────────┐
│         代码生成 Prompt 五要素          │
├─────────────────────────────────────────┤
│  1. 语言+框架+版本                      │
│     例：Python 3.12 + FastAPI 0.110    │
├─────────────────────────────────────────┤
│  2. 需求描述（功能+输入+输出）          │
│     例：传入订单列表，返回金额字典      │
├─────────────────────────────────────────┤
│  3. 约束条件（性能/安全/兼容性）        │
│     例：O(n) / 禁用 eval / 兼容 3.10+  │
├─────────────────────────────────────────┤
│  4. 代码风格（PEP 8 / ESLint）          │
│     例：遵循 PEP 8，类型注解齐全       │
├─────────────────────────────────────────┤
│  5. 输出格式（完整代码 / 片段+解释）    │
│     例：只输出代码块，不解释           │
└─────────────────────────────────────────┘
```

### 各场景 Prompt 要点表

| 场景 | 核心要点 | 关键约束 |
|------|---------|---------|
| 函数生成 | 单一职责 + 类型注解 + 边界处理 | 不引入额外依赖 |
| 类生成 | 属性+方法+魔术方法 + 继承关系 | 字段校验 |
| API 设计 | RESTful + Schema + 错误码 | 状态码规范 |
| SQL 生成 | DDL + DQL + 索引建议 | 防注入、性能 |
| 测试生成 | 正常/异常/边界 + 覆盖率 | 用例独立 |
| 代码审查 | 5 维度 + 问题等级 + 修复建议 | 客观、可执行 |
| 重构 | 保持行为不变 + 重构动机 | 不改签名 |
| Bug 修复 | 定位→分析→修复→验证 | 不掩盖根因 |
| Meta-Prompting | 生成/优化/评估三模式 | 迭代闭环 |

### Meta-Prompting 流程图

```text
       ┌──────────────┐
       │  任务需求    │
       └──────┬───────┘
              ▼
       ┌──────────────┐
       │ Prompt 生成器│ ──→ 初版 Prompt
       └──────┬───────┘
              ▼
       ┌──────────────┐
       │ Prompt 评估器│ ──→ 评分 + 问题清单
       └──────┬───────┘
              ▼
       ┌──────────────┐
       │ Prompt 优化器│ ──→ 优化版 Prompt
       └──────┬───────┘
              ▼
        评分达标？ ──否──→ 回到评估器
              │
              是
              ▼
         最终 Prompt
```

### 代码安全约束清单

```text
□ 禁止使用 eval / exec 执行动态代码
□ 禁止硬编码密钥、Token、密码（使用环境变量）
□ 禁止 SQL 字符串拼接（使用参数化查询）
□ 禁止信任用户输入（必须校验和转义）
□ 禁止使用过期/有漏洞的依赖版本
□ 文件操作必须限制路径范围（防目录穿越）
□ 网络请求必须设置超时和重试上限
□ 敏感日志必须脱敏（手机号/身份证/银行卡）
```

---

## 实战练习

### 练习 1：电商折扣函数生成与测试闭环

**任务**：
1. 使用 `Code/01-code-generation.md` 中的"函数生成"模板，生成一个支持多级用户折扣 + 满减 + 优惠券叠加的 `calculate_final_price` 函数
2. 使用 `Code/03-test-generation.md` 中的模板，为该函数生成 pytest 测试，要求覆盖率 ≥ 90%
3. 使用 `Code/02-code-review.md` 中的模板，对生成的函数进行代码审查

**验收标准**：
- 函数能正确处理 bronze/silver/gold 三级用户
- 测试覆盖正常、异常、边界三类用例
- 审查报告识别出至少 1 个潜在问题

### 练习 2：RESTful 商品 API 全栈生成

**任务**：
1. 使用 `Code/01-code-generation.md` 中的"API 设计"模板，生成 FastAPI 商品 CRUD 接口
2. 使用 `Code/01-code-generation.md` 中的"SQL 生成"模板，生成对应的 MySQL 表结构
3. 使用 `Code/03-test-generation.md` 中的"API 接口测试"模板，生成接口测试用例

**验收标准**：
- 接口符合 RESTful 规范
- 表结构含主键、外键、索引
- 测试用例覆盖所有接口的成功和失败场景

### 练习 3：Meta-Prompting 优化工作流

**任务**：
1. 写一个朴素的 Prompt："帮我写个客服回复"，记录 LLM 输出
2. 使用 `Code/05-meta-prompting.md` 中的"Prompt 生成器"，让 LLM 生成一个专业的客服回复 Prompt
3. 使用"Prompt 评估器"评估该 Prompt
4. 使用"Prompt 优化器"迭代优化
5. 对比初版与最终版 Prompt 的输出质量

**验收标准**：
- 完整记录三轮迭代过程
- 最终 Prompt 输出质量明显优于初版
- 写一段 200 字的迭代心得
