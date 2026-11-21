# Day13 - 防火墙与安全加固

安全是服务器的生命线。一台暴露在公网的服务器，平均几分钟就会收到第一次扫描探测，几小时内可能遭遇暴力破解尝试。如果没有防火墙限制端口、没有 SSH 加固、没有入侵检测，数据库被脱库、服务器被植入挖矿程序只是时间问题。本章系统讲解 Linux 防火墙（ufw / firewalld / iptables / nftables）的配置方法，SSH 服务安全加固策略，fail2ban 防暴力破解机制，以及系统级安全检查清单，帮你构筑服务器的多层安全防线。

---

## 学习目标

完成本章学习后，你应能够：

- 理解防火墙的基本概念：包过滤、状态检测、NAT、四表五链
- 熟练使用 `ufw` 配置 Ubuntu 防火墙规则（allow/deny/来源限制）
- 掌握 `firewalld` 的 zone 概念与 `firewall-cmd` 命令（CentOS 环境）
- 了解 `iptables` / `nftables` 底层框架与四表五链
- 对比 ufw / firewalld / iptables 的差异与适用场景
- 完成 SSH 服务安全加固（改端口、禁 root、禁密码、密钥认证、限用户）
- 部署 `fail2ban` 防止 SSH 暴力破解
- 了解 SELinux / AppArmor 强制访问控制机制
- 执行系统安全检查清单（最小化安装、关闭无用服务、端口扫描、审计）
- 为电商服务器制定完整的安全加固方案

---

## 理论知识讲解

### 一、防火墙基础

#### 1.1 防火墙概念

| 概念 | 说明 |
|------|------|
| **包过滤（Packet Filtering）** | 根据源 IP、目标 IP、端口、协议过滤数据包 |
| **状态检测（Stateful Inspection）** | 跟踪连接状态（NEW/ESTABLISHED/RELATED），允许已建立连接的回包 |
| **NAT（网络地址转换）** | 修改数据包的源/目标地址，实现端口映射、IP 伪装 |

#### 1.2 iptables / nftables 底层框架

Linux 防火墙底层是 **Netfilter** 内核框架，用户态工具经历了 `iptables` → `nftables` 的演进。

**四表（Table）**：处理不同类型规则

| 表 | 作用 | 常用度 |
|----|------|--------|
| `filter` | 包过滤（默认表） | 最常用 |
| `nat` | 地址转换（DNAT/SNAT/端口映射） | 常用 |
| `mangle` | 修改数据包（TOS/TTL/MARK） | 少用 |
| `raw` | 在连接追踪前处理（跳过状态检测） | 极少用 |

**五链（Chain）**：数据包经过的处理点

| 链 | 触发时机 | 典型用途 |
|----|---------|---------|
| `INPUT` | 数据包到达本机 | 入站过滤 |
| `OUTPUT` | 数据包从本机发出 | 出站过滤 |
| `FORWARD` | 数据包经过本机转发 | 路由器/网关 |
| `PREROUTING` | 路由前（DNAT） | 端口映射 |
| `POSTROUTING` | 路由后（SNAT） | IP 伪装 |

**数据包流向**：

```
                    ┌─────────────────────┐
   入站数据包 ─────→ │ PREROUTING (raw/mangle/nat) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    路由判断          │
                    └──┬───────────────┬──┘
                       │               │
              目标是本机│               │需转发
                       ▼               ▼
              ┌─────────────┐  ┌──────────────┐
              │ INPUT       │  │ FORWARD      │
              │ (mangle/    │  │ (mangle/     │
              │  filter)    │  │  filter)     │
              └──────┬──────┘  └──────┬───────┘
                     │                │
              ┌──────▼──────┐  ┌──────▼───────┐
              │ 本机应用     │  │ POSTROUTING  │
              └──────┬──────┘  │ (mangle/nat) │
                     │         └──────────────┘
              ┌──────▼──────┐
              │ OUTPUT      │
              │ (raw/mangle/│
              │  nat/filter)│
              └─────────────┘
```

---

### 二、ufw（Ubuntu 默认防火墙）

`ufw`（Uncomplicated Firewall）是 Ubuntu 默认的防火墙前端工具，语法简洁，底层调用 iptables。

#### 2.1 基础命令

```bash
# 启用防火墙（注意：启用前确保 SSH 端口已放行，否则会断连！）
sudo ufw enable

# 禁用防火墙
sudo ufw disable

# 查看防火墙状态
sudo ufw status

# 查看详细状态
sudo ufw status verbose

# 重置防火墙（清除所有规则）
sudo ufw reset

# 重新加载规则
sudo ufw reload
```

#### 2.2 默认策略

```bash
# 设置默认策略：拒绝所有入站，允许所有出站
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

#### 2.3 放行与拒绝规则

```bash
# 放行端口（指定协议）
sudo ufw allow 80/tcp        # HTTP
sudo ufw allow 443/tcp       # HTTPS
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 2222/tcp      # 自定义 SSH 端口

# 放行端口范围（需指定协议）
sudo ufw allow 3000:3100/tcp # Node.js 多实例

# 放行服务名（基于 /etc/services）
sudo ufw allow http
sudo ufw allow https
sudo ufw allow ssh

# 拒绝端口（阻止外部访问）
sudo ufw deny 3306           # 拒绝外部访问 MySQL
sudo ufw deny 6379           # 拒绝外部访问 Redis

# 来源 IP 限制（只允许内网访问数据库）
sudo ufw allow from 192.168.1.0/24 to any port 3306
sudo ufw allow from 192.168.1.0/24 to any port 6379

# 来源 IP 限制到指定端口
sudo ufw allow from 192.168.1.50 to any port 22
```

#### 2.4 删除规则

```bash
# 方式一：按规则语法删除
sudo ufw delete allow 80/tcp
sudo ufw delete deny 3306

# 方式二：按编号删除（推荐）
sudo ufw status numbered      # 查看规则编号
sudo ufw delete 3             # 删除第 3 条规则
```

#### 2.5 应用配置文件

`ufw` 支持基于应用配置文件管理规则，配置文件位于 `/etc/ufw/applications.d/`。

```bash
# 查看可用应用配置
sudo ufw app list

# 查看应用配置详情
sudo ufw app info "Nginx Full"

# 基于应用放行
sudo ufw allow "Nginx Full"
sudo ufw allow "OpenSSH"
```

**自定义应用配置示例**：

```bash
# 创建电商应用配置文件
sudo tee /etc/ufw/applications.d/ecommerce <<'EOF'
[Ecommerce]
title=Ecommerce Web Service
description=Ecommerce full stack (HTTP, HTTPS, SSH)
ports=80,443,22/tcp

[EcommerceInternal]
title=Ecommerce Internal Service
description=Ecommerce internal (MySQL, Redis) - only for internal access
ports=3306,6379/tcp
EOF

# 重新加载并应用
sudo ufw app update Ecommerce
sudo ufw allow Ecommerce
```

---

### 三、firewalld（CentOS/RHEL 默认防火墙）

`firewalld` 是 CentOS/RHEL/Rocky Linux 默认的防火墙管理工具，基于 zone（区域）概念。

#### 3.1 zone 概念

zone 是一组预定义的信任级别规则，不同网络环境使用不同 zone。

| zone | 信任级别 | 适用场景 |
|------|---------|---------|
| `drop` | 最低（丢弃所有入站） | 最高安全要求 |
| `block` | 低（拒绝所有入站，返回拒绝消息） | 高安全要求 |
| `public` | 中（只允许选中的连接） | 公网服务器（默认） |
| `external` | 中（对外网，支持 NAT） | 网关/路由器 |
| `internal` | 高（信任内网） | 内网服务器 |
| `dmz` | 中（非军事区） | DMZ 区域服务器 |
| `work` | 较高（工作网络） | 办公网络 |
| `home` | 较高（家庭网络） | 家庭网络 |
| `trusted` | 最高（允许所有） | 内部受信网络 |

#### 3.2 基础命令

```bash
# 查看防火墙状态
sudo firewall-cmd --state

# 查看当前激活的 zone
sudo firewall-cmd --get-active-zones

# 查看默认 zone
sudo firewall-cmd --get-default-zone

# 查看指定 zone 的所有规则
sudo firewall-cmd --zone=public --list-all

# 查看所有 zone 的配置
sudo firewall-cmd --list-all-zones
```

#### 3.3 服务与端口管理

```bash
# 放行服务（--permanent 永久生效，需 reload）
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --add-service=https --permanent
sudo firewall-cmd --add-service=ssh --permanent

# 放行端口
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --add-port=3000-3100/tcp --permanent

# 重新加载配置（使永久规则立即生效）
sudo firewall-cmd --reload

# 查看已放行的服务
sudo firewall-cmd --list-services

# 查看已放行的端口
sudo firewall-cmd --list-ports

# 移除服务/端口
sudo firewall-cmd --remove-service=http --permanent
sudo firewall-cmd --remove-port=8080/tcp --permanent
```

> **关键理解**：`firewall-cmd` 的规则分**运行时（runtime）**和**永久（permanent）**两种。不加 `--permanent` 的规则立即生效但重启失效；加了 `--permanent` 的规则需 `--reload` 才生效。

#### 3.4 rich-rule（复杂规则）

```bash
# 只允许内网 IP 访问 MySQL
sudo firewall-cmd --zone=public \
  --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 port port=3306 protocol=tcp accept' \
  --permanent

# 拒绝某个 IP 的所有访问
sudo firewall-cmd --zone=public \
  --add-rich-rule='rule family=ipv4 source address=1.2.3.4 reject' \
  --permanent

# 限制某个 IP 只能访问 80 端口
sudo firewall-cmd --zone=public \
  --add-rich-rule='rule family=ipv4 source address=192.168.1.50 port port=80 protocol=tcp accept' \
  --permanent
```

#### 3.5 ufw vs firewalld 对比

| 对比项 | ufw | firewalld |
|--------|-----|-----------|
| 默认发行版 | Ubuntu / Debian | CentOS / RHEL / Rocky |
| 配置复杂度 | 简单 | 中等 |
| 功能丰富度 | 基础 | 丰富（zone/rich-rule/interface 绑定） |
| 底层框架 | iptables | nftables（新）/ iptables（旧） |
| 规则管理 | 直接增删 | runtime + permanent 分离 |
| 适用场景 | 单机简单防护 | 复杂网络/多网卡/多 zone |

---

### 四、iptables / nftables（底层）

#### 4.1 iptables 命令

```bash
# 查看所有规则（-L 列出 -n 不解析 -v 详细 -n 数字）
sudo iptables -L -n -v

# 查看指定表
sudo iptables -t nat -L -n -v

# 追加规则：允许 80 端口入站
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# 追加规则：拒绝 3306 端口入站
sudo iptables -A INPUT -p tcp --dport 3306 -j DROP

# 插入规则到链首（优先级最高）
sudo iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT

# 删除规则
sudo iptables -D INPUT -p tcp --dport 80 -j ACCEPT

# 设置默认策略
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT
```

**iptables 动作（-j）**：

| 动作 | 说明 |
|------|------|
| `ACCEPT` | 接受数据包 |
| `DROP` | 丢弃数据包（不回应，对方会超时） |
| `REJECT` | 拒绝并回送 ICMP 错误消息 |
| `LOG` | 记录日志（不中断处理） |
| `SNAT` | 源地址转换 |
| `DNAT` | 目标地址转换 |

#### 4.2 规则持久化

```bash
# 保存规则到文件
sudo iptables-save > /etc/iptables.rules

# 从文件恢复规则
sudo iptables-restore < /etc/iptables.rules

# Ubuntu 安装 iptables-persistent 实现开机自动加载
sudo apt install -y iptables-persistent
# 安装时会提示保存当前规则
sudo netfilter-persistent save
sudo netfilter-persistent reload
```

#### 4.3 nftables（新框架）

`nftables` 是 iptables 的替代品，语法更统一，性能更好，CentOS 8+ / Ubuntu 22.04+ 默认使用。

```bash
# 查看规则集
sudo nft list ruleset

# 添加规则（语法与 iptables 不同）
sudo nft add rule inet filter input tcp dport 80 accept
sudo nft add rule inet filter input tcp dport 3306 drop

# nftables 兼容 iptables 语法（通过 iptables-nft 后端）
sudo iptables -L -n    # 实际调用 nftables
```

---

### 五、SSH 安全加固

SSH 是服务器的主要入口，也是最常被攻击的服务。加固 SSH 是安全防线的核心。

#### 5.1 修改 /etc/ssh/sshd_config

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak  # 先备份
sudo vim /etc/ssh/sshd_config
```

**关键安全配置项**：

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| `Port` | 2222 | 改默认端口（避开自动扫描） |
| `PermitRootLogin` | no | 禁止 root 直接登录 |
| `PasswordAuthentication` | no | 禁用密码，仅密钥 |
| `PubkeyAuthentication` | yes | 启用密钥认证 |
| `MaxAuthTries` | 3 | 最大认证尝试次数 |
| `LoginGraceTime` | 30 | 登录宽限时间（秒） |
| `AllowUsers` | deploy | 用户白名单 |
| `PermitEmptyPasswords` | no | 禁止空密码 |
| `X11Forwarding` | no | 禁用 X11 转发 |
| `ClientAliveInterval` | 300 | 客户端存活检查间隔（秒） |
| `ClientAliveCountMax` | 2 | 最大检查次数（超时断开） |
| `Protocol` | 2 | 仅允许 SSH 协议 v2 |

**完整配置示例**：

```bash
# /etc/ssh/sshd_config 安全加固
Port 2222                          # 改默认端口
PermitRootLogin no                 # 禁止 root 直接登录
PasswordAuthentication no          # 禁用密码认证
PubkeyAuthentication yes           # 启用密钥认证
MaxAuthTries 3                     # 最大认证尝试
LoginGraceTime 30                  # 登录宽限时间
PermitEmptyPasswords no            # 禁止空密码
X11Forwarding no                   # 禁用 X11 转发
AllowUsers deploy                  # 只允许 deploy 用户
ClientAliveInterval 300            # 存活检查间隔
ClientAliveCountMax 2              # 最大检查次数（300×2=600秒后断开）
```

```bash
# 修改后重启 sshd（注意：不要关闭当前 SSH 会话，先用新端口测试连接！）
sudo systemctl restart sshd

# 验证配置语法
sudo sshd -t
```

> **关键警告**：修改 SSH 端口后，务必先在防火墙放行新端口，否则会断连！且不要关闭当前会话，新开终端测试新端口能连接后再关闭旧会话。

#### 5.2 SSH 安全清单

- [ ] 修改默认端口 22 → 非标准端口（如 2222）
- [ ] 禁止 root 直接登录（`PermitRootLogin no`）
- [ ] 禁用密码认证，仅用密钥（`PasswordAuthentication no`）
- [ ] 配置用户白名单（`AllowUsers`）
- [ ] 限制认证尝试次数（`MaxAuthTries 3`）
- [ ] 设置超时断开（`ClientAliveInterval` + `ClientAliveCountMax`）
- [ ] 防火墙限制 SSH 来源 IP（只允许跳板机/办公网）
- [ ] 部署 fail2ban 防暴力破解
- [ ] 禁止空密码（`PermitEmptyPasswords no`）
- [ ] 仅允许协议 v2（`Protocol 2`）

---

### 六、fail2ban 防暴力破解

`fail2ban` 通过扫描日志文件，匹配失败模式，自动封禁恶意 IP（调用防火墙规则）。

#### 6.1 安装

```bash
# Ubuntu / Debian
sudo apt install -y fail2ban
```

#### 6.2 配置

fail2ban 的配置文件不要直接修改 `/etc/fail2ban/jail.conf`（升级会被覆盖），应创建 `/etc/fail2ban/jail.local`：

```bash
sudo tee /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
# 封禁时间（秒），默认 10 分钟
bantime = 3600

# 检测时间窗口（秒），在此窗口内失败 maxretry 次则封禁
findtime = 600

# 最大失败次数
maxretry = 3

# 封禁动作（调用 ufw）
banaction = ufw

# 忽略的 IP（白名单，不封禁本地和内网）
ignoreip = 127.0.0.1/8 ::1 192.168.1.0/24

[sshd]
# 启用 SSH 防护
enabled = true
# SSH 端口（与 sshd_config 一致）
port = 2222
# 日志文件路径
logpath = /var/log/auth.log
# 最大失败次数（覆盖全局）
maxretry = 3
EOF
```

#### 6.3 启动与管理

```bash
# 启动并设置开机自启
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# 重启 fail2ban（修改配置后）
sudo systemctl restart fail2ban

# 查看整体状态
sudo fail2ban-client status

# 查看 SSH 防护状态
sudo fail2ban-client status sshd
```

#### 6.4 手动管理封禁

```bash
# 手动封禁 IP
sudo fail2ban-client set sshd banip 1.2.3.4

# 手动解封 IP
sudo fail2ban-client set sshd unbanip 1.2.3.4

# 查看被封禁的 IP 列表
sudo fail2ban-client status sshd
```

#### 6.5 工作原理

```
SSH 登录失败 → /var/log/auth.log 记录 → fail2ban 扫描日志
       ↑                                        │
       │                                        ▼
   被攻击者尝试                          匹配失败模式
                                                 │
                                                 ▼
                                    失败次数 > maxretry？
                                       │           │
                                      是          否
                                       ▼           │
                                  调用 ufw       继续监控
                                  封禁 IP
                                       │
                                       ▼
                                  IP 被封禁 bantime 时间
                                  （默认 1 小时后自动解封）
```

#### 6.6 fail2ban 配置参数表

| 参数 | 作用 | 默认值 | 建议 |
|------|------|--------|------|
| `bantime` | 封禁时长（秒） | 600 | 3600（1 小时） |
| `findtime` | 检测窗口（秒） | 600 | 600（10 分钟） |
| `maxretry` | 最大失败次数 | 5 | 3 |
| `ignoreip` | 白名单 IP | 127.0.0.1 | 加内网网段 |
| `banaction` | 封禁方式 | iptables-multiport | ufw（Ubuntu） |

---

### 七、SELinux / AppArmor 简介

#### 7.1 强制访问控制（MAC）

传统的 Linux 权限是**自主访问控制（DAC）**，用户/进程对自己拥有的资源有完全控制权。**强制访问控制（MAC）**由系统管理员定义安全策略，即使 root 也受策略约束。

#### 7.2 SELinux（CentOS/RHEL 默认）

| 模式 | 说明 |
|------|------|
| `enforcing` | 强制模式，违规操作被阻止并记录 |
| `permissive` | 宽容模式，违规操作只记录不阻止（调试用） |
| `disabled` | 禁用 |

```bash
# 查看状态
sestatus
getenforce

# 临时切换模式
sudo setenforce 0   # 切换到 permissive
sudo setenforce 1   # 切换到 enforcing

# 永久配置
sudo vim /etc/selinux/config
# SELINUX=enforcing|permissive|disabled

# 查看安全上下文
ls -Z /var/www/html

# 排查 SELinux 拒绝
sudo aureport -a          # 审计报告
sudo ausearch -m avc      # 查找 AVC 拒绝记录
```

#### 7.3 AppArmor（Ubuntu 默认）

AppArmor 是基于**路径**的 MAC，配置比 SELinux 简单。

```bash
# 查看状态
sudo aa-status

# 查看已加载的配置文件
sudo apparmor_status

# 查看配置文件目录
ls /etc/apparmor.d/

# 重载配置
sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.mysqld
```

#### 7.4 何时启用/关闭

| 场景 | 建议 |
|------|------|
| 传统服务器部署 | 启用（增加安全） |
| 容器化环境（Docker/K8s） | 通常关闭（可能与容器冲突） |
| 调试服务不工作时 | 临时设为 permissive 排查 |
| 生产环境 | 建议启用 + 正确配置策略 |

---

### 八、系统安全检查清单

#### 8.1 最小化安装

```bash
# 不安装不需要的软件包
# 安装系统时选择 Minimal Install（最小化安装）

# 检查已安装的软件包
dpkg -l | wc -l
apt list --installed | wc -l

# 卸载不需要的软件
sudo apt autoremove --purge
```

#### 8.2 关闭无用服务

```bash
# 查看已启用的服务
systemctl list-unit-files --state=enabled

# 查看运行中的服务
systemctl list-units --type=service --state=running

# 禁用不需要的服务
sudo systemctl disable bluetooth
sudo systemctl disable cups
sudo systemctl disable avahi-daemon
```

#### 8.3 定期更新

```bash
# 手动更新
sudo apt update && sudo apt upgrade

# 自动安全更新
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# 配置自动更新
sudo tee /etc/apt/apt.conf.d/50unattended-upgrades <<'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
EOF
```

#### 8.4 审计（auditd）

```bash
# 安装审计工具
sudo apt install -y auditd

# 查看审计规则
sudo auditctl -l

# 添加审计规则（监控文件访问）
sudo auditctl -w /etc/passwd -p wa -k user_modification
sudo auditctl -w /etc/sudoers -p wa -k sudo_modification

# 查找审计记录
sudo ausearch -k user_modification

# 生成审计报告
sudo aureport --summary
```

#### 8.5 端口扫描（nmap）

```bash
# 安装 nmap
sudo apt install -y nmap

# 扫描本机所有 TCP 端口
sudo nmap -sT -p- localhost

# 扫描指定端口
sudo nmap -sT -p 22,80,443,3306,6379 localhost

# UDP 端口扫描
sudo nmap -sU -p 53,161 localhost

# 查看本机监听端口（不用 nmap 的方式）
ss -tlnp
ss -ulnp
```

#### 8.6 登录审计

```bash
# 查看登录成功记录
last | head -20

# 查看登录失败记录
sudo lastb | head -20

# 查看当前登录用户
who
w

# 查看最近一次登录信息
lastlog
```

#### 8.7 文件完整性检查（aide）

```bash
# 安装 AIDE（Advanced Intrusion Detection Environment）
sudo apt install -y aide

# 初始化数据库
sudo aideinit

# 将初始化数据库设为基准
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# 检查文件完整性
sudo aide --check
```

#### 8.8 弱密码检查（john / hydra）

```bash
# john 检查弱密码（需要先获取 shadow 文件）
sudo apt install -y john
sudo unshadow /etc/passwd /etc/shadow > /tmp/crack.txt
john /tmp/crack.txt
# 能被 john 快速破解的密码就是弱密码，需修改

# hydra 远程服务弱密码检测（仅授权测试）
# sudo apt install -y hydra
# hydra -l deploy -P passwordlist.txt ssh://192.168.1.100:2222
```

---

### 九、生产环境安全建议清单

| 类别 | 检查项 | 状态 |
|------|--------|------|
| **防火墙** | ufw/firewalld 已启用，默认拒绝入站 | [ ] |
| **防火墙** | 只开放必要端口（80/443/SSH） | [ ] |
| **防火墙** | 数据库端口（3306/6379）拒绝外部访问 | [ ] |
| **SSH** | 修改默认端口 | [ ] |
| **SSH** | 禁止 root 直接登录 | [ ] |
| **SSH** | 禁用密码，仅密钥认证 | [ ] |
| **SSH** | 配置用户白名单 | [ ] |
| **SSH** | 设置登录超时断开 | [ ] |
| **入侵防护** | fail2ban 已部署并运行 | [ ] |
| **入侵防护** | SSH 失败 3 次封禁 1 小时 | [ ] |
| **系统更新** | 已安装最新安全补丁 | [ ] |
| **系统更新** | 配置自动安全更新 | [ ] |
| **服务最小化** | 关闭无用服务 | [ ] |
| **服务最小化** | 卸载不需要的软件 | [ ] |
| **审计** | auditd 已启用并配置关键文件监控 | [ ] |
| **审计** | 定期检查登录失败记录 | [ ] |
| **权限** | 应用以非 root 用户运行 | [ ] |
| **权限** | sudo 仅授予必要用户 | [ ] |
| **文件** | 关键配置文件权限 600 | [ ] |
| **文件** | 定期检查文件完整性 | [ ] |
| **备份** | 重要数据定期备份 | [ ] |
| **监控** | 端口/服务/登录异常告警 | [ ] |

---

## 代码文件说明

| 文件 | 说明 | 权限要求 |
|------|------|---------|
| `Code/01-ufw-firewall.sh` | ufw 防火墙配置演示（电商场景：允许 80/443/SSH，拒绝 3306/6379） | sudo |
| `Code/02-firewalld-firewall.sh` | firewalld 防火墙配置演示（CentOS 环境示例，附 Ubuntu 对应说明） | sudo |
| `Code/03-ssh-hardening.sh` | SSH 安全加固脚本（改端口/禁root/禁密码/fail2ban） | sudo |
| `Code/04-security-checklist.md` | 安全加固清单文档（检查清单/端口扫描/审计配置/生产建议） | 参考 |

---

## 关键知识点总结

### 防火墙命令对比表（ufw / firewalld / iptables）

| 操作 | ufw | firewalld | iptables |
|------|-----|-----------|----------|
| 启用 | `ufw enable` | `systemctl start firewalld` | （默认启用） |
| 查看状态 | `ufw status` | `firewall-cmd --state` | `iptables -L -n` |
| 放行 80 | `ufw allow 80/tcp` | `firewall-cmd --add-service=http --permanent` | `iptables -A INPUT -p tcp --dport 80 -j ACCEPT` |
| 拒绝 3306 | `ufw deny 3306` | `firewall-cmd --add-rich-rule='...'` | `iptables -A INPUT -p tcp --dport 3306 -j DROP` |
| 来源限制 | `ufw allow from 192.168.1.0/24 to any port 3306` | `firewall-cmd --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 ...'` | `iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 3306 -j ACCEPT` |
| 保存规则 | 自动保存 | `firewall-cmd --reload` | `iptables-save > file` |
| 删除规则 | `ufw delete allow 80/tcp` | `firewall-cmd --remove-service=http --permanent` | `iptables -D INPUT -p tcp --dport 80 -j ACCEPT` |

### sshd_config 安全配置表

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| `Port` | 2222 | 改默认端口 |
| `PermitRootLogin` | no | 禁止 root 登录 |
| `PasswordAuthentication` | no | 禁用密码 |
| `PubkeyAuthentication` | yes | 启用密钥 |
| `MaxAuthTries` | 3 | 最大尝试次数 |
| `LoginGraceTime` | 30 | 登录宽限时间 |
| `AllowUsers` | deploy | 用户白名单 |
| `ClientAliveInterval` | 300 | 超时检查间隔 |
| `ClientAliveCountMax` | 2 | 超时检查次数 |
| `PermitEmptyPasswords` | no | 禁止空密码 |
| `X11Forwarding` | no | 禁用 X11 转发 |

### fail2ban 配置参数表

| 参数 | 作用 | 默认值 | 推荐值 |
|------|------|--------|--------|
| `bantime` | 封禁时长 | 600s | 3600s（1h） |
| `findtime` | 检测窗口 | 600s | 600s（10min） |
| `maxretry` | 最大失败次数 | 5 | 3 |
| `ignoreip` | 白名单 | 127.0.0.1 | 127.0.0.1 + 内网 |
| `banaction` | 封禁方式 | iptables | ufw（Ubuntu） |

### 安全检查清单速查

| 检查类别 | 命令 |
|---------|------|
| 监听端口 | `ss -tlnp` |
| 运行服务 | `systemctl list-units --type=service --state=running` |
| 登录记录 | `last` / `lastb` |
| 端口扫描 | `nmap -sT -p- localhost` |
| 系统更新 | `apt list --upgradable` |
| 防火墙状态 | `ufw status` / `firewall-cmd --state` |
| fail2ban 状态 | `fail2ban-client status` |
| 文件完整性 | `aide --check` |
| 审计日志 | `ausearch -m avc` |

---

## 实战练习

### 练习 1：电商服务器防火墙配置

**场景**：电商服务器 192.168.1.100 需配置防火墙，只允许必要端口对外。

**任务**：

1. 启用 ufw，设置默认策略（deny incoming / allow outgoing）
2. 放行 80（HTTP）、443（HTTPS）、22（SSH）端口
3. 拒绝 3306（MySQL）、6379（Redis）端口的外部访问
4. 只允许内网 192.168.1.0/24 访问 MySQL 和 Redis
5. 验证规则：用 `ufw status numbered` 查看

**验收**：外部无法访问 3306/6379，内网可以；80/443 正常访问。

### 练习 2：SSH 安全加固

**场景**：SSH 服务经常被暴力破解，需要加固。

**任务**：

1. 修改 SSH 端口为 2222（先在防火墙放行！）
2. 禁止 root 直接登录
3. 禁用密码认证，配置密钥登录（先生成密钥并测试！）
4. 限制最大认证尝试次数为 3
5. 配置登录超时（300 秒无操作断开）
6. 设置 AllowUsers 只允许 deploy 用户
7. 安装并配置 fail2ban（失败 3 次封禁 1 小时）
8. 重启 sshd 并验证

**验收**：用密码无法登录，用密钥可以；root 被拒绝；端口 22 无法连接，2222 可以。

### 练习 3：系统安全审计

**场景**：对服务器进行全面安全检查，发现潜在风险。

**任务**：

1. 用 `ss -tlnp` 列出所有监听端口，排查是否有异常端口
2. 用 `systemctl list-unit-files --state=enabled` 检查启用的服务，关闭不必要的
3. 用 `nmap -sT -p- localhost` 扫描本机所有端口
4. 用 `last` / `lastb` 检查登录成功/失败记录
5. 用 `apt list --upgradable` 检查可更新的包
6. 安装 auditd，配置监控 `/etc/passwd` 和 `/etc/sudoers` 的修改
7. 生成一份安全检查报告

**验收**：报告包含所有检查项的结果与改进建议。

---

> **下一章预告**：Day14 将综合运用前 13 天知识，完成从空白服务器到全栈服务部署的完整运维流程，包含服务器初始化、Nginx 反向代理、MySQL 备份、一键部署脚本。
