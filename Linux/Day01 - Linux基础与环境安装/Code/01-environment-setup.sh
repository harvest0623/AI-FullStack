#!/bin/bash
# 文件用途：Linux 学习环境初始化脚本
#           更新系统、安装基础工具包、设置时区、配置 vim、创建项目目录
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：sudo bash 01-environment-setup.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本完成 Day01 所需的练习环境初始化工作。
#   脚本可重复执行，已安装的包会跳过，已存在的目录会保留。
#   需要 root 权限（涉及 apt 安装、时区设置、/opt 目录操作）。
# ============================================================

# 严格模式：遇到错误立即退出，使用未定义变量报错
set -e

# === 0. 权限检查 ===
# 必须以 root 或 sudo 执行
if [ "$EUID" -ne 0 ]; then
    echo "================================================"
    echo "  错误：本脚本需要 root 权限执行"
    echo "  请使用：sudo bash $0"
    echo "================================================"
    exit 1
fi

echo "================================================"
echo "  Linux 学习环境初始化脚本"
echo "  系统：$(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"
echo "  内核：$(uname -r)"
echo "  时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"

# === 1. 更新系统软件包索引 ===
# apt update 仅刷新软件源索引，不安装任何包
# 升级已安装包用 apt upgrade（这里仅更新索引，避免脚本运行过久）
echo ""
echo ">>> [1/6] 更新软件包索引..."
apt update -y

# === 2. 安装基础工具包 ===
# tree    : 以树形结构显示目录
# htop    : 交互式进程监控（比 top 更直观）
# vim     : 文本编辑器
# git     : 版本控制
# curl    : HTTP 请求工具
# wget    : 文件下载工具
# unzip   : 解压 zip
# net-tools : 提供 ifconfig/netstat 等传统网络命令
# dnsutils  : 提供 dig/nslookup
# bash-completion : 命令补全增强
# man-db  : man 手册数据库
# dos2unix : Windows 换行符转 Unix（脚本开发常用）
echo ""
echo ">>> [2/6] 安装基础工具包..."
DEBIAN_FRONTEND=noninteractive apt install -y \
    tree \
    htop \
    vim \
    git \
    curl \
    wget \
    unzip \
    net-tools \
    dnsutils \
    bash-completion \
    man-db \
    dos2unix \
    less \
    rsync \
    ca-certificates

echo "    基础工具安装完成。"

# === 3. 设置时区为 Asia/Shanghai ===
# timedatectl set-timezone 设置系统时区
# 验证：timedatectl 或 date
echo ""
echo ">>> [3/6] 设置时区为 Asia/Shanghai..."
timedatectl set-timezone Asia/Shanghai
echo "    当前时区：$(timedatectl show -p Timezone --value)"
echo "    当前时间：$(date '+%Y-%m-%d %H:%M:%S %Z')"

# === 4. 配置 vim 基础设置 ===
# /etc/vim/vimrc.local 是系统级 vim 用户配置（不会被包升级覆盖）
# 设置：行号、自动缩进、4 空格缩进、不兼容 Vi 旧模式、语法高亮
echo ""
echo ">>> [4/6] 配置 vim 基础设置..."
VIMRC="/etc/vim/vimrc.local"
cat > "$VIMRC" <<'EOF'
" ============================================================
" AI-FullStack Linux 学习环境 vim 配置
" ============================================================
set nocompatible      " 关闭 Vi 兼容模式
syntax on             " 语法高亮
set number            " 显示行号
set relativenumber    " 相对行号（方便跳转）
set tabstop=4         " Tab 显示宽度
set shiftwidth=4      " 自动缩进宽度
set expandtab         " Tab 转为空格
set autoindent        " 自动缩进
set smartindent       " 智能缩进
set encoding=utf-8    " 编码
set fileencoding=utf-8
set backspace=indent,eol,start  " Backspace 可删除缩进和换行
set hlsearch          " 搜索高亮
set incsearch         " 增量搜索
set ignorecase        " 搜索忽略大小写
set smartcase         " 有大写时不忽略
set wrap              " 自动换行
set showcmd           " 显示输入的命令
set wildmenu          " 命令行补全菜单
set laststatus=2      " 总是显示状态栏
set ruler             " 显示光标位置
EOF
echo "    vim 配置已写入 $VIMRC"

# === 5. 创建电商项目目录结构 ===
# /opt/ecommerce/ 作为项目根目录
#   backend/  : 后端代码
#   logs/     : 应用日志
#   scripts/  : 运维脚本
#   backup/   : 数据备份
# /opt 通常用于存放第三方软件，适合放项目
echo ""
echo ">>> [5/6] 创建项目目录结构 /opt/ecommerce/..."
PROJECT_ROOT="/opt/ecommerce"
mkdir -p "$PROJECT_ROOT"/{backend,logs,scripts,backup}

# 在各目录下放一个 .gitkeep 占位文件，方便后续 git 管理
touch "$PROJECT_ROOT/backend/.gitkeep"
touch "$PROJECT_ROOT/logs/.gitkeep"
touch "$PROJECT_ROOT/scripts/.gitkeep"
touch "$PROJECT_ROOT/backup/.gitkeep"

# 在 logs 下创建一个子目录用于 Nginx 访问日志模拟
mkdir -p "$PROJECT_ROOT/logs/nginx"

echo "    项目目录结构："
tree -L 2 "$PROJECT_ROOT"

# === 6. 系统信息展示 ===
# 展示初始化后的关键系统信息，便于确认环境就绪
echo ""
echo ">>> [6/6] 系统信息确认..."
echo "------------------------------------------------"
echo "  主机名    : $(hostname)"
echo "  操作系统  : $(lsb_release -ds 2>/dev/null)"
echo "  内核版本  : $(uname -r)"
echo "  系统架构  : $(uname -m)"
echo "  当前用户  : $(whoami)"
echo "  当前目录  : $(pwd)"
echo "  当前时间  : $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "  时区      : $(timedatectl show -p Timezone --value)"
echo "  内存      : $(free -h | awk '/^Mem:/ {print $2 " 总计, " $7 " 可用"}')"
echo "  磁盘      : $(df -h / | awk 'NR==2 {print $2 " 总计, " $4 " 可用"}')"
echo "------------------------------------------------"

# 验证关键工具是否安装成功
echo ""
echo ">>> 关键工具验证："
for tool in tree htop vim git curl wget unzip; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "    [✓] $tool : $(command -v "$tool")"
    else
        echo "    [✗] $tool 未安装"
    fi
done

echo ""
echo "================================================"
echo "  环境初始化完成！"
echo "  下一步：执行 bash 02-basic-commands.sh 练习基础命令"
echo "================================================"
