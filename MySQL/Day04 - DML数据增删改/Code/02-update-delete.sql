-- ============================================================
-- 文件名称: 02-update-delete.sql
-- 文件用途: 演示 DML 中 UPDATE / DELETE 的各类操作
--           含: 单表更新、多列更新、ORDER BY+LIMIT 更新、
--               多表 UPDATE JOIN、单表删除、多表 DELETE JOIN、
--               TRUNCATE 对比、ON DUPLICATE KEY UPDATE、
--               sql_safe_updates、ROW_COUNT()、LAST_INSERT_ID()
--           基于 ecommerce 库的数据（先执行 01-insert-data.sql）
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day04/Code/02-update-delete.sql
-- 还原方式: 演示完重新 SOURCE 01-insert-data.sql 即可恢复数据
-- ============================================================

USE ecommerce;

-- ============================================================
-- 一、INSERT 复习与变体（承接 Day04 主题，铺垫更新删除）
-- ============================================================

-- 1.1 INSERT IGNORE: 唯一键冲突时忽略而非报错
--     场景: 批量插入时跳过已存在的记录
SELECT '--- 1.1 INSERT IGNORE 演示 ---' AS 提示;
SELECT username, email FROM users WHERE username = 'alice';
-- alice 已存在，下面会忽略而非报错
INSERT IGNORE INTO users (username, email, password_hash, role) VALUES
  ('alice', 'alice@163.com', 'hash_placeholder', 'customer'),
  ('newuser1', 'newuser1@163.com', 'hash_placeholder', 'customer');
SELECT username, email FROM users WHERE username IN ('alice','newuser1');
-- alice 不变，newuser1 新增成功

-- 1.2 INSERT ... ON DUPLICATE KEY UPDATE (upsert)
--     场景: 存在则更新，不存在则插入
SELECT '--- 1.2 ON DUPLICATE KEY UPDATE 演示 ---' AS 提示;
INSERT INTO accounts (user_id, balance, version) VALUES (11, 1000.00, 0)
  ON DUPLICATE KEY UPDATE balance = VALUES(balance), version = version + 1;
-- user_id=11 的账户不存在，会插入
SELECT user_id, balance, version FROM accounts WHERE user_id = 11;

-- 再次执行：user_id=11 已存在，触发 UPDATE，balance 更新，version+1
INSERT INTO accounts (user_id, balance, version) VALUES (11, 2000.00, 0)
  ON DUPLICATE KEY UPDATE balance = VALUES(balance), version = version + 1;
SELECT user_id, balance, version FROM accounts WHERE user_id = 11;
-- balance 变 2000，version 变 1

-- 1.3 REPLACE INTO: 唯一键冲突时先删后插（自增 id 会变，慎用）
SELECT '--- 1.3 REPLACE INTO 演示 ---' AS 提示;
SELECT id, username FROM users WHERE username = 'newuser1';
REPLACE INTO users (id, username, email, password_hash, role)
VALUES ((SELECT id FROM (SELECT id FROM users WHERE username='newuser1') t),
        'newuser1', 'newuser1@163.com', 'replaced_hash', 'customer');
-- 因 id 冲突，先删后插，id 不变（这里指定了同 id），email 等被替换
SELECT id, username, email, password_hash FROM users WHERE username = 'newuser1';


-- ============================================================
-- 二、UPDATE 单表更新
-- ============================================================

-- 2.1 单列更新（带 WHERE，避免全表更新）
SELECT '--- 2.1 单列 UPDATE ---' AS 提示;
SELECT id, name, price FROM products WHERE id = 13;
UPDATE products SET price = 109.00 WHERE id = 13;  -- T恤涨价
SELECT id, name, price FROM products WHERE id = 13;

-- 2.2 多列更新
SELECT '--- 2.2 多列 UPDATE ---' AS 提示;
UPDATE products
  SET price = 119.00, stock = stock + 100
WHERE id = 13;
SELECT id, name, price, stock FROM products WHERE id = 13;

-- 2.3 表达式更新（基于现有值）
SELECT '--- 2.3 表达式 UPDATE ---' AS 提示;
-- 全场上架商品降价 5%（演示用，注意 WHERE 限制范围）
UPDATE products SET price = ROUND(price * 0.95, 2) WHERE status = 'on_sale' AND category_id = 2;
SELECT id, name, price FROM products WHERE category_id = 2;

-- 2.4 ORDER BY + LIMIT 更新（只更新排序后的前 N 条）
SELECT '--- 2.4 ORDER BY + LIMIT UPDATE ---' AS 提示;
-- 给库存最少的 3 个在售商品补货 50
SELECT id, name, stock FROM products WHERE status='on_sale' ORDER BY stock ASC LIMIT 3;
UPDATE products
  SET stock = stock + 50
WHERE status = 'on_sale'
ORDER BY stock ASC
LIMIT 3;
SELECT id, name, stock FROM products WHERE status='on_sale' ORDER BY stock ASC LIMIT 5;

-- 2.5 用 CASE 条件更新
SELECT '--- 2.5 CASE 条件 UPDATE ---' AS 提示;
-- 按分类调整库存：手机类+10，电脑类+20
UPDATE products
  SET stock = CASE category_id
    WHEN 2 THEN stock + 10
    WHEN 3 THEN stock + 20
    ELSE stock
  END
WHERE category_id IN (2, 3);
SELECT id, name, category_id, stock FROM products WHERE category_id IN (2,3) ORDER BY category_id, id;


-- ============================================================
-- 三、UPDATE 多表 JOIN 更新
-- ============================================================

-- 3.1 根据订单明细更新商品库存（下单扣库存场景）
SELECT '--- 3.1 多表 UPDATE JOIN ---' AS 提示;
-- 先看商品1当前库存
SELECT id, name, stock FROM products WHERE id = 1;

-- 假设订单1的iPhone再买1台，扣库存：用 order_items 关联 products
UPDATE products p
JOIN order_items oi ON p.id = oi.product_id
SET p.stock = p.stock - oi.quantity
WHERE oi.order_id = 1;
SELECT id, name, stock FROM products WHERE id = 1;
-- 库存减少了订单1中iPhone的数量

-- 3.2 根据用户角色更新账户余额（演示关联 users 更新 accounts）
SELECT '--- 3.2 关联用户更新账户 ---' AS 提示;
-- 给所有 customer 角色用户充值 100
UPDATE accounts a
JOIN users u ON a.user_id = u.id
SET a.balance = a.balance + 100
WHERE u.role = 'customer';
SELECT u.username, u.role, a.balance
FROM accounts a JOIN users u ON a.user_id = u.id
WHERE u.role = 'customer'
ORDER BY a.balance DESC;


-- ============================================================
-- 四、DELETE 单表删除
-- ============================================================

-- 4.1 条件删除
SELECT '--- 4.1 条件 DELETE ---' AS 提示;
SELECT COUNT(*) AS 删除前 FROM reviews WHERE rating = 4;
DELETE FROM reviews WHERE rating = 4;
SELECT COUNT(*) AS 删除后 FROM reviews WHERE rating = 4;
SELECT COUNT(*) AS 评价总数 FROM reviews;

-- 4.2 ORDER BY + LIMIT 删除（删最早几条）
SELECT '--- 4.2 ORDER BY + LIMIT DELETE ---' AS 提示;
SELECT id, user_id, product_id FROM reviews ORDER BY id ASC LIMIT 3;
DELETE FROM reviews ORDER BY id ASC LIMIT 3;
SELECT COUNT(*) AS 删除后评价数 FROM reviews;


-- ============================================================
-- 五、DELETE 多表 JOIN 删除
-- ============================================================

-- 5.1 删除指定用户的所有评价（用 JOIN 或子查询）
SELECT '--- 5.1 多表 DELETE JOIN ---' AS 提示;
-- 先看 alice(user_id=3) 的评价
SELECT id, user_id, product_id FROM reviews WHERE user_id = 3;

-- 用多表 DELETE 语法删除 alice 的评价
DELETE r FROM reviews r
JOIN users u ON r.user_id = u.id
WHERE u.username = 'alice';
SELECT COUNT(*) AS alice评价数 FROM reviews r JOIN users u ON r.user_id=u.id WHERE u.username='alice';

-- 5.2 同时删除多张表的匹配行（DELETE t1, t2 FROM ...）
--     场景: 删除已取消的订单及其明细
SELECT '--- 5.2 级联删除多表 ---' AS 提示;
SELECT o.id AS 订单, oi.id AS 明细 FROM orders o LEFT JOIN order_items oi ON o.id=oi.order_id WHERE o.status='cancelled';

DELETE o, oi FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
WHERE o.status = 'cancelled';
SELECT COUNT(*) AS 取消订单数 FROM orders WHERE status='cancelled';
SELECT COUNT(*) AS 关联明细数 FROM order_items oi JOIN orders o ON o.id=oi.order_id WHERE o.status='cancelled';


-- ============================================================
-- 六、DELETE vs TRUNCATE vs DROP 对比
-- ============================================================

SELECT '--- 6. DELETE vs TRUNCATE vs DROP ---' AS 提示;

-- 6.1 创建临时对比表
DROP TABLE IF EXISTS truncate_vs_delete;
CREATE TABLE truncate_vs_delete (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  val INT
) ENGINE=InnoDB AUTO_INCREMENT=1000;
INSERT INTO truncate_vs_delete (val) VALUES (1),(2),(3),(4),(5);

SELECT '--- DELETE 方式 ---' AS 方式;
SELECT COUNT(*) AS 删除前, (SELECT AUTO_INCREMENT FROM information_schema.tables WHERE table_schema='ecommerce' AND table_name='truncate_vs_delete') AS 自增值 FROM truncate_vs_delete;
DELETE FROM truncate_vs_delete;  -- DML，可回滚，自增不重置
SELECT COUNT(*) AS 删除后, (SELECT AUTO_INCREMENT FROM information_schema.tables WHERE table_schema='ecommerce' AND table_name='truncate_vs_delete') AS 自增值 FROM truncate_vs_delete;
-- 自增值仍是 1006，DELETE 不重置

-- 重新插数据演示 TRUNCATE
INSERT INTO truncate_vs_delete (val) VALUES (10),(20),(30);
SELECT '--- TRUNCATE 方式 ---' AS 方式;
SELECT COUNT(*) AS 清空前, (SELECT AUTO_INCREMENT FROM information_schema.tables WHERE table_schema='ecommerce' AND table_name='truncate_vs_delete') AS 自增值 FROM truncate_vs_delete;
TRUNCATE TABLE truncate_vs_delete;  -- DDL，不可回滚，自增重置
SELECT COUNT(*) AS 清空后, (SELECT AUTO_INCREMENT FROM information_schema.tables WHERE table_schema='ecommerce' AND table_name='truncate_vs_delete') AS 自增值 FROM truncate_vs_delete;
-- 自增值回到 1，TRUNCATE 重置

-- DROP 演示
SELECT '--- DROP 方式 ---' AS 方式;
SHOW TABLES LIKE 'truncate_vs_delete';
DROP TABLE truncate_vs_delete;
SHOW TABLES LIKE 'truncate_vs_delete';  -- 表已不存在


-- ============================================================
-- 七、sql_safe_updates 安全更新模式
-- ============================================================

SELECT '--- 7. sql_safe_updates 安全模式 ---' AS 提示;

-- 查看当前设置
SHOW VARIABLES LIKE 'sql_safe_updates';

-- 临时开启安全更新模式（仅当前会话）
SET sql_safe_updates = 1;
SHOW VARIABLES LIKE 'sql_safe_updates';

-- 安全模式下，无 WHERE 或 WHERE 不含索引列的 UPDATE/DELETE 会报错
-- UPDATE products SET stock = 0;  -- ERROR 1175: You are using safe update mode
-- DELETE FROM reviews;            -- ERROR 1175

-- 带 WHERE 且列为索引时可执行
SELECT COUNT(*) FROM reviews;
DELETE FROM reviews WHERE rating = 1;  -- rating 不是索引列，仍会报错
-- 实际需用索引列或 LIMIT
DELETE FROM reviews WHERE id > 0 LIMIT 1;  -- 加 LIMIT 可绕过

-- 关闭安全模式恢复
SET sql_safe_updates = 0;
SHOW VARIABLES LIKE 'sql_safe_updates';


-- ============================================================
-- 八、ROW_COUNT() 与受影响行数
-- ============================================================

SELECT '--- 8. ROW_COUNT() 受影响行数 ---' AS 提示;

-- ROW_COUNT() 返回上一条 SQL 影响的行数
UPDATE products SET stock = stock WHERE category_id = 4;  -- 实际未改值
SELECT ROW_COUNT() AS 更新影响行数;  -- 返回匹配的行数（即使值未变）

DELETE FROM reviews WHERE rating = 2;
SELECT ROW_COUNT() AS 删除影响行数;

INSERT INTO accounts (user_id, balance) VALUES (12, 500.00);
SELECT ROW_COUNT() AS 插入影响行数;  -- 1


-- ============================================================
-- 九、LAST_INSERT_ID() 获取自增 ID
-- ============================================================

SELECT '--- 9. LAST_INSERT_ID() ---' AS 提示;

-- 插入新用户，立即获取自增 ID
INSERT INTO users (username, email, password_hash, role)
VALUES ('lastid_demo', 'lastid@demo.com', 'hash_demo', 'customer');

SELECT LAST_INSERT_ID() AS 最近自增ID;
SELECT id, username FROM users WHERE username = 'lastid_demo';

-- 用获取的 ID 关联插入账户（1:1）
INSERT INTO accounts (user_id, balance) VALUES (LAST_INSERT_ID(), 200.00);
SELECT user_id, balance FROM accounts WHERE user_id = (SELECT id FROM users WHERE username='lastid_demo');

-- 注意: 多行插入时 LAST_INSERT_ID() 返回第一条的 ID
INSERT INTO users (username, email, password_hash) VALUES
  ('batch1', 'batch1@demo.com', 'h'),
  ('batch2', 'batch2@demo.com', 'h');
SELECT LAST_INSERT_ID() AS 多行插入返回的首ID;  -- 返回 batch1 的 id


-- ============================================================
-- 十、事务中的 UPDATE/DELETE 可回滚（预告 TCL）
-- ============================================================

SELECT '--- 10. 事务回滚演示 ---' AS 提示;

-- 查看商品11当前价格
SELECT id, name, price FROM products WHERE id = 11;

BEGIN;
UPDATE products SET price = 999.99 WHERE id = 11;
SELECT id, name, price FROM products WHERE id = 11;  -- 改了
ROLLBACK;
SELECT id, name, price FROM products WHERE id = 11;  -- 回滚，恢复原价

-- TRUNCATE 是 DDL，不能回滚（对比）
-- BEGIN;
-- TRUNCATE TABLE reviews;  -- 即使在事务内，执行后不可回滚
-- ROLLBACK;
-- SELECT COUNT(*) FROM reviews;  -- 已清空，无法恢复


-- ============================================================
-- 十一、清理演示数据
-- ============================================================

-- 删除本脚本产生的演示用户与账户
DELETE FROM accounts WHERE user_id IN (SELECT id FROM (SELECT id FROM users WHERE username IN ('newuser1','lastid_demo','batch1','batch2','ivan','disabled_user') OR id > 12) t);
DELETE FROM users WHERE username IN ('newuser1','lastid_demo','batch1','batch2') OR id > 12;

SELECT COUNT(*) AS 最终用户数 FROM users;
SELECT COUNT(*) AS 最终评价数 FROM reviews;

-- ============================================================
-- 还原提示:
-- 本脚本对 ecommerce 数据做了大量修改（价格变动、删除评价等）。
-- 如需还原初始数据，请重新执行:
--   SOURCE 01-insert-data.sql
-- ============================================================

-- ============================================================
-- DML 更新删除演示完毕。
-- 核心结论:
--   1. UPDATE/DELETE 务必带 WHERE，生产环境开 sql_safe_updates
--   2. ON DUPLICATE KEY UPDATE 实现 upsert，REPLACE 是先删后插
--   3. 多表 UPDATE/DELETE JOIN 可跨表操作
--   4. TRUNCATE 重置自增、不可回滚；DELETE 可回滚、不重置
--   5. ROW_COUNT() 取影响行数，LAST_INSERT_ID() 取自增ID
--   6. 事务内 DML 可回滚，DDL（TRUNCATE/DROP）不可回滚
-- ============================================================
