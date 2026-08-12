# Day08 - 子查询

子查询（Subquery）是把一条 SELECT 语句嵌套在另一条 SQL 中的写法，它是拆解复杂业务查询的核心利器。当连接查询写起来拗口、当聚合结果要再拿去过滤、当"是否存在"这类存在性判断需要表达时，子查询往往比 JOIN 更直观。本天将系统梳理子查询的分类、位置、与外查询的关系，并对比 IN 与 EXISTS 的性能差异，最后引入 MySQL 8 的 CTE（公用表表达式）与递归查询，为后续复杂报表与树形结构查询打下基础。

## 学习目标

- 理解子查询的本质：一个查询嵌套在另一个查询中
- 按返回结果掌握四种子查询：标量、列、行、表子查询
- 区分相关子查询与非相关子查询的执行机制
- 熟练使用 EXISTS / NOT EXISTS 进行存在性检查
- 理解 ANY / ALL / SOME 与列子查询的配合
- 掌握派生表（FROM 子查询）的写法与别名要求
- 能够用 CTE（WITH AS）改写复杂子查询提升可读性
- 了解递归 CTE 查询树形结构（分类树）的方法
- 能判断子查询与 JOIN 的取舍场景

---

## 理论知识讲解

### 1. 子查询概念

**子查询**是嵌套在另一条 SQL 语句内部的 SELECT 语句，外层的语句称为**主查询**（或外查询），内层的称为**子查询**（或内查询）。子查询必须用小括号 `()` 包裹。

```sql
-- 子查询示例：查询价格高于平均价的商品
SELECT name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products);  -- 括号内即子查询
```

子查询可以出现在 SQL 的多个位置，承担不同角色：

| 出现位置 | 作用 | 常见返回形式 |
|---------|------|-------------|
| SELECT 子句 | 作为计算列 | 标量子查询 |
| WHERE 子句 | 作为过滤条件 | 标量 / 列 / 行子查询 |
| HAVING 子句 | 对分组结果过滤 | 标量 / 列子查询 |
| FROM 子句 | 作为临时表（派生表） | 表子查询 |
| EXISTS 后 | 存在性判断 | 任意（只看是否有行） |

### 2. 按返回结果分类

#### 2.1 标量子查询

返回**单行单列**一个值的子查询。可出现在 SELECT、WHERE、HAVING 等需要单一值的位置。

```sql
-- 查询高于全店平均价的商品
SELECT name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products);

-- 在 SELECT 子句中作为计算列：每件商品价格与均价的差
SELECT name, price,
       price - (SELECT AVG(price) FROM products) AS diff_from_avg
FROM products;
```

#### 2.2 列子查询

返回**一列多行**的子查询，常配合 `IN`、`ANY`、`ALL`、`SOME` 使用。

```sql
-- 查询有订单的商品（IN 配合列子查询）
SELECT name FROM products
WHERE id IN (SELECT product_id FROM order_items);
```

#### 2.3 行子查询

返回**单行多列**的子查询，配合行构造器 `(a, b) = (SELECT ...)` 使用，较少见但语义清晰。

```sql
-- 查询与某商品同分类同价格的其他商品
SELECT id, name, category_id, price
FROM products
WHERE (category_id, price) = (
    SELECT category_id, price FROM products WHERE id = 1
) AND id <> 1;
```

#### 2.4 表子查询

返回**多行多列**的子查询，主要用在 FROM 子句中作为**派生表**（Derived Table），也可配合 IN 做行构造器匹配。

```sql
-- 派生表：先聚合再过滤
SELECT t.user_id, t.total
FROM (
    SELECT user_id, SUM(total_amount) AS total
    FROM orders
    GROUP BY user_id
) t
WHERE t.total > 1000;
```

### 3. 按与外查询关系分类

#### 3.1 非相关子查询

子查询**不依赖**外查询的任何列，可独立执行一次，把结果交给外查询使用。优化器往往把它当作"先算一次"的常量。

```sql
-- 非相关子查询：内层只执行一次
SELECT name FROM products
WHERE category_id IN (SELECT id FROM categories WHERE parent_id = 0);
```

#### 3.2 相关子查询

子查询**引用了外查询的列**，对外查询的每一行都要重新执行一次子查询。EXISTS 是最典型的相关子查询。

```sql
-- 相关子查询：内层引用了外层 products 表的 id
SELECT name
FROM products p
WHERE EXISTS (
    SELECT 1 FROM reviews r WHERE r.product_id = p.id
);
```

> 相关子查询的性能取决于外查询的行数与索引情况，行数大时需警惕 N+1 执行。

### 4. 子查询的位置

| 位置 | 示例 | 说明 |
|------|------|------|
| SELECT | `SELECT name, (SELECT ...) FROM t` | 标量子查询作列 |
| WHERE | `WHERE col > (SELECT ...)` | 标量/列/行子查询作过滤 |
| HAVING | `HAVING SUM(x) > (SELECT ...)` | 对分组结果过滤 |
| FROM | `FROM (SELECT ...) t` | 派生表，必须起别名 |

### 5. EXISTS / NOT EXISTS

`EXISTS` 用于判断子查询是否"有结果行返回"，返回布尔值。它只关心"有没有行"，不关心列的值，所以子查询里常用 `SELECT 1` 或 `SELECT *`。

```sql
-- 查询有订单的用户
SELECT username
FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id
);

-- 查询没有被评价过的商品
SELECT name
FROM products p
WHERE NOT EXISTS (
    SELECT 1 FROM reviews r WHERE r.product_id = p.id
);
```

**性能特点**：EXISTS 一旦在子查询中找到第一行就立即返回 TRUE，无需扫描全部；对索引友好时性能往往优于 IN。

### 6. ANY / ALL / SOME

配合列子查询做比较：

- `expr op ANY (子查询)`：只要与子查询中**任意一个**值比较成立即为真
- `expr op ALL (子查询)`：必须与子查询中**所有**值比较都成立才为真
- `SOME` 是 `ANY` 的同义词

```sql
-- 查询比"任意一个"数码商品贵的商品（即比最便宜的贵）
SELECT name, price FROM products
WHERE price > ANY (SELECT price FROM products WHERE category_id = 1);

-- 查询比"所有"数码商品都贵的商品（即比最贵的还贵）
SELECT name, price FROM products
WHERE price > ALL (SELECT price FROM products WHERE category_id = 1);
```

> `= ANY` 等价于 `IN`；`<> ALL` 等价于 `NOT IN`。

### 7. IN vs EXISTS

| 维度 | IN | EXISTS |
|------|----|----|
| 语义 | 左值是否在右集合中 | 子查询是否有行返回 |
| 形式 | `x IN (SELECT col ...)` | `EXISTS (SELECT 1 ... WHERE ...)` |
| 典型场景 | 子查询结果集小 | 外表小、子查询表大且可走索引 |
| NULL 陷阱 | `NOT IN` 遇 NULL 返回空集 | `NOT EXISTS` 不受 NULL 影响 |
| 执行 | 先算子查询，再逐行匹配外表 | 逐行外表，每行触发子查询 |

**NULL 陷阱**：当 `NOT IN (子查询)` 的子查询结果中包含 NULL 时，整个 NOT IN 永远返回空，因为 `x <> NULL` 的结果是 UNKNOWN。这就是为什么"查找没有 X 的记录"推荐用 `NOT EXISTS` 而非 `NOT IN`。

### 8. 派生表（Derived Table）

派生表是 FROM 子句中的子查询，把"一次查询的结果"当作临时表再查。**必须起别名**，否则报错。

```sql
-- 派生表：每个用户的订单数，再筛>=3单的
SELECT t.user_id, t.order_cnt
FROM (
    SELECT user_id, COUNT(*) AS order_cnt
    FROM orders
    GROUP BY user_id
) t
WHERE t.order_cnt >= 3;
```

MySQL 8.0.14+ 支持 **LATERAL** 派生表，允许派生表引用左侧表的列（之前只能在相关子查询中实现）。

### 9. 子查询 vs JOIN

很多子查询都能改写为 JOIN，二者语义等价但写法与性能有别：

| 场景 | 推荐写法 | 原因 |
|------|---------|------|
| 只需"是否存在"判断 | EXISTS | 找到首行即返回，无需去重 |
| 需要展示关联表的列 | JOIN | 一次获取所有字段 |
| 需要聚合后再过滤 | 派生表 / CTE | JOIN 无法直接对聚合结果过滤 |
| 与"全集"比较（如均价、最大值） | 标量子查询 | 语义清晰，一次计算 |
| 行数极大且子查询无索引 | JOIN 通常更优 | 优化器对 JOIN 优化更成熟 |

经验法则：**要展示字段用 JOIN，要判断存在用 EXISTS，要做中间聚合用派生表/CTE**。

### 10. CTE（公用表表达式）WITH AS

CTE（Common Table Expression）用 `WITH 名称 AS (...)` 把子查询命名复用，是 MySQL 8.0 的重要特性。

**优势**：
- 提升可读性：把复杂子查询拆成命名块，避免"嵌套俄罗斯套娃"
- 可被多次引用：同一 CTE 在主查询中可多次使用
- 支持递归：递归 CTE 可遍历树形结构

```sql
-- 用 CTE 改写派生表
WITH user_order_stat AS (
    SELECT user_id, COUNT(*) AS order_cnt, SUM(total_amount) AS total
    FROM orders
    GROUP BY user_id
)
SELECT user_id, order_cnt, total
FROM user_order_stat
WHERE order_cnt >= 3;
```

**多个 CTE**：用逗号分隔，后面的可引用前面的。

```sql
WITH
heavy_users AS (
    SELECT user_id FROM orders GROUP BY user_id HAVING SUM(total_amount) > 1000
),
their_reviews AS (
    SELECT r.* FROM reviews r
    JOIN heavy_users h ON r.user_id = h.user_id
)
SELECT * FROM their_reviews;
```

### 11. 递归 CTE 简介

递归 CTE 由 `WITH RECURSIVE` 定义，包含**锚点成员**（基础查询）与**递归成员**（引用自身的查询），用 UNION/UNION ALL 连接。常用于树形结构遍历。

```sql
-- 递归查询分类树：从顶级分类往下找所有子孙
WITH RECURSIVE category_tree AS (
    -- 锚点：顶级分类（parent_id = 0）
    SELECT id, name, parent_id, 0 AS depth, CAST(id AS CHAR(1000)) AS path
    FROM categories
    WHERE parent_id = 0
    UNION ALL
    -- 递归：找下一级子分类
    SELECT c.id, c.name, c.parent_id, ct.depth + 1, CONCAT(ct.path, '->', c.id)
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT id, name, depth, path FROM category_tree ORDER BY path;
```

> 递归 CTE 默认有 1000 次递归上限，可用 `SET @@cte_max_recursion_depth = N;` 调整。

---

## 代码文件说明

| 文件 | 内容 |
|------|------|
| `Code/01-scalar-subquery.sql` | 标量子查询、ANY/ALL 演示，含 SELECT/WHERE/HAVING 多位置用法 |
| `Code/02-exists-subquery.sql` | EXISTS/NOT EXISTS、相关子查询、NOT IN 的 NULL 陷阱 |
| `Code/03-derived-table.sql` | 派生表、CTE WITH AS、递归 CTE 查分类树 |

执行方式：

```bash
mysql> USE ecommerce;
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day08 - 子查询/Code/01-scalar-subquery.sql;
```

---

## 关键知识点总结

### 子查询分类速查

| 分类 | 返回 | 典型位置 | 典型操作符 |
|------|------|---------|-----------|
| 标量子查询 | 单行单列 | SELECT / WHERE / HAVING | `>` `<` `=` `>=` |
| 列子查询 | 一列多行 | WHERE / HAVING | `IN` `ANY` `ALL` `SOME` |
| 行子查询 | 单行多列 | WHERE | `(a,b) = (SELECT ...)` |
| 表子查询 | 多行多列 | FROM（派生表） | 当临时表查询 |

### IN vs EXISTS 对比

| 维度 | IN | EXISTS |
|------|----|----|
| 是否相关 | 通常非相关 | 通常相关 |
| 执行顺序 | 先子查询后外表 | 逐行外表触发子查询 |
| 子查询集小 | ✅ 推荐 | 也可 |
| 外表小、子表大可走索引 | 一般 | ✅ 推荐 |
| NOT 形式遇 NULL | ❌ 返回空集 | ✅ 安全 |
| 是否返回字段 | 否（只过滤） | 否（只判断） |

### 子查询 vs JOIN 选择口诀

- 要"展示"关联字段 → JOIN
- 要"判断存在/不存在" → EXISTS / NOT EXISTS
- 要"与全集比较"（均价、最大值） → 标量子查询
- 要"先聚合再过滤" → 派生表或 CTE
- 要"拆解复杂逻辑" → CTE（WITH AS）

---

## 实战练习

### 练习 1：消费高于自身平均的用户订单

用相关子查询，找出每个用户中**金额高于该用户历史平均订单金额**的订单。提示：外层遍历 orders，子查询按 `user_id` 分组求 AVG。

**期望思路**：
```sql
SELECT o.id, o.user_id, o.total_amount
FROM orders o
WHERE o.total_amount > (
    SELECT AVG(o2.total_amount)
    FROM orders o2
    WHERE o2.user_id = o.user_id
);
```

### 练习 2：从未被评价的"在售"商品

分别用 `NOT EXISTS` 和 `NOT IN` 两种写法查询状态为 `on_sale` 但没有评价记录的商品，并对比两者在 reviews.product_id 可能为 NULL 时的差异。

**思考点**：若 reviews 表存在 `product_id IS NULL` 的脏数据，`NOT IN` 写法为何会"突然返回空"？如何规避？

### 练习 3：用 CTE 重写多级分类统计

用**递归 CTE** 计算每个顶级分类（parent_id = 0）下所有子孙分类的商品数量总和，输出：顶级分类名、商品总数。提示：递归出每个分类的"根分类 id"，再 JOIN products 聚合。
