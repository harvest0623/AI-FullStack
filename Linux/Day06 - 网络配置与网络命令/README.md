# Day06 - 网络配置与网络命令

网络是服务器与外界通信的桥梁，电商项目的用户请求要到达 Node.js 后端、后端要访问 MySQL 与 Redis、运维要 SSH 远程登录、文件要上传到服务器——每一步都依赖网络。当用户反馈"网站打不开"、"接口超时"、"数据库连不上"时，第一现场的排查工具就是 `ping`、`ss`、`telnet`、`curl`、`dig` 等网络命令。本章围绕电商服务器 `192.168.1.100` 系统讲解网络配置、连通性测试、DNS 查询、端口查看、curl/wget 文件传输、SSH 端口转发与 rsync 增量同步，并演示真实场景下"用户访问 80 端口不通"、"Node.js 连不上 MySQL 3306"等典型故障的定位思路。

---

## 学习目标

- 理解 IP、子网掩码、CIDR、网关、DNS、端口等核心网络概念
- 区分 TCP 与 UDP，了解知名端口、注册端口、动态端口范围
- 使用 `ip addr`、`ip route`、Netplan 配置服务器静态 IP
- 使用 `ping`、`telnet`、`nc`、`traceroute`、`mtr` 排查网络连通性
- 使用 `nslookup`、`dig`、`host` 查询 DNS 解析
- 使用 `ss`、`netstat`、`lsof` 查看端口监听与连接状态
- 熟练使用 `curl` 测试 GET/POST/PUT/DELETE 接口，掌握各种常用选项
- 使用 `wget` 下载文件、断点续传
- 配置 SSH 端口转发（本地/远程/动态）解决跨网络访问问题
- 使用 `scp` 与 `rsync` 高效传输文件

---

## 理论知识讲解

### 一、网络基础概念

| 概念 | 说明 |
|------|------|
| IP 地址 | 网络中设备的唯一标识，IPv4（32 位，如 `192.168.1.100`）/ IPv6（128 位，如 `fe80::1`） |
| 子网掩码 | 区分网络号与主机号，如 `255.255.255.0` |
| CIDR | 无类域间路由，简写 `192.168.1.0/24`，斜杠后为网络位长度 |
| 网关 | 跨网段通信的出口设备，通常是路由器内网 IP |
| DNS | 域名系统，将域名解析为 IP，如 `api.example.com → 192.168.1.100` |
| 端口 | 进程标识，0-65535，与 IP 组成套接字（socket） |
| MTU | 最大传输单元，以太网默认 1500 字节 |

**端口分类**：

| 范围 | 类别 | 示例 |
|------|------|------|
| 0-1023 | 知名端口（需 root 监听） | 22 (SSH) / 80 (HTTP) / 443 (HTTPS) / 3306 (MySQL) |
| 1024-49151 | 注册端口 | 3000 (Node.js) / 6379 (Redis) / 8080 (备用 HTTP) |
| 49152-65535 | 动态/临时端口 | 客户端连接时随机分配 |

**TCP vs UDP**：

| 特性 | TCP | UDP |
|------|-----|-----|
| 连接 | 面向连接（三次握手） | 无连接 |
| 可靠性 | 可靠（确认、重传、排序） | 不可靠（可能丢包） |
| 速度 | 较慢 | 快 |
| 适用场景 | HTTP/SSH/MySQL/邮件 | DNS 查询、视频流、游戏、VoIP |
| 报文头 | 20 字节起 | 8 字节 |

### 二、网络配置

#### 2.1 查看与配置 IP

```bash
# 查看 IP 地址（推荐，iproute2 套件）
ip addr show
ip addr show eth0
# 简写
ip a

# 查看路由表（替代旧 route 命令）
ip route show
ip route get 8.8.8.8       # 查看到某 IP 的路由路径

# 临时配置 IP（重启失效）
sudo ip addr add 192.168.1.100/24 dev eth0
sudo ip link set eth0 up

# 旧命令 ifconfig（需安装 net-tools）
ifconfig
ifconfig eth0
```

#### 2.2 Ubuntu Netplan 配置（永久生效）

Ubuntu 17.10+ 默认使用 Netplan 管理网络，配置文件位于 `/etc/netplan/*.yaml`：

```yaml
# /etc/netplan/01-netcfg.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 114.114.114.114]
```

```bash
# 应用配置
sudo netplan apply

# 测试配置（不应用，调试用）
sudo netplan try
```

#### 2.3 CentOS/RHEL 网络配置

```bash
# /etc/sysconfig/network-scripts/ifcfg-eth0
TYPE=Ethernet
BOOTPROTO=static
NAME=eth0
DEVICE=eth0
ONBOOT=yes
IPADDR=192.168.1.100
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
DNS1=8.8.8.8
DNS2=114.114.114.114
```

```bash
sudo systemctl restart network    # CentOS 7
sudo nmcli connection reload      # CentOS 8+
```

#### 2.4 DNS 配置

```bash
# /etc/resolv.conf —— DNS 服务器配置
nameserver 8.8.8.8
nameserver 114.114.114.114
search example.com

# /etc/hosts —— 本地域名解析（优先级高于 DNS）
192.168.1.100  api.example.com
127.0.0.1      localhost
```

> Ubuntu 上 `/etc/resolv.conf` 通常由 systemd-resolved 管理，是符号链接。永久修改 DNS 应编辑 `/etc/systemd/resolved.conf` 或 Netplan 中的 `nameservers` 字段，然后 `sudo systemctl restart systemd-resolved`。

#### 2.5 主机名配置

```bash
# 查看主机名
hostname
hostnamectl

# 临时修改
sudo hostname web-server-01

# 永久修改（推荐）
sudo hostnamectl set-hostname web-server-01
# 修改后会写入 /etc/hostname，并同步到 /etc/hosts
```

### 三、网络连通性测试

#### 3.1 ping

```bash
ping 192.168.1.1               # 持续 ping，Ctrl+C 停止
ping -c 4 8.8.8.8              # 发送 4 个包后停止
ping -i 0.5 8.8.8.8            # 间隔 0.5 秒
ping -W 2 -c 3 8.8.8.8         # 超时 2 秒，发 3 个包
ping -s 1000 -c 3 8.8.8.8      # 指定包大小（探测 MTU 问题）
```

#### 3.2 telnet 测试端口（已过时但简单）

```bash
# 测试 TCP 端口连通性
telnet 192.168.1.100 80
# Connected 表示通；Connection refused 表示端口未监听；超时表示被防火墙拦截

# 退出 telnet 交互：Ctrl+] 然后 q
```

#### 3.3 nc / ncat（netcat 万能工具）

```bash
# 安装
sudo apt install -y netcat-openbsd       # Ubuntu
# 或 nmap-ncat 在 CentOS

# 扫描端口是否开放
nc -zv 192.168.1.100 80                   # -z 仅扫描不发送数据，-v 详细输出
nc -zv 192.168.1.100 80 443 22            # 多端口
nc -zv 192.168.1.100 20-30                # 端口范围

# 监听端口（临时调试）
nc -l 8080                                # 监听 8080
nc 192.168.1.100 8080                     # 连接

# 传输文件
# 接收端：nc -l 8080 > file.txt
# 发送端：nc 192.168.1.100 8080 < file.txt
```

#### 3.4 traceroute / mtr / tracepath

```bash
# 路由追踪，显示数据包经过的每一跳
traceroute 8.8.8.8
traceroute -n 8.8.8.8                    # -n 不解析域名，速度更快
traceroute -T -p 80 8.8.8.8              # -T TCP 模式（绕过 ICMP 限制）

# mtr = traceroute + ping 持续刷新
sudo apt install -y mtr
mtr 8.8.8.8
mtr -n 8.8.8.8                           # 不解析域名
mtr --report 8.8.8.8                     # 报告模式，发 10 个包后退出

# tracepath 类似 traceroute，无需 root
tracepath 8.8.8.8
```

### 四、DNS 查询

```bash
# nslookup —— 简单 DNS 查询
nslookup api.example.com
nslookup api.example.com 8.8.8.8         # 指定 DNS 服务器

# dig —— 最强大的 DNS 工具
dig api.example.com                      # 默认 A 记录
dig +short api.example.com               # 仅返回 IP
dig api.example.com MX                   # 查询邮件记录
dig api.example.com NS                   # 查询域名服务器
dig api.example.com TXT                  # 查询 TXT 记录
dig @8.8.8.8 api.example.com             # 指定 DNS 服务器
dig api.example.com AAAA                 # IPv6 记录
dig -x 192.168.1.100                     # 反向解析

# host —— 简洁的 DNS 查询
host api.example.com
host -t MX example.com
```

### 五、端口与连接查看

#### 5.1 ss（推荐，替代 netstat）

```bash
# 查看所有 TCP 监听端口（最常用）
ss -tlnp
# -t TCP / -u UDP / -l 仅监听 / -n 不解析端口名 / -p 显示进程

# 查看指定端口
ss -tlnp | grep :80
ss -tlnp 'sport = :80'

# 查看所有已建立的连接
ss -tn

# 查看某 IP 的所有连接
ss -tn | grep 192.168.1.100

# 统计各状态连接数（排查 TIME_WAIT 过多）
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn
```

#### 5.2 netstat（旧命令）

```bash
# 安装
sudo apt install -y net-tools

netstat -tlnp                            # TCP 监听
netstat -unlp                            # UDP 监听
netstat -anp | grep :80                  # 80 端口所有连接
netstat -an | grep ESTABLISHED | wc -l   # 已建立连接数
```

#### 5.3 lsof 查看端口占用

```bash
# 查看某端口被哪个进程占用
sudo lsof -i:8080

# 查看所有网络连接
sudo lsof -i -P -n
# -i 网络 / -P 端口号不解析 / -n IP 不解析

# 查看某进程打开的所有网络连接
sudo lsof -p 1234 -i
```

### 六、curl 命令（API 测试利器）

```bash
# 基础 GET 请求
curl http://192.168.1.100:3000/api/health
curl https://api.example.com/users

# POST 请求（JSON）
curl -X POST http://192.168.1.100:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"alice","email":"alice@example.com"}'

# 携带认证 Token
curl -H "Authorization: Bearer eyJhbGciOi..." \
  http://192.168.1.100:3000/api/profile

# PUT / DELETE
curl -X PUT http://192.168.1.100:3000/api/users/1 \
  -H "Content-Type: application/json" -d '{"name":"bob"}'
curl -X DELETE http://192.168.1.100:3000/api/users/1

# 下载到指定文件
curl -o /tmp/file.tar.gz http://example.com/file.tar.gz
# 用原文件名下载
curl -O http://example.com/file.tar.gz

# 仅查看响应头
curl -I http://192.168.1.100:3000/api/health
# 同时显示响应头和正文
curl -i http://192.168.1.100:3000/api/health

# 详细过程（调试用，显示握手、TLS、请求头）
curl -v http://192.168.1.100:3000/api/health

# 跟随重定向
curl -L http://example.com/redirect

# 设置超时
curl --connect-timeout 5 --max-time 10 http://192.168.1.100:3000/api/health
# --connect-timeout 连接超时 / --max-time 总超时

# 携带 Cookie
curl --cookie "session=abc123" http://192.168.1.100:3000/api/cart
# 保存响应 Cookie 到文件
curl -c /tmp/cookies.txt http://192.168.1.100:3000/login -d "user=admin"
# 加载 Cookie 文件
curl -b /tmp/cookies.txt http://192.168.1.100:3000/api/cart

# 自定义 DNS 解析（绕过 DNS，直接指定 IP）
curl --resolve api.example.com:443:192.168.1.100 https://api.example.com/api/health

# 表单提交
curl -F "file=@/tmp/avatar.png" -F "userId=1" http://192.168.1.100:3000/api/upload

# 输出 HTTP 状态码
curl -s -o /dev/null -w "%{http_code}\n" http://192.168.1.100:3000/api/health
# -s 静默（不显示进度） / -o /dev/null 丢弃正文 / -w 输出格式化

# 详细计时信息（性能排查）
curl -o /dev/null -s -w "DNS:%{time_namelookup} Connect:%{time_connect} \
TTFB:%{time_starttransfer} Total:%{time_total}\n" \
  http://192.168.1.100:3000/api/health
```

### 七、wget 命令

```bash
# 基础下载
wget http://example.com/file.tar.gz

# 指定保存文件名
wget -O /tmp/myfile.tar.gz http://example.com/file.tar.gz

# 断点续传（大文件中断后继续）
wget -c http://example.com/large-file.iso

# 递归下载（镜像网站）
wget -r -l 2 http://example.com/           # 递归 2 层
wget -r -np http://example.com/docs/        # 不追溯到父目录

# 后台下载
wget -b http://example.com/large-file.iso

# 限速下载
wget --limit-rate=1M http://example.com/file

# 静默下载
wget -q http://example.com/file

# 重试与超时
wget -t 3 -T 30 http://example.com/file     # 重试 3 次，超时 30 秒

# 携带认证
wget --user=admin --password=secret http://example.com/protected
wget --header="Authorization: Bearer xxx" http://example.com/api
```

### 八、SSH 高级用法

#### 8.1 SSH 端口转发

```bash
# 本地转发（-L）：把远程服务映射到本地端口
# 把远程 192.168.1.100 的 MySQL 3306 映射到本地 13306
ssh -L 13306:127.0.0.1:3306 deploy@192.168.1.100
# 之后本地访问 127.0.0.1:13306 等同访问远程的 3306

# 本地转发后台运行
ssh -fN -L 13306:127.0.0.1:3306 deploy@192.168.1.100

# 远程转发（-R）：把本地服务映射到远程端口
# 让远程服务器上的其他进程通过 192.168.1.100:8080 访问本地 3000
ssh -R 8080:127.0.0.1:3000 deploy@192.168.1.100

# 动态转发（-D）：SOCKS5 代理
ssh -D 1080 deploy@192.168.1.100
# 浏览器设置 SOCKS5 代理 127.0.0.1:1080 即可通过 192.168.1.100 上网
```

| 类型 | 选项 | 方向 | 典型用途 |
|------|------|------|---------|
| 本地转发 | -L | 本地→远程 | 内网 MySQL/Redis 通过 SSH 跳板访问 |
| 远程转发 | -R | 远程→本地 | 把本地开发服务暴露给远程服务器 |
| 动态转发 | -D | 双向 | SOCKS5 代理，翻墙/匿名访问 |

#### 8.2 SSH 配置文件 `~/.ssh/config`

```ssh-config
# ~/.ssh/config
Host ecommerce
    HostName 192.168.1.100
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_rsa_ecommerce
    ServerAliveInterval 60
    ServerAliveCountMax 3

Host db-server
    HostName 192.168.1.200
    User deploy
    Port 2222

Host *
    StrictHostKeyChecking accept-new
```

配置后可直接 `ssh ecommerce` 而无需输入完整命令。

### 九、scp 与 rsync

#### 9.1 scp

```bash
# 上传文件到远程
scp /tmp/file.tar.gz deploy@192.168.1.100:/opt/ecommerce/

# 从远程下载
scp deploy@192.168.1.100:/opt/ecommerce/logs/app.log /tmp/

# 递归上传目录
scp -r /tmp/project deploy@192.168.1.100:/opt/ecommerce/

# 指定端口
scp -P 2222 file deploy@192.168.1.100:/tmp/

# 压缩传输
scp -C file deploy@192.168.1.100:/tmp/

# 两台远程之间传输
scp deploy@host1:/path/file deploy@host2:/path/
```

#### 9.2 rsync（增量同步利器）

```bash
# 基础同步（增量）
rsync -avz /opt/ecommerce/backend/ deploy@192.168.1.100:/opt/ecommerce/backend/
# -a 归档模式（保留权限/时间/符号链接/递归）
# -v 详细输出
# -z 压缩传输

# 删除目标多余文件（镜像同步）
rsync -avz --delete /opt/ecommerce/backend/ deploy@192.168.1.100:/opt/ecommerce/backend/

# 指定 SSH 端口
rsync -avz -e "ssh -p 2222" /src/ deploy@host:/dst/

# 排除某些文件
rsync -avz --exclude='node_modules' --exclude='.git' /src/ deploy@host:/dst/

# 断点续传（大文件）
rsync -avz --partial --progress /large-file deploy@host:/dst/

# 模拟运行（不真实传输）
rsync -avz --dry-run /src/ deploy@host:/dst/

# 显示进度
rsync -avz --progress /src/ deploy@host:/dst/
```

#### 9.3 rsync vs scp

| 特性 | scp | rsync |
|------|-----|-------|
| 传输方式 | 全量复制 | 增量（仅传差异部分） |
| 断点续传 | 不支持 | 支持（--partial） |
| 删除同步 | 不支持 | 支持（--delete） |
| 压缩 | -C（弱） | -z（更强） |
| 排除文件 | 不支持 | --exclude |
| 大文件效率 | 低（每次重传） | 高 |
| 简单场景 | 简单 | 略复杂 |

> 生产环境代码部署、备份同步一律用 rsync，scp 仅用于一次性小文件传输。

---

## 代码文件说明

| 文件 | 用途 | 是否需 root |
|------|------|------------|
| `Code/01-network-config.sh` | 演示 IP/路由查看、DNS 配置、Netplan 说明、主机名设置 | 部分需要 |
| `Code/02-network-diagnostics.sh` | 演示 ping/telnet/nc 端口测试、traceroute/mtr、nslookup/dig DNS 查询、ss/netstat/lsof 端口查看 | 部分需要 |
| `Code/03-curl-wget.sh` | 演示 curl GET/POST/PUT/DELETE、各种选项、下载文件、API 测试实战；wget 下载 | 否 |
| `Code/04-ssh-tunnel-rsync.sh` | 演示 SSH 端口转发、~/.ssh/config 配置、scp 上传下载、rsync 增量同步 | 否 |

---

## 关键知识点总结

### 1. 网络命令速查表

| 命令 | 用途 | 示例 |
|------|------|------|
| `ip addr` | 查看 IP | `ip a` |
| `ip route` | 查看路由 | `ip r` |
| `ping` | 测试连通性 | `ping -c 4 8.8.8.8` |
| `telnet host port` | 测端口 | `telnet 192.168.1.100 80` |
| `nc -zv host port` | 扫端口 | `nc -zv 192.168.1.100 80` |
| `traceroute` | 路由追踪 | `traceroute -n 8.8.8.8` |
| `mtr` | 追踪+ping | `mtr 8.8.8.8` |
| `nslookup` | DNS 查询 | `nslookup example.com` |
| `dig` | DNS 详细查询 | `dig +short example.com` |
| `ss -tlnp` | 端口监听 | `ss -tlnp \| grep :80` |
| `lsof -i:port` | 端口占用 | `sudo lsof -i:80` |
| `curl` | HTTP 请求 | `curl -X POST -d '...' URL` |
| `wget` | 下载文件 | `wget -c URL` |

### 2. curl 常用选项速查

| 选项 | 用途 |
|------|------|
| `-X METHOD` | 指定 HTTP 方法（GET/POST/PUT/DELETE） |
| `-H "Key: Value"` | 添加请求头 |
| `-d "data"` | 发送数据（默认 POST） |
| `-F "field=@file"` | 表单/文件上传 |
| `-o file` | 输出到文件 |
| `-O` | 用原文件名保存 |
| `-I` | 仅看响应头 |
| `-i` | 显示响应头和正文 |
| `-v` | 详细过程（调试） |
| `-L` | 跟随重定向 |
| `-s` | 静默模式 |
| `-w "%{http_code}"` | 输出格式化信息 |
| `--cookie "k=v"` | 携带 Cookie |
| `--resolve host:port:ip` | 自定义 DNS |
| `--connect-timeout N` | 连接超时 |
| `--max-time N` | 总超时 |

### 3. ss / netstat 输出字段说明

| 字段 | 含义 |
|------|------|
| State | 连接状态（LISTEN/ESTABLISHED/TIME_WAIT/SYN_SENT/CLOSE_WAIT） |
| Recv-Q | 接收队列字节数 |
| Send-Q | 发送队列字节数 |
| Local Address:Port | 本地地址端口 |
| Peer Address:Port | 对端地址端口 |
| PID/Program | 进程 ID 与程序名（需 root） |

**TCP 连接状态速查**：

| 状态 | 说明 | 排查意义 |
|------|------|---------|
| LISTEN | 监听中 | 服务正常启动 |
| ESTABLISHED | 已建立 | 正常连接中 |
| SYN_SENT | 已发 SYN | 等对端响应（可能被防火墙拦） |
| SYN_RECV | 收到 SYN | 三次握手进行中 |
| TIME_WAIT | 主动关闭后等待 | 大量出现需调 `tcp_tw_reuse` |
| CLOSE_WAIT | 对端关闭但本端未关闭 | 应用未调用 close()，可能代码 BUG |

### 4. SSH 端口转发对比表

| 类型 | 选项 | 命令格式 | 用途 |
|------|------|---------|------|
| 本地转发 | -L | `ssh -L 本地:远程IP:远程端口 user@host` | 通过 SSH 访问内网数据库 |
| 远程转发 | -R | `ssh -R 远程端口:本地IP:本地端口 user@host` | 把本地服务暴露给远程 |
| 动态转发 | -D | `ssh -D 本地端口 user@host` | SOCKS5 代理 |

---

## 实战练习

### 练习 1：定位"80 端口访问不通"问题

用户反馈电商网站打不开。请按以下步骤排查：

1. 在服务器上 `ss -tlnp | grep :80` 确认 Nginx 是否监听 80
2. 用 `curl -v http://127.0.0.1:80` 测试本地能否访问
3. 用 `nc -zv 192.168.1.100 80` 从另一台机器测试远程连通性
4. 若本地通而远程不通，检查 `sudo ufw status` 防火墙规则
5. 用 `journalctl -u nginx -p err` 查 Nginx 错误日志

**验收**：写一份排查报告，每步的输出与最终结论。

### 练习 2：通过 SSH 端口转发访问内网 MySQL

MySQL 仅监听 `127.0.0.1:3306`，无法直接远程访问。请：

1. 在本地机器执行 `ssh -L 13306:127.0.0.1:3306 deploy@192.168.1.100 -fN`
2. 用 `mysql -h 127.0.0.1 -P 13306 -u root -p` 连接
3. 用 `ss -tlnp | grep 13306` 验证本地监听
4. 写出 `~/.ssh/config` 配置，让 `ssh db-tunnel` 一键建立转发

### 练习 3：用 curl 完成电商 API 全流程测试

完成登录、查看商品、下单、查询订单的接口测试，要求：

1. 用 `curl -c /tmp/cookies.txt` 登录并保存 Cookie
2. 用 `curl -b /tmp/cookies.txt` 携带 Cookie 访问需认证接口
3. 用 `curl -w "%{http_code}"` 输出每次请求状态码
4. 用 `--connect-timeout 5 --max-time 10` 设置超时
5. 用 `curl -X POST -H "Content-Type: application/json" -d '{...}'` 提交 JSON
