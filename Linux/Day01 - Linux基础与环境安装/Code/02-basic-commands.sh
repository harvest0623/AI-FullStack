#!/bin/bash
# 文件用途：Linux 基础命令练习脚本
#           演示 ls/cd/pwd/mkdir/touch/cp/mv/rm 等基础命令
#           全部在 /tmp 下操作，不影响系统
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：bash 02-basic-commands.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本在 /tmp/linux-day01/ 下完成基础命令练习。
#   脚本可重复执行：每次先清理上次的练习目录再重新创建。
#   不需要 root 权限。
# ============================================================

# 练习根目录（每次执行都重新创建，保证可重复执行）
PRACTICE_DIR="/tmp/linux-day01"

echo "================================================"
echo "  Linux 基础命令练习"
echo "  练习目录：$PRACTICE_DIR"
echo "================================================"

# === 0. 清理上次练习目录（保证可重复执行）===
if [ -d "$PRACTICE_DIR" ]; then
    echo ""
    echo ">>> [0] 清理上次的练习目录..."
    rm -rf "$PRACTICE_DIR"
    echo "    已删除旧目录 $PRACTICE_DIR"
fi

# === 1. ls 命令演示 ===
# ls 是最常用的命令，用于列出目录内容
echo ""
echo ">>> [1] ls 命令演示..."
mkdir -p "$PRACTICE_DIR/ls-demo"
cd "$PRACTICE_DIR/ls-demo"

# 创建一些练习文件
touch file1.txt file2.txt file3.log .hiddenfile
mkdir -p subdir

echo "---- ls（默认：不显示隐藏文件，按列显示）----"
ls

echo ""
echo "---- ls -a（显示所有文件，含 . 开头的隐藏文件）----"
ls -a

echo ""
echo "---- ls -l（长格式：权限/链接数/所有者/大小/时间）----"
ls -l

echo ""
echo "---- ls -la（长格式 + 显示隐藏文件）----"
ls -la

echo ""
echo "---- ls -lh（文件大小人类可读 K/M/G）----"
ls -lh

echo ""
echo "---- ls -lt（按修改时间倒序，最新在前）----"
ls -lt

echo ""
echo "---- ls -lrt（按修改时间正序，最旧在前）----"
ls -lrt

echo ""
echo "---- ls -R（递归列出子目录）----"
ls -R

# === 2. cd 与 pwd 命令演示 ===
# cd 切换目录，pwd 显示当前目录
echo ""
echo ">>> [2] cd 与 pwd 命令演示..."
cd "$PRACTICE_DIR"

echo "---- pwd（显示当前工作目录的绝对路径）----"
pwd

echo ""
echo "---- cd ls-demo（进入子目录）+ pwd ----"
cd ls-demo
pwd

echo ""
echo "---- cd ..（返回上级目录）+ pwd ----"
cd ..
pwd

echo ""
echo "---- cd ~（回到家目录）+ pwd ----"
cd ~
pwd

echo ""
echo "---- cd -（回到上一次所在目录）+ pwd ----"
cd -
pwd

# 回到练习目录继续
cd "$PRACTICE_DIR"

# === 3. mkdir 命令演示 ===
# mkdir 创建目录，-p 递归创建父目录
echo ""
echo ">>> [3] mkdir 命令演示..."

echo "---- mkdir single-dir（创建单个目录）----"
mkdir single-dir
ls -d */

echo ""
echo "---- mkdir dir1 dir2 dir3（同时创建多个目录）----"
mkdir dir1 dir2 dir3
ls -d */

echo ""
echo "---- mkdir -p a/b/c/d（递归创建多级目录）----"
mkdir -p a/b/c/d
tree a

echo ""
echo "---- mkdir -p project/{backend/{src,test},frontend,docs}（花括号展开创建目录树）----"
mkdir -p project/{backend/{src,test},frontend,docs}
tree project

# === 4. touch 命令演示 ===
# touch 创建空文件或更新文件时间戳
echo ""
echo ">>> [4] touch 命令演示..."
cd "$PRACTICE_DIR/project/backend/src"

echo "---- touch app.js（创建空文件）----"
touch app.js
ls -l

echo ""
echo "---- touch utils.js config.js（同时创建多个文件）----"
touch utils.js config.js
ls -l

echo ""
echo "---- touch file{1..5}.txt（花括号批量创建）----"
touch file{1..5}.txt
ls -l

echo ""
echo "---- touch app.js（文件已存在则更新时间戳）----"
echo "    修改前时间：$(stat -c '%y' app.js)"
sleep 1
touch app.js
echo "    修改后时间：$(stat -c '%y' app.js)"

# === 5. cp 命令演示 ===
# cp 复制文件或目录
echo ""
echo ">>> [5] cp 命令演示..."
cd "$PRACTICE_DIR/project"

echo "---- cp backend/src/app.js backend/src/app.bak.js（复制文件）----"
cp backend/src/app.js backend/src/app.bak.js
ls -l backend/src/

echo ""
echo "---- cp -v backend/src/config.js docs/（显示复制过程）----"
cp -v backend/src/config.js docs/
ls -l docs/

echo ""
echo "---- cp -r backend docs/backend-bak（递归复制目录）----"
cp -r backend docs/backend-bak
ls -l docs/

echo ""
echo "---- cp -a backend docs/backend-archive（归档模式，保留权限/时间）----"
cp -a backend docs/backend-archive
ls -l docs/

# === 6. mv 命令演示 ===
# mv 移动或重命名文件
echo ""
echo ">>> [6] mv 命令演示..."
cd "$PRACTICE_DIR/project"

echo "---- mv backend/src/app.bak.js backend/src/app.backup.js（重命名）----"
mv backend/src/app.bak.js backend/src/app.backup.js
ls -l backend/src/

echo ""
echo "---- mv -v backend/src/file1.txt docs/（移动文件，显示过程）----"
mv -v backend/src/file1.txt docs/
ls -l docs/

echo ""
echo "---- mv -v backend/src/file2.txt backend/src/file3.txt backend/test/（批量移动）----"
mv -v backend/src/file2.txt backend/src/file3.txt backend/test/
ls -l backend/test/

# === 7. rm 命令演示 ===
# rm 删除文件或目录（危险！不可恢复）
echo ""
echo ">>> [7] rm 命令演示..."
cd "$PRACTICE_DIR/project"

echo "---- rm docs/file1.txt（删除文件）----"
rm docs/file1.txt
ls -l docs/

echo ""
echo "---- rm -i backend/src/file4.txt（交互式确认，输入 y 确认）----"
# 用 yes 自动回答 y，演示效果
yes | rm -i backend/src/file4.txt
ls -l backend/src/

echo ""
echo "---- rm -r docs/backend-bak（递归删除目录）----"
rm -r docs/backend-bak
ls -l docs/

echo ""
echo "---- rm -rf docs/backend-archive（强制递归删除，不提示）----"
rm -rf docs/backend-archive
ls -l docs/

# === 8. 综合练习：模拟电商项目目录初始化 ===
# 模拟在 /tmp 下创建电商项目的完整目录结构
echo ""
echo ">>> [8] 综合练习：模拟电商项目目录结构..."
cd "$PRACTICE_DIR"

# 创建完整的项目目录树
mkdir -p ecommerce/{backend/{src,config},frontend/{src,dist},logs/nginx,scripts,backup,data}

# 创建占位文件
touch ecommerce/backend/src/{app.js,router.js,model.js}
touch ecommerce/backend/config/{database.json,redis.json}
touch ecommerce/frontend/src/{index.html,main.js,style.css}
touch ecommerce/logs/nginx/{access.log,error.log}
touch ecommerce/scripts/{deploy.sh,backup.sh,health-check.sh}
touch ecommerce/backup/.gitkeep
touch ecommerce/data/.gitkeep

echo "---- 完整目录树：tree ecommerce ----"
tree ecommerce

echo ""
echo "---- 总文件数与目录数：----"
echo "    文件数：$(find ecommerce -type f | wc -l)"
echo "    目录数：$(find ecommerce -type d | wc -l)"
echo "    总大小：$(du -sh ecommerce | cut -f1)"

# === 9. 命令帮助演示 ===
# man / info / --help / whatis
echo ""
echo ">>> [9] 命令帮助演示..."
echo "---- whatis ls（一句话简介）----"
whatis ls 2>/dev/null || echo "    （man-db 索引可能未建立，可执行 sudo mandb 建立）"

echo ""
echo "---- ls --help（快速查看选项，前 15 行）----"
ls --help 2>&1 | head -n 15

echo ""
echo "---- man ls 的章节说明（前 10 行）----"
man ls 2>/dev/null | head -n 10 || echo "    （如 man 未安装，请执行 sudo apt install man-db）"

# === 10. history 与命令补全提示 ===
echo ""
echo ">>> [10] history 与命令补全提示..."
echo "    当前会话已执行的命令数：$(history | wc -l)"
echo ""
echo "    终端效率技巧："
echo "      - Tab          : 自动补全命令/路径（按两次列出候选）"
echo "      - Ctrl+R       : 反向搜索历史命令"
echo "      - Ctrl+L       : 清屏"
echo "      - Ctrl+A / E   : 光标移到行首 / 行尾"
echo "      - !!           : 执行上一条命令"
echo "      !\$            : 上一条命令的最后一个参数"
echo "      - history N    : 显示最近 N 条历史"

echo ""
echo "================================================"
echo "  基础命令练习完成！"
echo "  练习目录保留在：$PRACTICE_DIR"
echo "  可自行进入目录继续操作：cd $PRACTICE_DIR"
echo "  清理练习目录：rm -rf $PRACTICE_DIR"
echo "================================================"
