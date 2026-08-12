-- ============================================================
-- 文件用途: Day06 - 分组查询与 HAVING 演示
--           演示：单列/多列分组、HAVING、WHERE vs HAVING 对比、WITH ROLLUP
--                 按订单状态统计、按商品分类统计销售额
--           基于 ecommerce 库
-- 执行方式: mysql> source 本文件路径
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. GROUP BY 单列分组
-- ============================================================

-- 1.1 统计每个角色的用户数
SELECT
    role,
    COUNT(*) AS 用户数
FROM users
GROUP BY role;

-- 1.2 统计每种订单状态的数量
SELECT
    status,
    COUNT(*) AS 订单数
FROM orders
GROUP BY status;

-- 1.3 统计每个商品分类下的商品数
SELECT
    category_id,
    COUNT(*) AS 商品数
FROM products
GROUP BY category_id;

-- 1.4 统计每个评分等级的评价数
SELECT
    rating,
    COUNT(*) AS 评价数
FROM reviews
GROUP BY rating
ORDER BY rating DESC;

-- ============================================================
-- 2. GROUP BY 多列分组
-- ============================================================

-- 2.1 按 role + status 两级分组
SELECT
    role,
    status,
    COUNT(*) AS 用户数
FROM users
GROUP BY role, status
ORDER BY role, status;

-- 2.2 按订单状态 + 用户角色分组（需先 JOIN）
--     先通过 orders 找到 user_id，再 JOIN users 拿到 role
SELECT
    u.role,
    o.status,
    COUNT(*) AS 订单数
FROM orders o
INNER JOIN users u ON o.user_id = u.id
GROUP BY u.role, o.status
ORDER BY u.role, o.status;

-- 2.3 按商品分类 + 状态分组
SELECT
    category_id,
    status,
    COUNT(*) AS 商品数,
    ROUND(AVG(price), 2) AS 平均价
FROM products
GROUP BY category_id, status
ORDER BY category_id, status;

-- ============================================================
-- 3. SELECT 列的约束（ONLY_FULL_GROUP_BY）
-- ============================================================

-- 3.1 正确写法：SELECT 只选分组列与聚合列
SELECT
    role,
    COUNT(*) AS 用户数
FROM users
GROUP BY role;

-- 3.2 错误写法：username 不是分组列，也不是聚合列
--     在 MySQL 8 默认 ONLY_FULL_GROUP_BY 模式下会报错
-- SELECT role, username, COUNT(*) FROM users GROUP BY role;
-- 报错：Expression #2 of SELECT list is not in GROUP BY clause...

-- 3.3 查看当前 sql_mode（确认是否开启 ONLY_FULL_GROUP_BY）
SELECT @@sql_mode;

-- 3.4 临时关闭 ONLY_FULL_GROUP_BY（仅测试，生产不建议）
-- SET SESSION sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''));

-- 3.5 重新开启
-- SET SESSION sql_mode = CONCAT(@@sql_mode, ',ONLY_FULL_GROUP_BY');

-- ============================================================
-- 4. 多聚合函数组合
-- ============================================================

-- 4.1 每个商品分类的统计：商品数、最低价、最高价、平均价、库存总和
SELECT
    category_id,
    COUNT(*)           AS 商品数,
    MIN(price)         AS 最低价,
    MAX(price)         AS 最高价,
    ROUND(AVG(price),2) AS 平均价,
    SUM(stock)         AS 库存合计
FROM products
GROUP BY category_id
ORDER BY category_id;

-- 4.2 每个用户的订单统计
SELECT
    user_id,
    COUNT(*)                   AS 订单数,
    SUM(total_amount)          AS 总消费,
    ROUND(AVG(total_amount),2)  AS 平均订单金额,
    MIN(total_amount)          AS 最小订单,
    MAX(total_amount)          AS 最大订单
FROM orders
GROUP BY user_id
ORDER BY 总消费 DESC;

-- 4.3 每个商品的评价统计
SELECT
    product_id,
    COUNT(*)              AS 评价数,
    ROUND(AVG(rating),2)  AS 平均评分,
    MIN(rating)           AS 最低分,
    MAX(rating)           AS 最高分
FROM reviews
GROUP BY product_id
ORDER BY 平均评分 DESC, 评价数 DESC;

-- ============================================================
-- 5. HAVING 分组后过滤
-- ============================================================

-- 5.1 找出订单数 >= 3 的用户
SELECT
    user_id,
    COUNT(*) AS 订单数
FROM orders
GROUP BY user_id
HAVING COUNT(*) >= 3;

-- 5.2 找出总消费 > 5000 的用户
SELECT
    user_id,
    COUNT(*) AS 订单数,
    SUM(total_amount) AS 总消费
FROM orders
GROUP BY user_id
HAVING SUM(total_amount) > 5000
ORDER BY 总消费 DESC;

-- 5.3 找出平均评分 >= 4 的商品
SELECT
    product_id,
    COUNT(*) AS 评价数,
    ROUND(AVG(rating),2) AS 平均评分
FROM reviews
GROUP BY product_id
HAVING AVG(rating) >= 4
ORDER BY 平均评分 DESC;

-- 5.4 HAVING 中可以用 SELECT 别名（MySQL 特性，其他数据库不行）
SELECT
    user_id,
    COUNT(*) AS 订单数,
    SUM(total_amount) AS 总消费
FROM orders
GROUP BY user_id
HAVING 总消费 > 5000;   -- MySQL 允许在 HAVING 中引用别名

-- ============================================================
-- 6. WHERE vs HAVING 对比（核心！）
-- ============================================================

-- 6.1 同时用 WHERE 和 HAVING
--     WHERE 先过滤行（2025 年的订单）
--     GROUP BY 对过滤后的行分组
--     HAVING 再过滤组（订单数 >= 3）
SELECT
    user_id,
    COUNT(*) AS 订单数,
    SUM(total_amount) AS 总消费
FROM orders
WHERE created_at >= '2025-01-01'    -- 行级过滤（分组前）
GROUP BY user_id
HAVING COUNT(*) >= 3;               -- 组级过滤（分组后）

-- 6.2 错误尝试：在 WHERE 中用聚合函数（会报错）
-- SELECT user_id FROM orders WHERE COUNT(*) >= 3 GROUP BY user_id;
-- 报错：Invalid use of group function
-- 原因：聚合函数在 SELECT 阶段才计算，WHERE 在它之前执行

-- 6.3 对比表：
-- | 维度       | WHERE             | HAVING            |
-- | 执行时机   | 分组前            | 分组后            |
-- | 过滤对象   | 行                | 组                |
-- | 聚合函数  | 不能用            | 能用              |
-- | 别名引用   | 不能用            | MySQL 能用        |

-- 6.4 性能建议：能放 WHERE 就放 WHERE（先过滤减少分组数据量）
--     反例：把行级条件错误放到 HAVING
SELECT user_id, COUNT(*) AS 订单数
FROM orders
GROUP BY user_id
HAVING MAX(created_at) >= '2025-01-01';  -- 不推荐：本应放 WHERE
-- 推荐写法：
SELECT user_id, COUNT(*) AS 订单数
FROM orders
WHERE created_at >= '2025-01-01'         -- 推荐：放 WHERE 先过滤
GROUP BY user_id;

-- ============================================================
-- 7. WITH ROLLUP 分组小计与总计
-- ============================================================

-- 7.1 按角色统计用户数，并附加总计行
SELECT
    IFNULL(role, '总计') AS 角色,
    COUNT(*) AS 用户数
FROM users
GROUP BY role WITH ROLLUP;
-- 输出：admin | 3
--       editor | 5
--       customer | 92
--       总计 | 100   ← ROLLUP 生成的总计行

-- 7.2 按订单状态统计，并附加总计
SELECT
    IFNULL(status, '总计') AS 状态,
    COUNT(*) AS 订单数,
    ROUND(SUM(total_amount),2) AS 总金额
FROM orders
GROUP BY status WITH ROLLUP;

-- 7.3 多列 ROLLUP：按 role + status 两级分组
SELECT
    IFNULL(role, '所有角色') AS 角色,
    IFNULL(status, '所有状态') AS 状态,
    COUNT(*) AS 用户数
FROM users
GROUP BY role, status WITH ROLLUP
ORDER BY role, status;
-- 输出包含：
--   每个 (role,status) 组合行
--   每个 role 的小计行（status 为 NULL）
--   总计行（role 和 status 都为 NULL）

-- ============================================================
-- 8. 按订单状态统计（业务报表）
-- ============================================================

-- 8.1 各状态的订单数与总金额
SELECT
    status,
    COUNT(*) AS 订单数,
    ROUND(SUM(total_amount), 2) AS 总金额,
    ROUND(AVG(total_amount), 2) AS 平均金额
FROM orders
GROUP BY status
ORDER BY 总金额 DESC;

-- 8.2 状态 + 月份的组合统计
SELECT
    status,
    DATE_FORMAT(created_at, '%Y-%m') AS 月份,
    COUNT(*) AS 订单数,
    ROUND(SUM(total_amount), 2) AS 总金额
FROM orders
GROUP BY status, DATE_FORMAT(created_at, '%Y-%m')
ORDER BY 月份 DESC, status;

-- ============================================================
-- 9. 按商品分类统计销售额
-- ============================================================

-- 9.1 每个分类的商品数与库存
SELECT
    category_id,
    COUNT(*) AS 商品数,
    SUM(stock) AS 库存合计,
    ROUND(AVG(price),2) AS 平均价
FROM products
GROUP BY category_id
ORDER BY 商品数 DESC;

-- 9.2 每个分类的销售额（需 JOIN order_items 和 products）
--     统计每个商品分类的累计销售额
SELECT
    p.category_id,
    COUNT(DISTINCT oi.order_id) AS 订单数,
    SUM(oi.quantity * oi.unit_price) AS 销售额
FROM order_items oi
INNER JOIN products p ON oi.product_id = p.id
GROUP BY p.category_id
ORDER BY 销售额 DESC;

-- 9.3 每个分类的销售额，并附带总计（WITH ROLLUP）
SELECT
    IFNULL(p.category_id, '总计') AS 分类,
    COUNT(DISTINCT oi.order_id) AS 订单数,
    SUM(oi.quantity * oi.unit_price) AS 销售额
FROM order_items oi
INNER JOIN products p ON oi.product_id = p.id
GROUP BY p.category_id WITH ROLLUP;

-- ============================================================
-- 10. 条件聚合：用 CASE WHEN 做条件统计
-- ============================================================

-- 10.1 每个分类下：在售商品数 vs 下架商品数
SELECT
    category_id,
    COUNT(*) AS 商品总数,
    SUM(CASE WHEN status = 'on_sale'   THEN 1 ELSE 0 END) AS 在售数,
    SUM(CASE WHEN status = 'off_sale'  THEN 1 ELSE 0 END) AS 已下架数,
    SUM(CASE WHEN status = 'draft'     THEN 1 ELSE 0 END) AS 草稿数
FROM products
GROUP BY category_id
ORDER BY category_id;

-- 10.2 每个用户：不同状态订单数
SELECT
    user_id,
    COUNT(*) AS 总订单数,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS 已完成,
    SUM(CASE WHEN status = 'paid'      THEN 1 ELSE 0 END) AS 已支付,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS 已取消,
    SUM(CASE WHEN status = 'refunded'  THEN 1 ELSE 0 END) AS 已退款
FROM orders
GROUP BY user_id
ORDER BY 总订单数 DESC
LIMIT 20;

-- 10.3 评分分布：每个商品的好评/中评/差评数
SELECT
    product_id,
    COUNT(*) AS 评价总数,
    SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) AS 好评数,
    SUM(CASE WHEN rating = 3  THEN 1 ELSE 0 END) AS 中评数,
    SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) AS 差评数
FROM reviews
GROUP BY product_id
ORDER BY 评价总数 DESC
LIMIT 20;

-- ============================================================
-- 11. GROUP_CONCAT 配合 GROUP BY
-- ============================================================

-- 11.1 每个用户的订单号列表
SELECT
    user_id,
    COUNT(*) AS 订单数,
    GROUP_CONCAT(id ORDER BY id ASC SEPARATOR ',') AS 订单号列表
FROM orders
GROUP BY user_id
ORDER BY 订单数 DESC
LIMIT 10;

-- 11.2 每个商品分类下的商品名
SELECT
    category_id,
    COUNT(*) AS 商品数,
    GROUP_CONCAT(name SEPARATOR ' | ') AS 商品名列表
FROM products
GROUP BY category_id;

-- 11.3 每个用户的评分商品列表
SELECT
    user_id,
    COUNT(*) AS 评价数,
    GROUP_CONCAT(DISTINCT product_id ORDER BY product_id) AS 评价商品ID
FROM reviews
GROUP BY user_id
ORDER BY 评价数 DESC
LIMIT 10;

-- ============================================================
-- 12. 综合示例：用户消费报表
-- ============================================================

-- 12.1 找出 2025 年总消费 >= 10000 的高价值用户
SELECT
    user_id,
    COUNT(*) AS 订单数,
    ROUND(SUM(total_amount), 2) AS 总消费,
    ROUND(AVG(total_amount), 2) AS 平均订单,
    MAX(total_amount) AS 最大单笔,
    MIN(created_at) AS 首单时间,
    MAX(created_at) AS 末单时间
FROM orders
WHERE created_at >= '2025-01-01'
  AND status IN ('paid', 'shipped', 'completed')
GROUP BY user_id
HAVING SUM(total_amount) >= 10000
ORDER BY 总消费 DESC;
