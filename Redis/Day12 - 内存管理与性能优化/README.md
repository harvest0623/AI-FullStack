# Day12 - 内存管理与性能优化

Redis 是内存数据库，内存就是生命线——一台 32GB 的服务器装满 Redis 后，每一个字节的浪费、每一次主线程阻塞都会被放大。当数据量增长、QPS 上升，你必须回答这些问题：内存用在哪了？碎片率多少？哪些 Key 该淘汰？慢查询在哪？bigkey 怎么治？性能优化是生产运维的必修课，它不是一两个调优参数，而是一套从数据类型选型、内存规划、淘汰策略、慢查询分析到 bigkey 治理的系统工程。本章将全面梳理 Redis 内存查看手段、8 种淘汰策略、LRU 与 LFU 实现原理、慢查询日志、Pipeline 管道、bigkey 与热点 Key 治理，以及生产级性能优化最佳实践。

---

## 学习目标

完成本章学习后，你应能够：

- 用 `INFO memory`、`MEMORY USAGE`、`MEMORY STATS` 诊断内存使用情况
- 区分 `used_memory` 与 `used_memory_rss`，理解碎片率的含义
- 掌握 8 种淘汰策略的差异与适用场景，正确配置 `maxmemory-policy`
- 理解 Redis 近似 LRU 与 LFU 的实现原理及 `maxmemory-samples` 调优
- 用慢查询日志定位性能瓶颈
- 理解 Pipeline 原理，掌握其与事务的区别及集群下的注意事项
- 发现并治理 bigkey 与热点 Key
- 应用生产级性能优化最佳实践

---

## 一、理论知识：内存查看

### 1.1 INFO memory

`INFO memory` 是查看 Redis 内存整体情况的首要命令。

| 指标 | 含义 |
|------|------|
| `used_memory` | Redis 分配器分配的内存（逻辑内存，所有数据结构占用） |
| `used_memory_rss` | 操作系统视角的物理内存（RSS，含碎片） |
| `used_memory_peak` | 内存使用历史峰值 |
| `used_memory_dataset` | 实际存储数据占用（扣除元数据） |
| `mem_fragmentation_ratio` | 碎片率 = `used_memory_rss / used_memory` |
| `maxmemory` | 配置的最大内存上限 |

```
INFO memory
CONFIG GET maxmemory
```

### 1.2 MEMORY USAGE

查看单个 Key 占用内存：

```
MEMORY USAGE cache:product:1001
MEMORY USAGE cache:product:1001 SAMPLES 0    ; SAMPLES 0 表示全量采样
```

- 返回值单位为字节，包含 Key、value 及元数据开销
- 对大容器类型（Hash/List/Set/ZSet），`SAMPLES` 控制采样精度，默认 5

### 1.3 MEMORY STATS / MEMORY DOCTOR

```
MEMORY STATS       ; 详细内存统计（分项开销）
MEMORY DOCTOR      ; 内存诊断建议（自动分析健康度）
MEMORY MALLOC-STATS ; 底层分配器统计（Jemalloc）
```

### 1.4 used_memory vs used_memory_rss

| 概念 | used_memory | used_memory_rss |
|------|-------------|-----------------|
| 含义 | 逻辑内存（数据结构占用） | 物理 RSS（OS 视角） |
| 反映 | 实际数据大小 | 实际占物理内存 |
| 关系 | ≤ rss（含碎片） | ≥ used_memory |

**碎片率 `mem_fragmentation_ratio` 判读**：

| 碎片率 | 状态 | 处理 |
|--------|------|------|
| 1.0~1.5 | 正常 | 无需处理 |
| > 1.5 | 碎片多 | 开启 `activedefrag` 或重启整理 |
| < 1.0 | 在 swap | 严重，立即扩内存/排查 |

---

## 二、过期策略回顾（呼应 Day02）

Redis 采用**惰性删除 + 定期删除**组合策略管理过期 Key。

### 2.1 惰性删除

- 访问 Key 时检查是否过期，过期则删除并返回 nil
- 优点：CPU 友好（不主动扫描）
- 缺点：冷数据过期后不访问则一直占内存

### 2.2 定期删除

- 默认每 100ms（由 `hz` 控制）随机抽样检查过期 Key
- 每次抽取 20 个带过期的 Key，删除已过期的
- 如果过期比例超过 25%，继续抽样检查（避免堆积）
- 优点：主动清理，防止内存堆积
- 缺点：无法覆盖所有 Key

### 2.3 两者配合

```
CONFIG GET hz    ; 定期删除频率，默认 10（每秒 10 次）
```

- 惰性删除保证"访问时一定干净"
- 定期删除保证"不访问也能被清理"
- 两者都无法清理的，由淘汰策略兜底

---

## 三、淘汰策略 8 种详解

当内存使用达到 `maxmemory` 上限时，Redis 按淘汰策略主动删除部分 Key 以腾出空间。

| 策略 | 范围 | 淘汰规则 | 适用场景 |
|------|------|---------|---------|
| `noeviction` | — | 不淘汰，写入报 OOM | 默认，不允许丢数据 |
| `allkeys-lru` | 所有 Key | 最久未使用优先淘汰 | 纯缓存（推荐） |
| `allkeys-lfu` | 所有 Key | 最少使用优先淘汰 | 纯缓存（8.0+ 推荐） |
| `allkeys-random` | 所有 Key | 随机淘汰 | 无访问模式 |
| `volatile-lru` | 设过期的 Key | 最久未使用优先淘汰 | 混合持久化+缓存 |
| `volatile-lfu` | 设过期的 Key | 最少使用优先淘汰 | 混合持久化+缓存 |
| `volatile-random` | 设过期的 Key | 随机淘汰 | 无访问模式 |
| `volatile-ttl` | 设过期的 Key | TTL 最短优先淘汰 | 越快过期越先淘汰 |

```
CONFIG SET maxmemory 2gb
CONFIG SET maxmemory-policy allkeys-lru
```

> **选型建议**：
> - 纯缓存场景：`allkeys-lru`（或 `allkeys-lfu`）
> - 混合持久化+缓存：`volatile-lru`（保护不过期的持久化数据）
> - 不允许丢数据：`noeviction`（需做好容量规划）

---

## 四、LRU vs LFU 实现原理

### 4.1 Redis 近似 LRU

Redis 不维护全局 LRU 链表（内存开销大），而是采用**近似 LRU**：

- 每次淘汰时**随机采样** N 个 Key（`maxmemory-samples`，默认 5）
- 从采样中淘汰最久未访问的
- 采样数越大越接近精确 LRU，但 CPU 开销越高

```
CONFIG GET maxmemory-samples    ; 默认 5，可调到 10 提升精度
CONFIG SET maxmemory-samples 10
```

### 4.2 LFU（4.0+）

LRU 的问题：偶尔被访问的冷数据会"续命"，挤掉真正热点数据。LFU（Least Frequently Used）按访问频率淘汰：

- 每个 Key 维护访问计数（Morris 计数器，概率性递增）
- 计数随时间衰减（避免老热点永不被淘汰）
- 解决"偶尔访问就续命"的问题

### 4.3 maxmemory-samples 调优

| 采样数 | 精度 | CPU 开销 | 建议 |
|--------|------|---------|------|
| 3 | 低 | 低 | 极高 QPS 场景 |
| 5（默认） | 中 | 中 | 通用 |
| 10 | 高 | 中高 | 对淘汰精度要求高 |

---

## 五、慢查询日志

### 5.1 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `slowlog-log-slower-than` | 10000（微秒=10ms） | 超过该时长记录慢查询，0=全部记录，-1=关闭 |
| `slowlog-max-len` | 128 | 慢查询日志保留条数 |

```
CONFIG SET slowlog-log-slower-than 10000
CONFIG SET slowlog-max-len 128
```

### 5.2 查看与管理

```
SLOWLOG GET 10      ; 查看最近 10 条慢查询
SLOWLOG LEN         ; 当前慢查询条数
SLOWLOG RESET       ; 清空慢查询日志
```

### 5.3 常见慢查询成因

- `KEYS *`（全量扫描）
- `DEL` 大 Key（同步删除阻塞）
- 复杂的 `SORT`、`SINTER`、`ZUNIONSTORE`
- `HGETALL` 大 Hash
- 过大的 Lua 脚本

---

## 六、Pipeline 管道

### 6.1 原理

客户端批量发送命令，服务端依次执行后一次性返回，将 N 次 RTT 压缩为 1 次。性能提升可达 10 倍以上（取决于网络延迟）。

### 6.2 使用方式

```bash
# redis-cli 管道
redis-cli --pipe < commands.txt

# 客户端 Pipeline（ioredis）
const pipeline = redis.pipeline();
for (let i = 0; i < 1000; i++) pipeline.set(`k:${i}`, `v:${i}`);
await pipeline.exec();
```

### 6.3 Pipeline vs 事务

| 维度 | Pipeline | 事务（MULTI/EXEC） |
|------|----------|-------------------|
| 层次 | 网络层优化 | 逻辑层原子性 |
| 原子性 | 不保证 | 保证 |
| 目的 | 减少 RTT | 保证操作原子 |

### 6.4 集群下 Pipeline 注意

- Redis Cluster 中 Key 分布在不同节点，Pipeline 需按节点分组发送
- 可用 hash tag `{tag}` 强制相关 Key 落同一槽位

---

## 七、bigkey 发现与处理

### 7.1 什么是 bigkey

| 类型 | 判定标准 |
|------|---------|
| String | value > 10KB |
| Hash/List/Set/ZSet | 元素数 > 5000 |

### 7.2 危害

- 网络阻塞（大 value 占带宽）
- 内存不均（集群下单节点倾斜）
- 删除阻塞（`DEL` 大 Key 阻塞主线程）
- 过期阻塞（大 Key 过期删除阻塞）

### 7.3 发现

```bash
redis-cli --bigkeys                    # 扫描各类型最大 Key
redis-cli MEMORY USAGE key             # 单个 Key 内存
redis-cli SCAN 0                       # 渐进式扫描
```

### 7.4 处理

| 手段 | 命令 | 说明 |
|------|------|------|
| 异步删除 | `UNLINK key` | 4.0+，后台释放 |
| 分批删除 Hash | `HSCAN` + `HDEL` | 逐批删字段 |
| 分批删除 List | `LTRIM` | 逐步截断 |
| 分批删除 ZSet | `ZREMRANGEBYRANK` | 按排名分批 |
| 拆分 | 业务侧分片 | 拆成多个小 Key |

---

## 八、热点 Key 发现

| 方式 | 命令 | 注意 |
|------|------|------|
| `redis-cli --hotkeys` | 需 `maxmemory-policy=allkeys-lfu` | 扫描 LFU 计数高 Key |
| `MONITOR` | 实时监控所有命令 | **生产慎用**，严重降性能 |
| 代理层统计 | 在代理层统计访问频次 | 无侵入 |

**热点 Key 处理**：本地缓存（Caffeine）、Key 分片（多副本）、读写分离。

---

## 九、性能优化最佳实践

| 实践 | 做法 |
|------|------|
| 选择合适数据类型 | Hash 存对象省内存 vs String 存 JSON |
| 合理设置过期时间 | 避免内存常驻，随机过期防雪崩 |
| 使用 Pipeline | 减少网络 RTT，批量操作 |
| 避免大 Key 与热 Key | 拆分、分片、本地缓存 |
| 用 UNLINK 替代 DEL | 4.0+ 异步释放，不阻塞主线程 |
| 用 SCAN 替代 KEYS | 渐进式扫描，不阻塞 |
| 合理配置淘汰策略 | 纯缓存用 allkeys-lru/lfu |
| 开启 lazyfree | `lazyfree-lazy-eviction/expire/server-del` 全开 |
| 控制连接数 | `maxclients` + 客户端连接池 |
| 合理配置持久化 | AOF everysec，注意 fork 对大内存的影响 |

---

## 十、代码文件说明

| 文件 | 内容 |
|------|------|
| `Code/01-memory-management.redis` | INFO memory 查看、MEMORY USAGE 各类型 Key 对比、MEMORY STATS、maxmemory 与淘汰策略设置、构造淘汰场景、过期策略验证、碎片率与主动碎片整理 |
| `Code/02-eviction-strategy.redis` | 构造不同类型 Key、noeviction/allkeys-lru/volatile-lru/volatile-ttl 策略切换与淘汰行为观察、慢查询日志演示、bigkey 构造与 UNLINK 删除、热点 Key 发现 |
| `Code/03-performance-optimization.md` | Pipeline 使用与性能对比、bigkey 治理流程、热点 Key 发现、数据类型选型、连接池配置、生产配置清单、监控指标清单 |

**运行方式**：

```bash
redis-cli < "Day12 - 内存管理与性能优化/Code/01-memory-management.redis"
redis-cli < "Day12 - 内存管理与性能优化/Code/02-eviction-strategy.redis"
```

> 注意：脚本含 `FLUSHDB` 和 `CONFIG SET maxmemory` 等操作，请在独立学习环境执行；脚本末尾会恢复配置。

---

## 十一、关键知识点总结

### 淘汰策略速查表

| 策略 | 范围 | 规则 | 推荐 |
|------|------|------|------|
| noeviction | — | 不淘汰 | 默认/不允许丢数据 |
| allkeys-lru | 全部 | 最久未用 | 纯缓存 |
| allkeys-lfu | 全部 | 最少使用 | 纯缓存（8.0+） |
| allkeys-random | 全部 | 随机 | 无访问模式 |
| volatile-lru | 过期 Key | 最久未用 | 混合场景 |
| volatile-lfu | 过期 Key | 最少使用 | 混合场景 |
| volatile-random | 过期 Key | 随机 | 无访问模式 |
| volatile-ttl | 过期 Key | TTL 最短 | 越快过期越先淘汰 |

### 内存查看命令速查

| 命令 | 用途 |
|------|------|
| `INFO memory` | 内存整体概况 |
| `MEMORY USAGE key` | 单个 Key 内存 |
| `MEMORY STATS` | 详细分项统计 |
| `MEMORY DOCTOR` | 内存诊断建议 |
| `CONFIG GET maxmemory` | 最大内存配置 |
| `CONFIG GET maxmemory-policy` | 淘汰策略 |

### 性能优化清单

| 优化项 | 手段 |
|--------|------|
| 网络 | Pipeline 批量、就近部署 |
| 阻塞 | UNLINK、SCAN、避免 KEYS |
| 内存 | 数据类型选型、淘汰策略、碎片整理 |
| bigkey | 发现 → UNLINK/分批删 → 拆分 |
| 热点 Key | 本地缓存、分片、读写分离 |
| 持久化 | AOF everysec、控制 fork 影响 |
| 连接 | 连接池、maxclients |

### bigkey 处理流程

```
发现（--bigkeys / MEMORY USAGE）
   │
   ├─ 删除 → UNLINK（4.0+）/ HSCAN+HDEL 分批
   │
   └─ 保留 → 拆分 / 压缩 / 设过期
```

---

## 十二、实战练习

### 练习一：内存诊断与淘汰策略验证

1. 执行 `Code/01-memory-management.redis`，记录 `used_memory`、`used_memory_rss`、`mem_fragmentation_ratio` 的值
2. 设置 `maxmemory 1mb` 和 `maxmemory-policy allkeys-lru`，循环写入 200 个 10KB 的 Key
3. 用 `DBSIZE` 和 `SCAN` 观察淘汰后剩余的 Key 数量，验证 LRU 淘汰行为
4. 切换为 `volatile-ttl` 策略，设置不同 TTL 的 Key，观察淘汰顺序
5. 思考：为什么 `mem_fragmentation_ratio` 可能大于 1.5？如何处理？

### 练习二：bigkey 构造与治理

1. 构造一个含 10000 字段的 Hash（`bigkey:hash:demo`），用 `MEMORY USAGE` 查看占用
2. 尝试用 `DEL` 删除，观察是否阻塞（可用 `--latency` 并行观察）
3. 重新构造，用 `UNLINK` 异步删除，对比阻塞差异
4. 编写 `HSCAN` + `HDEL` 分批删除脚本（每批 100 字段），验证平滑删除效果
5. 思考：生产环境如何在不阻塞业务的前提下清理 bigkey？

### 练习三：Pipeline 性能对比实验

1. 编写脚本生成 10000 条 `SET key:N value:N` 命令，存入 `commands.txt`
2. 方式一：逐条执行（`redis-cli SET ...` 循环），记录总耗时
3. 方式二：`redis-cli --pipe < commands.txt`，记录总耗时
4. 计算性能提升倍数，验证 Pipeline 的 RTT 优化效果
5. 思考：Pipeline 为什么不保证原子性？在什么场景下应改用事务（MULTI/EXEC）？
