-- ============================================================
-- 文件名称: 03-index-failure.sql
-- 文件用途: 索引失效场景演示
--           通过 EXPLAIN 对比"索引失效"与"可走索引"两种写法
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day10 - 索引与执行计划/Code/03-index-failure.sql
-- 前置条件: 已执行 01-create-index.sql 创建好索引
-- ============================================================

USE ecommerce;

-- ============================================================
-- 场景一：函数包裹列导致索引失效
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 失效写法：YEAR(created_at) = 2024
--     函数包裹列后，索引无法直接匹配，type=ALL 全表扫描
--     注：orders 表的 created_at 无单独索引，演示用
-- ------------------------------------------------------------

-- 先建一个 created_at 索引用于对比
CREATE INDEX idx_orders_created ON orders(created_at);

-- 失效写法：函数包裹列
EXPLAIN SELECT * FROM orders WHERE YEAR(created_at) = 2024;

-- 正确写法：改写为范围查询，可走索引
EXPLAIN SELECT * FROM orders
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';

-- ------------------------------------------------------------
-- 1.2 函数索引（MySQL 8.0+）：让 YEAR(created_at) 也能走索引
--     建函数索引后，原查询可命中
-- ------------------------------------------------------------
CREATE INDEX idx_orders_year ON orders((YEAR(created_at)));

EXPLAIN SELECT * FROM orders WHERE YEAR(created_at) = 2024;

-- 清理演示用的函数索引
DROP INDEX idx_orders_year ON orders;
DROP INDEX idx_orders_created ON orders;


-- ============================================================
-- 场景二：隐式类型转换导致索引失效
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 products.category_id 是 INT 类型
--     传入字符串 '5' 触发隐式转换，等价于 CAST(category_id AS CHAR)='5'
--     函数包裹列 → 索引失效
-- ------------------------------------------------------------

-- 正确写法：类型匹配，走索引 type=ref
EXPLAIN SELECT * FROM products WHERE category_id = 5;

-- 失效写法：传字符串，隐式转换，索引失效 type=ALL
EXPLAIN SELECT * FROM products WHERE category_id = '5';

-- ------------------------------------------------------------
-- 2.2 products.status 是 VARCHAR/ENUM 类型
--     传入数值 1 触发隐式转换
-- ------------------------------------------------------------

-- 正确写法：传字符串
EXPLAIN SELECT * FROM products WHERE status = 'on_sale';

-- 失效写法：传数值（假设 status 是 VARCHAR）
-- 注：若 status 是 ENUM，行为略有差异，但通常仍失效
EXPLAIN SELECT * FROM products WHERE status = 1;


-- ============================================================
-- 场景三：LIKE 前导通配符导致索引失效
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 products.name 有索引 idx_products_name
-- ------------------------------------------------------------

-- 正确写法：右模糊，可走索引（最左前缀）
EXPLAIN SELECT * FROM products WHERE name LIKE 'iPhone%';

-- 失效写法：左模糊，索引失效 type=ALL
EXPLAIN SELECT * FROM products WHERE name LIKE '%iPhone';

-- 失效写法：左右模糊，索引失效 type=ALL
EXPLAIN SELECT * FROM products WHERE name LIKE '%iPhone%';

-- ------------------------------------------------------------
-- 3.2 全文检索替代方案：FULLTEXT 索引
--     适合真正需要"包含某词"的全文检索场景
-- ------------------------------------------------------------

-- 为 products.name 建全文索引（若已存在可跳过）
CREATE FULLTEXT INDEX ft_products_name ON products(name);

-- MATCH AGAINST 走全文索引
EXPLAIN SELECT id, name FROM products
WHERE MATCH(name) AGAINST('iPhone' IN NATURAL LANGUAGE MODE);

-- 查看结果
SELECT id, name FROM products
WHERE MATCH(name) AGAINST('iPhone' IN NATURAL LANGUAGE MODE)
LIMIT 5;

-- 清理演示用的全文索引
DROP INDEX ft_products_name ON products;


-- ============================================================
-- 场景四：OR 条件导致索引短路
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 OR 两侧列中有一方无索引，整体退化为全表扫描
--     products.name 有索引，products.stock 无索引
-- ------------------------------------------------------------

-- 失效写法：OR 短路，整体 type=ALL
EXPLAIN SELECT * FROM products WHERE name = 'iPhone 15 Pro' OR stock = 100;

-- 单独查 name 走索引 type=ref
EXPLAIN SELECT * FROM products WHERE name = 'iPhone 15 Pro';

-- ------------------------------------------------------------
-- 4.2 改写为 UNION ALL：两条查询分别走各自索引
-- ------------------------------------------------------------

EXPLAIN
SELECT * FROM products WHERE name = 'iPhone 15 Pro'
UNION ALL
SELECT * FROM products WHERE stock = 100 AND name <> 'iPhone 15 Pro';

-- ------------------------------------------------------------
-- 4.3 OR 两侧都有索引时：Index Merge 优化（8.0+）
--     products.name 和 products.category_id 都有索引
-- ------------------------------------------------------------

EXPLAIN SELECT * FROM products WHERE name = 'iPhone 15 Pro' OR category_id = 5;


-- ============================================================
-- 场景五：!= / <> / NOT IN 通常不走索引
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 != 通常不走索引（命中范围太大，优化器放弃）
-- ------------------------------------------------------------

-- 等值查询走索引 type=ref
EXPLAIN SELECT * FROM products WHERE category_id = 5;

-- != 不走索引 type=ALL
EXPLAIN SELECT * FROM products WHERE category_id != 5;

-- <> 同 !=
EXPLAIN SELECT * FROM products WHERE category_id <> 5;

-- ------------------------------------------------------------
-- 5.2 NOT IN 通常不走索引
-- ------------------------------------------------------------

EXPLAIN SELECT * FROM products WHERE category_id NOT IN (1, 2, 3);

-- ------------------------------------------------------------
-- 5.3 改写：用 IN 列举正向值
-- ------------------------------------------------------------

EXPLAIN SELECT * FROM products WHERE category_id IN (4, 5, 6, 7);


-- ============================================================
-- 场景六：IS NOT NULL 通常不走索引
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 users.deleted_at 软删除字段，多数为 NULL
--     IS NULL 通常可走索引（若 NULL 占少数）
--     IS NOT NULL 通常不走索引
-- ------------------------------------------------------------

-- 为 deleted_at 建索引用于演示
CREATE INDEX idx_users_deleted ON users(deleted_at);

-- IS NULL 通常走索引（NULL 占少数时）
EXPLAIN SELECT * FROM users WHERE deleted_at IS NULL;

-- IS NOT NULL 通常不走索引
EXPLAIN SELECT * FROM users WHERE deleted_at IS NOT NULL;

-- 清理
DROP INDEX idx_users_deleted ON users;


-- ============================================================
-- 场景七：最左前缀缺失
-- ============================================================

-- ------------------------------------------------------------
-- 7.1 联合索引 idx_products_cat_status_price(category_id, status, price)
--     缺最左列 category_id 无法命中索引
-- ------------------------------------------------------------

-- 命中：用 category_id
EXPLAIN SELECT * FROM products WHERE category_id = 5;

-- 命中：用 category_id + status
EXPLAIN SELECT * FROM products WHERE category_id = 5 AND status = 'on_sale';

-- 不命中：缺最左列 category_id
EXPLAIN SELECT * FROM products WHERE status = 'on_sale';

-- 不命中：缺最左列 category_id
EXPLAIN SELECT * FROM products WHERE status = 'on_sale' AND price > 1000;

-- 部分命中：跳过 status，只用 category_id
-- key_len 只包含 category_id 的 4 字节
EXPLAIN SELECT * FROM products WHERE category_id = 5 AND price > 1000;

-- ------------------------------------------------------------
-- 7.2 范围查询之后的列无法走索引
--     category_id 等值 + price 范围 + status 等值
--     price 范围查询后，status 无法走索引（但 ICP 可下推过滤）
-- ------------------------------------------------------------

-- status 在 price 范围之后，无法用于索引查找
EXPLAIN SELECT * FROM products
WHERE category_id = 5 AND price > 1000 AND status = 'on_sale';

-- 调整顺序：等值在前，范围在后
EXPLAIN SELECT * FROM products
WHERE category_id = 5 AND status = 'on_sale' AND price > 1000;


-- ============================================================
-- 场景八：字符集不一致导致联表索引失效
-- ============================================================

-- ------------------------------------------------------------
-- 8.1 若两表字符集不同（如 products utf8 与 order_items utf8mb4）
--     JOIN 时索引失效，走 Block Nested Loop
--     解决：统一字符集为 utf8mb4
--     注：本演示假设 ecommerce 表已统一 utf8mb4，此处仅说明
-- ------------------------------------------------------------

-- 正常 JOIN（字符集一致时走索引）
EXPLAIN SELECT p.name, oi.quantity
FROM products p
JOIN order_items oi ON p.id = oi.product_id
WHERE p.category_id = 5;

-- 查看表字符集
SELECT TABLE_NAME, TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'ecommerce';


-- ============================================================
-- 场景九：优化器主动放弃索引
-- ============================================================

-- ------------------------------------------------------------
-- 9.1 数据量小或索引区分度低时，优化器可能主动放弃索引
--     可用 FORCE INDEX 强制使用
-- ------------------------------------------------------------

-- 普通查询（优化器自主选择）
EXPLAIN SELECT * FROM products WHERE category_id = 5;

-- 强制使用 idx_products_cat_status
EXPLAIN SELECT * FROM products FORCE INDEX(idx_products_cat_status)
WHERE category_id = 5;

-- 强制忽略 idx_products_cat_status
EXPLAIN SELECT * FROM products IGNORE INDEX(idx_products_cat_status)
WHERE category_id = 5;


-- ============================================================
-- 场景十：SELECT * 强制回表，无法命中覆盖索引
-- ============================================================

-- ------------------------------------------------------------
-- 10.1 对比 SELECT * 与 SELECT 索引列
--      联合索引 idx_products_cat_status(category_id, status)
-- ------------------------------------------------------------

-- SELECT * 必然回表（无法覆盖所有列）
-- Extra 通常只有 Using where
EXPLAIN SELECT * FROM products WHERE category_id = 5;

-- 只查索引列（外加主键），命中覆盖索引
-- Extra 应有 Using index
EXPLAIN SELECT category_id, status FROM products WHERE category_id = 5;

EXPLAIN SELECT id, category_id, status FROM products WHERE category_id = 5;


-- ============================================================
-- 综合对比：同一查询的多种写法
-- ============================================================

-- ------------------------------------------------------------
-- 业务场景：查"分类 5 下 2024 年创建的在售商品，按价格降序"
-- ------------------------------------------------------------

-- 写法 A：索引失效（函数包裹列 + 无关列排序）
EXPLAIN SELECT * FROM products
WHERE category_id = 5
  AND YEAR(created_at) = 2024
  AND status = 'on_sale'
ORDER BY stock DESC;

-- 写法 B：部分走索引（YEAR 改范围，但 stock 排序仍 filesort）
EXPLAIN SELECT * FROM products
WHERE category_id = 5
  AND created_at >= '2024-01-01' AND created_at < '2025-01-01'
  AND status = 'on_sale'
ORDER BY stock DESC;

-- 写法 C：最优（范围改写 + 排序列纳入索引）
EXPLAIN SELECT * FROM products
WHERE category_id = 5
  AND status = 'on_sale'
  AND created_at >= '2024-01-01' AND created_at < '2025-01-01'
ORDER BY price DESC;


-- ============================================================
-- 小结
-- ============================================================
-- 通过本脚本可观察到索引失效的常见原因：
-- 1. 函数包裹列（YEAR/LOWER/LEFT）→ 改写或用函数索引
-- 2. 隐式类型转换（INT 传字符串）→ 类型严格匹配
-- 3. LIKE 左模糊（'%xxx'）→ 改右模糊或 FULLTEXT
-- 4. OR 短路（一侧无索引）→ UNION 改写或补索引
-- 5. != / <> / NOT IN → 改 IN 列举正向值
-- 6. IS NOT NULL → 业务规避
-- 7. 最左前缀缺失 → 调整索引或查询
-- 8. 字符集不一致 → 统一 utf8mb4
-- 9. 优化器主动放弃 → FORCE INDEX 强制
-- 10. SELECT * 强制回表 → 只查需要的列
--
-- 诊断索引是否失效的核心工具：EXPLAIN
-- 关注 type（是否 ALL）、key（是否 NULL）、Extra（是否 filesort/temporary）
-- ============================================================
