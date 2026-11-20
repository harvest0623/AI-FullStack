#!/bin/bash
# ============================================================
# 文件名：04-ssh-tunnel-rsync.sh
# 用途：演示 SSH 高级用法：端口转发（-L/-R/-D）、~/.ssh/config 配置、
#       scp 上传下载、rsync 增量同步
# 适用：Ubuntu 22.04 LTS
# 场景：电商项目服务器（192.168.1.100）的远程访问与文件同步
# 注意：本脚本以演示为主，真实传输需替换为目标主机与文件
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day06 - 04 SSH 高级用法演示"
echo "  端口转发 / SSH 配置 / scp / rsync"
echo "============================================================"

# 远程主机配置（演示用，可改成实际服务器）
REMOTE_HOST="192.168.1.100"
REMOTE_USER="deploy"
REMOTE_PORT="22"

# ---------- 1. SSH 端口转发 -L 本地转发 ----------

echo -e "\n[1] SSH 本地转发（-L）—— 把远程服务映射到本地端口"
cat <<EOF
场景：MySQL 仅监听 192.168.1.100 的 127.0.0.1:3306，本机无法直连
命令：ssh -L 13306:127.0.0.1:3306 ${REMOTE_USER}@${REMOTE_HOST}
说明：在本地 13306 端口监听，所有发往 127.0.0.1:13306 的流量
      都会通过 SSH 隧道转发到远程主机的 127.0.0.1:3306
之后访问：mysql -h 127.0.0.1 -P 13306 -u root -p

# 后台运行（-f 后台 -N 不执行远程命令 -T 不分配 TTY）
ssh -fNT -L 13306:127.0.0.1:3306 ${REMOTE_USER}@${REMOTE_HOST}

# 转发到远程网络中的另一台机器（数据库在内网另一台）
ssh -L 13306:10.0.0.5:3306 ${REMOTE_USER}@${REMOTE_HOST}
EOF

echo -e "\n[2] 本地转发的典型应用场景"
cat <<EOF
1. 远程 MySQL/Redis 仅监听 127.0.0.1，本地用 GUI 工具连接
   ssh -L 13306:127.0.0.1:3306 deploy@192.168.1.100
   ssh -L 16379:127.0.0.1:6379 deploy@192.168.1.100

2. 访问内网 Web 服务
   ssh -L 18080:10.0.0.8:80 deploy@192.168.1.100
   浏览器访问 http://127.0.0.1:18080

3. 同时转发多个端口
   ssh -L 13306:127.0.0.1:3306 -L 16379:127.0.0.1:6379 deploy@192.168.1.100
EOF

# ---------- 2. SSH 端口转发 -R 远程转发 ----------

echo -e "\n[3] SSH 远程转发（-R）—— 把本地服务映射到远程端口"
cat <<EOF
场景：本地开发服务器跑在 3000 端口，想让 192.168.1.100 上的其他进程能访问
命令：ssh -R 8080:127.0.0.1:3000 ${REMOTE_USER}@${REMOTE_HOST}
说明：在远程主机 192.168.1.100 上监听 8080 端口
      远程进程访问 127.0.0.1:8080 时，流量会通过 SSH 反向转发到本地的 3000

# 后台运行
ssh -fNT -R 8080:127.0.0.1:3000 ${REMOTE_USER}@${REMOTE_HOST}

# 应用场景：
# 1. 本地开发服务暴露给远程 webhook 调试
# 2. 内网穿透（把内网服务通过公网服务器暴露出去）
EOF

echo -e "\n[4] 远程转发注意事项"
cat <<EOF
- 默认远程转发只监听 127.0.0.1，远程其他主机无法访问
- 如需让远程其他主机也能访问，需要在远程 sshd_config 设置：
  GatewayPorts yes
- 然后重启远程 sshd：sudo systemctl restart sshd
- 或使用 -R 0.0.0.0:8080:127.0.0.1:3000 显式指定绑定地址
EOF

# ---------- 3. SSH 端口转发 -D 动态转发（SOCKS5 代理）----------

echo -e "\n[5] SSH 动态转发（-D）—— SOCKS5 代理"
cat <<EOF
场景：通过 192.168.1.100 作为代理上网
命令：ssh -D 1080 ${REMOTE_USER}@${REMOTE_HOST}
说明：在本地 1080 端口启动 SOCKS5 代理服务
      所有支持 SOCKS5 的应用都可通过此代理访问

# 后台运行
ssh -fNT -D 1080 ${REMOTE_USER}@${REMOTE_HOST}

# 浏览器配置：SOCKS5 代理 127.0.0.1:1080
# 命令行测试：curl --socks5 127.0.0.1:1080 http://ifconfig.me

# 应用场景：
# 1. 通过跳板机访问内网多个服务
# 2. 突破网络限制（如公司网络访问受限资源）
EOF

echo -e "\n[6] 端口转发三种模式对比"
cat <<EOF
┌──────────┬─────┬─────────────────────┬─────────────────────────┐
│ 类型     │选项 │ 方向                │ 典型用途                │
├──────────┼─────┼─────────────────────┼─────────────────────────┤
│ 本地转发 │ -L  │ 本地→远程           │ 访问内网 MySQL/Redis    │
│ 远程转发 │ -R  │ 远程→本地           │ 把本地服务暴露给远程    │
│ 动态转发 │ -D  │ 双向（SOCKS5 代理） │ 内网穿透/代理上网       │
└──────────┴─────┴─────────────────────┴─────────────────────────┘
EOF

# ---------- 4. SSH 配置文件 ~/.ssh/config ----------

echo -e "\n[7] SSH 配置文件 ~/.ssh/config —— 简化连接命令"
cat <<EOF
# 文件位置：~/.ssh/config（权限需为 600）
# 配置后可直接 ssh ecommerce 代替 ssh -p 22 -i ~/.ssh/id_rsa deploy@192.168.1.100

# 示例配置内容：
Host ecommerce
    HostName 192.168.1.100
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_rsa_ecommerce
    ServerAliveInterval 60
    ServerAliveCountMax 3
    LocalForward 13306 127.0.0.1:3306
    LocalForward 16379 127.0.0.1:6379

Host db-server
    HostName 192.168.1.200
    User deploy
    Port 2222
    IdentityFile ~/.ssh/id_rsa_db

Host *.internal
    User deploy
    IdentityFile ~/.ssh/id_rsa_internal
    StrictHostKeyChecking no

Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    StrictHostKeyChecking accept-new
EOF

echo -e "\n[8] ~/.ssh/config 常用字段说明"
cat <<EOF
HostName        实际连接的 IP 或域名
User            登录用户名
Port            SSH 端口（默认 22）
IdentityFile    私钥文件路径
ServerAliveInterval  保持连接，每 60 秒发送心跳
ServerAliveCountMax  3 次心跳失败才断开
LocalForward    自动建立本地端口转发
ProxyJump       跳板机（旧版用 ProxyCommand）
StrictHostKeyChecking  首次连接是否询问主机指纹
EOF

echo -e "\n[9] 检查当前用户的 SSH 配置"
if [ -f ~/.ssh/config ]; then
    echo "命令：cat ~/.ssh/config"
    cat ~/.ssh/config
else
    echo "~/.ssh/config 不存在，可创建："
    echo "  mkdir -p ~/.ssh && chmod 700 ~/.ssh"
    echo "  touch ~/.ssh/config && chmod 600 ~/.ssh/config"
fi

echo -e "\n[10] 跳板机（Jump Host）配置"
cat <<EOF
# 通过跳板机访问内网服务器
# 方法一：ProxyJump（OpenSSH 7.3+，推荐）
Host internal-db
    HostName 10.0.0.5
    User deploy
    ProxyJump ecommerce      # 通过 ecommerce 跳板

# 方法二：ProxyCommand（兼容旧版）
Host internal-db
    HostName 10.0.0.5
    User deploy
    ProxyCommand ssh ecommerce -W %h:%p

# 一条命令直达内网：ssh internal-db
EOF

# ---------- 5. scp 文件传输 ----------

echo -e "\n[11] scp —— 上传文件到远程"
cat <<EOF
# 上传单个文件
scp /opt/ecommerce/backend/dist/main.js ${REMOTE_USER}@${REMOTE_HOST}:/opt/ecommerce/backend/dist/

# 上传整个目录（-r 递归）
scp -r /opt/ecommerce/backend/dist ${REMOTE_USER}@${REMOTE_HOST}:/opt/ecommerce/backend/

# 指定端口（-P 大写）
scp -P 2222 file ${REMOTE_USER}@${REMOTE_HOST}:/tmp/

# 压缩传输（-C，弱压缩，仅适合未压缩文件）
scp -C large.log ${REMOTE_USER}@${REMOTE_HOST}:/tmp/

# 使用 SSH 配置中的别名
scp file ecommerce:/tmp/
EOF

echo -e "\n[12] scp —— 从远程下载"
cat <<EOF
# 下载单个文件
scp ${REMOTE_USER}@${REMOTE_HOST}:/opt/ecommerce/logs/app.log /tmp/

# 下载整个目录
scp -r ${REMOTE_USER}@${REMOTE_HOST}:/opt/ecommerce/logs /tmp/

# 两台远程服务器之间传输（不经本地中转）
scp ${REMOTE_USER}@host1:/path/file ${REMOTE_USER}@host2:/path/
EOF

echo -e "\n[13] scp 实战：下载电商日志到本地分析"
cat <<EOF
# 下载今天的应用日志
scp deploy@192.168.1.100:/opt/ecommerce/logs/\$(date +%Y-%m-%d).log /tmp/

# 下载 Nginx 访问日志
scp deploy@192.168.1.100:/var/log/nginx/access.log /tmp/nginx-access.log

# 上传部署脚本到服务器
scp -r ./scripts deploy@192.168.1.100:/opt/ecommerce/
EOF

# ---------- 6. rsync 增量同步 ----------

echo -e "\n[14] rsync —— 增量同步（推荐生产使用）"
cat <<EOF
# 基础同步（增量，仅传差异部分）
rsync -avz /opt/ecommerce/backend/ ${REMOTE_USER}@${REMOTE_HOST}:/opt/ecommerce/backend/

# 参数说明：
# -a 归档模式（= -rlptgoD，保留权限/时间/符号链接/递归/组/属主/设备文件）
# -v 详细输出
# -z 压缩传输

# 删除目标多余文件（镜像同步，谨慎使用！）
rsync -avz --delete /opt/ecommerce/backend/ ${REMOTE_USER}@${REMOTE_HOST}:/opt/ecommerce/backend/

# 排除某些文件
rsync -avz --exclude='node_modules' --exclude='.git' --exclude='*.log' \\
  /opt/ecommerce/backend/ ${REMOTE_USER}@${REMOTE_HOST}:/opt/ecommerce/backend/

# 指定 SSH 端口
rsync -avz -e "ssh -p 2222" /src/ ${REMOTE_USER}@${REMOTE_HOST}:/dst/

# 断点续传大文件
rsync -avz --partial --progress /large-file ${REMOTE_USER}@${REMOTE_HOST}:/dst/

# 模拟运行（不真实传输，仅显示将做什么）
rsync -avz --dry-run /src/ ${REMOTE_USER}@${REMOTE_HOST}:/dst/

# 显示进度条
rsync -avz --progress /src/ ${REMOTE_USER}@${REMOTE_HOST}:/dst/
EOF

echo -e "\n[15] rsync 路径末尾斜杠非常重要"
cat <<EOF
# 源路径末尾有斜杠：把 src/ 的内容同步到 dst/
rsync -avz /src/ /dst/
# 结果：/dst/file1, /dst/file2（src 目录本身不会出现）

# 源路径末尾无斜杠：把 src 目录本身同步到 dst 下
rsync -avz /src /dst/
# 结果：/dst/src/file1, /dst/src/file2（src 作为子目录）

# 实战：把本地 backend 内容同步到远程 backend 目录
rsync -avz --delete --exclude='node_modules' \\
  /opt/ecommerce/backend/ ${REMOTE_USER}@${REMOTE_HOST}:/opt/ecommerce/backend/
EOF

echo -e "\n[16] rsync vs scp 对比"
cat <<EOF
┌──────────────┬────────────────────┬──────────────────────┐
│ 特性         │ scp                │ rsync                │
├──────────────┼────────────────────┼──────────────────────┤
│ 传输方式     │ 全量复制           │ 增量（仅传差异）     │
│ 断点续传     │ 不支持             │ 支持（--partial）    │
│ 删除同步     │ 不支持             │ 支持（--delete）     │
│ 排除文件     │ 不支持             │ --exclude            │
│ 压缩         │ -C（弱）           │ -z（更强）           │
│ 大文件效率   │ 低（每次重传）     │ 高                   │
│ 简单小文件   │ ✓ 简单             │ 略复杂               │
│ 生产部署     │ ✗ 不推荐           │ ✓ 推荐               │
└──────────────┴────────────────────┴──────────────────────┘
EOF

echo -e "\n[17] 实战：rsync 部署电商项目"
cat <<EOF
# 1. 本地构建项目
cd /workspace/ecommerce
npm run build

# 2. 同步到生产服务器（自动删除远程多余旧文件）
rsync -avz --delete \\
  --exclude='node_modules' \\
  --exclude='.git' \\
  --exclude='.env' \\
  --exclude='*.log' \\
  /workspace/ecommerce/backend/dist/ \\
  deploy@192.168.1.100:/opt/ecommerce/backend/dist/

# 3. 同步 package.json 并安装依赖
rsync -avz /workspace/ecommerce/backend/package.json \\
  deploy@192.168.1.100:/opt/ecommerce/backend/
ssh deploy@192.168.1.100 "cd /opt/ecommerce/backend && npm install --production"

# 4. 重启服务
ssh deploy@192.168.1.100 "sudo systemctl restart ecommerce-backend"
EOF

echo -e "\n[18] SSH 免密登录（公钥认证）回顾"
cat <<EOF
# 1. 本地生成密钥对（已有则跳过）
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_rsa_ecommerce

# 2. 上传公钥到远程（一键完成）
ssh-copy-id -i ~/.ssh/id_rsa_ecommerce.pub deploy@192.168.1.100

# 3. 验证免密登录
ssh -i ~/.ssh/id_rsa_ecommerce deploy@192.168.1.100

# 配合 ~/.ssh/config 后可直接：ssh ecommerce
EOF

echo -e "\n============================================================"
echo "  Day06 - 04 SSH 高级用法演示 完成"
echo "============================================================"
