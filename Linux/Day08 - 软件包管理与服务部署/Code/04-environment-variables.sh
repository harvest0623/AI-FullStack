#!/bin/bash
# ============================================================
# 文件名：04-environment-variables.sh
# 用途：演示环境变量管理：export 临时变量、~/.bashrc 持久化、
#       /etc/profile 全局、/etc/profile.d/ 模块化、source 生效
# 适用：Ubuntu 22.04 LTS
# 场景：电商项目环境变量配置（NODE_ENV/PATH/JAVA_HOME 等）
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day08 - 04 环境变量管理演示"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"

# ---------- 1. 环境变量基础 ----------

echo -e "\n[1] 查看当前环境变量"
echo "命令：env | head -n 15"
env | head -n 15

echo -e "\n[2] 查看单个变量"
echo "命令：echo \$PATH"
echo "$PATH"
echo ""
echo "命令：echo \$HOME"
echo "$HOME"
echo ""
echo "命令：echo \$USER"
echo "$USER"

echo -e "\n[3] printenv —— 查看指定变量"
echo "命令：printenv PATH"
printenv PATH
echo "命令：printenv HOME"
printenv HOME

echo -e "\n[4] set vs env vs export"
cat <<'EOF'
set       # 显示所有变量（含 shell 变量与环境变量）
env       # 仅显示环境变量（可被子进程继承）
export    # 查看/设置环境变量
declare   # 声明变量属性

区别：
- Shell 变量：仅当前 Shell 可见，子进程不可见
- 环境变量：可被子进程继承（用 export 导出）
EOF

# ---------- 2. export 临时设置 ----------

echo -e "\n[5] export —— 临时设置环境变量（仅当前 Shell）"
echo "命令：export NODE_ENV=production"
export NODE_ENV=production
echo "命令：echo \$NODE_ENV"
echo "$NODE_ENV"

echo -e "\n[6] 验证 export 是当前 Shell 临时变量"
echo "命令：bash -c 'echo \$NODE_ENV'"
bash -c 'echo $NODE_ENV'    # 子 Shell 能继承 export 变量
echo ""
echo "对比：不 export 的变量子进程看不到"
MY_VAR=hello
echo "命令：bash -c 'echo \$MY_VAR'"
bash -c 'echo $MY_VAR'      # 输出为空

echo -e "\n[7] 一次设置多个变量"
export PORT=3000 DB_HOST=127.0.0.1 DB_PORT=3306
echo "PORT=$PORT  DB_HOST=$DB_HOST  DB_PORT=$DB_PORT"

echo -e "\n[8] 变量扩展与字符串操作"
cat <<'EOF'
# 变量赋值（等号两边不能有空格！）
VAR="hello world"

# 使用变量
echo $VAR
echo ${VAR}          # 推荐加花括号，避免歧义

# 字符串长度
echo ${#VAR}         # 11

# 截取子串
echo ${VAR:0:5}      # hello（从 0 开始取 5 个字符）
echo ${VAR:6}        # world（从 6 开始到结尾）

# 默认值
echo ${UNDEFINED:-default}    # default（变量未定义时用默认值）
echo ${UNDEFINED:=default}    # default 并赋值

# 替换
echo ${VAR/world/linux}       # hello linux

# 删除模式
FILE="/opt/ecommerce/backend/main.js"
echo ${FILE##*/}    # main.js（删除最长的 /* 前缀）
echo ${FILE%/*}     # /opt/ecommerce/backend（删除最短 /* 后缀）
EOF

# ---------- 3. PATH 环境变量 ----------

echo -e "\n[9] PATH —— 命令搜索路径"
echo "命令：echo \$PATH"
echo "$PATH"
echo ""
echo "说明：执行命令时，Shell 按 PATH 中目录顺序查找可执行文件"
echo "      用 which 查看命令位置：which node"

echo -e "\n[10] 临时添加 PATH"
echo "命令：export PATH=\$PATH:/usr/local/go/bin"
export PATH=$PATH:/usr/local/go/bin
echo "新 PATH: $PATH"

echo -e "\n[11] PATH 优先级问题"
cat <<'EOF'
# PATH 中前面的目录优先
# 比如自己编译的 nginx 在 /usr/local/nginx/sbin
export PATH=/usr/local/nginx/sbin:$PATH
# 这样执行 nginx 会用 /usr/local/nginx/sbin/nginx，而不是系统的

# 查看命令实际路径
which nginx
type nginx           # 显示命令类型（alias/builtin/file）
EOF

# ---------- 4. ~/.bashrc 用户级持久化 ----------

echo -e "\n[12] ~/.bashrc —— 用户级配置（推荐）"
echo "说明：每次打开新终端都执行"
echo "命令：tail -n 10 ~/.bashrc"
tail -n 10 ~/.bashrc 2>/dev/null || echo "（文件不存在）"

echo -e "\n[13] 向 ~/.bashrc 添加环境变量"
cat <<'EOF'
# 方式一：直接追加
echo 'export NODE_ENV=production' >> ~/.bashrc
echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc
echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc

# 方式二：编辑后添加（推荐，便于管理）
vim ~/.bashrc
# 在文件末尾添加：
# # Custom environment variables
# export NODE_ENV=production
# export PATH=$PATH:$HOME/.local/bin

# 立即生效（重要！）
source ~/.bashrc
# 或
. ~/.bashrc
EOF

echo -e "\n[14] ~/.bashrc 加载时机"
cat <<'EOF'
~/.bashrc 在以下场景加载：
1. 打开新终端窗口
2. bash 子进程启动
3. tmux 新建窗口

不会加载的场景：
1. SSH 登录（加载 ~/.bash_profile 或 ~/.profile）
2. 执行脚本（脚本用 #!/bin/bash 但不读 bashrc）
3. systemd 启动的服务

所以 systemd 服务的环境变量需要在 .service 文件中用 Environment= 设置
EOF

# ---------- 5. ~/.bash_profile / ~/.profile ----------

echo -e "\n[15] ~/.bash_profile —— 用户登录时加载"
cat <<'EOF'
# 加载时机：用户登录（SSH / su - / tty 登录）
# Ubuntu 默认不创建 ~/.bash_profile，使用 ~/.profile
# ~/.profile 通常会调用 ~/.bashrc

# 标准模板
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# 添加登录时执行的命令
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bash_profile
EOF

echo -e "\n[16] ~/.profile —— Ubuntu 默认用户级配置"
echo "命令：ls -l ~/.profile ~/.bash_profile ~/.bashrc 2>/dev/null"
ls -l ~/.profile ~/.bash_profile ~/.bashrc 2>/dev/null

echo -e "\n[17] ~/.bashrc vs ~/.bash_profile vs ~/.profile"
cat <<'EOF'
┌──────────────────┬──────────────────────┬─────────────────────┐
│ 文件             │ 加载时机             │ 用途                │
├──────────────────┼──────────────────────┼─────────────────────┤
│ ~/.bash_profile  │ 登录 Shell（SSH等）  │ 用户登录设置        │
│ ~/.bashrc        │ 非登录 Shell（新终端）│ 用户常用配置        │
│ ~/.profile       │ 登录 Shell（兼容）   │ Ubuntu 默认         │
│ ~/.bash_logout   │ 登出时               │ 清理操作            │
└──────────────────┴──────────────────────┴─────────────────────┘

最佳实践：
1. 把所有配置写在 ~/.bashrc
2. 在 ~/.bash_profile 中 source ~/.bashrc
3. 这样无论登录还是非登录 Shell 都能生效

# ~/.bash_profile 内容
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
EOF

# ---------- 6. /etc/profile 全局 ----------

echo -e "\n[18] /etc/profile —— 全局用户登录配置"
echo "命令：cat /etc/profile | grep -v '^#' | grep -v '^$' | head -n 15"
cat /etc/profile 2>/dev/null | grep -v '^#' | grep -v '^$' | head -n 15

echo -e "\n[19] /etc/profile 修改"
cat <<'EOF'
# /etc/profile 影响所有用户
# 谨慎修改！建议用 /etc/profile.d/ 模块化方式

# 示例：全局添加 JAVA_HOME
sudo tee -a /etc/profile <<'EOF'
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin
EOF

# 立即生效
source /etc/profile
EOF

# ---------- 7. /etc/profile.d/ 模块化（推荐）----------

echo -e "\n[20] /etc/profile.d/ —— 模块化全局配置（强烈推荐）"
echo "命令：ls -l /etc/profile.d/"
ls -l /etc/profile.d/ 2>/dev/null

echo -e "\n[21] 创建自定义模块化配置"
cat <<'EOF'
# 为电商项目创建独立配置文件
sudo tee /etc/profile.d/ecommerce.sh <<'EOF'
# 电商项目环境变量
export NODE_ENV=production
export APP_ROOT=/opt/ecommerce
export PATH=$PATH:$APP_ROOT/scripts

# Java 环境
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin

# Go 环境
export GOROOT=/usr/local/go
export GOPATH=$HOME/go
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin
EOF

# 必须有可执行权限
sudo chmod +x /etc/profile.d/ecommerce.sh

# 立即生效
source /etc/profile.d/ecommerce.sh

# 优势：
# 1. 不同应用配置独立，互不影响
# 2. 删除某应用时只需删除对应 .sh 文件
# 3. /etc/profile 会自动加载 /etc/profile.d/*.sh
EOF

echo -e "\n[22] /etc/profile.d/ 现有文件示例"
echo "命令：cat /etc/profile.d/*.sh 2>/dev/null | head -n 20"
cat /etc/profile.d/*.sh 2>/dev/null | head -n 20

# ---------- 8. /etc/environment 系统级 ----------

echo -e "\n[23] /etc/environment —— 系统级 KEY=VALUE（PAM 阶段加载）"
echo "命令：cat /etc/environment"
cat /etc/environment 2>/dev/null

echo -e "\n[24] /etc/environment 特点"
cat <<'EOF'
特点：
1. 由 PAM 在登录时读取
2. 只支持 KEY=VALUE 格式
3. 不支持变量展开（不能用 $VAR）
4. 影响所有用户、所有进程

# 示例
sudo tee -a /etc/environment <<'EOF'
NODE_ENV=production
JAVA_HOME=/usr/lib/jvm/java-17
APP_ROOT=/opt/ecommerce
EOF

# 注意：不支持 PATH=$PATH:/xxx 这种语法！
# PATH 已经存在的话直接覆盖，需要写完整
EOF

# ---------- 9. source 立即生效 ----------

echo -e "\n[25] source —— 立即重新加载配置"
cat <<'EOF'
# 修改 ~/.bashrc 后立即生效
source ~/.bashrc
# 简写
. ~/.bashrc

# 修改 /etc/profile 后
source /etc/profile

# 修改 /etc/profile.d/xxx.sh 后
source /etc/profile.d/xxx.sh

# 不用 source 的话需要：
# 1. 退出重新登录
# 2. 或打开新终端
EOF

echo -e "\n[26] source vs bash 执行脚本"
cat <<'EOF'
source script.sh   # 在当前 Shell 执行，变量/函数保留
. script.sh        # source 的简写
bash script.sh     # 在子 Shell 执行，变量不保留
./script.sh        # 同 bash，需可执行权限

# 测试
echo 'export TEST_VAR=hello' > /tmp/test.sh
bash /tmp/test.sh
echo $TEST_VAR        # 空（子 Shell 设置不影响父 Shell）

source /tmp/test.sh
echo $TEST_VAR        # hello
EOF

# ---------- 10. systemd 服务环境变量 ----------

echo -e "\n[27] systemd 服务的环境变量配置"
cat <<'EOF'
# systemd 服务不会读取 ~/.bashrc 或 /etc/profile
# 需要在单元文件中显式声明

# 方法一：Environment= 直接设置
[Service]
Environment="NODE_ENV=production"
Environment="PORT=3000"
Environment="DB_HOST=127.0.0.1"

# 方法二：EnvironmentFile= 从文件加载
[Service]
EnvironmentFile=-/etc/default/ecommerce-backend
EnvironmentFile=-/opt/ecommerce/backend/.env
# 前缀 - 表示文件不存在不报错

# /etc/default/ecommerce-backend 内容
NODE_ENV=production
PORT=3000
DB_HOST=127.0.0.1
DB_PORT=3306

# 修改后必须
sudo systemctl daemon-reload
sudo systemctl restart ecommerce-backend

# 验证服务实际的环境变量
cat /proc/$(pgrep -f ecommerce)/environ | tr '\0' '\n' | grep NODE_ENV
# 或
systemctl show ecommerce-backend -p Environment
EOF

# ---------- 11. 环境变量优先级 ----------

echo -e "\n[28] 环境变量加载顺序与优先级"
cat <<'EOF'
登录 Shell 加载顺序（后者覆盖前者）：
1. /etc/environment          （PAM 阶段，最早）
2. /etc/profile              （登录 Shell 启动）
3. /etc/profile.d/*.sh       （被 /etc/profile 调用）
4. ~/.bash_profile 或 ~/.profile  （用户登录 Shell）
   └─ ~/.bashrc              （通常被 bash_profile 调用）

非登录 Shell（新终端/tmux）：
1. ~/.bashrc

systemd 服务：
1. /etc/environment          （PAM 阶段，如果 UsePAM=yes）
2. 单元文件中的 Environment= 与 EnvironmentFile=

优先级（高覆盖低）：
systemd Environment > ~/.bashrc > ~/.bash_profile > /etc/profile.d/ > /etc/profile > /etc/environment
EOF

echo -e "\n[29] 实战：电商项目环境变量完整配置"
cat <<'EOF'
# 1. 系统级（所有用户、所有进程）
sudo tee /etc/environment <<'EOF'
NODE_ENV=production
EOF

# 2. 全局模块化（用户登录时加载）
sudo tee /etc/profile.d/ecommerce.sh <<'EOF'
export APP_ROOT=/opt/ecommerce
export PATH=$PATH:$APP_ROOT/scripts
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
EOF
sudo chmod +x /etc/profile.d/ecommerce.sh

# 3. 用户级（deploy 用户）
# 切换到 deploy 用户：su - deploy
# 然后编辑 ~/.bashrc 添加：
echo 'export NODE_ENV=production' >> ~/.bashrc
echo 'alias ll="ls -alF"' >> ~/.bashrc
echo 'alias gs="git status"' >> ~/.bashrc

# 4. 服务级（systemd 单元文件）
# /etc/systemd/system/ecommerce-backend.service
# [Service]
# Environment="NODE_ENV=production"
# Environment="PORT=3000"
# EnvironmentFile=-/opt/ecommerce/backend/.env

# 5. 应用级（.env 文件，被应用代码读取）
# /opt/ecommerce/backend/.env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=ecommerce
DB_PASSWORD=secret
REDIS_URL=redis://127.0.0.1:6379
JWT_SECRET=your-jwt-secret
EOF

# ---------- 12. 常用环境变量速查 ----------

echo -e "\n[30] 常用环境变量速查"
cat <<'EOF'
┌─────────────────┬──────────────────────────────────────────────┐
│ 变量            │ 用途                                         │
├─────────────────┼──────────────────────────────────────────────┤
│ PATH            │ 命令搜索路径                                │
│ HOME            │ 用户家目录                                  │
│ USER            │ 当前用户名                                  │
│ SHELL           │ 默认 Shell                                  │
│ PWD             │ 当前工作目录                                │
│ LANG            │ 系统语言                                    │
│ LD_LIBRARY_PATH │ 动态库搜索路径                              │
│ NODE_ENV        │ Node.js 环境（development/production）      │
│ JAVA_HOME       │ JDK 安装路径                                │
│ GOPATH          │ Go 工作空间                                 │
│ PYTHONPATH      │ Python 模块搜索路径                         │
│ NVM_DIR         │ nvm 安装目录                                │
│ EDITOR          │ 默认编辑器                                  │
│ TZ              │ 时区（如 Asia/Shanghai）                    │
│ http_proxy      │ HTTP 代理                                   │
│ HTTPS_PROXY     │ HTTPS 代理                                  │
│ NO_PROXY        │ 不走代理的地址                              │
└─────────────────┴──────────────────────────────────────────────┘
EOF

# 清理
rm -f /tmp/test.sh

echo -e "\n============================================================"
echo "  Day08 - 04 环境变量管理演示 完成"
echo "============================================================"
