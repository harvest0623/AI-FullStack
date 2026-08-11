# Day02 - DDL 库表操作与字符集

## 本章简介

DDL（Data Definition Language，数据定义语言）负责定义数据库的结构本身——库、表、列、索引、约束。它是所有数据操作的前提：没有表，就无法插入数据；表结构不合理，后续的查询与维护都会举步维艰。

本章围绕电商示例数据库 `ecommerce` 展开，先创建数据库并完成全部 7 张表的建表，再演示 `ALTER TABLE` 的各类结构变更操作，并深入讲解字符集与校对集这一容易踩坑的主题。掌握 DDL，意味着你能根据业务需求独立设计出结构清晰、约束完备的数据库 schema。

## 学习目标

- 掌握数据库的创建、删除、修改（`CREATE/DROP/ALTER DATABASE`）
- 理解字符集 `utf8mb4` 与校对集 `utf8mb4_unicode_ci` 的含义与选择
- 熟练使用 `CREATE TABLE` 完成带约束、注释、引擎配置的建表
- 掌握 `ALTER TABLE` 的加列、改列、改名、删列、改表名、加删索引等操作
- 区分 `DROP` / `TRUNCATE` / `DELETE`（DELETE 在 Day04 详讲）
- 了解临时表、内存表的概念
- 建立“表名小写下划线、必有主键、必有注释”的建表规范意识

## 理论知识讲解

### 1. 数据库操作

| 语句 | 作用 | 说明 |
| --- | --- | --- |
| `CREATE DATABASE db` | 创建数据库 | 加 `IF NOT EXISTS` 避免重复创建报错 |
| `DROP DATABASE db` | 删除数据库 | 加 `IF EXISTS` 避免不存在时报错；删除会连带删除所有表 |
| `ALTER DATABASE db` | 修改库属性 | 改字符集 / 校对集；只读属性不可改 |

```sql
-- 标准建库（推荐写法）
CREATE DATABASE IF NOT EXISTS ecommerce
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 修改库字符集
ALTER DATABASE ecommerce
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 删除库
DROP DATABASE IF EXISTS ecommerce;

-- 查看库的建库语句
SHOW CREATE DATABASE ecommerce\G
```

> `IF NOT EXISTS` / `IF EXISTS` 是防错的好习惯，在脚本化执行时尤其重要。

### 2. 字符集与校对集

#### 字符集（Character Set）

字符集决定“字符 → 字节”的编码方式。MySQL 中两个关键字符集：

| 字符集 | 最大字节/字符 | 说明 |
| --- | --- | --- |
| `utf8`（实为 `utf8mb3`） | 3 | **不能存 4 字节字符**（如部分 emoji、生僻字），8.0 中已弃用 |
| `utf8mb4` | 4 | 真正的 UTF-8，能存 emoji，**8.0 默认** |

> ⚠️ **3 字节陷阱**：5.7 默认 `latin1`，若手动选 `utf8`，遇到 emoji 会报错或丢失。**永远用 `utf8mb4`**。8.0 起 `utf8` 已被标记为弃用，未来版本将移除。

#### 校对集（Collation）

校对集决定字符比较与排序的规则，格式为 `字符集_语言_敏感度`：

| 校对集 | 含义 | 说明 |
| --- | --- | --- |
| `utf8mb4_unicode_ci` | 基于 Unicode，大小写不敏感 | 排序更符合语言习惯，5.7 推荐 |
| `utf8mb4_general_ci` | 简单规则，大小写不敏感 | 速度快，但语言准确性差 |
| `utf8mb4_0900_ai_ci` | 8.0 新默认，口音+大小写不敏感 | 8.0 默认 |
| `utf8mb4_bin` | 二进制比较，大小写敏感 | 严格区分大小写 |

- `ci` = case insensitive（大小写不敏感）
- `cs` = case sensitive（大小写敏感）
- `ai` = accent insensitive（口音不敏感，如 `é` = `e`）
- `bin` = binary（二进制）

```sql
-- 查看所有字符集
SHOW CHARACTER SET;

-- 查看 utf8mb4 的所有校对集
SHOW COLLATION LIKE 'utf8mb4%';

-- 演示校对集差异
SELECT 'ABC' = 'abc' AS ci比较,   -- utf8mb4_unicode_ci 下返回 1
       'ABC' = 'abc' COLLATE utf8mb4_bin AS bin比较;  -- 返回 0
```

> 本教程统一使用 `utf8mb4_unicode_ci`，与 8.0 默认 `utf8mb4_0900_ai_ci` 行为接近，兼容性好。

### 3. 建表 CREATE TABLE

完整建表语法骨架：

```sql
CREATE TABLE [IF NOT EXISTS] 表名 (
  列名 数据类型 [列级约束] [COMMENT '列注释'],
  ...
  [表级约束]
) [ENGINE=存储引擎] [DEFAULT CHARSET=字符集] [COLLATE=校对集] [COMMENT='表注释'];
```

#### 列定义要素

| 要素 | 作用 | 示例 |
| --- | --- | --- |
| 数据类型 | 决定存储格式与范围 | `BIGINT` / `VARCHAR(50)` / `DECIMAL(10,2)` |
| `NOT NULL` | 不允许 NULL | `username VARCHAR(50) NOT NULL` |
| `DEFAULT` | 默认值 | `status TINYINT DEFAULT 1` |
| `AUTO_INCREMENT` | 自增（必须是键） | `id BIGINT AUTO_INCREMENT PRIMARY KEY` |
| `UNIQUE` | 唯一约束 | `email VARCHAR(100) UNIQUE` |
| `COMMENT '...'` | 列注释 | `COMMENT '用户名'` |
| `PRIMARY KEY` | 主键 | `PRIMARY KEY` |

#### 数据类型简述

数据类型在 Day03 详讲，此处先列出本板块建表用到的：

| 类型 | 用途 |
| --- | --- |
| `BIGINT` | 大整数，主键常用 |
| `INT` / `TINYINT` | 普通整数 / 小整数（状态枚举） |
| `DECIMAL(10,2)` | 定点数，存金额 |
| `VARCHAR(N)` | 变长字符串 |
| `TEXT` | 长文本 |
| `ENUM(...)` | 枚举 |
| `TIMESTAMP` | 时间戳，可自动更新 |
| `DATE` | 日期 |

#### 引擎与字符集

```sql
CREATE TABLE users (
  ...
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

- `ENGINE=InnoDB`：默认且推荐，支持事务。
- `DEFAULT CHARSET=utf8mb4`：表默认字符集。
- `COLLATE=utf8mb4_unicode_ci`：表默认校对集。
- `COMMENT='...'`：表注释，团队协作必备。

### 4. 表修改 ALTER TABLE

`ALTER TABLE` 是 DDL 中最灵活也最危险的语句，下表速查：

| 操作 | 语法 | 示例 |
| --- | --- | --- |
| 加列 | `ADD COLUMN 列 类型 [位置]` | `ADD COLUMN phone VARCHAR(20) AFTER email` |
| 加多列 | `ADD COLUMN ..., ADD COLUMN ...` | 同时加多列 |
| 改类型/位置 | `MODIFY COLUMN 列 新类型 [位置]` | `MODIFY COLUMN phone VARCHAR(32)` |
| 改名+类型 | `CHANGE COLUMN 旧名 新名 新类型` | `CHANGE COLUMN is_hot is_featured TINYINT(1)` |
| 删列 | `DROP COLUMN 列` | `DROP COLUMN phone` |
| 改表名 | `RENAME TO 新名` | `RENAME TO product_reviews` |
| 加索引 | `ADD INDEX 名 (列)` | `ADD INDEX idx_name (name)` |
| 加唯一索引 | `ADD UNIQUE INDEX 名 (列)` | `ADD UNIQUE INDEX uk_sku (sku)` |
| 加主键 | `ADD PRIMARY KEY (列)` | 建表后补主键 |
| 加外键 | `ADD CONSTRAINT 名 FOREIGN KEY...` | 补外键 |
| 加 CHECK | `ADD CONSTRAINT 名 CHECK(条件)` | 8.0 真正校验 |
| 删索引 | `DROP INDEX 名` | `DROP INDEX idx_name` |
| 删主键 | `DROP PRIMARY KEY` | 主键通常不删 |
| 改表注释 | `COMMENT='新注释'` | `ALTER TABLE t COMMENT='新'` |
| 改表选项 | `ENGINE=... / CHARSET=...` | 转换字符集用 `CONVERT TO` |

#### 关键区别：MODIFY vs CHANGE

| 语句 | 改类型 | 改列名 |
| --- | --- | --- |
| `MODIFY COLUMN` | ✅ | ❌（必须保留原列名） |
| `CHANGE COLUMN` | ✅ | ✅（必须指定新列名，即使不变） |

```sql
-- 只改类型，用 MODIFY（更简洁）
ALTER TABLE users MODIFY COLUMN phone VARCHAR(32);

-- 改名（必须给新名，类型也要写全）
ALTER TABLE products CHANGE COLUMN is_hot is_featured TINYINT(1) DEFAULT 0;
```

#### 列位置关键字

| 关键字 | 含义 |
| --- | --- |
| `FIRST` | 列移到最前 |
| `AFTER 列名` | 列移到指定列之后 |
| 不写 | 默认加到末尾 |

> 列位置仅影响 `DESC` 显示顺序，对查询性能无影响，但对人阅读表结构有帮助。

### 5. 删表与清空

| 语句 | 作用 | 自增重置 | 事务 | 触发器 | 速度 |
| --- | --- | --- | --- | --- | --- |
| `DROP TABLE t` | 删除表结构+数据 | — | DDL，隐式提交 | 删表后无触发器 | 快 |
| `TRUNCATE TABLE t` | 清空表数据，保留结构 | ✅ 重置 | DDL，不可回滚 | 不触发 | 最快 |
| `DELETE FROM t` | 按条件删行 | ❌ 不重置 | DML，可回滚 | 触发 | 慢（逐行） |

```sql
-- 删表（带 IF EXISTS 防错）
DROP TABLE IF EXISTS old_logs;

-- 清空表（重置自增，不可回滚）
TRUNCATE TABLE test_data;

-- DELETE 详讲见 Day04
DELETE FROM test_data WHERE id < 100;
```

> `TRUNCATE` 是 DDL，执行后不可回滚；`DELETE` 是 DML，在事务内可 `ROLLBACK`。这是两者的本质区别，转账/订单等场景务必用 `DELETE`。

### 6. 临时表与内存表

| 类型 | 声明 | 生命周期 | 存储位置 |
| --- | --- | --- | --- |
| 临时表 | `CREATE TEMPORARY TABLE` | 会话级，断开自动删 | 默认 InnoDB，可内存 |
| 内存表 | `CREATE TABLE ... ENGINE=MEMORY` | 持久（结构），数据在内存 | 内存，重启丢数据 |

```sql
-- 临时表：仅当前会话可见，断开自动删除
CREATE TEMPORARY TABLE tmp_active_users AS
SELECT id, username FROM users WHERE status = 1;

SELECT * FROM tmp_active_users;
-- 断开连接后自动消失

-- 内存表：数据存内存，重启 MySQL 后数据丢失但表结构保留
CREATE TABLE cache_kv (
  k VARCHAR(50) PRIMARY KEY,
  v VARCHAR(200)
) ENGINE=MEMORY;
```

> 临时表常用于复杂查询的中间结果暂存；内存表适合做高频读写的字典缓存，但不适合大表。

### 7. 建表规范

| 规范 | 说明 | 反例 |
| --- | --- | --- |
| 表名小写+下划线 | `user_account` | `UserAccount` / `userAccount` |
| 必须有主键 | 推荐 `BIGINT AUTO_INCREMENT` | 无主键表 |
| 必须有表注释与列注释 | `COMMENT` | 无注释 |
| 字符集统一 utf8mb4 | 库表一致 | 混用 latin1 |
| 金额用 DECIMAL | `DECIMAL(10,2)` | `FLOAT` / `DOUBLE` |
| 时间用 TIMESTAMP/DATETIME | 自动更新 | 用 VARCHAR 存时间 |
| 外键视场景使用 | 互联网高并发常不用，靠应用保证 | 滥用外键影响性能 |
| 命名见名知意 | `created_at` / `deleted_at` | `c1` / `field1` |
| 软删除字段 | `deleted_at TIMESTAMP NULL` | 物理删除历史数据 |

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01-create-ecommerce.sql` | 创建 ecommerce 库 + 全部 7 张表，带完整约束、注释、引擎、字符集 |
| `Code/02-alter-table.sql` | 演示 ALTER TABLE 各类操作（加列/改列/改名/删列/改表名/加删索引/加约束） |
| `README.md` | 本章理论文档 |

执行顺序：

```sql
-- 先建库建表（基础）
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day02/Code/01-create-ecommerce.sql;

-- 再演练 ALTER（会修改结构，可随时重新执行上面的脚本还原）
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day02/Code/02-alter-table.sql;
```

## 关键知识点总结

### 1. DDL 语句速查

| 语句 | 作用 |
| --- | --- |
| `CREATE DATABASE` | 建库 |
| `DROP DATABASE` | 删库 |
| `CREATE TABLE` | 建表 |
| `ALTER TABLE` | 改表 |
| `DROP TABLE` | 删表 |
| `TRUNCATE TABLE` | 清空表 |

### 2. ALTER TABLE 操作速查表

| 操作 | 语句 |
| --- | --- |
| 加列 | `ALTER TABLE t ADD COLUMN c 类型 [AFTER/FIRST];` |
| 改类型 | `ALTER TABLE t MODIFY COLUMN c 新类型;` |
| 改名+类型 | `ALTER TABLE t CHANGE COLUMN 旧c 新c 类型;` |
| 删列 | `ALTER TABLE t DROP COLUMN c;` |
| 改表名 | `ALTER TABLE t RENAME TO 新名;` |
| 加普通索引 | `ALTER TABLE t ADD INDEX 名 (列);` |
| 加唯一索引 | `ALTER TABLE t ADD UNIQUE INDEX 名 (列);` |
| 删索引 | `ALTER TABLE t DROP INDEX 名;` |
| 加外键 | `ALTER TABLE t ADD CONSTRAINT 名 FOREIGN KEY(列) REFERENCES 父(列) ON DELETE ...;` |
| 加 CHECK | `ALTER TABLE t ADD CONSTRAINT 名 CHECK(条件);` |
| 改表注释 | `ALTER TABLE t COMMENT='...';` |
| 改字符集 | `ALTER TABLE t CONVERT TO CHARACTER SET utf8mb4 COLLATE ...;` |

### 3. 字符集要点

- 永远用 `utf8mb4`，不用 `utf8`（3 字节陷阱）。
- 校对集 `ci` 大小写不敏感、`bin` 大小写敏感。
- 8.0 默认 `utf8mb4_0900_ai_ci`，本教程统一用 `utf8mb4_unicode_ci`。

### 4. 删表三兄弟对比

| 维度 | DROP | TRUNCATE | DELETE |
| --- | --- | --- | --- |
| 删结构 | ✅ | ❌ | ❌ |
| 删数据 | ✅ | ✅（全表） | ✅（按条件） |
| 自增重置 | — | ✅ | ❌ |
| 事务 | DDL 隐式提交 | DDL 不可回滚 | DML 可回滚 |
| 触发器 | 删表后无 | 不触发 | 触发 |
| 速度 | 快 | 最快 | 慢 |

## 实战练习

1. **独立完成建表**
   - 删除并重新创建 `ecommerce` 库。
   - 不看示例脚本，独立写出 7 张表的 `CREATE TABLE` 语句。
   - 用 `SHOW CREATE TABLE` 对比与示例脚本的差异，重点关注约束与注释是否齐全。

2. **ALTER 操作练习**
   - 给 `users` 表加一列 `nickname VARCHAR(50)`，位置在 `username` 之后。
   - 把 `products.stock` 类型从 `INT` 改为 `MEDIUMINT UNSIGNED`（思考：为什么库存可以用 UNSIGNED）。
   - 把 `products.is_hot` 改名为 `is_featured`（若不存在则先加）。
   - 给 `orders` 表加复合索引 `(user_id, status)`，再删除它。
   - 给 `accounts.balance` 加 `CHECK (balance >= 0)` 约束，并尝试插入负数余额看报错。

3. **字符集探究**
   - 创建一个 `latin1` 字符集的表，插入含 emoji 的字符串，观察报错或乱码现象。
   - 用 `ALTER TABLE ... CONVERT TO CHARACTER SET utf8mb4` 转换该表字符集。
   - 编写 SQL 查询 `information_schema.tables`，列出服务器上所有非 `utf8mb4` 字符集的表。
