-- ============================================================
-- 文件用途: Day07 - 内连接（INNER JOIN）演示
--           演示：用户-订单连接、商品-分类连接、ON 条件、vs WHERE 老式写法
--           基于 ecommerce 库
-- 执行方式: mysql> source 本文件路径
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. INNER JOIN 基础：用户-订单连接
-- ============================================================

-- 1.1 查询有订单的用户的订单信息（标准 INNER JOIN ... ON 写法）
SELECT
    u.id AS 用户ID,
    u.username AS 用户名,
    o.id AS 订单ID,
    o.total_amount AS 订单金额,
    o.status AS 订单状态
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- 1.2 限制返回行数（避免输出过长）
SELECT
    u.username,
    o.id AS 订单ID,
    o.total_amount,
    o.status
FROM users u
INNER JOIN orders o ON u.id = o.user_id
LIMIT 20;

-- 1.3 加 WHERE 过滤：只看已完成订单
SELECT
    u.username,
    o.id AS 订单ID,
    o.total_amount,
    o.status
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';

-- 1.4 加 ORDER BY 和 LIMIT
SELECT
    u.username,
    o.id AS 订单ID,
    o.total_amount,
    o.created_at
FROM users u
INNER JOIN orders o ON u.id = o.user_id
ORDER BY o.total_amount DESC
LIMIT 10;

-- ============================================================
-- 2. INNER JOIN vs 老式 WHERE 写法（两种等价）
-- ============================================================

-- 2.1 推荐：标准 INNER JOIN ... ON 写法
--     优点：连接条件与过滤条件分离，语义清晰
SELECT u.username, o.total_amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';

-- 2.2 老式：逗号分隔 + WHERE 条件
--     缺点：容易漏 WHERE 退化成笛卡尔积；连接条件与过滤条件混在一起
SELECT u.username, o.total_amount
FROM users u, orders o
WHERE u.id = o.user_id
  AND o.status = 'completed';

-- 2.3 两种写法结果完全相同，但推荐用 INNER JOIN

-- ============================================================
-- 3. 商品-分类连接
-- ============================================================

-- 3.1 查询商品及其分类名
SELECT
    p.id AS 商品ID,
    p.name AS 商品名,
    p.price AS 价格,
    c.name AS 分类名
FROM products p
INNER JOIN categories c ON p.category_id = c.id
LIMIT 20;

-- 3.2 查询指定分类下的商品
SELECT
    p.name,
    p.price,
    c.name AS 分类名
FROM products p
INNER JOIN categories c ON p.category_id = c.id
WHERE c.name = '电子产品';

-- 3.3 查询每个分类的商品数量
SELECT
    c.name AS 分类名,
    COUNT(*) AS 商品数
FROM products p
INNER JOIN categories c ON p.category_id = c.id
GROUP BY c.id, c.name
ORDER BY 商品数 DESC;

-- ============================================================
-- 4. INNER JOIN 的特性：只保留匹配行
-- ============================================================

-- 4.1 INNER JOIN：没下过单的用户不会出现
SELECT COUNT(DISTINCT u.id) AS 有订单的用户数
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- 4.2 对比：全部用户数
SELECT COUNT(*) AS 全部用户数 FROM users;

-- 4.3 结论：INNER JOIN 只保留两表都匹配的行
--     没下过单的用户在 INNER JOIN 结果中不出现
--     （要查全部用户需用 LEFT JOIN，见 02-left-right-join.sql）

-- ============================================================
-- 5. USING 写法（两表列名相同时）
-- ============================================================

-- 5.1 当两表关联列同名时可用 USING
--     假设 order_items 表的 order_id 与 orders 表的 id 同名（实际表中是 id）
--     演示：order_items.product_id 与 products.id 不同名，这里用别名模拟

-- 标准写法
SELECT
    oi.order_id,
    oi.product_id,
    p.name AS 商品名
FROM order_items oi
INNER JOIN products p ON oi.product_id = p.id
LIMIT 10;

-- 5.2 USING 的特点：结果中关联列只出现一次
--     若用 ON，关联列会出现两次（左表一次、右表一次）

-- ============================================================
-- 6. INNER JOIN 配合聚合
-- ============================================================

-- 6.1 每个用户的订单数与总消费
SELECT
    u.id,
    u.username,
    COUNT(o.id) AS 订单数,
    SUM(o.total_amount) AS 总消费
FROM users u
INNER JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username
ORDER BY 总消费 DESC
LIMIT 20;

-- 6.2 每个分类的销售额（JOIN order_items）
SELECT
    c.name AS 分类名,
    COUNT(*) AS 销售记录数,
    SUM(oi.quantity * oi.unit_price) AS 销售额
FROM order_items oi
INNER JOIN products p ON oi.product_id = p.id
INNER JOIN categories c ON p.category_id = c.id
GROUP BY c.id, c.name
ORDER BY 销售额 DESC;

-- ============================================================
-- 7. INNER JOIN 加多条件
-- ============================================================

-- 7.1 ON 条件可以包含多个条件（用 AND 连接）
SELECT
    u.username,
    o.id AS 订单ID,
    o.total_amount,
    o.status
FROM users u
INNER JOIN orders o ON u.id = o.user_id
    AND o.status IN ('paid', 'completed')
    AND o.total_amount > 100
ORDER BY o.total_amount DESC
LIMIT 20;

-- 7.2 注意：INNER JOIN 中放 ON 还是 WHERE 对结果无影响
--     （因为 INNER JOIN 本身就丢弃不匹配行）
--     但放 ON 语义更清晰（表示连接条件）
SELECT
    u.username,
    o.id AS 订单ID,
    o.total_amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.status IN ('paid', 'completed')
  AND o.total_amount > 100;

-- ============================================================
-- 8. 笛卡尔积 CROSS JOIN（了解，慎用）
-- ============================================================

-- 8.1 CROSS JOIN：左表每行与右表每行都配对（N×M 行）
--     注意：行数会爆炸，限制返回
SELECT
    u.username,
    c.name AS 分类名
FROM users u
CROSS JOIN categories c
LIMIT 10;

-- 8.2 隐式笛卡尔积：逗号分隔不写 WHERE（危险！）
-- SELECT * FROM users, orders;  -- 不带条件 = 笛卡尔积，行数 N×M
--     生产环境严禁这种写法，会拖垮数据库

-- 8.3 CROSS JOIN 的合法用途：生成组合表
--     例：所有用户 × 所有角色的权限矩阵
SELECT u.username, r.role_name
FROM users u
CROSS JOIN (
    SELECT DISTINCT role AS role_name FROM users
) r
LIMIT 20;

-- ============================================================
-- 9. 综合示例：订单详情查询
-- ============================================================

-- 9.1 查询订单的完整信息（订单 + 用户 + 金额）
SELECT
    o.id AS 订单ID,
    u.username AS 用户名,
    u.email AS 邮箱,
    o.total_amount AS 金额,
    o.status AS 状态,
    o.created_at AS 下单时间
FROM orders o
INNER JOIN users u ON o.user_id = u.id
ORDER BY o.created_at DESC
LIMIT 20;

-- 9.2 查询在售商品及其分类（含价格区间过滤）
SELECT
    p.id,
    p.name AS 商品名,
    p.price AS 价格,
    p.stock AS 库存,
    c.name AS 分类名
FROM products p
INNER JOIN categories c ON p.category_id = c.id
WHERE p.status = 'on_sale'
  AND p.price BETWEEN 100 AND 1000
ORDER BY p.price DESC
LIMIT 20;
