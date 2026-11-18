#!/bin/bash
# 文件用途：压缩与解压命令练习
#           演示 tar 打包/解压 .tar.gz/.tar.bz2、gzip/gunzip、zip/unzip
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：bash 03-compression.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本在 /tmp/compression-demo/ 下完成压缩解压练习。
#   脚本可重复执行：每次清理上次结果重新创建。
#   不需要 root 权限。
# ============================================================

# 练习目录
WORK_DIR="/tmp/compression-demo"
SOURCE_DIR="$WORK_DIR/source"
EXTRACT_DIR="$WORK_DIR/extracted"

echo "================================================"
echo "  压缩与解压命令练习"
echo "  工作目录：$WORK_DIR"
echo "================================================"

# === 0. 清理与初始化 ===
echo ""
echo ">>> [0] 初始化工作目录..."
rm -rf "$WORK_DIR"
mkdir -p "$SOURCE_DIR" "$EXTRACT_DIR"

# 创建模拟项目文件作为压缩素材
mkdir -p "$SOURCE_DIR"/{backend,frontend,logs,scripts}
touch "$SOURCE_DIR/backend/app.js"
touch "$SOURCE_DIR/backend/router.js"
touch "$SOURCE_DIR/backend/config.json"
touch "$SOURCE_DIR/frontend/index.html"
touch "$SOURCE_DIR/frontend/style.css"
touch "$SOURCE_DIR/scripts/deploy.sh"
touch "$SOURCE_DIR/scripts/backup.sh"

# 创建一些日志文件
for i in 1 2 3; do
    echo "Log entry $i - $(date)" > "$SOURCE_DIR/logs/access-$i.log"
done

# 创建一个稍大的文件用于测试压缩率
for i in $(seq 1 100); do
    echo "Line $i: This is a repetitive line for compression testing. Hello Linux World." >> "$SOURCE_DIR/logs/app.log"
done

echo "    源目录结构："
tree "$SOURCE_DIR"
echo "    源目录大小：$(du -sh "$SOURCE_DIR" | cut -f1)"

# === 1. tar 打包（不压缩）===
echo ""
echo ">>> [1] tar 打包（仅打包，不压缩）..."

echo "---- tar -cvf archive.tar source/（打包）----"
cd "$WORK_DIR"
tar -cvf archive.tar source/
echo "    archive.tar 大小：$(ls -lh archive.tar | awk '{print $5}')"

echo ""
echo "---- tar -tvf archive.tar（查看包内容，不解压）----"
tar -tvf archive.tar

echo ""
echo "---- tar -xvf archive.tar -C extracted/（解压到指定目录）----"
tar -xvf archive.tar -C "$EXTRACT_DIR/"
echo "    解压后内容："
ls "$EXTRACT_DIR/source/"

# 清理解压结果，准备下一个练习
rm -rf "$EXTRACT_DIR"/*
rm -f archive.tar

# === 2. tar.gz 压缩（最常用）===
echo ""
echo ">>> [2] tar.gz 压缩（gzip，最常用）..."

echo "---- tar -zcvf archive.tar.gz source/（压缩为 .tar.gz）----"
cd "$WORK_DIR"
tar -zcvf archive.tar.gz source/
echo "    archive.tar.gz 大小：$(ls -lh archive.tar.gz | awk '{print $5}')"

echo ""
echo "---- tar -ztvf archive.tar.gz（查看压缩包内容）----"
tar -ztvf archive.tar.gz

echo ""
echo "---- tar -zxvf archive.tar.gz -C extracted/（解压到指定目录）----"
tar -zxvf archive.tar.gz -C "$EXTRACT_DIR/"
echo "    解压后验证："
ls "$EXTRACT_DIR/source/"

# 清理
rm -rf "$EXTRACT_DIR"/*
rm -f archive.tar.gz

# === 3. tar.bz2 压缩（bzip2，压缩率更高）===
echo ""
echo ">>> [3] tar.bz2 压缩（bzip2，压缩率更高）..."

echo "---- tar -jcvf archive.tar.bz2 source/（压缩为 .tar.bz2）----"
cd "$WORK_DIR"
tar -jcvf archive.tar.bz2 source/
echo "    archive.tar.bz2 大小：$(ls -lh archive.tar.bz2 | awk '{print $5}')"

echo ""
echo "---- tar -jtvf archive.tar.bz2（查看内容）----"
tar -jtvf archive.tar.bz2 | head -n 5

echo ""
echo "---- tar -jxvf archive.tar.bz2 -C extracted/（解压）----"
tar -jxvf archive.tar.bz2 -C "$EXTRACT_DIR/"
echo "    解压后验证："
ls "$EXTRACT_DIR/source/"

# 清理
rm -rf "$EXTRACT_DIR"/*
rm -f archive.tar.bz2

# === 4. tar.xz 压缩（xz，压缩率最高）===
echo ""
echo ">>> [4] tar.xz 压缩（xz，压缩率最高）..."

echo "---- tar -Jcvf archive.tar.xz source/（压缩为 .tar.xz）----"
cd "$WORK_DIR"
tar -Jcvf archive.tar.xz source/
echo "    archive.tar.xz 大小：$(ls -lh archive.tar.xz | awk '{print $5}')"

echo ""
echo "---- tar -Jtvf archive.tar.xz（查看内容）----"
tar -Jtvf archive.tar.xz | head -n 5

echo ""
echo "---- tar -Jxvf archive.tar.xz -C extracted/（解压）----"
tar -Jxvf archive.tar.xz -C "$EXTRACT_DIR/"
echo "    解压后验证："
ls "$EXTRACT_DIR/source/"

# === 5. 压缩格式对比 ===
echo ""
echo ">>> [5] 压缩格式对比..."

echo "---- 各格式文件大小对比 ----"
echo "    原始目录大小：$(du -sh "$SOURCE_DIR" | cut -f1)"
echo "    .tar      大小：$(ls -lh "$WORK_DIR/archive.tar.xz" 2>/dev/null | awk '{print $5}')（tar.xz）"

# 重新生成所有格式用于对比
cd "$WORK_DIR"
tar -cvf archive.tar source/ 2>/dev/null
tar -zcvf archive.tar.gz source/ 2>/dev/null
tar -jcvf archive.tar.bz2 source/ 2>/dev/null

echo ""
echo "    压缩格式大小对比表："
echo "    ------------------------------------------------"
printf "    %-20s %s\n" "格式" "大小"
echo "    ------------------------------------------------"
printf "    %-20s %s\n" "原始目录（du -sh）" "$(du -sh "$SOURCE_DIR" | cut -f1)"
printf "    %-20s %s\n" "archive.tar" "$(ls -lh archive.tar | awk '{print $5}')"
printf "    %-20s %s\n" "archive.tar.gz" "$(ls -lh archive.tar.gz | awk '{print $5}')"
printf "    %-20s %s\n" "archive.tar.bz2" "$(ls -lh archive.tar.bz2 | awk '{print $5}')"
printf "    %-20s %s\n" "archive.tar.xz" "$(ls -lh archive.tar.xz | awk '{print $5}')"
echo "    ------------------------------------------------"
echo "    结论：压缩率 .xz > .bz2 > .gz > .tar（不压缩）"
echo "          速度 .tar > .gz > .bz2 > .xz"

# === 6. gzip / gunzip 单文件压缩 ===
echo ""
echo ">>> [6] gzip / gunzip 单文件压缩..."

# 复制一个文件用于练习
cp "$SOURCE_DIR/logs/app.log" "$WORK_DIR/test-gzip.log"
echo "    原始文件大小：$(ls -lh "$WORK_DIR/test-gzip.log" | awk '{print $5}')"

echo ""
echo "---- gzip test-gzip.log（压缩，原文件消失）----"
cd "$WORK_DIR"
gzip test-gzip.log
ls -lh test-gzip.log.gz
echo "    压缩后大小：$(ls -lh test-gzip.log.gz | awk '{print $5}')"

echo ""
echo "---- gzip -l test-gzip.log.gz（查看压缩信息）----"
gzip -l test-gzip.log.gz

echo ""
echo "---- gunzip test-gzip.log.gz（解压）----"
gunzip test-gzip.log.gz
echo "    解压后文件：$(ls -lh test-gzip.log | awk '{print $5}')"

echo ""
echo "---- gzip -k test-gzip.log（保留原文件压缩）----"
gzip -k test-gzip.log
ls -lh test-gzip.log test-gzip.log.gz

echo ""
echo "---- zcat test-gzip.log.gz（直接查看压缩文件内容，前 3 行）----"
zcat test-gzip.log.gz | head -n 3

echo ""
echo "---- zgrep 'Line 50' test-gzip.log.gz（在压缩文件中搜索）----"
zgrep "Line 50" test-gzip.log.gz

# 清理
rm -f test-gzip.log test-gzip.log.gz

# === 7. zip / unzip 压缩 ===
echo ""
echo ">>> [7] zip / unzip 压缩..."

# 检查 zip 是否安装
if ! command -v zip >/dev/null 2>&1; then
    echo "    zip 未安装，正在安装..."
    sudo apt install -y zip unzip 2>/dev/null || {
        echo "    无法安装 zip，跳过此部分"
        echo "    手动安装：sudo apt install zip unzip"
    }
fi

if command -v zip >/dev/null 2>&1; then
    echo "---- zip -r archive.zip source/（递归压缩目录）----"
    cd "$WORK_DIR"
    zip -r archive.zip source/ > /dev/null
    echo "    archive.zip 大小：$(ls -lh archive.zip | awk '{print $5}')"

    echo ""
    echo "---- unzip -l archive.zip（查看内容）----"
    unzip -l archive.zip | head -n 10

    echo ""
    echo "---- unzip archive.zip -d extracted-zip/（解压到指定目录）----"
    mkdir -p "$WORK_DIR/extracted-zip"
    unzip archive.zip -d "$WORK_DIR/extracted-zip/" > /dev/null
    echo "    解压后内容："
    ls "$WORK_DIR/extracted-zip/source/"

    echo ""
    echo "---- zip -e secret.zip source/backend/config.json（加密码压缩）----"
    # 用 -P 指定密码（仅演示，生产环境用交互式 -e）
    zip -P "pass123" secret.zip source/backend/config.json > /dev/null
    echo "    secret.zip 大小：$(ls -lh secret.zip | awk '{print $5}')"

    echo ""
    echo "---- unzip -P pass123 secret.zip -d extracted-secret/（用密码解压）----"
    mkdir -p "$WORK_DIR/extracted-secret"
    unzip -P "pass123" secret.zip -d "$WORK_DIR/extracted-secret/" > /dev/null
    echo "    解压后内容："
    ls "$WORK_DIR/extracted-secret/source/backend/"

    # 清理
    rm -rf "$WORK_DIR/extracted-zip" "$WORK_DIR/extracted-secret"
    rm -f archive.zip secret.zip
fi

# === 8. tar 排除文件 ===
echo ""
echo ">>> [8] tar 排除特定文件..."

echo "---- tar -zcvf archive-excluded.tar.gz source/ --exclude='*.log'（排除日志文件）----"
cd "$WORK_DIR"
tar -zcvf archive-excluded.tar.gz source/ --exclude='*.log'
echo "    压缩包内容（无 .log 文件）："
tar -ztvf archive-excluded.tar.gz

echo ""
echo "---- tar -zcvf archive-excluded2.tar.gz source/ --exclude='logs'（排除 logs 目录）----"
tar -zcvf archive-excluded2.tar.gz source/ --exclude='logs'
echo "    压缩包内容（无 logs 目录）："
tar -ztvf archive-excluded2.tar.gz

# 清理
rm -f archive-excluded.tar.gz archive-excluded2.tar.gz

# === 9. tar 仅解压部分文件 ===
echo ""
echo ">>> [9] tar 仅解压部分文件..."

echo "---- 先打包完整目录 ----"
cd "$WORK_DIR"
tar -zcvf archive.tar.gz source/ > /dev/null

echo ""
echo "---- tar -zxvf archive.tar.gz source/backend/app.js（仅解压单个文件）----"
mkdir -p "$WORK_DIR/extract-partial"
tar -zxvf archive.tar.gz -C "$WORK_DIR/extract-partial/" source/backend/app.js
echo "    解压结果："
ls -l "$WORK_DIR/extract-partial/source/backend/"

echo ""
echo "---- tar -zxvf archive.tar.gz --wildcards 'source/backend/*.js'（通配符解压多个）----"
rm -rf "$WORK_DIR/extract-partial"
mkdir -p "$WORK_DIR/extract-partial"
tar -zxvf archive.tar.gz -C "$WORK_DIR/extract-partial/" --wildcards 'source/backend/*.js'
echo "    解压结果："
find "$WORK_DIR/extract-partial" -type f

# 清理
rm -rf "$WORK_DIR/extract-partial"

# === 10. 实战场景：备份项目目录 ===
echo ""
echo ">>> [10] 实战场景：备份电商项目..."

BACKUP_DIR="$WORK_DIR/backups"
mkdir -p "$BACKUP_DIR"

echo "---- 模拟项目备份（带时间戳）----"
BACKUP_FILE="ecommerce-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
echo "    备份文件名：$BACKUP_FILE"
echo "    备份命令：tar -zcvf $BACKUP_FILE source/"
cd "$WORK_DIR"
tar -zcvf "$BACKUP_DIR/$BACKUP_FILE" source/ > /dev/null
echo "    备份完成，大小：$(ls -lh "$BACKUP_DIR/$BACKUP_FILE" | awk '{print $5}')"

echo ""
echo "---- 查看备份内容 ----"
tar -ztvf "$BACKUP_DIR/$BACKUP_FILE"

echo ""
echo "---- 模拟恢复：解压备份到 restore/ 目录 ----"
mkdir -p "$WORK_DIR/restore"
tar -zxvf "$BACKUP_DIR/$BACKUP_FILE" -C "$WORK_DIR/restore/" > /dev/null
echo "    恢复后内容："
tree "$WORK_DIR/restore/source/"

echo ""
echo "---- 模拟清理旧备份（保留最近 2 个）----"
# 创建几个模拟旧备份
for i in 1 2 3; do
    touch "$BACKUP_DIR/old-backup-2026070$i.tar.gz"
done
echo "    清理前备份列表："
ls -lt "$BACKUP_DIR"
# 保留最近 2 个，删除其余
cd "$BACKUP_DIR"
ls -t | tail -n +3 | xargs rm -f
echo "    清理后备份列表："
ls -lt "$BACKUP_DIR"

# === 11. 软链接补充演示 ===
echo ""
echo ">>> [11] 软链接与硬链接演示..."

LINK_DIR="$WORK_DIR/links"
mkdir -p "$LINK_DIR"

# 创建源文件
echo "Hello Linux Link Demo" > "$LINK_DIR/original.txt"

echo "---- 创建硬链接 ----"
ln "$LINK_DIR/original.txt" "$LINK_DIR/hard.txt"
echo "    inode 对比（应相同）："
ls -li "$LINK_DIR/original.txt" "$LINK_DIR/hard.txt"

echo ""
echo "---- 创建软链接 ----"
ln -s "$LINK_DIR/original.txt" "$LINK_DIR/soft.txt"
echo "    inode 对比（应不同）："
ls -li "$LINK_DIR/original.txt" "$LINK_DIR/soft.txt"

echo ""
echo "---- readlink soft.txt（查看软链接指向）----"
readlink "$LINK_DIR/soft.txt"

echo ""
echo "---- readlink -f soft.txt（解析为绝对路径）----"
readlink -f "$LINK_DIR/soft.txt"

echo ""
echo "---- 删除原文件后观察 ----"
rm "$LINK_DIR/original.txt"
echo "    hard.txt 内容（仍可读，数据仍在）："
cat "$LINK_DIR/hard.txt"
echo "    soft.txt 内容（悬空链接，报错）："
cat "$LINK_DIR/soft.txt" 2>&1 || true

echo ""
echo "================================================"
echo "  压缩与解压命令练习完成！"
echo "  工作目录保留在：$WORK_DIR"
echo "  清理：rm -rf $WORK_DIR"
echo "================================================"
