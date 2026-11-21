# Day12 - 系统监控与性能调优

服务器性能问题排查是运维工作的核心能力。当电商大促期间接口响应变慢、数据库连接堆积、用户请求超时，能否在几分钟内定位瓶颈所在，直接决定了故障的影响范围。掌握系统监控工具，就等于拥有了透视服务器内部状态的"X 光机"——CPU 占用率、内存使用情况、磁盘 IO 吞吐、网络带宽流量，所有运行时指标都能被量化、被观测、被分析。本章系统讲解 Linux 四大性能维度（CPU、内存、磁盘 IO、网络）的监控工具与调优方法，配合进程级追踪与内核参数调优，帮助你建立起完整的性能排查方法论。

---

## 学习目标

完成本章学习后，你应能够：

- 理解 `load average` 三个数字的含义，判断系统负载是否过高
- 熟练使用 `top` / `htop` / `mpstat` 分析 CPU 使用率与多核负载分布
- 使用 `free` / `vmstat` 分析内存与 swap 使用情况，识别内存不足症状
- 使用 `iostat` / `iotop` 定位磁盘 IO 瓶颈，理解 `%util` 与 `await` 的区别
- 使用 `iftop` / `nethogs` / `ss` 排查网络连接与带宽占用
- 掌握 `sar` 综合监控工具，查看历史性能数据
- 使用 `strace` / `ltrace` / `perf` 追踪进程的系统调用与性能热点
- 建立"四维度排查"性能调优方法论：CPU → 内存 → 磁盘 IO → 网络
- 配置 `ulimit` 资源限制与 `sysctl` 内核参数调优
- 理解 OOM Killer 机制，应对内存耗尽场景

---

## 理论知识讲解

### 一、系统负载与 CPU 监控

#### 1.1 load average（系统平均负载）

`load average` 是 Linux 系统最直观的健康指标，表示一段时间内系统中**处于运行或等待状态的进程平均数**。

```bash
# uptime 命令查看负载
uptime
# 输出示例：up 10:30, 2 users, load average: 0.20, 0.18, 0.15

# /proc/loadavg 内核接口
cat /proc/loadavg
# 输出示例：0.20 0.18 0.15 2/150 12345
```

**三个数字的含义**：

| 位置 | 时间窗口 | 含义 |
|------|---------|------|
| 第 1 个 | 1 分钟 | 最近 1 分钟平均负载 |
| 第 2 个 | 5 分钟 | 最近 5 分钟平均负载 |
| 第 3 个 | 15 分钟 | 最近 15 分钟平均负载 |

**多少算高？** 判断标准是**与 CPU 逻辑核数的比值**：

```bash
# 查看 CPU 逻辑核数
nproc
# 假设输出 4

# 负载判断（以 4 核为例）：
# load < 4      → 正常，CPU 有富余
# load ≈ 4      → 满载，无空闲但能处理
# load > 4      → 过载，有进程在排队等待 CPU
# load > 4×2    → 严重过载，需立即排查
```

> **关键理解**：load average 包含的是"正在运行 + 等待 CPU + 等待 IO"的进程数，所以 IO 瓶颈也会推高 load average，不要一看到 load 高就以为是 CPU 不够。

#### 1.2 top 命令详解

`top` 是 Linux 最常用的实时进程监控工具，几乎所有发行版自带。

```bash
top
```

**top 输出字段详解（头部统计区）**：

```
top - 14:23:01 up 10:30,  2 users,  load average: 0.20, 0.18, 0.15
Tasks: 150 total,   1 running, 149 sleeping,   0 stopped,   0 zombie
%Cpu(s):  5.0 us,  2.0 sy,  0.0 ni, 92.5 id,  0.3 wa,  0.0 hi,  0.2 si,  0.0 st
MiB Mem :   3932.0 total,   1234.5 free,   1567.8 used,   1129.7 buff/cache
MiB Swap:   2048.0 total,   2048.0 free,      0.0 used.   2100.0 avail Mem
```

| 字段 | 含义 |
|------|------|
| `load average` | 1/5/15 分钟平均负载 |
| `Tasks: total/running/sleeping/stopped/zombie` | 进程总数与状态分布 |
| `%us` (user) | 用户态 CPU 占比（应用程序运行） |
| `%sy` (system) | 内核态 CPU 占比（系统调用） |
| `%ni` (nice) | 调整过优先级的进程占用 |
| `%id` (idle) | 空闲 CPU 占比 |
| `%wa` (iowait) | 等待 IO 的 CPU 占比 |
| `%hi` (hardware irq) | 硬中断占用 |
| `%si` (software irq) | 软中断占用 |
| `%st` (steal) | 被虚拟化偷走的 CPU（云服务器关注） |

**top 输出字段详解（进程列表区）**：

| 字段 | 含义 |
|------|------|
| `PID` | 进程 ID |
| `USER` | 进程所有者 |
| `PR` | 优先级（内核调度优先级） |
| `NI` | nice 值（-20 到 19，越小优先级越高） |
| `VIRT` | 虚拟内存大小（包含映射库、交换等，不代表实际占用） |
| `RES` | 常驻物理内存（实际使用的物理内存） |
| `SHR` | 共享内存 |
| `S` | 进程状态（R 运行/S 睡眠/D 不可中断/Z 僵尸） |
| `%CPU` | CPU 占用率 |
| `%MEM` | 内存占用率 |
| `TIME+` | 累计 CPU 时间 |

**top 交互命令**：

| 按键 | 功能 |
|------|------|
| `P` | 按 CPU 占用排序（默认） |
| `M` | 按内存占用排序 |
| `1` | 展开显示每个 CPU 核心的使用率 |
| `k` | 杀死指定 PID 的进程 |
| `q` | 退出 |
| `h` | 帮助 |
| `c` | 显示完整命令行 |
| `f` | 自定义显示字段 |
| `H` | 显示线程 |

#### 1.3 htop（增强版 top）

`htop` 提供彩色界面、鼠标操作、树形视图，比 `top` 更直观。

```bash
# 安装 htop
sudo apt install -y htop

# 启动 htop
htop
```

**htop 常用快捷键**：

| 按键 | 功能 |
|------|------|
| `F5` | 树形视图（显示进程父子关系） |
| `F4` | 过滤进程（输入关键词） |
| `F6` | 排序（选择排序字段） |
| `F9` | 发送信号（杀死进程） |
| `F2` | 设置（自定义显示列、颜色） |
| `+` / `-` | 折叠/展开子进程 |
| `t` | 树形显示 |

#### 1.4 mpstat（多核 CPU 监控）

`mpstat` 来自 `sysstat` 包，能查看每个 CPU 核心的使用情况，发现负载是否均衡。

```bash
# 安装 sysstat 包（包含 mpstat、iostat、sar 等）
sudo apt install -y sysstat

# 查看所有 CPU 核心使用率，每秒刷新一次
mpstat -P ALL 1
```

**mpstat 输出示例**：

```
10:00:01 AM  CPU   %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
10:00:02 AM  all    5.00    0.00    2.00    0.30    0.00    0.20    0.00    0.00    0.00   92.50
10:00:02 AM    0    8.00    0.00    3.00    0.00    0.00    0.00    0.00    0.00    0.00   89.00
10:00:02 AM    1    2.00    0.00    1.00    0.00    0.00    0.00    0.00    0.00    0.00   97.00
```

**关键字段**：

| 字段 | 含义 |
|------|------|
| `%usr` | 用户态时间（应用代码执行） |
| `%sys` | 内核态时间（系统调用） |
| `%iowait` | 等待 IO 完成的时间 |
| `%idle` | 空闲时间 |

#### 1.5 CPU 性能问题判断方法

| 现象 | 含义 | 排查方向 |
|------|------|---------|
| `%us` 高 | 用户态 CPU 占用高 | 应用程序代码效率问题（如死循环、复杂计算） |
| `%sy` 高 | 内核态 CPU 占用高 | 系统调用频繁（如大量 fork、锁竞争、上下文切换） |
| `%wa` 高 | IO 等待高 | 磁盘慢或网络 IO 阻塞，应用被 IO 拖累 |
| `%id` 低 | CPU 空闲少 | CPU 繁忙，需优化算法或扩容 |
| `%si` 高 | 软中断高 | 网络包处理量大（高并发场景） |
| `%st` 高 | 被偷走 | 云主机宿主超卖，需迁移或升级实例 |

---

### 二、内存监控

#### 2.1 free 命令

```bash
# 以人类可读格式显示内存
free -h
```

**free 输出字段详解**：

```
               total        used        free      shared  buff/cache   available
Mem:           3.8Gi       1.5Gi       1.2Gi       0.1Gi       1.1Gi       2.1Gi
Swap:          2.0Gi          0B       2.0Gi
```

| 字段 | 含义 |
|------|------|
| `total` | 物理内存总量 |
| `used` | 已使用内存（不含 buffer/cache） |
| `free` | 完全空闲内存 |
| `shared` | 共享内存（如 tmpfs） |
| `buff/cache` | 系统用作缓冲和缓存的内存 |
| `available` | **实际可用内存**（= free + 可回收的 buff/cache） |

> **关键认知**：Linux 会尽量利用空闲内存做 buffer/cache 加速 IO，所以 `free` 少不代表内存紧张。判断内存是否够用，**看 `available` 而不是 `free`**。

#### 2.2 buffer vs cache

| 概念 | 作用 | 场景 |
|------|------|------|
| **buffer（缓冲）** | 写缓冲，暂存待写入磁盘的数据 | 数据从内存写入磁盘时的中转 |
| **cache（缓存）** | 读缓存，缓存已从磁盘读取的数据 | 重复读取文件时直接命中内存 |

#### 2.3 vmstat 命令

`vmstat` 综合报告虚拟内存、进程、IO、CPU 状态，是性能排查的核心工具。

```bash
# 每秒刷新一次，持续观察
vmstat 1
```

**vmstat 输出示例**：

```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0      0 1234567 234567 890123    0    0    10    15  500  800  5  2 92  1  0
```

**vmstat 字段含义表**：

| 分类 | 字段 | 含义 |
|------|------|------|
| procs | `r` | 运行队列中的进程数（>CPU 核数说明 CPU 紧张） |
| procs | `b` | 处于 D 状态（不可中断睡眠，通常等待 IO）的进程数 |
| memory | `swpd` | 已使用的 swap 大小 |
| memory | `free` | 空闲内存 |
| memory | `buff` | buffer 大小 |
| memory | `cache` | cache 大小 |
| swap | `si` | swap in（每秒从 swap 读入内存的量） |
| swap | `so` | swap out（每秒从内存写入 swap 的量） |
| io | `bi` | block in（每秒从磁盘读入的块数） |
| io | `bo` | block out（每秒写入磁盘的块数） |
| system | `in` | 每秒中断数 |
| system | `cs` | 每秒上下文切换数 |
| cpu | `us/sy/id/wa/st` | 同 top 的 CPU 占比 |

> **关键判断**：`si`/`so` 持续大于 0，说明物理内存不足，系统在频繁使用 swap，会严重拖慢性能。

#### 2.4 smem（按进程查看内存）

`smem` 能更准确地展示每个进程的内存占用（包括 PSS 比例分配）。

```bash
# 安装 smem
sudo apt install -y smem

# 按进程查看内存，按 RSS 排序，人类可读
smem -r -k | head -20
```

| 指标 | 含义 |
|------|------|
| `USS` | Unique Set Size，进程独占内存（不含共享库） |
| `PSS` | Proportional Set Size，按比例分摊共享内存（最准确） |
| `RSS` | Resident Set Size，常驻内存（含共享库，会重复计算） |

---

### 三、磁盘 IO 监控

#### 3.1 iostat 命令

```bash
# 查看所有磁盘的扩展 IO 统计，每秒刷新
iostat -x 1
```

**iostat -x 输出字段含义表**：

| 字段 | 含义 |
|------|------|
| `rrqm/s` | 每秒合并的读请求数 |
| `wrqm/s` | 每秒合并的写请求数 |
| `r/s` | 每秒完成的读请求数 |
| `w/s` | 每秒完成的写请求数 |
| `rkB/s` | 每秒读取的 KB 数 |
| `wkB/s` | 每秒写入的 KB 数 |
| `avgrq-sz` | 平均请求大小（扇区数） |
| `avgqu-sz` | 平均请求队列长度 |
| `await` | 平均 IO 响应时间（毫秒，**重点关注**） |
| `%util` | 磁盘利用率（**重点关注**） |

**判断标准**：

- `%util` 接近 100%：磁盘带宽已打满，是瓶颈
- `await` 大于 10ms（SSD）或 20ms（HDD）：IO 延迟过高
- 队列深度 `avgqu-sz` 持续 >1：请求在排队

#### 3.2 iotop（按进程查看 IO）

```bash
# 安装 iotop
sudo apt install -y iotop

# 只显示有 IO 活动的进程
sudo iotop -oP
```

`iotop` 类似 `top`，但按进程显示 IO 读写速率，能定位"谁在疯狂读写磁盘"。

#### 3.3 dstat（综合监控）

```bash
# 安装 dstat
sudo apt install -y dstat

# 综合监控 CPU/内存/磁盘/网络（时间/CPU/内存/磁盘/网络）
dstat -tcmdn
```

`dstat` 一条命令同时展示多维度指标，替代 `vmstat` + `iostat` + `ifstat` 的组合。

---

### 四、网络监控

#### 4.1 iftop（按连接查看带宽）

```bash
# 安装 iftop
sudo apt install -y iftop

# 监控 eth0 网卡带宽，不解析主机名，显示端口
sudo iftop -i eth0 -n -P
```

`iftop` 按连接显示实时带宽使用，能看到哪个 IP 在大量传输数据。

#### 4.2 nethogs（按进程查看网络）

```bash
# 安装 nethogs
sudo apt install -y nethogs

# 按进程查看 eth0 网卡的网络流量
sudo nethogs eth0
```

`nethogs` 能定位"哪个进程在占满网络带宽"，对排查异常流量很有用。

#### 4.3 sar -n DEV（网络历史统计）

```bash
# 查看网卡历史流量统计
sar -n DEV 1
# 或查看历史数据
sar -n DEV -f /var/log/sysstat/sa$(date +%d)
```

#### 4.4 ss -s（连接统计）

```bash
# 查看连接统计概要
ss -s

# 查看所有 TCP 连接
ss -t -a

# 查看指定端口的连接
ss -t -a | grep :80
```

| 命令 | 功能 |
|------|------|
| `ss -s` | 连接数统计概要 |
| `ss -t -a` | 所有 TCP 连接 |
| `ss -u -a` | 所有 UDP 连接 |
| `ss -t state established` | 已建立的 TCP 连接 |

---

### 五、综合监控工具

#### 5.1 sar（sysstat 包）

`sar` 是历史性能数据回溯的核心工具，能查看过去任意时间的 CPU、内存、磁盘、网络状态。

```bash
# 需要先开启数据收集
sudo sed -i 's/false/true/g' /etc/default/sysstat
sudo systemctl restart sysstat
sudo systemctl enable sysstat

# CPU 使用率（每秒刷新）
sar -u 1

# 内存使用率
sar -r 1

# 磁盘 IO
sar -b 1

# 网络接口
sar -n DEV 1

# 查看今天的所有历史数据
sar -A
```

| 命令 | 功能 |
|------|------|
| `sar -u` | CPU 使用率 |
| `sar -r` | 内存使用率 |
| `sar -b` | 磁盘 IO |
| `sar -n DEV` | 网卡流量 |
| `sar -n TCP,ETCP` | TCP 连接统计 |
| `sar -q` | 队列长度与 load average |
| `sar -f /var/log/sysstat/saXX` | 查看某天的历史数据 |

#### 5.2 glances

```bash
# 安装 glances
sudo apt install -y glances

# 启动，每 5 秒刷新
glances -t 5
```

`glances` 是全屏综合监控工具，一个界面展示所有资源指标，还支持 Web 模式（`glances -w`）和 C/S 模式。

#### 5.3 nmon

```bash
# 安装 nmon
sudo apt install -y nmon

# 启动
nmon
```

IBM 出品的综合监控工具，交互式选择查看 CPU©、内存(M)、磁盘(D)、网络(N)等。

---

### 六、进程追踪

#### 6.1 strace（系统调用追踪）

```bash
# 追踪指定进程的系统调用
strace -p PID -f

# 统计系统调用次数与耗时
strace -c -p PID

# 只追踪特定类型的系统调用
strace -e trace=open,read,write -p PID

# 追踪命令并显示耗时
strace -T command
```

**strace 输出示例**：

```
open("/etc/hosts", O_RDONLY|O_CLOEXEC) = 3
read(3, "127.0.0.1\tlocalhost\n...", 4096) = 123
close(3)                                = 0
```

> **注意**：`strace` 基于 `ptrace`，有性能开销，生产环境慎用，排查完立即停止。

#### 6.2 ltrace（库函数追踪）

```bash
# 追踪进程调用的动态库函数
ltrace -p PID

# 统计库函数调用
ltrace -c command
```

#### 6.3 perf（性能分析）

```bash
# perf 来自 linux-tools 包
sudo apt install -y linux-tools-common linux-tools-$(uname -r)

# 采样 10 秒的 CPU 性能数据
sudo perf record -a -g -- sleep 10

# 查看报告
sudo perf report
```

`perf` 是 Linux 内核级性能分析工具，能定位 CPU 热点函数，适合深度性能优化。

---

### 七、性能调优思路

#### 7.1 排查方法论

**性能排查流程**（从宏观到微观）：

```
发现问题（响应慢/报错/告警）
        │
        ▼
Step 1: 看 load average（uptime）
        │  load 高吗？
        ▼
Step 2: 看 CPU（top / mpstat）
        │  us/sy/wa/id 哪个高？
        │  ├─ us 高 → 用户态问题 → 用 strace/perf 定位进程
        │  ├─ sy 高 → 内核态问题 → 系统调用/锁/上下文切换
        │  └─ wa 高 → IO 等待 → 进入 Step 3
        ▼
Step 3: 看内存（free / vmstat）
        │  available 够吗？si/so 频繁吗？
        │  ├─ 内存不足 → 加内存/优化应用
        │  └─ 内存够 → 进入 Step 4
        ▼
Step 4: 看磁盘 IO（iostat -x）
        │  %util 高吗？await 大吗？
        │  ├─ 是 → 用 iotop 定位进程 → 优化磁盘/加 SSD/加缓存
        │  └─ 否 → 进入 Step 5
        ▼
Step 5: 看网络（iftop / ss / nethogs）
        │  带宽打满吗？连接数异常吗？
        │  ├─ 是 → 升级带宽/CDN/压缩/排查异常连接
        │  └─ 否 → 检查应用日志/代码逻辑
        ▼
定位根因 → 修复 → 验证
```

#### 7.2 四维度调优策略

| 类型 | 现象 | 调优方向 |
|------|------|---------|
| CPU 密集型 | `%us` 高，`%id` 低 | 优化算法、加 CPU、加机器、异步化 |
| IO 密集型 | `%wa` 高，`%util` 高 | SSD 替换、加缓存（Redis）、批量读写、读写分离 |
| 内存不足 | `si/so` 频繁，`available` 低 | 加内存、优化应用内存、调整 swap 策略 |
| 网络瓶颈 | 带宽打满，连接堆积 | 升级带宽、CDN 加速、开启压缩、连接池优化 |

---

### 八、ulimit 资源限制

`ulimit` 限制单个用户/进程能使用的系统资源，防止某个进程耗尽资源。

```bash
# 查看当前用户的所有资源限制
ulimit -a

# 核心输出：
# open files      (-n) 1024     ← 文件描述符上限（生产需调大）
# max user processes (-u) 7857  ← 最大进程数
# stack size      (-s) 8192     ← 栈大小 KB
# file size       (-f) unlimited
# ...
```

**关键参数**：

| 参数 | 含义 | 默认值 | 生产建议 |
|------|------|--------|---------|
| `-n` | 文件描述符上限 | 1024 | 65535 |
| `-u` | 最大进程数 | ~几千 | 视场景调整 |
| `-s` | 栈大小 | 8192 KB | 视应用调整 |
| `-c` | core 文件大小 | 0 | 调试时设为 unlimited |

**永久配置方式**：

```bash
# 方式一：/etc/security/limits.conf（传统）
sudo tee -a /etc/security/limits.conf <<EOF
*               soft    nofile          65535
*               hard    nofile          65535
*               soft    nproc           65535
*               hard    nproc           65535
EOF

# 方式二：/etc/security/limits.d/*.conf（模块化，推荐）
sudo tee /etc/security/limits.d/ecommerce.conf <<EOF
deploy          soft    nofile          65535
deploy          hard    nofile          65535
EOF

# 对于 systemd 管理的服务，还需配置 LimitNOFILE
# 在 .service 文件中添加：
# [Service]
# LimitNOFILE=65535
```

---

### 九、/proc 与 /sys 文件系统

`/proc` 和 `/sys` 是内核暴露给用户空间的接口，能直接读取内核状态。

#### 9.1 /proc 常用文件

| 文件 | 内容 |
|------|------|
| `/proc/cpuinfo` | CPU 信息（型号、核数、频率） |
| `/proc/meminfo` | 内存详细信息 |
| `/proc/loadavg` | 负载平均值 |
| `/proc/version` | 内核版本 |
| `/proc/uptime` | 系统运行时间 |
| `/proc/filesystems` | 支持的文件系统 |

#### 9.2 /proc/[pid]/ 进程信息

```bash
# 查看进程状态（内存、信号、线程数等）
cat /proc/PID/status

# 查看进程启动命令与参数
cat /proc/PID/cmdline | tr '\0' ' '

# 查看进程环境变量
cat /proc/PID/environ | tr '\0' '\n'

# 查看进程打开的文件描述符
ls -l /proc/PID/fd/

# 查看进程的资源限制
cat /proc/PID/limits

# 查看进程的内存映射
cat /proc/PID/maps
```

#### 9.3 /proc/sys/ 与 sysctl

`/proc/sys/` 是内核参数接口，`sysctl` 命令是其友好封装。

```bash
# 查看所有内核参数
sysctl -a

# 查看特定参数
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
sysctl vm.swappiness

# 临时修改（重启失效）
sudo sysctl -w net.core.somaxconn=65535

# 永久修改：写入 /etc/sysctl.conf 或 /etc/sysctl.d/*.conf
sudo tee -a /etc/sysctl.d/99-ecommerce.conf <<EOF
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 10000 65535
vm.swappiness = 10
EOF

# 加载配置
sudo sysctl -p /etc/sysctl.d/99-ecommerce.conf
```

---

### 十、OOM Killer

当系统物理内存和 swap 都耗尽时，内核的 OOM Killer 会自动选择一个"得分最高"的进程杀掉，释放内存。

```bash
# 查看进程的 oom_score（分数越高越容易被杀）
cat /proc/PID/oom_score

# 调整进程的 oom 分数（-1000 到 1000，越低越不容易被杀）
echo -500 > /proc/PID/oom_score_adj

# 查看历史 OOM 记录
dmesg | grep -i oom
# 或
journalctl -k | grep -i oom
```

**OOM 应对策略**：

1. 监控 `available` 内存，提前预警
2. 关键服务设置 `oom_score_adj` 为负值（如 -500），降低被杀概率
3. 合理配置 swap 作为缓冲（但不要依赖 swap 跑服务）
4. 使用 `systemd` 的 `MemoryLimit` 限制单个服务内存上限
5. MySQL 等数据库服务配置合理的 `innodb_buffer_pool_size`，不要占满内存

---

## 代码文件说明

| 文件 | 说明 | 权限要求 |
|------|------|---------|
| `Code/01-cpu-memory-monitoring.sh` | CPU 与内存监控演示脚本，涵盖 uptime、top、htop、mpstat、free、vmstat、smem | 部分 sudo |
| `Code/02-disk-io-monitoring.sh` | 磁盘 IO 监控演示，iostat、iotop、dstat 使用与问题判断 | 部分 sudo |
| `Code/03-network-monitoring.sh` | 网络监控演示，iftop、nethogs、ss、sar 网络排查 | 部分 sudo |
| `Code/04-performance-tuning.md` | 性能调优指南文档，四维度排查方法、ulimit、sysctl、OOM、监控体系 | 参考 |

---

## 关键知识点总结

### 监控工具速查表

| 维度 | 实时工具 | 历史工具 | 进程级定位 |
|------|---------|---------|-----------|
| CPU | `top` / `htop` / `mpstat` | `sar -u` | `top` / `htop` / `perf` |
| 内存 | `free -h` / `vmstat` | `sar -r` | `smem` / `top` |
| 磁盘 IO | `iostat -x` / `vmstat` | `sar -b` | `iotop` |
| 网络 | `iftop` / `nethogs` / `ss` | `sar -n DEV` | `nethogs` |
| 综合 | `dstat` / `glances` / `nmon` | `sar -A` | `strace` / `ltrace` |

### top 字段含义表

| 字段 | 含义 | 关注点 |
|------|------|--------|
| `%us` | 用户态 CPU | 高 → 应用代码问题 |
| `%sy` | 内核态 CPU | 高 → 系统调用/锁 |
| `%wa` | IO 等待 | 高 → 磁盘瓶颈 |
| `%id` | 空闲 | 低 → CPU 繁忙 |
| `RES` | 常驻内存 | 进程实际内存占用 |
| `VIRT` | 虚拟内存 | 含映射库，不代表占用 |

### vmstat 字段含义表

| 字段 | 含义 | 异常判断 |
|------|------|---------|
| `r` | 运行队列 | > CPU 核数 → CPU 紧张 |
| `b` | D 状态进程 | >0 → IO 阻塞 |
| `si/so` | swap 换入换出 | >0 → 内存不足 |
| `bi/bo` | 块设备读写 | 高 → IO 密集 |
| `cs` | 上下文切换 | 过高 → 线程切换开销大 |

### iostat 字段含义表

| 字段 | 含义 | 异常判断 |
|------|------|---------|
| `%util` | 磁盘利用率 | 接近 100% → 磁盘打满 |
| `await` | IO 响应时间 | >10ms(SSD)/20ms(HDD) → 延迟高 |
| `avgqu-sz` | 队列长度 | >1 → 请求排队 |
| `r/s + w/s` | IOPS | 对照磁盘规格 |

### 性能排查流程图

```
        ┌──────────────────────────────────┐
        │        性能问题告警               │
        └──────────────┬───────────────────┘
                       ▼
              ┌────────────────┐
              │ uptime 看 load │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │  top 看 CPU    │
              │ us/sy/wa/id?   │
              └───┬────┬───┬───┘
         us 高 │  wa 高│  id 低│
               ▼      ▼      ▼
         应用代码  iostat  扩容
         strace   磁盘IO
         perf     iotop
                  │
                  ▼
         ┌────────────────┐
         │ free/vmstat    │
         │ available?     │
         │ si/so?         │
         └───┬────────┬───┘
        不足 │        │ 充足
            ▼        ▼
         加内存   iftop/ss
         优化     网络排查
```

### 内核参数调优清单

| 参数 | 默认值 | 建议值 | 作用 |
|------|--------|--------|------|
| `net.core.somaxconn` | 4096 | 65535 | 监听队列长度 |
| `net.ipv4.tcp_max_syn_backlog` | 1024 | 65535 | SYN 队列长度 |
| `net.ipv4.ip_local_port_range` | 32768-60999 | 10000-65535 | 本地端口范围 |
| `net.ipv4.tcp_tw_reuse` | 0 | 1 | 复用 TIME_WAIT |
| `net.ipv4.tcp_fin_timeout` | 60 | 15 | FIN 等待时间 |
| `vm.swappiness` | 60 | 10 | swap 倾向（越小越不爱用 swap） |
| `net.ipv4.tcp_keepalive_time` | 7200 | 600 | keepalive 探测间隔 |
| `fs.file-max` | ~十万 | 1048576 | 系统级文件描述符上限 |

---

## 实战练习

### 练习 1：性能瓶颈定位实战

**场景**：电商服务器 192.168.1.100 响应变慢，用户反馈接口超时。

**任务**：

1. 用 `uptime` 查看 load average，判断是否过载
2. 用 `top` 查看 CPU 占用最高的进程，记录 PID 与 `%CPU`
3. 用 `free -h` 查看 `available` 内存是否充足
4. 用 `iostat -x 1` 查看磁盘 `%util` 与 `await`
5. 用 `ss -s` 查看 TCP 连接数是否异常
6. 根据五步排查结果，判断瓶颈在哪个维度

**验收**：写一份排查报告，包含每步的命令输出截图与结论。

### 练习 2：内核参数调优

**场景**：Node.js 服务在高并发下出现连接超时，怀疑是内核网络参数限制。

**任务**：

1. 查看当前 `net.core.somaxconn` 与 `tcp_max_syn_backlog` 的值
2. 调整这两个参数为 65535（临时 + 永久配置）
3. 调整 `vm.swappiness` 为 10，减少 swap 使用倾向
4. 调整 `fs.file-max` 为 1048576，提高系统文件描述符上限
5. 用 `sysctl -p` 加载配置并验证

**验收**：重启系统后参数依然生效。

### 练习 3：OOM 排查与预防

**场景**：MySQL 服务在高峰期被 OOM Killer 杀掉，导致数据库中断。

**任务**：

1. 用 `dmesg | grep -i oom` 查看历史 OOM 记录，找到被杀的进程
2. 查看 MySQL 进程的 `oom_score`：`cat /proc/PID/oom_score`
3. 将 MySQL 服务的 `oom_score_adj` 设为 -500，降低被杀概率
4. 配置 systemd 服务的 `MemoryLimit`，限制单个服务内存上限
5. 编写一个监控脚本，当 `available` 内存低于 500MB 时发出告警

**验收**：配置完成后，MySQL 不再被 OOM Killer 误杀。

---

> **下一章预告**：Day13 将学习防火墙配置（ufw / firewalld / iptables）与 SSH 安全加固，构筑服务器的安全防线。
