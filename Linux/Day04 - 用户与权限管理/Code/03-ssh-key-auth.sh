#!/bin/bash
# 文件用途：SSH 密钥认证配置脚本
#           生成密钥对、配置 authorized_keys、修改 sshd_config 禁用密码登录
#           SSH 免密登录验证步骤
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：bash 03-ssh-key-auth.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本演示 SSH 密钥认证的完整配置流程。
#   包括：生成密钥对、配置 authorized_keys、修改 sshd_config。
#   ⚠️ 注意：修改 sshd_config 前，请保持当前 SSH 会话不断开！
#   另开终端测试新配置能否登录，否则可能被锁在外面。
#   脚本可重复执行。
# ============================================================

echo "================================================"
echo "  SSH 密钥认证配置演示"
echo "  当前用户：$(whoami)"
echo "  主机名：$(hostname)"
echo "================================================"

# === 1. SSH 密钥认证原理 ===
echo ""
echo ">>> [1] SSH 密钥认证原理..."
echo "    工作流程："
echo "    1. 客户端生成密钥对（私钥 + 公钥）"
echo "    2. 客户端把公钥传到服务器的 ~/.ssh/authorized_keys"
echo "    3. 客户端连接时，服务器用公钥挑战客户端"
echo "    4. 客户端用私钥解密挑战，证明身份"
echo "    5. 整个过程不传输密码，更安全"
echo ""
echo "    对称密码 vs 密钥认证："
echo "    密码认证：你知道什么 → 可能被暴力破解"
echo "    密钥认证：你拥有什么 → 私钥不离开本地"

# === 2. 检查现有密钥 ===
echo ""
echo ">>> [2] 检查现有 SSH 密钥..."

SSH_DIR="$HOME/.ssh"

echo "---- ~/.ssh/ 目录状态 ----"
if [ -d "$SSH_DIR" ]; then
    echo "    ~/.ssh/ 已存在"
    ls -la "$SSH_DIR"
else
    echo "    ~/.ssh/ 不存在"
fi

echo ""
echo "---- 检查现有密钥文件 ----"
for key in id_rsa id_ed25519 id_ecdsa id_dsa; do
    if [ -f "$SSH_DIR/$key" ]; then
        echo "    [✓] $SSH_DIR/$key （私钥）"
    fi
    if [ -f "$SSH_DIR/$key.pub" ]; then
        echo "    [✓] $SSH_DIR/$key.pub （公钥）"
    fi
done

if [ -f "$SSH_DIR/authorized_keys" ]; then
    echo ""
    echo "---- authorized_keys 内容（公钥数量）----"
    echo "    公钥数：$(wc -l < "$SSH_DIR/authorized_keys")"
fi

# === 3. 生成 SSH 密钥对 ===
echo ""
echo ">>> [3] 生成 SSH 密钥对..."

echo "---- 密钥算法对比 ----"
echo "    算法       安全性    速度    兼容性    推荐"
echo "    --------   ------    ----    ------    ----"
echo "    RSA 2048   中        快      最好      不推荐（已不够安全）"
echo "    RSA 4096   高        中      最好      可用"
echo "    ECDSA      高        快      好        可用"
echo "    Ed25519    最高      最快    较新      ★ 推荐"

echo ""
echo "---- 生成 Ed25519 密钥（推荐）----"
echo "    命令：ssh-keygen -t ed25519 -C \"deploy@$(hostname)\""
echo "    说明："
echo "      -t ed25519  : 算法类型"
echo "      -C \"comment\": 备注（通常用 邮箱@主机）"
echo "      -f path     : 指定密钥文件路径"
echo "      -N \"\"       : 空密码（自动化场景）"
echo "      -b 4096     : 仅 RSA 有效，指定位数"

# 实际生成密钥（如果不存在）
ED25519_KEY="$SSH_DIR/id_ed25519"
if [ -f "$ED25519_KEY" ]; then
    echo ""
    echo "    Ed25519 密钥已存在，跳过生成"
else
    echo ""
    echo "    正在生成 Ed25519 密钥对..."
    mkdir -p "$SSH_DIR"
    chmod 700 "$SSH_DIR"
    # 生成密钥（空密码，便于自动化演示）
    ssh-keygen -t ed25519 -C "deploy@$(hostname)" -f "$ED25519_KEY" -N "" <<< "y" >/dev/null 2>&1 || \
    ssh-keygen -t ed25519 -C "deploy@$(hostname)" -f "$ED25519_KEY" -N "" >/dev/null 2>&1
    echo "    密钥已生成"
fi

echo ""
echo "---- 生成的密钥文件 ----"
ls -la "$SSH_DIR/id_ed25519"* 2>/dev/null

echo ""
echo "---- 私钥内容（仅显示首尾，不泄露完整内容）----"
head -n 1 "$ED25519_KEY"
echo "    ...（中间内容省略）..."
tail -n 1 "$ED25519_KEY"

echo ""
echo "---- 公钥内容（可公开）----"
cat "$ED25519_KEY.pub"

echo ""
echo "---- 公钥指纹 ----"
ssh-keygen -lf "$ED25519_KEY.pub"

echo ""
echo "---- 公钥 Base64 指纹（MD5）----"
ssh-keygen -E md5 -lf "$ED25519_KEY.pub"

# === 4. 配置 authorized_keys ===
echo ""
echo ">>> [4] 配置 authorized_keys（允许公钥登录）..."

AUTH_KEYS="$SSH_DIR/authorized_keys"

echo "---- authorized_keys 权限要求 ----"
echo "    ~/.ssh/                700"
echo "    ~/.ssh/authorized_keys 600"
echo "    ~/.ssh/id_*           600（私钥）"
echo "    ~/.ssh/id_*.pub       644（公钥）"
echo "    ~/.ssh/config         600"
echo "    ~/.ssh/known_hosts    644"

echo ""
echo "---- 设置正确的权限 ----"
chmod 700 "$SSH_DIR"
touch "$AUTH_KEYS"
chmod 600 "$AUTH_KEYS"
ls -la "$SSH_DIR/"

echo ""
echo "---- 把公钥添加到 authorized_keys（模拟本机免密登录本机）----"
# 读取公钥
PUB_KEY=$(cat "$ED25519_KEY.pub")

# 检查是否已存在
if grep -qF "$PUB_KEY" "$AUTH_KEYS" 2>/dev/null; then
    echo "    公钥已在 authorized_keys 中，跳过添加"
else
    echo "$PUB_KEY" >> "$AUTH_KEYS"
    echo "    已添加公钥到 authorized_keys"
fi

echo ""
echo "---- authorized_keys 内容 ----"
cat "$AUTH_KEYS"

echo ""
echo "---- authorized_keys 行数（公钥数量）----"
wc -l "$AUTH_KEYS"

# === 5. ssh-copy-id 安装公钥到远程 ===
echo ""
echo ">>> [5] ssh-copy-id 安装公钥到远程服务器..."

echo "---- ssh-copy-id 命令说明 ----"
echo "    命令：ssh-copy-id deploy@192.168.1.100"
echo "    作用：自动把本地公钥传到远程的 ~/.ssh/authorized_keys"
echo "    选项："
echo "      -i key.pub    : 指定公钥文件"
echo "      -p port       : 指定端口"
echo "      -f            : 强制模式（不检查是否已存在）"

echo ""
echo "---- 常用示例 ----"
echo "    ssh-copy-id deploy@192.168.1.100"
echo "    ssh-copy-id -i ~/.ssh/id_ed25519.pub deploy@192.168.1.100"
echo "    ssh-copy-id -p 2222 deploy@192.168.1.100"
echo "    ssh-copy-id -i ~/.ssh/id_rsa.pub deploy@192.168.1.100"

echo ""
echo "---- 手动安装公钥（如 ssh-copy-id 不可用）----"
echo "    cat ~/.ssh/id_ed25519.pub | ssh deploy@192.168.1.100 \\"
echo "        \"mkdir -p ~/.ssh && chmod 700 ~/.ssh && \\"
echo "         cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\""

echo ""
echo "---- 测试本机免密登录 ----"
echo "    执行：ssh localhost echo 'SSH 免密登录成功'"
echo "    （如已配置本机公钥到本机 authorized_keys，应免密执行）"
ssh -o StrictHostKeyChecking=no -o BatchMode=yes localhost echo "SSH 免密登录测试成功" 2>/dev/null || \
    echo "    （本机免密测试需要确认，可手动执行：ssh localhost）"

# === 6. SSH 客户端配置文件 ===
echo ""
echo ">>> [6] SSH 客户端配置文件 ~/.ssh/config..."

CONFIG_FILE="$SSH_DIR/config"

echo "---- 创建 SSH config 文件（示例）----"
cat > "$CONFIG_FILE" <<EOF
# SSH 客户端配置文件
# 文件权限：chmod 600 ~/.ssh/config

# 电商项目主服务器
Host ecommerce
    HostName 192.168.1.100
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3

# 数据库服务器
Host db-server
    HostName 10.0.0.20
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519

# 跳板机配置
Host jump
    HostName jump.example.com
    User deploy
    Port 22

# 通过跳板机连接内网服务器
Host internal
    HostName 192.168.10.100
    User deploy
    ProxyJump jump

# 通用配置
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    AddKeysToAgent yes
EOF
chmod 600 "$CONFIG_FILE"

echo "    配置文件内容："
cat "$CONFIG_FILE"

echo ""
echo "---- 配置后可用别名连接 ----"
echo "    ssh ecommerce          # 连接电商服务器"
echo "    scp file.txt ecommerce:/tmp/   # 用别名传输文件"
echo "    rsync -avz ./project/ ecommerce:/opt/ecommerce/backend/"

# === 7. 修改 sshd_config 禁用密码登录 ===
echo ""
echo ">>> [7] 修改 sshd_config 禁用密码登录（⚠️ 需 sudo）..."

SSHD_CONFIG="/etc/ssh/sshd_config"

echo "    ⚠️ 警告：修改 sshd_config 前，请保持当前 SSH 会话不断开！"
echo "    另开终端测试新配置能否登录，否则可能被锁在外面。"
echo ""

if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
    echo "---- 当前 sshd_config 关键配置 ----"
    grep -E "^(Port|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|MaxAuthTries|AllowUsers|AllowGroups)" "$SSHD_CONFIG" 2>/dev/null || \
    echo "    （使用默认值）"

    echo ""
    echo "---- 建议的安全配置 ----"
    echo "    Port 22                        # 可改为非标准端口（如 22222）"
    echo "    PermitRootLogin no             # 禁止 root 直接登录"
    echo "    PasswordAuthentication no      # 禁用密码登录（仅密钥）"
    echo "    PubkeyAuthentication yes       # 启用密钥认证"
    echo "    MaxAuthTries 3                 # 最大认证尝试次数"
    echo "    AllowUsers deploy              # 仅允许指定用户登录"
    echo "    AllowGroups sudo               # 或按组允许"

    echo ""
    echo "---- 备份并修改 sshd_config ----"
    # 备份
    cp "$SSHD_CONFIG" "${SSHD_CONFIG}.bak.$(date +%Y%m%d%H%M%S)"
    echo "    已备份到 ${SSHD_CONFIG}.bak.$(date +%Y%m%d%H%M%S)"

    # 修改配置（注释掉原有行，添加新配置）
    # 注意：这里仅演示，不实际禁用密码登录，避免把用户锁在外面
    echo ""
    echo "    如需实际修改，请手动执行以下命令："
    echo "    sudo vim /etc/ssh/sshd_config"
    echo "    修改以下行："
    echo "      #PasswordAuthentication yes → PasswordAuthentication no"
    echo "      #PermitRootLogin prohibit-password → PermitRootLogin no"
    echo "    修改后重启："
    echo "      sudo systemctl restart sshd"
    echo ""
    echo "    或用 sed 一键修改（危险！确保密钥已配置好）："
    echo "      sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config"
    echo "      sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config"
    echo "      sudo systemctl restart sshd"

    # 实际创建一个推荐配置的示例文件（不覆盖原文件）
    cat > /tmp/sshd_config_recommended.conf <<'EOF'
# 推荐的 sshd_config 安全配置（仅供参考，不要直接覆盖原文件）
Port 22
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
AllowUsers deploy
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*
EOF
    echo ""
    echo "    推荐配置已保存到 /tmp/sshd_config_recommended.conf"
    echo "    可查看：cat /tmp/sshd_config_recommended.conf"

    echo ""
    echo "---- 测试 sshd 配置语法 ----"
    sshd -t 2>&1 && echo "    当前 sshd_config 语法正确" || echo "    当前 sshd_config 有语法错误"

else
    echo "    需要 root 权限修改 sshd_config"
    echo "    请执行：sudo bash $0"
    echo "    或手动修改：sudo vim /etc/ssh/sshd_config"
fi

# === 8. SSH 安全加固建议 ===
echo ""
echo ">>> [8] SSH 安全加固建议..."

echo "---- 1. 使用密钥认证，禁用密码 ----"
echo "    ssh-keygen -t ed25519"
echo "    ssh-copy-id deploy@server"
echo "    修改 sshd_config: PasswordAuthentication no"

echo ""
echo "---- 2. 禁止 root 直接登录 ----"
echo "    sshd_config: PermitRootLogin no"
echo "    用普通用户 + sudo 代替 root 直连"

echo ""
echo "---- 3. 修改默认端口 ----"
echo "    sshd_config: Port 22222"
echo "    连接时：ssh -p 22222 deploy@server"

echo ""
echo "---- 4. 限制登录用户 ----"
echo "    sshd_config: AllowUsers deploy"
echo "    或：AllowGroups sudo"

echo ""
echo "---- 5. 使用 fail2ban 防暴力破解 ----"
echo "    sudo apt install fail2ban"
echo "    自动封禁多次失败登录的 IP"

echo ""
echo "---- 6. 定期轮换密钥 ----"
echo "    定期生成新密钥，更新 authorized_keys"
echo "    删除离职员工的公钥"

echo ""
echo "---- 7. 监控 SSH 登录日志 ----"
echo "    sudo tail /var/log/auth.log         # Ubuntu"
echo "    sudo journalctl -u sshd -f          # 实时监控"
echo "    last -n 20                          # 最近登录记录"

# === 9. SSH 常用操作汇总 ===
echo ""
echo ">>> [9] SSH 常用操作汇总..."

echo "---- 基本连接 ----"
echo "    ssh user@host                     # 默认 22 端口"
echo "    ssh -p 2222 user@host             # 指定端口"
echo "    ssh -i ~/.ssh/key user@host       # 指定私钥"
echo "    ssh user@host 'command'           # 执行远程命令后退出"

echo ""
echo "---- 端口转发 ----"
echo "    ssh -L 8080:localhost:80 user@host    # 本地转发"
echo "    ssh -R 9090:localhost:3000 user@host  # 远程转发"
echo "    ssh -D 1080 user@host                 # SOCKS5 代理"

echo ""
echo "---- 文件传输 ----"
echo "    scp file user@host:/path/             # 上传"
echo "    scp user@host:/path/file ./            # 下载"
echo "    scp -P 2222 file user@host:/path/     # 指定端口"
echo "    scp -r dir user@host:/path/           # 递归"
echo "    rsync -avz ./dir/ user@host:/path/    # 增量同步"

echo ""
echo "---- SSH 代理（管理多个密钥）----"
echo "    eval \$(ssh-agent)                    # 启动 agent"
echo "    ssh-add ~/.ssh/id_ed25519             # 添加密钥到 agent"
echo "    ssh-add -l                            # 查看已添加的密钥"
echo "    ssh-add -D                            # 清除所有密钥"

# === 10. 验证清单 ===
echo ""
echo ">>> [10] SSH 密钥认证验证清单..."

echo "---- 检查清单 ----"
echo "    1. 密钥对已生成"
if [ -f "$SSH_DIR/id_ed25519" ]; then
    echo "       [✓] 私钥：$SSH_DIR/id_ed25519"
    echo "       [✓] 公钥：$SSH_DIR/id_ed25519.pub"
else
    echo "       [✗] 密钥未生成"
fi

echo ""
echo "    2. 权限正确"
if [ -d "$SSH_DIR" ]; then
    ssh_perm=$(stat -c '%a' "$SSH_DIR")
    if [ "$ssh_perm" = "700" ]; then
        echo "       [✓] ~/.ssh/ 权限 700"
    else
        echo "       [✗] ~/.ssh/ 权限 $ssh_perm（应为 700）"
    fi
fi
if [ -f "$SSH_DIR/id_ed25519" ]; then
    key_perm=$(stat -c '%a' "$SSH_DIR/id_ed25519")
    if [ "$key_perm" = "600" ]; then
        echo "       [✓] 私钥权限 600"
    else
        echo "       [✗] 私钥权限 $key_perm（应为 600）"
    fi
fi
if [ -f "$AUTH_KEYS" ]; then
    auth_perm=$(stat -c '%a' "$AUTH_KEYS")
    if [ "$auth_perm" = "600" ]; then
        echo "       [✓] authorized_keys 权限 600"
    else
        echo "       [✗] authorized_keys 权限 $auth_perm（应为 600）"
    fi
    echo "       [✓] authorized_keys 含 $(wc -l < "$AUTH_KEYS") 个公钥"
fi

echo ""
echo "    3. 测试免密登录"
echo "       执行：ssh localhost echo 'success'"
echo "       如输出 success 则免密登录配置成功"

echo ""
echo "    4. 远程服务器配置（需在远程执行）"
echo "       [ ] 公钥已添加到远程 ~/.ssh/authorized_keys"
echo "       [ ] sshd_config: PubkeyAuthentication yes"
echo "       [ ] sshd_config: PasswordAuthentication no（可选）"
echo "       [ ] sshd 服务已重启：sudo systemctl restart sshd"

echo ""
echo "================================================"
echo "  SSH 密钥认证配置演示完成！"
echo "  密钥文件：$SSH_DIR/id_ed25519（私钥）"
echo "  公钥文件：$SSH_DIR/id_ed25519.pub（公钥）"
echo "  配置文件：$SSH_DIR/config"
echo "  ⚠️ 私钥务必保密！不要泄露或上传到公开仓库！"
echo "================================================"
