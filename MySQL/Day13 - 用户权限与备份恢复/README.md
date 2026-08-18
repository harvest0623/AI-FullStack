# Day13 - 用户权限与备份恢复

权限分配是数据库安全的底线：一个被过度授权的应用账号，可能因为一条 `DELETE` 语句清空整张表。备份是数据生命线的最后一道防线：当磁盘损坏、误删数据、勒索病毒来袭时，备份是唯一能让你睡得着的东西。本章覆盖 MySQL 的用户管理、权限体系、角色机制，以及完整的备份恢复方案——从 `mysqldump` 逻辑备份到 `binlog` 按时间点恢复，再到主从复制与备份策略。

## 学习目标

- 理解 MySQL 权限体系：用户@主机、mysql 系统库的权限表结构
- 能创建、修改、删除用户，掌握密码策略与主机通配符
- 熟练使用 GRANT / REVOKE / SHOW GRANTS 管理权限，理解权限层级
- 掌握 MySQL 8 角色机制，能用角色简化权限管理
- 理解最小权限原则，能为应用账号、只读账号、DBA 账号设计合理权限
- 熟练使用 mysqldump 进行整库、单表、仅结构、仅数据等备份
- 理解 binlog 的作用，能用 mysqlbinlog 做按时间点恢复
- 了解物理备份、主从复制、3-2-1 备份策略

---

## 理论知识讲解

### 1. MySQL 权限体系

#### 1.1 用户身份：用户名@主机

MySQL 的用户身份由**用户名 + 主机名**两部分组成，缺一不可。同一个用户名从不同主机连接，可以有不同的密码与权限。

```
'root'@'localhost'         # 仅本机
'app'@'192.168.1.100'      # 单一 IP
'reader'@'192.168.%.%'      # 192.168.x.x 网段
'writer'@'%'                # 任意主机（最宽松，生产慎用）
```

#### 1.2 mysql 系统库的权限表

| 表 | 作用 |
|------|------|
| `user` | 全局权限 + 用户账号 + 密码 + 资源限制 |
| `db` | 库级权限 |
| `tables_priv` | 表级权限 |
| `columns_priv` | 列级权限 |
| `procs_priv` | 存储过程/函数权限 |
| `roles_edges` | 角色与用户的映射关系 |

> 验证流程：连接时查 `user` → 选中库后查 `db` → 操作表时查 `tables_priv` → 操作列时查 `columns_priv`，权限累加但**不覆盖**。

---

### 2. 用户管理

#### 2.1 创建用户

```sql
-- 创建用户（必须带 IDENTIFIED BY 设置密码）
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'App@123456';

-- 主机通配符
CREATE USER 'reader'@'192.168.%.%' IDENTIFIED BY 'Reader@123';
CREATE USER 'global_user'@'%' IDENTIFIED BY 'Global@123';
```

#### 2.2 修改密码

```sql
-- ALTER USER（推荐）
ALTER USER 'app_user'@'localhost' IDENTIFIED BY 'NewPass@789';

-- 当前用户改自己密码
ALTER USER USER() IDENTIFIED BY 'MyNew@123';

-- SET PASSWORD（旧语法，8.0 仍可用）
SET PASSWORD FOR 'app_user'@'localhost' = 'Pass@123';
```

#### 2.3 重命名用户

```sql
RENAME USER 'app_user'@'localhost' TO 'app'@'192.168.1.%';
```

#### 2.4 删除用户

```sql
DROP USER IF EXISTS 'app_user'@'localhost';
```

#### 2.5 密码策略 validate_password

MySQL 8.0 默认安装 `validate_password` 组件，密码必须满足策略：

```sql
-- 查看密码策略
SHOW VARIABLES LIKE 'validate_password%';
```

| 变量 | 含义 | 典型值 |
|------|------|------|
| `validate_password.policy` | 策略等级 | 0=LOW / 1=MEDIUM / 2=STRONG |
| `validate_password.length` | 最小长度 | 8 |
| `validate_password.mixed_case_count` | 大小写字母各几个 | 1 |
| `validate_password.number_count` | 数字个数 | 1 |
| `validate_password.special_char_count` | 特殊字符个数 | 1 |

> MEDIUM（默认）要求：长度≥8、含大小写字母、含数字、含特殊字符。例如 `App@123456` 满足。

---

### 3. 权限管理

#### 3.1 GRANT 授权

```sql
-- 授予库级权限
GRANT SELECT, INSERT, UPDATE, DELETE ON ecommerce.* TO 'app'@'192.168.1.%';

-- 授予表级权限
GRANT SELECT ON ecommerce.products TO 'reader'@'%';

-- 授予列级权限（罕见，仅暴露部分列）
GRANT SELECT (id, name, price) ON ecommerce.products TO 'analyst'@'%';

-- 授予全局权限（管理员级，慎用）
GRANT ALL PRIVILEGES ON *.* TO 'dba'@'localhost';

-- 授予并允许该用户再授权给别人
GRANT SELECT ON ecommerce.* TO 'lead'@'%' WITH GRANT OPTION;
```

#### 3.2 REVOKE 撤销权限

```sql
-- 撤销部分权限
REVOKE INSERT, DELETE ON ecommerce.* FROM 'app'@'192.168.1.%';

-- 撤销所有权限
REVOKE ALL PRIVILEGES, GRANT OPTION ON *.* FROM 'dba'@'localhost';
```

#### 3.3 SHOW GRANTS 查看权限

```sql
-- 查看指定用户
SHOW GRANTS FOR 'app'@'192.168.1.%';

-- 查看当前用户
SHOW GRANTS;
```

#### 3.4 权限层级

| 层级 | 语法 | 适用范围 |
|------|------|---------|
| 全局 | `ON *.*` | 所有库所有表 |
| 库级 | `ON db.*` | 某库所有表 |
| 表级 | `ON db.table` | 某张表 |
| 列级 | `ON db.table(col1,col2)` | 表的某些列 |
| 例程级 | `ON PROCEDURE db.proc` | 存储过程/函数 |

#### 3.5 常用权限速查

| 权限 | 作用 |
|------|------|
| `ALL [PRIVILEGES]` | 所有权限（除 GRANT OPTION） |
| `SELECT` / `INSERT` / `UPDATE` / `DELETE` | 基础 CRUD |
| `CREATE` / `DROP` / `ALTER` / `INDEX` | DDL |
| `REFERENCES` | 外键 |
| `GRANT OPTION` | 允许该用户授权 |
| `RELOAD` | FLUSH 操作 |
| `PROCESS` | 查看进程 |
| `SUPER` | 高级管理（8.0 已细分为多个） |
| `REPLICATION CLIENT` | 查看主从状态 |
| `REPLICATION SLAVE` | 作为从库复制 |
| `SHOW VIEW` | 查看视图定义 |
| `EXECUTE` | 执行存储过程 |
| `CREATE ROUTINE` / `ALTER ROUTINE` | 创建/修改存储过程 |
| `TRIGGER` / `EVENT` | 触发器/事件 |

#### 3.6 WITH GRANT OPTION

被授予 `WITH GRANT OPTION` 的用户，可把自己拥有的权限再授予他人。**这相当于"权限传递能力"，生产环境慎用**，否则权限会失控扩散。

---

### 4. 角色（MySQL 8）

#### 4.1 角色的价值

没用角色时：100 个应用账号要改权限，得逐个 GRANT。用角色后：把权限授予角色，再把角色授予用户，改权限只需改一次角色。

#### 4.2 角色操作

```sql
-- 创建角色
CREATE ROLE 'role_app', 'role_reader', 'role_dba';

-- 给角色授权（语法同用户）
GRANT SELECT, INSERT, UPDATE, DELETE ON ecommerce.* TO 'role_app';
GRANT SELECT ON ecommerce.* TO 'role_reader';
GRANT ALL PRIVILEGES ON *.* TO 'role_dba';

-- 把角色授予用户
GRANT 'role_app' TO 'app01'@'%', 'app02'@'%';
GRANT 'role_reader' TO 'analyst01'@'%';

-- 设置默认角色（用户连接后自动激活的角色）
SET DEFAULT ROLE 'role_app' TO 'app01'@'%';

-- 查看用户角色
SHOW GRANTS FOR 'app01'@'%';           -- 用户直接权限
SHOW GRANTS FOR 'app01'@'%' USING 'role_app';  -- 包含角色后的有效权限
```

#### 4.3 角色激活

用户连接后，角色默认**不会自动激活**（除非设置了 `SET DEFAULT ROLE`）。手动激活：

```sql
-- 当前会话激活角色
SET ROLE 'role_app';

-- 查看当前激活的角色
SELECT CURRENT_ROLE();
```

---

### 5. 最小权限原则

| 账号类型 | 推荐权限 | 说明 |
|---------|---------|------|
| 应用账号 | `SELECT, INSERT, UPDATE, DELETE` ON 业务库 | 仅 CRUD，不给 DDL |
| 只读账号 | `SELECT` ON 业务库 | 报表/分析用 |
| DBA 账号 | `ALL ON *.*` + `WITH GRANT OPTION` | 仅 DBA，localhost 限制 |
| 备份账号 | `SELECT, RELOAD, LOCK TABLES, REPLICATION CLIENT, SHOW VIEW, EVENT, TRIGGER` | mysqldump 必需 |
| 从库账号 | `REPLICATION SLAVE` | 主从复制专用 |

> **铁律**：root 不外用，应用账号绝不给 `DROP/ALTER/CREATE`，线上禁用 `GRANT OPTION`。

---

### 6. 备份恢复

#### 6.1 逻辑备份 mysqldump

```bash
# 备份整库（含建表与数据）
mysqldump -u root -p ecommerce > ecommerce.sql

# 备份单表
mysqldump -u root -p ecommerce users > users.sql

# 仅结构（-d / --no-data）
mysqldump -u root -p -d ecommerce > ecommerce_schema.sql

# 仅数据（-t / --no-create-info）
mysqldump -u root -p -t ecommerce > ecommerce_data.sql

# 条件备份
mysqldump -u root -p ecommerce orders --where="created_at > '2025-01-01'" > recent_orders.sql

# 一致性备份（InnoDB 事务快照，不锁表）
mysqldump -u root -p --single-transaction ecommerce > ecommerce.sql

# 含存储过程与触发器
mysqldump -u root -p --routines --triggers ecommerce > ecommerce_full.sql

# 备份所有库
mysqldump -u root -p --all-databases > all.sql
```

#### 6.2 恢复

```bash
# 方式一：命令行重定向
mysql -u root -p ecommerce < ecommerce.sql

# 方式二：mysql 客户端内 source
mysql> USE ecommerce;
mysql> SOURCE /path/to/ecommerce.sql;
```

#### 6.3 物理备份 vs 逻辑备份

| 维度 | 逻辑备份 (mysqldump) | 物理备份 (xtrabackup) |
|------|---------------------|---------------------|
| 输出 | SQL 文本 | 数据文件拷贝 |
| 速度 | 慢（要 SELECT + 生成 SQL） | 快（直接拷文件） |
| 体积 | 大（文本+SQL 语法） | 小（接近原数据） |
| 恢复 | 慢（要逐条 INSERT） | 快（拷回即可） |
| 跨版本 | 好（SQL 通用） | 差（绑定版本与引擎） |
| 锁表 | InnoDB 用 --single-transaction 不锁 | 不锁 |
| 工具 | 自带 | Percona XtraBackup |

#### 6.4 binlog 二进制日志

binlog 记录所有**写操作**（DDL + DML），用于：

- 增量恢复：从全量备份点之后，按 binlog 重放到任意时间点
- 主从复制：从库读取主库 binlog 重放

```sql
-- 查看是否开启 binlog
SHOW VARIABLES LIKE 'log_bin';
SHOW VARIABLES LIKE 'binlog_format';

-- 查看当前 binlog 文件与位置
SHOW MASTER STATUS;

-- 查看 binlog 列表
SHOW BINARY LOGS;

-- 查看某 binlog 内容（SQL 形式）
SHOW BINLOG EVENTS IN 'mysql-bin.000001' LIMIT 20;
```

```bash
# 用 mysqlbinlog 工具查看 / 导出
mysqlbinlog --start-datetime="2025-07-01 00:00:00" \
            --stop-datetime="2025-07-01 12:00:00" \
            mysql-bin.000001 > replay.sql

# 按时间点恢复（先恢复全量，再重放 binlog）
mysql -u root -p ecommerce < full_backup.sql
mysql -u root -p ecommerce < replay.sql

# 按 position 恢复（更精确）
mysqlbinlog --start-position=154 --stop-position=1024 mysql-bin.000001 | mysql -u root -p
```

#### 6.5 按时间点恢复流程

误删数据后，"按时间点恢复"的标准流程：

1. 立即停止业务写入，避免新数据覆盖 binlog
2. 用最近的**全量备份**恢复到一个临时库
3. 用 `mysqlbinlog` 导出全量备份点到误操作点之间的 binlog
4. 把 binlog 重放到临时库
5. 从临时库导出丢失的数据，回灌到生产库

#### 6.6 mysqldumpslow 慢查询分析

```bash
# 慢查询日志默认关闭，开启方式
# my.cnf: slow_query_log=1, long_query_time=1, slow_query_log_file=/var/log/mysql/slow.log

# 用 mysqldumpslow 分析
mysqldumpslow -s t -t 10 /var/log/mysql/slow.log
# -s t 按总时间排序
# -t 10 取前 10 条
# -s c 按次数, -s r 按平均行数

# 配合 EXPLAIN 优化慢 SQL
```

#### 6.7 xtrabackup（物理备份）

Percona XtraBackup 是开源物理备份工具：

```bash
# 全量备份
xtrabackup --backup --target-dir=/backup/full -u root -p

# 准备（apply-log）
xtrabackup --prepare --target-dir=/backup/full

# 增量备份
xtrabackup --backup --target-dir=/backup/inc1 \
           --incremental-basedir=/backup/full -u root -p

# 恢复（拷回数据目录）
xtrabackup --copy-back --target-dir=/backup/full
chown -R mysql:mysql /var/lib/mysql
systemctl start mysqld
```

---

### 7. 主从复制原理简介

```
主库写 binlog ──> 从库 IO 线程拉取 → relay log ──> 从库 SQL 线程重放
```

| 复制类型 | 说明 |
|---------|------|
| 异步复制 | 主库写完 binlog 即返回，不等从库确认（默认） |
| 半同步复制 | 主库至少等一个从库收到 binlog 才返回 |
| 组复制 MGR | 多主一致性，基于 Paxos 变体 |

> 主从延迟是异步复制的固有问题，金融场景常配半同步或组复制。

---

### 8. 备份策略

#### 8.1 3-2-1 原则

- **3** 份数据副本
- **2** 种不同介质（如硬盘 + 云存储）
- **1** 份异地存放

#### 8.2 全量+增量

| 周期 | 方式 | 说明 |
|------|------|------|
| 每日 | 全量 mysqldump | 凌晨低峰执行 |
| 每小时 | binlog 归档 | 增量恢复用 |
| 每周 | xtrabackup 物理全量 | 大库快速恢复 |

#### 8.3 定期演练

> **没演练过的备份等于没备份**。每季度至少做一次完整恢复演练，验证备份可用、流程顺畅、时间可控。

---

## 关键知识点总结

### 权限层级速查表

| 层级 | 语法 | 示例 |
|------|------|------|
| 全局 | `ON *.*` | `GRANT SELECT ON *.* TO u@h` |
| 库级 | `ON db.*` | `GRANT ALL ON ecommerce.* TO u@h` |
| 表级 | `ON db.tbl` | `GRANT SELECT ON ecommerce.users TO u@h` |
| 列级 | `ON db.tbl(c1,c2)` | `GRANT SELECT(id,name) ON ecommerce.users TO u@h` |
| 例程 | `ON PROCEDURE/FUNCTION db.routine` | `GRANT EXECUTE ON PROCEDURE ecommerce.sp_x TO u@h` |

### 常用权限速查表

| 权限 | 说明 | 典型授予对象 |
|------|------|------------|
| SELECT/INSERT/UPDATE/DELETE | CRUD | 应用账号 |
| CREATE/DROP/ALTER/INDEX | DDL | DBA |
| ALL PRIVILEGES | 所有 | DBA |
| GRANT OPTION | 可再授权 | 主管账号 |
| RELOAD | FLUSH | 运维 |
| PROCESS | 看进程 | 监控 |
| REPLICATION CLIENT | 看主从状态 | 监控 |
| REPLICATION SLAVE | 拉取 binlog | 从库 |
| SHOW VIEW | 查看视图 | 分析 |
| EXECUTE | 执行过程/函数 | 应用 |

### 备份方式对比表

| 方式 | 工具 | 速度 | 体积 | 恢复速度 | 跨版本 | 一致性 |
|------|------|------|------|---------|------|------|
| 逻辑备份 | mysqldump | 慢 | 大 | 慢 | 好 | --single-transaction |
| 物理备份 | xtrabackup | 快 | 小 | 快 | 差 | 不锁 |
| binlog 增量 | mysqlbinlog | - | 小 | 精确到点 | - | - |

### mysqldump 常用参数表

| 参数 | 作用 |
|------|------|
| `-u root -p` | 账号密码 |
| `--single-transaction` | InnoDB 一致性快照不锁表 |
| `--routines` | 含存储过程/函数 |
| `--triggers` | 含触发器 |
| `--events` | 含事件 |
| `--databases db1 db2` | 指定多个库 |
| `--all-databases` | 全部库 |
| `-d / --no-data` | 仅结构 |
| `-t / --no-create-info` | 仅数据 |
| `--where="条件"` | 条件导出 |
| `--master-data=2` | 记录 binlog 位置（注释） |
| `--flush-logs` | 备份后切新 binlog |
| `--quick` | 大表不缓存到内存（默认开启） |
| `--default-character-set=utf8mb4` | 指定字符集 |

---

## 代码文件说明

| 文件 | 内容 |
|------|------|
| `Code/01-user-privilege.sql` | 用户与权限演示：创建应用账号、授予 SELECT/INSERT/UPDATE、创建只读账号、创建角色并分配、SHOW GRANTS、REVOKE 演示、最小权限实践 |
| `Code/02-backup-restore.md` | 备份恢复操作指南：mysqldump 各场景命令、恢复步骤、binlog 查看与按时间点恢复、mysqldumpslow 使用、完整演练流程 |

> 注意：用户权限类 SQL 需要 root 权限执行；部分操作会真实创建账号，请按需删除或保留。

---

## 实战练习

### 练习一：设计三个角色并分配权限

设计 `role_app`（应用，CRUD）、`role_analyst`（分析师，只读 + SHOW VIEW）、`role_dba`（DBA，全权限）三个角色，分别授予对应的 `ecommerce` 库权限。然后创建三个用户 `app01`、`analyst01`、`dba01` 并分配角色，设置默认角色，最后用 `SHOW GRANTS ... USING` 验证有效权限。

### 练习二：完整的备份恢复演练

1. 用 `mysqldump --single-transaction` 备份 `ecommerce` 库到文件
2. 在 `users` 表故意"误删"一条记录，记下当前 binlog position
3. 用全量备份恢复到一个临时库 `ecommerce_restore`
4. 用 `mysqlbinlog` 从全量备份点到误删点导出 binlog，重放到临时库
5. 从临时库找出被删的记录，回灌到生产库

### 练习三：慢查询分析

开启慢查询日志（`long_query_time=1`），构造一条慢 SQL（如全表扫描 + 大量 `LIKE '%xx%'`），用 `mysqldumpslow` 统计 Top 慢查询，再用 EXPLAIN 分析并优化（加索引或改写 SQL）。
