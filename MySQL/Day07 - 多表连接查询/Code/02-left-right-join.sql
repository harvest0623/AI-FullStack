-- ============================================================
-- 文件用途: Day07 - 左/右连接（LEFT/RIGHT JOIN）演示
--           演示：查所有用户含无订单的、ON vs WHERE 区别演示
--                 LEFT JOIN 退化陷阱、RIGHT JOIN 与 LEFT JOIN 转换
--           基于 ecommerce 库
-- 执行方式: mysql> source 本文件路径
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. LEFT JOIN 基础：保留左表全部行
-- ============================================================

-- 1.1 查询所有用户及其订单（含没下单的用户）
--     LEFT JOIN：左表(users)全部保留，右表(orders)无匹配时填 NULL
SELECT
    u.id AS 用户ID,
    u.username AS 用户名,
    o.id AS 订单ID,
    o.total_amount AS 订单金额,
    o.status AS 订单状态
FROM users u                          -- 左表：全部保留
LEFT JOIN orders o ON u.id = o.user_id  -- 右表：无匹配填 NULL
LIMIT 30;

-- 1.2 对比 INNER JOIN：没下单的用户不出现
SELECT
    u.id AS 用户ID,
    u.username AS 用户名,
    o.id AS 订单ID
FROM users u
INNER JOIN orders o ON u.id = o.user_id
LIMIT 30;

-- 1.3 统计每个用户的订单数（LEFT JOIN 保证没下单的也算 0）
SELECT
    u.id,
    u.username,
    COUNT(o.id) AS 订单数
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username
ORDER BY 订单数 DESC
LIMIT 20;
-- 注意：COUNT(o.id) 在无匹配时返回 0（因为 o.id 是 NULL，COUNT 忽略 NULL）
--      若用 COUNT(*) 会返回 1（因为 LEFT JOIN 会保留一行，右表全 NULL）

-- ============================================================
-- 2. LEFT JOIN 经典模式：查"不存在 Y 的 X"
-- ============================================================

-- 2.1 查没下过单的用户（LEFT JOIN + WHERE 右表 IS NULL）
SELECT
    u.id,
    u.username,
    u.email
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL;
-- 解释：LEFT JOIN 后，没下单的用户那一行 o.id 为 NULL
--       WHERE o.id IS NULL 筛出这些用户

-- 2.2 查没有任何评价的商品
SELECT
    p.id,
    p.name
FROM products p
LEFT JOIN reviews r ON p.id = r.product_id
WHERE r.id IS NULL;

-- 2.3 查没有商品的分类
SELECT
    c.id,
    c.name
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
WHERE p.id IS NULL;

-- ============================================================
-- 3. LEFT JOIN 的 NULL 判断
-- ============================================================

-- 3.1 LEFT JOIN 无匹配时，右表所有列都是 NULL
--     判断"无匹配"最可靠的方式是检查右表主键 IS NULL
SELECT
    u.username,
    o.id AS 订单ID,
    CASE WHEN o.id IS NULL THEN '无订单' ELSE '有订单' END AS 状态
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LIMIT 20;

-- 3.2 注意：不要用右表的非主键列判断 NULL
--     因为该列本身可能存的就是 NULL（与无匹配难以区分）
--     用主键（如 o.id）最可靠

-- ============================================================
-- 4. ON vs WHERE 区别演示（核心陷阱！）
-- ============================================================

-- 4.1 场景：查所有用户，及其"已完成"订单
--     需求：保留所有用户（含没完成订单的）

-- 写法一【正确】：右表过滤条件放 ON
SELECT
    u.username,
    o.id AS 订单ID,
    o.status
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'completed';
-- 含义：保留所有用户；连接时只匹配 status='completed' 的订单
--       没完成订单的用户：订单字段为 NULL（保留）
-- 结果：所有用户都出现

-- 写法二【错误】：右表过滤条件放 WHERE
SELECT
    u.username,
    o.id AS 订单ID,
    o.status
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';
-- 含义：先 LEFT JOIN 全部，再过滤 o.status='completed'
-- 结果：只保留有完成订单的用户，没完成订单的用户被过滤
--       LEFT JOIN 退化成 INNER JOIN！

-- 4.2 对比两种写法的结果集
--     写法一：用户总数 = 全部用户数
SELECT COUNT(DISTINCT u.id) AS 用户数
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'completed';

--     写法二：用户数 < 全部用户数（退化成 INNER JOIN）
SELECT COUNT(DISTINCT u.id) AS 用户数
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';

-- 4.3 规则总结：
--     对右表的过滤条件：
--       想保留左表全部行 → 放 ON
--       想同时过滤左表（等同 INNER JOIN）→ 放 WHERE
--     对左表的过滤条件：
--       放 WHERE（放 ON 也能工作，但语义混乱，不推荐）

-- 4.4 补救写法（不推荐）：OR IS NULL
--     能保留左表，但可读性差
SELECT u.username, o.id AS 订单ID, o.status
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed' OR o.id IS NULL;
-- 推荐：直接把 o.status='completed' 放 ON

-- ============================================================
-- 5. RIGHT JOIN 右连接
-- ============================================================

-- 5.1 查询所有订单及其用户（含用户被删除的订单）
--     RIGHT JOIN：右表(orders)全部保留，左表(users)无匹配时填 NULL
SELECT
    u.username,
    o.id AS 订单ID,
    o.total_amount
FROM users u
RIGHT JOIN orders o ON u.id = o.user_id
LIMIT 20;

-- 5.2 RIGHT JOIN 总能改写为 LEFT JOIN（调换表顺序）
SELECT
    u.username,
    o.id AS 订单ID,
    o.total_amount
FROM orders o                          -- 把 orders 当左表
LEFT JOIN users u ON u.id = o.user_id
LIMIT 20;
-- 结果与上面 RIGHT JOIN 完全相同

-- 5.3 团队规范建议：统一用 LEFT JOIN，禁用 RIGHT JOIN
--     原因：方向一致，可读性好；混合使用容易混乱

-- ============================================================
-- 6. LEFT JOIN 配合聚合（重要）
-- ============================================================

-- 6.1 统计每个用户的订单数（含 0 订单用户）
SELECT
    u.id,
    u.username,
    COUNT(o.id) AS 订单数,
    IFNULL(SUM(o.total_amount), 0) AS 总消费
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username
ORDER BY 订单数 DESC, 总消费 DESC
LIMIT 30;
-- 要点：
--   COUNT(o.id) 在无匹配时返回 0（不是 1）
--   SUM 在无匹配时返回 NULL，用 IFNULL 转 0
--   COUNT(*) 会返回 1（因为 LEFT JOIN 保留了一行全 NULL 的右表数据）

-- 6.2 对比 COUNT(*) 与 COUNT(o.id) 在 LEFT JOIN 中的差异
SELECT
    u.username,
    COUNT(*)     AS 用COUNT星,   -- 无匹配时返回 1（含一行全 NULL）
    COUNT(o.id)  AS 用COUNT列    -- 无匹配时返回 0（忽略 NULL）
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username
ORDER BY 用COUNT星 DESC
LIMIT 20;
-- 结论：LEFT JOIN 统计右表数量时，必须用 COUNT(右表.主键)，不能用 COUNT(*)

-- 6.3 统计每个商品的评价数（含 0 评价商品）
SELECT
    p.id,
    p.name,
    COUNT(r.id) AS 评价数,
    IFNULL(ROUND(AVG(r.rating),2), 0) AS 平均评分
FROM products p
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id, p.name
ORDER BY 评价数 DESC, 平均评分 DESC
LIMIT 30;

-- ============================================================
-- 7. LEFT JOIN 多表
-- ============================================================

-- 7.1 查询用户 + 订单 + 订单详情（LEFT JOIN 链式）
SELECT
    u.username,
    o.id AS 订单ID,
    o.total_amount,
    oi.product_id,
    oi.quantity
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id
LIMIT 30;

-- 7.2 查询所有用户及其账户余额（LEFT JOIN accounts）
SELECT
    u.id,
    u.username,
    a.balance AS 余额
FROM users u
LEFT JOIN accounts a ON u.id = a.user_id
LIMIT 20;

-- ============================================================
-- 8. 综合示例
-- ============================================================

-- 8.1 查所有用户及其最近一笔订单（LEFT JOIN + 子查询思路，Day08 详讲）
SELECT
    u.id,
    u.username,
    o.id AS 最近订单ID,
    o.total_amount AS 最近订单金额,
    o.created_at AS 最近下单时间
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL
   OR o.id = (
       SELECT MAX(id) FROM orders WHERE user_id = u.id
   )
ORDER BY u.id
LIMIT 30;

-- 8.2 查所有商品及其评价数（含 0 评价商品）
SELECT
    p.id,
    p.name,
    p.price,
    COUNT(r.id) AS 评价数,
    IFNULL(ROUND(AVG(r.rating), 2), 0) AS 平均评分,
    CASE
        WHEN COUNT(r.id) = 0 THEN '无评价'
        WHEN AVG(r.rating) >= 4 THEN '好评'
        WHEN AVG(r.rating) >= 3 THEN '中评'
        ELSE '差评'
    END AS 评价等级
FROM products p
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id, p.name, p.price
ORDER BY 评价数 DESC, 平均评分 DESC
LIMIT 30;
