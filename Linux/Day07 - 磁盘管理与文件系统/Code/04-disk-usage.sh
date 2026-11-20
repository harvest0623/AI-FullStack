#!/bin/bash
# ============================================================
# 文件名：04-disk-usage.sh
# 用途：演示磁盘使用分析：df/du/ncdu、找出大文件大目录、
#       清理策略、inode 检查、文件描述符限制查看与调整
# 适用：Ubuntu 22.04 LTS
# 场景：电商服务器磁盘空间不足排查与清理
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day07 - 04 磁盘使用分析"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"

# ---------- 1. df 文件系统使用情况 ----------

echo -e "\n[1] df -h —— 查看所有文件系统使用情况"
echo "命令：df -h"
df -h
echo ""
echo "字段说明：Filesystem=分区 Size=总大小 Used=已用 Avail=可用 Use%=使用率 Mounted on=挂载点"
echo "告警阈值：使用率 > 80% 警告，> 90% 紧急"

echo -e "\n[2] df -hT —— 显示文件系统类型"
echo "命令：df -hT"
df -hT

echo -e "\n[3] df -h <目录> —— 查看某目录所在分区"
echo "命令：df -h /opt/ecommerce"
df -h /opt/ecommerce 2>/dev/null || df -h /

echo -e "\n[4] df -i —— 查看 inode 使用情况"
echo "命令：df -i"
df -i
echo ""
echo "重要：即使 df -h 显示有空间，inode 用尽也会报 'No space left on device'"
echo "通常发生在大量小文件场景（如 Session、缓存、邮件队列）"

echo -e "\n[5] df -x tmpfs —— 排除 tmpfs"
echo "命令：df -h -x tmpfs -x devtmpfs"
df -h -x tmpfs -x devtmpfs

# ---------- 2. du 目录占用 ----------

echo -e "\n[6] du -sh —— 查看目录总大小"
echo "命令：du -sh /opt /var /home /tmp 2>/dev/null"
sudo du -sh /opt /var /home /tmp 2>/dev/null || du -sh /opt /var /home /tmp 2>/dev/null

echo -e "\n[7] du -h --max-depth=1 —— 一级子目录大小"
echo "命令：du -h --max-depth=1 /var 2>/dev/null | sort -rh | head -n 10"
sudo du -h --max-depth=1 /var 2>/dev/null | sort -rh | head -n 10 || du -h --max-depth=1 /var 2>/dev/null | sort -rh | head -n 10

echo -e "\n[8] du 找出最大的目录"
echo "命令：du -h /opt/ecommerce 2>/dev/null | sort -rh | head -n 10"
sudo du -h /opt/ecommerce 2>/dev/null | sort -rh | head -n 10 || echo "（/opt/ecommerce 不存在）"

echo -e "\n[9] du 找出最大的文件"
echo "命令：find / -type f -size +100M 2>/dev/null | xargs ls -lh 2>/dev/null | sort -k5 -rh | head -n 10"
echo "查找大于 100MB 的文件："
sudo find / -type f -size +100M 2>/dev/null | head -n 10 | xargs ls -lh 2>/dev/null | awk '{print $5, $9}' | head -n 10 || echo "（需要 sudo 才能扫描全部目录）"

echo -e "\n[10] du -sh * —— 当前目录下按大小排序"
echo "命令：du -sh * 2>/dev/null | sort -rh"
echo "（在 /var/log 下演示）"
cd /var/log 2>/dev/null && du -sh * 2>/dev/null | sort -rh | head -n 10; cd - >/dev/null

# ---------- 3. ncdu 交互式分析 ----------

echo -e "\n[11] ncdu —— 交互式磁盘分析（推荐）"
if command -v ncdu >/dev/null 2>&1; then
    echo "ncdu 已安装"
    echo "命令：ncdu /"
    echo "  方向键导航 / d 删除 / q 退出 / ? 帮助"
    echo "  比 du 更快、更直观，支持交互删除"
    echo ""
    echo "命令：ncdu -x /  # -x 不跨文件系统"
    echo "命令：ncdu -e /var  # -e 启用扩展信息（显示权限/属主）"
else
    echo "未安装 ncdu，可执行：sudo apt install -y ncdu"
    echo "ncdu 是交互式的 du，比 du 更快更直观，强烈推荐"
fi

# ---------- 4. 大文件清理策略 ----------

echo -e "\n[12] 电商服务器典型可清理位置"
cat <<'EOF'
┌──────────────────────────────────────┬────────────────────────────────┐
│ 位置                                 │ 清理方式                       │
├──────────────────────────────────────┼────────────────────────────────┤
│ /var/log/*.log.[0-9]*               │ 删除旧日志（logrotate 管理）   │
│ /var/log/journal/                   │ journalctl --vacuum-size=500M  │
│ /var/log/nginx/access.log*          │ 清理或归档旧 access log        │
│ /tmp/*                              │ 重启自动清理，或定时删 >7天    │
│ /var/cache/apt/archives/*.deb       │ apt clean                      │
│ /opt/ecommerce/logs/*.log.[0-9]*    │ 删除旧应用日志                 │
│ /opt/ecommerce/node_modules         │ 不需要时删除                   │
│ /var/lib/docker/                    │ docker system prune -a         │
│ ~/.npm/_cacache                     │ npm cache clean --force        │
│ ~/.cache/pip                        │ pip cache purge                │
│ /var/lib/mysql/binlog.*             │ PURGE BINARY LOGS BEFORE NOW() │
└──────────────────────────────────────┴────────────────────────────────┘
EOF

echo -e "\n[13] 清理命令演示"
cat <<'EOF'
# 1. 清理 apt 缓存（释放数百 MB）
sudo apt clean
sudo apt autoclean             # 仅清理过期包

# 2. 清理 journal 日志（保留最近 7 天）
sudo journalctl --vacuum-time=7d
# 或限制总量
sudo journalctl --vacuum-size=500M

# 3. 清理旧日志文件（保留最近 7 天）
sudo find /var/log -name "*.log.*" -mtime +7 -delete
sudo find /opt/ecommerce/logs -name "*.log.*" -mtime +7 -delete

# 4. 清理临时文件
sudo find /tmp -type f -atime +7 -delete

# 5. 清理 Docker
docker system prune -a -f --volumes

# 6. 清理 npm 缓存
npm cache clean --force
# 或：rm -rf ~/.npm/_cacache

# 7. 清理 pip 缓存
pip cache purge
# 或：rm -rf ~/.cache/pip

# 8. 删除大日志文件内容（保留文件本身）
sudo truncate -s 0 /var/log/nginx/access.log
# 比 rm + reload 更优雅，不影响服务

# 9. 删除空目录
find /var/log -type d -empty -delete
EOF

# ---------- 5. 自动化磁盘告警 ----------

echo -e "\n[14] 自动化磁盘使用率检查脚本（可加入 crontab）"
cat <<'EOF'
#!/bin/bash
# 磁盘使用率告警脚本
THRESHOLD=80
HOSTNAME=$(hostname)
ALERT_EMAIL="ops@example.com"

df -h | awk 'NR>1 && $5 != "-" {print $5 " " $6}' | while read line; do
    USAGE=$(echo "$line" | awk '{print $1}' | tr -d '%')
    PART=$(echo "$line" | awk '{print $2}')
    if [ "$USAGE" -ge "$THRESHOLD" ]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $PART 使用率 ${USAGE}% (阈值 ${THRESHOLD}%)"
        # 发邮件告警
        # echo "..." | mail -s "磁盘告警 $HOSTNAME" $ALERT_EMAIL
    fi
done

# 加入 crontab 每小时检查
# crontab -e
# 0 * * * * /opt/ecommerce/scripts/disk-alert.sh >> /var/log/disk-alert.log 2>&1
EOF

# ---------- 6. inode 检查 ----------

echo -e "\n[15] inode 使用检查"
echo "命令：df -i"
df -i
echo ""
echo "高 inode 使用率场景："
cat <<'EOF'
- 大量 Session 文件（PHP /var/lib/php/sessions）
- 邮件队列（/var/spool/mqueue）
- 海量小图片/缓存
- 监控数据（Prometheus / RRD）

排查步骤：
1. df -i 找出 inode 使用率高的分区
2. sudo find /分区 -xdev -type f | wc -l   # 统计文件数
3. sudo find /分区 -xdev -type d -exec sh -c 'echo $(find "$0" -maxdepth 1 | wc -l) "$0"' {} \; | sort -rn | head
4. 定位到大量小文件目录后清理

# 创建大量小文件触发 inode 耗尽（仅演示）
# for i in $(seq 1 100000); do touch /tmp/small-$i; done
EOF

echo -e "\n[16] 重新格式化时指定更多 inode"
cat <<'EOF'
# ext4 默认每 16KB 一个 inode
# 小文件多时可调小（更多 inode）
sudo mkfs.ext4 -N 1000000 /dev/sdb1           # 指定 inode 数
sudo mkfs.ext4 -i 4096 /dev/sdb1               # 每 4KB 一个 inode（更密集）
# -i bytes-per-inode 越小 inode 越多

# 查看现有 ext4 inode 信息
sudo tune2fs -l /dev/sda1 | grep -i inode
EOF

# ---------- 7. 文件描述符限制 ----------

echo -e "\n[17] ulimit -n —— 查看当前文件描述符上限"
echo "命令：ulimit -n"
ulimit -n
echo "说明：默认 1024，高并发服务（Nginx/MySQL/Node.js）需要调到 65536+"

echo -e "\n[18] 查看某进程的文件描述符上限"
NGINX_PID=$(pgrep -f nginx | head -n1)
if [ -n "$NGINX_PID" ]; then
    echo "命令：cat /proc/$NGINX_PID/limits | grep 'open files'"
    cat /proc/$NGINX_PID/limits | grep "open files"
else
    SELF_PID=$$
    echo "（无 nginx 进程，查看当前 Shell PID=$SELF_PID）"
    echo "命令：cat /proc/$SELF_PID/limits | grep 'open files'"
    cat /proc/$SELF_PID/limits | grep "open files"
fi

echo -e "\n[19] 查看进程已打开的文件描述符数量"
SELF_PID=$$
echo "命令：ls /proc/$SELF_PID/fd/ | wc -l"
ls /proc/$SELF_PID/fd/ 2>/dev/null | wc -l

echo -e "\n[20] 查看进程打开的所有文件描述符"
echo "命令：ls -l /proc/$SELF_PID/fd/ | head -n 10"
ls -l /proc/$SELF_PID/fd/ 2>/dev/null | head -n 10
echo "字段说明：0=标准输入 1=标准输出 2=标准错误 3+=打开的文件/socket"

echo -e "\n[21] 临时调整文件描述符上限"
cat <<'EOF'
# 当前 Shell 临时调整（仅当前会话有效）
ulimit -n 65536
ulimit -n                    # 验证

# 注意：ulimit 只能调到 hard limit 范围内
# 查看 hard limit
ulimit -Hn
# 查看soft limit
ulimit -Sn
EOF

echo -e "\n[22] 永久调整文件描述符上限"
cat <<'EOF'
# 方法一：/etc/security/limits.conf（传统方式）
sudo tee -a /etc/security/limits.conf <<EOF
# 文件描述符上限
* soft nofile 65536
* hard nofile 65536
# 或仅针对某用户
deploy soft nofile 65536
deploy hard nofile 65536
# 进程数限制
* soft nproc 65535
* hard nproc 65535
EOF

# 方法二：/etc/security/limits.d/ 模块化（推荐）
sudo tee /etc/security/limits.d/99-ecommerce.conf <<EOF
deploy soft nofile 65536
deploy hard nofile 65536
EOF

# 方法三：systemd 服务在单元文件中设置
# /etc/systemd/system/ecommerce-backend.service
# [Service]
# LimitNOFILE=65536

# 重新登录后生效（limits.conf 在 PAM 阶段读取）
# systemd 服务需重启：sudo systemctl daemon-reload && sudo systemctl restart X

# 验证
# 重新登录后：ulimit -n
# 服务：cat /proc/$(pgrep -f service)/limits | grep "open files"
EOF

echo -e "\n[23] 系统级文件描述符上限"
echo "命令：cat /proc/sys/fs/file-max"
cat /proc/sys/fs/file-max
echo ""
echo "命令：cat /proc/sys/fs/file-nr  # 已分配/未使用/系统上限"
cat /proc/sys/fs/file-nr
echo "字段说明：第一列=已分配fd 第二列=已分配但未使用 第三列=系统上限"

echo -e "\n[24] 调整系统级 fd 上限"
cat <<'EOF'
# 临时
sudo sysctl -w fs.file-max=1000000

# 永久
echo 'fs.file-max = 1000000' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
EOF

echo -e "\n============================================================"
echo "  Day07 - 04 磁盘使用分析 完成"
echo "============================================================"
