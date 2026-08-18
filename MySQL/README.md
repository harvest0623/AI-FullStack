# MySQL 数据库学习指南

> 系统化掌握关系型数据库核心能力，为后端开发与 AI 全栈应用奠定数据存储与查询基础

> 共 14 天，覆盖从环境搭建、SQL 语法、索引事务到设计与性能优化的完整知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [示例数据库](#示例数据库)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是全栈学习系列的**数据持久化基石**。无论后端框架如何演进（Node.js / NestJS / Python），最终都要落到数据库上。MySQL 是全球使用最广泛的开源关系型数据库，掌握它意味着掌握关系型数据库的通用范式——SQL 语法、索引原理、事务隔离、范式设计这些知识可以迁移到 PostgreSQL、Oracle、SQL Server 等任意 RDBMS。

**学习目标**：完成本板块后，你应能：
- 熟练编写 DDL / DML / DQL 语句，完成任意业务表的建表、增删改查
- 理解 MySQL 数据类型体系，能为字段选择合适类型，避免存储浪费与精度问题
- 用多表连接、子查询、聚合、窗口函数解决复杂业务查询
- 看懂 EXPLAIN 执行计划，能诊断慢查询并做索引优化
- 理解 ACID 与四种隔离级别，能正确使用事务与锁避免并发问题
- 用视图、存储过程、触发器封装复用数据逻辑
- 独立完成数据库账号权限分配、备份恢复操作
- 用三大范式与反范式思想设计合理的表结构

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 SQL 脚本 + 实战练习
- 全程使用统一的电商示例数据库 `ecommerce`，前后连贯
- 所有 SQL 脚本可在 MySQL 8.0+ 直接 `source` 执行
- 紧扣工程化视角，多处铺垫后端集成与 AI 应用场景

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| 基础 SQL 概念 | 了解即可 | 知道"表、行、列、主键"概念即可，本板块从零讲起 |
| 命令行操作 | 基础 | 能用终端执行命令、配置环境变量 |
| 操作系统概念 | 基础 | 文件、进程、网络端口 |
| 任意编程语言 | 有即可 | 有后端开发经验更好理解数据库与应用的配合 |

**环境准备**：
- MySQL 8.0+（推荐 8.0 或 8.4 LTS，本板块以 8.0 为基准）
- 命令行客户端 `mysql`（随 MySQL Server 安装）或图形客户端（DBeaver / Navicat / DataGrip / MySQL Workbench，任选其一）
- 可选：Docker（用容器快速启动 MySQL，无需本地安装）

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                   MySQL 数据库学习路线（14天）                    │
└─────────────────────────────────────────────────────────────────┘

阶段一：基础与数据定义（Day01-Day04）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Day01 基础  │  Day02 DDL   │  Day03 数据  │  Day04 DML   │
│  与环境      │  库表操作    │  类型与约束  │  增删改      │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
阶段二：查询语言 DQL（Day05-Day09）
┌────────────┬────────────┬────────────┬────────────┬────────────┐
│ Day05 DQL  │ Day06 聚合 │ Day07 多表 │ Day08 子   │ Day09 函数 │
│ 基础查询   │ 与分组     │ 连接查询   │ 查询       │ 与窗口函数 │
└─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┘
      │            │            │            │            │
      ▼            ▼            ▼            ▼            ▼
阶段三：性能与事务（Day10-Day11）
┌──────────────────────┬──────────────────────┐
│  Day10 索引与执行计划 │  Day11 事务与锁机制   │
└──────────┬───────────┴──────────┬───────────┘
           │                      │
           ▼                      ▼
阶段四：进阶与运维（Day12-Day14）
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ Day12 视图/存储过程/  │ Day13 用户权限与      │ Day14 数据库设计与   │
│ 触发器               │ 备份恢复              │ 性能优化              │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

---

## 示例数据库

本板块全程使用一个**电商系统 `ecommerce`** 数据库作为示例，所有建表、查询、索引、事务都围绕它展开，保证知识连贯。

### 数据库 ER 概览

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│  users   │     │  categories  │     │ products │
│ 用户表   │     │  商品分类表  │     │ 商品表   │
└────┬─────┘     └──────┬───────┘     └────┬─────┘
     │                  │ (自连接)         │
     │                  └──────────────────┘
     │
     ├──────┬──────────────┐
     │      │              │
     ▼      ▼              ▼
┌─────────┐  ┌────────────┐  ┌──────────┐
│ orders  │  │ accounts   │  │ reviews  │
│ 订单表  │  │ 账户表     │  │ 评价表   │
└────┬────┘  └────────────┘  └──────────┘
     │
     ▼
┌──────────────┐
│ order_items  │
│ 订单详情表   │
└──────────────┘
```

### 核心表说明

| 表名 | 用途 | 演示重点 |
|------|------|---------|
| `users` | 用户账户 | 数据类型、约束、软删除 |
| `categories` | 商品分类（树形结构） | 自连接、外键 |
| `products` | 商品信息 | 索引、外键、类型选择 |
| `orders` | 订单主表 | 多表连接、状态枚举 |
| `order_items` | 订单明细 | 联合主键、外键级联 |
| `accounts` | 用户账户余额 | 事务转账、行锁 |
| `reviews` | 商品评价 | 聚合统计、窗口函数 |

> 各表的完整建表语句与测试数据在 Day02、Day04 中逐步创建，后续天数直接复用。

---

## 每日内容详表

### 阶段一：基础与数据定义

#### Day01 - MySQL基础与环境安装
- **核心**：关系型数据库概念、RDBMS、SQL 四类语言（DDL/DML/DQL/DCL）、MySQL 版本与发行版、安装、客户端工具、连接与基本操作、information_schema
- **代码**：`00-environment-check.sql` / `01-hello-sql.sql` / `README.md`（环境配置指南）
- **重点**：搭建可运行环境，理解 SQL 体系结构

#### Day02 - DDL库表操作与字符集
- **核心**：CREATE/DROP/ALTER DATABASE、字符集 utf8mb4 与校对集、CREATE TABLE、ALTER TABLE（加列/改列/删列/改表名/改引擎）、DROP TABLE、TRUNCATE、IF EXISTS/IF NOT EXISTS、注释
- **代码**：`01-create-ecommerce.sql`（建库建表）/ `02-alter-table.sql`（表结构修改）
- **重点**：建立 ecommerce 库全部表结构

#### Day03 - 数据类型与约束
- **核心**：数值类型（TINYINT/SMALLINT/INT/BIGINT/DECIMAL/FLOAT/DOUBLE）、字符串（CHAR/VARCHAR/TEXT/BLOB/ENUM/SET）、日期时间（DATE/TIME/DATETIME/TIMESTAMP/YEAR）、JSON、PRIMARY KEY、AUTO_INCREMENT、NOT NULL、UNIQUE、DEFAULT、CHECK、FOREIGN KEY、外键级联策略
- **代码**：`01-data-types-demo.sql` / `02-constraints-demo.sql`
- **重点**：类型选择原则、外键级联（CASCADE/RESTRICT/SET NULL）

#### Day04 - DML数据增删改
- **核心**：INSERT（单行/多行/INSERT...SELECT/INSERT...ON DUPLICATE KEY UPDATE/REPLACE）、UPDATE（多表更新、ORDER BY+LIMIT）、DELETE（多表删除）、TRUNCATE vs DELETE、安全更新模式 sql_safe_updates
- **代码**：`01-insert-data.sql`（灌入测试数据）/ `02-update-delete.sql`
- **重点**：ON DUPLICATE KEY UPDATE 的 upsert 场景

---

### 阶段二：查询语言 DQL

#### Day05 - DQL基础查询与运算符
- **核心**：SELECT、列别名 AS、DISTINCT、WHERE、运算符（比较/逻辑 AND OR NOT/IN/BETWEEN/LIKE/IS NULL/IS NOT NULL/REGEXP）、ORDER BY、LIMIT、分页公式、SELECT 执行顺序
- **代码**：`01-basic-select.sql` / `02-operators.sql` / `03-pagination.sql`
- **重点**：NULL 的三值逻辑、LIKE 通配符、分页偏移优化思路

#### Day06 - 聚合函数与分组查询
- **核心**：COUNT/SUM/AVG/MIN/MAX/GROUP_CONCAT、GROUP BY、HAVING、WHERE vs HAVING、WITH ROLLUP、SQL 完整执行顺序（FROM→JOIN→WHERE→GROUP BY→HAVING→SELECT→ORDER BY→LIMIT）
- **代码**：`01-aggregate-functions.sql` / `02-group-by-having.sql`
- **重点**：WHERE 与 HAVING 的本质区别、聚合函数对 NULL 的处理

#### Day07 - 多表连接查询
- **核心**：笛卡尔积、INNER JOIN、LEFT JOIN、RIGHT JOIN、CROSS JOIN、自连接（分类树）、多表连接（三表以上）、USING vs ON、自然连接 NATURAL JOIN
- **代码**：`01-inner-join.sql` / `02-left-right-join.sql` / `03-self-join.sql` / `04-multi-table-join.sql`
- **重点**：LEFT JOIN 的"保留左表"语义、自连接解决树形结构

#### Day08 - 子查询
- **核心**：标量子查询、列子查询、行子查询、表子查询、EXISTS/NOT EXISTS、相关子查询、ANY/ALL/SOME、子查询位置（SELECT/WHERE/FROM/HAVING）、派生表、IN vs EXISTS 性能
- **代码**：`01-scalar-subquery.sql` / `02-exists-subquery.sql` / `03-derived-table.sql`
- **重点**：相关子查询 vs 非相关子查询的执行差异

#### Day09 - 常用函数与窗口函数
- **核心**：字符串函数（CONCAT/SUBSTRING/TRIM/REPLACE/UPPER/LOWER/LENGTH）、数值函数（ROUND/CEIL/FLOOR/RAND/ABS/MOD）、日期函数（NOW/CURDATE/DATE_FORMAT/DATE_ADD/DATEDIFF/TIMESTAMPDIFF）、流程控制（IF/CASE WHEN/IFNULL/NULLIF/COALESCE）、类型转换 CAST/CONVERT、窗口函数（ROW_NUMBER/RANK/DENSE_RANK/LAG/LEAD/NTILE/SUM OVER/AVG OVER）
- **代码**：`01-string-numeric-functions.sql` / `02-date-functions.sql` / `03-control-functions.sql` / `04-window-functions.sql`
- **重点**：窗口函数是 MySQL 8 重大特性，解决"分组排名"类问题

---

### 阶段三：性能与事务

#### Day10 - 索引与执行计划
- **核心**：B+Tree 索引原理、索引类型（主键/唯一/普通/全文/联合/前缀/函数索引）、CREATE/ALTER/DROP INDEX、EXPLAIN 字段解读（id/select_type/table/type/key/key_len/rows/Extra）、最左前缀原则、索引失效场景、覆盖索引、回表、索引下推 ICP
- **代码**：`01-create-index.sql` / `02-explain-examples.sql` / `03-index-failure.sql`
- **重点**：看懂 EXPLAIN 是性能优化的起点

#### Day11 - 事务与锁机制
- **核心**：ACID、事务操作（BEGIN/COMMIT/ROLLBACK/SAVEPOINT）、四种隔离级别（READ UNCOMMITTED/READ COMMITTED/REPEATABLE READ/SERIALIZABLE）、脏读/不可重复读/幻读、MVCC 原理与 Read View、行锁/表锁/间隙锁/临键锁、死锁、SELECT...FOR UPDATE / LOCK IN SHARE MODE、乐观锁与悲观锁
- **代码**：`01-transaction-basic.sql` / `02-isolation-level.sql` / `03-lock-demo.sql`
- **重点**：MySQL 默认 RR 级别如何通过 MVCC + 间隙锁避免幻读

---

### 阶段四：进阶与运维

#### Day12 - 视图、存储过程、函数与触发器
- **核心**：VIEW（创建/修改/删除/可更新视图/检查选项）、存储过程（CREATE PROCEDURE/IN OUT INOUT 参数/变量/IF/CASE/WHILE/游标 CURSOR/异常处理）、自定义函数 CREATE FUNCTION、触发器（BEFORE/AFTER INSERT/UPDATE/DELETE）、事件调度器 EVENT
- **代码**：`01-view-demo.sql` / `02-procedure-demo.sql` / `03-function-demo.sql` / `04-trigger-demo.sql`
- **重点**：视图的封装复用、触发器的审计场景

#### Day13 - 用户权限与备份恢复
- **核心**：用户管理（CREATE USER/ALTER USER/DROP USER）、权限（GRANT/REVOKE/SHOW GRANTS）、角色（CREATE ROLE/GRANT TO）、密码策略、mysql 系统库、mysqldump 备份与恢复、binlog 与按时间点恢复、mysqldumpslow、主从复制原理简介
- **代码**：`01-user-privilege.sql` / `02-backup-restore.md`（备份恢复操作指南）
- **重点**：最小权限原则、备份是运维底线

#### Day14 - 数据库设计与性能优化
- **核心**：三大范式（1NF/2NF/3NF）与反范式、ER 建模、命名规范、主键设计（自增 vs UUID vs 雪花 ID）、慢查询日志、SQL 优化技巧（避免 SELECT *、避免函数包裹索引列、LIMIT 深分页优化、JOIN 优化、子查询优化）、分库分表简介、读写分离、与 ORM/应用层的配合
- **代码**：`01-normalization-demo.sql` / `02-slow-query-optimization.sql` / `03-design-best-practices.md`
- **重点**：范式是设计准绳、反范式是工程妥协

---

## 目录结构

```
MySQL/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - MySQL基础与环境安装/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天 SQL 脚本
│       ├── 00-environment-check.sql
│       ├── 01-hello-sql.sql
│       └── README.md
├── Day02 - DDL库表操作与字符集/
│   ├── README.md
│   └── Code/
│       ├── 01-create-ecommerce.sql
│       └── 02-alter-table.sql
├── ...（Day03-Day13 同构）...
└── Day14 - 数据库设计与性能优化/
    ├── README.md
    └── Code/
        ├── 01-normalization-demo.sql
        ├── 02-slow-query-optimization.sql
        └── 03-design-best-practices.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，均为 `.sql` 脚本（可在 mysql 客户端直接 `source` 执行）
- 部分天数含 `.md` 配套说明文档（环境配置、操作指南）

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-6 小时 | 约 2-3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 4-5 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **先读后写**：每天先通读 README，理解概念后再动手执行 SQL
2. **动手执行**：每个 `.sql` 文件都要在 MySQL 中实际运行，观察结果
3. **改写实验**：在示例基础上做修改，故意写错观察报错信息
4. **对照执行计划**：Day10 之后，每条查询都尝试用 EXPLAIN 分析
5. **完成实战**：每天 README 末尾的实战练习是巩固知识的关键
6. **结合应用层**：回想 NestJS/Node.js 板块中数据库集成部分，理解 SQL 与代码的配合

### 阶段性检查点

完成每个阶段后，应能回答以下问题：

- **阶段一完成后**：能否独立为一个业务模块设计完整的表结构（含类型、约束、外键）？
- **阶段二完成后**：能否用连接查询、子查询、窗口函数解决复杂报表需求？
- **阶段三完成后**：能否看懂 EXPLAIN 并为慢查询设计合适索引？能否解释 RR 级别如何防幻读？
- **阶段四完成后**：能否用范式设计库表、用视图/存储过程封装逻辑、完成用户授权与备份？

---

## 如何运行代码

### 方式一：Docker 启动 MySQL（推荐，零安装）

```bash
# 启动 MySQL 8.0 容器
docker run -d --name mysql-learn \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -p 3306:3306 \
  mysql:8.0

# 进入容器内的 mysql 客户端
docker exec -it mysql-learn mysql -uroot -p123456
```

### 方式二：本地安装 MySQL

1. 从 [MySQL 官网](https://dev.mysql.com/downloads/) 下载 MySQL 8.0 Community Server
2. 安装时记住 root 密码
3. 命令行连接：

```bash
mysql -u root -p
# 输入密码后进入 mysql> 提示符
```

### 执行 SQL 脚本

```sql
-- 方式一：在 mysql 客户端内用 source 命令
mysql> source d:/Coding/AI-FullStack/MySQL/Day02\ -\ DDL库表操作与字符集/Code/01-create-ecommerce.sql

-- 方式二：命令行直接执行
mysql -u root -p < "Day02 - DDL库表操作与字符集/Code/01-create-ecommerce.sql"
```

### 图形客户端（任选其一）

| 客户端 | 特点 | 适用 |
|--------|------|------|
| DBeaver | 免费开源、支持多种数据库 | 推荐通用 |
| Navicat | 功能强大、付费 | 专业开发 |
| DataGrip | JetBrains 出品、智能提示 | 已用 IDEA 生态 |
| MySQL Workbench | 官方出品、免费 | 入门 |

### 常用操作提示

```sql
-- 查看所有数据库
SHOW DATABASES;

-- 使用 ecommerce 库
USE ecommerce;

-- 查看当前库所有表
SHOW TABLES;

-- 查看表结构
DESC users;
-- 或
SHOW CREATE TABLE users\G

-- 查看建库建表语句
SHOW CREATE DATABASE ecommerce;
```

### Windows 用户注意

- SQL 脚本路径含中文与空格，`source` 命令建议用引号包裹或先 `cd` 到目录
- MySQL 默认不区分大小写（Windows / macOS），Linux 区分表名大小写
- 命令行中文乱码时执行：`SET NAMES utf8mb4;`

---

## 知识点速查

### SQL 语言分类速查

| 分类 | 全称 | 作用 | 代表语句 | 对应天数 |
|------|------|------|---------|---------|
| DDL | Data Definition Language | 定义结构 | CREATE / ALTER / DROP / TRUNCATE | Day02 |
| DML | Data Manipulation Language | 操作数据 | INSERT / UPDATE / DELETE | Day04 |
| DQL | Data Query Language | 查询数据 | SELECT | Day05-Day09 |
| DCL | Data Control Language | 控制权限 | GRANT / REVOKE | Day13 |
| TCL | Transaction Control Language | 事务控制 | BEGIN / COMMIT / ROLLBACK | Day11 |

### MySQL 数据类型速查

| 类别 | 类型 | 说明 | 对应天数 |
|------|------|------|---------|
| 整数 | TINYINT / SMALLINT / INT / BIGINT | 1/2/4/8 字节 | Day03 |
| 浮点 | FLOAT / DOUBLE | 近似值 | Day03 |
| 定点 | DECIMAL(M,D) | 精确值，存金额 | Day03 |
| 字符串 | CHAR(N) / VARCHAR(N) | 定长/变长 | Day03 |
| 文本 | TEXT / MEDIUMTEXT / LONGTEXT | 大文本 | Day03 |
| 日期 | DATE / TIME / DATETIME / TIMESTAMP | 日期时间 | Day03 |
| 枚举 | ENUM / SET | 单选/多选 | Day03 |
| JSON | JSON | 文档型（MySQL 8 增强） | Day03 |
| 二进制 | BLOB / BINARY / VARBINARY | 二进制数据 | Day03 |

### SQL 执行顺序速查

```
编写顺序：  SELECT → FROM → JOIN → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT
执行顺序：  FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

> 理解执行顺序是写对 GROUP BY / HAVING / 别名引用的关键。

### 索引类型速查

| 索引类型 | 关键字 | 特点 |
|---------|--------|------|
| 主键索引 | PRIMARY KEY | 唯一 + 非空，每表一个 |
| 唯一索引 | UNIQUE | 值唯一，允许 NULL |
| 普通索引 | INDEX / KEY | 加速查询，无约束 |
| 联合索引 | INDEX(a, b, c) | 多列组合，遵循最左前缀 |
| 全文索引 | FULLTEXT | 全文检索（MATCH AGAINST） |
| 前缀索引 | INDEX(col(10)) | 对字符串前 N 字符建索引 |

### 事务隔离级别速查

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 性能 |
|---------|------|----------|------|------|
| READ UNCOMMITTED | 可能 | 可能 | 可能 | 最高 |
| READ COMMITTED | 不可能 | 可能 | 可能 | 较高 |
| REPEATABLE READ（默认） | 不可能 | 不可能 | 不可能* | 中等 |
| SERIALIZABLE | 不可能 | 不可能 | 不可能 | 最低 |

> *MySQL 的 RR 级别通过间隙锁（Gap Lock）+ MVCC 基本可避免幻读。

### 常用命令速查

```bash
# 连接
mysql -u root -p                        # 本地连接
mysql -h 127.0.0.1 -P 3306 -u root -p   # 指定主机端口

# 备份恢复
mysqldump -u root -p ecommerce > backup.sql      # 备份整个库
mysqldump -u root -p ecommerce users > users.sql # 备份单表
mysql -u root -p ecommerce < backup.sql          # 恢复

# 服务管理
mysql.server start          # macOS 启动
net start mysql80           # Windows 启动
systemctl start mysqld      # Linux 启动
```

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **Redis** | 缓存层配合 MySQL，缓存击穿/穿透/雪崩、读写一致性 |
| **Node.js / NestJS** | Day17 数据库集成、TypeORM/Prisma 的 SQL 映射、连接池配置 |
| **PostgreSQL / MongoDB** | 对照学习，关系型 vs 文档型的差异，pgvector 向量检索 |
| **Docker** | MySQL 容器化部署、数据卷持久化、多服务编排 |
| **Linux** | MySQL 在 Linux 上的部署、性能调优、日志分析 |
| **LLM / RAG** | 知识库元数据存储、对话历史、SQL 在数据预处理中的作用 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [MySQL 8.0 官方文档](https://dev.mysql.com/doc/refman/8.0/en/) - 最权威的参考
- [MySQL 8.0 中文文档](https://www.mysqlzh.com/) - 中文翻译参考
- [MySQL Tutorial](https://dev.mysql.com/doc/refman/8.0/en/tutorial.html) - 官方入门教程
- [SQLZOO](https://sqlzoo.net/) - 在线交互式 SQL 练习
- [LeetCode 数据库](https://leetcode.cn/problemset/database/) - SQL 题目练习

---

## 贡献与反馈

本学习手册为原创内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用数据驱动你的全栈之路！**