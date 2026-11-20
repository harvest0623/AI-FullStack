# Day10 - Shell 脚本进阶 · 代码说明

本目录包含 Day10 所有 Shell 脚本，可在 Ubuntu 22.04+ 直接执行。

## 脚本列表

| 文件 | 用途 | 是否需要 sudo | 是否需要参数 |
| --- | --- | --- | --- |
| `01-conditionals.sh` | 条件判断：文件/字符串/数值测试、if/case、正则 | 否 | 可选（文件路径） |
| `02-loops.sh` | 循环：for/while/until/select、break/continue、while read | 否 | 否 |
| `03-functions.sh` | 函数：定义/调用/参数/返回值/local/递归 | 否 | 否 |
| `04-practical-scripts.sh` | 实战合集：备份/健康检查/批量建用户 | **是** | **是** |

## 执行方式

### 基础练习（无需 root）

```bash
cd /path/to/Day10/Code

# 条件判断
bash 01-conditionals.sh
bash 01-conditionals.sh /etc/passwd     # 指定文件测试

# 循环
bash 02-loops.sh

# 函数
bash 03-functions.sh
```

### 实战脚本（需 root/sudo）

```bash
# 1. 数据库备份（默认备份 ecommerce 库）
sudo bash 04-practical-scripts.sh backup_db
sudo bash 04-practical-scripts.sh backup_db mydb

# 2. 服务健康检查
sudo bash 04-practical-scripts.sh health_check

# 3. 批量创建用户
# 先准备用户名文件
cat > /tmp/users.txt <<'EOF'
# 每行一个用户，格式：用户名  或  用户名:密码:组名
deploy:Deploy@2024:developers
dev01:Dev@2024:developers
dev02:Dev@2024:developers
tester01:Test@2024:qa
EOF

sudo bash 04-practical-scripts.sh create_users /tmp/users.txt
```

## 实战脚本详解

### 1. backup_db —— 数据库自动备份

**功能**：
- 使用 `mysqldump` 导出指定数据库
- 通过管道 `| gzip` 压缩为 `.sql.gz`
- 自动创建备份目录 `/opt/ecommerce/backup/`
- 自动清理 7 天前的旧备份（`find -mtime +7`）
- 文件名含时间戳：`ecommerce_20260729_020000.sql.gz`

**生产建议**：
- 配合 crontab 每天凌晨执行：`0 2 * * * /path/to/04-practical-scripts.sh backup_db`
- MySQL 密码不要写在命令行，用 `~/.my.cnf` 或环境变量 `MYSQL_PWD`
- 异地备份：用 rsync 同步到另一台服务器

### 2. health_check —— 服务健康检查

**检查项**：
- systemd 服务状态（`systemctl is-active`）
- 端口监听状态（`ss -tln`）
- 进程存在性（`pgrep -x`）
- 磁盘使用率（`df`，超 80% 警告，超 90% 严重）
- 内存使用率（`free`，超 90% 警告）

**输出**：
- 终端彩色表格
- 详细日志写入 `/opt/ecommerce/logs/health_check_YYYYMMDD_HHMMSS.log`

**扩展**：
- 脚本中预留了告警接口（curl 调用 webhook），可对接飞书/钉钉/企业微信

### 3. create_users —— 批量用户创建

**用户名文件格式**：
```
# 每行一个用户，# 开头为注释
# 格式一：仅用户名（密码锁定，需管理员后续设置）
deploy

# 格式二：用户名:密码:组名
dev01:Dev@2024:developers
tester01:Test@2024:qa
```

**安全特性**：
- 用户名校验（正则 `^[a-zA-Z_][a-zA-Z0-9_-]*$`）
- 已存在用户自动跳过
- 指定的组不存在时自动创建
- 无密码用户自动锁定（`passwd -l`）

## 脚本调试技巧

```bash
# 语法检查（不执行）
bash -n 04-practical-scripts.sh

# 调试模式（打印每条命令）
bash -x 04-practical-scripts.sh health_check

# 局部调试：在脚本中加 set -x / set +x
set -x
... 需要调试的代码 ...
set +x
```

## 严格模式说明

实战脚本 `04-practical-scripts.sh` 开头使用了：

```bash
set -euo pipefail
```

| 选项 | 作用 |
| --- | --- |
| `-e` | 任何命令返回非 0 立即退出，避免错误被忽略 |
| `-u` | 使用未定义变量报错，避免拼错变量名 |
| `-o pipefail` | 管道中任一命令失败则整体失败 |

> 注意：`set -e` 对 `if` / `while` / `||` / `&&` 条件中的命令不生效，便于容错判断。

## 常见问题

### 1. `mysqldump: Got error: 1045: Access denied`

MySQL 认证问题，配置 `~/.my.cnf`：

```ini
[mysqldump]
user=root
password=your_password
```

### 2. `useradd: command not found`

可能不在 root 或 PATH 不完整，用 `sudo` 执行。

### 3. 健康检查显示服务 inactive 但实际在运行

服务名可能带 `d` 后缀（如 `mysqld`），脚本已做兼容处理。若仍异常，检查 `systemctl list-units --type=service | grep <关键字>`。
