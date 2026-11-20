#!/bin/bash
# 文件用途：字符串与数组练习——长度/截取/替换/删除/大小写、普通数组、关联数组
# 语法：bash 03-string-array.sh
# 场景：处理电商项目的服务名、端口、日志路径等字符串与数据结构

# ============================================================
# 一、字符串操作
# ============================================================
echo "========== 字符串操作 =========="

STR="Hello, ecommerce World, hello Shell"
echo "原字符串：$STR"
echo "长度 \${#STR}：${#STR}"

# 1. 截取
echo ""
echo "--- 截取 ---"
echo "从0取5 \${STR:0:5}：${STR:0:5}"
echo "从7取到末尾 \${STR:7}：${STR:7}"
echo "从7取10 \${STR:7:10}：${STR:7:10}"

# 2. 替换
echo ""
echo "--- 替换 ---"
echo "替换第一个 hello \${STR/hello/Hi}：${STR/hello/Hi}"
echo "替换所有 hello \${STR//hello/Hi}：${STR//hello/Hi}"

# 3. 删除（模式匹配，常用于处理文件名/路径）
echo ""
echo "--- 删除（模式匹配）---"
PATH_EXAMPLE="/opt/ecommerce/logs/access.log"
echo "原路径：$PATH_EXAMPLE"
echo "头部删最短 \${PATH_EXAMPLE#*/}：${PATH_EXAMPLE#*/}        # 删第一个 /"
echo "头部删最长 \${PATH_EXAMPLE##*/}：${PATH_EXAMPLE##*/}      # 删到最后一个 /，得到文件名"
echo "尾部删最短 \${PATH_EXAMPLE%.log}：${PATH_EXAMPLE%.log}    # 删 .log 后缀"
echo "尾部删最长 \${PATH_EXAMPLE%%.*}：${PATH_EXAMPLE%%.*}      # 删第一个点之后所有"

# 4. 大小写转换
echo ""
echo "--- 大小写 ---"
echo "全大写 \${STR^^}：${STR^^}"
echo "全小写 \${STR,,}：${STR,,}"
echo "首字母大写 \${STR^}：${STR^}"

# 5. 默认值
echo ""
echo "--- 默认值 ---"
LOG_DIR=""                                   # 空值
echo "空值时默认 \${LOG_DIR:-/var/log}：${LOG_DIR:-/var/log}    # 不赋值，仅使用"
echo "LOG_DIR 仍为空：[$LOG_DIR]"
echo "空值时赋值 \${LOG_DIR:=/var/log}：${LOG_DIR:=/var/log}    # 赋值并使用"
echo "LOG_DIR 已被赋值：$LOG_DIR"

# ============================================================
# 二、普通数组
# ============================================================
echo ""
echo "========== 普通数组 =========="

# 1. 定义
SERVICES=("nginx" "mysql" "redis")
SERVICES[3]="pm2"           # 追加元素
SERVICES+=("node")          # 末尾追加

echo "数组所有元素 \${SERVICES[@]}：${SERVICES[@]}"
echo "数组长度 \${#SERVICES[@]}：${#SERVICES[@]}"
echo "第一个元素 \${SERVICES[0]}：${SERVICES[0]}"
echo "切片（从1取2个）\${SERVICES[@]:1:2}：${SERVICES[@]:1:2}"

# 2. 遍历
echo ""
echo "--- 遍历普通数组 ---"
for svc in "${SERVICES[@]}"; do
    echo "  服务：$svc"
done

# 3. 带索引遍历
echo ""
echo "--- 带索引遍历 ---"
for i in "${!SERVICES[@]}"; do
    echo "  [$i] = ${SERVICES[$i]}"
done

# ============================================================
# 三、关联数组（declare -A）
# ============================================================
echo ""
echo "========== 关联数组 =========="

# 必须先 declare -A 声明
declare -A PORTS
PORTS["nginx"]=80
PORTS["mysql"]=3306
PORTS["redis"]=6379
PORTS["node"]=3000

# 1. 访问
echo "nginx 端口：${PORTS['nginx']}"
echo "mysql 端口：${PORTS['mysql']}"

# 2. 长度
echo "关联数组长度 \${#PORTS[@]}：${#PORTS[@]}"

# 3. 遍历所有 key
echo ""
echo "--- 遍历所有 key ---"
for key in "${!PORTS[@]}"; do
    echo "  $key -> ${PORTS[$key]}"
done

# 4. 遍历所有 value
echo ""
echo "--- 遍历所有 value ---"
for val in "${PORTS[@]}"; do
    echo "  port=$val"
done

# ============================================================
# 四、实战：电商服务清单
# ============================================================
echo ""
echo "========== 实战：电商服务清单 =========="

declare -A SVC_INFO
SVC_INFO["nginx"]="80:web服务器"
SVC_INFO["mysql"]="3306:数据库"
SVC_INFO["redis"]="6379:缓存"
SVC_INFO["node"]="3000:后端应用"

printf "%-10s %-8s %s\n" "服务" "端口" "说明"
printf "%-10s %-8s %s\n" "----" "----" "----"
for svc in "${!SVC_INFO[@]}"; do
    info="${SVC_INFO[$svc]}"
    port="${info%%:*}"
    desc="${info#*:}"
    printf "%-10s %-8s %s\n" "$svc" "$port" "$desc"
done

echo ""
echo "字符串与数组练习完毕。"
