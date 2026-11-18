# Day01 - Linux 基础与环境安装

## 本章简介

Linux 是服务器操作系统的绝对霸主，全球云计算市场占有率超过 90%，从互联网巨头的核心交易系统到个人开发者的博客站点，从 Docker 容器底层到 Kubernetes 集群节点，几乎所有后端服务最终都运行在 Linux 之上。掌握 Linux 是每一个后端工程师、运维工程师和 AI 应用工程师的必备技能，也是理解 Docker、Kubernetes、CI/CD 等现代云原生技术的根基。

本章作为 Linux 学习路线的起点，从操作系统的基本概念出发，理清内核与用户空间的边界、Linux 的起源与发行版体系，对比 Ubuntu 与 CentOS 两大主流发行版的差异，并完成可运行练习环境的搭建。掌握本章后，你将拥有一台可执行 Shell 命令的 Ubuntu 22.04 环境，理解终端与 Shell 的关系，并能用 `ls`、`cd`、`mkdir`、`rm` 等基础命令完成文件操作，为后续深入学习文件系统、文本处理、用户权限打下基础。

## 学习目标

- 理解操作系统的核心概念：内核、用户空间、系统调用
- 了解 Linux 的起源历史：Unix → Minix → Linux，理解 GNU 项目与 GPL 协议
- 区分 Debian 系与 RHEL 系两大发行版体系，掌握 apt 与 yum/dnf 包管理器差异
- 对比 Ubuntu 与 CentOS 的关键差异（包管理/服务管理/防火墙/文件系统）
- 理解 Shell 的概念，区分 bash/zsh/fish 与终端模拟器
- 读懂终端提示符 `user@host:dir$` 的含义
- 使用 SSH 远程连接服务器，配置 `~/.ssh/config` 简化连接
- 通过 WSL2、Docker、虚拟机、云服务器四种方式获取 Linux 环境
- 熟练使用基础命令：`ls`、`cd`、`pwd`、`mkdir`、`rmdir`、`rm`、`cp`、`mv`、`touch`
- 使用 `man`、`info`、`--help`、`whatis`、`tldr` 获取命令帮助
- 掌握 `history`、Tab 补全、`Ctrl+R` 搜索历史等终端效率技巧

## 理论知识讲解

### 1. 操作系统核心概念

操作系统（Operating System，OS）是管理计算机硬件与软件资源的系统软件，是用户与硬件之间的桥梁。理解 Linux 需要先理清三个核心概念：

| 概念 | 说明 | 示例 |
| --- | --- | --- |
| 内核（Kernel） | 操作系统的核心，直接管理 CPU、内存、磁盘、网卡等硬件，提供进程调度、内存管理、文件系统、网络协议栈、设备驱动 | Linux Kernel、Windows NT Kernel |
| 用户空间（User Space） | 运行在内核之上的应用程序空间，权限受限，不能直接访问硬件，必须通过系统调用请求内核服务 | bash、nginx、mysql、node |
| 系统调用（System Call） | 用户空间程序请求内核服务的接口，是用户态进入内核态的唯一合法入口 | `read()`、`write()`、`open()`、`fork()`、`exec()` |

**内核态与用户态的隔离**是现代操作系统的安全基石：

```
┌─────────────────────────────────────────────┐
│              用户空间（User Space）           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌───────┐ │
│  │ bash   │ │ nginx  │ │ mysql  │ │ node  │ │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬───┘ │
│      │          │          │          │      │
│      └──────────┴──────────┴──────────┘      │
│                   │ 系统调用                   │
├───────────────────┼─────────────────────────┤
│                   ▼                          │
│              内核空间（Kernel Space）          │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ 进程调度  │ │ 内存管理  │ │ 文件系统/VFS │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ 网络协议栈│ │ 设备驱动  │ │ 系统调用接口 │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
└─────────────────────────────────────────────┘
                  │
                  ▼
            硬件（CPU/内存/磁盘/网卡）
```

> 应用程序崩溃通常只影响自身，而内核崩溃会导致整个系统宕机（Kernel Panic）。

### 2. Linux 的起源与发展

Linux 的诞生是一段极客精神的传奇，理解这段历史有助于理解 Linux 的开源基因：

```
1969  Unix 诞生（AT&T Bell Labs, Ken Thompson & Dennis Ritchie）
  │    闭源但源码可在学术界流通，成为现代操作系统的鼻祖
  │
1983  Richard Stallman 发起 GNU 项目
  │    目标：创建一套完全自由的类 Unix 操作系统
  │    产出：GCC、Emacs、Bash、Coreutils 等核心工具
  │    协议：GPL（GNU General Public License）
  │
1987  Andrew Tanenbaum 开发 Minix
  │    用于教学的微内核 Unix-like 系统
  │    启发了 Linus Torvalds
  │
1991  Linus Torvalds 创建 Linux 内核（21岁，赫尔辛基大学）
  │    "Just for fun" —— 在 comp.os.minix 发布首次公告
  │    仅内核，无完整用户态工具
  │
1992  Linux 内核与 GNU 工具结合
  │    形成 GNU/Linux 完整操作系统
  │    "Linux is just the kernel, GNU is the rest"
  │
1996  Tux 企鹅成为 Linux 吉祥物
  │
2000s 各大发行版成熟（Red Hat、Debian、Ubuntu...）
  │
2003  Android 基于 Linux 内核
  │
2013  Docker 基于 Linux 内核特性（cgroups + namespaces）
  │
至今  Linux 统治服务器、移动端、云计算、超算
```

**GPL 协议核心要点**：

- 自由使用、修改、分发源码
- 修改后的代码必须同样以 GPL 协议开源（传染性协议）
- 商业可用，但不能闭源衍生作品
- Linux 内核至今仍采用 GPL v2

### 3. Linux 发行版体系

Linux 严格意义上只是内核，内核加上 GNU 工具、桌面环境、包管理器等组成完整的发行版（Distribution）。发行版体系庞大，但可归纳为两大主流：

```
                    Linux 发行版家族
                         │
          ┌──────────────┴──────────────┐
          │                             │
      Debian 系                      RHEL 系
   (apt/dpkg 包管理)              (yum/dnf/rpm 包管理)
          │                             │
   ┌──────┼──────┐              ┌───────┼───────┐
   │      │      │              │       │       │
 Debian Ubuntu Linux Mint     CentOS  RHEL   Rocky/AlmaLinux
 (1993) (2004)  (2006)        (2004) (2000)    (2021)
```

**Debian 系特点**：

- 包管理器：`apt`（高级）、`dpkg`（底层）
- 软件包格式：`.deb`
- 配置文件路径：`/etc/network/interfaces`（旧）、Netplan（新）
- 服务管理：`systemctl`（systemd，Ubuntu 16.04+）
- 防火墙：`ufw`（基于 iptables 的简化工具）
- 默认文件系统：ext4
- 适用场景：桌面、开发、云服务器、Docker 基础镜像

**RHEL 系特点**：

- 包管理器：`dnf`（Fedora/RHEL 8+/CentOS 8+）、`yum`（旧版）、`rpm`（底层）
- 软件包格式：`.rpm`
- 配置文件路径：`/etc/sysconfig/network-scripts/`
- 服务管理：`systemctl`（systemd）
- 防火墙：`firewalld`（基于 nftables/iptables）
- 默认文件系统：xfs
- 适用场景：企业服务器、金融、电信、政府

> CentOS 8 已于 2021 年底停止维护，社区推荐替代为 Rocky Linux 与 AlmaLinux，均与 RHEL 100% 兼容。

### 4. Ubuntu vs CentOS 对比

| 维度 | Ubuntu | CentOS / Rocky |
| --- | --- | --- |
| 包管理器 | `apt` / `apt-get` / `dpkg` | `dnf` / `yum` / `rpm` |
| 安装软件 | `apt install nginx` | `dnf install nginx` |
| 更新索引 | `apt update` | `dnf makecache` |
| 软件包格式 | `.deb` | `.rpm` |
| 服务管理 | `systemctl`（systemd） | `systemctl`（systemd） |
| 防火墙 | `ufw` | `firewalld` |
| 默认文件系统 | ext4 | xfs |
| 默认 Shell | bash | bash |
| 配置网络 | Netplan（`/etc/netplan/`） | NetworkManager（`/etc/sysconfig/network-scripts/`） |
| SELinux | 默认不装（用 AppArmor） | 默认开启 enforcing |
| 软件源 | Ubuntu PPA 丰富 | EPEL 仓库扩展 |
| 发布周期 | LTS 每 2 年（22.04 / 24.04） | 跟随 RHEL（约 3 年一版） |
| 支持周期 | LTS 5 年（付费延长至 10 年） | 10 年 |
| 适用场景 | 云服务器、开发、Docker、桌面 | 企业生产、金融、电信 |
| 文档社区 | Ubuntu Wiki / Ask Ubuntu | CentOS Wiki / RHEL 官方文档 |

> 本教程统一采用 **Ubuntu 22.04 LTS**，原因：社区活跃、Docker 镜像小、生态丰富、新手友好。

### 5. Shell 概念详解

**Shell 是什么**：Shell 是用户与内核交互的命令解释器，接收用户输入的命令，解析后调用系统调用交给内核执行，再把结果返回给用户。Shell 既是交互式命令行界面，也是一种脚本语言。

```
用户输入命令 → Shell 解析 → 系统调用 → 内核执行 → 返回结果 → Shell 显示
```

**常见 Shell 对比**：

| Shell | 全称 | 特点 | 默认于 |
| --- | --- | --- | --- |
| sh (Bourne Shell) | / | 最早的 Unix Shell，功能基础 | 老旧系统 |
| bash (Bourne Again Shell) | / | sh 的增强版，GNU 项目产物，最通用 | Ubuntu / CentOS / macOS |
| zsh | Z shell | 功能强大，补全智能，主题丰富（Oh My Zsh） | Kali Linux（默认） |
| fish | Friendly Interactive Shell | 开箱即用，语法与 bash 不兼容 | 部分发行版可选 |
| dash | Debian Almquist Shell | 轻量快速，用于执行 `/bin/sh` 脚本 | Ubuntu 的 `/bin/sh` |

> 查看当前 Shell：`echo $SHELL`；查看系统支持的所有 Shell：`cat /etc/shells`；切换默认 Shell：`chsh -s /bin/zsh`。

**终端模拟器（Terminal Emulator）**：现代 Linux 通常不直接连接物理终端设备，而是使用图形界面下的终端模拟器软件：

- GNOME Terminal（Ubuntu 默认）
- Konsole（KDE 默认）
- Terminator（分屏）
- Alacritty（GPU 加速）
- iTerm2（macOS）
- Windows Terminal（Windows）

**交互式 Shell 与脚本**：

- **交互式 Shell**：用户在终端逐条输入命令，Shell 实时执行并返回结果
- **非交互式 Shell**：执行脚本文件（`.sh`），Shell 一次性读取并执行所有命令
- 两者语法基本一致，但交互式有提示符、自动补全、历史记录等增强

### 6. 终端提示符

打开终端首先看到的就是提示符（Prompt），读懂它就知道了当前的用户身份、所在主机、所在目录：

```
deploy@ecommerce-server:/opt/ecommerce$ 
└─┬─┘└─────┬──────┘└─────┬──────┘ └┬┘
  │         │             │          │
  │         │             │          └─ $ 表示普通用户，# 表示 root
  │         │             └─ 当前工作目录（~ 表示家目录）
  │         └─ 主机名（hostname）
  └─ 当前用户名
```

**示例对比**：

```
deploy@ecommerce-server:~$ whoami      # 普通用户提示符 $
deploy
root@ecommerce-server:~# whoami        # root 用户提示符 #
root
```

提示符格式由环境变量 `PS1` 控制，可自定义。例如显示完整路径、加颜色、加 Git 分支等：

```bash
# 查看当前 PS1
echo $PS1

# 临时修改（加颜色与时间）
export PS1='\[\e[32m\]\u@\h\[\e[0m\]:\[\e[34m\]\w\[\e[0m\]\$ '
```

### 7. SSH 远程连接

服务器通常托管在机房或云端，运维人员通过 SSH（Secure Shell）协议远程登录操作。SSH 基于非对称加密，比 Telnet 安全得多。

**基本用法**：

```bash
# 默认 22 端口登录
ssh deploy@192.168.1.100

# 指定端口登录
ssh -p 2222 deploy@192.168.1.100

# 指定私钥文件
ssh -i ~/.ssh/id_rsa deploy@192.168.1.100

# 执行单条远程命令后退出
ssh deploy@192.168.1.100 'uptime'

# 端口转发（本地 8080 转发到远程 80）
ssh -L 8080:localhost:80 deploy@192.168.1.100
```

**SSH 配置文件 `~/.ssh/config`**：把常用的连接参数写入配置文件，简化日常命令：

```ssh-config
# ~/.ssh/config
Host ecommerce
    HostName 192.168.1.100
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60

Host db-server
    HostName 10.0.0.20
    User root
    Port 2222
```

配置后可直接 `ssh ecommerce` 连接，无需输入完整参数。

**SSH 首次连接指纹确认**：

```bash
ssh deploy@192.168.1.100
# The authenticity of host '192.168.1.100' can't be established.
# ED25519 key fingerprint is SHA256:xxxxx.
# Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
```

输入 `yes` 后，主机公钥会被记录到 `~/.ssh/known_hosts`，后续连接不再提示。如果远端主机重装系统导致公钥变化，会报错 `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!`，需用 `ssh-keygen -R 192.168.1.100` 清除旧记录。

### 8. 获取 Linux 环境的四种方式

| 方式 | 适合人群 | 优点 | 缺点 |
| --- | --- | --- | --- |
| WSL2 | Windows 用户 | 启动快、与 Windows 文件互通、资源占用低 | 非完整虚拟机，网络/ systemd 部分受限 |
| Docker 容器 | 有 Docker 环境 | 秒级启动、隔离干净、可多实例 | 无 systemd（默认），不适合练服务管理 |
| 虚拟机（VirtualBox/VMware） | 完整体验 | 完整系统、可练习磁盘分区/网络/内核 | 占用资源多、启动慢 |
| 云服务器 | 真实运维 | 真实公网 IP、可对外服务、完全生产体验 | 需付费、有安全风险 |

> 详细安装步骤见 `Code/README.md`。本教程推荐 Windows 用户使用 WSL2，已有 Docker 环境的用户用 Ubuntu 容器，需要完整体验的用虚拟机。

## 环境搭建

### 方式一：WSL2（Windows 用户推荐）

WSL2（Windows Subsystem for Linux 2）是微软提供的完整 Linux 内核虚拟化方案，性能接近原生，是 Windows 用户练习 Linux 的最佳选择。

```powershell
# 在 PowerShell（管理员）中执行
wsl --install -d Ubuntu-22.04

# 安装完成后重启，启动 Ubuntu 设置用户名密码
# Windows Terminal 会自动集成 WSL 入口

# 查看已安装的发行版
wsl -l -v

# 进入 WSL
wsl
```

### 方式二：Docker 容器

适合已安装 Docker 的用户，秒级启动、互不污染：

```bash
# 启动 Ubuntu 22.04 容器并挂载代码目录
docker run -it --name linux-learn \
  -v /path/to/Linux:/workspace \
  ubuntu:22.04 /bin/bash

# 退出后重新进入
docker start linux-learn
docker exec -it linux-learn /bin/bash

# 容器内安装基础工具
apt update && apt install -y tree vim curl wget git
```

### 方式三：虚拟机

完整体验，适合练习磁盘分区、内核编译、网络配置：

1. 下载 Ubuntu 22.04 LTS ISO：<https://ubuntu.com/download>
2. VirtualBox 或 VMware 新建虚拟机
3. 推荐配置：2 核 CPU / 2GB 内存 / 20GB 磁盘 / NAT 网卡
4. 安装时勾选 "Install OpenSSH server"

### 方式四：云服务器

真实运维环境，适合练习公网服务部署：

1. 阿里云 / 腾讯云 / AWS 购买 ECS / CVM / EC2
2. 选择 Ubuntu 22.04 LTS 镜像
3. 安全组放行 22 端口（SSH）
4. 用 `ssh root@公网IP` 连接
5. 立即创建普通用户并禁用 root 直连（安全实践，Day04 详解）

## 基本命令

### ls - 列出目录内容

```bash
ls                  # 列出当前目录文件（不显示隐藏文件）
ls -a               # 显示所有文件（含 . 开头的隐藏文件）
ls -l               # 长格式（权限、链接数、所有者、大小、修改时间）
ls -la              # 等同 -l -a 组合
ls -lh              # 文件大小人类可读（K/M/G）
ls -lt              # 按修改时间倒序
ls -lrt             # 按修改时间正序（最旧的在最后）
ls -lS              # 按文件大小排序
ls -R               # 递归列出子目录
ls -li              # 显示 inode 号
ls /etc /tmp        # 同时列出多个目录
ls *.sh             # 通配符：列出所有 .sh 文件
```

### cd - 切换目录

```bash
cd /opt/ecommerce   # 切换到绝对路径
cd backend          # 切换到相对路径（当前目录下的 backend）
cd ..               # 切换到上级目录
cd .                # 当前目录（很少单独用）
cd ~                # 切换到家目录
cd                  # 不带参数等同 cd ~
cd -                # 切换到上一次所在的目录
cd ~/scripts        # 家目录下的 scripts
```

### pwd - 显示当前目录

```bash
pwd                 # 显示当前工作目录的绝对路径
pwd -P              # 显示物理路径（解析软链接）
pwd -L              # 显示逻辑路径（默认，保留软链接）
```

### mkdir - 创建目录

```bash
mkdir logs          # 创建单个目录
mkdir logs scripts backup   # 同时创建多个
mkdir -p a/b/c/d    # 递归创建多级目录（父目录不存在时自动创建）
mkdir -m 700 secret # 创建时指定权限
mkdir -v test       # 显示创建信息
```

### rmdir - 删除空目录

```bash
rmdir emptydir      # 只能删除空目录，非空会报错
rmdir -p a/b/c      # 递归删除空的父目录链
```

> 删除非空目录用 `rm -r`。

### rm - 删除文件或目录

```bash
rm file.txt             # 删除文件
rm -i file.txt          # 交互式确认（防止误删）
rm -f file.txt          # 强制删除（不存在也不报错）
rm -r dir               # 递归删除目录及其内容
rm -rf dir              # 强制递归删除（危险！不可恢复）
rm *.log                # 删除所有 .log 文件
rm -- -file.txt         # 删除以 - 开头的文件（-- 表示参数结束）
```

> ⚠️ `rm -rf` 是 Linux 最危险的命令之一，执行前务必确认路径，严禁 `rm -rf /` 或 `rm -rf $UNDEFINED_VAR/`。

### cp - 复制

```bash
cp file.txt file.bak            # 复制文件
cp -i file.txt file.bak         # 目标存在时提示确认
cp -v file.txt /tmp/            # 显示复制过程
cp -r dir /tmp/                 # 递归复制目录
cp -a dir /tmp/                 # 归档模式（保留权限、链接、时间戳）
cp file1 file2 dir/             # 多个文件复制到目录
cp -u src dest                  # 仅当源比目标新或目标不存在时才复制
```

### mv - 移动 / 重命名

```bash
mv old.txt new.txt              # 重命名
mv file.txt /tmp/               # 移动到 /tmp
mv -i file.txt /tmp/            # 目标存在时确认
mv -v file.txt /tmp/            # 显示过程
mv file1 file2 dir/             # 多个文件移动到目录
mv -u src dest                  # 仅当源比目标新时才覆盖
```

### touch - 创建空文件 / 更新时间戳

```bash
touch newfile.txt           # 文件不存在则创建空文件
touch existing.txt          # 文件已存在则更新访问/修改时间
touch -t 202401010000 file  # 设置为指定时间（YYYYMMDDHHMM）
touch -a file               # 仅更新访问时间
touch -m file               # 仅更新修改时间
touch file{1..5}.txt        # 批量创建 file1.txt 到 file5.txt
```

## 命令帮助

Linux 命令数以千计，没有人能全部记住，**学会查帮助比死记硬背更重要**：

```bash
# man - 最权威的手册（manual）
man ls                      # 查看 ls 的手册
man 1 crontab               # 第 1 章：用户命令
man 5 crontab               # 第 5 章：配置文件格式
man -k password             # 关键词搜索（等同 apropos）

# 常用 man 章节
# 1 - 用户命令（ls/cat/cp）
# 2 - 系统调用（open/read/write）
# 3 - 库函数（printf/malloc）
# 4 - 设备文件（/dev/null、/dev/sda）
# 5 - 配置文件格式（/etc/passwd、crontab）
# 8 - 管理员命令（useradd/systemctl）

# info - GNU 的超文本手册（比 man 更详细）
info coreutils              # 查看 coreutils 命令集
info ls

# --help - 快速查看选项（最常用）
ls --help
grep --help

# whatis - 一句话简介
whatis ls
# ls (1) - list directory contents

# tldr - 社区维护的简明示例（需安装：apt install tldr）
tldr tar                    # 给出 tar 最常用示例
```

## history 与命令补全

### history - 命令历史

```bash
history                 # 查看历史命令列表
history 20              # 查看最近 20 条
!100                    # 执行第 100 条历史命令
!!                      # 执行上一条命令（常用于 sudo !!）
!ls                     # 执行最近一条以 ls 开头的命令
!$                      # 上一条命令的最后一个参数
!!:gs/old/new           # 上一条命令中的 old 替换为 new 再执行
history -c              # 清空当前会话历史
```

### Tab 补全

按一次 Tab 自动补全命令或路径；如果有多条匹配，按两次 Tab 列出所有候选：

```bash
cd /o[Tab]              # 补全为 cd /opt/
cd /opt/ec[Tab][Tab]    # 若 ecommerce 是唯一匹配则补全，否则列出候选
system[Tab]             # 补全 systemctl
```

补全不仅对命令和路径有效，`bash-completion` 包还能补全 `systemctl`、`apt`、`git` 等命令的子参数。

### Ctrl+R 搜索历史

```bash
# 按 Ctrl+R 后输入关键词，反向搜索历史命令
(reverse-i-search)`nginx': systemctl restart nginx
# 按 → 编辑该命令，按 Enter 直接执行，按 Ctrl+R 继续向前搜索
```

## 关键知识点总结

### Ubuntu vs CentOS 对比表（速查）

| 维度 | Ubuntu | CentOS / Rocky |
| --- | --- | --- |
| 包管理 | `apt install` | `dnf install` |
| 包格式 | `.deb` | `.rpm` |
| 防火墙 | `ufw` | `firewalld` |
| 服务管理 | `systemctl` | `systemctl` |
| 默认文件系统 | ext4 | xfs |
| 网络配置 | Netplan | NetworkManager |
| SELinux | AppArmor | SELinux enforcing |
| 适用场景 | 开发/云/Docker | 企业生产 |

### 基本命令速查表

| 命令 | 作用 | 常用选项 | 示例 |
| --- | --- | --- | --- |
| `ls` | 列出目录 | `-l -a -h -t -R` | `ls -lah /tmp` |
| `cd` | 切换目录 | `-` `~` | `cd -` |
| `pwd` | 显示当前目录 | `-P` | `pwd` |
| `mkdir` | 创建目录 | `-p -m` | `mkdir -p a/b/c` |
| `rmdir` | 删除空目录 | `-p` | `rmdir empty` |
| `rm` | 删除 | `-r -f -i` | `rm -rf dir` |
| `cp` | 复制 | `-r -i -v -a` | `cp -r dir /tmp` |
| `mv` | 移动/重命名 | `-i -v -u` | `mv old new` |
| `touch` | 创建空文件 | `-t -a -m` | `touch f.txt` |
| `man` | 查手册 | `1 5 8 -k` | `man 5 passwd` |
| `history` | 历史命令 | `-c` | `!100` `!!` |

### 终端快捷键表

| 快捷键 | 功能 |
| --- | --- |
| `Ctrl + C` | 终止当前命令 |
| `Ctrl + Z` | 挂起到后台 |
| `Ctrl + D` | 发送 EOF（退出 Shell / 退出登录） |
| `Ctrl + L` | 清屏（等同 `clear`） |
| `Ctrl + R` | 反向搜索历史命令 |
| `Ctrl + A` | 光标移到行首 |
| `Ctrl + E` | 光标移到行尾 |
| `Ctrl + W` | 删除光标前一个单词 |
| `Ctrl + U` | 删除光标前到行首 |
| `Ctrl + K` | 删除光标到行尾 |
| `Ctrl + Y` | 粘贴 Ctrl+W/U/K 删除的内容 |
| `Tab` | 自动补全（一次） / 列出候选（两次） |
| `↑` / `↓` | 翻看上一条 / 下一条历史 |
| `!!` | 执行上一条命令 |
| `!$` | 上一条命令最后一个参数 |

## 代码文件说明

| 文件 | 用途 | 执行方式 |
| --- | --- | --- |
| `Code/01-environment-setup.sh` | 环境初始化：更新系统、装基础工具、设时区、配 vim、建项目目录 | `sudo bash 01-environment-setup.sh` |
| `Code/02-basic-commands.sh` | 基础命令练习：ls/cd/pwd/mkdir/touch/cp/mv/rm | `bash 02-basic-commands.sh` |
| `Code/README.md` | 环境配置详细指南（WSL2 / Docker / 虚拟机 / 云服务器 / SSH / 终端工具） | 阅读文档 |

## 实战练习

### 练习一：搭建练习环境并验证

1. 用任一方式（WSL2 / Docker / 虚拟机）启动 Ubuntu 22.04
2. 执行 `Code/01-environment-setup.sh` 完成环境初始化
3. 验证：
   - `timedatectl` 显示时区为 `Asia/Shanghai`
   - `tree -L 2 /opt/ecommerce/` 显示四个子目录
   - `vim --version` 显示已安装
   - `htop` 可启动（按 q 退出）

### 练习二：基础命令综合练习

在 `/tmp/practice/` 下完成以下操作（执行 `Code/02-basic-commands.sh` 后再做一遍）：

```bash
# 1. 创建如下目录树
# /tmp/practice/
# ├── backend/
# │   ├── src/
# │   └── test/
# ├── frontend/
# │   ├── src/
# │   └── dist/
# └── docs/
mkdir -p /tmp/practice/{backend/{src,test},frontend/{src,dist},docs}

# 2. 在各 src 下创建文件
touch /tmp/practice/backend/src/{app.js,utils.js}
touch /tmp/practice/frontend/src/{index.html,main.js}

# 3. 复制 backend/src/app.js 到 docs/ 改名为 app.bak.js
cp /tmp/practice/backend/src/app.js /tmp/practice/docs/app.bak.js

# 4. 把 frontend/src/main.js 移动到 frontend/dist/
mv /tmp/practice/frontend/src/main.js /tmp/practice/frontend/dist/

# 5. 用 ls -R 显示整个目录树
ls -R /tmp/practice/

# 6. 清理：删除整个 practice 目录
rm -rf /tmp/practice/
```

### 练习三：SSH 连接与配置

准备两台 Linux 环境（或一台云服务器 + 本地 WSL）：

1. 在本地生成 SSH 密钥对：`ssh-keygen -t ed25519 -C "deploy@local"`
2. 用 `ssh-copy-id` 把公钥传到远端：`ssh-copy-id deploy@192.168.1.100`
3. 配置 `~/.ssh/config`，给远端起别名 `ecommerce`
4. 用 `ssh ecommerce` 免密登录
5. 登录后执行 `hostname`、`uname -a`、`lsb_release -a` 查看系统信息
6. 用 `man 5 ssh_config` 查阅 SSH 配置文件选项，尝试在 config 中添加 `ServerAliveInterval 60`
