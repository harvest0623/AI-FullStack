#!/bin/bash
# ============================================================
# 文件名：01-disk-partition.sh
# 用途：演示磁盘分区：lsblk 查看、fdisk/parted 分区操作、mkfs 格式化
# 适用：Ubuntu 22.04 LTS
# 场景：电商服务器新增数据盘 /dev/sdb 用于 MySQL 数据
# 注意：分区操作会破坏数据，请在无重要数据的磁盘上练习！
#       推荐用虚拟磁盘（losetup）或额外挂载的云盘做实验
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day07 - 01 磁盘分区演示"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"
echo "⚠ 警告：分区操作会破坏数据，请在练习盘上执行！"
echo ""

# ---------- 1. lsblk 查看块设备 ----------

echo "[1] lsblk —— 块设备树形视图"
echo "命令：lsblk"
lsblk
echo ""
echo "字段说明："
echo "  NAME=设备名  SIZE=大小  TYPE=类型(disk/part/lvm/rom)"
echo "  MOUNTPOINT=挂载点  RM=可移动  RO=只读"

echo -e "\n[2] lsblk -f —— 显示文件系统与 UUID"
echo "命令：lsblk -f"
lsblk -f
echo "说明：UUID 是文件系统唯一标识，fstab 中应使用 UUID 而非设备名"

echo -e "\n[3] lsblk -o —— 自定义输出字段"
echo "命令：lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL"
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL

# ---------- 2. fdisk 查看分区 ----------

echo -e "\n[4] fdisk -l —— 查看所有磁盘分区信息"
echo "命令：sudo fdisk -l"
sudo fdisk -l 2>/dev/null | head -n 30 || echo "（需要 sudo 权限）"

echo -e "\n[5] fdisk -l <磁盘> —— 查看指定磁盘"
# 自动选择一块非系统盘演示
SECOND_DISK=$(lsblk -d -n -o NAME | grep -v -E '^(sda|vda|nvme0n1|loop)' | head -n1)
if [ -n "$SECOND_DISK" ]; then
    echo "命令：sudo fdisk -l /dev/$SECOND_DISK"
    sudo fdisk -l "/dev/$SECOND_DISK" 2>/dev/null || echo "（需要 sudo 权限）"
else
    echo "未检测到第二块磁盘，可在虚拟机中添加新磁盘用于练习"
fi

# ---------- 3. parted 查看（GPT 推荐） ----------

echo -e "\n[6] parted -l —— 查看所有磁盘与分区表类型"
echo "命令：sudo parted -l"
sudo parted -l 2>/dev/null | head -n 30 || echo "（需要 sudo 权限）"

echo -e "\n[7] parted print —— 查看指定磁盘"
if [ -n "$SECOND_DISK" ]; then
    echo "命令：sudo parted /dev/$SECOND_DISK print"
    sudo parted "/dev/$SECOND_DISK" print 2>/dev/null || echo "（需要 sudo 权限）"
fi

# ---------- 4. fdisk 交互式分区（演示命令模板） ----------

echo -e "\n[8] fdisk 交互式分区（MBR，演示命令模板）"
cat <<'EOF'
sudo fdisk /dev/sdb
# 进入交互后按键说明：
# m        显示帮助
# p        打印当前分区表
# n        新建分区
#   p      选择主分区（primary）
#   1      分区号 1
#   <回车> 起始扇区默认
#   +50G   大小 50G（或回车用全部）
# t        修改分区类型
#   8e     设置为 LVM 类型
#   82     设置为 swap 类型
# d        删除分区
# w        保存并退出
# q        不保存退出
EOF

# ---------- 5. parted 一行命令创建 GPT 分区（生产脚本常用） ----------

echo -e "\n[9] parted 一行命令创建 GPT 分区"
cat <<EOF
# 假设新磁盘为 /dev/sdb
# 1. 创建 GPT 分区表
sudo parted -s /dev/sdb mklabel gpt

# 2. 创建一个占满整盘的分区
sudo parted -s /dev/sdb mkpart primary ext4 0% 100%

# 3. 创建多个分区（每个 50%）
sudo parted -s /dev/sdb mkpart primary 0% 50%
sudo parted -s /dev/sdb mkpart primary 50% 100%

# 4. 设置分区为 LVM 类型
sudo parted -s /dev/sdb set 1 lvm on

# 5. 验证
sudo parted /dev/sdb print
EOF

echo -e "\n[10] parted 交互式分区（演示命令）"
cat <<'EOF'
sudo parted /dev/sdb
# (parted) mklabel gpt
# (parted) mkpart data ext4 0% 100%
# (parted) print
# (parted) quit
EOF

# ---------- 6. 在虚拟磁盘上演示完整流程 ----------

echo -e "\n[11] 在虚拟磁盘上安全演示分区流程（推荐练习方式）"
cat <<'EOF'
# 1. 创建一个 1GB 的虚拟磁盘文件
sudo dd if=/dev/zero of=/tmp/virtual-disk.img bs=1M count=1024

# 2. 关联到 loop 设备
sudo losetup -fP /tmp/virtual-disk.img
LOOP_DEV=$(sudo losetup -l | grep virtual-disk.img | awk '{print $1}')
echo "loop 设备：$LOOP_DEV"

# 3. 用 parted 创建 GPT 分区
sudo parted -s "$LOOP_DEV" mklabel gpt
sudo parted -s "$LOOP_DEV" mkpart primary ext4 0% 100%

# 4. 格式化
sudo mkfs.ext4 "${LOOP_DEV}p1"

# 5. 挂载测试
sudo mkdir -p /mnt/vdisk
sudo mount "${LOOP_DEV}p1" /mnt/vdisk
df -h /mnt/vdisk

# 6. 清理
sudo umount /mnt/vdisk
sudo losetup -d "$LOOP_DEV"
rm /tmp/virtual-disk.img
EOF

# ---------- 7. mkfs 格式化 ----------

echo -e "\n[12] mkfs —— 格式化为 ext4"
cat <<'EOF'
# 假设新分区为 /dev/sdb1
sudo mkfs.ext4 /dev/sdb1                  # 基础格式化
sudo mkfs.ext4 -L ecommerce_data /dev/sdb1  # -L 设置卷标
sudo mkfs.ext4 -N 1000000 /dev/sdb1        # -N 指定 inode 数（小文件多时调大）

# 查看格式化结果
sudo blkid /dev/sdb1
sudo dumpe2fs /dev/sdb1 | head -n 20       # 查看 ext4 详细信息
EOF

echo -e "\n[13] mkfs —— 格式化为 xfs"
cat <<'EOF'
sudo mkfs.xfs /dev/sdb1
sudo mkfs.xfs -L ecommerce_data /dev/sdb1
sudo mkfs.xfs -f /dev/sdb1                 # -f 强制（覆盖已有文件系统）

# 查看 xfs 信息
sudo xfs_info /dev/sdb1
EOF

echo -e "\n[14] mkfs —— 其他文件系统"
cat <<'EOF'
# btrfs（支持快照、压缩、子卷）
sudo mkfs.btrfs /dev/sdb1
sudo mkfs.btrfs -L ecommerce_data /dev/sdb1

# FAT32（U 盘、EFI 分区）
sudo mkfs.fat -F 32 /dev/sdb1

# exfat（跨平台大文件）
sudo mkfs.exfat /dev/sdb1
EOF

echo -e "\n[15] 文件系统选择建议"
cat <<'EOF'
场景                    推荐文件系统
─────────────────────  ─────────────
Ubuntu 通用服务器        ext4（默认，稳定）
CentOS/RHEL 服务器       xfs（默认，高并发强）
数据库（MySQL/PG）       xfs（大文件高并发）
日志大量小文件           ext4（小文件性能更好）
需要快照/压缩            btrfs
数据完整性优先            zfs
U 盘 / EFI 分区          fat32
EOF

# ---------- 8. 安全删除分区 ----------

echo -e "\n[16] 删除分区"
cat <<'EOF'
# fdisk 删除
sudo fdisk /dev/sdb
# d        选择删除
# 1        分区号
# w        保存

# parted 删除
sudo parted -s /dev/sdb rm 1
EOF

echo -e "\n============================================================"
echo "  Day07 - 01 磁盘分区演示 完成"
echo "============================================================"
