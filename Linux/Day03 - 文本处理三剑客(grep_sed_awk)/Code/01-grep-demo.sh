#!/bin/bash
# 文件用途：grep 命令演示
#           在模拟日志中搜索关键词、-r 递归搜索、-v/-c/-n/-o/-A/-B/-C 选项、正则匹配
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：bash 01-grep-demo.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本先创建模拟的 Nginx 访问日志与应用日志，
#   然后用 grep 的各种选项进行搜索演示。
#   脚本可重复执行。
# ============================================================

# 工作目录
WORK_DIR="/tmp/grep-demo"

echo "================================================"
echo "  grep 文本搜索命令演示"
echo "  工作目录：$WORK_DIR"
echo "================================================"

# === 0. 创建模拟日志素材 ===
echo ""
echo ">>> [0] 创建模拟日志素材..."

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"/{logs/nginx,config}

# 创建 Nginx 访问日志（Combined Log Format）
cat > "$WORK_DIR/logs/nginx/access.log" <<'LOGEOF'
192.168.1.10 - - [29/Jul/2026:10:00:01 +0800] "GET /api/products HTTP/1.1" 200 1234 "-" "Mozilla/5.0 Chrome/120.0"
192.168.1.20 - - [29/Jul/2026:10:00:02 +0800] "GET /api/users/profile HTTP/1.1" 200 567 "-" "Mozilla/5.0 Firefox/121.0"
192.168.1.10 - - [29/Jul/2026:10:00:03 +0800] "POST /api/orders HTTP/1.1" 201 890 "-" "curl/7.81.0"
192.168.1.30 - - [29/Jul/2026:10:00:04 +0800] "GET /api/products/999 HTTP/1.1" 404 89 "-" "Mozilla/5.0 Chrome/120.0"
192.168.1.20 - - [29/Jul/2026:10:00:05 +0800] "GET /api/cart HTTP/1.1" 200 456 "-" "Mozilla/5.0 Firefox/121.0"
192.168.1.10 - - [29/Jul/2026:10:00:06 +0800] "GET /static/js/app.js HTTP/1.1" 200 8912 "https://example.com/" "Mozilla/5.0 Chrome/120.0"
192.168.1.40 - - [29/Jul/2026:10:00:07 +0800] "GET /api/products HTTP/1.1" 200 1234 "-" "Mozilla/5.0 Safari/17.0"
192.168.1.30 - - [29/Jul/2026:10:00:08 +0800] "GET /admin HTTP/1.1" 403 67 "-" "Mozilla/5.0 Chrome/120.0"
192.168.1.20 - - [29/Jul/2026:10:00:09 +0800] "PUT /api/users/profile HTTP/1.1" 200 234 "-" "Mozilla/5.0 Firefox/121.0"
192.168.1.10 - - [29/Jul/2026:10:00:10 +0800] "GET /api/orders/123 HTTP/1.1" 200 678 "-" "Mozilla/5.0 Chrome/120.0"
192.168.1.50 - - [29/Jul/2026:10:00:11 +0800] "GET /api/products HTTP/1.1" 500 45 "-" "curl/7.81.0"
192.168.1.30 - - [29/Jul/2026:10:00:12 +0800] "GET /static/css/style.css HTTP/1.1" 200 4567 "https://example.com/" "Mozilla/5.0 Chrome/120.0"
192.168.1.10 - - [29/Jul/2026:10:00:13 +0800] "DELETE /api/orders/456 HTTP/1.1" 204 0 "-" "curl/7.81.0"
192.168.1.20 - - [29/Jul/2026:10:00:14 +0800] "GET /api/products HTTP/1.1" 200 1234 "-" "Mozilla/5.0 Firefox/121.0"
192.168.1.40 - - [29/Jul/2026:10:00:15 +0800] "POST /api/auth/login HTTP/1.1" 200 345 "-" "Mozilla/5.0 Safari/17.0"
LOGEOF

# 创建应用错误日志
cat > "$WORK_DIR/logs/error.log" <<'LOGEOF'
[2026-07-29 10:00:01] ERROR: Database connection failed (attempt 1/3)
[2026-07-29 10:00:02] WARN: Cache miss for key user:profile:1001
[2026-07-29 10:00:03] ERROR: Invalid order ID 999
[2026-07-29 10:00:04] INFO: User login success (id=1001)
[2026-07-29 10:00:05] ERROR: Payment gateway timeout
[2026-07-29 10:00:06] WARN: Slow query detected (2.3s): SELECT * FROM orders
[2026-07-29 10:00:07] INFO: Order created (id=123)
[2026-07-29 10:00:08] ERROR: Redis connection refused
[2026-07-29 10:00:09] WARN: Rate limit exceeded for IP 192.168.1.30
[2026-07-29 10:00:10] INFO: Backup completed successfully
[2026-07-29 10:00:11] ERROR: Unhandled exception in /api/products
[2026-07-29 10:00:12] DEBUG: Query executed in 0.045s
LOGEOF

# 创建应用日志
cat > "$WORK_DIR/logs/app.log" <<'LOGEOF'
2026-07-29 10:00:00 INFO  Server starting on port 3000
2026-07-29 10:00:01 INFO  Loading configuration from config/app.env
2026-07-29 10:00:02 DEBUG Connecting to database mysql://localhost:3306
2026-07-29 10:00:03 ERROR Database connection failed: Connection refused
2026-07-29 10:00:04 WARN  Retrying connection (attempt 1/3)
2026-07-29 10:00:05 INFO  Database connected successfully
2026-07-29 10:00:06 DEBUG Connecting to Redis redis://localhost:6379
2026-07-29 10:00:07 INFO  Redis connected successfully
2026-07-29 10:00:08 INFO  Routes registered: /api/products, /api/users, /api/orders
2026-07-29 10:00:09 WARN  Deprecated endpoint /api/v1/legacy will be removed
2026-07-29 10:00:10 INFO  Server started on port 3000
2026-07-29 10:00:11 ERROR Failed to load plugin: analytics
2026-07-29 10:00:12 INFO  Health check ready at /health
LOGEOF

# 创建配置文件（用于递归搜索演示）
cat > "$WORK_DIR/config/database.conf" <<'EOF'
# MySQL Database Configuration
host=localhost
port=3306
username=ecommerce_user
password=SecretPass123
database=ecommerce
pool_size=10
EOF

cat > "$WORK_DIR/config/redis.conf" <<'EOF'
# Redis Configuration
host=localhost
port=6379
password=RedisPass456
db=0
EOF

cat > "$WORK_DIR/config/app.env" <<'EOF'
NODE_ENV=production
PORT=3000
JWT_SECRET=MySecretKey789
LOG_LEVEL=info
DATABASE_URL=mysql://ecommerce_user:SecretPass123@localhost:3306/ecommerce
EOF

echo "    模拟日志已创建："
echo "      - access.log ($(wc -l < "$WORK_DIR/logs/nginx/access.log") 行)"
echo "      - error.log ($(wc -l < "$WORK_DIR/logs/error.log") 行)"
echo "      - app.log ($(wc -l < "$WORK_DIR/logs/app.log") 行)"
echo "      - config/ 目录（3 个配置文件）"

ACCESS_LOG="$WORK_DIR/logs/nginx/access.log"
ERROR_LOG="$WORK_DIR/logs/error.log"
APP_LOG="$WORK_DIR/logs/app.log"

# === 1. grep 基本用法 ===
echo ""
echo ">>> [1] grep 基本用法..."

echo "---- grep 'ERROR' error.log（搜索含 ERROR 的行）----"
grep "ERROR" "$ERROR_LOG"

echo ""
echo "---- grep 'error' error.log（默认区分大小写，无结果）----"
grep "error" "$ERROR_LOG" || echo "    （无匹配，因为区分大小写）"

echo ""
echo "---- grep -i 'error' error.log（忽略大小写）----"
grep -i "error" "$ERROR_LOG"

# === 2. grep -v 反选 ===
echo ""
echo ">>> [2] grep -v 反选（不匹配的行）..."

echo "---- grep -v 'ERROR' error.log（不含 ERROR 的行）----"
grep -v "ERROR" "$ERROR_LOG"

echo ""
echo "---- grep -v '^#' config/database.conf（排除注释行）----"
grep -v "^#" "$WORK_DIR/config/database.conf"

echo ""
echo "---- grep -v '^$\|^#' config/database.conf（排除空行和注释行）----"
grep -v "^$\|^#" "$WORK_DIR/config/database.conf"

# === 3. grep -c 计数 ===
echo ""
echo ">>> [3] grep -c 计数（仅输出匹配行数）..."

echo "---- grep -c 'ERROR' error.log（ERROR 行数）----"
grep -c "ERROR" "$ERROR_LOG"

echo ""
echo "---- grep -c '200' access.log（200 状态码行数）----"
grep -c " 200 " "$ACCESS_LOG"

echo ""
echo "---- grep -c '404\|500' access.log（404 或 500 行数）----"
grep -c " 404 \| 500 " "$ACCESS_LOG"

# === 4. grep -n 显示行号 ===
echo ""
echo ">>> [4] grep -n 显示行号..."

echo "---- grep -n 'ERROR' error.log（带行号）----"
grep -n "ERROR" "$ERROR_LOG"

echo ""
echo "---- grep -n '192.168.1.10' access.log（IP 192.168.1.10 的请求行号）----"
grep -n "192.168.1.10" "$ACCESS_LOG"

# === 5. grep -o 仅输出匹配部分 ===
echo ""
echo ">>> [5] grep -o 仅输出匹配部分..."

echo "---- grep -o '[0-9]\+' error.log（提取所有数字）----"
grep -o "[0-9]\+" "$ERROR_LOG" | head -n 10

echo ""
echo "---- grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' access.log（提取所有 IP）----"
grep -oE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" "$ACCESS_LOG" | sort -u

echo ""
echo "---- grep -oE 'HTTP/[0-9.]+' access.log（提取 HTTP 版本）----"
grep -oE "HTTP/[0-9.]+" "$ACCESS_LOG" | sort | uniq -c

# === 6. grep -w 全词匹配 ===
echo ""
echo ">>> [6] grep -w 全词匹配..."

echo "---- grep 'port' app.log（普通匹配，会匹配 port、portable 等）----"
grep "port" "$APP_LOG"

echo ""
echo "---- grep -w 'port' app.log（全词匹配，仅匹配 port 单词）----"
grep -w "port" "$APP_LOG"

# === 7. grep -A/-B/-C 上下文 ===
echo ""
echo ">>> [7] grep -A/-B/-C 上下文..."

echo "---- grep -A 2 'ERROR' error.log（匹配行后 2 行）----"
grep -A 2 "ERROR" "$ERROR_LOG"

echo ""
echo "---- grep -B 1 'ERROR' error.log（匹配行前 1 行）----"
grep -B 1 "ERROR" "$ERROR_LOG"

echo ""
echo "---- grep -C 1 'ERROR' error.log（匹配行前后各 1 行）----"
grep -C 1 "ERROR" "$ERROR_LOG"

echo ""
echo "---- grep -C 2 'Database' app.log（Database 相关上下文）----"
grep -C 2 "Database" "$APP_LOG"

# === 8. grep -E 扩展正则 ===
echo ""
echo ">>> [8] grep -E 扩展正则..."

echo "---- grep -E 'ERROR|WARN' error.log（ERROR 或 WARN）----"
grep -E "ERROR|WARN" "$ERROR_LOG"

echo ""
echo "---- grep -E '404|500' access.log（404 或 500 状态码）----"
grep -E " (404|500) " "$ACCESS_LOG"

echo ""
echo "---- grep -E 'GET|POST|PUT|DELETE' access.log（所有请求方法，前 5 行）----"
grep -oE '"(GET|POST|PUT|DELETE)' "$ACCESS_LOG" | head -n 5

echo ""
echo "---- grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' access.log（以 IP 开头的行，前 3 行）----"
grep -E "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" "$ACCESS_LOG" | head -n 3

# === 9. grep -P Perl 正则 ===
echo ""
echo ">>> [9] grep -P Perl 正则（如支持）..."

if echo "test" | grep -P "test" >/dev/null 2>&1; then
    echo "---- grep -P '\d+' error.log（提取数字）----"
    grep -oP "\d+" "$ERROR_LOG" | head -n 5

    echo ""
    echo "---- grep -P '\berror\b' app.log（全词匹配 error，忽略大小写）----"
    grep -iP "\berror\b" "$APP_LOG"

    echo ""
    echo "---- grep -P 'password\s*=\s*\S+' config/database.conf（提取密码配置行）----"
    grep -P "password\s*=\s*\S+" "$WORK_DIR/config/database.conf"
else
    echo "    当前 grep 不支持 -P（Perl 正则），可用 -E 替代"
fi

# === 10. grep -r 递归搜索 ===
echo ""
echo ">>> [10] grep -r 递归搜索目录..."

echo "---- grep -r 'password' config/（搜索含 password 的文件）----"
grep -r "password" "$WORK_DIR/config/"

echo ""
echo "---- grep -rn 'port' config/（带行号递归搜索）----"
grep -rn "port" "$WORK_DIR/config/"

echo ""
echo "---- grep -rl 'password' config/（仅显示含匹配的文件名）----"
grep -rl "password" "$WORK_DIR/config/"

echo ""
echo "---- grep -ri 'ERROR\|WARN' logs/（递归忽略大小写搜索）----"
grep -ri "ERROR\|WARN" "$WORK_DIR/logs/" | head -n 5

echo ""
echo "---- grep -r --include='*.log' 'ERROR' logs/（仅搜索 .log 文件）----"
grep -r --include="*.log" "ERROR" "$WORK_DIR/logs/"

echo ""
echo "---- grep -r --exclude='access.log' 'INFO' logs/（排除 access.log）----"
grep -r --exclude="access.log" "INFO" "$WORK_DIR/logs/"

# === 11. grep --color 高亮 ===
echo ""
echo ">>> [11] grep --color 高亮匹配（终端可见）..."

echo "---- grep --color 'ERROR' error.log（ERROR 高亮显示）----"
grep --color "ERROR" "$ERROR_LOG" | head -n 3

echo ""
echo "---- grep --color -E '[0-9]+' error.log（数字高亮，前 3 行）----"
grep --color -E "[0-9]+" "$ERROR_LOG" | head -n 3

# === 12. grep 实战场景 ===
echo ""
echo ">>> [12] grep 实战场景..."

echo "---- 场景 1：找出所有 4xx 和 5xx 错误请求 ----"
grep -E " (4[0-9]{2}|5[0-9]{2}) " "$ACCESS_LOG"

echo ""
echo "---- 场景 2：统计各状态码数量 ----"
grep -oE " [0-9]{3} " "$ACCESS_LOG" | sort | uniq -c | sort -rn

echo ""
echo "---- 场景 3：找出所有 POST 请求 ----"
grep '"POST' "$ACCESS_LOG"

echo ""
echo "---- 场景 4：找出访问 /admin 的请求 ----"
grep "/admin" "$ACCESS_LOG"

echo ""
echo "---- 场景 5：搜索敏感配置（密码、密钥）----"
grep -rinE "password|secret|key" "$WORK_DIR/config/"

echo ""
echo "---- 场景 6：统计每个 IP 的访问次数 ----"
grep -oE "^[0-9.]+" "$ACCESS_LOG" | sort | uniq -c | sort -rn

echo ""
echo "---- 场景 7：查找进程（排除 grep 自身）----"
ps aux | grep "bash" | grep -v "grep" | head -n 3

echo ""
echo "---- 场景 8：查找含特定错误的日志及上下文 ----"
grep -n -C 1 "connection" "$ERROR_LOG"

echo ""
echo "================================================"
echo "  grep 演示完成！"
echo "  日志素材保留在：$WORK_DIR"
echo "  后续 sed/awk 脚本会复用类似素材"
echo "================================================"
