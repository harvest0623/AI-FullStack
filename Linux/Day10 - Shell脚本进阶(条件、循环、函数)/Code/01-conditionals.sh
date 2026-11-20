#!/bin/bash
# ============================================================
# 文件名：01-conditionals.sh
# 用途：条件判断练习——文件/字符串/数值测试、if/case、[[]] vs []
# 场景：电商项目运维中的各种判断逻辑
# 语法：bash 01-conditionals.sh [文件路径]
# ============================================================

echo "========== Day10 - 01 条件判断练习 =========="

# ============================================================
# 一、文件测试
# ============================================================
echo ""
echo "---------- 一、文件测试 ----------"

FILE="${1:-/etc/hostname}"     # 用第一个参数，默认 /etc/hostname

# [ ] 写法
if [ -e "$FILE" ]; then
    echo "[ ] 文件存在：$FILE"
fi

# [[ ]] 写法（推荐）
if [[ -f "$FILE" ]]; then
    echo "[[ ]] 是普通文件：$FILE"
elif [[ -d "$FILE" ]]; then
    echo "[[ ]] 是目录：$FILE"
fi

# 权限测试
[[ -r "$FILE" ]] && echo "可读"
[[ -w "$FILE" ]] && echo "可写"
[[ -x "$FILE" ]] && echo "可执行"

# 非空测试
if [[ -s "$FILE" ]]; then
    echo "文件非空，大小：$(stat -c %s "$FILE") 字节"
fi

# 符号链接测试
[[ -L "$FILE" ]] && echo "是符号链接" || echo "不是符号链接"

# 比较两个文件的新旧
FILE_A="/etc/hostname"
FILE_B="/etc/passwd"
if [[ -f "$FILE_A" && -f "$FILE_B" ]]; then
    if [[ "$FILE_A" -nt "$FILE_B" ]]; then
        echo "$FILE_A 比 $FILE_B 新"
    else
        echo "$FILE_A 不比 $FILE_B 新"
    fi
fi

# ============================================================
# 二、字符串测试
# ============================================================
echo ""
echo "---------- 二、字符串测试 ----------"

STR1="ecommerce"
STR2="ecommerce"
STR3="ECommerce"
EMPTY=""

# 相等
if [[ "$STR1" == "$STR2" ]]; then
    echo "'$STR1' == '$STR2'：相等"
fi

# 不等
if [[ "$STR1" != "$STR3" ]]; then
    echo "'$STR1' != '$STR3'：不等（区分大小写）"
fi

# 空字符串判断
[[ -z "$EMPTY" ]] && echo "EMPTY 变量为空"
[[ -n "$STR1" ]] && echo "STR1 变量非空"

# 模式匹配（glob，仅 [[ ]] 支持）
FILENAME="nginx.conf"
if [[ "$FILENAME" == *.conf ]]; then
    echo "$FILENAME 是配置文件（*.conf 匹配）"
fi

# 字典序比较
if [[ "apple" < "banana" ]]; then
    echo "apple 排在 banana 前面"
fi

# ============================================================
# 三、数值测试
# ============================================================
echo ""
echo "---------- 三、数值测试 ----------"

PORT=80
MAX_PORT=1024
CPU_LOAD=85

# -eq -ne -lt -le -gt -ge
if [[ $PORT -lt $MAX_PORT ]]; then
    echo "端口 $PORT 小于 $MAX_PORT（特权端口）"
fi

if [[ $CPU_LOAD -gt 80 ]]; then
    echo "CPU 负载 $CPU_LOAD% 超过 80% 阈值！"
elif [[ $CPU_LOAD -ge 50 ]]; then
    echo "CPU 负载 $CPU_LOAD% 中等"
else
    echo "CPU 负载 $CPU_LOAD% 正常"
fi

# [[ ]] 中也可直接用 > < >= <= 比较数值（算术比较）
if [[ $PORT -eq 80 ]]; then
    echo "端口是 80"
fi

# ============================================================
# 四、[ ] vs [[ ]] 对比
# ============================================================
echo ""
echo "---------- 四、[ ] vs [[ ]] 对比 ----------"

VAR=""

# [ ] 中变量为空需加引号，否则报错
# 错误写法：[ $VAR = "" ]  → [ = "" ] 语法错误
# 正确写法：
if [ -z "$VAR" ]; then
    echo "[ ] 用 -z 判空：VAR 为空"
fi

# [[ ]] 中变量为空也安全
if [[ -z $VAR ]]; then
    echo "[[ ]] 用 -z 判空：VAR 为空（无需引号）"
fi

# 逻辑运算对比
A=1
B=2
# [ ] 用 -a -o
if [ $A -eq 1 -a $B -eq 2 ]; then
    echo "[ ] 逻辑与：A==1 且 B==2"
fi
# [[ ]] 用 && ||
if [[ $A -eq 1 && $B -eq 2 ]]; then
    echo "[[ ]] 逻辑与：A==1 且 B==2"
fi

# 命令间用 && ||
[ -f /etc/hostname ] && echo "/etc/hostname 存在" || echo "/etc/hostname 不存在"

# ============================================================
# 五、正则匹配 =~
# ============================================================
echo ""
echo "---------- 五、正则匹配 =~ ----------"

IP="192.168.1.100"
if [[ $IP =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
    echo "'$IP' 符合 IPv4 格式"
fi

# 捕获组
if [[ $IP =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    echo "完整匹配：${BASH_REMATCH[0]}"
    echo "第一段：${BASH_REMATCH[1]}"
    echo "第二段：${BASH_REMATCH[2]}"
fi

# 判断纯数字
NUM="12345"
[[ $NUM =~ ^[0-9]+$ ]] && echo "'$NUM' 是纯数字"

# 判断邮箱
EMAIL="admin@ecommerce.com"
[[ $EMAIL =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]] && echo "'$EMAIL' 是邮箱格式"

# ============================================================
# 六、if-elif-else 实战
# ============================================================
echo ""
echo "---------- 六、if-elif-else 实战 ----------"

# 根据磁盘使用率判断
DISK_USAGE=$(df / | awk 'NR==2 {print int($5)}')
echo "根分区使用率：${DISK_USAGE}%"

if [[ $DISK_USAGE -ge 90 ]]; then
    echo "严重：磁盘使用率 >= 90%，需立即清理！"
elif [[ $DISK_USAGE -ge 80 ]]; then
    echo "警告：磁盘使用率 >= 80%，建议清理"
elif [[ $DISK_USAGE -ge 60 ]]; then
    echo "提示：磁盘使用率 >= 60%，关注"
else
    echo "正常：磁盘使用率 < 60%"
fi

# ============================================================
# 七、case 语句实战
# ============================================================
echo ""
echo "---------- 七、case 语句实战 ----------"

# 模拟服务管理
SERVICE="${2:-nginx}"     # 第二个参数，默认 nginx

case "$SERVICE" in
    nginx|httpd)
        echo "处理 Web 服务：$SERVICE"
        ;;
    mysql|mariadb)
        echo "处理数据库服务：$SERVICE"
        ;;
    redis|memcached)
        echo "处理缓存服务：$SERVICE"
        ;;
    *)
        echo "未知服务：$SERVICE"
        echo "支持：nginx|httpd|mysql|mariadb|redis|memcached"
        ;;
esac

# case 匹配数字范围
HOUR=$(date +%H)
case $HOUR in
    0[0-6])  echo "凌晨时段（$HOUR 时）" ;;
    0[7-9]|1[0-8]) echo "工作时段（$HOUR 时）" ;;
    1[9-9]|2[0-3]) echo "晚间时段（$HOUR 时）" ;;
esac

echo ""
echo "条件判断练习完毕。"
