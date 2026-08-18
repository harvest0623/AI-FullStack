-- ============================================================
-- 文件名称: 01-view-demo.sql
-- 文件用途: 视图 VIEW 演示脚本
--           1. 商品销售统计视图（聚合 + JOIN，不可更新）
--           2. 用户订单汇总视图（聚合视图）
--           3. 可更新视图（简单视图，支持 DML 落到原表）
--           4. WITH CHECK OPTION（保证更新后仍满足视图条件）
--           5. 视图修改与删除
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day12 - 视图、存储过程、函数与触发器/Code/01-view-demo.sql
-- ============================================================

USE ecommerce;

-- ------------------------------------------------------------
-- 0. 清理可能存在的旧视图（保证可重复执行）
-- ------------------------------------------------------------
DROP VIEW IF EXISTS v_product_sales;
DROP VIEW IF EXISTS v_user_order_summary;
DROP VIEW IF EXISTS v_active_users;
DROP VIEW IF EXISTS v_active_users_check;
DROP VIEW IF EXISTS v_user_email_only;

-- ============================================================
-- 1. 商品销售统计视图（含聚合 + JOIN，不可更新）
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 创建视图：每个商品的销售数量、销售额、订单数
--     底层表：products LEFT JOIN order_items
--     LEFT JOIN 保证没销量的商品也列出
-- ------------------------------------------------------------
CREATE VIEW v_product_sales AS
SELECT
    p.id            AS product_id,
    p.name          AS product_name,
    p.price         AS price,
    p.stock         AS stock,
    p.status        AS status,
    COALESCE(SUM(oi.quantity), 0)              AS sold_qty,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS sold_amount,
    COUNT(oi.id)                               AS order_cnt
FROM products p
LEFT JOIN order_items oi ON oi.product_id = p.id
GROUP BY p.id, p.name, p.price, p.stock, p.status;

-- ------------------------------------------------------------
-- 1.2 查询视图（与查表写法完全一致）
--     查销量 Top 5 商品
-- ------------------------------------------------------------
SELECT product_id, product_name, sold_qty, sold_amount, order_cnt
FROM v_product_sales
ORDER BY sold_qty DESC
LIMIT 5;

-- ------------------------------------------------------------
-- 1.3 视图再过滤：销量 > 0 但库存 < 10 的"热销缺货"商品
-- ------------------------------------------------------------
SELECT product_name, sold_qty, stock
FROM v_product_sales
WHERE sold_qty > 0 AND stock < 10
ORDER BY sold_qty DESC;

-- ------------------------------------------------------------
-- 1.4 验证该视图不可更新（含聚合，UPDATE 会被拒绝）
--     下列语句会报错：The target table v_product_sales of the UPDATE is not updatable
--     （已注释，避免 source 执行中断）
-- ------------------------------------------------------------
-- UPDATE v_product_sales SET stock = 100 WHERE product_id = 1;

-- ============================================================
-- 2. 用户订单汇总视图（聚合视图）
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 每个用户的订单数、消费总额、最近下单时间
-- ------------------------------------------------------------
CREATE VIEW v_user_order_summary AS
SELECT
    u.id,
    u.username,
    u.email,
    u.role,
    COUNT(o.id)                       AS order_count,
    COALESCE(SUM(o.total_amount), 0)  AS total_spent,
    MAX(o.created_at)                 AS last_order_at
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.id, u.username, u.email, u.role;

-- ------------------------------------------------------------
-- 2.2 查询视图：消费 Top 5 用户
-- ------------------------------------------------------------
SELECT id, username, role, order_count, total_spent, last_order_at
FROM v_user_order_summary
ORDER BY total_spent DESC
LIMIT 5;

-- ------------------------------------------------------------
-- 2.3 视图嵌套查询：找出"高消费且未活跃"用户（最近 90 天未下单）
-- ------------------------------------------------------------
SELECT username, total_spent, last_order_at
FROM v_user_order_summary
WHERE total_spent > 1000
  AND (last_order_at IS NULL OR last_order_at < NOW() - INTERVAL 90 DAY)
ORDER BY total_spent DESC;

-- ============================================================
-- 3. 可更新视图（简单视图，支持 INSERT/UPDATE/DELETE）
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 创建简单视图：只查 status=1 的活跃用户的部分列
--     无聚合、无 JOIN、无 GROUP BY → 可更新
-- ------------------------------------------------------------
CREATE VIEW v_active_users AS
SELECT id, username, email, role, status, created_at
FROM users
WHERE status = 1;

-- ------------------------------------------------------------
-- 3.2 通过视图查询
-- ------------------------------------------------------------
SELECT id, username, email, status FROM v_active_users LIMIT 5;

-- ------------------------------------------------------------
-- 3.3 通过视图 INSERT（数据落到 users 表）
--     先记下当前 users 表行数
-- ------------------------------------------------------------
SELECT COUNT(*) AS users_total_before FROM users;

INSERT INTO v_active_users(id, username, email, role, status, created_at)
VALUES (900001, 'view_test_user_1', 'vt1@demo.com', 'customer', 1, NOW());

-- ------------------------------------------------------------
-- 3.4 验证：users 表多了一行，视图也能查到
-- ------------------------------------------------------------
SELECT COUNT(*) AS users_total_after FROM users;
SELECT id, username, email, status FROM users WHERE id = 900001;
SELECT id, username, email, status FROM v_active_users WHERE id = 900001;

-- ------------------------------------------------------------
-- 3.5 通过视图 UPDATE
-- ------------------------------------------------------------
UPDATE v_active_users SET email = 'vt1_updated@demo.com' WHERE id = 900001;
SELECT id, username, email FROM users WHERE id = 900001;

-- ------------------------------------------------------------
-- 3.6 通过视图 DELETE（实际删除 users 表的行）
-- ------------------------------------------------------------
DELETE FROM v_active_users WHERE id = 900001;
SELECT COUNT(*) AS users_total_final FROM users;
SELECT id FROM users WHERE id = 900001;  -- 应无结果

-- ============================================================
-- 4. WITH CHECK OPTION（保证更新后仍满足视图条件）
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 创建带 CHECK OPTION 的视图
--     仅包含 status=1 的用户，且强制写入/更新后仍必须 status=1
-- ------------------------------------------------------------
CREATE VIEW v_active_users_check AS
SELECT id, username, email, role, status, created_at
FROM users
WHERE status = 1
WITH CHECK OPTION;

-- ------------------------------------------------------------
-- 4.2 演示：插入 status=0 的行会被拒绝
--     （已注释，避免 source 执行中断，可手动放开验证）
-- ------------------------------------------------------------
-- INSERT INTO v_active_users_check(id, username, email, role, status, created_at)
-- VALUES (900002, 'check_test', 'ct@demo.com', 'customer', 0, NOW());
-- 报错: CHECK OPTION failed 'ecommerce.v_active_users_check'

-- ------------------------------------------------------------
-- 4.3 合法插入：status=1 通过
-- ------------------------------------------------------------
INSERT INTO v_active_users_check(id, username, email, role, status, created_at)
VALUES (900003, 'check_ok', 'co@demo.com', 'customer', 1, NOW());

SELECT id, username, status FROM v_active_users_check WHERE id = 900003;

-- ------------------------------------------------------------
-- 4.4 演示：把 status 改为 0 会被拒绝（改后不满足 WHERE status=1）
--     （已注释）
-- ------------------------------------------------------------
-- UPDATE v_active_users_check SET status = 0 WHERE id = 900003;
-- 报错: CHECK OPTION failed

-- ------------------------------------------------------------
-- 4.5 合法更新：仍保持 status=1，通过
-- ------------------------------------------------------------
UPDATE v_active_users_check SET email = 'co2@demo.com' WHERE id = 900003;
SELECT id, username, email, status FROM v_active_users_check WHERE id = 900003;

-- ------------------------------------------------------------
-- 4.6 清理测试数据
-- ------------------------------------------------------------
DELETE FROM users WHERE id = 900003;

-- ============================================================
-- 5. 视图修改与删除
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 用 CREATE OR REPLACE VIEW 修改视图定义
--     给 v_active_users 增加返回 deleted_at 字段
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_active_users AS
SELECT id, username, email, role, status, created_at, deleted_at
FROM users
WHERE status = 1;

-- 查看视图定义
SHOW CREATE VIEW v_active_users\G

-- ------------------------------------------------------------
-- 5.2 用 ALTER VIEW 修改视图
--     去掉 deleted_at，恢复原定义
-- ------------------------------------------------------------
ALTER VIEW v_active_users AS
SELECT id, username, email, role, status, created_at
FROM users
WHERE status = 1;

SHOW CREATE VIEW v_active_users\G

-- ------------------------------------------------------------
-- 5.3 查看当前库所有视图
-- ------------------------------------------------------------
SELECT table_name AS 视图名
FROM information_schema.views
WHERE table_schema = 'ecommerce';

-- ------------------------------------------------------------
-- 5.4 删除视图（IF EXISTS 防止不存在时报错）
-- ------------------------------------------------------------
DROP VIEW IF EXISTS v_product_sales;
DROP VIEW IF EXISTS v_user_order_summary;
DROP VIEW IF EXISTS v_active_users;
DROP VIEW IF EXISTS v_active_users_check;

-- ------------------------------------------------------------
-- 5.5 验证删除
-- ------------------------------------------------------------
SELECT table_name AS 视图名
FROM information_schema.views
WHERE table_schema = 'ecommerce';

-- ============================================================
-- 视图演示完毕。
-- 关键结论：
--   1) 聚合/JOIN/DISTINCT 视图不可 DML；简单视图可更新
--   2) WITH CHECK OPTION 保证"写入/更新后仍能从视图查到"
--   3) 视图是查询的封装，不加速查询；嵌套层数尽量浅
-- ============================================================
