# Day05 - DQL基础查询与运算符

SELECT 是 SQL 的灵魂。据统计，生产环境中超过 90% 的数据库操作都是查询——新增、修改、删除终究是少数，真正喂饱业务系统的是源源不断的查询流量。一条写得糟糕的 SELECT 可以拖垮整个数据库，一条写得漂亮的 SELECT 可以让原本需要应用层几百行代码才能完成的逻辑在一行 SQL 里收口。掌握 DQL（Data Query Language，数据查询语言）是通往后端开发与数据分析师的必经之路，而今天要讲的 SELECT 基础语法、运算符、NULL 处理、排序与分页，构成了所有复杂查询的底层积木。

本章是阶段二（DQL 五天）的第一天，从最朴素的 `SELECT *` 切入，逐步引入列别名、去重、条件过滤、各类运算符、排序与分页。每个知识点都配可直接 `source` 执行的 SQL 脚本，建议边读边在 MySQL 中运行，亲手感受每一条语句的输出。本章基于 Day02 建好的 `ecommerce` 库，假设 Day04 已灌入测试数据。

---

## 学习目标

完成本章后，你应能：

- 写出规范的 SELECT 语句，灵活运用列别名（AS）、表别名、DISTINCT 去重
- 用 WHERE 子句结合各类运算符过滤数据，知道每个运算符的适用场景与陷阱
- 解释 NULL 的三值逻辑，说清为什么 `WHERE col = NULL` 永远查不到数据
- 用 BETWEEN、IN、LIKE、REGEXP 解决范围、集合、模糊匹配需求
- 用 ORDER BY 对结果排序，包括多列排序、按别名排序、NULL 值排序
- 用 LIMIT 实现分页，掌握分页公式 `(page-1)*size, size`，了解深分页的性能隐患
- 说出 SELECT 的编写顺序与执行顺序的差异，明白为什么 WHERE 中不能引用 SELECT 中的别名

---

## 理论知识讲解

### 1. SELECT 基础语法

#### 1.1 最朴素的查询：SELECT 列 FROM 表

SELECT 的基本骨架是 `SELECT 要查什么 FROM 从哪查`。要查的可以是具体列名，也可以是 `*` 表示所有列。

```sql
-- 查询所有列
SELECT * FROM users;

-- 查询指定列（推荐：节省带宽、明确意图）
SELECT id, username, email FROM users;
```

> 工程建议：生产代码避免 `SELECT *`。它会返回所有列（包括 TEXT 大字段），增加网络传输与内存开销；当表结构变更时，`SELECT *` 的结果会悄悄变化，可能破坏依赖列顺序的代码。

#### 1.2 列别名 AS

列别名让结果更易读，关键字 `AS` 可以省略：

```sql
SELECT username AS 用户名, email AS 邮箱 FROM users;
-- 等价于（省略 AS）
SELECT username 用户名, email 邮箱 FROM users;
```

别名常用于计算列、聚合列、函数列，因为这些列原本没有名字：

```sql
-- 给计算结果起名
SELECT name, price * 0.9 AS 折扣价 FROM products;
```

#### 1.3 表别名

多表查询时给表起短别名，是 SQL 的常见写法（Day07 会大量使用）：

```sql
SELECT u.id, u.username
FROM users AS u
WHERE u.role = 'customer';
-- AS 同样可省略：FROM users u
```

#### 1.4 DISTINCT 去重

`DISTINCT` 对整行结果去重（不是对单列）。它作用于 SELECT 后所有列的组合。

```sql
-- 查询所有出现过订单的用户 id（去重）
SELECT DISTINCT user_id FROM orders;

-- 注意：DISTINCT 作用于 (user_id, status) 组合，不是只作用于 user_id
SELECT DISTINCT user_id, status FROM orders;
```

| 写法 | 含义 |
|------|------|
| `SELECT DISTINCT a` | a 的所有不同值 |
| `SELECT DISTINCT a, b` | (a, b) 所有不同组合 |
| `SELECT a, DISTINCT b` | 语法错误，DISTINCT 必须放在所有列前 |

### 2. WHERE 子句：条件过滤

WHERE 在 FROM 之后、GROUP BY 之前执行，用于从表中筛选满足条件的行。

```sql
SELECT id, username, role
FROM users
WHERE role = 'customer' AND status = 1;
```

WHERE 中的条件由运算符组合而成，下面逐类讲解。

### 3. 运算符详解

#### 3.1 比较运算符

| 运算符 | 含义 | 示例 |
|--------|------|------|
| `=` | 等于 | `WHERE role = 'admin'` |
| `<>` / `!=` | 不等于 | `WHERE status <> 0` |
| `<` | 小于 | `WHERE price < 100` |
| `>` | 大于 | `WHERE stock > 50` |
| `<=` | 小于等于 | `WHERE rating <= 3` |
| `>=` | 大于等于 | `WHERE total_amount >= 1000` |
| `<=>` | NULL 安全等于 | `WHERE deleted_at <=> NULL` |

`<=>` 是 MySQL 特有的运算符，专门解决 NULL 比较问题（见 3.7 节）。

#### 3.2 逻辑运算符

| 运算符 | 含义 | 优先级 |
|--------|------|--------|
| `NOT` | 非 | 高 |
| `AND` | 与 | 中 |
| `OR` | 或 | 低 |

优先级：`NOT > AND > OR`。写复杂条件时强烈建议用括号显式分组，避免依赖默认优先级：

```sql
-- 不好：依赖优先级，可读性差
WHERE role = 'admin' OR role = 'editor' AND status = 1
-- 实际等价于：role='admin' OR (role='editor' AND status=1)

-- 推荐：用括号明确意图
WHERE (role = 'admin' OR role = 'editor') AND status = 1
```

#### 3.3 范围运算符 BETWEEN

```sql
-- 查询价格在 100 到 1000 之间的商品（含两端）
SELECT id, name, price FROM products
WHERE price BETWEEN 100 AND 1000;

-- 反向：不在该范围
SELECT id, name, price FROM products
WHERE price NOT BETWEEN 100 AND 1000;
```

| 特性 | 说明 |
|------|------|
| 边界 | 包含两端（闭区间） |
| 数据类型 | 数值、日期、字符串均可（字符串按字典序） |
| 下限 ≤ 上限 | 否则查不到数据 |
| 与 `>= AND <=` 等价 | 但 BETWEEN 可读性更好 |

#### 3.4 集合运算符 IN

```sql
-- 查询指定状态的订单
SELECT id, status FROM orders
WHERE status IN ('paid', 'shipped', 'completed');

-- 反向：不在此集合
SELECT id, status FROM orders
WHERE status NOT IN ('cancelled', 'refunded');
```

`IN` 与多个 `OR` 等价，但更简洁，且在子查询场景下几乎是唯一写法（Day08 详讲）。

> 陷阱：`NOT IN` 与 NULL 的组合会带来意外结果。如果子查询返回值中包含 NULL，`NOT IN` 永远查不到数据（因为 `x <> NULL` 的结果是 NULL，不是 true）。Day08 会深入展开。

#### 3.5 模糊匹配 LIKE

LIKE 用两个通配符：

| 通配符 | 含义 |
|--------|------|
| `%` | 任意多个字符（包括 0 个） |
| `_` | 任意单个字符（必须 1 个） |

```sql
-- 以 'admin' 开头的用户名
SELECT username FROM users WHERE username LIKE 'admin%';

-- 第二个字符是 'o' 的用户名
SELECT username FROM users WHERE username LIKE '_o%';

-- 含 '@gmail' 的邮箱
SELECT email FROM users WHERE email LIKE '%@gmail%';
```

通配符转义：当字符串本身包含 `%` 或 `_` 时，用 `ESCAPE` 指定转义字符：

```sql
-- 查询名称中含 '50%' 的商品（把 % 当普通字符）
SELECT name FROM products WHERE name LIKE '%50\%%' ESCAPE '\\';
-- 第一个 % 是通配符，中间 \% 是被转义的字面 %，最后一个 % 又是通配符
```

> 性能提示：`LIKE 'abc%'`（前缀匹配）可以走索引；`LIKE '%abc'`（后缀匹配）无法走索引，会全表扫描。详情见 Day10。

#### 3.6 正则表达式 REGEXP / RLIKE

MySQL 支持 POSIX 风格正则（不是 PCRE），关键字 `REGEXP` 或别名 `RLIKE`：

```sql
-- 用户名以字母开头、后跟数字
SELECT username FROM users WHERE username REGEXP '^[a-zA-Z][0-9]+$';

-- 邮箱以 .com 或 .cn 结尾
SELECT email FROM users WHERE email REGEXP '\\.(com|cn)$';
```

| 元字符 | 含义 |
|--------|------|
| `^` | 字符串开头 |
| `$` | 字符串结尾 |
| `.` | 任意单个字符 |
| `[abc]` | 字符集合 |
| `[^abc]` | 非字符集合 |
| `a\|b` | 或 |
| `*` | 0 或多次 |
| `+` | 1 或多次 |
| `{n,m}` | n 到 m 次 |

`REGEXP` 与 `LIKE` 的关键区别：`REGEXP` 是部分匹配（只要字符串中存在匹配子串就为真），而 `LIKE` 默认不匹配（除非加 `%`）。

```sql
-- LIKE 必须用通配符才能匹配子串
SELECT 'hello world' LIKE 'world';              -- 0 (false)
SELECT 'hello world' LIKE '%world%';            -- 1 (true)

-- REGEXP 自动部分匹配
SELECT 'hello world' REGEXP 'world';            -- 1 (true)
```

#### 3.7 空值判断 IS NULL

NULL 是 SQL 中最特殊的值——它表示"未知"或"不存在"，不是空字符串也不是 0。

```sql
-- 正确：判断 NULL
SELECT id, username FROM users WHERE deleted_at IS NULL;
SELECT id, username FROM users WHERE deleted_at IS NOT NULL;

-- 错误：永远查不到 NULL
SELECT id, username FROM users WHERE deleted_at = NULL;     -- 永远返回空
SELECT id, username FROM users WHERE deleted_at <> NULL;    -- 永远返回空
```

为什么 `= NULL` 不行？这涉及 SQL 的三值逻辑，见下一节。

#### 3.8 NULL 安全等于 <=>

`<=>` 是 MySQL 扩展，专门处理 NULL：

| 表达式 | a 是 NULL 时 | a 不是 NULL 时 |
|--------|------------|--------------|
| `a = b` | 永远是 NULL | 正常比较 |
| `a <=> b` | 与 b 是否为 NULL 比较 | 正常比较 |

```sql
-- 查 deleted_at 是 NULL 的用户（与 IS NULL 等价）
SELECT id FROM users WHERE deleted_at <=> NULL;

-- 当 deleted_at 可能是 NULL 也可能是日期时，<=> 更简洁
SELECT id FROM users WHERE deleted_at <=> '2025-01-01';
```

### 4. NULL 的三值逻辑

SQL 不只有 true / false，还有第三种结果：NULL（未知）。这是初学者最容易踩的坑。

#### 4.1 NULL 与任何值比较都是 NULL

```sql
SELECT NULL = 1;       -- NULL
SELECT NULL = NULL;    -- NULL（不是 true！）
SELECT NULL <> 1;      -- NULL（不是 true！）
```

既然 `NULL = NULL` 的结果是 NULL（不是 true），WHERE 子句只保留结果为 true 的行，所以 `WHERE deleted_at = NULL` 一条都查不到。

#### 4.2 三值逻辑真值表

| A | B | A AND B | A OR B | NOT A |
|---|---|---------|--------|-------|
| T | T | T | T | F |
| T | F | F | T | F |
| T | N | N | T | F |
| F | F | F | F | T |
| F | N | F | N | T |
| N | N | N | N | N |

> 记忆口诀：AND 取最小值（F < N < T），OR 取最大值。

#### 4.3 NULL 在聚合函数中的处理

- `COUNT(列)` 忽略 NULL 行
- `SUM / AVG` 忽略 NULL
- `COUNT(*)` 不忽略（统计所有行）

详情见 Day06。

#### 4.4 NULL 处理函数

```sql
-- IFNULL(a, b)：a 为 NULL 则返回 b
SELECT IFNULL(deleted_at, '未删除') AS 状态 FROM users;

-- COALESCE(a, b, c, ...)：返回第一个非 NULL 的参数
SELECT COALESCE(deleted_at, 'active') FROM users;

-- NULLIF(a, b)：a=b 时返回 NULL，否则返回 a
SELECT NULLIF(status, 0) FROM users;
```

### 5. ORDER BY 排序

#### 5.1 升序与降序

```sql
-- 默认升序 ASC
SELECT id, price FROM products ORDER BY price;

-- 降序 DESC
SELECT id, price FROM products ORDER BY price DESC;

-- 多列排序：先按 status 升序，再按 price 降序
SELECT id, status, price FROM products
ORDER BY status ASC, price DESC;
```

| 关键字 | 含义 | 默认 |
|--------|------|------|
| ASC | 升序（小→大） | 默认值，可省略 |
| DESC | 降序（大→小） | 必须显式写 |

#### 5.2 NULL 在排序中的位置

MySQL 默认把 NULL 当作最小值：

```sql
-- 升序时 NULL 排最前
SELECT id, deleted_at FROM users ORDER BY deleted_at ASC;
-- 降序时 NULL 排最后
SELECT id, deleted_at FROM users ORDER BY deleted_at DESC;
```

> 其他数据库行为不同：Oracle 默认 NULL 最大；PostgreSQL 默认 NULL 最大。跨库迁移时要注意。

#### 5.3 按别名或表达式排序

```sql
-- 按列别名排序（WHERE 不能用别名，但 ORDER BY 可以）
SELECT name, price * stock AS 总价值 FROM products
ORDER BY 总价值 DESC;

-- 按表达式排序
SELECT name, price FROM products ORDER BY price * stock DESC;

-- 按列序号排序（不推荐，可读性差）
SELECT name, price FROM products ORDER BY 2 DESC;
```

### 6. LIMIT 限制结果

#### 6.1 取前 N 条

```sql
-- 取价格最高的 3 件商品
SELECT id, name, price FROM products
ORDER BY price DESC
LIMIT 3;
```

#### 6.2 分页

两种等价写法：

```sql
-- 写法一：LIMIT offset, size
SELECT id, name, price FROM products
ORDER BY price DESC
LIMIT 0, 10;   -- 偏移 0，取 10 条

-- 写法二：LIMIT size OFFSET offset
SELECT id, name, price FROM products
ORDER BY price DESC
LIMIT 10 OFFSET 0;
```

#### 6.3 分页公式

```
LIMIT (page - 1) * size, size
```

| 参数 | 含义 | 示例 |
|------|------|------|
| page | 页码（从 1 开始） | 第 2 页 |
| size | 每页条数 | 10 |
| offset | 跳过多少条 | (2-1)*10 = 10 |

#### 6.4 深分页问题

当 offset 很大时，MySQL 仍然要扫描 offset+size 行再丢弃前 offset 行：

```sql
-- 第 10000 页（每页 10 条），要扫描 100010 行
SELECT id, name FROM products ORDER BY id LIMIT 99990, 10;
```

深分页优化方案（Day14 详讲）：
- 用 `WHERE id > 上次最大id` 替代 offset（游标分页）
- 用覆盖索引减少回表
- 用延迟关联：先查主键再 JOIN

### 7. SELECT 完整语法结构与执行顺序

#### 7.1 编写顺序

```sql
SELECT    列/表达式/聚合
FROM      表
[JOIN     表2 ON 条件]
WHERE     行过滤条件
GROUP BY  分组列
HAVING    组过滤条件
ORDER BY  排序列
LIMIT     offset, size;
```

#### 7.2 执行顺序（核心！）

```
FROM      → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
                                              ↑
                                     聚合函数在这里才计算
```

#### 7.3 编写顺序 vs 执行顺序对比

| 步骤 | 编写顺序 | 执行顺序 | 说明 |
|------|---------|---------|------|
| 1 | SELECT | FROM | 先确定数据来源 |
| 2 | FROM | JOIN | 处理表连接 |
| 3 | JOIN | WHERE | 过滤行 |
| 4 | WHERE | GROUP BY | 分组 |
| 5 | GROUP BY | HAVING | 过滤组 |
| 6 | HAVING | SELECT | 选列、计算别名与聚合 |
| 7 | ORDER BY | ORDER BY | 排序 |
| 8 | LIMIT | LIMIT | 截取 |

> 关键推论：
> - **WHERE 中不能用 SELECT 别名**：因为 SELECT 在 WHERE 之后才执行，别名还没诞生。
> - **ORDER BY 可以用 SELECT 别名**：因为它在 SELECT 之后执行。
> - **GROUP BY 在 SELECT 之前**：所以 GROUP BY 不能引用 SELECT 中的别名（MySQL 是个例外，允许这种写法，但其他数据库不允许，移植时要小心）。

#### 7.4 一个完整示例

```sql
-- 查询状态为在售、库存大于 0 的商品，按价格降序，取前 10 条
SELECT
    id,
    name,
    price,
    stock,
    price * stock AS total_value
FROM products
WHERE status = 'on_sale' AND stock > 0
ORDER BY price DESC
LIMIT 10;
```

执行流程：
1. FROM products：取出 products 全部行
2. WHERE：过滤出 status='on_sale' 且 stock>0 的行
3. SELECT：选出 id/name/price/stock 列，计算 total_value 别名
4. ORDER BY：按 price 降序
5. LIMIT：取前 10 条

---

## 代码文件说明

| 文件 | 内容 | 主要演示 |
|------|------|---------|
| `Code/01-basic-select.sql` | SELECT 基础 | 查列、别名、DISTINCT、ORDER BY、LIMIT 综合 |
| `Code/02-operators.sql` | 运算符演示 | 比较、逻辑、IN、BETWEEN、LIKE、REGEXP、IS NULL、<=> |
| `Code/03-pagination.sql` | 分页查询 | LIMIT 两种语法、分页公式、深分页问题预告 |

每个脚本开头均 `USE ecommerce;`，可直接在 MySQL 客户端用 `source` 执行。

---

## 关键知识点总结

### 运算符速查表

| 类别 | 运算符 | 用法 | 示例 |
|------|--------|------|------|
| 比较 | `= <> < > <= >=` | 数值/字符串/日期比较 | `WHERE price > 100` |
| NULL 安全 | `<=>` | 处理 NULL 比较 | `WHERE deleted_at <=> NULL` |
| 逻辑 | `AND OR NOT` | 组合条件 | `WHERE a=1 AND (b=2 OR c=3)` |
| 范围 | `BETWEEN a AND b` | 闭区间 | `WHERE price BETWEEN 100 AND 1000` |
| 集合 | `IN (...)` | 离散值集合 | `WHERE status IN ('paid','shipped')` |
| 模糊 | `LIKE` | 通配符匹配 | `WHERE name LIKE '手机%'` |
| 正则 | `REGEXP` | 正则匹配 | `WHERE email REGEXP '@gmail'` |
| 空值 | `IS NULL / IS NOT NULL` | NULL 判断 | `WHERE deleted_at IS NULL` |

### NULL 三值逻辑真值表

| 表达式 | NULL 比较的结果 | WHERE 是否保留行 |
|--------|----------------|----------------|
| `NULL = 1` | NULL | 否 |
| `NULL = NULL` | NULL | 否 |
| `NULL <> 1` | NULL | 否 |
| `NULL IS NULL` | TRUE | 是 |
| `NULL <=> NULL` | TRUE | 是 |
| `NULL + 1` | NULL | （算术运算返回 NULL） |

> 一句话记忆：**判断 NULL 永远用 IS NULL / IS NOT NULL / <=>，绝不用 =**。

### SQL 执行顺序口诀

```
FROM-WHERE-GROUP-HAVING-SELECT-ORDER-LIMIT
```

> 七字诀："先选表，再选行，分完组再选列，最后排序截条"。

---

## 实战练习

> 以下练习基于 `ecommerce` 库，请先确保 Day04 已灌入测试数据。

### 练习 1：用户筛选

写一条查询，返回所有"未被软删除的、状态为 1 的普通消费者（customer）"，按注册时间倒序，取前 20 条。返回字段：id、username、email、created_at。

提示：
- `deleted_at IS NULL` 判断未删除
- 多个条件用 AND 组合
- `ORDER BY created_at DESC`

### 练习 2：商品价格区间搜索

写一条查询，返回所有"在售（on_sale）状态下、价格在 50 到 500 之间、库存大于 0"的商品，结果按价格升序、库存降序排列。返回字段：name、price、stock。

提示：
- 用 BETWEEN AND 简化范围条件
- 多列排序：`ORDER BY price ASC, stock DESC`

### 练习 3：订单状态分页

假设每页 15 条，请写一条查询返回第 3 页的订单数据（按 id 升序）。返回字段：id、user_id、total_amount、status、created_at。

提示：
- 分页公式：`LIMIT (page-1)*size, size`
- 第 3 页每页 15 条 → `LIMIT 30, 15`
- 思考：如果订单总数达到 100 万，第 1000 页这种深分页会有什么问题？
