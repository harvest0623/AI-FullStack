# Day02 - 全局命令与 Key 管理

## 本章简介

在 Redis 中，Key 是数据的"第一公民"。每一个缓存项、会话、计数器、队列，最终都以一个 Key 的形式存在于内存中。Key 命名是否规范、过期策略是否合理、扫描方式是否安全，直接决定了 Redis 在生产环境的稳定性与可维护性。一次不假思索的 `KEYS *` 就能让百万级 Key 的实例卡顿数秒，进而拖垮整个上游服务。

本章系统讲解 Redis 的全局命令与 Key 管理机制：从命名规范出发，对比 `KEYS` 与 `SCAN` 的差异，掌握 `TYPE` / `EXISTS` / `DEL` / `UNLINK` / `RENAME` 等常用操作，深入理解 `EXPIRE` 家族与过期策略（惰性删除 + 定期删除），并了解多数据库与 `MOVE` 的使用边界。掌握本章后，你将能安全、高效地管理 Redis 中的 Key，避免生产事故。

## 学习目标

- 掌握 Key 命名规范（冒号分隔层级、避免过长与特殊字符）
- 理解 `KEYS` 的危险性，熟练使用 `SCAN` 渐进式扫描
- 使用 `TYPE` / `EXISTS` / `DEL` / `UNLINK` / `RENAME` 管理 Key
- 掌握 `EXPIRE` / `PEXPIRE` / `EXPIREAT` / `PEXPIREAT` 设置过期的四种方式
- 使用 `TTL` / `PTTL` 查看剩余时间，`PERSIST` 移除过期
- 理解 `OBJECT ENCODING`、`COPY`、`DUMP` / `RESTORE` 等高级命令
- 理解多数据库 `SELECT 0-15` 与 Redis Cluster 只用 DB 0 的原因
- 掌握过期策略：惰性删除 + 定期删除的协作机制
- 理解过期 Key 的内存回收时机

## 理论知识讲解

### 1. Key 命名规范

Redis 的 Key 本质是字符串，理论上可以取任意名字，但良好的命名规范能显著提升可维护性。

**推荐规范**：

- 用冒号 `:` 分隔层级，形如 `业务域:对象:标识`，例如 `cache:product:1001`、`session:token-abc`。
- 保持简洁，单个 Key 建议不超过 44 字节（触发 embstr 编码），最长不超过 1KB。
- 避免特殊字符（空格、换行、二进制），便于在客户端与日志中处理。
- 业务前缀统一，便于 `SCAN` 按前缀过滤与批量管理。

**电商场景命名示例**：

```
cache:product:{id}          → 商品详情缓存
cache:user:{id}             → 用户信息缓存
session:{token}             → 用户登录会话
cart:{user_id}              → 购物车
leaderboard:sales           → 销量排行榜
online:users                → 在线用户
counter:page:views          → 页面浏览量
stock:lock:{product_id}     → 库存锁
```

> 反例：`user 1001 cache`（含空格）、`very_long_key_name_that_should_be_shortened`（过长）、`p:1`（含义不明）。

### 2. KEYS pattern：通配符扫描（生产禁用）

`KEYS pattern` 用于一次性返回所有匹配的 Key，支持通配符：

| 通配符 | 含义 | 示例 |
| --- | --- | --- |
| `*` | 任意数量字符 | `KEYS cache:*` |
| `?` | 单个字符 | `KEYS cache:product:?` |
| `[]` | 字符集合 | `KEYS cache:product:[12]` |
| `\x` | 转义特殊字符 | `KEYS user\:*` |

**为什么生产环境禁用 KEYS**：`KEYS` 是一次性遍历整个 Key 空间，时间复杂度 O(N)。当 Key 数量达到百万级时，单次执行可能阻塞数秒，期间所有其他命令都会排队等待，导致服务雪崩。

```bash
# 危险！生产环境绝对禁止
KEYS *
KEYS cache:*
```

> 唯一允许使用 `KEYS` 的场景：调试环境、Key 数量极少（百级以内）且确认无并发压力。

### 3. SCAN cursor：渐进式扫描（推荐）

`SCAN` 是 `KEYS` 的安全替代方案，采用游标机制分批返回，不会阻塞服务器。

```
SCAN cursor [MATCH pattern] [COUNT n] [TYPE type]
```

- `cursor`：游标，第一次传 0，后续传上一次返回的游标，直到返回 0 表示遍历完成。
- `MATCH pattern`：可选，匹配模式（同 KEYS 通配符）。
- `COUNT n`：建议每次返回的数量（非严格保证，只是提示）。
- `TYPE type`：按数据类型过滤（6.0+）。

**SCAN 优于 KEYS 的原因**：

| 维度 | KEYS | SCAN |
| --- | --- | --- |
| 执行方式 | 一次性遍历全量 | 分批渐进遍历 |
| 阻塞 | 长时间阻塞 | 单次极短，不阻塞 |
| 内存 | 一次性返回全部结果 | 每批返回少量 |
| 一致性 | 强一致快照 | 弱一致（遍历期间数据可能变化） |
| 生产可用 | 否 | 是 |

**游标机制要点**：

- 游标不保证无重复、不保证无遗漏（遍历期间 Key 被 resize 可能重复或遗漏），业务侧需自行去重。
- `COUNT` 只是建议值，实际返回数量可能多也可能少。
- 返回游标为 0 才表示遍历结束。

相关命令：`HSCAN`（Hash）、`SSCAN`（Set）、`ZSCAN`（Sorted Set），分别用于扫描大 Hash/Set/ZSet 内部元素。

### 4. TYPE / EXISTS / DEL / UNLINK

| 命令 | 作用 | 说明 |
| --- | --- | --- |
| `TYPE key` | 查看数据类型 | 返回 string/list/hash/set/zset/stream 等 |
| `EXISTS key [key ...]` | 判断是否存在 | 返回存在的数量（可传多个 Key） |
| `DEL key [key ...]` | 同步删除 | 阻塞执行，大 Key 慎用 |
| `UNLINK key [key ...]` | 异步删除（4.0+） | 后台线程释放内存，不阻塞主线程 |

**DEL vs UNLINK**：删除大 Key（如含百万元素的 List）时，`DEL` 会在主线程同步释放内存，可能阻塞数百毫秒；`UNLINK` 则将内存释放交给后台线程，主线程几乎无开销。生产环境删除大 Key **必须用 UNLINK**。

### 5. RENAME / RENAMENX

- `RENAME key newkey`：重命名，若 newkey 已存在会被覆盖。
- `RENAMENX key newkey`：仅当 newkey 不存在时重命名。

> `RENAME` 会把原 Key 的 TTL 一并带到新 Key，需注意。

### 6. EXPIRE 家族：设置过期

| 命令 | 单位 | 说明 |
| --- | --- | --- |
| `EXPIRE key seconds` | 秒 | 设置剩余存活秒数 |
| `PEXPIRE key milliseconds` | 毫秒 | 设置剩余存活毫秒数 |
| `EXPIREAT key timestamp` | 秒 | 设置 Unix 时间戳（秒）过期点 |
| `PEXPIREAT key timestamp-ms` | 毫秒 | 设置 Unix 时间戳（毫秒）过期点 |

四种方式本质相同，最终都转化为 `PEXPIREAT`（绝对时间戳）存储。

### 7. TTL / PTTL / PERSIST

- `TTL key`：返回剩余秒数。-1 表示永不过期，-2 表示 Key 不存在。
- `PTTL key`：返回剩余毫秒数，精度更高。
- `PERSIST key`：移除过期时间，使 Key 变为永久。

### 8. RANDOMKEY / OBJECT / COPY / DUMP / RESTORE

- `RANDOMKEY`：随机返回一个 Key。
- `OBJECT ENCODING key`：查看底层编码（int/embstr/raw/listpack/quicklist/hashtable/intset/skiplist…）。
- `OBJECT REFCOUNT key`：查看引用计数。
- `OBJECT IDLETIME key`：查看空闲时间（多久未被访问，需开启 LRU/LFU）。
- `COPY key newkey [DB db] [REPLACE]`（6.2+）：复制 Key，可跨库。
- `DUMP key`：序列化 Key 的值（用于迁移）。
- `RESTORE key ttl serialized-value [REPLACE] [ABSTTL]`：反序列化恢复。

### 9. 多数据库 SELECT 0-15 与 MOVE

Redis 默认提供 16 个数据库（DB 0-15），用 `SELECT n` 切换。

| 命令 | 作用 |
| --- | --- |
| `SELECT n` | 切换到 DB n |
| `MOVE key db` | 将 Key 移动到另一个 DB |
| `DBSIZE` | 查看当前 DB 的 Key 数量 |
| `FLUSHDB` | 清空当前 DB |
| `FLUSHALL` | 清空所有 DB（危险） |

**为什么 Redis Cluster 只用 DB 0**：Cluster 模式下，Key 按 CRC16 哈希分配到 16384 个槽位，分摊到多个节点。如果允许使用多个 DB，跨库的 `MOVE` 与槽位计算会产生冲突，因此 Cluster 模式强制只使用 DB 0。生产环境推荐统一用 DB 0，通过 Key 前缀区分业务，而非依赖多 DB。

### 10. 过期策略详解

Redis 的过期 Key 不会立即被删除，而是采用**惰性删除 + 定期删除**双策略组合。

**惰性删除**：

- 时机：每次访问某个 Key 时（GET/SET/HGET 等），先检查是否过期，过期则删除并返回 nil。
- 优点：CPU 友好，只在访问时消耗。
- 缺点：大量过期但不再被访问的 Key（"冷过期 Key"）会长期占用内存。

**定期删除**：

- 时机：Redis 每秒执行 10 次（由 `hz` 配置控制）周期性任务，每次随机抽样部分设置了过期的 Key 检查，删除其中已过期的。
- 策略：每次抽样 `active-expire-keys` 个，若过期比例超过 25%，立即再抽一轮，直到比例下降或时间用尽。
- 优点：主动清理冷过期 Key，避免内存泄漏。
- 缺点：随机抽样，无法保证所有过期 Key 立即被清理。

**为什么不用定时器**：为每个 Key 设置一个定时器在理论可行，但当 Key 数量达到百万级时，定时器本身的开销（维护定时器堆、上下文切换）远超收益，且会让内存管理复杂化。Redis 选择"惰性 + 定期"的折中方案，在 CPU 与内存之间取得平衡。

### 11. 过期 Key 的内存回收时机

过期 Key 的真正内存释放发生在：

1. **惰性删除触发时**：访问到过期 Key，主线程删除并释放。
2. **定期删除触发时**：周期抽样删除。
3. **淘汰策略触发时**（Day12 详讲）：内存达到 `maxmemory` 上限时，按淘汰策略主动驱逐 Key（含未过期的）。

> 注意：过期 Key 在被删除前仍占用内存。如果业务写入大量带 TTL 但不再访问的 Key，仅靠惰性删除会导致内存不释放，必须依赖定期删除与淘汰策略。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01-global-commands.redis` | 全局命令演示：SCAN、TYPE、EXISTS、RENAME、OBJECT ENCODING、COPY 等 |
| `Code/02-key-expiration.redis` | 过期机制演示：EXPIRE/PEXPIRE/EXPIREAT、TTL/PTTL、PERSIST、惰性删除与定期删除 |

执行方式：

```bash
redis-cli < "Day02 - 全局命令与Key管理/Code/01-global-commands.redis"
redis-cli < "Day02 - 全局命令与Key管理/Code/02-key-expiration.redis"
```

## 关键知识点总结

### Key 管理命令速查表

| 命令 | 作用 | 复杂度 |
| --- | --- | --- |
| `KEYS pattern` | 通配符匹配全部 | O(N) 生产禁用 |
| `SCAN cursor [MATCH] [COUNT] [TYPE]` | 渐进扫描 | O(1) 单次 |
| `TYPE key` | 查看类型 | O(1) |
| `EXISTS key [key ...]` | 判断存在 | O(N) N=Key数 |
| `DEL key [key ...]` | 同步删除 | O(N) 大Key慢 |
| `UNLINK key [key ...]` | 异步删除 | O(1) 主线程 |
| `RENAME key newkey` | 重命名 | O(1) |
| `EXPIRE key seconds` | 设过期（秒） | O(1) |
| `PEXPIRE key ms` | 设过期（毫秒） | O(1) |
| `EXPIREAT key ts` | 设过期时间点（秒） | O(1) |
| `TTL key` | 剩余秒数 | O(1) |
| `PTTL key` | 剩余毫秒 | O(1) |
| `PERSIST key` | 移除过期 | O(1) |
| `RANDOMKEY` | 随机返回一个 Key | O(1) |
| `OBJECT ENCODING key` | 查看底层编码 | O(1) |
| `COPY key newkey` | 复制 Key | O(1)/O(N) |
| `SELECT n` | 切换数据库 | O(1) |
| `MOVE key db` | 跨库移动 | O(1) |
| `DBSIZE` | 当前库 Key 数 | O(1) |

### 过期策略对比

| 策略 | 触发时机 | 优点 | 缺点 |
| --- | --- | --- | --- |
| 惰性删除 | 访问 Key 时 | CPU 友好 | 冷过期 Key 占内存 |
| 定期删除 | 周期抽样（10次/秒） | 主动清理 | 随机抽样有遗漏 |
| 淘汰策略 | 内存达上限 | 兜底保护 | 可能驱逐有用 Key |

### TTL 返回值含义

| 返回值 | 含义 |
| --- | --- |
| 正数 | 剩余存活时间 |
| -1 | Key 存在但永不过期 |
| -2 | Key 不存在 |

## 实战练习

1. **SCAN 替代 KEYS 实战**
   - 用脚本或循环写入 1000 个 Key：`SET cache:product:1 v` … `SET cache:product:1000 v`。
   - 执行 `KEYS cache:product:*` 观察一次性返回（仅可在调试环境）。
   - 用 `SCAN 0 MATCH cache:product:* COUNT 100` 循环遍历，记录每批返回的游标与数量，直到游标为 0。
   - 思考：为什么某批返回的数量可能不等于 100？

2. **过期策略观察**
   - 执行 `SET cache:product:exp1 "v" EX 5`，立即 `TTL cache:product:exp1` 观察。
   - 等待 6 秒后 `GET cache:product:exp1`，确认返回 nil，体会惰性删除。
   - 写入 1000 个 `EX 2` 的 Key，2 秒后用 `DBSIZE` 观察数量变化，体会定期删除（可能不会立即归零）。

3. **DEL vs UNLINK 对比**
   - 用循环向一个 List 写入 10 万个元素：`RPUSH big:list v1 v2 ...`（可写脚本生成）。
   - 执行 `DEL big:list`，用 `TIME` 命令前后对比观察耗时。
   - 重新写入同样数据，执行 `UNLINK big:list`，对比耗时差异。
   - 思考：为什么生产环境删除大 Key 必须用 UNLINK？
