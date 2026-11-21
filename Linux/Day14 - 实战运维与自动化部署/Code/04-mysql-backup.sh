#!/bin/bash
# ============================================================
# 文件名：04-mysql-backup.sh
# 用途：MySQL 自动备份脚本
# 场景：电商服务器 192.168.1.100 数据库定时备份
# 说明：mysqldump 全量备份、gzip 压缩、按日期命名
#       保留最近 30 天、备份完成检查、crontab 配置示例
# 运行：sudo bash 04-mysql-backup.sh
# 权限：需要 root/sudo 权限（读取 MySQL 凭证）
# crontab：0 2 * * * root /opt/ecommerce/scripts/04-mysql-backup.sh
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
error()   { echo -e "${RED}[ERROR]${NC} $1"; }
section() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

# ---------- 日志记录函数 ----------
LOG_FILE="/var/log/mysql-backup-$(date +%Y%m%d-%H%M%S).log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# ---------- 错误处理函数 ----------
handle_error() {
    local exit_code=$?
    error "备份失败！退出码：${exit_code}"
    error "请检查日志：${LOG_FILE}"
    # 备份失败时发送告警（可选）
    # echo "MySQL 备份失败：$(date)" | mail -s "MySQL Backup FAILED" ops@example.com
    exit ${exit_code}
}
trap 'handle_error' ERR

# ---------- 权限检查 ----------
if [ "${EUID}" -ne 0 ]; then
    error "此脚本需要 root 权限执行，请使用 sudo"
    echo "  sudo bash $0"
    exit 1
fi

# ============================================================
# 配置变量（根据实际环境修改）
# ============================================================
MYSQL_USER="root"
MYSQL_PASSWORD=""                 # 从配置文件读取
MYSQL_HOST="127.0.0.1"
MYSQL_PORT="3306"

# 数据库列表（空格分隔，备份多个数据库）
DATABASES="ecommerce"

# 备份配置
BACKUP_DIR="/opt/ecommerce/backup/mysql"
RETENTION_DAYS=30                 # 保留天数
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_HOST=$(hostname -s)

# 压缩配置
COMPRESS=true                     # 是否压缩

# 读取 MySQL 密码（从配置文件）
MYSQL_ENV_FILE="/opt/ecommerce/config/mysql.env"
if [ -f "${MYSQL_ENV_FILE}" ]; then
    source "${MYSQL_ENV_FILE}"
    MYSQL_PASSWORD="${MYSQL_ROOT_PASSWORD:-}"
    info "从 ${MYSQL_ENV_FILE} 读取 MySQL 凭证"
else
    warn "未找到 MySQL 凭证文件 ${MYSQL_ENV_FILE}"
    warn "请手动输入 MySQL root 密码："
    read -s MYSQL_PASSWORD
fi

# 检查密码是否设置
if [ -z "${MYSQL_PASSWORD}" ]; then
    error "MySQL 密码为空，无法备份"
    exit 1
fi

log "MySQL 自动备份脚本启动"
log "服务器：192.168.1.100"
log "备份目录：${BACKUP_DIR}"
log "保留天数：${RETENTION_DAYS} 天"

# ============================================================
# 第一部分：准备工作
# ============================================================
section "第一部分：准备工作"

# 创建备份目录（幂等）
log "创建备份目录"
mkdir -p "${BACKUP_DIR}"
chown -R root:root "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"
success "备份目录已就绪：${BACKUP_DIR}"

# 检查 MySQL 是否运行
log "检查 MySQL 服务状态"
if ! systemctl is-active --quiet mysql; then
    error "MySQL 服务未运行，无法备份"
    exit 1
fi
success "MySQL 服务运行正常"

# 检查 MySQL 连接
log "验证 MySQL 连接"
if ! mysql -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" -h "${MYSQL_HOST}" -P "${MYSQL_PORT}" -e "SELECT 1" &> /dev/null; then
    error "MySQL 连接失败，请检查凭证"
    exit 1
fi
success "MySQL 连接正常"

# 显示数据库列表
log "待备份数据库：${DATABASES}"

# ============================================================
# 第二部分：执行备份
# ============================================================
section "第二部分：执行全量备份"

# 备份统计
TOTAL_SIZE=0
BACKUP_COUNT=0
FAILED_COUNT=0

for DB in ${DATABASES}; do
    log "备份数据库：${DB}"

    # 备份文件名
    BACKUP_FILE="${BACKUP_DIR}/${DB}_${BACKUP_HOST}_${BACKUP_DATE}.sql"

    # 执行 mysqldump 全量备份
    # 参数说明：
    #   --single-transaction  → InnoDB 一致性快照（不锁表）
    #   --quick               → 不缓存整个结果集（大表必须）
    #   --routines            → 备份存储过程和函数
    #   --triggers            → 备份触发器
    #   --events              → 备份事件调度器
    #   --set-gtid-purged=OFF → 不在备份中写入 GTID 信息
    #   --hex-blob            → 十六进制备份 BLOB 字段
    mysqldump -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" -h "${MYSQL_HOST}" -P "${MYSQL_PORT}" \
        --single-transaction \
        --quick \
        --routines \
        --triggers \
        --events \
        --set-gtid-purged=OFF \
        --hex-blob \
        "${DB}" > "${BACKUP_FILE}" 2>/dev/null

    # 检查备份是否成功
    if [ $? -eq 0 ] && [ -s "${BACKUP_FILE}" ]; then
        # 压缩备份文件
        if [ "${COMPRESS}" = true ]; then
            log "压缩备份文件"
            gzip "${BACKUP_FILE}"
            BACKUP_FILE="${BACKUP_FILE}.gz"
        fi

        # 获取备份文件大小
        FILE_SIZE=$(stat -c %s "${BACKUP_FILE}" 2>/dev/null || stat -f %z "${BACKUP_FILE}" 2>/dev/null)
        FILE_SIZE_MB=$((FILE_SIZE / 1024 / 1024))

        # 计算备份文件 MD5（用于完整性校验）
        FILE_MD5=$(md5sum "${BACKUP_FILE}" | awk '{print $1}')

        success "数据库 ${DB} 备份成功"
        info "  文件：${BACKUP_FILE}"
        info "  大小：${FILE_SIZE_MB} MB"
        info "  MD5：${FILE_MD5}"

        TOTAL_SIZE=$((TOTAL_SIZE + FILE_SIZE))
        BACKUP_COUNT=$((BACKUP_COUNT + 1))

        # 记录备份信息到日志文件
        echo "${BACKUP_DATE} | ${DB} | ${BACKUP_FILE} | ${FILE_SIZE_MB}MB | ${FILE_MD5}" >> "${BACKUP_DIR}/backup_history.log"
    else
        error "数据库 ${DB} 备份失败！"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        # 清理空文件
        rm -f "${BACKUP_FILE}"
    fi
done

echo ""

# ============================================================
# 第三部分：备份完成检查
# ============================================================
section "第三部分：备份完成检查"

TOTAL_SIZE_MB=$((TOTAL_SIZE / 1024 / 1024))

info "备份统计："
echo "  ┌──────────────────┬──────────────────────────┐"
echo "  │ 统计项           │ 值                       │"
echo "  ├──────────────────┼──────────────────────────┤"
echo "  │ 备份时间         │ ${BACKUP_DATE}           │"
echo "  │ 成功数量         │ ${BACKUP_COUNT}                      │"
echo "  │ 失败数量         │ ${FAILED_COUNT}                      │"
echo "  │ 总大小           │ ${TOTAL_SIZE_MB} MB                  │"
echo "  │ 备份目录         │ ${BACKUP_DIR}  │"
echo "  └──────────────────┴──────────────────────────┘"
echo ""

if [ "${FAILED_COUNT}" -gt 0 ]; then
    error "有 ${FAILED_COUNT} 个数据库备份失败！"
    exit 1
fi

success "所有数据库备份成功！"

# ============================================================
# 第四部分：清理过期备份
# ============================================================
section "第四部分：清理过期备份"

log "清理 ${RETENTION_DAYS} 天前的旧备份"
DELETED_COUNT=$(find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -type f -print -delete | wc -l)
DELETED_COUNT=${DELETED_COUNT:-0}

if [ "${DELETED_COUNT}" -gt 0 ]; then
    success "已清理 ${DELETED_COUNT} 个过期备份"
else
    info "无过期备份需清理"
fi

# 显示当前备份列表
echo ""
log "当前备份文件列表："
ls -lh "${BACKUP_DIR}"/*.sql.gz 2>/dev/null || info "无备份文件"
echo ""

# 统计备份占用空间
BACKUP_TOTAL=$(du -sh "${BACKUP_DIR}" 2>/dev/null | awk '{print $1}')
info "备份目录总占用：${BACKUP_TOTAL}"

# ============================================================
# 第五部分：备份验证（可选）
# ============================================================
section "第五部分：备份验证"

# 验证最新备份文件的完整性
LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | head -1)

if [ -n "${LATEST_BACKUP}" ]; then
    log "验证最新备份文件：${LATEST_BACKUP}"

    # 检查 gzip 完整性
    if gzip -t "${LATEST_BACKUP}" 2>/dev/null; then
        success "gzip 完整性验证通过"
    else
        error "gzip 完整性验证失败！备份文件可能损坏"
        exit 1
    fi

    # 检查备份内容（解压查看是否有 SQL 语句）
    SQL_CHECK=$(zcat "${LATEST_BACKUP}" | head -100 | grep -c "CREATE TABLE\|INSERT INTO\|CREATE DATABASE" 2>/dev/null || echo "0")
    if [ "${SQL_CHECK}" -gt 0 ]; then
        success "备份内容验证通过（包含 ${SQL_CHECK} 条 SQL 语句）"
    else
        warn "备份内容可能为空或格式异常"
    fi
else
    warn "未找到备份文件，跳过验证"
fi

echo ""

# ============================================================
# 第六部分：crontab 配置说明
# ============================================================
section "第六部分：crontab 配置说明"

info "配置定时备份（每天凌晨 2 点执行）："
echo ""
echo "  # 方式一：系统级 crontab（推荐）"
echo "  sudo tee /etc/cron.d/mysql-backup <<'CRON'"
echo "  # MySQL 自动备份（每天凌晨 2 点）"
echo "  0 2 * * * root /opt/ecommerce/scripts/04-mysql-backup.sh >> /var/log/mysql-backup-cron.log 2>&1"
echo "  CRON"
echo ""
echo "  # 方式二：crontab -e 编辑"
echo "  sudo crontab -e"
echo "  # 添加以下行："
echo "  0 2 * * * /opt/ecommerce/scripts/04-mysql-backup.sh >> /var/log/mysql-backup-cron.log 2>&1"
echo ""
echo "  # 验证 cron 是否已配置"
echo "  sudo crontab -l | grep mysql-backup"
echo ""

info "其他备份频率示例："
echo "  ┌───────────────────┬──────────────────────────────────────┐"
echo "  │ 频率              │ cron 表达式                          │"
echo "  ├───────────────────┼──────────────────────────────────────┤"
echo "  │ 每天凌晨 2 点     │ 0 2 * * *                            │"
echo "  │ 每 6 小时         │ 0 */6 * * *                          │"
echo "  │ 每周日凌晨 2 点   │ 0 2 * * 0                            │"
echo "  │ 每月 1 号凌晨 2 点│ 0 2 1 * *                            │"
echo "  └───────────────────┴──────────────────────────────────────┘"
echo ""

# ============================================================
# 第七部分：备份恢复说明
# ============================================================
section "第七部分：备份恢复说明"

info "备份恢复步骤："
echo ""
echo "  # 1. 解压备份文件（如已压缩）"
echo "  gunzip ${BACKUP_DIR}/ecommerce_${BACKUP_HOST}_${BACKUP_DATE}.sql.gz"
echo ""
echo "  # 2. 恢复到 MySQL"
echo "  mysql -u root -p ecommerce < ${BACKUP_DIR}/ecommerce_${BACKUP_HOST}_${BACKUP_DATE}.sql"
echo ""
echo "  # 3. 或恢复到新数据库"
echo "  mysql -u root -p -e 'CREATE DATABASE ecommerce_restore CHARACTER SET utf8mb4;'"
echo "  mysql -u root -p ecommerce_restore < ${BACKUP_DIR}/ecommerce_${BACKUP_HOST}_${BACKUP_DATE}.sql"
echo ""
echo "  # 4. 验证恢复结果"
echo "  mysql -u root -p -e 'USE ecommerce; SHOW TABLES;'"
echo "  mysql -u root -p -e 'USE ecommerce; SELECT COUNT(*) FROM users;'"
echo ""

warn "恢复注意事项："
echo "  1. 恢复前先停应用（避免恢复期间有写入）"
echo "  2. 恢复前备份当前数据（防止覆盖）"
echo "  3. 大数据库恢复可能需要较长时间"
echo "  4. 恢复后验证数据完整性（行数/关键字段）"
echo "  5. 恢复后重启应用并验证功能"
echo ""

# ============================================================
# 第八部分：备份策略建议
# ============================================================
section "第八部分：备份策略建议"

info "3-2-1 备份原则："
echo "  ┌───┬──────────────────────────────────────────────────┐"
echo "  │ 3 │ 至少保留 3 份数据                               │"
echo "  │ 2 │ 存储在 2 种不同介质（本地磁盘 + 对象存储）       │"
echo "  │ 1 │ 至少 1 份异地（云存储/异地机房）                │"
echo "  └───┴──────────────────────────────────────────────────┘"
echo ""

info "电商场景备份策略建议："
echo "  ┌─────────────────┬──────────────────┬──────────────────────┐"
echo "  │ 备份类型        │ 频率             │ 保留时间             │"
echo "  ├─────────────────┼──────────────────┼──────────────────────┤"
echo "  │ 全量备份        │ 每天凌晨 2 点    │ 30 天                │"
echo "  │ 增量备份(binlog) │ 实时             │ 7 天                 │"
echo "  │ 周备份          │ 每周日           │ 12 周                │"
echo "  │ 月备份          │ 每月 1 号        │ 12 月                │"
echo "  │ 异地备份        │ 每天上传到 OSS   │ 90 天                │"
echo "  └─────────────────┴──────────────────┴──────────────────────┘"
echo ""

info "异地备份命令（上传到对象存储）："
echo "  # 阿里云 OSS"
echo "  ossutil cp ${BACKUP_DIR}/ecommerce_*.sql.gz oss://backup-bucket/mysql/"
echo ""
echo "  # AWS S3"
echo "  aws s3 cp ${BACKUP_DIR}/ecommerce_*.sql.gz s3://backup-bucket/mysql/"
echo ""
echo "  # 腾讯云 COS"
echo "  coscli cp ${BACKUP_DIR}/ecommerce_*.sql.gz cos://backup-bucket/mysql/"
echo ""

success "MySQL 备份脚本执行完成！"
log "日志文件：${LOG_FILE}"
log "备份历史：${BACKUP_DIR}/backup_history.log"
