# 性能调优指南

> 本文档是 Day12 系统监控与性能调优的综合参考，涵盖四维度排查方法论、ulimit 与 sysctl 调优清单、OOM Killer 应对、生产环境监控建议、Prometheus + Grafana 简介。

---

## 一、四维度性能排查方法论

性能问题排查遵循"从宏观到微观、从系统到进程"的原则，按 CPU → 内存 → 磁盘 IO → 网络 四个维度依次排查。

### 1.1 排查流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    性能问题告警                              │
│            （响应慢 / 报错 / 监控告警 / 用户反馈）           │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
                ┌──────────────────────┐
                │ Step 1: 看 load avg  │  uptime / /proc/loadavg
                │ 判断系统是否过载     │  load > CPU 核数？
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │ Step 2: 看 CPU       │  top / mpstat -P ALL
                │ us/sy/wa/id 哪个高？ │
                └──┬───────┬───────┬───┘
            us 高  │ wa 高 │ id 低 │ sy 高
                   ▼       ▼       ▼       ▼
              应用代码  磁盘IO  扩容   系统调用
              strace   iostat  优化   锁竞争
              perf     iotop         上下文切换
                   │       │
                   ▼       ▼
                ┌──────────────────────┐
                │ Step 3: 看内存       │  free -h / vmstat 1
                │ available 够吗？     │  si/so 频繁吗？
                │ si/so 有活动吗？     │
                └──┬───────────────┬───┘
              不足 │               │ 充足
                   ▼               ▼
              加内存           ┌──────────────────────┐
              优化应用         │ Step 4: 看磁盘 IO    │  iostat -x 1
              调 swappiness    │ %util 高吗？         │  await 大吗？
                              │ await 大吗？         │
                              └──┬───────────────┬───┘
                          是   │               │ 否
                               ▼               ▼
                          iotop 定位进程    ┌──────────────────────┐
                          SSD 升级          │ Step 5: 看网络       │  iftop / ss
                          加缓存            │ 带宽打满吗？         │  nethogs
                                            │ 连接数异常吗？       │
                                            └──┬───────────────┬───┘
                                          是   │               │ 否
                                               ▼               ▼
                                          CDN/压缩         检查应用日志
                                          限流/封IP        代码逻辑
                                          升级带宽
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ 定位根因 → 修复     │
                                    │ → 验证 → 复盘       │
                                    └─────────────────────┘
```

### 1.2 四维度调优策略对比

| 类型 | 典型现象 | 监控工具 | 调优方向 |
|------|---------|---------|---------|
| **CPU 密集型** | `%us` 高，`%id` 低，load 高 | top、mpstat、perf | 优化算法、异步化、加 CPU/加机器 |
| **内核态高** | `%sy` 高，`cs` 高 | top、vmstat、perf | 减少系统调用、优化锁、减少上下文切换 |
| **IO 密集型** | `%wa` 高，`%util` 高，`await` 大 | iostat、iotop | SSD 替换、加缓存、批量读写、读写分离 |
| **内存不足** | `si/so` 频繁，`available` 低 | free、vmstat、smem | 加内存、优化应用内存、调 swappiness |
| **网络瓶颈** | 带宽打满，连接堆积 | iftop、ss、nethogs | 升级带宽、CDN、压缩、连接池优化 |

### 1.3 各维度排查命令速查

#### CPU 排查
```bash
# 1. 查看系统负载
uptime                              # load average
cat /proc/loadavg                   # 内核接口

# 2. 查看 CPU 整体使用率
top -b -n 1 | head -5               # us/sy/wa/id
mpstat 1 3                          # 多核 CPU 使用率

# 3. 定位 CPU 占用最高的进程
top -b -n 1 | head -20              # 按 %CPU 排序
ps aux --sort=-%cpu | head -10      # 静态查看

# 4. 深度分析（有性能开销，慎用）
sudo perf record -a -g -- sleep 10  # 采样
sudo perf report                    # 分析热点函数
strace -c -p PID                    # 系统调用统计
```

#### 内存排查
```bash
# 1. 查看内存概览
free -h                             # available 是关键
cat /proc/meminfo                   # 详细信息

# 2. 查看 swap 与内存动态
vmstat 1 5                          # si/so/bi/bo

# 3. 定位内存占用最高的进程
ps aux --sort=-%mem | head -10      # 按 %MEM 排序
smem -r -k | head -20               # 按 RSS 排序（更准确）

# 4. 检查 OOM 历史
dmesg | grep -i oom
journalctl -k | grep -i oom
```

#### 磁盘 IO 排查
```bash
# 1. 查看磁盘 IO 概览
iostat -x 1 3                       # %util/await

# 2. 定位 IO 最高的进程
sudo iotop -oP                      # 交互式
sudo iotop -b -oP -n 3              # 批处理

# 3. 查看磁盘使用
df -h                               # 分区使用率
du -sh /var/log/*                   # 目录大小

# 4. 综合监控
dstat -tcdny                        # CPU/磁盘/网络综合
```

#### 网络排查
```bash
# 1. 查看连接统计
ss -s                               # 概要
ss -t -a | head -20                 # TCP 连接详情
ss -t state established | wc -l     # 已建立连接数

# 2. 查看带宽使用
sudo iftop -i eth0 -n -P            # 连接级带宽
sudo nethogs eth0                   # 进程级带宽

# 3. 查看历史网络数据
sar -n DEV 1                        # 实时
sar -n DEV -f /var/log/sysstat/sa$(date +%d)  # 今天历史

# 4. 连通性测试
ping -c 4 8.8.8.8                   # 连通性
mtr 8.8.8.8                         # 路由追踪
curl -w "@-" -o /dev/null -s https://example.com <<'EOF'
    DNS: %{time_namelookup}s
    Connect: %{time_connect}s
    TLS: %{time_appconnect}s
    Total: %{time_total}s
EOF
```

---

## 二、ulimit 与文件描述符调优

### 2.1 ulimit 基础

```bash
# 查看所有资源限制
ulimit -a

# 关键参数：
# open files      (-n) 1024     ← 文件描述符（生产需调大到 65535）
# max user processes (-u) 7857  ← 最大进程/线程数
# stack size      (-s) 8192     ← 栈大小 KB
# core file size  (-c) 0        ← core dump 文件大小
```

### 2.2 文件描述符调优（高并发必备）

**为什么需要调优？** 默认 1024 的文件描述符上限对高并发服务（Nginx、Node.js、MySQL）远远不够，每个连接都要占用一个 fd。

**方式一：/etc/security/limits.conf（传统）**

```bash
# 编辑配置文件
sudo tee -a /etc/security/limits.conf <<EOF

# 电商项目性能调优
*               soft    nofile          65535
*               hard    nofile          65535
*               soft    nproc           65535
*               hard    nproc           65535
root            soft    nofile          65535
root            hard    nofile          65535
EOF

# 重新登录后生效（或重启）
```

**方式二：/etc/security/limits.d/*.conf（模块化，推荐）**

```bash
# 为 deploy 用户单独配置
sudo tee /etc/security/limits.d/ecommerce.conf <<EOF
deploy          soft    nofile          65535
deploy          hard    nofile          65535
deploy          soft    nproc           65535
deploy          hard    nproc           65535
mysql           soft    nofile          65535
mysql           hard    nofile          65535
EOF
```

**方式三：systemd 服务配置（针对服务）**

```ini
# 对于 systemd 管理的服务，limits.conf 可能不生效
# 需要在 .service 文件中配置：
[Service]
LimitNOFILE=65535
LimitNPROC=65535

# 或通过 systemctl edit 修改：
# sudo systemctl edit nginx
# [Service]
# LimitNOFILE=65535
```

### 2.3 验证与排查

```bash
# 查看当前用户的 fd 上限
ulimit -n

# 查看进程的 fd 上限
cat /proc/PID/limits | grep "Max open files"

# 查看进程打开的 fd 数量
ls /proc/PID/fd | wc -l

# 查看系统级 fd 上限
cat /proc/sys/fs/file-max

# 查看 fd 使用情况
cat /proc/sys/fs/file-nr
# 输出：已分配 未使用但已预留 系统上限
```

---

## 三、sysctl 内核参数调优清单

### 3.1 网络参数调优（高并发必备）

```bash
sudo tee /etc/sysctl.d/99-ecommerce.conf <<'EOF'
# ============================================================
# 电商服务器内核参数调优
# 适用于高并发 Web 服务（Nginx + Node.js）
# ============================================================

# ---------- 网络参数 ----------
# 监听队列长度（连接请求队列，高并发需调大）
net.core.somaxconn = 65535

# SYN 队列长度（半连接队列，防 SYN Flood）
net.ipv4.tcp_max_syn_backlog = 65535

# 已建立连接队列
net.core.netdev_max_backlog = 65535

# 本地端口范围（高并发时端口不够用会报错）
net.ipv4.ip_local_port_range = 10000 65535

# 复用 TIME_WAIT 连接（高并发短连接必备）
net.ipv4.tcp_tw_reuse = 1

# FIN 等待时间（默认 60s，缩短可释放连接）
net.ipv4.tcp_fin_timeout = 15

# TCP keepalive 探测间隔（默认 7200s=2h，缩短可及时发现死连接）
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3

# 开启 SYN cookies（防 SYN Flood 攻击）
net.ipv4.tcp_syncookies = 1

# TCP 快速打开
net.ipv4.tcp_fastopen = 3

# 增大 TCP 读写缓冲区（高带宽场景）
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# ---------- 内存参数 ----------
# swap 使用倾向（0-100，越小越不爱用 swap）
# 生产环境建议 10，数据库服务器建议 1
vm.swappiness = 10

# 内存过量提交策略
vm.overcommit_memory = 1

# ---------- 文件描述符 ----------
# 系统级文件描述符上限
fs.file-max = 1048576

# inotify 监控上限（文件监控服务需要）
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 1048576
EOF

# 立即加载配置
sudo sysctl -p /etc/sysctl.d/99-ecommerce.conf

# 验证配置
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_tw_reuse
sysctl vm.swappiness
```

### 3.2 内核参数调优清单表

| 参数 | 默认值 | 建议值 | 作用 | 适用场景 |
|------|--------|--------|------|---------|
| `net.core.somaxconn` | 4096 | 65535 | 监听队列长度 | 高并发 Web |
| `net.ipv4.tcp_max_syn_backlog` | 1024 | 65535 | SYN 队列长度 | 高并发/防攻击 |
| `net.ipv4.ip_local_port_range` | 32768-60999 | 10000-65535 | 本地端口范围 | 高并发客户端 |
| `net.ipv4.tcp_tw_reuse` | 0 | 1 | 复用 TIME_WAIT | 短连接场景 |
| `net.ipv4.tcp_fin_timeout` | 60 | 15 | FIN 等待时间 | 短连接场景 |
| `net.ipv4.tcp_keepalive_time` | 7200 | 600 | keepalive 间隔 | 长连接保活 |
| `net.ipv4.tcp_syncookies` | 1 | 1 | 防 SYN Flood | 安全防护 |
| `vm.swappiness` | 60 | 10 | swap 倾向 | 通用/数据库 |
| `fs.file-max` | ~十万 | 1048576 | 系统 fd 上限 | 高并发 |
| `fs.inotify.max_user_watches` | 8192 | 1048576 | 文件监控上限 | 热重载/文件监控 |

### 3.3 数据库服务器专用参数

```bash
# MySQL 服务器专用调优
sudo tee /etc/sysctl.d/99-mysql.conf <<'EOF'
# 数据库服务器 swap 倾向设为 1（尽量不用 swap）
vm.swappiness = 1

# 内存过量提交（数据库分配大内存需谨慎）
vm.overcommit_memory = 0

# 透明大页禁用（数据库建议禁用，可能导致性能抖动）
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
EOF
```

---

## 四、OOM Killer 应对

### 4.1 OOM Killer 机制

当系统物理内存和 swap 都耗尽时，内核的 OOM（Out Of Memory）Killer 会自动选择一个"oom_score 得分最高"的进程杀掉，释放内存。oom_score 基于进程内存占用量计算。

### 4.2 排查 OOM 事件

```bash
# 查看内核日志中的 OOM 记录
dmesg | grep -i oom
# 或
journalctl -k | grep -i oom

# 输出示例：
# Out of memory: Killed process 1234 (mysqld) total-vm:2048000kB, anon-rss:1500000kB
# 说明 mysqld 因占用内存最多被 OOM Killer 杀掉
```

### 4.3 保护关键服务

```bash
# 1. 查看进程的 oom_score（分数越高越容易被杀）
cat /proc/PID/oom_score

# 2. 调整进程的 oom 分数（-1000 到 1000，越低越不容易被杀）
# -1000 表示完全禁止 OOM Killer 杀此进程
echo -1000 > /proc/PID/oom_score_adj

# 3. 对于 systemd 服务，在 .service 文件中配置
# [Service]
# OOMScoreAdjust=-500
```

### 4.4 systemd 内存限制

```ini
# 限制单个服务的内存上限，防止其耗尽系统内存
[Service]
# 限制最大内存使用 2GB
MemoryLimit=2G

# 或使用 MemoryMax（新版 systemd）
MemoryMax=2G

# 内存低于此值时触发告警（不杀进程）
MemoryHigh=1800M
```

### 4.5 MySQL 专用 OOM 防护

```bash
# MySQL 是 OOM 的高频受害者，需特别保护

# 1. 配置 systemd 服务保护
sudo systemctl edit mysqld
# 添加：
# [Service]
# OOMScoreAdjust=-1000
# MemoryLimit=4G

# 2. 合理配置 MySQL 内存参数
# /etc/mysql/mysql.conf.d/mysqld.cnf
# innodb_buffer_pool_size = 2G  # 不超过物理内存 70%
# max_connections = 200
# innodb_log_file_size = 256M

# 3. 监控 MySQL 内存使用
mysql -e "SHOW VARIABLES LIKE 'innodb_buffer_pool_size';"
```

---

## 五、生产环境监控建议

### 5.1 监控分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    生产环境监控体系                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  采集指标   ┌─────────────┐  告警         │
│  │  被监控节点  │ ─────────→ │   监控服务   │ ────→  运维   │
│  │             │             │             │               │
│  │ Node Exporter│            │ Prometheus  │  邮件/短信    │
│  │ MySQL Exporter│           │ (时序数据库) │  钉钉/飞书    │
│  │ Redis Exporter│           │             │  Webhook      │
│  └─────────────┘             └──────┬──────┘               │
│                                     │                       │
│                                     ▼                       │
│                              ┌─────────────┐               │
│                              │   Grafana   │               │
│                              │  (可视化)   │               │
│                              │  仪表盘     │               │
│                              └─────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 监控指标清单

**必须监控的指标**：

| 维度 | 指标 | 告警阈值 |
|------|------|---------|
| CPU | CPU 使用率 | 持续 > 80% 告警 |
| CPU | load average | > CPU 核数 × 1.5 告警 |
| 内存 | available 内存 | < 总内存 20% 告警 |
| 内存 | swap 使用率 | > 50% 告警 |
| 磁盘 | 磁盘使用率 | > 85% 告警 |
| 磁盘 | inode 使用率 | > 85% 告警 |
| 磁盘 IO | %util | 持续 > 90% 告警 |
| 网络 | 带宽使用率 | > 80% 告警 |
| 网络 | TCP 连接数 | 异常增长告警 |
| 服务 | 服务存活 | 服务挂掉立即告警 |
| 服务 | 响应时间 | > 1s 告警 |
| 业务 | 错误率 | > 1% 告警 |

### 5.3 基础监控脚本示例

```bash
#!/bin/bash
# 简易监控告警脚本（生产环境建议用 Prometheus + Grafana）

ALERT_EMAIL="ops@example.com"
THRESHOLD_CPU=80          # CPU 使用率阈值
THRESHOLD_MEM=20          # 可用内存百分比阈值
THRESHOLD_DISK=85         # 磁盘使用率阈值

# 检查 CPU
CPU_IDLE=$(top -b -n 1 | grep "%Cpu" | awk -F',' '{print $4}' | awk '{print $1}')
CPU_USED=$(echo "100 - ${CPU_IDLE%.*}" | bc)
if [ "${CPU_USED}" -gt "${THRESHOLD_CPU}" ]; then
    echo "[ALERT] CPU 使用率 ${CPU_USED}% 超过阈值 ${THRESHOLD_CPU}%"
fi

# 检查内存
MEM_TOTAL=$(free -m | awk '/Mem:/ {print $2}')
MEM_AVAIL=$(free -m | awk '/Mem:/ {print $7}')
MEM_AVAIL_PCT=$((MEM_AVAIL * 100 / MEM_TOTAL))
if [ "${MEM_AVAIL_PCT}" -lt "${THRESHOLD_MEM}" ]; then
    echo "[ALERT] 可用内存 ${MEM_AVAIL_PCT}% 低于阈值 ${THRESHOLD_MEM}%"
fi

# 检查磁盘
df -h | awk -v threshold=${THRESHOLD_DISK} 'NR>1 {
    usage=gsub(/%/,"",$5)
    if ($5+0 > threshold) {
        print "[ALERT] 分区 "$1" 使用率 "$5"% 超过阈值 "threshold"%"
    }
}'
```

---

## 六、Prometheus + Grafana 简介

### 6.1 什么是 Prometheus

**Prometheus** 是 SoundCloud 开源的监控系统，现已成为 CNCF 第二个毕业项目（仅次于 Kubernetes）。特点：

- **时序数据库**：专门存储带时间戳的指标数据
- **Pull 模式**：主动拉取被监控节点的指标（而非被动接收）
- **多维数据模型**：指标名 + 标签（label）唯一标识一条时间序列
- **PromQL**：强大的查询语言
- **告警内置**：Alertmanager 独立告警组件

### 6.2 什么是 Grafana

**Grafana** 是开源的数据可视化平台，支持多种数据源（Prometheus、MySQL、InfluxDB 等），提供丰富的图表与仪表盘。

### 6.3 快速部署示例

```bash
# 1. 安装 Prometheus
sudo apt install -y prometheus prometheus-node-exporter
sudo systemctl enable prometheus prometheus-node-exporter
sudo systemctl start prometheus prometheus-node-exporter

# Prometheus 默认端口：9090
# Node Exporter 默认端口：9100

# 2. 安装 Grafana
sudo apt-get install -y adduser libfontconfig1
wget https://dl.grafana.com/oss/release/grafana_10.0.0_amd64.deb
sudo dpkg -i grafana_10.0.0_amd64.deb
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Grafana 默认端口：3000
# 默认账号密码：admin / admin

# 3. 在 Grafana 中添加 Prometheus 数据源
# Configuration → Data Sources → Add data source → Prometheus
# URL: http://localhost:9090

# 4. 导入 Node Exporter 仪表盘
# Dashboard → Import → 输入 ID 1860（Node Exporter Full）
```

### 6.4 常用 PromQL 查询

```promql
# CPU 使用率
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 内存使用率
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100

# 磁盘使用率
node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100

# 网络入站流量
rate(node_network_receive_bytes_total{device="eth0"}[5m])

# TCP 连接数
node_netstat_Tcp_CurrEstab
```

### 6.5 监控方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **sar + 脚本** | 简单、系统自带 | 无告警、无可视化 | 单机临时排查 |
| **Zabbix** | 功能全、agent 完善 | 重量级、配置复杂 | 传统企业运维 |
| **Prometheus + Grafana** | 云原生、社区活跃、可视化强 | 需学习 PromQL | 互联网公司、K8s 环境 |
| **Datadog / 云监控** | 开箱即用、集成多 | 收费、数据出境合规 | 快速上线、SaaS |

---

## 七、性能调优总结

### 7.1 调优原则

1. **先定位再调优**：不要盲目调参，先用监控工具定位瓶颈
2. **一次只改一个变量**：避免多个改动同时生效，无法判断哪个起作用
3. **测试验证**：调优后必须压测验证效果
4. **备份原配置**：调优前备份配置文件，便于回滚
5. **渐进式调优**：从小幅度开始，观察效果再决定是否继续

### 7.2 常见误区

| 误区 | 正确做法 |
|------|---------|
| free 少就加内存 | 看 available，Linux 会用空闲内存做 cache |
| load 高就加 CPU | 先区分是 CPU 瓶颈还是 IO 瓶颈 |
| 加 swap 解决内存不足 | swap 只是缓冲，不能替代物理内存 |
| 一味调大内核参数 | 参数相互关联，需整体考虑 |
| 关闭 swap 提升性能 | OOM 风险增大，建议设 swappiness=1 而非关闭 |

### 7.3 电商场景调优清单

```bash
# ============================================================
# 电商服务器 192.168.1.100 性能调优清单
# ============================================================

# [ ] 1. 文件描述符调优（ulimit -n 65535）
# [ ] 2. 内核网络参数调优（somaxconn/tcp_tw_reuse 等）
# [ ] 3. vm.swappiness 调为 10
# [ ] 4. 开启 sysstat 数据收集（sar 历史数据）
# [ ] 5. 安装并配置 Prometheus + Node Exporter
# [ ] 6. 配置 Grafana 仪表盘
# [ ] 7. 设置关键指标告警（CPU/内存/磁盘/服务存活）
# [ ] 8. MySQL 设置 innodb_buffer_pool_size（物理内存 70%）
# [ ] 9. MySQL 配置 OOM 保护（oom_score_adj = -1000）
# [ ] 10. Nginx worker_connections 调优
# [ ] 11. Node.js --max-old-space-size 设置合理内存上限
# [ ] 12. Redis maxmemory 配置与淘汰策略
```

---

> **相关文件**：
> - `01-cpu-memory-monitoring.sh` - CPU 与内存监控演示
> - `02-disk-io-monitoring.sh` - 磁盘 IO 监控演示
> - `03-network-monitoring.sh` - 网络监控演示
> - `04-performance-tuning.md` - 本文档（性能调优指南）
