-- ============================================================
-- 文件名称: 03-derived-table.sql
-- 文件用途: 派生表（FROM 子查询）、CTE（WITH AS）、递归 CTE 演示
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day08 - 子查询/Code/03-derived-table.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 一、派生表（Derived Table）：FROM 子句中的子查询
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 派生表基本用法：先聚合每个用户的订单数与总额，再筛选>=3单
--     注意：派生表必须起别名（这里叫 t），否则报错
-- ------------------------------------------------------------
SELECT t.user_id, t.order_cnt, t.total_spent
FROM (
    SELECT user_id,
           COUNT(*)        AS order_cnt,
           SUM(total_amount) AS total_spent
    FROM orders
    GROUP BY user_id
) t
WHERE t.order_cnt >= 3
ORDER BY t.total_spent DESC;

-- ------------------------------------------------------------
-- 1.2 派生表 + 关联：每个用户的订单数与账户余额对比
--     派生表与 accounts 表 JOIN
-- ------------------------------------------------------------
SELECT t.user_id, t.order_cnt, t.total_spent, a.balance
FROM (
    SELECT user_id, COUNT(*) AS order_cnt, SUM(total_amount) AS total_spent
    FROM orders
    GROUP BY user_id
) t
LEFT JOIN accounts a ON a.user_id = t.user_id
ORDER BY t.total_spent DESC;

-- ------------------------------------------------------------
-- 1.3 派生表嵌套：每个分类的"平均商品价格"再按平均价排序
-- ------------------------------------------------------------
SELECT t.category_id, t.avg_price, c.name AS category_name
FROM (
    SELECT category_id, AVG(price) AS avg_price
    FROM products
    GROUP BY category_id
) t
JOIN categories c ON c.id = t.category_id
ORDER BY t.avg_price DESC;

-- ============================================================
-- 二、CTE（公用表表达式）WITH AS
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 用 CTE 改写派生表（1.1 的等价写法）
--     CTE 把子查询命名复用，可读性更好
-- ------------------------------------------------------------
WITH user_order_stat AS (
    SELECT user_id,
           COUNT(*)          AS order_cnt,
           SUM(total_amount) AS total_spent
    FROM orders
    GROUP BY user_id
)
SELECT user_id, order_cnt, total_spent
FROM user_order_stat
WHERE order_cnt >= 3
ORDER BY total_spent DESC;

-- ------------------------------------------------------------
-- 2.2 多个 CTE：用逗号分隔，后面的可引用前面的
--     先找出"消费超 1000"的重度用户，再查他们的评价
-- ------------------------------------------------------------
WITH
heavy_users AS (
    SELECT user_id
    FROM orders
    GROUP BY user_id
    HAVING SUM(total_amount) > 1000
),
their_reviews AS (
    SELECT r.user_id, r.product_id, r.rating, r.content
    FROM reviews r
    JOIN heavy_users h ON r.user_id = h.user_id
)
SELECT user_id, product_id, rating, LEFT(content, 30) AS content_preview
FROM their_reviews
ORDER BY user_id, product_id;

-- ------------------------------------------------------------
-- 2.3 CTE 多次引用：同一 CTE 在主查询中被引用两次
--     计算每个商品评价数与"全店评价数中位数"的对比
-- ------------------------------------------------------------
WITH product_review_cnt AS (
    SELECT product_id, COUNT(*) AS cnt
    FROM reviews
    GROUP BY product_id
)
SELECT p.id, p.name,
       COALESCE(prc.cnt, 0) AS review_cnt,
       (SELECT AVG(cnt) FROM product_review_cnt) AS avg_review_cnt
FROM products p
LEFT JOIN product_review_cnt prc ON prc.product_id = p.id
ORDER BY review_cnt DESC
LIMIT 10;

-- ============================================================
-- 三、派生表 vs CTE 对比（语义等价，写法差异）
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 派生表写法（嵌套在 FROM）
-- ------------------------------------------------------------
SELECT d.category_id, d.product_cnt, c.name
FROM (
    SELECT category_id, COUNT(*) AS product_cnt
    FROM products
    GROUP BY category_id
) d
JOIN categories c ON c.id = d.category_id
ORDER BY d.product_cnt DESC;

-- ------------------------------------------------------------
-- 3.2 CTE 写法（命名提前，扁平化）
-- ------------------------------------------------------------
WITH cat_product_cnt AS (
    SELECT category_id, COUNT(*) AS product_cnt
    FROM products
    GROUP BY category_id
)
SELECT cpc.category_id, cpc.product_cnt, c.name
FROM cat_product_cnt cpc
JOIN categories c ON c.id = cpc.category_id
ORDER BY cpc.product_cnt DESC;

-- ============================================================
-- 四、递归 CTE：查询分类树
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 先查看分类表结构，了解 parent_id（0=顶级）与层级
-- ------------------------------------------------------------
SELECT id, name, parent_id, sort_order
FROM categories
ORDER BY parent_id, sort_order;

-- ------------------------------------------------------------
-- 4.2 递归 CTE：从顶级分类往下找所有子孙分类
--     锚点：parent_id = 0 的顶级分类
--     递归：JOIN 自身，parent_id 指向上一层 id
--     depth 记录层级，path 记录路径便于排序与查看
-- ------------------------------------------------------------
WITH RECURSIVE category_tree AS (
    -- 锚点成员：顶级分类
    SELECT id, name, parent_id, 0 AS depth,
           CAST(id AS CHAR(1000)) AS path,
           name AS path_name
    FROM categories
    WHERE parent_id = 0
    UNION ALL
    -- 递归成员：子分类
    SELECT c.id, c.name, c.parent_id, ct.depth + 1,
           CONCAT(ct.path, '->', c.id),
           CONCAT(ct.path_name, ' > ', c.name)
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT id, name, parent_id, depth, path_name
FROM category_tree
ORDER BY path;

-- ------------------------------------------------------------
-- 4.3 递归 CTE 反向：从指定分类往上找所有祖先
--     假设查找 id = 5 的分类的所有上级（含自身）
-- ------------------------------------------------------------
WITH RECURSIVE ancestor_chain AS (
    -- 锚点：从指定分类开始
    SELECT id, name, parent_id, 0 AS depth
    FROM categories
    WHERE id = 5
    UNION ALL
    -- 递归：找上一级父分类
    SELECT c.id, c.name, c.parent_id, ac.depth + 1
    FROM categories c
    JOIN ancestor_chain ac ON c.id = ac.parent_id
)
SELECT id, name, parent_id, depth AS steps_from_target
FROM ancestor_chain
ORDER BY depth;

-- ------------------------------------------------------------
-- 4.4 递归 CTE 统计：每个顶级分类下所有子孙分类的商品总数
--     思路：递归出每个分类的"根分类 id"，再 JOIN products 聚合
-- ------------------------------------------------------------
WITH RECURSIVE cat_with_root AS (
    -- 锚点：顶级分类，根就是自己
    SELECT id, name, parent_id, id AS root_id, name AS root_name
    FROM categories
    WHERE parent_id = 0
    UNION ALL
    -- 递归：子分类继承父分类的 root_id
    SELECT c.id, c.name, c.parent_id, cwr.root_id, cwr.root_name
    FROM categories c
    JOIN cat_with_root cwr ON c.parent_id = cwr.id
)
SELECT cwr.root_id, cwr.root_name, COUNT(p.id) AS product_total
FROM cat_with_root cwr
LEFT JOIN products p ON p.category_id = cwr.id
GROUP BY cwr.root_id, cwr.root_name
ORDER BY product_total DESC;

-- ============================================================
-- 五、LATERAL 派生表（MySQL 8.0.14+）
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 LATERAL 允许派生表引用左侧表的列
--     示例：每个用户最近 2 笔订单（按时间倒序）
--     普通 JOIN 无法做"每行取前 N 条"，LATERAL 可实现
-- ------------------------------------------------------------
SELECT u.id AS user_id, u.username, o.id AS order_id, o.total_amount, o.created_at
FROM users u
JOIN LATERAL (
    SELECT id, total_amount, created_at
    FROM orders
    WHERE user_id = u.id
    ORDER BY created_at DESC
    LIMIT 2
) o ON TRUE
ORDER BY u.id, o.created_at DESC;

-- 对照：用窗口函数 ROW_NUMBER 也能实现"每组前 N"（Day09 详解）
-- WITH ranked AS (
--     SELECT id, user_id, total_amount, created_at,
--            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
--     FROM orders
-- )
-- SELECT * FROM ranked WHERE rn <= 2 ORDER BY user_id, rn;

-- ============================================================
-- 派生表与 CTE 演示完毕。
-- 要点：派生表必须起别名；CTE 提升可读性且可多次引用；
--       递归 CTE 用 WITH RECURSIVE + UNION ALL 遍历树形结构；
--       LATERAL 派生表可实现"每组取前 N"。
-- ============================================================
