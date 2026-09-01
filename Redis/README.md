# Redis 学习指南

> 系统化掌握内存数据库核心能力，为后端缓存、消息队列与高并发架构奠定基础

> 共 12 天，覆盖从环境搭建、数据类型、功能特性到高可用与性能优化的完整知识体系

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

本板块是全栈学习系列的**缓存与高并发基石**。如果说 MySQL 解决的是"数据存哪里"的问题，Redis 解决的是"数据怎么快"的问题。Redis 是全球最流行的内存数据库，凭借纯内存操作和单线程模型，单实例 QPS 可达 10 万+，广泛用于缓存、会话管理、消息队列、排行榜、分布式锁、限流等场景。

**学习目标**：完成本板块后，你应能：
- 熟练使用 Redis 全部核心数据类型（String/List/Hash/Set/ZSet）及其应用场景
- 掌握 Bitmap、HyperLogLog、Geo、Stream 等高级类型的用法
- 理解 Redis 过期策略、淘汰机制，合理规划内存
- 用 Pub/Sub 与 Stream 实现消息通信
- 用事务与 Lua 脚本保证操作原子性
- 理解 RDB 与 AOF 两种持久化方式的取舍
- 部署主从复制、哨兵 Sentinel 与集群 Cluster
- 设计缓存模式（Cache-Aside/Write-Through）、解决缓存三大问题
- 实现分布式锁、限流器、排行榜等经典组件

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行命令脚本 + 实战练习
- 全程使用统一的电商缓存场景，前后连贯
- 所有命令脚本可在 Redis 7.0+ 直接执行
- 紧扣工程化视角，多处铺垫后端集成与 AI 应用场景

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| 基础数据结构 | 了解即可 | 知道"字符串、列表、哈希表、集合、有序集合"概念 |
| 命令行操作 | 基础 | 能用终端执行命令、配置环境变量 |
| 网络概念 | 基础 | TCP、端口、客户端-服务端模型 |
| MySQL 板块 | 已完成更好 | 缓存与数据库的配合场景需要数据库知识 |

**环境准备**：
- Redis 7.0+（推荐 7.2 或 7.4，本板块以 7.x 为基准）
- 命令行客户端 `redis-cli`（随 Redis Server 安装）或图形客户端（RedisInsight / Another Redis Desktop Manager / Redis Commander，任选其一）
- 可选：Docker（用容器快速启动 Redis，无需本地安装）

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Redis 学习路线（12天）                         │
└─────────────────────────────────────────────────────────────────┘

阶段一：基础与环境（Day01-Day02）
┌──────────────┬──────────────┐
│  Day01 基础  │  Day02 全局  │
│  与环境      │  命令与Key   │
│              │  管理        │
└──────┬───────┴──────┬───────┘
       │              │
       ▼              ▼
阶段二：数据类型（Day03-Day06）
┌────────────┬────────────┬────────────┬────────────┐
│ Day03      │ Day04      │ Day05     │ Day06       │
│ String与   │ Hash与Set │ Sorted    │ 高级数据   │
│ List       │           │ Set       │ 类型       │
└─────┬──────┴─────┬──────┴─────┬─────┴─────┬──────┘
      │            │            │           │
      ▼            ▼            ▼           ▼
阶段三：功能特性（Day07-Day09）
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  Day07 发布订阅与    │  Day08 事务与        │  Day09 持久化机制     │
│  Stream 消息队列     │  Lua 脚本            │  （RDB 与 AOF）       │
└──────────┬───────────┴──────────┬───────────┴──────────┬───────────┘
           │                      │                      │
           ▼                      ▼                      ▼
阶段四：架构与应用（Day10-Day12）
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  Day10 主从复制与    │  Day11 缓存模式与    │  Day12 内存管理与     │
│  高可用              │  分布式锁            │  性能优化             │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

---

## 示例场景

本板块全程围绕一个**电商平台的 Redis 层**展开，配合 MySQL 板块的 `ecommerce` 数据库，覆盖缓存、会话、购物车、排行榜、限流、分布式锁等经典场景。

### Key 命名规范

```
统一前缀规范：业务域:对象:标识

缓存类：
  cache:product:{id}          → 商品详情缓存（String/Hash）
  cache:category:{id}         → 分类树缓存（Hash）
  cache:user:{id}             → 用户信息缓存（Hash）

会话类：
  session:{token}             → 用户登录会话（Hash + TTL）
  online:users                → 在线用户集合（Set/Bitmap）

购物车：
  cart:{user_id}              → 购物车（Hash: product_id → quantity）

排行榜：
  leaderboard:sales:daily     → 每日销量排行（Sorted Set）
  leaderboard:sales:monthly   → 月度销量排行

限流：
  rate:limit:{user_id}:{api}  → API 限流计数器

库存锁：
  stock:lock:{product_id}     → 库存分布式锁

消息：
  stream:orders               → 订单事件流
  pubsub:notifications        → 实时通知频道

计数器：
  counter:page:views:{page}   → 页面浏览量
  counter:uv:{date}           → 独立访客（HyperLogLog）
```

> 各天的命令脚本围绕这些 Key 展开，逐步构建完整的电商 Redis 层。

---

## 每日内容详表

### 阶段一：基础与环境

#### Day01 - Redis基础与环境安装
- **核心**：Redis 简介与定位、内存数据库 vs 磁盘数据库、单线程模型与 IO 多路复用、Redis vs Memcached、安装方式（Docker/源码编译/包管理器）、redis-cli 连接、CONFIG、INFO、PING、SELECT、DBSIZE、FLUSHDB/FLUSHALL
- **代码**：`00-environment-check.redis` / `01-hello-redis.redis` / `README.md`（环境配置指南）
- **重点**：理解单线程为何高性能

#### Day02 - 全局命令与Key管理
- **核心**：KEYS / SCAN、TYPE、EXISTS、DEL、RENAME、EXPIRE / PEXPIRE / EXPIREAT、TTL / PTTL、PERSIST、RANDOMKEY、DBSIZE、SELECT（多数据库）、MOVE、OBJECT ENCODING、Key 命名规范、过期策略（惰性删除 + 定期删除）
- **代码**：`01-global-commands.redis` / `02-key-expiration.redis`
- **重点**：KEYS 的危险性与 SCAN 替代、过期底层机制

---

### 阶段二：数据类型

#### Day03 - String与List数据类型
- **核心**：
  - String：SET/GET/SETEX/PSETEX/SETNX/MSET/MGET/APPEND/STRLEN/INCR/DECR/INCRBY/DECRBY/INCRBYFLOAT/GETRANGE/SETRANGE/GETSET、应用场景（缓存/计数器/分布式锁基础/限流）
  - List：LPUSH/RPUSH/LPOP/RPOP/LRANGE/LLEN/LINDEX/LSET/LINSERT/LREM/LTRIM/BLPOP/BRPOP/RPOPLPUSH/LMOVE、底层结构（quicklist/ziplist）、应用场景（消息队列/最新列表/栈/队列）
- **代码**：`01-string-commands.redis` / `02-list-commands.redis`
- **重点**：INCR 原子性与并发安全、List 实现消息队列的局限

#### Day04 - Hash与Set数据类型
- **核心**：
  - Hash：HSET/HGET/HMSET/HMGET/HGETALL/HDEL/HSETNX/HINCRBY/HINCRBYFLOAT/HEXISTS/HKEYS/HVALS/HLEN/HSCAN/HRANDFIELD、底层结构（listpack/hashtable）、应用场景（对象存储/购物车/用户信息）
  - Set：SADD/SREM/SMEMBERS/SISMEMBER/SCARD/SPOP/SRANDMEMBER/SMOVE/SDIFF/SDIFFSTORE/SINTER/SINTERSTORE/SUNION/SUNIONSTORE/SSCAN、底层结构（intset/hashtable）、应用场景（标签/共同好友/去重/抽奖）
- **代码**：`01-hash-commands.redis` / `02-set-commands.redis`
- **重点**：Hash 存对象 vs String 存 JSON、Set 集合运算的威力

#### Day05 - Sorted Set有序集合
- **核心**：ZADD/ZREM/ZSCORE/ZINCRBY/ZCARD/ZCOUNT/ZRANGE/ZREVRANGE/ZRANGEBYSCORE/ZREVRANGEBYSCORE/ZRANK/ZREVRANK/ZREMRANGEBYRANK/ZREMRANGEBYSCORE/ZPOPMIN/ZPOPMAX/BZPOPMIN/BZPOPMAX/ZUNIONSTORE/ZINTERSTORE/ZRANDMEMBER/ZMSCORE、底层结构（listpack/skiplist+dict）、应用场景（排行榜/延迟队列/带权重的随机选择）
- **代码**：`01-sorted-set-commands.redis` / `02-leaderboard-demo.redis`
- **重点**：跳表（SkipList）原理、排行榜完整实现

#### Day06 - 高级数据类型
- **核心**：Bitmap（SETBIT/GETBIT/BITCOUNT/BITOP/BITPOS，应用：签到/在线状态/布隆过滤器简介）、HyperLogLog（PFADD/PFCOUNT/PFMERGE，应用：UV 统计）、Geo（GEOADD/GEOPOS/GEODIST/GEORADIUS/GEORADIUSBYMEMBER/GEOSEARCH，应用：附近的人/门店）、Stream（XADD/XLEN/XREAD/XRANGE/XREVRANGE/XGROUP/XREADGROUP/XACK/XLEN/XINFO/XTRIM，应用：消息队列/事件溯源）、Bitfields（BITFIELD/BITFIELD_RO）
- **代码**：`01-bitmap-demo.redis` / `02-hyperloglog-demo.redis` / `03-geo-demo.redis` / `04-stream-demo.redis`
- **重点**：Bitmap 签到统计、HyperLogLog 去重原理、Stream 消费组

---

### 阶段三：功能特性

#### Day07 - 发布订阅与Stream消息队列
- **核心**：Pub/Sub（SUBSCRIBE/PUBLISH/UNSUBSCRIBE/PSUBSCRIBE/PUNSUBSCRIBE/PUBSUB）、Pub/Sub 局限性（无持久化/无消费确认）、Stream 消息队列完整方案（消费者组/XREADGROUP/XACK/XPENDING/XCLAIM/死信处理）、Stream vs Kafka vs RabbitMQ 简要对比
- **代码**：`01-pubsub-demo.redis` / `02-stream-mq-demo.redis` / `README.md`（多终端操作指南）
- **重点**：Stream 消费者组与消息确认机制

#### Day08 - 事务与Lua脚本
- **核心**：MULTI/EXEC/DISCARD/WATCH、事务的 ACID 分析（不支持回滚的原因）、WATCH 乐观锁、Lua 脚本（EVAL/EVALSHA/SCRIPT LOAD/SCRIPT EXISTS/SCRIPT FLUSH）、Lua 语法速览（变量/条件/循环/Redis 调用 redis.call vs redis.pcall）、脚本原子性保证、SCRIPT LOAD + EVALSHA 优化、安全注意事项（KEYS vs ARGV）
- **代码**：`01-transaction-demo.redis` / `02-lua-script-demo.redis` / `03-lua-inventory.lua`
- **重点**：WATCH 乐观锁实战、Lua 脚本实现原子库存扣减

#### Day09 - 持久化机制
- **核心**：RDB 快照（save/bgsave、触发时机、文件格式、优缺点）、AOF 追加（appendonly/appendfsync always/everysec/no、重写机制 bgrewriteaof、优缺点）、RDB + AOF 混合持久化（4.0+）、数据恢复流程、持久化对性能的影响、生产配置建议
- **代码**：`01-rdb-config.redis` / `02-aof-config.redis` / `03-persistence-guide.md`（持久化策略指南）
- **重点**：AOF everysec 的折中、混合持久化的优势

---

### 阶段四：架构与应用

#### Day10 - 主从复制与高可用
- **核心**：主从复制（REPLICAOF/SLAVEOF、全量同步 vs 增量同步、PSYNC、复制积压缓冲区、读写分离）、Sentinel 哨兵（监控/通知/自动故障转移/配置中心、quorum 与 majority、故障转移流程）、Cluster 集群（16384 槽位、CRC16 分片、Gossip 协议、MOVED/ASK 重定向、集群扩缩容）、三种方案对比与选型
- **代码**：`01-replication-setup.md` / `02-sentinel-setup.md` / `03-cluster-setup.md`（配置文件与操作步骤）
- **重点**：理解复制原理与故障转移机制

#### Day11 - 缓存模式与分布式锁
- **核心**：
  - 缓存模式：Cache-Aside（旁路缓存）、Read-Through、Write-Through、Write-Behind（回写）
  - 缓存三大问题：缓存穿透（null 值缓存/布隆过滤器）、缓存击穿（互斥锁/热点永不过期）、缓存雪崩（随机过期时间/熔断降级）
  - 缓存一致性：先更新DB后删缓存 vs 先删缓存后更新DB、延迟双删、最终一致性
  - 分布式锁：SETNX → SET NX EX、锁的释放（Lua 保证原子）、Redlock 算法、锁续期（看门狗机制）、Redisson 简介对比
- **代码**：`01-cache-patterns.redis` / `02-cache-problems.redis` / `03-distributed-lock.redis`
- **重点**：缓存一致性方案、分布式锁的正确实现

#### Day12 - 内存管理与性能优化
- **核心**：内存查看（INFO memory / MEMORY USAGE / MEMORY STATS）、过期策略回顾（惰性+定期）、淘汰策略 8 种（noeviction/allkeys-lru/allkeys-lfu/allkeys-random/volatile-lru/volatile-lfu/volatile-random/volatile-ttl）、LRU vs LFU 实现、maxmemory 配置、慢查询日志（slowlog-get/slowlog-len）、Pipeline 批量操作、集群下 Pipeline 注意事项、bigkey 发现与处理、热点 Key 发现、性能优化最佳实践
- **代码**：`01-memory-management.redis` / `02-eviction-strategy.redis` / `03-performance-optimization.md`（优化清单）
- **重点**：淘汰策略选择、Pipeline 性能提升、bigkey 治理

---

## 目录结构

```
Redis/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - Redis基础与环境安装/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天命令脚本
│       ├── 00-environment-check.redis
│       ├── 01-hello-redis.redis
│       └── README.md
├── Day02 - 全局命令与Key管理/
│   ├── README.md
│   └── Code/
│       ├── 01-global-commands.redis
│       └── 02-key-expiration.redis
├── ...（Day03-Day11 同构）...
└── Day12 - 内存管理与性能优化/
    ├── README.md
    └── Code/
        ├── 01-memory-management.redis
        ├── 02-eviction-strategy.redis
        └── 03-performance-optimization.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，`.redis` 为 Redis 命令脚本（可 `redis-cli < file.redis` 执行或复制粘贴）
- `.lua` 为 Lua 脚本文件
- `.md` 为配置指南或操作说明文档
- 部分天数需要多终端操作（如 Pub/Sub），配套说明文档详述步骤

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 3-5 小时 | 约 2 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 4 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **先读后写**：每天先通读 README，理解概念后在 redis-cli 中亲手敲命令
2. **动手执行**：每个 `.redis` 文件都要用 redis-cli 实际运行，观察返回值
3. **改写实验**：改参数、改数据，观察行为变化
4. **多终端协作**：Day07/Day10/Day11 需要开多个 redis-cli 终端模拟并发
5. **结合 MySQL**：回想 MySQL 板块，理解缓存与数据库的配合
6. **完成实战**：每天 README 末尾的实战练习是巩固知识的关键

### 阶段性检查点

完成每个阶段后，应能回答以下问题：

- **阶段一完成后**：能否解释 Redis 单线程为何能达到 10 万 QPS？
- **阶段二完成后**：能否为每个业务场景选择最合适的数据类型？
- **阶段三完成后**：能否用 Lua 脚本保证操作原子性？能否解释 RDB 与 AOF 的取舍？
- **阶段四完成后**：能否设计完整的缓存方案并解决三大缓存问题？

---

## 如何运行代码

### 方式一：Docker 启动 Redis（推荐，零安装）

```bash
# 启动 Redis 7.x 容器
docker run -d --name redis-learn \
  -p 6379:6379 \
  redis:7

# 进入容器内的 redis-cli
docker exec -it redis-learn redis-cli

# 带密码启动（生产推荐）
docker run -d --name redis-learn \
  -p 6379:6379 \
  redis:7 --requirepass yourpassword

# 连接带密码的 Redis
docker exec -it redis-learn redis-cli -a yourpassword
```

### 方式二：本地安装 Redis

1. **Linux**：`apt install redis-server` 或源码编译 `make && make install`
2. **macOS**：`brew install redis`
3. **Windows**：使用 WSL2 或 Docker（官方不直接支持 Windows）
4. 命令行连接：

```bash
redis-cli                          # 默认连接 127.0.0.1:6379
redis-cli -h 127.0.0.1 -p 6379    # 指定地址端口
redis-cli -a yourpassword          # 带密码连接
redis-cli --stat                   # 实时监控统计信息
```

### 执行命令脚本

```bash
# 方式一：管道执行整个文件
redis-cli < "Day03 - String与List数据类型/Code/01-string-commands.redis"

# 方式二：在 redis-cli 中逐行复制粘贴
redis-cli
127.0.0.1:6379> SET hello "world"
127.0.0.1:6379> GET hello

# 方式三：执行 Lua 脚本
redis-cli --eval "Day08 - 事务与Lua脚本/Code/03-lua-inventory.lua" 1 stock:product:1001
```

### 图形客户端（任选其一）

| 客户端 | 特点 | 适用 |
|--------|------|------|
| RedisInsight | 官方出品、免费、功能强大 | 推荐通用 |
| Another Redis Desktop Manager | 开源免费、跨平台 | 入门 |
| Redis Commander | Web 界面、开源 | 偏好浏览器 |
| DataGrip | JetBrains 出品 | 已用 IDEA 生态 |

### 常用操作提示

```bash
# 在 redis-cli 中
PING                              # 测试连接
SELECT 0                          # 选择数据库（默认 0，共 16 个）
DBSIZE                            # 当前库 Key 数量
INFO                              # 服务器信息
CONFIG GET maxmemory              # 查看配置
KEYS *                            # 查看所有 Key（生产慎用！）
SCAN 0                            # 渐进式扫描
FLUSHDB                           # 清空当前库（开发调试用）
FLUSHALL                          # 清空所有库（危险！）

# 命令行直接执行单条命令
redis-cli SET mykey "hello"
redis-cli GET mykey
redis-cli INCR counter
```

### Windows 用户注意

- Redis 官方不直接支持 Windows，推荐使用 WSL2 或 Docker
- `.redis` 脚本文件编码为 UTF-8 无 BOM
- 路径含中文与空格时，管道命令建议用引号包裹

---

## 知识点速查

### Redis 数据类型速查

| 类型 | 核心命令 | 典型场景 | 对应天数 |
|------|---------|---------|---------|
| String | SET / GET / INCR | 缓存 / 计数器 / 限流 | Day03 |
| List | LPUSH / RPOP / LRANGE | 消息队列 / 最新列表 | Day03 |
| Hash | HSET / HGET / HGETALL | 对象存储 / 购物车 | Day04 |
| Set | SADD / SINTER / SUNION | 标签 / 去重 / 共同好友 | Day04 |
| Sorted Set | ZADD / ZRANGE / ZRANK | 排行榜 / 延迟队列 | Day05 |
| Bitmap | SETBIT / BITCOUNT / BITOP | 签到 / 在线状态 | Day06 |
| HyperLogLog | PFADD / PFCOUNT | UV 去重统计 | Day06 |
| Geo | GEOADD / GEODIST / GEOSEARCH | 附近的人/店 | Day06 |
| Stream | XADD / XREAD / XREADGROUP | 消息队列 | Day06、Day07 |

### 过期与淘汰策略速查

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| noeviction | 不淘汰，写入报错 | 默认，不允许丢数据 |
| allkeys-lru | 所有 Key 中淘汰最久未使用 | 纯缓存场景 |
| allkeys-lfu | 所有 Key 中淘汰最少使用 | 纯缓存场景（8.0+） |
| allkeys-random | 所有 Key 中随机淘汰 | 无访问模式 |
| volatile-lru | 设了过期的 Key 中 LRU | 混合持久化+缓存 |
| volatile-lfu | 设了过期的 Key 中 LFU | 混合持久化+缓存 |
| volatile-random | 设了过期的 Key 中随机 | 无访问模式 |
| volatile-ttl | 设了过期的 Key 中 TTL 最短优先 | 越快过期越先淘汰 |

### 缓存问题速查

| 问题 | 原因 | 解决方案 | 对应天数 |
|------|------|---------|---------|
| 缓存穿透 | 查询不存在的数据 | null 值缓存 / 布隆过滤器 | Day11 |
| 缓存击穿 | 热点 Key 过期瞬间 | 互斥锁 / 热点永不过期 | Day11 |
| 缓存雪崩 | 大量 Key 同时过期 | 随机过期时间 / 熔断降级 | Day11 |
| 缓存不一致 | 并发读写 | 延迟双删 / 最终一致性 | Day11 |

### 常用命令速查

```bash
# 服务管理
redis-server /etc/redis/redis.conf    # 指定配置启动
redis-cli shutdown                    # 优雅关闭
redis-cli BGSAVE                      # 后台 RDB 快照
redis-cli BGREWRITEAOF               # AOF 重写
redis-cli INFO memory                 # 查看内存信息
redis-cli CONFIG GET *                # 查看所有配置
redis-cli CONFIG SET maxmemory 1gb     # 设置最大内存

# 监控
redis-cli MONITOR                     # 实时监控所有命令（调试用）
redis-cli --latency                    # 测量延迟
redis-cli SLOWLOG GET 10               # 查看慢查询
redis-cli MEMORY USAGE key             # 查看单个 Key 内存占用
redis-cli CLIENT LIST                 # 查看客户端连接

# 批量操作
redis-cli --pipe < commands.txt        # 管道批量执行
echo "SET k v" | redis-cli             # 单条管道
```

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **MySQL** | 缓存与数据库的配合、缓存一致性、读写分离 |
| **Node.js / NestJS** | Day17 缓存集成、ioredis 客户端、会话存储、限流中间件 |
| **Docker** | Redis 容器化部署、集群编排、数据卷持久化 |
| **Linux** | Redis 在 Linux 上的部署、性能调优、网络配置 |
| **LLM / RAG** | 对话上下文缓存、向量检索缓存、限流保护、会话管理 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [Redis 官方文档](https://redis.io/docs/) - 最权威的参考
- [Redis 命令参考](https://redis.io/commands/) - 全部命令详解
- [Redis 最佳实践](https://redis.io/docs/manual/) - 运维与架构指南
- [Redis 设计与实现](http://redisbook.com/) - 深入底层数据结构（黄健宏著）
- [Try Redis](https://try.redis.io/) - 在线交互式入门

---

## 贡献与反馈

> 本学习手册为原创内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用内存速度驱动你的全栈之路！**