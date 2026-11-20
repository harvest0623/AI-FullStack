#!/bin/bash
# ============================================================
# 文件名：01-network-config.sh
# 用途：演示 Linux 网络配置：查看 IP/路由、DNS 配置、Netplan 说明、主机名设置
# 适用：Ubuntu 22.04 LTS
# 场景：电商项目服务器（192.168.1.100）网络配置排查
# 注意：含 sudo 的命令需具备 root/sudo 权限
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day06 - 01 网络配置演示"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"

# ---------- 1. 查看 IP 地址 ----------

echo -e "\n[1] ip addr —— 查看所有网络接口与 IP"
echo "命令：ip addr show"
ip addr show
echo ""
echo "说明：现代 Linux 推荐 iproute2 套件（ip 命令）替代旧 net-tools（ifconfig）"

echo -e "\n[2] ip addr show <接口> —— 查看指定接口"
# 自动选择第一个非 lo 接口
IFACE=$(ip -o link show | awk -F': ' '{print $2}' | grep -v '^lo$' | head -n1)
echo "命令：ip addr show $IFACE"
ip addr show "$IFACE"

echo -e "\n[3] 提取本机 IPv4 地址（脚本常用）"
echo "命令：ip -4 addr show $IFACE | grep inet | awk '{print \$2}'"
ip -4 addr show "$IFACE" | grep inet | awk '{print $2}'

echo -e "\n[4] ifconfig —— 旧命令对比（需安装 net-tools）"
if command -v ifconfig >/dev/null 2>&1; then
    echo "命令：ifconfig $IFACE"
    ifconfig "$IFACE"
else
    echo "未安装 net-tools，可执行：sudo apt install -y net-tools"
fi

# ---------- 2. 查看路由表 ----------

echo -e "\n[5] ip route —— 查看路由表"
echo "命令：ip route show"
ip route show
echo ""
echo "说明：default via 192.168.1.1 dev eth0 表示默认网关为 192.168.1.1"

echo -e "\n[6] ip route get —— 查看到某 IP 的路由路径"
echo "命令：ip route get 8.8.8.8"
ip route get 8.8.8.8

# ---------- 3. DNS 配置 ----------

echo -e "\n[7] /etc/resolv.conf —— DNS 服务器配置"
echo "命令：cat /etc/resolv.conf"
cat /etc/resolv.conf
echo ""
echo "注意：Ubuntu 上 /etc/resolv.conf 通常由 systemd-resolved 管理，是符号链接"
ls -l /etc/resolv.conf

echo -e "\n[8] resolvectl status —— 查看 systemd-resolved 状态"
if command -v resolvectl >/dev/null 2>&1; then
    echo "命令：resolvectl status | head -n 20"
    resolvectl status 2>/dev/null | head -n 20
else
    echo "systemd-resolved 未启用"
fi

echo -e "\n[9] /etc/hosts —— 本地域名解析（优先级高于 DNS）"
echo "命令：cat /etc/hosts"
cat /etc/hosts
echo ""
echo "电商项目可在 /etc/hosts 中加入："
echo "  192.168.1.100  api.example.com"
echo "  192.168.1.200  db.internal"

# ---------- 4. Ubuntu Netplan 配置说明 ----------

echo -e "\n[10] Netplan 配置文件位置"
echo "命令：ls -l /etc/netplan/"
ls -l /etc/netplan/ 2>/dev/null || echo "（无 Netplan 配置，可能不是 Ubuntu）"

echo -e "\n[11] 查看 Netplan 配置内容（如存在）"
NETPLAN_FILE=$(ls /etc/netplan/*.yaml 2>/dev/null | head -n1)
if [ -n "$NETPLAN_FILE" ]; then
    echo "命令：cat $NETPLAN_FILE"
    cat "$NETPLAN_FILE"
else
    echo "未找到 Netplan 配置文件"
fi

echo -e "\n[12] Netplan 静态 IP 配置示例（仅打印，不应用）"
cat <<'EOF'
# /etc/netplan/01-netcfg.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 114.114.114.114]

# 应用配置：sudo netplan apply
# 测试配置：sudo netplan try（30 秒后自动回滚，防止 SSH 断开）
EOF

echo -e "\n[13] CentOS 网络配置示例（对比）"
cat <<'EOF'
# /etc/sysconfig/network-scripts/ifcfg-eth0
TYPE=Ethernet
BOOTPROTO=static
NAME=eth0
DEVICE=eth0
ONBOOT=yes
IPADDR=192.168.1.100
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
DNS1=8.8.8.8
DNS2=114.114.114.114

# 重启网络：sudo systemctl restart network (CentOS 7)
# 或：sudo nmcli connection reload && sudo nmcli connection up eth0 (CentOS 8+)
EOF

# ---------- 5. 主机名配置 ----------

echo -e "\n[14] hostnamectl —— 查看主机名信息"
echo "命令：hostnamectl"
hostnamectl 2>/dev/null || hostname

echo -e "\n[15] 修改主机名（需 sudo）"
echo "命令：sudo hostnamectl set-hostname ecommerce-server"
echo "执行后写入 /etc/hostname，新 SSH 会话生效"
echo "查看：cat /etc/hostname"
cat /etc/hostname

# ---------- 6. 网络接口统计 ----------

echo -e "\n[16] ip -s link —— 查看接口收发包统计"
echo "命令：ip -s link show $IFACE"
ip -s link show "$IFACE"
echo "说明：RX 收包 / TX 发包，errors/dropped 应为 0，否则有网络问题"

echo -e "\n============================================================"
echo "  Day06 - 01 网络配置演示 完成"
echo "============================================================"
