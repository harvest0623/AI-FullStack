#!/bin/bash
# ============================================================
# 文件名：02-disk-io-monitoring.sh
# 用途：磁盘 IO 监控演示脚本
# 场景：电商服务器 192.168.1.100 磁盘性能排查
# 说明：演示 iostat、iotop、dstat 的使用，讲解 %util/await 解读
# 运行：bash 02-disk-io-monitoring.sh
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
LOG_FILE="/tmp/disk-io-monitor-$(date +%Y%m%d-%H%M%S).log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "磁盘 IO 监控脚本启动"
log "服务器：192.168.1.100 (Ubuntu 22.04)"

# ============================================================
# 第一部分：iostat 磁盘 IO 统计
# ============================================================
section "第一部分：iostat 磁盘 IO 统计"

# 检查 sysstat 包是否安装（包含 iostat）
if ! command -v iostat &> /dev/null; then
    info "sysstat 未安装，安装中...（需要 sudo 权限）"
    sudo apt install -y sysstat
fi
success "iostat 已安装"
echo ""

# iostat 基础输出（CPU 与磁盘概览）
log "iostat 基础输出（iostat 1 2 每秒一次共两次）"
iostat 1 2
echo ""

info "iostat 基础字段："
echo "  tps    = 每秒传输次数（IOPS）"
echo "  kB_read/s  = 每秒读取 KB"
echo "  kB_wrtn/s  = 每秒写入 KB"
echo ""

# iostat -x 扩展输出（重点关注 %util 和 await）
log "iostat -x 扩展输出（iostat -x 1 2）"
iostat -x 1 2
echo ""

info "iostat -x 扩展字段详解："
echo "  ┌────────────┬──────────────────────────────────────────────┐"
echo "  │ 字段       │ 含义                                         │"
echo "  ├────────────┼──────────────────────────────────────────────┤"
echo "  │ rrqm/s     │ 每秒合并的读请求数                           │"
echo "  │ wrqm/s     │ 每秒合并的写请求数                           │"
echo "  │ r/s        │ 每秒完成的读请求数                           │"
echo "  │ w/s        │ 每秒完成的写请求数                           │"
echo "  │ rkB/s      │ 每秒读取的 KB 数                             │"
echo "  │ wkB/s      │ 每秒写入的 KB 数                             │"
echo "  │ avgrq-sz   │ 平均请求大小（扇区数）                       │"
echo "  │ avgqu-sz   │ 平均请求队列长度（>1→请求排队）              │"
echo "  │ await      │ 平均 IO 响应时间（毫秒，★重点关注）          │"
echo "  │ %util      │ 磁盘利用率（★重点关注，接近100%→磁盘打满）   │"
echo "  └────────────┴──────────────────────────────────────────────┘"
echo ""

# 提取 %util 判断磁盘是否打满
log "提取磁盘 %util 判断是否打满"
# iostat -x 输出中，磁盘行最后一列是 %util
iostat -x 1 2 | tail -n +4 | awk 'NF>1 {print "磁盘 "$1" 的 %util = "$NF}' | grep -v "^$"
echo ""

info "磁盘 IO 问题判断标准："
echo "  ┌──────────────────────┬──────────────────────────────────────┐"
echo "  │ 现象                 │ 含义                                 │"
echo "  ├──────────────────────┼──────────────────────────────────────┤"
echo "  │ %util 接近 100%      │ 磁盘带宽已打满，是瓶颈               │"
echo "  │ await > 10ms (SSD)   │ SSD IO 延迟过高                      │"
echo "  │ await > 20ms (HDD)   │ HDD IO 延迟过高                      │"
echo "  │ avgqu-sz 持续 > 1    │ 请求在排队等待                       │"
echo "  │ r/s + w/s 持续高     │ IOPS 高，对照磁盘规格判断            │"
echo "  └──────────────────────┴──────────────────────────────────────┘"
echo ""

warn "场景示例：MySQL 数据库磁盘 await 高"
echo "  现象：iostat 显示 await 持续 > 50ms"
echo "  排查：1.iotop 定位哪个进程在读写"
echo "        2.检查 MySQL 慢查询日志"
echo "        3.检查 innodb_buffer_pool_size 是否合理"
echo "        4.考虑升级 SSD 或加内存提升缓存命中率"

# ============================================================
# 第二部分：iotop 按进程查看 IO
# ============================================================
section "第二部分：iotop 按进程查看 IO"

# 检查 iotop 是否安装
if ! command -v iotop &> /dev/null; then
    info "iotop 未安装，安装中...（需要 sudo 权限）"
    sudo apt install -y iotop
fi
success "iotop 已安装"
echo ""

info "iotop 使用说明："
echo "  sudo iotop        → 交互式查看所有进程 IO（类似 top 但看 IO）"
echo "  sudo iotop -o     → 只显示有 IO 活动的进程"
echo "  sudo iotop -oP    → 只显示有 IO 活动的进程，显示进程名"
echo "  sudo iotop -b -n 3→ 批处理模式，输出 3 次"
echo ""

# iotop 批处理模式输出一次
log "iotop 批处理模式输出（sudo iotop -b -oP -n 2）"
info "执行 iotop 需要 root 权限"
sudo iotop -b -oP -n 2 2>/dev/null | head -20 || warn "iotop 需要 sudo 权限执行"
echo ""

info "iotop 关键字段："
echo "  TID       = 线程 ID"
echo "  PRIO      = IO 优先级"
echo "  DISK READ = 每秒读取速率"
echo "  DISK WRITE= 每秒写入速率"
echo "  SWAPIN    = swap 使用比例"
echo "  IO        = IO 占比"
echo "  COMMAND   = 进程命令"
echo ""
echo "  场景：数据库磁盘繁忙时，用 iotop 定位是 mysqld 还是其他进程在读写"

# ============================================================
# 第三部分：dstat 综合监控
# ============================================================
section "第三部分：dstat 综合监控工具"

# 检查 dstat 是否安装
if ! command -v dstat &> /dev/null; then
    info "dstat 未安装，安装中...（需要 sudo 权限）"
    sudo apt install -y dstat
fi
success "dstat 已安装"
echo ""

info "dstat 常用组合："
echo "  dstat                → 默认（CPU/磁盘/网络/分页/系统）"
echo "  dstat -t             → 加上时间戳"
echo "  dstat -c             → 只看 CPU"
echo "  dstat -d             → 只看磁盘"
echo "  dstat -n             → 只看网络"
echo "  dstat -m             → 只看内存"
echo "  dstat -tcmdn         → 时间/CPU/内存/磁盘/网络综合"
echo "  dstat --top-io       → 显示 IO 最高的进程"
echo "  dstat --top-bio      → 显示块设备 IO 最高的进程"
echo "  dstat --top-cpu      → 显示 CPU 占用最高的进程"
echo "  dstat --top-mem      → 显示内存占用最高的进程"
echo ""

# dstat 输出 5 次（每秒一次）
log "dstat 综合监控输出 5 次（dstat -tcmdn 1 5）"
dstat -tcmdn 1 5 2>/dev/null || warn "dstat 执行失败"
echo ""

info "dstat 优势："
echo "  一条命令同时展示 CPU/内存/磁盘/网络多维度指标"
echo "  替代 vmstat + iostat + ifstat 的组合"
echo "  适合快速全局概览"

# ============================================================
# 第四部分：磁盘 IO 性能问题判断流程
# ============================================================
section "第四部分：磁盘 IO 性能问题判断流程"

info "磁盘 IO 排查流程："
echo "  Step 1: iostat -x 1 查看全局磁盘 IO 状态"
echo "          → %util 高吗？await 大吗？"
echo ""
echo "  Step 2: iotop -oP 定位是哪个进程在读写"
echo "          → mysqld? nginx? redis? 还是异常进程？"
echo ""
echo "  Step 3: 针对进程排查"
echo "          → 数据库：查慢查询、检查 buffer pool、索引优化"
echo "          → 日志服务：检查日志写入量、考虑异步写或日志切割"
echo "          → 应用：检查是否有大文件读写、是否可加缓存"
echo ""
echo "  Step 4: 优化方案"
echo "          → SSD 替换 HDD（最直接的提升）"
echo "          → 加内存提升缓存命中率（减少磁盘读）"
echo "          → 读写分离、批量写入"
echo "          → Redis 缓存热点数据"
echo ""

info "常见磁盘 IO 问题场景："
echo "  ┌────────────────────────┬──────────────────────────────────────┐"
echo "  │ 场景                   │ 优化方向                             │"
echo "  ├────────────────────────┼──────────────────────────────────────┤"
echo "  │ MySQL 磁盘 IO 高       │ 加大 innodb_buffer_pool_size         │"
echo "  │                        │ 优化慢查询、加索引                   │"
echo "  │                        │ 读写分离、SSD 升级                   │"
echo "  ├────────────────────────┼──────────────────────────────────────┤"
echo "  │ Nginx 日志写入频繁     │ 开启 buffer、异步写入                │"
echo "  │                        │ logrotate 日志切割                   │"
echo "  │                        │ 考虑日志收集到 ELK                   │"
echo "  ├────────────────────────┼──────────────────────────────────────┤"
echo "  │ Node.js 大量写文件     │ 使用流式写入、批量写入               │"
echo "  │                        │ 临时文件放 tmpfs（内存盘）           │"
echo "  ├────────────────────────┼──────────────────────────────────────┤"
echo "  │ Redis 持久化 IO 抖动   │ 调整 appendfsync 策略                │"
echo "  │                        │ RDB 快照错峰执行                     │"
echo "  └────────────────────────┴──────────────────────────────────────┘"
echo ""

success "磁盘 IO 监控演示完成！"
log "日志文件：${LOG_FILE}"
echo ""
info "下一步建议："
echo "  1. 手动执行 sudo iotop -oP 持续观察进程 IO"
echo "  2. 手动执行 iostat -x 1 持续监控磁盘状态"
echo "  3. 运行 03-network-monitoring.sh 学习网络监控"
