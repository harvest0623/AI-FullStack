#!/bin/bash
# ============================================================
# 文件名：02-loops.sh
# 用途：循环练习——for/while/until/select、break/continue、while read line
# 场景：电商项目批量处理服务、遍历日志文件
# 语法：bash 02-loops.sh
# ============================================================

echo "========== Day10 - 02 循环练习 =========="

# ============================================================
# 一、for in 列表
# ============================================================
echo ""
echo "---------- 一、for in 列表 ----------"

# 1. 空格分隔的值
echo "--- 遍历服务列表 ---"
for svc in nginx mysql redis pm2; do
    echo "  服务：$svc"
done

# 2. 命令替换
echo ""
echo "--- 遍历 /opt 下的目录（命令替换）---"
for dir in $(ls /opt 2>/dev/null); do
    echo "  /opt/$dir"
done

# 3. 数组
echo ""
echo "--- 遍历数组 ---"
services=("nginx" "mysql" "redis" "node")
for svc in "${services[@]}"; do
    echo "  数组元素：$svc"
done

# 4. seq 命令
echo ""
echo "--- seq 生成序列 ---"
for i in $(seq 1 5); do
    echo "  第 $i 次"
done

# 5. 花括号展开
echo ""
echo "--- 花括号展开 ---"
for n in {1..5}; do
    echo "  n=$n"
done
for c in {a..e}; do
    echo "  c=$c"
done

# ============================================================
# 二、C 风格 for
# ============================================================
echo ""
echo "---------- 二、C 风格 for ----------"

for ((i=0; i<5; i++)); do
    echo "  i = $i"
done

echo ""
echo "--- 倒序 ---"
for ((i=10; i>=0; i-=2)); do
    echo "  i = $i"
done

echo ""
echo "--- 双变量 ---"
for ((i=0, j=10; i<5; i++, j--)); do
    echo "  i=$i, j=$j"
done

# ============================================================
# 三、while 循环
# ============================================================
echo ""
echo "---------- 三、while 循环 ----------"

count=0
while [[ $count -lt 5 ]]; do
    echo "  count = $count"
    ((count++))
done

# while 读用户输入（用管道模拟）
echo ""
echo "--- while 读输入（模拟）---"
printf "nginx\nmysql\nredis\n" | while read line; do
    echo "  读到：$line"
done

# ============================================================
# 四、until 循环
# ============================================================
echo ""
echo "---------- 四、until 循环 ----------"

count=0
until [[ $count -ge 5 ]]; do
    echo "  count = $count（until 条件为假时循环）"
    ((count++))
done

# ============================================================
# 五、break 与 continue
# ============================================================
echo ""
echo "---------- 五、break 与 continue ----------"

echo "--- break 跳出循环 ---"
for i in {1..10}; do
    [[ $i -eq 5 ]] && break
    echo "  i=$i"
done
echo "  break 后 i=$i"

echo ""
echo "--- continue 跳过本次 ---"
for i in {1..6}; do
    [[ $((i % 2)) -eq 0 ]] && continue
    echo "  奇数：$i"
done

echo ""
echo "--- 嵌套循环 break 2 跳出多层 ---"
for i in {1..3}; do
    for j in {1..3}; do
        [[ $i -eq 2 && $j -eq 2 ]] && break 2
        echo "  i=$i, j=$j"
    done
done

# ============================================================
# 六、while read line 遍历文件
# ============================================================
echo ""
echo "---------- 六、while read line 遍历文件 ----------"

# 创建测试文件
TEST_FILE="/tmp/ecommerce_services.txt"
cat > "$TEST_FILE" <<EOF
nginx 80 web服务器
mysql 3306 数据库
redis 6379 缓存服务
node 3000 后端应用
EOF

echo "测试文件内容：$TEST_FILE"
echo "--- 逐行读取（标准写法 IFS= read -r）---"
while IFS= read -r line; do
    echo "  行内容：$line"
done < "$TEST_FILE"

echo ""
echo "--- 按字段读取 ---"
while read svc port desc; do
    printf "  服务=%-8s 端口=%-6s 说明=%s\n" "$svc" "$port" "$desc"
done < "$TEST_FILE"

# 清理测试文件
rm -f "$TEST_FILE"

# ============================================================
# 七、select 菜单
# ============================================================
echo ""
echo "---------- 七、select 交互菜单 ----------"

# select 是交互式的，这里用管道模拟输入
echo "（真实交互中会显示菜单，这里用管道模拟选择）"
echo "1" | {
    PS3="请选择要检查的服务: "
    select svc in nginx mysql redis 退出; do
        case "$svc" in
            nginx|mysql|redis)
                echo "  你选择了检查 $svc"
                ;;
            退出)
                echo "  退出菜单"
                break
                ;;
            *)
                echo "  无效选择"
                ;;
        esac
        break   # 模拟环境下只执行一次
    done
}

# ============================================================
# 八、实战：批量检查服务状态
# ============================================================
echo ""
echo "---------- 八、实战：批量检查服务状态 ----------"

services=("nginx" "mysql" "redis" "ssh")

printf "%-10s %-10s %s\n" "服务" "状态" "说明"
printf "%-10s %-10s %s\n" "------" "------" "----"

for svc in "${services[@]}"; do
    # 用 systemctl 检查（非 root 也可查询）
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        status="running"
    elif systemctl is-active --quiet "${svc}d" 2>/dev/null; then
        status="running"
    else
        status="stopped"
    fi

    case "$svc" in
        nginx)  desc="Web 服务器" ;;
        mysql)  desc="数据库" ;;
        redis)  desc="缓存" ;;
        ssh)    desc="远程登录" ;;
        *)      desc="未知" ;;
    esac

    printf "%-10s %-10s %s\n" "$svc" "$status" "$desc"
done

echo ""
echo "循环练习完毕。"
