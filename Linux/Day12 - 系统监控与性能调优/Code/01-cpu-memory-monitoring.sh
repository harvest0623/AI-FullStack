#!/bin/bash
# ============================================================
# 文件名：01-cpu-memory-monitoring.sh
# 用途：CPU 与内存监控演示脚本
# 场景：电商服务器 192.168.1.100 性能监控
# 说明：演示 uptime、top、htop、mpstat、free、vmstat、smem 的使用
#       并讲解 CPU/内存性能问题的判断方法
# 运行：bash 01-cpu-memory-monitoring.sh
# 权限：部分命令需要 sudo（已标注）
# ============================================================

set -euo pipefail

# ---------- 颜色输出函数 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # 恢复默认颜色

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }
section() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

# ---------- 日志记录函数 ----------
LOG_FILE="/tmp/cpu-memory-monitor-$(date +%Y%m%d-%H%M%S).log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "CPU 与内存监控脚本启动"
log "服务器：192.168.1.100 (Ubuntu 22.04)"

# ============================================================
# 第一部分：系统负载 load average
# ============================================================
section "第一部分：系统负载监控（load average）"

# uptime 查看系统运行时间与负载
log "执行 uptime 查看系统负载"
uptime
echo ""

# /proc/loadavg 内核接口直接读取负载
log "读取 /proc/loadavg 内核接口"
cat /proc/loadavg
echo ""

# 获取 CPU 逻辑核数
CPU_CORES=$(nproc)
log "当前服务器 CPU 逻辑核数：${CPU_CORES}"

# 读取 1 分钟平均负载
LOAD_1MIN=$(awk '{print $1}' /proc/loadavg)
log "1 分钟平均负载：${LOAD_1MIN}"

# 用 bc 比较浮点数，判断负载是否过高
if (( $(echo "${LOAD_1MIN} > ${CPU_CORES}" | bc -l) )); then
    warn "负载 ${LOAD_1MIN} > CPU 核数 ${CPU_CORES}，系统过载！"
    warn "可能原因：CPU 密集型进程 / IO 等待 / 内存不足导致频繁 swap"
elif (( $(echo "${LOAD_1MIN} > ${CPU_CORES} * 0.7" | bc -l) )); then
    warn "负载 ${LOAD_1MIN} 接近 CPU 核数 ${CPU_CORES}，需关注"
else
    success "负载 ${LOAD_1MIN} 正常（CPU 核数 ${CPU_CORES}）"
fi

# ============================================================
# 第二部分：top 命令字段详解
# ============================================================
section "第二部分：top 命令与 CPU 使用率"

# top 批处理模式输出一次（-b 批处理 -n 1 只输出一次）
log "top 批处理模式输出（-b -n 1）"
top -b -n 1 | head -15
echo ""

info "top 头部字段解读："
echo "  %Cpu(s): us=用户态  sy=内核态  ni=nice  id=空闲  wa=IO等待  hi=硬中断  si=软中断  st=被偷走"
echo "  判断：us 高→应用问题  sy 高→系统调用多  wa 高→磁盘瓶颈  id 低→CPU繁忙"
echo ""

# 提取 CPU 空闲率判断 CPU 是否繁忙
# top 输出中 %Cpu(s) 行的 id 字段
log "提取当前 CPU 空闲率（id）"
CPU_IDLE=$(top -b -n 1 | grep "%Cpu" | awk -F',' '{print $4}' | awk '{print $1}')
log "CPU 空闲率：${CPU_IDLE}%"
if (( $(echo "${CPU_IDLE%.*} < 20" | bc -l 2>/dev/null || echo 0) )); then
    warn "CPU 空闲率低于 20%，CPU 繁忙！"
else
    success "CPU 空闲率正常"
fi

# ============================================================
# 第三部分：htop 增强版监控
# ============================================================
section "第三部分：htop 增强版监控工具"

# 检查 htop 是否安装
if ! command -v htop &> /dev/null; then
    info "htop 未安装，安装中...（需要 sudo 权限）"
    sudo apt install -y htop
fi
success "htop 已安装"
echo ""
info "htop 交互操作说明："
echo "  F2  → 设置（自定义显示列、颜色）"
echo "  F4  → 过滤进程（输入关键词）"
echo "  F5  → 树形视图（显示进程父子关系）"
echo "  F6  → 排序（选择排序字段）"
echo "  F9  → 发送信号（杀死进程）"
echo "  q   → 退出"
echo ""
info "htop 是交互式工具，请手动执行 htop 体验（本脚本不自动启动）"

# ============================================================
# 第四部分：mpstat 多核 CPU 监控
# ============================================================
section "第四部分：mpstat 多核 CPU 监控"

# 检查 sysstat 包是否安装（包含 mpstat、iostat、sar）
if ! command -v mpstat &> /dev/null; then
    info "sysstat 未安装，安装中...（需要 sudo 权限）"
    sudo apt install -y sysstat
fi
success "mpstat 已安装"
echo ""

# mpstat 查看所有 CPU 核心使用率（只输出一次）
log "mpstat 查看所有 CPU 核心使用率（mpstat -P ALL 1 1）"
mpstat -P ALL 1 1 2>/dev/null || warn "mpstat 执行失败"
echo ""

info "mpstat 字段解读："
echo "  %usr   = 用户态时间（应用代码执行）"
echo "  %sys   = 内核态时间（系统调用）"
echo "  %iowait= 等待 IO 完成的时间"
echo "  %idle  = 空闲时间"
echo ""
echo "  判断：若某核 %iowait 持续高 → 该核在等 IO"
echo "        若 %usr 高 → 用户态应用占满 CPU"

# ============================================================
# 第五部分：free 内存监控
# ============================================================
section "第五部分：free 内存监控"

# free -h 以人类可读格式显示内存
log "free -h 查看内存使用情况"
free -h
echo ""

info "free 字段解读："
echo "  total      = 物理内存总量"
echo "  used       = 已使用（不含 buff/cache）"
echo "  free       = 完全空闲"
echo "  buff/cache = 系统缓冲/缓存（可回收）"
echo "  available  = 实际可用（= free + 可回收 buff/cache）"
echo ""
warn "关键认知：判断内存是否够用，看 available 而不是 free！"
echo "  Linux 会用空闲内存做 cache 加速 IO，free 少不代表内存紧张"
echo ""

# 提取 available 内存（MB）并判断
AVAIL_MEM=$(free -m | awk '/Mem:/ {print $7}')
log "当前 available 内存：${AVAIL_MEM} MB"
if [ "${AVAIL_MEM}" -lt 500 ]; then
    warn "可用内存低于 500MB，内存紧张！需排查内存占用"
elif [ "${AVAIL_MEM}" -lt 1000 ]; then
    warn "可用内存低于 1GB，建议关注"
else
    success "可用内存充足（${AVAIL_MEM} MB）"
fi

# buffer vs cache 说明
info "buffer vs cache："
echo "  buffer（缓冲）= 写缓冲，暂存待写入磁盘的数据"
echo "  cache（缓存） = 读缓存，缓存已从磁盘读取的数据"

# ============================================================
# 第六部分：vmstat 综合监控
# ============================================================
section "第六部分：vmstat 综合监控"

# vmstat 输出一次（不带间隔参数只输出一次）
log "vmstat 输出当前状态（vmstat 1 3 每秒一次共三次）"
vmstat 1 3
echo ""

info "vmstat 关键字段解读："
echo "  ┌─ procs ────────────────────────────────┐"
echo "  │ r  = 运行队列进程数（>CPU核数→CPU紧张）│"
echo "  │ b  = D 状态进程数（等待IO，>0→IO阻塞） │"
echo "  └────────────────────────────────────────┘"
echo "  ┌─ swap ─────────────────────────────────┐"
echo "  │ si = swap in（>0→内存不足，换入内存）  │"
echo "  │ so = swap out（>0→内存不足，换出到盘） │"
echo "  └────────────────────────────────────────┘"
echo "  ┌─ io ───────────────────────────────────┐"
echo "  │ bi = block in（每秒从磁盘读入块数）    │"
echo "  │ bo = block out（每秒写入磁盘块数）     │"
echo "  └────────────────────────────────────────┘"
echo "  ┌─ system ───────────────────────────────┐"
echo "  │ in = 每秒中断数                        │"
echo "  │ cs = 每秒上下文切换数                  │"
echo "  └────────────────────────────────────────┘"
echo "  ┌─ cpu ──────────────────────────────────┐"
echo "  │ us/sy/id/wa/st 同 top                  │"
echo "  └────────────────────────────────────────┘"
echo ""

# 检查 swap 使用情况
SWAP_SI=$(vmstat 1 2 | tail -1 | awk '{print $7}')
SWAP_SO=$(vmstat 1 2 | tail -1 | awk '{print $8}')
log "当前 swap in(si)：${SWAP_SI}，swap out(so)：${SWAP_SO}"
if [ "${SWAP_SI}" -gt 0 ] || [ "${SWAP_SO}" -gt 0 ]; then
    warn "检测到 swap 换入换出活动，内存可能不足！"
    warn "建议：1.检查内存占用最高的进程 2.考虑加内存 3.优化应用内存使用"
else
    success "无 swap 换入换出，内存状态正常"
fi

# ============================================================
# 第七部分：smem 按进程查看内存
# ============================================================
section "第七部分：smem 按进程查看内存"

# 检查 smem 是否安装
if ! command -v smem &> /dev/null; then
    info "smem 未安装，安装中...（需要 sudo 权限）"
    sudo apt install -y smem
fi
success "smem 已安装"
echo ""

# smem -r -k 按 RSS 排序，人类可读，显示前 15 个进程
log "smem 按进程内存占用排序（前 15）"
smem -r -k 2>/dev/null | head -16 || warn "smem 执行失败"
echo ""

info "smem 内存指标说明："
echo "  USS = Unique Set Size，进程独占内存（不含共享库）"
echo "  PSS = Proportional Set Size，按比例分摊共享内存（最准确）"
echo "  RSS = Resident Set Size，常驻内存（含共享库，会重复计算）"
echo ""
echo "  场景：排查内存占用时，PSS 最准确；RSS 最直观但有重复计算"

# ============================================================
# 第八部分：CPU/内存性能问题判断方法总结
# ============================================================
section "第八部分：CPU/内存性能问题判断方法总结"

info "CPU 性能问题判断："
echo "  ┌──────────┬──────────────────────────────┬──────────────────────┐"
echo "  │ 现象     │ 含义                         │ 排查方向             │"
echo "  ├──────────┼──────────────────────────────┼──────────────────────┤"
echo "  │ %us 高   │ 用户态 CPU 占用高            │ 应用代码效率问题     │"
echo "  │ %sy 高   │ 内核态 CPU 占用高            │ 系统调用/锁/上下文切换│"
echo "  │ %wa 高   │ IO 等待高                    │ 磁盘瓶颈→查 iostat   │"
echo "  │ %id 低   │ CPU 空闲少                   │ CPU 繁忙→优化/扩容   │"
echo "  │ %si 高   │ 软中断高                     │ 网络包处理量大       │"
echo "  │ %st 高   │ 被虚拟化偷走                 │ 云主机超卖→迁移      │"
echo "  └──────────┴──────────────────────────────┴──────────────────────┘"
echo ""

info "内存性能问题判断："
echo "  ┌────────────────────┬────────────────────────────────────────┐"
echo "  │ 现象               │ 含义                                   │"
echo "  ├────────────────────┼────────────────────────────────────────┤"
echo "  │ available 低       │ 实际可用内存不足                       │"
echo "  │ si/so 持续 > 0     │ 物理内存不足，频繁使用 swap            │"
echo "  │ swap used 持续增长 │ 内存泄漏或负载过高                     │"
echo "  │ OOM Killer 触发    │ 内存耗尽，内核杀进程                   │"
echo "  └────────────────────┴────────────────────────────────────────┘"
echo ""

success "CPU 与内存监控演示完成！"
log "日志文件：${LOG_FILE}"
echo ""
info "下一步建议："
echo "  1. 手动执行 htop 体验交互式监控"
echo "  2. 手动执行 top 按 1 查看每个 CPU 核心使用率"
echo "  3. 手动执行 vmstat 1 持续观察内存与 IO 变化"
echo "  4. 运行 02-disk-io-monitoring.sh 学习磁盘 IO 监控"
