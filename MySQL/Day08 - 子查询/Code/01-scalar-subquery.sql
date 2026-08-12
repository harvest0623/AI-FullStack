-- ============================================================
-- 文件名称: 01-scalar-subquery.sql
-- 文件用途: 标量子查询、列子查询、行子查询演示
--           演示 ANY / ALL / SOME 与列子查询的配合
--           覆盖 SELECT / WHERE / HAVING 多位置子查询用法
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day08 - 子查询/Code/01-scalar-subquery.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 一、标量子查询（返回单行单列）
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 查询高于全店平均价的商品（WHERE 中使用标量子查询）
--     子查询 SELECT AVG(price) FROM products 只执行一次，返回一个常数
-- ------------------------------------------------------------
SELECT id, name, category_id, price
FROM products
WHERE price > (SELECT AVG(price) FROM products)
ORDER BY price DESC;

-- 先看一下平均价，对比验证
SELECT AVG(price) AS avg_price FROM products;

-- ------------------------------------------------------------
-- 1.2 标量子查询出现在 SELECT 子句：每件商品价格与均价的差
--     标量子查询可作为计算列，对每行都重新求值（此处为非相关，仍是常数）
-- ------------------------------------------------------------
SELECT id, name, price,
       ROUND(price - (SELECT AVG(price) FROM products), 2) AS diff_from_avg
FROM products
ORDER BY diff_from_avg DESC
LIMIT 10;

-- ------------------------------------------------------------
-- 1.3 标量子查询出现在 HAVING：筛选订单总额高于"全店单笔平均订单额"的用户
--     HAVING 在 GROUP BY 之后执行，用于过滤分组结果
-- ------------------------------------------------------------
SELECT user_id, COUNT(*) AS order_cnt, SUM(total_amount) AS total_spent
FROM orders
GROUP BY user_id
HAVING SUM(total_amount) / COUNT(*) > (SELECT AVG(total_amount) FROM orders)
ORDER BY total_spent DESC;

-- ------------------------------------------------------------
-- 1.4 相关标量子查询：查询每个用户高于"自身平均订单额"的订单
--     子查询引用了外层 orders 表的 user_id，每行重新求值
-- ------------------------------------------------------------
SELECT o.id, o.user_id, o.total_amount, o.created_at
FROM orders o
WHERE o.total_amount > (
    -- 该用户的平均订单额
    SELECT AVG(o2.total_amount)
    FROM orders o2
    WHERE o2.user_id = o.user_id
)
ORDER BY o.user_id, o.total_amount DESC;

-- ============================================================
-- 二、列子查询（返回一列多行，配合 IN / ANY / ALL / SOME）
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 IN + 列子查询：查询"有被下单"的商品
--     子查询返回所有 order_items 中的 product_id 列
-- ------------------------------------------------------------
SELECT id, name, price, stock
FROM products
WHERE id IN (SELECT product_id FROM order_items)
ORDER BY id;

-- ------------------------------------------------------------
-- 2.2 NOT IN + 列子查询：查询"从未被下单"的商品
--     注意：若子查询结果含 NULL，NOT IN 会整体返回空（见 02 文件演示）
-- ------------------------------------------------------------
SELECT id, name, price, stock
FROM products
WHERE id NOT IN (SELECT product_id FROM order_items WHERE product_id IS NOT NULL)
ORDER BY id;

-- ============================================================
-- 三、ANY / ALL / SOME 演示
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 ANY：比"任意一个"顶级分类商品贵 => 比最便宜的还贵即可
--     > ANY 等价于 > MIN(子查询结果)
-- ------------------------------------------------------------
SELECT id, name, price
FROM products
WHERE price > ANY (
    SELECT price FROM products WHERE category_id = 1
)
ORDER BY price DESC
LIMIT 10;

-- 对照：ANY 的最小值
SELECT MIN(price) AS min_price_cat1 FROM products WHERE category_id = 1;

-- ------------------------------------------------------------
-- 3.2 ALL：比"所有"顶级分类商品都贵 => 比最贵的还贵
--     > ALL 等价于 > MAX(子查询结果)
-- ------------------------------------------------------------
SELECT id, name, price
FROM products
WHERE price > ALL (
    SELECT price FROM products WHERE category_id = 1
)
ORDER BY price DESC;

-- 对照：ALL 的最大值
SELECT MAX(price) AS max_price_cat1 FROM products WHERE category_id = 1;

-- ------------------------------------------------------------
-- 3.3 = ANY 等价于 IN：查询出现在订单详情中的商品
-- ------------------------------------------------------------
SELECT id, name
FROM products
WHERE id = ANY (SELECT product_id FROM order_items)
ORDER BY id;

-- ------------------------------------------------------------
-- 3.4 <> ALL 等价于 NOT IN：查询从未被下单的商品
-- ------------------------------------------------------------
SELECT id, name
FROM products
WHERE id <> ALL (SELECT product_id FROM order_items WHERE product_id IS NOT NULL)
ORDER BY id;

-- ============================================================
-- 四、行子查询（返回单行多列，配合行构造器）
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 行子查询：查询与 id=1 商品"同分类同价格"的其他商品
--     使用行构造器 (col1, col2) = (SELECT ...)
-- ------------------------------------------------------------
SELECT id, name, category_id, price
FROM products
WHERE (category_id, price) = (
    SELECT category_id, price FROM products WHERE id = 1
)
  AND id <> 1
ORDER BY id;

-- 对照：先看 id=1 商品的分类和价格
SELECT id, name, category_id, price FROM products WHERE id = 1;

-- ============================================================
-- 五、子查询在 SELECT 子句的常见用法（关联子查询作列）
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 每个商品被评价的次数（相关标量子查询作列）
--     子查询引用外层 products.id，对每行商品执行一次
-- ------------------------------------------------------------
SELECT p.id, p.name,
       (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id) AS review_cnt
FROM products p
ORDER BY review_cnt DESC, p.id
LIMIT 10;

-- ------------------------------------------------------------
-- 5.2 每个用户的订单总数与总消费（相关标量子查询作列）
-- ------------------------------------------------------------
SELECT u.id, u.username,
       (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_cnt,
       (SELECT COALESCE(SUM(o.total_amount), 0) FROM orders o WHERE o.user_id = u.id) AS total_spent
FROM users u
ORDER BY total_spent DESC
LIMIT 10;

-- ============================================================
-- 六、嵌套子查询：子查询内部再套子查询
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 查询"消费总额最高的用户"的订单详情
--     外层：查该用户的订单
--     中层：按 user_id 求和并取最大 user_id
--     内层：SUM 聚合
-- ------------------------------------------------------------
SELECT o.id, o.user_id, o.total_amount, o.status, o.created_at
FROM orders o
WHERE o.user_id = (
    SELECT user_id
    FROM orders
    GROUP BY user_id
    ORDER BY SUM(total_amount) DESC
    LIMIT 1
)
ORDER BY o.created_at;

-- 对照：先看消费总额排行
SELECT user_id, SUM(total_amount) AS total
FROM orders
GROUP BY user_id
ORDER BY total DESC
LIMIT 3;

-- ============================================================
-- 标量子查询演示完毕。
-- 要点：标量子查询返回单值，可出现在 SELECT/WHERE/HAVING；
--       列子查询配合 IN/ANY/ALL；行子查询配合行构造器；
--       相关子查询对外层每行重新求值，注意性能。
-- ============================================================
