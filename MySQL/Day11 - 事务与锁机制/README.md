# Day11 - 事务与锁机制

> 事务保证数据一致性，是金融、订单等核心业务的生命线。一笔转账如果"扣款成功但加款失败"，钱就凭空消失了。ACID 是数据库对业务的承诺，而锁与 MVCC 是兑现承诺的底层机制。本章从事务概念、ACID、四种隔离级别、并发问题（脏读/不可重复读/幻读）讲起，深入 MVCC 原理与 InnoDB 锁体系，最后落到 SELECT...FOR UPDATE 与乐观锁的实战。

---

## 目录

- [一、本章简介](#一本章简介)
- [二、学习目标](#二学习目标)
- [三、理论知识](#三理论知识)
  - [3.1 事务概念](#31-事务概念)
  - [3.2 ACID 特性](#32-acid-特性)
  - [3.3 事务操作](#33-事务操作)
  - [3.4 并发问题](#34-并发问题)
  - [3.5 四种隔离级别](#35-四种隔离级别)
  - [3.6 MVCC 多版本并发控制](#36-mvcc-多版本并发控制)
  - [3.7 锁机制](#37-锁机制)
  - [3.8 死锁](#38-死锁)
  - [3.9 乐观锁 vs 悲观锁](#39-乐观锁-vs-悲观锁)
  - [3.10 SELECT...FOR UPDATE 实战](#310-selectfor-update-实战)
- [四、代码文件说明](#四代码文件说明)
- [五、关键知识点总结](#五关键知识点总结)
- [六、实战练习](#六实战练习)

---

## 一、本章简介

考虑一个经典场景：用户 A 给用户 B 转账 100 元。这涉及两步操作：

1. 从 A 的账户扣减 100 元
2. 给 B 的账户增加 100 元

如果第 1 步成功后系统崩溃，第 2 步没执行，A 的钱扣了但 B 没收到，钱凭空消失。这就是为什么数据库需要**事务**——把这两步绑定成一个"要么全成功、要么全失败"的原子操作。

但事务要解决的远不止"原子性"。在并发环境下，多个事务同时操作同一份数据，会产生三类问题：

- **脏读**：事务 A 读到了事务 B 还没提交的数据，结果 B 回滚了，A 读到的是"脏"数据。
- **不可重复读**：事务 A 两次读同一行，结果不同——因为事务 B 在中间修改并提交了。
- **幻读**：事务 A 两次执行同一查询，结果集行数不同——因为事务 B 在中间插入/删除了符合条件的行。

数据库用**隔离级别**来权衡"并发性能"与"数据正确性"：隔离越严，问题越少，但并发越低。MySQL 默认的 REPEATABLE READ（可重复读）级别，通过 MVCC（多版本并发控制）+ 间隙锁，在性能与正确性之间取得了不错的平衡。

本章按照"事务基础 → 并发问题 → 隔离级别 → MVCC → 锁机制 → 实战"的顺序展开。由于并发场景需要多个数据库连接，单文件无法真正演示并发，配套 SQL 脚本用顺序语句模拟流程，并在注释中详细说明"如何开两个终端复现"。

---

## 二、学习目标

完成本章后，你应当能够：

1. **解释事务是什么**：能用自己的话说清"一个操作序列、要么全成功要么全失败"的含义。
2. **逐字解释 ACID**：原子性、一致性、隔离性、持久性，并指出各自靠什么实现（undo log / redo log / 锁 + MVCC / redo log）。
3. **使用事务控制语句**：`BEGIN`、`COMMIT`、`ROLLBACK`、`SAVEPOINT`、`ROLLBACK TO SAVEPOINT`，理解 `autocommit` 默认值。
4. **区分三种并发问题**：脏读、不可重复读、幻读，能各举一个具体场景。
5. **背诵四种隔离级别**：READ UNCOMMITTED、READ COMMITTED、REPEATABLE READ、SERIALIZABLE，知道各自解决哪些问题、MySQL 默认是哪个。
6. **解释 MVCC 原理**：隐藏列 `trx_id`、`roll_pointer`、Read View 的生成时机（RC vs RR）、可见性判断算法。
7. **区分 InnoDB 锁类型**：表锁 vs 行锁、共享锁 S vs 排他锁 X、记录锁、间隙锁、临键锁、意向锁。
8. **理解死锁**：能描述死锁产生条件，知道 InnoDB 死锁检测机制，能列出避免死锁的实践。
9. **对比乐观锁与悲观锁**：知道 `SELECT...FOR UPDATE` 是悲观锁，`version + CAS` 是乐观锁，各自适用场景。
10. **编写转账事务**：用 `FOR UPDATE` 锁账户、`COMMIT` 提交，保证扣款与加款的原子性。

---

## 三、理论知识

### 3.1 事务概念

**事务（Transaction）** 是数据库操作的最小逻辑执行单元，由一条或多条 SQL 组成，具有"要么全部成功、要么全部失败"的原子性。

```sql
-- 经典转账事务
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;  -- A 扣款
UPDATE accounts SET balance = balance + 100 WHERE user_id = 2;  -- B 加款
COMMIT;
-- 若任一步失败：ROLLBACK; 两步都不生效
```

**事务的生命周期**

```
   BEGIN / START TRANSACTION
            │
            ▼
   ┌────────────────────┐
   │  执行 SQL 语句序列   │
   │  INSERT/UPDATE/...  │
   └─────────┬──────────┘
             │
        ┌────┴────┐
        ▼         ▼
     COMMIT    ROLLBACK
     （提交）   （回滚）
        │         │
        ▼         ▼
   数据持久化   数据恢复到 BEGIN 前状态
```

**显式事务 vs 隐式事务**

- **显式事务**：用 `BEGIN`/`START TRANSACTION` 开启，`COMMIT`/`ROLLBACK` 结束。
- **隐式事务**：MySQL 默认 `autocommit=1`，每条 SQL 自动包裹成一个事务并立即提交。`SET autocommit=0` 可关闭自动提交，后续 SQL 都在一个隐式事务中，直到手动 `COMMIT`/`ROLLBACK`。

DDL 语句（`CREATE`/`ALTER`/`DROP`）会**隐式提交**当前事务，无法回滚。

---

### 3.2 ACID 特性

事务的四大特性，每个都有对应的实现机制：

| 特性 | 含义 | 实现机制 |
|------|------|---------|
| **A**tomicity（原子性） | 事务内操作要么全做要么全不做 | **undo log**（回滚日志） |
| **C**onsistency（一致性） | 事务执行前后数据保持一致状态 | A + I + D 共同保证 + 业务约束 |
| **I**solation（隔离性） | 并发事务互不干扰 | **锁 + MVCC** |
| **D**urability（持久性） | 提交后数据永久保存 | **redo log**（重做日志） |

**原子性详解**

原子性靠 undo log 实现。每条 SQL 执行前，InnoDB 先把"反向操作"写入 undo log：

- INSERT 的 undo log 是 DELETE
- DELETE 的 undo log 是 INSERT
- UPDATE 的 undo log 是反向 UPDATE

回滚时按 undo log 反向执行，把数据恢复到事务开始前的状态。undo log 还用于 MVCC 读取历史版本。

**一致性详解**

一致性是事务的最终目标——数据从一个合法状态转到另一个合法状态。例如转账前后，两个账户的总金额应保持不变。一致性由 A + I + D 共同保证，外加业务约束（外键、唯一键、CHECK 约束、应用层校验）。

**隔离性详解**

隔离性靠锁与 MVCC 实现。锁是悲观思路——"先锁住再操作"；MVCC 是乐观思路——"读历史版本，不阻塞写"。不同隔离级别在锁与 MVCC 之间做不同取舍。

**持久性详解**

持久性靠 redo log 实现。InnoDB 修改数据时，先写 redo log（顺序 IO，很快），再写磁盘数据页（随机 IO，较慢）。即使数据页还没落盘系统就崩溃，重启后也能从 redo log 恢复。这就是 **WAL（Write-Ahead Logging）** 机制。

---

### 3.3 事务操作

**开启事务**

```sql
-- 方式一：BEGIN（推荐，简洁）
BEGIN;

-- 方式二：START TRANSACTION（等价，可指定读写选项）
START TRANSACTION;
START TRANSACTION READ WRITE;   -- 读写事务（默认）
START TRANSACTION READ ONLY;    -- 只读事务（优化器可优化）
```

**提交与回滚**

```sql
COMMIT;      -- 提交，所有修改永久生效
ROLLBACK;    -- 回滚，所有修改撤销
```

**SAVEPOINT（保存点）**

事务内部可设多个保存点，回滚到指定保存点而非整个事务：

```sql
BEGIN;
INSERT INTO orders (...) VALUES (...);
SAVEPOINT sp1;            -- 设保存点
INSERT INTO order_items (...) VALUES (...);
SAVEPOINT sp2;
UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;

-- 发现 order_items 插入有误，但 orders 没问题
ROLLBACK TO SAVEPOINT sp1;  -- 只回滚到 sp1，sp1 之前的 orders 保留
-- 此时仍可继续操作或最终 COMMIT
COMMIT;
```

**自动提交**

```sql
-- 查看自动提交设置
SHOW VARIABLES LIKE 'autocommit';   -- 默认 ON（1）

-- 关闭自动提交（后续 SQL 都在隐式事务中）
SET autocommit = 0;

-- 恢复自动提交
SET autocommit = 1;
```

**隐式提交的触发条件**

以下语句会自动提交当前事务：

- DDL 语句：`CREATE`/`ALTER`/`DROP`/`TRUNCATE`
- `BEGIN`/`START TRANSACTION`（开启新事务前提交前一个）
- `LOAD DATA`/`LOCK TABLES`/`UNLOCK TABLES`
- `SET autocommit=1`

**事务隔离级别查看与设置**

```sql
-- 查看当前会话隔离级别
SELECT @@transaction_isolation;

-- 查看全局隔离级别
SELECT @@global.transaction_isolation;

-- 设置当前会话隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- 设置全局隔离级别
SET GLOBAL TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

---

### 3.4 并发问题

三种典型并发问题，由弱到强：

**① 脏读（Dirty Read）**

事务 A 读到了事务 B **未提交**的数据。若 B 回滚，A 读到的就是"脏"数据。

```
时刻    事务 A                  事务 B
T1                              BEGIN;
T2                              UPDATE accounts SET balance=balance+100 WHERE id=1;
T3      SELECT balance FROM accounts WHERE id=1;  -- 读到 B 未提交的值（脏读）
T4                              ROLLBACK;          -- B 回滚
T5      -- A 拿到的 balance 是不存在的"脏"数据
```

**② 不可重复读（Non-Repeatable Read）**

事务 A 两次读**同一行**，结果不同——因为事务 B 在中间**修改并提交**了。

```
时刻    事务 A                       事务 B
T1      BEGIN;
T2      SELECT balance FROM accounts WHERE id=1;  -- 余额 100
T3                                   BEGIN;
T4                                   UPDATE accounts SET balance=200 WHERE id=1;
T5                                   COMMIT;
T6      SELECT balance FROM accounts WHERE id=1;  -- 余额 200（不可重复读）
```

**③ 幻读（Phantom Read）**

事务 A 两次执行**同一查询**，结果集**行数**不同——因为事务 B 在中间**插入或删除**了符合条件的行。

```
时刻    事务 A                                      事务 B
T1      BEGIN;
T2      SELECT * FROM orders WHERE user_id=1;       -- 5 行
T3                                                BEGIN;
T4                                                INSERT INTO orders (..., user_id=1, ...) VALUES (...);
T5                                                COMMIT;
T6      SELECT * FROM orders WHERE user_id=1;       -- 6 行（多了一行"幻影"）
```

**对比表**

| 问题 | 触发条件 | 影响 |
|------|---------|------|
| 脏读 | 读未提交数据 | 数据不一致，业务错乱 |
| 不可重复读 | 同一行被修改提交 | 同一事务内读取结果不一致 |
| 幻读 | 同一查询范围被插入/删除 | 结果集行数变化 |

不可重复读侧重**修改**，幻读侧重**新增/删除**。解决不可重复读只需行锁，解决幻读需要间隙锁或 MVCC。

---

### 3.5 四种隔离级别

SQL 标准定义四种隔离级别，隔离性从弱到强，并发性能从高到低：

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 性能 | 说明 |
|---------|------|----------|------|------|------|
| READ UNCOMMITTED（读未提交） | 可能 | 可能 | 可能 | 最高 | 几乎不用 |
| READ COMMITTED（读已提交） | 不可能 | 可能 | 可能 | 较高 | Oracle/PG 默认 |
| **REPEATABLE READ（可重复读）** | 不可能 | 不可能 | 不可能* | 中等 | **MySQL 默认** |
| SERIALIZABLE（串行化） | 不可能 | 不可能 | 不可能 | 最低 | 强制串行 |

> *MySQL 的 RR 级别通过间隙锁（Gap Lock）+ MVCC 基本可避免幻读，但 SQL 标准的 RR 仍允许幻读。

**① READ UNCOMMITTED**

允许读到未提交数据（脏读）。基本无实用价值，仅用于演示。

**② READ COMMITTED（RC）**

只能读到已提交数据，解决了脏读。但同一事务内两次读同一行可能不同（不可重复读）。Oracle、PostgreSQL 默认此级别。

RC 级别下，每条 SELECT 都会生成新的 Read View，所以能读到其他事务最新提交的数据。

**③ REPEATABLE READ（RR）**

MySQL 默认级别。同一事务内多次读同一行结果一致（可重复读），通过 MVCC 实现。MySQL 的 RR 还通过间隙锁解决了幻读。

RR 级别下，事务首次 SELECT 时生成 Read View，后续复用，所以读到的总是事务开始时的快照。

**④ SERIALIZABLE**

最严格级别。所有事务串行执行，完全无并发问题，但性能最差。InnoDB 在此级别下，所有 SELECT 隐式加共享锁，几乎不用于生产。

**查看与切换**

```sql
SELECT @@transaction_isolation;   -- 查看当前级别（默认 REPEATABLE-READ）
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- 切换后下次事务生效
```

---

### 3.6 MVCC 多版本并发控制

**MVCC（Multi-Version Concurrency Control）** 是 InnoDB 实现 RC 与 RR 隔离级别的核心机制。思路是：**读不阻塞写，写不阻塞读**——通过给每行维护多个历史版本实现。

**隐藏列**

InnoDB 每行数据都有两个隐藏列：

| 隐藏列 | 含义 |
|--------|------|
| `DB_TRX_ID`（6 字节） | 最后一次修改该行的事务 ID |
| `DB_ROLL_PTR`（7 字节） | 回滚指针，指向 undo log 中的上一版本 |

每次 UPDATE 都会：
1. 把旧值写入 undo log，形成历史版本链
2. 更新当前行，写入新的 `DB_TRX_ID` 与 `DB_ROLL_PTR`

```
当前行: balance=200, trx_id=300, roll_ptr → undo log
                                          │
                                          ▼
                            undo log: balance=100, trx_id=200, roll_ptr →
                                                                     │
                                                                     ▼
                                                       undo log: balance=50, trx_id=100, roll_ptr=NULL
```

**Read View（读视图）**

事务执行 SELECT 时生成 Read View，记录"当前活跃事务列表"：

| 字段 | 含义 |
|------|------|
| `m_ids` | 生成 Read View 时所有未提交事务的 ID 列表 |
| `min_trx_id` | m_ids 中最小值 |
| `max_trx_id` | 下一个将分配的事务 ID |
| `creator_trx_id` | 当前事务自己的 ID |

**可见性判断算法**

对于某行的 `trx_id`：

1. `trx_id == creator_trx_id`：自己修改的，可见。
2. `trx_id < min_trx_id`：该版本在 Read View 之前已提交，可见。
3. `trx_id >= max_trx_id`：该版本在 Read View 之后才生成，不可见。
4. `min_trx_id <= trx_id < max_trx_id`：检查 `trx_id` 是否在 `m_ids` 中：
   - 在：未提交，不可见
   - 不在：已提交，可见

若当前版本不可见，沿 `roll_ptr` 找 undo log 中的上一版本，重复判断，直到找到可见版本或版本链耗尽。

**RC vs RR 的 Read View 生成时机**

| 隔离级别 | Read View 生成时机 | 效果 |
|---------|------------------|------|
| RC | 每条 SELECT 都生成新的 | 能读到最新已提交数据（不可重复读） |
| RR | 事务首次 SELECT 生成，后续复用 | 事务内读取结果一致（可重复读） |

**MVCC 原理图**

```
           事务 A (id=100)                事务 B (id=200)             事务 C (id=300)
           ─────────────                  ─────────────              ─────────────
T1         BEGIN;                                                    BEGIN;
T2         UPDATE accounts
           SET balance=200 WHERE id=1;
           (未提交)
T3                                        BEGIN;
T4                                        SELECT balance FROM accounts WHERE id=1;
                                          ↑ 生成 Read View: m_ids=[100,200,300]
                                          ↑ trx_id=100 在 m_ids 中，不可见
                                          ↑ 沿 roll_ptr 找旧版本 trx_id=50 < min_trx_id
                                          ↑ 可见，返回 balance=100
T5                                                                    BEGIN;
T6                                                                    UPDATE accounts
                                                                      SET balance=300 WHERE id=1;
                                                                      COMMIT;
T7                                        SELECT balance FROM accounts WHERE id=1;
                                          ↑ RR: 复用 T4 的 Read View，仍读 balance=100
                                          ↑ RC: 生成新 Read View，m_ids=[100,200]
                                          ↑   trx_id=300 不在 m_ids，已提交，可见
                                          ↑   返回 balance=300
```

**MVCC 只解决"快照读"**

- **快照读**：普通 SELECT，走 MVCC，读历史版本。
- **当前读**：`SELECT...FOR UPDATE`、`SELECT...LOCK IN SHARE MODE`、`UPDATE`、`DELETE`、`INSERT`，读最新数据并加锁。

MVCC 不隔离当前读，当前读靠锁保证一致性。

---

### 3.7 锁机制

**表锁 vs 行锁**

| 维度 | 表锁 | 行锁 |
|------|------|------|
| 粒度 | 整张表 | 单行（实际是索引项） |
| 加锁开销 | 小 | 大 |
| 并发度 | 低 | 高 |
| 引擎 | MyISAM（仅表锁） | InnoDB（默认行锁） |

InnoDB 行锁是**基于索引**的——若 UPDATE/DELETE 的 WHERE 没走索引，会退化为表锁。

**共享锁 S vs 排他锁 X**

| 锁类型 | 标记 | 加锁方式 | 兼容性 |
|--------|------|---------|--------|
| 共享锁 S（读锁） | S | `SELECT ... LOCK IN SHARE MODE` / `SELECT ... FOR SHARE`（8.0） | S 与 S 兼容，S 与 X 互斥 |
| 排他锁 X（写锁） | X | `SELECT ... FOR UPDATE` / `UPDATE` / `DELETE` / `INSERT` | X 与任何锁互斥 |

**记录锁 Record Lock**

锁住索引上的**单条记录**。例如 `WHERE id=1 FOR UPDATE` 会在 id=1 的索引项加记录锁。

**间隙锁 Gap Lock**

锁住索引记录之间的**区间**（不含记录本身），防止其他事务在区间内插入新记录，从而避免幻读。

例如索引上有 id=5、id=10，间隙锁锁住 `(5, 10)` 区间，其他事务无法插入 id=6/7/8/9。

间隙锁只在 RR 级别生效，RC 级别无间隙锁。

**临键锁 Next-Key Lock**

**记录锁 + 间隙锁**的组合，锁住一个左开右闭区间 `(id=5, id=10]`。这是 RR 级别下行锁的默认形态，既防修改又防插入。

**意向锁 Intention Lock（表级）**

InnoDB 在加行锁前，先在表上加意向锁，用于快速判断"是否有事务在表内加了行锁"：

- **IS（意向共享）**：事务准备加行级 S 锁前，先加表级 IS
- **IX（意向排他）**：事务准备加行级 X 锁前，先加表级 IX

意向锁之间互相兼容，意向锁与表级 S/X 锁互斥。这样其他事务想加表锁时，只需检查意向锁，无需逐行检查行锁。

**锁兼容矩阵**

|  | IS | IX | S | X |
|--|----|----|---|---|
| **IS** | ✅ | ✅ | ✅ | ❌ |
| **IX** | ✅ | ✅ | ❌ | ❌ |
| **S** | ✅ | ❌ | ✅ | ❌ |
| **X** | ❌ | ❌ | ❌ | ❌ |

**查看锁信息**

```sql
-- 8.0 推荐用 performance_schema.data_locks
SELECT * FROM performance_schema.data_locks;
SELECT * FROM performance_schema.data_lock_waits;

-- 老版本用 INFORMATION_SCHEMA.INNODB_LOCKS（8.0 已废弃）
```

---

### 3.8 死锁

**死锁定义**

两个或多个事务互相持有对方需要的锁，形成循环等待，永远无法继续执行。

```
时刻    事务 A                       事务 B
T1      BEGIN;                       BEGIN;
T2      UPDATE accounts SET ...      UPDATE accounts SET ...
        WHERE id=1;  -- 锁 id=1          WHERE id=2;  -- 锁 id=2
T3      UPDATE accounts SET ...      UPDATE accounts SET ...
        WHERE id=2;  -- 等 B 释放         WHERE id=1;  -- 等 A 释放
T4      ↙ 互相等待 ↘
        A 等 B 释放 id=2，B 等 A 释放 id=1
        → 死锁
```

**InnoDB 死锁检测**

InnoDB 默认开启死锁检测（`innodb_deadlock_detect=ON`），发现死锁后**主动回滚代价较小的事务**，让另一个事务继续。被回滚的事务会收到错误：

```
ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction
```

**避免死锁的实践**

1. **固定加锁顺序**：所有事务按相同顺序加锁（如按 id 升序）。
2. **缩短事务**：事务越短，持锁时间越短，死锁概率越低。
3. **降低隔离级别**：RR 比 RC 更易死锁（间隙锁多），业务允许时用 RC。
4. **批量操作拆分**：大批量 UPDATE 拆成小批，减少单次持锁量。
5. **合理索引**：无索引的 UPDATE 会退化为表锁，更易死锁。
6. **应用层重试**：捕获 1213 错误后自动重试（注意幂等性）。

**死锁排查**

```sql
SHOW ENGINE INNODB STATUS\G
-- 输出中 "LATEST DETECTED DEADLOCK" 段含死锁详情
```

---

### 3.9 乐观锁 vs 悲观锁

**悲观锁（Pessimistic Lock）**

假设"冲突一定会发生"，先锁后操作：

```sql
-- 转账场景：先锁账户再操作
BEGIN;
SELECT balance FROM accounts WHERE user_id = 1 FOR UPDATE;  -- 加 X 锁
-- 应用层判断余额是否够
UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE user_id = 2;
COMMIT;  -- 释放锁
```

适用：写多读少、冲突频繁、强一致性要求高。

**乐观锁（Optimistic Lock）**

假设"冲突很少发生"，不加锁，更新时检查版本：

```sql
-- accounts 表加 version 字段
ALTER TABLE accounts ADD COLUMN version INT DEFAULT 0;

-- 第一步：先读出余额与版本
SELECT balance, version FROM accounts WHERE user_id = 1;
-- 假设返回 balance=100, version=3

-- 第二步：应用层判断余额后，带版本号更新
UPDATE accounts
SET balance = balance - 100, version = version + 1
WHERE user_id = 1 AND version = 3;
-- 若返回 affected_rows=1，更新成功
-- 若返回 affected_rows=0，说明版本变了（其他事务先更新了），需重试
```

适用：读多写少、冲突少、性能敏感。

**对比表**

| 维度 | 悲观锁 | 乐观锁 |
|------|--------|--------|
| 思路 | 先锁后操作 | 不锁，更新时校验 |
| 实现 | `SELECT...FOR UPDATE` | version 字段 + CAS |
| 并发性 | 低（持锁期间阻塞其他事务） | 高（无锁，失败重试） |
| 一致性 | 强（数据库保证） | 弱（需应用层处理重试） |
| 适用 | 写多读少、冲突频繁 | 读多写少、冲突少 |
| 死锁风险 | 有 | 无 |
| 复杂度 | 简单 | 需重试逻辑 |

---

### 3.10 SELECT...FOR UPDATE 实战

**转账场景完整流程**

```sql
-- accounts 表：id, user_id, balance, version
-- 假设 user_id=1 余额 1000，user_id=2 余额 500

-- 步骤一：开启事务
BEGIN;

-- 步骤二：锁定两个账户（按 id 升序加锁，避免死锁）
SELECT balance FROM accounts WHERE user_id = 1 FOR UPDATE;
SELECT balance FROM accounts WHERE user_id = 2 FOR UPDATE;

-- 步骤三：应用层判断 user_id=1 余额 >= 100
-- 若不够则 ROLLBACK

-- 步骤四：执行扣款与加款
UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE user_id = 2;

-- 步骤五：提交，释放锁
COMMIT;
```

**关键点**

1. **`FOR UPDATE` 必须在事务内**：事务外执行无效（自动提交后锁立即释放）。
2. **加锁顺序固定**：所有转账事务都按 user_id 升序加锁，避免死锁。
3. **`FOR UPDATE` 走索引**：`WHERE user_id=1` 必须有 user_id 索引，否则退化为表锁。
4. **锁在 COMMIT/ROLLBACK 后释放**：事务结束前，其他事务的 `FOR UPDATE` 会阻塞等待。

**FOR UPDATE vs LOCK IN SHARE MODE**

| 场景 | 推荐 |
|------|------|
| 修改前锁定（转账） | `FOR UPDATE`（X 锁） |
| 只读但需保证读取后不被修改 | `LOCK IN SHARE MODE`（S 锁，8.0 推荐 `FOR SHARE`） |

**8.0 新语法**

```sql
-- 等价 LOCK IN SHARE MODE
SELECT * FROM accounts WHERE user_id = 1 FOR SHARE;

-- 跳过锁等待（行已被锁时不阻塞，直接报错）
SELECT * FROM accounts WHERE user_id = 1 FOR UPDATE NOWAIT;

-- 等待指定时间后超时
SELECT * FROM accounts WHERE user_id = 1 FOR UPDATE WAIT 5;

-- 跳过已锁定的行
SELECT * FROM accounts WHERE user_id = 1 FOR UPDATE SKIP LOCKED;
```

---

## 四、代码文件说明

本章配套三个 SQL 脚本，均位于 `Code/` 目录下：

| 文件 | 内容 | 关键演示 |
|------|------|---------|
| `01-transaction-basic.sql` | 事务基础演示 | BEGIN/COMMIT/ROLLBACK、SAVEPOINT、转账事务在 accounts 表，验证 ROLLBACK 后余额不变 |
| `02-isolation-level.sql` | 隔离级别演示 | SET SESSION TRANSACTION ISOLATION LEVEL，注释详细说明如何开两个终端验证脏读/不可重复读/幻读 |
| `03-lock-demo.sql` | 锁演示 | FOR UPDATE 排他锁、LOCK IN SHARE MODE 共享锁、行锁 vs 表锁、间隙锁、乐观锁 version 方案 |

**重要说明**：事务与锁的并发演示需要**多个数据库连接**，单文件无法真正并发。SQL 脚本中用顺序语句演示核心流程，并用详细注释说明"如何开两个终端/两个连接"来复现并发场景。

**前置依赖**：假设 `ecommerce` 库及 `accounts` 表已存在（Day02-Day04 创建）。`accounts` 表需含 `version` 字段用于乐观锁演示（脚本中会动态添加）。

---

## 五、关键知识点总结

### 隔离级别与并发问题对照表

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 性能 | MySQL 默认 |
|---------|------|----------|------|------|-----------|
| READ UNCOMMITTED | 可能 | 可能 | 可能 | ⭐⭐⭐⭐⭐ | 否 |
| READ COMMITTED | 不可能 | 可能 | 可能 | ⭐⭐⭐⭐ | 否（Oracle/PG 默认） |
| REPEATABLE READ | 不可能 | 不可能 | 不可能* | ⭐⭐⭐ | **是** |
| SERIALIZABLE | 不可能 | 不可能 | 不可能 | ⭐ | 否 |

> *MySQL 的 RR 通过间隙锁 + MVCC 基本避免幻读。

### 锁类型速查表

| 锁类型 | 粒度 | 作用 | 触发 |
|--------|------|------|------|
| 共享锁 S | 行 | 读锁，允许多个 S 并存 | `LOCK IN SHARE MODE` / `FOR SHARE` |
| 排他锁 X | 行 | 写锁，独占 | `FOR UPDATE` / `UPDATE` / `DELETE` |
| 记录锁 | 行 | 锁单条索引记录 | 等值查询命中记录 |
| 间隙锁 | 区间 | 锁索引区间，防插入 | 范围查询（RR） |
| 临键锁 | 区间 | 记录锁 + 间隙锁 | RR 默认行锁形态 |
| 意向锁 IS/IX | 表 | 协调行锁与表锁 | 加行锁前自动加 |
| 自增锁 AUTO-INC | 表 | 保证自增列唯一 | INSERT 自增列 |

### MVCC 原理图

```
            当前数据行
┌─────────────────────────────────────┐
│ id=1, balance=200, trx_id=300       │
│              roll_ptr ─────────┐    │
└────────────────────────────────┼────┘
                                 ▼
              undo log (历史版本链)
┌─────────────────────────────────────┐
│ id=1, balance=100, trx_id=200       │
│              roll_ptr ─────────┐    │
└────────────────────────────────┼────┘
                                 ▼
┌─────────────────────────────────────┐
│ id=1, balance=50, trx_id=100        │
│              roll_ptr=NULL          │
└─────────────────────────────────────┘

事务 SELECT 时生成 Read View：
  m_ids = [活跃事务列表]
  按 trx_id 判断可见性，不可见则沿 roll_ptr 找历史版本

RC: 每条 SELECT 生成新 Read View
RR: 事务首次 SELECT 生成，后续复用
```

### 乐观锁 vs 悲观锁对比表

| 维度 | 悲观锁 | 乐观锁 |
|------|--------|--------|
| 思路 | 先锁后操作 | 不锁，更新时校验版本 |
| 实现 | `FOR UPDATE` | version + CAS |
| 并发性 | 低 | 高 |
| 死锁风险 | 有 | 无 |
| 适用 | 写多读少 | 读多写少 |
| 一致性 | 数据库保证 | 应用层重试 |

### ACID 实现机制

| 特性 | 实现机制 |
|------|---------|
| 原子性 A | undo log（回滚日志） |
| 一致性 C | A + I + D + 业务约束 |
| 隔离性 I | 锁 + MVCC |
| 持久性 D | redo log（重做日志，WAL） |

---

## 六、实战练习

### 练习一：转账事务实战

**场景**：基于 `accounts` 表，模拟用户 1 给用户 2 转账 200 元。

**要求**：
1. 编写完整转账事务，使用 `FOR UPDATE` 锁定两个账户。
2. 在事务内查询余额，判断是否足够（不足则回滚）。
3. 验证：转账前后两个账户总金额不变。
4. 思考：为什么两个 `FOR UPDATE` 要按 user_id 升序执行？

```sql
-- 参考骨架
BEGIN;
SELECT balance FROM accounts WHERE user_id = 1 FOR UPDATE;
SELECT balance FROM accounts WHERE user_id = 2 FOR UPDATE;
-- 若 user_id=1 余额 < 200，ROLLBACK;
UPDATE accounts SET balance = balance - 200 WHERE user_id = 1;
UPDATE accounts SET balance = balance + 200 WHERE user_id = 2;
COMMIT;
```

### 练习二：用乐观锁实现转账

**场景**：用 `version` 字段实现乐观锁转账，对比与悲观锁的差异。

**要求**：
1. 为 `accounts` 表添加 `version INT DEFAULT 0` 字段。
2. 先读出 user_id=1 的 `balance` 与 `version`。
3. 用 `UPDATE ... WHERE user_id=1 AND version=?` 更新，检查 `affected_rows`。
4. 若失败（affected_rows=0），重试整个流程（最多 3 次）。
5. 思考：乐观锁与悲观锁哪个更适合"高并发抢购"场景？为什么？

### 练习三：复现不可重复读（开两个终端）

**场景**：用两个终端验证 RC 级别下的不可重复读，以及 RR 级别如何避免。

**步骤**：
1. 终端 A 与终端 B 都设置隔离级别为 RC：
   ```sql
   SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
   ```
2. 终端 A 开启事务，查询 user_id=1 的 balance（假设 1000）。
3. 终端 B 修改 user_id=1 的 balance 为 2000 并提交。
4. 终端 A 再次查询，应看到 2000（不可重复读）。
5. 把两个终端都改为 RR 级别，重复步骤 2-4，终端 A 第二次查询应仍为 1000（可重复读）。

**要求**：
1. 完整复现上述流程，记录每一步的查询结果。
2. 用 `SELECT * FROM performance_schema.data_locks` 观察 RR 级别下的锁情况。
3. 思考：RR 级别下，终端 A 的 SELECT 是否加了锁？为什么终端 B 的 UPDATE 还能成功提交？

---

> 本章是数据库一致性的核心。完成本章后，你已经掌握了 MySQL 性能与事务两大主题。下一章 Day12 将进入视图、存储过程、函数与触发器，学习如何用数据库对象封装复用逻辑。
