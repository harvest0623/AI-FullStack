# Day07 - 发布订阅与 Stream 消息队列

消息通信是后端系统的核心能力之一。Redis 提供了两种差异显著的消息方案：**Pub/Sub 发布订阅**是最简单的消息模式，发布者把消息推送到频道，订阅者实时接收，"fire and forget"即发即忘，适合实时通知、聊天等容忍丢消息的场景；**Stream 消息队列**则是 Redis 5.0 引入的生产级方案，具备持久化、消费组、消息确认、可回溯等完整能力，可以替代轻量级 Kafka/RabbitMQ。本天深入对比两者差异，并完整演练 Stream 消费者组的死信处理流程，是 Redis 从"缓存工具"走向"消息基础设施"的关键内容。

## 学习目标

- 理解 Pub/Sub 发布订阅模型与命令（SUBSCRIBE/PUBLISH/PSUBSCRIBE/PUBSUB）
- 理解 Pub/Sub 的局限性（无持久化、无消费确认、离线丢消息、无消费组）
- 深入掌握 Stream 作为消息队列的完整流程：创建组、生产、消费、确认、待确认查询、死信转移
- 理解 Stream 消息 ID 机制与 MAXLEN/MINID 裁剪策略
- 对比 Stream / Kafka / RabbitMQ 的适用场景
- 能根据业务场景在 Pub/Sub 与 Stream 之间做出正确选择

---

## 理论知识讲解

### 1. Pub/Sub 发布订阅模型

#### 1.1 概念

Pub/Sub 是 Redis 最简单的消息模式。发布者（Publisher）把消息发送到一个**频道（Channel）**，所有订阅该频道的客户端都会实时收到消息。Redis 只负责"转发"，**不存储任何消息**——消息发出后立即丢弃，离线订阅者收不到。

```
┌─────────────┐         PUBLISH          ┌─────────┐         推送          ┌──────────────┐
│  Publisher  │ ────────────────────────► │  Redis  │ ───────────────────► │  Subscriber  │
└─────────────┘   pubsub:notifications    │ Server  │   pubsub:notifications└──────────────┘
                                          │         │         推送          ┌──────────────┐
                                          │         │ ───────────────────► │  Subscriber  │
                                          └─────────┘                       └──────────────┘
                                              不存储消息，fire and forget
```

#### 1.2 核心命令

```redis
SUBSCRIBE channel [channel ...]              # 订阅一个或多个频道（阻塞）
UNSUBSCRIBE [channel ...]                    # 取消订阅
PSUBSCRIBE pattern [pattern ...]             # 按模式订阅（如 news.*）
PUNSUBSCRIBE [pattern ...]                   # 取消模式订阅
PUBLISH channel message                      # 发布消息到频道
PUBSUB CHANNELS [pattern]                    # 列出当前有订阅者的频道
PUBSUB NUMSUB [channel ...]                  # 查询某频道的订阅者数量
PUBSUB NUMPAT                                # 查询模式订阅总数
```

#### 1.3 使用示例

订阅端（终端 A）：
```redis
SUBSCRIBE pubsub:notifications
```

发布端（终端 B）：
```redis
PUBLISH pubsub:notifications "order:1001 has been shipped"
```

模式订阅：
```redis
PSUBSCRIBE order.*         # 订阅 order.create、order.pay、order.ship 等
```

#### 1.4 Pub/Sub 的局限性

| 局限 | 说明 | 后果 |
|------|------|------|
| 无持久化 | 消息不存储，发出即丢 | 离线订阅者收不到历史消息 |
| 无消费确认 | 没有 ACK 机制 | 消费者处理失败无法重试 |
| 无消费组 | 所有订阅者都收到全部消息 | 无法"一条消息只被一个消费者处理" |
| 消息堆积不可控 | 无法限制积压 | 慢消费者会被 Redis 主动断开（output buffer 超限） |
| 频道查询受限 | 只能查"当前有订阅者的频道" | 无法知道历史频道 |

> Pub/Sub 适合：实时通知、聊天室、日志广播、配置变更通知。不适合：订单处理、任务队列、需要可靠投递的场景。

### 2. Stream 作为消息队列（深入）

#### 2.1 Stream vs Pub/Sub

| 维度 | Pub/Sub | Stream |
|------|---------|--------|
| 持久化 | 否 | 是（落盘 + AOF） |
| 消费确认 | 无 | XACK |
| 消费组 | 无 | 有（一条消息组内只投递给一个消费者） |
| 离线消息 | 丢失 | 可回溯（按 ID 读取历史） |
| 消息堆积 | 不可控 | 可控（MAXLEN/MINID 裁剪） |
| 阻塞等待 | SUBSCRIBE 阻塞 | XREAD/XREADGROUP BLOCK |
| 模式订阅 | PSUBSCRIBE | 不支持（需自己路由） |
| 适用场景 | 实时广播 | 可靠消息队列 |

#### 2.2 消费组模型完整流程

```
┌────────────────────────────────────────────────────────────────────┐
│                     Stream 消费组完整流程                            │
└────────────────────────────────────────────────────────────────────┘

1. 创建消费组
   XGROUP CREATE stream:orders order_processors $ MKSTREAM
   ── $ 表示只消费创建组之后的新消息；0 表示从头消费
   ── MKSTREAM 表示 Stream 不存在时自动创建

2. 生产者写入消息
   XADD stream:orders * type "create" orderId "1001"
   ── * 自动生成 ID（毫秒时间戳-序号）

3. 消费者拉取消息（消费组模式）
   XREADGROUP GROUP order_processors consumer-1 COUNT 10 BLOCK 5000 STREAMS stream:orders >
   ── > 表示"未投递给本组的新消息"
   ── 拉取后消息进入该消费者的 pending 列表（待确认）

4. 消费者处理完后确认
   XACK stream:orders order_processors <msgid>
   ── 确认后从 pending 列表移除；不确认则一直保留

5. 查看待确认消息
   XPENDING stream:orders order_processors
   ── 返回待确认总数、最小/最大 ID、各消费者的待确认数

6. 死信处理：转移超时消息
   XCLAIM stream:orders order_processors consumer-3 30000 <msgid>
   ── 把 idle 超过 30 秒的待确认消息转移给 consumer-3
   ── 或用 XAUTOCLAIM 批量自动转移

7. 消息裁剪
   XTRIM stream:orders MAXLEN ~ 10000
   ── 近似裁剪到 10000 条，性能更好
```

#### 2.3 消费者组保证

- **每条消息只被组内一个消费者处理**：消费组内 `>` 投递是排他的
- **消息可回溯**：用 `XREADGROUP ... 0` 可重新读取 pending 列表
- **故障转移**：消费者崩溃后，其 pending 消息可被 XCLAIM 转移给其他消费者
- **不同组独立消费**：多个消费组可各自从头消费同一条 Stream，互不影响

#### 2.4 Stream 消息 ID

- `*`：由 Redis 自动生成，格式 `<毫秒时间戳>-<序号>`，如 `1738000000000-0`
- 手动指定：`XADD stream 1738000000000-0 field value`，必须大于当前最大 ID
- 同一毫秒内多条消息，序号递增：`...-0`、`...-1`、`...-2`
- ID 单调递增，天然按时间有序

#### 2.5 MAXLEN / MINID 裁剪策略

```redis
XTRIM key MAXLEN = 1000          # 精确裁剪到 1000 条
XTRIM key MAXLEN ~ 1000          # 近似裁剪（性能更好，可能略多）
XTRIM key MINID = 1738000000000-0   # 删除 ID 小于指定值的消息
XTRIM key MINID ~ 1738000000000-0   # 近似版本
```

`~` 近似裁剪通过删除整个 listpack 节点来提升性能，允许多保留少量消息，生产环境推荐。

也可以在 XADD 时直接带裁剪：`XADD stream MAXLEN ~ 10000 * field value`。

#### 2.6 Stream vs Kafka vs RabbitMQ 对比

| 维度 | Redis Stream | Kafka | RabbitMQ |
|------|--------------|-------|----------|
| 部署复杂度 | 极低（单机即可） | 高（依赖 ZK/KRaft） | 中 |
| 持久化 | RDB + AOF | 磁盘日志 | 可选持久化 |
| 吞吐量 | 10万+/秒 | 百万/秒 | 万级/秒 |
| 消费组 | 支持 | 支持 | 支持（队列模型） |
| 消息回溯 | 支持（按 ID） | 支持（按 offset） | 不支持 |
| 延迟 | 极低（内存） | 低 | 中 |
| 消息堆积 | 受内存限制 | 磁盘海量 | 内存/磁盘 |
| 适用场景 | 中小规模、低延迟、与 Redis 共栈 | 大数据流、日志、事件驱动 | 企业级消息路由、复杂协议 |

> Redis Stream 适合：QPS 10 万以内、对延迟敏感、已用 Redis 不想引入新组件、消息量可控的场景。大数据量日志流仍推荐 Kafka。

### 3. 应用场景

#### 3.1 实时通知（Pub/Sub）

用户下单、发货、退款等事件实时推送给前端：`PUBLISH pubsub:notifications '{"event":"ship","orderId":"1001"}'`。前端用 WebSocket 订阅频道即可。容忍丢消息（关键业务用 Stream 兜底）。

#### 3.2 订单事件流（Stream）

订单生命周期事件（创建、支付、发货、签收、退款）全部追加到 `stream:orders`，多个消费组分别处理：
- `order_processors`：更新订单状态
- `inventory_sync`：扣减/恢复库存
- `analytics`：实时统计分析

#### 3.3 聊天消息（Pub/Sub + Stream 混合）

- 在线用户用 Pub/Sub 实时推送（低延迟）
- 离线消息用 Stream 存储，用户上线后回拉

---

## 代码文件说明

| 文件 | 内容 |
|------|------|
| `Code/01-pubsub-demo.redis` | Pub/Sub 演示：PUBLISH 发布消息、PUBSUB 查询频道与订阅数；说明 SUBSCRIBE 是阻塞命令需多终端操作 |
| `Code/02-stream-mq-demo.redis` | Stream 消费者组完整演示：创建 Stream、创建消费组、XADD 生产、XREADGROUP 消费、XACK 确认、XPENDING 查待确认、XCLAIM/XAUTOCLAIM 转移死信、XINFO 查看组信息 |
| `Code/README.md` | 多终端操作指南：说明如何开多个 redis-cli 终端模拟 Pub/Sub 订阅者/发布者、Stream 生产者/消费者 |

> Pub/Sub 需要多终端协作，无法在单个 `.redis` 管道文件中演示完整流程。请先阅读 `Code/README.md` 了解操作方式。

---

## 关键知识点总结

### Pub/Sub 命令速查

| 命令 | 作用 | 备注 |
|------|------|------|
| SUBSCRIBE | 订阅频道 | 阻塞 |
| UNSUBSCRIBE | 取消订阅 | |
| PSUBSCRIBE | 模式订阅 | 如 `news.*` |
| PUNSUBSCRIBE | 取消模式订阅 | |
| PUBLISH | 发布消息 | 返回收到消息的订阅者数 |
| PUBSUB CHANNELS | 列出活跃频道 | |
| PUBSUB NUMSUB | 查订阅者数 | |
| PUBSUB NUMPAT | 模式订阅总数 | |

### Stream 消费组流程图

```
┌──────────────┐   XADD    ┌───────────────────────────────────┐
│  Producer    │ ─────────►│          Stream:orders            │
└──────────────┘           │  msg1  msg2  msg3  msg4  msg5 ... │
                           └─────────────┬─────────────────────┘
                                         │ XREADGROUP GROUP g c1 >
                                         │ (排他投递，组内一个消费者拿一条)
                      ┌──────────────────┼──────────────────┐
                      ▼                  ▼                  ▼
                ┌──────────┐       ┌──────────┐       ┌──────────┐
                │consumer-1│       │consumer-2│       │consumer-3│
                │ pending  │       │ pending  │       │ pending  │
                │  [msg1]  │       │  [msg2]  │       │  [msg3]  │
                └────┬─────┘       └────┬─────┘       └────┬─────┘
                     │ XACK            │ 崩溃未 ACK       │ XACK
                     ▼                 │                  ▼
                 已确认              pending 列表保留    已确认
                                     │
                                     │ XPENDING 查询
                                     │ XCLAIM/XAUTOCLAIM 转移
                                     ▼
                               consumer-3 重新处理
```

### 三种消息方案对比表

| 维度 | Redis Pub/Sub | Redis Stream | Kafka |
|------|--------------|--------------|-------|
| 持久化 | 否 | 是 | 是 |
| 消费确认 | 无 | XACK | offset commit |
| 消费组 | 无 | 有 | 有 |
| 离线消息 | 丢 | 可回溯 | 可回溯 |
| 消息堆积 | 不可控 | MAXLEN | 磁盘海量 |
| 模式订阅 | PSUBSCRIBE | 无 | 无 |
| 吞吐量 | 高 | 10万+/秒 | 百万/秒 |
| 部署复杂度 | 极低 | 极低 | 高 |
| 适用 | 实时广播 | 中小规模可靠队列 | 大数据流 |

---

## 实战练习

### 练习 1：实时通知频道

模拟电商平台的实时通知系统：
1. 开两个 redis-cli 终端
2. 终端 A 执行 `SUBSCRIBE pubsub:notifications` 进入订阅
3. 终端 B 执行 `PUBLISH pubsub:notifications "订单 1001 已发货"`
4. 观察 A 是否收到消息
5. 关闭 A，再从 B 发布一条消息，重新订阅 A，验证"离线丢消息"
6. 用 `PUBSUB CHANNELS` 查看活跃频道，`PUBSUB NUMSUB pubsub:notifications` 查订阅者数

**提示**：详细步骤见 `Code/README.md`。

### 练习 2：订单事件流消费组

实现一个订单事件流的完整消费组流程：
1. 创建 Stream `stream:orders`，写入 5 条订单事件（create/pay/ship 等）
2. 创建消费组 `order_processors`，从头消费
3. 启动 consumer-1 消费 3 条消息，XACK 其中 2 条，1 条不确认（模拟处理失败）
4. 启动 consumer-2 消费剩余 2 条
5. 用 XPENDING 查看 consumer-1 的待确认消息
6. 用 XAUTOCLAIM 把 consumer-1 超时消息转移给 consumer-3
7. consumer-3 处理完后 XACK
8. 用 XINFO GROUPS 与 XINFO CONSUMERS 查看最终状态

**提示**：完整命令见 `Code/02-stream-mq-demo.redis`。

### 练习 3：Pub/Sub 与 Stream 混合通知系统

设计一个混合方案：
1. 关键订单事件用 Stream 持久化（`stream:orders`），保证不丢
2. 用户在线时用 Pub/Sub 实时推送通知（`pubsub:notifications`）
3. 思考：如何用 Redis 的 keyspace notification（键空间通知）配合 Stream 实现消息二级分发？

**提示**：Stream 消费组处理完后，再用 PUBLISH 推一份到 Pub/Sub 频道给在线用户；离线用户下次上线从 Stream 回拉。
