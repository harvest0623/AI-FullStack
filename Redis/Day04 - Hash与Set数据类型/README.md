# Day04 - Hash 与 Set 数据类型

## 本章简介

Hash 与 Set 是 Redis 中两个高频使用的数据类型。Hash 是 field-value（字段-值）映射表，天然适合存储对象——一个商品的所有属性（名称、价格、库存）可放在同一个 Hash 的不同 field 中，既能整体读取，也能独立更新某个字段，比"String 存 JSON"更灵活、内存更省。Set 则是无序、不重复的字符串集合，最大特色是支持集合运算（交集、并集、差集），是实现标签系统、共同关注、去重、抽奖等场景的利器。

本章系统讲解 Hash 与 Set 两大类型的全部命令、底层编码、应用场景，并通过电商场景（商品信息、购物车、用户信息、用户标签、共同关注、抽奖）落地演示，重点对比"Hash 存对象 vs String 存 JSON"的取舍。掌握本章后，你将为对象存储与集合运算类需求选择正确类型并高效实现。

## 学习目标

- 理解 Hash 类型的特点：field-value 映射、适合存对象、底层编码（listpack/hashtable）
- 掌握 Hash 全部命令：HSET/HGET/HMGET/HGETALL/HKEYS/HVALS/HLEN/HSETNX/HEXISTS/HDEL/HINCRBY/HINCRBYFLOAT/HRANDFIELD/HSCAN
- 应用 Hash 解决：对象存储、购物车、配置项存储
- 对比 Hash 存对象与 String 存 JSON 的内存效率与字段独立读写能力
- 理解 Set 类型的特点：无序、不重复、底层编码（intset/hashtable/listpack）
- 掌握 Set 全部命令：SADD/SREM/SMEMBERS/SISMEMBER/SCARD/SPOP/SRANDMEMBER/SMOVE + 集合运算
- 应用 Set 解决：标签系统、共同关注、去重、抽奖、黑白名单

## 理论知识讲解

### 一、Hash 类型

#### 1. Hash 是什么

Hash 是一个 field-value（字段-值）映射表，可以理解为"Key 下面嵌套一个小字典"。例如：

```
cache:product:1 (Hash)
  ├── name  → iPhone 15
  ├── price → 5999
  └── stock → 1000
```

每个 Hash 可以存 2^32 - 1 个字段。Hash 非常适合存对象：相比"一个对象存成一个 JSON String"，Hash 允许独立读写单个字段，避免每次更新都重写整个对象。

#### 2. 写入与读取

| 命令 | 作用 |
| --- | --- |
| `HSET key field value [field value ...]` | 设置一个或多个字段（可批量） |
| `HGET key field` | 读取单个字段 |
| `HMGET key field [field ...]` | 批量读取多个字段（不存在的返回 nil） |
| `HGETALL key` | 读取全部字段与值 |
| `HKEYS key` | 读取所有字段名 |
| `HVALS key` | 读取所有值 |
| `HLEN key` | 字段数量 |

> `HMSET` 已弃用，因为 `HSET` 从 4.0 起支持多字段，统一用 `HSET` 即可。

#### 3. 字段级操作

| 命令 | 作用 |
| --- | --- |
| `HSETNX key field value` | 仅当字段不存在时设置 |
| `HEXISTS key field` | 判断字段是否存在 |
| `HDEL key field [field ...]` | 删除一个或多个字段 |

#### 4. 数值字段原子操作

| 命令 | 作用 |
| --- | --- |
| `HINCRBY key field n` | 字段值 +n（整数） |
| `HINCRBYFLOAT key field f` | 字段值 +f（浮点） |

`HINCRBY` 让 Hash 字段也具备原子计数能力，例如购物车中商品数量增减无需读出再加。

#### 5. 随机与扫描

| 命令 | 作用 |
| --- | --- |
| `HRANDFIELD key [count [WITHVALUES]]` | 随机返回字段（6.2+） |
| `HSCAN key cursor [MATCH pattern] [COUNT n]` | 渐进扫描字段 |

#### 6. 底层编码

| 编码 | 条件 | 说明 |
| --- | --- | --- |
| `listpack` | 字段数 ≤ 128 且所有值 ≤ 64 字节（默认阈值） | 连续内存，省空间 |
| `hashtable` | 超过阈值 | 真正的哈希表，O(1) 读写 |

阈值由 `hash-max-listpack-entries` 与 `hash-max-listpack-value` 控制。listpack 节省内存但字段过多时性能下降，超过阈值自动转为 hashtable。

#### 7. 应用场景

| 场景 | Key 设计 | field-value |
| --- | --- | --- |
| 商品信息 | `cache:product:{id}` | name/price/stock → 值 |
| 用户信息 | `cache:user:{id}` | name/email/age → 值 |
| 购物车 | `cart:{user_id}` | product_id → quantity |
| 配置项 | `config:app` | key → value |

**购物车示例**：

```
HSET cart:1001 1001 2 1002 1    # 商品 1001 数量 2，商品 1002 数量 1
HINCRBY cart:1001 1001 1        # 商品 1001 数量 +1 → 3
HDEL cart:1001 1002              # 移除商品 1002
HGETALL cart:1001                # 查看购物车
```

#### 8. Hash 存对象 vs String 存 JSON

| 维度 | Hash 存对象 | String 存 JSON |
| --- | --- | --- |
| 部分更新 | ✅ HSET 单字段，省带宽 | ❌ 需 GET-修改-SET 整体 |
| 单字段读取 | ✅ HGET O(1) | ❌ 需 GET 整个 JSON 后解析 |
| 内存效率 | 字段少时 listpack 更省 | 小 JSON 接近 |
| 整体读写 | ❌ HGETALL 多次 | ✅ 一次性 GET |
| 字段级 TTL | ❌ Hash 不支持字段级过期 | ✅ 可拆成多个 String |
| 复杂嵌套 | ❌ 只支持扁平 field-value | ✅ JSON 支持任意嵌套 |

**选型建议**：扁平对象（如商品基础信息）用 Hash；嵌套结构（如含数组、多层对象）用 String 存 JSON；需要字段级 TTL 时拆成多个 String。

### 二、Set 类型

#### 1. Set 是什么

Set 是无序、不重复的字符串集合。最大特色：自动去重 + 支持集合运算（交、并、差）。

#### 2. 基础操作

| 命令 | 作用 |
| --- | --- |
| `SADD key member [member ...]` | 添加元素（已存在的会被忽略） |
| `SREM key member [member ...]` | 移除元素 |
| `SMEMBERS key` | 返回所有元素 |
| `SISMEMBER key member` | 判断是否成员（返回 0/1） |
| `SCARD key` | 集合元素数量 |

> `SMEMBERS` 在大集合上会阻塞，生产环境扫描大 Set 应用 `SSCAN`。

#### 3. 随机与移动

| 命令 | 作用 |
| --- | --- |
| `SPOP key [count]` | 随机弹出（删除）元素 |
| `SRANDMEMBER key [count]` | 随机返回（不删除）元素 |
| `SMOVE source dest member` | 把元素从 source 移到 dest |

`SPOP` 适合抽奖（抽中即移除），`SRANDMEMBER` 适合随机推荐（可重复）。

#### 4. 集合运算

| 命令 | 作用 |
| --- | --- |
| `SDIFF key [key ...]` | 差集（第一个有、其余没有） |
| `SDIFFSTORE dest key [key ...]` | 差集存到 dest |
| `SINTER key [key ...]` | 交集 |
| `SINTERSTORE dest key [key ...]` | 交集存到 dest |
| `SINTERCARD numkeys key [key ...] [LIMIT n]` | 仅返回交集数量（7.0+） |
| `SUNION key [key ...]` | 并集 |
| `SUNIONSTORE dest key [key ...]` | 并集存到 dest |

`SINTERCARD` 只返回数量不返回元素，适合"只关心共同数量"的场景，更省内存与带宽。

#### 5. 扫描

| 命令 | 作用 |
| --- | --- |
| `SSCAN key cursor [MATCH pattern] [COUNT n]` | 渐进扫描元素 |

#### 6. 底层编码

| 编码 | 条件 | 说明 |
| --- | --- | --- |
| `intset` | 全部元素为整数且数量 ≤ 512 | 紧凑数组，省内存 |
| `listpack` | 元素少且短（7.2+） | 连续内存 |
| `hashtable` | 超过阈值或含非整数 | 真正的哈希表 |

阈值由 `set-max-intset-entries`、`set-max-listpack-entries`、`set-max-listpack-value` 控制。

#### 7. 应用场景

| 场景 | Key 设计 | 命令 |
| --- | --- | --- |
| 用户标签 | `tags:user:{id}` | SADD/SREM/SMEMBERS |
| 商品标签 | `tags:product:{id}` | SADD/SMEMBERS |
| 共同关注 | `following:{user_id}` | SINTER |
| 去重（UV） | `uv:page:{page}` | SADD/SADD + SCARD |
| 抽奖 | `lottery:{activity}` | SPOP/SRANDMEMBER |
| 黑白名单 | `blacklist` / `whitelist` | SISMEMBER |

**共同关注示例**：

```
SADD following:1001 2001 2002 2003
SADD following:1002 2002 2003 2004
SINTER following:1001 following:1002     # 返回 2002 2003
```

**抽奖示例**：

```
SADD lottery:activity-1 "user-A" "user-B" "user-C" "user-D" "user-E"
SRANDMEMBER lottery:activity-1 2     # 随机抽 2 名（不删除，可重复抽）
SPOP lottery:activity-1 1            # 随机抽 1 名（删除，不可重复抽）
```

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01-hash-commands.redis` | Hash 全部命令演示：HSET/HGET/HGETALL、HINCRBY、应用场景（商品信息、购物车、用户信息） |
| `Code/02-set-commands.redis` | Set 全部命令演示：SADD/SREM/SMEMBERS、SDIFF/SINTER/SUNION、应用场景（标签、共同关注、抽奖） |

执行方式：

```bash
redis-cli < "Day04 - Hash与Set数据类型/Code/01-hash-commands.redis"
redis-cli < "Day04 - Hash与Set数据类型/Code/02-set-commands.redis"
```

## 关键知识点总结

### Hash 命令速查

| 命令 | 作用 | 复杂度 |
| --- | --- | --- |
| `HSET key f v [f v ...]` | 设置字段 | O(N) N=字段数 |
| `HGET key f` | 读字段 | O(1) |
| `HMGET key f [f ...]` | 批量读 | O(N) |
| `HGETALL key` | 读全部 | O(N) |
| `HKEYS key` | 所有字段名 | O(N) |
| `HVALS key` | 所有值 | O(N) |
| `HLEN key` | 字段数 | O(1) |
| `HSETNX key f v` | 字段不存在才设 | O(1) |
| `HEXISTS key f` | 字段是否存在 | O(1) |
| `HDEL key f [f ...]` | 删字段 | O(N) |
| `HINCRBY key f n` | 字段 +n | O(1) |
| `HINCRBYFLOAT key f f` | 字段 +f | O(1) |
| `HRANDFIELD key [count [WITHVALUES]]` | 随机字段 | O(N) |
| `HSCAN key cursor [MATCH] [COUNT]` | 渐进扫描 | O(1) 单次 |

### Set 命令速查

| 命令 | 作用 | 复杂度 |
| --- | --- | --- |
| `SADD key m [m ...]` | 添加 | O(N) |
| `SREM key m [m ...]` | 移除 | O(N) |
| `SMEMBERS key` | 全部元素 | O(N) |
| `SISMEMBER key m` | 是否成员 | O(1) |
| `SCARD key` | 元素数 | O(1) |
| `SPOP key [count]` | 随机弹出 | O(N) |
| `SRANDMEMBER key [count]` | 随机返回 | O(N) |
| `SMOVE src dest m` | 移动元素 | O(1) |
| `SDIFF key [key ...]` | 差集 | O(N) |
| `SINTER key [key ...]` | 交集 | O(N*M) |
| `SINTERCARD numkeys key... [LIMIT]` | 交集数量 | O(N*M) |
| `SUNION key [key ...]` | 并集 | O(N) |
| `SDIFFSTORE/SINTERSTORE/SUNIONSTORE` | 运算结果存 dest | O(N) |
| `SSCAN key cursor [MATCH] [COUNT]` | 渐进扫描 | O(1) 单次 |

### 应用场景对照表

| 场景 | Hash | Set |
| --- | --- | --- |
| 对象存储 | ✅ HSET/HGETALL | ❌ |
| 购物车 | ✅ field=product_id | ❌ |
| 配置项 | ✅ field=key | ❌ |
| 标签系统 | ❌ | ✅ SADD/SMEMBERS |
| 共同关注 | ❌ | ✅ SINTER |
| 去重 | ❌ | ✅ SADD + SCARD |
| 抽奖 | ❌ | ✅ SPOP/SRANDMEMBER |
| 黑白名单 | ❌ | ✅ SISMEMBER |

### 底层编码对照表

| 类型 | 小数据编码 | 大数据编码 |
| --- | --- | --- |
| Hash | listpack（≤128 字段且值 ≤64 字节） | hashtable |
| Set | intset（全整数 ≤512）/ listpack（7.2+） | hashtable |

## 实战练习

1. **购物车完整实现**
   - 用 Hash 实现购物车：`HSET cart:1001 1001 2 1002 1 1003 3`。
   - 商品 1001 再加 1 件：`HINCRBY cart:1001 1001 1`。
   - 移除商品 1002：`HDEL cart:1001 1002`。
   - 查看购物车：`HGETALL cart:1001`，统计种类：`HLEN cart:1001`。
   - 思考：如果商品 1001 数量减到 0，是否需要主动 HDEL？（是，否则留下空字段）

2. **共同关注与推荐**
   - 用户 1001 关注：`SADD following:1001 2001 2002 2003 2005`。
   - 用户 1002 关注：`SADD following:1002 2002 2003 2004`。
   - 求共同关注：`SINTER following:1001 following:1002`。
   - 求 1001 关注但 1002 未关注（推荐 1002 关注）：`SDIFF following:1001 following:1002`。
   - 求两人关注并集：`SUNION following:1001 following:1002`。

3. **抽奖活动**
   - 录入参与者：`SADD lottery:act1 u1 u2 u3 u4 u5 u6 u7 u8 u9 u10`。
   - 一等奖抽 1 名（抽中即移除，不可重复）：`SPOP lottery:act1 1`。
   - 二等奖抽 2 名（同上）：`SPOP lottery:act1 2`。
   - 随机推荐 3 名（不删除，可重复）：`SRANDMEMBER lottery:act1 3`。
   - 查看剩余参与人数：`SCARD lottery:act1`。
