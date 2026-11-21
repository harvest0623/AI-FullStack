# Linux 学习指南

> 系统化掌握 Linux 操作系统核心能力，为后端开发、运维与 AI 应用部署奠定服务器基础

> 共 14 天，覆盖从环境搭建、文件操作、Shell 脚本到系统监控与自动化部署的完整知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [示例场景](#示例场景)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是全栈学习系列的**操作系统基石**。无论你用 Node.js、Python 还是 Java 做后端，最终都要部署到 Linux 服务器上；无论你用 Docker 还是 Kubernetes，底层都是 Linux 内核能力；无论你做 MySQL 运维还是 Redis 调优，都离不开 Linux 性能分析工具。Linux 是全球服务器操作系统的绝对霸主（云计算市场占有率超过 90%），掌握 Linux 是每一个后端工程师和 AI 应用工程师的必备技能。

**学习目标**：完成本板块后，你应能：
- 熟练使用 Linux 常用命令完成文件操作、文本处理、用户管理、进程管理
- 理解 Linux 文件系统层次标准（FHS）与权限模型
- 用 grep/sed/awk 三剑客高效处理文本与日志
- 编写 Shell 脚本实现自动化任务
- 配置网络、磁盘、软件包与服务
- 使用 systemd 管理服务生命周期
- 用定时任务与日志系统实现运维自动化
- 掌握系统监控与性能调优工具（top/vmstat/iostat/htop）
- 配置防火墙与安全加固
- 完成 Nginx / MySQL / Redis / Node.js 服务的部署与运维

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 Shell 脚本 + 实战练习
- 全程围绕一个**电商项目服务器运维**场景展开，前后连贯
- 所有 Shell 脚本可在 Ubuntu 22.04+ / CentOS 8+ 直接执行
- 紧扣工程化视角，多处铺垫后端部署与 AI 应用场景

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| 命令行基础 | 了解即可 | 知道终端是什么、能打字即可 |
| 操作系统概念 | 基础 | 文件、目录、进程概念 |
| 网络概念 | 基础 | IP、端口、TCP/UDP |
| 后端开发经验 | 有更好 | 理解服务部署需求 |

**环境准备**：
- Ubuntu 22.04 LTS（推荐）或 CentOS 8 / Rocky Linux 9
- 获取方式：云服务器（阿里云/腾讯云/AWS）、虚拟机（VirtualBox/VMware）、WSL2（Windows 子系统）、Docker 容器
- SSH 客户端：系统自带终端（macOS/Linux）、PuTTY / Xshell / Windows Terminal（Windows）

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Linux 学习路线（14天）                        │
└─────────────────────────────────────────────────────────────────┘

阶段一：基础与文件操作（Day01-Day04）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Day01 基础  │  Day02 文件  │  Day03 文本  │  Day04 用户  │
│  与环境      │  系统操作    │  处理三剑客  │  与权限      │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
阶段二：系统管理（Day05-Day08）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Day05 进程  │  Day06 网络  │  Day07 磁盘  │  Day08 软件包│
│  与服务      │  配置        │  与文件系统  │  与服务部署  │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
阶段三：Shell 脚本与自动化（Day09-Day11）
┌──────────────┬──────────────┬──────────────┐
│  Day09 Shell │  Day10 Shell │  Day11 定时  │
│  基础        │  进阶        │  任务与日志   │
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       ▼              ▼              ▼
阶段四：监控安全与实战（Day12-Day14）
┌──────────────┬──────────────┬──────────────┐
│  Day12 系统监控│  Day13 防火墙│  Day14 实战  │
│  与性能调优    │  与安全加固  │  运维部署    │
└──────────────┴──────────────┴──────────────┘
```

---

## 示例场景

本板块全程围绕一个**电商项目服务器运维**场景展开，模拟从拿到一台空白服务器到部署完整服务栈的全过程。

### 服务器环境

```
服务器：Ubuntu 22.04 LTS
IP：192.168.1.100
项目：电商全栈应用（ecommerce）

部署架构：
┌──────────────────────────────────────────────────┐
│                  Linux Server                    │
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │
│  │ Nginx   │→ │ Node.js │  │ MySQL 8.0       │  │
│  │ :80/:443│  │ :3000   │  │ :3306           │  │
│  └─────────┘  └─────────┘  └─────────────────┘  │
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │
│  │ Redis 7 │  │ PM2     │  │ Logrotate       │  │
│  │ :6379   │  │ 进程管理│  │ 日志轮转        │  │
│  └─────────┘  └─────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 用户与目录规划

```
用户规划：
  deploy          → 部署用户（非root，sudo权限）
  www-data        → Web服务运行用户
  mysql           → MySQL运行用户
  redis           → Redis运行用户

目录规划：
  /opt/ecommerce/              → 项目根目录
  /opt/ecommerce/backend/      → 后端代码
  /opt/ecommerce/logs/        → 应用日志
  /opt/ecommerce/scripts/     → 运维脚本
  /opt/ecommerce/backup/      → 数据备份
  /etc/nginx/sites-available/  → Nginx 配置
  /var/log/ecommerce/          → 系统日志
```

> 各天的命令与脚本围绕这个服务器环境展开，逐步完成从系统初始化到服务部署的完整流程。

---

## 每日内容详表

### 阶段一：基础与文件操作

#### Day01 - Linux基础与环境安装
- **核心**：操作系统概念、Linux 起源与发行版（Ubuntu/Debian vs CentOS/RHEL）、内核与用户空间、终端与 Shell（bash/zsh）、SSH 远程连接、虚拟机/WSL2/云服务器获取方式、基本命令（ls/cd/pwd/mkdir/rm/cp/mv）、命令帮助（man/info/--help/whatis）、history、命令补全 Tab
- **代码**：`01-environment-setup.sh`（环境初始化）/ `02-basic-commands.sh`（基础命令练习）/ `README.md`（环境配置指南）
- **重点**：搭建可用的 Linux 练习环境

#### Day02 - 文件系统与目录操作
- **核心**：FHS 目录结构（/etc /var /home /opt /tmp /proc /sys）、绝对路径与相对路径、文件操作（touch/cat/less/more/head/tail/nl/wc/sort/uniq/cut/tr/tee/file/stat）、目录操作（mkdir -p/rmdir/tree）、文件查找（find/locate/which/whereis）、软链接与硬链接（ln -s/ln）、文件压缩与解压（tar/gzip/gunzip/zip/unzip/xz/zstd）、通配符与特殊字符
- **代码**：`01-file-operations.sh` / `02-file-search.sh` / `03-compression.sh`
- **重点**：find 命令的强大查找能力、软链接 vs 硬链接

#### Day03 - 文本处理三剑客(grep/sed/awk)
- **核心**：grep（基本/扩展正则、-r 递归、-v 反选、-c 计数、-n 行号、-o 仅匹配、-A/-B/-C 上下文）、sed（流编辑器、地址定界、s 替换、d 删除、a 追加、i 插入、p 打印、-i 原地修改、多命令 -e）、awk（字段与记录、NR/NF、BEGIN/END 块、模式匹配、内置变量、数组、printf 格式化）、正则表达式速览、管道与重定向（| / > / >> / 2> / 2>&1 / <）、xargs、cut、tr、sort、uniq、column
- **代码**：`01-grep-demo.sh` / `02-sed-demo.sh` / `03-awk-demo.sh` / `04-pipeline-redirect.sh`
- **重点**：三剑客配合管道处理日志的实战能力

#### Day04 - 用户与权限管理
- **核心**：用户管理（useradd/usermod/userdel/passwd/id/whoami/who/w）、用户组管理（groupadd/groupmod/groupdel/gpasswd/newgrp）、su 与 sudo（su -/sudo/sudoers/visudo）、文件权限（rwx/数字表示法/chmod/chown/chgrp）、特殊权限（SUID/SGID/Sticky Bit）、umask、ACL（setfacl/getfacl）、SSH 密钥认证（ssh-keygen/ssh-copy-id/authorized_keys）
- **代码**：`01-user-group-management.sh` / `02-permission-management.sh` / `03-ssh-key-auth.sh`
- **重点**：权限模型理解、sudo 安全配置、SSH 免密登录

---

### 阶段二：系统管理

#### Day05 - 进程管理与服务管理
- **核心**：进程概念（PID/PPID/进程状态）、进程查看（ps/ps aux/pstree/top/htop/pgrep/pidof）、进程控制（kill/killall/pkill/信号列表/nice/renice/jobs/bg/fg/nohup/&);
- **核心**：systemd 服务管理（systemctl start/stop/restart/status/enable/disable/reload/daemon-reload/list-units/list-unit-files）、journalctl 日志（journalctl -u/-f/--since/--until/-p）、单元文件结构（[Unit]/[Service]/[Install]）、自定义 systemd 服务、service 命令（旧版兼容）、/etc/init.d/
- **代码**：`01-process-management.sh` / `02-systemd-service-management.sh` / `ecommerce-backend.service`（自定义服务文件）
- **重点**：systemd 是现代 Linux 服务管理的核心

#### Day06 - 网络配置与网络命令
- **核心**：网络基础（IP/子网/网关/DNS/端口）、网络配置（ip addr/ip route/ifconfig/route/网络配置文件）、网络连通性（ping/telnet/nc/traceroute/mtr/tracepath）、DNS 查询（nslookup/dig/host）、端口查看（ss/netstat/lsof -i）、curl（GET/POST/-H/-d/--cookie/--resolve/--connect-timeout）、wget（递归下载/断点续传）、防火墙状态查看、SSH 端口转发（-L/-R/-D）、scp/rsync 文件传输
- **代码**：`01-network-config.sh` / `02-network-diagnostics.sh` / `03-curl-wget.sh` / `04-ssh-tunnel-rsync.sh`
- **重点**：ss/netstat 排查端口占用、curl 测试 API、rsync 高效同步

#### Day07 - 磁盘管理与文件系统
- **核心**：磁盘分区（lsblk/fdisk/parted/gdisk）、文件系统（mkfs.ext4/mkfs.xfs/mkfs.btrfs）、挂载与卸载（mount/umount/fstab 自动挂载/umount -l）、磁盘使用查看（df -h/du -sh/ncdu）、LVM 逻辑卷（pv/vg/lv 创建/扩容/缩容）、交换分区（swap/swapoff/swapon）、文件系统检查（fsck）、iNode 与文件描述符
- **代码**：`01-disk-partition.sh` / `02-filesystem-mount.sh` / `03-lvm-management.sh` / `04-disk-usage.sh`
- **重点**：LVM 动态扩容是生产必备技能

#### Day08 - 软件包管理与服务部署
- **核心**：Debian 系（apt/apt-get/dpkg/apt-cache/sources.list/PPA）、RHEL 系（yum/dnf/rpm/repo）、源码编译（./configure && make && make install）、服务部署实战（Nginx 安装配置、MySQL 安装初始化、Redis 安装、Node.js nvm 版本管理 + PM2 进程管理）、环境变量（/etc/profile / ~/.bashrc / ~/.bash_profile / export）
- **代码**：`01-package-management.sh` / `02-deploy-nginx.sh` / `03-deploy-nodejs-pm2.sh` / `04-environment-variables.sh`
- **重点**：从零部署一套完整的 Web 服务栈

---

### 阶段三：Shell 脚本与自动化

#### Day09 - Shell脚本基础
- **核心**：Shell 脚本结构（#!/bin/bash、注释、执行方式 bash/chmod +x/source/.）、变量（自定义变量/环境变量/位置参数 $1-$9/$#/$@/$*/$?/$$/$!）、字符串操作（长度/截取/替换/大小写）、数组（定义/访问/遍历/长度）、命令替换 `` 与 $()、算术运算（$(()) / $[] / expr / let）、read 读取输入、echo 与 printf 输出、printf 格式化
- **代码**：`01-hello-shell.sh` / `02-variables.sh` / `03-string-array.sh` / `04-arithmetic-read.sh`
- **重点**：变量与位置参数是脚本编程的基础

#### Day10 - Shell脚本进阶(条件/循环/函数)
- **核心**：条件判断（test/[]/[[]] 文件测试/字符串测试/数值测试、if/elif/else/fi、case/esac）、循环（for/in/do/done、while、until、break/continue、seq、C 风格 for）、函数（定义/调用/参数/return/局部变量 local）、数组遍历与关联数组（declare -A）、正则与 =~、select 菜单、trap 信号处理、set -e/-u/-x 调试、脚本调试（bash -x/-n/-v）
- **代码**：`01-conditionals.sh` / `02-loops.sh` / `03-functions.sh` / `04-practical-scripts.sh`（实战脚本合集：备份/健康检查/批量部署）
- **重点**：条件判断、循环与函数的综合运用

#### Day11 - 定时任务与日志管理
- **核心**：crontab（crontab -e/-l/-r、cron 表达式五段式、@reboot/@daily/@weekly、/etc/crontab 系统级、anacron）、at 一次性任务、日志系统（rsyslog / /var/log/ 结构、journalctl 详解、dmesg 内核日志）、logrotate 日志轮转（配置文件/参数/rotate/compress/size/daily）、应用日志管理（PM2 logs、Docker logs、自定义日志切割）、时间同步（timedatectl/chrony/ntpdate）
- **代码**：`01-crontab-examples.sh` / `02-logrotate-ecommerce.conf` / `03-log-management.sh` / `04-time-sync.sh`
- **重点**：crontab 与 logrotate 是运维自动化的两大支柱

---

### 阶段四：监控安全与实战

#### Day12 - 系统监控与性能调优
- **核心**：CPU 监控（top/htop/mpstat/loadavg）、内存监控（free/vmstat/smem）、磁盘 IO（iostat/iotop/dstat）、网络监控（iftop/nethogs/sar）、进程追踪（strace/ltrace/perf）、系统综合（sar/sysstat/dstat/glances）、性能调优思路（CPU/内存/IO/网络四维度排查）、ulimit 资源限制、/proc 与 /sys 文件系统、OOM Killer
- **代码**：`01-cpu-memory-monitoring.sh` / `02-disk-io-monitoring.sh` / `03-network-monitoring.sh` / `04-performance-tuning.md`（性能调优指南）
- **重点**：top/vmstat/iostat 三大性能分析利器

#### Day13 - 防火墙与安全加固
- **核心**：ufw（Ubuntu 默认，enable/allow/deny/status/rule）、firewalld（CentOS/RHEL 默认，zone/service/port/add/remove）、iptables/nftables（底层规则链）、SSH 安全加固（禁用 root 登录、改端口、密钥认证、fail2ban 防暴力破解）、SELinux/AppArmor 简介、系统安全清单（最小化安装、关闭无用服务、定期更新、审计 auditd）、端口扫描（nmap）、漏洞检查
- **代码**：`01-ufw-firewall.sh` / `02-firewalld-firewall.sh` / `03-ssh-hardening.sh` / `04-security-checklist.md`（安全加固清单）
- **重点**：防火墙配置与 SSH 安全是服务器安全的第一道防线

#### Day14 - 实战运维与自动化部署
- **核心**：服务器初始化脚本（创建用户/配置 SSH/安装基础软件/设置时区/优化系统参数）、Nginx 反向代理配置（upstream/负载均衡/HTTPS 证书/域名配置）、MySQL 自动化部署与备份脚本、Redis 部署与配置、Node.js + PM2 部署脚本、一键部署脚本（综合运用前 13 天知识）、Docker 与 Docker Compose 简介与对比、运维最佳实践总结
- **代码**：`01-server-init.sh`（服务器初始化）/ `02-deploy-nginx-reverse-proxy.conf`（Nginx 反向代理配置）/ `03-deploy-full-stack.sh`（一键部署全栈服务）/ `04-mysql-backup.sh`（MySQL 自动备份）/ `05-ops-best-practices.md`（运维最佳实践）
- **重点**：综合运用所学知识完成完整的服务部署与运维

---

## 目录结构

```
Linux/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - Linux基础与环境安装/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天 Shell 脚本
│       ├── 01-environment-setup.sh
│       ├── 02-basic-commands.sh
│       └── README.md
├── Day02 - 文件系统与目录操作/
│   ├── README.md
│   └── Code/
│       ├── 01-file-operations.sh
│       ├── 02-file-search.sh
│       └── 03-compression.sh
├── ...（Day03-Day13 同构）...
└── Day14 - 实战运维与自动化部署/
    ├── README.md
    └── Code/
        ├── 01-server-init.sh
        ├── 02-deploy-nginx-reverse-proxy.conf
        ├── 03-deploy-full-stack.sh
        ├── 04-mysql-backup.sh
        └── 05-ops-best-practices.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，以 `.sh`（Shell 脚本）为主
- 配置文件使用对应扩展名（`.conf` / `.service` / `.md`）
- 部分脚本需要 root/sudo 权限执行，README 中会标注

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-6 小时 | 约 2-3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 4-5 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **必须动手**：Linux 是实践性最强的板块，每条命令都要在真实终端中敲一遍
2. **先读后练**：每天先通读 README，理解概念后动手执行脚本
3. **故意犯错**：尝试错误命令、错误参数，观察系统如何报错
4. **多用 man**：遇到不熟悉的命令，先 `man command` 查官方手册
5. **结合部署**：回想 MySQL/Redis/Node.js/NestJS 板块，理解这些服务如何在 Linux 上运行
6. **完成实战**：每天 README 末尾的实战练习是巩固知识的关键
7. **Day14 是综合**：最后一天的部署脚本是前 13 天知识的总检验

### 阶段性检查点

完成每个阶段后，应能回答以下问题：

- **阶段一完成后**：能否在命令行中完成文件查找、文本处理、权限配置？
- **阶段二完成后**：能否用 systemd 管理服务、排查网络问题、扩容磁盘、部署软件？
- **阶段三完成后**：能否编写 Shell 脚本实现自动化任务、配置定时任务与日志轮转？
- **阶段四完成后**：能否完成服务器初始化、安全加固、性能调优与全栈服务部署？

---

## 如何运行代码

### 方式一：WSL2（Windows 用户推荐）

```powershell
# 在 PowerShell 中启用 WSL2
wsl --install -d Ubuntu-22.04

# 启动后设置用户名密码即可使用
# Windows Terminal 自动集成 WSL
```

### 方式二：Docker 容器

```bash
# 启动 Ubuntu 容器作为练习环境
docker run -it --name linux-learn ubuntu:22.04 /bin/bash

# 挂载本地代码目录（方便编辑）
docker run -it --name linux-learn \
  -v /path/to/Linux:/workspace \
  ubuntu:22.04 /bin/bash
```

### 方式三：虚拟机

1. 下载 Ubuntu 22.04 LTS ISO
2. 用 VirtualBox / VMware 创建虚拟机
3. 建议配置：2 核 CPU / 2GB 内存 / 20GB 磁盘

### 方式四：云服务器

```bash
# 购买云服务器后用 SSH 连接
ssh root@your-server-ip

# 创建练习用户
useradd -m -s /bin/bash student
passwd student
usermod -aG sudo student

# 切换到练习用户
su - student
```

### 执行 Shell 脚本

```bash
# 方式一：直接执行（需可执行权限）
chmod +x script.sh
./script.sh

# 方式二：用 bash 执行（无需可执行权限）
bash script.sh

# 方式三：source 执行（在当前 Shell 中执行，影响当前环境）
source script.sh
# 或
. script.sh

# 方式四：管道执行
cat script.sh | bash
```

### 常用终端快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + C` | 终止当前命令 |
| `Ctrl + Z` | 挂起到后台 |
| `Ctrl + D` | 发送 EOF（退出 Shell） |
| `Ctrl + L` | 清屏（等同 clear） |
| `Ctrl + R` | 搜索历史命令 |
| `Ctrl + A` | 光标移到行首 |
| `Ctrl + E` | 光标移到行尾 |
| `Tab` | 自动补全 |
| `!!` | 执行上一条命令 |
| `!$` | 上一条命令的最后一个参数 |

### Windows 用户注意

- 推荐使用 WSL2 而非 Cygwin / Git Bash（WSL2 是完整的 Linux 内核）
- `.sh` 文件在 Windows 中编辑时注意换行符（LF vs CRLF），建议用 VS Code 设置为 LF
- 用 `dos2unix script.sh` 可将 CRLF 转为 LF
- SSH 客户端推荐 Windows Terminal + OpenSSH

---

## 知识点速查

### 常用命令分类速查

| 类别 | 命令 | 对应天数 |
|------|------|---------|
| 文件操作 | ls / cd / cp / mv / rm / touch / cat / less / head / tail | Day01-Day02 |
| 文件查找 | find / locate / which / whereis | Day02 |
| 文本处理 | grep / sed / awk / cut / sort / uniq / tr / tee | Day03 |
| 用户权限 | useradd / passwd / chmod / chown / sudo / ssh-keygen | Day04 |
| 进程管理 | ps / top / kill / killall / pstree / nohup | Day05 |
| 服务管理 | systemctl / journalctl | Day05 |
| 网络 | ip / ping / ss / curl / wget / scp / rsync | Day06 |
| 磁盘 | lsblk / fdisk / mount / df / du / lvm | Day07 |
| 软件包 | apt / dpkg / yum / dnf / rpm | Day08 |
| Shell | bash / source / chmod +x / bash -x | Day09-Day10 |
| 定时任务 | crontab / at / logrotate | Day11 |
| 监控 | top / htop / vmstat / iostat / free / sar | Day12 |
| 安全 | ufw / firewalld / iptables / fail2ban | Day13 |

### Vim 基础速查

| 模式 | 命令 | 功能 |
|------|------|------|
| 命令模式 | `i` | 进入插入模式 |
| 命令模式 | `o` | 下方新建行并进入插入模式 |
| 命令模式 | `dd` | 删除整行 |
| 命令模式 | `yy` | 复制整行 |
| 命令模式 | `p` | 粘贴 |
| 命令模式 | `u` | 撤销 |
| 命令模式 | `Ctrl + r` | 重做 |
| 命令模式 | `gg` | 跳到文件首 |
| 命令模式 | `G` | 跳到文件尾 |
| 命令模式 | `/keyword` | 搜索关键词 |
| 命令模式 | `n` / `N` | 下一个/上一个匹配 |
| 任意模式 | `Esc` | 回到命令模式 |
| 命令模式 | `:w` | 保存 |
| 命令模式 | `:q` | 退出 |
| 命令模式 | `:wq` | 保存并退出 |
| 命令模式 | `:q!` | 强制退出不保存 |
| 命令模式 | `:set number` | 显示行号 |

### 权限数字速查

```
权限          数字  含义
---           0    无权限
--x           1    仅执行
-w-           2    仅写
-wx           3    写+执行
r--           4    仅读
r-x           5    读+执行
rw-           6    读+写
rwx           7    读+写+执行

常用组合：
755  rwxr-xr-x   目录/可执行文件
644  rw-r--r--   普通文件
600  rw-------   私密文件（如 SSH 私钥）
777  rwxrwxrwx   全开（危险！仅临时调试）
```

### systemd 服务管理速查

```bash
systemctl start service        # 启动服务
systemctl stop service         # 停止服务
systemctl restart service      # 重启服务
systemctl reload service       # 重载配置（不中断）
systemctl status service       # 查看状态
systemctl enable service       # 开机自启
systemctl disable service      # 禁用开机自启
systemctl is-active service    # 是否运行中
systemctl is-enabled service   # 是否开机自启
systemctl list-units --type=service --state=running  # 运行中的服务
systemctl daemon-reload        # 重新加载单元文件

journalctl -u service          # 查看服务日志
journalctl -u service -f       # 实时跟踪日志
journalctl --since today       # 今天的日志
journalctl -p err              # 错误级别日志
```

### crontab 表达式速查

```
┌──────── 分钟 (0-59)
│ ┌────── 小时 (0-23)
│ │ ┌──── 日 (1-31)
│ │ │ ┌── 月 (1-12)
│ │ │ │ ─ 星期 (0-7, 0和7都是周日)
│ │ │ │ │
* * * * * command

示例：
*/5 * * * *     command       # 每5分钟
0 * * * *       command       # 每小时整点
0 2 * * *       command       # 每天凌晨2点
0 0 * * 0       command       # 每周日午夜
0 0 1 * *       command       # 每月1号午夜
0 9-18 * * 1-5  command       # 工作日9-18点每小时
@daily           command       # 每天（等同 0 0 * * *）
@reboot          command       # 开机时
```

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **Docker** | 容器化部署、Dockerfile 编写、容器编排，Linux 是 Docker 的底层 |
| **Node.js / NestJS** | 服务部署到 Linux、PM2 进程管理、Nginx 反向代理 |
| **MySQL** | MySQL 在 Linux 上的安装配置、性能调优、备份脚本 |
| **Redis** | Redis 在 Linux 上的部署、内存调优、集群搭建 |
| **LLM / RAG** | GPU 服务器管理、模型部署、Python 环境管理 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [Linux 官方文档](https://www.kernel.org/doc/html/latest/) - 内核文档
- [Ubuntu 官方文档](https://help.ubuntu.com/) - Ubuntu 使用指南
- [Linux 命令大全](https://www.runoob.com/linux/linux-command-manual.html) - 中文命令参考
- [The Linux Documentation Project](https://tldp.org/) - 经典 Linux 文档
- [Shell Scripting Tutorial](https://www.shellscript.sh/) - Shell 脚本教程
- [Linux Performance](http://www.brendangregg.com/linuxperf.html) - 性能调优大师 Brendan Gregg

---

## 贡献与反馈

本学习手册为原创内容，参考 GitHub 优质仓库的文档风格但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用命令行掌控你的全栈之路！**
