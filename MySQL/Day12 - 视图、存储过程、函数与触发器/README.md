# Day12 - 视图、存储过程、函数与触发器

视图把复杂的查询封装成一张"虚拟表"，存储过程把一串业务逻辑封装成可调用的程序，函数让 SQL 具备计算能力，触发器在数据变更时自动执行审计与同步。它们共同构成 MySQL 的"可编程能力"，是把数据库从单纯的存储仓库升级为业务逻辑执行平台的关键。本章将围绕电商库 `ecommerce` 完整演示这四类对象的创建、使用与避坑。

## 学习目标

- 理解视图的本质，能创建、修改、删除视图，并判断视图是否可更新
- 掌握 `WITH CHECK OPTION` 的作用，理解其保护语义
- 能编写带 IN/OUT/INOUT 参数、流程控制、游标的存储过程
- 能创建自定义函数，并在 `SELECT` 中使用
- 理解触发器的 BEFORE/AFTER 时机与 NEW/OLD 引用，能落地审计日志场景
- 了解事件调度器 EVENT 的定时任务能力
- 明辨"何时把逻辑下沉到数据库、何时留在应用层"的取舍

---

## 理论知识讲解

### 1. 视图 VIEW

#### 1.1 概念

视图是一张**虚拟表**：它本身不存储数据，只存储一条 `SELECT` 查询的定义。查询视图时，MySQL 把视图定义展开为底层查询，再在基础表上执行。

```
用户 ──查询──> 视图(虚拟表) ──展开──> 基础表(users/orders/...)
```

#### 1.2 创建、修改、删除

```sql
-- 创建视图
CREATE VIEW v_product_sales AS
SELECT p.id, p.name, SUM(oi.quantity) AS sold_qty
FROM products p
JOIN order_items oi ON oi.product_id = p.id
GROUP BY p.id, p.name;

-- 修改视图（替换定义）
CREATE OR REPLACE VIEW v_product_sales AS
SELECT p.id, p.name, p.price, SUM(oi.quantity) AS sold_qty
FROM products p
LEFT JOIN order_items oi ON oi.product_id = p.id
GROUP BY p.id, p.name, p.price;

-- 查看视图定义
SHOW CREATE VIEW v_product_sales\G

-- 删除视图（IF EXISTS 防报错）
DROP VIEW IF EXISTS v_product_sales;
```

#### 1.3 查询视图与查表无异

```sql
SELECT * FROM v_product_sales WHERE sold_qty > 100 ORDER BY sold_qty DESC;
```

#### 1.4 可更新视图

简单视图（无聚合、无 DISTINCT、无 JOIN、无 GROUP BY、无子查询）支持 `INSERT/UPDATE/DELETE`，操作会落到基础表上：

```sql
CREATE VIEW v_active_users AS
SELECT id, username, email FROM users WHERE status = 1;

-- 以下 DML 实际修改 users 表
INSERT INTO v_active_users(id, username, email) VALUES (1001, 'tom', 'tom@x.com');
UPDATE v_active_users SET email = 'tom2@x.com' WHERE id = 1001;
DELETE FROM v_active_users WHERE id = 1001;
```

#### 1.5 WITH CHECK OPTION

保证通过视图更新的行**更新后仍满足视图 WHERE 条件**，避免"插进视图却查不到"的怪象：

```sql
CREATE VIEW v_active_users AS
SELECT id, username, email, status FROM users WHERE status = 1
WITH CHECK OPTION;

-- 下列 INSERT 会被拒绝，因为 status=0 不满足视图条件
-- INSERT INTO v_active_users(id, username, email, status) VALUES (1002, 'jerry', 'j@x.com', 0);
-- ERROR: CHECK OPTION failed
```

#### 1.6 视图的用途

| 用途 | 说明 |
|------|------|
| 简化查询 | 把复杂 JOIN/聚合封装，业务方只 `SELECT * FROM v_xxx` |
| 权限隔离 | 只暴露部分列给某账号（行级/列级权限） |
| 兼容旧接口 | 表结构变了，用视图保留旧字段名供老代码使用 |
| 报表复用 | 报表 SQL 统一管理在视图里 |

#### 1.7 视图的局限

- **性能不一定更好**：视图本身不加速查询，复杂视图展开后仍是慢 SQL
- **嵌套视图难维护**：视图套视图，调优与排错难度陡升
- **可更新视图限制多**：含聚合/JOIN 的视图不可 DML

---

### 2. 存储过程 PROCEDURE

#### 2.1 基本语法

```sql
DELIMITER $$  -- 切换分隔符，避免 ; 被当作过程体结束
CREATE PROCEDURE transfer(IN from_uid INT, IN to_uid INT, IN amount DECIMAL(10,2))
BEGIN
    -- 过程体
    UPDATE accounts SET balance = balance - amount WHERE user_id = from_uid;
    UPDATE accounts SET balance = balance + amount WHERE user_id = to_uid;
END$$
DELIMITER ;  -- 恢复分号

CALL transfer(1, 2, 100.00);  -- 调用
```

#### 2.2 参数模式

| 模式 | 说明 |
|------|------|
| IN | 入参（默认），调用方传入，过程内只读 |
| OUT | 出参，过程内赋值，返回给调用方 |
| INOUT | 既入又出 |

```sql
CREATE PROCEDURE stat_order(IN uid INT, OUT cnt INT, OUT total DECIMAL(10,2))
BEGIN
    SELECT COUNT(*), COALESCE(SUM(total_amount), 0) INTO cnt, total
    FROM orders WHERE user_id = uid;
END;

CALL stat_order(1, @c, @t);
SELECT @c AS 订单数, @t AS 总额;
```

#### 2.3 变量与赋值

```sql
-- 局部变量（必须 DECLARE 在 BEGIN 之后最前）
DECLARE v_name VARCHAR(50) DEFAULT '';
DECLARE v_cnt INT DEFAULT 0;

-- 赋值
SET v_name = 'alice';
SELECT username INTO v_name FROM users WHERE id = 1 LIMIT 1;
```

#### 2.4 流程控制

```sql
-- IF
IF v_cnt > 0 THEN
    -- ...
ELSEIF v_cnt = 0 THEN
    -- ...
ELSE
    -- ...
END IF;

-- CASE
CASE
    WHEN v_role = 'admin' THEN SET v_level = 3;
    WHEN v_role = 'editor' THEN SET v_level = 2;
    ELSE SET v_level = 1;
END CASE;

-- WHILE
WHILE v_i < 10 DO
    SET v_i = v_i + 1;
END WHILE;

-- REPEAT
REPEAT
    SET v_i = v_i + 1;
UNTIL v_i >= 10 END REPEAT;

-- LOOP + LEAVE
my_loop: LOOP
    SET v_i = v_i + 1;
    IF v_i >= 10 THEN LEAVE my_loop; END IF;
END LOOP;
```

#### 2.5 游标 CURSOR

游标用于逐行处理查询结果：

```sql
DECLARE done INT DEFAULT 0;
DECLARE v_uid INT;
DECLARE cur CURSOR FOR SELECT id FROM users WHERE status = 1;
DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;  -- 取完置标志

OPEN cur;
read_loop: LOOP
    FETCH cur INTO v_uid;
    IF done = 1 THEN LEAVE read_loop; END IF;
    -- 处理 v_uid
END LOOP;
CLOSE cur;
```

#### 2.6 存储过程 vs 应用层代码

| 维度 | 存储过程 | 应用层代码 |
|------|---------|-----------|
| 网络开销 | 一次调用，少往返 | 多次 SQL 多次往返 |
| 事务边界 | 内部可控 | 应用控制更灵活 |
| 可调试性 | 差，日志难打 | 好，IDE 调试 |
| 版本管理 | 难，需同步到库 | Git 即可 |
| 可移植性 | 差，绑定厂商 | 好 |
| 团队协作 | DBA 与开发边界模糊 | 职责清晰 |

> **实践建议**：除非有强一致性事务场景（如核心转账、对账），否则优先把逻辑放应用层。存储过程不应当作"省事"工具滥用。

---

### 3. 自定义函数 FUNCTION

#### 3.1 基本语法

```sql
DELIMITER $$
CREATE FUNCTION calc_discount_price(price DECIMAL(10,2), off DECIMAL(4,2))
RETURNS DECIMAL(10,2)
DETERMINISTIC  -- 相同输入恒返回相同输出
BEGIN
    RETURN ROUND(price * (1 - off), 2);
END$$
DELIMITER ;

SELECT name, price, calc_discount_price(price, 0.10) AS 折后价 FROM products LIMIT 5;
```

#### 3.2 函数特性声明

| 声明 | 含义 |
|------|------|
| DETERMINISTIC | 相同参数恒返回相同结果 |
| READS SQL DATA | 函数内含 SELECT，但不修改数据 |
| NO SQL | 函数内不含 SQL |
| MODIFIES SQL DATA | 函数内含写操作（少用） |

> 若未开启 `log_bin_trust_function_creators`，函数必须显式声明 `DETERMINISTIC` 或 `READS SQL DATA`，否则创建失败。

#### 3.3 函数 vs 存储过程

| 维度 | 函数 FUNCTION | 存储过程 PROCEDURE |
|------|--------------|-------------------|
| 返回值 | 必须 RETURN 单值 | 可无返回，可用 OUT 多个 |
| 调用方式 | `SELECT fn()` / 嵌入表达式 | `CALL proc()` |
| 使用场景 | 表达式中计算 | 封装业务流程 |
| 事务 | 不能 BEGIN/COMMIT | 可以 |
| 结果集 | 不能返回结果集 | 可以 SELECT 输出多行 |

---

### 4. 触发器 TRIGGER

#### 4.1 基本语法

```sql
DELIMITER $$
CREATE TRIGGER trg_user_soft_delete
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    -- 把删除时间写入 deleted_at，实现软删除审计
    IF NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL THEN
        -- 可在此写审计日志
    END IF;
END$$
DELIMITER ;
```

#### 4.2 NEW 与 OLD 引用

| 触发时机 | INSERT | UPDATE | DELETE |
|---------|--------|--------|--------|
| BEFORE | NEW（待插入） | NEW（新值）/ OLD（旧值） | OLD（待删除） |
| AFTER | NEW（已插入） | NEW / OLD | OLD（已删除） |

> `NEW` 在 INSERT/UPDATE 可读可改（BEFORE 阶段修改会生效）；`OLD` 只读。

#### 4.3 触发器时机矩阵

| 时机 | 典型场景 |
|------|---------|
| BEFORE INSERT | 数据校验、默认值填充、格式化 |
| AFTER INSERT | 同步统计表、发事件通知 |
| BEFORE UPDATE | 数据校验、阻止非法变更 |
| AFTER UPDATE | 审计日志（记录前后值） |
| BEFORE DELETE | 阻止删除（如已关联订单） |
| AFTER DELETE | 级联清理、统计衰减 |

#### 4.4 典型场景

1. **审计日志**：记录关键字段的变更前后值到日志表
2. **自动时间戳**：`updated_at` 字段自动更新
3. **级联统计**：订单创建后自动累加用户消费总额
4. **数据校验**：BEFORE 触发器中用 `SIGNAL SQLSTATE` 抛错阻止非法操作

```sql
-- 用 SIGNAL 抛错
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '库存不足，禁止下单';
```

#### 4.5 触发器的坑

- **性能影响**：每行都触发，大批量写入时开销显著
- **调试困难**：触发器隐式执行，问题难定位
- **隐式行为**：新人不知道有触发器，遇到"莫名"数据变更摸不着头脑
- **级联触发**：A 表触发器改 B 表，B 表触发器又改 A 表，可能死循环
- **不能用 COMMIT/ROLLBACK**：触发器内不能显式事务控制

> **实践建议**：触发器只用于审计、时间戳这类"必须紧贴数据"的逻辑，业务流程别放触发器里。

---

### 5. 事件调度器 EVENT

#### 5.1 开启调度器

```sql
-- 查看状态
SHOW VARIABLES LIKE 'event_scheduler';

-- 开启（运行时）
SET GLOBAL event_scheduler = ON;

-- 永久开启：在 my.cnf / my.ini 加 event_scheduler=ON
```

#### 5.2 创建定时事件

```sql
CREATE EVENT evt_clean_logs
ON SCHEDULE EVERY 1 DAY STARTS TIMESTAMP(CURRENT_DATE + 1, '03:00:00')
DO
    DELETE FROM operation_logs WHERE created_at < NOW() - INTERVAL 30 DAY;
```

#### 5.3 事件管理

```sql
ALTER EVENT evt_clean_logs DISABLE;  -- 暂停
ALTER EVENT evt_clean_logs ENABLE;   -- 恢复
DROP EVENT IF EXISTS evt_clean_logs;
```

> 事件调度器常用于：定时清理日志、定时统计报表、定时归档历史数据。

---

## 关键知识点总结

### 视图 / 过程 / 函数 / 触发器对比表

| 对象 | 关键字 | 是否存数据 | 调用方式 | 主要用途 |
|------|--------|----------|---------|---------|
| 视图 | VIEW | 否（存定义） | SELECT | 封装查询、权限隔离 |
| 存储过程 | PROCEDURE | 否 | CALL | 封装业务流程 |
| 函数 | FUNCTION | 否 | 嵌入表达式 | 计算返回值 |
| 触发器 | TRIGGER | 否 | 自动触发 | 审计、级联、校验 |
| 事件 | EVENT | 否 | 定时调度 | 周期任务 |

### 触发器时机矩阵

|  | BEFORE | AFTER |
|---|---|---|
| INSERT | 校验/默认值 | 同步统计/通知 |
| UPDATE | 校验/阻止 | 审计日志 |
| DELETE | 阻止删除 | 级联清理 |

### DELIMITER 使用要点

- 存储过程、函数、触发器、事件的过程体含 `;`，必须先切换 `DELIMITER $$`
- 过程体结束后用 `$$` 收尾，再用 `DELIMITER ;` 恢复
- 切换后普通 SQL 也用新分隔符，注意恢复以免后续脚本异常

---

## 代码文件说明

| 文件 | 内容 |
|------|------|
| `Code/01-view-demo.sql` | 视图演示：商品销售统计视图、用户订单汇总视图、可更新视图、WITH CHECK OPTION、DROP VIEW |
| `Code/02-procedure-demo.sql` | 存储过程演示：转账过程、分页查询 IN 参数、订单统计 OUT 参数、游标遍历 |
| `Code/03-function-demo.sql` | 自定义函数：折扣价计算、金额格式化、用户等级判断 |
| `Code/04-trigger-demo.sql` | 触发器演示：用户软删除审计、商品库存变更日志、订单状态变更记录（覆盖 BEFORE/AFTER 各类型） |

执行方式：

```sql
mysql> USE ecommerce;
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day12 - 视图、存储过程、函数与触发器/Code/01-view-demo.sql
```

> Windows 路径含空格与中文，建议先 `cd` 到对应目录，或使用引号包裹路径。所有脚本可在 MySQL 8.0+ 直接 `source` 执行。

---

## 实战练习

### 练习一：商品评价摘要视图

创建视图 `v_product_review_summary`，包含商品 ID、名称、评价数、平均分、好评率（rating≥4 的占比）。然后写一条查询，从该视图查出"好评率低于 60% 且评价数≥10"的商品。

### 练习二：批量补库存存储过程

编写存储过程 `sp_restock_low_stock(threshold INT, add_qty INT)`，把库存低于 `threshold` 的所有在售商品库存增加 `add_qty`，并通过 OUT 参数返回受影响行数。调用示例：`CALL sp_restock_low_stock(10, 50, @affected);`。

### 练习三：订单状态变更审计触发器

创建 `orders` 表的 AFTER UPDATE 触发器 `trg_order_status_log`，当 `status` 字段发生变化时，把变更前后的状态、订单 ID、操作时间写入新表 `order_status_log`。然后执行一次 UPDATE 验证日志是否落库。
