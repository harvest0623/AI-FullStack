# 持久化策略指南

> 本文是 Day09 的配套指南，提供 RDB / AOF / 混合持久化三种方案的选型决策树、生产环境配置模板、备份恢复操作流程与灾难恢复演练步骤。

---

## 一、选型决策树

```
                       你的业务能容忍丢失多少数据？
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
   完全可重建                最多 1 秒                  不能丢
   （纯缓存）              （一般数据库）            （金融级）
        │                       │                       │
        ▼                       ▼                       ▼
   关闭持久化          AOF everysec +           AOF always +
   save ""              RDB 备份 +               主从复制 +
   appendonly no        混合持久化               异地容灾
                        │                       │
                        ▼                       ▼
                  推荐配置 A                 推荐配置 C
                                              │
                                              ▼
                                        性能损耗大，
                                        仅关键数据使用

   ┌─────────────────────────────────────────────────┐
   │  推荐配置 A（绝大多数业务）                        │
   │  appendonly yes                                  │
   │  appendfsync everysec                            │
   │  aof-use-rdb-preamble yes                        │
   │  save 900 1                                     │
   │  save 300 10                                    │
   │  save 60 10000                                  │
   └─────────────────────────────────────────────────┘
```

### 三种方案对照

| 方案 | 配置 | 数据丢失窗口 | 恢复速度 | 适用场景 |
|------|------|-------------|---------|---------|
| **纯 RDB** | `save 900 1` 等 + `appendonly no` | 大（分钟级） | 最快 | 备份、纯缓存 |
| **纯 AOF** | `appendonly yes` + `aof-use-rdb-preamble no` | 小（秒级） | 较慢 | 兼容旧版本 |
| **混合** | `appendonly yes` + `aof-use-rdb-preamble yes` | 小（秒级） | 快 | **生产首选** |

---

## 二、生产环境配置模板

### 2.1 通用业务（推荐）

`redis.conf` 关键片段：

```conf
# ===== RDB 配置 =====
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data/redis

# ===== AOF 配置 =====
appendonly yes
appendfilename "appendonly.aof"
appenddirname "appendonlydir"
appendfsync everysec
no-appendfsync-on-rewrite no

# ===== 混合持久化 =====
aof-use-rdb-preamble yes

# ===== 自动重写 =====
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# ===== 内存上限（防 COW 翻倍） =====
maxmemory 4gb
maxmemory-policy noeviction
```

### 2.2 纯缓存场景（追求性能）

```conf
save ""
appendonly no
# 关闭持久化，重启从 MySQL 重建
```

### 2.3 关键数据场景（金融级）

```conf
appendonly yes
appendfsync always        # 每条命令刷盘，最安全
aof-use-rdb-preamble yes
save 900 1                 # 同时保留 RDB 作为冷备

# 主从复制 + Sentinel 见 Day10
# 异地容灾：定时把 dump.rdb 同步到对象存储
```

---

## 三、备份恢复操作流程

### 3.1 RDB 备份与恢复

#### 在线备份（不停服）

```bash
# 1. 触发 BGSAVE（异步，不影响服务）
redis-cli -h <host> -p <port> -a <password> BGSAVE

# 2. 轮询等待完成
while [ "$(redis-cli -a <password> INFO persistence | grep rdb_bgsave_in_progress | awk -F: '{print $2}' | tr -d '\r')" != "0" ]; do
  sleep 1
done

# 3. 获取 RDB 文件路径
REDIS_DIR=$(redis-cli -a <password> CONFIG GET dir | tail -1)
RDB_FILE=$(redis-cli -a <password> CONFIG GET dbfilename | tail -1)

# 4. 复制到备份目录（用 cp 而非 mv，保留原文件）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp "$REDIS_DIR/$RDB_FILE" "/backup/redis/dump_${TIMESTAMP}.rdb"

# 5. 同步到对象存储（可选）
# aws s3 cp /backup/redis/dump_${TIMESTAMP}.rdb s3://your-bucket/redis-backup/
```

#### 恢复流程

```bash
# 1. 停止 Redis
redis-cli shutdown nosave

# 2. 替换 RDB 文件
cp /backup/redis/dump_20260728_120000.rdb /data/redis/dump.rdb

# 3. 启动 Redis（自动加载 dump.rdb）
redis-server /etc/redis/redis.conf

# 4. 验证数据
redis-cli DBSIZE
redis-cli GET stock:product:1001
```

### 3.2 AOF 备份与恢复

#### 在线备份

```bash
# 1. 触发 BGREWRITEAOF，生成紧凑文件
redis-cli BGREWRITEAOF

# 2. 等待重写完成
while [ "$(redis-cli INFO persistence | grep aof_rewrite_in_progress | awk -F: '{print $2}' | tr -d '\r')" != "0" ]; do
  sleep 1
done

# 3. 复制 AOF 目录（7.0+ 为 appendonlydir）
cp -r /data/redis/appendonlydir /backup/redis/aof_$(date +%Y%m%d_%H%M%S)
```

#### 恢复流程

```bash
# 1. 停止 Redis
redis-cli shutdown nosave

# 2. 替换 AOF 目录
rm -rf /data/redis/appendonlydir
cp -r /backup/redis/aof_20260728_120000 /data/redis/appendonlydir

# 3. 启动 Redis（自动加载 AOF）
redis-server /etc/redis/redis.conf
```

### 3.3 AOF 文件损坏修复

若 AOF 文件末尾被截断（断电场景），Redis 拒绝启动：

```
Bad file format reading the append only file: \
  make a backup of your AOF file, then use ./redis-check-aof --fix <file>
```

修复命令：

```bash
# 1. 先备份损坏的文件
cp appendonly.aof appendonly.aof.bak

# 2. 用工具修复（会截断末尾不完整的命令）
redis-check-aof --fix appendonly.aof

# 3. RDB 文件损坏用 redis-check-rdb
redis-check-rdb dump.rdb
```

---

## 四、灾难恢复演练步骤

### 演练目标

验证持久化配置是否生效，模拟"写入 → 故障 → 恢复"全流程，确保 RTO（恢复时间目标）与 RPO（恢复点目标）达标。

### 演练脚本（Docker 环境）

```bash
# ============================================================
# 步骤 1：准备环境
# ============================================================
docker run -d --name redis-drill \
  -p 6379:6379 \
  -v /tmp/redis-drill:/data \
  redis:7 \
  redis-server --appendonly yes --appendfsync everysec --save 60 1

# ============================================================
# 步骤 2：写入测试数据
# ============================================================
redis-cli SET stock:product:drill1 100
redis-cli SET stock:product:drill2 200
redis-cli HSET cart:user:drill product:1001 2
redis-cli ZADD leaderboard:drill 100 product:1001 200 product:1002

# 验证数据
redis-cli DBSIZE
# 期望：4

# ============================================================
# 步骤 3：触发持久化
# ============================================================
redis-cli BGSAVE
redis-cli BGREWRITEAOF

# 等待完成
sleep 3

# 查看持久化文件
ls -lh /tmp/redis-drill/
ls -lh /tmp/redis-drill/appendonlydir/

# ============================================================
# 步骤 4：备份持久化文件
# ============================================================
mkdir -p /tmp/redis-backup
cp /tmp/redis-drill/dump.rdb /tmp/redis-backup/dump_$(date +%s).rdb
cp -r /tmp/redis-drill/appendonlydir /tmp/redis-backup/

# ============================================================
# 步骤 5：模拟故障（强制杀进程，模拟断电）
# ============================================================
docker kill redis-drill
docker rm redis-drill

# ============================================================
# 步骤 6：用备份恢复（仅用 RDB 演练）
# ============================================================
# 删除原始数据目录模拟彻底损坏
rm -rf /tmp/redis-drill

# 重新创建目录并恢复 RDB
mkdir -p /tmp/redis-drill
cp /tmp/redis-backup/dump_*.rdb /tmp/redis-drill/dump.rdb

# 用只加载 RDB 的配置启动（关闭 AOF）
docker run -d --name redis-restore \
  -p 6379:6379 \
  -v /tmp/redis-drill:/data \
  redis:7 \
  redis-server --appendonly no --dbfilename dump.rdb

sleep 2

# ============================================================
# 步骤 7：验证恢复结果
# ============================================================
echo "=== 验证恢复数据 ==="
redis-cli DBSIZE
redis-cli GET stock:product:drill1
redis-cli GET stock:product:drill2
redis-cli HGETALL cart:user:drill
redis-cli ZRANGE leaderboard:drill 0 -1 WITHSCORES

# 期望输出：
# (integer) 4
# "100"
# "200"
# 1) "product:1001"
# 2) "2"
# 1) "product:1002"
# 2) "200"
# 3) "product:1001"
# 4) "100"

# ============================================================
# 步骤 8：清理
# ============================================================
docker stop redis-restore
docker rm redis-restore
rm -rf /tmp/redis-drill /tmp/redis-backup
```

### 演练检查清单

| 检查项 | 期望结果 | 实际结果 |
|--------|---------|---------|
| BGSAVE 成功 | `rdb_last_bgsave_status:ok` | ☐ |
| BGREWRITEAOF 成功 | `aof_last_bgrewrite_status:ok` | ☐ |
| RDB 文件存在 | `dump.rdb` 在 dir 目录 | ☐ |
| AOF 目录存在 | `appendonlydir/` 存在 | ☐ |
| 强杀后数据可恢复 | 启动后 DBSIZE 一致 | ☐ |
| RTO 测量 | 恢复耗时 < 5 分钟 | ☐ |
| RPO 测量 | 数据丢失 < 1 秒（AOF everysec） | ☐ |

---

## 五、运维注意事项

### 5.1 大实例优化

- **fork 阻塞**：>10GB 实例的 fork 耗时可能 >100ms，影响响应延迟
  - 解决：使用支持 THPI（Transparent Huge Pages）的内核
  - 或分片：用 Cluster 拆成多个小实例
- **磁盘 IO**：AOF 持续追加 + RDB 间歇写入，可能成为瓶颈
  - 解决：持久化文件放独立 SSD
  - 调大 `auto-aof-rewrite-min-size`，减少重写频率

### 5.2 监控指标

| 指标 | 来源 | 健康值 | 告警阈值 |
|------|------|--------|---------|
| `latest_fork_usec` | INFO stats | < 100ms | > 1s |
| `rdb_last_bgsave_status` | INFO persistence | ok | err |
| `aof_last_bgrewrite_status` | INFO persistence | ok | err |
| `aof_pending_fsync` | INFO persistence | 0 | 持续 > 0 |
| 持久化文件大小 | 文件系统 | — | 突增告警 |
| 磁盘剩余空间 | 文件系统 | > 30% | < 20% |

### 5.3 常见故障

| 故障 | 现象 | 处理 |
|------|------|------|
| BGSAVE 失败 | `rdb_last_bgsave_status:err` | 检查磁盘空间、权限 |
| fork 失败 | `Can't save in background: fork: Cannot allocate memory` | 调大 `vm.overcommit_memory=1` |
| AOF 文件损坏 | 启动报 Bad file format | `redis-check-aof --fix` |
| 磁盘满 | 写入报 `MISCONF Redis is configured to save RDB...` | 清理磁盘或临时 `CONFIG SET stop-writes-on-bgsave-error no` |

---

## 六、选型建议总结

```
┌─────────────────────────────────────────────────────┐
│  选型口诀                                           │
│                                                     │
│  能丢就关持久化（纯缓存）                            │
│  一般业务 everysec（推荐）                          │
│  关键数据 always + 主从                             │
│  4.0+ 优先用混合（aof-use-rdb-preamble yes）       │
│  大实例注意 fork 与磁盘 IO                          │
│  定期演练灾难恢复，别等出事才发现备份是坏的          │
└─────────────────────────────────────────────────────┘
```
