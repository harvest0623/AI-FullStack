# 哨兵 Sentinel 搭建指南

> 本指南用 Docker 搭建 **1 主 2 从 3 哨兵** 的最小高可用环境，演示自动故障转移全过程。

---

## 一、架构与端口规划

```
┌─────────────────────────────────────────────────────────┐
│                      Sentinel 集群                       │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│   │Sentinel1 │  │Sentinel2 │  │Sentinel3 │              │
│   │ :26379   │  │ :26380   │  │ :26381   │              │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│        │             │             │  监控              │
│        └─────────────┼─────────────┘                   │
│                      │                                   │
└──────────────────────┼─────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐
   │  主节点  │◀──│ 从节点1  │    │ 从节点2  │
   │  :6379  │复制│  :6380  │    │  :6381  │
   └─────────┘    └─────────┘    └─────────┘
```

| 服务 | 容器名 | 端口 | 角色 |
|------|--------|------|------|
| Redis Master | redis-sentinel-master | 6379 | 主 |
| Redis Slave1 | redis-sentinel-slave1 | 6380 | 从 |
| Redis Slave2 | redis-sentinel-slave2 | 6381 | 从 |
| Sentinel1 | redis-sentinel1 | 26379 | 哨兵 |
| Sentinel2 | redis-sentinel2 | 26380 | 哨兵 |
| Sentinel3 | redis-sentinel3 | 26381 | 哨兵 |

---

## 二、环境准备

```bash
# 创建网络
docker network create redis-sentinel

# 创建配置与数据目录
mkdir -p /tmp/redis-sentinel/{master,slave1,slave2,sentinel1,sentinel2,sentinel3}
```

### 2.1 Redis 节点配置

```bash
# 主节点配置（含脑裂防护）
cat > /tmp/redis-sentinel/master/redis.conf <<'EOF'
port 6379
bind 0.0.0.0
appendonly yes
appendfsync everysec
min-replicas-to-write 1
min-replicas-max-lag 10
EOF

# 从节点 1 配置
cat > /tmp/redis-sentinel/slave1/redis.conf <<'EOF'
port 6380
bind 0.0.0.0
replicaof redis-master 6379
replica-read-only yes
replica-priority 100
appendonly yes
EOF

# 从节点 2 配置（优先级更高，故障转移时更可能被选为新主）
cat > /tmp/redis-sentinel/slave2/redis.conf <<'EOF'
port 6381
bind 0.0.0.0
replicaof redis-master 6379
replica-read-only yes
replica-priority 50
appendonly yes
EOF
```

### 2.2 Sentinel 配置

3 个哨兵配置相同，仅监听端口不同：

```bash
# Sentinel1
cat > /tmp/redis-sentinel/sentinel1/sentinel.conf <<'EOF'
port 26379
sentinel monitor mymaster redis-master 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 30000
EOF

# Sentinel2
cat > /tmp/redis-sentinel/sentinel2/sentinel.conf <<'EOF'
port 26380
sentinel monitor mymaster redis-master 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 30000
EOF

# Sentinel3
cat > /tmp/redis-sentinel/sentinel3/sentinel.conf <<'EOF'
port 26381
sentinel monitor mymaster redis-master 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 30000
EOF
```

**配置说明**：

| 参数 | 值 | 含义 |
|------|-----|------|
| `sentinel monitor mymaster redis-master 6379 2` | quorum=2 | 至少 2 个哨兵同意才判定 ODOWN |
| `sentinel down-after-milliseconds mymaster 5000` | 5 秒 | 5 秒未响应判定 SDOWN |
| `sentinel parallel-syncs mymaster 1` | 1 | 故障转移时同时同步新主的从节点数 |
| `sentinel failover-timeout mymaster 30000` | 30 秒 | 故障转移超时 |

---

## 三、启动集群

### 3.1 启动 Redis 主从

```bash
# 主节点
docker run -d --name redis-master \
  --network redis-sentinel \
  --network-alias redis-master \
  -p 6379:6379 \
  -v /tmp/redis-sentinel/master/redis.conf:/etc/redis/redis.conf \
  -v /tmp/redis-sentinel/master:/data \
  redis:7 redis-server /etc/redis/redis.conf

# 从节点 1
docker run -d --name redis-slave1 \
  --network redis-sentinel \
  -p 6380:6380 \
  -v /tmp/redis-sentinel/slave1/redis.conf:/etc/redis/redis.conf \
  -v /tmp/redis-sentinel/slave1:/data \
  redis:7 redis-server /etc/redis/redis.conf

# 从节点 2
docker run -d --name redis-slave2 \
  --network redis-sentinel \
  -p 6381:6381 \
  -v /tmp/redis-sentinel/slave2/redis.conf:/etc/redis/redis.conf \
  -v /tmp/redis-sentinel/slave2:/data \
  redis:7 redis-server /etc/redis/redis.conf

# 等待复制建立
sleep 5
```

### 3.2 验证主从状态

```bash
redis-cli -p 6379 INFO replication | grep -E "role|connected_slaves"
# 期望：role:master / connected_slaves:2
```

### 3.3 启动 3 个 Sentinel

```bash
docker run -d --name redis-sentinel1 \
  --network redis-sentinel \
  -p 26379:26379 \
  -v /tmp/redis-sentinel/sentinel1/sentinel.conf:/etc/redis/sentinel.conf \
  redis:7 redis-sentinel /etc/redis/sentinel.conf

docker run -d --name redis-sentinel2 \
  --network redis-sentinel \
  -p 26380:26380 \
  -v /tmp/redis-sentinel/sentinel2/sentinel.conf:/etc/redis/sentinel.conf \
  redis:7 redis-sentinel /etc/redis/sentinel.conf

docker run -d --name redis-sentinel3 \
  --network redis-sentinel \
  -p 26381:26381 \
  -v /tmp/redis-sentinel/sentinel3/sentinel.conf:/etc/redis/sentinel.conf \
  redis:7 redis-sentinel /etc/redis/sentinel.conf

sleep 5
```

### 3.4 查看 Sentinel 状态

```bash
# 连接任意 Sentinel 查看监控状态
redis-cli -p 26379 SENTINEL masters
# 输出主节点信息：name=mymaster, ip, port, num-slaves, num-other-sentinels

redis-cli -p 26379 SENTINEL sentinels mymaster
# 输出其他 Sentinel 节点

redis-cli -p 26379 SENTINEL replicas mymaster
# 输出从节点列表
```

期望看到 `num-other-sentinels=2`（共 3 个 Sentinel，互相发现）。

---

## 四、写入测试数据

```bash
redis-cli -p 6379 SET stock:product:1001 50
redis-cli -p 6379 SET stock:product:1002 30
redis-cli -p 6379 HSET cart:user:1001 product:1001 2

# 验证从节点已同步
redis-cli -p 6380 GET stock:product:1001   # 期望 50
redis-cli -p 6381 GET stock:product:1001   # 期望 50
```

---

## 五、模拟主节点故障，观察自动转移

### 5.1 强制停止主节点

```bash
# 记录当前主节点地址
redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster
# 期望输出：redis-master 6379

# 强杀主节点（模拟宕机）
docker stop redis-master
```

### 5.2 观察故障转移过程

```bash
# 实时查看 Sentinel1 日志
docker logs -f redis-sentinel1
```

期望依次看到（5 秒 SDOWN + 2 个 Sentinel 同意 ODOWN + Raft 选举 + 选新主）：

```
+sdown master mymaster redis-master 6379
+odown master mymaster redis-master 6379 #quorum 2/2
+new-epoch 1
+vote-for-leader <sentinel_id>
+config-update-from sentinel ...
+switch-master mymaster redis-master 6379 <new_master_ip> <new_port>
```

> `down-after-milliseconds` 设为 5 秒，便于快速观察。生产建议 30 秒。

### 5.3 验证新主已选举

```bash
# 等待转移完成（约 10-20 秒）
sleep 20

# 查询 Sentinel 当前主节点地址
redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster
# 期望输出：redis-slave2 6381（因为 slave2 的 replica-priority=50 更低）

# 验证新主可写
redis-cli -p 6381 SET stock:product:1001 60
# 期望：OK

# 另一个从节点已切换复制源
redis-cli -p 6380 INFO replication | grep master_host
# 期望：master_host:redis-slave2
```

### 5.4 验证脑裂防护

主节点配置了 `min-replicas-to-write 1`，强杀后即使旧主被网络分区，也无法写入（没有从节点在线）：

```bash
# 尝试启动旧主并写入（模拟脑裂）
docker start redis-master
sleep 3

# 旧主此时已变成从节点（Sentinel 通知它 REPLICAOF 新主）
redis-cli -p 6379 INFO replication | grep role
# 期望：role:slave
```

---

## 六、客户端连接 Sentinel

应用不应直连 Redis，而是通过 Sentinel 获取主地址：

### 6.1 命令行查询

```bash
# 获取当前主节点
redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster
# 返回 [host, port]
```

### 6.2 Python 客户端示例（redis-py）

```python
from redis.sentinel import Sentinel

sentinel = Sentinel([
    ('127.0.0.1', 26379),
    ('127.0.0.1', 26380),
    ('127.0.0.1', 26381),
])

# 自动获取主节点
master = sentinel.master_for('mymaster', socket_timeout=0.5)
slave = sentinel.slave_for('mymaster', socket_timeout=0.5)

# 写主
master.set('stock:product:2001', '100')
# 读从
print(slave.get('stock:product:2001'))

# 故障转移后，客户端会自动发现新主并切换
```

### 6.3 Node.js 客户端示例（ioredis）

```javascript
const Redis = require('ioredis');

const sentinel = new Redis({
  sentinels: [
    { host: '127.0.0.1', port: 26379 },
    { host: '127.0.0.1', port: 26380 },
    { host: '127.0.0.1', port: 26381 },
  ],
  name: 'mymaster',
  // 故障转移后自动重连新主
});
```

---

## 七、Sentinel 命令速查

| 命令 | 作用 |
|------|------|
| `SENTINEL masters` | 列出所有监控的主节点 |
| `SENTINEL master <name>` | 查看指定主节点详情 |
| `SENTINEL replicas <name>` | 列出从节点 |
| `SENTINEL sentinels <name>` | 列出其他 Sentinel |
| `SENTINEL get-master-addr-by-name <name>` | 获取主节点地址 |
| `SENTINEL failover <name>` | 手动触发故障转移 |
| `SENTINEL reset <name>` | 重置该主节点状态（重新发现） |
| `SENTINEL flushconfig` | 把内存配置写回 sentinel.conf |

### 在 redis-cli 中执行的查询脚本

连接 Sentinel（端口 26379）后：

```redis
-- 查看所有监控的主节点
SENTINEL masters

-- 查看 mymaster 详情
SENTINEL master mymaster

-- 查看从节点
SENTINEL replicas mymaster

-- 查看其他哨兵
SENTINEL sentinels mymaster

-- 获取主节点地址
SENTINEL get-master-addr-by-name mymaster

-- 手动触发故障转移（慎用，会改变主从拓扑）
SENTINEL failover mymaster
```

---

## 八、清理环境

```bash
docker stop redis-master redis-slave1 redis-slave2 \
         redis-sentinel1 redis-sentinel2 redis-sentinel3
docker rm   redis-master redis-slave1 redis-slave2 \
         redis-sentinel1 redis-sentinel2 redis-sentinel3
docker network rm redis-sentinel
rm -rf /tmp/redis-sentinel
```

---

## 九、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Sentinel 互相发现失败 | 网络不通 | 确认在同一 `--network` |
| `num-other-sentinels=0` | Sentinel 间未通信 | 检查 `sentinel monitor` 配置的 IP 一致 |
| 故障转移不触发 | quorum 过高 | quorum 应 ≤ Sentinel 数量的一半 |
| 转移后客户端连不上旧主 | 客户端未感知 | 使用支持 Sentinel 的客户端库 |
| `+failover-abort-no-good-slave` | 没有合适的从节点 | 检查从节点 `replica-priority` 不为 0 |

> **生产部署要点**：Sentinel 至少 3 节点（奇数）；`down-after-milliseconds` 建议 30 秒避免误判；客户端必须支持 Sentinel 协议。
