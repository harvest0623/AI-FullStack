# Day03 - String 与 List 数据类型

## 本章简介

String 是 Redis 最基础、最常用的数据类型，所有 Key 都是字符串，而 String 类型的 Value 既可以存文本，也可以存数字、二进制（图片、序列化数据），最大支持 512MB。基于 String 的 `INCR` 原子计数器，Redis 成为高并发计数与限流场景的首选。List 则是有序字符串列表，按插入顺序排列、可重复，是实现简单消息队列、最新列表、固定长度历史记录的利器。

本章系统讲解 String 与 List 两大类型的全部命令、底层编码、应用场景，并通过电商场景（商品缓存、页面浏览量、限流计数器、最新订单、消息队列）落地演示。掌握本章后，你将能为"缓存 + 计数 + 队列"类需求选择合适的类型并正确实现。

## 学习目标

- 理解 String 类型的特点：二进制安全、最大 512MB、底层编码（int/embstr/raw）
- 掌握 String 全部命令：SET 各选项、GET 家族、MSET/MGET、APPEND/STRLEN/GETRANGE/SETRANGE、INCR 家族
- 应用 String 解决：缓存、计数器、限流、分布式锁基础、ID 生成器
- 理解 List 类型的特点：有序、可重复、底层编码（listpack/quicklist）
- 掌握 List 全部命令：LPUSH/RPUSH、LPOP/RPOP、LRANGE/LINDEX/LSET、LLEN/LINSERT/LREM/LTRIM、BLPOP/BRPOP、LMOVE
- 应用 List 解决：消息队列、最新列表、固定长度列表、栈与队列
- 理解 List 实现消息队列的局限与 Stream 的优势（Day07 详讲）

## 理论知识讲解

### 一、String 类型

#### 1. String 是什么

String 是 Redis 最基础的类型，一个 Key 对应一个 String Value。它有三个关键特性：

- **二进制安全**：可以存任意二进制数据（图片、序列化字节、压缩数据），不因 `\0` 截断。
- **最大 512MB**：单个 String 值上限 512MB（但实际不建议存超过 1MB，影响性能）。
- **数字友好**：存整数时可直接用 `INCR` / `DECR` 原子操作，无需先读后写。

#### 2. SET 命令与选项详解

```
SET key value [EX seconds] [PX ms] [NX|XX] [KEEPTTL] [GET]
```

| 选项 | 含义 | 典型场景 |
| --- | --- | --- |
| `EX seconds` | 设置秒级过期 | 缓存带 TTL |
| `PX ms` | 设置毫秒级过期 | 精确过期 |
| `NX` | 仅当 Key 不存在时写入 | 分布式锁、首次写入 |
| `XX` | 仅当 Key 已存在时写入 | 更新场景 |
| `KEEPTTL` | 保留现有 TTL（6.0+） | 更新值但不重置过期 |
| `GET` | 返回旧值（6.2+） | 原子更新并取旧值 |

`NX` 与 `XX` 互斥，不能同时使用。

#### 3. GET 家族

| 命令 | 作用 |
| --- | --- |
| `GET key` | 读取值 |
| `GETSET key value` | 设置新值并返回旧值（旧命令，可用 `SET ... GET` 替代） |
| `GETDEL key` | 删除并返回旧值（6.2+） |
| `GETEX key [EX\|PX\|EXAT\|PXAT]` | 获取值并设置/移除过期（6.2+） |

#### 4. SETEX / PSETEX / SETNX（旧命令）

| 命令 | 等价写法 | 状态 |
| --- | --- | --- |
| `SETEX key seconds value` | `SET key value EX seconds` | 已弃用 |
| `PSETEX key ms value` | `SET key value PX ms` | 已弃用 |
| `SETNX key value` | `SET key value NX` | 已弃用 |

新代码统一用 `SET` 加选项即可。

#### 5. MSET / MGET：批量操作

- `MSET k1 v1 k2 v2 ...`：批量写入，原子性（全部成功或全部失败）。
- `MGET k1 k2 ...`：批量读取，返回数组（不存在的返回 nil）。

批量操作能显著减少网络往返（RTT），高并发场景应优先使用。

#### 6. APPEND / STRLEN / GETRANGE / SETRANGE

| 命令 | 作用 |
| --- | --- |
| `APPEND key value` | 追加到末尾，返回追加后总长度 |
| `STRLEN key` | 返回字节长度 |
| `GETRANGE key start end` | 截取子串（闭区间，支持负索引） |
| `SETRANGE key offset value` | 从 offset 处覆写 |

#### 7. INCR 家族：原子计数器

| 命令 | 作用 |
| --- | --- |
| `INCR key` | +1 |
| `DECR key` | -1 |
| `INCRBY key n` | +n（整数） |
| `DECRBY key n` | -n（整数） |
| `INCRBYFLOAT key f` | +f（浮点数） |

**原子性**：`INCR` 是单命令原子操作，即使 100 个客户端同时 `INCR counter`，最终结果也正确递增，无需加锁。这是 Redis 计数器的核心优势。

> 注意：`INCR` 要求 Value 是整数表示，否则报错。`INCRBYFLOAT` 要求是数字（整数或浮点）。

#### 8. 应用场景

| 场景 | 实现方式 |
| --- | --- |
| 缓存 JSON/HTML | `SET cache:product:1 '{"name":"iPhone"}'` |
| 计数器（PV） | `INCR counter:page:views:home` |
| 限流 | `INCR rate:limit:user:1` + 首次 `EXPIRE` 设窗口 |
| 分布式锁基础 | `SET stock:lock:1 token NX EX 30` |
| ID 生成器 | `INCR id:generator:order` |
| UV 计数（粗略） | `INCR counter:uv:20240101` |

**限流示例（固定窗口）**：

```
INCR rate:limit:user:1001:api-order    # 计数 +1
# 若返回 1，说明是窗口第一次，设置 1 秒过期
EXPIRE rate:limit:user:1001:api-order 1
# 若计数 > 阈值（如 10），拒绝请求
```

#### 9. 底层编码

| 编码 | 条件 | 说明 |
| --- | --- | --- |
| `int` | 值为整数且 ≤ long 范围 | 整数直接存储，省内存 |
| `embstr` | 字符串且 ≤ 44 字节 | SDS 与对象连续内存，一次分配 |
| `raw` | 字符串且 > 44 字节 | 两次内存分配 |

Redis 7.x 优化：embstr 在某些场景下不会因修改而强制转 raw（如 `APPEND`）。

### 二、List 类型

#### 1. List 是什么

List 是有序字符串列表，按插入顺序排列、允许重复元素。可从两端插入（LPUSH/RPUSH）与弹出（LPOP/RPOP），支持按索引访问（LINDEX）、范围查询（LRANGE）。

#### 2. 插入与弹出

| 命令 | 作用 |
| --- | --- |
| `LPUSH key v1 [v2 ...]` | 左端（头部）插入 |
| `RPUSH key v1 [v2 ...]` | 右端（尾部）插入 |
| `LPUSHX key v1 [v2 ...]` | 仅当 Key 存在时左插 |
| `RPUSHX key v1 [v2 ...]` | 仅当 Key 存在时右插 |
| `LPOP key [count]` | 左端弹出（6.2+ 支持一次弹多个） |
| `RPOP key [count]` | 右端弹出 |

#### 3. 查询与修改

| 命令 | 作用 |
| --- | --- |
| `LRANGE key start end` | 范围查询（闭区间，支持负索引） |
| `LINDEX key index` | 按索引取元素 |
| `LSET key index value` | 修改指定索引元素 |
| `LLEN key` | 列表长度 |

#### 4. 插入与删除

| 命令 | 作用 |
| --- | --- |
| `LINSERT key BEFORE\|AFTER pivot value` | 在 pivot 前/后插入 |
| `LREM key count value` | 删除指定元素（count>0 从头，<0 从尾，=0 全部） |
| `LTRIM key start end` | 只保留指定范围，其余删除（常用于固定长度列表） |

#### 5. 阻塞弹出

| 命令 | 作用 |
| --- | --- |
| `BLPOP key [key ...] timeout` | 阻塞左弹，超时返回 nil |
| `BRPOP key [key ...] timeout` | 阻塞右弹 |
| `BLMOVE source dest from to timeout` | 阻塞版 LMOVE |

阻塞命令是 List 实现消息队列的关键：消费者无消息时挂起等待，避免轮询浪费 CPU。

#### 6. RPOPLPUSH / LMOVE / BLMOVE

| 命令 | 作用 |
| --- | --- |
| `RPOPLPUSH source dest` | 从 source 右弹并左推到 dest（旧命令） |
| `LMOVE source dest LEFT\|RIGHT LEFT\|RIGHT` | 灵活迁移元素（6.2+，替代 RPOPLPUSH） |
| `BLMOVE source dest from to timeout` | 阻塞版 LMOVE |

`LMOVE` 的"安全弹出推送"特性：原子地把元素从 source 移到 dest，避免消费者处理失败时丢消息。

#### 7. 底层编码

| 编码 | 条件 | 说明 |
| --- | --- | --- |
| `listpack` | 小列表（元素少且短） | 连续内存，省空间 |
| `quicklist` | 大列表 | 双向链表 + 节点内 listpack，兼顾内存与性能 |

Redis 7.0 起 List 默认用 listpack 替代 ziplist，修复了连锁更新问题。

#### 8. 应用场景

| 场景 | 实现方式 |
| --- | --- |
| 消息队列 | 生产者 `LPUSH`，消费者 `BRPOP` |
| 最新列表 | `LPUSH` 新内容 + `LTRIM` 保留前 N 条 |
| 栈（LIFO） | `LPUSH` + `LPOP` |
| 队列（FIFO） | `LPUSH` + `RPOP` |
| 安全队列 | `LPUSH` + `LMOVE` 到处理中列表 |

#### 9. List 消息队列的局限

List 作为消息队列存在明显不足：

- **无消费确认**：消费者 `RPOP` 后消息即从队列消失，若处理失败消息丢失。
- **无持久化保证**：Redis 重启（未开持久化）数据丢失。
- **无消费组**：一条消息只能被一个消费者处理，无法广播。
- **无回溯**：消费后无法重新读取历史消息。

这些局限由 **Stream**（Day06/Day07 详讲）解决：Stream 提供消费组、ACK 确认、消息持久化、回溯重放，是 Redis 原生消息队列的正确方案。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01-string-commands.redis` | String 全部命令演示：SET 选项、INCR 计数器、MSET/MGET、GETRANGE/SETRANGE、应用场景 |
| `Code/02-list-commands.redis` | List 全部命令演示：LPUSH/RPUSH、LPOP/RPOP、LRANGE、BLPOP/BRPOP、LMOVE、消息队列演示 |

执行方式：

```bash
redis-cli < "Day03 - String与List数据类型/Code/01-string-commands.redis"
redis-cli < "Day03 - String与List数据类型/Code/02-list-commands.redis"
```

## 关键知识点总结

### String 命令速查

| 命令 | 作用 | 复杂度 |
| --- | --- | --- |
| `SET key v [EX\|PX\|NX\|XX\|KEEPTTL\|GET]` | 写入 | O(1) |
| `GET key` | 读取 | O(1) |
| `GETSET key v` | 设新返旧 | O(1) |
| `GETDEL key` | 删并返旧 | O(1) |
| `GETEX key [EX\|PX\|...]` | 取并设过期 | O(1) |
| `MSET k1 v1 ...` | 批量写 | O(N) |
| `MGET k1 ...` | 批量读 | O(N) |
| `APPEND key v` | 追加 | O(1) |
| `STRLEN key` | 长度 | O(1) |
| `GETRANGE key s e` | 截取 | O(N) |
| `SETRANGE key off v` | 覆写 | O(N) |
| `INCR key` | +1 | O(1) |
| `DECR key` | -1 | O(1) |
| `INCRBY key n` | +n | O(1) |
| `DECRBY key n` | -n | O(1) |
| `INCRBYFLOAT key f` | +f | O(1) |

### List 命令速查

| 命令 | 作用 | 复杂度 |
| --- | --- | --- |
| `LPUSH key v...` | 左插 | O(N) |
| `RPUSH key v...` | 右插 | O(N) |
| `LPOP key [count]` | 左弹 | O(N) |
| `RPOP key [count]` | 右弹 | O(N) |
| `LRANGE key s e` | 范围查 | O(N) |
| `LINDEX key i` | 索引查 | O(N) |
| `LSET key i v` | 索引改 | O(N) |
| `LLEN key` | 长度 | O(1) |
| `LINSERT key BEFORE\|AFTER pivot v` | 插入 | O(N) |
| `LREM key count v` | 删除 | O(N) |
| `LTRIM key s e` | 修剪 | O(N) |
| `BLPOP key... timeout` | 阻塞左弹 | O(1) |
| `BRPOP key... timeout` | 阻塞右弹 | O(1) |
| `LMOVE src dest L\|R L\|R` | 迁移 | O(1) |
| `BLMOVE src dest f t timeout` | 阻塞迁移 | O(1) |

### 应用场景对照表

| 场景 | String | List |
| --- | --- | --- |
| 缓存对象 | ✅ 存 JSON | ❌ |
| 计数器 | ✅ INCR | ❌ |
| 限流 | ✅ INCR+EXPIRE | ❌ |
| 分布式锁 | ✅ SET NX EX | ❌ |
| 消息队列 | ❌ | ✅ LPUSH+BRPOP |
| 最新列表 | ❌ | ✅ LPUSH+LTRIM |
| 栈 | ❌ | ✅ LPUSH+LPOP |
| 队列 | ❌ | ✅ LPUSH+RPOP |

### 底层编码对照表

| 类型 | 小数据编码 | 大数据编码 |
| --- | --- | --- |
| String | int / embstr | raw |
| List | listpack | quicklist |

## 实战练习

1. **限流计数器实现**
   - 用 String 实现"每用户每秒最多调用 10 次 API"的限流。
   - 提示：`INCR rate:limit:user:1001:order` → 若返回 1 则 `EXPIRE ... 1` → 若 > 10 则拒绝。
   - 思考：这种"固定窗口"限流有什么缺陷？（边界突刺问题）如何改进？（滑动窗口，提示：用 Sorted Set）

2. **最新订单列表**
   - 模拟 5 个订单产生：`LPUSH latest:orders "order-5" "order-4" "order-3" "order-2" "order-1"`。
   - 用 `LTRIM latest:orders 0 9` 保留最新 10 条。
   - 用 `LRANGE latest:orders 0 -1` 查看最新订单。
   - 再 `LPUSH latest:orders "order-6"`，观察 `LTRIM` 后顺序与长度。

3. **消息队列演示（需两个终端）**
   - 终端 A（消费者）：执行 `BRPOP queue:orders 30`，观察阻塞等待。
   - 终端 B（生产者）：执行 `LPUSH queue:orders "order-1001"`。
   - 观察终端 A 收到消息并解除阻塞。
   - 思考：如果消费者收到消息后处理失败，消息是否丢失？如何用 `LMOVE` 实现"处理中列表"避免丢失？
