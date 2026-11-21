#!/bin/bash
# ============================================================
# 文件名：01-ufw-firewall.sh
# 用途：ufw 防火墙配置演示脚本
# 场景：电商服务器 192.168.1.100 防火墙配置
# 说明：演示 ufw enable/status/allow/deny/来源限制
#       为电商场景配置：允许 80/443/SSH，拒绝 3306/6379 外部访问
# 运行：sudo bash 01-ufw-firewall.sh
# 权限：需要 root/sudo 权限
# ============================================================

set -euo pipefail

# ---------- 颜色输出函数 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }
section() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

# ---------- 日志记录函数 ----------
LOG_FILE="/var/log/ufw-config-$(date +%Y%m%d-%H%M%S).log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# ---------- 权限检查 ----------
if [ "${EUID}" -ne 0 ]; then
    error "此脚本需要 root 权限执行，请使用 sudo"
    echo "  sudo bash $0"
    exit 1
fi

log "ufw 防火墙配置脚本启动"
log "服务器：192.168.1.100 (Ubuntu 22.04)"

# ============================================================
# 第一部分：ufw 基础命令
# ============================================================
section "第一部分：ufw 基础命令"

# 检查 ufw 是否安装
if ! command -v ufw &> /dev/null; then
    info "ufw 未安装，安装中..."
    apt update && apt install -y ufw
fi
success "ufw 已安装"
echo ""

# 查看当前 ufw 状态
log "查看当前 ufw 状态"
ufw status verbose
echo ""

info "ufw 基础命令："
echo "  ufw enable              → 启用防火墙"
echo "  ufw disable             → 禁用防火墙"
echo "  ufw status              → 查看状态"
echo "  ufw status verbose      → 查看详细状态"
echo "  ufw reset               → 重置所有规则"
echo "  ufw reload              → 重新加载规则"
echo "  ufw default deny incoming  → 默认拒绝入站"
echo "  ufw default allow outgoing → 默认允许出站"

# ============================================================
# 第二部分：设置默认策略
# ============================================================
section "第二部分：设置默认策略"

# 设置默认策略：拒绝所有入站，允许所有出站
log "设置默认策略：deny incoming / allow outgoing"
ufw default deny incoming
ufw default allow outgoing
success "默认策略已设置"
echo ""

info "默认策略说明："
echo "  deny incoming  → 拒绝所有外部主动连接（安全优先）"
echo "  allow outgoing → 允许本机主动向外连接（正常通信需要）"
echo "  后续用 allow 规则逐个放行需要的端口"

# ============================================================
# 第三部分：放行必要端口（电商场景）
# ============================================================
section "第三部分：放行必要端口（电商场景）"

# SSH 端口（默认 22，如已改端口需放行新端口）
log "放行 SSH 端口 22"
ufw allow 22/tcp
success "已放行 SSH (22/tcp)"

# HTTP 端口
log "放行 HTTP 端口 80"
ufw allow 80/tcp
success "已放行 HTTP (80/tcp)"

# HTTPS 端口
log "放行 HTTPS 端口 443"
ufw allow 443/tcp
success "已放行 HTTPS (443/tcp)"

echo ""

# 放行 Node.js 应用端口（仅内网访问）
log "放行 Node.js 端口 3000（仅内网 192.168.1.0/24）"
ufw allow from 192.168.1.0/24 to any port 3000
success "已放行 Node.js (3000) 限内网访问"
echo ""

info "电商场景端口规划："
echo "  ┌──────────┬──────────────────┬──────────────────────────┐"
echo "  │ 端口     │ 服务             │ 访问策略                 │"
echo "  ├──────────┼──────────────────┼──────────────────────────┤"
echo "  │ 22/tcp   │ SSH              │ 允许（建议限 IP）        │"
echo "  │ 80/tcp   │ HTTP (Nginx)     │ 允许（公网访问）         │"
echo "  │ 443/tcp  │ HTTPS (Nginx)    │ 允许（公网访问）         │"
echo "  │ 3000/tcp │ Node.js          │ 仅内网（Nginx 反代）     │"
echo "  │ 3306/tcp │ MySQL            │ 拒绝外部（仅内网）       │"
echo "  │ 6379/tcp │ Redis            │ 拒绝外部（仅内网）       │"
echo "  └──────────┴──────────────────┴──────────────────────────┘"

# ============================================================
# 第四部分：拒绝数据库端口外部访问
# ============================================================
section "第四部分：拒绝数据库端口外部访问"

# 拒绝 MySQL 外部访问
log "拒绝 MySQL 端口 3306 外部访问"
ufw deny 3306
success "已拒绝 MySQL (3306) 外部访问"

# 拒绝 Redis 外部访问
log "拒绝 Redis 端口 6379 外部访问"
ufw deny 6379
success "已拒绝 Redis (6379) 外部访问"
echo ""

# 但允许内网访问数据库（运维需要）
log "允许内网 192.168.1.0/24 访问 MySQL"
ufw allow from 192.168.1.0/24 to any port 3306
success "已允许内网访问 MySQL (3306)"

log "允许内网 192.168.1.0/24 访问 Redis"
ufw allow from 192.168.1.0/24 to any port 6379
success "已允许内网访问 Redis (6379)"
echo ""

warn "安全策略说明："
echo "  MySQL/Redis 端口拒绝所有外部访问"
echo "  只允许内网 192.168.1.0/24 访问（运维管理需要）"
echo "  这样即使数据库密码泄露，外部也无法直接连接"

# ============================================================
# 第五部分：来源 IP 限制（SSH 加固）
# ============================================================
section "第五部分：来源 IP 限制（SSH 加固）"

info "SSH 来源限制方案（可选，按需启用）："
echo ""
echo "  方案一：只允许办公网/跳板机 IP 访问 SSH"
echo "    ufw delete allow 22/tcp                              # 先删除原规则"
echo "    ufw allow from 203.0.113.10 to any port 22          # 跳板机"
echo "    ufw allow from 192.168.1.0/24 to any port 22        # 内网"
echo ""
echo "  方案二：使用非标准端口"
echo "    ufw allow 2222/tcp                                   # 放行新端口"
echo "    （修改 sshd_config Port 2222 后删除 22 端口规则）"
echo ""

# 询问是否启用 SSH 来源限制
read -r -p "是否启用 SSH 来源限制（只允许内网访问 SSH）？[y/N] " response
if [[ "${response}" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    log "启用 SSH 来源限制（只允许内网）"
    ufw delete allow 22/tcp 2>/dev/null || true
    ufw allow from 192.168.1.0/24 to any port 22
    success "SSH 已限制为仅内网访问"
    warn "注意：如果你当前通过公网 SSH 连接，这会导致你断连！"
else
    info "跳过 SSH 来源限制（保持 SSH 对外开放）"
fi

# ============================================================
# 第六部分：启用防火墙
# ============================================================
section "第六部分：启用防火墙"

# 启用前检查 SSH 是否已放行（防止断连）
SSH_ALLOWED=$(ufw status | grep -c "22/tcp" || echo "0")
if [ "${SSH_ALLOWED}" -eq 0 ]; then
    warn "SSH 端口 22 未放行，启用防火墙可能导致断连！"
    warn "自动放行 SSH 端口..."
    ufw allow 22/tcp
fi

# 启用 ufw（-y 自动确认）
log "启用 ufw 防火墙"
echo "y" | ufw enable
success "ufw 防火墙已启用"
echo ""

# 查看最终规则
log "查看最终防火墙规则"
ufw status numbered
echo ""

# ============================================================
# 第七部分：应用配置文件
# ============================================================
section "第七部分：应用配置文件（自定义）"

info "ufw 支持基于应用配置文件管理规则"
echo "  配置文件目录：/etc/ufw/applications.d/"
echo ""

# 创建电商应用配置文件
log "创建电商应用配置文件"
cat > /etc/ufw/applications.d/ecommerce <<'EOF'
[Ecommerce]
title=Ecommerce Web Service
description=Ecommerce full stack (HTTP, HTTPS, SSH)
ports=80,443,22/tcp

[EcommerceInternal]
title=Ecommerce Internal Service
description=Ecommerce internal (MySQL, Redis) - internal access only
ports=3306,6379/tcp
EOF

# 更新应用配置
ufw app update Ecommerce
success "电商应用配置文件已创建"

log "查看可用应用配置"
ufw app list
echo ""

info "基于应用放行示例："
echo "  ufw allow 'Ecommerce'           → 放行电商 Web 服务（80/443/22）"
echo "  ufw allow 'OpenSSH'             → 放行 SSH"
echo "  ufw allow 'Nginx Full'          → 放行 Nginx（80/443）"

# ============================================================
# 第八部分：规则管理演示
# ============================================================
section "第八部分：规则管理演示"

info "规则管理常用命令："
echo ""
echo "  # 查看规则（带编号）"
echo "  ufw status numbered"
echo ""
echo "  # 按编号删除规则"
echo "  ufw delete 3"
echo ""
echo "  # 按语法删除规则"
echo "  ufw delete allow 80/tcp"
echo ""
echo "  # 重置所有规则（慎用）"
echo "  ufw reset"
echo ""
echo "  # 重新加载规则"
echo "  ufw reload"
echo ""

# 显示当前所有规则
log "当前所有防火墙规则："
ufw status numbered
echo ""

# ============================================================
# 第九部分：防火墙验证
# ============================================================
section "第九部分：防火墙验证"

info "验证防火墙配置："
echo ""

# 检查 ufw 是否启用
if ufw status | grep -q "Status: active"; then
    success "防火墙已启用"
else
    error "防火墙未启用！"
fi

# 检查关键端口
check_port() {
    local port=$1
    local name=$2
    if ufw status | grep -q "${port}/tcp"; then
        success "${name} (端口 ${port}) 规则已配置"
    else
        warn "${name} (端口 ${port}) 规则未配置"
    fi
}

check_port 22 "SSH"
check_port 80 "HTTP"
check_port 443 "HTTPS"

# 检查数据库是否被拒绝
if ufw status | grep -q "3306"; then
    success "MySQL (3306) 规则已配置"
fi
if ufw status | grep -q "6379"; then
    success "Redis (6379) 规则已配置"
fi

echo ""
success "ufw 防火墙配置完成！"
log "日志文件：${LOG_FILE}"
echo ""
info "验证建议："
echo "  1. 从外部机器尝试访问 80/443（应该成功）"
echo "  2. 从外部机器尝试访问 3306/6379（应该被拒绝）"
echo "  3. 从内网机器尝试访问 3306/6379（应该成功）"
echo "  4. 用 nmap -sT -p 22,80,443,3306,6379 192.168.1.100 扫描验证"
