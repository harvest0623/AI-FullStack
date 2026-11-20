#!/bin/bash
# ============================================================
# 文件名：03-functions.sh
# 用途：函数练习——定义/调用/参数/返回值/局部变量 local/递归/echo+$()
# 场景：电商项目运维脚本中的函数封装
# 语法：bash 03-functions.sh
# ============================================================

echo "========== Day10 - 03 函数练习 =========="

# ============================================================
# 一、函数定义与调用
# ============================================================
echo ""
echo "---------- 一、函数定义与调用 ----------"

# 写法一：function 关键字
function greet() {
    echo "Hello, $1! 欢迎使用电商运维脚本。"
}

# 写法二：省略 function（推荐，POSIX 兼容）
show_version() {
    echo "脚本版本：1.0.0"
    echo "项目：ecommerce"
}

# 调用（参数用空格分隔，不加括号）
greet "admin"
greet "developer"
show_version

# ============================================================
# 二、函数参数
# ============================================================
echo ""
echo "---------- 二、函数参数 ----------"

show_info() {
    echo "  脚本名 \$0：$0"
    echo "  函数内 \$1：$1"
    echo "  函数内 \$2：$2"
    echo "  参数个数 \$#：$#"
    echo "  所有参数 \$@：$@"
}

echo "调用 show_info nginx 3306："
show_info nginx 3306

echo ""
echo "调用 show_info a b c d："
show_info a b c d

# ============================================================
# 三、返回值：退出码 return
# ============================================================
echo ""
echo "---------- 三、返回值：退出码 return ----------"

# 判断是否 root
is_root() {
    if [[ $UID -eq 0 ]]; then
        return 0      # 成功
    else
        return 1      # 失败
    fi
}

# 判断端口是否在监听
is_port_listening() {
    local port=$1
    if ss -tln 2>/dev/null | grep -q ":$port "; then
        return 0
    else
        return 1
    fi
}

# 用 if 调用
if is_root; then
    echo "当前是 root 用户"
else
    echo "当前不是 root 用户（UID=$UID）"
fi

# 用 && || 调用
is_port_listening 22 && echo "端口 22 在监听" || echo "端口 22 未监听"
is_port_listening 80 && echo "端口 80 在监听" || echo "端口 80 未监听"

# ============================================================
# 四、返回值：字符串 echo + $()
# ============================================================
echo ""
echo "---------- 四、返回值：字符串 echo + $() ----------"

# 拼接服务信息
format_service() {
    local name=$1
    local port=$2
    local desc=${3:-未命名}
    echo "$name:$port:$desc"
}

result=$(format_service "nginx" "80" "Web服务器")
echo "返回值：$result"

# 获取当前日期时间字符串
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

ts=$(get_timestamp)
echo "时间戳：$ts"

# 计算两个数之和
add() {
    local a=$1
    local b=$2
    echo $((a + b))
}

sum=$(add 10 20)
echo "10 + 20 = $sum"

# ============================================================
# 五、局部变量 local
# ============================================================
echo ""
echo "---------- 五、局部变量 local ----------"

counter=100      # 全局变量

# 不用 local（会污染全局）
inc_global() {
    counter=200
    echo "  函数内 counter=$counter"
}

# 用 local（不影响全局）
inc_local() {
    local counter=300
    echo "  函数内 counter=$counter（local）"
}

echo "调用前 counter=$counter"
inc_global
echo "inc_global 后 counter=$counter（被修改了！）"
inc_local
echo "inc_local 后 counter=$counter（local 不影响全局）"

# ============================================================
# 六、递归调用
# ============================================================
echo ""
echo "---------- 六、递归调用 ----------"

# 阶乘
factorial() {
    local n=$1
    if [[ $n -le 1 ]]; then
        echo 1
    else
        local prev
        prev=$(factorial $((n - 1)))
        echo $((n * prev))
    fi
}

for n in 1 2 3 4 5 6 7 8; do
    echo "  $n! = $(factorial $n)"
done

# 斐波那契数列
fib() {
    local n=$1
    if [[ $n -le 0 ]]; then
        echo 0
    elif [[ $n -eq 1 ]]; then
        echo 1
    else
        local a b
        a=$(fib $((n - 1)))
        b=$(fib $((n - 2)))
        echo $((a + b))
    fi
}

echo ""
echo "斐波那契数列前 10 项："
for i in {0..9}; do
    echo -n "$(fib $i) "
done
echo ""

# ============================================================
# 七、函数综合实战
# ============================================================
echo ""
echo "---------- 七、函数综合实战 ----------"

# 日志函数
log() {
    local level=$1
    shift
    local msg="$*"
    local ts
    ts=$(date '+%F %T')
    case "$level" in
        INFO)  echo "[$ts] [INFO]  $msg" ;;
        WARN)  echo "[$ts] [WARN]  $msg" ;;
        ERROR) echo "[$ts] [ERROR] $msg" ;;
        *)     echo "[$ts] [????]  $msg" ;;
    esac
}

# 检查服务状态
check_service() {
    local svc=$1
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        log INFO "服务 $svc 运行正常"
        return 0
    else
        log WARN "服务 $svc 未运行"
        return 1
    fi
}

# 批量检查
log INFO "开始服务巡检..."
services=("ssh" "nginx" "mysql" "redis")
for svc in "${services[@]}"; do
    check_service "$svc"
done
log INFO "服务巡检完成"

echo ""
echo "函数练习完毕。"
