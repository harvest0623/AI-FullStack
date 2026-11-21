#!/bin/bash
# ============================================================
# 文件名：03-network-monitoring.sh
# 用途：网络监控演示脚本
# 场景：电商服务器 192.168.1.100 网络性能排查
# 说明：演示 iftop、nethogs、ss、sar 网络监控工具
#       讲解网络问题排查方法
# 运行：bash 03-network-monitoring.sh
# 权限：部分命令需要 sudo（已标注）
# ============================================================

set -euo pipefail

# ---------- 颜色输出函数 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
section() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

# ---------- 日志记录函数 ----------
LOG_FILE="/tmp/network-monitor-$(date +%Y%m%d-%H%M%S).log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "网络监控脚本启动"
log "服务器：192.168.1.100 (Ubuntu 22.04)"

# ============================================================
# 第一部分：ss 连接统计
# ============================================================
section "第一部分：ss 连接统计（netstat 替代工具）"

# ss 是现代 Linux 替代 netstat 的工具，更快更高效
log "ss -s 查看连接统计概要"
ss -s
echo ""

info "ss -s 输出解读："
echo "  TCP:   total/established/syn-sent/syn-recv/..."
echo "  Transport: 各协议连接数统计"
echo ""
echo "  判断：established 数持续增长 → 可能连接泄漏"
echo "        TIME-WAIT 数过多 → 需调整 tcp_tw_reuse"
echo ""

# 查看所有 TCP 连接
log "ss -t -a 查看所有 TCP 连接（前 20 行）"
ss -t -a | head -20
echo ""

# 查看已建立的 TCP 连接数
log "统计已建立的 TCP 连接数"
ESTABLISHED_COUNT=$(ss -t state established | wc -l)
log "已建立 TCP 连接数：${ESTABLISHED_COUNT}"
echo ""

# 查看 80 端口连接（Nginx）
log "查看 80 端口连接（ss -t -a | grep :80）"
ss -t -a | grep ':80' | head -10 || info "当前无 80 端口连接"
echo ""

info "ss 常用命令："
echo "  ┌────────────────────────────┬──────────────────────────────┐"
echo "  │ 命令                       │ 功能                         │"
echo "  ├────────────────────────────┼──────────────────────────────┤"
echo "  │ ss -s                      │ 连接数统计概要               │"
echo "  │ ss -t -a                   │ 所有 TCP 连接                │"
echo "  │ ss -u -a                   │ 所有 UDP 连接                │"
echo "  │ ss -t state established    │ 已建立的 TCP 连接            │"
echo "  │ ss -t state time-wait      │ TIME_WAIT 状态连接           │"
echo "  │ ss -tlnp                   │ 监听端口与进程               │"
echo "  │ ss -t -a | grep :80        │ 80 端口连接                  │"
echo "  └────────────────────────────┴──────────────────────────────┘"
echo ""

# 统计各状态连接数
log "统计 TCP 各状态连接数"
ss -t -a | awk '{print $1}' | sort | uniq -c | sort -rn
echo ""

# TIME-WAIT 过多说明
TIME_WAIT_COUNT=$(ss -t state time-wait 2>/dev/null | wc -l)
log "TIME_WAIT 状态连接数：${TIME_WAIT_COUNT}"
if [ "${TIME_WAIT_COUNT}" -gt 1000 ]; then
    warn "TIME_WAIT 连接过万，建议优化："
    echo "  1. 开启 tcp_tw_reuse：sudo sysctl -w net.ipv4.tcp_tw_reuse=1"
    echo "  2. 减小 tcp_fin_timeout：sudo sysctl -w net.ipv4.tcp_fin_timeout=15"
    echo "  3. 检查应用是否正确关闭连接（连接池复用）"
fi

# ============================================================
# 第二部分：iftop 按连接查看带宽
# ============================================================
section "第二部分：iftop 按连接查看带宽"

# 检查 iftop 是否安装
if ! command -v iftop &> /dev/null; then
    info "iftop 未安装，安装中...（需要 sudo 权限）"
    sudo apt install -y iftop
fi
success "iftop 已安装"
echo ""

# 获取主网卡名称（替代旧版 eth0）
PRIMARY_NIC=$(ip route | grep default | awk '{print $5}' | head -1)
log "主网卡：${PRIMARY_NIC}"
echo ""

info "iftop 使用说明："
echo "  sudo iftop                      → 监控主网卡带宽"
echo "  sudo iftop -i ${PRIMARY_NIC}             → 指定网卡"
echo "  sudo iftop -i ${PRIMARY_NIC} -n          → 不解析主机名（更快）"
echo "  sudo iftop -i ${PRIMARY_NIC} -n -P       → 显示端口"
echo "  sudo iftop -i ${PRIMARY_NIC} -n -N -P    → 不解析端口名"
echo ""
echo "  iftop 交互命令："
echo "    n  → 切换主机名解析"
echo "    s  → 切换源主机显示"
echo "    d  → 切换目标主机显示"
echo "    t  → 切换显示模式"
echo "    q  → 退出"
echo ""
info "iftop 是交互式工具，请手动执行体验（本脚本不自动启动）"
echo ""
info "iftop 界面解读："
echo "  ┌──────────────────────────────────────────────────────────┐"
echo "  │ 左侧：源主机    右侧：目标主机                           │"
echo "  │ 中间柱状图：实时带宽（=> 发送，<= 接收）                 │"
echo "  │ 底部三行：累计发送/接收/总计 TX/RX/CUM                   │"
echo "  │                                                          │"
echo "  │ 场景：发现某个外部 IP 大量传输 → 可能是异常流量/被攻击   │"
echo "  └──────────────────────────────────────────────────────────┘"

# ============================================================
# 第三部分：nethogs 按进程查看网络
# ============================================================
section "第三部分：nethogs 按进程查看网络使用"

# 检查 nethogs 是否安装
if ! command -v nethogs &> /dev/null; then
    info "nethogs 未安装，安装中...（需要 sudo 权限）"
    sudo apt install -y nethogs
fi
success "nethogs 已安装"
echo ""

info "nethogs 使用说明："
echo "  sudo nethogs                   → 查看所有进程网络流量"
echo "  sudo nethogs ${PRIMARY_NIC}            → 指定网卡"
echo ""
echo "  nethogs 交互命令："
echo "    m  → 切换显示模式（KB/s 或 B/s）"
echo "    r  → 按接收排序"
echo "    s  → 按发送排序"
echo "    q  → 退出"
echo ""
info "nethogs 是交互式工具，请手动执行体验"
echo ""
info "nethogs 优势："
echo "  iftop 只能看到连接级带宽，无法定位进程"
echo "  nethogs 能直接看到哪个进程在占网络带宽"
echo "  场景：发现带宽被打满，用 nethogs 定位是 nginx 还是异常进程"

# ============================================================
# 第四部分：sar 网络历史统计
# ============================================================
section "第四部分：sar 网络历史统计"

# 检查 sar 是否安装（sysstat 包）
if ! command -v sar &> /dev/null; then
    info "sysstat 未安装，安装中...（需要 sudo 权限）"
    sudo apt install -y sysstat
fi

# 检查 sar 数据收集是否开启
if [ -f /etc/default/sysstat ]; then
    ENABLED=$(grep -E "^ENABLED=" /etc/default/sysstat | cut -d'"' -f2)
    if [ "${ENABLED}" != "true" ]; then
        warn "sar 数据收集未开启，执行开启步骤（需要 sudo）"
        sudo sed -i 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
        sudo systemctl restart sysstat
        sudo systemctl enable sysstat
        success "sar 数据收集已开启"
    else
        success "sar 数据收集已开启"
    fi
fi
echo ""

# sar 实时网络统计
log "sar -n DEV 1 3 实时网卡流量统计（每秒一次共三次）"
sar -n DEV 1 3 2>/dev/null || warn "sar 无历史数据，需运行一段时间后查看"
echo ""

info "sar -n DEV 输出字段："
echo "  IFACE    = 网卡名"
echo "  rxpck/s  = 每秒接收包数"
echo "  txpck/s  = 每秒发送包数"
echo "  rxkB/s   = 每秒接收 KB"
echo "  txkB/s   = 每秒发送 KB"
echo "  rxcmp/s  = 每秒接收压缩包"
echo "  txcmp/s  = 每秒发送压缩包"
echo "  rxmcst/s = 每秒接收多播包"
echo ""

info "sar 查看历史数据："
echo "  sar -n DEV                          → 今天的网卡流量"
echo "  sar -n DEV -f /var/log/sysstat/sa28 → 查看 28 号的网卡流量"
echo "  sar -n DEV -s 10:00:00 -e 12:00:00  → 指定时间段"
echo ""
echo "  场景：凌晨流量突增排查 → 用 sar 查看历史时段网卡流量"

# ============================================================
# 第五部分：网络问题排查方法
# ============================================================
section "第五部分：网络问题排查方法"

info "网络性能问题判断标准："
echo "  ┌──────────────────────────┬──────────────────────────────────┐"
echo "  │ 现象                     │ 含义                             │"
echo "  ├──────────────────────────┼──────────────────────────────────┤"
echo "  │ iftop 显示带宽打满       │ 网络吞吐量达上限                 │"
echo "  │ ss 连接数异常多          │ 可能被攻击或连接泄漏             │"
echo "  │ TIME_WAIT 过多           │ 连接未复用，需调内核参数         │"
echo "  │ SYN_RECV 多              │ 可能遭受 SYN Flood 攻击          │"
echo "  │ 某外部 IP 大量连接       │ 可能有爬虫或攻击                 │"
echo "  └──────────────────────────┴──────────────────────────────────┘"
echo ""

info "网络排查流程："
echo "  Step 1: ss -s 看连接总数是否异常"
echo "          → 连接数暴涨？TIME_WAIT 过多？"
echo ""
echo "  Step 2: ss -t -a 看连接详情"
echo "          → 哪些 IP 在连接？端口分布？"
echo ""
echo "  Step 3: iftop 看实时带宽"
echo "          → 带宽打满了吗？哪个连接流量大？"
echo ""
echo "  Step 4: nethogs 定位进程"
echo "          → 哪个进程在占带宽？"
echo ""
echo "  Step 5: sar -n DEV 看历史趋势"
echo "          → 什么时候开始流量异常？"
echo ""

warn "电商场景网络问题示例："
echo "  ┌──────────────────────────┬──────────────────────────────────┐"
echo "  │ 问题                     │ 解决方案                         │"
echo "  ├──────────────────────────┼──────────────────────────────────┤"
echo "  │ 大促带宽打满             │ 1.CDN 分流静态资源               │"
echo "  │                          │ 2.开启 gzip 压缩                 │"
echo "  │                          │ 3.升级带宽                       │"
echo "  ├──────────────────────────┼──────────────────────────────────┤"
echo "  │ SYN Flood 攻击           │ 1.开启 syncookies                │"
echo "  │                          │ 2.调整 tcp_max_syn_backlog       │"
echo "  │                          │ 3.用 fail2ban 封 IP              │"
echo "  ├──────────────────────────┼──────────────────────────────────┤"
echo "  │ TIME_WAIT 过多           │ 1.开启 tcp_tw_reuse              │"
echo "  │                          │ 2.应用层连接池复用               │"
echo "  │                          │ 3.减小 fin_timeout               │"
echo "  ├──────────────────────────┼──────────────────────────────────┤"
echo "  │ 异常 IP 大量请求         │ 1.iftop 定位 IP                  │"
echo "  │                          │ 2.Nginx 限流 limit_req           │"
echo "  │                          │ 3.防火墙封 IP                    │"
echo "  └──────────────────────────┴──────────────────────────────────┘"
echo ""

# ============================================================
# 第六部分：补充网络监控命令
# ============================================================
section "第六部分：补充网络监控命令"

info "其他常用网络监控命令："
echo ""

# 查看网卡信息与 IP
log "ip addr 查看网卡与 IP"
ip addr show "${PRIMARY_NIC}" 2>/dev/null | head -10
echo ""

# 查看路由表
log "ip route 查看路由表"
ip route | head -5
echo ""

# 查看网络接口流量统计
log "ip -s link 查看网卡流量统计"
ip -s link show "${PRIMARY_NIC}" 2>/dev/null
echo ""

info "网络监控命令速查："
echo "  ┌────────────────────────┬──────────────────────────────────┐"
echo "  │ 命令                   │ 功能                             │"
echo "  ├────────────────────────┼──────────────────────────────────┤"
echo "  │ ss -s                  │ 连接统计概要                     │"
echo "  │ ss -tlnp               │ 监听端口与进程                   │"
echo "  │ iftop -i eth0 -n -P    │ 实时连接级带宽                   │"
echo "  │ nethogs eth0           │ 进程级网络流量                   │"
echo "  │ sar -n DEV 1           │ 网卡流量历史                     │"
echo "  │ ip -s link             │ 网卡收发包统计                   │"
echo "  │ ping host              │ 连通性测试                       │"
echo "  │ mtr host               │ 路由追踪（结合 ping+traceroute） │"
echo "  │ curl -w '@-' -o /dev/null -s URL │ HTTP 请求耗时分析      │"
echo "  └────────────────────────┴──────────────────────────────────┘"
echo ""

success "网络监控演示完成！"
log "日志文件：${LOG_FILE}"
echo ""
info "下一步建议："
echo "  1. 手动执行 sudo iftop -i ${PRIMARY_NIC} -n -P 体验带宽监控"
echo "  2. 手动执行 sudo nethogs ${PRIMARY_NIC} 定位网络进程"
echo "  3. 阅读 04-performance-tuning.md 学习综合性能调优"
