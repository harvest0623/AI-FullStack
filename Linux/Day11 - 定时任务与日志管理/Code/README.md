# Day11 - 定时任务与日志管理 · 代码说明

本目录包含 Day11 所有脚本与配置文件，可在 Ubuntu 22.04+ 直接执行。

## 文件列表

| 文件 | 用途 | 是否需要 sudo | 类型 |
| --- | --- | --- | --- |
| `01-crontab-examples.sh` | crontab 示例（仅展示，不修改 crontab） | 否 | Shell 脚本 |
| `02-logrotate-ecommerce.conf` | logrotate 配置文件 | 部署时需要 | 配置文件 |
| `03-log-management.sh` | 日志管理脚本 | 部分（已标注） | Shell 脚本 |
| `04-time-sync.sh` | 时间同步脚本 | **是** | Shell 脚本 |

## 执行方式

### 1. crontab 示例（只读展示）

```bash
bash 01-crontab-examples.sh
```

> 此脚本只打印配置示例，不会修改 crontab。如需启用某项任务，用 `crontab -e` 手动添加。

### 2. 部署 logrotate 配置

```bash
# 复制配置到系统目录（需 sudo）
sudo cp 02-logrotate-ecommerce.conf /etc/logrotate.d/ecommerce

# 调试模式（dry run，只打印不执行）
sudo logrotate -d /etc/logrotate.d/ecommerce

# 强制执行一次（测试效果）
sudo logrotate -f /etc/logrotate.d/ecommerce

# 验证：查看日志目录
ls -lh /opt/ecommerce/logs/
# 应看到：app.log（新空文件）+ app.log-20260729.gz（旧文件压缩）
```

> 配置生效后，系统每天自动执行（由 `/etc/cron.daily/logrotate` 触发）。

### 3. 日志管理

```bash
# 普通用户可执行（部分查询需 sudo）
bash 03-log-management.sh

# 或用 sudo 获取完整信息
sudo bash 03-log-management.sh
```

### 4. 时间同步（需 root）

```bash
sudo bash 04-time-sync.sh
```

## 实际配置 crontab 的步骤

### 步骤一：编辑 crontab

```bash
# 当前用户
crontab -e

# 或指定 deploy 用户（需 root）
sudo crontab -u deploy -e
```

### 步骤二：添加任务（参考 01 脚本的输出）

```bash
# 在 crontab 中添加以下内容
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/node/bin
MAILTO=""

# 每天凌晨2点备份数据库
0 2 * * * /opt/ecommerce/scripts/backup_db.sh >> /var/log/ecommerce/backup.log 2>&1

# 每5分钟健康检查
*/5 * * * * /opt/ecommerce/scripts/health_check.sh >> /var/log/ecommerce/health.log 2>&1
```

### 步骤三：验证

```bash
# 确认任务已写入
crontab -l

# 查看 cron 服务状态
systemctl status cron

# 实时查看 cron 执行日志
sudo journalctl -u cron -f
# 或
sudo grep CRON /var/log/syslog
```

## 系统级定时任务（推荐方式）

把任务放在 `/etc/cron.d/` 下独立文件，便于管理：

```bash
sudo tee /etc/cron.d/ecommerce <<'EOF'
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

0 2 * * * root /opt/ecommerce/scripts/backup_db.sh >> /var/log/ecommerce/backup.log 2>&1
*/5 * * * * deploy /opt/ecommerce/scripts/health_check.sh >> /var/log/ecommerce/health.log 2>&1
EOF

sudo chmod 644 /etc/cron.d/ecommerce
```

## 常见问题

### 1. cron 任务不执行

排查步骤：

```bash
# 1. 检查 cron 服务
systemctl status cron

# 2. 确认任务已写入
crontab -l

# 3. 查看执行日志
sudo grep CRON /var/log/syslog | tail -20

# 4. 手动执行脚本测试
/opt/ecommerce/scripts/backup_db.sh

# 5. 检查 PATH（cron 环境 PATH 很小）
#    → 在 crontab 中显式设置 PATH，或脚本中用绝对路径

# 6. 检查权限
ls -l /opt/ecommerce/scripts/backup_db.sh
chmod +x /opt/ecommerce/scripts/backup_db.sh
```

### 2. logrotate 不生效

```bash
# 调试模式查看
sudo logrotate -d /etc/logrotate.d/ecommerce

# 检查状态文件
cat /var/lib/logrotate/status

# 检查配置语法
sudo logrotate -d /etc/logrotate.d/ecommerce 2>&1 | grep -i error

# 强制执行测试
sudo logrotate -f /etc/logrotate.d/ecommerce
```

### 3. chrony 同步失败

```bash
# 查看同步状态
chronyc tracking

# 查看时间源
chronyc sources -v

# 检查能否访问 NTP 服务器
ping -c 3 ntp.aliyun.com

# 手动强制同步
sudo chronyc -a makestep

# 检查防火墙是否放行 NTP（UDP 123）
sudo ufw allow ntp    # Ubuntu
```

### 4. journalctl 占用磁盘过大

```bash
# 查看占用
journalctl --disk-usage

# 清理 7 天前
sudo journalctl --vacuum-time=7d

# 限制总大小 500MB
sudo journalctl --vacuum-size=500M

# 永久限制：编辑 /etc/systemd/journald.conf
# SystemMaxUse=500M
# MaxRetentionSec=2week
sudo systemctl restart systemd-journald
```

## 最佳实践

1. **cron 任务一定要重定向输出到日志文件**，避免邮件堆积
2. **脚本中用绝对路径**，不依赖 cron 的 PATH
3. **logrotate 配置放在 `/etc/logrotate.d/`**，不修改全局 `/etc/logrotate.conf`
4. **时间同步用 chrony**，不用已弃用的 ntpdate
5. **定期检查日志磁盘占用**，避免日志撑满磁盘导致服务崩溃
6. **生产环境监控时间偏移**，超过 1 秒告警
