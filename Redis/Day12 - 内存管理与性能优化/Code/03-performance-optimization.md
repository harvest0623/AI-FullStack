# Redis 性能优化最佳实践

> 本文档为 Day12 性能优化配套说明，涵盖 Pipeline 使用、bigkey 治理、热点 Key 发现、数据类型选型、连接池配置、生产环境配置清单与监控指标清单。

---

## 一、Pipeline 管道使用与性能对比

### 1.1 原理

Redis 命令基于请求-响应模型，每条命令需一次网络往返（RTT）。Pipeline 允许客户端**批量发送多条命令**，服务端依次执行后一次性返回所有结果，将 N 次 RTT 压缩为 1 次。

### 1.2 性能对比

| 方式 | 10000 条 SET 命令 | 说明 |
|------|------------------|------|
| 逐条执行 | ~1.5s（本机）/ ~15s（跨机房） | 每条命令一次 RTT |
| Pipeline | ~0.15s（本机）/ ~0.3s（跨机房） | 10~50 倍提升 |

### 1.3 使用方式

**方式一：redis-cli --pipe 批量执行**

```bash
# 生成命令文件
for i in $(seq 1 10000); do echo "SET key:$i value:$i"; done > commands.txt

# 管道批量执行
redis-cli --pipe < commands.txt
```

**方式二：客户端 Pipeline（以 ioredis 为例）**

```javascript
const pipeline = redis.pipeline();
for (let i = 0; i < 10000; i++) {
  pipeline.set(`key:${i}`, `value:${i}`);
}
const results = await pipeline.exec();
```

**方式三：redis-cli 交互式管道**

```bash
# 多条命令一次性发送
(echo "SET k1 v1"; echo "SET k2 v2"; echo "GET k1") | redis-cli
```

### 1.4 Pipeline vs 事务

| 维度 | Pipeline | 事务（MULTI/EXEC） |
|------|----------|-------------------|
| 层次 | 网络层优化 | 逻辑层原子性 |
| 原子性 | 不保证（命令间可插入其他客户端命令） | 保证（EXEC 前命令不入队执行） |
| 目的 | 减少 RTT | 保证操作原子 |
| 可组合 | 可与事务结合使用 | 独立机制 |

### 1.5 集群下 Pipeline 注意事项

Redis Cluster 中 Key 分布在不同槽位（节点），Pipeline 要求命令发往同一节点。解决方案：
- **按节点分组**：客户端先计算各 Key 所属节点，分组发送 Pipeline
- **hash tag**：用 `{tag}` 强制相关 Key 落在同一槽位，如 `cache:{product}:1001`、`cache:{product}:1002`

---

## 二、bigkey 发现与治理

### 2.1 什么是 bigkey

| 类型 | bigkey 判定标准 |
|------|----------------|
| String | 单个 value > 10KB（严格可定 1MB） |
| Hash | 元素数 > 5000 或总大小 > 10MB |
| List | 元素数 > 5000 |
| Set | 元素数 > 5000 |
| Sorted Set | 元素数 > 5000 |

### 2.2 bigkey 危害

- **网络阻塞**：读取大 Key 占用大量带宽，阻塞其他请求
- **内存不均**：集群下单节点内存倾斜
- **删除阻塞**：`DEL` 大 Key 同步删除，阻塞主线程数秒（Redis 6.0 前单线程）
- **过期阻塞**：大 Key 过期时的删除操作阻塞主线程

### 2.3 发现 bigkey

**方式一：redis-cli --bigkeys（推荐）**

```bash
redis-cli --bigkeys
# 扫描各类型最大的 Key，给出 top 统计
```

**方式二：MEMORY USAGE 逐个检查**

```bash
redis-cli MEMORY USAGE cache:product:1001
# 返回该 Key 占用字节数（含元数据）
```

**方式三：SCAN + DEBUG OBJECT**

```bash
# 渐进式扫描所有 Key，结合 TYPE 和 DEBUG OBJECT 分析
redis-cli SCAN 0
redis-cli DEBUG OBJECT cache:product:1001
```

### 2.4 处理 bigkey

| 手段 | 命令 | 说明 |
|------|------|------|
| 异步删除 | `UNLINK key` | 4.0+，后台线程释放内存，不阻塞主线程 |
| 分批删除 Hash | `HSCAN` + `HDEL` | 逐批删除字段，避免一次性阻塞 |
| 分批删除 List | `LTRIM` | 逐步截断 |
| 分批删除 Set | `SSCAN` + `SREM` | 逐批删除成员 |
| 分批删除 ZSet | `ZREMRANGEBYRANK` | 按排名分批删除 |
| 拆分大 Key | 业务侧分片 | 如 `cache:product:1001:part1`、`part2` |

### 2.5 bigkey 处理流程

```
发现 bigkey（--bigkeys / MEMORY USAGE）
    │
    ▼
评估是否需要删除？
    │
    ├─ 是 → UNLINK 异步删除（4.0+）
    │       或 HSCAN/SSCAN 分批删除
    │
    └─ 否（业务需要）→ 拆分大 Key
                       压缩 value（如 JSON→MsgPack）
                       设置合理过期时间
```

---

## 三、热点 Key 发现

### 3.1 发现方式

| 方式 | 命令 | 优缺点 |
|------|------|--------|
| redis-cli --hotkeys | `redis-cli --hotkeys` | 需 `maxmemory-policy=allkeys-lfu`，扫描 LFU 计数高的 Key |
| MONITOR | `redis-cli MONITOR` | 实时监控所有命令，**生产慎用**（严重降性能） |
| 代理层统计 | 在 Twemproxy/Redis Cluster Proxy 层统计 | 无侵入，但需代理支持 |
| 客户端采样 | 客户端记录访问 Key 频次 | 灵活，但需改造代码 |

### 3.2 热点 Key 处理

- **本地缓存**：在应用本地缓存热点 Key（Caffeine/Guava），减少对 Redis 的访问
- **Key 分片**：将热点 Key 拆分为多个副本（如 `hotkey:1`、`hotkey:2`），随机访问
- **读写分离**：读请求分散到从节点

---

## 四、数据类型选择优化

### 4.1 Hash 存对象 vs String 存 JSON

| 维度 | String 存 JSON | Hash 存字段 |
|------|---------------|------------|
| 内存占用 | 较大（元数据 + JSON 字符串） | 较小（ziplist 编码时） |
| 部分更新 | 需 GET→改→SET 全量 | HSET 单字段 |
| 读取效率 | 一次 GET 取全部 | 可 HGET 单字段或 HGETALL |
| 过期管理 | 整体过期 | 无法对 Hash 单字段过期 |

**建议**：对象字段数 < 512 且单字段 < 64 字节时，用 Hash（触发 ziplist 编码，省内存）；否则用 String 存 JSON。

### 4.2 数据类型选择清单

| 场景 | 推荐类型 | 理由 |
|------|---------|------|
| 商品详情缓存 | String（JSON） | 整体读写，结构简单 |
| 用户信息（频繁改单字段） | Hash | 部分更新高效 |
| 购物车 | Hash | product_id→quantity 天然映射 |
| 排行榜 | Sorted Set | 自带排序 |
| 去重 / 标签 | Set | 天然去重 |
| UV 统计 | HyperLogLog | 固定 12KB 内存 |
| 签到 / 在线状态 | Bitmap | 极省内存 |
| 延迟队列 | Sorted Set | score=执行时间戳 |

---

## 五、连接池配置建议

### 5.1 关键参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| maxclients | 10000（服务端） | Redis 最大连接数，默认 10000 |
| 连接池大小 | 应用实例数 × 50~100 | 客户端连接池上限 |
| minIdle | 10~20 | 最小空闲连接 |
| maxIdle | 50~100 | 最大空闲连接 |
| 连接超时 | 200ms | 建立连接超时 |
| 读写超时 | 1000ms | 命令读写超时 |
| 健康检查 | 开启 | 定期 PING 保活 |

### 5.2 ioredis 连接池示例

```javascript
const Redis = require('ioredis');

const redis = new Redis({
  host: '127.0.0.1',
  port: 6379,
  maxRetriesPerRequest: 3,
  enableReadyCheck: true,
  connectTimeout: 200,
  commandTimeout: 1000,
  // 连接池
  family: 4,
  keepAlive: true,
});
```

### 5.3 控制连接数

```bash
# 服务端查看当前连接数
redis-cli CLIENT LIST

# 设置最大连接数
CONFIG SET maxclients 10000

# 超时断开空闲连接
CONFIG SET timeout 300
```

---

## 六、生产环境配置清单

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| maxmemory | 物理内存 60~70% | 预留空间给 fork/RDB |
| maxmemory-policy | allkeys-lru（纯缓存）/ volatile-lru（混合） | 按场景选择 |
| appendonly | yes | 开启 AOF |
| appendfsync | everysec | 每秒刷盘，平衡性能与安全 |
| save | 900 1 / 300 10 / 60 10000 | RDB 自动快照 |
| timeout | 300 | 空闲连接超时 |
| tcp-keepalive | 60 | TCP 保活 |
| hash-max-listpack-entries | 512 | Hash ziplist 阈值 |
| list-max-listpack-size | -2 | List 压缩阈值 |
| set-max-intset-entries | 512 | Set intset 阈值 |
| zset-max-listpack-entries | 128 | ZSet ziplist 阈值 |
| slowlog-log-slower-than | 10000 | 慢查询阈值 10ms |
| slowlog-max-len | 128 | 慢查询保留条数 |
| lazyfree-lazy-eviction | yes | 异步淘汰释放 |
| lazyfree-lazy-expire | yes | 异步过期释放 |
| lazyfree-lazy-server-del | yes | 异步 DEL 释放 |
| hz | 10 | 过期检查频率 |
| activedefrag | yes（4.0+） | 主动碎片整理 |

---

## 七、监控指标清单

### 7.1 核心监控指标

| 指标 | 命令 | 告警阈值 |
|------|------|---------|
| 内存使用率 | INFO memory → used_memory / maxmemory | > 80% 告警 |
| 内存碎片率 | INFO memory → mem_fragmentation_ratio | > 1.5 或 < 1.0 告警 |
| 连接数 | INFO clients → connected_clients | > maxclients × 80% 告警 |
| QPS | INFO stats → instantaneous_ops_per_sec | 按基线设定 |
| 命中率 | INFO stats → keyspace_hits / (keyspace_hits + keyspace_misses) | < 90% 需排查 |
| 慢查询数 | SLOWLOG LEN | 持续增长需排查 |
| 主从延迟 | INFO replication → 主从 offset 差 | > 1MB 告警 |
| RDB/AOF 状态 | INFO persistence → rdb_bgsave_in_progress | 持续进行需排查 |
| 键过期数 | INFO stats → expired_keys | 异常增长需排查 |
| 淘汰数 | INFO stats → evicted_keys | 持续淘汰需扩容 |

### 7.2 监控命令速查

```bash
# 实时 QPS 与内存
redis-cli --stat

# 延迟监测
redis-cli --latency
redis-cli --latency-history

# 大 Key 扫描
redis-cli --bigkeys

# 热点 Key 扫描（需 allkeys-lfu）
redis-cli --hotkeys

# 内存详情
redis-cli INFO memory

# 客户端连接
redis-cli CLIENT LIST
redis-cli INFO clients
```

---

## 八、性能优化清单速查

| 优化项 | 做法 |
|--------|------|
| 减少 RTT | 使用 Pipeline 批量命令 |
| 避免阻塞 | 用 UNLINK 替代 DEL，SCAN 替代 KEYS |
| 省内存 | 选对数据类型，Hash 优于 String 存对象 |
| 防穿透 | null 值缓存 + 布隆过滤器 |
| 防击穿 | 互斥锁 + 逻辑过期 |
| 防雪崩 | 随机过期 + 高可用 |
| 控内存 | 合理 maxmemory + 淘汰策略 |
| 治 bigkey | UNLINK 删除 + 拆分 + 异步释放 |
| 控连接 | 连接池 + maxclients |
| 开异步 | lazyfree 系列配置全开 |
| 持久化折中 | AOF everysec + RDB 定期快照 |
