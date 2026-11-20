#!/bin/bash
# ============================================================
# 文件名：02-deploy-nginx.sh
# 用途：部署 Nginx，含安装、配置文件目录结构、虚拟主机、
#       反向代理、负载均衡配置示例
# 适用：Ubuntu 22.04 LTS
# 场景：电商项目 Nginx 部署（前端静态 + 后端 API 反代）
# 注意：含 sudo 命令，需具备 sudo 权限
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day08 - 02 Nginx 部署实战"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"
echo "提示：本脚本含 sudo 命令，请以具备 sudo 权限的用户执行"
echo ""

# ---------- 1. 安装 Nginx ----------

echo -e "\n[1] 安装 Nginx"
echo "命令：sudo apt install -y nginx"
if ! command -v nginx >/dev/null 2>&1; then
    sudo apt install -y nginx 2>&1 | tail -n 5
else
    echo "nginx 已安装：$(nginx -v 2>&1)"
fi

echo -e "\n[2] 验证 Nginx 版本"
nginx -v 2>&1

# ---------- 2. Nginx 配置文件目录结构 ----------

echo -e "\n[3] Nginx 配置文件目录结构（Ubuntu）"
echo "命令：ls -l /etc/nginx/"
ls -l /etc/nginx/

echo -e "\n[4] 配置文件说明"
cat <<'EOF'
/etc/nginx/nginx.conf              ← 主配置文件（全局）
/etc/nginx/sites-available/        ← 可用站点配置（Ubuntu 风格）
/etc/nginx/sites-enabled/          ← 已启用站点（软链接到 available）
/etc/nginx/conf.d/                 ← 额外配置（CentOS 风格，Ubuntu 也支持）
/etc/nginx/snippets/               ← 可复用的配置片段
/etc/nginx/mime.types              ← MIME 类型映射
/var/www/html/                     ← 默认网站根目录
/var/log/nginx/access.log          ← 访问日志
/var/log/nginx/error.log           ← 错误日志
/usr/sbin/nginx                    ← 可执行文件
EOF

echo -e "\n[5] 查看主配置文件结构"
echo "命令：cat /etc/nginx/nginx.conf | grep -v '^#' | grep -v '^$' | head -n 30"
cat /etc/nginx/nginx.conf | grep -v '^#' | grep -v '^$' | head -n 30

# ---------- 3. systemctl 管理 Nginx ----------

echo -e "\n[6] systemctl 管理 Nginx"
echo "命令：sudo systemctl status nginx --no-pager"
sudo systemctl status nginx --no-pager 2>&1 | head -n 15

echo -e "\n[7] systemctl 常用管理命令"
cat <<'EOF'
sudo systemctl start nginx             # 启动
sudo systemctl stop nginx              # 停止
sudo systemctl restart nginx           # 重启（中断服务）
sudo systemctl reload nginx            # 重载配置（不中断，推荐）
sudo systemctl enable nginx            # 开机自启
sudo systemctl enable --now nginx      # 启动并开机自启
sudo systemctl disable nginx           # 禁用开机自启
sudo systemctl is-active nginx         # 是否运行
sudo systemctl is-enabled nginx        # 是否开机自启
EOF

echo -e "\n[8] nginx 命令行工具"
cat <<'EOF'
nginx -t                # 测试配置语法（重要！修改后必测）
nginx -T                # 打印完整配置（含 include 的所有文件）
nginx -v                # 查看版本
nginx -V                # 查看版本与编译选项
nginx -s reload         # 重新加载配置（等同 systemctl reload）
nginx -s stop           # 快速停止
nginx -s quit           # 优雅停止（处理完当前请求）
nginx -s reopen         # 重新打开日志文件（日志切割用）
EOF

echo -e "\n[9] 测试配置语法（重要！）"
echo "命令：sudo nginx -t"
sudo nginx -t

# ---------- 4. 默认站点查看 ----------

echo -e "\n[10] 默认站点配置"
echo "命令：cat /etc/nginx/sites-enabled/default | grep -v '^#' | grep -v '^$' | head -n 20"
cat /etc/nginx/sites-enabled/default 2>/dev/null | grep -v '^#' | grep -v '^$' | head -n 20 || echo "（无默认站点配置）"

echo -e "\n[11] 测试默认站点"
echo "命令：curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/"
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/ 2>/dev/null || echo "（Nginx 未启动或被防火墙拦截）"

# ---------- 5. 虚拟主机配置 ----------

echo -e "\n[12] 虚拟主机配置示例（多个域名共用 80 端口）"
cat <<'EOF'
# /etc/nginx/sites-available/ecommerce-frontend
# 电商前端站点
server {
    listen 80;
    server_name www.example.com;

    root /opt/ecommerce/frontend/dist;
    index index.html;

    # SPA 单页应用路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # gzip 压缩
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1000;
}

# 后台管理站点
server {
    listen 80;
    server_name admin.example.com;

    root /opt/ecommerce/admin/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

echo -e "\n[13] 启用虚拟主机"
cat <<'EOF'
# 1. 创建配置文件
sudo vim /etc/nginx/sites-available/ecommerce-frontend
# 粘贴上面的配置

# 2. 创建软链接启用
sudo ln -s /etc/nginx/sites-available/ecommerce-frontend /etc/nginx/sites-enabled/

# 3. 测试配置
sudo nginx -t

# 4. 重载
sudo systemctl reload nginx
EOF

# ---------- 6. 反向代理配置 ----------

echo -e "\n[14] 反向代理配置示例（前端 + 后端 API）"
cat <<'EOF'
# /etc/nginx/sites-available/ecommerce-api
server {
    listen 80;
    server_name api.example.com;

    # 客户端上传文件大小限制
    client_max_body_size 20M;

    # API 反向代理到 Node.js 后端
    location /api/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件（图片/上传文件）
    location /static/ {
        alias /opt/ecommerce/uploads/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:3000/api/health;
        access_log off;
    }
}
EOF

echo -e "\n[15] 反向代理常用 proxy_set_header 说明"
cat <<'EOF'
proxy_set_header Host $host;
  # 把客户端请求的 Host 头传给后端，后端能识别访问的域名

proxy_set_header X-Real-IP $remote_addr;
  # 把客户端真实 IP 传给后端（不加的话后端只能看到 Nginx 的 IP）

proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  # 代理链路 IP 列表，用于多层代理场景

proxy_set_header X-Forwarded-Proto $scheme;
  # 告诉后端客户端用的是 http 还是 https

# 后端获取真实 IP：
# Express: req.headers['x-real-ip']
# NestJS: @Headers('x-real-ip') ip
EOF

# ---------- 7. 负载均衡配置 ----------

echo -e "\n[16] 负载均衡配置示例"
cat <<'EOF'
# /etc/nginx/conf.d/upstream.conf
upstream ecommerce_backend {
    # 轮询（默认）
    # server 127.0.0.1:3000;
    # server 127.0.0.1:3001;

    # 加权轮询（性能强的机器权重高）
    server 127.0.0.1:3000 weight=3;
    server 127.0.0.1:3001 weight=2;
    server 127.0.0.1:3002 weight=1;

    # ip_hash（同一 IP 固定到同一后端，解决 session 问题）
    # ip_hash;

    # least_conn（最少连接数优先）
    # least_conn;

    # 健康检查参数
    # server 127.0.0.1:3003 max_fails=3 fail_timeout=30s;

    # 长连接复用（减少 TCP 握手开销）
    keepalive 32;
}

# /etc/nginx/sites-available/ecommerce-lb
server {
    listen 80;
    server_name api.example.com;

    location /api/ {
        proxy_pass http://ecommerce_backend;
        proxy_http_version 1.1;

        # 配合 upstream keepalive
        proxy_set_header Connection "";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

echo -e "\n[17] 负载均衡策略对比"
cat <<'EOF'
┌──────────────┬──────────────────────────────────────────────┐
│ 策略         │ 说明                                         │
├──────────────┼──────────────────────────────────────────────┤
│ 轮询（默认） │ 按顺序逐一分配                              │
│ weight       │ 按权重分配（性能强的权重高）                │
│ ip_hash      │ 同一 IP 固定到同一后端（解决 session 问题） │
│ least_conn   │ 分配给连接数最少的后端                      │
│ hash $key    │ 一致性哈希（如 hash $request_uri 缓存友好）│
└──────────────┴──────────────────────────────────────────────┘
EOF

# ---------- 8. HTTPS 配置 ----------

echo -e "\n[18] HTTPS 配置（Let's Encrypt 免费证书）"
cat <<'EOF'
# 1. 安装 certbot
sudo apt install -y certbot python3-certbot-nginx

# 2. 申请证书（自动修改 Nginx 配置）
sudo certbot --nginx -d api.example.com -d www.example.com

# 3. 手动 HTTPS 配置
# /etc/nginx/sites-available/ecommerce-ssl
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location /api/ {
        proxy_pass http://127.0.0.1:3000;
    }
}

# HTTP 自动跳转 HTTPS
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$host$request_uri;
}

# 4. 证书自动续期（certbot 已自动配置）
sudo certbot renew --dry-run       # 测试续期
# crontab 自动续期
# 0 3 * * * /usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

# ---------- 9. 日志与访问控制 ----------

echo -e "\n[19] Nginx 日志配置"
cat <<'EOF'
# 自定义日志格式（在 http 块中）
log_format main '$remote_addr - $remote_user [$time_local] '
                '"$request" $status $body_bytes_sent '
                '"$http_referer" "$http_user_agent" '
                'rt=$request_time uct=$upstream_connect_time '
                'uht=$upstream_header_time urt=$upstream_response_time';

# 在 server 块中
access_log /var/log/nginx/ecommerce-access.log main;
error_log /var/log/nginx/ecommerce-error.log warn;

# 不记录健康检查日志
location /health {
    access_log off;
    proxy_pass http://127.0.0.1:3000/api/health;
}
EOF

echo -e "\n[20] 访问控制"
cat <<'EOF'
# 仅允许指定 IP 访问
location /admin/ {
    allow 192.168.1.0/24;          # 允许内网
    allow 10.0.0.0/8;
    deny all;                      # 拒绝其他
    proxy_pass http://127.0.0.1:3000;
}

# Basic 认证
location /admin/ {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:3000;
}

# 生成 .htpasswd
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd adminuser
EOF

# ---------- 10. 性能优化 ----------

echo -e "\n[21] Nginx 性能优化常用配置"
cat <<'EOF'
# /etc/nginx/nginx.conf 全局优化
worker_processes auto;             # 自动按 CPU 核心数
worker_connections 10240;          # 每个 worker 最大连接数
multi_accept on;                   # 一次接受多个连接

# HTTP 块优化
sendfile on;                       # 零拷贝
tcp_nopush on;                     # 等数据包满再发
tcp_nodelay on;                    # 禁用 Nagle 算法（小包立即发）
keepalive_timeout 65;
keepalive_requests 1000;
server_tokens off;                 # 隐藏版本号（安全）

# gzip 压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

# 缓冲区
client_body_buffer_size 16K;
client_header_buffer_size 1k;
large_client_header_buffers 4 8k;
EOF

echo -e "\n[22] 验证 Nginx 完整配置"
echo "命令：sudo nginx -T 2>/dev/null | head -n 30"
sudo nginx -T 2>/dev/null | head -n 30

# ---------- 11. 完整部署流程 ----------

echo -e "\n[23] Nginx 部署完整流程"
cat <<'EOF'
# 1. 安装
sudo apt install -y nginx

# 2. 创建网站目录
sudo mkdir -p /opt/ecommerce/frontend/dist
echo '<h1>Ecommerce Frontend</h1>' | sudo tee /opt/ecommerce/frontend/dist/index.html

# 3. 创建虚拟主机配置
sudo tee /etc/nginx/sites-available/ecommerce <<'EOF'
server {
    listen 80;
    server_name _;
    root /opt/ecommerce/frontend/dist;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# 4. 启用站点
sudo ln -sf /etc/nginx/sites-available/ecommerce /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 5. 测试配置
sudo nginx -t

# 6. 重载
sudo systemctl reload nginx

# 7. 验证
curl -I http://127.0.0.1/
curl http://127.0.0.1/api/health

# 8. 设置开机自启
sudo systemctl enable nginx
EOF

echo -e "\n============================================================"
echo "  Day08 - 02 Nginx 部署实战 完成"
echo "============================================================"
