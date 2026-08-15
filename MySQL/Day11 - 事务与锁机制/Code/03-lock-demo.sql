-- ============================================================
-- 文件名称: 03-lock-demo.sql
-- 文件用途: 锁机制演示
--           FOR UPDATE 排他锁、LOCK IN SHARE MODE 共享锁
--           行锁 vs 表锁、间隙锁、乐观锁 version 方案
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day11 - 事务与锁机制/Code/03-lock-demo.sql
-- 前置条件: ecommerce 库及 accounts 表已存在
-- 重要说明: 锁演示需两个数据库连接，本文件用顺序语句与注释说明
-- ============================================================

USE ecommerce;

-- ============================================================
-- 第一部分：FOR UPDATE 排他锁演示
-- ============================================================
-- ============================================================
-- 【多终端验证方法】
-- 1. 准备两个 MySQL 客户端连接（终端 A、终端 B）
-- 2. 两个终端都执行：USE ecommerce;
--
-- 步骤：
--   T1 终端 A: BEGIN;
--   T2 终端 A: SELECT balance FROM accounts WHERE user_id = 1 FOR UPDATE;
--             （对 user_id=1 加排他锁 X）
--   T3 终端 B: BEGIN;
--   T4 终端 B: SELECT balance FROM accounts WHERE user_id = 1 FOR UPDATE;
--             → 阻塞等待（被 A 的 X 锁阻塞）
--   T5 终端 A: COMMIT;  （释放锁）
--   T6 终端 B: 此时查询返回（获得锁）
--   T7 终端 B: COMMIT;
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 单连接演示 FOR UPDATE 基本用法
--     FOR UPDATE 必须在事务内，否则锁立即释放
-- ------------------------------------------------------------

-- 确保所有 user_id 都有索引（避免退化为表锁）
-- 假设 accounts 表的 user_id 已建索引（Day10 已建或脚本动态建）
SHOW INDEX FROM accounts;

-- 若 user_id 无索引，先建一个
-- CREATE INDEX idx_accounts_user_id ON accounts(user_id);

SELECT user_id, balance FROM accounts WHERE user_id = 1;

BEGIN;
-- 加排他锁
SELECT balance FROM accounts WHERE user_id = 1 FOR UPDATE;
-- 此时其他事务对 user_id=1 的 FOR UPDATE / UPDATE / DELETE 都会阻塞
SELECT user_id, balance FROM accounts WHERE user_id = 1;
COMMIT;  -- 释放锁

-- ------------------------------------------------------------
-- 1.2 FOR UPDATE 转账场景（完整流程）
-- ============================================================
-- 【多终端验证】
--   终端 A 执行转账事务，终端 B 尝试同时转账，应阻塞
--
--   终端 A                          | 终端 B
--   --------------------------------|--------------------------
--   BEGIN;                          |
--   SELECT balance FROM accounts    |
--   WHERE user_id = 1 FOR UPDATE;   |
--   SELECT balance FROM accounts    |
--   WHERE user_id = 2 FOR UPDATE;   |
--                                  | BEGIN;
--                                  | SELECT balance FROM accounts
--                                  | WHERE user_id = 1 FOR UPDATE;
--                                  | → 阻塞等待 A 释放
--   UPDATE accounts SET balance =   |
--     balance - 100 WHERE user_id=1;|
--   UPDATE accounts SET balance =   |
--     balance + 100 WHERE user_id=2;|
--   COMMIT;                         | → A 提交后 B 获得锁
--                                  | ... 继续 B 的转账
--                                  | COMMIT;
-- ============================================================

-- ------------------------------------------------------------
-- 1.3 单连接演示转账流程
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

BEGIN;
-- 按 user_id 升序加锁（避免死锁）
SELECT balance FROM accounts WHERE user_id = 1 FOR UPDATE;
SELECT balance FROM accounts WHERE user_id = 2 FOR UPDATE;

-- 应用层判断余额后执行
UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE user_id = 2;

COMMIT;

-- 验证
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);


-- ============================================================
-- 第二部分：LOCK IN SHARE MODE 共享锁演示
-- ============================================================
-- ============================================================
-- 【多终端验证方法】
--   终端 A                          | 终端 B
--   --------------------------------|--------------------------
--   BEGIN;                          |
--   SELECT balance FROM accounts    |
--   WHERE user_id = 1               |
--   LOCK IN SHARE MODE;             |  （加共享锁 S）
--                                  | BEGIN;
--                                  | SELECT balance FROM accounts
--                                  | WHERE user_id = 1
--                                  | LOCK IN SHARE MODE;
--                                  | → 成功返回（S 锁兼容）
--                                  |
--                                  | UPDATE accounts SET balance=balance+100
--                                  | WHERE user_id = 1;
--                                  | → 阻塞等待（X 锁与 S 锁互斥）
--   COMMIT;                         | → A 释放 S 锁后 B 的 UPDATE 执行
--                                  | COMMIT;
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 单连接演示 LOCK IN SHARE MODE
--     MySQL 8.0 推荐 FOR SHARE 语法
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id = 1;

BEGIN;
-- 加共享锁（8.0 推荐用 FOR SHARE）
SELECT balance FROM accounts WHERE user_id = 1 FOR SHARE;
-- 等价：SELECT balance FROM accounts WHERE user_id = 1 LOCK IN SHARE MODE;

-- 此时其他事务可以读（加 S 锁），但不能修改（X 锁被阻塞）
SELECT user_id, balance FROM accounts WHERE user_id = 1;
COMMIT;  -- 释放锁

-- ------------------------------------------------------------
-- 2.2 共享锁 vs 排他锁兼容性
-- ============================================================
-- 锁兼容矩阵：
--           | IS  | IX  | S   | X
-- ----------|-----|-----|-----|-----
-- IS        | ✅  | ✅  | ✅  | ❌
-- IX        | ✅  | ✅  | ❌  | ❌
-- S         | ✅  | ❌  | ✅  | ❌
-- X         | ❌  | ❌  | ❌  | ❌
--
-- 结论：
--   - S 锁之间兼容（多个事务可同时读）
--   - X 锁与任何锁互斥（写独占）
--   - 意向锁之间互相兼容
-- ============================================================


-- ============================================================
-- 第三部分：行锁 vs 表锁
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 InnoDB 行锁基于索引
--     WHERE 走索引 → 行锁
--     WHERE 不走索引 → 退化为表锁
-- ------------------------------------------------------------

-- 确保 user_id 有索引
SHOW INDEX FROM accounts;

-- ------------------------------------------------------------
-- 3.2 行锁演示：WHERE 走索引
-- ============================================================
-- 【多终端验证】
--   终端 A                          | 终端 B
--   --------------------------------|--------------------------
--   BEGIN;                          |
--   UPDATE accounts SET balance =   |
--     balance + 100                 |
--   WHERE user_id = 1;              |  （行锁，只锁 user_id=1）
--                                  | BEGIN;
--                                  | UPDATE accounts SET balance = balance + 100
--                                  | WHERE user_id = 2;
--                                  | → 成功（不同行不互斥）
--                                  | COMMIT;
--   COMMIT;                         |
-- ============================================================

-- ------------------------------------------------------------
-- 3.3 表锁演示：WHERE 不走索引
--     若 user_id 无索引，UPDATE 会锁整张表
--     此时其他事务更新任何行都会阻塞
-- ============================================================
-- 【多终端验证】（先 DROP 索引模拟无索引场景）
--   ALTER TABLE accounts DROP INDEX idx_accounts_user_id;
--
--   终端 A                          | 终端 B
--   --------------------------------|--------------------------
--   BEGIN;                          |
--   UPDATE accounts SET balance =   |
--     balance + 100                 |
--   WHERE user_id = 1;              |  （表锁！锁整张表）
--                                  | BEGIN;
--                                  | UPDATE accounts SET balance = balance + 100
--                                  | WHERE user_id = 2;
--                                  | → 阻塞（即使不同行）
--                                  | → 等待 A 释放表锁
--   COMMIT;                         | → B 才能执行
--                                  | COMMIT;
--
--   恢复索引：
--   CREATE INDEX idx_accounts_user_id ON accounts(user_id);
-- ============================================================

-- ------------------------------------------------------------
-- 3.4 单连接演示行锁（基于索引）
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

BEGIN;
-- 锁 user_id=1（行锁）
UPDATE accounts SET balance = balance + 10 WHERE user_id = 1;
-- 其他事务可以同时更新 user_id=2（不互斥）
SELECT user_id, balance FROM accounts WHERE user_id = 1;
COMMIT;

-- 恢复
UPDATE accounts SET balance = balance - 10 WHERE user_id = 1;


-- ============================================================
-- 第四部分：间隙锁 Gap Lock 演示（RR 级别）
-- ============================================================
-- ============================================================
-- 【多终端验证方法】
-- 前提：保持默认 REPEATABLE READ 隔离级别
--
-- 步骤：
--   T1 终端 A: BEGIN;
--   T2 终端 A: SELECT * FROM accounts WHERE user_id BETWEEN 5 AND 10 FOR UPDATE;
--             （加临键锁，锁住区间 (已存在的值], 以及间隙）
--             假设 user_id=5 和 user_id=10 存在，锁住 (5, 10] 与间隙
--   T3 终端 B: BEGIN;
--   T4 终端 B: INSERT INTO accounts (user_id, balance) VALUES (7, 1000);
--             → 阻塞！间隙锁防止插入
--   T5 终端 A: COMMIT;
--   T6 终端 B: 此时 INSERT 才成功
--   T7 终端 B: ROLLBACK;  （撤销测试数据）
--
-- 结论：RR 级别下，范围查询的 FOR UPDATE 会加间隙锁
--       防止其他事务在区间内插入，避免幻读
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 单连接演示间隙锁（无法真正演示阻塞，仅说明）
-- ------------------------------------------------------------

-- 确保 RR 级别
SELECT @@transaction_isolation;

-- 假设 accounts 表有 user_id = 1, 2, 3, 4, 5
SELECT user_id, balance FROM accounts ORDER BY user_id;

BEGIN;
-- 范围查询加 FOR UPDATE，触发间隙锁
-- 假设 user_id=3 和 user_id=5 存在，会锁住 (3, 5] 与间隙 (3, 5)
SELECT * FROM accounts WHERE user_id BETWEEN 3 AND 5 FOR UPDATE;

-- 此时其他事务无法 INSERT user_id=4（落在间隙内）
-- INSERT INTO accounts (user_id, balance) VALUES (4, 1000);  → 阻塞

COMMIT;  -- 释放间隙锁

-- ------------------------------------------------------------
-- 4.2 间隙锁只在 RR 级别生效
--     RC 级别无间隙锁，允许插入
-- ============================================================
-- 【验证方法】
--   两个终端都设置：SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
--   重复上述步骤，终端 B 的 INSERT 不会阻塞
-- ============================================================


-- ============================================================
-- 第五部分：意向锁演示
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 意向锁是表级锁，加行锁前自动加
--     作用：快速判断"是否有事务在表内加了行锁"
-- ------------------------------------------------------------

-- 查看锁信息（8.0 推荐 performance_schema.data_locks）
-- 在另一终端执行 FOR UPDATE 后，本终端查看锁

BEGIN;
SELECT balance FROM accounts WHERE user_id = 1 FOR UPDATE;

-- 查看当前事务持有的锁（在另一个终端执行更直观）
SELECT * FROM performance_schema.data_locks
WHERE OBJECT_SCHEMA = 'ecommerce' AND OBJECT_NAME = 'accounts';

COMMIT;

-- ------------------------------------------------------------
-- 5.2 意向锁类型
--     IS（意向共享）：准备加行级 S 锁前
--     IX（意向排他）：准备加行级 X 锁前
--     意向锁之间互相兼容，与表级 S/X 锁互斥
-- ============================================================


-- ============================================================
-- 第六部分：乐观锁 version 方案
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 为 accounts 表添加 version 字段
--     乐观锁核心：更新时检查版本号
-- ------------------------------------------------------------

-- 检查是否已有 version 列
SHOW COLUMNS FROM accounts LIKE 'version';

-- 若无则添加（若已存在则跳过）
ALTER TABLE accounts ADD COLUMN version INT NOT NULL DEFAULT 0;

-- 初始化 version
UPDATE accounts SET version = 0 WHERE version IS NULL OR version = 0;

SELECT user_id, balance, version FROM accounts WHERE user_id IN (1, 2);

-- ------------------------------------------------------------
-- 6.2 乐观锁转账流程
--     第一步：读取余额与版本号
--     第二步：应用层判断余额
--     第三步：带版本号更新（CAS）
--     第四步：检查 affected_rows，为 0 则重试
-- ------------------------------------------------------------

-- 第一步：读取
SELECT user_id, balance, version FROM accounts WHERE user_id = 1;
-- 假设返回 balance=900, version=0

-- 第二步：应用层判断余额 >= 100（此处用变量模拟）
SET @expected_version = 0;
SET @transfer_amount = 100;

-- 第三步：带版本号更新（CAS：Compare And Swap）
UPDATE accounts
SET balance = balance - @transfer_amount, version = version + 1
WHERE user_id = 1 AND version = @expected_version;
-- 若 affected_rows = 1，更新成功
-- 若 affected_rows = 0，说明版本变了（其他事务先更新），需重试

-- 查看更新结果
SELECT user_id, balance, version FROM accounts WHERE user_id = 1;

-- ------------------------------------------------------------
-- 6.3 乐观锁失败重试模拟
-- ============================================================
-- 【多终端验证】
--   终端 A                          | 终端 B
--   --------------------------------|--------------------------
--   SELECT balance, version FROM    |
--   accounts WHERE user_id = 1;     |
--   → balance=800, version=1        |
--                                  | SELECT balance, version FROM
--                                  | accounts WHERE user_id = 1;
--                                  | → balance=800, version=1
--                                  | UPDATE accounts SET balance=balance-100,
--                                  |   version=version+1
--                                  | WHERE user_id=1 AND version=1;
--                                  | → 成功，version 变 2
--   UPDATE accounts SET             |
--     balance=balance-100,          |
--     version=version+1             |
--   WHERE user_id=1 AND version=1;  |
--   → affected_rows=0（失败！）     |
--   → 需重试：重新读 balance, version
--   → 用新版本号再次 UPDATE
-- ============================================================

-- ------------------------------------------------------------
-- 6.4 乐观锁完整重试逻辑（用存储过程模拟）
--     实际应用中在应用层实现重试
-- ------------------------------------------------------------
DELIMITER //

DROP PROCEDURE IF EXISTS optimistic_transfer //
CREATE PROCEDURE optimistic_transfer(
  IN p_from_user_id INT,
  IN p_to_user_id INT,
  IN p_amount DECIMAL(10,2),
  IN p_max_retry INT
)
BEGIN
  DECLARE v_retry_count INT DEFAULT 0;
  DECLARE v_current_version INT;
  DECLARE v_current_balance DECIMAL(10,2);
  DECLARE v_affected INT;

  retry_loop: LOOP
    -- 读取当前余额与版本号
    SELECT balance, version INTO v_current_balance, v_current_version
    FROM accounts WHERE user_id = p_from_user_id;

    -- 判断余额是否足够
    IF v_current_balance < p_amount THEN
      SELECT CONCAT('余额不足: ', v_current_balance, ' < ', p_amount) AS error;
      LEAVE retry_loop;
    END IF;

    -- 尝试 CAS 更新
    UPDATE accounts
    SET balance = balance - p_amount, version = version + 1
    WHERE user_id = p_from_user_id AND version = v_current_version;

    SET v_affected = ROW_COUNT();

    IF v_affected = 1 THEN
      -- 成功，给收款方加款
      UPDATE accounts
      SET balance = balance + p_amount, version = version + 1
      WHERE user_id = p_to_user_id;

      SELECT '转账成功' AS result, v_retry_count AS retries;
      LEAVE retry_loop;
    ELSE
      -- 失败，重试
      SET v_retry_count = v_retry_count + 1;
      IF v_retry_count >= p_max_retry THEN
        SELECT CONCAT('重试 ', p_max_retry, ' 次仍失败') AS error;
        LEAVE retry_loop;
      END IF;
    END IF;
  END LOOP;
END //

DELIMITER ;

-- ------------------------------------------------------------
-- 6.5 调用乐观锁转账存储过程
-- ------------------------------------------------------------

-- 查看转账前
SELECT user_id, balance, version FROM accounts WHERE user_id IN (1, 2);

-- 调用：用户 1 给用户 2 转 50 元，最多重试 3 次
CALL optimistic_transfer(1, 2, 50.00, 3);

-- 查看转账后
SELECT user_id, balance, version FROM accounts WHERE user_id IN (1, 2);

-- 清理存储过程
DROP PROCEDURE IF EXISTS optimistic_transfer;


-- ============================================================
-- 第七部分：死锁演示
-- ============================================================
-- ============================================================
-- 【多终端验证方法】
--   终端 A                          | 终端 B
--   --------------------------------|--------------------------
--   BEGIN;                          | BEGIN;
--   UPDATE accounts SET             |
--   balance=balance+100             |
--   WHERE user_id=1;  -- 锁 id=1    |
--                                  | UPDATE accounts SET
--                                  |   balance=balance+100
--                                  | WHERE user_id=2;  -- 锁 id=2
--   UPDATE accounts SET             |
--   balance=balance+100             |
--   WHERE user_id=2;                |
--   → 阻塞（等 B 释放 id=2）        |
--                                  | UPDATE accounts SET
--                                  |   balance=balance+100
--                                  | WHERE user_id=1;
--                                  | → 阻塞（等 A 释放 id=1）
--   → 死锁！InnoDB 检测后回滚一方
--   → 一方收到：ERROR 1213 (40001): Deadlock found
-- ============================================================

-- ------------------------------------------------------------
-- 7.1 避免死锁的实践
--     1. 固定加锁顺序（如按 user_id 升序）
--     2. 缩短事务（持锁时间越短越好）
--     3. 降低隔离级别（RC 比 RR 间隙锁少）
--     4. 合理索引（避免表锁）
--     5. 应用层重试（捕获 1213 错误后重试）
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- 7.2 查看死锁信息
-- ------------------------------------------------------------

-- 查看最近一次死锁详情
SHOW ENGINE INNODB STATUS\G
-- 输出中 "LATEST DETECTED DEADLOCK" 段含死锁详情

-- 查看锁等待情况
SELECT * FROM performance_schema.data_lock_waits;

-- 查看当前锁信息
SELECT * FROM performance_schema.data_locks
WHERE OBJECT_SCHEMA = 'ecommerce';


-- ============================================================
-- 第八部分：8.0 新特性 NOWAIT / SKIP LOCKED
-- ============================================================

-- ------------------------------------------------------------
-- 8.1 FOR UPDATE NOWAIT：行已被锁时不阻塞，立即报错
--     适合"抢锁失败立即返回"的场景
-- ------------------------------------------------------------

-- 假设另一终端已锁 user_id=1
-- SELECT balance FROM accounts WHERE user_id = 1 FOR UPDATE NOWAIT;
-- → ERROR 3572 (HY000): Statement aborted. Lock wait time(s) exceeded.

-- ------------------------------------------------------------
-- 8.2 FOR UPDATE SKIP LOCKED：跳过已锁定的行
--     适合"任务队列"场景，跳过被其他 worker 锁定的任务
-- ------------------------------------------------------------

-- 假设 user_id=1 被锁，user_id=2 未锁
-- SELECT balance FROM accounts WHERE user_id IN (1, 2) FOR UPDATE SKIP LOCKED;
-- → 只返回 user_id=2（跳过被锁的 user_id=1）

-- ------------------------------------------------------------
-- 8.3 单连接演示（无阻塞场景）
-- ------------------------------------------------------------

BEGIN;
SELECT user_id, balance FROM accounts WHERE user_id = 1 FOR UPDATE NOWAIT;
COMMIT;

BEGIN;
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2) FOR UPDATE SKIP LOCKED;
COMMIT;


-- ============================================================
-- 第九部分：清理与恢复
-- ============================================================

-- ------------------------------------------------------------
-- 9.1 恢复 accounts 表数据（如需）
--     确保转账演示后的数据恢复到初始状态
-- ------------------------------------------------------------

-- 查看当前状态
SELECT user_id, balance, version FROM accounts ORDER BY user_id;

-- 若 version 字段是本脚本添加的，可保留或删除
-- ALTER TABLE accounts DROP COLUMN version;

-- ------------------------------------------------------------
-- 9.2 确保隔离级别恢复默认
-- ------------------------------------------------------------
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SELECT @@transaction_isolation;


-- ============================================================
-- 小结
-- ============================================================
-- 通过本脚本可观察到：
-- 1. FOR UPDATE 加排他锁 X，LOCK IN SHARE MODE / FOR SHARE 加共享锁 S
-- 2. InnoDB 行锁基于索引，无索引退化为表锁
-- 3. RR 级别下范围查询会加间隙锁，防止幻读
-- 4. 乐观锁用 version + CAS 实现，适合读多写少
-- 5. 死锁通过固定加锁顺序 + 缩短事务避免
-- 6. 8.0 的 NOWAIT / SKIP LOCKED 提供更灵活的锁控制
--
-- 关键：锁演示需要两个数据库连接
-- 请按注释中的步骤开两个终端交替执行，观察阻塞与释放
-- ============================================================
