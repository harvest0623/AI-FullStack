#!/bin/bash
# 文件用途：用户与组管理演示
#           创建 deploy 用户、加入 sudo 组、创建 www-data/mysql/redis 系统用户模拟
#           groupadd/gpasswd/usermod 操作、id/who/last 查看
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：sudo bash 01-user-group-management.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本演示 Linux 用户与组管理的完整流程。
#   模拟电商项目的用户体系：deploy、www-data、mysql、redis。
#   需要 root 权限执行。
#   脚本可重复执行：已存在的用户/组会跳过创建。
# ============================================================

# 严格模式
set -e

# === 0. 权限检查 ===
if [ "$EUID" -ne 0 ]; then
    echo "================================================"
    echo "  错误：本脚本需要 root 权限执行"
    echo "  请使用：sudo bash $0"
    echo "================================================"
    exit 1
fi

echo "================================================"
echo "  用户与组管理演示"
echo "  当前用户：$(whoami)"
echo "  系统时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"

# === 1. 查看当前用户与组信息 ===
echo ""
echo ">>> [1] 查看当前系统用户与组信息..."

echo "---- whoami（当前用户名）----"
whoami

echo ""
echo "---- id（当前用户 UID/GID/组）----"
id

echo ""
echo "---- who（当前登录的用户）----"
who

echo ""
echo "---- w（登录用户及其活动）----"
w | head -n 5

echo ""
echo "---- 系统中的用户数：----"
echo "    总用户数：$(wc -l < /etc/passwd)"
echo "    普通用户（UID >= 1000）："
awk -F: '$3>=1000 {print "      " $1 " (UID:" $3 ")"}' /etc/passwd

echo ""
echo "---- 系统用户（UID < 1000，前 10 个）----"
awk -F: '$3<1000 {print "      " $1 " (UID:" $3 ")"}' /etc/passwd | head -n 10

echo ""
echo "---- 系统中的组数：$(wc -l < /etc/group) ----"

# === 2. 创建 developers 组 ===
echo ""
echo ">>> [2] 创建 developers 组..."

if getent group developers >/dev/null 2>&1; then
    echo "    developers 组已存在，跳过创建"
else
    groupadd developers
    echo "    已创建 developers 组"
fi

# 查看组信息
getent group developers

# === 3. 创建 deploy 用户（部署用户）===
echo ""
echo ">>> [3] 创建 deploy 用户（部署用户）..."

if id deploy >/dev/null 2>&1; then
    echo "    deploy 用户已存在，跳过创建"
else
    # -m 创建家目录
    # -s /bin/bash 指定登录 Shell
    # -c 备注信息
    useradd -m -s /bin/bash -c "Deploy User" deploy
    echo "    已创建 deploy 用户"
    echo "    设置密码（请输入）："
    passwd deploy
fi

# 查看 deploy 用户信息
echo ""
echo "---- deploy 用户信息：----"
id deploy
getent passwd deploy

# === 4. 把 deploy 加入 sudo 组与 developers 组 ===
echo ""
echo ">>> [4] 把 deploy 加入 sudo 组与 developers 组..."

# -aG 追加到附加组（不会替换原组）
usermod -aG sudo deploy
usermod -aG developers deploy

# 等效写法：gpasswd -a deploy sudo
# gpasswd -a deploy developers

echo "    deploy 所属的组："
groups deploy

echo ""
echo "---- /etc/group 中 deploy 的归属 ----"
grep "deploy" /etc/group

# === 5. 创建系统用户（模拟服务运行用户）===
echo ""
echo ">>> [5] 创建系统用户（模拟服务运行用户）..."

# www-data 用户通常已存在（Ubuntu 预装）
for svc_user in www-data mysql redis; do
    if id "$svc_user" >/dev/null 2>&1; then
        echo "    $svc_user 用户已存在（UID: $(id -u $svc_user)）"
    else
        # -r 创建系统用户（UID 1-999）
        # -s /sbin/nologin 禁止登录
        # -M 不创建家目录
        useradd -r -s /usr/sbin/nologin -M "$svc_user"
        echo "    已创建系统用户 $svc_user（UID: $(id -u $svc_user)）"
    fi
done

echo ""
echo "---- 系统用户信息：----"
for svc_user in www-data mysql redis; do
    echo "    $svc_user:"
    getent passwd "$svc_user"
done

# === 6. 用户信息查看命令 ===
echo ""
echo ">>> [6] 用户信息查看命令..."

echo "---- id deploy（完整信息）----"
id deploy

echo ""
echo "---- groups deploy（所属组）----"
groups deploy

echo ""
echo "---- getent passwd deploy（用户信息）----"
getent passwd deploy

echo ""
echo "---- /etc/passwd 字段解析（deploy）----"
PASSWD_LINE=$(getent passwd deploy)
echo "    原始行: $PASSWD_LINE"
echo "    字段解析:"
echo "      1. 用户名      : $(echo "$PASSWD_LINE" | cut -d: -f1)"
echo "      2. 密码占位    : $(echo "$PASSWD_LINE" | cut -d: -f2)"
echo "      3. UID         : $(echo "$PASSWD_LINE" | cut -d: -f3)"
echo "      4. GID         : $(echo "$PASSWD_LINE" | cut -d: -f4)"
echo "      5. 描述信息    : $(echo "$PASSWD_LINE" | cut -d: -f5)"
echo "      6. 家目录      : $(echo "$PASSWD_LINE" | cut -d: -f6)"
echo "      7. Shell       : $(echo "$PASSWD_LINE" | cut -d: -f7)"

echo ""
echo "---- /etc/shadow 字段（仅显示状态，不显示哈希）----"
passwd -S deploy

# === 7. 登录历史查看 ===
echo ""
echo ">>> [7] 登录历史查看..."

echo "---- last（最近登录记录，前 5 条）----"
last -n 5 2>/dev/null || echo "    （无登录记录或 last 不可用）"

echo ""
echo "---- last deploy（deploy 用户登录历史）----"
last deploy -n 5 2>/dev/null || echo "    （deploy 无登录记录）"

echo ""
echo "---- lastlog（所有用户最后登录时间，前 5 个有记录的）----"
lastlog 2>/dev/null | grep -v "Never logged in" | head -n 5 || echo "    （lastlog 不可用）"

# === 8. 用户组管理演示 ===
echo ""
echo ">>> [8] 用户组管理演示..."

# 创建运维组
if getent group ops >/dev/null 2>&1; then
    echo "    ops 组已存在"
else
    groupadd ops
    echo "    已创建 ops 组"
fi

# 用 gpasswd 添加用户到组
echo ""
echo "---- gpasswd -a deploy ops（添加 deploy 到 ops 组）----"
gpasswd -a deploy ops
groups deploy

# 用 gpasswd 移除用户
echo ""
echo "---- gpasswd -d deploy ops（从 ops 组移除 deploy）----"
gpasswd -d deploy ops
groups deploy

# 修改组名
echo ""
echo "---- groupmod -n operations ops（改组名）----"
groupmod -n operations ops 2>/dev/null || echo "    （ops 可能已不存在）"
getent group operations || echo "    operations 组不存在"

# === 9. usermod 修改用户属性 ===
echo ""
echo ">>> [9] usermod 修改用户属性..."

echo "---- 修改 deploy 的备注信息 ----"
usermod -c "Ecommerce Deploy User" deploy
getent passwd deploy | cut -d: -f5

echo ""
echo "---- 修改 deploy 的 Shell 为 zsh（如已安装）----"
if command -v zsh >/dev/null 2>&1; then
    usermod -s /bin/zsh deploy
    echo "    Shell 已改为 zsh"
else
    echo "    zsh 未安装，保持 /bin/bash"
    usermod -s /bin/bash deploy
fi
getent passwd deploy | cut -d: -f7

echo ""
echo "---- 锁定/解锁用户演示 ----"
echo "    锁定前状态：$(passwd -S deploy)"
usermod -L deploy
echo "    锁定后状态：$(passwd -S deploy)"
usermod -U deploy
echo "    解锁后状态：$(passwd -S deploy)"

# === 10. su 与 sudo 演示 ===
echo ""
echo ">>> [10] su 与 sudo 演示（说明）..."

echo "---- su - deploy（切换到 deploy 用户，需交互式终端）----"
echo "    在终端中执行：su - deploy"
echo "    切换后执行 whoami、id、pwd 验证环境变量已加载"

echo ""
echo "---- sudo 命令示例 ----"
echo "    sudo whoami           # 以 root 身份执行 whoami"
echo "    sudo -u www-data whoami   # 以 www-data 身份执行"
echo "    sudo -l               # 查看当前用户的 sudo 权限"
echo "    sudo -i               # 启动交互式 root Shell"

echo ""
echo "---- 配置 sudo 免密（visudo）----"
echo "    执行：sudo visudo -f /etc/sudoers.d/deploy"
echo "    写入：deploy ALL=(ALL) NOPASSWD: ALL"

# 创建 sudoers 配置文件示例
cat > /etc/sudoers.d/deploy <<'EOF'
# deploy 用户的 sudo 权限配置
# 语法：用户 主机=(运行身份) [NOPASSWD:] 命令

# 允许 deploy 免密执行所有命令（生产环境慎用）
deploy ALL=(ALL) NOPASSWD: ALL

# 更安全的配置：仅允许执行特定命令
# deploy ALL=(ALL) /usr/bin/systemctl restart nginx
# deploy ALL=(ALL) /usr/bin/systemctl restart mysql
# deploy ALL=(ALL) /usr/bin/apt update
EOF
chmod 440 /etc/sudoers.d/deploy
echo "    已创建 /etc/sudoers.d/deploy（权限 440）"

# 验证 sudoers 语法
echo ""
echo "---- 验证 sudoers 语法 ----"
visudo -cf /etc/sudoers.d/deploy && echo "    语法正确" || echo "    语法错误！"

# === 11. 用户体系总览 ===
echo ""
echo ">>> [11] 电商项目用户体系总览..."

echo "---- 项目用户列表 ----"
echo "    用户名        UID    GID    Shell            家目录              说明"
echo "    ----------    ----   ----   --------------   ----------------    -----"
for user in deploy www-data mysql redis; do
    if id "$user" >/dev/null 2>&1; then
        info=$(getent passwd "$user")
        username=$(echo "$info" | cut -d: -f1)
        uid=$(echo "$info" | cut -d: -f3)
        gid=$(echo "$info" | cut -d: -f4)
        shell=$(echo "$info" | cut -d: -f7)
        home=$(echo "$info" | cut -d: -f6)
        comment=$(echo "$info" | cut -d: -f5)
        printf "    %-12s  %-5s  %-5s  %-16s %-18s %s\n" "$username" "$uid" "$gid" "$shell" "$home" "$comment"
    fi
done

echo ""
echo "---- 项目组列表 ----"
for group in developers sudo operations; do
    if getent group "$group" >/dev/null 2>&1; then
        info=$(getent group "$group")
        groupname=$(echo "$info" | cut -d: -f1)
        gid=$(echo "$info" | cut -d: -f3)
        members=$(echo "$info" | cut -d: -f4)
        printf "    %-15s GID:%-5s 成员:%s\n" "$groupname" "$gid" "$members"
    fi
done

echo ""
echo "================================================"
echo "  用户与组管理演示完成！"
echo "  下一步：执行 sudo bash 02-permission-management.sh"
echo "================================================"
