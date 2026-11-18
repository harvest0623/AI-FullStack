#!/bin/bash
# 文件用途：管道与重定向演示
#           演示 | 管道链、>/>>/2>/2>&1 重定向、/dev/null、Here Document、xargs 组合命令
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：bash 04-pipeline-redirect.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本演示 Linux 管道与重定向的各种用法。
#   脚本可重复执行，所有操作在 /tmp 下进行。
# ============================================================

# 工作目录
WORK_DIR="/tmp/pipeline-demo"

echo "================================================"
echo "  管道与重定向演示"
echo "  工作目录：$WORK_DIR"
echo "================================================"

# === 0. 初始化 ===
echo ""
echo ">>> [0] 初始化工作目录..."
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# === 1. 管道 | 基础用法 ===
echo ""
echo ">>> [1] 管道 | 基础用法（前一个命令的输出作为后一个的输入）..."

echo "---- ls -l /etc | head -n 5（目录列表前 5 行）----"
ls -l /etc | head -n 5

echo ""
echo "---- ls -l /etc | wc -l（统计文件数）----"
ls -l /etc | wc -l

echo ""
echo "---- cat /etc/passwd | cut -d: -f1（提取用户名）----"
cat /etc/passwd | cut -d: -f1 | head -n 5

echo ""
echo "---- ps aux | grep bash | grep -v grep（查找 bash 进程）----"
ps aux | grep "bash" | grep -v "grep" | head -n 3

# === 2. 管道链（多级管道）===
echo ""
echo ">>> [2] 管道链（多级管道组合）..."

echo "---- cat /etc/passwd | cut -d: -f1 | sort | head -n 5（用户名排序后前 5）----"
cat /etc/passwd | cut -d: -f1 | sort | head -n 5

echo ""
echo "---- cat /etc/passwd | cut -d: -f7 | sort | uniq -c | sort -rn（统计 Shell 类型分布）----"
cat /etc/passwd | cut -d: -f7 | sort | uniq -c | sort -rn

echo ""
echo "---- ls -l /etc | grep '^d' | wc -l（统计 /etc 下的目录数）----"
ls -l /etc | grep "^d" | wc -l

echo ""
echo "---- ps aux | awk '{print \$1}' | sort | uniq -c | sort -rn | head -n 5（用户进程数 Top 5）----"
ps aux | awk "{print \$1}" | sort | uniq -c | sort -rn | head -n 5

echo ""
echo "---- echo 'hello world foo bar' | tr ' ' '\n' | sort | uniq -c（单词统计）----"
echo "hello world foo bar hello foo" | tr " " "\n" | sort | uniq -c | sort -rn

# === 3. 输出重定向 > 与 >> ===
echo ""
echo ">>> [3] 输出重定向 > 覆盖 与 >> 追加..."

echo "---- echo 'hello' > file.txt（覆盖写入）----"
echo "hello" > "$WORK_DIR/file.txt"
cat "$WORK_DIR/file.txt"

echo ""
echo "---- echo 'world' >> file.txt（追加写入）----"
echo "world" >> "$WORK_DIR/file.txt"
cat "$WORK_DIR/file.txt"

echo ""
echo "---- echo 'line3' >> file.txt（再追加）----"
echo "line3" >> "$WORK_DIR/file.txt"
cat "$WORK_DIR/file.txt"

echo ""
echo "---- echo 'overwrite' > file.txt（覆盖，原内容消失）----"
echo "overwrite" > "$WORK_DIR/file.txt"
cat "$WORK_DIR/file.txt"

echo ""
echo "---- ls -l > listing.txt（目录列表写入文件）----"
ls -l /etc > "$WORK_DIR/listing.txt"
echo "    listing.txt 行数：$(wc -l < "$WORK_DIR/listing.txt")"

echo ""
echo "---- date >> timestamp.log（追加时间戳）----"
date >> "$WORK_DIR/timestamp.log"
sleep 1
date >> "$WORK_DIR/timestamp.log"
cat "$WORK_DIR/timestamp.log"

# === 4. 错误重定向 2> ===
echo ""
echo ">>> [4] 错误重定向 2>..."

echo "---- ls /nonexistent（正常显示错误）----"
ls /nonexistent 2>&1 | head -n 1

echo ""
echo "---- ls /nonexistent 2> error.log（错误写入文件，屏幕无输出）----"
ls /nonexistent 2> "$WORK_DIR/error.log"
echo "    error.log 内容："
cat "$WORK_DIR/error.log"

echo ""
echo "---- ls /etc /nonexistent 2> error.log（正常输出到屏幕，错误到文件）----"
ls /etc /nonexistent 2> "$WORK_DIR/error2.log" | head -n 3
echo "    error2.log 内容："
cat "$WORK_DIR/error2.log"

# === 5. 合并标准输出与错误 2>&1 / &> ===
echo ""
echo ">>> [5] 合并标准输出与错误 2>&1 与 &>..."

echo "---- ls /etc /nonexistent > all.log 2>&1（合并到同一文件）----"
ls /etc /nonexistent > "$WORK_DIR/all.log" 2>&1
echo "    all.log 行数：$(wc -l < "$WORK_DIR/all.log")"
echo "    all.log 前 3 行："
head -n 3 "$WORK_DIR/all.log"
echo "    all.log 后 3 行："
tail -n 3 "$WORK_DIR/all.log"

echo ""
echo "---- ls /etc /nonexistent &> all2.log（Bash 4+ 简写）----"
ls /etc /nonexistent &> "$WORK_DIR/all2.log"
echo "    all2.log 行数：$(wc -l < "$WORK_DIR/all2.log")"

echo ""
echo "---- ls /etc /nonexistent 2>&1 | head -n 5（合并后通过管道）----"
ls /etc /nonexistent 2>&1 | head -n 5

# === 6. /dev/null 黑洞设备 ===
echo ""
echo ">>> [6] /dev/null 黑洞设备（丢弃输出）..."

echo "---- ls /nonexistent 2> /dev/null（错误丢弃，屏幕无输出）----"
ls /nonexistent 2> /dev/null
echo "    （上方无错误输出）"

echo ""
echo "---- command &> /dev/null（所有输出丢弃，常用于 cron）----"
ls /etc /nonexistent &> /dev/null
echo "    （上方无任何输出）"

echo ""
echo "---- cat /dev/null > file.txt（清空文件内容）----"
echo "some content" > "$WORK_DIR/clear-test.txt"
echo "    清空前：$(cat "$WORK_DIR/clear-test.txt")"
cat /dev/null > "$WORK_DIR/clear-test.txt"
echo "    清空后：'$([ -s "$WORK_DIR/clear-test.txt" ] && cat "$WORK_DIR/clear-test.txt" || echo "文件为空")'"

echo ""
echo "---- > file.txt（简写清空）----"
echo "content" > "$WORK_DIR/clear2.txt"
> "$WORK_DIR/clear2.txt"
echo "    清空后文件大小：$(stat -c '%s' "$WORK_DIR/clear2.txt") 字节"

echo ""
echo "---- grep 查找进程时丢弃错误 ----"
grep "root" /etc/shadow 2> /dev/null | head -n 1 || echo "    （无权限或无匹配，错误已丢弃）"

# === 7. 输入重定向 < ===
echo ""
echo ">>> [7] 输入重定向 <..."

echo "---- wc -l < /etc/passwd（从文件读取输入统计行数）----"
wc -l < /etc/passwd

echo ""
echo "---- sort < file.txt（从文件读取排序）----"
echo -e "banana\napple\ncherry" > "$WORK_DIR/fruits.txt"
sort < "$WORK_DIR/fruits.txt"

echo ""
echo "---- wc -l < file.txt vs cat file.txt | wc -l（两种写法等价）----"
echo "    方式1：wc -l < file.txt = $(wc -l < "$WORK_DIR/fruits.txt")"
echo "    方式2：cat file.txt | wc -l = $(cat "$WORK_DIR/fruits.txt" | wc -l)"

# === 8. Here Document <<EOF ===
echo ""
echo ">>> [8] Here Document <<EOF（多行输入）..."

echo "---- cat <<EOF > file（多行写入文件）----"
cat <<EOF > "$WORK_DIR/config.conf"
# 服务器配置文件
server {
    listen 80;
    server_name example.com;
    root /opt/ecommerce/frontend;
}
EOF
echo "    生成的文件内容："
cat "$WORK_DIR/config.conf"

echo ""
echo "---- cat <<'EOF'（加引号，变量不展开）----"
cat <<'EOF' > "$WORK_DIR/no-expand.txt"
当前用户是: $USER
当前目录是: $PWD
日期是: $(date)
EOF
echo "    （变量未展开，原样输出）"
cat "$WORK_DIR/no-expand.txt"

echo ""
echo "---- cat <<EOF（不加引号，变量展开）----"
cat <<EOF > "$WORK_DIR/expanded.txt"
当前用户是: $USER
当前目录是: $PWD
日期是: $(date '+%Y-%m-%d')
EOF
echo "    （变量已展开）"
cat "$WORK_DIR/expanded.txt"

echo ""
echo "---- 在 Shell 脚本中生成配置文件（实战）----"
cat <<EOF > "$WORK_DIR/nginx-app.conf"
# 自动生成的 Nginx 配置
# 生成时间: $(date)
upstream backend {
    server 127.0.0.1:3000;
    keepalive 32;
}

server {
    listen 80;
    server_name $USER-ecommerce.local;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
echo "    生成的 nginx-app.conf："
cat "$WORK_DIR/nginx-app.conf"

# === 9. Here String <<< ===
echo ""
echo ">>> [9] Here String <<<（单行输入）..."

echo "---- grep 'error' <<< 'this is an error message' ----"
grep "error" <<< "this is an error message"

echo ""
echo "---- wc -w <<< 'count these words' ----"
wc -w <<< "count these words"

echo ""
echo "---- awk '{print \$2}' <<< 'hello world' ----"
awk "{print \$2}" <<< "hello world"

echo ""
echo "---- bc <<< '3 + 5'（计算器）----"
bc <<< "3 + 5"

echo ""
echo "---- bc <<< 'scale=2; 10 / 3'（浮点除法）----"
bc <<< "scale=2; 10 / 3"

# === 10. xargs 参数传递 ===
echo ""
echo ">>> [10] xargs 参数传递（把输入转为命令参数）..."

echo "---- echo 'a b c' | xargs mkdir（创建多个目录）----"
echo "a b c" | xargs mkdir -p "$WORK_DIR/xargs-test/"
ls "$WORK_DIR/xargs-test/"

echo ""
echo "---- echo '1 2 3 4 5' | xargs -n 2 echo（每次 2 个参数）----"
echo "1 2 3 4 5" | xargs -n 2 echo

echo ""
echo "---- find + xargs grep（在找到的文件中搜索）----"
find /etc -name "*.conf" -type f 2>/dev/null | head -n 3 | xargs grep -l "port" 2>/dev/null | head -n 3

echo ""
echo "---- find + xargs -I {} mv（用占位符批量操作）----"
mkdir -p "$WORK_DIR/xargs-rename"
touch "$WORK_DIR/xargs-rename"/file{1..3}.txt
find "$WORK_DIR/xargs-rename" -name "*.txt" | xargs -I {} mv {} {}.bak
ls "$WORK_DIR/xargs-rename/"

echo ""
echo "---- find -print0 | xargs -0（处理含空格文件名）----"
mkdir -p "$WORK_DIR/space-test"
touch "$WORK_DIR/space-test/my file.txt"
touch "$WORK_DIR/space-test/another file.log"
find "$WORK_DIR/space-test" -type f -print0 | xargs -0 ls -l

echo ""
echo "---- find + xargs wc -l（批量统计行数）----"
find /etc -name "*.conf" -type f 2>/dev/null | head -n 3 | xargs wc -l 2>/dev/null

echo ""
echo "---- echo URLs | xargs curl（批量下载，仅演示不执行）----"
echo "    示例：echo 'url1 url2' | xargs -n 1 curl -O"
echo "    示例：find . -name '*.jpg' | xargs -P 4 -I {} convert {} {}.thumb.jpg（并行 4 个）"

# === 11. 综合实战：日志分析管道链 ===
echo ""
echo ">>> [11] 综合实战：日志分析管道链..."

# 创建模拟访问日志
cat > "$WORK_DIR/app-access.log" <<'LOGEOF'
192.168.1.10 - - [29/Jul/2026:10:00:01 +0800] "GET /api/products HTTP/1.1" 200 1234
192.168.1.20 - - [29/Jul/2026:10:00:02 +0800] "GET /api/users HTTP/1.1" 200 567
192.168.1.10 - - [29/Jul/2026:10:00:03 +0800] "POST /api/orders HTTP/1.1" 201 890
192.168.1.30 - - [29/Jul/2026:10:00:04 +0800] "GET /api/products/999 HTTP/1.1" 404 89
192.168.1.10 - - [29/Jul/2026:10:00:05 +0800] "GET /api/cart HTTP/1.1" 200 456
192.168.1.40 - - [29/Jul/2026:10:00:06 +0800] "GET /api/products HTTP/1.1" 500 45
192.168.1.20 - - [29/Jul/2026:10:00:07 +0800] "GET /api/orders/123 HTTP/1.1" 200 678
192.168.1.10 - - [29/Jul/2026:10:00:08 +0800] "DELETE /api/orders/456 HTTP/1.1" 204 0
192.168.1.30 - - [29/Jul/2026:10:00:09 +0800] "GET /admin HTTP/1.1" 403 67
192.168.1.20 - - [29/Jul/2026:10:00:10 +0800] "GET /api/products HTTP/1.1" 200 1234
LOGEOF

echo "---- 场景 1：统计 Top 3 访问 IP ----"
awk "{print \$1}" "$WORK_DIR/app-access.log" | sort | uniq -c | sort -rn | head -n 3

echo ""
echo "---- 场景 2：统计状态码分布 ----"
awk "{print \$9}" "$WORK_DIR/app-access.log" | sort | uniq -c | sort -rn

echo ""
echo "---- 场景 3：找出所有错误请求（4xx/5xx）----"
awk "\$9>=400" "$WORK_DIR/app-access.log" | head -n 5

echo ""
echo "---- 场景 4：统计总流量 ----"
awk "{sum+=\$10} END {printf \"总流量: %d 字节 (%.2f KB)\\n\", sum, sum/1024}" "$WORK_DIR/app-access.log"

echo ""
echo "---- 场景 5：找出访问量最大的 API 路径 ----"
awk -F'"' "{split(\$2,a,\" \"); print a[2]}" "$WORK_DIR/app-access.log" | sort | uniq -c | sort -rn | head -n 5

echo ""
echo "---- 场景 6：生成访问报表并保存到文件 ----"
{
    echo "===================================="
    echo "  访问日志分析报表"
    echo "  生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "===================================="
    echo ""
    echo "1. 总请求数:"
    wc -l < "$WORK_DIR/app-access.log" | awk '{print "   " $1 " 个请求"}'
    echo ""
    echo "2. 状态码分布:"
    awk "{count[\$9]++} END {for(c in count) printf \"   %s: %d 次\\n\", c, count[c]}" "$WORK_DIR/app-access.log" | sort
    echo ""
    echo "3. Top 3 IP:"
    awk "{count[\$1]++} END {for(ip in count) printf \"   %s %d 次\\n\", count[ip], ip}" "$WORK_DIR/app-access.log" | sort -rn | head -n 3
    echo ""
    echo "4. 总流量:"
    awk "{sum+=\$10} END {printf \"   %d 字节 (%.2f KB)\\n\", sum, sum/1024}" "$WORK_DIR/app-access.log"
    echo ""
    echo "===================================="
} > "$WORK_DIR/report.txt"

echo "    报表已保存到 $WORK_DIR/report.txt："
cat "$WORK_DIR/report.txt"

# === 12. 进程替换 <() ===
echo ""
echo ">>> [12] 进程替换 <()（高级用法）..."

echo "---- diff <(ls /etc) <(ls /etc) （对比两个命令的输出）----"
diff <(ls /etc | head -n 5) <(ls /etc | head -n 5) && echo "    （无差异）"

echo ""
echo "---- comm <(sort file1) <(sort file2)（比较两个排序后的输出）----"
echo -e "apple\nbanana\ncherry" > "$WORK_DIR/list1.txt"
echo -e "banana\ncherry\ndate" > "$WORK_DIR/list2.txt"
echo "    list1: apple banana cherry"
echo "    list2: banana cherry date"
echo "    comm 输出（第1列仅list1, 第2列仅list2, 第3列都有）:"
comm <(sort "$WORK_DIR/list1.txt") <(sort "$WORK_DIR/list2.txt")

# === 13. 重定向顺序的重要性 ===
echo ""
echo ">>> [13] 重定向顺序的重要性..."

echo "---- 错误顺序：ls /etc /bad 2>&1 > file（stderr 仍到屏幕）----"
echo "    说明：2>&1 在 > file 之前，stderr 指向当时的 stdout（屏幕），"
echo "          之后 stdout 才重定向到 file，所以 stderr 仍在屏幕"
ls /etc /nonexistent 2>&1 > "$WORK_DIR/order-test.log" 2>&1 | head -n 1 || true

echo ""
echo "---- 正确顺序：ls /etc /bad > file 2>&1（stderr 也到 file）----"
ls /etc /nonexistent > "$WORK_DIR/order-test2.log" 2>&1
echo "    order-test2.log 行数：$(wc -l < "$WORK_DIR/order-test2.log")（含错误信息）"

# === 清理 ===
echo ""
echo "================================================"
echo "  管道与重定向演示完成！"
echo "  工作目录保留在：$WORK_DIR"
echo "  清理：rm -rf $WORK_DIR"
echo "================================================"
