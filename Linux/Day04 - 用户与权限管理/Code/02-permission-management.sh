#!/bin/bash
# 文件用途：权限管理演示
#           演示 chmod 数字法/符号法、chown/chgrp、SUID/SGID/Sticky 演示
#           umask 设置、ACL setfacl/getfacl 演示
#           在 /opt/ecommerce/ 下设置项目权限
# 适用系统：Ubuntu 22.04 LTS（及更高版本）
# 执行方式：sudo bash 02-permission-management.sh
# 作者：AI-FullStack

# ============================================================
# 脚本说明：
#   本脚本演示 Linux 文件权限管理的各种命令。
#   在 /tmp/permission-demo/ 下操作，不影响系统。
#   部分操作会设置 /opt/ecommerce/ 的项目权限。
#   需要 root 权限执行。
#   脚本可重复执行。
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

# 工作目录
WORK_DIR="/tmp/permission-demo"

echo "================================================"
echo "  权限管理演示"
echo "  工作目录：$WORK_DIR"
echo "================================================"

# === 0. 初始化工作目录 ===
echo ""
echo ">>> [0] 初始化工作目录..."
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# 创建练习文件
touch "$WORK_DIR/file1.txt" "$WORK_DIR/file2.txt" "$WORK_DIR/script.sh"
echo "#!/bin/bash" > "$WORK_DIR/script.sh"
echo "echo hello" >> "$WORK_DIR/script.sh"
mkdir -p "$WORK_DIR/shared-dir"
mkdir -p "$WORK_DIR/private-dir"

echo "    初始文件列表："
ls -la "$WORK_DIR"

# === 1. 权限模型说明 ===
echo ""
echo ">>> [1] 权限模型说明..."
echo "    ls -l 第一列解析（以 -rwxr-xr-- 为例）："
echo "    - rwx r-x r--"
echo "    │ └─┬─┘ └─┬─┘ └─┬─┘"
echo "    │   │     │     └─ 其他用户（Other）：r--（读）"
echo "    │   │     └────── 所属组（Group）：r-x（读+执行）"
echo "    │   └──────────── 所有者（Owner）：rwx（读+写+执行）"
echo "    └──────────────── 文件类型（- 文件，d 目录，l 链接）"
echo ""
echo "    权限数字：r=4, w=2, x=1"
echo "    755 = rwxr-xr-x（7=4+2+1, 5=4+0+1, 5=4+0+1）"
echo "    644 = rw-r--r--（6=4+2, 4=4+0, 4=4+0）"

# === 2. chmod 数字法 ===
echo ""
echo ">>> [2] chmod 数字法修改权限..."

echo "---- chmod 755 script.sh（rwxr-xr-x，所有者全，其他读+执行）----"
chmod 755 "$WORK_DIR/script.sh"
ls -l "$WORK_DIR/script.sh"

echo ""
echo "---- chmod 644 file1.txt（rw-r--r--，所有者读写，其他只读）----"
chmod 644 "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chmod 600 file2.txt（rw-------，仅所有者读写，如密钥文件）----"
chmod 600 "$WORK_DIR/file2.txt"
ls -l "$WORK_DIR/file2.txt"

echo ""
echo "---- chmod 700 private-dir（rwx------，仅所有者可访问，如 ~/.ssh）----"
chmod 700 "$WORK_DIR/private-dir"
ls -ld "$WORK_DIR/private-dir"

echo ""
echo "---- chmod 777 shared-dir（rwxrwxrwx，全开，危险！仅演示）----"
chmod 777 "$WORK_DIR/shared-dir"
ls -ld "$WORK_DIR/shared-dir"

echo ""
echo "---- chmod 444 file1.txt（r--r--r--，全部只读）----"
chmod 444 "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

# 恢复
chmod 644 "$WORK_DIR/file1.txt"

# === 3. chmod 符号法 ===
echo ""
echo ">>> [3] chmod 符号法修改权限..."

echo "---- 当前 file1.txt 权限：$(stat -c '%A' "$WORK_DIR/file1.txt") ----"

echo ""
echo "---- chmod u+x file1.txt（所有者增加执行权限）----"
chmod u+x "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chmod u-x file1.txt（所有者去除执行权限）----"
chmod u-x "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chmod g+w file1.txt（组增加写权限）----"
chmod g+w "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chmod o-w file1.txt（其他去除写权限）----"
chmod o-w "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chmod o=r file1.txt（其他设为只读，覆盖原权限）----"
chmod o=r "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chmod a+r file1.txt（所有人增加读权限）----"
chmod a+r "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chmod u+x,g+w file1.txt（多个修改）----"
chmod u+x,g+w "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chmod +x script.sh（等同 a+x，所有人增加执行）----"
chmod +x "$WORK_DIR/script.sh"
ls -l "$WORK_DIR/script.sh"

# === 4. chown / chgrp 修改所有者与组 ===
echo ""
echo ">>> [4] chown / chgrp 修改所有者与组..."

# 确保 deploy 用户存在（如不存在则创建）
if ! id deploy >/dev/null 2>&1; then
    useradd -m -s /bin/bash deploy 2>/dev/null || true
fi
if ! id www-data >/dev/null 2>&1; then
    useradd -r -s /usr/sbin/nologin www-data 2>/dev/null || true
fi

echo "---- 当前 file1.txt 所有者：$(stat -c '%U:%G' "$WORK_DIR/file1.txt") ----"

echo ""
echo "---- chown deploy file1.txt（修改所有者为 deploy）----"
chown deploy "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chown deploy:www-data file1.txt（修改所有者与组）----"
chown deploy:www-data "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chown :deploy file1.txt（仅修改组）----"
chown :deploy "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chgrp www-data file1.txt（用 chgrp 修改组，等同 chown :www-data）----"
chgrp www-data "$WORK_DIR/file1.txt"
ls -l "$WORK_DIR/file1.txt"

echo ""
echo "---- chown -R deploy:deploy shared-dir/（递归修改目录及内容）----"
mkdir -p "$WORK_DIR/shared-dir/sub"
touch "$WORK_DIR/shared-dir/file{1..3}.txt"
chown -R deploy:deploy "$WORK_DIR/shared-dir"
ls -lR "$WORK_DIR/shared-dir"

# === 5. 特殊权限位：SUID ===
echo ""
echo ">>> [5] 特殊权限位：SUID（Set User ID）..."

echo "---- 查看 /usr/bin/passwd 的 SUID（典型示例）----"
ls -l /usr/bin/passwd
echo "    注意 s 替代了 x，表示 SUID"
echo "    普通用户执行 passwd 时，进程以 root 身份运行"

echo ""
echo "---- 给 script.sh 设置 SUID ----"
cp "$WORK_DIR/script.sh" "$WORK_DIR/suid-test.sh"
chmod 4755 "$WORK_DIR/suid-test.sh"      # 数字法：前面加 4
ls -l "$WORK_DIR/suid-test.sh"
echo "    注意 s 替代了所有者的 x"

echo ""
echo "---- 用符号法设置 SUID ----"
chmod u+s "$WORK_DIR/suid-test.sh"
ls -l "$WORK_DIR/suid-test.sh"

echo ""
echo "---- 去除 SUID ----"
chmod u-s "$WORK_DIR/suid-test.sh"
ls -l "$WORK_DIR/suid-test.sh"

# === 6. 特殊权限位：SGID ===
echo ""
echo ">>> [6] 特殊权限位：SGID（Set Group ID）..."

echo "---- 给 shared-dir 设置 SGID（目录下新建文件继承组）----"
chown deploy:developers "$WORK_DIR/shared-dir" 2>/dev/null || \
    chown deploy:deploy "$WORK_DIR/shared-dir"
chmod 2775 "$WORK_DIR/shared-dir"         # 数字法：前面加 2
ls -ld "$WORK_DIR/shared-dir"
echo "    注意 s 替代了组的 x"

echo ""
echo "---- 用符号法设置 SGID ----"
chmod g+s "$WORK_DIR/shared-dir"
ls -ld "$WORK_DIR/shared-dir"

echo ""
echo "---- 验证 SGID 效果：在 shared-dir 下创建文件，组应继承目录的组 ----"
current_group=$(stat -c '%G' "$WORK_DIR/shared-dir")
echo "    目录所属组：$current_group"
# 切换到 deploy 用户创建文件（如可切换）
su - deploy -c "touch $WORK_DIR/shared-dir/test-sgid.txt" 2>/dev/null || \
    touch "$WORK_DIR/shared-dir/test-sgid.txt"
echo "    新建文件的组：$(stat -c '%G' "$WORK_DIR/shared-dir/test-sgid.txt")"
echo "    （应与目录组相同：$current_group）"

# === 7. 特殊权限位：Sticky Bit ===
echo ""
echo ">>> [7] 特殊权限位：Sticky Bit..."

echo "---- 查看 /tmp 的 Sticky Bit（典型示例）----"
ls -ld /tmp
echo "    注意 t 替代了其他的 x"
echo "    /tmp 所有人可写，但文件只有所有者能删除"

echo ""
echo "---- 给 shared-dir 设置 Sticky Bit ----"
chmod 1777 "$WORK_DIR/shared-dir"         # 数字法：前面加 1
ls -ld "$WORK_DIR/shared-dir"
echo "    注意 t 替代了其他的 x"

echo ""
echo "---- 用符号法设置 Sticky Bit ----"
chmod +t "$WORK_DIR/shared-dir"
ls -ld "$WORK_DIR/shared-dir"

echo ""
echo "---- 去除 Sticky Bit ----"
chmod -t "$WORK_DIR/shared-dir"
ls -ld "$WORK_DIR/shared-dir"

# === 8. 特殊权限位总结 ===
echo ""
echo ">>> [8] 特殊权限位总结..."

echo "    权限      数字  符号     显示           作用"
echo "    ------    ----  ------   -----------    ----"
echo "    SUID      4000  u+s      rwsr-xr-x      文件以所有者身份执行"
echo "    SGID      2000  g+s      rwxr-sr-x      目录下文件继承组"
echo "    Sticky    1000  +t       rwxrwxrwt      目录下文件仅所有者可删"

echo ""
echo "    组合示例："
echo "    4755  = SUID + 755  → rwsr-xr-x  （如 passwd）"
echo "    2755  = SGID + 755  → rwxr-sr-x  （共享目录）"
echo "    1777  = Sticky+777  → rwxrwxrwt  （如 /tmp）"
echo "    6755  = SUID+SGID   → rwsr-sr-x  （很少用）"

# === 9. umask 默认权限 ===
echo ""
echo ">>> [9] umask 默认权限掩码..."

echo "---- 当前 umask：$(umask) ----"

echo ""
echo "---- umask 计算方式 ----"
echo "    目录默认权限 = 777 - umask"
echo "    文件默认权限 = 666 - umask（文件默认无执行）"
echo ""
echo "    umask 022: 目录=755(rwxr-xr-x), 文件=644(rw-r--r--)"
echo "    umask 077: 目录=700(rwx------), 文件=600(rw-------)"
echo "    umask 002: 目录=775(rwxrwxr-x), 文件=664(rw-rw-r--)"

echo ""
echo "---- 测试不同 umask 下创建文件的权限 ----"
echo "    umask 022 创建文件："
( umask 022; touch "$WORK_DIR/umask-022.txt"; ls -l "$WORK_DIR/umask-022.txt" )

echo "    umask 077 创建文件："
( umask 077; touch "$WORK_DIR/umask-077.txt"; ls -l "$WORK_DIR/umask-077.txt" )

echo "    umask 002 创建文件："
( umask 002; touch "$WORK_DIR/umask-002.txt"; ls -l "$WORK_DIR/umask-002.txt" )

echo "    umask 000 创建文件："
( umask 000; touch "$WORK_DIR/umask-000.txt"; ls -l "$WORK_DIR/umask-000.txt" )

echo ""
echo "---- 测试不同 umask 下创建目录的权限 ----"
echo "    umask 022 创建目录："
( umask 022; mkdir "$WORK_DIR/umask-dir-022"; ls -ld "$WORK_DIR/umask-dir-022" )

echo "    umask 077 创建目录："
( umask 077; mkdir "$WORK_DIR/umask-dir-077"; ls -ld "$WORK_DIR/umask-dir-077" )

# 恢复 umask
umask 022
echo ""
echo "    已恢复 umask 为 022"

# === 10. ACL 访问控制列表 ===
echo ""
echo ">>> [10] ACL 访问控制列表..."

# 检查 ACL 工具是否可用
if ! command -v setfacl >/dev/null 2>&1; then
    echo "    ACL 工具未安装，正在安装..."
    apt install -y acl 2>/dev/null || {
        echo "    无法安装 acl，跳过 ACL 部分"
        echo "    手动安装：sudo apt install acl"
    }
fi

if command -v setfacl >/dev/null 2>&1; then
    echo "---- 准备 ACL 测试文件 ----"
    cp "$WORK_DIR/file1.txt" "$WORK_DIR/acl-test.txt"
    chown deploy:deploy "$WORK_DIR/acl-test.txt"
    chmod 640 "$WORK_DIR/acl-test.txt"
    echo "    初始权限："
    ls -l "$WORK_DIR/acl-test.txt"

    echo ""
    echo "---- getfacl acl-test.txt（查看 ACL）----"
    getfacl "$WORK_DIR/acl-test.txt"

    echo ""
    echo "---- setfacl -m u:www-data:rw acl-test.txt（给 www-data 读写权限）----"
    setfacl -m u:www-data:rw "$WORK_DIR/acl-test.txt"
    ls -l "$WORK_DIR/acl-test.txt"
    echo "    注意权限后多了 + 号"
    getfacl "$WORK_DIR/acl-test.txt"

    echo ""
    echo "---- setfacl -m g:developers:rx acl-test.txt（给 developers 组读执行）----"
    getent group developers >/dev/null 2>&1 || groupadd developers
    setfacl -m g:developers:rx "$WORK_DIR/acl-test.txt"
    getfacl "$WORK_DIR/acl-test.txt"

    echo ""
    echo "---- setfacl -x u:www-data acl-test.txt（移除 www-data 的 ACL）----"
    setfacl -x u:www-data "$WORK_DIR/acl-test.txt"
    getfacl "$WORK_DIR/acl-test.txt"

    echo ""
    echo "---- setfacl -b acl-test.txt（清除所有 ACL）----"
    setfacl -b "$WORK_DIR/acl-test.txt"
    ls -l "$WORK_DIR/acl-test.txt"
    echo "    注意 + 号已消失"
    getfacl "$WORK_DIR/acl-test.txt"

    # ACL 递归设置
    echo ""
    echo "---- setfacl -R -m u:www-data:rx shared-dir/（递归设置 ACL）----"
    setfacl -R -m u:www-data:rx "$WORK_DIR/shared-dir"
    getfacl "$WORK_DIR/shared-dir"

    # ACL 默认权限（目录下新建文件继承）
    echo ""
    echo "---- setfacl -d -m u:www-data:rx shared-dir/（设置默认 ACL）----"
    setfacl -d -m u:www-data:rx "$WORK_DIR/shared-dir"
    getfacl "$WORK_DIR/shared-dir"
    echo "    之后在 shared-dir 下新建的文件会自动继承此 ACL"

    # 清理 ACL
    setfacl -bR "$WORK_DIR/shared-dir" 2>/dev/null
fi

# === 11. 实战：设置 /opt/ecommerce/ 项目权限 ===
echo ""
echo ">>> [11] 实战：设置 /opt/ecommerce/ 项目权限..."

PROJECT_ROOT="/opt/ecommerce"

if [ -d "$PROJECT_ROOT" ]; then
    echo "---- 项目目录存在，设置权限 ----"

    # 1. 设置所有者与组
    # 确保 deploy 用户与 developers 组存在
    id deploy >/dev/null 2>&1 || useradd -m -s /bin/bash deploy 2>/dev/null || true
    getent group developers >/dev/null 2>&1 || groupadd developers 2>/dev/null || true

    chown -R deploy:developers "$PROJECT_ROOT"
    echo "    所有者：deploy，组：developers"

    # 2. 目录设为 755，文件设为 644
    find "$PROJECT_ROOT" -type d -exec chmod 755 {} \;
    find "$PROJECT_ROOT" -type f -exec chmod 644 {} \;
    echo "    目录权限：755，文件权限：644"

    # 3. scripts 下的脚本设为可执行
    if [ -d "$PROJECT_ROOT/scripts" ]; then
        find "$PROJECT_ROOT/scripts" -name "*.sh" -exec chmod 755 {} \;
        echo "    scripts/*.sh 权限：755（可执行）"
    fi

    # 4. logs 目录设为组可写 + SGID
    if [ -d "$PROJECT_ROOT/logs" ]; then
        chmod 775 "$PROJECT_ROOT/logs"
        chmod g+s "$PROJECT_ROOT/logs"
        echo "    logs 权限：775 + SGID（组可写，新建文件继承组）"
    fi

    # 5. backup 目录设为 700（仅 deploy 可访问）
    if [ -d "$PROJECT_ROOT/backup" ]; then
        chmod 700 "$PROJECT_ROOT/backup"
        echo "    backup 权限：700（仅 deploy 可访问）"
    fi

    # 6. 用 ACL 给 www-data 读取配置的权限
    if [ -d "$PROJECT_ROOT/backend/config" ]; then
        setfacl -m u:www-data:r "$PROJECT_ROOT/backend/config" 2>/dev/null && \
            echo "    ACL: www-data 可读 backend/config"
    fi

    echo ""
    echo "---- 项目权限总览 ----"
    echo "    目录结构："
    tree -L 2 "$PROJECT_ROOT" 2>/dev/null || find "$PROJECT_ROOT" -maxdepth 2 | sort

    echo ""
    echo "    权限详情："
    ls -la "$PROJECT_ROOT/"

    echo ""
    echo "    logs 目录 ACL："
    getfacl "$PROJECT_ROOT/logs" 2>/dev/null || true

else
    echo "    /opt/ecommerce/ 不存在，跳过项目权限设置"
    echo "    请先执行 Day01 的 01-environment-setup.sh 创建项目目录"
fi

# === 12. 权限检查命令 ===
echo ""
echo ">>> [12] 权限检查命令汇总..."

echo "---- ls -l（查看权限）----"
ls -l "$WORK_DIR/"

echo ""
echo "---- stat -c '%A %a %U:%G %n' file（权限符号/数字/所有者/文件名）----"
stat -c '%A %a %U:%G %n' "$WORK_DIR/file1.txt"

echo ""
echo "---- find -perm（按权限查找）----"
echo "    权限为 644 的文件："
find "$WORK_DIR" -type f -perm 644

echo ""
echo "    权限包含 SUID 的文件（系统范围，前 5 个）："
find /usr/bin -type f -perm -4000 2>/dev/null | head -n 5

echo ""
echo "    权限包含 SGID 的文件（系统范围，前 5 个）："
find /usr/bin -type f -perm -2000 2>/dev/null | head -n 5

echo ""
echo "    权限包含 Sticky Bit 的目录："
find / -maxdepth 2 -type d -perm -1000 2>/dev/null | head -n 5

# 清理
echo ""
echo "================================================"
echo "  权限管理演示完成！"
echo "  工作目录保留在：$WORK_DIR"
echo "  清理：rm -rf $WORK_DIR"
echo "  下一步：执行 bash 03-ssh-key-auth.sh"
echo "================================================"
