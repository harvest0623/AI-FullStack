#!/bin/bash
# 文件用途：算术运算与输入练习——$(())/$[]/expr/let、自增自减、read -p/-s/-t、echo -e、printf
# 语法：bash 04-arithmetic-read.sh
# 场景：电商项目统计、用户交互输入、格式化输出报表

# ============================================================
# 一、算术运算
# ============================================================
echo "========== 算术运算 =========="

A=10
B=3
echo "A=$A, B=$B"

# 1. $(()) 推荐
echo ""
echo "--- \$((expr)) 推荐 ---"
echo "A+B = $((A + B))        # 加"
echo "A-B = $((A - B))        # 减"
echo "A*B = $((A * B))        # 乘"
echo "A/B = $((A / B))        # 除（整数，截断小数）"
echo "A%B = $((A % B))        # 取余"
echo "A**2 = $((A ** 2))      # 幂"

# 2. $[] 旧语法
echo ""
echo "--- \$[expr] 旧语法 ---"
echo "A+B = $[A + B]"
echo "A*B = $[A * B]"

# 3. expr（需空格，乘号要转义）
echo ""
echo "--- expr（需空格）---"
echo "A+B = $(expr $A + $B)"
echo "A-B = $(expr $A - $B)"
echo "A*B = $(expr $A \* $B)      # 乘号必须转义"
echo "A/B = $(expr $A / $B)"
echo "A%B = $(expr $A % $B)"

# 4. let
echo ""
echo "--- let ---"
let RESULT=A+B
echo "let RESULT=A+B => $RESULT"
let "RESULT = A * B"
echo "let RESULT=A*B => $RESULT"

# 5. 自增自减
echo ""
echo "--- 自增自减 ---"
COUNT=0
((COUNT++))
echo "COUNT++ => $COUNT"
((COUNT++))
echo "COUNT++ => $COUNT"
((COUNT--))
echo "COUNT-- => $COUNT"

# 6. 浮点运算需借助 bc
echo ""
echo "--- 浮点运算（借助 bc）---"
echo "10/3 = $(echo "scale=2; 10/3" | bc)        # scale=2 保留2位小数"
echo "10/3 = $(echo "scale=4; 10/3" | bc)        # scale=4 保留4位小数"

# ============================================================
# 二、read 读取输入
# ============================================================
echo ""
echo "========== read 读取输入 =========="

# 1. 基本读取（演示用 here-doc 传入，避免交互卡住）
echo ""
echo "--- read 基本读取（用管道模拟用户输入）---"
echo "ecommerce" | while read PROJECT_NAME; do
    echo "读到的项目名：$PROJECT_NAME"
done

# 2. read -p 带提示（真实交互，注释掉避免脚本阻塞）
# read -p "请输入项目名: " PROJECT_NAME
# echo "你输入的是：$PROJECT_NAME"

# 3. read -s 静默输入（密码），用管道模拟
echo ""
echo "--- read -s 静默输入（用管道模拟密码）---"
echo "secret123" | while read -s PASSWORD; do
    echo "密码已接收（不回显），长度：${#PASSWORD}"
done

# 4. read -t 超时
echo ""
echo "--- read -t 超时（5秒）---"
echo "（真实交互中：read -t 5 -p '5秒内输入: ' ANS）"
# if read -t 5 -p "5秒内输入: " ANS; then
#     echo "你输入了：$ANS"
# else
#     echo "超时未输入"
# fi

# 5. 读取多个字段
echo ""
echo "--- 读取多个字段 ---"
printf "nginx 80\nmysql 3306\nredis 6379\n" | while read SVC PORT_NUM; do
    echo "  服务 $SVC 监听端口 $PORT_NUM"
done

# ============================================================
# 三、echo 输出
# ============================================================
echo ""
echo "========== echo 输出 =========="

echo "默认换行"
echo -n "不换行 -> "
echo "继续这一行"
echo -e "解析转义：第一行\n第二行\n制表符\t结束"
echo -e "颜色输出（如支持）：\033[32m绿色文字\033[0m"

# ============================================================
# 四、printf 格式化输出
# ============================================================
echo ""
echo "========== printf 格式化输出 =========="

# 1. 基本格式符
echo "--- 基本格式符 ---"
printf "%s 部署在端口 %d\n" "nginx" 80
printf "PI = %.2f\n" 3.14159
printf "十六进制 255 = %x\n" 255

# 2. 对齐表格
echo ""
echo "--- 对齐表格（电商服务清单）---"
printf "%-12s %-8s %-10s %s\n" "服务" "端口" "状态" "备注"
printf "%-12s %-8s %-10s %s\n" "----------" "------" "--------" "----------"
printf "%-12s %-8d %-10s %s\n" "nginx" 80 "running" "Web服务器"
printf "%-12s %-8d %-10s %s\n" "mysql" 3306 "running" "数据库"
printf "%-12s %-8d %-10s %s\n" "redis" 6379 "running" "缓存"
printf "%-12s %-8d %-10s %s\n" "node-app" 3000 "running" "后端应用"

# 3. 数字对齐
echo ""
echo "--- 数字右对齐 ---"
for n in 1 23 456 7890; do
    printf "%8d\n" "$n"
done

# 4. 浮点对齐
echo ""
echo "--- 浮点对齐 ---"
printf "%-10s %10.2f\n" "收入" 12345.678
printf "%-10s %10.2f\n" "支出" 9876.5
printf "%-10s %10.2f\n" "利润" 2469.178

echo ""
echo "算术运算与输入输出练习完毕。"
