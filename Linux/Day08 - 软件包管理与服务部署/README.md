# Day08 - 软件包管理与服务部署

从拿到一台空白 Ubuntu 服务器到电商项目真正对外提供服务，需要经过：更新软件源 → 安装 Nginx/MySQL/Redis/Node.js → 编写配置 → 启动服务 → 设置开机自启 → 配置环境变量。这条路径既涉及 Debian 系的 `apt`/`dpkg` 包管理，也涉及 RHEL 系的 `dnf`/`rpm`，甚至需要从源码 `./configure && make && make install` 编译特定版本。本章将围绕电商服务器 `192.168.1.100` 系统讲解软件包管理、源码编译、Nginx/Node.js/PM2 部署实战与环境变量管理，让你完成从空白服务器到上线服务的"最后一公里"。

---

## 学习目标

- 熟练使用 `apt`/`apt-get`/`dpkg`/`apt-cache` 管理 Debian 系软件包
- 了解 RHEL 系 `dnf`/`yum`/`rpm` 与 apt 的对应关系
- 掌握源码编译安装的"三步曲"：`./configure && make && make install`
- 实战部署 Nginx，理解虚拟主机与反向代理配置
- 使用 nvm 管理 Node.js 版本，使用 PM2 管理进程
- 掌握环境变量多层级配置（export / .bashrc / .bash_profile / /etc/profile / /etc/profile.d/）

---

## 理论知识讲解

### 一、Debian 系包管理（apt）

#### 1.1 apt 命令家族

| 命令 | 用途 | 示例 |
|------|------|------|
| `apt update` | 更新软件源索引 | `sudo apt update` |
| `apt upgrade` | 升级所有已装包 | `sudo apt upgrade` |
| `apt install` | 安装包 | `sudo apt install -y nginx` |
| `apt remove` | 卸载包（保留配置） | `sudo apt remove nginx` |
| `apt purge` | 卸载包（含配置） | `sudo apt purge nginx` |
| `apt autoremove` | 清理无用依赖 | `sudo apt autoremove` |
| `apt search` | 搜索包 | `apt search nginx` |
| `apt show` | 查看包详情 | `apt show nginx` |
| `apt list --installed` | 列出已安装 | `apt list --installed` |
| `apt list --upgradable` | 列出可升级 | `apt list --upgradable` |

```bash
# 安装时一并安装推荐包（默认行为，加 --no-install-recommends 跳过）
sudo apt install nginx

# 安装指定版本
sudo apt install nginx=1.18.0-0ubuntu1

# 修复损坏依赖
sudo apt --fix-broken install

# 仅下载不安装
sudo apt install -d nginx
```

#### 1.2 apt-cache 与 dpkg 底层

```bash
# apt-cache 查询包信息
apt-cache policy nginx            # 查看版本候选（哪个版本会被安装）
apt-cache depends nginx           # 查看依赖
apt-cache rdepends nginx          # 查看反向依赖（谁依赖它）
apt-cache search keyword          # 搜索
apt-cache showpkg nginx           # 详细包信息

# dpkg 底层操作（apt 的底层）
sudo dpkg -i package.deb          # 安装本地 .deb 包
sudo dpkg -r package              # 卸载（保留配置）
sudo dpkg -P package              # 卸载（含配置）
dpkg -l                           # 列出所有已装
dpkg -l | grep nginx              # 过滤
dpkg -L nginx                     # 查看包安装的所有文件
dpkg -S /usr/sbin/nginx           # 查询某文件属于哪个包
dpkg --print-architecture         # 查看系统架构
```

#### 1.3 软件源配置

```bash
# /etc/apt/sources.list —— 主源配置
deb http://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse

# 字段说明：
# deb        二进制包（deb-src 是源码包）
# URL        镜像地址
# jammy      Ubuntu 22.04 代号
# main       官方自由软件
# restricted 官方非自由软件（驱动等）
# universe   社区维护
# multiverse 非自由软件

# /etc/apt/sources.list.d/ —— 第三方源（推荐放这里，便于管理）
# 文件以 .list 结尾，格式同上

# PPA（个人软件包归档）
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:nginx/stable
sudo apt update

# 阿里云镜像源（推荐国内服务器）
# 直接替换 sources.list 中的 archive.ubuntu.com 为 mirrors.aliyun.com

# 新版密钥管理（signed-by）
# 把 GPG 密钥放到 /etc/apt/keyrings/，sources.list 中用 signed-by 指定
# 例：Node.js 官方源
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
sudo apt update
```

### 二、RHEL 系包管理（dnf/yum）

| 命令 | 用途 | 对应 apt |
|------|------|---------|
| `dnf install` | 安装 | apt install |
| `dnf remove` | 卸载 | apt remove |
| `dnf update` | 升级 | apt upgrade |
| `dnf search` | 搜索 | apt search |
| `dnf info` | 详情 | apt show |
| `dnf list installed` | 列出已装 | apt list --installed |
| `dnf groupinstall` | 组安装 | 无对应（apt 用 task） |
| `dnf history` | 历史记录 | 无对应 |
| `dnf clean all` | 清理缓存 | apt clean |

```bash
# CentOS 7 用 yum，CentOS 8+/RHEL 8+ 用 dnf（yum 是 dnf 的软链接）
sudo dnf install -y nginx
sudo dnf remove nginx

# 组安装（一次性装一组软件）
sudo dnf groupinstall "Development Tools"
# Ubuntu 对应：sudo apt install -y build-essential

# rpm 底层
sudo rpm -ivh package.rpm       # 安装（i=install v=verbose h=hash进度）
sudo rpm -e package             # 卸载
sudo rpm -Uvh package.rpm       # 升级
rpm -qa                         # 列出所有已装
rpm -qa | grep nginx
rpm -qf /usr/sbin/nginx         # 查文件属于哪个包
rpm -ql nginx                   # 查包安装了哪些文件
rpm -qi nginx                   # 包信息
rpm -qip package.rpm            # 未安装包的信息

# /etc/yum.repos.d/*.repo 配置文件
# [baseos]
# name=CentOS Stream $releasever - BaseOS
# baseurl=http://mirrors.aliyun.com/centos-stream/$releasever-stream/BaseOS/$basearch/os/
# gpgcheck=1
# enabled=1
# gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
```

### 三、源码编译安装

```bash
# 经典三步曲
./configure && make && make install

# 1. configure —— 检查依赖、生成 Makefile
./configure --prefix=/usr/local/nginx \
            --with-http_ssl_module \
            --with-http_v2_module

# 2. make —— 编译
make -j$(nproc)                  # -j 并行编译，nproc 是 CPU 核心数

# 3. make install —— 安装
sudo make install

# 卸载（如果 Makefile 支持）
sudo make uninstall
```

**何时用源码编译**：

- 官方源版本过旧（如 Ubuntu 22.04 默认 Nginx 1.18，需要 1.25）
- 需要特定编译选项（如开启 HTTP/3）
- 官方源没有这个包
- 学习目的（理解编译过程）

```bash
# 完整示例：编译安装 Nginx 1.25
# 1. 安装编译依赖
sudo apt install -y build-essential libpcre3-dev zlib1g-dev libssl-dev

# 2. 下载源码
wget http://nginx.org/download/nginx-1.25.3.tar.gz
tar -zxvf nginx-1.25.3.tar.gz
cd nginx-1.25.3

# 3. 配置
./configure --prefix=/usr/local/nginx \
            --with-http_ssl_module \
            --with-http_v2_module \
            --with-http_realip_module \
            --with-http_gzip_static_module

# 4. 编译并安装
make -j$(nproc)
sudo make install

# 5. 添加到 PATH
echo 'export PATH=$PATH:/usr/local/nginx/sbin' | sudo tee /etc/profile.d/nginx.sh
source /etc/profile.d/nginx.sh

# 6. 验证
nginx -v
```

### 四、服务部署实战

#### 4.1 Nginx

```bash
# 安装
sudo apt install -y nginx

# 验证
nginx -v
nginx -t                           # 测试配置语法
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx

# 配置文件目录
/etc/nginx/nginx.conf              # 主配置
/etc/nginx/sites-available/        # 可用站点（Ubuntu）
/etc/nginx/sites-enabled/          # 已启用站点（软链接到 available）
/etc/nginx/conf.d/                 # 额外配置（CentOS 风格，Ubuntu 也支持）

# 重新加载配置（不中断服务）
sudo nginx -s reload
# 或
sudo systemctl reload nginx
```

**虚拟主机配置**：

```nginx
# /etc/nginx/sites-available/ecommerce
server {
    listen 80;
    server_name api.example.com;
    root /opt/ecommerce/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 80;
    server_name admin.example.com;
    root /opt/ecommerce/admin/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ecommerce /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**反向代理**：

```nginx
# /etc/nginx/sites-available/ecommerce-api
server {
    listen 80;
    server_name api.example.com;

    # 反向代理到 Node.js 后端
    location /api/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件
    location /static/ {
        root /opt/ecommerce;
        expires 30d;
    }
}
```

**负载均衡**：

```nginx
# /etc/nginx/conf.d/upstream.conf
upstream ecommerce_backend {
    # 轮询（默认）
    server 127.0.0.1:3000 weight=3;
    server 127.0.0.1:3001 weight=2;
    server 127.0.0.1:3002 weight=1;

    # 健康检查
    keepalive 32;
}

server {
    listen 80;
    server_name api.example.com;

    location /api/ {
        proxy_pass http://ecommerce_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

#### 4.2 MySQL

```bash
sudo apt install -y mysql-server
sudo mysql_secure_installation     # 安全初始化
sudo systemctl enable --now mysql

# 配置文件
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
# [mysqld]
# bind-address = 0.0.0.0
# max_connections = 200
# character-set-server = utf8mb4
```

#### 4.3 Redis

```bash
sudo apt install -y redis-server
sudo systemctl enable --now redis-server

# 配置文件
sudo vim /etc/redis/redis.conf
# bind 127.0.0.1
# requirepass your_strong_password
# maxmemory 512mb
# maxmemory-policy allkeys-lru
```

#### 4.4 Node.js + nvm

```bash
# 安装 nvm（Node Version Manager）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash

# 加载 nvm
source ~/.bashrc

# 安装 Node.js LTS
nvm install --lts
nvm install 20            # 指定版本
nvm use 20
nvm use --lts

# 设置默认版本
nvm alias default 20

# 查看已安装版本
nvm ls

# 镜像加速（国内服务器）
export NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node

# npm 镜像源管理
npm config set registry https://registry.npmmirror.com
# 或用 nrm 切换
npm install -g nrm
nrm ls
nrm use taobao
```

#### 4.5 PM2 进程管理

```bash
# 安装
npm install -g pm2

# 启动应用
pm2 start app.js
pm2 start app.js --name "ecommerce-api"
pm2 start app.js -i 4            # 集群模式启动 4 个进程
pm2 start app.js -i max          # 用尽所有 CPU 核心

# 启动 npm 脚本
pm2 start npm --name "ecommerce" -- start
pm2 start yarn --name "ecommerce" -- start

# 管理
pm2 list                         # 列出所有进程
pm2 stop all                     # 停止全部
pm2 stop ecommerce               # 停止指定
pm2 restart ecommerce            # 重启
pm2 reload ecommerce             # 零停机重启（集群模式）
pm2 delete ecommerce             # 删除进程

# 查看日志
pm2 logs                         # 所有日志
pm2 logs ecommerce               # 指定进程
pm2 logs --lines 200             # 最近 200 行

# 监控
pm2 monit                        # 实时监控 CPU/内存
pm2 status                       # 状态概览
pm2 describe ecommerce           # 详细信息

# 开机自启
pm2 startup                      # 生成 systemd 启动脚本
# 按提示执行 sudo env PATH=... pm2 startup ...
pm2 save                         # 保存当前进程列表

# 配置文件方式启动
pm2 start ecosystem.config.js
pm2 start ecosystem.config.js --env production
```

**ecosystem.config.js 示例**：

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'ecommerce-api',
    script: './dist/main.js',
    instances: 4,                    // 集群实例数（或 'max'）
    exec_mode: 'cluster',            // 集群模式
    cwd: '/opt/ecommerce/backend',
    env: {
      NODE_ENV: 'development',
      PORT: 3000
    },
    env_production: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    max_memory_restart: '1G',        // 内存超 1G 自动重启
    error_file: '/opt/ecommerce/logs/err.log',
    out_file: '/opt/ecommerce/logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
    merge_logs: true,
    autorestart: true,
    watch: false,
    ignore_watch: ['node_modules', 'logs']
  }]
};
```

### 五、环境变量管理

| 文件 | 作用范围 | 生效时机 | 用途 |
|------|---------|---------|------|
| `export VAR=value` | 当前 Shell | 立即 | 临时测试 |
| `~/.bashrc` | 当前用户 | 每次打开终端 | 用户级别名/PATH |
| `~/.bash_profile` | 当前用户 | 登录时（SSH） | 用户级登录设置 |
| `~/.profile` | 当前用户 | 登录时（兼容） | Ubuntu 默认用户级 |
| `/etc/profile` | 全局所有用户 | 登录时 | 系统级登录设置 |
| `/etc/environment` | 全局所有用户 | 系统启动 | 系统级 KEY=VALUE |
| `/etc/profile.d/*.sh` | 全局所有用户 | 登录时 | 模块化系统配置（推荐） |

```bash
# 临时设置（仅当前 Shell）
export NODE_ENV=production
export PATH=$PATH:/usr/local/go/bin

# 查看环境变量
env                               # 所有
echo $NODE_ENV                    # 单个
printenv PATH                     # 单个

# ~/.bashrc 用户级
echo 'export NODE_ENV=production' >> ~/.bashrc
echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc

# /etc/profile.d/ 全局模块化（推荐）
echo 'export JAVA_HOME=/usr/lib/jvm/java-17' | sudo tee /etc/profile.d/java.sh
echo 'export PATH=$PATH:$JAVA_HOME/bin' | sudo tee -a /etc/profile.d/java.sh
sudo chmod +x /etc/profile.d/java.sh

# /etc/environment 系统级（仅 KEY=VALUE，不支持变量展开）
sudo tee -a /etc/environment <<EOF
NODE_ENV=production
JAVA_HOME=/usr/lib/jvm/java-17
EOF

# 立即生效
source ~/.bashrc                  # 当前 Shell
source /etc/profile               # 全局
# 或重新登录
```

**systemd 服务的环境变量**：

```ini
# 在 .service 文件中
[Service]
Environment="NODE_ENV=production"
Environment="PORT=3000"
EnvironmentFile=-/opt/ecommerce/backend/.env

# 或在 /etc/default/servicename 中
# 然后单元文件中：
EnvironmentFile=-/etc/default/ecommerce-backend
```

---

## 代码文件说明

| 文件 | 用途 | 是否需 root |
|------|------|------------|
| `Code/01-package-management.sh` | 演示 apt 安装/卸载/搜索、dpkg 查询、源码编译示例 | 是 |
| `Code/02-deploy-nginx.sh` | 部署 Nginx，含虚拟主机、反向代理、负载均衡配置 | 是 |
| `Code/03-deploy-nodejs-pm2.sh` | 用 nvm 安装 Node.js、PM2 进程管理、ecosystem 配置 | 部分需要 |
| `Code/04-environment-variables.sh` | 演示 export/.bashrc/profile/profile.d 环境变量配置 | 部分需要 |

---

## 关键知识点总结

### 1. apt vs dnf 命令对照表

| 操作 | apt（Debian/Ubuntu） | dnf（RHEL/CentOS） |
|------|---------------------|-------------------|
| 更新索引 | `apt update` | `dnf check-update` |
| 升级所有 | `apt upgrade` | `dnf upgrade` |
| 安装 | `apt install pkg` | `dnf install pkg` |
| 卸载 | `apt remove pkg` | `dnf remove pkg` |
| 卸载+配置 | `apt purge pkg` | `dnf remove pkg`（默认含配置） |
| 清理依赖 | `apt autoremove` | `dnf autoremove` |
| 搜索 | `apt search keyword` | `dnf search keyword` |
| 详情 | `apt show pkg` | `dnf info pkg` |
| 已装列表 | `apt list --installed` | `dnf list installed` |
| 包文件查询 | `dpkg -S file` | `rpm -qf file` |
| 包内容查询 | `dpkg -L pkg` | `rpm -ql pkg` |
| 本地包安装 | `dpkg -i pkg.deb` | `rpm -ivh pkg.rpm` |
| 缓存清理 | `apt clean` | `dnf clean all` |
| 源配置 | `/etc/apt/sources.list` | `/etc/yum.repos.d/*.repo` |

### 2. dpkg/rpm 命令速查

| 操作 | dpkg | rpm |
|------|------|-----|
| 安装本地包 | `dpkg -i pkg.deb` | `rpm -ivh pkg.rpm` |
| 升级 | `dpkg -i pkg.deb` | `rpm -Uvh pkg.rpm` |
| 卸载（保留配置） | `dpkg -r pkg` | `rpm -e pkg` |
| 卸载（含配置） | `dpkg -P pkg` | `rpm -e pkg` |
| 列出所有 | `dpkg -l` | `rpm -qa` |
| 查询包文件 | `dpkg -L pkg` | `rpm -ql pkg` |
| 文件归属包 | `dpkg -S file` | `rpm -qf file` |
| 包信息 | `dpkg -s pkg` | `rpm -qi pkg` |

### 3. nvm/pm2 命令速查

| nvm 命令 | 用途 | pm2 命令 | 用途 |
|---------|------|---------|------|
| `nvm install 20` | 安装 Node 20 | `pm2 start app.js` | 启动 |
| `nvm use 20` | 切换版本 | `pm2 list` | 列表 |
| `nvm ls` | 列出已装 | `pm2 stop all` | 停止全部 |
| `nvm alias default 20` | 设默认 | `pm2 restart name` | 重启 |
| `nvm uninstall 20` | 卸载版本 | `pm2 reload name` | 零停机重启 |
| `nvm current` | 当前版本 | `pm2 delete name` | 删除 |
| `nvm run 20 app.js` | 用某版本运行 | `pm2 logs` | 日志 |
| | | `pm2 monit` | 监控 |
| | | `pm2 startup` | 开机自启 |
| | | `pm2 save` | 保存列表 |

### 4. 环境变量文件优先级表

| 文件 | 作用范围 | 加载时机 | 推荐用途 |
|------|---------|---------|---------|
| `/etc/environment` | 全局系统级 | 系统启动 | KEY=VALUE（不支持展开） |
| `/etc/profile` | 全局用户登录 | 登录时 | 系统级 PATH |
| `/etc/profile.d/*.sh` | 全局用户登录 | 登录时（被 profile 调用） | 模块化配置（推荐） |
| `~/.bash_profile` | 当前用户登录 | 登录时 | 用户级登录设置 |
| `~/.bashrc` | 当前用户非登录 | 每次开新 Shell | 用户级常用配置（推荐） |
| `~/.profile` | 当前用户登录 | 登录时（Ubuntu 默认） | 兼容性配置 |

**加载顺序（登录 Shell）**：`/etc/profile` → `/etc/profile.d/*.sh` → `~/.bash_profile`（若不存在则 `~/.bash_login`，再不存在则 `~/.profile`）

**非登录 Shell（如 tmux 新窗口）**：仅加载 `~/.bashrc`

---

## 实战练习

### 练习 1：从零部署 Nginx + 反向代理

电商前端已构建到 `/opt/ecommerce/frontend/dist`，后端运行在 `127.0.0.1:3000`，请：

1. 用 `apt install nginx` 安装 Nginx
2. 在 `/etc/nginx/sites-available/ecommerce` 配置虚拟主机
3. 配置 `/` 指向前端静态文件，`/api/` 反向代理到后端
4. 用 `ln -s` 启用站点
5. 用 `nginx -t` 测试配置
6. 用 `systemctl reload nginx` 平滑重载
7. 用 `curl http://127.0.0.1/` 与 `curl http://127.0.0.1/api/health` 验证

### 练习 2：用 PM2 部署集群模式后端

电商后端是 Node.js 应用，要求：

1. 用 nvm 安装 Node.js 20 LTS
2. 用 `npm install -g pm2` 安装 PM2
3. 编写 `ecosystem.config.js` 配置 4 个集群实例
4. 用 `pm2 start ecosystem.config.js --env production` 启动
5. 用 `pm2 startup` 与 `pm2 save` 设置开机自启
6. 用 `pm2 monit` 监控
7. 测试 `pm2 reload` 零停机重启

### 练习 3：配置 NODE_ENV 与 PATH

部署完成后需要确保环境变量在所有场景下生效：

1. 在 `/etc/profile.d/ecommerce.sh` 设置 `NODE_ENV=production`
2. 在 `~/.bashrc` 添加 `nvm` 加载脚本
3. 在 systemd 单元文件中设置 `Environment=NODE_ENV=production`
4. 在 `/etc/environment` 设置 `JAVA_HOME`（如有 Java 服务）
5. 验证：SSH 登录、`systemctl` 启动的服务、`bash -c` 子进程都能读到正确变量
