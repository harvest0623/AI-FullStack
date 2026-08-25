# 集群 Cluster 搭建指南

> 本指南用 Docker 搭建 **6 节点 3 主 3 从** 的 Redis Cluster 最小集群，演示分片、MOVED 重定向、扩缩容、故障转移。

---

## 一、架构与端口规划

```
                Redis Cluster (3 主 3 从)
   ┌────────────────────────────────────────────────────┐
   │                                                    │
   │  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
   │  │ Master A │    │ Master B │    │ Master C │      │
   │  │ :7000    │    │ :7001    │    │ :7002    │      │
   │  │ 槽 0-5460│    │槽5461-10922│  │槽10923-16383│    │
   │  └────┬─────┘    └────┬─────┘    └────┬─────┘      │
   │       │复制          │复制          │复制          │
   │  ┌────┴─────┐    ┌────┴─────┐    ┌────┴─────┐      │
   │  │ Slave A' │    │ Slave B' │    │ Slave C' │      │
   │  │ :7003    │    │ :7004    │    │ :7005    │      │
   │  └──────────┘    └──────────┘    └──────────┘      │
   │                                                    │
   │  Gossip 协议：节点间通过 端口+10000 的集群总线通信    │
   └────────────────────────────────────────────────────┘
```

| 节点 | 容器名 | 客户端端口 | 集群总线端口 | 角色 |
|------|--------|----------|------------|------|
| Node 1 | redis-node1 | 7000 | 17000 | Master A |
| Node 2 | redis-node2 | 7001 | 17001 | Master B |
| Node 3 | redis-node3 | 7002 | 17002 | Master C |
| Node 4 | redis-node4 | 7003 | 17003 | Slave A' |
| Node 5 | redis-node5 | 7004 | 17004 | Slave B' |
| Node 6 | redis-node6 | 7005 | 17005 | Slave C' |

> **关键**：每个节点需开放两个端口——客户端端口（如 7000）和集群总线端口（7000+10000=17000）。

---

## 二、环境准备

### 2.1 创建网络与目录

```bash
docker network create redis-cluster

mkdir -p /tmp/redis-cluster/{node1,node2,node3,node4,node5,node6}
```

### 2.2 通用配置模板

每个节点的 `redis.conf` 仅端口不同：

```bash
# Node1
cat > /tmp/redis-cluster/node1/redis.conf <<'EOF'
port 7000
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
appendfsync everysec
EOF

# Node2 ~ Node6 同理，port 依次为 7001 ~ 7005
for i in 2 3 4 5 6; do
  port=$((6999 + i))
  cat > /tmp/redis-cluster/node$i/redis.conf <<EOF
port $port
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
appendfsync everysec
EOF
done
```

**配置说明**：

| 参数 | 值 | 含义 |
|------|-----|------|
| `cluster-enabled yes` | — | 开启集群模式（必需） |
| `cluster-config-file nodes.conf` | — | 集群拓扑持久化文件（节点自动维护） |
| `cluster-node-timeout 5000` | 5 秒 | 节点失联超时（判定 PFAIL） |

---

## 三、启动 6 个节点

### 3.1 启动脚本

```bash
for i in 1 2 3 4 5 6; do
  port=$((6999 + i))
  bus_port=$((16999 + i))
  docker run -d --name redis-node$i \
    --network redis-cluster \
    --network-alias redis-node$i \
    -p $port:$port \
    -p $bus_port:$bus_port \
    -v /tmp/redis-cluster/node$i/redis.conf:/etc/redis/redis.conf \
    -v /tmp/redis-cluster/node$i:/data \
    redis:7 redis-server /etc/redis/redis.conf
done

sleep 3
```

### 3.2 验证节点启动

```bash
docker logs redis-node1 | tail -5
# 期望看到：Running mode=cluster, cluster enabled

# 单独连一个节点，此时还未加入集群
redis-cli -p 7000 CLUSTER INFO
# cluster_state:fail （尚未组建集群）
```

---

## 四、创建集群

### 4.1 用 redis-cli 一键创建

```bash
# 创建 3 主 3 从的集群，--cluster-replicas 1 表示每个主配 1 个从
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
  --cluster-replicas 1

# 交互提示输入 yes 确认槽位分配
```

### 4.2 验证集群状态

```bash
# 集群信息
redis-cli -p 7000 CLUSTER INFO
```

期望输出：
```
cluster_state:ok
cluster_slots_assigned:16384
cluster_slots_ok:16384
cluster_known_nodes:6
cluster_size:3
```

### 4.3 查看节点与槽位分配

```bash
redis-cli -p 7000 CLUSTER NODES
```

期望输出（精简）：
```
<id1> ... myself,master - 0 ... 0-5460 [slave-id4]
<id2> ... master       - 0 ... 5461-10922 [slave-id5]
<id3> ... master       - 0 ... 10923-16383 [slave-id6]
<id4> ... slave        <id1> 0 ...
<id5> ... slave        <id2> 0 ...
<id6> ... slave        <id3> 0 ...
```

```bash
# 用 redis-cli --cluster 查看更直观
redis-cli --cluster check 127.0.0.1:7000

# 查看槽位分布
redis-cli -p 7000 CLUSTER SLOTS
```

---

## 五、Cluster 基本操作

### 5.1 读写数据（自动路由）

```bash
# 必须加 -c 启用集群模式（自动跟随 MOVED 重定向）
redis-cli -c -p 7000 SET stock:product:1001 50
# OK（可能内部发生了 MOVED 重定向）

redis-cli -c -p 7000 GET stock:product:1001
# "50"

# 不加 -c 时会看到 MOVED 错误
redis-cli -p 7000 SET stock:product:1001 50
# (error) MOVED 5798 127.0.0.1:700X
```

### 5.2 观察槽位归属

```bash
# 计算某个 key 的槽位
redis-cli -p 7000 CLUSTER KEYSLOT stock:product:1001
# 返回槽位号，例如 5798

# 查询该槽位归属哪个节点
redis-cli -p 7000 CLUSTER SLOTS | grep -A 5 5798
```

### 5.3 MOVED 重定向演示

```bash
# 故意连错节点
redis-cli -p 7000 SET stock:product:1001 50
# (error) MOVED <slot> 127.0.0.1:700X
# 客户端应缓存此映射，下次直连正确节点

# 查看哪些 key 在哪个节点
for port in 7000 7001 7002; do
  echo "=== 节点 $port ==="
  redis-cli -p $port DBSIZE
done
```

### 5.4 批量写入测试分片

```bash
# 写入 1000 个 key，观察分布
for i in $(seq 1 1000); do
  redis-cli -c -p 7000 SET "test:k$i" "v$i" > /dev/null
done

# 各节点 key 数量
for port in 7000 7001 7002; do
  echo "Master $port: $(redis-cli -p $port DBSIZE) keys"
done
# 期望：三个主节点大致均匀分布（各约 333 个）
```

---

## 六、Hash Tag 演示

让相关 key 落在同一槽位，便于事务/多键操作：

```bash
# 计算不同 hash tag 的槽位
redis-cli -p 7000 CLUSTER KEYSLOT "{user:1001}:cart"
redis-cli -p 7000 CLUSTER KEYSLOT "{user:1001}:orders"
redis-cli -p 7000 CLUSTER KEYSLOT "{user:1001}:profile"
# 三者返回相同的槽位号！

# 写入数据
redis-cli -c -p 7000 SET "{user:1001}:cart" "product:1001,2"
redis-cli -c -p 7000 SET "{user:1001}:orders" "order:5001"
redis-cli -c -p 7000 SET "{user:1001}:profile" "alice"

# 可在同节点执行 MGET（多键操作需同槽位）
redis-cli -c -p 7000 MGET "{user:1001}:cart" "{user:1001}:orders" "{user:1001}:profile"
# 1) "product:1001,2"
# 2) "order:5001"
# 3) "alice"

# 不加 hash tag 的 key 槽位不同，MGET 会失败
redis-cli -c -p 7000 MGET user:1001:cart user:2002:cart
# (error) CROSSSLOT Keys in request don't hash to the same slot
```

---

## 七、集群扩容

### 7.1 启动新节点（Node7、Node8）

```bash
mkdir -p /tmp/redis-cluster/{node7,node8}

for i in 7 8; do
  port=$((6999 + i))
  bus_port=$((16999 + i))
  cat > /tmp/redis-cluster/node$i/redis.conf <<EOF
port $port
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
appendfsync everysec
EOF
  docker run -d --name redis-node$i \
    --network redis-cluster \
    --network-alias redis-node$i \
    -p $port:$port \
    -p $bus_port:$bus_port \
    -v /tmp/redis-cluster/node$i/redis.conf:/etc/redis/redis.conf \
    -v /tmp/redis-cluster/node$i:/data \
    redis:7 redis-server /etc/redis/redis.conf
done

sleep 3
```

### 7.2 加入集群

```bash
# 把 Node7 加入集群（成为新主，但暂未分配槽位）
redis-cli --cluster add-node 127.0.0.1:7006 127.0.0.1:7000

# 把 Node8 作为 Node7 的从节点加入
NODE7_ID=$(redis-cli -p 7000 CLUSTER NODES | grep "redis-node7" | awk '{print $1}' | head -1)
redis-cli --cluster add-node 127.0.0.1:7007 127.0.0.1:7000 --cluster-slave --cluster-master-id $NODE7_ID
```

### 7.3 分配槽位（Reshard）

```bash
# 从现有 3 个主各迁移一部分槽位到 Node7
redis-cli --cluster reshard 127.0.0.1:7000 \
  --cluster-from all \
  --cluster-to $NODE7_ID \
  --cluster-slots 1000 \
  --cluster-yes

# 验证槽位已迁移
redis-cli --cluster check 127.0.0.1:7000
# 期望：Node7 持有约 1000 个槽位
```

---

## 八、集群缩容

### 8.1 迁移槽位回其他节点

```bash
# 假设要移除 Node7（id 已知）
# 先把它的槽位迁移到其他节点
redis-cli --cluster reshard 127.0.0.1:7000 \
  --cluster-from $NODE7_ID \
  --cluster-to <target_master_id> \
  --cluster-slots 1000 \
  --cluster-yes
```

### 8.2 移除节点

```bash
# 先删除从节点 Node8
NODE8_ID=$(redis-cli -p 7000 CLUSTER NODES | grep "redis-node8" | awk '{print $1}' | head -1)
redis-cli --cluster del-node 127.0.0.1:7000 $NODE8_ID

# 再删除主节点 Node7（必须先迁移完所有槽位）
redis-cli --cluster del-node 127.0.0.1:7000 $NODE7_ID

# 验证
redis-cli --cluster check 127.0.0.1:7000
# 期望：回到 3 主 3 从
```

---

## 九、故障转移测试

### 9.1 模拟主节点宕机

```bash
# 查看当前各主节点 ID 与从节点
redis-cli -p 7000 CLUSTER NODES

# 停掉 Master A（端口 7000）
docker stop redis-node1

# 等待故障检测（cluster-node-timeout 5 秒 + 转移时间）
sleep 30
```

### 9.2 验证从节点升级为新主

```bash
# 查看集群状态（连任意存活节点）
redis-cli -p 7001 CLUSTER NODES
# 期望：原 redis-node1 的从节点（redis-node4）变成 master

# 集群仍可读写
redis-cli -c -p 7001 SET stock:product:2001 100
# OK

# 集群状态应为 ok
redis-cli -p 7001 CLUSTER INFO | grep cluster_state
# cluster_state:ok
```

### 9.3 恢复原主

```bash
# 启动原主节点
docker start redis-node1
sleep 5

# 原主变成从节点
redis-cli -p 7001 CLUSTER NODES | grep redis-node1
# 期望：role=slave，master 指向 redis-node4
```

---

## 十、Cluster 命令速查

| 命令 | 作用 |
|------|------|
| `CLUSTER INFO` | 集群整体状态 |
| `CLUSTER NODES` | 所有节点信息（含主从、槽位） |
| `CLUSTER SLOTS` | 槽位与节点映射 |
| `CLUSTER COUNTKEYSINSLOT <slot>` | 某槽位的 key 数量 |
| `CLUSTER KEYSLOT <key>` | 计算 key 所属槽位 |
| `CLUSTER MEET <ip> <port>` | 把节点加入集群 |
| `CLUSTER FORGET <node_id>` | 从集群移除节点 |
| `CLUSTER REPLICATE <node_id>` | 把当前节点设为指定主节点的从 |
| `CLUSTER FAILOVER` | 手动触发从节点升级为主（需在从节点执行） |
| `CLUSTER RESET HARD` | 重置集群状态（危险，仅调试用） |

### redis-cli --cluster 子命令

```bash
redis-cli --cluster create ...        # 创建集群
redis-cli --cluster check <host:port> # 检查集群
redis-cli --cluster info <host:port>  # 集群信息
redis-cli --cluster fix <host:port>   # 修复集群
redis-cli --cluster reshard <host:port> # 槽位迁移
redis-cli --cluster rebalance <host:port> # 均衡槽位
redis-cli --cluster add-node ...     # 加入节点
redis-cli --cluster del-node ...      # 移除节点
redis-cli --cluster call <host:port> <cmd> # 在所有节点执行命令
```

### 在 redis-cli 中执行的查询脚本

连接任意集群节点（带 -c 集群模式）后：

```redis
-- 集群状态
CLUSTER INFO

-- 节点列表
CLUSTER NODES

-- 槽位分布
CLUSTER SLOTS

-- 计算 key 的槽位
CLUSTER KEYSLOT stock:product:1001

-- 查询槽位 key 数量
CLUSTER COUNTKEYSINSLOT 5798

-- 当前节点角色
ROLE
```

---

## 十一、清理环境

```bash
# 停止并删除所有节点
for i in 1 2 3 4 5 6 7 8; do
  docker stop redis-node$i 2>/dev/null
  docker rm redis-node$i 2>/dev/null
done

docker network rm redis-cluster
rm -rf /tmp/redis-cluster
```

---

## 十二、客户端连接

### 12.1 命令行

```bash
# 必须加 -c 启用集群模式（自动跟随 MOVED/ASK）
redis-cli -c -p 7000

# 批量操作
redis-cli -c -p 7000 -h 127.0.0.1 --pipe < data.txt
```

### 12.2 Python（redis-py）

```python
from redis.cluster import RedisCluster

rc = RedisCluster(host='127.0.0.1', port=7000)

# 自动路由到正确节点
rc.set('stock:product:1001', '50')
print(rc.get('stock:product:1001'))
```

### 12.3 Node.js（ioredis）

```javascript
const Redis = require('ioredis');

const cluster = new Redis.Cluster([
  { host: '127.0.0.1', port: 7000 },
  { host: '127.0.0.1', port: 7001 },
  { host: '127.0.0.1', port: 7002 },
]);

await cluster.set('stock:product:1001', '50');
console.log(await cluster.get('stock:product:1001'));
```

---

## 十三、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `[ERR] Node 127.0.0.1:7000 is not empty` | 节点已有数据 | 用全新数据目录，或 `FLUSHALL` + `CLUSTER RESET HARD` |
| 集群状态 `cluster_state:fail` | 槽位未全部分配或多数主节点挂掉 | `redis-cli --cluster fix` 修复 |
| `CROSSSLOT` 错误 | 多键操作不在同槽位 | 用 hash tag `{}` 包裹 |
| 节点加入后 `cluster_known_nodes` 不变 | 集群总线端口未开放 | 确认 `port+10000` 也已映射 |
| `CLUSTER FAILOVER` 报错 | 在主节点上执行 | 必须在从节点执行 |
| 客户端不识别 MOVED | 未用集群客户端 | 用 `redis-cli -c` 或支持集群的客户端库 |

> **生产部署要点**：至少 3 主 3 从（6 节点）；主从分布在不同物理机；`cluster-node-timeout` 建议 15-30 秒；客户端必须支持集群协议；大 key 避免用 `KEYS`，用 `SCAN` 分片遍历。
