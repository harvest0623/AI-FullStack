-- ============================================================
-- 文件名称: 04-trigger-demo.sql
-- 文件用途: 触发器 TRIGGER 演示脚本
--           1. 用户软删除审计触发器（BEFORE UPDATE）
--           2. 商品库存变更日志触发器（AFTER UPDATE）
--           3. 订单状态变更记录触发器（AFTER UPDATE）
--           4. 下单时库存校验触发器（BEFORE INSERT，演示 SIGNAL）
--           5. AFTER INSERT 同步统计表
--           6. BEFORE DELETE 阻止删除已下单商品
-- 注意事项: 触发器体含 ; 分号，需切换 DELIMITER
--           每张表同时机同事件只能有一个触发器
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day12 - 视图、存储过程、函数与触发器/Code/04-trigger-demo.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 0. 准备审计日志表
-- ============================================================

-- ------------------------------------------------------------
-- 0.1 用户操作审计表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS user_audit_log;
CREATE TABLE user_audit_log (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT          NOT NULL COMMENT '用户ID',
    action       VARCHAR(20)  NOT NULL COMMENT '操作类型 soft_delete/restore',
    old_deleted_at DATETIME   NULL     COMMENT '原删除时间',
    new_deleted_at DATETIME   NULL     COMMENT '新删除时间',
    operate_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户操作审计日志';

-- ------------------------------------------------------------
-- 0.2 商品库存变更日志表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS product_stock_log;
CREATE TABLE product_stock_log (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id    INT          NOT NULL,
    old_stock     INT          NOT NULL,
    new_stock     INT          NOT NULL,
    delta         INT          NOT NULL COMMENT '变更量=新-旧',
    operate_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品库存变更日志';

-- ------------------------------------------------------------
-- 0.3 订单状态变更记录表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS order_status_log;
CREATE TABLE order_status_log (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id     BIGINT        NOT NULL,
    old_status   VARCHAR(20)   NULL,
    new_status   VARCHAR(20)   NOT NULL,
    operate_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order_id(order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单状态变更记录';

-- ------------------------------------------------------------
-- 0.4 用户消费统计表（用于 AFTER INSERT 同步演示）
-- ------------------------------------------------------------
DROP TABLE IF EXISTS user_spent_stat;
CREATE TABLE user_spent_stat (
    user_id      INT            PRIMARY KEY,
    total_spent  DECIMAL(12,2)  NOT NULL DEFAULT 0,
    order_count  INT            NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户消费统计';

-- ------------------------------------------------------------
-- 0.5 清理旧触发器（保证可重复执行）
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_user_soft_delete;
DROP TRIGGER IF EXISTS trg_product_stock_change;
DROP TRIGGER IF EXISTS trg_order_status_change;
DROP TRIGGER IF EXISTS trg_order_items_before_insert;
DROP TRIGGER IF EXISTS trg_orders_after_insert;

-- ============================================================
-- 1. 用户软删除审计触发器（BEFORE UPDATE）
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 当 users.deleted_at 字段从 NULL 变为非 NULL 时
--     记录一条"软删除"审计日志
--     BEFORE 时机：可在触发器中校验/修改 NEW 值
-- ------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_user_soft_delete
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    -- 检测 deleted_at 从 NULL → 有值
    IF (OLD.deleted_at IS NULL AND NEW.deleted_at IS NOT NULL) THEN
        INSERT INTO user_audit_log(user_id, action, old_deleted_at, new_deleted_at, operate_time)
        VALUES (OLD.id, 'soft_delete', OLD.deleted_at, NEW.deleted_at, NOW());
    END IF;

    -- 检测 deleted_at 从有值 → NULL（恢复）
    IF (OLD.deleted_at IS NOT NULL AND NEW.deleted_at IS NULL) THEN
        INSERT INTO user_audit_log(user_id, action, old_deleted_at, new_deleted_at, operate_time)
        VALUES (OLD.id, 'restore', OLD.deleted_at, NEW.deleted_at, NOW());
    END IF;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 1.2 测试：选一个真实用户，软删除后再恢复
-- ------------------------------------------------------------
SET @test_uid := (SELECT id FROM users WHERE deleted_at IS NULL LIMIT 1);
SELECT @test_uid AS 待测试用户, deleted_at FROM users WHERE id = @test_uid;

-- 执行软删除：把 deleted_at 设为当前时间
UPDATE users SET deleted_at = NOW() WHERE id = @test_uid;
-- 恢复：清空 deleted_at
UPDATE users SET deleted_at = NULL WHERE id = @test_uid;

-- ------------------------------------------------------------
-- 1.3 查看审计日志
-- ------------------------------------------------------------
SELECT * FROM user_audit_log WHERE user_id = @test_uid;

-- 清理本次测试日志
DELETE FROM user_audit_log WHERE user_id = @test_uid;

-- ============================================================
-- 2. 商品库存变更日志触发器（AFTER UPDATE）
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 当 products.stock 发生变化时，记录变更前后的值
--     AFTER 时机：操作已落库，适合写日志
-- ------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_product_stock_change
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    IF OLD.stock <> NEW.stock THEN
        INSERT INTO product_stock_log(product_id, old_stock, new_stock, delta, operate_time)
        VALUES (OLD.id, OLD.stock, NEW.stock, NEW.stock - OLD.stock, NOW());
    END IF;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 2.2 测试：选一个真实商品，调整库存
-- ------------------------------------------------------------
SET @test_pid := (SELECT id FROM products LIMIT 1);
SELECT @test_pid AS 待测试商品, stock FROM products WHERE id = @test_pid;

-- 增加库存 10
UPDATE products SET stock = stock + 10 WHERE id = @test_pid;
-- 减少库存 5
UPDATE products SET stock = stock - 5 WHERE id = @test_pid;

-- ------------------------------------------------------------
-- 2.3 查看库存变更日志
-- ------------------------------------------------------------
SELECT * FROM product_stock_log WHERE product_id = @test_pid ORDER BY id;

-- 恢复库存：减去净变化量 (10 - 5 = 5)
UPDATE products SET stock = stock - 5 WHERE id = @test_pid;

-- 清理本次测试日志
DELETE FROM product_stock_log WHERE product_id = @test_pid;

-- ============================================================
-- 3. 订单状态变更记录触发器（AFTER UPDATE）
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 当 orders.status 发生变化时记录前后状态
--     只在状态真正改变时才记录，避免无谓日志
-- ------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_order_status_change
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO order_status_log(order_id, old_status, new_status, operate_time)
        VALUES (OLD.id, OLD.status, NEW.status, NOW());
    END IF;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 3.2 测试：选一个真实订单，改两次状态
-- ------------------------------------------------------------
SET @test_oid := (SELECT id FROM orders LIMIT 1);
SELECT @test_oid AS 待测试订单, status FROM orders WHERE id = @test_oid;

-- 假设原状态是 pending → 改为 paid
UPDATE orders SET status = 'paid' WHERE id = @test_oid AND status = 'pending';
-- paid → shipped
UPDATE orders SET status = 'shipped' WHERE id = @test_oid AND status = 'paid';

-- ------------------------------------------------------------
-- 3.3 查看状态变更记录
-- ------------------------------------------------------------
SELECT * FROM order_status_log WHERE order_id = @test_oid ORDER BY id;

-- 清理本次测试日志（保留订单原状态由实际业务决定，这里仅清理日志）
DELETE FROM order_status_log WHERE order_id = @test_oid;

-- ============================================================
-- 4. 下单时库存校验触发器（BEFORE INSERT，演示 SIGNAL）
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 当向 order_items 插入时，检查商品库存是否足够
--     不足则用 SIGNAL 抛错，阻止插入
--     BEFORE 时机：可在插入前校验，失败则整条 INSERT 回滚
-- ------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_order_items_before_insert
BEFORE INSERT ON order_items
FOR EACH ROW
BEGIN
    DECLARE v_stock INT;
    DECLARE v_status VARCHAR(20);

    SELECT stock, status INTO v_stock, v_status
    FROM products
    WHERE id = NEW.product_id;

    -- 商品必须是在售状态
    IF v_status <> 'on_sale' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '商品非在售状态，禁止下单';
    END IF;

    -- 库存必须足够
    IF v_stock < NEW.quantity THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '库存不足，禁止下单';
    END IF;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 4.2 测试：选一个真实商品与订单
-- ------------------------------------------------------------
SET @oi_oid := (SELECT id FROM orders LIMIT 1);
SET @oi_pid := (SELECT id FROM products WHERE status = 'on_sale' LIMIT 1);
SELECT @oi_oid AS 订单ID, @oi_pid AS 商品ID, stock FROM products WHERE id = @oi_pid;

-- ------------------------------------------------------------
-- 4.3 正常插入：quantity = 1（应成功）
--     注意：插入后需手动清理，避免污染数据
-- ------------------------------------------------------------
INSERT INTO order_items(order_id, product_id, quantity, unit_price)
VALUES(@oi_oid, @oi_pid, 1, (SELECT price FROM products WHERE id = @oi_pid));

SELECT id, order_id, product_id, quantity FROM order_items
WHERE order_id = @oi_oid AND product_id = @oi_pid
ORDER BY id DESC LIMIT 1;

-- 清理
DELETE FROM order_items
WHERE order_id = @oi_oid AND product_id = @oi_pid
ORDER BY id DESC LIMIT 1;

-- ------------------------------------------------------------
-- 4.4 演示：插入超大数量触发库存校验失败
--     （已注释，可手动放开观察 SIGNAL 报错）
-- ------------------------------------------------------------
-- INSERT INTO order_items(order_id, product_id, quantity, unit_price)
-- VALUES(@oi_oid, @oi_pid, 999999, 1.00);
-- 报错: '库存不足，禁止下单'

-- ============================================================
-- 5. AFTER INSERT 同步统计表
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 当订单创建后，自动把消费金额累加到 user_spent_stat
--     若统计行不存在则插入（INSERT...ON DUPLICATE KEY UPDATE）
--     演示触发器内对其他表的级联写操作
-- ------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_orders_after_insert
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    INSERT INTO user_spent_stat(user_id, total_spent, order_count)
    VALUES (NEW.user_id, NEW.total_amount, 1)
    ON DUPLICATE KEY UPDATE
        total_spent = total_spent + NEW.total_amount,
        order_count = order_count + 1;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 5.2 测试：选一个用户，新建订单
-- ------------------------------------------------------------
SET @ins_uid := (SELECT id FROM users WHERE role = 'customer' LIMIT 1);
SELECT @ins_uid AS 测试用户;

-- 测试前先清理统计行
DELETE FROM user_spent_stat WHERE user_id = @ins_uid;

-- 插入两条测试订单（用一个不冲突的大 ID 避免影响业务）
INSERT INTO orders(id, user_id, total_amount, status, created_at)
VALUES (9000001, @ins_uid, 100.00, 'pending', NOW());

INSERT INTO orders(id, user_id, total_amount, status, created_at)
VALUES (9000002, @ins_uid, 200.00, 'pending', NOW());

-- ------------------------------------------------------------
-- 5.3 查看统计表是否自动更新
-- ------------------------------------------------------------
SELECT * FROM user_spent_stat WHERE user_id = @ins_uid;

-- ------------------------------------------------------------
-- 5.4 清理测试订单与统计行
--     注意：删除订单不会自动衰减统计（演示触发器只做增量同步）
--           真实场景需配合 AFTER DELETE / AFTER UPDATE 触发器
-- ------------------------------------------------------------
DELETE FROM orders WHERE id IN (9000001, 9000002);
DELETE FROM user_spent_stat WHERE user_id = @ins_uid;

-- ============================================================
-- 6. BEFORE DELETE 阻止删除已下单商品
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 当尝试删除一个已经被下单的商品时，触发器抛错阻止
--     演示 BEFORE DELETE + SIGNAL 的"数据保护"场景
--     注意：products 表可能已有外键约束，这里再加一层业务保护
-- ------------------------------------------------------------
-- 该触发器默认注释，避免与外键约束冲突或影响后续脚本
-- DELIMITER $$
--
-- CREATE TRIGGER trg_product_before_delete
-- BEFORE DELETE ON products
-- FOR EACH ROW
-- BEGIN
--     DECLARE v_order_cnt INT DEFAULT 0;
--     SELECT COUNT(*) INTO v_order_cnt
--     FROM order_items
--     WHERE product_id = OLD.id;
--     IF v_order_cnt > 0 THEN
--         SIGNAL SQLSTATE '45000'
--             SET MESSAGE_TEXT = '该商品已被下单，禁止删除';
--     END IF;
-- END$$
--
-- DELIMITER ;

-- ============================================================
-- 7. 查看与删除触发器
-- ============================================================

-- ------------------------------------------------------------
-- 7.1 查看当前库所有触发器
-- ------------------------------------------------------------
SELECT
    trigger_name,
    event_manipulation AS event,
    event_object_table AS tbl,
    action_timing      AS timing,
    action_statement   AS body
FROM information_schema.triggers
WHERE trigger_schema = 'ecommerce'
ORDER BY event_object_table, action_timing, event_manipulation;

-- ------------------------------------------------------------
-- 7.2 删除所有演示触发器
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_user_soft_delete;
DROP TRIGGER IF EXISTS trg_product_stock_change;
DROP TRIGGER IF EXISTS trg_order_status_change;
DROP TRIGGER IF EXISTS trg_order_items_before_insert;
DROP TRIGGER IF EXISTS trg_orders_after_insert;

-- ------------------------------------------------------------
-- 7.3 删除演示用审计表（可选：若想保留日志表可注释掉）
-- ------------------------------------------------------------
-- DROP TABLE IF EXISTS user_audit_log;
-- DROP TABLE IF EXISTS product_stock_log;
-- DROP TABLE IF EXISTS order_status_log;
-- DROP TABLE IF EXISTS user_spent_stat;

-- ============================================================
-- 触发器演示完毕。
-- 关键结论：
--   1) BEFORE 时机适合校验/默认值填充/修改 NEW；AFTER 适合审计/同步
--   2) NEW 在 INSERT/UPDATE 可用，OLD 在 UPDATE/DELETE 可用
--   3) SIGNAL SQLSTATE '45000' 是触发器内抛错的标准方式
--   4) 触发器 FOR EACH ROW 每行触发，批量操作开销显著
--   5) 隐式行为难调试，业务流程尽量放应用层
-- ============================================================
