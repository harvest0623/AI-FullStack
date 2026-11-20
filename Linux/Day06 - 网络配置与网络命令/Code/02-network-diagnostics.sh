#!/bin/bash
# ============================================================
# 文件名：02-network-diagnostics.sh
# 用途：演示网络诊断：ping/telnet/nc 端口测试、traceroute/mtr、
#       nslookup/dig DNS 查询、ss/netstat/lsof 端口查看
# 适用：Ubuntu 22.04 LTS
# 场景：电商项目服务器网络故障排查（端口不通/DNS 失败等）
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day06 - 02 网络诊断演示"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"

# 测试目标（可改成实际服务器）
TARGET_HOST="8.8.8.8"
TARGET_DOMAIN="www.baidu.com"
LOCAL_SERVICES=(22 80 443 3306 6379)

# ---------- 1. ping 连通性测试 ----------

echo -e "\n[1] ping —— 测试网络连通性"
echo "命令：ping -c 4 -W 2 $TARGET_HOST"
ping -c 4 -W 2 "$TARGET_HOST" 2>&1 || echo "（ping 失败，可能是 ICMP 被防火墙拦截）"

echo -e "\n[2] ping 域名 —— 同时验证 DNS 解析"
echo "命令：ping -c 3 $TARGET_DOMAIN"
ping -c 3 "$TARGET_DOMAIN" 2>&1 || echo "（域名解析或网络有问题）"

# ---------- 2. telnet 端口测试 ----------

echo -e "\n[3] telnet —— 测试 TCP 端口连通性（已过时但简单）"
if command -v telnet >/dev/null 2>&1; then
    echo "命令：echo '' | timeout 3 telnet $TARGET_DOMAIN 80"
    echo "" | timeout 3 telnet "$TARGET_DOMAIN" 80 2>&1 | head -n 5
    echo "Connected 表示端口通；Connection refused 表示端口未监听；超时表示被防火墙拦截"
else
    echo "未安装 telnet，可执行：sudo apt install -y telnet"
fi

# ---------- 3. nc 端口扫描 ----------

echo -e "\n[4] nc (netcat) —— 端口扫描（推荐）"
if command -v nc >/dev/null 2>&1; then
    echo "命令：nc -zv $TARGET_DOMAIN 80 443 2>&1"
    nc -zv "$TARGET_DOMAIN" 80 443 2>&1
    echo ""
    echo "命令：nc -zv 127.0.0.1 ${LOCAL_SERVICES[*]} 2>&1  # 扫描本机端口"
    nc -zv 127.0.0.1 "${LOCAL_SERVICES[@]}" 2>&1
    echo ""
    echo "命令：nc -zv 127.0.0.1 20-30 2>&1  # 扫描端口范围"
    nc -zv 127.0.0.1 20-30 2>&1 | head -n 5
else
    echo "未安装 nc，可执行：sudo apt install -y netcat-openbsd"
fi

echo -e "\n[5] nc 文件传输示例（演示命令，不真实传输）"
cat <<'EOF'
# 接收端先监听
nc -l 8080 > received-file.txt

# 发送端连接并发送
nc 192.168.1.100 8080 < file-to-send.txt

# 注意：传输完成后两端都需要 Ctrl+C 退出
EOF

# ---------- 4. traceroute / mtr 路由追踪 ----------

echo -e "\n[6] traceroute —— 路由追踪"
if command -v traceroute >/dev/null 2>&1; then
    echo "命令：traceroute -n -m 15 $TARGET_HOST"
    traceroute -n -m 15 "$TARGET_HOST" 2>&1 | head -n 20
else
    echo "未安装 traceroute，可执行：sudo apt install -y traceroute"
fi

echo -e "\n[7] tracepath —— 类似 traceroute，无需 root"
if command -v tracepath >/dev/null 2>&1; then
    echo "命令：tracepath -n $TARGET_HOST | head -n 10"
    tracepath -n "$TARGET_HOST" 2>&1 | head -n 10
else
    echo "未安装 tracepath"
fi

echo -e "\n[8] mtr —— traceroute + ping 持续刷新"
if command -v mtr >/dev/null 2>&1; then
    echo "命令：mtr --report -n $TARGET_HOST  # 报告模式，发 10 个包后退出"
    mtr --report -n "$TARGET_HOST" 2>&1 | head -n 20
else
    echo "未安装 mtr，可执行：sudo apt install -y mtr"
fi

# ---------- 5. DNS 查询 ----------

echo -e "\n[9] nslookup —— 简单 DNS 查询"
if command -v nslookup >/dev/null 2>&1; then
    echo "命令：nslookup $TARGET_DOMAIN"
    nslookup "$TARGET_DOMAIN" 2>&1 | head -n 10
    echo ""
    echo "命令：nslookup $TARGET_DOMAIN 8.8.8.8  # 指定 DNS 服务器"
    nslookup "$TARGET_DOMAIN" 8.8.8.8 2>&1 | head -n 10
else
    echo "未安装 nslookup，可执行：sudo apt install -y dnsutils"
fi

echo -e "\n[10] dig —— 强大的 DNS 工具"
if command -v dig >/dev/null 2>&1; then
    echo "命令：dig $TARGET_DOMAIN"
    dig "$TARGET_DOMAIN" 2>&1 | head -n 20
    echo ""
    echo "命令：dig +short $TARGET_DOMAIN  # 仅返回 IP"
    dig +short "$TARGET_DOMAIN"
    echo ""
    echo "命令：dig $TARGET_DOMAIN MX  # 查询邮件记录"
    dig "$TARGET_DOMAIN" MX +short 2>/dev/null
    echo ""
    echo "命令：dig @8.8.8.8 $TARGET_DOMAIN  # 指定 DNS 服务器"
    dig @8.8.8.8 "$TARGET_DOMAIN" +short 2>&1
else
    echo "未安装 dig，可执行：sudo apt install -y dnsutils"
fi

echo -e "\n[11] host —— 简洁 DNS 查询"
if command -v host >/dev/null 2>&1; then
    echo "命令：host $TARGET_DOMAIN"
    host "$TARGET_DOMAIN" 2>&1 | head -n 5
else
    echo "未安装 host"
fi

# ---------- 6. 端口监听与连接查看 ----------

echo -e "\n[12] ss —— 查看 TCP 监听端口（推荐，替代 netstat）"
echo "命令：ss -tlnp"
ss -tlnp 2>/dev/null | head -n 20
echo ""
echo "字段说明："
echo "  State=LISTEN 表示正在监听"
echo "  Local Address:Port 监听地址端口（127.0.0.1 仅本地；0.0.0.0 全网卡；:: IPv6 全网卡）"
echo "  PID/Program 进程信息（需 root）"

echo -e "\n[13] ss 查看指定端口"
echo "命令：ss -tlnp | grep -E ':80|:3306|:6379'"
ss -tlnp 2>/dev/null | grep -E ':80|:3306|:6379' || echo "（80/3306/6379 端口未监听）"

echo -e "\n[14] ss 查看已建立连接"
echo "命令：ss -tn state established | head -n 10"
ss -tn state established 2>/dev/null | head -n 10

echo -e "\n[15] ss 统计各状态连接数（排查 TIME_WAIT 过多）"
echo "命令：ss -tan | awk '{print \$1}' | sort | uniq -c | sort -rn"
ss -tan 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn

echo -e "\n[16] netstat —— 旧命令（需安装 net-tools）"
if command -v netstat >/dev/null 2>&1; then
    echo "命令：netstat -tlnp | head -n 15"
    netstat -tlnp 2>/dev/null | head -n 15
    echo ""
    echo "命令：netstat -an | grep ESTABLISHED | wc -l  # 已建立连接数"
    netstat -an 2>/dev/null | grep ESTABLISHED | wc -l
else
    echo "未安装 netstat，可执行：sudo apt install -y net-tools"
    echo "现代 Linux 推荐 ss（更高效，无需 root 即可查看基本端口）"
fi

echo -e "\n[17] lsof —— 查看端口占用进程（需 sudo 查看其他用户进程）"
if command -v lsof >/dev/null 2>&1; then
    echo "命令：sudo lsof -i:22  # 谁在监听 22 端口"
    sudo lsof -i:22 2>/dev/null | head -n 10 || lsof -i:22 2>/dev/null | head -n 10
    echo ""
    echo "命令：lsof -i -P -n | head -n 10  # 所有网络连接（-P 端口号 -n 不解析）"
    lsof -i -P -n 2>/dev/null | head -n 10
else
    echo "未安装 lsof，可执行：sudo apt install -y lsof"
fi

echo -e "\n[18] 排查端口不通的标准流程"
cat <<'EOF'
1. 服务端：ss -tlnp | grep :端口    # 确认服务在监听
   - 127.0.0.1:80 → 仅本机可访问
   - 0.0.0.0:80 / *:80 → 对外开放

2. 服务端：curl -v http://127.0.0.1:端口  # 本地能否访问

3. 客户端：nc -zv 服务IP 端口           # 远程能否连通
   - Connection refused → 服务未监听或监听 127.0.0.1
   - 超时 → 防火墙拦截

4. 服务端：sudo ufw status              # 检查防火墙
   sudo ufw allow 80/tcp                # 放行 80 端口

5. 服务端：journalctl -u 服务名 -p err   # 查看服务错误日志
EOF

echo -e "\n============================================================"
echo "  Day06 - 02 网络诊断演示 完成"
echo "============================================================"
