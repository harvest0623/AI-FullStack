-- ============================================================
-- 文件名称: 02-procedure-demo.sql
-- 文件用途: 存储过程 PROCEDURE 演示脚本
--           1. 转账存储过程（事务 + 异常处理）
--           2. 分页查询存储过程（IN 参数）
--           3. 订单统计存储过程（OUT 参数）
--           4. 带游标遍历的存储过程（CURSOR + HANDLER）
--           5. 流程控制综合示例
-- 注意事项: 存储过程体含 ; 分号，需切换 DELIMITER
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day12 - 视图、存储过程、函数与触发器/Code/02-procedure-demo.sql
-- ============================================================

USE ecommerce;

-- ------------------------------------------------------------
-- 0. 清理旧存储过程（保证可重复执行）
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_transfer;
DROP PROCEDURE IF EXISTS sp_page_products;
DROP PROCEDURE IF EXISTS sp_stat_user_orders;
DROP PROCEDURE IF EXISTS sp_iterate_active_users;
DROP PROCEDURE IF EXISTS sp_classify_product;

-- ============================================================
-- 1. 转账存储过程（事务 + 异常处理）
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 创建转账过程
--     - IN from_uid / to_uid / amount
--     - 使用 DECLARE EXIT HANDLER 捕获异常并 ROLLBACK
--     - 显式 BEGIN/COMMIT/ROLLBACK
-- ------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE sp_transfer(
    IN from_uid INT,
    IN to_uid   INT,
    IN amount   DECIMAL(10,2)
)
BEGIN
    -- 异常处理：发生错误时回滚并返回错误信息
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT '转账失败，已回滚' AS result, from_uid, to_uid, amount;
    END;

    START TRANSACTION;

    -- 扣款：使用乐观条件 balance >= amount 防止透支
    UPDATE accounts
       SET balance = balance - amount
     WHERE user_id = from_uid
       AND balance >= amount;

    -- 若上面影响行数为 0，说明余额不足，人为抛错
    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '余额不足或转出账户不存在';
    END IF;

    -- 加款
    UPDATE accounts
       SET balance = balance + amount
     WHERE user_id = to_uid;

    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '收款账户不存在';
    END IF;

    COMMIT;

    SELECT '转账成功' AS result, from_uid, to_uid, amount;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 1.2 调用前查看账户余额
-- ------------------------------------------------------------
SELECT user_id, balance, version FROM accounts ORDER BY user_id LIMIT 10;

-- ------------------------------------------------------------
-- 1.3 调用转账过程（取前两个账户互转，金额设小一些避免失败）
--     注意：需要 accounts 表有数据，若为空请先在 Day04 灌入测试数据
-- ------------------------------------------------------------
-- 取出两个真实存在的 user_id
SET @u1 := (SELECT user_id FROM accounts ORDER BY user_id LIMIT 1);
SET @u2 := (SELECT user_id FROM accounts ORDER BY user_id LIMIT 1, 1);
SET @amt := 10.00;

SELECT @u1 AS 转出, @u2 AS 转入, @amt AS 金额;

CALL sp_transfer(@u1, @u2, @amt);

-- ------------------------------------------------------------
-- 1.4 调用后查看余额变化
-- ------------------------------------------------------------
SELECT user_id, balance, version FROM accounts
WHERE user_id IN (@u1, @u2);

-- ------------------------------------------------------------
-- 1.5 演示余额不足触发回滚（设一个超大金额）
--     （已注释，可手动放开观察"转账失败"分支）
-- ------------------------------------------------------------
-- CALL sp_transfer(@u1, @u2, 999999999.99);

-- ============================================================
-- 2. 分页查询存储过程（IN 参数）
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 通用分页查询商品
--     - IN p_page：页码（从 1 开始）
--     - IN p_size：每页条数
--     - IN p_status：商品状态过滤（NULL 表示不过滤）
-- ------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE sp_page_products(
    IN p_page   INT,
    IN p_size   INT,
    IN p_status VARCHAR(20)
)
BEGIN
    DECLARE v_offset INT;

    -- 容错：页码最小 1
    IF p_page < 1 OR p_page IS NULL THEN
        SET p_page = 1;
    END IF;

    -- 容错：每页条数限制 1~200
    IF p_size < 1 OR p_size IS NULL THEN
        SET p_size = 10;
    ELSEIF p_size > 200 THEN
        SET p_size = 200;
    END IF;

    SET v_offset = (p_page - 1) * p_size;

    -- 动态拼接：用 CASE 判断是否过滤 status
    SELECT
        p.id, p.name, p.category_id, p.price, p.stock, p.status, p.created_at
    FROM products p
    WHERE p_status IS NULL OR p.status = p_status
    ORDER BY p.id
    LIMIT v_offset, p_size;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 2.2 调用分页查询
-- ------------------------------------------------------------
-- 第 1 页，每页 5 条，全部状态
CALL sp_page_products(1, 5, NULL);

-- 第 2 页，每页 5 条，只看在售
CALL sp_page_products(2, 5, 'on_sale');

-- 容错测试：传非法页码
CALL sp_page_products(-1, 0, NULL);

-- ============================================================
-- 3. 订单统计存储过程（OUT 参数）
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 统计某用户的订单数、总消费、平均客单价
--     通过 OUT 参数返回，调用方用 @变量 接收
-- ------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE sp_stat_user_orders(
    IN  p_uid     INT,
    OUT p_cnt     INT,
    OUT p_total   DECIMAL(12,2),
    OUT p_avg     DECIMAL(12,2)
)
BEGIN
    SELECT
        COUNT(*),
        COALESCE(SUM(total_amount), 0),
        COALESCE(AVG(total_amount), 0)
    INTO p_cnt, p_total, p_avg
    FROM orders
    WHERE user_id = p_uid;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 3.2 调用并查看 OUT 结果
-- ------------------------------------------------------------
SET @stat_uid := (SELECT id FROM users WHERE role = 'customer' LIMIT 1);
SELECT @stat_uid AS 待统计用户;

CALL sp_stat_user_orders(@stat_uid, @cnt, @total, @avg);

SELECT
    @stat_uid AS user_id,
    @cnt      AS 订单数,
    @total    AS 消费总额,
    @avg      AS 平均客单价;

-- ------------------------------------------------------------
-- 3.3 对照直接查询验证
-- ------------------------------------------------------------
SELECT
    COUNT(*)            AS 订单数,
    COALESCE(SUM(total_amount), 0) AS 消费总额,
    COALESCE(AVG(total_amount), 0) AS 平均客单价
FROM orders
WHERE user_id = @stat_uid;

-- ============================================================
-- 4. 带游标遍历的存储过程（CURSOR + HANDLER）
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 用游标遍历所有 status=1 的用户
--     汇总每个用户的订单数到一张临时结果表
-- ------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE sp_iterate_active_users()
BEGIN
    -- 局部变量必须先声明
    DECLARE v_uid      INT;
    DECLARE v_uname    VARCHAR(50);
    DECLARE v_cnt      INT;
    DECLARE v_done     INT DEFAULT 0;

    -- 游标声明（必须在 DECLARE HANDLER 之前）
    DECLARE cur CURSOR FOR
        SELECT id, username FROM users WHERE status = 1;

    -- NOT FOUND 处理器：游标取完时把 v_done 置 1
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    -- 临时表存结果（用临时表方便最后一次性 SELECT 出来）
    DROP TEMPORARY TABLE IF EXISTS tmp_user_order_cnt;
    CREATE TEMPORARY TABLE tmp_user_order_cnt(
        user_id INT,
        username VARCHAR(50),
        order_cnt INT
    );

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO v_uid, v_uname;
        IF v_done = 1 THEN
            LEAVE read_loop;
        END IF;

        -- 查每个用户的订单数
        SELECT COUNT(*) INTO v_cnt FROM orders WHERE user_id = v_uid;

        INSERT INTO tmp_user_order_cnt VALUES (v_uid, v_uname, v_cnt);
    END LOOP;

    CLOSE cur;

    -- 输出结果
    SELECT user_id, username, order_cnt
    FROM tmp_user_order_cnt
    ORDER BY order_cnt DESC, user_id;

    DROP TEMPORARY TABLE IF EXISTS tmp_user_order_cnt;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 4.2 调用游标存储过程
-- ------------------------------------------------------------
CALL sp_iterate_active_users();

-- ============================================================
-- 5. 流程控制综合示例：CASE WHEN 给商品分级
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 根据 status 与 stock 给商品打标签
--     演示 CASE WHEN 的多分支
-- ------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE sp_classify_product(IN p_pid INT)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_stock  INT;
    DECLARE v_label  VARCHAR(50);

    SELECT status, stock INTO v_status, v_stock
    FROM products
    WHERE id = p_pid;

    IF v_status IS NULL THEN
        SELECT '商品不存在' AS label, p_pid AS product_id;
    ELSE
        CASE
            WHEN v_status = 'draft'              THEN SET v_label = '草稿未上架';
            WHEN v_status = 'off_sale'           THEN SET v_label = '已下架';
            WHEN v_status = 'on_sale' AND v_stock = 0 THEN SET v_label = '在售缺货';
            WHEN v_status = 'on_sale' AND v_stock < 10 THEN SET v_label = '在售低库存';
            WHEN v_status = 'on_sale' AND v_stock < 100 THEN SET v_label = '在售正常';
            WHEN v_status = 'on_sale'            THEN SET v_label = '在售库存充足';
            ELSE SET v_label = '未知状态';
        END CASE;

        SELECT p_pid AS product_id, v_status AS status, v_stock AS stock, v_label AS label;
    END IF;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 5.2 调用：取一个真实商品 ID 测试
-- ------------------------------------------------------------
SET @cls_pid := (SELECT id FROM products LIMIT 1);
CALL sp_classify_product(@cls_pid);

-- 测试不存在的 ID
CALL sp_classify_product(-1);

-- ============================================================
-- 6. 查看与删除存储过程
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 查看存储过程状态
-- ------------------------------------------------------------
SELECT routine_name, routine_type, created, last_altered
FROM information_schema.routines
WHERE routine_schema = 'ecommerce'
ORDER BY routine_name;

-- ------------------------------------------------------------
-- 6.2 查看某存储过程定义
-- ------------------------------------------------------------
SHOW CREATE PROCEDURE sp_transfer\G

-- ------------------------------------------------------------
-- 6.3 删除所有演示存储过程
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_transfer;
DROP PROCEDURE IF EXISTS sp_page_products;
DROP PROCEDURE IF EXISTS sp_stat_user_orders;
DROP PROCEDURE IF EXISTS sp_iterate_active_users;
DROP PROCEDURE IF EXISTS sp_classify_product;

-- ============================================================
-- 存储过程演示完毕。
-- 关键结论：
--   1) DELIMITER $$ 切换分隔符，过程体结束后 DELIMITER ; 恢复
--   2) IN 入参 / OUT 出参 / INOUT 既入又出
--   3) 游标四步：DECLARE CURSOR → OPEN → FETCH(LOOP) → CLOSE
--   4) DECLARE CONTINUE HANDLER FOR NOT FOUND 是游标取完的标准套路
--   5) SIGNAL SQLSTATE '45000' 用于自定义抛错
-- ============================================================
