#!/bin/bash
# 文件用途：文件查找命令练习
#           演示 find 各种条件、locate、which/whereis
#           在 /opt/ecommerce/ 下查找文件
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：bash 02-file-search.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本在 /opt/ecommerce/ 下完成文件查找练习。
#   脚本会先创建一些模拟文件作为查找素材。
#   脚本可重复执行。
#   不需要 root 权限（若 /opt/ecommerce 无写权限则改用 /tmp）。
# ============================================================

# 项目根目录
PROJECT_ROOT="/opt/ecommerce"

# 如果 /opt/ecommerce 不存在或无写权限，使用 /tmp 备用目录
if [ ! -d "$PROJECT_ROOT" ] || [ ! -w "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="/tmp/ecommerce-search"
fi

echo "================================================"
echo "  文件查找命令练习"
echo "  查找目录：$PROJECT_ROOT"
echo "================================================"

# === 0. 创建查找素材（模拟电商项目文件结构）===
echo ""
echo ">>> [0] 创建查找素材..."

# 创建目录结构
mkdir -p "$PROJECT_ROOT"/{backend/{src,config,tests},frontend/{src,dist,assets},logs/nginx,scripts,backup,data/uploads}

# 创建各类文件
touch "$PROJECT_ROOT/backend/src/app.js"
touch "$PROJECT_ROOT/backend/src/router.js"
touch "$PROJECT_ROOT/backend/src/model.js"
touch "$PROJECT_ROOT/backend/src/utils.js"
touch "$PROJECT_ROOT/backend/config/database.json"
touch "$PROJECT_ROOT/backend/config/redis.json"
touch "$PROJECT_ROOT/backend/config/app.env"
touch "$PROJECT_ROOT/backend/tests/user.test.js"
touch "$PROJECT_ROOT/backend/tests/order.test.js"
touch "$PROJECT_ROOT/frontend/src/index.html"
touch "$PROJECT_ROOT/frontend/src/main.js"
touch "$PROJECT_ROOT/frontend/src/style.css"
touch "$PROJECT_ROOT/frontend/assets/logo.png"
touch "$PROJECT_ROOT/scripts/deploy.sh"
touch "$PROJECT_ROOT/scripts/backup.sh"
touch "$PROJECT_ROOT/scripts/health-check.sh"

# 创建一些日志文件（不同时间、大小）
for i in $(seq 1 5); do
    head -c "${i}K" /dev/urandom > "$PROJECT_ROOT/logs/nginx/access-$i.log" 2>/dev/null || \
    dd if=/dev/zero of="$PROJECT_ROOT/logs/nginx/access-$i.log" bs=1024 count="$i" 2>/dev/null
done

# 创建一些临时文件
touch "$PROJECT_ROOT/backend/src/~temp.js"
touch "$PROJECT_ROOT/data/cache.tmp"
touch "$PROJECT_ROOT/backup/.gitkeep"

# 创建几个大文件（用于 -size 练习）
dd if=/dev/zero of="$PROJECT_ROOT/data/bigfile.bin" bs=1M count=2 2>/dev/null
dd if=/dev/zero of="$PROJECT_ROOT/data/uploads/large-upload.dat" bs=1M count=1 2>/dev/null

# 创建软链接（用于 -type l 练习）
ln -sf "$PROJECT_ROOT/backend/src/app.js" "$PROJECT_ROOT/backend/current-app.js"

echo "    查找素材已创建，目录结构："
tree -L 3 "$PROJECT_ROOT" 2>/dev/null || find "$PROJECT_ROOT" -maxdepth 3 | sort

# === 1. find 基本查找（按名称）===
echo ""
echo ">>> [1] find 按名称查找..."

echo "---- find -name '*.js'（查找所有 .js 文件）----"
find "$PROJECT_ROOT" -name "*.js"

echo ""
echo "---- find -iname '*.JS'（忽略大小写）----"
find "$PROJECT_ROOT" -iname "*.JS"

echo ""
echo "---- find -name 'database*'（查找以 database 开头的文件）----"
find "$PROJECT_ROOT" -name "database*"

echo ""
echo "---- find -name '*.json'（查找所有 JSON 配置文件）----"
find "$PROJECT_ROOT" -name "*.json"

# === 2. find 按类型查找 ===
echo ""
echo ">>> [2] find 按类型查找..."

echo "---- find -type f（仅普通文件，前 10 个）----"
find "$PROJECT_ROOT" -type f | head -n 10

echo ""
echo "---- find -type d（仅目录）----"
find "$PROJECT_ROOT" -type d

echo ""
echo "---- find -type l（仅符号链接）----"
find "$PROJECT_ROOT" -type l

# === 3. find 按大小查找 ===
echo ""
echo ">>> [3] find 按大小查找..."

echo "---- find -size +1M（大于 1MB 的文件）----"
find "$PROJECT_ROOT" -size +1M -exec ls -lh {} \;

echo ""
echo "---- find -size -1k（小于 1KB 的文件，前 5 个）----"
find "$PROJECT_ROOT" -size -1k -type f | head -n 5

echo ""
echo "---- find -size +1k -size -2k（1KB 到 2KB 之间）----"
find "$PROJECT_ROOT" -size +1k -size -2k -exec ls -lh {} \;

# === 4. find 按时间查找 ===
echo ""
echo ">>> [4] find 按时间查找..."

echo "---- find -mmin -60（60 分钟内修改过的文件）----"
find "$PROJECT_ROOT" -mmin -60 -type f | head -n 5

echo ""
echo "---- find -mtime -1（1 天内修改过的文件）----"
find "$PROJECT_ROOT" -mtime -1 -type f | wc -l
echo "    （以上为 1 天内修改的文件数）"

echo ""
echo "---- find -mtime +0（1 天前修改过的文件，应无结果）----"
find "$PROJECT_ROOT" -mtime +0 -type f | wc -l
echo "    （以上为 1 天前修改的文件数）"

# === 5. find 按用户与权限查找 ===
echo ""
echo ">>> [5] find 按用户与权限查找..."

echo "---- find -user \$USER（属于当前用户的文件，前 5 个）----"
find "$PROJECT_ROOT" -user "$USER" -type f | head -n 5

echo ""
echo "---- find -perm 644（权限恰好 644，前 5 个）----"
find "$PROJECT_ROOT" -perm 644 -type f | head -n 5

echo ""
echo "---- find -perm -644（权限至少包含 644，前 3 个）----"
find "$PROJECT_ROOT" -perm -644 -type f | head -n 3

# === 6. find 逻辑组合 ===
echo ""
echo ">>> [6] find 逻辑组合..."

echo "---- find -name '*.js' -o -name '*.json'（JS 或 JSON 文件）----"
find "$PROJECT_ROOT" \( -name "*.js" -o -name "*.json" \) -type f

echo ""
echo "---- find -name '*.js' -a -size +1k（JS 文件且大于 1KB）----"
find "$PROJECT_ROOT" -name "*.js" -a -size +1k -type f

echo ""
echo "---- find -not -name '*.js'（不是 JS 的文件，前 5 个）----"
find "$PROJECT_ROOT" -type f -not -name "*.js" | head -n 5

echo ""
echo "---- find -name '*.tmp' -o -name '~*'（临时文件）----"
find "$PROJECT_ROOT" \( -name "*.tmp" -o -name "~*" \) -type f

# === 7. find 动作（-exec / -delete）===
echo ""
echo ">>> [7] find 动作..."

echo "---- find -name '*.log' -exec wc -l {} \\;（统计每个日志行数）----"
find "$PROJECT_ROOT" -name "*.log" -exec wc -l {} \;

echo ""
echo "---- find -name '*.log' -exec ls -lh {} +（批量显示详情，性能更好）----"
find "$PROJECT_ROOT" -name "*.log" -exec ls -lh {} +

echo ""
echo "---- find -name '*.log' -exec ls -lh {} \\;（逐个显示，性能较差）----"
find "$PROJECT_ROOT" -name "*.log" -exec ls -lh {} \;

echo ""
echo "---- find -name '*.tmp' -print（先预览要删除的临时文件）----"
find "$PROJECT_ROOT" -name "*.tmp" -print

echo ""
echo "---- find -name '*.tmp' -delete（删除临时文件）----"
find "$PROJECT_ROOT" -name "*.tmp" -delete
echo "    删除后剩余 .tmp 文件数：$(find "$PROJECT_ROOT" -name "*.tmp" | wc -l)"

echo ""
echo "---- find -name '~*' -delete（删除以 ~ 开头的临时文件）----"
find "$PROJECT_ROOT" -name "~*" -delete
echo "    删除后剩余 ~ 开头文件数：$(find "$PROJECT_ROOT" -name "~*" | wc -l)"

echo ""
echo "---- find -empty（查找空文件与空目录）----"
find "$PROJECT_ROOT" -empty

# === 8. find 综合实战 ===
echo ""
echo ">>> [8] find 综合实战场景..."

echo "---- 场景 1：找出所有 .js 文件并按修改时间排序（最新在前）----"
find "$PROJECT_ROOT" -name "*.js" -type f -printf '%T+ %p\n' 2>/dev/null | sort -r | head -n 5
# 注：-printf 是 GNU find 扩展，非 POSIX 标准

echo ""
echo "---- 场景 2：统计各类型文件数量 ----"
echo "    .js 文件：$(find "$PROJECT_ROOT" -name "*.js" | wc -l)"
echo "    .json 文件：$(find "$PROJECT_ROOT" -name "*.json" | wc -l)"
echo "    .sh 文件：$(find "$PROJECT_ROOT" -name "*.sh" | wc -l)"
echo "    .log 文件：$(find "$PROJECT_ROOT" -name "*.log" | wc -l)"
echo "    .html 文件：$(find "$PROJECT_ROOT" -name "*.html" | wc -l)"

echo ""
echo "---- 场景 3：计算 backend 目录总大小 ----"
echo "    backend 目录大小：$(du -sh "$PROJECT_ROOT/backend" | cut -f1)"

echo ""
echo "---- 场景 4：找出最近修改的 3 个文件 ----"
find "$PROJECT_ROOT" -type f -printf '%T+ %p\n' 2>/dev/null | sort -r | head -n 3

echo ""
echo "---- 场景 5：找出大于 100KB 的文件并按大小排序 ----"
find "$PROJECT_ROOT" -size +100k -type f -exec ls -lh {} + 2>/dev/null | sort -k5 -h

# === 9. locate 命令演示 ===
echo ""
echo ">>> [9] locate 命令演示..."

if command -v locate >/dev/null 2>&1; then
    echo "---- locate app.js（查找名为 app.js 的文件，前 5 个）----"
    locate app.js 2>/dev/null | head -n 5 || echo "    （数据库可能未建立，执行 sudo updatedb）"

    echo ""
    echo "---- locate -i nginx.conf（忽略大小写）----"
    locate -i nginx.conf 2>/dev/null | head -n 5

    echo ""
    echo "---- locate -c '.sh$'（统计 .sh 文件数量）----"
    locate -c '\.sh$' 2>/dev/null || echo "    （正则需用 -r 选项）"
else
    echo "    locate 未安装，可执行：sudo apt install -y plocate"
    echo "    安装后执行：sudo updatedb 建立数据库"
    echo ""
    echo "    locate 与 find 对比："
    echo "      locate  - 查数据库，速度快，但不实时"
    echo "      find    - 遍历目录，速度慢，但实时准确"
fi

# === 10. which / whereis / type 命令演示 ===
echo ""
echo ">>> [10] which / whereis / type 命令演示..."

echo "---- which python3（查找 python3 命令路径）----"
which python3 2>/dev/null || echo "    python3 未安装"

echo ""
echo "---- which bash（查找 bash 路径）----"
which bash

echo ""
echo "---- which -a bash（显示所有匹配）----"
which -a bash

echo ""
echo "---- whereis python3（查找二进制、源码、man）----"
whereis python3 2>/dev/null || echo "    python3 未安装"

echo ""
echo "---- whereis -b ls（仅二进制）----"
whereis -b ls

echo ""
echo "---- whereis -m ls（仅 man 手册）----"
whereis -m ls

echo ""
echo "---- type ls（查看命令类型）----"
type ls

echo ""
echo "---- type cd（cd 是 shell 内建命令）----"
type cd

echo ""
echo "---- type ll（可能是别名）----"
type ll 2>/dev/null || echo "    ll 未定义"

# === 11. 综合练习：模拟运维查找任务 ===
echo ""
echo ">>> [11] 综合练习：运维查找任务..."

echo "---- 任务 1：找出所有 .env 配置文件（可能含敏感信息，需重点保护）----"
find "$PROJECT_ROOT" -name "*.env" -o -name ".env*" | head -n 5

echo ""
echo "---- 任务 2：找出所有脚本文件并显示权限 ----"
find "$PROJECT_ROOT" -name "*.sh" -exec ls -l {} \;

echo ""
echo "---- 任务 3：找出 data 目录下的大文件（>500KB）----"
find "$PROJECT_ROOT/data" -size +500k -exec ls -lh {} \;

echo ""
echo "---- 任务 4：统计项目总文件数、目录数、总大小 ----"
echo "    文件总数：$(find "$PROJECT_ROOT" -type f | wc -l)"
echo "    目录总数：$(find "$PROJECT_ROOT" -type d | wc -l)"
echo "    项目大小：$(du -sh "$PROJECT_ROOT" | cut -f1)"

# 清理软链接
rm -f "$PROJECT_ROOT/backend/current-app.js"

echo ""
echo "================================================"
echo "  文件查找命令练习完成！"
echo "  查找素材保留在：$PROJECT_ROOT"
echo "  可继续执行：bash 03-compression.sh 练习压缩解压"
echo "================================================"
