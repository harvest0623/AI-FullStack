# Day07 - 多表连接查询

关系型数据库的精髓在于"关系"。Day02-Day04 我们把一个完整的电商系统拆成了 users、products、orders 等 7 张表——这种拆解叫"范式设计"，目的是消除冗余、保证一致性。但拆开容易重组难：业务查询时往往需要"用户名 + 订单金额 + 商品名"这种跨表信息，这时就要靠 JOIN 把分散在多张表中的数据重新组装成一行。JOIN 是 SQL 区别于 NoSQL 的核心能力，也是面试与实战中最容易拉开差距的知识点——会写 JOIN 只算入门，写对 LEFT JOIN 的 ON 与 WHERE 区别、理解驱动表选择、能驾驭四表以上的连环 JOIN，才算真正掌握。

本章系统讲解七种 JOIN：笛卡尔积 CROSS JOIN、INNER JOIN、LEFT JOIN、RIGHT JOIN，以及自连接（Self Join）处理树形分类结构。重点讲清楚两个易错点：一是 LEFT JOIN 中条件放在 ON 还是 WHERE 的区别（放错会让左连接退化成内连接），二是多表 JOIN 的执行顺序与驱动表选择对性能的影响。掌握本章后，你就能用一条 SQL 解决"查每个用户买了哪些商品、各买多少"这类看似复杂的需求，而不必在应用层写多层 for 循环。

---

## 学习目标

完成本章后，你应能：

- 解释为什么需要多表连接（范式设计导致数据分散），并用一句话讲清 JOIN 的作用
- 写出笛卡尔积 CROSS JOIN，理解它为何危险（N×M 行爆炸）
- 用 INNER JOIN 查询两表匹配的行，说清 ON 与 WHERE 的区别
- 用 LEFT JOIN 保留左表全部行，知道何时该用左连接
- 用 RIGHT JOIN 保留右表全部行，并理解它总能改写为 LEFT JOIN
- 区分 ON 子句、USING(列名)、NATURAL JOIN 三种连接条件的写法与适用场景
- 用自连接（Self Join）解决树形结构（分类树）、员工-经理这类同表关联问题
- 写出三表、四表以上的多表连接，理解 JOIN 的执行顺序与驱动表
- 讲清 LEFT JOIN 中条件放在 ON 还是 WHERE 的区别（放 WHERE 会退化成 INNER JOIN）

---

## 理论知识讲解

### 1. 为什么要连接

范式设计把数据拆到多张表以消除冗余：

```
users 表：存用户基础信息（id, username, email）
orders 表：存订单（id, user_id, total_amount）   ← user_id 是外键
```

好处：用户改邮箱只改 users 表一处，不会在订单表里留下旧邮箱。代价：查"某用户的订单金额"时，需要把 users 与 orders 拼起来——这就是 JOIN 的作用。

```
users.id ──── orders.user_id
（主键）        （外键）
```

JOIN 通过两个表之间的关联列，把分散的行重新组合成宽表。

### 2. 笛卡尔积 CROSS JOIN

笛卡尔积是"无连接条件"的 JOIN：左表每行与右表每行都配对一次，结果行数 = 左表行数 × 右表行数。

```sql
-- 笛卡尔积：N × M 行
SELECT * FROM users CROSS JOIN orders;
-- 或隐式写法（逗号分隔，老式 SQL）
SELECT * FROM users, orders;
```

| 左表行数 | 右表行数 | 结果行数 |
|---------|---------|---------|
| 100 | 1000 | 100,000 |
| 1万 | 1万 | 1亿（危险！） |

> 警告：忘记写 WHERE 条件的多表查询会退化为笛卡尔积，可能把数据库拖垮。生产环境严禁 `SELECT * FROM a, b` 不带条件。

CROSS JOIN 的合法用途：生成组合表（比如"所有用户 × 所有角色"的权限矩阵）。

### 3. INNER JOIN 内连接

INNER JOIN 只保留两表中**匹配**的行，丢弃不匹配的行。

```sql
-- 查询有订单的用户的订单信息
SELECT u.id, u.username, o.id AS order_id, o.total_amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id;
```

#### 3.1 ON 子句

ON 指定连接条件，通常是外键关系：

```sql
FROM users u
INNER JOIN orders o ON u.id = o.user_id
```

#### 3.2 INNER JOIN vs WHERE（老式写法）

两种写法等价，但推荐 INNER JOIN：

```sql
-- 推荐：标准 SQL，语义清晰
SELECT u.username, o.total_amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- 老式：逗号分隔 + WHERE 条件
SELECT u.username, o.total_amount
FROM users u, orders o
WHERE u.id = o.user_id;
```

| 写法 | 优点 | 缺点 |
|------|------|------|
| INNER JOIN ... ON | 语义清晰，连接条件与过滤条件分离 | 略长 |
| FROM a, b WHERE | 简短 | 容易漏 WHERE 退化成笛卡尔积，连接与过滤混在一起 |

#### 3.3 INNER JOIN 的特性

- 只保留两表都匹配的行
- 左表或右表中无匹配的行**不会出现**在结果中
- 若用户没下过单，该用户不会出现在"用户-订单"INNER JOIN 结果中

### 4. LEFT JOIN 左连接

LEFT JOIN 保留左表的**全部**行，右表无匹配时填 NULL。

```sql
-- 查询所有用户及其订单（含没下单的用户）
SELECT u.id, u.username, o.id AS order_id, o.total_amount
FROM users u                          -- 左表
LEFT JOIN orders o ON u.id = o.user_id;  -- 右表
-- 没下过单的用户：order_id 与 total_amount 为 NULL
```

#### 4.1 何时用 LEFT JOIN

- 查"全部 X，及其可能存在的 Y"：查所有用户及其订单（包含没下单的）
- 查"不存在 Y 的 X"：查没下过单的用户（LEFT JOIN + WHERE 右表字段 IS NULL）

```sql
-- 查没下过单的用户（LEFT JOIN + WHERE 右表 IS NULL）
SELECT u.id, u.username
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL;
```

#### 4.2 LEFT JOIN 的 NULL 含义

当右表无匹配时，右表所有列都填 NULL。这与"右表该列本身存的就是 NULL"难以区分，但通过右表主键（如 o.id）是否为 NULL 判断最可靠。

### 5. RIGHT JOIN 右连接

RIGHT JOIN 保留右表的全部行，左表无匹配时填 NULL。

```sql
-- 查询所有订单及其用户（含用户被删除的订单）
SELECT u.username, o.id AS order_id, o.total_amount
FROM users u
RIGHT JOIN orders o ON u.id = o.user_id;
```

> 实战建议：RIGHT JOIN 总能改写为 LEFT JOIN（调换两表顺序）。多数团队规范禁用 RIGHT JOIN，统一用 LEFT JOIN 保持代码方向一致。

```sql
-- 上面等价于
SELECT u.username, o.id AS order_id, o.total_amount
FROM orders o                          -- 把 orders 当左表
LEFT JOIN users u ON u.id = o.user_id;
```

### 6. 连接条件的三种写法

#### 6.1 ON 子句（最通用）

```sql
FROM users u INNER JOIN orders o ON u.id = o.user_id
```

ON 支持任意条件，不限于等值比较。

#### 6.2 USING(列名)（两表列名相同时）

```sql
-- 当两表关联列同名时可用 USING
FROM orders o INNER JOIN order_items oi USING(order_id)
-- 等价于：ON o.order_id = oi.order_id
```

USING 的特点：
- 两表列名必须相同
- 结果中该列只出现一次（ON 写法会出现两次：o.order_id 和 oi.order_id）

#### 6.3 NATURAL JOIN 自然连接

```sql
-- 自动以两表所有同名列作为连接条件
FROM users u NATURAL JOIN accounts
-- 等价于：ON u.id = a.user_id（如果只有 id 同名）
```

> 不推荐 NATURAL JOIN：连接条件隐式（依赖列名），表结构变更（新增同名列）会悄悄改变连接行为，难以排查。

### 7. 多表连接

三表以上 JOIN 是常态。写法是连续 JOIN：

```sql
-- 查询订单详情：订单 + 用户 + 商品
SELECT
    o.id AS order_id,
    u.username,
    p.name AS product_name,
    oi.quantity,
    oi.unit_price
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id;
```

#### 7.1 JOIN 顺序

从左到右依次连接：

```
orders ──JOIN── users ──JOIN── order_items ──JOIN── products
```

MySQL 优化器可能重排连接顺序（基于成本），但书写顺序影响可读性。建议从"主表"出发，逐个关联维度表。

#### 7.2 性能注意

- 每多一个 JOIN，理论扫描行数可能增长
- 连接列上要有索引（外键通常自动建索引，但显式建更稳妥）
- 驱动表选择由优化器决定，小表驱动大表更优（详见 Day10）

### 8. 自连接 Self Join

自连接是"表与自己 JOIN"，用表别名区分两次引用。常用于：

#### 8.1 分类树（categories 表的 parent_id）

categories 表有 `id, name, parent_id`，parent_id 指向父分类的 id。查"分类名 + 父分类名"：

```sql
-- c 是子分类，p 是父分类（同一张表，用不同别名）
SELECT
    c.id,
    c.name AS 分类名,
    p.name AS 父分类名
FROM categories c
LEFT JOIN categories p ON c.parent_id = p.id;
-- 顶级分类 parent_id = 0，无父分类，用 LEFT JOIN 保留
```

#### 8.2 员工-经理

员工表的 manager_id 指向另一个员工的 id：

```sql
SELECT
    e.name AS 员工,
    m.name AS 经理
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

#### 8.3 好友关系

```sql
SELECT a.user_id, b.user_id
FROM friends a
INNER JOIN friends b ON a.friend_id = b.user_id AND b.friend_id = a.user_id;
```

### 9. JOIN 的执行原理

MySQL 的 JOIN 基于"嵌套循环连接"（Nested Loop Join）：

```
for 左表每行 r:
    for 右表每行 s:
        if r.关联列 匹配 s.关联列:
            输出 (r, s) 组合行
```

#### 9.1 驱动表与被驱动表

- **驱动表**：外层循环遍历的表
- **被驱动表**：内层循环查的表

驱动表选择影响性能：被驱动表的关联列有索引时，内层循环变成索引查找（O(log N)），而非全表扫描（O(N)）。

#### 9.2 优化器的影响

MySQL 优化器会根据统计信息自动选择驱动表（不一定按书写顺序）。一般原则：小表驱动大表。

### 10. LEFT JOIN 的常见陷阱：ON vs WHERE

这是 LEFT JOIN 最容易踩的坑。**条件放在 ON 还是 WHERE，语义完全不同**。

#### 10.1 陷阱演示

```sql
-- 写法一：条件放 ON
SELECT u.username, o.id, o.status
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'completed';
-- 含义：保留所有用户；对每个用户，连接其"已完成"的订单（没有则填 NULL）
-- 结果：所有用户都出现，没下过完成订单的用户 order 字段为 NULL

-- 写法二：条件放 WHERE
SELECT u.username, o.id, o.status
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';
-- 含义：先 LEFT JOIN，再过滤 o.status='completed'
-- 结果：只保留有"已完成"订单的用户，没下过完成订单的用户被过滤掉
--      LEFT JOIN 退化成了 INNER JOIN！
```

#### 10.2 规则总结

| 条件位置 | 作用对象 | 对 LEFT JOIN 的影响 |
|---------|---------|---------------------|
| ON | 连接条件，决定右表哪些行参与连接 | 不影响左表保留全部行 |
| WHERE | 过滤最终结果行 | 会过滤左表行，可能让 LEFT JOIN 退化成 INNER JOIN |

> 规则：对**右表**的过滤条件，若希望保留左表全部行（保持 LEFT JOIN 语义），必须放 ON；若希望同时过滤左表（等同于 INNER JOIN），才放 WHERE。

#### 10.3 正确写法对照

```sql
-- 需求：查所有用户，及其"已完成"订单（没完成订单的用户也要显示）

-- 正确：右表条件放 ON
SELECT u.username, o.id AS order_id
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'completed';

-- 错误：右表条件放 WHERE（LEFT JOIN 退化）
SELECT u.username, o.id AS order_id
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed' OR o.status IS NULL;
-- 这种 OR IS NULL 写法能"补救"但可读性差，推荐直接放 ON

-- 需求：查"有已完成订单"的用户（等同于 INNER JOIN）
-- 此时放 WHERE 是对的
SELECT u.username, o.id AS order_id
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';
```

---

## 代码文件说明

| 文件 | 内容 | 主要演示 |
|------|------|---------|
| `Code/01-inner-join.sql` | 内连接演示 | 用户-订单、商品-分类 |
| `Code/02-left-right-join.sql` | 左/右连接演示 | 查所有用户含无订单的、ON vs WHERE 区别演示 |
| `Code/03-self-join.sql` | 自连接演示 | categories 树形结构：查分类及父分类名 |
| `Code/04-multi-table-join.sql` | 多表连接 | 订单→用户→订单详情→商品四表联查、统计每用户各类商品购买数 |

每个脚本开头均 `USE ecommerce;`，可直接在 MySQL 客户端用 `source` 执行。

---

## 关键知识点总结

### JOIN 类型对比表

| JOIN 类型 | 保留左表 | 保留右表 | 保留不匹配行 | 典型场景 |
|----------|---------|---------|------------|---------|
| CROSS JOIN | 是 | 是 | 全部（N×M） | 生成组合表 |
| INNER JOIN | 是（匹配的） | 是（匹配的） | 否 | 查两表共有的数据 |
| LEFT JOIN | 是 | 是（匹配的） | 左表不匹配行（右表填 NULL） | 查全部左表 + 关联右表 |
| RIGHT JOIN | 是（匹配的） | 是 | 右表不匹配行（左表填 NULL） | 查全部右表 + 关联左表 |
| FULL JOIN | 是 | 是 | 两表不匹配行都保留 | MySQL 不支持，用 UNION 模拟 |

> MySQL 不支持 FULL OUTER JOIN，可用 `LEFT JOIN UNION RIGHT JOIN` 模拟。

### ON vs WHERE 对比表（LEFT JOIN 场景）

| 维度 | ON 子句 | WHERE 子句 |
|------|---------|-----------|
| 作用阶段 | 连接阶段 | 连接后过滤阶段 |
| 对左表的影响 | 不影响（左表全保留） | 会过滤左表行 |
| 对右表的影响 | 决定哪些右表行参与连接 | 过滤最终结果 |
| 右表条件放这里 | 保留 LEFT JOIN 语义 | 可能让 LEFT JOIN 退化成 INNER JOIN |
| 推荐用法 | 右表过滤条件放 ON | 左表过滤条件放 WHERE |

### JOIN 写法速查

| 写法 | 示例 | 适用 |
|------|------|------|
| 标准 ON | `a JOIN b ON a.id = b.aid` | 通用（推荐） |
| USING | `a JOIN b USING(id)` | 两表列名相同 |
| NATURAL JOIN | `a NATURAL JOIN b` | 不推荐（隐式条件） |
| 老式逗号 | `FROM a, b WHERE a.id=b.aid` | 不推荐（易漏 WHERE） |

### LEFT JOIN 常用模式

```sql
-- 模式一：查全部左表 + 关联右表（右表可能无）
SELECT ... FROM a LEFT JOIN b ON a.id = b.aid;

-- 模式二：查"右表无匹配"的左表行（找缺失）
SELECT ... FROM a LEFT JOIN b ON a.id = b.aid WHERE b.id IS NULL;

-- 模式三：查左表 + 右表特定条件（右表条件放 ON）
SELECT ... FROM a LEFT JOIN b ON a.id = b.aid AND b.status = 'ok';
```

---

## 实战练习

> 以下练习基于 `ecommerce` 库，请先确保 Day02 建表、Day04 灌入测试数据。

### 练习 1：用户订单详情

写一条查询，返回每个订单的：订单 id、用户名、订单总金额、订单状态、下单时间。要求包含所有订单（即使用户已被软删除）。

提示：
- 以 orders 为左表，LEFT JOIN users
- `ON o.user_id = u.id`
- 思考：为什么这里用 LEFT JOIN 而不是 INNER JOIN？

### 练习 2：无评价商品

写一条查询，找出"没有任何评价"的商品，返回商品 id 与商品名。

提示：
- 以 products 为左表，LEFT JOIN reviews
- `WHERE r.id IS NULL` 找右表无匹配的行
- 思考：能否用 NOT IN 子查询实现？（Day08 会讲）

### 练习 3：分类树查询

写一条查询，返回每个分类的：分类 id、分类名、父分类名（顶级分类的父分类名显示为"顶级分类"）。

提示：
- categories 自连接：`c LEFT JOIN categories p ON c.parent_id = p.id`
- `IFNULL(p.name, '顶级分类')` 处理顶级分类
- 思考：为什么用 LEFT JOIN 而不是 INNER JOIN？（顶级分类 parent_id=0，无父分类）

### 练习 4：用户购买的商品分类统计

写一条查询，统计每个用户购买的商品数量按分类汇总。返回：用户名、分类名、购买总数量。

提示：
- 四表连接：orders → users → order_items → products → categories
- 需要 JOIN categories 表拿分类名
- GROUP BY u.username, c.name
- SUM(oi.quantity)
