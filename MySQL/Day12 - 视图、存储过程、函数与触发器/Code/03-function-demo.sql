-- ============================================================
-- 文件名称: 03-function-demo.sql
-- 文件用途: 自定义函数 FUNCTION 演示脚本
--           1. 计算折扣价函数（DETERMINISTIC，纯计算）
--           2. 格式化金额函数（DETERMINISTIC，字符串处理）
--           3. 用户等级判断函数（READS SQL DATA，含查询）
--           4. 函数在 SELECT 中使用
-- 注意事项: 函数体含 ; 分号，需切换 DELIMITER
--           若未开启 log_bin_trust_function_creators，
--           函数必须声明 DETERMINISTIC / READS SQL DATA 等
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day12 - 视图、存储过程、函数与触发器/Code/03-function-demo.sql
-- ============================================================

USE ecommerce;

-- ------------------------------------------------------------
-- 0. 清理旧函数（保证可重复执行）
-- ------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_calc_discount_price;
DROP FUNCTION IF EXISTS fn_format_money;
DROP FUNCTION IF EXISTS fn_user_level;
DROP FUNCTION IF EXISTS fn_full_category_path;

-- ============================================================
-- 1. 计算折扣价函数（DETERMINISTIC 纯计算）
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 创建函数：传入原价与折扣率，返回折后价
--     - DETERMINISTIC：相同输入恒返回相同输出
--     - NO SQL：函数内不含 SQL 语句（只有 RETURN 计算）
-- ------------------------------------------------------------
DELIMITER $$

CREATE FUNCTION fn_calc_discount_price(
    p_price DECIMAL(10,2),
    p_off   DECIMAL(4,2)
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
NO SQL
BEGIN
    -- 折扣率范围校验
    IF p_off < 0 OR p_off > 1 THEN
        RETURN NULL;
    END IF;

    RETURN ROUND(p_price * (1 - p_off), 2);
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 1.2 直接调用函数
-- ------------------------------------------------------------
SELECT fn_calc_discount_price(100.00, 0.10) AS 九折价,
       fn_calc_discount_price(200.00, 0.25) AS 七五折价,
       fn_calc_discount_price(50.00, 1.50)  AS 非法折扣;

-- ------------------------------------------------------------
-- 1.3 在 SELECT 中使用：给所有在售商品打 9 折
-- ------------------------------------------------------------
SELECT
    id, name, price,
    fn_calc_discount_price(price, 0.10) AS 九折后价
FROM products
WHERE status = 'on_sale'
LIMIT 5;

-- ============================================================
-- 2. 格式化金额函数（DETERMINISTIC 字符串处理）
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 把数字金额格式化为 "¥1,234.56" 形式
--     - FORMAT 函数自带千分位
--     - CONCAT 拼货币符号
-- ------------------------------------------------------------
DELIMITER $$

CREATE FUNCTION fn_format_money(p_amount DECIMAL(12,2))
RETURNS VARCHAR(30)
DETERMINISTIC
NO SQL
BEGIN
    -- NULL 直接返回 '¥0.00'
    IF p_amount IS NULL THEN
        RETURN '¥0.00';
    END IF;

    RETURN CONCAT('¥', FORMAT(p_amount, 2));
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 2.2 调用
-- ------------------------------------------------------------
SELECT fn_format_money(1234567.89) AS 大额,
       fn_format_money(0.5)        AS 小额,
       fn_format_money(NULL)       AS 空值;

-- ------------------------------------------------------------
-- 2.3 与订单表结合
-- ------------------------------------------------------------
SELECT
    id,
    total_amount,
    fn_format_money(total_amount) AS 金额展示
FROM orders
ORDER BY total_amount DESC
LIMIT 5;

-- ============================================================
-- 3. 用户等级判断函数（READS SQL DATA 含查询）
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 根据用户 ID 查询其总消费额，返回等级标签
--     - READS SQL DATA：函数内含 SELECT，但不写数据
--     - 注意：函数内不能返回结果集，只能 RETURN 单值
-- ------------------------------------------------------------
DELIMITER $$

CREATE FUNCTION fn_user_level(p_uid INT)
RETURNS VARCHAR(20)
READS SQL DATA
BEGIN
    DECLARE v_total DECIMAL(12,2) DEFAULT 0;
    DECLARE v_role  VARCHAR(20);

    -- 取出角色与消费总额
    SELECT u.role, COALESCE(SUM(o.total_amount), 0)
    INTO v_role, v_total
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    WHERE u.id = p_uid
    GROUP BY u.role;

    -- 用户不存在
    IF v_role IS NULL THEN
        RETURN '不存在';
    END IF;

    -- 管理员/编辑直接返回
    IF v_role = 'admin' THEN
        RETURN '管理员';
    ELSEIF v_role = 'editor' THEN
        RETURN '编辑';
    END IF;

    -- 普通用户按消费额分级
    CASE
        WHEN v_total >= 5000 THEN RETURN '钻石';
        WHEN v_total >= 2000 THEN RETURN '黄金';
        WHEN v_total >= 500  THEN RETURN '白银';
        WHEN v_total > 0     THEN RETURN '青铜';
        ELSE RETURN '新用户';
    END CASE;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 3.2 调用：取若干用户测试
-- ------------------------------------------------------------
SELECT id, username, role, fn_user_level(id) AS 等级
FROM users
ORDER BY id
LIMIT 10;

-- ------------------------------------------------------------
-- 3.3 测试不存在的用户
-- ------------------------------------------------------------
SELECT fn_user_level(-1) AS 等级;

-- ============================================================
-- 4. 综合示例：分类完整路径函数（循环思路）
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 给定 category_id，向上回溯拼接 "父分类 > 子分类"
--     用带 label 的 WHILE 循环实现（MySQL 8 也可用 CTE 递归）
--     演示函数内的循环与字符串拼接
--     v_safe 计数器防止异常数据导致死循环
-- ------------------------------------------------------------
DELIMITER $$

CREATE FUNCTION fn_full_category_path(p_cat_id INT)
RETURNS VARCHAR(500)
READS SQL DATA
BEGIN
    DECLARE v_path  VARCHAR(500) DEFAULT '';
    DECLARE v_name  VARCHAR(100);
    DECLARE v_pid   INT;
    DECLARE v_cur   INT;
    DECLARE v_safe  INT DEFAULT 0;

    SET v_cur = p_cat_id;

    cat_loop: WHILE v_cur > 0 AND v_safe < 20 DO
        SELECT name, parent_id INTO v_name, v_pid
        FROM categories
        WHERE id = v_cur;

        -- 查不到该分类则退出
        IF v_name IS NULL THEN
            LEAVE cat_loop;
        END IF;

        -- 向上拼接：父级在前，子级在后
        IF v_path = '' THEN
            SET v_path = v_name;
        ELSE
            SET v_path = CONCAT(v_name, ' > ', v_path);
        END IF;

        SET v_cur = v_pid;
        SET v_safe = v_safe + 1;
    END WHILE;

    RETURN v_path;
END$$

DELIMITER ;

-- ------------------------------------------------------------
-- 4.2 调用：查若干分类的完整路径
-- ------------------------------------------------------------
SELECT id, name, parent_id, fn_full_category_path(id) AS 完整路径
FROM categories
ORDER BY id
LIMIT 10;

-- ============================================================
-- 5. 函数 vs 存储过程对照演示
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 函数可嵌入 SELECT；存储过程只能 CALL
--     下面这条 SELECT 同时用了 3 个自定义函数
-- ------------------------------------------------------------
SELECT
    p.id,
    p.name,
    p.price,
    fn_calc_discount_price(p.price, 0.10)     AS 九折价,
    fn_format_money(p.price)                  AS 原价格式,
    fn_full_category_path(p.category_id)      AS 分类路径
FROM products p
WHERE p.status = 'on_sale'
LIMIT 5;

-- ============================================================
-- 6. 查看与删除函数
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 查看当前库所有函数
-- ------------------------------------------------------------
SELECT routine_name, routine_type, data_access, is_deterministic
FROM information_schema.routines
WHERE routine_schema = 'ecommerce'
  AND routine_type = 'FUNCTION'
ORDER BY routine_name;

-- ------------------------------------------------------------
-- 6.2 查看某函数定义
-- ------------------------------------------------------------
SHOW CREATE FUNCTION fn_user_level\G

-- ------------------------------------------------------------
-- 6.3 删除所有演示函数
-- ------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_calc_discount_price;
DROP FUNCTION IF EXISTS fn_format_money;
DROP FUNCTION IF EXISTS fn_user_level;
DROP FUNCTION IF EXISTS fn_full_category_path;

-- ============================================================
-- 自定义函数演示完毕。
-- 关键结论：
--   1) 函数必须声明 RETURNS 与 RETURN
--   2) DETERMINISTIC / READS SQL DATA 等特性声明影响 binlog 与创建
--   3) 函数可在 SELECT 中直接使用，存储过程只能 CALL
--   4) 函数内不能返回结果集，不能 COMMIT/ROLLBACK
--   5) 纯计算用 NO SQL + DETERMINISTIC；含查询用 READS SQL DATA
-- ============================================================
