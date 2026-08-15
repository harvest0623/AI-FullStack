-- ============================================================
-- 文件名称: 01-transaction-basic.sql
-- 文件用途: 事务基础演示
--           BEGIN/COMMIT/ROLLBACK、SAVEPOINT、转账事务
--           在 accounts 表模拟，验证 ROLLBACK 后余额不变
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day11 - 事务与锁机制/Code/01-transaction-basic.sql
-- 前置条件: ecommerce 库及 accounts 表已存在
-- 说明: 单 SQL 文件无法真正并发，用顺序语句模拟事务流程
-- ============================================================

USE ecommerce;

-- ============================================================
-- 第一部分：autocommit 自动提交
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 查看自动提交设置（默认 ON）
--     autocommit=1 时，每条 SQL 自动包裹成事务并立即提交
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'autocommit';

-- ------------------------------------------------------------
-- 1.2 演示 autocommit=1：单条 UPDATE 自动提交，无法回滚
--     先记下当前余额
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

-- 自动提交模式：UPDATE 直接生效
-- UPDATE accounts SET balance = balance + 1 WHERE user_id = 1;
-- 即使后面执行 ROLLBACK 也无效（因为已经提交了）
-- ROLLBACK;

-- 恢复余额（如果上面执行了）
-- UPDATE accounts SET balance = balance - 1 WHERE user_id = 1;

SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);


-- ============================================================
-- 第二部分：BEGIN / COMMIT / ROLLBACK 基础
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 演示 COMMIT：事务内修改后提交，修改持久化
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id = 1;

BEGIN;
UPDATE accounts SET balance = balance + 100 WHERE user_id = 1;
-- 事务内查询：已生效（当前事务可见自己的修改）
SELECT user_id, balance FROM accounts WHERE user_id = 1;
COMMIT;

-- 提交后查询：仍然生效
SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- 恢复原值
UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;
SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- ------------------------------------------------------------
-- 2.2 演示 ROLLBACK：事务内修改后回滚，修改撤销
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id = 1;

BEGIN;
UPDATE accounts SET balance = balance + 500 WHERE user_id = 1;
-- 事务内查询：已生效
SELECT user_id, balance FROM accounts WHERE user_id = 1;
ROLLBACK;

-- 回滚后查询：恢复原值（验证 ROLLBACK 后余额不变）
SELECT user_id, balance FROM accounts WHERE user_id = 1;


-- ============================================================
-- 第三部分：SAVEPOINT 保存点
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 SAVEPOINT 演示：部分回滚
--     场景：一个事务内分步操作，某一步失败时只回滚到保存点
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

BEGIN;

-- 第一步：给 user_id=1 加 100
UPDATE accounts SET balance = balance + 100 WHERE user_id = 1;
SAVEPOINT sp1;  -- 设保存点 sp1

-- 第二步：给 user_id=2 加 200
UPDATE accounts SET balance = balance + 200 WHERE user_id = 2;
SAVEPOINT sp2;  -- 设保存点 sp2

-- 第三步：给 user_id=1 再加 300
UPDATE accounts SET balance = balance + 300 WHERE user_id = 1;

-- 查看当前事务内状态
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

-- 假设第三步操作有问题，回滚到 sp2（保留第一步和第二步）
ROLLBACK TO SAVEPOINT sp2;

-- 查看：第三步撤销，第一步和第二步保留
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

-- 还可以继续回滚到 sp1
ROLLBACK TO SAVEPOINT sp1;

-- 查看：第二步也撤销，只剩第一步
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

-- 最终决定整体回滚
ROLLBACK;

-- 验证：所有修改撤销
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

-- ------------------------------------------------------------
-- 3.2 SAVEPOINT 配合 COMMIT：部分回滚后提交剩余
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id = 1;

BEGIN;
UPDATE accounts SET balance = balance + 50 WHERE user_id = 1;
SAVEPOINT sp_before_risky;

-- 假设这一步有风险
UPDATE accounts SET balance = balance + 9999 WHERE user_id = 1;

-- 发现不对，回滚到 sp_before_risky
ROLLBACK TO SAVEPOINT sp_before_risky;

-- 提交保留的部分
COMMIT;

-- 验证：只 +50 生效，+9999 被回滚
SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- 恢复
UPDATE accounts SET balance = balance - 50 WHERE user_id = 1;


-- ============================================================
-- 第四部分：转账事务完整演示
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 经典转账：用户 1 给用户 2 转 200 元
--     关键：两条 UPDATE 在同一事务，要么全成功要么全失败
-- ------------------------------------------------------------
SELECT user_id, balance,
       (SELECT SUM(balance) FROM accounts WHERE user_id IN (1, 2)) AS total_balance
FROM accounts WHERE user_id IN (1, 2);

BEGIN;

-- 扣款：用户 1 减 200
UPDATE accounts SET balance = balance - 200 WHERE user_id = 1;
-- 加款：用户 2 加 200
UPDATE accounts SET balance = balance + 200 WHERE user_id = 2;

COMMIT;

-- 验证：转账前后总金额不变
SELECT user_id, balance,
       (SELECT SUM(balance) FROM accounts WHERE user_id IN (1, 2)) AS total_balance
FROM accounts WHERE user_id IN (1, 2);

-- ------------------------------------------------------------
-- 4.2 转账失败回滚演示：模拟扣款成功后加款失败
--     单文件无法真正"失败"，用显式 ROLLBACK 模拟
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

BEGIN;

-- 扣款成功
UPDATE accounts SET balance = balance - 200 WHERE user_id = 1;
SELECT user_id, balance FROM accounts WHERE user_id = 1;  -- 事务内可见已扣

-- 假设加款时出错（这里用显式 ROLLBACK 模拟异常）
-- 实际场景：网络中断、约束冲突、应用层抛异常等
ROLLBACK;

-- 验证：扣款也被撤销，余额恢复
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

-- ------------------------------------------------------------
-- 4.3 完整转账事务（带余额检查）
--     应用层逻辑用 SQL 模拟：余额不足则回滚
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);

BEGIN;

-- 查询付款方余额（实际应用中应用层判断）
SELECT @balance_from := balance FROM accounts WHERE user_id = 1;
SELECT @balance_from AS balance_of_user_1;

-- 判断余额是否足够（这里假设转 200，需 >= 200）
-- 若不足，回滚
-- 注意：MySQL 不支持 IF 语句在普通 SQL 中，需用存储过程或在应用层判断
-- 这里用 CASE WHEN 演示逻辑

-- 模拟：余额足够时执行转账
UPDATE accounts SET balance = balance - 200 WHERE user_id = 1 AND balance >= 200;
-- 若上面 affected_rows=0 说明余额不足，应回滚

UPDATE accounts SET balance = balance + 200 WHERE user_id = 2;

COMMIT;

-- 验证
SELECT user_id, balance FROM accounts WHERE user_id IN (1, 2);


-- ============================================================
-- 第五部分：隐式提交（DDL 语句）
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 DDL 语句会隐式提交当前事务
--     注意：执行后无法回滚
-- ------------------------------------------------------------
SELECT user_id, balance FROM accounts WHERE user_id = 1;

BEGIN;
UPDATE accounts SET balance = balance + 1000 WHERE user_id = 1;

-- DDL 语句隐式提交前面所有操作
-- 这里用 ALTER TABLE 演示（实际不要随意改表结构）
-- ALTER TABLE accounts ADD COLUMN remark VARCHAR(50);

-- 即使执行 ROLLBACK 也无效（DDL 已隐式提交）
-- ROLLBACK;

-- 验证：balance 已 +1000（无法回滚）
-- SELECT user_id, balance FROM accounts WHERE user_id = 1;

-- 恢复
-- UPDATE accounts SET balance = balance - 1000 WHERE user_id = 1;
-- ALTER TABLE accounts DROP COLUMN remark;

SELECT user_id, balance FROM accounts WHERE user_id = 1;


-- ============================================================
-- 第六部分：事务隔离级别查看
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 查看当前会话与全局隔离级别
-- ------------------------------------------------------------
SELECT @@transaction_isolation AS session_isolation,
       @@global.transaction_isolation AS global_isolation;

-- 默认应为 REPEATABLE-READ
SHOW VARIABLES LIKE 'transaction_isolation';

-- ------------------------------------------------------------
-- 6.2 查看自动提交与锁超时设置
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'autocommit';
SHOW VARIABLES LIKE 'innodb_lock_wait_timeout';  -- 行锁等待超时（默认 50 秒）
SHOW VARIABLES LIKE 'innodb_deadlock_detect';    -- 死锁检测（默认 ON）


-- ============================================================
-- 小结
-- ============================================================
-- 通过本脚本可观察到：
-- 1. BEGIN/COMMIT/ROLLBACK 是事务控制的三大语句
-- 2. SAVEPOINT 支持事务内部分回滚，灵活控制
-- 3. 转账事务保证扣款与加款的原子性
-- 4. ROLLBACK 后数据恢复到事务开始前状态
-- 5. DDL 语句会隐式提交，无法回滚
-- 6. MySQL 默认隔离级别 REPEATABLE-READ
--
-- 注意：本脚本为单连接顺序执行，无法演示并发场景
-- 并发演示请参考 02-isolation-level.sql 与 03-lock-demo.sql
-- 需要开两个终端/两个连接复现
-- ============================================================
