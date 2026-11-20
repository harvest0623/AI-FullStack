#!/bin/bash
# ============================================================
# 文件名：03-lvm-management.sh
# 用途：演示 LVM 逻辑卷管理：PV/VG/LV 创建、扩容、文件系统扩容
# 适用：Ubuntu 22.04 LTS
# 场景：电商服务器为 MySQL 数据目录动态扩容
# 注意：本脚本以命令模板演示为主，实际执行需在练习环境
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day07 - 03 LVM 逻辑卷管理演示"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"
echo "提示：LVM 操作需 root 权限，请用具备 sudo 的用户执行"
echo ""

# ---------- 1. LVM 概念回顾 ----------

echo "[1] LVM 三层架构"
cat <<'EOF'
                  逻辑卷 LV（格式化挂载使用）
                       ↑
                  卷组 VG（PV 池子，可动态添加 PV）
                       ↑
              ┌────────┴────────┐
           物理卷 PV          物理卷 PV
           /dev/sdb1          /dev/sdc1

流程：磁盘/分区 → pvcreate → vgcreate → lvcreate → mkfs → mount
扩容：pvcreate 新盘 → vgextend → lvextend → resize2fs/xfs_growfs
EOF

echo -e "\n[2] 检查 LVM 工具是否已安装"
if command -v pvs >/dev/null 2>&1; then
    echo "✓ lvm2 已安装"
    echo "命令：lvm version | head -n 2"
    lvm version 2>/dev/null | head -n 2
else
    echo "✗ 未安装 lvm2，请执行：sudo apt install -y lvm2"
fi

# ---------- 2. 查看现有 LVM 状态 ----------

echo -e "\n[3] pvs —— 查看所有物理卷"
echo "命令：sudo pvs"
sudo pvs 2>/dev/null || echo "（无 PV 或需要 sudo）"

echo -e "\n[4] vgs —— 查看所有卷组"
echo "命令：sudo vgs"
sudo vgs 2>/dev/null || echo "（无 VG 或需要 sudo）"

echo -e "\n[5] lvs —— 查看所有逻辑卷"
echo "命令：sudo lvs"
sudo lvs 2>/dev/null || echo "（无 LV 或需要 sudo）"

echo -e "\n[6] pvdisplay —— 详细查看 PV"
echo "命令：sudo pvdisplay"
sudo pvdisplay 2>/dev/null | head -n 20 || echo "（无 PV 或需要 sudo）"

echo -e "\n[7] vgdisplay —— 详细查看 VG"
echo "命令：sudo vgdisplay"
sudo vgdisplay 2>/dev/null | head -n 20 || echo "（无 VG 或需要 sudo）"

echo -e "\n[8] lvdisplay —— 详细查看 LV"
echo "命令：sudo lvdisplay"
sudo lvdisplay 2>/dev/null | head -n 20 || echo "（无 LV 或需要 sudo）"

# ---------- 3. PV 操作 ----------

echo -e "\n[9] pvcreate —— 创建物理卷"
cat <<'EOF'
# 把分区创建为 PV（推荐方式）
sudo pvcreate /dev/sdb1
sudo pvcreate /dev/sdc1

# 也可以把整块磁盘作为 PV（不分区，更简洁）
sudo pvcreate /dev/sdb
sudo pvcreate /dev/sdc

# 批量创建
sudo pvcreate /dev/sdb1 /dev/sdc1 /dev/sdd1

# 创建后查看
sudo pvs
sudo pvdisplay
EOF

echo -e "\n[10] pvremove —— 删除物理卷"
cat <<'EOF'
# 删除前需先从 VG 移除（vgreduce）
sudo pvremove /dev/sdb1
EOF

# ---------- 4. VG 操作 ----------

echo -e "\n[11] vgcreate —— 创建卷组"
cat <<'EOF'
# 用一个或多个 PV 创建 VG
sudo vgcreate vg_data /dev/sdb1 /dev/sdc1

# 指定 PE 大小（默认 4MB，PE 越小空间利用率越高但元数据越大）
sudo vgcreate -s 16M vg_data /dev/sdb1

# 查看
sudo vgs
sudo vgdisplay
EOF

echo -e "\n[12] vgextend —— 扩展卷组（添加新 PV）"
cat <<'EOF'
# 当 VG 空间不足时，加新盘扩展
sudo pvcreate /dev/sdd1                    # 先创建 PV
sudo vgextend vg_data /dev/sdd1            # 加入 VG
sudo vgs                                   # 查看扩展后大小
EOF

echo -e "\n[13] vgreduce —— 缩减卷组（移除 PV）"
cat <<'EOF'
# 移除 PV 前需先把数据迁移到其他 PV
sudo pvmove /dev/sdc1                      # 迁移数据（可能很慢）
sudo vgreduce vg_data /dev/sdc1            # 从 VG 移除
sudo pvremove /dev/sdc1                    # 删除 PV
EOF

# ---------- 5. LV 操作 ----------

echo -e "\n[14] lvcreate —— 创建逻辑卷"
cat <<'EOF'
# 创建指定大小的 LV
sudo lvcreate -L 50G -n lv_mysql vg_data

# 创建占满 VG 剩余空间的 LV
sudo lvcreate -l 100%FREE -n lv_data vg_data

# -L 指定大小（如 50G/500M）
# -l 指定 LE 数（100%FREE = 用尽剩余）
# -n 指定 LV 名称

# 创建后 LV 设备路径有两种：
# /dev/vg_data/lv_mysql
# /dev/mapper/vg_data-lv_mysql   （两者等价）

# 查看
sudo lvs
sudo lvdisplay
EOF

echo -e "\n[15] lvextend —— 扩容逻辑卷（核心操作）"
cat <<'EOF'
# 加 10G
sudo lvextend -L +10G /dev/vg_data/lv_mysql

# 扩到指定大小（如 100G）
sudo lvextend -L 100G /dev/vg_data/lv_mysql

# 用尽 VG 剩余空间
sudo lvextend -l +100%FREE /dev/vg_data/lv_mysql

# 扩容同时同步文件系统（一条命令搞定 ext4）
sudo lvextend -L +10G -r /dev/vg_data/lv_mysql   # -r 自动 resize2fs

# xfs 的话 -r 也能自动调 xfs_growfs
sudo lvextend -L +10G -r /dev/vg_data/lv_mysql
EOF

echo -e "\n[16] 扩容后必须同步文件系统"
cat <<'EOF'
# 注意：lvextend 只扩大 LV，文件系统不知道空间变大了
# 必须执行以下命令让文件系统识别新空间

# ext4 文件系统扩容（指定设备名）
sudo resize2fs /dev/vg_data/lv_mysql

# xfs 文件系统扩容（必须指定挂载点，不是设备名！）
sudo xfs_growfs /var/lib/mysql

# 验证
df -h /var/lib/mysql
EOF

# ---------- 6. 完整流程实战 ----------

echo -e "\n[17] LVM 完整创建流程（生产部署模板）"
cat <<'EOF'
# === 场景：电商服务器初始化数据盘 ===
# 假设有两块新盘 /dev/sdb 和 /dev/sdc，分别 100GB

# 1. 创建 PV
sudo pvcreate /dev/sdb /dev/sdc

# 2. 创建 VG（PE 16MB）
sudo vgcreate -s 16M vg_data /dev/sdb /dev/sdc

# 3. 创建 LV
# 3.1 MySQL 数据卷 80GB
sudo lvcreate -L 80G -n lv_mysql vg_data
# 3.2 Redis 数据卷 20GB
sudo lvcreate -L 20G -n lv_redis vg_data
# 3.3 应用日志卷 50GB
sudo lvcreate -L 50G -n lv_logs vg_data
# 3.4 剩余空间给备份卷
sudo lvcreate -l 100%FREE -n lv_backup vg_data

# 4. 格式化（数据库用 xfs，日志用 ext4）
sudo mkfs.xfs /dev/vg_data/lv_mysql
sudo mkfs.xfs /dev/vg_data/lv_redis
sudo mkfs.ext4 /dev/vg_data/lv_logs
sudo mkfs.ext4 /dev/vg_data/lv_backup

# 5. 创建挂载点
sudo mkdir -p /var/lib/mysql /var/lib/redis /var/log/ecommerce /opt/ecommerce/backup

# 6. 临时挂载
sudo mount /dev/vg_data/lv_mysql /var/lib/mysql
sudo mount /dev/vg_data/lv_redis /var/lib/redis
sudo mount /dev/vg_data/lv_logs /var/log/ecommerce
sudo mount /dev/vg_data/lv_backup /opt/ecommerce/backup

# 7. 写入 fstab（用 UUID）
for lv in lv_mysql lv_redis lv_logs lv_backup; do
    UUID=$(sudo blkid -s UUID -o value /dev/vg_data/$lv)
    TYPE=$(sudo blkid -s TYPE -o value /dev/vg_data/$lv)
    MP=$(df --output=target /dev/vg_data/$lv | tail -n1)
    echo "UUID=$UUID $MP $TYPE defaults,noatime 0 2" | sudo tee -a /etc/fstab
done

# 8. 验证 fstab
sudo mount -a
df -h
EOF

echo -e "\n[18] 在线扩容实战（不停 MySQL）"
cat <<'EOF'
# === 场景：MySQL 数据目录满了，加新盘扩容 ===

# 1. 确认当前状态
df -h /var/lib/mysql                       # 查看使用率
sudo lvs                                   # 查看 LV 大小
sudo vgs                                   # 查看 VG 剩余空间

# 2. 假设 VG 没空间了，加新盘 /dev/sdd
sudo pvcreate /dev/sdd
sudo vgextend vg_data /dev/sdd
sudo vgs                                   # 确认 VG 空间增加

# 3. 扩容 LV（不停 MySQL）
sudo lvextend -L +50G /dev/vg_data/lv_mysql
# 或用 -r 一步到位
sudo lvextend -L +50G -r /dev/vg_data/lv_mysql

# 4. 同步文件系统（如果没用 -r）
sudo xfs_growfs /var/lib/mysql             # xfs 用挂载点
# 或
sudo resize2fs /dev/vg_data/lv_mysql       # ext4 用设备名

# 5. 验证
df -h /var/lib/mysql                       # 看到空间增加
sudo lvs                                   # LV 变大

# 整个过程 MySQL 完全无感知，无需停止服务！
EOF

# ---------- 7. LVM 快照 ----------

echo -e "\n[19] LVM 快照 —— 一致性备份"
cat <<'EOF'
# 创建快照（不影响原 LV 读写）
sudo lvcreate -L 10G -s -n lv_mysql_snapshot /dev/vg_data/lv_mysql

# 挂载快照（只读）
sudo mount -o ro /dev/vg_data/lv_mysql_snapshot /mnt/snapshot

# 从快照备份（一致性视图）
sudo tar -czf /backup/mysql-$(date +%Y%m%d).tar.gz -C /mnt/snapshot .

# 备份完成后删除快照（释放空间）
sudo umount /mnt/snapshot
sudo lvremove -f /dev/vg_data/lv_mysql_snapshot

# 注意：快照大小建议为原 LV 的 10%-20%（取决于备份期间的写入量）
# 快照满了会自动失效，需及时删除
EOF

# ---------- 8. 删除 LVM ----------

echo -e "\n[20] 删除 LVM（逆序操作）"
cat <<'EOF'
# 1. 卸载
sudo umount /var/lib/mysql

# 2. 删除 LV
sudo lvremove /dev/vg_data/lv_mysql

# 3. 删除 VG（VG 下所有 LV 都已删除后）
sudo vgremove vg_data

# 4. 删除 PV
sudo pvremove /dev/sdb /dev/sdc
EOF

echo -e "\n============================================================"
echo "  Day07 - 03 LVM 逻辑卷管理演示 完成"
echo "============================================================"
