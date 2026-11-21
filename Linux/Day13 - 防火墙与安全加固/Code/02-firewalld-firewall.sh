#!/bin/bash
# ============================================================
# 文件名：02-firewalld-firewall.sh
# 用途：firewalld 防火墙配置演示脚本
# 场景：CentOS/RHEL 环境防火墙配置（电商服务器示例）
# 说明：演示 firewalld 的 zone/service/port/rich-rule 配置
#       如果在 Ubuntu 上执行，说明 ufw 与 firewalld 的对应关系
# 运行：sudo bash 02-firewalld-firewall.sh
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
section() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

# ---------- 日志记录函数 ----------
LOG_FILE="/tmp/firewalld-config-$(date +%Y%m%d-%H%M%S).log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "firewalld 防火墙配置脚本启动"

# ============================================================
# 环境检测
# ============================================================
section "环境检测"

# 检测当前系统
if command -v firewall-cmd &> /dev/null; then
    success "检测到 firewalld（CentOS/RHEL/Rocky 环境）"
    FIREWALLD_AVAILABLE=true
elif command -v ufw &> /dev/null; then
    warn "当前系统是 Ubuntu（使用 ufw），未安装 firewalld"
    info "本脚本将展示 firewalld 的配置方法（仅供参考）"
    info "如需在 Ubuntu 上安装 firewalld，可执行：apt install -y firewalld"
    FIREWALLD_AVAILABLE=false
else
    warn "未检测到 firewalld 或 ufw"
    FIREWALLD_AVAILABLE=false
fi
echo ""

# ============================================================
# 第一部分：firewalld zone 概念
# ============================================================
section "第一部分：firewalld zone 概念"

info "firewalld 基于 zone（区域）管理规则，不同网络环境使用不同 zone："
echo ""
echo "  ┌──────────┬──────────────────────────┬──────────────────────┐"
echo "  │ zone     │ 信任级别                 │ 适用场景             │"
echo "  ├──────────┼──────────────────────────┼──────────────────────┤"
echo "  │ drop     │ 最低（丢弃所有入站）     │ 最高安全要求         │"
echo "  │ block    │ 低（拒绝所有，返回消息） │ 高安全要求           │"
echo "  │ public   │ 中（只允许选中连接）     │ 公网服务器（默认）   │"
echo "  │ external │ 中（对外，支持 NAT）     │ 网关/路由器          │"
echo "  │ internal │ 高（信任内网）           │ 内网服务器           │"
echo "  │ dmz      │ 中（非军事区）           │ DMZ 区域服务器       │"
echo "  │ work     │ 较高（工作网络）         │ 办公网络             │"
echo "  │ home     │ 较高（家庭网络）         │ 家庭网络             │"
echo "  │ trusted  │ 最高（允许所有）         │ 内部受信网络         │"
echo "  └──────────┴──────────────────────────┴──────────────────────┘"
echo ""

# 如果 firewalld 可用，展示实际状态
if [ "${FIREWALLD_AVAILABLE}" = "true" ]; then
    log "查看 firewalld 状态"
    firewall-cmd --state
    echo ""

    log "查看默认 zone"
    firewall-cmd --get-default-zone
    echo ""

    log "查看当前激活的 zone"
    firewall-cmd --get-active-zones
    echo ""

    log "查看 public zone 的所有规则"
    firewall-cmd --zone=public --list-all
    echo ""
fi

info "zone 管理命令："
echo "  firewall-cmd --get-default-zone           → 查看默认 zone"
echo "  firewall-cmd --set-default-zone=public    → 设置默认 zone"
echo "  firewall-cmd --get-active-zones           → 查看激活的 zone"
echo "  firewall-cmd --zone=public --list-all     → 查看 zone 详情"
echo "  firewall-cmd --list-all-zones             → 查看所有 zone"

# ============================================================
# 第二部分：服务与端口管理
# ============================================================
section "第二部分：服务与端口管理"

info "firewalld 管理服务与端口："
echo ""
echo "  ┌────────────────────────────────────────────┬──────────────────────────┐"
echo "  │ 命令                                       │ 功能                     │"
echo "  ├────────────────────────────────────────────┼──────────────────────────┤"
echo "  │ firewall-cmd --add-service=http --permanent│ 永久放行 HTTP 服务       │"
echo "  │ firewall-cmd --add-service=https --permanent│ 永久放行 HTTPS 服务    │"
echo "  │ firewall-cmd --add-service=ssh --permanent │ 永久放行 SSH 服务        │"
echo "  │ firewall-cmd --add-port=8080/tcp --permanent│ 永久放行 8080 端口     │"
echo "  │ firewall-cmd --add-port=3000-3100/tcp --permanent│ 放行端口范围       │"
echo "  │ firewall-cmd --reload                      │ 重新加载（使永久生效）   │"
echo "  │ firewall-cmd --list-services               → 查看已放行服务          │"
echo "  │ firewall-cmd --list-ports                  → 查看已放行端口          │"
echo "  │ firewall-cmd --remove-service=http --permanent│ 移除 HTTP 服务       │"
echo "  │ firewall-cmd --remove-port=8080/tcp --permanent│ 移除 8080 端口      │"
echo "  └────────────────────────────────────────────┴──────────────────────────┘"
echo ""

warn "关键理解：runtime vs permanent"
echo "  不加 --permanent：runtime 规则，立即生效但重启失效"
echo "  加 --permanent：永久规则，需 --reload 才生效"
echo "  生产环境建议：先加 --permanent，再 --reload"
echo ""

# 如果 firewalld 可用，执行实际配置
if [ "${FIREWALLD_AVAILABLE}" = "true" ]; then
    log "为电商场景配置 firewalld 规则"
    echo ""

    # 放行 Web 服务
    info "放行 HTTP/HTTPS 服务"
    firewall-cmd --add-service=http --permanent
    firewall-cmd --add-service=https --permanent
    success "已放行 HTTP/HTTPS"

    # 放行 SSH
    info "放行 SSH 服务"
    firewall-cmd --add-service=ssh --permanent
    success "已放行 SSH"

    # 放行 Node.js 端口
    info "放行 Node.js 端口 3000"
    firewall-cmd --add-port=3000/tcp --permanent
    success "已放行 3000/tcp"

    # 重新加载使永久规则生效
    info "重新加载防火墙规则"
    firewall-cmd --reload
    success "规则已重新加载"
    echo ""

    # 查看配置结果
    log "查看已放行的服务"
    firewall-cmd --list-services
    echo ""

    log "查看已放行的端口"
    firewall-cmd --list-ports
    echo ""
fi

# ============================================================
# 第三部分：rich-rule 复杂规则
# ============================================================
section "第三部分：rich-rule 复杂规则"

info "rich-rule 用于配置更复杂的规则（来源 IP 限制等）："
echo ""
echo "  # 只允许内网 192.168.1.0/24 访问 MySQL"
echo "  firewall-cmd --zone=public \\"
echo "    --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 port port=3306 protocol=tcp accept' \\"
echo "    --permanent"
echo ""
echo "  # 只允许内网 192.168.1.0/24 访问 Redis"
echo "  firewall-cmd --zone=public \\"
echo "    --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 port port=6379 protocol=tcp accept' \\"
echo "    --permanent"
echo ""
echo "  # 拒绝某个恶意 IP 的所有访问"
echo "  firewall-cmd --zone=public \\"
echo "    --add-rich-rule='rule family=ipv4 source address=1.2.3.4 reject' \\"
echo "    --permanent"
echo ""
echo "  # 限制 SSH 只允许跳板机访问"
echo "  firewall-cmd --zone=public \\"
echo "    --add-rich-rule='rule family=ipv4 source address=203.0.113.10 port port=22 protocol=tcp accept' \\"
echo "    --permanent"
echo "  firewall-cmd --remove-service=ssh --permanent   # 移除默认 SSH 放行"
echo ""

# 如果 firewalld 可用，执行实际配置
if [ "${FIREWALLD_AVAILABLE}" = "true" ]; then
    log "为电商场景配置 rich-rule"
    echo ""

    # 内网访问 MySQL
    info "配置内网 192.168.1.0/24 访问 MySQL"
    firewall-cmd --zone=public \
        --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 port port=3306 protocol=tcp accept' \
        --permanent
    success "已配置内网访问 MySQL"

    # 内网访问 Redis
    info "配置内网 192.168.1.0/24 访问 Redis"
    firewall-cmd --zone=public \
        --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 port port=6379 protocol=tcp accept' \
        --permanent
    success "已配置内网访问 Redis"

    # 重新加载
    firewall-cmd --reload
    success "规则已重新加载"
    echo ""

    # 查看 rich-rule
    log "查看 public zone 的所有规则（含 rich-rule）"
    firewall-cmd --zone=public --list-all
    echo ""
fi

# ============================================================
# 第四部分：ufw vs firewalld 对比
# ============================================================
section "第四部分：ufw vs firewalld 对应关系"

info "如果你在 Ubuntu 上用 ufw，以下是 firewalld 命令的 ufw 对应："
echo ""
echo "  ┌──────────────────────────┬─────────────────────────────────────────────────┐"
echo "  │ firewalld                │ ufw 对应命令                                    │"
echo "  ├──────────────────────────┼─────────────────────────────────────────────────┤"
echo "  │ --add-service=http       │ ufw allow 80/tcp                                │"
echo "  │ --add-service=https      │ ufw allow 443/tcp                               │"
echo "  │ --add-port=8080/tcp      │ ufw allow 8080/tcp                              │"
echo "  │ --remove-service=http    │ ufw delete allow 80/tcp                         │"
echo "  │ --reload                 │ ufw reload                                      │"
echo "  │ --list-all               │ ufw status verbose                              │"
echo "  │ rich-rule 来源限制       │ ufw allow from 192.168.1.0/24 to any port 3306 │"
echo "  └──────────────────────────┴─────────────────────────────────────────────────┘"
echo ""

info "ufw vs firewalld 对比："
echo "  ┌────────────┬─────────────────────┬─────────────────────────────┐"
echo "  │ 对比项     │ ufw                 │ firewalld                   │"
echo "  ├────────────┼─────────────────────┼─────────────────────────────┤"
echo "  │ 默认发行版 │ Ubuntu / Debian     │ CentOS / RHEL / Rocky       │"
echo "  │ 配置复杂度 │ 简单                │ 中等                        │"
echo "  │ 功能丰富度 │ 基础                │ 丰富（zone/rich-rule）      │"
echo "  │ 规则管理   │ 直接增删            │ runtime + permanent 分离    │"
echo "  │ 适用场景   │ 单机简单防护        │ 复杂网络/多网卡/多 zone     │"
echo "  └────────────┴─────────────────────┴─────────────────────────────┘"

# ============================================================
# 第五部分：iptables 底层说明
# ============================================================
section "第五部分：iptables 底层框架说明"

info "ufw 和 firewalld 底层都是调用 iptables/nftables："
echo ""
echo "  ufw       → iptables（Ubuntu）"
echo "  firewalld → nftables（CentOS 8+）/ iptables（CentOS 7）"
echo ""
echo "  iptables 直接操作命令（了解，不建议直接用）："
echo "    iptables -L -n -v                           → 查看所有规则"
echo "    iptables -A INPUT -p tcp --dport 80 -j ACCEPT  → 允许 80 端口"
echo "    iptables -A INPUT -p tcp --dport 3306 -j DROP  → 拒绝 3306 端口"
echo "    iptables -D INPUT -p tcp --dport 80 -j ACCEPT  → 删除规则"
echo "    iptables-save > /etc/iptables.rules         → 保存规则"
echo "    iptables-restore < /etc/iptables.rules      → 恢复规则"
echo ""
echo "  四表五链："
echo "    四表：filter（过滤）/ nat（地址转换）/ mangle（修改包）/ raw"
echo "    五链：INPUT / OUTPUT / FORWARD / PREROUTING / POSTROUTING"
echo ""

if [ "${FIREWALLD_AVAILABLE}" = "true" ]; then
    log "查看底层 iptables 规则（firewalld 生成的）"
    iptables -L -n -v | head -30
    echo ""
fi

# ============================================================
# 第六部分：电商场景完整配置总结
# ============================================================
section "第六部分：电商场景完整配置总结"

info "电商服务器 192.168.1.100 防火墙配置清单："
echo ""
echo "  ┌──────────┬──────────────────┬──────────────────────────────────┐"
echo "  │ 端口     │ 服务             │ firewalld 配置                  │"
echo "  ├──────────┼──────────────────┼──────────────────────────────────┤"
echo "  │ 22/tcp   │ SSH              │ --add-service=ssh               │"
echo "  │ 80/tcp   │ HTTP (Nginx)     │ --add-service=http              │"
echo "  │ 443/tcp  │ HTTPS (Nginx)    │ --add-service=https             │"
echo "  │ 3000/tcp │ Node.js          │ --add-port=3000/tcp             │"
echo "  │ 3306/tcp │ MySQL            │ rich-rule 限内网 192.168.1.0/24 │"
echo "  │ 6379/tcp │ Redis            │ rich-rule 限内网 192.168.1.0/24 │"
echo "  └──────────┴──────────────────┴──────────────────────────────────┘"
echo ""

info "CentOS 完整配置命令（复制即可执行）："
echo "  # 放行 Web 与 SSH"
echo "  firewall-cmd --add-service=http --permanent"
echo "  firewall-cmd --add-service=https --permanent"
echo "  firewall-cmd --add-service=ssh --permanent"
echo "  firewall-cmd --add-port=3000/tcp --permanent"
echo ""
echo "  # 内网访问数据库"
echo "  firewall-cmd --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 port port=3306 protocol=tcp accept' --permanent"
echo "  firewall-cmd --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 port port=6379 protocol=tcp accept' --permanent"
echo ""
echo "  # 重新加载生效"
echo "  firewall-cmd --reload"
echo ""
echo "  # 验证"
echo "  firewall-cmd --list-all"
echo ""

success "firewalld 防火墙配置演示完成！"
log "日志文件：${LOG_FILE}"
echo ""
info "下一步建议："
echo "  1. 如果是 Ubuntu 环境，运行 01-ufw-firewall.sh 配置 ufw"
echo "  2. 运行 03-ssh-hardening.sh 进行 SSH 安全加固"
echo "  3. 阅读 04-security-checklist.md 学习完整安全检查清单"
