# Day04 - DML 数据增删改

## 本章简介

DML（Data Manipulation Language，数据操纵语言）负责对表中数据进行增、删、改，是应用层最频繁的数据库操作。每一次用户注册、下单、改密码、删评论，背后都是 INSERT / UPDATE / DELETE 在工作。

与定义结构的 DDL 不同，DML 操作的是“数据本身”，它支持事务回滚、受 `sql_safe_updates` 保护、并能通过 `ROW_COUNT()` 与 `LAST_INSERT_ID()` 获取执行反馈。本章在已建好的 `ecommerce` 库上灌入真实测试数据，再系统演练各类 INSERT、UPDATE、DELETE 变体，并对比 DELETE / TRUNCATE / DROP 三者的本质差异，为后续查询与事务章节打好数据基础。

## 学习目标

- 掌握 INSERT 的单行、多行、`INSERT...SET`、`INSERT...SELECT`、`INSERT IGNORE`、`ON DUPLICATE KEY UPDATE`、`REPLACE INTO` 等变体
- 掌握 UPDATE 的单表、多列、表达式、`ORDER BY+LIMIT`、`CASE`、多表 JOIN 更新
- 掌握 DELETE 的单表、`ORDER BY+LIMIT`、多表 JOIN 删除
- 区分 DELETE / TRUNCATE / DROP 在速度、自增、事务、触发器上的差异
- 理解 `sql_safe_updates` 安全更新模式的作用
- 掌握 `ROW_COUNT()` 与 `LAST_INSERT_ID()` 的使用场景

## 理论知识讲解

### 1. INSERT 插入

#### 基本变体

| 语法 | 说明 | 示例 |
| --- | --- | --- |
| `INSERT INTO t(a,b) VALUES(1,2)` | 单行插入 | 标准写法 |
| `INSERT INTO t(a,b) VALUES(1,2),(3,4)` | 多行批量插入 | 推荐，比多次单插快 |
| `INSERT INTO t SET a=1, b=2` | SET 写法 | 仅 MySQL 支持，可读性好 |
| `INSERT INTO t(a,b) SELECT ...` | 从查询结果插入 | 复制表、汇总落表 |
| `INSERT IGNORE INTO ...` | 唯一键冲突时忽略 | 批量跳过已存在 |
| `INSERT ... ON DUPLICATE KEY UPDATE` | 冲突则更新（upsert） | 存在则改，不存在则插 |
| `REPLACE INTO ...` | 冲突则先删后插 | 自增 id 会变，慎用 |

```sql
-- 1. 多行批量插入（推荐）
INSERT INTO users (username, email, password_hash) VALUES
  ('user1', 'u1@x.com', 'h1'),
  ('user2', 'u2@x.com', 'h2');

-- 2. INSERT ... SELECT（从旧表迁数据）
INSERT INTO users_bak(username, email)
SELECT username, email FROM users WHERE status = 1;

-- 3. INSERT IGNORE（冲突跳过，不报错）
INSERT IGNORE INTO users (username, email, password_hash)
VALUES ('user1', 'new@x.com', 'h');  -- user1 已存在，整条跳过

-- 4. ON DUPLICATE KEY UPDATE（upsert，推荐）
INSERT INTO accounts (user_id, balance) VALUES (1, 100)
ON DUPLICATE KEY UPDATE balance = balance + 100;  -- 存在则余额+100

-- 5. REPLACE INTO（先删后插，自增 id 变化）
REPLACE INTO users (id, username, email, password_hash)
VALUES (1, 'admin', 'admin@x.com', 'newhash');  -- id=1 先删再插
```

#### ON DUPLICATE KEY UPDATE vs REPLACE INTO

| 维度 | ON DUPLICATE KEY UPDATE | REPLACE INTO |
| --- | --- | --- |
| 冲突处理 | 更新现有行 | 先删旧行再插新行 |
| 自增 ID | 不变 | 变化（新 id） |
| 触发器 | 触发 UPDATE | 触发 DELETE + INSERT |
| 外键 | 不影响子表 | 若被外键引用可能失败 |
| 推荐 | ✅ 推荐 | ⚠️ 慎用 |

> **upsert 优先用 `ON DUPLICATE KEY UPDATE`**，它不会改变自增 ID，对外键友好。

### 2. UPDATE 更新

#### 基本语法

```sql
UPDATE 表名
SET 列1 = 值1 [, 列2 = 值2 ...]
[WHERE 条件]
[ORDER BY ...]
[LIMIT n];
```

> ⚠️ **UPDATE 不带 WHERE 会更新全表**，生产环境务必带 WHERE，建议开启 `sql_safe_updates`。

#### 变体示例

```sql
-- 1. 单列更新
UPDATE products SET price = 199.00 WHERE id = 13;

-- 2. 多列更新
UPDATE products SET price = 199.00, stock = stock + 100 WHERE id = 13;

-- 3. 表达式更新（基于当前值）
UPDATE products SET stock = stock - 1 WHERE id = 1 AND stock > 0;

-- 4. CASE 条件更新
UPDATE products SET stock = CASE category_id
  WHEN 2 THEN stock + 10
  WHEN 3 THEN stock + 20
  ELSE stock
END WHERE category_id IN (2, 3);

-- 5. ORDER BY + LIMIT（只更新前 N 条）
UPDATE products SET stock = stock + 50
WHERE status = 'on_sale'
ORDER BY stock ASC LIMIT 3;  -- 给库存最少的3个补货

-- 6. 多表 JOIN 更新（根据关联表更新）
UPDATE products p
JOIN order_items oi ON p.id = oi.product_id
SET p.stock = p.stock - oi.quantity
WHERE oi.order_id = 1;
```

#### 多表 UPDATE JOIN 语法

```sql
UPDATE t1 [INNER|LEFT] JOIN t2 ON t1.id = t2.t1_id
SET t1.col = t2.col
WHERE ...;
```

> 多表更新常用于“根据订单扣库存”、“根据用户角色调整余额”等关联场景。

### 3. DELETE 删除

#### 基本语法

```sql
DELETE FROM 表名
[WHERE 条件]
[ORDER BY ...]
[LIMIT n];
```

> ⚠️ **DELETE 不带 WHERE 会清空全表**，但可事务回滚（区别于 TRUNCATE）。

#### 变体示例

```sql
-- 1. 条件删除
DELETE FROM reviews WHERE rating < 3;

-- 2. ORDER BY + LIMIT 删除
DELETE FROM logs ORDER BY created_at ASC LIMIT 1000;  -- 删最早的1000条

-- 3. 多表 DELETE JOIN（删 alice 的所有评价）
DELETE r FROM reviews r
JOIN users u ON r.user_id = u.id
WHERE u.username = 'alice';

-- 4. 同时删多张表的匹配行
DELETE o, oi FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
WHERE o.status = 'cancelled';
```

#### 多表 DELETE 语法

```sql
-- 只删 t1
DELETE t1 FROM t1 JOIN t2 ON t1.id = t2.t1_id WHERE ...;

-- 同时删 t1 和 t2
DELETE t1, t2 FROM t1 JOIN t2 ON ... WHERE ...;
```

### 4. DELETE vs TRUNCATE vs DROP 对比

| 维度 | DELETE | TRUNCATE | DROP |
| --- | --- | --- | --- |
| 类别 | DML | DDL | DDL |
| 作用 | 按条件删行 | 清空全表数据 | 删除表结构+数据 |
| WHERE | ✅ 支持 | ❌ 不支持 | — |
| 事务 | ✅ 可回滚 | ❌ 不可回滚 | ❌ 不可回滚 |
| 自增重置 | ❌ 不重置 | ✅ 重置为1 | — |
| 触发器 | ✅ 触发 | ❌ 不触发 | 表删了无触发器 |
| 速度 | 慢（逐行） | 快（直接释放） | 最快 |
| 占用 undo | 大 | 小 | — |
| 适合场景 | 删部分行 | 清空全表 | 删表 |

```sql
-- DELETE: 可回滚，自增不重置
BEGIN;
DELETE FROM t;
ROLLBACK;  -- 数据恢复

-- TRUNCATE: 不可回滚，自增重置
TRUNCATE TABLE t;  -- 即使在 BEGIN...ROLLBACK 内也无效

-- DROP: 表彻底消失
DROP TABLE t;
```

> **生产环境清空表数据优先用 DELETE + WHERE**，需要重置自增才考虑 TRUNCATE；DROP 慎之又慎。

### 5. sql_safe_updates 安全更新模式

`sql_safe_updates` 防止无 WHERE 或 WHERE 不含索引列的全表 UPDATE/DELETE，是 MySQL 的“防呆机制”。

```sql
-- 查看状态
SHOW VARIABLES LIKE 'sql_safe_updates';

-- 开启（仅当前会话）
SET sql_safe_updates = 1;

-- 开启后，以下语句会报错 1175：
-- UPDATE products SET stock = 0;                  -- 无 WHERE
-- DELETE FROM reviews;                             -- 无 WHERE
-- UPDATE products SET stock = 0 WHERE name LIKE '%';  -- WHERE 列无索引

-- 允许的写法（WHERE 列有索引，或加 LIMIT）
UPDATE products SET stock = 0 WHERE id = 1;          -- id 是主键
DELETE FROM reviews WHERE id > 0 LIMIT 10;           -- 加 LIMIT
```

| 行为 | 安全模式 OFF | 安全模式 ON |
| --- | --- | --- |
| 无 WHERE 的 UPDATE/DELETE | 执行（危险） | 报错 1175 |
| WHERE 列无索引 | 执行 | 报错 1175 |
| WHERE 列有索引 | 执行 | 执行 |
| 加 LIMIT | 执行 | 执行 |

> 建议开发环境与生产环境都开启 `sql_safe_updates`，避免 `UPDATE t SET ...` 漏写 WHERE 导致全表被改。

### 6. ROW_COUNT() 与受影响行数

`ROW_COUNT()` 返回上一条 SQL 语句影响的行数，常用于存储过程与脚本判断。

```sql
UPDATE products SET stock = stock + 1 WHERE category_id = 2;
SELECT ROW_COUNT();  -- 返回更新的行数

DELETE FROM reviews WHERE rating = 1;
SELECT ROW_COUNT();  -- 返回删除的行数

INSERT INTO users (username, email) VALUES ('a','a@x.com');
SELECT ROW_COUNT();  -- 返回 1
```

> 在应用层（如 JDBC/Go/Python 驱动）通常通过 API 直接获取 `affected_rows`，无需 SQL 查询。

### 7. LAST_INSERT_ID() 获取自增 ID

```sql
INSERT INTO users (username, email, password_hash) VALUES ('tom', 'tom@x.com', 'h');
SELECT LAST_INSERT_ID();  -- 返回 tom 的自增 id
```

**关键规则**：

- 返回**当前连接**最近一次 INSERT 的自增 ID，与其他连接无关。
- 多行插入时，返回**第一条**的自增 ID，不是最后一条。
- 若上一条 INSERT 未产生自增 ID（如手动指定 id），返回值不变。

```sql
-- 多行插入，LAST_INSERT_ID 返回第一条的 id
INSERT INTO users (username, email) VALUES ('a','a@x.com'),('b','b@x.com');
SELECT LAST_INSERT_ID();  -- 返回 'a' 的 id

-- 用 LAST_INSERT_ID 关联插入从表
INSERT INTO accounts (user_id, balance) VALUES (LAST_INSERT_ID(), 100);
```

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01-insert-data.sql` | 向 ecommerce 灌入测试数据（12用户/10分类/20商品/8订单/10账户/12评价） |
| `Code/02-update-delete.sql` | 演示各类 UPDATE/DELETE 操作与对比，每步带 SELECT 验证 |
| `README.md` | 本章理论文档 |

执行顺序：

```sql
-- 1. 确保表结构存在（Day02 已建）
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day02/Code/01-create-ecommerce.sql;

-- 2. 灌入测试数据
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day04/Code/01-insert-data.sql;

-- 3. 演练 UPDATE/DELETE（会修改数据，可重新执行第2步还原）
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day04/Code/02-update-delete.sql;
```

> `02-update-delete.sql` 会修改 ecommerce 数据，演练后可重新执行 `01-insert-data.sql` 还原。

## 关键知识点总结

### 1. INSERT 变体速查

| 变体 | 冲突处理 | 自增ID | 推荐 |
| --- | --- | --- | --- |
| `INSERT` | 报错 | 新增 | 标准 |
| `INSERT IGNORE` | 忽略 | 跳过的无 | 批量跳过 |
| `ON DUPLICATE KEY UPDATE` | 更新 | 不变 | ✅ upsert |
| `REPLACE INTO` | 先删后插 | 变化 | ⚠️ 慎用 |

### 2. DELETE / TRUNCATE / DROP 对比

| 维度 | DELETE | TRUNCATE | DROP |
| --- | --- | --- | --- |
| 类别 | DML | DDL | DDL |
| 删数据 | 按条件 | 全表 | 全表+结构 |
| 事务回滚 | ✅ | ❌ | ❌ |
| 自增重置 | ❌ | ✅ | — |
| 触发器 | ✅ | ❌ | 无 |
| 速度 | 慢 | 快 | 最快 |

### 3. 安全更新模式

- `SET sql_safe_updates = 1;` 开启后，无 WHERE 或 WHERE 列无索引的 UPDATE/DELETE 报错 1175。
- 生产环境建议常开。

### 4. 常用反馈函数

| 函数 | 作用 |
| --- | --- |
| `ROW_COUNT()` | 上一条 SQL 影响行数 |
| `LAST_INSERT_ID()` | 当前连接最近自增 ID（多行返回首条） |

### 5. 多表操作语法

```sql
-- 多表更新
UPDATE t1 JOIN t2 ON ... SET t1.col = ... WHERE ...;

-- 多表删除（删 t1）
DELETE t1 FROM t1 JOIN t2 ON ... WHERE ...;

-- 多表删除（同时删 t1, t2）
DELETE t1, t2 FROM t1 JOIN t2 ON ... WHERE ...;
```

## 实战练习

1. **upsert 实战**
   - 向 `accounts` 表插入 `(user_id=3, balance=500)`，若已存在则余额改为 `balance + 500`，使用 `ON DUPLICATE KEY UPDATE`。
   - 再用 `REPLACE INTO` 对 `users` 表的 `id=3` 记录做一次替换，对比两种方式后 `id` 是否变化。
   - 思考：为什么转账场景必须用 `ON DUPLICATE KEY UPDATE` 而非 `REPLACE`？

2. **批量库存调整**
   - 用一条 `UPDATE ... CASE` 把所有 `status='on_sale'` 的商品按分类调价：手机类降价 5%、电脑类降价 3%、其他类不变。
   - 用多表 `UPDATE JOIN` 根据 `order_items` 扣减 `products.stock`（模拟全部订单已发货扣库存）。
   - 用 `ORDER BY stock ASC LIMIT 5` 给库存最少的 5 个在售商品补货 100。

3. **DELETE 与 TRUNCATE 对比实验**
   - 创建 `log_test(id AUTO_INCREMENT, msg)` 表，插入 5 条记录（自增到 5）。
   - 用 `DELETE FROM log_test` 清空，再插入 1 条，观察新 id 是 6（不重置）。
   - 用 `TRUNCATE TABLE log_test` 清空，再插入 1 条，观察新 id 是 1（重置）。
   - 在事务内执行 `DELETE` 后 `ROLLBACK`，验证数据恢复；再对 `TRUNCATE` 做同样实验，验证不可回滚。
