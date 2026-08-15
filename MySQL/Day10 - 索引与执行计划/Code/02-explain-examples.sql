-- ============================================================
-- 文件名称: 02-explain-examples.sql
-- 文件用途: EXPLAIN 执行计划各字段演示
--           构造 const / ref / range / index / ALL 等不同 type
--           演示 Using index / Using filesort / Using temporary 等 Extra
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day10 - 索引与执行计划/Code/02-explain-examples.sql
-- 前置条件: 已执行 01-create-index.sql 创建好索引
-- ============================================================

USE ecommerce;

-- ============================================================
-- 第一部分：type 字段全景演示
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 type=const：通过主键或唯一索引等值查询，最多返回 1 行
--     性能：⭐⭐⭐⭐⭐
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE id = 1;

EXPLAIN SELECT * FROM users WHERE email = 'alice@example.com';

-- ------------------------------------------------------------
-- 1.2 type=ref：通过普通索引等值查询，可能返回多行
--     性能：⭐⭐⭐⭐
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE name = 'iPhone 15 Pro';

EXPLAIN SELECT * FROM products WHERE category_id = 5;

-- ------------------------------------------------------------
-- 1.3 type=range：索引范围扫描（BETWEEN / > / < / IN）
--     性能：⭐⭐⭐
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE id BETWEEN 1 AND 100;

EXPLAIN SELECT * FROM products WHERE category_id = 5 AND price > 1000;

EXPLAIN SELECT * FROM orders
WHERE user_id = 100
  AND created_at BETWEEN '2024-01-01' AND '2024-06-30';

-- ------------------------------------------------------------
-- 1.4 type=index：扫描整棵索引树（不回表）
--     触发：SELECT COUNT(*) 或只查索引列且无 WHERE
--     性能：⭐⭐（扫描整个索引，比 ALL 略快）
-- ------------------------------------------------------------
EXPLAIN SELECT COUNT(*) FROM products;

EXPLAIN SELECT id, name FROM products;

-- ------------------------------------------------------------
-- 1.5 type=ALL：全表扫描
--     触发：无索引或索引失效
--     性能：⭐（必优化）
--     以下查询条件无可用索引，触发全表扫描
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE stock = 100;

EXPLAIN SELECT * FROM orders WHERE total_amount > 1000;

-- ------------------------------------------------------------
-- 1.6 type=eq_ref：联表时被驱动表用主键/唯一索引等值匹配
--     性能：⭐⭐⭐⭐⭐
--     场景：orders JOIN users ON orders.user_id = users.id
--     users 表作为被驱动表，用主键 id 等值匹配，type=eq_ref
-- ------------------------------------------------------------
EXPLAIN SELECT o.id, u.username
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.user_id = 100;


-- ============================================================
-- 第二部分：id 与 select_type 字段演示
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 SIMPLE：简单查询，无子查询/UNION
--     id=1, select_type=SIMPLE
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE id = 1;

-- ------------------------------------------------------------
-- 2.2 PRIMARY + SUBQUERY：含子查询
--     外层 id=1 select_type=PRIMARY
--     子查询 id=2 select_type=SUBQUERY
--     id 不同时，id 越大越先执行
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM orders
WHERE user_id = (SELECT id FROM users WHERE email = 'alice@example.com');

-- ------------------------------------------------------------
-- 2.3 PRIMARY + DERIVED：FROM 子句的派生表
--     derived 表 id=2 select_type=DERIVED
-- ------------------------------------------------------------
EXPLAIN SELECT t.category_id, t.cnt
FROM (
  SELECT category_id, COUNT(*) AS cnt
  FROM products
  GROUP BY category_id
) t
WHERE t.cnt > 10;

-- ------------------------------------------------------------
-- 2.4 UNION：UNION 查询
--     第一段 id=1 select_type=PRIMARY
--     第二段 id=2 select_type=UNION
--     结果集 id=NULL select_type=UNION RESULT, table=<union1,2>
-- ------------------------------------------------------------
EXPLAIN
SELECT id, name FROM products WHERE category_id = 1
UNION
SELECT id, name FROM products WHERE category_id = 2;


-- ============================================================
-- 第三部分：possible_keys 与 key 字段
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 possible_keys 列出可能用到的索引，key 是实际选中的
--     场景：products 有多个索引可选
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE category_id = 5 AND status = 'on_sale';

-- ------------------------------------------------------------
-- 3.2 优化器可能放弃索引（数据量小或区分度低）
--     possible_keys 有索引，但 key=NULL 表示没用索引
--     可用 FORCE INDEX 强制使用
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products FORCE INDEX(idx_products_name)
WHERE name = 'iPhone 15 Pro';


-- ============================================================
-- 第四部分：key_len 字段（判断联合索引用了几列）
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 联合索引 idx_products_cat_status_price(category_id, status, price)
--     假设定义：category_id INT NOT NULL, status VARCHAR(20) NOT NULL, price DECIMAL(10,2)
--     字节数计算（utf8mb4）：
--       category_id INT NOT NULL            = 4 字节
--       status VARCHAR(20) NOT NULL utf8mb4 = 4*20 + 2 = 82 字节
--       price DECIMAL(10,2) NOT NULL        = 5 字节
-- ------------------------------------------------------------

-- 只用 category_id：key_len 应为 4
EXPLAIN SELECT * FROM products WHERE category_id = 5;

-- 用 category_id + status：key_len 应为 4 + 82 = 86
EXPLAIN SELECT * FROM products WHERE category_id = 5 AND status = 'on_sale';

-- 用全部三列：key_len 应为 4 + 82 + 5 = 91
EXPLAIN SELECT * FROM products
WHERE category_id = 5 AND status = 'on_sale' AND price > 1000;

-- ------------------------------------------------------------
-- 4.2 key_len 计算：注意 NULL 标记额外 +1
--     若列允许 NULL，每列额外 +1 字节
--     可通过 SHOW CREATE TABLE 查看列定义
-- ------------------------------------------------------------
SHOW CREATE TABLE products\G


-- ============================================================
-- 第五部分：rows 与 filtered 字段
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 rows：预估扫描行数（不是结果行数）
--     filtered：扫描后过滤剩余百分比
--     真实结果估算 = rows × filtered / 100
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE category_id = 5;

EXPLAIN SELECT * FROM products WHERE category_id = 5 AND status = 'on_sale';

EXPLAIN SELECT * FROM products
WHERE category_id = 5 AND status = 'on_sale' AND price > 1000;


-- ============================================================
-- 第六部分：Extra 字段演示（重要）
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 Using index：覆盖索引，不回表
--     查询列全部在索引中，性能最佳
--     场景：联合索引 idx_products_cat_status(category_id, status)
--     只查 category_id 和 status（外加隐含的主键 id）
-- ------------------------------------------------------------
EXPLAIN SELECT category_id, status FROM products WHERE category_id = 5;

EXPLAIN SELECT id, category_id, status FROM products WHERE category_id = 5;

-- ------------------------------------------------------------
-- 6.2 Using where：Server 层过滤（通常配合回表）
--     普通现象，不一定有问题
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE category_id = 5 AND price > 1000;

-- ------------------------------------------------------------
-- 6.3 Using index condition：索引下推 ICP
--     场景：联合索引最左前缀用尽后，剩余列在引擎层过滤
--     联合索引 idx_products_cat_status(category_id, status)
--     LIKE 'iPhone%' 走范围，status 在索引层过滤（ICP）
--     注：需要 status 列在联合索引中
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products
WHERE name LIKE 'iPhone%' AND category_id = 5;

-- ------------------------------------------------------------
-- 6.4 Using filesort：额外排序（无法用索引顺序，需优化）
--     场景：ORDER BY 的列不在索引中，或顺序与索引不一致
--     此处 stock 无索引，必须额外排序
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE category_id = 5 ORDER BY stock DESC;

-- ------------------------------------------------------------
-- 6.5 Using filesort 可优化：把排序列纳入联合索引
--     联合索引 idx_products_cat_status_price(category_id, status, price)
--     ORDER BY price 可命中索引顺序，免 filesort
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products
WHERE category_id = 5 AND status = 'on_sale'
ORDER BY price DESC;

-- ------------------------------------------------------------
-- 6.6 Using temporary：使用临时表（GROUP BY / DISTINCT 常见）
--     场景：GROUP BY 的列无索引
--     此处按 stock 分组，stock 无索引
-- ------------------------------------------------------------
EXPLAIN SELECT stock, COUNT(*) FROM products GROUP BY stock;

-- ------------------------------------------------------------
-- 6.7 Using temporary 可优化：分组列加索引
--     按 category_id 分组，category_id 在索引中
--     应不再出现 Using temporary
-- ------------------------------------------------------------
EXPLAIN SELECT category_id, COUNT(*) FROM products GROUP BY category_id;

-- ------------------------------------------------------------
-- 6.8 Using join buffer (Block Nested Loop)：联表无索引
--     场景：JOIN 列无索引，退化为 BNL 算法
--     注：order_items.product_id 此前未建索引
-- ------------------------------------------------------------
EXPLAIN SELECT p.name, oi.quantity
FROM products p
JOIN order_items oi ON p.id = oi.product_id
WHERE p.category_id = 5;

-- 为 order_items(product_id) 建索引后查看变化
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

EXPLAIN SELECT p.name, oi.quantity
FROM products p
JOIN order_items oi ON p.id = oi.product_id
WHERE p.category_id = 5;

-- ------------------------------------------------------------
-- 6.9 Impossible WHERE：WHERE 恒假
--     场景：条件不可能成立
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE 1 = 0;

EXPLAIN SELECT * FROM products WHERE id = 1 AND id = 2;


-- ============================================================
-- 第七部分：FORMAT=TREE（8.0+ 更直观）
-- ============================================================

-- ------------------------------------------------------------
-- 7.1 树形格式展示执行计划，含成本估算
--     适合复杂 SQL 诊断
-- ------------------------------------------------------------
EXPLAIN FORMAT=TREE
SELECT p.name, o.id, oi.quantity
FROM products p
JOIN order_items oi ON p.id = oi.product_id
JOIN orders o ON oi.order_id = o.id
WHERE p.category_id = 5
ORDER BY p.price DESC
LIMIT 20;


-- ============================================================
-- 第八部分：小结
-- ============================================================
-- 通过本脚本可观察到：
-- 1. type 字段从 const 到 ALL 性能递减，ALL 必须优化
-- 2. Extra 出现 Using index 是理想状态（覆盖索引）
-- 3. Extra 出现 Using filesort / Using temporary 需警惕
-- 4. key_len 可判断联合索引命中了几列
-- 5. 联表 JOIN 列必须有索引，否则走 BNL 性能差
--
-- 下一步：执行 03-index-failure.sql 学习索引失效场景
-- ============================================================
