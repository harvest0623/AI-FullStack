-- ============================================================
-- 文件名称: 02-slow-query-optimization.sql
-- 文件用途: 慢查询优化演示脚本
--           1. 慢查询日志开启与查看
--           2. 构造慢查询并 EXPLAIN 分析
--           3. 索引优化：加索引前后对比
--           4. SQL 改写优化：函数包裹 / 隐式转换
--           5. 深分页优化：延迟关联 / 子查询 / 游标
--           6. 子查询改 JOIN
--           7. OR 改 UNION ALL
--           8. IN vs EXISTS 对比
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day14 - 数据库设计与性能优化/Code/02-slow-query-optimization.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. 慢查询日志
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 查看慢查询日志配置
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'slow_query_log';          -- 是否开启
SHOW VARIABLES LIKE 'slow_query_log_file';     -- 日志文件路径
SHOW VARIABLES LIKE 'long_query_time';         -- 慢阈值（秒）
SHOW VARIABLES LIKE 'log_queries_not_using_indexes';  -- 是否记录未用索引的 SQL

-- ------------------------------------------------------------
-- 1.2 开启慢查询日志（运行时，重启失效）
--     生产环境建议在 my.cnf 配置永久开启
-- ------------------------------------------------------------
-- SET GLOBAL slow_query_log = ON;
-- SET GLOBAL long_query_time = 1;
-- SET GLOBAL log_queries_not_using_indexes = ON;

-- ------------------------------------------------------------
-- 1.3 my.cnf 永久配置示例（参考）
--     [mysqld]
--     slow_query_log = 1
--     slow_query_log_file = /var/log/mysql/slow.log
--     long_query_time = 1
--     log_queries_not_using_indexes = 1
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- 1.4 用 mysqldumpslow 分析慢日志（在系统 shell 执行，非 SQL）
--     mysqldumpslow -s t -t 10 /var/log/mysql/slow.log
-- ------------------------------------------------------------

-- ============================================================
-- 2. 准备演示数据：构造一张大表用于慢查询演示
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 创建演示表 slow_demo（无索引）
--     模拟"无索引导致全表扫描"的慢查询场景
-- ------------------------------------------------------------
DROP TABLE IF EXISTS slow_demo;
CREATE TABLE slow_demo (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    amount      DECIMAL(10,2),
    status      VARCHAR(20),
    created_at  DATETIME,
    remark      VARCHAR(200)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='慢查询演示表';

-- ------------------------------------------------------------
-- 2.2 灌入测试数据（用存储过程批量插入 5 万行）
--     注意：若已有数据可跳过此步
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_fill_slow_demo;
DELIMITER $$
CREATE PROCEDURE sp_fill_slow_demo(IN p_cnt INT)
BEGIN
    DECLARE i INT DEFAULT 0;
    WHILE i < p_cnt DO
        INSERT INTO slow_demo(user_id, amount, status, created_at, remark)
        VALUES (
            FLOOR(RAND() * 1000) + 1,
            ROUND(RAND() * 1000, 2),
            ELT(1 + FLOOR(RAND() * 4), 'pending', 'paid', 'shipped', 'completed'),
            DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 365) DAY),
            CONCAT('remark_', i)
        );
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;

-- 调用：插入 5 万行（按需调整数量，数据量大效果明显）
CALL sp_fill_slow_demo(50000);
DROP PROCEDURE IF EXISTS sp_fill_slow_demo;

-- 查看数据量
SELECT COUNT(*) AS total_rows FROM slow_demo;

-- ============================================================
-- 3. 慢查询一：无索引导致全表扫描
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 查询某用户的订单（无索引，全表扫描）
--     type=ALL，rows=全表行数，Extra=Using where
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo WHERE user_id = 500;

-- 实际执行（观察耗时）
SELECT SQL_NO_CACHE COUNT(*) FROM slow_demo WHERE user_id = 500;

-- ------------------------------------------------------------
-- 3.2 加索引后再 EXPLAIN
-- ------------------------------------------------------------
CREATE INDEX idx_user_id ON slow_demo(user_id);

EXPLAIN
SELECT * FROM slow_demo WHERE user_id = 500;
-- 优化后：type=ref，rows=预估命中行数，key=idx_user_id

-- 再执行（观察耗时下降）
SELECT SQL_NO_CACHE COUNT(*) FROM slow_demo WHERE user_id = 500;

-- ============================================================
-- 4. 慢查询二：函数包裹索引列导致失效
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 查询 2025 年 7 月的订单
--     YEAR() 函数包裹 created_at，索引失效
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo
WHERE YEAR(created_at) = 2025 AND MONTH(created_at) = 7;

-- ------------------------------------------------------------
-- 4.2 先给 created_at 加索引
-- ------------------------------------------------------------
CREATE INDEX idx_created_at ON slow_demo(created_at);

-- 函数包裹仍失效
EXPLAIN
SELECT * FROM slow_demo WHERE YEAR(created_at) = 2025 AND MONTH(created_at) = 7;
-- type=ALL，key=NULL（索引失效）

-- ------------------------------------------------------------
-- 4.3 改写为范围查询，索引生效
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo
WHERE created_at >= '2025-07-01 00:00:00'
  AND created_at <  '2025-08-01 00:00:00';
-- type=range，key=idx_created_at

-- ============================================================
-- 5. 慢查询三：隐式类型转换
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 user_id 是 INT，但传字符串
--     MySQL 会把每行的 user_id 转成字符串比较，索引失效
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo WHERE user_id = '500';
-- 在某些版本/字符集下会索引失效；8.0 较新版本可能优化了

-- ------------------------------------------------------------
-- 5.2 类型匹配，索引生效
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo WHERE user_id = 500;

-- ------------------------------------------------------------
-- 5.3 status 是 VARCHAR，但传数字（更隐蔽的隐式转换）
--     若 status 列有索引，传数字会失效
-- ------------------------------------------------------------
CREATE INDEX idx_status ON slow_demo(status);

EXPLAIN
SELECT * FROM slow_demo WHERE status = 1;
-- type=ALL（隐式转换失效）

EXPLAIN
SELECT * FROM slow_demo WHERE status = 'paid';
-- type=ref（正常）

-- ============================================================
-- 6. 慢查询四：深分页优化
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 传统 LIMIT 深分页（OFFSET 大时需扫描前面所有行）
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo ORDER BY id LIMIT 10000, 10;

-- ------------------------------------------------------------
-- 6.2 优化方案 1：延迟关联
--     先用覆盖索引查 id，再 JOIN 取详情
-- ------------------------------------------------------------
EXPLAIN
SELECT s.* FROM slow_demo s
INNER JOIN (
    SELECT id FROM slow_demo ORDER BY id LIMIT 10000, 10
) t ON s.id = t.id;

-- ------------------------------------------------------------
-- 6.3 优化方案 2：子查询
--     用 WHERE id > 上次最大 id 代替 OFFSET
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo
WHERE id > (SELECT id FROM slow_demo ORDER BY id LIMIT 10000, 1)
ORDER BY id LIMIT 10;

-- ------------------------------------------------------------
-- 6.4 优化方案 3：游标分页（推荐）
--     记住上一页最后一条 id，下次查询从该 id 之后取
--     假设上一页最后 id = 10010
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo WHERE id > 10010 ORDER BY id LIMIT 10;
-- type=range，key=PRIMARY，最高效

-- ============================================================
-- 7. 慢查询五：子查询改 JOIN
-- ============================================================

-- ------------------------------------------------------------
-- 7.1 用子查询查"消费超过 1000 的用户"
--     相关子查询，每行执行一次
-- ------------------------------------------------------------
EXPLAIN
SELECT u.id, u.username
FROM users u
WHERE u.id IN (
    SELECT user_id FROM orders WHERE total_amount > 100
);

-- ------------------------------------------------------------
-- 7.2 改写为 JOIN + DISTINCT
--     通常比 IN 子查询快
-- ------------------------------------------------------------
EXPLAIN
SELECT DISTINCT u.id, u.username
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE o.total_amount > 100;

-- ------------------------------------------------------------
-- 7.3 改写为 EXISTS（相关子查询另一种写法）
--     外层表小时 EXISTS 更快
-- ------------------------------------------------------------
EXPLAIN
SELECT u.id, u.username
FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.total_amount > 100
);

-- ============================================================
-- 8. 慢查询六：OR 改 UNION ALL
-- ============================================================

-- ------------------------------------------------------------
-- 8.1 OR 查询（可能不走索引）
--     若 user_id 和 status 各有索引，OR 可能合并索引
--     但在某些场景下优化器会选择全表扫描
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo
WHERE user_id = 500 OR status = 'paid';

-- ------------------------------------------------------------
-- 8.2 改 UNION ALL，两个子查询各走各自索引
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo WHERE user_id = 500
UNION ALL
SELECT * FROM slow_demo WHERE status = 'paid' AND (user_id <> 500 OR user_id IS NULL);

-- ============================================================
-- 9. 慢查询七：避免 SELECT *
-- ============================================================

-- ------------------------------------------------------------
-- 9.1 SELECT * 会取所有列，可能回表
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo WHERE user_id = 500;

-- ------------------------------------------------------------
-- 9.2 只取需要的列，若能命中覆盖索引则无需回表
--     创建覆盖索引 (user_id, status)
-- ------------------------------------------------------------
CREATE INDEX idx_uid_status ON slow_demo(user_id, status);

EXPLAIN
SELECT user_id, status FROM slow_demo WHERE user_id = 500;
-- Extra=Using index（覆盖索引，无需回表）

-- ============================================================
-- 10. 慢查询八：JOIN 优化
-- ============================================================

-- ------------------------------------------------------------
-- 10.1 JOIN 时确保 ON 列有索引
--      orders.user_id 已有索引（ecommerce 库建表时创建）
-- ------------------------------------------------------------
EXPLAIN
SELECT u.username, o.id, o.total_amount
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.role = 'admin';

-- ------------------------------------------------------------
-- 10.2 小表驱动大表
--      users（admin 少量）驱动 orders（大表）
--      MySQL 优化器一般会自动选小表为驱动表
--      但写法上可优先过滤小表
-- ------------------------------------------------------------
EXPLAIN
SELECT u.username, o.id, o.total_amount
FROM (SELECT id, username FROM users WHERE role = 'admin') u
JOIN orders o ON o.user_id = u.id;

-- ============================================================
-- 11. 慢查询九：LIKE 左模糊
-- ============================================================

-- ------------------------------------------------------------
-- 11.1 左模糊 %xx 索引失效
-- ------------------------------------------------------------
EXPLAIN
SELECT * FROM slow_demo WHERE remark LIKE '%remark_1%';

-- ------------------------------------------------------------
-- 11.2 右模糊 xx% 可用索引（若 remark 有索引）
-- ------------------------------------------------------------
CREATE INDEX idx_remark ON slow_demo(remark);

EXPLAIN
SELECT * FROM slow_demo WHERE remark LIKE 'remark_1%';
-- type=range，可走索引

-- 左模糊仍失效
EXPLAIN
SELECT * FROM slow_demo WHERE remark LIKE '%100';

-- ============================================================
-- 12. 综合优化对比表
-- ============================================================

-- ------------------------------------------------------------
-- 12.1 汇总各场景的优化前后对比（手动观察 EXPLAIN 输出）
-- ------------------------------------------------------------
-- 场景 1：无索引 → 加索引
--   前：type=ALL, key=NULL
--   后：type=ref,  key=idx_user_id

-- 场景 2：函数包裹 → 范围查询
--   前：type=ALL, key=NULL
--   后：type=range, key=idx_created_at

-- 场景 3：隐式转换 → 类型匹配
--   前：type=ALL（status=1）
--   后：type=ref （status='paid'）

-- 场景 4：深分页 OFFSET → 游标分页
--   前：扫描 10000+10 行
--   后：type=range，扫描 10 行

-- 场景 5：子查询 → JOIN
--   前：DEPENDENT SUBQUERY
--   后：SIMPLE JOIN

-- ============================================================
-- 13. 清理演示数据（可选）
-- ============================================================
-- 若想保留演示表，注释掉以下语句
-- DROP TABLE IF EXISTS slow_demo;

-- 删除演示创建的索引（若保留表）
-- DROP INDEX idx_user_id    ON slow_demo;
-- DROP INDEX idx_created_at ON slow_demo;
-- DROP INDEX idx_status     ON slow_demo;
-- DROP INDEX idx_uid_status ON slow_demo;
-- DROP INDEX idx_remark     ON slow_demo;

-- ============================================================
-- 慢查询优化演示完毕。
-- 关键结论：
--   1) 用 EXPLAIN 看类型：至少要 range，避免 ALL
--   2) 索引列不加函数，避免隐式类型转换
--   3) 深分页用游标或延迟关联
--   4) 子查询优先改 JOIN
--   5) OR 改 UNION ALL，让各子查询走各自索引
--   6) SELECT * 改具体列，争取覆盖索引
--   7) 优化前先定位（EXPLAIN + 慢日志），优化后压测验证
-- ============================================================
