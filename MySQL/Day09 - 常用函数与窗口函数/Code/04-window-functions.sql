-- ============================================================
-- 文件名称: 04-window-functions.sql
-- 文件用途: 窗口函数演示：排名 / 偏移 / 聚合 / 累计 / 按分类排名
--           窗口函数是 MySQL 8.0 最重磅特性之一
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day09 - 常用函数与窗口函数/Code/04-window-functions.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 一、窗口函数 vs GROUP BY 对比（先理解概念）
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 GROUP BY：每个分类的平均价格（结果行数 = 分类数）
-- ------------------------------------------------------------
SELECT category_id, AVG(price) AS avg_price
FROM products
GROUP BY category_id
ORDER BY category_id;

-- ------------------------------------------------------------
-- 1.2 窗口函数：每件商品 + 该分类的平均价格（结果行数 = 商品数）
--     保留明细行，额外附加聚合结果
-- ------------------------------------------------------------
SELECT name, category_id, price,
       AVG(price) OVER (PARTITION BY category_id) AS cat_avg
FROM products
ORDER BY category_id, price DESC
LIMIT 10;

-- ============================================================
-- 二、排序类窗口函数：ROW_NUMBER / RANK / DENSE_RANK
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 全店商品按价格降序排名（不加 PARTITION 即全表一个窗口）
-- ------------------------------------------------------------
SELECT name, price,
       ROW_NUMBER() OVER (ORDER BY price DESC) AS rn,
       RANK()       OVER (ORDER BY price DESC) AS rk,
       DENSE_RANK() OVER (ORDER BY price DESC) AS drk
FROM products
ORDER BY price DESC
LIMIT 15;

-- ------------------------------------------------------------
-- 2.2 每个分类内按价格降序排名（PARTITION BY category_id）
--     这是"分组排名"最经典用法
-- ------------------------------------------------------------
SELECT name, category_id, price,
       ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY price DESC) AS rn,
       RANK()       OVER (PARTITION BY category_id ORDER BY price DESC) AS rk,
       DENSE_RANK() OVER (PARTITION BY category_id ORDER BY price DESC) AS drk
FROM products
ORDER BY category_id, price DESC
LIMIT 20;

-- ------------------------------------------------------------
-- 2.3 三种排名的区别演示（构造并列数据）
--     ROW_NUMBER：1,2,3,4（永不重复）
--     RANK：1,2,2,4（并列后跳号）
--     DENSE_RANK：1,2,2,3（并列不跳号）
-- ------------------------------------------------------------
WITH demo AS (
    SELECT 'A' AS name, 100 AS price UNION ALL
    SELECT 'B', 90  UNION ALL
    SELECT 'C', 90  UNION ALL
    SELECT 'D', 80
)
SELECT name, price,
       ROW_NUMBER() OVER (ORDER BY price DESC) AS rn,
       RANK()       OVER (ORDER BY price DESC) AS rk,
       DENSE_RANK() OVER (ORDER BY price DESC) AS drk
FROM demo;

-- ============================================================
-- 三、取每组前 N：窗口函数的经典场景
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 每个分类价格最高的前 2 件商品
--     思路：先用 ROW_NUMBER 排名，再用外层 WHERE 过滤
-- ------------------------------------------------------------
WITH ranked AS (
    SELECT name, category_id, price,
           ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY price DESC) AS rn
    FROM products
)
SELECT category_id, name, price, rn
FROM ranked
WHERE rn <= 2
ORDER BY category_id, rn;

-- ------------------------------------------------------------
-- 3.2 每个用户最近 3 笔订单
-- ------------------------------------------------------------
WITH ranked_orders AS (
    SELECT id, user_id, total_amount, created_at, status,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
    FROM orders
)
SELECT user_id, id AS order_id, total_amount, status, created_at, rn
FROM ranked_orders
WHERE rn <= 3
ORDER BY user_id, rn
LIMIT 20;

-- ============================================================
-- 四、NTILE：分桶
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 NTILE(4)：把商品按价格分成 4 档（四分位）
--     1 = 最低 25%，4 = 最高 25%
-- ------------------------------------------------------------
SELECT name, price,
       NTILE(4) OVER (ORDER BY price ASC) AS price_quartile
FROM products
ORDER BY price_quartile, price DESC
LIMIT 20;

-- ============================================================
-- 五、偏移类窗口函数：LAG / LEAD
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 LAG：取当前行之前的值（环比、同用户上一笔订单）
-- ------------------------------------------------------------
SELECT user_id, id AS order_id, created_at, total_amount,
       LAG(total_amount, 1, 0) OVER (
           PARTITION BY user_id ORDER BY created_at
       ) AS prev_amount,
       total_amount - LAG(total_amount, 1, 0) OVER (
           PARTITION BY user_id ORDER BY created_at
       ) AS diff
FROM orders
ORDER BY user_id, created_at
LIMIT 15;

-- ------------------------------------------------------------
-- 5.2 LEAD：取当前行之后的值（下一笔订单）
-- ------------------------------------------------------------
SELECT user_id, id AS order_id, created_at, total_amount,
       LEAD(total_amount, 1) OVER (
           PARTITION BY user_id ORDER BY created_at
       ) AS next_amount
FROM orders
ORDER BY user_id, created_at
LIMIT 15;

-- ------------------------------------------------------------
-- 5.3 LAG 第二个参数：取前 2 行
-- ------------------------------------------------------------
SELECT user_id, created_at, total_amount,
       LAG(total_amount, 2) OVER (
           PARTITION BY user_id ORDER BY created_at
       ) AS amount_2_orders_ago
FROM orders
ORDER BY user_id, created_at
LIMIT 15;

-- ============================================================
-- 六、聚合类窗口函数
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 SUM OVER：每个分类的商品价格总和 + 单价占比
-- ------------------------------------------------------------
SELECT name, category_id, price,
       SUM(price) OVER (PARTITION BY category_id) AS cat_total,
       ROUND(price / SUM(price) OVER (PARTITION BY category_id) * 100, 2) AS pct_in_cat
FROM products
ORDER BY category_id, price DESC
LIMIT 15;

-- ------------------------------------------------------------
-- 6.2 COUNT OVER：每件商品所在分类的商品总数
-- ------------------------------------------------------------
SELECT name, category_id,
       COUNT(*) OVER (PARTITION BY category_id) AS cat_product_cnt
FROM products
ORDER BY category_id
LIMIT 15;

-- ------------------------------------------------------------
-- 6.3 AVG OVER：每件商品与所在分类均价的对比
-- ------------------------------------------------------------
SELECT name, category_id, price,
       ROUND(AVG(price) OVER (PARTITION BY category_id), 2) AS cat_avg,
       ROUND(price - AVG(price) OVER (PARTITION BY category_id), 2) AS diff_from_avg
FROM products
ORDER BY category_id, price DESC
LIMIT 15;

-- ------------------------------------------------------------
-- 6.4 MAX/MIN OVER：每件商品与所在分类最高/最低价对比
-- ------------------------------------------------------------
SELECT name, category_id, price,
       MAX(price) OVER (PARTITION BY category_id) AS cat_max,
       MIN(price) OVER (PARTITION BY category_id) AS cat_min,
       MAX(price) OVER (PARTITION BY category_id) - price AS gap_from_max
FROM products
ORDER BY category_id, price DESC
LIMIT 15;

-- ============================================================
-- 七、窗口框架：累计求和（重点）
-- ============================================================

-- ------------------------------------------------------------
-- 7.1 累计求和：按订单日期累计订单金额
--     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
--     含义：从第一行累加到当前行
-- ------------------------------------------------------------
SELECT id, DATE(created_at) AS order_date, total_amount,
       SUM(total_amount) OVER (
           ORDER BY DATE(created_at)
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS cumulative_amount
FROM orders
ORDER BY order_date, id
LIMIT 20;

-- ------------------------------------------------------------
-- 7.2 按用户累计消费
--     PARTITION BY user_id 分组，每组内按时间累计
-- ------------------------------------------------------------
SELECT user_id, created_at, total_amount,
       SUM(total_amount) OVER (
           PARTITION BY user_id
           ORDER BY created_at
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS cumulative_spent
FROM orders
ORDER BY user_id, created_at
LIMIT 20;

-- ------------------------------------------------------------
-- 7.3 移动平均：当前及前 2 行的平均值（3 日移动平均）
--     ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
-- ------------------------------------------------------------
SELECT id, DATE(created_at) AS order_date, total_amount,
       ROUND(AVG(total_amount) OVER (
           ORDER BY DATE(created_at)
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ), 2) AS moving_avg_3
FROM orders
ORDER BY order_date, id
LIMIT 20;

-- ============================================================
-- 八、FIRST_VALUE / LAST_VALUE / NTH_VALUE
-- ============================================================

-- ------------------------------------------------------------
-- 8.1 FIRST_VALUE：每个分类内价格最低的商品名
-- ------------------------------------------------------------
SELECT name, category_id, price,
       FIRST_VALUE(name) OVER (
           PARTITION BY category_id ORDER BY price ASC
       ) AS cheapest_in_cat
FROM products
ORDER BY category_id, price
LIMIT 15;

-- ------------------------------------------------------------
-- 8.2 LAST_VALUE：每个分类内价格最高的商品名
--     注意：LAST_VALUE 默认框架到"当前行"，需手动改为整组
--     ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
-- ------------------------------------------------------------
SELECT name, category_id, price,
       LAST_VALUE(name) OVER (
           PARTITION BY category_id ORDER BY price ASC
           ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
       ) AS most_expensive_in_cat
FROM products
ORDER BY category_id, price
LIMIT 15;

-- ------------------------------------------------------------
-- 8.3 NTH_VALUE：取窗口内第 2 行的值
-- ------------------------------------------------------------
SELECT name, category_id, price,
       NTH_VALUE(name, 2) OVER (
           PARTITION BY category_id ORDER BY price DESC
           ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
       ) AS second_expensive
FROM products
ORDER BY category_id, price DESC
LIMIT 15;

-- ============================================================
-- 九、综合实战：商品销量排行 + 分类内排名
-- ============================================================

-- ------------------------------------------------------------
-- 9.1 每个商品的销量与销售额，并在分类内按销量排名
--     先用 CTE 聚合 order_items 得到每个商品销量
--     再用窗口函数在分类内排名
-- ------------------------------------------------------------
WITH product_sales AS (
    SELECT p.id, p.name, p.category_id,
           COALESCE(SUM(oi.quantity), 0) AS sold_qty,
           COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
    FROM products p
    LEFT JOIN order_items oi ON oi.product_id = p.id
    GROUP BY p.id, p.name, p.category_id
)
SELECT id, name, category_id, sold_qty, revenue,
       ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY sold_qty DESC) AS sales_rank_in_cat,
       RANK()       OVER (ORDER BY sold_qty DESC) AS sales_rank_global
FROM product_sales
ORDER BY category_id, sales_rank_in_cat
LIMIT 20;

-- ------------------------------------------------------------
-- 9.2 每个分类的销量冠军商品（只用窗口函数 + 过滤）
-- ------------------------------------------------------------
WITH product_sales AS (
    SELECT p.id, p.name, p.category_id,
           COALESCE(SUM(oi.quantity), 0) AS sold_qty
    FROM products p
    LEFT JOIN order_items oi ON oi.product_id = p.id
    GROUP BY p.id, p.name, p.category_id
),
ranked AS (
    SELECT id, name, category_id, sold_qty,
           ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY sold_qty DESC) AS rn
    FROM product_sales
)
SELECT category_id, name, sold_qty
FROM ranked
WHERE rn = 1
ORDER BY sold_qty DESC;

-- ============================================================
-- 窗口函数演示完毕。
-- 要点：
--   1. 窗口函数保留明细行，GROUP BY 合并行
--   2. ROW_NUMBER 不重复、RANK 跳号、DENSE_RANK 不跳号
--   3. LAG/LEAD 取前后行，常用于环比
--   4. SUM/AVG OVER 做分组聚合占比、移动平均
--   5. 累计求和用 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
--   6. 取每组前 N：ROW_NUMBER + 外层 WHERE 过滤
--   7. LAST_VALUE 注意默认框架，需改为整组范围
-- ============================================================
