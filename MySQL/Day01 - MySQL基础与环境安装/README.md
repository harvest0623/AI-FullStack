# Day01 - MySQL 基础与环境安装

## 本章简介

关系型数据库是后端数据存储的基石，而 MySQL 是全球最流行的开源关系型数据库管理系统（RDBMS），在互联网公司、中小企业、个人项目中广泛使用。无论是用户信息、商品数据、订单流水，还是日志记录、配置管理，MySQL 都能以结构化的方式高效存取。

本章作为 MySQL 学习路线的起点，从数据库的基本概念出发，理清关系型数据库的核心术语与 SQL 语言分类，并完成 MySQL 8.0+ 的环境搭建与连通性验证，为后续 DDL、DML、DQL 的学习打下基础。掌握本章后，你将拥有一台可执行 SQL 的 MySQL 环境，并理解每一条 SQL 属于哪一语言类别。

## 学习目标

- 理解关系型数据库的演进与核心概念（表、行、列、主键、外键、关系）
- 区分 SQL 语言的五大类别（DDL / DML / DQL / DCL / TCL）
- 了解 MySQL 版本演进与 8.0 关键特性
- 对比 InnoDB 与 MyISAM 存储引擎并理解默认选择 InnoDB 的原因
- 完成 MySQL 8.0+ 环境搭建（Docker 方式 + 本地安装方式）
- 使用 mysql 命令行连接服务器并执行基本操作
- 了解 information_schema 系统库的作用

## 理论知识讲解

### 1. 数据库演进：从文件到 DBMS

早期数据存储依赖操作系统文件（如 `.txt`、`.csv`、`.json`），随着数据量与并发量增长，文件方案的缺陷逐渐暴露：

| 维度 | 文件存储 | 数据库管理系统（DBMS） |
| --- | --- | --- |
| 并发控制 | 自行加锁，易冲突 | 引擎层自动行锁/表锁 |
| 数据一致性 | 应用层保证 | 事务 ACID 保证 |
| 查询能力 | 全文件扫描 | 索引、优化器、SQL 查询 |
| 安全权限 | 文件系统权限 | 用户/库/表/列级权限 |
| 备份恢复 | 手动复制 | binlog / mysqldump / PITR |

数据库管理系统（DBMS）正是为了解决这些问题而诞生。按数据组织模型可分为：

- **关系型数据库（RDBMS）**：以二维表组织数据，表之间通过外键建立关系，使用 SQL 操作。代表：MySQL、PostgreSQL、Oracle、SQL Server。
- **非关系型数据库（NoSQL）**：以键值、文档、列族、图等结构组织数据，弱化一致性、强调扩展性。代表：Redis（KV）、MongoDB（文档）、Cassandra（列族）、Neo4j（图）。

实际项目中常**混合使用**：核心交易数据存 MySQL，缓存与计数存 Redis，日志/半结构化数据存 MongoDB。

### 2. 关系型数据库核心概念

| 概念 | 说明 | 示例 |
| --- | --- | --- |
| 表（Table） | 数据的二维结构，由行和列组成 | `users` 用户表 |
| 行（Row / Record） | 表中一条记录，对应一个实体 | 一个用户 |
| 列（Column / Field） | 表中一个字段，所有行共享同一列定义 | `email` 列 |
| 主键（Primary Key） | 唯一标识一行，非空且唯一 | `id` |
| 外键（Foreign Key） | 引用其他表主键，建立表间关系 | `orders.user_id` → `users.id` |
| 索引（Index） | 提升查询速度的辅助结构，以空间换时间 | 在 `email` 上建唯一索引 |
| 约束（Constraint） | 限制列取值规则，保证数据完整性 | `NOT NULL` / `UNIQUE` / `CHECK` |

**表间关系**有三种基本形式：

- **一对一（1:1）**：一个用户对应一个账户详情，建表时把外键设为 `UNIQUE`。
- **一对多（1:N）**：最常见，一个用户对应多个订单，在“多”的一方加外键。
- **多对多（M:N）**：通过中间表实现，如用户与角色，中间表 `user_role(user_id, role_id)`。

### 3. 主流 RDBMS 与 MySQL 的地位

| 数据库 | 厂商 | 特点 | 典型场景 |
| --- | --- | --- | --- |
| MySQL | Oracle | 开源、轻量、生态成熟 | 互联网 Web 应用、中小型业务 |
| PostgreSQL | 社区 | 开源、功能强、标准严格 | 复杂查询、GIS、数据分析 |
| Oracle | Oracle | 商业、功能全面、昂贵 | 金融、电信、大型企业 |
| SQL Server | Microsoft | 商业、与 Windows 生态深度整合 | 企业内部系统、.NET 项目 |

MySQL 因其**开源免费、部署简单、性能稳定、社区活跃**，长期占据开源数据库市场份额第一，是后端工程师必备技能。

### 4. SQL 语言分类

SQL（Structured Query Language）是操作关系型数据库的标准语言，按功能分为五大类：

| 类别 | 全称 | 作用 | 代表语句 | 本板块章节 |
| --- | --- | --- | --- | --- |
| DDL | Data Definition Language | 定义结构 | `CREATE` / `ALTER` / `DROP` | Day02 |
| DML | Data Manipulation Language | 操作数据 | `INSERT` / `UPDATE` / `DELETE` | Day04 |
| DQL | Data Query Language | 查询数据 | `SELECT` | 后续查询天 |
| DCL | Data Control Language | 权限控制 | `GRANT` / `REVOKE` | 后续进阶 |
| TCL | Transaction Control Language | 事务控制 | `BEGIN` / `COMMIT` / `ROLLBACK` | 后续事务天 |

> 也有教材把 DQL 归入 DML，本教程为便于学习将其单独列出。

### 5. MySQL 版本演进

| 版本 | 发布年份 | 关键特性 | 维护状态 |
| --- | --- | --- | --- |
| 5.7 | 2015 | JSON 初步支持、性能优化 | 已 EOL |
| 8.0 | 2018 | 窗口函数、CTE、不可见索引、降序索引、JSON 增强、角色权限 | 长期支持 |
| 8.4 LTS | 2024 | 8.x 系列长期支持版 | 当前 LTS |

**MySQL 8.0 重要特性**：

- **窗口函数（Window Functions）**：`ROW_NUMBER()`、`RANK()`、`SUM() OVER()` 等，无需自连接即可排名、累计。
- **公共表表达式（CTE）**：`WITH` 子句，简化复杂查询与递归查询。
- **不可见索引（Invisible Index）**：可临时隐藏索引观察优化器行为，安全评估删除。
- **降序索引**：`INDEX(col DESC)` 真正生效（5.7 仅语法兼容）。
- **JSON 增强**：`JSON_TABLE()`、`JSON_ARRAYAGG()` 等。
- **角色（Role）**：可创建角色批量授权，简化权限管理。
- **默认字符集改为 utf8mb4**：5.7 默认 latin1，8.0 默认 utf8mb4。

> 本教程所有脚本基于 **MySQL 8.0+**，建议使用 8.4 LTS。

### 6. 存储引擎：InnoDB vs MyISAM

存储引擎决定数据如何存储、如何索引、是否支持事务。MySQL 通过 `SHOW ENGINES` 可查看支持的引擎。

| 维度 | InnoDB（8.0 默认） | MyISAM（5.5 前默认） |
| --- | --- | --- |
| 事务支持 | 支持 ACID 事务 | 不支持事务 |
| 锁粒度 | 行锁（高并发优） | 表锁（并发差） |
| 外键 | 支持 | 不支持 |
| 崩溃恢复 | 支持（redo log） | 不支持，易损坏 |
| 全文索引 | 5.6+ 支持 | 支持 |
| 适用场景 | OLTP 交易系统 | 只读历史归档（已不推荐） |

**为什么默认 InnoDB**：现代业务几乎都需要事务与高并发，InnoDB 是唯一支持 ACID 事务的内置引擎，5.5 起即为默认。除非特殊归档场景，**永远选 InnoDB**。

### 7. 客户端工具

| 工具 | 类型 | 特点 |
| --- | --- | --- |
| mysql | 命令行 | 官方自带，轻量，必学 |
| MySQL Workbench | GUI | 官方图形客户端，跨平台 |
| DBeaver | GUI | 开源、支持多数据库、免费 |
| Navicat | GUI | 商业、功能强大、收费 |
| DataGrip | GUI | JetBrains 出品、智能提示、收费 |

> 命令行 `mysql` 是基础，务必熟练；GUI 工具按个人喜好选择，本教程示例均可在命令行执行。

## 环境搭建

本教程提供两种安装方式，**推荐 Docker 方式**（隔离干净、可重置）。

### 方式一：Docker 部署（推荐）

前置条件：已安装 Docker Desktop（Windows/Mac）或 Docker Engine（Linux）。

```bash
# 1. 拉取 MySQL 8.4 LTS 镜像
docker pull mysql:8.4

# 2. 启动容器（端口 3306，root 密码 root123）
#    挂载数据卷避免数据丢失；字符集默认 utf8mb4
docker run -d \
  --name mysql84 \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=ecommerce \
  -v mysql84-data:/var/lib/mysql \
  --restart=unless-stopped \
  mysql:8.4 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci

# 3. 查看容器状态
docker ps
docker logs mysql84

# 4. 进入容器执行 mysql 命令行
docker exec -it mysql84 mysql -uroot -proot123

# 5. 进入容器后可执行 SOURCE 脚本
mysql> SOURCE /path/to/00-environment-check.sql
#    或在宿主机执行:
docker exec -i mysql84 mysql -uroot -proot123 < 00-environment-check.sql

# 6. 停止 / 启动 / 删除容器
docker stop mysql84
docker start mysql84
docker rm -f mysql84   # 注意：不会删除数据卷 mysql84-data
docker volume rm mysql84-data   # 彻底清除数据
```

> 在 Windows PowerShell 中换行使用反引号 `` ` ``，Linux/Mac 使用反斜杠 `\`。

### 方式二：本地安装

**Windows**：

1. 访问 https://dev.mysql.com/downloads/installer/ 下载 MySQL Installer。
2. 选择 "Server only" 或 "Custom" 安装 MySQL Server 8.4。
3. 配置时选择 "Use Strong Password Encryption"。
4. 设置 root 密码（建议 `root123` 便于练习，生产环境务必复杂）。
5. 将 MySQL 服务设为 Windows 服务，开机自启。
6. 把 `C:\Program Files\MySQL\MySQL Server 8.4\bin` 加入 PATH。

**Linux（Ubuntu/Debian）**：

```bash
# 1. 更新 apt 源并安装
sudo apt update
sudo apt install mysql-server-8.4

# 2. 初始化安全配置
sudo mysql_secure_installation

# 3. 登录（Ubuntu 默认 root 走 auth_socket，需切到 mysql_native_password 或新建用户）
sudo mysql
# 在 mysql 内创建练习用户:
# CREATE USER 'dev'@'%' IDENTIFIED BY 'dev123';
# GRANT ALL PRIVILEGES ON *.* TO 'dev'@'%';
# FLUSH PRIVILEGES;
```

**Mac（Homebrew）**：

```bash
brew install mysql@8.4
brew services start mysql@8.4
mysql -uroot
```

### 验证安装

```bash
mysql -u root -p
# 输入密码后进入 mysql 提示符

mysql> SELECT VERSION();
+-----------+
| VERSION() |
+-----------+
| 8.4.x     |
+-----------+
```

看到 `8.4.x` 表示安装成功。

## 连接与基本操作

### 连接服务器

```bash
# 基本连接
mysql -u root -p

# 指定主机与端口
mysql -h 127.0.0.1 -P 3306 -u root -p

# 直接连接到指定库
mysql -u root -p ecommerce

# 指定默认字符集（避免中文乱码）
mysql -u root -p --default-character-set=utf8mb4
```

### 常用元命令（以 `\` 开头）

| 命令 | 作用 |
| --- | --- |
| `\s` | 查看服务器状态（版本、字符集、连接信息） |
| `\G` | 纵向显示结果（每行一列），适合宽表 |
| `\c` | 取消当前正在输入的 SQL |
| `\q` | 退出 mysql 客户端 |
| `\d` | 修改语句结束符（如改成 `//` 写存储过程） |
| `help` | 查看帮助，`help contents` 查看分类 |

### 基本操作演示

```sql
-- 查看所有数据库
SHOW DATABASES;

-- 切换到 ecommerce 库
USE ecommerce;

-- 查看当前库的所有表
SHOW TABLES;

-- 查看表结构（字段、类型、键）
DESC users;

-- 查看建表语句（含字符集、引擎、注释）
SHOW CREATE TABLE users\G

-- 查看当前用户与库
SELECT CURRENT_USER(), DATABASE();

-- 查看服务器状态
\s
```

## information_schema 简介

`information_schema` 是 MySQL 自带的元数据信息库，以视图形式提供数据库、表、列、索引、字符集等元信息。**只读**，不可修改。

常用查询示例：

```sql
-- 1. 查看所有用户库的表数量
SELECT table_schema AS 库, COUNT(*) AS 表数量
FROM information_schema.tables
WHERE table_schema NOT IN ('information_schema','mysql','performance_schema','sys')
GROUP BY table_schema;

-- 2. 查看某库所有表及其引擎、行数（行数为估算值）
SELECT table_name AS 表名, engine AS 引擎, table_rows AS 估算行数, table_comment AS 注释
FROM information_schema.tables
WHERE table_schema = 'ecommerce';

-- 3. 查找包含 'email' 字段的所有表与列
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'ecommerce' AND column_name LIKE '%email%';

-- 4. 查看所有字符集及其最大字节长度
SELECT charset, description, maxlen
FROM information_schema.character_sets
ORDER BY charset;

-- 5. 查看 ecommerce 库所有索引
SELECT table_name, index_name, column_name, non_unique
FROM information_schema.statistics
WHERE table_schema = 'ecommerce'
ORDER BY table_name, index_name, seq_in_index;
```

> 实际工作中，`information_schema` 是排查“某字段在哪些表出现”、“哪些表没用 InnoDB”等元信息问题的利器。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/00-environment-check.sql` | 环境检查：版本、字符集、引擎、SQL 模式、连接数等 |
| `Code/01-hello-sql.sql` | 第一个 SQL：建库建表、增查改删、删表删库完整流程 |
| `README.md` | 本章理论文档与环境配置指南 |

执行方式（在 mysql 客户端内）：

```sql
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day01/Code/00-environment-check.sql;
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day01/Code/01-hello-sql.sql;
```

## 关键知识点总结

1. **数据库演进**：文件存储 → DBMS，关系型（MySQL）与 NoSQL（Redis/Mongo）互补。
2. **核心概念**：表/行/列/主键/外键/索引/约束；关系分 1:1、1:N、M:N。
3. **SQL 五类**：DDL（结构）、DML（数据）、DQL（查询）、DCL（权限）、TCL（事务）。
4. **MySQL 版本**：推荐 8.0+ 或 8.4 LTS，支持窗口函数、CTE、JSON 增强。
5. **存储引擎**：默认 InnoDB，支持事务、行锁、外键、崩溃恢复；MyISAM 已不推荐。
6. **字符集**：8.0 默认 utf8mb4，能完整支持 4 字节 emoji（utf8 实为 utf8mb3 不能）。
7. **客户端**：`mysql` 命令行是基础；GUI 可选 Workbench / DBeaver / Navicat / DataGrip。
8. **元命令**：`\s` 看状态、`\G` 纵向显示、`\c` 取消、`\q` 退出。
9. **information_schema**：只读元数据库，查表/列/索引/字符集的利器。

## 实战练习

1. **环境就绪验证**
   - 用 Docker 启动 MySQL 8.4 容器，root 密码设为 `root123`。
   - 用 `mysql -uroot -proot123` 连入，执行 `SELECT VERSION();` 确认版本。
   - 执行 `SOURCE` 加载 `00-environment-check.sql`，截图保留字符集、引擎、SQL 模式三项结果。

2. **元命令练习**
   - 连入 mysql 后，依次执行：`\s`、`SHOW DATABASES;`、`USE mysql;`、`SHOW TABLES;`、`DESC user;`。
   - 输入一条未写完的 SQL `SELECT * FROM user` 然后按 `\c` 取消，观察行为。
   - 执行 `SELECT * FROM mysql.user\G` 体会纵向显示与横向显示的区别。

3. **information_schema 查询**
   - 编写一条 SQL，统计 `mysql` 系统库中表的数量。
   - 编写一条 SQL，列出 `information_schema.character_sets` 中 `maxlen = 4` 的所有字符集。
   - 编写一条 SQL，查找当前服务器上所有引擎不是 InnoDB 的用户表（`table_schema` 排除系统库）。
