-- ============================================================
-- 文件用途: Day07 - 多表连接（三表/四表 JOIN）演示
--           演示：订单→用户→订单详情→商品四表联查
--                 统计每用户各类商品购买数、订单完整信息查询
--           基于 ecommerce 库
-- 执行方式: mysql> source 本文件路径
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. 三表连接：订单 + 用户 + 订单详情
-- ============================================================

-- 1.1 查询订单详情（订单 + 用户 + 订单详情）
SELECT
    o.id AS 订单ID,
    u.username AS 用户名,
    o.status AS 订单状态,
    o.created_at AS 下单时间,
    oi.product_id AS 商品ID,
    oi.quantity AS 数量,
    oi.unit_price AS 单价
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
ORDER BY o.id, oi.id
LIMIT 30;
-- 连接顺序：
--   orders ──JOIN── users（拿用户名）
--          ──JOIN── order_items（拿订单详情）

-- 1.2 加 WHERE 过滤：只看已完成订单
SELECT
    o.id AS 订单ID,
    u.username AS 用户名,
    oi.product_id AS 商品ID,
    oi.quantity AS 数量,
    oi.unit_price AS 单价,
    oi.quantity * oi.unit_price AS 小计
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
WHERE o.status = 'completed'
ORDER BY o.id
LIMIT 30;

-- ============================================================
-- 2. 四表连接：订单 + 用户 + 订单详情 + 商品
-- ============================================================

-- 2.1 订单完整详情：用户名 + 商品名 + 数量 + 单价
SELECT
    o.id AS 订单ID,
    u.username AS 用户名,
    p.name AS 商品名,
    oi.quantity AS 数量,
    oi.unit_price AS 单价,
    oi.quantity * oi.unit_price AS 小计,
    o.status AS 订单状态,
    o.created_at AS 下单时间
FROM orders o
INNER JOIN users u ON o.user_id = u.id          -- 拿用户名
INNER JOIN order_items oi ON o.id = oi.order_id  -- 拿订单详情
INNER JOIN products p ON oi.product_id = p.id    -- 拿商品名
ORDER BY o.id, oi.id
LIMIT 50;
-- 连接链：
--   orders ──JOIN── users
--          ──JOIN── order_items ──JOIN── products
-- 每个 JOIN 都用 ON 指定关联列（外键关系）

-- 2.2 限制返回行数 + 排序
SELECT
    o.id AS 订单ID,
    u.username AS 用户名,
    p.name AS 商品名,
    oi.quantity AS 数量,
    oi.unit_price AS 单价,
    oi.quantity * oi.unit_price AS 小计
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
ORDER BY o.created_at DESC, o.id
LIMIT 30;

-- ============================================================
-- 3. 五表连接：订单 + 用户 + 订单详情 + 商品 + 分类
-- ============================================================

-- 3.1 订单详情含商品分类名
SELECT
    o.id AS 订单ID,
    u.username AS 用户名,
    p.name AS 商品名,
    c.name AS 分类名,
    oi.quantity AS 数量,
    oi.unit_price AS 单价,
    oi.quantity * oi.unit_price AS 小计,
    o.created_at AS 下单时间
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
INNER JOIN categories c ON p.category_id = c.id
ORDER BY o.id, oi.id
LIMIT 50;
-- 连接链：
--   orders ──JOIN── users
--          ──JOIN── order_items ──JOIN── products ──JOIN── categories

-- ============================================================
-- 4. 统计每用户各类商品购买数
-- ============================================================

-- 4.1 每个用户购买的商品数量按分类汇总
SELECT
    u.username AS 用户名,
    c.name AS 分类名,
    SUM(oi.quantity) AS 购买总数量,
    COUNT(DISTINCT o.id) AS 涉及订单数
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
INNER JOIN categories c ON p.category_id = c.id
GROUP BY u.id, u.username, c.id, c.name
ORDER BY u.username, 购买总数量 DESC
LIMIT 30;

-- 4.2 每个用户购买的各类商品销售额
SELECT
    u.username AS 用户名,
    c.name AS 分类名,
    SUM(oi.quantity * oi.unit_price) AS 销售额,
    SUM(oi.quantity) AS 购买数量
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
INNER JOIN categories c ON p.category_id = c.id
GROUP BY u.id, u.username, c.id, c.name
ORDER BY u.username, 销售额 DESC
LIMIT 30;

-- 4.3 每个用户购买的总数量与总金额（汇总）
SELECT
    u.username AS 用户名,
    COUNT(DISTINCT o.id) AS 订单数,
    SUM(oi.quantity) AS 总购买数量,
    SUM(oi.quantity * oi.unit_price) AS 总消费
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
GROUP BY u.id, u.username
ORDER BY 总消费 DESC
LIMIT 30;

-- ============================================================
-- 5. 统计每个分类的销售情况
-- ============================================================

-- 5.1 每个分类的销售总额与销售数量
SELECT
    c.name AS 分类名,
    COUNT(DISTINCT o.id) AS 订单数,
    COUNT(DISTINCT p.id) AS 商品数,
    SUM(oi.quantity) AS 总销量,
    SUM(oi.quantity * oi.unit_price) AS 总销售额,
    ROUND(AVG(oi.unit_price), 2) AS 平均单价
FROM categories c
INNER JOIN products p ON p.category_id = c.id
INNER JOIN order_items oi ON oi.product_id = p.id
INNER JOIN orders o ON oi.order_id = o.id
GROUP BY c.id, c.name
ORDER BY 总销售额 DESC;
-- 注意：从 categories 出发用 INNER JOIN，只显示有商品的分类

-- 5.2 每个分类的销售情况（LEFT JOIN，含无销售商品的分类）
SELECT
    c.name AS 分类名,
    COUNT(DISTINCT p.id) AS 商品数,
    COUNT(DISTINCT oi.order_id) AS 订单数,
    IFNULL(SUM(oi.quantity), 0) AS 总销量,
    IFNULL(SUM(oi.quantity * oi.unit_price), 0) AS 总销售额
FROM categories c
LEFT JOIN products p ON p.category_id = c.id
LEFT JOIN order_items oi ON oi.product_id = p.id
LEFT JOIN orders o ON oi.order_id = o.id
GROUP BY c.id, c.name
ORDER BY 总销售额 DESC;
-- LEFT JOIN：保留所有分类，无销售的分类销售额为 0

-- ============================================================
-- 6. JOIN 顺序与驱动表
-- ============================================================

-- 6.1 不同的 JOIN 书写顺序，结果相同
--     MySQL 优化器会自动选择最优连接顺序

-- 写法一：从 orders 出发
SELECT o.id, u.username, p.name
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
LIMIT 10;

-- 写法二：从 users 出发
SELECT o.id, u.username, p.name
FROM users u
INNER JOIN orders o ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
LIMIT 10;

-- 6.2 性能建议：
--     - 连接列（外键）上要有索引
--     - 小表驱动大表（优化器通常能自动判断）
--     - 避免笛卡尔积（一定要写 ON 条件）
--     - 只 SELECT 需要的列，避免 SELECT *

-- ============================================================
-- 7. LEFT JOIN 多表链（保留左表全部行）
-- ============================================================

-- 7.1 查所有用户及其订单详情（含没下单的、订单无详情的）
SELECT
    u.username AS 用户名,
    o.id AS 订单ID,
    o.total_amount AS 订单金额,
    oi.product_id AS 商品ID,
    oi.quantity AS 数量
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id
ORDER BY u.id, o.id, oi.id
LIMIT 50;
-- LEFT JOIN 链：保留所有用户
--   没下单的用户：订单字段 NULL
--   订单无详情的：商品字段 NULL

-- 7.2 LEFT JOIN 多表 + 聚合
SELECT
    u.username AS 用户名,
    COUNT(DISTINCT o.id) AS 订单数,
    COUNT(oi.id) AS 订单详情数,
    IFNULL(SUM(oi.quantity * oi.unit_price), 0) AS 总消费
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY u.id, u.username
ORDER BY 总消费 DESC
LIMIT 30;
-- 注意：COUNT(DISTINCT o.id) 在无订单时返回 0
--       COUNT(oi.id) 在无详情时返回 0
--       SUM 在全 NULL 时返回 NULL，用 IFNULL 转 0

-- ============================================================
-- 8. 综合示例：完整订单报表
-- ============================================================

-- 8.1 订单详情报表（含用户、商品、分类、数量、金额、状态）
SELECT
    o.id AS 订单ID,
    u.username AS 用户名,
    u.email AS 邮箱,
    p.name AS 商品名,
    c.name AS 分类名,
    oi.quantity AS 数量,
    oi.unit_price AS 单价,
    oi.quantity * oi.unit_price AS 小计,
    o.total_amount AS 订单总额,
    o.status AS 状态,
    o.created_at AS 下单时间
FROM orders o
INNER JOIN users u ON o.user_id = u.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
INNER JOIN categories c ON p.category_id = c.id
ORDER BY o.created_at DESC, o.id, oi.id
LIMIT 50;

-- 8.2 每个订单的明细汇总（订单 + 用户 + 明细数 + 明细总额）
SELECT
    o.id AS 订单ID,
    u.username AS 用户名,
    o.status AS 状态,
    COUNT(oi.id) AS 明细数,
    SUM(oi.quantity) AS 商品总数,
    SUM(oi.quantity * oi.unit_price) AS 明细合计,
    o.total_amount AS 订单总额,
    o.created_at AS 下单时间
FROM orders o
INNER JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, u.username, o.status, o.total_amount, o.created_at
ORDER BY o.created_at DESC
LIMIT 30;
-- LEFT JOIN order_items：保留无明细的订单（虽然业务上不应该出现）

-- 8.3 商品销售排行榜（按销售额降序）
SELECT
    p.id AS 商品ID,
    p.name AS 商品名,
    c.name AS 分类名,
    p.price AS 单价,
    COUNT(DISTINCT oi.order_id) AS 销售次数,
    SUM(oi.quantity) AS 总销量,
    SUM(oi.quantity * oi.unit_price) AS 总销售额
FROM products p
INNER JOIN categories c ON p.category_id = c.id
INNER JOIN order_items oi ON oi.product_id = p.id
GROUP BY p.id, p.name, c.name, p.price
ORDER BY 总销售额 DESC
LIMIT 20;
-- INNER JOIN：只显示有销售记录的商品
-- 若要包含未销售商品，改用 LEFT JOIN order_items

-- 8.4 用户消费排行榜（按总消费降序，含 0 消费用户）
SELECT
    u.id AS 用户ID,
    u.username AS 用户名,
    u.email AS 邮箱,
    COUNT(DISTINCT o.id) AS 订单数,
    IFNULL(SUM(oi.quantity * oi.unit_price), 0) AS 总消费
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY u.id, u.username, u.email
ORDER BY 总消费 DESC
LIMIT 30;
