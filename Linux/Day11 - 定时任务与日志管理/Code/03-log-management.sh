#!/bin/bash
# ============================================================
# 文件名：03-log-management.sh
# 用途：日志管理脚本——查看各类系统日志、journalctl 查询、
#       日志清理策略、应用日志检查
# 场景：电商项目 /opt/ecommerce/ 运维日志排查
# 语法：bash 03-log-management.sh
# 权限：部分命令需要 sudo（已标注），普通用户可执行大部分查询
# ============================================================

set -uo pipefail      # 不用 -e，避免某条查询失败就退出

# ---------- 颜色输出 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
section() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

echo -e "${CYAN}========== Day11 - 03 日志管理脚本 ==========${NC}"
info "主机：$(hostname)  时间：$(date '+%F %T')"

# ============================================================
# 一、系统日志查看
# ============================================================
section "一、系统日志查看"

# 1. 全局系统日志（Ubuntu: syslog, CentOS: messages）
info "1. 全局系统日志（最近 10 行）"
if [[ -f /var/log/syslog ]]; then
    tail -n 10 /var/log/syslog
elif [[ -f /var/log/messages ]]; then
    tail -n 10 /var/log/messages
else
    warn "未找到 syslog 或 messages"
fi

echo ""
info "2. 认证日志（最近 10 行，登录记录）"
if [[ -f /var/log/auth.log ]]; then
    tail -n 10 /var/log/auth.log
elif [[ -f /var/log/secure ]]; then
    tail -n 10 /var/log/secure
else
    warn "未找到 auth.log 或 secure"
fi

echo ""
info "3. 查找登录失败记录（暴力破解排查）"
if [[ -f /var/log/auth.log ]]; then
    grep "Failed password" /var/log/auth.log 2>/dev/null | tail -n 5 || info "  无登录失败记录"
elif [[ -f /var/log/secure ]]; then
    grep "Failed password" /var/log/secure 2>/dev/null | tail -n 5 || info "  无登录失败记录"
fi

# 4. cron 日志
echo ""
info "4. cron 任务执行日志（最近 10 条）"
if [[ -f /var/log/cron.log ]]; then
    grep CRON /var/log/cron.log | tail -n 10
elif [[ -f /var/log/cron ]]; then
    grep CRON /var/log/cron | tail -n 10
else
    info "  cron 日志未单独记录，可用 journalctl -u cron 查看"
    journalctl -u cron --no-pager -n 10 2>/dev/null || true
fi

# 5. 内核日志 dmesg
echo ""
info "5. 内核日志 dmesg（最近 10 条，带时间戳）"
dmesg -T 2>/dev/null | tail -n 10 || warn "dmesg 需要 sudo 权限"

# 6. 登录历史
echo ""
info "6. 最近登录记录（last）"
last -n 5 2>/dev/null || warn "last 命令不可用"

# ============================================================
# 二、journalctl 查询
# ============================================================
section "二、journalctl 查询"

info "1. 最近 10 条系统日志"
journalctl --no-pager -n 10 2>/dev/null || warn "journalctl 不可用"

echo ""
info "2. 今天的错误级别日志（err 及以上）"
journalctl --no-pager --since today -p err 2>/dev/null | tail -n 20 || warn "无错误日志或 journalctl 不可用"

echo ""
info "3. SSH 服务日志（最近 10 条）"
journalctl --no-pager -u ssh -n 10 2>/dev/null || journalctl --no-pager -u sshd -n 10 2>/dev/null || warn "无 SSH 服务日志"

echo ""
info "4. 最近 1 小时的日志"
journalctl --no-pager --since "1 hour ago" 2>/dev/null | tail -n 15 || true

echo ""
info "5. 本次启动的日志概览"
journalctl --no-pager --boot 2>/dev/null | tail -n 10 || true

# ============================================================
# 三、日志磁盘占用与清理
# ============================================================
section "三、日志磁盘占用与清理"

info "1. /var/log 磁盘占用（前 20 大文件/目录）"
if [[ $UID -eq 0 ]]; then
    du -sh /var/log/* 2>/dev/null | sort -rh | head -n 20
else
    info "  （需 sudo 查看完整占用）"
    du -sh /var/log/* 2>/dev/null | sort -rh | head -n 20 || true
fi

echo ""
info "2. journal 日志磁盘占用"
journalctl --disk-usage 2>/dev/null || warn "journalctl 不可用"

echo ""
info "3. 大日志文件排查（>100M）"
if [[ $UID -eq 0 ]]; then
    find /var/log -type f -size +100M -exec ls -lh {} \; 2>/dev/null || info "  无超大日志文件"
else
    info "  （需 sudo 查找 /var/log 下大文件）"
fi

echo ""
info "4. journal 日志清理策略（演示，不实际执行）"
cat <<'EOF'
  # 清理 7 天前的 journal 日志
  sudo journalctl --vacuum-time=7d

  # 限制 journal 总大小为 500MB
  sudo journalctl --vacuum-size=500M

  # 限制 journal 保留文件数
  sudo journalctl --vacuum-files=5

  # 永久限制：编辑 /etc/systemd/journald.conf
  # SystemMaxUse=500M
  # MaxRetentionSec=2week
  # 然后 sudo systemctl restart systemd-journald
EOF

echo ""
info "5. 清理旧日志文件（演示，不实际执行）"
cat <<'EOF'
  # 删除 30 天前的 .gz 压缩日志
  find /var/log -name "*.gz" -mtime +30 -delete

  # 清空日志文件（保留文件本身，不重启服务）
  truncate -s 0 /var/log/some.log

  # 用 logrotate 正规轮转（推荐）
  sudo logrotate -f /etc/logrotate.d/ecommerce
EOF

# ============================================================
# 四、应用日志检查
# ============================================================
section "四、应用日志检查"

APP_LOG_DIR="/opt/ecommerce/logs"

info "1. 电商项目日志目录：$APP_LOG_DIR"
if [[ -d "$APP_LOG_DIR" ]]; then
    echo "  日志文件列表："
    ls -lh "$APP_LOG_DIR"/*.log 2>/dev/null | awk '{print "    "$NF" ("$5")"}' || info "  无 .log 文件"
    echo ""
    echo "  日志总大小：$(du -sh "$APP_LOG_DIR" 2>/dev/null | awk '{print $1}')"
else
    warn "  日志目录不存在：$APP_LOG_DIR"
    info "  创建测试目录与日志..."
    mkdir -p "$APP_LOG_DIR" 2>/dev/null && {
        echo "[$(date)] INFO  应用启动" > "$APP_LOG_DIR/app.log"
        echo "[$(date)] INFO  收到请求 GET /api/products" >> "$APP_LOG_DIR/app.log"
        echo "[$(date)] WARN  响应较慢: 1.2s" >> "$APP_LOG_DIR/app.log"
        echo "[$(date)] ERROR 数据库连接超时" >> "$APP_LOG_DIR/app.log"
        echo "[$(date)] INFO  应用就绪" >> "$APP_LOG_DIR/app.log"
        success "  已创建测试日志：$APP_LOG_DIR/app.log"
    } || warn "  无法创建目录（权限不足）"
fi

echo ""
info "2. 应用错误日志（含 ERROR 的行）"
if [[ -d "$APP_LOG_DIR" ]]; then
    grep -r "ERROR" "$APP_LOG_DIR"/*.log 2>/dev/null | tail -n 10 || info "  无错误日志"
fi

echo ""
info "3. 应用警告日志（含 WARN 的行）"
if [[ -d "$APP_LOG_DIR" ]]; then
    grep -r "WARN" "$APP_LOG_DIR"/*.log 2>/dev/null | tail -n 10 || info "  无警告日志"
fi

echo ""
info "4. Nginx 访问日志（最近 10 条）"
NGINX_ACCESS="/var/log/nginx/access.log"
if [[ -f "$NGINX_ACCESS" ]]; then
    tail -n 10 "$NGINX_ACCESS"
else
    warn "  Nginx 访问日志不存在：$NGINX_ACCESS"
fi

echo ""
info "5. Nginx 错误日志（最近 10 条）"
NGINX_ERROR="/var/log/nginx/error.log"
if [[ -f "$NGINX_ERROR" ]]; then
    tail -n 10 "$NGINX_ERROR"
else
    warn "  Nginx 错误日志不存在：$NGINX_ERROR"
fi

# ============================================================
# 五、PM2 日志（若安装了 PM2）
# ============================================================
section "五、PM2 应用日志"

if command -v pm2 >/dev/null 2>&1; then
    info "PM2 进程列表："
    pm2 list 2>/dev/null || true

    echo ""
    info "PM2 日志目录：~/.pm2/logs/"
    ls -lh ~/.pm2/logs/ 2>/dev/null || info "  无 PM2 日志"

    echo ""
    info "PM2 日志大小："
    du -sh ~/.pm2/logs/ 2>/dev/null || true

    echo ""
    info "PM2 日志管理命令："
    echo "  pm2 logs                    # 查看所有应用日志（实时）"
    echo "  pm2 logs app --lines 100    # 指定应用最近 100 行"
    echo "  pm2 flush                   # 清空所有日志"
    echo "  pm2 install pm2-logrotate   # 安装 PM2 日志轮转模块"
else
    info "未安装 PM2，跳过 PM2 日志检查"
fi

# ============================================================
# 六、Docker 日志（若安装了 Docker）
# ============================================================
section "六、Docker 容器日志"

if command -v docker >/dev/null 2>&1; then
    if [[ $UID -ne 0 ]] && ! groups | grep -q docker; then
        warn "当前用户不在 docker 组，需 sudo 或加入 docker 组"
    fi

    info "运行中的容器："
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null || warn "无法访问 docker"

    echo ""
    info "Docker 日志磁盘占用："
    sudo sh -c 'du -sh /var/lib/docker/containers/*/*-json.log 2>/dev/null | sort -rh | head -5' 2>/dev/null \
        || info "  （需 sudo 查看 docker 日志占用）"

    echo ""
    info "Docker 日志管理建议："
    cat <<'EOF'
  # 查看容器日志
  docker logs <container>
  docker logs -f --tail 100 <container>

  # 限制日志大小：编辑 /etc/docker/daemon.json
  {
    "log-driver": "json-file",
    "log-opts": {
      "max-size": "10m",
      "max-file": "3"
    }
  }
  # 然后 sudo systemctl restart docker
EOF
else
    info "未安装 Docker，跳过 Docker 日志检查"
fi

# ============================================================
# 七、日志收集方案简介
# ============================================================
section "七、日志收集方案简介"

cat <<'EOF'
生产环境推荐集中式日志管理：

1. ELK Stack
   - Elasticsearch：存储与搜索
   - Logstash：日志采集与处理
   - Kibana：可视化
   - 适合：大型项目，功能全面，资源消耗大

2. Loki + Grafana
   - Loki：日志存储（轻量）
   - Promtail：日志采集
   - Grafana：可视化
   - 适合：已有 Prometheus/Grafana 的环境，轻量级

3. Docker 日志驱动
   - fluentd / fluentbit 驱动直接把日志发到集中系统
   - 适合：容器化环境
EOF

echo ""
success "日志管理脚本执行完毕。"
