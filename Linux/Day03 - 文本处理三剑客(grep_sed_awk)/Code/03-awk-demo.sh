#!/bin/bash
# 文件用途：awk 文本分析演示
#           演示字段提取、BEGIN/END 块、NR/NF 变量、条件过滤
#           求和/平均、数组统计计数、printf 格式化输出、分析 Nginx 访问日志
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：bash 03-awk-demo.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本先创建模拟的 Nginx 访问日志与结构化数据，
#   然后用 awk 的各种功能进行分析演示。
#   脚本可重复执行。
# ============================================================

# 工作目录
WORK_DIR="/tmp/awk-demo"

echo "================================================"
echo "  awk 文本分析演示"
echo "  工作目录：$WORK_DIR"
echo "================================================"

# === 0. 创建模拟素材 ===
echo ""
echo ">>> [0] 创建模拟日志与数据素材..."

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# 创建 Nginx 访问日志（Combined Log Format）
cat > "$WORK_DIR/access.log" <<'LOGEOF'
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

# 创建 CSV 格式的销售数据
cat > "$WORK_DIR/sales.csv" <<'EOF'
date,product,quantity,price,city
2026-07-01,iPhone 15,5,5999,北京
2026-07-01,iPad Pro,3,6999,上海
2026-07-02,iPhone 15,8,5999,广州
2026-07-02,MacBook Pro,2,12999,北京
2026-07-03,iPhone 15,10,5999,深圳
2026-07-03,AirPods Pro,15,1999,上海
2026-07-04,iPad Pro,4,6999,广州
2026-07-04,MacBook Pro,3,12999,深圳
2026-07-05,AirPods Pro,20,1999,北京
2026-07-05,iPhone 15,6,5999,上海
EOF

# 创建 /etc/passwd 的简化版
cat > "$WORK_DIR/users.txt" <<'EOF'
deploy:x:1000:1000:Deploy User:/home/deploy:/bin/bash
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
mysql:x:1001:1001:MySQL Server:/var/lib/mysql:/bin/false
redis:x:1002:1002:Redis Server:/var/lib/redis:/bin/false
git:x:1003:1003:Git User:/home/git:/bin/bash
EOF

# 创建数值数据
cat > "$WORK_DIR/numbers.txt" <<'EOF'
100
200
150
300
50
250
180
EOF

echo "    模拟素材已创建："
echo "      - access.log（Nginx 访问日志，$(wc -l < "$WORK_DIR/access.log") 行）"
echo "      - sales.csv（销售数据，$(wc -l < "$WORK_DIR/sales.csv") 行）"
echo "      - users.txt（用户数据，$(wc -l < "$WORK_DIR/users.txt") 行）"
echo "      - numbers.txt（数值数据，$(wc -l < "$WORK_DIR/numbers.txt") 行）"

ACCESS_LOG="$WORK_DIR/access.log"

# === 1. awk 基本字段提取 ===
echo ""
echo ">>> [1] awk 基本字段提取（默认空格分隔）..."

echo "---- awk '{print \$1}' access.log（提取第 1 列 IP）----"
awk '{print $1}' "$ACCESS_LOG" | head -n 5

echo ""
echo "---- awk '{print \$1, \$9}' access.log（IP + 状态码）----"
awk '{print $1, $9}' "$ACCESS_LOG" | head -n 5

echo ""
echo "---- awk '{print \$NF}' access.log（最后一列 User-Agent）----"
awk '{print $NF}' "$ACCESS_LOG" | head -n 3

echo ""
echo "---- awk '{print NR, \$1}' access.log（行号 + IP）----"
awk '{print NR, $1}' "$ACCESS_LOG" | head -n 5

echo ""
echo "---- awk '{print NF}' access.log（每行字段数）----"
awk '{print NF}' "$ACCESS_LOG" | head -n 3

# === 2. awk -F 指定分隔符 ===
echo ""
echo ">>> [2] awk -F 指定分隔符..."

echo "---- awk -F: '{print \$1}' users.txt（用户名）----"
awk -F: '{print $1}' "$WORK_DIR/users.txt"

echo ""
echo "---- awk -F: '{print \$1, \$3, \$6}' users.txt（用户名 + UID + 家目录）----"
awk -F: '{print $1, $3, $6}' "$WORK_DIR/users.txt"

echo ""
echo "---- awk -F, '{print \$1, \$2, \$4}' sales.csv（CSV 日期 + 商品 + 价格）----"
awk -F, '{print $1, $2, $4}' "$WORK_DIR/sales.csv"

echo ""
echo "---- awk 'BEGIN{FS=\":\"; OFS=\" | \"} {print \$1, \$3, \$7}' users.txt（自定义输出分隔符）----"
awk 'BEGIN{FS=":"; OFS=" | "} {print $1, $3, $7}' "$WORK_DIR/users.txt"

# === 3. awk BEGIN / END 块 ===
echo ""
echo ">>> [3] awk BEGIN / END 块..."

echo "---- awk 'BEGIN{print \"=== 用户列表 ===\"} {print \$1} END{print \"=== 共 \" NR \" 行 ===\"}' users.txt ----"
awk -F: 'BEGIN{print "=== 用户列表 ==="} {print $1} END{print "=== 共 " NR " 行 ==="}' "$WORK_DIR/users.txt"

echo ""
echo "---- awk 'BEGIN{print \"开始统计\"} {sum+=\$1} END{print \"总和: \" sum}' numbers.txt ----"
awk 'BEGIN{print "开始统计"} {sum+=$1} END{print "总和: " sum}' "$WORK_DIR/numbers.txt"

echo ""
echo "---- awk '{sum+=\$1; count++} END{print \"总和: \" sum; print \"个数: \" count; print \"平均: \" sum/count}' numbers.txt ----"
awk '{sum+=$1; count++} END{print "总和: " sum; print "个数: " count; print "平均: " sum/count}' "$WORK_DIR/numbers.txt"

echo ""
echo "---- awk 'END{print \"总行数: \" NR}' access.log ----"
awk 'END{print "总行数: " NR}' "$ACCESS_LOG"

# === 4. awk NR / NF 变量 ===
echo ""
echo ">>> [4] awk NR / NF 变量..."

echo "---- awk 'NR==1' access.log（仅第 1 行）----"
awk 'NR==1' "$ACCESS_LOG"

echo ""
echo "---- awk 'NR>1' sales.csv（跳过标题行）----"
awk -F, 'NR>1' "$WORK_DIR/sales.csv"

echo ""
echo "---- awk 'NR<=3' access.log（前 3 行）----"
awk 'NR<=3' "$ACCESS_LOG"

echo ""
echo "---- awk 'NR>=5 && NR<=8' access.log（第 5-8 行）----"
awk 'NR>=5 && NR<=8' "$ACCESS_LOG"

echo ""
echo "---- awk '{print NR \": \" NF \" 个字段\"}' access.log（行号 + 字段数，前 3 行）----"
awk '{print NR ": " NF " 个字段"}' "$ACCESS_LOG" | head -n 3

echo ""
echo "---- awk 'END{print \"字段数最多的行: \" maxNF}' access.log（最大字段数）----"
awk '{if(NF>maxNF) maxNF=NF} END{print "最大字段数: " maxNF}' "$ACCESS_LOG"

# === 5. awk 条件过滤 ===
echo ""
echo ">>> [5] awk 条件过滤..."

echo "---- awk '\$9==404' access.log（404 状态码）----"
awk '$9==404' "$ACCESS_LOG"

echo ""
echo "---- awk '\$9>=400' access.log（所有 4xx 和 5xx 错误）----"
awk '$9>=400' "$ACCESS_LOG"

echo ""
echo "---- awk '\$9==200' access.log（200 状态码，前 3 行）----"
awk '$9==200' "$ACCESS_LOG" | head -n 3

echo ""
echo "---- awk '\$1==\"192.168.1.10\"' access.log（特定 IP 的请求）----"
awk '$1=="192.168.1.10"' "$ACCESS_LOG"

echo ""
echo "---- awk 'NF>10' access.log（字段数大于 10 的行，前 3 行）----"
awk 'NF>10' "$ACCESS_LOG" | head -n 3

echo ""
echo "---- awk -F, '\$4>5000' sales.csv（价格大于 5000 的商品）----"
awk -F, '$4>5000' "$WORK_DIR/sales.csv"

echo ""
echo "---- awk -F: '\$3>=1000' users.txt（UID >= 1000 的普通用户）----"
awk -F: '$3>=1000' "$WORK_DIR/users.txt"

# === 6. awk 正则匹配 ===
echo ""
echo ">>> [6] awk 正则匹配..."

echo "---- awk '/404/' access.log（含 404 的行，等同 grep）----"
awk '/404/' "$ACCESS_LOG"

echo ""
echo "---- awk '\$1 ~ /^192.168.1.1/' access.log（IP 以 192.168.1.1 开头）----"
awk '$1 ~ /^192\.168\.1\.1/' "$ACCESS_LOG"

echo ""
echo "---- awk '\$1 !~ /^192.168.1.10/' access.log（IP 不是 192.168.1.10）----"
awk '$1 !~ /^192\.168\.1\.10/' "$ACCESS_LOG" | head -n 3

echo ""
echo "---- awk '/POST|PUT|DELETE/' access.log（POST/PUT/DELETE 请求）----"
awk '/POST|PUT|DELETE/' "$ACCESS_LOG"

echo ""
echo "---- awk -F, '/iPhone/' sales.csv（iPhone 销售记录）----"
awk -F, '/iPhone/' "$WORK_DIR/sales.csv"

# === 7. awk 求和与统计 ===
echo ""
echo ">>> [7] awk 求和与统计..."

echo "---- awk '{sum+=\$10} END{print \"总流量: \" sum \" 字节\"}' access.log ----"
awk '{sum+=$10} END{print "总流量: " sum " 字节 (" sum/1024 " KB)"}' "$ACCESS_LOG"

echo ""
echo "---- awk -F, 'NR>1{sum+=\$3*\$4} END{print \"总销售额: \" sum \" 元\"}' sales.csv ----"
awk -F, 'NR>1{sum+=$3*$4} END{print "总销售额: " sum " 元"}' "$WORK_DIR/sales.csv"

echo ""
echo "---- awk -F, 'NR>1{sum+=\$3*\$4} END{print \"平均单笔: \" sum/(NR-1) \" 元\"}' sales.csv ----"
awk -F, 'NR>1{sum+=$3*$4} END{print "平均单笔: " sum/(NR-1) " 元"}' "$WORK_DIR/sales.csv"

echo ""
echo "---- awk '{sum+=\$1; if(\$1>max) max=\$1; if(min==\"\"||\$1<min) min=\$1} END{print \"总和:\"sum, \"最大:\"max, \"最小:\"min, \"平均:\"sum/NR}' numbers.txt ----"
awk '{sum+=$1; if($1>max) max=$1; if(min==""||$1<min) min=$1} END{print "总和:"sum, "最大:"max, "最小:"min, "平均:"sum/NR}' "$WORK_DIR/numbers.txt"

echo ""
echo "---- awk -F, 'NR>1{count[\$2]++} END{for(p in count) print count[p], p}' sales.csv（每商品销售次数）----"
awk -F, 'NR>1{count[$2]++} END{for(p in count) print count[p], p}' "$WORK_DIR/sales.csv" | sort -rn

# === 8. awk 数组统计 ===
echo ""
echo ">>> [8] awk 数组统计（关联数组）..."

echo "---- 统计每个 IP 的访问次数（Top 5）----"
awk '{count[$1]++} END{for(ip in count) print count[ip], ip}' "$ACCESS_LOG" | sort -rn | head -n 5

echo ""
echo "---- 统计各 HTTP 状态码出现次数 ----"
awk '{count[$9]++} END{for(code in count) print code, count[code]}' "$ACCESS_LOG" | sort

echo ""
echo "---- 统计每个城市的销售额 ----"
awk -F, 'NR>1{sum[$5]+=$3*$4} END{for(city in sum) print city, sum[city] " 元"}' "$WORK_DIR/sales.csv" | sort

echo ""
echo "---- 统计每个商品的销售数量 ----"
awk -F, 'NR>1{sum[$2]+=$3} END{for(p in sum) print sum[p], p}' "$WORK_DIR/sales.csv" | sort -rn

echo ""
echo "---- 统计每个商品的销售额 ----"
awk -F, 'NR>1{sum[$2]+=$3*$4} END{for(p in sum) print sum[p], p}' "$WORK_DIR/sales.csv" | sort -rn

echo ""
echo "---- 统计每个用户的 Shell 类型 ----"
awk -F: '{count[$7]++} END{for(shell in count) print count[shell], shell}' "$WORK_DIR/users.txt"

# === 9. awk printf 格式化输出 ===
echo ""
echo ">>> [9] awk printf 格式化输出..."

echo "---- awk '{printf \"%-4d %s\\n\", NR, \$1}' access.log（行号左对齐 4 字符）----"
awk '{printf "%-4d %s\n", NR, $1}' "$ACCESS_LOG" | head -n 5

echo ""
echo "---- awk -F: '{printf \"用户: %-12s UID: %5d Shell: %s\\n\", \$1, \$3, \$7}' users.txt ----"
awk -F: '{printf "用户: %-12s UID: %5d Shell: %s\n", $1, $3, $7}' "$WORK_DIR/users.txt"

echo ""
echo "---- awk -F, 'NR>1{printf \"%-12s 数量:%3d 单价:%6d 小计:%8d\\n\", \$2, \$3, \$4, \$3*\$4}' sales.csv ----"
awk -F, 'NR>1{printf "%-12s 数量:%3d 单价:%6d 小计:%8d\n", $2, $3, $4, $3*$4}' "$WORK_DIR/sales.csv"

echo ""
echo "---- awk -F, 'NR>1{sum[\$2]+=\$3*\$4} END{printf \"%-15s %10s\\n\", \"商品\", \"销售额\"; for(p in sum) printf \"%-15s %10d\\n\", p, sum[p]}' sales.csv ----"
awk -F, 'NR>1{sum[$2]+=$3*$4} END{printf "%-15s %10s\n", "商品", "销售额"; for(p in sum) printf "%-15s %10d\n", p, sum[p]}' "$WORK_DIR/sales.csv"

# === 10. awk 分析 Nginx 访问日志（综合实战）===
echo ""
echo ">>> [10] awk 综合实战：分析 Nginx 访问日志..."

echo "---- 报表标题 ----"
awk 'BEGIN{
    printf "================================================\n"
    printf "          Nginx 访问日志分析报表\n"
    printf "================================================\n"
}' "$ACCESS_LOG"

echo ""
echo "---- 1. 总请求数 ----"
awk 'END{print "总请求数:", NR}' "$ACCESS_LOG"

echo ""
echo "---- 2. 状态码分布 ----"
awk '{
    count[$9]++
} END {
    printf "  状态码  次数  占比\n"
    printf "  ------  ----  ----\n"
    for (code in count) {
        printf "  %6s  %4d  %.1f%%\n", code, count[code], count[code]/NR*100
    }
}' "$ACCESS_LOG" | sort

echo ""
echo "---- 3. Top 5 访问 IP ----"
awk '{
    count[$1]++
} END {
    printf "  排名  IP              次数\n"
    printf "  ----  --------------  ----\n"
    for (ip in count) {
        printf "%s %d\n", count[ip], ip
    }
}' "$ACCESS_LOG" | sort -rn | head -n 5 | awk '{printf "  #%d   %s  %d\n", NR, $2, $1}'

echo ""
echo "---- 4. 请求方法分布 ----"
awk -F'"' '{
    split($2, method, " ")
    count[method[1]]++
} END {
    for (m in count) print "  ", m, count[m], "次"
}' "$ACCESS_LOG"

echo ""
echo "---- 5. 总流量统计 ----"
awk '{
    sum += $10
} END {
    printf "  总流量: %d 字节 (%.2f KB, %.2f MB)\n", sum, sum/1024, sum/1024/1024
    printf "  平均每请求: %.0f 字节\n", sum/NR
}' "$ACCESS_LOG"

echo ""
echo "---- 6. 错误请求详情（4xx/5xx）----"
awk '$9>=400 {
    printf "  [%s] %s %s → %s ( %s 字节)\n", $9, $1, $6, $7, $10
}' "$ACCESS_LOG"

# === 11. awk 高级用法 ===
echo ""
echo ">>> [11] awk 高级用法..."

echo "---- awk 多条件组合 ----"
awk '$9==200 && $1=="192.168.1.10"' "$ACCESS_LOG" | head -n 3
echo "    （192.168.1.10 的 200 响应请求）"

echo ""
echo "---- awk 范围模式（/start/,/end/）----"
awk '/192.168.1.30/,/192.168.1.40/' "$ACCESS_LOG"
echo "    （从 192.168.1.30 到 192.168.1.40 之间的行）"

echo ""
echo "---- awk 多文件处理（FNR vs NR）----"
awk '{
    print FILENAME ":" FNR ":" $1
}' "$WORK_DIR/numbers.txt" "$WORK_DIR/users.txt" | head -n 5

echo ""
echo "---- awk gsub 全局替换 ----"
awk '{gsub(/192\.168/, "10.0"); print}' "$ACCESS_LOG" | head -n 3

echo ""
echo "---- awk 条件赋值 ----"
awk -F, 'NR>1{
    if ($3*$4 > 20000) grade = "高价值"
    else if ($3*$4 > 5000) grade = "中价值"
    else grade = "低价值"
    printf "%-12s %8d  %s\n", $2, $3*$4, grade
}' "$WORK_DIR/sales.csv"

echo ""
echo "================================================"
echo "  awk 演示完成！"
echo "  素材保留在：$WORK_DIR"
echo "  清理：rm -rf $WORK_DIR"
echo "================================================"
