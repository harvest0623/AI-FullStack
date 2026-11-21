#!/bin/bash
# ============================================================
# 文件名：01-server-init.sh
# 用途：服务器初始化综合脚本
# 场景：电商服务器 192.168.1.100 全新初始化
# 说明：系统更新、时区设置、基础工具安装、创建 deploy 用户
#       配置 sudo、SSH 密钥、防火墙配置、SSH 加固
#       内核参数调优、创建项目目录结构
#       幂等可重复执行（已安装/已配置的跳过）
# 运行：sudo bash 01-server-init.sh
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
LOG_FILE="/var/log/server-init-$(date +%Y%m%d-%H%M%S).log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# ---------- 错误处理函数 ----------
handle_error() {
    local exit_code=$?
    error "脚本在第 ${LINENO} 行执行失败，退出码：${exit_code}"
    error "请检查日志：${LOG_FILE}"
    exit ${exit_code}
}
trap 'handle_error' ERR

# ---------- 权限检查 ----------
if [ "${EUID}" -ne 0 ]; then
    error "此脚本需要 root 权限执行，请使用 sudo"
    echo "  sudo bash $0"
    exit 1
fi

# ---------- 配置变量 ----------
DEPLOY_USER="deploy"
DEPLOY_PASSWORD=""                 # 留空则不设置密码（建议用密钥）
SSH_PORT=2222                      # SSH 端口
TIMEZONE="Asia/Shanghai"
PROJECT_ROOT="/opt/ecommerce"

log "服务器初始化脚本启动"
log "服务器：192.168.1.100 (Ubuntu 22.04)"
log "日志文件：${LOG_FILE}"

# ============================================================
# 第一部分：系统更新
# ============================================================
section "第一部分：系统更新"

# 检查是否需要更新
log "更新软件包索引"
apt update -qq

log "升级已安装的软件包"
apt upgrade -y -qq

log "安装安全更新"
unattended-upgrade -d 2>/dev/null || apt install -y unattended-upgrades 2>/dev/null || true

success "系统更新完成"

# ============================================================
# 第二部分：时区与时间同步
# ============================================================
section "第二部分：时区与时间同步"

# 设置时区（幂等：检查当前时区）
CURRENT_TZ=$(timedatectl show --property=Timezone --value 2>/dev/null || echo "")
if [ "${CURRENT_TZ}" != "${TIMEZONE}" ]; then
    log "设置时区为 ${TIMEZONE}"
    timedatectl set-timezone "${TIMEZONE}"
    success "时区已设置为 ${TIMEZONE}"
else
    success "时区已是 ${TIMEZONE}，跳过"
fi

# 开启 NTP 时间同步
if ! timedatectl show --property=NTP --value | grep -q "yes"; then
    log "开启 NTP 时间同步"
    timedatectl set-ntp true
    success "NTP 时间同步已开启"
else
    success "NTP 已开启，跳过"
fi

# 显示当前时间
log "当前时间：$(date)"

# ============================================================
# 第三部分：基础工具安装
# ============================================================
section "第三部分：基础工具安装"

# 需要安装的基础工具列表
BASIC_TOOLS=(
    vim
    git
    curl
    wget
    htop
    sysstat
    iotop
    iftop
    nethogs
    dstat
    glances
    nmon
    smem
    strace
    ltrace
    nmap
    tree
    unzip
    rsync
    net-tools
    dnsutils
    telnet
    mtr-tiny
    jq
    build-essential
)

# 幂等安装：逐个检查是否已安装
log "安装基础工具"
for tool in "${BASIC_TOOLS[@]}"; do
    if dpkg -s "${tool}" &> /dev/null; then
        info "${tool} 已安装，跳过"
    else
        log "安装 ${tool}"
        apt install -y -qq "${tool}" 2>/dev/null || warn "${tool} 安装失败（可能包名不同），跳过"
    fi
done
success "基础工具安装完成"

# ============================================================
# 第四部分：创建部署用户
# ============================================================
section "第四部分：创建部署用户"

# 幂等：检查用户是否已存在
if id "${DEPLOY_USER}" &> /dev/null; then
    success "用户 ${DEPLOY_USER} 已存在，跳过创建"
else
    log "创建部署用户 ${DEPLOY_USER}"
    useradd -m -s /bin/bash "${DEPLOY_USER}"
    success "用户 ${DEPLOY_USER} 已创建"

    # 设置密码（如果配置了密码）
    if [ -n "${DEPLOY_PASSWORD}" ]; then
        echo "${DEPLOY_USER}:${DEPLOY_PASSWORD}" | chpasswd
        success "用户 ${DEPLOY_USER} 密码已设置"
    else
        info "未设置密码（建议使用 SSH 密钥登录）"
    fi
fi

# 配置 sudo 权限（幂等）
if groups "${DEPLOY_USER}" | grep -q "sudo"; then
    success "${DEPLOY_USER} 已在 sudo 组，跳过"
else
    log "将 ${DEPLOY_USER} 加入 sudo 组"
    usermod -aG sudo "${DEPLOY_USER}"
    success "${DEPLOY_USER} 已加入 sudo 组"
fi

# 配置免密 sudo（可选，方便部署）
SUDOERS_FILE="/etc/sudoers.d/${DEPLOY_USER}"
if [ ! -f "${SUDOERS_FILE}" ]; then
    log "配置 ${DEPLOY_USER} 免密 sudo"
    echo "${DEPLOY_USER} ALL=(ALL) NOPASSWD:ALL" > "${SUDOERS_FILE}"
    chmod 440 "${SUDOERS_FILE}"
    success "${DEPLOY_USER} 免密 sudo 已配置"
else
    success "${DEPLOY_USER} 免密 sudo 已配置，跳过"
fi

# ============================================================
# 第五部分：SSH 密钥配置
# ============================================================
section "第五部分：SSH 密钥配置"

# 为 deploy 用户配置 .ssh 目录
DEPLOY_HOME=$(getent passwd "${DEPLOY_USER}" | cut -d: -f6)
SSH_DIR="${DEPLOY_HOME}/.ssh"

if [ ! -d "${SSH_DIR}" ]; then
    log "创建 ${SSH_DIR} 目录"
    mkdir -p "${SSH_DIR}"
    chmod 700 "${SSH_DIR}"
    chown "${DEPLOY_USER}:${DEPLOY_USER}" "${SSH_DIR}"
    success ".ssh 目录已创建"
else
    success ".ssh 目录已存在，跳过"
fi

# 检查 authorized_keys 是否存在
if [ ! -f "${SSH_DIR}/authorized_keys" ]; then
    touch "${SSH_DIR}/authorized_keys"
    chmod 600 "${SSH_DIR}/authorized_keys"
    chown "${DEPLOY_USER}:${DEPLOY_USER}" "${SSH_DIR}/authorized_keys"
    success "authorized_keys 已创建"
fi

info "请将本地公钥添加到服务器："
echo "  # 在本地机器执行："
echo "  ssh-copy-id -p ${SSH_PORT} ${DEPLOY_USER}@192.168.1.100"
echo ""
echo "  # 或手动复制公钥到 ${SSH_DIR}/authorized_keys"

# ============================================================
# 第六部分：防火墙配置
# ============================================================
section "第六部分：防火墙配置"

# 检查 ufw 是否安装
if ! command -v ufw &> /dev/null; then
    log "安装 ufw"
    apt install -y -qq ufw
fi

# 设置默认策略（幂等）
log "设置防火墙默认策略"
ufw default deny incoming 2>/dev/null || true
ufw default allow outgoing 2>/dev/null || true

# 放行必要端口（幂等：检查规则是否已存在）
add_ufw_rule() {
    local rule=$1
    local name=$2
    if ufw status | grep -q "${rule}"; then
        success "${name} 规则已存在，跳过"
    else
        ufw allow ${rule} 2>/dev/null
        success "${name} 规则已添加"
    fi
}

log "配置防火墙规则"
add_ufw_rule "${SSH_PORT}/tcp" "SSH 端口 ${SSH_PORT}"
add_ufw_rule "80/tcp" "HTTP 端口 80"
add_ufw_rule "443/tcp" "HTTPS 端口 443"

# 拒绝数据库端口外部访问（幂等）
deny_ufw_rule() {
    local port=$1
    local name=$2
    if ufw status | grep -q "${port}.*DENY"; then
        success "${name} DENY 规则已存在，跳过"
    else
        ufw deny ${port} 2>/dev/null || true
        success "${name} DENY 规则已添加"
    fi
}

deny_ufw_rule "3306" "MySQL 端口"
deny_ufw_rule "6379" "Redis 端口"

# 内网访问数据库
add_internal_rule() {
    local port=$1
    local name=$2
    if ufw status | grep -q "192.168.1.0/24.*${port}"; then
        success "${name} 内网规则已存在，跳过"
    else
        ufw allow from 192.168.1.0/24 to any port ${port} 2>/dev/null || true
        success "${name} 内网规则已添加"
    fi
}

add_internal_rule "3306" "MySQL"
add_internal_rule "6379" "Redis"

# 启用防火墙（幂等：检查是否已启用）
if ufw status | grep -q "Status: active"; then
    success "防火墙已启用，跳过"
else
    log "启用防火墙"
    echo "y" | ufw enable
    success "防火墙已启用"
fi

# 显示防火墙状态
log "当前防火墙规则："
ufw status numbered

# ============================================================
# 第七部分：SSH 加固
# ============================================================
section "第七部分：SSH 加固"

SSHD_CONFIG="/etc/ssh/sshd_config"

# 备份原配置（幂等：检查备份是否已存在）
BACKUP_FILE="${SSHD_CONFIG}.backup.$(date +%Y%m%d%H%M%S)"
if [ ! -f "${SSHD_CONFIG}.backup" ]; then
    log "备份 sshd_config"
    cp "${SSHD_CONFIG}" "${BACKUP_FILE}"
    success "已备份到 ${BACKUP_FILE}"
fi

# 修改 SSH 配置的函数（幂等：先检查是否已配置）
update_sshd_config() {
    local key=$1
    local value=$2
    # 检查是否已配置
    if grep -q "^${key} ${value}" "${SSHD_CONFIG}"; then
        success "${key} 已配置为 ${value}，跳过"
    else
        # 注释掉原有配置
        sed -i "s/^${key}.*/#&/" "${SSHD_CONFIG}"
        # 追加新配置
        echo "${key} ${value}" >> "${SSHD_CONFIG}"
        success "${key} 已设置为 ${value}"
    fi
}

log "加固 SSH 配置"
update_sshd_config "Port" "${SSH_PORT}"
update_sshd_config "PermitRootLogin" "no"
update_sshd_config "PasswordAuthentication" "no"
update_sshd_config "PubkeyAuthentication" "yes"
update_sshd_config "MaxAuthTries" "3"
update_sshd_config "LoginGraceTime" "30"
update_sshd_config "ClientAliveInterval" "300"
update_sshd_config "ClientAliveCountMax" "2"
update_sshd_config "PermitEmptyPasswords" "no"
update_sshd_config "X11Forwarding" "no"
update_sshd_config "AllowUsers" "${DEPLOY_USER}"

# 验证配置语法
log "验证 sshd 配置语法"
if sshd -t; then
    success "sshd 配置语法正确"
    # 重启 sshd
    log "重启 sshd"
    systemctl restart sshd
    success "sshd 已重启"
else
    error "sshd 配置语法错误！"
    warn "可用备份恢复：cp ${BACKUP_FILE} ${SSHD_CONFIG}"
    exit 1
fi

# ============================================================
# 第八部分：fail2ban 防暴力破解
# ============================================================
section "第八部分：fail2ban 防暴力破解"

# 幂等安装
if ! command -v fail2ban-client &> /dev/null; then
    log "安装 fail2ban"
    apt install -y -qq fail2ban
fi
success "fail2ban 已安装"

# 配置 jail.local（幂等：检查是否已配置）
JAIL_LOCAL="/etc/fail2ban/jail.local"
if [ -f "${JAIL_LOCAL}" ]; then
    success "fail2ban 配置已存在，跳过"
else
    log "创建 fail2ban 配置"
    cat > "${JAIL_LOCAL}" <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
banaction = ufw
ignoreip = 127.0.0.1/8 ::1 192.168.1.0/24

[sshd]
enabled = true
port = ${SSH_PORT}
logpath = /var/log/auth.log
maxretry = 3
EOF
    success "fail2ban 配置已创建"
fi

# 启动并设置开机自启（幂等）
log "启动 fail2ban"
systemctl restart fail2ban
systemctl enable fail2ban 2>/dev/null || true
success "fail2ban 已启动并设置开机自启"

# ============================================================
# 第九部分：ulimit 资源限制调优
# ============================================================
section "第九部分：ulimit 资源限制调优"

# 配置文件描述符限制（幂等：检查是否已配置）
LIMITS_FILE="/etc/security/limits.d/ecommerce.conf"
if [ -f "${LIMITS_FILE}" ]; then
    success "ulimit 配置已存在，跳过"
else
    log "配置文件描述符限制"
    cat > "${LIMITS_FILE}" <<EOF
# 电商项目文件描述符与进程数调优
*               soft    nofile          65535
*               hard    nofile          65535
*               soft    nproc           65535
*               hard    nproc           65535
root            soft    nofile          65535
root            hard    nofile          65535
${DEPLOY_USER}  soft    nofile          65535
${DEPLOY_USER}  hard    nofile          65535
EOF
    success "ulimit 配置已创建（重新登录后生效）"
fi

# ============================================================
# 第十部分：sysctl 内核参数调优
# ============================================================
section "第十部分：sysctl 内核参数调优"

# 配置内核参数（幂等：检查是否已配置）
SYSCTL_FILE="/etc/sysctl.d/99-ecommerce.conf"
if [ -f "${SYSCTL_FILE}" ]; then
    success "sysctl 配置已存在，跳过"
else
    log "配置内核参数"
    cat > "${SYSCTL_FILE}" <<'EOF'
# 电商服务器内核参数调优

# 网络参数
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.ip_local_port_range = 10000 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_syncookies = 1
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# 内存参数
vm.swappiness = 10
vm.overcommit_memory = 1

# 文件描述符
fs.file-max = 1048576
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 1048576
EOF

    # 加载配置
    sysctl -p "${SYSCTL_FILE}" > /dev/null 2>&1
    success "内核参数已配置并加载"
fi

# ============================================================
# 第十一部分：创建项目目录结构
# ============================================================
section "第十一部分：创建项目目录结构"

# 创建项目目录（幂等：mkdir -p）
log "创建项目目录结构"
mkdir -p "${PROJECT_ROOT}"/{backend,logs,scripts,backup,config}
mkdir -p /var/log/ecommerce

# 设置权限
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${PROJECT_ROOT}"
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" /var/log/ecommerce

success "项目目录已创建"
log "目录结构："
tree -L 2 "${PROJECT_ROOT}" 2>/dev/null || ls -la "${PROJECT_ROOT}"

# ============================================================
# 第十二部分：开启 sysstat 数据收集
# ============================================================
section "第十二部分：开启 sysstat 数据收集"

# 检查 sysstat 配置
if [ -f /etc/default/sysstat ]; then
    ENABLED=$(grep -E "^ENABLED=" /etc/default/sysstat | cut -d'"' -f2 2>/dev/null || echo "")
    if [ "${ENABLED}" != "true" ]; then
        log "开启 sysstat 数据收集"
        sed -i 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
        systemctl restart sysstat
        systemctl enable sysstat 2>/dev/null || true
        success "sysstat 数据收集已开启"
    else
        success "sysstat 已开启，跳过"
    fi
fi

# ============================================================
# 第十三部分：验证初始化结果
# ============================================================
section "第十三部分：验证初始化结果"

info "初始化验证："
echo ""

# 验证系统更新
success "系统更新：已完成"

# 验证时区
CURRENT_TZ=$(timedatectl show --property=Timezone --value)
success "时区：${CURRENT_TZ}"

# 验证 deploy 用户
if id "${DEPLOY_USER}" &> /dev/null; then
    success "部署用户 ${DEPLOY_USER}：已创建"
else
    error "部署用户 ${DEPLOY_USER}：未创建"
fi

# 验证防火墙
if ufw status | grep -q "Status: active"; then
    success "防火墙：已启用"
else
    warn "防火墙：未启用"
fi

# 验证 SSH 配置
if grep -q "^Port ${SSH_PORT}" "${SSHD_CONFIG}"; then
    success "SSH 端口：${SSH_PORT}"
else
    warn "SSH 端口：未修改"
fi

# 验证 fail2ban
if systemctl is-active --quiet fail2ban; then
    success "fail2ban：运行中"
else
    warn "fail2ban：未运行"
fi

# 验证 ulimit
if [ -f "${LIMITS_FILE}" ]; then
    success "ulimit 配置：已创建"
fi

# 验证 sysctl
if [ -f "${SYSCTL_FILE}" ]; then
    success "sysctl 配置：已创建"
fi

# 验证项目目录
if [ -d "${PROJECT_ROOT}" ]; then
    success "项目目录：${PROJECT_ROOT} 已创建"
fi

echo ""

# ============================================================
# 总结
# ============================================================
section "初始化总结"

success "服务器初始化完成！"
echo ""
info "初始化内容："
echo "  1. 系统更新 + 安全补丁"
echo "  2. 时区设置：${TIMEZONE} + NTP 同步"
echo "  3. 基础工具安装（${#BASIC_TOOLS[@]} 个）"
echo "  4. 部署用户：${DEPLOY_USER}（sudo 免密）"
echo "  5. 防火墙：ufw 已启用（80/443/${SSH_PORT} 放行，3306/6379 拒绝）"
echo "  6. SSH 加固：端口 ${SSH_PORT}，禁 root，禁密码，仅密钥"
echo "  7. fail2ban：防暴力破解（失败 3 次封禁 1 小时）"
echo "  8. ulimit：文件描述符 65535"
echo "  9. sysctl：内核网络参数调优"
echo "  10. 项目目录：${PROJECT_ROOT}"
echo "  11. sysstat：性能数据收集已开启"
echo ""
warn "下一步操作："
echo "  1. 将本地 SSH 公钥上传到服务器："
echo "     ssh-copy-id -p ${SSH_PORT} ${DEPLOY_USER}@192.168.1.100"
echo "  2. 用新端口测试连接："
echo "     ssh -p ${SSH_PORT} ${DEPLOY_USER}@192.168.1.100"
echo "  3. 执行全栈部署："
echo "     sudo bash 03-deploy-full-stack.sh"
echo ""
log "日志文件：${LOG_FILE}"
log "SSH 配置备份：${BACKUP_FILE}"
