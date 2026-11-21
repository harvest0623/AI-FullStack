# Day11 - 定时任务与日志管理

## 本章简介

如果说 Day09、Day10 让你写出了能干活的 Shell 脚本，那么 Day11 解决的是两个更关键的问题：**谁来定时触发这些脚本**，以及**脚本运行后产生的日志怎么管**。定时任务（crontab / at）让运维从“手动敲命令”升级为“配置好就自动跑”，日志系统（rsyslog / journalctl / logrotate）让每一次运行都可追溯、可排查、可归档。两者合在一起，构成了生产环境运维自动化的两大支柱：自动化执行 + 可观测性。

本章系统讲解 crontab 五段式表达式与系统级定时任务、at 一次性任务、rsyslog 日志服务与 `/var/log/` 目录结构、systemd journalctl 的强大查询能力、logrotate 日志轮转配置，以及应用层日志（PM2/Docker）管理与时间同步（chrony）。所有配置与脚本围绕电商项目 `/opt/ecommerce/` 展开，可在 Ubuntu 22.04+ 直接执行。

## 学习目标

- 熟练使用 `crontab -e/-l/-r` 管理用户级定时任务
- 掌握 cron 五段式表达式与特殊字符（`*` `*/n` `-` `,`）及预定义宏
- 区分用户级 crontab 与系统级 `/etc/crontab`、`/etc/cron.d/`、`/etc/cron.daily/` 等
- 理解 crontab 的 PATH 限制与输出邮件问题，掌握重定向到日志的写法
- 掌握 `at` 一次性任务的创建、查看与删除
- 理解 rsyslog 的 facility.priority 机制与 `/var/log/` 目录结构
- 熟练使用 `journalctl` 按服务、时间、级别查询 systemd 日志
- 掌握 `logrotate` 配置参数与手动执行/调试方法
- 了解 PM2 / Docker 应用日志管理与日志收集方案（ELK / Loki）
- 掌握 `timedatectl` 时区设置与 `chrony` 时间同步配置

## 理论知识讲解

### 1. crontab 定时任务

#### 1.1 cron 服务

cron 是 Linux 默认的定时任务服务，Ubuntu 上由 `cron` 包提供（CentOS 为 `cronie`）。

```bash
# Ubuntu
systemctl status cron          # 查看状态
systemctl enable cron          # 开机自启
systemctl start cron           # 启动

# CentOS
systemctl status crond
systemctl enable crond
```

#### 1.2 crontab 命令

| 命令 | 作用 |
| --- | --- |
| `crontab -e` | 编辑当前用户的定时任务 |
| `crontab -l` | 列出当前用户的定时任务 |
| `crontab -r` | 删除当前用户的所有定时任务 |
| `crontab -u user -e` | 编辑指定用户的定时任务（需 root） |
| `crontab -u user -l` | 列出指定用户的定时任务 |

> `crontab -e` 会调用默认编辑器（通常是 nano），可设 `export EDITOR=vim` 改用 vim。

#### 1.3 cron 表达式五段式

```
┌──────── 分钟 (0-59)
│ ┌────── 小时 (0-23)
│ │ ┌──── 日 (1-31)
│ │ │ ┌── 月 (1-12)
│ │ │ │ ─ 星期 (0-7, 0和7都是周日)
│ │ │ │ │
* * * * * command
```

| 表达式 | 含义 |
| --- | --- |
| `*/5 * * * * cmd` | 每 5 分钟 |
| `0 * * * * cmd` | 每小时整点 |
| `0 2 * * * cmd` | 每天凌晨 2 点 |
| `0 0 * * 0 cmd` | 每周日午夜 |
| `0 0 1 * * cmd` | 每月 1 号午夜 |
| `0 9-18 * * 1-5 cmd` | 工作日 9-18 点每小时 |
| `30 3,15 * * * cmd` | 每天 3:30 和 15:30 |
| `0 0 * * 6 cmd` | 每周六午夜 |

#### 1.4 特殊字符

| 字符 | 含义 | 示例 |
| --- | --- | --- |
| `*` | 任意值 | `* * * * *` 每分钟 |
| `*/n` | 每 n 个单位 | `*/5 * * * *` 每 5 分钟 |
| `-` | 范围 | `0 9-17 * * *` 9 到 17 点每小时 |
| `,` | 列表 | `0 3,15 * * *` 3 点和 15 点 |

#### 1.5 预定义宏

| 宏 | 等价表达式 | 含义 |
| --- | --- | --- |
| `@reboot` | - | 开机时执行一次 |
| `@yearly` / `@annually` | `0 0 1 1 *` | 每年 1 月 1 日 |
| `@monthly` | `0 0 1 * *` | 每月 1 日 |
| `@weekly` | `0 0 * * 0` | 每周日 |
| `@daily` / `@midnight` | `0 0 * * *` | 每天午夜 |
| `@hourly` | `0 * * * *` | 每小时 |

#### 1.6 系统级 crontab

除用户级 `crontab -e` 外，系统级定时任务通过文件配置：

| 文件/目录 | 说明 |
| --- | --- |
| `/etc/crontab` | 系统主 crontab，比用户级多一列“用户名” |
| `/etc/cron.d/` | 各服务独立的 crontab 片段（推荐方式） |
| `/etc/cron.daily/` | 每天执行的脚本目录 |
| `/etc/cron.hourly/` | 每小时执行 |
| `/etc/cron.weekly/` | 每周执行 |
| `/etc/cron.monthly/` | 每月执行 |

`/etc/crontab` 格式（多一列用户名）：

```
# m h dom mon dow user  command
0 2 * * * root /opt/ecommerce/scripts/backup_db.sh
*/5 * * * * deploy /opt/ecommerce/scripts/health_check.sh
```

> 推荐把自定义系统级任务放在 `/etc/cron.d/` 下独立文件中，便于管理与卸载。

#### 1.7 crontab 环境变量陷阱

cron 执行时的环境与登录 Shell **不同**：

- **PATH 很有限**：通常只有 `/usr/bin:/bin`，`mysqldump`、`docker`、`node` 等可能找不到
- **没有 `~/.bashrc`**：自定义环境变量不生效
- **工作目录**：通常是用户家目录

**解决方案**：

```bash
# 方案一：脚本中用绝对路径
/usr/bin/mysqldump ecommerce > /opt/ecommerce/backup/db.sql

# 方案二：crontab 中设置 PATH
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 2 * * * /opt/ecommerce/scripts/backup_db.sh

# 方案三：脚本开头加载环境
#!/bin/bash
source /etc/profile
source ~/.bashrc
```

#### 1.8 crontab 输出处理

cron 默认把命令的 stdout/stderr **发邮件**给任务所属用户（需要 mailto 服务）。生产环境通常：

```bash
# 丢弃所有输出（不推荐，排查问题困难）
0 2 * * * /script.sh > /dev/null 2>&1

# 重定向到日志文件（推荐）
0 2 * * * /script.sh >> /var/log/ecommerce/backup.log 2>&1

# 设置 MAILTO 为空，禁止发邮件
MAILTO=""
0 2 * * * /script.sh
```

#### 1.9 crontab 调试

```bash
# 查看 cron 服务日志
grep CRON /var/log/syslog           # Ubuntu
journalctl -u cron -f               # 实时跟踪

# 常见问题排查
# 1. 脚本手动执行正常，cron 执行失败 → 90% 是 PATH 或环境变量问题
# 2. 检查脚本是否用了相对路径 → 改为绝对路径
# 3. 检查脚本权限 → chmod +x
# 4. 检查 cron 服务是否运行 → systemctl status cron
```

### 2. at 一次性任务

`at` 用于在**指定时间执行一次**的任务，与 crontab 的“循环执行”互补。

```bash
# 安装（Ubuntu）
sudo apt install at

# 启动服务
sudo systemctl enable --now atd

# 10 分钟后执行
echo "/opt/ecommerce/scripts/deploy.sh" | at now + 10 minutes

# 明天 14:00 执行
echo "backup.sh" | at 14:00 tomorrow

# 具体日期时间
echo "reboot" | at 02:00 2026-08-01

# 交互式输入（Ctrl+D 结束）
at now + 5 minutes
at> echo "hello"
at> <EOT>

# 查看
at -l                # 列出待执行任务
atq                  # 等价
at -c 1              # 查看任务1的详细内容

# 删除
atrm 1               # 删除任务1
```

| 对比 | crontab | at |
| --- | --- | --- |
| 执行次数 | 循环执行 | 仅一次 |
| 配置方式 | `crontab -e` | `at` 命令 |
| 适用场景 | 每日备份、定期巡检 | 一次性部署、延时重启 |
| 服务 | cron | atd |

### 3. 日志系统

#### 3.1 rsyslog

rsyslog 是 Ubuntu/CentOS 默认的系统日志服务，按 `facility.priority` 规则把日志分发到不同文件。

**facility（日志来源）**：`auth` `authpriv` `daemon` `kern` `mail` `cron` `user` `local0-7` 等

**priority（日志级别，从低到高）**：`debug` `info` `notice` `warn` `err` `crit` `alert` `emerg`

配置文件 `/etc/rsyslog.conf` 与 `/etc/rsyslog.d/*.conf`：

```
# 格式：facility.priority  动作
auth,authpriv.*      /var/log/auth.log
*.*;auth,authpriv.none  /var/log/syslog
cron.*               /var/log/cron.log
mail.*               /var/log/mail.log
local0.*             /var/log/ecommerce/app.log     # 自定义应用日志
```

> 自定义应用可用 `logger -p local0.info "msg"` 把日志写入 rsyslog。

#### 3.2 `/var/log/` 目录结构

| 文件 | 说明 | Ubuntu | CentOS |
| --- | --- | --- | --- |
| `syslog` / `messages` | 全局系统日志 | `/var/log/syslog` | `/var/log/messages` |
| `auth.log` / `secure` | 认证日志（登录、sudo） | `/var/log/auth.log` | `/var/log/secure` |
| `kern.log` | 内核日志 | `/var/log/kern.log` | `/var/log/messages` |
| `dmesg` | 启动日志（环形缓冲区） | `/var/log/dmesg` | `/var/log/dmesg` |
| `cron.log` | cron 任务日志 | `/var/log/cron.log` | `/var/log/cron` |
| `mail.log` | 邮件日志 | `/var/log/mail.log` | `/var/log/maillog` |
| `dpkg.log` | apt 安装日志 | `/var/log/dpkg.log` | - |
| `yum.log` | yum 安装日志 | - | `/var/log/yum.log` |

```bash
# 常用查看命令
tail -f /var/log/syslog                  # 实时跟踪系统日志
grep "Failed password" /var/log/auth.log # 查找登录失败记录
dmesg -T                                 # 内核日志（带时间戳）
last                                     # 登录历史
lastb                                    # 登录失败历史
```

#### 3.3 journalctl（systemd 日志）

systemd 用 `journald` 收集日志，`journalctl` 是其查询工具，比传统文件日志更强大：

```bash
# 按服务查询
journalctl -u nginx                # nginx 服务日志
journalctl -u mysql --since today  # 今天的 mysql 日志

# 实时跟踪
journalctl -f                      # 类似 tail -f
journalctl -u nginx -f             # 跟踪指定服务

# 按时间范围
journalctl --since "2026-07-29 00:00:00" --until "2026-07-29 12:00:00"
journalctl --since "1 hour ago"    # 最近 1 小时
journalctl --since today           # 今天
journalctl --since yesterday       # 昨天

# 按级别
journalctl -p err                  # 仅错误级别
journalctl -p warning              # 警告及以上
journalctl -p crit                 # 严重及以上

# 按数量
journalctl -n 50                   # 最近 50 条
journalctl -n 100 -u nginx         # nginx 最近 100 条

# 磁盘管理
journalctl --disk-usage            # 日志磁盘占用
journalctl --vacuum-time=7d        # 清理 7 天前日志
journalctl --vacuum-size=500M      # 限制日志总大小 500MB

# 其他
journalctl --no-pager              # 不分页（适合管道）
journalctl -k                      # 仅内核日志
journalctl _PID=1234               # 按进程 PID
journalctl --boot                  # 本次启动日志
journalctl --list-boots            # 列出所有启动记录
```

#### 3.4 dmesg

`dmesg` 读取内核环形缓冲区，主要看硬件、驱动、启动信息：

```bash
dmesg                       # 全部内核日志
dmesg -T                    # 显示人类可读时间
dmesg --level=err           # 仅错误
dmesg | grep -i usb         # 查找 USB 设备
dmesg | grep -i eth         # 查找网卡
dmesg | tail -20            # 最近 20 条
```

### 4. logrotate 日志轮转

#### 4.1 为什么需要轮转

日志文件会无限增长，最终撑满磁盘导致服务崩溃。logrotate 定期把日志“重命名归档 + 新建空文件 + 压缩旧文件 + 删除过旧文件”，让日志占用空间可控。

#### 4.2 配置文件

| 文件 | 说明 |
| --- | --- |
| `/etc/logrotate.conf` | 全局主配置 |
| `/etc/logrotate.d/*` | 各服务独立配置（推荐） |

#### 4.3 配置参数

| 参数 | 作用 |
| --- | --- |
| `daily` / `weekly` / `monthly` | 轮转周期 |
| `rotate 7` | 保留 7 个旧文件 |
| `size 100M` | 达到 100M 时轮转（与周期是“或”关系） |
| `compress` | 用 gzip 压缩旧文件 |
| `delaycompress` | 延迟一轮再压缩（下次轮转才压缩上次的） |
| `missingok` | 日志文件不存在不报错 |
| `notifempty` | 空文件不轮转 |
| `create 644 user group` | 创建新文件并指定权限属主 |
| `dateext` | 用日期做扩展名（如 `app.log-20260729`） |
| `copytruncate` | 复制后截断原文件（不重启服务） |
| `sharedscripts` | 多个日志匹配时脚本只执行一次 |
| `postrotate ... endscript` | 轮转后执行脚本（常用于重启服务） |
| `prerotate ... endscript` | 轮转前执行脚本 |

#### 4.4 配置示例

```
# /etc/logrotate.d/ecommerce
/opt/ecommerce/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    dateext
    create 644 deploy deploy
    sharedscripts
    postrotate
        # 轮转后通知应用重新打开日志文件
        if [ -f /var/run/ecommerce.pid ]; then
            kill -USR1 $(cat /var/run/ecommerce.pid) 2>/dev/null || true
        fi
    endscript
}
```

#### 4.5 `copytruncate` vs `postrotate`

| 方式 | 原理 | 优点 | 缺点 |
| --- | --- | --- | --- |
| `create` + `postrotate` | 重命名旧文件，新建空文件，发信号让服务重新打开 | 不丢日志 | 服务需支持信号重开日志 |
| `copytruncate` | 复制旧文件，截断原文件为空 | 无需重启服务、无需信号 | 复制与截断之间可能丢少量日志 |

> Node.js 应用（PM2）常用 `copytruncate`，Nginx 用 `postrotate` + `kill -USR1`。

#### 4.6 手动执行与调试

```bash
# 手动执行（强制轮转）
sudo logrotate -f /etc/logrotate.d/ecommerce

# 调试模式（dry run，只打印不执行）
sudo logrotate -d /etc/logrotate.d/ecommerce

# 查看状态
cat /var/lib/logrotate/status
```

### 5. 应用日志管理

#### 5.1 PM2 日志

```bash
pm2 logs                    # 查看所有应用日志（实时）
pm2 logs app --lines 100    # 指定应用最近 100 行
pm2 flush                   # 清空所有日志
pm2 install pm2-logrotate   # 安装 PM2 日志轮转模块
```

PM2 日志默认在 `~/.pm2/logs/`，配置文件 `ecosystem.config.js` 可自定义：

```js
module.exports = {
  apps: [{
    name: 'ecommerce-api',
    script: 'dist/main.js',
    out_file: '/opt/ecommerce/logs/out.log',
    error_file: '/opt/ecommerce/logs/error.log',
    merge_logs: true,
    time: true,
  }]
}
```

#### 5.2 Docker 容器日志

```bash
docker logs <container>           # 查看容器日志
docker logs -f --tail 100 <c>     # 跟踪最近 100 行
docker logs --since 30m <c>       # 最近 30 分钟
```

Docker 默认用 `json-file` 驱动，日志在 `/var/lib/docker/containers/<id>/<id>-json.log`，需限制大小：

```json
// /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

#### 5.3 日志收集方案

| 方案 | 组成 | 特点 |
| --- | --- | --- |
| ELK | Elasticsearch + Logstash + Kibana | 功能全，资源消耗大 |
| EFK | Elasticsearch + Fluentd + Kibana | 容器友好 |
| Loki + Grafana | Loki + Promtail + Grafana | 轻量，与 Prometheus 统一 |
| Graylog | Graylog + MongoDB + Elasticsearch | 开源集中式 |

### 6. 时间同步

#### 6.1 为什么生产必须时间同步

- **日志排序**：多机排查问题时，时间不一致无法对齐日志
- **定时任务**：cron 依赖系统时间，时间偏移会导致任务提前或延后
- **分布式系统**：数据库主从复制、分布式锁、TLS 证书校验都对时间敏感
- **金融交易**：订单时间戳必须准确

#### 6.2 timedatectl

```bash
timedatectl                              # 查看当前时间与时区
timedatectl list-timezones | grep Asia   # 列出亚洲时区
timedatectl set-timezone Asia/Shanghai   # 设置时区
timedatectl set-ntp true                 # 开启 NTP 同步
```

#### 6.3 chrony（推荐）

chrony 是现代 Linux 推荐的时间同步工具，比旧版 ntpd 更快收敛、更省资源。

```bash
# Ubuntu 安装
sudo apt install chrony
sudo systemctl enable --now chronyd

# CentOS 已默认安装
systemctl status chronyd
```

配置文件 `/etc/chrony/chrony.conf`（Ubuntu）或 `/etc/chrony.conf`（CentOS）：

```
# 使用阿里云 NTP 服务器（国内更快）
pool ntp.aliyun.com iburst
pool cn.pool.ntp.org iburst

# 允许本地网络同步（作为时间服务器时）
allow 192.168.1.0/24

# 记录漂移
driftfile /var/lib/chrony/chrony.drift
makestep 1.0 3
rtcsync
```

```bash
# 查看同步状态
chronyc tracking           # 详细状态
chronyc sources -v         # 时间源列表
chronyc sourcestats        # 统计信息
```

#### 6.4 ntpdate（旧，不推荐）

```bash
sudo ntpdate ntp.aliyun.com       # 手动同步一次
# ntpdate 已被弃用，推荐用 chronyc makeshift
```

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01-crontab-examples.sh` | crontab 示例：各种 cron 表达式、系统级配置、PATH 设置、输出重定向 |
| `Code/02-logrotate-ecommerce.conf` | logrotate 配置：电商项目与 Nginx 日志轮转 |
| `Code/03-log-management.sh` | 日志管理：查看系统日志、journalctl 查询、日志清理 |
| `Code/04-time-sync.sh` | 时间同步：时区设置、chrony 安装配置、同步验证 |
| `Code/README.md` | 脚本执行说明与注意事项 |

执行方式：

```bash
cd /opt/ecommerce/scripts/

# crontab 示例（只展示配置，不修改 crontab）
bash 01-crontab-examples.sh

# 部署 logrotate 配置（需 root）
sudo cp 02-logrotate-ecommerce.conf /etc/logrotate.d/ecommerce
sudo logrotate -d /etc/logrotate.d/ecommerce    # 调试
sudo logrotate -f /etc/logrotate.d/ecommerce    # 强制执行

# 日志管理
sudo bash 03-log-management.sh

# 时间同步（需 root）
sudo bash 04-time-sync.sh
```

## 关键知识点总结

### cron 表达式速查

```
┌──────── 分钟 (0-59)
│ ┌────── 小时 (0-23)
│ │ ┌──── 日 (1-31)
│ │ │ ┌── 月 (1-12)
│ │ │ │ ─ 星期 (0-7, 0和7都是周日)
│ │ │ │ │
* * * * * command

*/5 * * * *     每5分钟
0 * * * *       每小时整点
0 2 * * *       每天凌晨2点
0 0 * * 0       每周日午夜
0 0 1 * *       每月1号午夜
0 9-18 * * 1-5  工作日9-18点每小时
@daily          每天（等同 0 0 * * *）
@reboot         开机时
```

### crontab vs at 对比表

| 维度 | crontab | at |
| --- | --- | --- |
| 执行次数 | 循环 | 一次 |
| 配置方式 | `crontab -e` | `at` 命令 |
| 服务 | cron | atd |
| 查看命令 | `crontab -l` | `at -l` / `atq` |
| 删除命令 | `crontab -r` | `atrm <id>` |
| 典型场景 | 每日备份、定期巡检 | 一次性部署、延时重启 |

### 日志文件速查表

| 路径 | 内容 | Ubuntu | CentOS |
| --- | --- | --- | --- |
| 全局系统日志 | syslog | ✓ | messages |
| 认证日志 | auth.log | ✓ | secure |
| 内核日志 | kern.log | ✓ | messages |
| 启动日志 | dmesg | ✓ | dmesg |
| cron 日志 | cron.log | ✓ | cron |
| systemd 日志 | `journalctl` | ✓ | ✓ |

### logrotate 参数速查表

| 参数 | 作用 |
| --- | --- |
| `daily/weekly/monthly` | 轮转周期 |
| `rotate N` | 保留 N 个旧文件 |
| `size 100M` | 达到大小轮转 |
| `compress` | 压缩旧文件 |
| `delaycompress` | 延迟一轮压缩 |
| `missingok` | 文件不存在不报错 |
| `notifempty` | 空文件不轮转 |
| `create 644 user group` | 新文件权限属主 |
| `dateext` | 日期扩展名 |
| `copytruncate` | 复制截断（不重启服务） |
| `postrotate/endscript` | 轮转后执行脚本 |
| `sharedscripts` | 脚本只执行一次 |

### journalctl 常用命令速查

| 命令 | 作用 |
| --- | --- |
| `journalctl -u svc` | 按服务查 |
| `journalctl -f` | 实时跟踪 |
| `journalctl --since today` | 今天的日志 |
| `journalctl -p err` | 错误级别 |
| `journalctl -n 50` | 最近 50 条 |
| `journalctl --disk-usage` | 磁盘占用 |
| `journalctl --vacuum-time=7d` | 清理 7 天前 |
| `journalctl --vacuum-size=500M` | 限制 500MB |
| `journalctl -k` | 仅内核日志 |
| `journalctl --boot` | 本次启动日志 |

## 实战练习

1. **配置电商项目定时备份**
   - 编写备份脚本 `/opt/ecommerce/scripts/backup.sh`（可复用 Day10 的 `backup_db`）。
   - 用 `crontab -e` 配置：每天凌晨 2 点执行备份，输出重定向到 `/var/log/ecommerce/backup.log`。
   - 用 `crontab -l` 验证任务已添加，用 `grep CRON /var/log/syslog` 确认执行记录。
   - 练习把时间临时改为“2 分钟后”验证任务确实触发。

2. **部署 logrotate 配置**
   - 在 `/opt/ecommerce/logs/` 下创建测试日志文件并写入内容。
   - 把 `02-logrotate-ecommerce.conf` 复制到 `/etc/logrotate.d/ecommerce`。
   - 用 `logrotate -d` 调试查看轮转计划，用 `logrotate -f` 强制执行一次。
   - 验证旧文件被压缩为 `.gz`，新空文件被创建。

3. **日志排查演练**
   - 用 `journalctl -u ssh --since "1 hour ago"` 查看 SSH 服务最近一小时日志。
   - 用 `grep "Failed password" /var/log/auth.log | tail -20` 查找最近登录失败记录。
   - 用 `journalctl -p err --since today` 查看今天所有错误级别日志。
   - 用 `journalctl --disk-usage` 查看日志占用，用 `--vacuum-time=7d` 清理 7 天前日志（练习环境）。
