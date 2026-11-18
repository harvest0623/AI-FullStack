#!/bin/bash
# 文件用途：文件操作命令练习
#           演示 cat/less/head/tail/wc/sort/uniq/cut/tr/tee/stat 等命令
#           先在 /opt/ecommerce/logs/ 下创建模拟日志作为练习素材
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：bash 01-file-operations.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本先创建模拟的 Nginx 访问日志与应用错误日志，
#   然后用各种文件操作命令进行分析。
#   脚本可重复执行：每次重新生成日志。
#   需要 /opt/ecommerce/logs/ 目录存在（由 Day01 脚本创建）。
# ============================================================

# 日志目录（如不存在则创建）
LOG_DIR="/opt/ecommerce/logs"
ACCESS_LOG="$LOG_DIR/nginx/access.log"
ERROR_LOG="$LOG_DIR/error.log"
APP_LOG="$LOG_DIR/app.log"

# 如果 /opt/ecommerce 不存在，在 /tmp 下创建备用目录
if [ ! -d "/opt/ecommerce" ]; then
    LOG_DIR="/tmp/ecommerce-logs"
    ACCESS_LOG="$LOG_DIR/nginx/access.log"
    ERROR_LOG="$LOG_DIR/error.log"
    APP_LOG="$LOG_DIR/app.log"
fi

echo "================================================"
echo "  文件操作命令练习"
echo "  日志目录：$LOG_DIR"
echo "================================================"

# === 0. 创建模拟日志素材 ===
echo ""
echo ">>> [0] 创建模拟日志素材..."

mkdir -p "$LOG_DIR/nginx"

# 生成模拟 Nginx 访问日志（Combined Log Format）
# 格式：IP - - [时间] "请求行" 状态码 字节数 "Referer" "User-Agent"
cat > "$ACCESS_LOG" <<'LOGEOF'
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

# 生成模拟应用错误日志
cat > "$ERROR_LOG" <<'LOGEOF'
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
LOGEOF

# 生成模拟应用日志（含空行与重复行，用于 sort/uniq 练习）
cat > "$APP_LOG" <<'LOGEOF'
INFO  Server started on port 3000
DEBUG Loading configuration from /opt/ecommerce/backend/config.json
INFO  Database connected: mysql://localhost:3306/ecommerce

INFO  Redis connected: redis://localhost:6379
DEBUG Initializing middleware: cors
DEBUG Initializing middleware: helmet
INFO  Routes registered: /api/products, /api/users, /api/orders

ERROR Failed to load optional plugin: analytics
INFO  Server started on port 3000
DEBUG Loading configuration from /opt/ecommerce/backend/config.json
WARN  Deprecated API endpoint /api/v1/legacy
INFO  Health check endpoint ready: /health
LOGEOF

echo "    模拟日志已生成："
echo "      - $ACCESS_LOG ($(wc -l < "$ACCESS_LOG") 行)"
echo "      - $ERROR_LOG ($(wc -l < "$ERROR_LOG") 行)"
echo "      - $APP_LOG ($(wc -l < "$APP_LOG") 行)"

# === 1. cat 命令演示 ===
echo ""
echo ">>> [1] cat 命令演示..."

echo "---- cat error.log（查看整个文件）----"
cat "$ERROR_LOG"

echo ""
echo "---- cat -n app.log（显示行号）----"
cat -n "$APP_LOG" | head -n 8

echo ""
echo "---- cat -b app.log（仅非空行编号）----"
cat -b "$APP_LOG" | head -n 8

echo ""
echo "---- cat -s app.log（压缩连续空行）----"
cat -s "$APP_LOG" | head -n 8

echo ""
echo "---- cat -A app.log（显示特殊字符，行尾 $，Tab ^I）----"
cat -A "$ERROR_LOG" | head -n 3

# === 2. less 命令演示（脚本中无法交互，仅提示用法）===
echo ""
echo ">>> [2] less 命令演示（交互式，脚本中仅提示用法）..."
echo "    在终端中执行：less $ACCESS_LOG"
echo "    常用快捷键："
echo "      Space/f  向下翻页    b       向上翻页"
echo "      g        跳到首部    G       跳到尾部"
echo "      /keyword 向下搜索    ?keyword 向上搜索"
echo "      n/N      下/上一个   q       退出"
echo ""
echo "    more $ERROR_LOG   # 简单分页（仅向下）"

# === 3. head / tail 命令演示 ===
echo ""
echo ">>> [3] head / tail 命令演示..."

echo "---- head -n 5 access.log（前 5 行）----"
head -n 5 "$ACCESS_LOG"

echo ""
echo "---- head -n 3 error.log（前 3 行）----"
head -n 3 "$ERROR_LOG"

echo ""
echo "---- tail -n 5 access.log（后 5 行）----"
tail -n 5 "$ACCESS_LOG"

echo ""
echo "---- tail -n 3 error.log（后 3 行）----"
tail -n 3 "$ERROR_LOG"

echo ""
echo "---- tail -n +5 access.log（从第 5 行到末尾，前 3 行）----"
tail -n +5 "$ACCESS_LOG" | head -n 3

echo ""
echo "---- tail -f 提示（实时追踪，交互式）----"
echo "    在终端中执行：tail -f $ACCESS_LOG"
echo "    新增内容会实时显示，按 Ctrl+C 退出"
echo "    tail -F $ACCESS_LOG  # 文件被轮转后继续追踪新文件"

# === 4. nl 命令演示 ===
echo ""
echo ">>> [4] nl 命令演示（显示行号）..."

echo "---- nl error.log（默认空行不编号）----"
nl "$ERROR_LOG" | head -n 5

echo ""
echo "---- nl -ba app.log（所有行都编号）----"
nl -ba "$APP_LOG" | head -n 8

# === 5. wc 命令演示 ===
echo ""
echo ">>> [5] wc 命令演示（统计行/词/字节）..."

echo "---- wc access.log（行数 词数 字节数 文件名）----"
wc "$ACCESS_LOG"

echo ""
echo "---- wc -l access.log（仅行数）----"
wc -l "$ACCESS_LOG"

echo ""
echo "---- wc -w error.log（单词数）----"
wc -w "$ERROR_LOG"

echo ""
echo "---- wc -c access.log（字节数）----"
wc -c "$ACCESS_LOG"

echo ""
echo "---- wc -L access.log（最长行长度）----"
wc -L "$ACCESS_LOG"

echo ""
echo "---- 组合：统计 /opt/ecommerce 下的文件数（管道）----"
find "$LOG_DIR" -type f | wc -l

# === 6. sort 命令演示 ===
echo ""
echo ">>> [6] sort 命令演示（排序）..."

echo "---- sort app.log（默认字典序）----"
sort "$APP_LOG" | head -n 6

echo ""
echo "---- sort -r app.log（降序）----"
sort -r "$APP_LOG" | head -n 4

echo ""
echo "---- sort -u app.log（排序并去重）----"
sort -u "$APP_LOG" | head -n 8

echo ""
echo "---- 提取访问日志的 HTTP 状态码并按数值排序 ----"
# awk 在 Day03 详解，这里先用 cut 配合
# access.log 格式：IP - - [time] "REQ" STATUS BYTES ...
# 状态码是第 9 个字段（以空格分隔）
cut -d' ' -f9 "$ACCESS_LOG" | sort -n | uniq -c

echo ""
echo "---- 提取访问日志的 IP 并按出现次数排序 ----"
cut -d' ' -f1 "$ACCESS_LOG" | sort | uniq -c | sort -rn

# === 7. uniq 命令演示 ===
echo ""
echo ">>> [7] uniq 命令演示（去重，需先 sort）..."

echo "---- 原始 app.log 中的日志级别列 ----"
cut -d' ' -f1 "$APP_LOG"

echo ""
echo "---- sort | uniq -c（去重并统计次数）----"
cut -d' ' -f1 "$APP_LOG" | sort | uniq -c

echo ""
echo "---- sort | uniq -c | sort -rn（按次数降序）----"
cut -d' ' -f1 "$APP_LOG" | sort | uniq -c | sort -rn

echo ""
echo "---- sort | uniq -d（仅显示重复的行）----"
cut -d' ' -f1 "$APP_LOG" | sort | uniq -d

echo ""
echo "---- sort | uniq -u（仅显示不重复的行）----"
cut -d' ' -f1 "$APP_LOG" | sort | uniq -u

# === 8. cut 命令演示 ===
echo ""
echo ">>> [8] cut 命令演示（分列提取）..."

echo "---- cut -d' ' -f1 access.log（提取 IP，第 1 列）----"
cut -d' ' -f1 "$ACCESS_LOG" | head -n 5

echo ""
echo "---- cut -d' ' -f1,9 access.log（IP + 状态码）----"
cut -d' ' -f1,9 "$ACCESS_LOG" | head -n 5

echo ""
echo "---- cut -c 1-20 access.log（按字符位置，前 20 字符）----"
cut -c 1-20 "$ACCESS_LOG" | head -n 3

echo ""
echo "---- cut -d: -f1,3 /etc/passwd（用户名 + UID）----"
cut -d: -f1,3 /etc/passwd | head -n 5

# === 9. tr 命令演示 ===
echo ""
echo ">>> [9] tr 命令演示（替换/删除/压缩字符）..."

echo "---- tr 'a-z' 'A-Z'（小写转大写）----"
echo "Hello Linux World" | tr 'a-z' 'A-Z'

echo ""
echo "---- tr 'A-Z' 'a-z'（大写转小写）----"
echo "Hello Linux World" | tr 'A-Z' 'a-z'

echo ""
echo "---- tr -s ' '（压缩重复空格）----"
echo "hello    world    linux" | tr -s ' '

echo ""
echo "---- tr -d ' '（删除所有空格）----"
echo "192.168.1.100" | tr -d '.'

echo ""
echo "---- tr '.' '-'（点号转横线）----"
echo "192.168.1.100" | tr '.' '-'

echo ""
echo "---- tr -dc '0-9\n'（仅保留数字与换行）----"
echo "order123,price456,total789" | tr -dc '0-9\n'

echo ""
echo "---- cat error.log | tr 'a-z' 'A-Z'（日志转大写，前 3 行）----"
cat "$ERROR_LOG" | tr 'a-z' 'A-Z' | head -n 3

# === 10. tee 命令演示 ===
echo ""
echo ">>> [10] tee 命令演示（双向输出）..."

echo "---- ls -l | tee /tmp/files.txt（输出到屏幕同时写文件）----"
ls -l "$LOG_DIR" | tee /tmp/files.txt

echo ""
echo "---- 验证文件已写入 ----"
echo "    /tmp/files.txt 行数：$(wc -l < /tmp/files.txt)"

echo ""
echo "---- ls -l | tee -a /tmp/files.txt（追加模式）----"
ls -l "$LOG_DIR/nginx" | tee -a /tmp/files.txt
echo "    追加后行数：$(wc -l < /tmp/files.txt)"

echo ""
echo "---- ls -l | tee a.txt b.txt（同时写入多个文件）----"
ls -l "$LOG_DIR" | tee /tmp/files-a.txt /tmp/files-b.txt > /dev/null
echo "    a.txt 行数：$(wc -l < /tmp/files-a.txt)，b.txt 行数：$(wc -l < /tmp/files-b.txt)"

# 清理 tee 演示产生的临时文件
rm -f /tmp/files.txt /tmp/files-a.txt /tmp/files-b.txt

# === 11. file 与 stat 命令演示 ===
echo ""
echo ">>> [11] file 与 stat 命令演示..."

echo "---- file access.log（文件类型）----"
file "$ACCESS_LOG"

echo ""
echo "---- file /usr/bin/ls（ELF 可执行文件）----"
file /usr/bin/ls

echo ""
echo "---- file /dev/null（字符设备）----"
file /dev/null

echo ""
echo "---- file -i access.log（MIME 类型）----"
file -i "$ACCESS_LOG"

echo ""
echo "---- stat access.log（完整元信息）----"
stat "$ACCESS_LOG"

echo ""
echo "---- stat -c '%n %s %y' access.log（自定义格式：名称 大小 修改时间）----"
stat -c '%n %s %y' "$ACCESS_LOG"

echo ""
echo "---- stat -c '%a' access.log（权限数字）----"
stat -c '%a' "$ACCESS_LOG"

echo ""
echo "================================================"
echo "  文件操作命令练习完成！"
echo "  日志素材保留在：$LOG_DIR"
echo "  后续脚本 02-file-search.sh 与 Day03 脚本会用到这些日志"
echo "================================================"
