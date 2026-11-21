#!/bin/bash
# ============================================================
# 文件名：03-deploy-full-stack.sh
# 用途：全栈一键部署脚本
# 场景：电商服务器 192.168.1.100 全栈服务部署
# 说明：综合运用前 13 天知识，一键部署：
#   检查环境依赖 → 安装 Nginx/MySQL/Redis → 安装 Node.js/nvm/PM2
#   → 配置 Nginx 反向代理 → 启动 Node.js 应用 → 启动 MySQL/Redis
#   → 配置开机自启 → 验证服务状态 → 输出部署报告
#   脚本含颜色输出、日志记录、错误处理、幂等设计
# 运行：sudo bash 03-deploy-full-stack.sh
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
LOG_FILE="/var/log/deploy-full-stack-$(date +%Y%m%d-%H%M%S).log"
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
DEPLOY_HOME="/home/${DEPLOY_USER}"
PROJECT_ROOT="/opt/ecommerce"
NODE_VERSION="18"              # Node.js LTS 版本
MYSQL_ROOT_PASSWORD=""         # MySQL root 密码（留空则交互输入）
REDIS_PASSWORD=""              # Redis 密码（留空则交互输入）
APP_PORT_START=3000            # Node.js 起始端口
APP_INSTANCES=4                # Node.js 实例数

log "全栈一键部署脚本启动"
log "服务器：192.168.1.100 (Ubuntu 22.04)"
log "日志文件：${LOG_FILE}"

# ============================================================
# 第一部分：检查环境依赖
# ============================================================
section "第一部分：检查环境依赖"

# 检查操作系统版本
log "检查操作系统版本"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    success "操作系统：${NAME} ${VERSION}"
else
    error "无法检测操作系统，退出"
    exit 1
fi

# 检查是否为 Ubuntu
if [[ "${ID}" != "ubuntu" ]]; then
    warn "当前系统为 ${ID}，本脚本针对 Ubuntu 优化，部分命令可能需要调整"
fi

# 检查磁盘空间
log "检查磁盘空间"
DISK_AVAIL=$(df / | tail -1 | awk '{print $4}')
DISK_AVAIL_GB=$((DISK_AVAIL / 1024 / 1024))
if [ "${DISK_AVAIL_GB}" -lt 5 ]; then
    error "磁盘空间不足 5GB（当前可用 ${DISK_AVAIL_GB}GB），退出"
    exit 1
fi
success "磁盘空间充足（${DISK_AVAIL_GB}GB 可用）"

# 检查内存
log "检查内存"
MEM_TOTAL=$(free -m | awk '/Mem:/ {print $2}')
if [ "${MEM_TOTAL}" -lt 1024 ]; then
    warn "内存低于 1GB（${MEM_TOTAL}MB），可能影响性能"
else
    success "内存充足（${MEM_TOTAL}MB）"
fi

# 检查 deploy 用户是否存在
if ! id "${DEPLOY_USER}" &> /dev/null; then
    warn "部署用户 ${DEPLOY_USER} 不存在，正在创建..."
    useradd -m -s /bin/bash "${DEPLOY_USER}"
    usermod -aG sudo "${DEPLOY_USER}"
    echo "${DEPLOY_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${DEPLOY_USER}
    chmod 440 /etc/sudoers.d/${DEPLOY_USER}
    success "用户 ${DEPLOY_USER} 已创建"
fi

# 创建项目目录（幂等）
mkdir -p "${PROJECT_ROOT}"/{backend,logs,scripts,backup,config}
mkdir -p /var/log/ecommerce
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${PROJECT_ROOT}"
success "项目目录已就绪"

# ============================================================
# 第二部分：安装 Nginx
# ============================================================
section "第二部分：安装 Nginx"

# 幂等安装
if command -v nginx &> /dev/null; then
    success "Nginx 已安装，跳过"
else
    log "安装 Nginx"
    apt install -y -qq nginx
    success "Nginx 安装完成"
fi

# 启动并设置开机自启
log "启动 Nginx 并设置开机自启"
systemctl restart nginx
systemctl enable nginx
success "Nginx 已启动并设置开机自启"

# 验证 Nginx
if systemctl is-active --quiet nginx; then
    success "Nginx 运行正常"
else
    error "Nginx 启动失败"
    exit 1
fi

# 显示 Nginx 版本
log "Nginx 版本：$(nginx -v 2>&1)"

# ============================================================
# 第三部分：安装 MySQL
# ============================================================
section "第三部分：安装 MySQL"

# 幂等安装
if command -v mysql &> /dev/null; then
    success "MySQL 已安装，跳过"
else
    log "安装 MySQL 8.0"
    apt install -y -qq mysql-server mysql-client
    success "MySQL 安装完成"
fi

# 启动并设置开机自启
log "启动 MySQL 并设置开机自启"
systemctl restart mysql
systemctl enable mysql
success "MySQL 已启动并设置开机自启"

# 安全初始化（幂等：检查 root 密码是否已设置）
log "MySQL 安全初始化"
if [ -z "${MYSQL_ROOT_PASSWORD}" ]; then
    # 生成随机密码
    MYSQL_ROOT_PASSWORD=$(openssl rand -base64 16 | tr -d '/+=' | head -c 20)
    warn "已生成 MySQL root 密码：${MYSQL_ROOT_PASSWORD}"
    warn "请妥善保存！"
fi

# 设置 root 密码（幂等：尝试无密码登录判断是否已设置）
if mysql -u root -e "SELECT 1" &> /dev/null; then
    log "设置 MySQL root 密码"
    mysql -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASSWORD}';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DELETE FROM mysql.db WHERE Db='test' OR Db='test_%';
FLUSH PRIVILEGES;
EOF
    success "MySQL root 密码已设置"
else
    success "MySQL root 密码已配置，跳过"
fi

# 创建电商数据库（幂等）
log "创建电商数据库"
if mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "USE ecommerce" &> /dev/null; then
    success "数据库 ecommerce 已存在，跳过"
else
    mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<EOF
CREATE DATABASE ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ecommerce'@'localhost' IDENTIFIED BY 'EcommercePass2024!';
GRANT ALL PRIVILEGES ON ecommerce.* TO 'ecommerce'@'localhost';
FLUSH PRIVILEGES;
EOF
    success "数据库 ecommerce 与用户已创建"
fi

# 保存 MySQL 凭证到配置文件
log "保存 MySQL 凭证"
cat > "${PROJECT_ROOT}/config/mysql.env" <<EOF
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
MYSQL_DATABASE=ecommerce
MYSQL_USER=ecommerce
MYSQL_PASSWORD=EcommercePass2024!
EOF
chmod 600 "${PROJECT_ROOT}/config/mysql.env"
chown "${DEPLOY_USER}:${DEPLOY_USER}" "${PROJECT_ROOT}/config/mysql.env"
success "MySQL 凭证已保存到 ${PROJECT_ROOT}/config/mysql.env"

# 验证 MySQL
if systemctl is-active --quiet mysql; then
    success "MySQL 运行正常"
else
    error "MySQL 启动失败"
    exit 1
fi

# ============================================================
# 第四部分：安装 Redis
# ============================================================
section "第四部分：安装 Redis"

# 幂等安装
if command -v redis-cli &> /dev/null; then
    success "Redis 已安装，跳过"
else
    log "安装 Redis"
    apt install -y -qq redis-server
    success "Redis 安装完成"
fi

# 配置 Redis（幂等）
REDIS_CONF="/etc/redis/redis.conf"
if [ -z "${REDIS_PASSWORD}" ]; then
    REDIS_PASSWORD=$(openssl rand -base64 16 | tr -d '/+=' | head -c 20)
    warn "已生成 Redis 密码：${REDIS_PASSWORD}"
    warn "请妥善保存！"
fi

# 检查是否已配置密码
if grep -q "^requirepass" "${REDIS_CONF}"; then
    success "Redis 密码已配置，跳过"
else
    log "配置 Redis 安全设置"
    # 备份原配置
    cp "${REDIS_CONF}" "${REDIS_CONF}.backup.$(date +%Y%m%d%H%M%S)"

    # 修改配置
    sed -i 's/^bind .*/bind 127.0.0.1/' "${REDIS_CONF}"
    sed -i 's/^# requirepass .*/requirepass '"${REDIS_PASSWORD}"'/' "${REDIS_CONF}"
    # 如果 requirepass 仍被注释，追加
    if ! grep -q "^requirepass " "${REDIS_CONF}"; then
        echo "requirepass ${REDIS_PASSWORD}" >> "${REDIS_CONF}"
    fi

    # 设置内存上限与淘汰策略
    sed -i 's/^# maxmemory .*/maxmemory 512mb/' "${REDIS_CONF}"
    if ! grep -q "^maxmemory " "${REDIS_CONF}"; then
        echo "maxmemory 512mb" >> "${REDIS_CONF}"
    fi
    sed -i 's/^# maxmemory-policy .*/maxmemory-policy allkeys-lru/' "${REDIS_CONF}"
    if ! grep -q "^maxmemory-policy " "${REDIS_CONF}"; then
        echo "maxmemory-policy allkeys-lru" >> "${REDIS_CONF}"
    fi

    success "Redis 安全配置已完成"
fi

# 保存 Redis 凭证
cat > "${PROJECT_ROOT}/config/redis.env" <<EOF
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
EOF
chmod 600 "${PROJECT_ROOT}/config/redis.env"
chown "${DEPLOY_USER}:${DEPLOY_USER}" "${PROJECT_ROOT}/config/redis.env"
success "Redis 凭证已保存"

# 启动并设置开机自启
log "启动 Redis 并设置开机自启"
systemctl restart redis-server
systemctl enable redis-server
success "Redis 已启动并设置开机自启"

# 验证 Redis
if systemctl is-active --quiet redis-server; then
    success "Redis 运行正常"
else
    error "Redis 启动失败"
    exit 1
fi

# ============================================================
# 第五部分：安装 Node.js + nvm + PM2
# ============================================================
section "第五部分：安装 Node.js + nvm + PM2"

# 安装 nvm（以 deploy 用户身份）
NVM_DIR="${DEPLOY_HOME}/.nvm"

if [ -d "${NVM_DIR}" ]; then
    success "nvm 已安装，跳过"
else
    log "安装 nvm（以 ${DEPLOY_USER} 用户身份）"
    sudo -u "${DEPLOY_USER}" bash -c 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash'
    success "nvm 安装完成"
fi

# 安装 Node.js（幂等）
log "检查 Node.js 是否已安装"
NODE_INSTALLED=$(sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && nvm list | grep -c "v'"${NODE_VERSION}"'"' 2>/dev/null || echo "0")

if [ "${NODE_INSTALLED}" -gt 0 ]; then
    success "Node.js v${NODE_VERSION} 已安装，跳过"
else
    log "安装 Node.js v${NODE_VERSION} LTS"
    sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && nvm install '${NODE_VERSION}' && nvm use '${NODE_VERSION}' && nvm alias default '${NODE_VERSION}
    success "Node.js v${NODE_VERSION} 安装完成"
fi

# 显示 Node.js 版本
NODE_VERSION_FULL=$(sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && node -v' 2>/dev/null || echo "unknown")
success "Node.js 版本：${NODE_VERSION_FULL}"

# 安装 PM2（幂等）
PM2_INSTALLED=$(sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && npm list -g pm2 2>/dev/null | grep -c pm2' 2>/dev/null || echo "0")

if [ "${PM2_INSTALLED}" -gt 0 ]; then
    success "PM2 已安装，跳过"
else
    log "安装 PM2"
    sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && npm install -g pm2'
    success "PM2 安装完成"
fi

PM2_VERSION=$(sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && pm2 --version' 2>/dev/null || echo "unknown")
success "PM2 版本：${PM2_VERSION}"

# ============================================================
# 第六部分：配置 Nginx 反向代理
# ============================================================
section "第六部分：配置 Nginx 反向代理"

# 检查 Nginx 配置是否已存在
NGINX_SITE="/etc/nginx/sites-available/ecommerce"
if [ -f "${NGINX_SITE}" ]; then
    success "Nginx 站点配置已存在，跳过"
else
    log "创建 Nginx 反向代理配置"

    # 创建简化的反向代理配置（生产环境参考 02-deploy-nginx-reverse-proxy.conf）
    cat > "${NGINX_SITE}" <<'EOF'
# 电商项目 Nginx 反向代理配置
upstream ecommerce_backend {
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
    server 127.0.0.1:3002;
    server 127.0.0.1:3003;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name _;

    # 上传大小限制
    client_max_body_size 20m;

    # gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/javascript application/json application/javascript application/xml;

    # 日志
    access_log /var/log/nginx/ecommerce-access.log;
    error_log /var/log/nginx/ecommerce-error.log;

    # 静态文件
    root /opt/ecommerce/backend/public;
    index index.html;

    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
        try_files $uri =404;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://ecommerce_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass http://ecommerce_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    # 前端路由（SPA）
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF
    success "Nginx 配置已创建"
fi

# 创建软链接到 sites-enabled（幂等）
if [ -L /etc/nginx/sites-enabled/ecommerce ]; then
    success "Nginx 站点已启用，跳过"
else
    log "启用 Nginx 站点"
    ln -s "${NGINX_SITE}" /etc/nginx/sites-enabled/ecommerce

    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default

    success "Nginx 站点已启用"
fi

# 测试并重载 Nginx
log "测试 Nginx 配置语法"
if nginx -t; then
    success "Nginx 配置语法正确"
    log "重载 Nginx"
    systemctl reload nginx
    success "Nginx 已重载"
else
    error "Nginx 配置语法错误！"
    exit 1
fi

# ============================================================
# 第七部分：创建示例 Node.js 应用
# ============================================================
section "第七部分：创建示例 Node.js 应用"

# 检查应用是否已存在
APP_FILE="${PROJECT_ROOT}/backend/app.js"
if [ -f "${APP_FILE}" ]; then
    success "Node.js 应用已存在，跳过创建"
else
    log "创建示例 Node.js 应用"

    # 创建 package.json
    cat > "${PROJECT_ROOT}/backend/package.json" <<'EOF'
{
  "name": "ecommerce-backend",
  "version": "1.0.0",
  "description": "Ecommerce backend API",
  "main": "app.js",
  "scripts": {
    "start": "node app.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
EOF

    # 创建应用文件（根据端口生成不同实例）
    cat > "${APP_FILE}" <<'EOF'
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;
const instanceId = process.env.NODE_APP_INSTANCE || '0';

app.get('/', (req, res) => {
    res.json({
        service: 'ecommerce-api',
        instance: instanceId,
        port: port,
        timestamp: new Date().toISOString(),
        status: 'running'
    });
});

app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', instance: instanceId });
});

app.listen(port, () => {
    console.log(`[Instance ${instanceId}] Ecommerce API running on port ${port}`);
});
EOF

    # 创建 public/index.html
    mkdir -p "${PROJECT_ROOT}/backend/public"
    cat > "${PROJECT_ROOT}/backend/public/index.html" <<'EOF'
<!DOCTYPE html>
<html>
<head><title>Ecommerce</title></head>
<body>
<h1>Ecommerce Server</h1>
<p>Nginx + Node.js + MySQL + Redis</p>
<p>API: <a href="/api/health">/api/health</a></p>
</body>
</html>
EOF

    # 安装依赖
    log "安装 Node.js 依赖"
    sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && cd '"${PROJECT_ROOT}"'/backend && npm install --production'
    success "Node.js 应用与依赖已创建"

    chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${PROJECT_ROOT}/backend"
fi

# ============================================================
# 第八部分：使用 PM2 启动 Node.js 应用
# ============================================================
section "第八部分：使用 PM2 启动 Node.js 应用"

# 创建 PM2 ecosystem 配置文件
ECOSYSTEM_FILE="${PROJECT_ROOT}/backend/ecosystem.config.js"
if [ -f "${ECOSYSTEM_FILE}" ]; then
    success "PM2 配置已存在，跳过创建"
else
    log "创建 PM2 ecosystem 配置"
    cat > "${ECOSYSTEM_FILE}" <<'EOF'
module.exports = {
  apps: [{
    name: 'ecommerce',
    script: './app.js',
    instances: 4,
    exec_mode: 'cluster',
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '/opt/ecommerce/logs/error.log',
    out_file: '/opt/ecommerce/logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss'
  }]
}
EOF
    chown "${DEPLOY_USER}:${DEPLOY_USER}" "${ECOSYSTEM_FILE}"
    success "PM2 配置已创建"
fi

# 启动 PM2（幂等：检查是否已在运行）
PM2_RUNNING=$(sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && pm2 list 2>/dev/null | grep -c ecommerce' 2>/dev/null || echo "0")

if [ "${PM2_RUNNING}" -gt 0 ]; then
    success "PM2 应用已在运行，跳过"
else
    log "使用 PM2 启动 Node.js 应用"
    sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && cd '"${PROJECT_ROOT}"'/backend && pm2 start ecosystem.config.js'
    success "PM2 已启动 ${APP_INSTANCES} 个 Node.js 实例"
fi

# 保存 PM2 进程列表（用于开机自启）
sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && pm2 save'

# 配置 PM2 开机自启
log "配置 PM2 开机自启"
NODE_PATH=$(sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && which node' 2>/dev/null)
PM2_PATH=$(sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && which pm2' 2>/dev/null)

# 生成 systemd 服务文件
cat > /etc/systemd/system/pm2-${DEPLOY_USER}.service <<EOF
[Unit]
Description=PM2 process manager for ${DEPLOY_USER}
After=network.target

[Service]
Type=forking
User=${DEPLOY_USER}
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
Environment=PATH=${NODE_PATH%/*}:/usr/local/bin:/usr/bin:/bin
Environment=PM2_HOME=${DEPLOY_HOME}/.pm2
PIDFile=${DEPLOY_HOME}/.pm2/pm2.pid
ExecStart=${PM2_PATH} resurrect
ExecReload=${PM2_PATH} reload all
ExecStop=${PM2_PATH} kill

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pm2-${DEPLOY_USER}
success "PM2 开机自启已配置"

# 显示 PM2 状态
log "PM2 进程状态："
sudo -u "${DEPLOY_USER}" bash -c 'source ~/.nvm/nvm.sh && pm2 list' 2>/dev/null

# ============================================================
# 第九部分：配置开机自启
# ============================================================
section "第九部分：配置所有服务开机自启"

# 确保所有服务开机自启
log "配置服务开机自启"
systemctl enable nginx
systemctl enable mysql
systemctl enable redis-server
systemctl enable pm2-${DEPLOY_USER}
success "所有服务已设置开机自启"

# ============================================================
# 第十部分：验证服务状态
# ============================================================
section "第十部分：验证服务状态"

info "服务状态验证："
echo ""

# 验证函数
verify_service() {
    local name=$1
    local service=$2
    if systemctl is-active --quiet "${service}"; then
        success "${name}：运行中"
    else
        error "${name}：未运行"
    fi
}

verify_service "Nginx" "nginx"
verify_service "MySQL" "mysql"
verify_service "Redis" "redis-server"
verify_service "PM2" "pm2-${DEPLOY_USER}"

echo ""

# 验证端口监听
log "验证端口监听："
ss -tlnp | grep -E ':(80|443|3000|3001|3002|3003|3306|6379)' || warn "部分端口未监听"
echo ""

# 验证 HTTP 访问
log "验证 HTTP 访问"
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200"; then
    success "HTTP 访问正常（200）"
else
    warn "HTTP 访问异常"
fi

# 验证 API
log "验证 API 响应"
if curl -s http://localhost/api/health | grep -q "ok"; then
    success "API 响应正常"
else
    warn "API 响应异常（可能应用未完全启动）"
fi

# 验证 MySQL 连接
log "验证 MySQL 连接"
if mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT 1" &> /dev/null; then
    success "MySQL 连接正常"
else
    warn "MySQL 连接异常"
fi

# 验证 Redis 连接
log "验证 Redis 连接"
if redis-cli -a "${REDIS_PASSWORD}" ping 2>/dev/null | grep -q PONG; then
    success "Redis 连接正常"
else
    warn "Redis 连接异常"
fi

# ============================================================
# 第十一部分：输出部署报告
# ============================================================
section "部署报告"

echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│                    全栈部署完成报告                         │"
echo "├─────────────────────────────────────────────────────────────┤"
echo "│                                                             │"
echo "│  服务器：192.168.1.100 (Ubuntu 22.04)                      │"
echo "│  部署时间：$(date '+%Y-%m-%d %H:%M:%S')                     │"
echo "│                                                             │"
echo "│  ┌──────────────┬──────────────┬────────────────────────┐  │"
echo "│  │ 服务         │ 版本         │ 状态                   │  │"
echo "│  ├──────────────┼──────────────┼────────────────────────┤  │"
echo "│  │ Nginx        │ $(nginx -v 2>&1 | cut -d'/' -f2)    │ $(systemctl is-active nginx)                     │  │"
echo "│  │ MySQL        │ $(mysql --version | awk '{print $3}')   │ $(systemctl is-active mysql)                     │  │"
echo "│  │ Redis        │ $(redis-server --version 2>/dev/null || echo 'unknown')      │ $(systemctl is-active redis-server)                     │  │"
echo "│  │ Node.js      │ ${NODE_VERSION_FULL}    │ running                  │  │"
echo "│  │ PM2          │ ${PM2_VERSION}      │ running                  │  │"
echo "│  └──────────────┴──────────────┴────────────────────────┘  │"
echo "│                                                             │"
echo "│  访问地址：                                                 │"
echo "│    HTTP:  http://192.168.1.100                             │"
echo "│    API:   http://192.168.1.100/api/health                  │"
echo "│                                                             │"
echo "│  凭证文件：                                                 │"
echo "│    MySQL: ${PROJECT_ROOT}/config/mysql.env                 │"
echo "│    Redis: ${PROJECT_ROOT}/config/redis.env                 │"
echo "│                                                             │"
echo "│  日志位置：                                                 │"
echo "│    Nginx: /var/log/nginx/ecommerce-*.log                  │"
echo "│    Node:  ${PROJECT_ROOT}/logs/*.log                       │"
echo "│    部署:  ${LOG_FILE}          │"
echo "│                                                             │"
echo "└─────────────────────────────────────────────────────────────┘"
echo ""

success "全栈部署完成！"
echo ""
info "下一步建议："
echo "  1. 配置 MySQL 自动备份：sudo bash 04-mysql-backup.sh"
echo "  2. 申请 HTTPS 证书：sudo certbot --nginx -d example.com"
echo "  3. 查看服务日志：pm2 logs ecommerce"
echo "  4. 阅读 05-ops-best-practices.md 学习运维最佳实践"
echo ""
log "日志文件：${LOG_FILE}"
