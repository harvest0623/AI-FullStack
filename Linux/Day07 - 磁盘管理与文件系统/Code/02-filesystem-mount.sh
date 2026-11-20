#!/bin/bash
# ============================================================
# 文件名：02-filesystem-mount.sh
# 用途：演示文件系统挂载：mount/umount、blkid 获取 UUID、
#       /etc/fstab 配置、mount -a 验证
# 适用：Ubuntu 22.04 LTS
# 场景：电商服务器挂载数据盘到 /opt/ecommerce/data
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day07 - 02 文件系统挂载演示"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"

# ---------- 1. 查看当前挂载状态 ----------

echo -e "\n[1] mount —— 查看所有挂载"
echo "命令：mount | head -n 15"
mount | head -n 15

echo -e "\n[2] findmnt —— 更友好的挂载树形视图"
echo "命令：findmnt | head -n 20"
findmnt | head -n 20

echo -e "\n[3] findmnt 查看某挂载点"
echo "命令：findmnt /"
findmnt /

# ---------- 2. blkid 获取 UUID ----------

echo -e "\n[4] blkid —— 获取所有分区的 UUID 与文件系统类型"
echo "命令：sudo blkid"
sudo blkid 2>/dev/null || echo "（需要 sudo 权限）"

echo -e "\n[5] blkid 查询指定分区"
SECOND_DISK=$(lsblk -d -n -o NAME | grep -v -E '^(sda|vda|nvme0n1|loop)' | head -n1)
if [ -n "$SECOND_DISK" ]; then
    echo "命令：sudo blkid /dev/${SECOND_DISK}1"
    sudo blkid "/dev/${SECOND_DISK}1" 2>/dev/null
fi

echo -e "\n[6] 仅获取 UUID 字段（脚本中常用）"
echo "命令：sudo blkid -s UUID -o value /dev/sda1"
sudo blkid -s UUID -o value /dev/sda1 2>/dev/null

echo -e "\n[7] lsblk -f —— 同样可显示 UUID"
echo "命令：lsblk -f"
lsblk -f

# ---------- 3. mount 挂载 ----------

echo -e "\n[8] mount —— 临时挂载（重启失效）"
cat <<'EOF'
# 基础挂载
sudo mount /dev/sdb1 /mnt/data

# 指定文件系统类型
sudo mount -t ext4 /dev/sdb1 /mnt/data
sudo mount -t xfs /dev/sdb1 /mnt/data

# 挂载选项
sudo mount -o rw,noatime /dev/sdb1 /mnt/data
# rw 读写（默认）
# ro 只读
# noatime 不更新访问时间（提升性能，推荐数据库）
# nodiratime 不更新目录访问时间
# defaults = rw,suid,dev,exec,auto,nouser,async

# 挂载 ISO 镜像
sudo mount -o loop ubuntu-22.04.iso /mnt/iso

# 挂载 NFS 共享
sudo mount -t nfs 192.168.1.200:/share /mnt/nfs

# 重新挂载为读写（解除只读）
sudo mount -o remount,rw /mnt/data
EOF

# ---------- 4. 实际演示：在虚拟磁盘上完整挂载流程 ----------

echo -e "\n[9] 在虚拟磁盘上演示完整挂载流程"
cat <<'EOF'
# 1. 创建虚拟磁盘
sudo dd if=/dev/zero of=/tmp/test-disk.img bs=1M count=200
sudo losetup -fP /tmp/test-disk.img
LOOP=$(sudo losetup -l | grep test-disk.img | awk '{print $1}')

# 2. 分区格式化
sudo parted -s "$LOOP" mklabel gpt
sudo parted -s "$LOOP" mkpart primary ext4 0% 100%
sudo mkfs.ext4 -L testdata "${LOOP}p1"

# 3. 挂载
sudo mkdir -p /mnt/testdata
sudo mount "${LOOP}p1" /mnt/testdata

# 4. 验证
df -h /mnt/testdata
sudo touch /mnt/testdata/hello.txt
ls -l /mnt/testdata/

# 5. 卸载清理
sudo umount /mnt/testdata
sudo losetup -d "$LOOP"
rm /tmp/test-disk.img
EOF

# ---------- 5. umount 卸载 ----------

echo -e "\n[10] umount —— 卸载文件系统"
cat <<'EOF'
# 卸载（用挂载点或设备名都可以）
sudo umount /mnt/data
sudo umount /dev/sdb1

# 设备 busy 时报错 "target is busy"
# 解决办法：
# 1. 找出占用进程
sudo lsof /mnt/data           # 查看哪个进程在使用
sudo fuser -m /mnt/data       # 另一个工具

# 2. 杀掉占用进程后卸载
sudo fuser -km /mnt/data      # 直接杀掉占用进程
sudo umount /mnt/data

# 3. 懒卸载（立即解挂，但等占用进程关闭后才真正释放）
sudo umount -l /mnt/data
EOF

# ---------- 6. /etc/fstab 自动挂载 ----------

echo -e "\n[11] /etc/fstab —— 开机自动挂载配置"
echo "命令：cat /etc/fstab"
cat /etc/fstab

echo -e "\n[12] /etc/fstab 字段说明"
cat <<'EOF'
设备                   挂载点            文件系统  挂载选项              dump  pass
UUID=xxx-yyy-zzz       /mnt/data         ext4      defaults,noatime      0     2
UUID=aaa-bbb-ccc       /var/lib/mysql    xfs       defaults,noatime      0     2
/swapfile              none              swap      sw                    0     0
tmpfs                  /tmp              tmpfs     defaults,size=2G      0     0

字段说明：
1. 设备      设备名 / UUID / LABEL（推荐 UUID，设备名会变）
2. 挂载点    挂载目录（swap 用 none）
3. 文件系统  ext4 / xfs / swap / tmpfs / nfs
4. 挂载选项  defaults（默认）/ rw,noatime / sw（swap）
5. dump      是否用 dump 备份（0=否，1=是，现代系统一般 0）
6. pass      开机 fsck 顺序（0=跳过，1=根分区，2=其他）
EOF

echo -e "\n[13] 写入 fstab 的标准流程"
cat <<'EOF'
# 1. 获取分区的 UUID 和文件系统类型
sudo blkid /dev/sdb1
# 输出示例：/dev/sdb1: UUID="abc-123" TYPE="ext4"

# 2. 创建挂载点
sudo mkdir -p /mnt/data

# 3. 临时挂载测试
sudo mount /dev/sdb1 /mnt/data

# 4. 写入 fstab（用 UUID，避免设备名变化）
echo "UUID=$(sudo blkid -s UUID -o value /dev/sdb1) /mnt/data ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab

# 5. 测试 fstab 配置（重要！错误配置会导致无法开机）
sudo umount /mnt/data
sudo mount -a          # 重新挂载 fstab 中所有项
df -h /mnt/data        # 验证挂载成功

# 6. 如出错，立即修正 fstab
sudo vim /etc/fstab    # 修复后再次 mount -a 测试
EOF

# ---------- 7. mount -a 测试 ----------

echo -e "\n[14] mount -a —— 测试 fstab 配置（重要）"
echo "命令：sudo mount -a"
sudo mount -a 2>&1 || echo "（fstab 有错误，请检查！开机可能失败）"
echo ""
echo "重要：每次修改 /etc/fstab 后必须执行 mount -a 测试"
echo "      错误的 fstab 会导致系统无法开机"

echo -e "\n[15] 挂载选项性能对比"
cat <<'EOF'
选项          性能影响              推荐场景
─────────    ──────────────────   ─────────────
defaults     标准                  通用
noatime      不更新访问时间 +5%IO  数据库、日志
nodiratime   不更新目录访问时间    略好于 atime
relatime     仅修改时更新 atime    默认折中（推荐）
data=writeback  写回（最快最不安全） 不推荐生产
data=ordered    顺序（默认平衡）   ext4 默认
data=journal    日志（最安全最慢）  重要数据
EOF

# ---------- 8. 挂载 NFS / 网络文件系统 ----------

echo -e "\n[16] 挂载 NFS 共享"
cat <<'EOF'
# 安装 NFS 客户端
sudo apt install -y nfs-common

# 临时挂载
sudo mount -t nfs 192.168.1.200:/share /mnt/nfs

# 挂载选项（推荐）
sudo mount -t nfs -o rw,hard,tcp,timeo=600,retrans=2 192.168.1.200:/share /mnt/nfs

# 写入 fstab
echo "192.168.1.200:/share /mnt/nfs nfs defaults,hard,tcp,timeo=600 0 0" | sudo tee -a /etc/fstab
EOF

# ---------- 9. 挂载 tmpfs 内存盘 ----------

echo -e "\n[17] tmpfs —— 内存文件系统（高速缓存场景）"
cat <<'EOF'
# 临时挂载 2GB tmpfs
sudo mount -t tmpfs -o size=2G tmpfs /mnt/cache

# 持久化到 fstab
echo "tmpfs /mnt/cache tmpfs defaults,size=2G,mode=1777 0 0" | sudo tee -a /etc/fstab

# 应用场景：
# 1. Redis 临时数据
# 2. Nginx 代理缓存
# 3. 编译临时目录
# 4. 高速会话存储

# 注意：tmpfs 数据在重启后丢失！不要存重要数据
EOF

echo -e "\n============================================================"
echo "  Day07 - 02 文件系统挂载演示 完成"
echo "============================================================"
