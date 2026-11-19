# Day05 - 进程管理与服务管理

进程是 Linux 系统运行的基本单位，每一条执行的命令、每一个后台守护进程都对应一个进程；而 systemd 则是现代 Linux 发行版（Ubuntu / CentOS / Debian 等）默认的服务管理器，负责在系统启动时并行拉起各项服务并管理其整个生命周期。对后端工程师而言，电商后端的 Node.js 进程为何被 OOM 杀掉、Nginx 服务为何 reload 后不生效、MySQL 服务崩溃后为何没有自动拉起——这些问题都需要通过进程管理与服务管理来回答。本章将围绕电商项目服务器（`192.168.1.100`，部署路径 `/opt/ecommerce/`）系统讲解进程查看、进程控制、信号机制、systemd 服务管理与 journalctl 日志查询，并为 Node.js 后端编写一份可上生产的 systemd 单元文件。

---

## 学习目标

完成本章后，你应该能够：

- 理解程序与进程的区别，能读懂 `ps aux`、`top` 输出中每个字段的含义
- 熟练使用 `kill`、`killall`、`pkill` 向进程发送信号，并理解 SIGHUP / SIGTERM / SIGKILL 的差异
- 掌握 `&`、`nohup`、`jobs`、`bg`、`fg` 等后台任务管理手段，能让进程在 SSH 断开后继续运行
- 使用 `nice` / `renice` 调整进程优先级
- 通过 `/proc` 文件系统查看进程的运行时信息
- 熟练使用 `systemctl` 管理服务的启动、停止、重载、开机自启
- 使用 `journalctl` 按服务、时间、级别、PID 多维查询日志
- 编写一份完整的 systemd 自定义服务单元文件，并理解 `[Unit]`、`[Service]`、`[Install]` 三段结构
- 区分 `systemctl` 与旧版 `service` 命令的关系

---

## 理论知识讲解

### 一、进程管理

#### 1.1 进程基本概念

| 概念 | 说明 |
|------|------|
| 程序 | 存储在磁盘上的可执行文件（静态），如 `/usr/bin/node` |
| 进程 | 程序运行后的实例（动态），占用内存、CPU 等资源 |
| PID | 进程 ID，唯一标识一个进程，由内核分配 |
| PPID | 父进程 ID，启动该进程的上一级进程 |
| UID / GID | 启动该进程的用户 ID / 组 ID |
| 守护进程 | 在后台运行的特殊进程，通常以 `d` 结尾（如 `sshd`、`mysqld`） |

**进程状态码**（`ps` 与 `top` 输出中的 STAT 字段）：

| 状态码 | 名称 | 说明 |
|--------|------|------|
| R | Running / Runnable | 正在运行或在就绪队列等待 CPU |
| S | Interruptible Sleep | 可中断睡眠，等待事件（最常见） |
| D | Uninterruptible Sleep | 不可中断睡眠，通常在等待磁盘 IO |
| Z | Zombie | 僵尸进程，已退出但父进程未回收 |
| T | Stopped / Traced | 停止状态，如被 `Ctrl+Z` 挂起或被调试器接管 |
| I | Idle | 空闲的内核线程 |

> 僵尸进程（Z）本身不占用内存，但占用 PID 资源，过多会导致无法创建新进程。解决办法是杀死其父进程或让父进程调用 `wait()` 回收。

#### 1.2 进程查看命令

```bash
# 查看所有进程（BSD 风格，最常用）
ps aux

# 查看所有进程（System V 风格，显示 PPID）
ps -ef

# 配合 grep 过滤特定进程
ps -ef | grep nginx

# 以树形结构显示进程（-p 显示 PID）
pstree -p

# 查找指定名称进程的 PID（-l 显示名称、-u 指定用户、-t 指定终端）
pgrep -l nginx
pgrep -u deploy -l node

# 按名称直接取 PID
pidof nginx
```

**`top` 交互式进程监控**：

```bash
top
```

进入后可见关键字段：

| 字段 | 含义 |
|------|------|
| VIRT | 进程申请的虚拟内存总量（含映射文件、交换区） |
| RES | 实际使用的物理内存 |
| SHR | 共享内存 |
| %CPU | CPU 占用率 |
| %MEM | 物理内存占用率 |
| TIME+ | 累计 CPU 时间 |

`top` 内交互命令：

| 按键 | 功能 |
|------|------|
| `P` | 按 CPU 占用排序 |
| `M` | 按内存占用排序 |
| `k` | 输入 PID 杀死进程 |
| `1` | 展开各 CPU 核心使用情况 |
| `q` | 退出 |
| `h` | 帮助 |

`htop` 是 `top` 的增强版，支持颜色、横向滚动、鼠标点击操作：

```bash
# 安装
sudo apt install -y htop

# 启动
htop
```

#### 1.3 进程控制：信号机制

`kill` 命令本质上是通过 PID 向进程发送信号。先用 `kill -l` 查看所有信号：

```bash
kill -l
```

常用信号速查：

| 信号 | 编号 | 名称 | 含义 | 是否可被捕获/忽略 |
|------|------|------|------|-------------------|
| SIGHUP | 1 | 挂起 | 终端断开时发送；常用于让守护进程重载配置 | 可 |
| SIGINT | 2 | 中断 | `Ctrl+C` 触发 | 可 |
| SIGKILL | 9 | 强制杀死 | 内核直接清理，进程无法捕获 | 不可 |
| SIGTERM | 15 | 终止 | 默认信号，允许进程优雅退出 | 可 |
| SIGSTOP | 19 | 停止 | 暂停进程（不可被捕获） | 不可 |
| SIGCONT | 18 | 继续 | 恢复被 SIGSTOP 暂停的进程 | 可 |

```bash
# 优雅终止（推荐）
kill -15 1234
kill -TERM 1234
kill 1234        # 默认即 SIGTERM

# 强制杀死（最后手段，可能丢数据）
kill -9 1234
kill -KILL 1234

# 重载配置文件（不重启进程）
kill -HUP $(pidof nginx)

# 按名称杀进程（匹配精确名称）
killall node

# 按模式杀进程（匹配正则）
pkill -f "node /opt/ecommerce"
```

> 生产环境优先使用 `kill -15`，给进程处理善后（关闭连接、刷盘）的机会；`kill -9` 可能导致数据库损坏、文件半写入。

#### 1.4 进程优先级：nice / renice

`nice` 值范围 `-20 ~ 19`，**值越低优先级越高**。默认 `0`，普通用户只能调高（降低优先级），root 可调低。

```bash
# 以 nice 值 10 启动命令
nice -n 10 tar -czf backup.tar.gz /opt/ecommerce

# 调整已运行进程的优先级（PID 1234 调到 -5）
sudo renice -5 1234

# 按用户和进程名批量调整
sudo renice +5 -u deploy -p $(pgrep node)
```

#### 1.5 后台任务管理

```bash
# 后台运行（命令尾部加 &）
node /opt/ecommerce/backend/dist/main.js &

# 输出任务编号和 PID，例如 [1] 12345

# 查看当前 Shell 的后台任务
jobs

# 把最近一个挂起的任务放到后台继续运行
bg

# 把后台任务调回前台
fg %1

# SSH 断开后继续运行（忽略 SIGHUP，输出重定向到 nohup.out）
nohup node /opt/ecommerce/backend/dist/main.js > /opt/ecommerce/logs/app.log 2>&1 &

# 让已运行的任务脱离当前 Shell（取消 HUP 关联）
disown -h %1
```

| 方式 | 退出 Shell 后是否继续 | 输出处理 |
|------|----------------------|---------|
| `command &` | 否（受 SIGHUP 影响） | 终端 |
| `nohup command &` | 是 | `nohup.out` 或重定向文件 |
| `disown` | 是 | 不变 |
| `systemd` 服务 | 是（推荐生产） | journalctl / 配置文件 |

#### 1.6 /proc 文件系统

`/proc` 是内核暴露的虚拟文件系统，每个进程都有 `/proc/[PID]/` 目录：

| 文件 | 内容 |
|------|------|
| `status` | 进程状态（名称、PID、内存、信号掩码） |
| `cmdline` | 启动命令（参数以 `\0` 分隔） |
| `environ` | 环境变量（以 `\0` 分隔） |
| `cwd` | 当前工作目录的符号链接 |
| `exe` | 可执行文件的符号链接 |
| `fd/` | 打开的文件描述符目录 |
| `limits` | 资源限制（文件描述符数、CPU 时间等） |

```bash
# 查看进程的完整启动命令（\0 替换为空格便于阅读）
cat /proc/$(pidof nginx)/cmdline | tr '\0' ' '; echo

# 查看进程环境变量
cat /proc/1234/environ | tr '\0' '\n'

# 查看进程的文件描述符上限
cat /proc/1234/limits | grep "open files"

# 查看进程打开的所有文件
ls -l /proc/1234/fd/
```

---

### 二、systemd 服务管理

#### 2.1 systemd 简介

`systemd` 是现代 Linux 的初始化系统（PID 1），取代了传统的 SysVinit。相比 SysVinit 串行启动脚本，systemd 具有以下优势：

- **并行启动**：通过 socket 激活与依赖关系图，启动速度大幅提升
- **依赖管理**：声明式描述服务依赖（`Requires` / `Wants` / `After`）
- **统一日志**：所有服务日志统一由 `journald` 收集，可通过 `journalctl` 查询
- **资源隔离**：基于 cgroup，可对服务做 CPU、内存、IO 限制
- **按需启动**：socket / D-Bus / path 激活机制

#### 2.2 systemctl 核心命令

```bash
# 服务生命周期管理
sudo systemctl start nginx          # 启动
sudo systemctl stop nginx           # 停止
sudo systemctl restart nginx        # 重启（中断服务）
sudo systemctl reload nginx         # 重载配置（不中断）
sudo systemctl status nginx         # 查看状态

# 开机自启管理
sudo systemctl enable nginx         # 开机自启
sudo systemctl disable nginx        # 禁用开机自启
sudo systemctl enable --now nginx   # 启动并设置开机自启
sudo systemctl disable --now nginx  # 停止并禁用开机自启

# 状态查询
systemctl is-active nginx           # 是否运行中（输出 active/inactive）
systemctl is-enabled nginx          # 是否开机自启（输出 enabled/disabled）
systemctl is-failed nginx           # 是否进入失败状态

# 列表查询
systemctl list-units --type=service --state=running          # 正在运行的服务
systemctl list-units --type=service --state=failed           # 失败的服务
systemctl list-unit-files --type=service                     # 所有服务单元文件

# 单元文件变更后必须执行
sudo systemctl daemon-reload

# 彻底禁用（防止被其他服务激活）
sudo systemctl mask nginx
sudo systemctl unmask nginx
```

#### 2.3 journalctl 日志查询

```bash
# 查看某个服务的日志
journalctl -u nginx

# 实时跟踪日志（类似 tail -f）
journalctl -u nginx -f

# 按时间范围过滤
journalctl --since today
journalctl --since "2026-07-29 09:00:00" --until "2026-07-29 12:00:00"
journalctl -u nginx --since "1 hour ago"

# 按级别过滤（emerg/alert/crit/err/warning notice/info/debug）
journalctl -p err
journalctl -u nginx -p warning

# 不分页显示最近 100 条
journalctl -u nginx --no-pager -n 100

# 按 PID 查询
journalctl _PID=1234

# 查看内核日志
journalctl -k

# 显示日志的元数据（更详细的字段）
journalctl -o verbose -u nginx

# 磁盘占用与清理
journalctl --disk-usage
sudo journalctl --vacuum-time=7d      # 只保留最近 7 天
sudo journalctl --vacuum-size=500M    # 只保留 500MB
```

#### 2.4 systemd 单元文件结构

单元文件位置：

| 路径 | 用途 |
|------|------|
| `/etc/systemd/system/` | 管理员自定义（优先级最高） |
| `/run/systemd/system/` | 运行时临时单元 |
| `/usr/lib/systemd/system/` | 软件包安装时携带 |

**完整单元文件结构示例**：

```ini
[Unit]
Description=Ecommerce Backend Service
Documentation=https://github.com/your-org/ecommerce
After=network.target mysql.service redis.service
Wants=redis.service
Requires=mysql.service

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/opt/ecommerce/backend
Environment=NODE_ENV=production
Environment=PORT=3000
EnvironmentFile=-/opt/ecommerce/backend/.env
ExecStart=/usr/bin/node /opt/ecommerce/backend/dist/main.js
ExecStop=/bin/kill -TERM $MAINPID
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
TimeoutStopSec=30
KillMode=mixed
KillSignal=SIGTERM

# 资源限制
LimitNOFILE=65536
MemoryMax=1G
CPUQuota=200%

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ecommerce-backend

[Install]
WantedBy=multi-user.target
```

字段说明：

**[Unit] 段**：

| 字段 | 说明 |
|------|------|
| Description | 单元的可读描述 |
| Documentation | 文档 URL |
| After | 当前单元在这些单元之后启动（仅顺序，不强制依赖） |
| Before | 当前单元在这些单元之前启动 |
| Wants | 弱依赖：启动当前单元时也尝试启动这些单元，失败不影响 |
| Requires | 强依赖：依赖单元启动失败则当前单元也失败 |
| Conflicts | 互斥单元 |

**[Service] 段**：

| 字段 | 说明 |
|------|------|
| Type | 启动类型：simple（默认，前台）/ forking（fork 出守护进程）/ oneshot（一次性任务）/ notify |
| User / Group | 运行身份 |
| WorkingDirectory | 工作目录 |
| Environment | 直接设置环境变量 |
| EnvironmentFile | 从文件加载环境变量（前缀 `-` 表示文件不存在不报错） |
| ExecStart | 启动命令 |
| ExecStop | 停止命令（不指定则发 KillSignal） |
| ExecReload | 重载命令 |
| Restart | 重启策略：no / on-success / on-failure / on-abnormal / always |
| RestartSec | 重启间隔秒数 |
| TimeoutStopSec | 停止超时（超时后发 SIGKILL） |
| KillMode | 进程组杀灭方式：control-group / process / mixed |
| KillSignal | 停止信号，默认 SIGTERM |

**[Install] 段**：

| 字段 | 说明 |
|------|------|
| WantedBy | 启用时的弱依赖目标，最常用 `multi-user.target`（多用户模式，等同运行级 3） |
| RequiredBy | 启用时的强依赖目标 |
| Alias | 别名 |

**自定义服务上线流程**：

```bash
# 1. 拷贝单元文件到 systemd 目录
sudo cp ecommerce-backend.service /etc/systemd/system/

# 2. 重新加载 systemd 配置（识别新文件）
sudo systemctl daemon-reload

# 3. 启用并启动
sudo systemctl enable --now ecommerce-backend

# 4. 验证
sudo systemctl status ecommerce-backend
journalctl -u ecommerce-backend -f
```

#### 2.5 service 命令（旧版兼容）

`service` 是 SysVinit 时代的兼容命令，内部会转发到 `systemctl`：

```bash
service nginx start       # 等同 systemctl start nginx
service nginx status
service nginx restart

# 等同于直接调用 SysVinit 脚本
/etc/init.d/nginx restart
```

新脚本与服务管理**一律使用 `systemctl`**，`service` 仅在旧系统或兼容脚本中见到。

---

## 代码文件说明

| 文件 | 用途 | 是否需 root |
|------|------|------------|
| `Code/01-process-management.sh` | 演示 ps、pstree、top 字段、kill 信号、nohup、jobs/bg/fg、nice/renice、/proc 查询 | 部分命令需要 |
| `Code/02-systemd-service-management.sh` | 演示 systemctl 生命周期、状态查询、列表查询、journalctl 日志查询、enable/disable | 是 |
| `Code/ecommerce-backend.service` | 电商 Node.js 后端的 systemd 单元文件，可直接拷贝到 `/etc/systemd/system/` 上线 | 是（部署时） |

---

## 关键知识点总结

### 1. 进程信号速查表

| 信号 | 编号 | 触发方式 | 推荐用途 |
|------|------|---------|---------|
| SIGHUP | 1 | 终端断开 / 手动发送 | 重载守护进程配置 |
| SIGINT | 2 | `Ctrl+C` | 交互式终止前台进程 |
| SIGKILL | 9 | `kill -9` | 强制结束（最后手段） |
| SIGTERM | 15 | `kill` 默认 | 优雅终止（推荐） |
| SIGSTOP | 19 | `Ctrl+Z` | 暂停进程 |
| SIGCONT | 18 | `bg` / `kill -18` | 恢复暂停的进程 |

### 2. systemctl 命令速查表

| 命令 | 用途 |
|------|------|
| `systemctl start X` | 启动服务 |
| `systemctl stop X` | 停止服务 |
| `systemctl restart X` | 重启服务 |
| `systemctl reload X` | 重载配置 |
| `systemctl status X` | 查看状态 |
| `systemctl enable X` | 开机自启 |
| `systemctl disable X` | 禁用开机自启 |
| `systemctl enable --now X` | 启动并设置开机自启 |
| `systemctl is-active X` | 是否运行 |
| `systemctl is-enabled X` | 是否开机自启 |
| `systemctl list-units --type=service --state=running` | 运行中的服务 |
| `systemctl list-unit-files --type=service` | 所有单元文件 |
| `systemctl daemon-reload` | 重载单元文件 |
| `systemctl mask X` | 彻底禁用 |
| `systemctl unmask X` | 取消彻底禁用 |

### 3. systemd 单元文件结构表

| 段 | 关键字段 | 用途 |
|----|---------|------|
| [Unit] | Description / Documentation | 元信息 |
| [Unit] | After / Before | 启动顺序 |
| [Unit] | Wants / Requires / Conflicts | 依赖关系 |
| [Service] | Type | 启动类型（simple/forking/oneshot/notify） |
| [Service] | User / Group / WorkingDirectory | 运行身份与环境 |
| [Service] | ExecStart / ExecStop / ExecReload | 启停重载命令 |
| [Service] | Restart / RestartSec | 重启策略 |
| [Service] | Environment / EnvironmentFile | 环境变量 |
| [Service] | LimitNOFILE / MemoryMax / CPUQuota | 资源限制 |
| [Install] | WantedBy | 启用时的依赖目标（一般 multi-user.target） |

### 4. journalctl 常用选项表

| 选项 | 用途 |
|------|------|
| `-u 服务` | 按服务过滤 |
| `-f` | 实时跟踪 |
| `--since 时间` / `--until 时间` | 时间范围 |
| `-p 级别` | 按级别过滤（err / warning / info…） |
| `-n N` | 最近 N 条 |
| `--no-pager` | 不分页（脚本中使用） |
| `_PID=xxx` | 按 PID 过滤 |
| `-k` | 内核日志 |
| `-o verbose` | 详细字段 |
| `--disk-usage` | 磁盘占用 |
| `--vacuum-time=7d` | 清理 7 天前日志 |
| `--vacuum-size=500M` | 限制日志总量 |

---

## 实战练习

### 练习 1：用 systemd 接管 Node.js 后端

电商后端目前用 `nohup` 在 SSH 会话中启动，运维同事每次重启服务器都需要手动拉起。请：

1. 将 `Code/ecommerce-backend.service` 拷贝到 `/etc/systemd/system/`
2. 执行 `daemon-reload` 让 systemd 识别
3. 用 `enable --now` 启动并设置开机自启
4. 用 `systemctl status` 与 `journalctl -u` 验证服务运行状态
5. 故意 `kill -9` 杀死 node 主进程，观察 systemd 是否会按 `Restart=always` 自动拉起

**验收标准**：服务异常退出后 5 秒内自动恢复；服务器重启后服务自动运行。

### 练习 2：定位线上 OOM 进程

某天 `journalctl -u ecommerce-backend` 显示 node 进程被 OOM Killer 杀掉：

1. 用 `journalctl -k | grep -i "out of memory"` 找到 OOM 触发记录
2. 用 `ps aux --sort=-rss | head` 找出当前占用内存最高的进程
3. 给 node 服务在单元文件中加上 `MemoryMax=1G` 限制
4. 重启服务，用 `systemctl show ecommerce-backend -p MemoryCurrent` 查看内存使用

### 练习 3：信号对比实验

写一个简单的 bash 脚本捕获 SIGTERM、SIGINT、SIGHUP 三种信号并打印日志，分别用 `kill -15`、`kill -2`、`kill -1` 测试脚本输出，观察哪些信号被捕获、`kill -9` 是否还能被捕获，并记录到 `/tmp/signal-test.log`。
