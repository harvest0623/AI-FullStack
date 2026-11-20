#!/bin/bash
# ============================================================
# 文件名：04-practical-scripts.sh
# 用途：实战脚本合集（3 个生产级脚本）
#       1. backup_db      —— 数据库自动备份
#       2. health_check   —— 服务健康检查（Nginx/MySQL/Redis）
#       3. create_users   —— 批量用户创建（从文件读取用户名）
# 场景：电商项目 /opt/ecommerce/ 运维自动化
# 语法：
#   sudo bash 04-practical-scripts.sh backup_db   [数据库名]
#   sudo bash 04-practical-scripts.sh health_check
#   sudo bash 04-practical-scripts.sh create_users <用户名文件>
# 权限：需 root/sudo 执行（涉及系统用户与数据库备份）
# ============================================================

set -euo pipefail

# ---------- 颜色与日志 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $(date '+%F %T') $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $(date '+%F %T') $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $(date '+%F %T') $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $(date '+%F %T') $*" >&2; }
section() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

# ---------- 全局常量 ----------
APP_NAME="ecommerce"
APP_DIR="/opt/ecommerce"
BACKUP_DIR="${APP_DIR}/backup"
LOG_DIR="${APP_DIR}/logs"
RETAIN_DAYS=7                 # 备份保留天数

# ---------- 清理函数 + trap ----------
TMP_FILES=()
cleanup() {
    if [[ ${#TMP_FILES[@]} -gt 0 ]]; then
        info "清理临时文件..."
        for f in "${TMP_FILES[@]}"; do
            rm -f "$f"
        done
    fi
}
trap cleanup EXIT

# ============================================================
# 脚本一：数据库自动备份 backup_db
# ============================================================
backup_db() {
    local db_name="${1:-ecommerce}"
    local backup_file
    backup_file="${BACKUP_DIR}/${db_name}_$(date +%Y%m%d_%H%M%S).sql.gz"

    section "数据库备份：$db_name"

    # 检查备份目录
    if [[ ! -d "$BACKUP_DIR" ]]; then
        info "创建备份目录：$BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi

    # 检查 mysqldump 是否可用
    if ! command -v mysqldump >/dev/null 2>&1; then
        error "未找到 mysqldump 命令，请安装 mysql-client"
        return 1
    fi

    # 检查 MySQL 是否在运行
    if ! systemctl is-active --quiet mysql 2>/dev/null && \
       ! systemctl is-active --quiet mysqld 2>/dev/null; then
        warn "MySQL 服务未运行，尝试启动..."
        systemctl start mysql 2>/dev/null || systemctl start mysqld 2>/dev/null || {
            error "无法启动 MySQL 服务"
            return 1
        }
    fi

    info "开始备份数据库：$db_name"
    info "备份文件：$backup_file"

    # 执行备份（mysqldump 输出管道给 gzip 压缩）
    # 注意：生产环境应使用配置文件或环境变量传递密码，避免命令行暴露
    if mysqldump --single-transaction --routines --triggers "$db_name" 2>/dev/null | gzip > "$backup_file"; then
        local size
        size=$(du -h "$backup_file" | awk '{print $1}')
        success "备份完成：$backup_file ($size)"
    else
        error "备份失败"
        rm -f "$backup_file"
        return 1
    fi

    # 清理过期备份
    info "清理 ${RETAIN_DAYS} 天前的旧备份..."
    local deleted=0
    while IFS= read -r old_file; do
        [[ -z "$old_file" ]] && continue
        rm -f "$old_file"
        info "已删除旧备份：$(basename "$old_file")"
        ((deleted++))
    done < <(find "$BACKUP_DIR" -name "${db_name}_*.sql.gz" -type f -mtime +${RETAIN_DAYS} 2>/dev/null)

    if [[ $deleted -eq 0 ]]; then
        info "无过期备份需要清理"
    else
        success "共清理 $deleted 个过期备份"
    fi

    # 列出当前备份
    info "当前 ${db_name} 的备份列表："
    ls -lh "$BACKUP_DIR"/${db_name}_*.sql.gz 2>/dev/null | awk '{print "  "$NF, $5}' || info "  （无备份文件）"
}

# ============================================================
# 脚本二：服务健康检查 health_check
# ============================================================
health_check() {
    section "服务健康检查"

    # 定义要检查的服务（服务名 | 进程名 | 端口 | 描述）
    declare -a services=(
        "nginx|nginx|80|Web服务器"
        "mysql|mysqld|3306|数据库"
        "redis|redis-server|6379|缓存服务"
    )

    local all_ok=true
    local report_file
    report_file="${LOG_DIR}/health_check_$(date +%Y%m%d_%H%M%S).log"
    TMP_FILES+=("$report_file")

    mkdir -p "$LOG_DIR"

    {
        echo "========================================"
        echo "  电商服务健康检查报告"
        echo "  时间：$(date '+%F %T')"
        echo "  主机：$(hostname) ($(hostname -I 2>/dev/null | awk '{print $1}'))"
        echo "========================================"
        echo ""
    } > "$report_file"

    printf "%-12s %-10s %-8s %-10s %s\n" "服务" "systemd" "端口" "进程" "状态" | tee -a "$report_file"
    printf "%-12s %-10s %-8s %-10s %s\n" "----------" "--------" "------" "--------" "------" | tee -a "$report_file"

    for entry in "${services[@]}"; do
        # 解析字段
        IFS='|' read -r svc_name proc_name port desc <<< "$entry"

        # 1. 检查 systemd 服务状态
        local svc_status
        if systemctl is-active --quiet "$svc_name" 2>/dev/null; then
            svc_status="active"
        else
            svc_status="inactive"
        fi

        # 2. 检查端口是否在监听
        local port_status
        if ss -tln 2>/dev/null | grep -q ":${port}\b"; then
            port_status="listen"
        else
            port_status="closed"
        fi

        # 3. 检查进程是否存在
        local proc_status
        if pgrep -x "$proc_name" >/dev/null 2>&1; then
            proc_status="running"
        else
            proc_status="stopped"
        fi

        # 4. 综合判断
        local overall
        if [[ "$svc_status" == "active" && "$port_status" == "listen" && "$proc_status" == "running" ]]; then
            overall="${GREEN}健康${NC}"
        elif [[ "$port_status" == "listen" || "$proc_status" == "running" ]]; then
            overall="${YELLOW}异常${NC}"
            all_ok=false
        else
            overall="${RED}宕机${NC}"
            all_ok=false
        fi

        printf "%-12s %-10s %-8s %-10s %b\n" "$svc_name" "$svc_status" "$port" "$proc_status" "$overall" | tee -a "$report_file"
    done

    echo "" | tee -a "$report_file"

    # 检查磁盘使用率
    info "检查磁盘使用率..."
    while read -r line; do
        local usage
        usage=$(echo "$line" | awk '{print int($5)}')
        local mount
        mount=$(echo "$line" | awk '{print $6}')
        if [[ $usage -ge 90 ]]; then
            warn "磁盘 $mount 使用率 ${usage}% 超过 90%！" | tee -a "$report_file"
            all_ok=false
        elif [[ $usage -ge 80 ]]; then
            warn "磁盘 $mount 使用率 ${usage}% 超过 80%" | tee -a "$report_file"
        fi
    done < <(df -h | awk 'NR>1')

    # 检查内存
    info "检查内存使用率..."
    local mem_total mem_used mem_usage
    mem_total=$(free | awk '/Mem:/ {print $2}')
    mem_used=$(free | awk '/Mem:/ {print $3}')
    if [[ $mem_total -gt 0 ]]; then
        mem_usage=$((mem_used * 100 / mem_total))
        if [[ $mem_usage -ge 90 ]]; then
            warn "内存使用率 ${mem_usage}% 超过 90%！" | tee -a "$report_file"
            all_ok=false
        else
            info "内存使用率：${mem_usage}%" | tee -a "$report_file"
        fi
    fi

    echo "" | tee -a "$report_file"
    if [[ $all_ok == true ]]; then
        success "所有服务运行正常，详细报告：$report_file"
    else
        error "发现异常，请及时处理！详细报告：$report_file"
        # 这里可扩展：发送告警邮件 / 调用 webhook / 发送飞书通知
        # 例如：curl -X POST https://hook.example.com/alert -d "service down"
        return 1
    fi
}

# ============================================================
# 脚本三：批量用户创建 create_users
# ============================================================
create_users() {
    local user_file="$1"

    section "批量用户创建"

    # 参数检查
    if [[ -z "$user_file" ]]; then
        error "请提供用户名文件"
        echo "  用法：$0 create_users <用户名文件>"
        echo "  文件格式：每行一个用户名，或 用户名:密码:组名"
        echo "  示例文件内容："
        echo "    deploy"
        echo "    dev01:Dev@2024:developers"
        echo "    tester01:Test@2024:qa"
        return 1
    fi

    # 文件存在检查
    if [[ ! -f "$user_file" ]]; then
        error "用户名文件不存在：$user_file"
        return 1
    fi

    # root 权限检查
    if [[ $UID -ne 0 ]]; then
        error "创建用户需要 root 权限，请使用 sudo 执行"
        return 1
    fi

    info "从文件读取用户列表：$user_file"
    info "文件格式：用户名[:密码:组名]"

    local created=0
    local skipped=0
    local failed=0

    while IFS= read -r line || [[ -n "$line" ]]; do
        # 跳过空行和注释
        line=$(echo "$line" | xargs)    # 去首尾空格
        [[ -z "$line" ]] && continue
        [[ "$line" == \#* ]] && continue

        # 解析字段：用户名:密码:组名
        local username password groupname
        if [[ "$line" == *:* ]]; then
            IFS=':' read -r username password groupname <<< "$line"
        else
            username="$line"
            password=""
            groupname=""
        fi

        # 用户名校验：只能字母数字下划线，不能数字开头
        if [[ ! "$username" =~ ^[a-zA-Z_][a-zA-Z0-9_-]*$ ]]; then
            warn "用户名 '$username' 不合法，跳过"
            ((skipped++))
            continue
        fi

        # 检查用户是否已存在
        if id "$username" >/dev/null 2>&1; then
            warn "用户 $username 已存在，跳过"
            ((skipped++))
            continue
        fi

        # 创建组（如指定且不存在）
        if [[ -n "$groupname" ]]; then
            if ! getent group "$groupname" >/dev/null 2>&1; then
                groupadd "$groupname" 2>/dev/null && info "创建组：$groupname"
            fi
        fi

        # 创建用户
        local useradd_opts="-m -s /bin/bash"
        if [[ -n "$groupname" ]]; then
            useradd_opts="$useradd_opts -g $groupname"
        fi

        if useradd $useradd_opts "$username" 2>/dev/null; then
            # 设置密码
            if [[ -n "$password" ]]; then
                echo "$username:$password" | chpasswd 2>/dev/null
            else
                # 无密码则锁定，需管理员后续设置
                passwd -l "$username" >/dev/null 2>&1
            fi

            # 首次登录强制改密码（可选）
            # chage -d 0 "$username"

            success "创建用户：$username${groupname:+ (组: $groupname)}"
            ((created++))
        else
            error "创建用户失败：$username"
            ((failed++))
        fi
    done < "$user_file"

    echo ""
    info "批量创建完成：成功 $created 个，跳过 $skipped 个，失败 $failed 个"

    if [[ $created -gt 0 ]]; then
        info "新用户列表："
        while IFS= read -r line; do
            line=$(echo "$line" | xargs)
            [[ -z "$line" ]] && continue
            [[ "$line" == \#* ]] && continue
            local uname
            if [[ "$line" == *:* ]]; then
                uname="${line%%:*}"
            else
                uname="$line"
            fi
            id "$uname" 2>/dev/null | sed 's/^/  /'
        done < "$user_file"
    fi
}

# ============================================================
# 主入口：参数分发
# ============================================================
main() {
    local cmd="${1:-}"

    if [[ -z "$cmd" ]]; then
        echo "用法：$0 <命令> [参数]"
        echo ""
        echo "可用命令："
        echo "  backup_db [数据库名]      数据库自动备份（默认 ecommerce）"
        echo "  health_check              服务健康检查（Nginx/MySQL/Redis）"
        echo "  create_users <文件>       从文件批量创建用户"
        echo ""
        echo "示例："
        echo "  sudo bash $0 backup_db ecommerce"
        echo "  sudo bash $0 health_check"
        echo "  sudo bash $0 create_users /tmp/users.txt"
        exit 1
    fi

    shift    # 移除命令参数

    case "$cmd" in
        backup_db)
            backup_db "$@"
            ;;
        health_check)
            health_check
            ;;
        create_users)
            create_users "$@"
            ;;
        *)
            error "未知命令：$cmd"
            echo "可用命令：backup_db | health_check | create_users"
            exit 1
            ;;
    esac
}

main "$@"
