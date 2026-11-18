# Day01 Code - 环境配置详细指南

本文件提供 Linux 学习环境的四种搭建方式的详细步骤，以及 SSH 配置与终端工具推荐。任选一种方式即可开始学习，推荐 Windows 用户使用 WSL2。

---

## 目录

- [方式一：WSL2（Windows 用户推荐）](#方式一wsl2windows-用户推荐)
- [方式二：Docker 容器](#方式二docker-容器)
- [方式三：虚拟机（VirtualBox / VMware）](#方式三虚拟机virtualbox--vmware)
- [方式四：云服务器](#方式四云服务器)
- [SSH 配置详解](#ssh-配置详解)
- [终端工具推荐](#终端工具推荐)
- [换行符与编码问题](#换行符与编码问题)

---

## 方式一：WSL2（Windows 用户推荐）

WSL2 是 Windows Subsystem for Linux 2 的缩写，是微软提供的完整 Linux 内核虚拟化方案。相比 WSL1，WSL2 使用真正的 Linux 内核，兼容性接近原生虚拟机，性能更高。

### 前置要求

- Windows 10 版本 2004（Build 19041）及以上，或 Windows 11
- 启用虚拟化（BIOS 中开启 VT-x / AMD-V）
- 至少 4GB 内存

### 安装步骤

#### 1. 启用 WSL 与虚拟机平台功能

以**管理员身份**打开 PowerShell，执行：

```powershell
# 一键安装（Windows 10 2004+ / Windows 11）
wsl --install

# 该命令会自动：
# - 启用"虚拟机平台"功能
# - 启用"适用于 Linux 的 Windows 子系统"功能
# - 下载并安装 Linux 内核
# - 将 WSL 默认版本设为 2
# - 安装默认发行版（Ubuntu）
```

如果 `wsl --install` 不可用（旧版 Windows），手动启用：

```powershell
# 启用 WSL 功能
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 启用虚拟机平台
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 重启电脑
shutdown /r /t 0

# 重启后，下载并安装 WSL2 内核更新包：
# https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi

# 将 WSL 默认版本设为 2
wsl --set-default-version 2
```

#### 2. 安装 Ubuntu 22.04

```powershell
# 列出可用的发行版
wsl --list --online

# 安装 Ubuntu 22.04
wsl --install -d Ubuntu-22.04

# 查看已安装的发行版及其版本
wsl --list --verbose
# 输出示例：
#   NAME            STATE           VERSION
#   Ubuntu-22.04    Running         2
```

#### 3. 初始化用户

安装完成后，Ubuntu 会自动启动（或从开始菜单启动），首次启动需设置用户名和密码：

```bash
# 首次启动会提示：
# Enter new UNIX username: deploy
# New password: ********
# Retype new password: ********

# 设置完成后进入 Shell
whoami        # deploy
pwd           # /home/deploy
```

#### 4. 常用 WSL 命令

```powershell
# 在 PowerShell 中执行
wsl                       # 进入默认发行版
wsl -d Ubuntu-22.04       # 进入指定发行版
wsl --list --verbose      # 查看所有发行版及状态
wsl --set-default Ubuntu-22.04   # 设置默认发行版
wsl --shutdown            # 关闭所有 WSL 实例
wsl --terminate Ubuntu-22.04     # 关闭指定实例
wsl --update              # 更新 WSL 内核
wsl --status              # 查看WSL状态
```

#### 5. WSL 与 Windows 文件互通

```bash
# 在 WSL 中访问 Windows 文件（C 盘）
ls /mnt/c/Users/
cd /mnt/c/Users/YourName/Desktop

# 在 Windows 中访问 WSL 文件
# 资源管理器地址栏输入：
\\wsl$\Ubuntu-22.04\home\deploy
# 或
\\wsl.localhost\Ubuntu-22.04\home\deploy
```

#### 6. 配置 VS Code 集成

```bash
# 在 WSL 中安装 code 命令
# （VS Code 会自动检测并提示安装）
code .

# 或在 Windows 的 VS Code 中安装 "WSL" 扩展
# 然后按 F1 → "WSL: Connect to WSL"
```

#### 7. WSL2 资源限制

WSL2 默认会占用较多内存，可通过 `.wslconfig` 限制：

```ini
# 文件位置：C:\Users\YourName\.wslconfig
[wsl2]
memory=4GB
processors=2
swap=2GB
localhostForwarding=true
```

修改后执行 `wsl --shutdown` 再重启 WSL 生效。

### WSL2 注意事项

- WSL2 默认不启动 systemd（Ubuntu 22.04 可手动开启），如需练习 `systemctl`：
  ```ini
  # /etc/wsl.conf
  [boot]
  systemd=true
  ```
  修改后 `wsl --shutdown` 重启生效。
- 网络方面 WSL2 使用 NAT 模式，localhost 可双向访问，但局域网其他机器默认访问不到 WSL 内的服务（需端口转发）。
- 跨文件系统操作（在 WSL 中操作 `/mnt/c/`）性能较差，建议项目代码放在 WSL 文件系统（`/home/` 下）。

---

## 方式二：Docker 容器

适合已安装 Docker 的用户，秒级启动、互不污染、可同时跑多个实例。

### 前置要求

- 已安装 Docker（Windows 用 Docker Desktop，Linux 用 `apt install docker.io`）

### 启动 Ubuntu 练习容器

```bash
# 启动一个 Ubuntu 22.04 容器，并挂载本地代码目录
# Windows PowerShell（路径用 Windows 格式）：
docker run -it --name linux-learn `
  -v D:\Coding\AI-FullStack\Linux:/workspace `
  ubuntu:22.04 /bin/bash

# Linux / macOS：
docker run -it --name linux-learn \
  -v /path/to/Linux:/workspace \
  ubuntu:22.04 /bin/bash

# 进入容器后先更新系统并安装基础工具
apt update && apt install -y sudo vim tree curl wget git
```

### 容器管理常用命令

```bash
# 退出容器（容器会停止）
exit

# 重新启动已停止的容器
docker start linux-learn

# 进入正在运行的容器
docker exec -it linux-learn /bin/bash

# 查看所有容器（含已停止的）
docker ps -a

# 删除容器
docker rm -f linux-learn

# 删除镜像
docker rmi ubuntu:22.04
```

### 让容器支持 sudo 与 systemd

默认 Ubuntu 容器没有 sudo，也没有 systemd。如需练习用户管理：

```bash
# 安装 sudo
apt update && apt install -y sudo

# 创建一个普通用户并加入 sudo 组
useradd -m -s /bin/bash deploy
echo "deploy:deploy" | chpasswd
usermod -aG sudo deploy

# 切换到普通用户
su - deploy
```

如需练习 systemd（不推荐在容器中），需以特权模式启动：

```bash
docker run -it --name linux-systemd \
  --privileged \
  -v /sys/fs/cgroup:/sys/fs/cgroup \
  jrei/systemd-ubuntu:22.04
```

---

## 方式三：虚拟机（VirtualBox / VMware）

适合需要完整 Linux 体验的场景，可练习磁盘分区、内核编译、网络配置。

### 前置要求

- 主机至少 8GB 内存（推荐 16GB）
- BIOS 开启虚拟化（VT-x / AMD-V）
- 20GB 以上空闲磁盘空间

### 安装步骤

#### 1. 下载 Ubuntu ISO

- 官网：<https://ubuntu.com/download/desktop>（桌面版，带图形界面）
- 服务器版：<https://ubuntu.com/download/server>（无图形界面，更轻量）
- 推荐 Ubuntu 22.04 LTS Desktop ISO（约 4.7GB）

#### 2. 安装虚拟机软件

- **VirtualBox**（免费）：<https://www.virtualbox.org/>
- **VMware Workstation Player**（个人免费）：<https://www.vmware.com/products/workstation-player.html>

#### 3. 创建虚拟机

推荐配置：

| 配置项 | 推荐值 | 说明 |
| --- | --- | --- |
| CPU | 2 核 | 练习足够 |
| 内存 | 2GB（最低）/ 4GB（推荐） | 内存大些更流畅 |
| 磁盘 | 30GB | 动态分配 |
| 网卡 | NAT | 最简单，可上网 |
| 显存 | 16MB | 桌面版需要 |

#### 4. 安装 Ubuntu

1. 在虚拟机软件中新建虚拟机，选择下载的 ISO 文件作为启动盘
2. 启动虚拟机，按提示安装
3. 安装时勾选：
   - ✅ Download updates while installing Ubuntu
   - ✅ Install third-party software
   - ✅ **Install OpenSSH server**（重要，方便 SSH 连接）
4. 安装完成后重启，移除 ISO

#### 5. 配置 SSH 远程连接

虚拟机中以 NAT 网卡模式启动后，需配置端口转发才能从主机 SSH 进虚拟机：

**VirtualBox 端口转发**：

1. 虚拟机设置 → 网络 → 高级 → 端口转发
2. 添加规则：主机端口 2222 → 子系统端口 22

```bash
# 主机终端执行
ssh -p 2222 deploy@127.0.0.1
```

**桥接模式**（虚拟机直接获取局域网 IP）：

1. 虚拟机设置 → 网络 → 网卡连接方式改为"桥接网卡"
2. 在虚拟机内执行 `ip addr` 获取 IP（如 192.168.1.x）
3. 主机直接 `ssh deploy@192.168.1.x`

#### 6. 安装增强功能（VirtualBox Guest Additions）

```bash
# VirtualBox 菜单 → 设备 → 安装增强功能
# 然后在虚拟机中执行：
sudo apt update
sudo apt install -y build-essential dkms linux-headers-$(uname -r)
sudo mount /dev/cdrom /media/cdrom
sudo /media/cdrom/VBoxLinuxAdditions.run
sudo reboot

# 增强功能提供：
# - 共享剪贴板
# - 拖放文件
# - 自适应分辨率
# - 共享文件夹
```

### 共享文件夹

```bash
# VirtualBox 设置 → 共享文件夹 → 添加主机文件夹
# 勾选"自动挂载"和"固定分配"
# 虚拟机中访问：
ls /media/sf_SharedFolder/

# 加入 vboxsf 组以获得访问权限
sudo usermod -aG vboxsf $USER
# 重新登录生效
```

---

## 方式四：云服务器

真实运维环境，适合练习公网服务部署、安全加固。

### 选择云厂商

| 厂商 | 适合人群 | 价格 | 特点 |
| --- | --- | --- | --- |
| 阿里云 ECS | 国内用户 | 学生 9.5 元/月起 | 中文文档全、网络快 |
| 腾讯云 CVM | 国内用户 | 学生 10 元/月起 | 首单优惠多 |
| 华为云 ECS | 企业用户 | 中等 | 政企合规 |
| AWS EC2 | 海外/学习 | 免费 12 个月（t2.micro） | 全球节点、生态丰富 |
| Vultr / DigitalOcean | 海外 | $5/月起 | 按小时计费、随时销毁 |

### 购买与连接步骤

#### 1. 购买服务器

- 地域：选离你近的（国内选华东 1、华北 2）
- 镜像：Ubuntu 22.04 LTS 64 位
- 实例规格：1 核 2GB（学习足够）
- 系统盘：40GB 高效云盘
- 带宽：1Mbps 按量计费（便宜）或 5Mbps 固定带宽
- 安全组：放行 22（SSH）、80（HTTP）、443（HTTPS）

#### 2. 配置 SSH 密钥对（推荐）

- 在云控制台创建密钥对，下载私钥 `.pem` 文件
- 绑定密钥对到实例
- 用密钥登录（无需密码）：

```bash
# 修改私钥文件权限（必须，否则 SSH 拒绝使用）
chmod 400 your-key.pem

# 用私钥登录
ssh -i your-key.pem ubuntu@公网IP
```

> 阿里云 Ubuntu 镜像默认用户是 `ubuntu`，腾讯云也是 `ubuntu`，AWS EC2 也是 `ubuntu`。root 用户默认禁用 SSH 登录。

#### 3. 首次登录后的初始化

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 设置时区
sudo timedatectl set-timezone Asia/Shanghai

# 创建部署用户（如不存在）
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy
sudo passwd deploy

# 配置 SSH 密钥登录 deploy 用户
sudo mkdir -p /home/deploy/.ssh
sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys

# 切换到 deploy 用户
sudo su - deploy
```

#### 4. 安全加固（Day13 详解）

```bash
# 修改 SSH 默认端口（如改为 22222）
sudo vim /etc/ssh/sshd_config
# 修改 Port 22 → Port 22222

# 禁用 root 直连
# PermitRootLogin no

# 禁用密码登录（仅密钥登录）
# PasswordAuthentication no

# 重启 SSH 服务
sudo systemctl restart sshd

# 之后连接需指定端口
ssh -p 22222 deploy@公网IP
```

### 云服务器成本控制

- 学习用选按量付费，用完释放
- 用快照备份数据，方便随时恢复
- 关注厂商活动，学生认证有大幅优惠

---

## SSH 配置详解

### SSH 客户端配置文件

`~/.ssh/config` 文件可以预定义连接参数，简化 SSH 命令：

```ssh-config
# ~/.ssh/config
# 文件权限必须为 600：chmod 600 ~/.ssh/config

# 电商项目主服务器
Host ecommerce
    HostName 192.168.1.100
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3

# 数据库服务器
Host db
    HostName 10.0.0.20
    User root
    Port 2222
    IdentityFile ~/.ssh/id_rsa

# 跳板机配置
Host jump
    HostName jump.example.com
    User deploy

# 通过跳板机连接内网服务器
Host internal
    HostName 192.168.10.100
    User deploy
    ProxyJump jump
```

配置完成后：

```bash
# 直接用别名连接
ssh ecommerce

# scp 也可用别名
scp file.txt ecommerce:/tmp/

# rsync 也可用别名
rsync -avz ./project/ ecommerce:/opt/ecommerce/backend/
```

### SSH 密钥管理

```bash
# 生成 ed25519 密钥（推荐，更安全更快）
ssh-keygen -t ed25519 -C "deploy@local"

# 生成 RSA 密钥（兼容性最好，4096 位）
ssh-keygen -t rsa -b 4096 -C "deploy@local"

# 指定密钥文件路径
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_github -C "github"

# 查看密钥指纹
ssh-keygen -lf ~/.ssh/id_ed25519.pub

# 把公钥传到远程服务器
ssh-copy-id deploy@192.168.1.100
ssh-copy-id -i ~/.ssh/id_ed25519.pub deploy@192.168.1.100
ssh-copy-id -p 2222 deploy@192.168.1.100

# 手动添加公钥（如 ssh-copy-id 不可用）
cat ~/.ssh/id_ed25519.pub | ssh deploy@192.168.1.100 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### SSH 文件权限要求

```
~/.ssh/                   700
~/.ssh/id_*              600  (私钥)
~/.ssh/id_*.pub          644  (公钥)
~/.ssh/authorized_keys   600
~/.ssh/known_hosts       644
~/.ssh/config            600
```

权限不对是 SSH 拒绝登录的最常见原因。

### SSH 端口转发

```bash
# 本地端口转发（访问本地 8080 等同于访问远程 80）
ssh -L 8080:localhost:80 deploy@192.168.1.100
# 浏览器访问 http://localhost:8080 即可访问远程 Nginx

# 远程端口转发（让远程能访问本地服务）
ssh -R 9090:localhost:3000 deploy@192.168.1.100
# 远程访问 localhost:9090 等同于访问本地 3000

# 动态端口转发（SOCKS5 代理）
ssh -D 1080 deploy@192.168.1.100
# 浏览器设置 SOCKS5 代理 127.0.0.1:1080

# 后台运行端口转发
ssh -fNL 8080:localhost:80 deploy@192.168.1.100
```

### scp 与 rsync 文件传输

```bash
# scp 简单文件传输
scp file.txt deploy@192.168.1.100:/tmp/                    # 上传
scp deploy@192.168.1.100:/var/log/syslog ./                # 下载
scp -r directory deploy@192.168.1.100:/tmp/                # 递归上传目录
scp -P 2222 file.txt deploy@192.168.1.100:/tmp/            # 指定端口（大写 P）

# rsync 增量同步（更高效，支持断点续传）
rsync -avz ./project/ deploy@192.168.1.100:/opt/ecommerce/backend/
# -a 归档模式（保留权限/时间/软链接等）
# -v 显示过程
# -z 压缩传输
# --delete 删除目标中源已不存在的文件（谨慎使用）
# --exclude 排除文件
rsync -avz --exclude='node_modules' --exclude='.git' \
  ./project/ deploy@192.168.1.100:/opt/ecommerce/backend/
```

---

## 终端工具推荐

### Windows

| 工具 | 特点 | 价格 |
| --- | --- | --- |
| **Windows Terminal** | 微软官方、多标签、支持 WSL/PowerShell/CMD | 免费 |
| **Tabby** | 跨平台、颜值高、插件丰富 | 免费 |
| **Xshell** | 老牌 SSH 客户端、会话管理强 | 个人免费 |
| **MobaXterm** | 内置 X Server、SFTP、一键工具集 | 个人免费 |
| **PuTTY** | 最经典、轻量、功能基础 | 免费 |
| **Termius** | 跨平台、云同步、移动端可用 | 免费/付费 |

### macOS

| 工具 | 特点 | 价格 |
| --- | --- | --- |
| **iTerm2** | macOS 终端王者、分屏、热键、配色 | 免费 |
| **Terminal.app** | 系统自带、够用 | 免费 |
| **Warp** | AI 加持、现代化设计 | 免费/付费 |

### Linux

| 工具 | 特点 |
| --- | --- |
| **GNOME Terminal** | Ubuntu 默认 |
| **Konsole** | KDE 默认 |
| **Terminator** | 分屏神器 |
| **Alacritty** | GPU 加速、配置文件驱动 |
| **Kitty** | GPU 加速、支持图片显示 |
| **Tilix** | GTK3 分屏终端 |

### 跨平台终端复用器

| 工具 | 说明 |
| --- | --- |
| **tmux** | 终端复用器，断开 SSH 后进程不退出，会话恢复 |
| **screen** | 老牌终端复用器，功能比 tmux 少 |
| **Zellij** | 现代化终端复用器，开箱即用 |

> 强烈推荐学习 **tmux**，远程服务器长时间任务必备。基本用法：`tmux` 新建会话、`Ctrl+B D` 脱离、`tmux attach` 恢复。

### Oh My Zsh（可选美化）

```bash
# 安装 zsh
sudo apt install -y zsh

# 安装 Oh My Zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# 切换默认 Shell 为 zsh
chsh -s $(which zsh)

# 推荐主题：agnoster / powerlevel10k
# 推荐插件：git / z / autosuggestions / syntax-highlighting
```

---

## 换行符与编码问题

### Windows 与 Linux 换行符差异

- Windows：`CRLF`（`\r\n`）—— 回车 + 换行
- Linux/macOS：`LF`（`\n`）—— 仅换行

在 Windows 编辑的 Shell 脚本直接传到 Linux 执行会报错：

```bash
bash: ./script.sh: /bin/bash^M: bad interpreter: No such file or directory
```

### 解决方案

#### 方案一：用 dos2unix 转换

```bash
# 安装
sudo apt install -y dos2unix

# 转换
dos2unix script.sh

# 批量转换
dos2unix *.sh
```

#### 方案二：用 sed 转换

```bash
# 去除所有 \r
sed -i 's/\r$//' script.sh
```

#### 方案三：在 VS Code 中设置

1. 打开文件
2. 右下角点击 "CRLF" → 切换为 "LF"
3. 全局设置：`Settings → Files: Eol → \n`

#### 方案四：用 .gitattributes 统一

```
# .gitattributes
*.sh text eol=lf
*.py text eol=lf
*.conf text eol=lf
```

### 文件编码

- 推荐：UTF-8（无 BOM）
- Windows 记事本默认可能是 GBK 或 UTF-8 with BOM
- 用 VS Code 编辑时确认右下角编码为 "UTF-8"

```bash
# 查看文件编码
file -i script.sh

# 转换编码（如 GBK → UTF-8）
iconv -f GBK -t UTF-8 input.sh -o output.sh
```

---

## 环境验证清单

完成环境搭建后，执行以下命令验证：

```bash
# 1. 系统版本
lsb_release -a
# 期望：Ubuntu 22.04 LTS

# 2. 内核版本
uname -r
# 期望：5.15 或更高

# 3. 当前用户
whoami
# 期望：非 root（推荐用普通用户 + sudo）

# 4. 磁盘空间
df -h /
# 期望：至少 10GB 可用

# 5. 内存
free -h
# 期望：至少 1GB

# 6. 网络
ping -c 3 8.8.8.8
# 期望：能 ping 通

# 7. 软件源
sudo apt update
# 期望：无错误

# 8. 时区
timedatectl
# 期望：Asia/Shanghai

# 9. 基础工具
which tree vim curl wget git
# 期望：都能找到路径

# 10. 执行环境初始化脚本
sudo bash /workspace/Day01\ -\ Linux基础与环境安装/Code/01-environment-setup.sh
# 期望：脚本顺利执行完成
```

全部通过后，即可开始 Day01 的学习！
