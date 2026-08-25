# 主从复制搭建指南

> 本指南用 Docker 搭建一主一从的最小复制环境，演示全量同步、增量同步、读写分离。所有命令在 Windows PowerShell / Linux bash 下均可执行（注意换行符）。

---

## 一、环境准备

### 1.1 网络与目录

```bash
# 创建专用网络，让容器间用服务名通信
docker network create redis-repl

# 创建数据目录
mkdir -p /tmp/redis-repl/master /tmp/redis-repl/slave
```

### 1.2 主节点配置文件

```bash
cat > /tmp/redis-repl/master/redis.conf <<'EOF'
port 6379
bind 0.0.0.0
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
# 关键：从节点连接时需要密码则配置 requirepass，本演示不设密码
EOF
```

### 1.3 从节点配置文件

```bash
cat > /tmp/redis-repl/slave/redis.conf <<'EOF'
port 6380
bind 0.0.0.0
replicaof redis-master 6379
replica-read-only yes
appendonly yes
appendfsync everysec
EOF
```

---

## 二、启动主从

### 2.1 启动主节点

```bash
docker run -d --name redis-master \
  --network redis-repl \
  --network-alias redis-master \
  -p 6379:6379 \
  -v /tmp/redis-repl/master/redis.conf:/etc/redis/redis.conf \
  -v /tmp/redis-repl/master:/data \
  redis:7 redis-server /etc/redis/redis.conf
```

### 2.2 启动从节点

```bash
docker run -d --name redis-slave \
  --network redis-repl \
  --network-alias redis-slave \
  -p 6380:6380 \
  -v /tmp/redis-repl/slave/redis.conf:/etc/redis/redis.conf \
  -v /tmp/redis-repl/slave:/data \
  redis:7 redis-server /etc/redis/redis.conf
```

> 关键点：`--network-alias redis-master` 让从节点配置里的 `replicaof redis-master 6379` 能解析到主节点容器。

### 2.3 验证启动状态

```bash
# 查看主节点日志，确认 RDB/AOF 加载完成
docker logs redis-master | tail -20

# 查看从节点日志，确认已连接主节点
docker logs redis-slave | tail -20
```

期望看到从节点日志中类似：
```
* MASTER <-> REPLICA sync started
* MASTER <-> REPLICA sync: Finished with success
```

---

## 三、验证复制

### 3.1 查看复制状态

```bash
# 主节点复制信息
redis-cli -p 6379 INFO replication
```

期望输出关键字段：
```
role:master
connected_slaves:1
slave0:ip=172.x.x.x,port=6380,state=online,offset=XXX,lag=0
master_replid:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
master_repl_offset:XXX
```

```bash
# 从节点复制信息
redis-cli -p 6380 INFO replication
```

期望输出：
```
role:slave
master_host:redis-master
master_port:6379
master_link_status:up
slave_repl_offset:XXX
```

### 3.2 全量同步验证

```bash
# 1. 在主节点写入数据
redis-cli -p 6379 SET stock:product:1001 50
redis-cli -p 6379 SET stock:product:1002 30
redis-cli -p 6379 HSET cart:user:1001 product:1001 2 product:1002 1
redis-cli -p 6379 ZADD leaderboard:sales 50 product:1001 30 product:1002

# 2. 在从节点读取，验证数据已同步
redis-cli -p 6380 GET stock:product:1001
# 期望：50

redis-cli -p 6380 HGETALL cart:user:1001
# 期望：product:1001 / 2 / product:1002 / 1

redis-cli -p 6380 ZRANGE leaderboard:sales 0 -1 WITHSCORES
# 期望：product:1002 / 30 / product:1001 / 50
```

### 3.3 增量同步验证

```bash
# 1. 记录当前 offset
redis-cli -p 6379 INFO replication | grep master_repl_offset
# 假设输出：master_repl_offset:1000

# 2. 写入新数据
redis-cli -p 6379 INCR stock:product:1001
redis-cli -p 6379 INCR stock:product:1001

# 3. offset 应增长
redis-cli -p 6379 INFO replication | grep master_repl_offset
# 期望：master_repl_offset:10XX（比之前大）

# 4. 从节点能立即读到新值
redis-cli -p 6380 GET stock:product:1001
# 期望：52
```

### 3.4 断线重连增量同步

```bash
# 1. 暂停从节点
docker stop redis-slave

# 2. 在主节点写入若干数据
redis-cli -p 6379 INCR stock:product:1001
redis-cli -p 6379 INCR stock:product:1001
redis-cli -p 6379 INCR stock:product:1001

# 3. 重启从节点
docker start redis-slave
sleep 3

# 4. 验证断线期间的命令已增量同步
redis-cli -p 6380 GET stock:product:1001
# 期望：包含断线期间的 3 次 INCR

# 5. 查看日志，应看到 +CONTINUE（增量同步）
docker logs redis-slave --tail 10 | grep -i "sync\|continue"
```

> 若断线时间过长（超出 `repl-backlog-size` 默认 1MB 的范围），会触发全量同步而非增量。可在日志中观察是否出现 `FULLRESYNC`。

---

## 四、读写分离测试

### 4.1 从节点只读验证

```bash
# 从节点写入应被拒绝
redis-cli -p 6380 SET stock:product:9999 1
# 期望：(error) READONLY You can't write against a read only replica.
```

### 4.2 读写分离模式

```
写请求 → 主节点 (6379) → 异步复制 → 从节点 (6380) ← 读请求
```

```bash
# 应用层伪代码（伪代码，仅示意）
# writeClient = redis.Redis(host='master', port=6379)
# readClient  = redis.Redis(host='slave',  port=6380)
#
# writeClient.set('stock:product:1001', 50)
# data = readClient.get('stock:product:1001')
```

### 4.3 主从延迟观察

```bash
# 1. 主节点连续写
for i in $(seq 1 100); do redis-cli -p 6379 INCR counter:delay; done

# 2. 立即在从节点读，可能略小于 100
redis-cli -p 6380 GET counter:delay

# 3. 稍等后再读，应等于 100
sleep 1
redis-cli -p 6380 GET counter:delay
```

> **结论**：异步复制有毫秒~秒级延迟，强一致读必须走主节点。

---

## 五、关键命令速查

| 命令 | 作用 |
|------|------|
| `REPLICAOF host port` | 设为从节点 |
| `REPLICAOF NO ONE` | 取消从节点身份 |
| `INFO replication` | 查看复制状态 |
| `CONFIG GET repl-backlog-size` | 查看复制缓冲区大小 |
| `CONFIG SET repl-backlog-size 32mb` | 调大缓冲区（断线更不易全量） |

### 在 redis-cli 中执行的查询脚本

连接主节点后可执行以下命令查看状态：

```redis
-- 主节点复制状态
INFO replication

-- 复制缓冲区配置
CONFIG GET repl-backlog-size
CONFIG GET repl-backlog-ttl
CONFIG GET replica-priority

-- 主节点角色
ROLE
```

连接从节点后：

```redis
-- 从节点复制状态
INFO replication

-- 从节点角色
ROLE

-- 主从延迟（slave_repl_offset 与 master_repl_offset 的差值）
INFO replication
```

---

## 六、清理环境

```bash
docker stop redis-master redis-slave
docker rm redis-master redis-slave
docker network rm redis-repl
rm -rf /tmp/redis-repl
```

---

## 七、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 从节点日志 `master_link_status:down` | 网络不通或主节点密码错 | 检查网络、`masterauth` 配置 |
| 频繁全量同步 | `repl-backlog-size` 太小 | 调大到 32MB+ |
| 主从延迟大 | 主节点写入压力大、网络拥塞 | 加从节点分担读、检查网络 |
| 从节点 `replica-read-only` 关闭 | 配置错误 | 确认 `replica-read-only yes` |
| `REPLICAOF` 命令报错 | 版本 < 5.0 | 改用 `SLAVEOF` |
