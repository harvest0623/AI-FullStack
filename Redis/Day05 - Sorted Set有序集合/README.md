# Day05 - Sorted Set 有序集合

Sorted Set（有序集合，简称 ZSet）是 Redis 最具特色的数据类型。它在 Set 的基础上为每个成员关联了一个 `score`（分值），并按分值自动排序。正是这种"成员唯一 + 自动排序"的特性，使 Sorted Set 成为排行榜、延迟队列、带权重随机等场景的天然选择。掌握 Sorted Set，等于掌握了 Redis 在"排序"领域的杀手锏。

## 学习目标

- 理解 Sorted Set 的核心特性：成员唯一、按 score 排序、O(logN) 操作复杂度
- 熟练使用 ZADD 全部选项（NX/XX/GT/LT/CH/INCR），并根据场景选择合适组合
- 掌握范围查询（ZRANGE / ZRANGEBYSCORE）与排名查询（ZRANK / ZREVRANK）
- 理解集合运算 ZUNIONSTORE / ZINTERSTORE / ZINTERCARD 及 AGGREGATE、WEIGHTS
- 理解弹出与阻塞弹出 ZPOPMIN / ZPOPMAX / BZPOPMIN / BZPOPMAX
- 了解底层结构 listpack 与 skiplist + dict 的切换条件
- 理解跳表（SkipList）原理及其相比平衡树的优势
- 完整实现电商排行榜（销量排行、Top 10、翻页、月度合并、用户排名查询）

---

## 理论知识讲解

### 1. Sorted Set 是什么

Sorted Set 是一个**有序的、成员唯一的集合**，每个成员关联一个浮点数 `score`，Redis 按 score 升序维护成员。它兼具 Set 的"去重"和 List 的"有序"两种特性，且所有操作都是 O(logN) 级别。

| 特性 | Set | Sorted Set |
|------|-----|------------|
| 成员唯一 | 是 | 是 |
| 自动排序 | 否 | 按 score 升序 |
| 查找复杂度 | O(1) | O(logN) |
| 范围查询 | 不支持 | 支持（按索引/score/字典序） |
| 单成员操作 | SADD/SREM O(1) | ZADD/ZREM O(logN) |
| 典型场景 | 标签/去重 | 排行榜/延迟队列 |

> 同一个 Sorted Set 中，多个成员可以有相同的 score，此时按成员的字典序排列。

### 2. ZADD 添加成员与选项详解

```
ZADD key [NX|XX] [GT|LT] [CH] [INCR] score member [score member ...]
```

| 选项 | 含义 | 典型用途 |
|------|------|---------|
| `NX` | 只添加新成员，不更新已存在成员 | 首次写入后不再覆盖 |
| `XX` | 只更新已存在成员，不添加新成员 | 仅修改已有数据 |
| `GT` | 仅当新 score 大于当前 score 时更新 | 取最大值（如历史最高分） |
| `LT` | 仅当新 score 小于当前 score 时更新 | 取最小值（如历史最低价） |
| `CH` | 返回值改为"被改变的成员数"（新增 + 更新） | 关心总变更数 |
| `INCR` | 将 score 视为增量，类似 ZINCRBY | 原子累加，返回新值（此时只能单个成员） |

> 默认行为：返回新增成员数（不含更新）。NX/GT/LT/XX 互斥规则详见官方文档，常见组合：`ZADD key NX` 防覆盖，`ZADD key GT CH` 仅刷新最高分。

```redis
ZADD leaderboard:sales:daily 100 "product:001" 200 "product:002"
ZADD leaderboard:sales:daily NX 150 "product:001"     # NX 不更新已存在成员
ZADD leaderboard:sales:daily GT 300 "product:001"      # 仅当 300 > 当前值时更新
ZADD leaderboard:sales:daily INCR 50 "product:001"     # 等价于 ZINCRBY
```

### 3. ZREM / ZSCORE / ZMSCORE

```redis
ZREM key member [member ...]                  # 删除成员，返回实际删除数
ZSCORE key member                             # 查询单个成员 score，不存在返回 nil
ZMSCORE key member [member ...]               # 批量查询 score，不存在的返回 nil
```

### 4. ZINCRBY 增加 score

```redis
ZINCRBY key increment member                  # 对成员 score 增加增量
```

`ZINCRBY` 是排行榜"增量更新"的核心命令。例如某商品卖出 5 件，调用 `ZINCRBY leaderboard:sales:daily 5 "product:001"` 即可原子地把销量加 5，且自动重排。

### 5. ZCARD / ZCOUNT 计数

```redis
ZCARD key                                     # 返回成员总数
ZCOUNT key min max                            # 返回 score 在 [min, max] 内的成员数
```

`min`/`max` 支持开区间：`(` 表示不包含，例如 `ZCOUNT key (80 100` 统计 80 < score ≤ 100 的成员数。也支持 `+inf` / `-inf`。

### 6. ZRANGE / ZREVRANGE 按索引范围查询

```redis
ZRANGE key start stop [WITHSCORES]            # 升序，按索引取 [start, stop]
ZREVRANGE key start stop [WITHSCORES]         # 降序，按索引取 [start, stop]
```

索引从 0 开始，支持负数（-1 表示最后一个）。`WITHSCORES` 会把 score 跟在成员后面成对返回。

```redis
ZREVRANGE leaderboard:sales:daily 0 9 WITHSCORES    # 销量 Top 10
ZREVRANGE leaderboard:sales:daily 10 19 WITHSCORES  # 第 11-20 名（翻页第二页）
```

> Redis 6.2+ 推荐用统一的 `ZRANGE` 配合 `BYSCORE` / `BYLEX` / `REV` / `LIMIT` 选项替代 `ZREVRANGEBYSCORE` 等老命令，但老命令仍广泛使用。

### 7. ZRANGEBYSCORE / ZREVRANGEBYSCORE 按 score 范围

```redis
ZRANGEBYSCORE key min max [WITHSCORES] [LIMIT offset count]
ZREVRANGEBYSCORE key max min [WITHSCORES] [LIMIT offset count]
```

注意 `ZREVRANGEBYSCORE` 的参数是 `max min`（先大后小）。`LIMIT offset count` 支持分页。

```redis
ZRANGEBYSCORE leaderboard:sales:daily 80 100 LIMIT 0 10   # 80 ≤ score ≤ 100 的前 10 个
ZRANGEBYSCORE leaderboard:sales:daily (80 +inf             # score > 80 的全部
```

### 8. ZRANGE BYLEX / 按字典序范围

Redis 6.2+ 的 `ZRANGE key min max BYLEX` 用于在 **score 相同**时按成员字典序查询：

```redis
ZRANGE myzset - + BYLEX                  # 全部，按字典序
ZRANGE myzset "[a" "[f" BYLEX            # 成员在 [a, f] 之间
ZRANGE myzset "(a" "(f" BYLEX            # 开区间 (a, f)
```

`[` 表示包含，`(` 表示不包含，`-`/`+` 表示最小/最大。仅在所有成员 score 相同时才有意义。

### 9. ZRANK / ZREVRANK 排名查询

```redis
ZRANK key member                  # 升序排名（0 开始）
ZREVRANK key member               # 降序排名（0 开始，即"第几名"）
```

排行榜中通常用 `ZREVRANK` 查询"该用户排第几名"。

### 10. ZREMRANGEBYRANK / ZREMRANGEBYSCORE

```redis
ZREMRANGEBYRANK key start stop              # 按索引范围删除
ZREMRANGEBYSCORE key min max                # 按 score 范围删除
```

常用于**只保留 Top N**：`ZREMRANGEBYRANK key 0 -(N+1)` 删除排名 N 之后的成员。

### 11. ZPOPMIN / ZPOPMAX / BZPOPMIN / BZPOPMAX

```redis
ZPOPMIN key [count]                  # 弹出 score 最小的成员
ZPOPMAX key [count]                  # 弹出 score 最大的成员
BZPOPMIN key [key ...] timeout       # 阻塞式 ZPOPMIN（秒级超时，0 表示永久阻塞）
BZPOPMAX key [key ...] timeout       # 阻塞式 ZPOPMAX
```

`BZPOP*` 是阻塞版本，常用于实现**延迟队列**的消费端：score 存放执行时间戳，消费者用 `BZPOPMIN` 等待最早到期的任务。

### 12. ZUNIONSTORE / ZINTERSTORE / ZINTERCARD

```redis
ZUNIONSTORE dest numkeys key [key ...] [WEIGHTS w1 ...] [AGGREGATE SUM|MIN|MAX]
ZINTERSTORE dest numkeys key [key ...] [WEIGHTS w1 ...] [AGGREGATE SUM|MIN|MAX]
ZINTERCARD numkeys key [key ...] [LIMIT limit]            # 7.0+ 只返回交集数量，不存结果
```

| 选项 | 含义 |
|------|------|
| `WEIGHTS` | 给每个源 Sorted Set 的 score 乘以权重后再聚合 |
| `AGGREGATE SUM` | 默认，将各集合中同一成员的 score 求和 |
| `AGGREGATE MIN` | 取最小 |
| `AGGREGATE MAX` | 取最大 |

```redis
ZUNIONSTORE leaderboard:sales:monthly 2 leaderboard:sales:daily:20250101 leaderboard:sales:daily:20250102
```

`ZINTERCARD` 只算交集元素个数，不实际落盘，适合"同时上过两个榜的商品数"这种统计。

### 13. ZRANDMEMBER

```redis
ZRANDMEMBER key [count [WITHSCORES]]          # 随机返回成员，count 正数去重、负数可重复
```

可用于"带权重的随机抽奖"：score 越高越靠前，但 ZRANDMEMBER 本身是等概率的，加权随机通常配合 Lua 或多次 ZPOPMAX 实现。

---

### 14. 底层结构：listpack 与 skiplist + dict

Redis 7.0 之后，Sorted Set 的底层编码有两种：

| 编码 | 触发条件 | 数据结构 | 优势 |
|------|---------|---------|------|
| `listpack` | 成员数 < 128 且每个元素长度 < 64 字节 | 紧凑连续内存的小型列表 | 内存占用极小、访问连续友好 |
| `skiplist + dict` | 超过上述任一阈值 | 跳表 + 哈希表组合 | 范围查询 O(logN)、单点查询 O(1) |

可通过 `OBJECT ENCODING key` 查看当前编码。阈值由 `zset-max-listpack-entries` 和 `zset-max-listpack-value` 配置控制。

#### 为什么需要"跳表 + 字典"两套结构？

- **跳表（skiplist）**：负责按 score 排序，支持范围查询、排名，O(logN)
- **字典（dict）**：成员 → score 的映射，支持 O(1) 查询单成员的 score（ZSCORE）
- 两者共享同一份成员对象，内存代价可控

如果只有跳表，ZSCORE 需 O(logN)；如果只有字典，范围查询需 O(NlogN) 排序。组合后两类操作都高效。

### 15. 跳表（SkipList）原理

跳表是一种**概率平衡的多层链表**，通过为部分节点建立"索引层"来实现类似二分查找的效果。

```
Level 3:  HEAD ──────────────────────► 30 ─────────► NULL
Level 2:  HEAD ──────► 10 ───────────► 30 ──────► 50 ─► NULL
Level 1:  HEAD ─► 5 ─► 10 ─► 20 ────► 30 ─► 40 ─► 50 ─► NULL
Level 0:  HEAD ─► 5 ─► 10 ─► 20 ─► 25 ─► 30 ─► 40 ─► 50 ─► 60 ─► NULL
```

- 每个节点按概率（通常 1/2 或 1/4）决定是否"提升"到上一层
- 查找从最高层开始，遇到比目标大的就下降一层，类似走"快速通道"
- 平均时间复杂度 O(logN)，最坏 O(N)（概率极低）

#### 跳表 vs 平衡树（AVL/红黑树）

| 维度 | 跳表 | 平衡树 |
|------|------|--------|
| 实现复杂度 | 简单（链表 + 概率） | 复杂（旋转/重染色） |
| 范围查询 | 友好（链表顺序遍历） | 需中序遍历 |
| 并发友好 | 链表局部加锁容易 | 旋转影响范围大 |
| 内存灵活 | 每节点指针数可变 | 固定指针 |
| 平均复杂度 | O(logN) | O(logN) |

Redis 作者 antirez 选择跳表的原因：实现简单、范围查询天然友好、内存可控。这也是 Sorted Set 能高效支撑排行榜翻页的根本所在。

---

### 16. 应用场景

#### 16.1 排行榜

- 销量排行：`ZINCRBY leaderboard:sales:daily N "product:xxx"`，每次下单增量更新
- 积分排行：用户签到/消费/活动得积分，`ZADD` 或 `ZINCRBY` 维护
- 热搜排行：score = 搜索次数，定期 `ZREMRANGEBYRANK` 只保留 Top N

#### 16.2 延迟队列

score 存放任务执行的时间戳，消费者用 `BZPOPMIN` 阻塞等待最早到期的任务。例如订单 30 分钟未支付自动取消：下单时 `ZADD delay:order:cancel <now+1800> "order:12345"`。

#### 16.3 带权重的随机选择

score 作为权重，配合 Lua 脚本实现加权随机抽样（比 ZRANDMEMBER 的等概率更可控）。

#### 16.4 时间线 / Feed 流

score 存放微博/动态的时间戳，`ZREVRANGE` 取最新 N 条；关注的人的动态可通过 `ZUNIONSTORE` 合并。

---

## 代码文件说明

| 文件 | 内容 |
|------|------|
| `Code/01-sorted-set-commands.redis` | Sorted Set 全部命令演示：ZADD 各选项、ZINCRBY、ZCARD/ZCOUNT、ZRANGE/ZREVRANGE、ZRANGEBYSCORE、ZRANK/ZREVRANK、ZPOPMIN/ZPOPMAX、ZUNIONSTORE/ZINTERSTORE/ZINTERCARD、ZRANDMEMBER、ZMSCORE |
| `Code/02-leaderboard-demo.redis` | 排行榜完整实战：商品销量 ZINCRBY 增量更新、Top 10 查询、翻页、月度排行 ZUNIONSTORE 合并、用户排名 ZREVRANK 查询 |

> 执行方式：`redis-cli < Code/01-sorted-set-commands.redis`，或进入 redis-cli 后逐行复制粘贴。

---

## 关键知识点总结

### Sorted Set 命令速查

| 命令 | 作用 | 复杂度 |
|------|------|--------|
| ZADD | 添加/更新成员 | O(logN) |
| ZREM | 删除成员 | O(logN) |
| ZSCORE / ZMSCORE | 查 score | O(1) / O(M) |
| ZINCRBY | score 增量 | O(logN) |
| ZCARD | 成员总数 | O(1) |
| ZCOUNT | score 范围内数量 | O(logN) |
| ZRANGE / ZREVRANGE | 索引范围 | O(logN+M) |
| ZRANGEBYSCORE | score 范围 | O(logN+M) |
| ZRANK / ZREVRANK | 排名 | O(logN) |
| ZPOPMIN / ZPOPMAX | 弹出最值 | O(logN) |
| BZPOPMIN / BZPOPMAX | 阻塞弹出 | O(logN) |
| ZUNIONSTORE / ZINTERSTORE | 并集/交集 | O(N log N) |
| ZINTERCARD | 交集数量 | O(N) |

### 跳表结构示意

```
            ┌──────────────┐
       L3:  │  HEAD        │────────────────────────► 50 ─► NULL
            └──────┬───────┘
       L2:  HEAD ─► 20 ─────────► 40 ─────────► 50 ─► NULL
            │
       L1:  HEAD ─► 10 ─► 20 ─► 30 ─► 40 ─► 50 ─► NULL
            │
       L0:  HEAD ─► 5 ─► 10 ─► 20 ─► 30 ─► 40 ─► 50 ─► 60 ─► NULL

查找 30：L3 跳到 50（超了，下降）→ L2 到 40（超了，下降）→ L1 到 30 命中
```

### 应用场景对照表

| 场景 | 典型命令 | score 含义 |
|------|---------|-----------|
| 销量排行 | ZINCRBY / ZREVRANGE | 销量件数 |
| 积分排行 | ZADD / ZREVRANK | 用户积分 |
| 延迟队列 | ZADD / BZPOPMIN | 执行时间戳 |
| 热搜榜 | ZINCRBY / ZREMRANGEBYRANK | 搜索次数 |
| 时间线 | ZADD / ZREVRANGE | 发布时间戳 |
| 加权随机 | ZPOPMAX / Lua | 权重值 |

---

## 实战练习

### 练习 1：商品销量日榜自动维护

设计一个电商日销量排行榜的完整维护流程：
1. 初始状态下，3 个商品分别售出 10、25、8 件，写入 `leaderboard:sales:daily`
2. 商品 `product:002` 又售出 12 件，使用 `ZINCRBY` 增量更新
3. 查询当前 Top 3 商品及其销量
4. 查询商品 `product:001` 的当前排名（从高到低）

**提示**：排行榜从高到低，用 `ZREVRANGE` 与 `ZREVRANK`。

### 练习 2：周榜合并与 Top N 裁剪

假设你保存了一周内每天的销量榜 `leaderboard:sales:daily:20250120` ~ `leaderboard:sales:daily:20250126`：
1. 用 `ZUNIONSTORE` 合并 7 天的榜单为 `leaderboard:sales:weekly`（默认 SUM 聚合）
2. 只保留周榜前 100 名，其余用 `ZREMRANGEBYRANK` 删除
3. 统计周榜中有多少商品销量超过 500 件（用 `ZCOUNT`）

### 练习 3：延迟队列实现

实现一个"订单超时取消"延迟队列：
1. 模拟 3 个订单，分别在 60 秒、120 秒、180 秒后到期，用 `ZADD delay:order:cancel <timestamp> "order:xxx"` 写入
2. 用 `ZRANGEBYSCORE delay:order:cancel -inf <now>` 查询已到期的订单
3. 模拟消费者取出最早到期的订单：`BZPOPMIN delay:order:cancel 1`
4. 思考：消费者拿到订单后取消操作成功，应该如何从队列删除该成员？

**提示**：`BZPOPMIN` 已经弹出成员，无需再删；若是 `ZRANGEBYSCORE` 拿到的则需要 `ZREM`。
