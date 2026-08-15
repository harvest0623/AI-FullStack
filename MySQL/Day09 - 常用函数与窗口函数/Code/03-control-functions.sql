-- ============================================================
-- 文件名称: 03-control-functions.sql
-- 文件用途: 流程控制函数演示：IF / CASE WHEN / IFNULL / NULLIF / COALESCE / CAST
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day09 - 常用函数与窗口函数/Code/03-control-functions.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 一、IF 函数
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 IF(expr, a, b)：expr 为真返回 a，否则 b
-- ------------------------------------------------------------
SELECT IF(1 = 1, '真', '假') AS r1,
       IF(1 > 2, '真', '假') AS r2,
       IF(NULL, '真', '假')  AS r3;   -- NULL 视为假

-- 给商品价格打标记
SELECT name, price,
       IF(price >= 100, '高价', '低价') AS price_tag
FROM products
LIMIT 8;

-- 给订单状态打标记（是否已付款）
SELECT id, status,
       IF(status IN ('paid','shipped','completed'), '已付款', '未付款') AS pay_status
FROM orders
LIMIT 8;

-- ------------------------------------------------------------
-- 1.2 IF 嵌套：多条件判断（不如 CASE 清晰，不推荐多层嵌套）
-- ------------------------------------------------------------
SELECT name, price,
       IF(price < 50, '低价', IF(price < 200, '中价', '高价')) AS level
FROM products
LIMIT 8;

-- ============================================================
-- 二、CASE WHEN（重点）
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 搜索 CASE（推荐）：按条件判断，类似 if-elif-else
-- ------------------------------------------------------------
SELECT name, price,
       CASE
           WHEN price < 50           THEN '低价'
           WHEN price < 200          THEN '中价'
           WHEN price < 500          THEN '高价'
           ELSE '奢华'
       END AS price_level
FROM products
ORDER BY price
LIMIT 10;

-- ------------------------------------------------------------
-- 2.2 简单 CASE：按等值匹配
-- ------------------------------------------------------------
SELECT name, status,
       CASE status
           WHEN 'draft'    THEN '草稿'
           WHEN 'on_sale'  THEN '在售'
           WHEN 'off_sale' THEN '已下架'
           ELSE '未知状态'
       END AS status_cn
FROM products
LIMIT 10;

-- 订单状态翻译
SELECT id, status,
       CASE status
           WHEN 'pending'   THEN '待付款'
           WHEN 'paid'      THEN '已付款'
           WHEN 'shipped'   THEN '已发货'
           WHEN 'completed' THEN '已完成'
           WHEN 'cancelled' THEN '已取消'
           WHEN 'refunded'  THEN '已退款'
           ELSE '未知'
       END AS status_cn
FROM orders
LIMIT 10;

-- ------------------------------------------------------------
-- 2.3 CASE 聚合：统计各状态商品数
--     CASE WHEN 配合 SUM/COUNT 实现行转列统计
-- ------------------------------------------------------------
SELECT
    SUM(CASE WHEN status = 'draft'    THEN 1 ELSE 0 END) AS draft_cnt,
    SUM(CASE WHEN status = 'on_sale'  THEN 1 ELSE 0 END) AS on_sale_cnt,
    SUM(CASE WHEN status = 'off_sale' THEN 1 ELSE 0 END) AS off_sale_cnt,
    COUNT(*) AS total
FROM products;

-- ------------------------------------------------------------
-- 2.4 CASE 在 ORDER BY 中实现自定义排序
--     让"在售"排最前、"草稿"其次、"下架"最后
-- ------------------------------------------------------------
SELECT id, name, status
FROM products
ORDER BY CASE status
           WHEN 'on_sale'  THEN 1
           WHEN 'draft'    THEN 2
           WHEN 'off_sale' THEN 3
           ELSE 4
         END,
         id
LIMIT 10;

-- ============================================================
-- 三、NULL 处理函数
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 IFNULL(a, b)：a 为 NULL 返回 b，否则 a
-- ------------------------------------------------------------
SELECT IFNULL(NULL, '默认值')  AS r1,   -- 默认值
       IFNULL('有值', '默认值') AS r2;   -- 有值

-- 账户余额为 NULL 时显示 0
SELECT user_id, balance, IFNULL(balance, 0) AS safe_balance
FROM accounts
LIMIT 8;

-- ------------------------------------------------------------
-- 3.2 NULLIF(a, b)：a = b 返回 NULL，否则返回 a
--     常用于避免除以 0
-- ------------------------------------------------------------
SELECT NULLIF(5, 5) AS r1,    -- NULL
       NULLIF(5, 3) AS r2;    -- 5

-- 避免除以 0：若分母为 0 转成 NULL，结果为 NULL 而非报错
SELECT 100 / NULLIF(0, 0) AS safe_div;   -- NULL

-- ------------------------------------------------------------
-- 3.3 COALESCE(a, b, c, ...)：返回第一个非 NULL 值
--     比 IFNULL 更强大，支持多个参数
-- ------------------------------------------------------------
SELECT COALESCE(NULL, NULL, '第三个', '第四个') AS r1,  -- 第三个
       COALESCE(NULL, NULL, NULL) AS r2;               -- NULL

-- 用户展示名：优先昵称、其次用户名、最后"匿名"
-- （users 表若无 nickname 字段，则演示用 email 兜底）
SELECT id, username, email,
       COALESCE(email, username, '匿名') AS display_name
FROM users
LIMIT 8;

-- ============================================================
-- 四、类型转换 CAST / CONVERT
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 CAST(expr AS type)：字符串转数值/日期等
-- ------------------------------------------------------------
SELECT CAST('123'   AS SIGNED)     AS to_int,      -- 123
       CAST('45.67' AS DECIMAL(10,1)) AS to_dec,   -- 45.7（四舍五入）
       CAST('2026-07-27' AS DATE)    AS to_date,
       CAST('2026-07-27 14:30:00' AS DATETIME) AS to_dt;

-- 字符串数字参与运算
SELECT CAST('100' AS SIGNED) + 50 AS result;

-- ------------------------------------------------------------
-- 4.2 CONVERT(expr, type)：功能与 CAST 相同，语法不同
-- ------------------------------------------------------------
SELECT CONVERT('456', SIGNED)   AS to_int2,
       CONVERT('78.99', DECIMAL(10,2)) AS to_dec2,
       CONVERT('2026-07-27', DATE) AS to_date2;

-- ------------------------------------------------------------
-- 4.3 常见目标类型
--     SIGNED / UNSIGNED（整数）
--     CHAR（字符串）
--     DATE / DATETIME / TIME（日期时间）
--     DECIMAL(m, n)（定点数）
--     BINARY（二进制）
-- ------------------------------------------------------------
SELECT CAST(3.14159 AS SIGNED)        AS to_int,     -- 3
       CAST(3.14159 AS UNSIGNED)      AS to_uint,    -- 3
       CAST(123 AS CHAR(5))           AS to_char,    -- '123'
       CAST(123.456 AS DECIMAL(10,2)) AS to_decimal; -- 123.46

-- ------------------------------------------------------------
-- 4.4 价格统一为 2 位小数展示
-- ------------------------------------------------------------
SELECT name, price,
       CAST(price AS DECIMAL(10,2)) AS price_fmt
FROM products
LIMIT 8;

-- ============================================================
-- 五、综合应用
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 用户活跃度分级（CASE + COALESCE + 子查询统计）
-- ------------------------------------------------------------
SELECT u.id, u.username,
       COALESCE(o.order_cnt, 0) AS order_cnt,
       CASE
           WHEN COALESCE(o.order_cnt, 0) >= 5  THEN '超级用户'
           WHEN COALESCE(o.order_cnt, 0) >= 2  THEN '活跃用户'
           WHEN COALESCE(o.order_cnt, 0) >= 1  THEN '普通用户'
           ELSE '沉默用户'
       END AS user_level
FROM users u
LEFT JOIN (
    SELECT user_id, COUNT(*) AS order_cnt
    FROM orders
    GROUP BY user_id
) o ON o.user_id = u.id
ORDER BY order_cnt DESC
LIMIT 10;

-- ------------------------------------------------------------
-- 5.2 订单金额格式化展示（CAST + CONCAT）
--     拼接人民币符号与两位小数
-- ------------------------------------------------------------
SELECT id,
       CONCAT('￥', CAST(total_amount AS DECIMAL(10,2))) AS amount_cn,
       status
FROM orders
LIMIT 8;

-- ------------------------------------------------------------
-- 5.3 库存预警报表（CASE + IF + 字符串函数）
-- ------------------------------------------------------------
SELECT id, name, stock, status,
       CASE
           WHEN stock = 0          THEN '缺货'
           WHEN stock < 10         THEN '低库存'
           WHEN stock < 50         THEN '库存偏少'
           ELSE '库存充足'
       END AS stock_alert,
       IF(status = 'on_sale', '正常销售', '非在售') AS sale_state
FROM products
ORDER BY stock
LIMIT 10;

-- ------------------------------------------------------------
-- 5.4 评价星级文字化（简单 CASE）
-- ------------------------------------------------------------
SELECT id, product_id, rating,
       CASE rating
           WHEN 5 THEN '好评'
           WHEN 4 THEN '较好'
           WHEN 3 THEN '一般'
           WHEN 2 THEN '较差'
           WHEN 1 THEN '差评'
           ELSE '未评级'
       END AS rating_text
FROM reviews
LIMIT 10;

-- ============================================================
-- 流程控制函数演示完毕。
-- 要点：IF 适合二选一；CASE WHEN 适合多分支与行转列统计；
--       IFNULL 处理单个 NULL，COALESCE 处理多个备选；
--       CAST/CONVERT 做类型转换，DECIMAL 控制精度。
-- ============================================================
