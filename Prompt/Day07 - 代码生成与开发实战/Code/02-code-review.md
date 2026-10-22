# 代码审查模板

> 本文件提供一份完整的代码审查 Prompt 模板，角色为资深 Code Reviewer，覆盖 5 大审查维度，输出含问题等级、具体位置、修复建议的结构化报告。配套 2 个真实示例（Python / TypeScript）。

---

## 模板说明
- 用途：对给定代码进行专业 Code Review，输出结构化审查报告
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{language}}`、`{{code}}`、`{{context}}`

## 完整模板

```text
你是一名资深 Code Reviewer，拥有 10 年以上 {{language}} 项目审查经验，曾在大型互联网公司负责代码质量与安全审计。

请对以下代码进行严格审查。

【代码】
{{code}}

【上下文】
{{context}}

审查维度（逐一覆盖，不得遗漏）：
1. 安全性：注入风险、敏感信息泄露、权限校验、依赖漏洞
2. 性能：时间/空间复杂度、N+1 查询、不必要的循环、内存泄漏
3. 可读性：命名、注释、函数长度、职责单一、抽象层次
4. 最佳实践：是否符合语言/框架惯例、设计模式误用
5. 错误处理：异常捕获是否合理、是否吞错、是否暴露堆栈

输出格式（严格遵循）：

## 审查总评
- 总体评分：x/10
- 一句话结论

## 问题清单
按问题等级排序（严重 → 警告 → 建议），每条包含：

### [问题等级] 问题标题
- 位置：文件名:行号 或 函数名
- 维度：安全 / 性能 / 可读性 / 最佳实践 / 错误处理
- 描述：问题说明
- 影响：可能导致的后果
- 修复建议：给出修复后的代码片段

## 优秀实践
列出代码中值得肯定的做法（至少 2 条）

## 改进优先级建议
按修复顺序列出前 3 项
```

## 使用示例

### 示例 1：Python 代码审查

#### 输入
```text
你是一名资深 Code Reviewer，拥有 10 年以上 Python 项目审查经验，曾在大型互联网公司负责代码质量与安全审计。

请对以下代码进行严格审查。

【代码】
```python
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    sql = "SELECT * FROM users WHERE id = " + str(user_id)
    cur.execute(sql)
    row = cur.fetchone()
    return row

def login(username, password):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")
    user = cur.fetchone()
    if user:
        return "登录成功 token=" + password
    return "失败"

def process_orders(order_ids):
    result = []
    for oid in order_ids:
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders WHERE id = " + str(oid))
        result.append(cur.fetchone())
    return result
```

【上下文】
这是一个电商客服系统的数据访问层，处理用户登录和订单查询。生产环境使用 SQLite（即将迁移到 PostgreSQL）。

（输出格式同上模板）
```

#### 预期输出
```markdown
## 审查总评
- 总体评分：3/10
- 一句话结论：存在严重的 SQL 注入、明文密码、连接泄漏三大致命问题，必须立即重构后才能上线。

## 问题清单

### [严重] SQL 注入漏洞（字符串拼接）
- 位置：get_user 第 5 行、login 第 11 行、process_orders 第 18 行
- 维度：安全
- 描述：所有 SQL 均通过字符串拼接构造，user_id、username、password 均未参数化。
- 影响：攻击者可通过构造输入获取任意数据、绕过登录、删除表。
- 修复建议：
```python
cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
cur.execute(
    "SELECT * FROM users WHERE username=? AND password_hash=?",
    (username, hashed_password),
)
```

### [严重] 明文密码存储与返回
- 位置：login 第 11、13 行
- 维度：安全
- 描述：直接比对明文密码，且登录成功时将密码作为 token 返回。
- 影响：数据库泄露即全部账号失陷；token 即密码，可被重放。
- 修复建议：使用 bcrypt/argon2 哈希存储；登录后返回 JWT token，不返回任何密码相关信息。

### [严重] 数据库连接未关闭
- 位置：所有函数
- 维度：错误处理 / 性能
- 描述：connect 后未 close，也未使用 with 上下文管理。
- 影响：连接泄漏，长时间运行导致连接耗尽。
- 修复建议：
```python
with sqlite3.connect("users.db") as conn:
    cur = conn.cursor()
    cur.execute("...", (user_id,))
    return cur.fetchone()
```

### [警告] N+1 查询
- 位置：process_orders
- 维度：性能
- 描述：对每个 order_id 单独建连接并查询，order_ids 长度为 N 时执行 N 次查询。
- 影响：列表越长越慢。
- 修复建议：
```python
placeholders = ",".join("?" * len(order_ids))
cur.execute(
    f"SELECT * FROM orders WHERE id IN ({placeholders})",
    order_ids,
)
```

### [警告] 缺少异常处理
- 位置：所有函数
- 维度：错误处理
- 描述：未捕获 sqlite3.Error，异常会直接抛到上层。
- 修复建议：使用 try/except 记录日志并返回受控错误。

### [建议] 缺少类型注解与 docstring
- 位置：所有函数
- 维度：可读性 / 最佳实践
- 修复建议：补充 type hints 与 Google Style docstring。

### [建议] 函数职责混杂
- 位置：login
- 维度：可读性
- 描述：login 同时完成查询、比对、token 生成三件事。
- 修复建议：拆分为 verify_password / generate_token。

## 优秀实践
1. 使用 fetchone / fetchall 而非遍历游标，符合 DB-API 用法
2. 函数命名简洁达意

## 改进优先级建议
1. 立即修复 SQL 注入（参数化查询）
2. 引入密码哈希与 JWT token
3. 重构连接管理（with + 异常处理）
```

### 示例 2：TypeScript 代码审查

#### 输入
```text
你是一名资深 Code Reviewer，拥有 10 年以上 TypeScript 项目审查经验。

请对以下代码进行严格审查。

【代码】
```typescript
import axios from "axios";

async function fetchUserData(userId: any) {
    const response = await axios.get(`https://api.example.com/users/${userId}`);
    return response.data;
}

async function fetchAllUsers() {
    const users: any[] = [];
    for (let i = 1; i <= 1000; i++) {
        const user = await fetchUserData(i);
        users.push(user);
    }
    return users;
}

function parseConfig(raw: string) {
    return eval("(" + raw + ")");
}

const API_KEY = "sk-1234567890abcdef";

export { fetchUserData, fetchAllUsers, parseConfig, API_KEY };
```

【上下文】
Node.js 18 后端服务，使用 axios 调用第三方用户 API。

（输出格式同上模板）
```

#### 预期输出
```markdown
## 审查总评
- 总体评分：2/10
- 一句话结论：存在 eval 执行任意代码、硬编码密钥、any 滥用、串行 N+1 调用四类严重问题，禁止合入。

## 问题清单

### [严重] eval 执行任意代码
- 位置：parseConfig
- 维度：安全
- 描述：使用 eval 解析字符串，可执行任意 JS 代码。
- 影响：若 raw 来源于用户输入，将导致 RCE。
- 修复建议：使用 JSON.parse；如需更复杂结构，使用 vm2 等沙箱。

### [严重] 硬编码 API_KEY 并导出
- 位置：第 17 行、第 19 行
- 维度：安全
- 描述：密钥硬编码在源码中并被 export，泄露到所有引入方。
- 影响：密钥一旦泄露无法审计，需轮换。
- 修复建议：
```typescript
const API_KEY = process.env.API_KEY;
if (!API_KEY) throw new Error("API_KEY 未配置");
```

### [严重] 滥用 any
- 位置：fetchUserData 参数、fetchAllUsers 变量
- 维度：最佳实践
- 描述：userId 与 users 均为 any，丧失类型保护。
- 影响：编译期错误无法捕获，运行时崩溃。
- 修复建议：
```typescript
interface User { id: number; name: string; }
async function fetchUserData(userId: number): Promise<User> { ... }
```

### [警告] 串行 N+1 调用
- 位置：fetchAllUsers
- 维度：性能
- 描述：循环内 await，1000 次调用串行执行。
- 影响：总耗时 ≈ 1000 × 单次延迟。
- 修复建议：使用 Promise.all + 并发上限（如 p-limit）。

### [警告] 缺少超时与重试
- 位置：fetchUserData
- 维度：错误处理
- 描述：axios 调用未设置 timeout，第三方 API 卡住时整服务卡住。
- 修复建议：
```typescript
await axios.get(url, { timeout: 5000 });
```

### [建议] 缺少 try/catch
- 位置：所有 async 函数
- 维度：错误处理
- 修复建议：捕获 axios.AxiosError 并转换为业务异常。

## 优秀实践
1. 使用 async/await 而非回调，代码风格现代
2. 函数命名清晰

## 改进优先级建议
1. 移除 eval，改用 JSON.parse
2. API_KEY 改为环境变量
3. fetchAllUsers 改为并发调用
```

## 调优建议
- 温度：0.0（审查需稳定客观）
- 若审查大型 PR，先让 LLM 输出"代码概览"，再逐文件审查
- 可在 Prompt 中追加"参考 OWASP Top 10"提升安全审查深度
- 若需团队规范对齐，追加"遵循团队编码规范 {{team_style_guide}}"
