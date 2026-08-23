# Day07 Code - 多终端操作指南

本目录的演示涉及 Redis 的 Pub/Sub 与 Stream 消息队列，部分场景需要**同时开多个 redis-cli 终端**才能完整观察消息流转。本指南说明如何准备终端、按顺序执行命令，并给出可复制的命令清单。

## 准备工作

### 启动 Redis 服务

确保 Redis 7.0+ 已启动（默认端口 6379）。可用 Docker 或本地安装：

```bash
# Docker 方式
docker run -d --name redis-learn -p 6379:6379 redis:7

# 本地安装方式（Linux/macOS）
redis-server                     # 默认前台启动
# 或后台启动
redis-server --daemonize yes
```

### 打开多个终端

建议准备 3-4 个终端窗口（或标签页），每个终端都执行 `redis-cli` 连接到同一个 Redis 实例：

```bash
redis-cli
# 如果有密码
redis-cli -a yourpassword
# 如果用 Docker
docker exec -it redis-learn redis-cli
```

> 终端之间共享同一个 Redis 数据库，因此所有命令操作的是同一份数据。

---

## 场景一：Pub/Sub 发布订阅演示

### 涉及文件

- `01-pubsub-demo.redis`

### 步骤

#### 步骤 1：终端 A - 订阅者

打开终端 A，进入 redis-cli，执行订阅命令：

```redis
SUBSCRIBE pubsub:notifications
```

执行后终端 A 进入**阻塞订阅状态**，提示符变为：

```
Reading messages... (press Ctrl-C to quit)
1) "subscribe"
2) "pubsub:notifications"
3) (integer) 1
```

> 进入订阅状态后，该终端**无法执行其他命令**，只能接收消息。退出按 `Ctrl+C`。

#### 步骤 2：终端 B - 发布者

打开终端 B，进入 redis-cli，发布消息：

```redis
PUBLISH pubsub:notifications "order:1001 has been shipped"
```

返回 `(integer) 1` 表示有 1 个订阅者收到了消息。

切换回终端 A，应立即看到：

```
1) "message"
2) "pubsub:notifications"
3) "order:1001 has been shipped"
```

#### 步骤 3：发布多条通知

在终端 B 继续发布：

```redis
PUBLISH pubsub:notifications "{\"event\":\"order.pay\",\"orderId\":\"1001\",\"payMethod\":\"alipay\"}"
PUBLISH pubsub:notifications "{\"event\":\"user.login\",\"userId\":\"u:1\"}"
PUBLISH pubsub:notifications "{\"event\":\"coupon.grant\",\"userId\":\"u:1\",\"couponId\":\"c:100\"}"
```

终端 A 会逐条收到。

#### 步骤 4：验证离线丢消息

1. 在终端 A 按 `Ctrl+C` 退出订阅（模拟订阅者离线）
2. 在终端 B 发布一条消息：

   ```redis
   PUBLISH pubsub:notifications "this message will be lost"
   ```

   返回 `(integer) 0`（无订阅者）

3. 终端 A 重新订阅：

   ```redis
   SUBSCRIBE pubsub:notifications
   ```

4. **观察**：终端 A 收不到刚才那条 "this message will be lost" 消息——**Pub/Sub 不存储消息，离线期间的消息永久丢失**。

#### 步骤 5：多订阅者广播

开终端 C，也订阅同一频道：

```redis
SUBSCRIBE pubsub:notifications
```

终端 B 发布一条消息：

```redis
PUBLISH pubsub:notifications "broadcast to all"
```

**观察**：终端 A 和终端 C **都收到**这条消息——Pub/Sub 是广播模式，每个订阅者都收到全部消息。

#### 步骤 6：模式订阅

终端 C 先 `Ctrl+C` 退出，改用模式订阅：

```redis
PSUBSCRIBE order.*
```

终端 B 发布：

```redis
PUBLISH order.create "order:1003 created"
PUBLISH order.pay "order:1003 paid"
PUBLISH order.ship "order:1003 shipped"
PUBLISH order.cancel "order:1004 cancelled"
```

终端 C 收到的消息会包含 4 个字段（含 pattern）：

```
1) "pmessage"
2) "order.*"              # 匹配的模式
3) "order.create"         # 实际频道
4) "order:1003 created"   # 消息内容
```

#### 步骤 7：PUBSUB 查询命令

在终端 B（非订阅状态）执行：

```redis
PUBSUB CHANNELS                        # 列出所有有订阅者的频道
PUBSUB CHANNELS pubsub:*               # 按模式过滤
PUBSUB NUMSUB pubsub:notifications     # 查询某频道订阅者数
PUBSUB NUMSUB pubsub:notifications pubsub:orders pubsub:chat
PUBSUB NUMPAT                          # 模式订阅总数
```

---

## 场景二：Stream 消息队列消费者组演示

### 涉及文件

- `02-stream-mq-demo.redis`

Stream 的消费组流程**可以**在单个终端用管道文件完成（因为 XREADGROUP 不像 SUBSCRIBE 那样永久阻塞）。但为了清晰观察"生产者-消费者"协作，建议开多终端。

### 方式一：单终端管道执行（快速验证）

```bash
cd "d:/Coding/AI-FullStack/Redis/Day07 - 发布订阅与Stream消息队列/Code"
redis-cli < 02-stream-mq-demo.redis
```

### 方式二：多终端手动演示（推荐，理解更深入）

#### 终端 A - 准备 Stream 与消费组

```redis
DEL stream:orders

XADD stream:orders * event "create" orderId "1001" userId "u:1" amount 99.9
XADD stream:orders * event "create" orderId "1002" userId "u:2" amount 199.5
XADD stream:orders * event "pay"    orderId "1001" userId "u:1" payMethod "alipay"
XADD stream:orders * event "create" orderId "1003" userId "u:3" amount 49.0
XADD stream:orders * event "pay"    orderId "1002" userId "u:2" payMethod "wechat"

XGROUP CREATE stream:orders order_processors 0
```

#### 终端 B - consumer-1 消费

```redis
XREADGROUP GROUP order_processors consumer-1 COUNT 3 STREAMS stream:orders >
```

记录返回的 3 条消息 ID（形如 `1738000000000-0`）。

#### 终端 B - consumer-1 确认前 2 条

把上一步返回的前 2 个消息 ID 替换 `<msgid1>` `<msgid2>`：

```redis
XACK stream:orders order_processors <msgid1> <msgid2>
```

#### 终端 C - consumer-2 消费剩余

```redis
XREADGROUP GROUP order_processors consumer-2 COUNT 5 STREAMS stream:orders >
```

**故意不 ACK**，模拟 consumer-2 处理中崩溃。

#### 终端 A - 查看待确认消息

```redis
XPENDING stream:orders order_processors
XPENDING stream:orders order_processors - + 10
XINFO CONSUMERS stream:orders order_processors
```

#### 终端 A - 死信转移给 consumer-3

手动转移单条（替换 `<msgid>` 为 consumer-2 pending 中的消息 ID）：

```redis
XCLAIM stream:orders order_processors consumer-3 0 <msgid>
```

或自动批量转移：

```redis
XAUTOCLAIM stream:orders order_processors consumer-3 0 - COUNT 10
```

#### 终端 C - consumer-3 重新处理并 ACK

```redis
XREADGROUP GROUP order_processors consumer-3 COUNT 10 STREAMS stream:orders 0
```

处理完后 ACK（替换真实消息 ID）：

```redis
XACK stream:orders order_processors <msgid1> <msgid2> ...
```

#### 终端 A - 查看最终状态

```redis
XINFO STREAM stream:orders
XINFO GROUPS stream:orders
XINFO CONSUMERS stream:orders order_processors
XPENDING stream:orders order_processors
```

---

## 场景三：阻塞式消费演示

### 终端 A - 消费者阻塞等待

```redis
XREADGROUP GROUP order_processors consumer-1 COUNT 1 BLOCK 60000 STREAMS stream:orders >
```

`BLOCK 60000` 表示最多阻塞 60 秒。此时终端 A 进入等待状态。

### 终端 B - 生产者写入新消息

```redis
XADD stream:orders * event "create" orderId "1099" userId "u:9" amount 1.0
```

终端 A 应立即收到这条新消息并返回。

---

## 场景四：多消费组独立消费演示

同一个 Stream 可以被多个消费组独立消费，互不影响。

### 终端 A - 创建两个消费组

```redis
XGROUP CREATE stream:orders order_processors 0
XGROUP CREATE stream:orders order_auditors 0
```

### 终端 B - order_processors 组消费

```redis
XREADGROUP GROUP order_processors consumer-1 COUNT 3 STREAMS stream:orders >
```

### 终端 C - order_auditors 组消费（同样的消息）

```redis
XREADGROUP GROUP order_auditors auditor-1 COUNT 3 STREAMS stream:orders >
```

**观察**：两个消费组各自从头消费了同样的 3 条消息，互不影响。这适合"订单状态更新"和"审计日志"两个独立业务同时订阅同一 Stream。

---

## 常用命令速查

### Pub/Sub

```redis
SUBSCRIBE channel [channel ...]              # 订阅
UNSUBSCRIBE [channel ...]                    # 取消订阅
PSUBSCRIBE pattern [pattern ...]             # 模式订阅
PUNSUBSCRIBE [pattern ...]                   # 取消模式订阅
PUBLISH channel message                      # 发布消息
PUBSUB CHANNELS [pattern]                    # 活跃频道
PUBSUB NUMSUB [channel ...]                  # 订阅者数
PUBSUB NUMPAT                                # 模式订阅总数
```

### Stream 消费组

```redis
XGROUP CREATE key group id [MKSTREAM]        # 创建消费组
XREADGROUP GROUP g c [COUNT n] [BLOCK ms] STREAMS key >   # 消费新消息
XREADGROUP GROUP g c [COUNT n] STREAMS key 0               # 重新读 pending
XACK key group id [id ...]                   # 确认消息
XPENDING key group [start end count] [consumer]            # 待确认消息
XCLAIM key group consumer min-idle-time id [id ...]        # 转移消息
XAUTOCLAIM key group consumer min-idle-time start [count]  # 自动批量转移
XINFO STREAM key                              # Stream 信息
XINFO GROUPS key                              # 所有消费组
XINFO CONSUMERS key group                     # 组内消费者
XTRIM key MAXLEN|MINID [=|~] threshold        # 裁剪
XDEL key id [id ...]                          # 删除消息
```

---

## 常见问题

### Q1：SUBSCRIBE 后无法执行其他命令？

SUBSCRIBE/PSUBSCRIBE 会让客户端进入**订阅模式**，只能接收消息，不能执行其他命令。需要开新终端或在订阅终端按 `Ctrl+C` 退出订阅模式。

### Q2：为什么 PUBLISH 返回 0？

返回值是"收到该消息的订阅者数量"。返回 0 表示没有订阅者，消息已丢失。Pub/Sub 不存储消息。

### Q3：Stream 消费者崩溃后消息会丢吗？

不会。消费者用 XREADGROUP 拉取的消息会进入 pending 列表，必须 XACK 才算处理完成。崩溃后消息保留在 pending，可用 XCLAIM/XAUTOCLAIM 转移给其他消费者重新处理。

### Q4：XREADGROUP 的 `>` 和 `0` 有什么区别？

- `>`：消费组**未投递过的新消息**（首次投递给该消费者）
- `0`：重新读取**该消费者自己 pending 列表**中的消息（用于重试）

### Q5：Stream 会无限增长吗？

会。Stream 默认不自动裁剪，需要用 `XTRIM` 或在 `XADD` 时带 `MAXLEN`/`MINID` 控制。生产环境推荐 `XADD stream MAXLEN ~ 10000 * field value`。

### Q6：Pub/Sub 和 Stream 怎么选？

- 需要**实时广播**、容忍丢消息、无需回溯 → Pub/Sub
- 需要**可靠投递**、消费确认、消费组、消息回溯 → Stream
- 复杂场景可混合：Stream 持久化 + Pub/Sub 实时推送

---

## 清理演示数据

演示完成后清理：

```redis
DEL stream:orders
UNSUBSCRIBE
PUNSUBSCRIBE
```

> Pub/Sub 频道无需 DEL（不存储数据）。订阅者退出后频道自动消失。
