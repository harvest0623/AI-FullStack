-- ============================================================
-- 文件名称: 02-isolation-level.sql
-- 文件用途: 隔离级别演示
--           SET SESSION TRANSACTION ISOLATION LEVEL...
--           用详细注释说明如何开两个终端验证脏读/不可重复读/幻读
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day11 - 事务与锁机制/Code/02-isolation-level.sql
-- 前置条件: ecommerce 库及 accounts、orders 表已存在
-- 重要说明: 并发演示需两个数据库连接，本文件用顺序语句与注释说明
-- ============================================================

USE ecommerce;

-- ============================================================
-- 第一部分：隔离级别基础
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 查看当前隔离级别（默认 REPEATABLE-READ）
-- ------------------------------------------------------------
SELECT @@transaction_isolation AS current_isolation,
       @@global.transaction_isolation AS global_isolation;

-- ------------------------------------------------------------
-- 1.2 四种隔离级别切换语法
--     注意：SESSION 级别只影响当前连接，GLOBAL 级别影响新连接
-- ------------------------------------------------------------

-- 切换到 READ UNCOMMITTED（读未提交）
-- SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- 切换到 READ COMMITTED（读已提交，Oracle/PG 默认）
-- SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- 切换到 REPEATABLE READ（可重复读，MySQL 默认）
-- SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- 切换到 SERIALIZABLE（串行化）
-- SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- 查看切换后的级别
-- SELECT @@transaction_isolation;


-- ============================================================
-- 第二部分：脏读演示（READ UNCOMMITTED）
-- ============================================================
-- ============================================================
-- 【多终端验证方法】
-- 1. 准备两个 MySQL 客户端连接（终端 A、终端 B）
-- 2. 两个终端都执行：USE ecommerce;
-- 3. 两个终端都设置隔离级别为 READ UNCOMMITTED：
--    SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
--
-- 步骤（按顺序在两个终端交替执行）：
--   T1 终端 A: BEGIN;
--   T2 终端 A: UPDATE accounts SET balance = balance + 500 WHERE user_id = 1;
--             （不 COMMIT）
--   T3 终端 B: BEGIN;
--   T4 终端 B: SELECT balance FROM accounts WHERE user_id = 1;
--             → 能读到终端 A 未提交的 +500（脏读！）
--   T5 终端 A: ROLLBACK;
--   T6 终端 B: SELECT balance FROM accounts WHERE user_id = 1;
--             → 又变回原值（说明之前读到的是脏数据）
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 单连接模拟脏读流程（无法真正并发，仅演示语句）
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- 假设这是终端 A
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
BEGIN;
UPDATE accounts SET balance = balance + 500 WHERE user_id = 1;
-- 此时终端 B 在 READ UNCOMMITTED 下 SELECT 会读到 +500（脏读）

SELECT user_id, balance FROM accounts WHERE user_id = 1;  -- 事务内可见
ROLLBACK;  -- 回滚

-- 终端 B 再读时，又变回原值
SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- 恢复隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;


-- ============================================================
-- 第三部分：不可重复读演示（READ COMMITTED）
-- ============================================================
-- ============================================================
-- 【多终端验证方法】
-- 1. 两个终端都设置隔离级别为 READ COMMITTED：
--    SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
--
-- 步骤：
--   T1 终端 A: BEGIN;
--   T2 终端 A: SELECT balance FROM accounts WHERE user_id = 1;
--             → 假设读到 1000
--   T3 终端 B: BEGIN;
--   T4 终端 B: UPDATE accounts SET balance = 2000 WHERE user_id = 1;
--   T5 终端 B: COMMIT;
--   T6 终端 A: SELECT balance FROM accounts WHERE user_id = 1;
--             → 读到 2000（不可重复读！同一事务两次读结果不同）
--   T7 终端 A: COMMIT;
--
-- 对比 REPEATABLE READ：
--   把隔离级别改为 REPEATABLE READ 重复上述步骤
--   T6 终端 A 第二次 SELECT 仍读到 1000（可重复读）
--   因为 RR 在首次 SELECT 时生成 Read View，后续复用
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 单连接演示 RC 下的不可重复读
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id = 1;

SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

BEGIN;
-- 第一次读
SELECT user_id, balance FROM accounts WHERE user_id = 1;
-- 假设此时另一个事务修改并提交了 balance
-- 这里用本事务外的 UPDATE 模拟（autocommit 模式下立即提交）
UPDATE accounts SET balance = balance + 100 WHERE user_id = 1;
-- 第二次读（在 RC 下会读到最新已提交值，发生不可重复读）
SELECT user_id, balance FROM accounts WHERE user_id = 1;
ROLLBACK;

-- 注意：上面 ROLLBACK 会撤销 BEGIN 内的所有操作
-- 但因 UPDATE 是在事务内执行的，ROLLBACK 会撤销它
-- 真正的不可重复读需要两个连接，这里仅演示语句
SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- 恢复隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- ------------------------------------------------------------
-- 3.2 单连接演示 RR 下的可重复读
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- RR 是默认级别，无需切换
BEGIN;
-- 第一次读（生成 Read View）
SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- 模拟其他事务修改（在事务外用 autocommit 自动提交）
-- UPDATE accounts SET balance = balance + 100 WHERE user_id = 1;
-- COMMIT;

-- 第二次读（RR 复用 Read View，仍读到旧值）
SELECT user_id, balance FROM accounts WHERE user_id = 1;
COMMIT;

SELECT user_id, balance FROM accounts WHERE user_id = 1;


-- ============================================================
-- 第四部分：幻读演示（REPEATABLE READ）
-- ============================================================
-- ============================================================
-- 【多终端验证方法】
-- 1. 两个终端都保持 REPEATABLE READ（默认）
--
-- 步骤：
--   T1 终端 A: BEGIN;
--   T2 终端 A: SELECT COUNT(*) FROM orders WHERE user_id = 1;
--             → 假设 5 行
--   T3 终端 B: BEGIN;
--   T4 终端 B: INSERT INTO orders (..., user_id, ...) VALUES (...);
--   T5 终端 B: COMMIT;
--   T6 终端 A: SELECT COUNT(*) FROM orders WHERE user_id = 1;
--             → RR 下仍读到 5（快照读，不幻读）
--   T7 终端 A: SELECT * FROM orders WHERE user_id = 1 FOR UPDATE;
--             → 当前读，会读到 6 行（FOR UPDATE 触发当前读）
--   T8 终端 A: COMMIT;
--
-- 结论：
--   - RR 的快照读（普通 SELECT）通过 MVCC 避免幻读
--   - RR 的当前读（FOR UPDATE / LOCK IN SHARE MODE）通过间隙锁避免幻读
--   - 但若先快照读再当前读，可能"感觉"到幻读（行数变了）
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 单连接演示 RR 快照读避免幻读
-- ------------------------------------------------------------
SELECT COUNT(*) AS order_count_user1 FROM orders WHERE user_id = 1;

BEGIN;
-- 第一次查询（快照读，生成 Read View）
SELECT COUNT(*) AS first_read FROM orders WHERE user_id = 1;

-- 假设另一事务插入了新订单（这里用本事务内 INSERT 模拟）
-- INSERT INTO orders (user_id, total_amount, status) VALUES (1, 99.00, 'pending');

-- 第二次查询（RR 复用 Read View，仍读到旧值）
SELECT COUNT(*) AS second_read FROM orders WHERE user_id = 1;
COMMIT;

SELECT COUNT(*) AS final_count FROM orders WHERE user_id = 1;

-- ------------------------------------------------------------
-- 4.2 当前读 vs 快照读对比
--     快照读：普通 SELECT，走 MVCC
--     当前读：FOR UPDATE / LOCK IN SHARE MODE / UPDATE / DELETE
-- ============================================================
-- 【多终端验证】
--   T1 终端 A: BEGIN;
--   T2 终端 A: SELECT * FROM orders WHERE user_id = 1;  -- 快照读，5 行
--   T3 终端 B: INSERT INTO orders (..., user_id, ...) VALUES (...);
--   T4 终端 B: COMMIT;
--   T5 终端 A: SELECT * FROM orders WHERE user_id = 1;          -- 仍 5 行
--   T6 终端 A: SELECT * FROM orders WHERE user_id = 1 FOR UPDATE;  -- 当前读，6 行
--   T7 终端 A: COMMIT;
-- ============================================================


-- ============================================================
-- 第五部分：SERIALIZABLE 串行化演示
-- ============================================================
-- ============================================================
-- 【多终端验证方法】
-- 1. 两个终端都设置隔离级别为 SERIALIZABLE：
--    SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;
--
-- 步骤：
--   T1 终端 A: BEGIN;
--   T2 终端 A: SELECT * FROM accounts WHERE user_id = 1;
--             （隐式加共享锁）
--   T3 终端 B: BEGIN;
--   T4 终端 B: UPDATE accounts SET balance = balance + 100 WHERE user_id = 1;
--             → 阻塞等待（被 A 的共享锁阻塞）
--   T5 终端 A: COMMIT;  （释放锁）
--   T6 终端 B: 此时 UPDATE 才执行成功
--   T7 终端 B: COMMIT;
--
-- 结论：SERIALIZABLE 下所有读隐式加共享锁，写必须等读释放
--       完全串行，无并发问题但性能最差
-- ============================================================


-- ============================================================
-- 第六部分：MVCC 验证（Read View）
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 查看事务 ID（每个事务有唯一 trx_id）
--     MySQL 8.0 可通过 information_schema.innodb_trx 查看活跃事务
-- ------------------------------------------------------------
SELECT trx_id, trx_state, trx_started, trx_query
FROM information_schema.innodb_trx
ORDER BY trx_started;

-- ------------------------------------------------------------
-- 6.2 单连接演示 MVCC 版本链
--     同一事务内多次读同一行，RR 下结果一致
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id = 1;

BEGIN;
-- 第一次读（生成 Read View，记下当前活跃事务列表）
SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- 此时若另一事务修改了该行并提交，本事务的 Read View 不会更新
-- 仍读到旧版本（通过 undo log 历史版本链）

-- 第二次读（复用 Read View，结果一致）
SELECT user_id, balance FROM accounts WHERE user_id = 1;
COMMIT;

-- ------------------------------------------------------------
-- 6.3 RC vs RR 的 Read View 生成时机对比
-- ============================================================
-- 隔离级别    | Read View 生成时机           | 效果
-- ----------- | ---------------------------- | ------------------------
-- RC          | 每条 SELECT 都生成新 Read View | 能读到最新已提交数据
-- RR          | 事务首次 SELECT 生成，后续复用 | 事务内读取结果一致
-- ============================================================


-- ============================================================
-- 第七部分：综合实验（开两个终端执行）
-- ============================================================
-- ============================================================
-- 实验 1：验证 RC 的不可重复读
-- 终端 A：SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- 终端 B：SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
--
-- 终端 A                          | 终端 B
-- --------------------------------|--------------------------
-- BEGIN;                          |
-- SELECT balance FROM accounts    |
-- WHERE user_id = 1;  -- 1000     |
--                                 | BEGIN;
--                                 | UPDATE accounts SET balance=2000 WHERE user_id=1;
--                                 | COMMIT;
-- SELECT balance FROM accounts    |
-- WHERE user_id = 1;  -- 2000     |  ← 不可重复读！
-- COMMIT;                         |
--
-- 恢复数据：
-- UPDATE accounts SET balance = 1000 WHERE user_id = 1;
--
-- ----------------------------------------------------------------
-- 实验 2：验证 RR 的可重复读
-- 终端 A：保持默认 REPEATABLE READ
-- 终端 B：保持默认 REPEATABLE READ
--
-- 终端 A                          | 终端 B
-- --------------------------------|--------------------------
-- BEGIN;                          |
-- SELECT balance FROM accounts    |
-- WHERE user_id = 1;  -- 1000     |
--                                 | BEGIN;
--                                 | UPDATE accounts SET balance=2000 WHERE user_id=1;
--                                 | COMMIT;
-- SELECT balance FROM accounts    |
-- WHERE user_id = 1;  -- 1000     |  ← 可重复读！（读旧版本）
-- COMMIT;                         |
--
-- COMMIT 后再读：2000（新事务生成新 Read View）
-- SELECT balance FROM accounts WHERE user_id = 1;  -- 2000
--
-- 恢复数据：
-- UPDATE accounts SET balance = 1000 WHERE user_id = 1;
--
-- ----------------------------------------------------------------
-- 实验 3：验证 RR 的幻读避免（快照读）
-- 终端 A：保持默认 REPEATABLE READ
-- 终端 B：保持默认 REPEATABLE READ
--
-- 终端 A                          | 终端 B
-- --------------------------------|--------------------------
-- BEGIN;                          |
-- SELECT COUNT(*) FROM orders     |
-- WHERE user_id = 1;  -- 5        |
--                                 | BEGIN;
--                                 | INSERT INTO orders (user_id, total_amount, status)
--                                 | VALUES (1, 99.00, 'pending');
--                                 | COMMIT;
-- SELECT COUNT(*) FROM orders     |
-- WHERE user_id = 1;  -- 5        |  ← 不幻读！（快照读）
-- COMMIT;                         |
--
-- COMMIT 后再读：6（新事务）
-- SELECT COUNT(*) FROM orders WHERE user_id = 1;  -- 6
--
-- 恢复数据：删除刚插入的订单
-- DELETE FROM orders WHERE user_id = 1 ORDER BY id DESC LIMIT 1;
-- ============================================================


-- ============================================================
-- 小结
-- ============================================================
-- 通过本脚本可观察到：
-- 1. MySQL 默认 REPEATABLE READ，通过 MVCC 实现可重复读
-- 2. READ UNCOMMITTED 会脏读，几乎不用
-- 3. READ COMMITTED 有不可重复读，Oracle/PG 默认此级别
-- 4. RR 通过间隙锁 + MVCC 基本避免幻读
-- 5. SERIALIZABLE 完全串行，性能最差
--
-- 关键：理解 Read View 的生成时机
--   RC：每条 SELECT 生成新 Read View
--   RR：事务首次 SELECT 生成，后续复用
--
-- 注意：真正的并发演示需要两个数据库连接
-- 请按注释中的步骤开两个终端交替执行
-- ============================================================
