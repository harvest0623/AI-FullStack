#!/bin/bash
# ============================================================
# 文件名：01-package-management.sh
# 用途：演示软件包管理：apt 安装/卸载/搜索、dpkg 查询、
#       源码编译安装示例、apt vs dnf 对照
# 适用：Ubuntu 22.04 LTS
# 场景：电商服务器初始化时安装各类基础软件
# 注意：含 sudo 命令，需具备 sudo 权限
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day08 - 01 软件包管理演示"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"
echo "提示：本脚本含 sudo 命令，请以具备 sudo 权限的用户执行"
echo ""

# ---------- 1. apt update / upgrade ----------

echo -e "\n[1] apt update —— 更新软件源索引（不会安装任何东西）"
echo "命令：sudo apt update"
sudo apt update 2>&1 | tail -n 10

echo -e "\n[2] apt list --upgradable —— 查看可升级的包"
echo "命令：apt list --upgradable 2>/dev/null | head -n 10"
apt list --upgradable 2>/dev/null | head -n 10

echo -e "\n[3] apt upgrade —— 升级所有已装包（演示命令，不真实执行）"
cat <<'EOF'
sudo apt upgrade -y                # 升级所有包
sudo apt upgrade -y nginx          # 仅升级 nginx
sudo apt dist-upgrade -y           # 升级并处理依赖变化（更激进）
EOF

# ---------- 2. apt install / remove ----------

echo -e "\n[4] apt install —— 安装软件包"
cat <<'EOF'
# 基础安装
sudo apt install -y nginx          # -y 自动 yes

# 安装时不安装推荐包（节省空间）
sudo apt install --no-install-recommends nginx

# 安装指定版本
sudo apt install nginx=1.18.0-0ubuntu1

# 同时安装多个
sudo apt install -y nginx mysql-server redis-server

# 修复损坏依赖
sudo apt --fix-broken install
EOF

echo -e "\n[5] 实战：安装基础运维工具"
echo "命令：sudo apt install -y curl wget vim git htop tree unzip"
sudo apt install -y curl wget vim git htop tree unzip 2>&1 | tail -n 5

# ---------- 3. apt remove / purge / autoremove ----------

echo -e "\n[6] apt remove / purge —— 卸载软件包"
cat <<'EOF'
# remove 保留配置文件
sudo apt remove nginx

# purge 连同配置文件一起删除
sudo apt purge nginx

# autoremove 清理不再需要的依赖包
sudo apt autoremove -y

# 一条命令彻底卸载
sudo apt purge -y nginx && sudo apt autoremove -y
EOF

# ---------- 4. apt search / show ----------

echo -e "\n[7] apt search —— 搜索软件包"
echo "命令：apt search nginx 2>/dev/null | head -n 15"
apt search nginx 2>/dev/null | head -n 15

echo -e "\n[8] apt show —— 查看包详情"
echo "命令：apt show nginx 2>/dev/null"
apt show nginx 2>/dev/null | head -n 20

echo -e "\n[9] apt list --installed —— 列出已安装的包"
echo "命令：apt list --installed 2>/dev/null | wc -l"
apt list --installed 2>/dev/null | wc -l
echo "命令：apt list --installed 2>/dev/null | grep -E 'nginx|mysql|redis'"
apt list --installed 2>/dev/null | grep -E 'nginx|mysql|redis' || echo "（暂未安装这些服务）"

# ---------- 5. apt-cache 底层查询 ----------

echo -e "\n[10] apt-cache policy —— 查看版本候选"
echo "命令：apt-cache policy nginx"
apt-cache policy nginx 2>/dev/null | head -n 15

echo -e "\n[11] apt-cache depends —— 查看依赖关系"
echo "命令：apt-cache depends nginx | head -n 15"
apt-cache depends nginx 2>/dev/null | head -n 15

echo -e "\n[12] apt-cache rdepends —— 反向依赖（谁依赖它）"
echo "命令：apt-cache rdepends nginx | head -n 10"
apt-cache rdepends nginx 2>/dev/null | head -n 10

# ---------- 6. dpkg 底层操作 ----------

echo -e "\n[13] dpkg -l —— 列出所有已安装包"
echo "命令：dpkg -l | head -n 10"
dpkg -l | head -n 10

echo -e "\n[14] dpkg -l | grep —— 过滤已安装包"
echo "命令：dpkg -l | grep -E 'nginx|mysql|redis'"
dpkg -l | grep -E 'nginx|mysql|redis' || echo "（未找到这些包）"

echo -e "\n[15] dpkg -L —— 查看包安装了哪些文件"
echo "命令：dpkg -L curl | head -n 15"
dpkg -L curl 2>/dev/null | head -n 15

echo -e "\n[16] dpkg -S —— 查询某文件属于哪个包"
echo "命令：dpkg -S /usr/bin/curl"
dpkg -S /usr/bin/curl 2>/dev/null
echo "命令：dpkg -S /usr/sbin/nginx"
dpkg -S /usr/sbin/nginx 2>/dev/null || echo "（nginx 未安装）"

echo -e "\n[17] dpkg -i —— 安装本地 .deb 包"
cat <<'EOF'
# 下载 .deb 包
wget http://example.com/package.deb

# 安装（不解决依赖，可能报错）
sudo dpkg -i package.deb

# 若报依赖错误，用 apt 修复
sudo apt --fix-broken install

# 卸载
sudo dpkg -r package       # 保留配置
sudo dpkg -P package       # 含配置
EOF

# ---------- 7. 软件源配置 ----------

echo -e "\n[18] /etc/apt/sources.list —— 主源配置"
echo "命令：cat /etc/apt/sources.list | head -n 15"
cat /etc/apt/sources.list 2>/dev/null | head -n 15 || echo "（文件不存在或为空）"

echo -e "\n[19] /etc/apt/sources.list.d/ —— 第三方源"
echo "命令：ls -l /etc/apt/sources.list.d/"
ls -l /etc/apt/sources.list.d/ 2>/dev/null

echo -e "\n[20] 阿里云镜像源配置（国内服务器推荐）"
cat <<'EOF'
# Ubuntu 22.04 (jammy) 阿里云源
# 备份原文件
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak

# 替换为阿里云源
sudo tee /etc/apt/sources.list <<EOF
deb http://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-backports main restricted universe multiverse
EOF

# 更新索引
sudo apt update
EOF

echo -e "\n[21] PPA —— 个人软件包归档"
cat <<'EOF'
# 安装 add-apt-repository 命令
sudo apt install -y software-properties-common

# 添加 PPA 源
sudo add-apt-repository ppa:nginx/stable
sudo apt update

# 删除 PPA
sudo add-apt-repository --remove ppa:nginx/stable
EOF

echo -e "\n[22] 新版密钥管理（signed-by，推荐）"
cat <<'EOF'
# 以 Node.js 官方源为例
# 1. 下载并转换 GPG 密钥
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg

# 2. 添加源（用 signed-by 指定密钥）
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | \
  sudo tee /etc/apt/sources.list.d/nodesource.list

# 3. 更新并安装
sudo apt update
sudo apt install -y nodejs
EOF

# ---------- 8. 源码编译安装 ----------

echo -e "\n[23] 源码编译安装三步曲"
cat <<'EOF'
# 经典三步曲
./configure && make && make install

# 1. ./configure —— 检查依赖、生成 Makefile
./configure --prefix=/usr/local/nginx \
            --with-http_ssl_module \
            --with-http_v2_module

# 2. make —— 编译（-j 并行编译加速）
make -j$(nproc)

# 3. make install —— 安装到 --prefix 指定路径
sudo make install

# 卸载（如果 Makefile 支持）
sudo make uninstall
EOF

echo -e "\n[24] 实战：源码编译安装 Nginx 1.25"
cat <<'EOF'
# 1. 安装编译依赖
sudo apt install -y build-essential libpcre3-dev zlib1g-dev libssl-dev

# 2. 下载源码
cd /usr/local/src
sudo wget http://nginx.org/download/nginx-1.25.3.tar.gz
sudo tar -zxvf nginx-1.25.3.tar.gz
cd nginx-1.25.3

# 3. 配置编译选项
sudo ./configure \
    --prefix=/usr/local/nginx \
    --with-http_ssl_module \
    --with-http_v2_module \
    --with-http_realip_module \
    --with-http_gzip_static_module \
    --with-threads

# 4. 编译并安装
sudo make -j$(nproc)
sudo make install

# 5. 添加到 PATH
echo 'export PATH=$PATH:/usr/local/nginx/sbin' | sudo tee /etc/profile.d/nginx.sh
source /etc/profile.d/nginx.sh

# 6. 验证
nginx -v
nginx -t

# 7. 创建 systemd 服务（可选）
sudo tee /etc/systemd/system/nginx-custom.service <<EOF
[Unit]
Description=Nginx Custom Build
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/nginx/sbin/nginx
ExecReload=/usr/local/nginx/sbin/nginx -s reload
ExecStop=/usr/local/nginx/sbin/nginx -s quit
PIDFile=/usr/local/nginx/logs/nginx.pid

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now nginx-custom
EOF

# ---------- 9. apt vs dnf 对照 ----------

echo -e "\n[25] apt vs dnf 命令对照表"
cat <<'EOF'
┌──────────────┬──────────────────────────────┬──────────────────────────────┐
│ 操作         │ apt (Debian/Ubuntu)          │ dnf (RHEL/CentOS)            │
├──────────────┼──────────────────────────────┼──────────────────────────────┤
│ 更新索引     │ apt update                   │ dnf check-update             │
│ 升级所有     │ apt upgrade                  │ dnf upgrade                  │
│ 安装         │ apt install pkg              │ dnf install pkg              │
│ 卸载         │ apt remove pkg               │ dnf remove pkg               │
│ 卸载+配置    │ apt purge pkg                │ dnf remove pkg（默认含配置） │
│ 清理依赖     │ apt autoremove               │ dnf autoremove               │
│ 搜索         │ apt search keyword           │ dnf search keyword           │
│ 详情         │ apt show pkg                 │ dnf info pkg                 │
│ 已装列表     │ apt list --installed         │ dnf list installed           │
│ 包文件查询   │ dpkg -S file                 │ rpm -qf file                 │
│ 包内容查询   │ dpkg -L pkg                  │ rpm -ql pkg                  │
│ 本地包安装   │ dpkg -i pkg.deb              │ rpm -ivh pkg.rpm             │
│ 缓存清理     │ apt clean                    │ dnf clean all                │
│ 源配置       │ /etc/apt/sources.list        │ /etc/yum.repos.d/*.repo      │
└──────────────┴──────────────────────────────┴──────────────────────────────┘
EOF

echo -e "\n[26] dnf / rpm 命令示例（CentOS/RHEL）"
cat <<'EOF'
# dnf 命令
sudo dnf install -y nginx
sudo dnf remove nginx
sudo dnf search nginx
sudo dnf info nginx
sudo dnf list installed
sudo dnf groupinstall "Development Tools"     # 组安装
sudo dnf history                              # 操作历史

# rpm 命令
sudo rpm -ivh package.rpm     # 安装（i=install v=verbose h=hash）
sudo rpm -Uvh package.rpm     # 升级
sudo rpm -e package           # 卸载
rpm -qa                       # 列出所有已装
rpm -qa | grep nginx
rpm -qf /usr/sbin/nginx       # 查文件属于哪个包
rpm -ql nginx                 # 查包安装了哪些文件
rpm -qi nginx                 # 包信息
EOF

echo -e "\n============================================================"
echo "  Day08 - 01 软件包管理演示 完成"
echo "============================================================"
