-- ============================================================
-- 文件用途: Day06 - 聚合函数演示
--           演示：COUNT 三种写法对比、SUM/AVG/MIN/MAX、GROUP_CONCAT、NULL 处理
--           基于 ecommerce 库
-- 执行方式: mysql> source 本文件路径
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. COUNT 函数：三种写法对比（重点！）
-- ============================================================

-- 1.1 COUNT(*)：统计所有行（含 NULL 行，不忽略任何行）
SELECT COUNT(*) AS 总用户数 FROM users;

-- 1.2 COUNT(列)：统计该列非 NULL 值的个数（忽略 NULL）
SELECT COUNT(deleted_at) AS 已删除用户数 FROM users;

-- 1.3 COUNT(DISTINCT 列)：统计该列不同非 NULL 值的个数
SELECT COUNT(DISTINCT role) AS 不同角色数 FROM users;

-- 1.4 三种写法放在一起对比
SELECT
    COUNT(*)              AS 总行数,
    COUNT(deleted_at)     AS 非空删除时间数,
    COUNT(DISTINCT role)  AS 不同角色数
FROM users;

-- 1.5 对比 COUNT(*) 与 COUNT(列) 的差异
--     COUNT(*) 包含 deleted_at IS NULL 的行
--     COUNT(deleted_at) 只统计 deleted_at IS NOT NULL 的行
SELECT
    COUNT(*) AS 全部用户,
    COUNT(deleted_at) AS 已删除用户,
    COUNT(*) - COUNT(deleted_at) AS 未删除用户
FROM users;

-- 1.6 统计不同状态的订单数
SELECT COUNT(*) AS 订单总数 FROM orders;
SELECT COUNT(DISTINCT status) AS 不同订单状态数 FROM orders;

-- ============================================================
-- 2. SUM 求和
-- ============================================================

-- 2.1 所有订单的总金额
SELECT SUM(total_amount) AS 总销售额 FROM orders;

-- 2.2 已完成订单的总金额
SELECT SUM(total_amount) AS 已完成销售额
FROM orders
WHERE status = 'completed';

-- 2.3 所有商品的库存总数
SELECT SUM(stock) AS 库存总数 FROM products;

-- 2.4 SUM 对 NULL 的处理：忽略 NULL
--     假设某些订单 total_amount 为 NULL，SUM 会跳过它们
SELECT SUM(total_amount) AS 总销售额 FROM orders;

-- ============================================================
-- 3. AVG 平均值
-- ============================================================

-- 3.1 所有商品的平均价格
SELECT AVG(price) AS 平均价格 FROM products;

-- 3.2 在售商品的平均价格
SELECT AVG(price) AS 在售平均价
FROM products
WHERE status = 'on_sale';

-- 3.3 AVG 对 NULL 的处理：忽略 NULL 行（分母不含 NULL 行）
--     若想"NULL 当作 0 参与平均"，用 IFNULL
SELECT
    AVG(price)              AS 默认平均_忽略NULL,
    AVG(IFNULL(price, 0))  AS NULL当0的平均
FROM products;

-- 3.4 保留两位小数（AVG 常配合 ROUND）
SELECT ROUND(AVG(price), 2) AS 平均价格保留两位 FROM products;

-- 3.5 平均评分
SELECT ROUND(AVG(rating), 2) AS 平均评分 FROM reviews;

-- ============================================================
-- 4. MIN / MAX 最值
-- ============================================================

-- 4.1 商品的最低价和最高价
SELECT
    MIN(price) AS 最低价,
    MAX(price) AS 最高价
FROM products;

-- 4.2 订单的最早创建时间与最晚创建时间
SELECT
    MIN(created_at) AS 最早订单,
    MAX(created_at) AS 最新订单
FROM orders;

-- 4.3 最高评分与最低评分
SELECT MIN(rating) AS 最低评分, MAX(rating) AS 最高评分 FROM reviews;

-- 4.4 最低库存（找库存最少的商品）
SELECT MIN(stock) AS 最低库存 FROM products;

-- ============================================================
-- 5. 聚合函数不搭配 GROUP BY 时：返回单行结果
-- ============================================================

-- 5.1 一条查询同时获取多个统计值
SELECT
    COUNT(*)         AS 商品总数,
    MIN(price)        AS 最低价,
    MAX(price)        AS 最高价,
    ROUND(AVG(price),2) AS 平均价,
    SUM(stock)        AS 库存合计
FROM products;

-- 5.2 同时统计订单多个指标
SELECT
    COUNT(*)                  AS 订单总数,
    SUM(total_amount)         AS 总金额,
    ROUND(AVG(total_amount),2) AS 平均订单金额,
    MIN(total_amount)         AS 最小订单,
    MAX(total_amount)         AS 最大订单
FROM orders;

-- ============================================================
-- 6. GROUP_CONCAT 拼接函数
-- ============================================================

-- 6.1 把所有角色拼接成逗号分隔的字符串
SELECT GROUP_CONCAT(role) AS 所有角色 FROM users;

-- 6.2 去重拼接
SELECT GROUP_CONCAT(DISTINCT role) AS 所有不同角色 FROM users;

-- 6.3 自定义分隔符
SELECT GROUP_CONCAT(DISTINCT role SEPARATOR ' | ') AS 角色 FROM users;

-- 6.4 排序后拼接
SELECT GROUP_CONCAT(username ORDER BY id DESC SEPARATOR ',') AS 用户名列表
FROM users;

-- 6.5 限制拼接长度（默认 1024 字节，超过会被截断）
--     调大方法：SET SESSION group_concat_max_len = 1000000;
SELECT GROUP_CONCAT(name SEPARATOR ',') AS 商品名列表 FROM products;

-- ============================================================
-- 7. 聚合函数对 NULL 处理对比演示
-- ============================================================

-- 7.1 创建临时表演示 NULL 处理
DROP TEMPORARY TABLE IF EXISTS demo_null;
CREATE TEMPORARY TABLE demo_null (
    id INT PRIMARY KEY,
    val INT
);
INSERT INTO demo_null (id, val) VALUES
    (1, 100),
    (2, 200),
    (3, NULL),
    (4, 300),
    (5, NULL);

-- 7.2 对比各种聚合函数对 NULL 的处理
SELECT
    COUNT(*)         AS 总行数,        -- 5（含 NULL 行）
    COUNT(val)       AS 非NULL值数,     -- 3（忽略 NULL）
    SUM(val)         AS 求和,          -- 600（忽略 NULL，不是 600+0）
    AVG(val)         AS 平均值,         -- 200（300/3，分母不含 NULL 行）
    AVG(IFNULL(val,0)) AS NULL当0的平均, -- 120（600/5）
    MIN(val)         AS 最小值,         -- 100（忽略 NULL）
    MAX(val)         AS 最大值,         -- 300（忽略 NULL）
    GROUP_CONCAT(val) AS 拼接           -- 100,200,300（忽略 NULL）
FROM demo_null;

-- 7.3 关键结论：
--     COUNT(*) 统计所有行（含 NULL 行）
--     其他所有聚合函数（COUNT(列)、SUM、AVG、MIN、MAX、GROUP_CONCAT）都忽略 NULL
--     AVG 的分母是"非 NULL 值的个数"，不是总行数

-- 7.4 全为 NULL 的情况
SELECT
    COUNT(*)   AS 总行数,
    COUNT(val) AS 非NULL数,
    SUM(val)   AS 求和,   -- 全 NULL 时 SUM 返回 NULL
    AVG(val)   AS 平均    -- 全 NULL 时 AVG 返回 NULL
FROM demo_null
WHERE val IS NULL;

-- 清理临时表
DROP TEMPORARY TABLE IF EXISTS demo_null;

-- ============================================================
-- 8. 聚合函数配合 IFNULL / COALESCE 处理 NULL
-- ============================================================

-- 8.1 用 IFNULL 把 NULL 当作 0 参与统计
SELECT
    COUNT(*)                AS 订单数,
    SUM(IFNULL(total_amount, 0)) AS 总金额_NULL当0
FROM orders;

-- 8.2 用 COALESCE 给聚合结果兜底（全 NULL 时返回 0 而不是 NULL）
SELECT
    COALESCE(SUM(total_amount), 0) AS 总金额_空则0
FROM orders
WHERE status = 'refunded';

-- ============================================================
-- 9. 综合示例：商品统计报表
-- ============================================================

-- 9.1 在售商品的整体统计
SELECT
    COUNT(*)                  AS 在售商品数,
    ROUND(AVG(price), 2)      AS 平均价格,
    MIN(price)                AS 最低价,
    MAX(price)                AS 最高价,
    SUM(stock)                AS 库存总数,
    GROUP_CONCAT(DISTINCT name SEPARATOR ' | ') AS 商品名_前若干
FROM products
WHERE status = 'on_sale';

-- 9.2 评价统计
SELECT
    COUNT(*)              AS 评价总数,
    ROUND(AVG(rating), 2) AS 平均评分,
    MIN(rating)           AS 最低评分,
    MAX(rating)           AS 最高评分
FROM reviews;
