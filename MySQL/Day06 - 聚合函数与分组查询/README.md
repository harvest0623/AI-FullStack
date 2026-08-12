# Day06 - 聚合函数与分组查询

聚合与分组是数据分析的核心。关系型数据库存储的是"明细"——每一行记录一笔订单、一条评价、一次转账；但业务真正想要看的往往是"统计"——本月销售额多少、各类目商品均价几何、哪个用户消费最高。把"明细"压成"统计"的工具就是聚合函数（COUNT、SUM、AVG、MIN、MAX）与分组（GROUP BY）。一条写得好的聚合查询，相当于把 Excel 透视表的能力下沉到数据库层，让数据库替你完成统计计算，而不是把全表数据拉到应用层再用代码循环累加。

本章承接 Day05 的 SELECT 基础，往上加一层"聚合维度"。重点讲清楚三件事：聚合函数对 NULL 的处理差异（COUNT(*) 与 COUNT(列) 是初学者最容易混淆的点）、WHERE 与 HAVING 的本质区别（一个在分组前过滤行、一个在分组后过滤组）、以及 SQL 的完整执行顺序（为什么 HAVING 能用聚合函数而 WHERE 不能）。掌握这些，你就能写出"按 X 分组，统计 Y，只保留 Z 满足条件的组"这类业务报表查询。

---

## 学习目标

完成本章后，你应能：

- 正确使用五大聚合函数 COUNT / SUM / AVG / MIN / MAX，并说清 COUNT(*)、COUNT(列)、COUNT(DISTINCT 列) 三者的区别
- 解释聚合函数如何处理 NULL（哪些忽略 NULL、哪些不忽略），避免统计结果偏差
- 用 GROUP BY 实现单列分组与多列分组，理解"SELECT 只能选分组列或聚合列"的约束
- 用 HAVING 对分组结果过滤，并用一句话讲清 WHERE 与 HAVING 的本质区别
- 用 WITH ROLLUP 生成分组小计与总计
- 用 GROUP_CONCAT 拼接分组内的值
- 完整背诵 SQL 执行顺序：FROM→JOIN→WHERE→GROUP BY→HAVING→SELECT→ORDER BY→LIMIT
- 理解 MySQL 8 的 ONLY_FULL_GROUP_BY 模式对写法的约束

---

## 理论知识讲解

### 1. 聚合函数

聚合函数把多行数据"压"成一个值。一行入参是 N 行，出参是 1 行。

| 函数 | 作用 | 示例 |
|------|------|------|
| `COUNT(*)` | 统计行数（含 NULL 行） | `SELECT COUNT(*) FROM users` |
| `COUNT(列)` | 统计该列非 NULL 值的个数 | `SELECT COUNT(deleted_at) FROM users` |
| `COUNT(DISTINCT 列)` | 统计该列不同非 NULL 值的个数 | `SELECT COUNT(DISTINCT role) FROM users` |
| `SUM(列)` | 求和（忽略 NULL） | `SELECT SUM(total_amount) FROM orders` |
| `AVG(列)` | 平均值（忽略 NULL） | `SELECT AVG(price) FROM products` |
| `MIN(列)` | 最小值（忽略 NULL） | `SELECT MIN(price) FROM products` |
| `MAX(列)` | 最大值（忽略 NULL） | `SELECT MAX(price) FROM products` |
| `GROUP_CONCAT(列)` | 拼接分组内的值 | `SELECT GROUP_CONCAT(role) FROM users` |

#### 1.1 COUNT 的三种写法对比（重点！）

```sql
SELECT
    COUNT(*)              AS 总行数,
    COUNT(deleted_at)     AS 非空删除时间数,
    COUNT(DISTINCT role)  AS 不同角色数
FROM users;
```

| 写法 | 是否统计 NULL 行 | 是否去重 |
|------|----------------|---------|
| `COUNT(*)` | 是（统计所有行） | 否 |
| `COUNT(主键)` | 是（主键非 NULL） | 否 |
| `COUNT(列)` | 否（只统计该列非 NULL 的行） | 否 |
| `COUNT(DISTINCT 列)` | 否（只统计非 NULL 的不同值） | 是 |

> 经典误区：以为 `COUNT(列)` 等于 `COUNT(*)`。当列中有 NULL 时两者结果不同。统计"总行数"永远用 `COUNT(*)`，统计"某列有值的行数"才用 `COUNT(列)`。

#### 1.2 SUM / AVG 对 NULL 的处理

SUM 和 AVG 都**忽略 NULL**：

```sql
-- 假设有 3 行：price = 100, 200, NULL
SELECT SUM(price) FROM t;  -- 300（NULL 被忽略，不是 100+200+0）
SELECT AVG(price) FROM t;  -- 150（NULL 被忽略，平均 = 300/2，不是 300/3）
```

| 场景 | SUM | AVG |
|------|-----|-----|
| 列全为 NULL | 返回 NULL | 返回 NULL |
| 列含部分 NULL | 忽略 NULL 求和 | 忽略 NULL 求平均（分母不含 NULL 行） |
| 列全非 NULL | 正常求和 | 正常求平均 |

> 陷阱：AVG 忽略 NULL 会让分母变小，结果偏大。若想"NULL 当作 0 参与平均"，用 `AVG(IFNULL(price, 0))` 或 `SUM(IFNULL(price,0))/COUNT(*)`。

#### 1.3 MIN / MAX 对 NULL 的处理

MIN、MAX 同样忽略 NULL。当列全为 NULL 时返回 NULL。

```sql
SELECT MIN(price), MAX(price) FROM products;
```

#### 1.4 GROUP_CONCAT 拼接

```sql
-- 把所有角色拼接成逗号分隔的字符串
SELECT GROUP_CONCAT(role) FROM users;
-- 输出示例：admin,editor,customer,customer,...

-- 去重拼接
SELECT GROUP_CONCAT(DISTINCT role) FROM users;

-- 自定义分隔符
SELECT GROUP_CONCAT(DISTINCT role SEPARATOR ' | ') FROM users;

-- 排序后拼接
SELECT GROUP_CONCAT(username ORDER BY id DESC SEPARATOR ',') FROM users;
```

GROUP_CONCAT 默认上限 1024 字节，超过会被截断。可通过 `SET SESSION group_concat_max_len = 1000000;` 调大。

### 2. GROUP BY 分组

#### 2.1 单列分组

```sql
-- 统计每个角色的用户数
SELECT role, COUNT(*) AS 用户数
FROM users
GROUP BY role;
```

执行过程：
1. FROM users 取出全部行
2. GROUP BY role 按 role 值分桶（admin 一桶、editor 一桶、customer 一桶）
3. 对每桶应用 COUNT(*) 聚合
4. SELECT 输出每桶的 role 值与计数

#### 2.2 多列分组

```sql
-- 统计每个角色下、每个状态的用户数
SELECT role, status, COUNT(*) AS 用户数
FROM users
GROUP BY role, status;
```

多列分组的语义：先按 role 分组，role 相同的再按 status 细分。结果集的每一行对应一个 (role, status) 组合。

#### 2.3 SELECT 列的约束（重要）

GROUP BY 之后，SELECT 子句**只能选**：
- 分组列本身（如 role、status）
- 聚合函数（如 COUNT(*)、SUM(price)）

**不能直接选非分组列**（如 username），因为一个组里有多个 username，数据库无法决定返回哪一个。

```sql
-- 错误：username 不是分组列，也没在聚合函数里
SELECT role, username, COUNT(*)
FROM users
GROUP BY role;
-- MySQL 8 会报错：Expression #2 of SELECT list is not in GROUP BY...
```

> MySQL 5.7 之前默认允许这种写法（随机返回一个 username），MySQL 5.7+ 默认开启 `ONLY_FULL_GROUP_BY` 模式禁止。这是好事，强制写出正确的查询。

### 3. HAVING 分组后过滤

#### 3.1 基本用法

```sql
-- 统计下单数 >= 3 的用户
SELECT user_id, COUNT(*) AS 订单数
FROM orders
GROUP BY user_id
HAVING COUNT(*) >= 3;
```

HAVING 用于**过滤分组后的结果**，条件中可以引用聚合函数（WHERE 不行）。

#### 3.2 WHERE vs HAVING（核心对比）

| 对比项 | WHERE | HAVING |
|--------|-------|--------|
| 执行时机 | 分组**前** | 分组**后** |
| 过滤对象 | 行 | 组 |
| 能否用聚合函数 | 不能 | 能 |
| 能否用 SELECT 别名 | 不能（MySQL 例外） | 能（MySQL） |
| 能否用分组列 | 能 | 能 |
| 写在哪个子句 | GROUP BY 之前 | GROUP BY 之后 |

```sql
-- 同时用 WHERE 和 HAVING：
-- 先用 WHERE 过滤掉 2025 年之前的订单（行级过滤）
-- 再按用户分组，用 HAVING 保留订单数 >= 3 的用户（组级过滤）
SELECT user_id, COUNT(*) AS 订单数, SUM(total_amount) AS 总消费
FROM orders
WHERE created_at >= '2025-01-01'
GROUP BY user_id
HAVING COUNT(*) >= 3;
```

> 记忆口诀：**WHERE 过滤行在分组前，HAVING 过滤组在分组后**。能放 WHERE 就放 WHERE（先过滤再分组，减少分组数据量，性能更好）。

### 4. WITH ROLLUP 分组小计

```sql
-- 按角色统计用户数，并附加总计行
SELECT role, COUNT(*) AS 用户数
FROM users
GROUP BY role WITH ROLLUP;
```

输出：
```
admin     |  3
editor    |  5
customer  | 92
NULL      | 100   ← ROLLUP 生成的总计行，role 列为 NULL
```

ROLLUP 会在每个分组层级后追加一行汇总，多列分组时会产生多级小计：

```sql
-- 按 role, status 两级分组并 ROLLUP
SELECT role, status, COUNT(*) AS 用户数
FROM users
GROUP BY role, status WITH ROLLUP;
-- 会有：每个 (role,status) 组合行 + 每个 role 的小计行 + 总计行
```

> 用 `IFNULL(role, '总计')` 把 NULL 标签替换成可读文字。

### 5. GROUP BY 与聚合函数的组合

#### 5.1 多聚合函数组合

```sql
-- 每个商品分类的统计：商品数、最低价、最高价、平均价、库存总和
SELECT
    category_id,
    COUNT(*) AS 商品数,
    MIN(price) AS 最低价,
    MAX(price) AS 最高价,
    AVG(price) AS 平均价,
    SUM(stock) AS 库存合计
FROM products
GROUP BY category_id;
```

#### 5.2 配合 IF / CASE 做条件聚合

```sql
-- 按商品分类统计：在售商品数 vs 下架商品数
SELECT
    category_id,
    SUM(CASE WHEN status = 'on_sale' THEN 1 ELSE 0 END) AS 在售数,
    SUM(CASE WHEN status = 'off_sale' THEN 1 ELSE 0 END) AS 下架数
FROM products
GROUP BY category_id;
```

这种"按条件计数"的写法在报表查询中极为常见。

### 6. SQL 完整执行顺序

Day05 讲过基础执行顺序，加入聚合后完整版如下：

```
编写顺序：  SELECT → FROM → JOIN → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT
执行顺序：  FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

详细步骤：

| 步骤 | 子句 | 作用 | 能否用别名 | 能否用聚合 |
|------|------|------|----------|----------|
| 1 | FROM | 确定数据来源表 | - | - |
| 2 | JOIN | 连接多表 | - | - |
| 3 | WHERE | 过滤行 | 否 | 否 |
| 4 | GROUP BY | 分组 | MySQL 允许 | - |
| 5 | HAVING | 过滤组 | MySQL 允许 | 是 |
| 6 | SELECT | 选列、计算别名、计算聚合 | - | 是 |
| 7 | ORDER BY | 排序 | 是 | 是 |
| 8 | LIMIT | 截取 | - | - |

> 关键推论：
> - WHERE 中不能用聚合函数（因为聚合在 SELECT 阶段才计算，WHERE 在它之前）
> - WHERE 中不能用 SELECT 别名（别名在 SELECT 阶段才诞生）
> - HAVING 中可以用聚合函数（HAVING 在 GROUP BY 之后）
> - ORDER BY 中可以用聚合和别名（它在最后）

### 7. ONLY_FULL_GROUP_BY 模式

MySQL 8 默认开启 `sql_mode=ONLY_FULL_GROUP_BY`，要求 SELECT 中所有非聚合列都必须出现在 GROUP BY 中。

```sql
-- 查看当前 sql_mode
SELECT @@sql_mode;

-- 临时关闭（仅测试用，生产不建议）
SET SESSION sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''));

-- 重新开启
SET SESSION sql_mode = CONCAT(@@sql_mode, ',ONLY_FULL_GROUP_BY');
```

> 关闭它会让你写出"返回不确定值"的查询（如 `SELECT role, username, COUNT(*) FROM users GROUP BY role` 中 username 取哪个值是随机的），是 bug 温床。保持开启。

### 8. GROUP_CONCAT 函数详解

```sql
-- 每个用户的订单号列表（拼接成字符串）
SELECT
    user_id,
    GROUP_CONCAT(id ORDER BY id ASC SEPARATOR ',') AS 订单号列表
FROM orders
GROUP BY user_id;

-- 每个商品分类下的所有商品名（去重拼接）
SELECT
    category_id,
    GROUP_CONCAT(DISTINCT name SEPARATOR ' | ') AS 商品名列表
FROM products
GROUP BY category_id;
```

| 参数 | 作用 |
|------|------|
| `DISTINCT` | 去重 |
| `ORDER BY` | 拼接前排序 |
| `SEPARATOR` | 自定义分隔符（默认逗号） |

---

## 代码文件说明

| 文件 | 内容 | 主要演示 |
|------|------|---------|
| `Code/01-aggregate-functions.sql` | 聚合函数演示 | COUNT 三种写法对比、SUM/AVG/MIN/MAX、GROUP_CONCAT、NULL 处理 |
| `Code/02-group-by-having.sql` | 分组查询 | 单列/多列分组、HAVING、WHERE vs HAVING 对比、WITH ROLLUP、按订单状态统计、按商品分类统计销售额 |

每个脚本开头均 `USE ecommerce;`，可直接在 MySQL 客户端用 `source` 执行。

---

## 关键知识点总结

### 聚合函数速查

| 函数 | 作用 | NULL 处理 | 配合 DISTINCT |
|------|------|----------|--------------|
| `COUNT(*)` | 统计所有行（含 NULL 行） | 不忽略（全算） | 不支持 |
| `COUNT(列)` | 统计非 NULL 值 | 忽略 NULL | 支持 |
| `SUM(列)` | 求和 | 忽略 NULL | 支持 |
| `AVG(列)` | 平均值（分母不含 NULL 行） | 忽略 NULL | 支持 |
| `MIN(列)` | 最小值 | 忽略 NULL | 支持 |
| `MAX(列)` | 最大值 | 忽略 NULL | 支持 |
| `GROUP_CONCAT(列)` | 拼接字符串 | 忽略 NULL | 支持 |

> 一句话记忆：除了 `COUNT(*)`，所有聚合函数都忽略 NULL。

### WHERE vs HAVING 对比表

| 维度 | WHERE | HAVING |
|------|-------|--------|
| 执行阶段 | 分组**前** | 分组**后** |
| 过滤对象 | 单行 | 分组（聚合后的组） |
| 聚合函数 | **不可用** | 可用 |
| 别名引用 | 不可（MySQL 例外） | 可（MySQL） |
| 是否减少分组数据 | 是（先过滤再分组） | 否（先分组再过滤） |
| 性能建议 | 优先用 WHERE | 只在需要聚合条件时用 HAVING |

### SQL 完整执行顺序图

```
┌──────────────────────────────────────────────────────────┐
│                  SQL 执行顺序（含聚合）                  │
└──────────────────────────────────────────────────────────┘

  ① FROM        确定数据来源表
       │
       ▼
  ② JOIN        连接多表（Day07 详讲）
       │
       ▼
  ③ WHERE       过滤行（不能用聚合函数、不能用别名）
       │
       ▼
  ④ GROUP BY    分组（按列值分桶）
       │
       ▼
  ⑤ HAVING      过滤组（可以用聚合函数、可以用别名）
       │
       ▼
  ⑥ SELECT      选列、计算别名、计算聚合函数
       │
       ▼
  ⑦ ORDER BY    排序（可以用别名、可以用聚合）
       │
       ▼
  ⑧ LIMIT       截取（分页）
```

> 记忆口诀：**FROM-JOIN-WHERE-GROUP-HAVING-SELECT-ORDER-LIMIT**，"先选表、再连表、过滤行、分完组、过滤组、选列算聚合、排序截条"。

---

## 实战练习

> 以下练习基于 `ecommerce` 库，请先确保 Day04 已灌入测试数据。

### 练习 1：用户角色统计

写一条查询，统计每个角色（role）下的用户数，并按用户数从多到少排序。要求附带总计行（用 WITH ROLLUP），并把总计行的 NULL 替换为"全部"。

提示：
- `GROUP BY role WITH ROLLUP`
- `IFNULL(role, '全部')` 替换 NULL 标签
- `ORDER BY 用户数 DESC`（注意 ROLLUP 行会参与排序）

### 练习 2：高价值用户筛选

写一条查询，找出"2025 年总消费金额 >= 10000"的用户，返回 user_id、订单数、总消费金额，按总消费降序。

提示：
- WHERE 过滤 `created_at >= '2025-01-01'`
- GROUP BY user_id
- HAVING 过滤 `SUM(total_amount) >= 10000`
- SELECT 用 COUNT(*) 和 SUM(total_amount)

### 练习 3：商品销售报表

写一条查询，按商品分类统计每个分类的：商品数、在售商品数、平均价格、最高价、最低价。只显示商品数 >= 5 的分类。

提示：
- GROUP BY category_id
- 用 `SUM(CASE WHEN status='on_sale' THEN 1 ELSE 0 END)` 统计在售数
- HAVING COUNT(*) >= 5
- 思考：为什么"在售商品数 >= 5"应该放 HAVING 而不是 WHERE？
