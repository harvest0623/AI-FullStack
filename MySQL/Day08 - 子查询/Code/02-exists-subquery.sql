-- ============================================================
-- 文件名称: 02-exists-subquery.sql
-- 文件用途: EXISTS / NOT EXISTS 演示
--           相关子查询、存在性检查
--           NOT IN 的 NULL 陷阱演示与规避
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day08 - 子查询/Code/02-exists-subquery.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 一、EXISTS：判断子查询是否有行返回
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 查询"有下过订单"的用户
--     EXISTS 只关心子查询是否能查到行，不关心列值，故用 SELECT 1
--     子查询引用外层 users.id，属于相关子查询
-- ------------------------------------------------------------
SELECT u.id, u.username, u.email
FROM users u
WHERE EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.user_id = u.id
)
ORDER BY u.id;

-- 对照：用 IN 实现同样语义
SELECT u.id, u.username, u.email
FROM users u
WHERE u.id IN (SELECT user_id FROM orders)
ORDER BY u.id;

-- ------------------------------------------------------------
-- 1.2 查询"有评价记录"的商品
-- ------------------------------------------------------------
SELECT p.id, p.name, p.price
FROM products p
WHERE EXISTS (
    SELECT 1 FROM reviews r WHERE r.product_id = p.id
)
ORDER BY p.id;

-- ============================================================
-- 二、NOT EXISTS：判断子查询是否无行返回
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 查询"没有评价"的商品
--     NOT EXISTS 不受 NULL 影响，是"查找没有 X 的记录"的首选写法
-- ------------------------------------------------------------
SELECT p.id, p.name, p.price, p.status
FROM products p
WHERE NOT EXISTS (
    SELECT 1 FROM reviews r WHERE r.product_id = p.id
)
ORDER BY p.id;

-- ------------------------------------------------------------
-- 2.2 查询"从未被下单"的商品
-- ------------------------------------------------------------
SELECT p.id, p.name, p.price, p.stock
FROM products p
WHERE NOT EXISTS (
    SELECT 1 FROM order_items oi WHERE oi.product_id = p.id
)
ORDER BY p.id;

-- ------------------------------------------------------------
-- 2.3 查询"没有订单"的用户（潜在流失用户）
-- ------------------------------------------------------------
SELECT u.id, u.username, u.created_at
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id
)
ORDER BY u.created_at;

-- ============================================================
-- 三、相关子查询的其他用法
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 查询每个分类中价格最高的商品（相关子查询 + ALL）
--     外层遍历每个商品，子查询找"同分类中所有商品价格"，用 >= ALL 判断是否最大
-- ------------------------------------------------------------
SELECT p.id, p.name, p.category_id, p.price
FROM products p
WHERE p.price >= ALL (
    SELECT p2.price FROM products p2 WHERE p2.category_id = p.category_id
)
ORDER BY p.category_id, p.price DESC;

-- 对照：用 GROUP BY 找每个分类最高价
SELECT category_id, MAX(price) AS max_price
FROM products
GROUP BY category_id
ORDER BY category_id;

-- ------------------------------------------------------------
-- 3.2 查询评价数 >= 2 的商品（EXISTS 形式的关联判断）
--     用相关子查询统计每个商品的评价数
-- ------------------------------------------------------------
SELECT p.id, p.name,
       (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id) AS review_cnt
FROM products p
WHERE (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id) >= 2
ORDER BY review_cnt DESC, p.id;

-- ============================================================
-- 四、NOT IN 的 NULL 陷阱演示
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 临时构造一个含 NULL 的子查询结果，演示 NOT IN 失效
--     若 reviews 表中存在 product_id IS NULL 的脏数据：
--       NOT IN (1, 2, NULL) 对任意 x 都返回 UNKNOWN => 整体结果为空
-- ------------------------------------------------------------
-- 检查 reviews 表是否有 product_id 为 NULL 的记录
SELECT COUNT(*) AS null_product_reviews FROM reviews WHERE product_id IS NULL;

-- 演示 NULL 陷阱：用 UNION 显式构造一个含 NULL 的集合
-- 这条查询会返回空集，即使 products 表里有未被评价的商品
SELECT id, name
FROM products
WHERE id NOT IN (
    SELECT product_id FROM reviews
    UNION SELECT NULL  -- 故意注入一个 NULL
)
ORDER BY id;

-- ------------------------------------------------------------
-- 4.2 规避 NULL 陷阱的方法一：子查询中过滤掉 NULL
--     加 WHERE product_id IS NOT NULL
-- ------------------------------------------------------------
SELECT id, name
FROM products
WHERE id NOT IN (SELECT product_id FROM reviews WHERE product_id IS NOT NULL)
ORDER BY id;

-- ------------------------------------------------------------
-- 4.3 规避 NULL 陷阱的方法二（推荐）：改用 NOT EXISTS
--     NOT EXISTS 天然不受 NULL 影响
-- ------------------------------------------------------------
SELECT p.id, p.name
FROM products p
WHERE NOT EXISTS (
    SELECT 1 FROM reviews r WHERE r.product_id = p.id
)
ORDER BY p.id;

-- ============================================================
-- 五、EXISTS vs IN 性能对比示例
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 当子查询结果集较小时，IN 与 EXISTS 性能接近
--     查询有评价的商品：两种写法对比
-- ------------------------------------------------------------
-- 写法 A：IN（先算子查询所有 product_id，再匹配外表）
SELECT p.id, p.name
FROM products p
WHERE p.id IN (SELECT product_id FROM reviews)
ORDER BY p.id;

-- 写法 B：EXISTS（逐行外表，子查询走索引找到首行即返回）
SELECT p.id, p.name
FROM products p
WHERE EXISTS (SELECT 1 FROM reviews r WHERE r.product_id = p.id)
ORDER BY p.id;

-- ------------------------------------------------------------
-- 5.2 经验：外表小、子表大且子表关联列有索引时，EXISTS 更优
--         子查询结果集小时，IN 更直观
-- ------------------------------------------------------------
-- 用 EXPLAIN 对比两种写法（Day10 详解 EXPLAIN）
-- EXPLAIN SELECT * FROM products p WHERE p.id IN (SELECT product_id FROM reviews);
-- EXPLAIN SELECT * FROM products p WHERE EXISTS (SELECT 1 FROM reviews r WHERE r.product_id = p.id);

-- ============================================================
-- 六、EXISTS 的双表关联判断
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 查询"既下了单又写了评价"的活跃用户
--     两个 EXISTS 同时满足
-- ------------------------------------------------------------
SELECT u.id, u.username
FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id)
  AND EXISTS (SELECT 1 FROM reviews r WHERE r.user_id = u.id)
ORDER BY u.id;

-- ============================================================
-- EXISTS 子查询演示完毕。
-- 要点：EXISTS 只判断有无行返回；NOT EXISTS 不受 NULL 影响；
--       "查找没有 X 的记录"优先用 NOT EXISTS 而非 NOT IN；
--       相关子查询对外层每行触发一次，注意索引与行数。
-- ============================================================
