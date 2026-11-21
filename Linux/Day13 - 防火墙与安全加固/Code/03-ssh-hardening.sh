#!/bin/bash
# ============================================================
# 文件名：03-ssh-hardening.sh
# 用途：SSH 安全加固脚本
# 场景：电商服务器 192.168.1.100 SSH 安全加固
# 说明：修改 sshd_config（改端口/禁root/禁密码/限用户/超时设置）
#       安装配置 fail2ban 防暴力破解
#       执行 SSH 安全检查
# 运行：sudo bash 03-ssh-hardening.sh
# 权限：需要 root/sudo 权限
# 警告：修改 SSH 配置有断连风险，请保持当前会话，新开终端测试！
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
LOG_FILE="/var/log/ssh-hardening-$(date +%Y%m%d-%H%M%S).log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# ---------- 权限检查 ----------
if [ "${EUID}" -ne 0 ]; then
    error "此脚本需要 root 权限执行，请使用 sudo"
    echo "  sudo bash $0"
    exit 1
fi

log "SSH 安全加固脚本启动"
log "服务器：192.168.1.100 (Ubuntu 22.04)"

# ---------- 配置变量（可按需修改） ----------
SSH_NEW_PORT=2222              # 新 SSH 端口
SSH_ALLOW_USERS="deploy"       # 允许登录的用户
MAX_AUTH_TRIES=3               # 最大认证尝试次数
LOGIN_GRACE_TIME=30            # 登录宽限时间（秒）
CLIENT_ALIVE_INTERVAL=300      # 客户端存活检查间隔（秒）
CLIENT_ALIVE_COUNT_MAX=2       # 最大检查次数
FAIL2BAN_BANTIME=3600          # fail2ban 封禁时长（秒）
FAIL2BAN_FINDTIME=600          # fail2ban 检测窗口（秒）
FAIL2BAN_MAXRETRY=3            # fail2ban 最大失败次数

# ============================================================
# 第一部分：备份原配置
# ============================================================
section "第一部分：备份原配置"

SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP_FILE="${SSHD_CONFIG}.backup.$(date +%Y%m%d%H%M%S)"

# 备份 sshd_config
if [ -f "${SSHD_CONFIG}" ]; then
    log "备份 ${SSHD_CONFIG} → ${BACKUP_FILE}"
    cp "${SSHD_CONFIG}" "${BACKUP_FILE}"
    success "配置已备份到 ${BACKUP_FILE}"
else
    error "未找到 ${SSHD_CONFIG}，退出"
    exit 1
fi
echo ""

warn "重要提醒："
echo "  1. 修改 SSH 配置有断连风险！"
echo "  2. 请保持当前 SSH 会话不要关闭"
echo "  3. 新开一个终端用新配置测试连接"
echo "  4. 测试成功后再关闭旧会话"
echo ""

# ============================================================
# 第二部分：修改 sshd_config
# ============================================================
section "第二部分：修改 sshd_config 安全配置"

info "将执行以下加固："
echo "  1. 修改 SSH 端口：22 → ${SSH_NEW_PORT}"
echo "  2. 禁止 root 直接登录"
echo "  3. 禁用密码认证（仅密钥）"
echo "  4. 启用密钥认证"
echo "  5. 限制最大认证尝试：${MAX_AUTH_TRIES} 次"
echo "  6. 设置登录超时：${CLIENT_ALIVE_INTERVAL}×${CLIENT_ALIVE_COUNT_MAX}=$((${CLIENT_ALIVE_INTERVAL}*${CLIENT_ALIVE_COUNT_MAX})) 秒"
echo "  7. 限制用户白名单：${SSH_ALLOW_USERS}"
echo ""

# 询问是否继续
read -r -p "确认执行 SSH 加固？[y/N] " response
if [[ ! "${response}" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    info "已取消，退出脚本"
    exit 0
fi
echo ""

# 修改 SSH 端口
log "修改 SSH 端口为 ${SSH_NEW_PORT}"
# 先注释掉原有 Port 行，再添加新端口
sed -i 's/^Port/#Port/' "${SSHD_CONFIG}"
echo "Port ${SSH_NEW_PORT}" >> "${SSHD_CONFIG}"
success "SSH 端口已修改为 ${SSH_NEW_PORT}"

# 禁止 root 直接登录
log "禁止 root 直接登录（PermitRootLogin no）"
sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' "${SSHD_CONFIG}"
# 如果不存在则追加
if ! grep -q "^PermitRootLogin no" "${SSHD_CONFIG}"; then
    echo "PermitRootLogin no" >> "${SSHD_CONFIG}"
fi
success "已禁止 root 直接登录"

# 禁用密码认证（仅密钥）
log "禁用密码认证（PasswordAuthentication no）"
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' "${SSHD_CONFIG}"
if ! grep -q "^PasswordAuthentication no" "${SSHD_CONFIG}"; then
    echo "PasswordAuthentication no" >> "${SSHD_CONFIG}"
fi
success "已禁用密码认证"

# 启用密钥认证
log "启用密钥认证（PubkeyAuthentication yes）"
sed -i 's/^PubkeyAuthentication.*/PubkeyAuthentication yes/' "${SSHD_CONFIG}"
if ! grep -q "^PubkeyAuthentication yes" "${SSHD_CONFIG}"; then
    echo "PubkeyAuthentication yes" >> "${SSHD_CONFIG}"
fi
success "已启用密钥认证"

# 限制最大认证尝试次数
log "设置最大认证尝试次数 ${MAX_AUTH_TRIES}"
sed -i 's/^MaxAuthTries.*/MaxAuthTries '"${MAX_AUTH_TRIES}"'/' "${SSHD_CONFIG}"
if ! grep -q "^MaxAuthTries ${MAX_AUTH_TRIES}" "${SSHD_CONFIG}"; then
    echo "MaxAuthTries ${MAX_AUTH_TRIES}" >> "${SSHD_CONFIG}"
fi
success "最大认证尝试次数设为 ${MAX_AUTH_TRIES}"

# 登录宽限时间
log "设置登录宽限时间 ${LOGIN_GRACE_TIME} 秒"
sed -i 's/^LoginGraceTime.*/LoginGraceTime '"${LOGIN_GRACE_TIME}"'/' "${SSHD_CONFIG}"
if ! grep -q "^LoginGraceTime ${LOGIN_GRACE_TIME}" "${SSHD_CONFIG}"; then
    echo "LoginGraceTime ${LOGIN_GRACE_TIME}" >> "${SSHD_CONFIG}"
fi
success "登录宽限时间设为 ${LOGIN_GRACE_TIME} 秒"

# 客户端存活检查
log "设置客户端超时断开（${CLIENT_ALIVE_INTERVAL}×${CLIENT_ALIVE_COUNT_MAX}）"
sed -i 's/^ClientAliveInterval.*/ClientAliveInterval '"${CLIENT_ALIVE_INTERVAL}"'/' "${SSHD_CONFIG}"
if ! grep -q "^ClientAliveInterval ${CLIENT_ALIVE_INTERVAL}" "${SSHD_CONFIG}"; then
    echo "ClientAliveInterval ${CLIENT_ALIVE_INTERVAL}" >> "${SSHD_CONFIG}"
fi
sed -i 's/^ClientAliveCountMax.*/ClientAliveCountMax '"${CLIENT_ALIVE_COUNT_MAX}"'/' "${SSHD_CONFIG}"
if ! grep -q "^ClientAliveCountMax ${CLIENT_ALIVE_COUNT_MAX}" "${SSHD_CONFIG}"; then
    echo "ClientAliveCountMax ${CLIENT_ALIVE_COUNT_MAX}" >> "${SSHD_CONFIG}"
fi
success "超时断开设为 $((${CLIENT_ALIVE_INTERVAL}*${CLIENT_ALIVE_COUNT_MAX})) 秒"

# 用户白名单
log "设置用户白名单：${SSH_ALLOW_USERS}"
sed -i 's/^AllowUsers.*/AllowUsers '"${SSH_ALLOW_USERS}"'/' "${SSHD_CONFIG}"
if ! grep -q "^AllowUsers ${SSH_ALLOW_USERS}" "${SSHD_CONFIG}"; then
    echo "AllowUsers ${SSH_ALLOW_USERS}" >> "${SSHD_CONFIG}"
fi
success "用户白名单设为 ${SSH_ALLOW_USERS}"

# 禁止空密码
log "禁止空密码（PermitEmptyPasswords no）"
sed -i 's/^PermitEmptyPasswords.*/PermitEmptyPasswords no/' "${SSHD_CONFIG}"
if ! grep -q "^PermitEmptyPasswords no" "${SSHD_CONFIG}"; then
    echo "PermitEmptyPasswords no" >> "${SSHD_CONFIG}"
fi
success "已禁止空密码"

# 禁用 X11 转发
log "禁用 X11 转发（X11Forwarding no）"
sed -i 's/^X11Forwarding.*/X11Forwarding no/' "${SSHD_CONFIG}"
if ! grep -q "^X11Forwarding no" "${SSHD_CONFIG}"; then
    echo "X11Forwarding no" >> "${SSHD_CONFIG}"
fi
success "已禁用 X11 转发"
echo ""

# ============================================================
# 第三部分：验证配置语法
# ============================================================
section "第三部分：验证配置语法"

# 用 sshd -t 检查配置语法
log "检查 sshd 配置语法"
if sshd -t; then
    success "sshd 配置语法正确"
else
    error "sshd 配置语法错误！请检查 ${SSHD_CONFIG}"
    warn "可用备份恢复：cp ${BACKUP_FILE} ${SSHD_CONFIG}"
    exit 1
fi
echo ""

# 显示加固后的关键配置
log "加固后的关键配置："
echo "  ┌──────────────────────────────┬─────────────────────┐"
echo "  │ 配置项                       │ 值                  │"
echo "  ├──────────────────────────────┼─────────────────────┤"
echo "  │ Port                         │ ${SSH_NEW_PORT}                │"
echo "  │ PermitRootLogin              │ no                  │"
echo "  │ PasswordAuthentication       │ no                  │"
echo "  │ PubkeyAuthentication         │ yes                 │"
echo "  │ MaxAuthTries                 │ ${MAX_AUTH_TRIES}                   │"
echo "  │ LoginGraceTime               │ ${LOGIN_GRACE_TIME}                  │"
echo "  │ ClientAliveInterval          │ ${CLIENT_ALIVE_INTERVAL}                 │"
echo "  │ ClientAliveCountMax          │ ${CLIENT_ALIVE_COUNT_MAX}                   │"
echo "  │ AllowUsers                   │ ${SSH_ALLOW_USERS}            │"
echo "  │ PermitEmptyPasswords         │ no                  │"
echo "  │ X11Forwarding                │ no                  │"
echo "  └──────────────────────────────┴─────────────────────┘"
echo ""

# ============================================================
# 第四部分：防火墙放行新端口
# ============================================================
section "第四部分：防火墙放行新端口"

# 检查 ufw 是否启用
if command -v ufw &> /dev/null && ufw status | grep -q "active"; then
    log "检测到 ufw 已启用，放行新 SSH 端口 ${SSH_NEW_PORT}"
    ufw allow ${SSH_NEW_PORT}/tcp
    success "已放行端口 ${SSH_NEW_PORT}/tcp"
    warn "旧端口 22 的规则暂不删除，确认新端口可用后再删"
elif command -v firewall-cmd &> /dev/null; then
    log "检测到 firewalld，放行新 SSH 端口 ${SSH_NEW_PORT}"
    firewall-cmd --add-port=${SSH_NEW_PORT}/tcp --permanent
    firewall-cmd --reload
    success "已放行端口 ${SSH_NEW_PORT}/tcp"
else
    warn "未检测到防火墙，请手动放行端口 ${SSH_NEW_PORT}"
fi
echo ""

# ============================================================
# 第五部分：重启 sshd 服务
# ============================================================
section "第五部分：重启 sshd 服务"

log "重启 sshd 服务"
systemctl restart sshd
success "sshd 已重启"
echo ""

warn "重要！请按以下步骤验证："
echo "  1. 【不要关闭当前会话】"
echo "  2. 新开一个终端，用新端口连接测试："
echo "     ssh -p ${SSH_NEW_PORT} ${SSH_ALLOW_USERS}@192.168.1.100"
echo "  3. 测试密码登录应被拒绝（用 -o PreferredAuthentications=password）"
echo "  4. 测试密钥登录应成功"
echo "  5. 确认无误后，再关闭旧会话"
echo ""
echo "  如果无法连接，恢复配置："
echo "     sudo cp ${BACKUP_FILE} ${SSHD_CONFIG}"
echo "     sudo systemctl restart sshd"
echo ""

# ============================================================
# 第六部分：安装配置 fail2ban
# ============================================================
section "第六部分：安装配置 fail2ban"

# 安装 fail2ban
if ! command -v fail2ban-client &> /dev/null; then
    log "安装 fail2ban"
    apt update && apt install -y fail2ban
fi
success "fail2ban 已安装"
echo ""

# 创建 jail.local 配置（不直接修改 jail.conf）
log "创建 fail2ban 配置 /etc/fail2ban/jail.local"
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
# 封禁时长（秒）
bantime = ${FAIL2BAN_BANTIME}

# 检测时间窗口（秒）
findtime = ${FAIL2BAN_FINDTIME}

# 最大失败次数
maxretry = ${FAIL2BAN_MAXRETRY}

# 封禁动作（Ubuntu 使用 ufw）
banaction = ufw

# 白名单 IP（不封禁本地和内网）
ignoreip = 127.0.0.1/8 ::1 192.168.1.0/24

[sshd]
# 启用 SSH 防护
enabled = true
# SSH 端口（与 sshd_config 一致）
port = ${SSH_NEW_PORT}
# 日志文件路径
logpath = /var/log/auth.log
# 最大失败次数
maxretry = ${FAIL2BAN_MAXRETRY}
EOF

success "fail2ban 配置已创建"
echo ""

info "fail2ban 配置参数："
echo "  ┌──────────────┬──────────────┬──────────────────────────────┐"
echo "  │ 参数         │ 值           │ 说明                         │"
echo "  ├──────────────┼──────────────┼──────────────────────────────┤"
echo "  │ bantime      │ ${FAIL2BAN_BANTIME}s        │ 封禁时长（1 小时）           │"
echo "  │ findtime     │ ${FAIL2BAN_FINDTIME}s        │ 检测窗口（10 分钟）          │"
echo "  │ maxretry     │ ${FAIL2BAN_MAXRETRY}            │ 最大失败次数                 │"
echo "  │ banaction    │ ufw          │ 调用 ufw 封禁                │"
echo "  │ ignoreip     │ 内网+本地    │ 白名单                       │"
echo "  └──────────────┴──────────────┴──────────────────────────────┘"
echo ""

# 重启 fail2ban
log "重启 fail2ban"
systemctl restart fail2ban
systemctl enable fail2ban
success "fail2ban 已启动并设置开机自启"
echo ""

# 查看 fail2ban 状态
log "查看 fail2ban 整体状态"
fail2ban-client status
echo ""

log "查看 sshd 防护状态"
fail2ban-client status sshd
echo ""

info "fail2ban 管理命令："
echo "  fail2ban-client status              → 查看整体状态"
echo "  fail2ban-client status sshd         → 查看 SSH 防护详情"
echo "  fail2ban-client set sshd banip IP   → 手动封禁 IP"
echo "  fail2ban-client set sshd unbanip IP → 手动解封 IP"
echo "  systemctl restart fail2ban          → 重启（改配置后）"

# ============================================================
# 第七部分：SSH 安全检查清单
# ============================================================
section "第七部分：SSH 安全检查清单"

info "SSH 安全检查清单："
echo ""
echo "  ┌──┬──────────────────────────────┬──────────────────────────┐"
echo "  │✓ │ 检查项                       │ 状态                     │"
echo "  ├──┼──────────────────────────────┼──────────────────────────┤"

# 检查每项配置
check_item() {
    local name=$1
    local pattern=$2
    local expected=$3
    if grep -q "^${pattern}" "${SSHD_CONFIG}"; then
        echo "  │✓ │ ${name}$(printf '%*s' $((28-${#name})) '') │ 已配置$(printf '%*s' $((18-${#expected})) '') │"
    else
        echo "  │✗ │ ${name}$(printf '%*s' $((28-${#name})) '') │ 未配置$(printf '%*s' $((18-${#expected})) '') │"
    fi
}

check_item "修改默认端口" "Port ${SSH_NEW_PORT}" "Port ${SSH_NEW_PORT}"
check_item "禁止 root 登录" "PermitRootLogin no" "no"
check_item "禁用密码认证" "PasswordAuthentication no" "no"
check_item "启用密钥认证" "PubkeyAuthentication yes" "yes"
check_item "最大认证尝试" "MaxAuthTries ${MAX_AUTH_TRIES}" "${MAX_AUTH_TRIES}"
check_item "用户白名单" "AllowUsers ${SSH_ALLOW_USERS}" "${SSH_ALLOW_USERS}"
check_item "禁止空密码" "PermitEmptyPasswords no" "no"
check_item "禁用 X11 转发" "X11Forwarding no" "no"
check_item "超时断开" "ClientAliveInterval" "${CLIENT_ALIVE_INTERVAL}s"
echo "  └──┴──────────────────────────────┴──────────────────────────┘"
echo ""

# 检查 fail2ban
if systemctl is-active --quiet fail2ban; then
    success "fail2ban 已运行"
else
    warn "fail2ban 未运行"
fi

# 检查防火墙
if command -v ufw &> /dev/null && ufw status | grep -q "active"; then
    success "ufw 防火墙已启用"
elif command -v firewall-cmd &> /dev/null && firewall-cmd --state 2>/dev/null | grep -q "running"; then
    success "firewalld 防火墙已启用"
else
    warn "防火墙未启用"
fi
echo ""

# ============================================================
# 第八部分：验证 SSH 密钥配置
# ============================================================
section "第八部分：验证 SSH 密钥配置"

# 检查 deploy 用户的密钥
DEPLOY_HOME=$(getent passwd ${SSH_ALLOW_USERS} 2>/dev/null | cut -d: -f6 || echo "")
if [ -n "${DEPLOY_HOME}" ]; then
    if [ -d "${DEPLOY_HOME}/.ssh" ]; then
        if [ -f "${DEPLOY_HOME}/.ssh/authorized_keys" ]; then
            KEY_COUNT=$(wc -l < "${DEPLOY_HOME}/.ssh/authorized_keys")
            success "${SSH_ALLOW_USERS} 用户已配置 ${KEY_COUNT} 个公钥"
        else
            warn "${SSH_ALLOW_USERS} 用户未配置 authorized_keys，禁用密码后将无法登录！"
            warn "请立即配置密钥："
            echo "    # 在本地机器生成密钥"
            echo "    ssh-keygen -t ed25519 -C 'deploy@ecommerce'"
            echo "    # 上传公钥到服务器"
            echo "    ssh-copy-id -p ${SSH_NEW_PORT} ${SSH_ALLOW_USERS}@192.168.1.100"
        fi
    else
        warn "${SSH_ALLOW_USERS} 用户无 .ssh 目录"
    fi
else
    warn "用户 ${SSH_ALLOW_USERS} 不存在，请先创建："
    echo "    useradd -m -s /bin/bash ${SSH_ALLOW_USERS}"
    echo "    passwd ${SSH_ALLOW_USERS}"
    echo "    usermod -aG sudo ${SSH_ALLOW_USERS}"
fi
echo ""

# ============================================================
# 第九部分：总结
# ============================================================
section "第九部分：加固总结"

success "SSH 安全加固完成！"
echo ""
info "加固内容："
echo "  1. SSH 端口：22 → ${SSH_NEW_PORT}"
echo "  2. 禁止 root 登录"
echo "  3. 禁用密码认证，仅密钥"
echo "  4. 限制用户：${SSH_ALLOW_USERS}"
echo "  5. 最大认证尝试：${MAX_AUTH_TRIES} 次"
echo "  6. 超时断开：$((${CLIENT_ALIVE_INTERVAL}*${CLIENT_ALIVE_COUNT_MAX})) 秒无操作"
echo "  7. fail2ban 防暴力破解（失败 ${FAIL2BAN_MAXRETRY} 次封禁 $((${FAIL2BAN_BANTIME}/60)) 分钟）"
echo ""
warn "立即验证（新终端）："
echo "  ssh -p ${SSH_NEW_PORT} ${SSH_ALLOW_USERS}@192.168.1.100"
echo ""
log "日志文件：${LOG_FILE}"
log "配置备份：${BACKUP_FILE}"
echo ""
info "下一步建议："
echo "  1. 阅读 04-security-checklist.md 学习完整安全检查"
echo "  2. 确认新端口可连接后，删除防火墙的 22 端口规则"
echo "  3. 定期检查 fail2ban 状态：fail2ban-client status sshd"
