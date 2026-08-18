# 备份恢复操作指南

> 本文档配套 `Day13 - 用户权限与备份恢复`，提供 MySQL 备份恢复的完整命令清单与演练流程。所有命令在 Linux/macOS/Windows 通用，路径按需调整。

---

## 1. mysqldump 逻辑备份

### 1.1 整库备份（最常用）

```bash
# 含建表语句 + 数据，InnoDB 用 --single-transaction 不锁表
mysqldump -u root -p --single-transaction --default-character-set=utf8mb4 \
          --routines --triggers --events \
          ecommerce > ecommerce_$(date +%Y%m%d).sql
```

### 1.2 单表备份

```bash
mysqldump -u root -p --single-transaction ecommerce users > users_$(date +%Y%m%d).sql
```

### 1.3 多表备份

```bash
mysqldump -u root -p --single-transaction ecommerce users orders order_items > core_tables.sql
```

### 1.4 仅结构（不含数据）

```bash
# -d 等价于 --no-data
mysqldump -u root -p -d --single-transaction ecommerce > ecommerce_schema.sql
```

### 1.5 仅数据（不含建表）

```bash
# -t 等价于 --no-create-info
mysqldump -u root -p -t --single-transaction ecommerce > ecommerce_data.sql
```

### 1.6 条件备份（按 WHERE）

```bash
# 仅备份 2025 年的订单
mysqldump -u root -p --single-transaction ecommerce orders \
          --where="created_at >= '2025-01-01' AND created_at < '2026-01-01'" \
          > orders_2025.sql
```

### 1.7 备份所有库

```bash
mysqldump -u root -p --all-databases --single-transaction --routines --triggers --events \
          > all_databases.sql
```

### 1.8 记录 binlog 位置（用于增量恢复）

```bash
# --master-data=2 把 binlog 文件与位置以注释形式写入备份文件开头
# =1 则是非注释的 CHANGE MASTER 语句（搭建从库用）
mysqldump -u root -p --single-transaction --master-data=2 --flush-logs \
          ecommerce > ecommerce_with_pos.sql
```

查看备份文件开头的 binlog 位置：

```bash
head -30 ecommerce_with_pos.sql | grep "CHANGE MASTER"
# 输出类似：-- CHANGE MASTER TO MASTER_LOG_FILE='mysql-bin.000010', MASTER_LOG_POS=154;
```

### 1.9 压缩备份（大库必备）

```bash
# 用 gzip 压缩，体积通常压缩到 1/5 ~ 1/10
mysqldump -u root -p --single-transaction ecommerce | gzip > ecommerce.sql.gz

# 解压恢复
gunzip < ecommerce.sql.gz | mysql -u root -p ecommerce
```

### 1.10 备份账号所需权限

```sql
-- 创建专用的备份账号
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'Backup@123456';
GRANT SELECT, RELOAD, LOCK TABLES, REPLICATION CLIENT, SHOW VIEW, EVENT, TRIGGER
ON *.* TO 'backup_user'@'localhost';
FLUSH PRIVILEGES;
```

用备份账号执行：

```bash
mysqldump -u backup_user -p --single-transaction ecommerce > ecommerce.sql
```

---

## 2. 恢复

### 2.1 命令行重定向恢复

```bash
mysql -u root -p ecommerce < ecommerce.sql
```

### 2.2 mysql 客户端内 source 恢复

```sql
-- 先建库（若备份文件不含 CREATE DATABASE）
CREATE DATABASE IF NOT EXISTS ecommerce DEFAULT CHARSET utf8mb4;
USE ecommerce;
SOURCE /path/to/ecommerce.sql;
```

### 2.3 恢复到不同库名

```bash
# 备份 ecommerce，恢复到 ecommerce_test
mysqldump -u root -p --single-transaction -d ecommerce > schema.sql
mysql -u root -p -e "CREATE DATABASE ecommerce_test DEFAULT CHARSET utf8mb4"
mysql -u root -p ecommerce_test < schema.sql

# 数据部分用 sed 替换库名（仅当备份含 USE 语句时）
mysqldump -u root -p -t --single-transaction ecommerce > data.sql
mysql -u root -p ecommerce_test < data.sql
```

### 2.4 恢复单表

```bash
# 从整库备份中提取某张表的语句
sed -n '/-- Current Database: `ecommerce`/,/-- Current Database:/p' all_databases.sql > ecommerce.sql

# 用 awk 提取单表（更精确）
awk '/-- Table structure for table `users`/,/-- Table structure for table/' ecommerce.sql > users_only.sql
mysql -u root -p ecommerce < users_only.sql
```

### 2.5 恢复时的注意事项

1. **字符集一致**：备份与目标库字符集需一致，建议加 `--default-character-set=utf8mb4`
2. **关闭外键检查**：恢复大表前可临时关闭外键检查加速
   ```sql
   SET FOREIGN_KEY_CHECKS = 0;
   SOURCE /path/to/backup.sql;
   SET FOREIGN_KEY_CHECKS = 1;
   ```
3. **关闭唯一性检查**：批量 INSERT 前关闭可加速
   ```sql
   SET UNIQUE_CHECKS = 0;
   -- 恢复数据
   SET UNIQUE_CHECKS = 1;
   ```
4. **大文件恢复**：用管道避免内存爆炸
   ```bash
   mysql -u root -p dbname < big_backup.sql
   # 而不是先 cat 再 source
   ```

---

## 3. binlog 二进制日志

### 3.1 开启 binlog

在 `my.cnf` / `my.ini` 的 `[mysqld]` 段加：

```ini
[mysqld]
log_bin           = mysql-bin
binlog_format     = ROW       # 推荐 ROW，最准确
expire_logs_days  = 7         # 保留 7 天
max_binlog_size   = 100M      # 单文件最大 100MB
server_id         = 1         # 主从复制必需
```

重启 MySQL 生效。

### 3.2 查看 binlog 状态

```sql
-- 是否开启
SHOW VARIABLES LIKE 'log_bin';
SHOW VARIABLES LIKE 'binlog_format';

-- 当前 binlog 文件与位置
SHOW MASTER STATUS;

-- 所有 binlog 文件列表
SHOW BINARY LOGS;

-- 查看某 binlog 的事件（SQL 形式）
SHOW BINLOG EVENTS IN 'mysql-bin.000001' LIMIT 20;
```

### 3.3 用 mysqlbinlog 工具查看

```bash
# 查看完整内容
mysqlbinlog mysql-bin.000001

# 按时间范围
mysqlbinlog --start-datetime="2025-07-01 00:00:00" \
            --stop-datetime="2025-07-01 12:00:00" \
            mysql-bin.000001

# 按 position
mysqlbinlog --start-position=154 --stop-position=1024 mysql-bin.000001

# 指定库
mysqlbinlog --database=ecommerce mysql-bin.000001

# 输出到文件
mysqlbinlog mysql-bin.000001 > binlog_replay.sql
```

### 3.4 按时间点恢复（PITR）

**典型场景**：中午 12:00 误删了 users 表，需恢复到 11:59:59 的状态。

**步骤**：

1. **立即停止业务写入**（避免新 binlog 覆盖）

2. **找到最近的完整备份**（假设是凌晨 2:00 的全量备份）

3. **查看全量备份记录的 binlog 位置**：
   ```bash
   head -30 ecommerce_full.sql | grep "CHANGE MASTER"
   # 假设输出：MASTER_LOG_FILE='mysql-bin.000010', MASTER_LOG_POS=154
   ```

4. **恢复全量备份到临时库**：
   ```bash
   mysql -u root -p -e "CREATE DATABASE ecommerce_restore DEFAULT CHARSET utf8mb4"
   mysql -u root -p ecommerce_restore < ecommerce_full.sql
   ```

5. **导出全量备份点到误删点之间的 binlog**：
   ```bash
   mysqlbinlog --start-position=154 \
               --stop-datetime="2025-07-27 11:59:59" \
               mysql-bin.000010 mysql-bin.000011 \
               > replay.sql
   ```

6. **重放 binlog 到临时库**：
   ```bash
   mysql -u root -p ecommerce_restore < replay.sql
   ```

7. **从临时库导出丢失数据回灌生产**：
   ```sql
   -- 临时库已有完整数据（到误删前）
   -- 从临时库导出到生产库
   INSERT INTO ecommerce.users
   SELECT * FROM ecommerce_restore.users
   WHERE id NOT IN (SELECT id FROM ecommerce.users);
   ```

### 3.5 binlog 格式对比

| 格式 | 说明 | 优缺点 |
|------|------|------|
| STATEMENT | 记录 SQL 语句 | 体积小，但 NOW()/RAND() 等不确定函数主从不一致 |
| ROW | 记录每行变更 | 体积大，但准确，主从一致（**推荐**） |
| MIXED | 混合 | 自动选择，折中 |

---

## 4. mysqldumpslow 慢查询分析

### 4.1 开启慢查询日志

在 `my.cnf` / `my.ini` 加：

```ini
[mysqld]
slow_query_log         = 1
slow_query_log_file    = /var/log/mysql/slow.log     # Linux
# slow_query_log_file  = D:/mysql/logs/slow.log       # Windows
long_query_time        = 1                             # 超过 1 秒记录
log_queries_not_using_indexes = 1                      # 未用索引也记录
```

运行时动态开启：

```sql
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';
```

### 4.2 用 mysqldumpslow 分析

```bash
# 按总耗时排序，取前 10
mysqldumpslow -s t -t 10 /var/log/mysql/slow.log

# 按次数排序
mysqldumpslow -s c -t 10 /var/log/mysql/slow.log

# 按平均行数排序
mysqldumpslow -s r -t 10 /var/log/mysql/slow.log

# 按平均耗时排序
mysqldumpslow -s at -t 10 /var/log/mysql/slow.log
```

| 参数 | 含义 |
|------|------|
| `-s t` | 按总时间排序 |
| `-s at` | 按平均时间排序 |
| `-s c` | 按次数排序 |
| `-s r` | 按总行数排序 |
| `-s ar` | 按平均行数排序 |
| `-t N` | 取前 N 条 |
| `-g pattern` | 正则过滤（如 `-g select` 只看 SELECT） |

### 4.3 输出示例解读

```
Count: 50  Time=2.30s (115s)  Lock=0.00s (0s)  Rows=1000.0 (50000)
  SELECT * FROM orders WHERE status = 'S' AND created_at LIKE 'S'
```

- `Count: 50`：执行了 50 次
- `Time=2.30s (115s)`：平均 2.3 秒，总耗时 115 秒
- `Rows=1000.0 (50000)`：平均返回 1000 行，总 50000 行
- `S`：字符串被替换为占位符（脱敏）

> 看到这条慢查询，应立刻想到：`created_at LIKE 'S%'` 是否可用索引？是否该改范围查询？

---

## 5. xtrabackup 物理备份（简介）

### 5.1 安装

```bash
# CentOS / RHEL
yum install percona-xtrabackup

# Ubuntu / Debian
apt install percona-xtrabackup
```

### 5.2 全量备份

```bash
xtrabackup --backup --target-dir=/backup/full \
           --user=root --password=YourPass
```

### 5.3 准备（apply-log，使备份一致）

```bash
xtrabackup --prepare --target-dir=/backup/full
```

### 5.4 增量备份

```bash
# 基于全量做增量
xtrabackup --backup --target-dir=/backup/inc1 \
           --incremental-basedir=/backup/full \
           --user=root --password=YourPass

# 基于增量做增量
xtrabackup --backup --target-dir=/backup/inc2 \
           --incremental-basedir=/backup/inc1 \
           --user=root --password=YourPass
```

### 5.5 恢复

```bash
# 1. 先 prepare 全量（合并增量）
xtrabackup --prepare --target-dir=/backup/full
xtrabackup --prepare --target-dir=/backup/full --incremental-dir=/backup/inc1
xtrabackup --prepare --target-dir=/backup/full --incremental-dir=/backup/inc2

# 2. 停 MySQL
systemctl stop mysqld

# 3. 拷回数据目录
xtrabackup --copy-back --target-dir=/backup/full

# 4. 改属主
chown -R mysql:mysql /var/lib/mysql

# 5. 启动
systemctl start mysqld
```

---

## 6. 主从复制配置

### 6.1 主库配置

`my.cnf`：

```ini
[mysqld]
server_id         = 1
log_bin           = mysql-bin
binlog_format     = ROW
binlog_do_db      = ecommerce    # 只记录 ecommerce 库（可选）
```

创建复制账号：

```sql
CREATE USER 'repl_user'@'192.168.%.%' IDENTIFIED BY 'Repl@123456';
GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'192.168.%.%';
FLUSH PRIVILEGES;

-- 查看主库状态
SHOW MASTER STATUS;
-- 记下 File 与 Position
```

### 6.2 从库配置

`my.cnf`：

```ini
[mysqld]
server_id         = 2
relay_log         = relay-bin
read_only         = 1            # 从库只读
```

设置主库信息并启动复制：

```sql
CHANGE REPLICATION SOURCE TO
    SOURCE_HOST='192.168.1.10',
    SOURCE_USER='repl_user',
    SOURCE_PASSWORD='Repl@123456',
    SOURCE_LOG_FILE='mysql-bin.000010',
    SOURCE_LOG_POS=154;

START REPLICA;     -- 8.0+ 新语法（旧：START SLAVE）
SHOW REPLICA STATUS\G
```

关键状态字段：

- `Slave_IO_Running: Yes`：IO 线程正常
- `Slave_SQL_Running: Yes`：SQL 线程正常
- `Seconds_Behind_Master: 0`：主从延迟秒数

---

## 7. 完整演练流程

### 7.1 演练目标

模拟"误删 users 表"，从备份完整恢复，验证 RTO < 30 分钟。

### 7.2 演练步骤

```bash
# 步骤 1：全量备份（凌晨）
mysqldump -u root -p --single-transaction --master-data=2 --flush-logs \
          --routines --triggers --events \
          ecommerce > /backup/ecommerce_full_$(date +%Y%m%d).sql

# 步骤 2：业务正常写入（产生 binlog）
mysql -u root -p ecommerce -e "
INSERT INTO users(id, username, email, role, status, created_at)
VALUES (800001, 'drill_user_1', 'd1@x.com', 'customer', 1, NOW());
INSERT INTO users(id, username, email, role, status, created_at)
VALUES (800002, 'drill_user_2', 'd2@x.com', 'customer', 1, NOW());
"

# 步骤 3：模拟误删（中午 12:00）
mysql -u root -p ecommerce -e "DROP TABLE users;"

# 步骤 4：查看备份中的 binlog 位置
head -30 /backup/ecommerce_full_*.sql | grep "CHANGE MASTER"
# 假设：MASTER_LOG_FILE='mysql-bin.000020', MASTER_LOG_POS=154

# 步骤 5：恢复全量到临时库
mysql -u root -p -e "CREATE DATABASE ecommerce_drill DEFAULT CHARSET utf8mb4"
mysql -u root -p ecommerce_drill < /backup/ecommerce_full_*.sql

# 步骤 6：导出全量备份点到误删点之间的 binlog
mysqlbinlog --start-position=154 \
            --stop-datetime="$(date '+%Y-%m-%d %H:%M:%S')" \
            mysql-bin.000020 \
            > /tmp/replay.sql

# 步骤 7：重放到临时库
mysql -u root -p ecommerce_drill < /tmp/replay.sql

# 步骤 8：验证临时库数据完整
mysql -u root -p ecommerce_drill -e "SELECT COUNT(*) FROM users;"

# 步骤 9：从临时库导出 users 表结构与数据回灌生产
mysqldump -u root -p ecommerce_drill users > /tmp/users_recovered.sql
mysql -u root -p ecommerce < /tmp/users_recovered.sql

# 步骤 10：验证生产库
mysql -u root -p ecommerce -e "SELECT COUNT(*) FROM users;"

# 清理
mysql -u root -p -e "DROP DATABASE ecommerce_drill"
rm /tmp/replay.sql /tmp/users_recovered.sql
```

### 7.3 演练记录表

| 项 | 计划 | 实际 |
|----|------|------|
| 备份可用性 | 可恢复 | □ |
| RTO（恢复时间目标） | < 30 分钟 | □ 分钟 |
| RPO（数据丢失量） | 0（含 binlog） | □ |
| 流程顺畅 | 无卡点 | □ |
| 责任人 | DBA | □ |

---

## 8. 备份策略建议

### 8.1 中小型库（< 50GB）

| 周期 | 方式 | 保留 |
|------|------|------|
| 每日 02:00 | mysqldump 全量 | 7 天 |
| 每小时 | binlog 归档 | 7 天 |
| 每周日 | 异地复制 | 4 周 |

### 8.2 大型库（> 50GB）

| 周期 | 方式 | 保留 |
|------|------|------|
| 每周日 02:00 | xtrabackup 物理全量 | 4 周 |
| 每日 02:00 | xtrabackup 增量 | 7 天 |
| 每小时 | binlog 归档 | 7 天 |
| 实时 | 主从复制 | - |

### 8.3 3-2-1 原则

- **3** 份数据副本（生产 + 本地备份 + 异地备份）
- **2** 种不同介质（如本地磁盘 + 对象存储 S3/OSS）
- **1** 份异地存放（异地机房或云存储）

### 8.4 自动化脚本示例

```bash
#!/bin/bash
# backup_ecommerce.sh - 电商库每日备份脚本

BACKUP_DIR=/backup/mysql
DATE=$(date +%Y%m%d)
DB=ecommerce
USER=root
PASS_FILE=/root/.my.cnf   # 把密码放 [client] 段，避免命令行暴露

# 全量备份
mysqldump --defaults-file=$PASS_FILE --single-transaction \
          --master-data=2 --routines --triggers --events \
          $DB | gzip > $BACKUP_DIR/${DB}_${DATE}.sql.gz

# 切新 binlog
mysqladmin --defaults-file=$PASS_FILE flush-logs

# 保留 7 天
find $BACKUP_DIR -name "${DB}_*.sql.gz" -mtime +7 -delete

# 异地同步（示例：上传到对象存储）
# aws s3 cp $BACKUP_DIR/${DB}_${DATE}.sql.gz s3://my-bucket/mysql/

echo "[$(date)] backup done: ${DB}_${DATE}.sql.gz"
```

加入 crontab：

```bash
# 每日凌晨 2 点执行
0 2 * * * /opt/scripts/backup_ecommerce.sh >> /var/log/mysql_backup.log 2>&1
```

---

## 9. 常见问题排查

### 9.1 mysqldump 报锁表超时

```
mysqldump: Error 2013: Lost connection to MySQL server during query
```

**原因**：MyISAM 表无法用 `--single-transaction`，会锁表；大表锁超时。

**解决**：
- 全部用 InnoDB 引擎
- 或加 `--lock-tables`（短暂锁）
- 或用 xtrabackup 物理备份

### 9.2 恢复时外键报错

```
ERROR 1452 (23000): Cannot add or update a child row
```

**解决**：恢复前临时关闭外键检查：

```sql
SET FOREIGN_KEY_CHECKS = 0;
SOURCE backup.sql;
SET FOREIGN_KEY_CHECKS = 1;
```

### 9.3 binlog 被删导致无法恢复

**原因**：`expire_logs_days` 设置过短，binlog 被自动清理。

**预防**：
- 生产环境至少保留 7 天
- 重要操作前先 `FLUSH LOGS` 切新 binlog
- 定期把 binlog 归档到对象存储

### 9.4 主从延迟过大

**排查**：

```sql
SHOW REPLICA STATUS\G
-- 关注 Seconds_Behind_Master
```

**常见原因**：
- 从库硬件差
- 大事务（一次 INSERT 万行）
- 从库被业务查询拖慢
- 网络带宽不足

**解决**：
- 多线程复制：`SET GLOBAL replica_parallel_workers = 8;`
- 大事务拆小
- 从库独立机器

---

## 10. 关键命令速查

```bash
# 备份
mysqldump -u root -p --single-transaction ecommerce > bak.sql
mysqldump -u root -p -d ecommerce > schema.sql          # 仅结构
mysqldump -u root -p -t ecommerce > data.sql            # 仅数据
mysqldump -u root -p --where="id<100" ecommerce users > partial.sql

# 恢复
mysql -u root -p ecommerce < bak.sql
# 或 mysql> SOURCE bak.sql

# binlog
SHOW MASTER STATUS;                          -- 当前位置
SHOW BINARY LOGS;                            -- 文件列表
mysqlbinlog --start-datetime="..." mysql-bin.000001 > replay.sql

# 慢查询
mysqldumpslow -s t -t 10 slow.log

# 主从
SHOW MASTER STATUS;        -- 主库
SHOW REPLICA STATUS\G      -- 从库（8.0+）
START REPLICA;             -- 启动复制
STOP REPLICA;              -- 停止复制
```

---

> **最后一句话**：没演练过的备份等于没备份。请每季度至少做一次完整恢复演练。
