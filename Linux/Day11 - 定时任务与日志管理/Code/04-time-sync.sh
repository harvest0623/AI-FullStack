#!/bin/bash
# ============================================================
# 文件名：04-time-sync.sh
# 用途：时间同步脚本——时区设置、chrony 安装与配置、时间同步验证
# 场景：电商项目服务器时间同步（Ubuntu 22.04 LTS）
# 语法：sudo bash 04-time-sync.sh
# 权限：需 root/sudo 执行（涉及系统时间与服务管理）
# ============================================================

set -uo pipefail

# ---------- 颜色输出 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
section() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

# ---------- root 权限检查 ----------
check_root() {
    if [[ $UID -ne 0 ]]; then
        error "本脚本需要 root 权限执行，请使用 sudo"
        echo "  命令：sudo bash $0"
        exit 1
    fi
}

echo -e "${CYAN}========== Day11 - 04 时间同步脚本 ==========${NC}"
info "主机：$(hostname)  当前时间：$(date '+%F %T')"

# ============================================================
# 一、查看当前时间与时区
# ============================================================
section "一、查看当前时间与时区"

info "1. timedatectl 当前状态："
timedatectl

echo ""
info "2. 当前时区："
timedatectl status | grep "Time zone" || cat /etc/timezone 2>/dev/null

echo ""
info "3. 当前系统时间："
date

echo ""
info "4. 硬件时钟（RTC）："
hwclock 2>/dev/null || info "  hwclock 不可用"

echo ""
info "5. 可用时区列表（亚洲）："
timedatectl list-timezones 2>/dev/null | grep "Asia/" | head -n 20 || info "  无法列出时区"

# ============================================================
# 二、设置时区为 Asia/Shanghai
# ============================================================
section "二、设置时区"

CURRENT_TZ=$(timedatectl status 2>/dev/null | grep "Time zone" | awk '{print $3}')

if [[ "$CURRENT_TZ" == "Asia/Shanghai" ]]; then
    success "当前时区已是 Asia/Shanghai，无需修改"
else
    info "当前时区：$CURRENT_TZ"
    info "设置时区为 Asia/Shanghai..."
    check_root
    timedatectl set-timezone Asia/Shanghai
    if [[ $? -eq 0 ]]; then
        success "时区已设置为 Asia/Shanghai"
        info "当前时间：$(date '+%F %T %Z')"
    else
        error "时区设置失败"
        exit 1
    fi
fi

# ============================================================
# 三、安装与配置 chrony
# ============================================================
section "三、chrony 时间同步服务"

# 检查是否已安装 chrony
if command -v chronyd >/dev/null 2>&1; then
    success "chrony 已安装"
    chronyd --version 2>&1 | head -n 1
else
    info "chrony 未安装，开始安装..."
    check_root

    # 检测包管理器
    if command -v apt >/dev/null 2>&1; then
        info "使用 apt 安装 chrony..."
        apt update -qq && apt install -y chrony
    elif command -v yum >/dev/null 2>&1; then
        info "使用 yum 安装 chrony..."
        yum install -y chrony
    elif command -v dnf >/dev/null 2>&1; then
        info "使用 dnf 安装 chrony..."
        dnf install -y chrony
    else
        error "未找到支持的包管理器（apt/yum/dnf）"
        exit 1
    fi

    if command -v chronyd >/dev/null 2>&1; then
        success "chrony 安装成功"
    else
        error "chrony 安装失败"
        exit 1
    fi
fi

echo ""
info "chrony 服务状态："
systemctl status chronyd --no-pager 2>/dev/null | head -n 10 || systemctl status chrony --no-pager 2>/dev/null | head -n 10

# 启用并启动 chrony
echo ""
info "启用 chrony 开机自启并启动..."
check_root
systemctl enable chronyd 2>/dev/null || systemctl enable chrony 2>/dev/null
systemctl restart chronyd 2>/dev/null || systemctl restart chrony 2>/dev/null
sleep 2

if systemctl is-active --quiet chronyd 2>/dev/null || systemctl is-active --quiet chrony 2>/dev/null; then
    success "chrony 服务已启动"
else
    error "chrony 服务启动失败"
fi

# ============================================================
# 四、配置 chrony 使用阿里云 NTP 服务器
# ============================================================
section "四、配置 NTP 服务器"

# 确定 chrony 配置文件路径
CHRONY_CONF=""
for conf in /etc/chrony/chrony.conf /etc/chrony.conf; do
    if [[ -f "$conf" ]]; then
        CHRONY_CONF="$conf"
        break
    fi
done

if [[ -z "$CHRONY_CONF" ]]; then
    warn "未找到 chrony 配置文件，跳过配置"
else
    info "chrony 配置文件：$CHRONY_CONF"
    echo ""
    info "当前 NTP 服务器配置："
    grep -E "^pool|^server" "$CHRONY_CONF" 2>/dev/null || info "  无 pool/server 配置"

    # 备份原配置
    check_root
    BACKUP_FILE="${CHRONY_CONF}.bak.$(date +%Y%m%d%H%M%S)"
    cp "$CHRONY_CONF" "$BACKUP_FILE"
    info "已备份原配置到：$BACKUP_FILE"

    # 写入国内 NTP 服务器配置
    info "写入阿里云 NTP 服务器配置..."
    cat > "$CHRONY_CONF" <<'EOF'
# ============ chrony NTP 配置 ============
# 使用阿里云 NTP 服务器（国内访问快）
pool ntp.aliyun.com iburst
pool cn.pool.ntp.org iburst

# 备用：腾讯云 / 国家授时中心
# pool ntp.tencent.com iburst
# pool ntp.ntsc.ac.cn iburst

# 记录时钟漂移
driftfile /var/lib/chrony/chrony.drift

# 允许 chrony 在大偏差时立即步进校正时间
makestep 1.0 3

# 启用硬件时间同步
rtcsync

# 允许本地网络客户端同步（作为内网时间服务器时取消注释）
# allow 192.168.1.0/24

# 本地提供时间（即使未同步也提供服务，需配合 allow）
# local stratum 10

# 日志目录
logdir /var/log/chrony
EOF

    success "chrony 配置已更新"
    echo ""
    info "重启 chrony 服务..."
    systemctl restart chronyd 2>/dev/null || systemctl restart chrony 2>/dev/null
    sleep 3
fi

# ============================================================
# 五、验证时间同步
# ============================================================
section "五、验证时间同步"

# 开启 NTP 同步
info "开启 NTP 同步..."
check_root
timedatectl set-ntp true 2>/dev/null || true
sleep 2

echo ""
info "1. timedatectl 同步状态："
timedatectl status

echo ""
info "2. chronyc tracking（详细同步状态）："
chronyc tracking 2>/dev/null || warn "chronyc 不可用"

echo ""
info "3. chronyc sources（时间源列表）："
chronyc sources -v 2>/dev/null || warn "chronyc 不可用"

echo ""
info "4. chronyc sourcestats（时间源统计）："
chronyc sourcestats 2>/dev/null || warn "chronyc 不可用"

echo ""
info "字段说明："
cat <<'EOF'
  chronyc tracking 输出：
    Reference ID    : 使用的 NTP 服务器
    Stratum         : 层级（1=直连原子钟，2=从1同步，越小越准）
    Ref time        : 上次同步时间
    System time     : 系统时间与 NTP 的偏差
    Last offset     : 上次偏移量
    RMS offset      : 均方根偏移
    Frequency       : 时钟频率漂移
    Poll interval   : 轮询间隔（秒）
    Leap status     : 闰秒状态（Normal 正常）

  chronyc sources 输出：
    ^  = 服务器（stratum 1，直连）
    ^* = 当前最佳同步源
    ^+ = 备选源
    ^? : 连接中或不可达
EOF

# ============================================================
# 六、旧版 ntpdate 对比（已弃用）
# ============================================================
section "六、ntpdate 对比（已弃用）"

cat <<'EOF'
ntpdate 是旧版时间同步工具，已被弃用，推荐用 chrony：

  # ntpdate 手动同步（已弃用）
  sudo ntpdate ntp.aliyun.com

  # chrony 手动同步（推荐）
  sudo chronyc -a makestep

ntpdate 弃用原因：
  1. ntpdate 是一次性同步，不持续校正
  2. chrony 持续运行，自动校正时钟漂移
  3. chrony 收敛更快，对网络中断更鲁棒
  4. Ubuntu 22.04 / CentOS 8+ 默认已移除 ntpdate

chrony vs ntpd：
  | 维度     | chrony      | ntpd        |
  |----------|-------------|-------------|
  | 收敛速度  | 快           | 慢          |
  | 资源占用  | 小           | 较大        |
  | 网络中断  | 鲁棒         | 需重新同步  |
  | 推荐度    | ★★★★★       | ★★★        |
EOF

# ============================================================
# 七、为什么生产必须时间同步
# ============================================================
section "七、生产环境时间同步的重要性"

cat <<'EOF'
时间不一致会导致严重问题：

1. 日志排序错乱
   多台服务器排查问题时，时间偏差导致日志无法对齐
   → 故障根因被掩盖

2. 定时任务错乱
   cron 依赖系统时间，时间偏移导致任务提前或延后执行
   → 备份缺失、报表错误

3. 分布式系统问题
   - 数据库主从复制：时间差导致 binlog 顺序错乱
   - 分布式锁：TTL 失效时间不准
   - TLS 证书：时间超前会导致证书未生效，滞后会导致已过期
   → 数据不一致、连接失败

4. 金融交易
   订单时间戳、交易记录必须准确
   → 订单乱序、对账失败

5. 认证与安全
   Kerberos 票据、JWT token、OTP 验证码都依赖时间
   → 认证失败、安全漏洞

生产建议：
  - 所有服务器必须安装 chrony 并配置相同 NTP 源
  - 定期检查 chronyc tracking 确认同步状态
  - 监控时间偏移，超过 1 秒告警
EOF

echo ""
success "时间同步脚本执行完毕。"
info "当前时间：$(date '+%F %T %Z')"
info "时区：$(timedatectl status 2>/dev/null | grep 'Time zone' | awk '{print $3}')"
