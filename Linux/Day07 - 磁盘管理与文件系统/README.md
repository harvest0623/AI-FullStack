# Day07 - 磁盘管理与文件系统

磁盘是服务器数据的载体，磁盘管理是运维工程师的核心技能。电商项目的图片存储、MySQL 数据、Redis 持久化文件、应用日志、用户上传文件都持续增长，磁盘空间不足会导致写入失败、数据库锁表甚至服务崩溃；而生产环境又不能停机扩展，因此 LVM 逻辑卷管理的动态扩容能力成为线上运维的必备技能。本章将围绕电商服务器 `192.168.1.100` 系统讲解磁盘查看、分区操作、文件系统格式化、挂载与 `/etc/fstab` 自动挂载、LVM 逻辑卷管理、Swap 交换分区、inode 与文件描述符等核心知识，并演示"数据盘满了如何在线扩容"这一典型生产场景。

---

## 学习目标

- 理解硬盘类型、分区表（MBR vs GPT）、文件系统（ext4/xfs/btrfs）的差异
- 使用 `lsblk`、`fdisk -l`、`df -h`、`du -sh` 查看磁盘和文件系统状态
- 掌握 `fdisk` 与 `parted` 分区操作
- 使用 `mkfs` 格式化 ext4/xfs 文件系统
- 使用 `mount`/`umount` 挂载卸载，配置 `/etc/fstab` 实现开机自动挂载
- 理解 LVM 概念（PV/VG/LV），完成创建、扩容全流程
- 配置 Swap 交换分区（分区型与文件型）
- 理解 inode 与文件描述符，能定位 inode 耗尽与 fd 限制问题

---

## 理论知识讲解

### 一、磁盘基础知识

#### 1.1 硬盘类型

| 类型 | 全称 | 特点 | 适用场景 |
|------|------|------|---------|
| HDD | 机械硬盘 | 容量大、便宜、随机 IO 慢 | 冷数据、备份 |
| SSD | 固态硬盘 | 速度快、随机 IO 强、价格高 | 数据库、热数据 |
| NVMe | 非易失性内存表达 | 极快（PCIe 通道）、价格高 | 高性能数据库、AI 训练 |

#### 1.2 分区表：MBR vs GPT

| 特性 | MBR (Master Boot Record) | GPT (GUID Partition Table) |
|------|--------------------------|----------------------------|
| 最大磁盘 | 2TB | 18EB（理论） |
| 最大分区数 | 4 主分区（或 3 主 + 1 扩展） | 128 个 |
| 分区标识 | 4 字节签名 | 16 字节 GUID |
| 工具 | fdisk | gdisk / parted |
| 引导方式 | BIOS | UEFI |
| 推荐 | 已过时 | 现代标准 |

#### 1.3 文件系统对比

| 文件系统 | 最大文件 | 最大分区 | 特性 | 适用 |
|---------|---------|---------|------|------|
| ext4 | 16TB | 1EB | 稳定、生态成熟、支持日志 | Ubuntu/Debian 默认 |
| xfs | 8EB | 8EB | 高并发 IO、大文件强、不能缩容 | CentOS/RHEL 默认 |
| btrfs | 16EB | 16EB | 快照、压缩、子卷、校验 | 高级特性需求 |
| zfs | 16EB | 16EB | 数据完整性、快照、RAID | 数据库存储 |
| fat32 | 4GB | 2TB | 兼容性最好 | U 盘、EFI 分区 |

> 生产建议：数据库服务器选 xfs（高并发大文件强）；通用服务器选 ext4（稳定可靠）；需要快照的选 btrfs。

### 二、磁盘查看命令

#### 2.1 lsblk —— 块设备树形视图

```bash
lsblk                          # 树形显示所有块设备
lsblk -f                       # 显示文件系统信息（UUID/TYPE）
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL
```

输出字段说明：

| 字段 | 含义 |
|------|------|
| NAME | 设备名（sda/sda1） |
| MAJ:MIN | 主次设备号 |
| RM | 是否可移动（0 否/1 是） |
| SIZE | 设备大小 |
| RO | 是否只读 |
| TYPE | 类型（disk/part/rom/lvm） |
| MOUNTPOINT | 挂载点 |

#### 2.2 fdisk / parted

```bash
# 查看所有磁盘的分区信息
sudo fdisk -l
sudo fdisk -l /dev/sda

# parted 既能查看也能管理 GPT
sudo parted -l
sudo parted /dev/sdb print
```

#### 2.3 df —— 文件系统使用情况

```bash
df -h                          # 人类可读（GB/MB）
df -h /opt/ecommerce           # 查看某目录所在分区使用情况
df -i                          # 查看 inode 使用情况
df -T                          # 显示文件系统类型
df -x tmpfs                    # 排除 tmpfs
```

#### 2.4 du —— 目录占用空间

```bash
du -sh /opt/ecommerce          # 显示目录总大小
du -h --max-depth=1 /opt/ecommerce    # 一级子目录大小
du -h /var/log | sort -rh | head -n 10  # 找出最大的 10 个目录
du -sh * | sort -rh            # 当前目录下文件/目录按大小排序
du -ah /opt | sort -rh | head -n 10  # 找出最大的 10 个文件
```

#### 2.5 ncdu —— 交互式磁盘分析

```bash
sudo apt install -y ncdu
ncdu /                         # 扫描整个文件系统
ncdu /opt/ecommerce            # 扫描指定目录
# 操作：方向键导航，d 删除，q 退出
```

### 三、分区操作

#### 3.1 fdisk 交互式分区（MBR）

```bash
sudo fdisk /dev/sdb
# 进入交互后：
# m 显示帮助
# p 打印分区表
# n 新建分区（p 主分区/e 扩展分区）
# d 删除分区
# t 修改分区类型（82 = swap, 8e = LVM）
# w 保存并退出
# q 不保存退出
```

#### 3.2 parted 命令（GPT 推荐）

```bash
# 一行命令创建 GPT 分区（生产脚本常用）
sudo parted -s /dev/sdb mklabel gpt
sudo parted -s /dev/sdb mkpart primary ext4 0% 100%

# 创建多个分区
sudo parted -s /dev/sdb mkpart primary 0% 50%
sudo parted -s /dev/sdb mkpart primary 50% 100%

# 交互式
sudo parted /dev/sdb
(parted) mklabel gpt
(parted) mkpart data ext4 0% 100%
(parted) print
(parted) quit
```

> parted 的 mkpart 后第一字段虽名为 `primary`，但在 GPT 下只是个标签名，无主/扩展分区概念。

### 四、文件系统

#### 4.1 mkfs 格式化

```bash
# 格式化为 ext4
sudo mkfs.ext4 /dev/sdb1
sudo mkfs.ext4 -L ecommerce_data /dev/sdb1     # -L 设置卷标

# 格式化为 xfs
sudo mkfs.xfs /dev/sdb1
sudo mkfs.xfs -L ecommerce_data /dev/sdb1

# 格式化为 btrfs
sudo mkfs.btrfs /dev/sdb1

# 格式化为 FAT32
sudo mkfs.fat -F 32 /dev/sdb1
```

### 五、挂载与卸载

#### 5.1 mount / umount

```bash
# 临时挂载（重启失效）
sudo mount /dev/sdb1 /mnt/data

# 指定文件系统类型
sudo mount -t ext4 /dev/sdb1 /mnt/data

# 挂载选项
sudo mount -o rw,noatime /dev/sdb1 /mnt/data

# 查看所有挂载
mount | grep /dev/sdb1
findmnt                          # 更友好的挂载查看

# 卸载
sudo umount /mnt/data
sudo umount /dev/sdb1

# 强制懒卸载（设备 busy 时）
sudo umount -l /mnt/data
```

#### 5.2 /etc/fstab 自动挂载

`/etc/fstab` 是开机自动挂载的配置文件，格式为 6 个字段：

| 字段 | 含义 | 示例 |
|------|------|------|
| 设备 | 设备名、UUID 或 LABEL | `UUID=xxx` / `/dev/sdb1` |
| 挂载点 | 挂载目录 | `/mnt/data` |
| 文件系统 | 类型 | `ext4` / `xfs` / `swap` |
| 挂载选项 | 选项 | `defaults` / `rw,noatime` |
| dump | 是否备份（0 否/1 是） | `0` |
| pass | 启动时 fsck 顺序（0 跳过/1 根分区/2 其他） | `0` |

```bash
# /etc/fstab 示例
UUID=xxx-yyy-zzz  /mnt/data       ext4    defaults,noatime        0 2
UUID=aaa-bbb-ccc  /var/lib/mysql  xfs     defaults,noatime        0 2
none              /swapfile       swap    sw                      0 0
```

```bash
# 获取分区 UUID
sudo blkid
sudo blkid /dev/sdb1

# 测试 fstab 配置是否正确（重要！写错会导致开机失败）
sudo mount -a

# 重新挂载所有（应用 fstab 变更）
sudo mount -a
```

> **生产建议**：fstab 中一律使用 UUID，不用设备名。因为设备名（sda/sdb）在不同启动顺序下可能变化，UUID 是文件系统唯一标识。

### 六、LVM 逻辑卷管理（重点）

#### 6.1 LVM 概念

LVM（Logical Volume Manager）在物理磁盘之上引入抽象层，将多个物理分区组合成虚拟大磁盘，再从中切出逻辑卷供挂载使用。最大优势是**动态扩容不中断服务**。

```
┌─────────────────────────────────────────────────────┐
│  逻辑卷 LV：/dev/vg_ecommerce/lv_data  (可动态扩容) │
├─────────────────────────────────────────────────────┤
│  卷组 VG：vg_ecommerce  (PV 池子，可动态添加 PV)    │
├──────────────┬──────────────┬───────────────────────┤
│ 物理卷 PV    │ 物理卷 PV    │ 物理卷 PV             │
│ /dev/sdb1    │ /dev/sdc1    │ /dev/sdd1             │
├──────────────┼──────────────┼───────────────────────┤
│ 物理磁盘 sdb │ 物理磁盘 sdc │ 物理磁盘 sdd          │
└──────────────┴──────────────┴───────────────────────┘
```

| 概念 | 全称 | 说明 |
|------|------|------|
| PV | Physical Volume | 物理卷，由磁盘/分区初始化而来 |
| VG | Volume Group | 卷组，由一个或多个 PV 组成 |
| LV | Logical Volume | 逻辑卷，从 VG 中切出，可格式化挂载 |
| PE | Physical Extent | PV 的最小分配单元（默认 4MB） |
| LE | Logical Extent | LV 的最小单元，与 PE 一一对应 |

#### 6.2 PV 操作

```bash
# 创建 PV
sudo pvcreate /dev/sdb1 /dev/sdc1
sudo pvcreate /dev/sdb              # 整盘作为 PV 也可以

# 查看
sudo pvdisplay                      # 详细
sudo pvs                            # 简洁
sudo pvscan                         # 扫描所有 PV

# 删除 PV（需先从 VG 移除）
sudo pvremove /dev/sdb1
```

#### 6.3 VG 操作

```bash
# 创建 VG
sudo vgcreate vg_ecommerce /dev/sdb1 /dev/sdc1

# 指定 PE 大小（默认 4MB）
sudo vgcreate -s 16M vg_ecommerce /dev/sdb1

# 查看
sudo vgdisplay
sudo vgs

# 扩展 VG（添加新 PV）
sudo vgextend vg_ecommerce /dev/sdd1

# 缩减 VG（移除 PV，需先用 pvmove 迁移数据）
sudo pvmove /dev/sdc1
sudo vgreduce vg_ecommerce /dev/sdc1

# 删除 VG
sudo vgremove vg_ecommerce
```

#### 6.4 LV 操作

```bash
# 创建 LV
sudo lvcreate -L 50G -n lv_data vg_ecommerce       # 指定大小
sudo lvcreate -l 100%FREE -n lv_data vg_ecommerce  # 用尽剩余空间
sudo lvcreate -L 50G -n lv_data vg_ecommerce -C y  # -C y 连续分配

# LV 设备路径
# /dev/vg_ecommerce/lv_data 或 /dev/mapper/vg_ecommerce-lv_data

# 查看
sudo lvdisplay
sudo lvs

# 扩容 LV
sudo lvextend -L +10G /dev/vg_ecommerce/lv_data        # 加 10G
sudo lvextend -L 100G /dev/vg_ecommerce/lv_data        # 扩到 100G
sudo lvextend -l +100%FREE /dev/vg_ecommerce/lv_data   # 用尽剩余

# 扩容后必须同步文件系统（否则 df -h 看不到变化）
sudo resize2fs /dev/vg_ecommerce/lv_data              # ext4
sudo xfs_growfs /mnt/data                             # xfs（需指定挂载点）
```

#### 6.5 LVM 完整流程

```bash
# 1. 准备分区并标记为 LVM 类型（fdisk 中 t -> 8e）
# 或直接用整盘
sudo pvcreate /dev/sdb /dev/sdc

# 2. 创建 VG
sudo vgcreate vg_data /dev/sdb /dev/sdc

# 3. 创建 LV
sudo lvcreate -L 100G -n lv_mysql vg_data
sudo lvcreate -L 50G -n lv_redis vg_data

# 4. 格式化
sudo mkfs.xfs /dev/vg_data/lv_mysql
sudo mkfs.ext4 /dev/vg_data/lv_redis

# 5. 挂载
sudo mkdir -p /var/lib/mysql /var/lib/redis
sudo mount /dev/vg_data/lv_mysql /var/lib/mysql
sudo mount /dev/vg_data/lv_redis /var/lib/redis

# 6. 写入 fstab（用 UUID）
echo "UUID=$(sudo blkid -s UUID -o value /dev/vg_data/lv_mysql) /var/lib/mysql xfs defaults,noatime 0 2" | sudo tee -a /etc/fstab

# 7. 后续扩容（不停服务）
sudo lvextend -L +50G /dev/vg_data/lv_mysql
sudo xfs_growfs /var/lib/mysql
```

#### 6.6 LVM 优势

- **动态扩容**：不停服务在线扩容
- **跨磁盘**：多个小磁盘组合成大卷
- **快照**：`lvcreate -s` 创建快照，用于备份
- **条带化**：跨多 PV 提升性能
- **镜像**：跨多 PV 提升可靠性

### 七、Swap 交换分区

#### 7.1 分区型 Swap

```bash
# 创建 swap 分区（fdisk 中 t -> 82）
sudo mkswap /dev/sdb2

# 启用
sudo swapon /dev/sdb2

# 关闭
sudo swapoff /dev/sdb2

# 查看交换空间
free -h
swapon --show
cat /proc/swaps
```

#### 7.2 文件型 Swap（无需分区，更灵活）

```bash
# 创建 2GB swap 文件
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 开机自动挂载
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 关闭
sudo swapoff /swapfile
sudo rm /swapfile
```

#### 7.3 swappiness 参数

```bash
# 查看当前值（0-100，越大越倾向于使用 swap）
cat /proc/sys/vm/swappiness
sysctl vm.swappiness

# 临时修改
sudo sysctl vm.swappiness=10

# 永久修改
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

| 值 | 适用场景 |
|----|---------|
| 0 | 尽量不用 swap（数据库服务器推荐） |
| 10 | 通用服务器 |
| 60 | 默认值 |
| 100 | 积极使用 swap（内存紧张的桌面） |

### 八、文件系统检查与 inode

#### 8.1 fsck

```bash
# 检查文件系统（必须先卸载！）
sudo umount /dev/sdb1
sudo fsck /dev/sdb1
sudo fsck -y /dev/sdb1            # -y 自动回答 yes
sudo fsck.ext4 -f /dev/sdb1       # 强制检查 ext4
sudo fsck.xfs /dev/sdb1           # xfs 一般只在严重故障时检查

# 检查根分区（需要从 LiveUSB 启动或单用户模式）
sudo fsck /dev/sda1
```

#### 8.2 inode 概念

inode（索引节点）是文件元数据结构，存储文件的权限、属主、大小、数据块位置等信息，但不存储文件名。文件名存储在目录项中，通过 inode 号关联。

```bash
# 查看文件 inode 号
ls -i file.txt
stat file.txt

# 查看 inode 使用情况
df -i

# 查看分区 inode 总数
sudo tune2fs -l /dev/sda1 | grep "Inode count"
```

**inode 耗尽问题**：

```bash
# 即使 df -h 显示磁盘还有空间，但创建文件报错 "No space left on device"
# 检查 df -i，可能是 inode 用尽（大量小文件导致）

# 找出小文件最多的目录
sudo find /var -type f | xargs -I{} dirname {} | sort | uniq -c | sort -rn | head

# 解决办法：
# 1. 删除无用小文件
# 2. 重新格式化时指定更多 inode：mkfs.ext4 -N 1000000 /dev/sdb1
```

#### 8.3 文件描述符

```bash
# 查看当前用户的文件描述符上限
ulimit -n

# 查看某进程的文件描述符上限
cat /proc/$(pgrep -f nginx | head -n1)/limits | grep "open files"

# 查看某进程打开的文件描述符
ls -l /proc/1234/fd/ | wc -l

# 临时调整（仅当前 Shell）
ulimit -n 65536

# 永久调整（修改 /etc/security/limits.conf）
# * soft nofile 65536
# * hard nofile 65536

# systemd 服务则在单元文件中设置 LimitNOFILE=65536
```

---

## 代码文件说明

| 文件 | 用途 | 是否需 root |
|------|------|------------|
| `Code/01-disk-partition.sh` | 演示 lsblk 查看、fdisk/parted 分区、mkfs 格式化 | 是 |
| `Code/02-filesystem-mount.sh` | 演示 mount/umount、blkid、/etc/fstab 配置 | 是 |
| `Code/03-lvm-management.sh` | 演示 PV/VG/LV 创建、扩容、文件系统扩容 | 是 |
| `Code/04-disk-usage.sh` | 演示 df/du/ncdu 磁盘使用分析、inode 检查、fd 限制 | 部分需要 |

---

## 关键知识点总结

### 1. 磁盘命令速查表

| 命令 | 用途 | 示例 |
|------|------|------|
| `lsblk` | 块设备树形视图 | `lsblk -f` |
| `fdisk -l` | 分区详细信息 | `sudo fdisk -l /dev/sda` |
| `parted -l` | GPT 分区查看 | `sudo parted -l` |
| `df -h` | 文件系统使用 | `df -hT` |
| `df -i` | inode 使用 | `df -i` |
| `du -sh` | 目录占用 | `du -sh /opt` |
| `du --max-depth=1` | 一级子目录大小 | `du -h --max-depth=1 /var` |
| `ncdu` | 交互式分析 | `ncdu /` |
| `blkid` | 获取 UUID | `sudo blkid /dev/sdb1` |
| `mount` | 挂载 | `sudo mount /dev/sdb1 /mnt` |
| `umount` | 卸载 | `sudo umount /mnt` |
| `free -h` | 内存与 swap | `free -h` |
| `swapon` | 启用 swap | `sudo swapon /swapfile` |
| `fsck` | 文件系统检查 | `sudo fsck /dev/sdb1` |

### 2. 文件系统对比表

| 文件系统 | 默认发行版 | 最大文件 | 在线扩容 | 缩容 | 快照 | 推荐 |
|---------|----------|---------|---------|------|------|------|
| ext4 | Ubuntu/Debian | 16TB | resize2fs | 支持 | 否 | 通用 |
| xfs | CentOS/RHEL | 8EB | xfs_growfs | 不支持 | 否 | 数据库 |
| btrfs | - | 16EB | 支持 | 支持 | 是 | 高级特性 |
| zfs | - | 16EB | 支持 | 支持 | 是 | 数据完整性 |

### 3. LVM 概念图

```
   物理磁盘            物理卷 PV          卷组 VG          逻辑卷 LV
  ┌────────┐         ┌────────┐       ┌──────────────────────┐   ┌──────────────┐
  │ /dev/  │  pvcreate│ /dev/  │vgcreate│                     │   │ lv_data      │
  │ sdb    │ ───────→│ sdb   │ ────→ │   vg_ecommerce       │ ─→│  /mnt/data   │
  └────────┘         └────────┘       │  (PV 池子)           │   └──────────────┘
  ┌────────┐         ┌────────┐       │                     │   ┌──────────────┐
  │ /dev/  │  pvcreate│ /dev/  │       │                     │   │ lv_mysql     │
  │ sdc    │ ───────→│ sdc   │ ────→ │                     │ ─→│  /var/lib/   │
  └────────┘         └────────┘       └──────────────────────┘   │   mysql      │
                                                                  └──────────────┘
  扩容流程：
  1. 加新磁盘 → pvcreate /dev/sdd
  2. vgextend vg_ecommerce /dev/sdd
  3. lvextend -l +100%FREE /dev/vg_ecommerce/lv_data
  4. resize2fs（ext4）/ xfs_growfs（xfs）
```

### 4. fstab 字段说明表

| 字段 | 含义 | 常用值 |
|------|------|-------|
| 1. 设备 | 设备名或 UUID | `UUID=xxx` / `/dev/sdb1` |
| 2. 挂载点 | 挂载目录 | `/mnt/data` / `none`（swap） |
| 3. 文件系统 | 类型 | `ext4` / `xfs` / `swap` |
| 4. 挂载选项 | 选项 | `defaults` / `rw,noatime` |
| 5. dump | 是否 dump 备份 | `0` |
| 6. pass | fsck 顺序 | `0`（跳过）/ `1`（根）/ `2`（其他） |

---

## 实战练习

### 练习 1：为 MySQL 数据目录扩容

电商 MySQL 数据目录 `/var/lib/mysql` 所在分区已使用 90%，运维加了 100GB 新盘 `/dev/sdb`，请：

1. 用 `lsblk` 与 `fdisk -l` 确认新盘
2. 用 `parted` 创建 GPT 分区并标记为 LVM
3. 创建 PV 加入现有 VG `vg_data`
4. 用 `lvextend` 给 `lv_mysql` 扩容 50GB
5. 用 `xfs_growfs` 同步文件系统
6. 用 `df -h` 与 `lvs` 验证扩容结果

**验收**：MySQL 服务无需停止，扩容后可用空间增加 50GB。

### 练习 2：排查 "No space left on device" 但 `df -h` 显示有空间

某天 Nginx 上传图片报错 "No space left on device"，但 `df -h /var` 显示还有 50GB 空间。

1. 用 `df -i /var` 检查 inode 使用率
2. 用 `find /var -type f | wc -l` 统计文件数
3. 用 `find /var -type f -mtime +30 -delete` 删除 30 天前的旧文件
4. 重新检查 `df -i`

**验收**：inode 使用率下降到 50% 以下。

### 练习 3：创建文件型 Swap

云服务器只有 2GB 内存，编译 Node.js 模块时被 OOM 杀掉。请：

1. 用 `free -h` 与 `swapon --show` 检查当前 swap
2. 创建 2GB swap 文件 `/swapfile`
3. 启用并写入 `/etc/fstab`
4. 调整 `vm.swappiness=10`
5. 验证 `free -h` 显示 Swap 增加 2GB

**验收**：重启后 swap 仍生效；再次编译模块不再 OOM。
