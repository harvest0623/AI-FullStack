#!/bin/bash
# ============================================================
# 文件名：01-crontab-examples.sh
# 用途：crontab 示例——展示各种 cron 表达式写法、系统级配置、
#       PATH 设置、输出重定向（仅展示，不直接修改 crontab）
# 场景：电商项目 /opt/ecommerce/ 定时任务配置参考
# 语法：bash 01-crontab-examples.sh
# 注意：本脚本只打印配置示例，不会修改任何 crontab。
#       需要实际配置时，请用 crontab -e 手动添加，或复制对应片段。
# ============================================================

echo "========== Day11 - 01 crontab 示例 =========="
echo "本脚本仅展示配置示例，不修改 crontab。"
echo "如需启用，请用 crontab -e 手动添加对应行。"

# ============================================================
# 一、cron 表达式五段式说明
# ============================================================
echo ""
echo "---------- 一、cron 表达式五段式 ----------"
cat <<'EOF'
┌──────── 分钟 (0-59)
│ ┌────── 小时 (0-23)
│ │ ┌──── 日 (1-31)
│ │ │ ┌── 月 (1-12)
│ │ │ │ ─ 星期 (0-7, 0和7都是周日)
│ │ │ │ │
* * * * * command
EOF

# ============================================================
# 二、常见 cron 表达式示例
# ============================================================
echo ""
echo "---------- 二、常见 cron 表达式示例 ----------"
cat <<'EOF'
# 频率
*/5 * * * * /script.sh              # 每5分钟
*/30 * * * * /script.sh             # 每30分钟
0 * * * * /script.sh                # 每小时整点
0 */2 * * * /script.sh              # 每2小时

# 每天
0 2 * * * /script.sh                # 每天凌晨2点
0 0 * * * /script.sh                # 每天午夜
30 3 * * * /script.sh               # 每天3:30

# 每周
0 0 * * 0 /script.sh                # 每周日午夜
0 0 * * 6 /script.sh                # 每周六午夜
0 2 * * 1 /script.sh                # 每周一凌晨2点

# 每月
0 0 1 * * /script.sh                # 每月1号午夜
0 2 15 * * /script.sh               # 每月15号凌晨2点

# 工作日
0 9-18 * * 1-5 /script.sh           # 工作日9-18点每小时
0 9 * * 1-5 /script.sh              # 工作日早上9点

# 列表
0 3,15 * * * /script.sh             # 每天3:00和15:00
0 0 1,15 * * /script.sh             # 每月1号和15号午夜
EOF

# ============================================================
# 三、电商项目定时任务配置示例
# ============================================================
echo ""
echo "---------- 三、电商项目定时任务配置示例 ----------"
echo "（以下为 crontab -e 中应添加的内容）"
echo ""
cat <<'EOF'
# ============ 电商项目定时任务 ============
# 在 crontab -e 中添加以下内容（deploy 用户）

# 设置 PATH（cron 环境 PATH 很有限，需显式声明）
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/node/bin

# 禁止发邮件
MAILTO=""

# ---------- 数据库备份 ----------
# 每天凌晨2点备份数据库，日志写入 backup.log
0 2 * * * /opt/ecommerce/scripts/backup_db.sh >> /var/log/ecommerce/backup.log 2>&1

# ---------- 服务健康检查 ----------
# 每5分钟检查 Nginx/MySQL/Redis 状态
*/5 * * * * /opt/ecommerce/scripts/health_check.sh >> /var/log/ecommerce/health.log 2>&1

# ---------- 日志清理 ----------
# 每天凌晨3点清理7天前的应用日志
0 3 * * * find /opt/ecommerce/logs -name "*.log" -mtime +7 -delete

# ---------- SSL 证书检查 ----------
# 每周一上午9点检查证书到期情况
0 9 * * 1 /opt/ecommerce/scripts/check_ssl.sh

# ---------- Redis 持久化备份 ----------
# 每小时复制 RDB 文件到备份目录
0 * * * * cp /var/lib/redis/dump.rdb /opt/ecommerce/backup/redis_$(date +\%Y\%m\%d_\%H\%M).rdb

# ---------- Node.js 应用日志切割通知 ----------
# 每天午夜让 PM2 重启日志
@daily pm2 reloadLogs
EOF

# ============================================================
# 四、预定义宏示例
# ============================================================
echo ""
echo "---------- 四、预定义宏 ----------"
cat <<'EOF'
@reboot /opt/ecommerce/scripts/startup.sh     # 开机时执行
@yearly /opt/ecommerce/scripts/yearly_report.sh # 每年1月1日
@monthly /opt/ecommerce/scripts/monthly_report.sh # 每月1日
@weekly /opt/ecommerce/scripts/weekly_cleanup.sh  # 每周日
@daily /opt/ecommerce/scripts/daily_tasks.sh      # 每天午夜
@hourly /opt/ecommerce/scripts/hourly_check.sh    # 每小时
EOF

# ============================================================
# 五、系统级 crontab 配置示例
# ============================================================
echo ""
echo "---------- 五、系统级 crontab 配置 ----------"
echo "（/etc/crontab 与 /etc/cron.d/ 比用户级多一列“用户名”）"
echo ""
cat <<'EOF'
# /etc/crontab 系统主配置
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# m h dom mon dow user  command
0 2 * * * root    /opt/ecommerce/scripts/backup_db.sh
*/5 * * * * deploy /opt/ecommerce/scripts/health_check.sh
0 4 * * 0 root    /opt/ecommerce/scripts/weekly_cleanup.sh
EOF

echo ""
echo "推荐：把自定义任务放在 /etc/cron.d/ 下独立文件"
echo ""
cat <<'EOF'
# 文件：/etc/cron.d/ecommerce
# 内容格式同 /etc/crontab（含用户名列）
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

0 2 * * * root /opt/ecommerce/scripts/backup_db.sh >> /var/log/ecommerce/backup.log 2>&1
*/5 * * * * deploy /opt/ecommerce/scripts/health_check.sh >> /var/log/ecommerce/health.log 2>&1
EOF

# ============================================================
# 六、cron 目录方式（/etc/cron.daily/ 等）
# ============================================================
echo ""
echo "---------- 六、cron 目录方式 ----------"
cat <<'EOF'
# 把可执行脚本放入对应目录，自动按周期执行
/etc/cron.hourly/    # 每小时执行（实际是 /etc/crontab 中 17 * * * * run-parts）
/etc/cron.daily/     # 每天执行
/etc/cron.weekly/    # 每周执行
/etc/cron.monthly/   # 每月执行

# 示例：创建每日备份脚本
sudo tee /etc/cron.daily/ecommerce-backup <<'SCRIPT'
#!/bin/bash
/opt/ecommerce/scripts/backup_db.sh >> /var/log/ecommerce/backup.log 2>&1
SCRIPT
sudo chmod +x /etc/cron.daily/ecommerce-backup
EOF

# ============================================================
# 七、crontab 管理命令
# ============================================================
echo ""
echo "---------- 七、crontab 管理命令 ----------"
cat <<'EOF'
crontab -l                  # 列出当前用户的定时任务
crontab -e                  # 编辑当前用户的定时任务
crontab -r                  # 删除当前用户的所有定时任务（谨慎！）
crontab -u deploy -l        # 查看 deploy 用户的任务（需 root）
crontab -u deploy -e        # 编辑 deploy 用户的任务（需 root）

# 查看 cron 服务状态
systemctl status cron           # Ubuntu
systemctl status crond          # CentOS

# 查看 cron 执行日志
grep CRON /var/log/syslog       # Ubuntu
grep CRON /var/log/cron         # CentOS
journalctl -u cron -f           # 实时跟踪
EOF

# ============================================================
# 八、cron 调试与常见坑
# ============================================================
echo ""
echo "---------- 八、cron 调试与常见坑 ----------"
cat <<'EOF'
常见问题：脚本手动执行正常，cron 执行失败
排查步骤：
1. PATH 问题 → cron 环境 PATH 很小，脚本中用绝对路径或 crontab 设 PATH
2. 环境变量 → cron 不加载 ~/.bashrc，需在脚本内 source 或显式设置
3. 工作目录 → cron 默认在家目录，脚本中用 cd 或绝对路径
4. 权限问题 → 脚本需 chmod +x，确保 cron 运行用户有权限
5. 输出未处理 → 默认发邮件，建议重定向到日志文件
6. 换行符 → Windows 编辑的脚本需 dos2unix 转换
7. 时间不对 → 检查时区 timedatectl，确保时间同步

调试命令：
sudo grep CRON /var/log/syslog | tail -20     # 查看最近 cron 执行记录
sudo journalctl -u cron --since "1 hour ago"  # 最近一小时 cron 日志
crontab -l                                    # 确认任务已写入
EOF

# ============================================================
# 九、at 一次性任务示例
# ============================================================
echo ""
echo "---------- 九、at 一次性任务示例 ----------"
cat <<'EOF'
# at 用于一次性定时任务（需安装：sudo apt install at && sudo systemctl enable --now atd）

# 10分钟后执行
echo "/opt/ecommerce/scripts/deploy.sh" | at now + 10 minutes

# 明天下午2点执行
echo "/opt/ecommerce/scripts/maintenance.sh" | at 14:00 tomorrow

# 具体日期时间
echo "reboot" | at 02:00 2026-08-01

# 查看
at -l                # 列出待执行任务
atq                  # 等价
at -c 1              # 查看任务1详细内容

# 删除
atrm 1               # 删除任务1
EOF

echo ""
echo "crontab 示例展示完毕。"
echo "如需启用某项任务，请用 crontab -e 添加对应配置行。"
