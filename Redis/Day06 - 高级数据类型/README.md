# Day06 - 高级数据类型

Bitmap、HyperLogLog、Geo、Stream 是 Redis 提供的高级数据结构。它们并非全新的"数据类型"，而是基于 String / Sorted Set 等基础类型扩展出的专用能力，用以**用极小的内存解决特定场景问题**：Bitmap 用一位表示一个布尔状态实现签到与在线统计；HyperLogLog 用固定 12KB 估算亿级去重基数；Geo 用 GeoHash 编码实现附近门店搜索；Stream 提供类似 Kafka 的消息流与消费组模型。本天内容是 Redis 从"存储工具"走向"业务基础设施工具"的关键一跃。

## 学习目标

- 掌握 Bitmap 的位操作（SETBIT/GETBIT/BITCOUNT/BITOP/BITPOS）并实现用户签到、连续活跃统计
- 理解 HyperLogLog 的基数估算原理，用 PFADD/PFCOUNT/PFMERGE 实现 UV 与 DAU/MAU 统计
- 掌握 Geo 的 GEOADD/GEODIST/GEOSEARCH 并实现附近门店、距离计算
- 理解 Stream 的消息流模型与消费组机制（XADD/XREAD/XGROUP/XREADGROUP/XACK/XPENDING/XCLAIM/XTRIM）
- 了解 Bitfield 多位域操作
- 理解每种高级类型与基础类型的内存效率差异与适用边界

---

## 理论知识讲解

### 1. Bitmap（位图）

#### 1.1 概念

Bitmap 并不是独立的类型，而是 **String 类型的位操作扩展**。一个 String 的每个二进制位都可以独立设置（0/1），用来表示一个布尔状态。例如一个长度为 1 亿的位图只需约 12 MB 内存，远小于用 Set 存储 1 亿个用户 ID 的开销。

| 维度 | 说明 |
|------|------|
| 底层类型 | String |
| 最大位数 | 受 String 最大长度限制（512MB，约 42 亿位） |
| 操作复杂度 | SETBIT/GETBIT O(1)，BITCOUNT O(N) |
| 适用场景 | 用户签到、在线状态、活跃统计、布隆过滤器 |

#### 1.2 核心命令

```redis
SETBIT key offset value              # 设置第 offset 位的值（0 或 1）
GETBIT key offset                    # 获取第 offset 位的值
BITCOUNT key [start end [BYTE|BIT]]  # 统计为 1 的位数
BITPOS key bit [start [end [BYTE|BIT]]]   # 查找第一个值为 bit 的位
BITOP operation destkey key [key ...]     # AND/OR/XOR/NOT 位运算
BITFIELD key [GET type offset]            # 多位域操作
       [SET type offset value]
       [INCRBY type offset increment]
       [OVERFLOW WRAP|SAT|FAIL]
```

#### 1.3 用户签到场景

约定 Key：`sign:user:{userId}:{yyyymm}`，offset = 当月第几天（1-31）。例如 `sign:user:1:202501` 的第 15 位为 1 表示用户 1 在 1 月 15 日签到。

```redis
# 用户 1 在 2025-01-15 签到（offset = 15）
SETBIT sign:user:1:202501 15 1
# 查询是否签到
GETBIT sign:user:1:202501 15
# 当月签到总天数
BITCOUNT sign:user:1:202501
```

#### 1.4 连续签到天数计算

从当天 offset 往前逐位 `GETBIT`，遇到 0 即停。更高效的做法是用 `BITFIELD` 一次取一段位，再用位运算处理。

#### 1.5 BITOP 求活跃用户交集

每个日期一个位图，第 N 位表示用户 N 是否活跃：

```redis
BITOP AND active:weekly  active:20250101 active:20250102 active:20250103
BITCOUNT active:weekly   # 3 天都活跃的用户数
```

#### 1.6 布隆过滤器简介

布隆过滤器（Bloom Filter）是一种概率型数据结构，用 Bitmap + 多个哈希函数实现"元素是否存在"的快速判断：

- 添加元素：用 k 个哈希函数计算 k 个位，全部置 1
- 查询元素：检查对应 k 个位，全为 1 则"可能存在"，有 0 则"一定不存在"
- 特点：可能有假阳性（误判存在），但绝不会假阴性

Redis 本身没有原生 Bloom Filter 命令，但可通过 `BITFIELD` + Lua 模拟，或使用 RedisBloom 模块。常用于**缓存穿透防护**：查询前先过布隆过滤器，不存在的 key 直接返回。

### 2. HyperLogLog（基数估算）

#### 2.1 概念

HyperLogLog（HLL）是用于**估算集合中不重复元素数量**的概率算法。它**不存储元素本身**，只维护一个固定 12KB 的状态，估算误差约 0.81%。相比用 Set 存储全部元素再 SCARD，HLL 在亿级数据下可节省数百倍内存。

| 维度 | Set 去重 | HyperLogLog |
|------|---------|-------------|
| 内存占用 | 与元素数成正比 | 固定约 12KB |
| 是否存储元素 | 是 | 否 |
| 精度 | 精确 | 约 0.81% 误差 |
| 是否可回查元素 | 是 | 否 |
| 合并操作 | SUNIONSTORE | PFMERGE |
| 适用场景 | 需要元素本身 | 只需基数（UV/DAU） |

#### 2.2 核心命令

```redis
PFADD key element [element ...]        # 添加元素
PFCOUNT key [key ...]                  # 返回基数（单个或多个合并后的估算）
PFMERGE destkey sourcekey [sourcekey ...]  # 合并多个 HLL
```

#### 2.3 UV 统计场景

约定 Key：`counter:uv:{yyyymmdd}`，每次访问 `PFADD counter:uv:20250128 "user:42"`。

```redis
PFADD counter:uv:20250128 "user:1" "user:2" "user:3" "user:1"   # user:1 重复只算一次
PFCOUNT counter:uv:20250128                                       # 返回 3
PFMERGE counter:uv:week2025_05 counter:uv:20250128 ...             # 合并周 UV
```

### 3. Geo（地理位置）

#### 3.1 概念

Geo 是基于 Sorted Set 的扩展。Redis 将经纬度用 **GeoHash** 编码为一个 52 位整数作为 score，存入 Sorted Set。这样既能 O(logN) 范围查询，又能用距离/经纬度框选。

| 维度 | 说明 |
|------|------|
| 底层类型 | Sorted Set |
| 编码方式 | GeoHash（经纬度交织编码为 52 位整数） |
| 精度 | 约 ±0.5 米 |
| 适用场景 | 附近门店、距离计算、商圈搜索 |

#### 3.2 核心命令

```redis
GEOADD key longitude latitude member [lon lat member ...]   # 添加地理点
GEOPOS key member [member ...]                              # 获取经纬度
GEODIST key member1 member2 [m|km|ft|mi]                    # 计算两点距离
GEOSEARCH key FROMLONLAT lon lat                            # 以坐标为中心搜索
            BYRADIUS radius m|km|ft|mi                       # 按半径
            | BYBOX width height m|km|ft|mi                  # 按矩形框
            ASC|DESC                                         # 排序（近到远 / 远到近）
            COUNT count [ANY]                                # 限制数量
            WITHCOORD                                        # 返回经纬度
            WITHDIST                                         # 返回距离
GEOSEARCHSTORE dest src ...                                 # 7.0+ 将搜索结果存入新 key
```

> 旧的 `GEORADIUS` / `GEORADIUSBYMEMBER` 已在 6.2.0 弃用，新代码请用 `GEOSEARCH` / `GEOSEARCHSTORE`。

#### 3.3 附近门店场景

约定 Key：`geo:stores`，每个门店为一个 member。

```redis
GEOADD geo:stores 116.404 39.915 "store:001" 116.487 39.998 "store:002"
GEODIST geo:stores "store:001" "store:002" km
GEOSEARCH geo:stores FROMLONLAT 116.40 39.92 BYRADIUS 3 km ASC COUNT 10 WITHDIST WITHCOORD
```

### 4. Stream（流）

#### 4.1 概念

Stream 是 Redis 5.0 引入的消息流数据类型，类似 Kafka 的消费组模型。它**持久化存储消息**、支持**消费组**、支持**消息确认（ACK）**、可**回溯历史消息**，弥补了 Pub/Sub 的所有短板。

| 维度 | Pub/Sub | Stream |
|------|---------|--------|
| 持久化 | 否 | 是 |
| 消费确认 | 无 | XACK |
| 消费组 | 无 | 有 |
| 离线消息 | 丢失 | 可回溯 |
| 消息堆积 | 不可控 | 可控（MAXLEN/MINID） |

#### 4.2 生产端：XADD

```redis
XADD key [NOMKSTREAM] [MAXLEN|MINID [=|~] threshold [LIMIT count]] * | id field value [field value ...]
```

- `*` 表示由 Redis 自动生成 ID（时间戳-序号）
- `MAXLEN ~ N` 表示近似裁剪到 N 条（性能更好，允许多一点）
- `NOMKSTREAM` 表示 key 不存在时不创建

```redis
XADD stream:orders * type "create" orderId "1001" amount 99.9
XADD stream:orders MAXLEN ~ 10000 * type "pay" orderId "1001"
```

#### 4.3 查询：XLEN / XRANGE / XREVRANGE / XREAD

```redis
XLEN key                                       # 消息总数
XRANGE key start end [COUNT count]             # 按时间正序查
XREVRANGE key end start [COUNT count]          # 按时间倒序查
XREAD [COUNT count] [BLOCK ms] STREAMS key [key ...] id [id ...]   # 读取
```

`XREAD` 中 `id` 用 `$` 表示"只读最新消息"，`0` 表示"从头开始"。

#### 4.4 消费组：XGROUP / XREADGROUP / XACK

```redis
XGROUP CREATE key groupname id [MKSTREAM]      # 创建消费组，id 用 $ 表示只读新消息，0 表示从头
XREADGROUP GROUP group consumer [COUNT count] [BLOCK ms] STREAMS key [key ...] id [id ...]
XACK key group id [id ...]                     # 确认消息已处理
```

`XREADGROUP` 中 id 用 `>` 表示"消费组未投递过的新消息"，用 `0` 表示"重新读取该消费者待确认的消息"。

#### 4.5 待确认消息与死信处理：XPENDING / XCLAIM / XAUTOCLAIM

```redis
XPENDING key group [start end count] [consumer]          # 查看待确认消息
XCLAIM key group consumer min-idle-time id [id ...]      # 转移超时消息给其他消费者
XAUTOCLAIM key group consumer min-idle-time start [count] # 6.2+ 自动批量转移
```

死信处理流程：消费者 A 拿到消息后崩溃未 ACK → 该消息进入 pending 列表 → 消费者 B 用 XCLAIM 把 idle 时间超过阈值的消息转移给自己重新处理。

#### 4.6 状态查询：XINFO

```redis
XINFO STREAM key                     # Stream 整体信息
XINFO GROUPS key                     # 所有消费组
XINFO CONSUMERS key group            # 某组内所有消费者
```

#### 4.7 裁剪与删除：XTRIM / XDEL

```redis
XTRIM key MAXLEN|MINID [=|~] threshold [LIMIT count]    # 裁剪
XDEL key id [id ...]                                     # 删除指定消息
```

#### 4.8 应用场景

- 消息队列：订单事件流 `stream:orders`，多消费者并行处理
- 事件溯源（Event Sourcing）：所有状态变更以事件形式追加到 Stream
- 实时通知：用户通知中心，按时间线展示

### 5. Bitfield（位域）

BITFIELD 允许在一次命令中对 String 的多个位段进行原子操作，支持 u1~u64、i1~i64 类型。

```redis
BITFIELD key
  GET u8 0               # 读取从 0 位起的 8 位无符号整数
  SET u8 0 200           # 写入
  INCRBY u8 0 10         # 增量
  OVERFLOW WRAP|SAT|FAIL # 溢出策略：环绕/饱和/报错
```

`BITFIELD_RO` 是只读版本（不允许 SET/INCRBY），用于副本节点。

应用：紧凑计数器（一个 String 存多个小计数器）、计数器溢出控制。

---

## 代码文件说明

| 文件 | 内容 |
|------|------|
| `Code/01-bitmap-demo.redis` | Bitmap 演示：用户签到 `sign:user:1:202501`、月签到统计 BITCOUNT、连续签到天数计算、BITOP 求连续活跃用户 |
| `Code/02-hyperloglog-demo.redis` | HyperLogLog 演示：UV 统计 `counter:uv:20250128`、PFADD/PFCOUNT、PFMERGE 合并日 UV 为周 UV、与 Set 去重对比内存 |
| `Code/03-geo-demo.redis` | Geo 演示：GEOADD 添加门店 `geo:stores`、GEOPOS/GEODIST 距离、GEOSEARCH 搜索附近门店 WITHDIST WITHCOORD ASC COUNT |
| `Code/04-stream-demo.redis` | Stream 演示：XADD 添加订单事件 `stream:orders`、XRANGE/XREAD 查询、消费组 XGROUP/XREADGROUP/XACK、XPENDING/XCLAIM 死信处理、XTRIM 裁剪 |

> 执行方式：`redis-cli < Code/01-bitmap-demo.redis`，或进入 redis-cli 后逐行复制粘贴。

---

## 关键知识点总结

### 高级类型速查表

| 类型 | 底层 | 核心命令 | 内存特征 |
|------|------|---------|---------|
| Bitmap | String | SETBIT / GETBIT / BITCOUNT / BITOP | 1 位表示 1 个状态，1 亿位 ≈ 12 MB |
| HyperLogLog | String | PFADD / PFCOUNT / PFMERGE | 固定 ~12KB，与元素数无关 |
| Geo | Sorted Set | GEOADD / GEOSEARCH / GEODIST | 与成员数成正比 |
| Stream | Radix Tree + listpack | XADD / XREAD / XREADGROUP / XACK | 与消息数成正比 |
| Bitfield | String | BITFIELD GET/SET/INCRBY | 一段位表示一个整数 |

### 应用场景对照表

| 场景 | 推荐类型 | Key 设计 |
|------|---------|---------|
| 用户签到 | Bitmap | `sign:user:{id}:{ym}` |
| 在线用户 | Bitmap | `online:users:{date}` |
| UV / DAU | HyperLogLog | `counter:uv:{date}` |
| 月活 MAU | HyperLogLog | `counter:mau:{ym}` = PFMERGE 日 UV |
| 附近门店 | Geo | `geo:stores` |
| 距离计算 | Geo | `geo:stores` + GEODIST |
| 订单事件流 | Stream | `stream:orders` |
| 消息队列 | Stream | `stream:{biz}` + 消费组 |
| 缓存穿透防护 | Bitmap（布隆） | `bloom:{biz}` |

### 内存效率对比

统计 1 亿用户的 UV：

| 方案 | 内存占用 | 精度 |
|------|---------|------|
| Set 存全部 user_id | 数 GB | 精确 |
| Bitmap（1 亿位） | 约 12 MB | 精确（已知用户 ID 范围） |
| HyperLogLog | 约 12 KB | 0.81% 误差 |

> Bitmap 适合"用户 ID 连续或可映射到连续位"的场景；HLL 适合"任意元素、只需基数"的场景。

---

## 实战练习

### 练习 1：用户签到系统

设计一个用户签到系统：
1. 用户 1 在 2025-01 月的第 1、2、3、5、6、8、10 天签到，写入 `sign:user:1:202501`
2. 统计该用户当月签到总天数
3. 实现一个"查询连续签到天数"的思路：从第 10 天往前逐位 GETBIT，遇到 0 即停
4. 用 BITOP 求用户 1 和用户 2 在 2025-01 月都签到的天数

**提示**：BITOP AND 的结果再 BITCOUNT 即得交集天数。

### 练习 2：UV 与周活合并

1. 模拟 2025-01-28 的 5 个独立访客写入 `counter:uv:20250128`
2. 模拟 2025-01-29 的 4 个独立访客写入 `counter:uv:20250129`（其中 2 个与昨日重复）
3. 用 PFMERGE 合并为 `counter:uv:week2025_05`，应得 7 个左右（去重后）
4. 用 `OBJECT ENCODING` 查看 HLL 的底层编码
5. 对比用 Set 存同样数据的 `MEMORY USAGE`

### 练习 3：附近门店搜索

1. 添加 5 个门店到 `geo:stores`，经纬度自定（可模拟北京三里屯、国贸、五道口等）
2. 计算任意两个门店的距离（km）
3. 以三里屯为中心，搜索半径 5km 内的门店，按距离升序，最多返回 10 个，返回距离与坐标
4. 改用 BYBOX 搜索一个 10km × 10km 的矩形区域

### 练习 4：订单事件流消费组

1. 创建 Stream `stream:orders`，添加 3 条订单创建事件
2. 创建消费组 `order_processors`，从 `0` 开始消费
3. 用 consumer-1 消费 2 条消息并 XACK
4. 故意让 consumer-2 拿到 1 条消息但不 ACK（模拟崩溃）
5. 用 XPENDING 查看待确认消息
6. 用 XCLAIM 把超时消息转移给 consumer-3 重新处理
7. 用 XTRIM 把 Stream 裁剪到 2 条

**提示**：详细命令见 `Code/04-stream-demo.redis`。
