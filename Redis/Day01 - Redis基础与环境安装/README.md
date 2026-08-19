# Day01 - Redis 基础与环境安装

## 本章简介

Redis（Remote Dictionary Server）是全球最流行的内存数据库，由 Salvatore Sanfilippo（antirez）于 2009 年开源。它以键值对（key-value）形式存储数据，全部数据驻留内存，单实例 QPS 可达 10 万以上，被广泛用于缓存、会话管理、消息队列、排行榜、限流、分布式锁等高并发场景。在现代后端架构中，Redis 几乎是仅次于关系型数据库的"第二块存储基石"。

本章作为 Redis 学习路线的起点，从"内存数据库是什么"出发，理清单线程模型与 IO 多路复用为何能带来高性能，对比 Redis 与 Memcached 的差异，并完成 Redis 7.0+ 的环境搭建与连通性验证。掌握本章后，你将拥有一台可执行命令的 Redis 实例，并理解每一条基础命令背后的设计取舍。

## 学习目标

- 理解 Redis 的定位：内存数据库、key-value 存储、丰富的数据结构
- 对比内存数据库与磁盘数据库的速度、成本与适用场景
- 理解 Redis 单线程模型为何也能达到 10 万 QPS（纯内存 + IO 多路复用 + 避免上下文切换）
- 掌握 IO 多路复用（epoll/kqueue/select）与 Redis 事件循环的关系
- 对比 Redis 与 Memcached 的核心差异
- 了解 Redis 版本演进（5.x → 6.x → 7.x）与关键特性
- 列举 Redis 的典型使用场景
- 完成 Redis 7.0+ 环境搭建（Docker 方式 + 本地安装方式）
- 使用 redis-cli 连接服务器并执行 PING / SELECT / DBSIZE / INFO / CONFIG 等基本操作
- 了解 redis.conf 核心配置参数

## 理论知识讲解

### 1. Redis 是什么

Redis 是一个开源的、基于内存的、可持久化的键值数据库。它有三个关键标签：

- **内存数据库**：数据默认全部存放在内存中，读写不经过磁盘，因此极快。
- **key-value 存储**：所有数据以键值对形式组织，Key 是字符串，Value 可以是多种数据结构。
- **丰富的数据结构**：Value 不仅支持字符串，还支持 List、Hash、Set、Sorted Set、Bitmap、HyperLogLog、Geo、Stream 等，这是 Redis 区别于其他 KV 缓存的最大特色。

与传统关系型数据库不同，Redis 不提供 SQL 查询语言，而是通过一组命令（command）操作数据。每条命令的语义明确、执行时间可控（多数为 O(1) 或 O(log N)），这是它保持高性能与稳定性的重要原因。

### 2. 内存数据库 vs 磁盘数据库

| 维度 | 内存数据库（Redis） | 磁盘数据库（MySQL） |
| --- | --- | --- |
| 数据存放位置 | 内存 | 磁盘（内存作缓存） |
| 读写速度 | 极快（微秒级，10 万 QPS+） | 较慢（毫秒级，千级 QPS） |
| 数据容量 | 受内存限制（GB 级） | 受磁盘限制（TB 级） |
| 成本 | 单位存储成本高 | 单位存储成本低 |
| 持久化 | 需额外机制（RDB/AOF） | 天然持久 |
| 数据结构 | 丰富（List/Hash/Set/ZSet…） | 二维表 + SQL |
| 事务 | 弱（MULTI/EXEC，无回滚） | 强（ACID） |
| 适用场景 | 缓存/会话/计数/排行榜/队列 | 核心交易数据/复杂查询 |

实践中两者**互补使用**：核心交易数据存 MySQL，热点缓存与会话存 Redis。Redis 做缓存不是因为它"比 MySQL 好"，而是因为它"比 MySQL 快且适合特定场景"。一旦断电，内存数据丢失，因此 Redis 的持久化机制（Day09 详讲）对生产环境至关重要。

### 3. Redis 单线程模型：为何单线程也能 10 万 QPS

一个常见的疑问是：Redis 核心命令处理是单线程的，为什么还能达到 10 万 QPS？答案有三点：

1. **纯内存操作**：数据在内存中，读写本身就是纳秒到微秒级，远快于磁盘。单线程瓶颈不在 CPU，而在 IO。
2. **IO 多路复用**：Redis 使用 epoll（Linux）/ kqueue（Mac）/ select（跨平台回退）同时监听大量客户端连接，一个线程即可处理数万并发连接，无需为每个连接分配线程。
3. **避免上下文切换与锁竞争**：多线程在线程切换、加锁解锁上会消耗 CPU，Redis 单线程模型天然避免了这些开销，命令按顺序串行执行，无需加锁。

> 注意：Redis 的"单线程"指的是**命令处理**单线程。6.0 起，网络读写（IO）引入了多线程，但命令执行仍是单线程，因此对使用者而言数据访问依然是串行、无锁的。

**单线程模型的代价**：某条命令如果执行过慢（如 `KEYS *` 在百万 Key 上扫描），会阻塞所有后续命令。这也是生产环境禁用 `KEYS` 的根本原因（Day02 详讲）。

### 4. IO 多路复用与 Redis 事件循环

IO 多路复用（IO Multiplexing）是一种"一个线程同时监听多个 IO 事件"的技术。其核心系统调用：

| 机制 | 平台 | 特点 |
| --- | --- | --- |
| select | 跨平台 | 监听数量有限（通常 1024），线性扫描，效率低 |
| poll | 跨平台 | 无数量限制，仍线性扫描 |
| epoll | Linux | 事件驱动回调，O(1) 通知，高并发首选 |
| kqueue | Mac/BSD | 类似 epoll，性能优秀 |

Redis 的事件循环（Event Loop）工作流程：

1. 主线程调用 epoll_wait 等待事件（客户端连接、读、写）。
2. 有事件就绪时，依次处理：接受新连接 → 读取命令 → 解析 → 执行命令 → 写回响应。
3. 处理完一批事件后，再回到 epoll_wait 继续等待。

整个过程中只有一个线程在工作，命令按到达顺序串行执行，无需加锁。这种模型在"请求量极大但单次操作极快"的场景下效率极高。

### 5. Redis vs Memcached

| 维度 | Redis | Memcached |
| --- | --- | --- |
| 数据结构 | 丰富（String/List/Hash/Set/ZSet/Stream…） | 仅 String |
| 持久化 | 支持 RDB / AOF | 不支持，重启即丢 |
| 集群 | 原生 Cluster + 主从 + 哨兵 | 客户端分片 |
| 单/多线程 | 命令单线程（6.0 IO 多线程） | 多线程 |
| 内存管理 | 自主 jemalloc | slab allocator |
| 单值上限 | String 512MB | 1MB |
| 适用场景 | 缓存 + 数据结构 + 消息队列 | 纯 KV 缓存 |

Memcached 设计更简单，纯缓存场景下性能稳定；Redis 功能更全面，几乎是"瑞士军刀"，因此成为当前主流选择。

### 6. Redis 版本演进

| 版本 | 发布年份 | 关键特性 | 维护状态 |
| --- | --- | --- | --- |
| 5.0 | 2018 | Stream 类型、集群管理工具改进 | 已 EOL |
| 6.0 | 2020 | 多线程 IO、ACL 权限、客户端缓存、RESP3 | 已 EOL |
| 6.2 | 2021 | 大量命令增强（COPY/SMISMEMBER/GEOSEARCH） | 已 EOL |
| 7.0 | 2022 | Function（替代 EVAL）、Sharded Pub/Sub、listpack 全面替换 ziplist | 长期支持 |
| 7.2 | 2023 | 多核 IO 性能优化、Bug 修复 | 当前稳定 |
| 7.4 | 2024 | Hash/List 性能改进、新命令 | 最新 |

**Redis 7.x 重大变化**：

- **Function**：用持久化的 Lua 函数库替代临时 `EVAL`，脚本随数据持久化。
- **Sharded Pub/Sub**：分片发布订阅，消息只在所属槽位的节点传播，降低集群广播开销。
- **listpack 全面替代 ziplist**：修复 ziplist 连锁更新问题，小数据结构更稳定。
- **ACL（6.0 引入）**：用户级权限控制，可限制命令与 Key 访问范围。
- **多线程 IO（6.0 引入）**：默认关闭，开启后可显著提升网络吞吐。

> 本教程所有脚本基于 **Redis 7.0+**，推荐 7.2 或 7.4。

### 7. Redis 使用场景

| 场景 | 典型用法 | 涉及数据类型 |
| --- | --- | --- |
| 缓存 | 商品/用户详情缓存 | String / Hash |
| 会话管理 | 登录会话 + TTL | String / Hash |
| 消息队列 | 订单事件流 | List / Stream |
| 排行榜 | 销量/积分排行 | Sorted Set |
| 限流 | API 调用频次限制 | String（INCR + EXPIRE） |
| 分布式锁 | 库存扣减互斥 | String（SET NX EX） |
| 计数器 | 页面浏览量 | String（INCR） |
| 去重 | UV 独立访客 | Set / HyperLogLog |
| 标签/关系 | 共同关注 | Set（SINTER） |
| 地理位置 | 附近门店 | Geo |

本板块全程围绕**电商平台 Redis 层**展开，逐天把这些场景落到具体命令上。

## 环境搭建

本教程提供两种安装方式，**推荐 Docker 方式**（隔离干净、可重置）。详细步骤见 `Code/README.md`。

### 方式一：Docker 部署（推荐）

```bash
# 1. 拉取 Redis 7.x 镜像
docker pull redis:7

# 2. 启动容器（端口 6379，无密码，学习用）
docker run -d \
  --name redis-learn \
  -p 6379:6379 \
  -v redis-learn-data:/data \
  --restart=unless-stopped \
  redis:7

# 3. 查看容器状态
docker ps
docker logs redis-learn

# 4. 进入容器执行 redis-cli
docker exec -it redis-learn redis-cli

# 5. 在宿主机管道执行脚本
docker exec -i redis-learn redis-cli < "Day01 - Redis基础与环境安装/Code/00-environment-check.redis"

# 6. 带密码启动（生产推荐）
docker run -d --name redis-learn \
  -p 6379:6379 \
  -v redis-learn-data:/data \
  redis:7 --requirepass yourpassword

# 7. 连接带密码的 Redis
docker exec -it redis-learn redis-cli -a yourpassword

# 8. 停止 / 启动 / 删除容器
docker stop redis-learn
docker start redis-learn
docker rm -f redis-learn          # 不会删除数据卷
docker volume rm redis-learn-data # 彻底清除数据
```

### 方式二：本地安装

**Linux（Ubuntu/Debian）**：

```bash
sudo apt update
sudo apt install redis-server
redis-server --version          # 确认版本
redis-cli ping                  # 测试服务
```

**Linux（源码编译，推荐用于获取最新版）**：

```bash
wget https://download.redis.io/releases/redis-7.2.5.tar.gz
tar xzf redis-7.2.5.tar.gz
cd redis-7.2.5
make
sudo make install
redis-server                    # 默认前台启动
```

**macOS（Homebrew）**：

```bash
brew install redis
brew services start redis
redis-cli ping
```

**Windows**：

Redis 官方不直接支持 Windows，推荐使用 WSL2 或 Docker。微软曾维护过移植版但已停止更新，不建议生产使用。

### 验证安装

```bash
redis-cli
127.0.0.1:6379> PING
PONG
127.0.0.1:6379> INFO server
# Server
redis_version:7.2.x
...
```

看到 `PONG` 与 `redis_version:7.2.x` 即表示环境就绪。

## 连接与基本操作

### 连接服务器

```bash
redis-cli                          # 默认连接 127.0.0.1:6379
redis-cli -h 127.0.0.1 -p 6379     # 指定地址端口
redis-cli -a yourpassword          # 带密码连接
redis-cli -n 1                     # 直接选择 DB 1
redis-cli --stat                   # 实时监控统计信息
redis-cli MONITOR                  # 实时打印所有命令（调试用）
```

### 基本命令演示

```bash
# 1. 测试连通性
PING                               # 返回 PONG

# 2. 选择数据库（默认 0，共 16 个：0-15）
SELECT 0
SELECT 15

# 3. 查看当前库 Key 数量
DBSIZE

# 4. 查看服务器信息
INFO server                        # 服务端信息
INFO memory                        # 内存信息
INFO stats                         # 统计信息

# 5. 查看 / 修改配置
CONFIG GET maxmemory               # 查看最大内存
CONFIG GET databases               # 查看数据库数量
CONFIG SET maxmemory 256mb         # 设置最大内存（生产慎用，重启失效）

# 6. 清空数据（危险！仅开发调试用）
FLUSHDB                            # 清空当前库
FLUSHALL                           # 清空所有库（极端危险）
```

> `CONFIG SET` 修改的配置在 Redis 重启后失效，永久生效需修改 `redis.conf` 并重启。

## Redis 配置文件 redis.conf 核心参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `bind` | 127.0.0.1 | 监听地址，生产应限制为内网 |
| `port` | 6379 | 监听端口 |
| `requirepass` | 空 | 访问密码，生产必设 |
| `databases` | 16 | 数据库数量 |
| `maxmemory` | 0（不限） | 最大内存上限，缓存场景必设 |
| `maxmemory-policy` | noeviction | 淘汰策略（Day12 详讲） |
| `save` | 3600 1 / 300 100 / 60 10000 | RDB 触发条件 |
| `appendonly` | no | 是否开启 AOF |
| `appendfsync` | everysec | AOF 刷盘策略 |
| `timeout` | 0 | 客户端空闲超时（0 表示不超时） |
| `tcp-keepalive` | 300 | TCP 保活探测间隔 |
| `loglevel` | notice | 日志级别 |
| `dir` | ./ | 工作目录（RDB/AOF 文件位置） |

启动时指定配置文件：

```bash
redis-server /etc/redis/redis.conf
```

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/00-environment-check.redis` | 环境检查：PING、INFO server、CONFIG、DBSIZE、SELECT 0-15 |
| `Code/01-hello-redis.redis` | 第一个 Redis 命令：SET/GET/DEL/EXISTS/EXPIRE/TTL 等基础流程 |
| `Code/README.md` | 环境配置详细指南（Docker、本地安装、redis-cli、图形客户端） |

执行方式：

```bash
# 方式一：管道执行整个文件
redis-cli < "Day01 - Redis基础与环境安装/Code/00-environment-check.redis"

# 方式二：在 redis-cli 中逐行复制粘贴
redis-cli
127.0.0.1:6379> PING

# 方式三：Docker 环境
docker exec -i redis-learn redis-cli < "Day01 - Redis基础与环境安装/Code/00-environment-check.redis"
```

## 关键知识点总结

1. **Redis 定位**：内存型 key-value 数据库，数据驻留内存，单实例 10 万 QPS+。
2. **内存 vs 磁盘**：内存快但贵且易失，磁盘慢但便宜且持久，两者互补。
3. **单线程高性能三要素**：纯内存 + IO 多路复用 + 避免上下文切换与锁竞争。
4. **IO 多路复用**：epoll/kqueue/select，一个线程处理数万连接，Redis 事件循环核心。
5. **Redis vs Memcached**：Redis 数据结构丰富、支持持久化与集群，是当前主流。
6. **版本演进**：5.x 引入 Stream，6.x 多线程 IO + ACL，7.x Function + Sharded Pub/Sub + listpack。
7. **典型场景**：缓存、会话、消息队列、排行榜、限流、分布式锁、计数器、去重。
8. **基础命令**：PING 测连接、SELECT 选库、DBSIZE 看 Key 数、INFO 看状态、CONFIG 配置、FLUSHDB/FLUSHALL 清库。
9. **redis.conf**：bind/port/requirepass/maxmemory/appendonly 等是生产必懂参数。
10. **环境验证**：`PING` 返回 `PONG`、`INFO server` 显示 `7.2.x` 即合格。

## 实战练习

1. **环境就绪验证**
   - 用 Docker 启动 Redis 7 容器，端口 6379，数据卷 `redis-learn-data`。
   - 用 `redis-cli ping` 确认返回 `PONG`。
   - 管道执行 `00-environment-check.redis`，截图保留 `redis_version`、`maxmemory`、`databases` 三项结果。

2. **基础命令熟悉**
   - 连入 redis-cli，依次执行：`SELECT 0` → `DBSIZE` → `INFO server` → `CONFIG GET maxmemory` → `SELECT 1` → `DBSIZE`。
   - 思考：为什么刚启动的 Redis 每个 DB 的 Key 数都是 0？16 个数据库之间数据是否隔离？
   - 执行 `CONFIG SET maxmemory 100mb` 后再 `CONFIG GET maxmemory`，观察变化（注意：重启后失效）。

3. **第一个电商 Key**
   - 执行 `SET cache:product:1 "iPhone 15"` 写入一条商品缓存。
   - 执行 `GET cache:product:1` 确认能读回。
   - 执行 `EXPIRE cache:product:1 60` 设置 60 秒过期，再用 `TTL cache:product:1` 观察剩余秒数。
   - 等待 60 秒后再次 `GET cache:product:1`，观察返回值（应为 nil），体会过期机制。
