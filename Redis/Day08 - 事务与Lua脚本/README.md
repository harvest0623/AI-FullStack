# Day08 - 事务与 Lua 脚本

Redis 单线程模型保证了单条命令的原子性，但实际业务往往需要"多条命令作为一个整体执行"。例如电商下单场景中，扣减库存、写订单、扣余额必须要么全部成功，要么全部不执行。Redis 通过 **事务（MULTI/EXEC）** 提供了基础的批处理原子性保证，又通过 **Lua 脚本** 提供了更强大的、能在脚本内做条件判断的原子性方案。本章将系统讲解 Redis 事务的 ACID 特性、WATCH 乐观锁原理，以及 Lua 脚本的开发模式与最佳实践，并用 Lua 实现一个完整的原子库存扣减脚本。

---

## 学习目标

- 掌握 `MULTI` / `EXEC` / `DISCARD` / `WATCH` / `UNWATCH` 五个事务命令的语义与用法
- 理解 Redis 事务的 ACID 特性，特别是"不支持回滚"的设计取舍
- 区分命令语法错误与运行时错误对事务的不同影响
- 能够用 WATCH 乐观锁解决并发扣减库存场景
- 掌握 `EVAL` / `EVALSHA` / `SCRIPT LOAD` / `SCRIPT FLUSH` 等 Lua 脚本命令
- 理解 Lua 脚本的原子性保证、`KEYS` 与 `ARGV` 的传参规范
- 能编写条件判断型 Lua 脚本（检查库存→扣减→返回结果）
- 知道何时该用事务、何时该用 Lua 脚本

---

## 理论知识讲解

### 一、Redis 事务

#### 1.1 事务的本质

Redis 事务是一组命令的有序集合，它保证：

- **命令按顺序执行**，不会被其他客户端插入打断
- **要么全部入队后一次性执行（EXEC），要么全部不执行（DISCARD 或 WATCH 失效）**

注意：Redis 事务**没有回滚机制**，与 MySQL 的事务在语义上有本质区别。

#### 1.2 核心命令

| 命令 | 作用 | 返回值 |
|------|------|--------|
| `MULTI` | 开启事务，后续命令进入队列不执行 | `OK` |
| `EXEC` | 执行队列中的所有命令 | 数组，每条命令的结果 |
| `DISCARD` | 取消事务，清空命令队列 | `OK` |
| `WATCH key [key ...]` | 乐观锁，监控一个或多个 key | `OK` |
| `UNWATCH` | 取消所有 key 的监控 | `OK` |

**基本流程**：

```
MULTI            # 开启事务，返回 OK
SET k1 v1        # 入队，返回 QUEUED
SET k2 v2        # 入队，返回 QUEUED
EXEC             # 执行所有入队命令，返回 [OK, OK]
```

#### 1.3 事务的 ACID 分析

| 特性 | 是否满足 | 说明 |
|------|---------|------|
| **原子性（Atomicity）** | 部分满足 | 命令要么全部执行、要么全部不执行，但**不支持回滚**：运行时错误不会影响其他命令 |
| **一致性（Consistency）** | 满足 | 事务前后数据始终一致，不会留下中间态（除非业务逻辑本身有 bug） |
| **隔离性（Isolation）** | 满足 | 单线程模型，事务执行期间不会被打断 |
| **持久性（Durability）** | 取决于配置 | 仅在 AOF + `appendfsync always` 时可保证；RDB 或 everysec 仍有丢失窗口 |

#### 1.4 命令错误 vs 运行时错误

这是 Redis 事务最容易踩坑的地方，两种错误处理方式完全不同：

**① 命令语法错误（入队前就发现）**：整个事务不会执行

```
MULTI
SET stock:product:1001 50
SETT stock:product:1002 60     # 拼写错误：SETT 不存在
INCR stock:product:1001
EXEC
# 返回：(error) EXECABORT Transaction discarded because of previous errors.
# 三条命令全部不执行
```

**② 运行时错误（执行时才报错）**：其他命令仍然执行，**不回滚**

```
MULTI
SET stock:product:1001 "abc"   # 把 String 设为非数字
INCR stock:product:1001        # 运行时错误：value is not an integer
SET stock:product:1002 60
EXEC
# 返回：
# 1) OK
# 2) (error) ERR value is not an integer or out of range
# 3) OK
# stock:product:1002 仍然被成功设置了！
```

#### 1.5 为什么 Redis 不支持回滚

Redis 作者 antirez 给出的设计理由：

1. **错误源于编程 bug**：运行时错误（如对非数字 String 执行 INCR）本质是程序员写错了代码，不应在生产环境出现
2. **回滚复杂且影响性能**：支持回滚需要记录 undo log，这与 Redis 极简、高性能的设计哲学相悖
3. **实际生产中很少触发**：成熟业务的命令都是固定模板，运行时错误率极低

这是一种**实用主义取舍**：用极简实现换取高性能，把"避免错误"的责任交给开发者。

#### 1.6 WATCH 乐观锁

`WATCH` 实现了类似 CAS（Compare-And-Swap）的乐观锁机制，解决"读取-修改-写入"的并发问题。

**工作流程**：

```
# 客户端 A                    # 客户端 B
WATCH stock:product:1001
val = GET stock:product:1001   # 假设读到 50
                               SET stock:product:1001 30   # 别的客户端改了！
MULTI
DECR stock:product:1001
EXEC
# 返回 (nil)，事务被放弃
# 因为 WATCH 监控的 key 在 EXEC 前被修改了
```

**WATCH 乐观锁库存扣减伪代码**（实际生产建议用 Lua，见下文）：

```python
while True:
    WATCH stock:product:1001
    stock = int(GET stock:product:1001)
    if stock < 1:
        UNWATCH
        return "库存不足"
    MULTI
    DECR stock:product:1001
    result = EXEC
    if result is not None:   # 不是 nil，说明没被并发打断
        return "扣减成功"
    # 否则重试
```

**注意**：
- `WATCH` 必须在 `MULTI` 之前调用
- `EXEC` 执行后会自动 `UNWATCH`，无论成功或失败
- `DISCARD` 也会自动 `UNWATCH`

---

### 二、Lua 脚本

#### 2.1 为什么需要 Lua

事务的局限：MULTI/EXEC 队列中的命令是**无条件执行**的，无法根据中间结果做判断。例如"库存不足就不扣减"这种逻辑，事务做不到。

Lua 脚本的优势：

- **条件判断**：可以在脚本内 `if ... then ... end`，根据当前值决定后续操作
- **原子性**：脚本执行期间 Redis 单线程被独占，其他命令阻塞等待
- **减少网络往返**：多条命令一次发送、一次返回
- **复用性**：`SCRIPT LOAD` 缓存后，客户端只需发 sha1 即可

#### 2.2 EVAL 命令

```
EVAL script numkeys key [key ...] arg [arg ...]
```

- `script`：Lua 脚本字符串
- `numkeys`：后面有几个 key（必须声明，Redis 集群据此路由）
- `key [key ...]`：操作的所有 key，在脚本内通过 `KEYS[1]`、`KEYS[2]` 访问
- `arg [arg ...]`：附加参数，在脚本内通过 `ARGV[1]`、`ARGV[2]` 访问

**示例**：

```
EVAL "return redis.call('SET', KEYS[1], ARGV[1])" 1 stock:product:1001 50
# 等价于 SET stock:product:1001 50
```

#### 2.3 EVALSHA 与 SCRIPT 命令

| 命令 | 作用 |
|------|------|
| `SCRIPT LOAD script` | 加载脚本到缓存，返回 sha1 摘要（不执行） |
| `EVALSHA sha1 numkeys key [...] arg [...]` | 用 sha1 执行已缓存的脚本 |
| `SCRIPT EXISTS sha1 [sha1 ...]` | 检查脚本是否已缓存 |
| `SCRIPT FLUSH` | 清空脚本缓存 |
| `SCRIPT KILL` | 终止正在运行的脚本（仅当未执行过写操作时有效） |

**优化流程**：首次用 `SCRIPT LOAD` 缓存脚本，之后只用 `EVALSHA` 发送 40 字符的 sha1，省网络带宽。

```
SCRIPT LOAD "return redis.call('GET', KEYS[1])"
# 返回：e0e1f9fabfc9d4800c877a7034fcef5ea0b63d3c
EVALSHA e0e1f9fabfc9d4800c877a7034fcef5ea0b63d3c 1 stock:product:1001
```

#### 2.4 Lua 语法速览

| 语法 | 示例 |
|------|------|
| 变量声明 | `local x = 10` |
| 条件 | `if x > 0 then ... elseif x == 0 then ... else ... end` |
| 循环 | `for i=1,10 do ... end` / `while x > 0 do ... end` |
| 注释 | `-- 单行注释` / `--[[ 多行注释 ]]` |
| 返回值 | `return 1` / `return {1, 2, 3}` |
| 字符串拼接 | `"hello " .. KEYS[1]` |
| 类型转换 | `tonumber(ARGV[1])` / `tostring(x)` |
| 逻辑运算 | `and` / `or` / `not` |

#### 2.5 Redis 调用：redis.call vs redis.pcall

| 函数 | 行为 |
|------|------|
| `redis.call(command, ...)` | 执行 Redis 命令；出错时**直接中断脚本**并把错误返回给客户端 |
| `redis.pcall(command, ...)` | 执行 Redis 命令；出错时**返回错误对象**，脚本可继续处理 |

```lua
-- 用 pcall 容错
local ok, err = pcall(redis.call, 'GET', KEYS[1])
if not ok then
    return "error: " .. err
end
```

#### 2.6 KEYS 与 ARGV 的安全规范

**核心原则：所有 key 必须通过 `KEYS` 传入，绝不在脚本里拼接 key 名。**

原因：
1. **集群路由**：Redis Cluster 需要根据 key 计算槽位，脚本里硬编码的 key 无法被路由
2. **审计与权限**：ACL 系统只能识别 KEYS 中的 key，拼接的 key 会绕过权限检查

```lua
-- 错误：硬编码 key 名
local stock = redis.call('GET', 'stock:product:1001')

-- 正确：用 KEYS 传参
local stock = redis.call('GET', KEYS[1])
local amount = tonumber(ARGV[1])
```

#### 2.7 脚本原子性与时间限制

- **原子性**：脚本执行期间 Redis 单线程被独占，其他客户端命令全部阻塞等待
- **时间限制**：`lua-time-limit`（默认 5000 毫秒 / 5 秒）超过后会允许其他命令执行 `SCRIPT KILL` 或 `SHUTDOWN NOSAVE`
- **SCRIPT KILL 的限制**：如果脚本已经执行过写操作，`SCRIPT KILL` 无效，只能 `SHUTDOWN NOSAVE` 强制重启

因此写 Lua 脚本必须**避免死循环和耗时操作**（如全表 SCAN），保证快速返回。

#### 2.8 安全注意事项

1. **不拼接 key**：用 `KEYS` 传参，方便集群路由与审计
2. **避免长时间运行**：复杂逻辑拆分，必要时用 `pcall` 容错
3. **SCRIPT LOAD 缓存优化**：避免每次 EVAL 发送大段脚本
4. **不信任用户输入**：ARGV 转换为数字前要做类型检查
5. **避免随机性**：脚本内调用 `TIME`、`RANDOMKEY` 等命令会导致主从复制不一致（4.0+ 已通过 `redis.replicate_commands()` 部分缓解，但应尽量避免）

#### 2.9 Function（7.0+ 新特性）

Redis 7.0 引入了 **Functions**，作为 EVAL/EVALSHA 的演进方案：

| 特性 | EVAL 脚本 | Function（7.0+） |
|------|----------|-----------------|
| 注册方式 | SCRIPT LOAD 缓存 | FUNCTION LOAD 持久化注册 |
| 跨实例同步 | 主从复制只同步执行结果 | 主从复制同步函数定义 |
| 重启保留 | 重启后丢失 | 持久化到 RDB/AOF，重启保留 |
| 命名空间 | 用 sha1 标识 | 用 library + function 名标识 |
| 调用方式 | EVALSHA sha1 | FCALL name numkeys ... |

```
# 注册一个 library
FUNCTION LOAD "#!lua name=mylib
redis.register_function('setnx_ex', function(keys, args)
    if redis.call('EXISTS', keys[1]) == 0 then
        return redis.call('SET', keys[1], args[1], 'EX', args[2])
    end
    return 0
end)"

# 调用
FCALL setnx_ex 1 stock:lock:1001 "uuid" 30
```

> 本章重点讲解 EVAL 模式（仍是业界主流写法），Function 作为了解即可。

---

### 三、事务 vs Lua 对比

| 维度 | 事务（MULTI/EXEC） | Lua 脚本（EVAL） |
|------|-------------------|------------------|
| **原子性** | 命令全部执行或全部不执行 | 整个脚本原子执行 |
| **条件判断** | ❌ 不支持 | ✅ 支持 if/else |
| **回滚** | ❌ 不支持 | ❌ 不支持 |
| **网络往返** | 多次（MULTI→命令→EXEC） | 1 次 |
| **错误处理** | 运行时错误不回滚 | 可用 pcall 捕获处理 |
| **复用性** | 每次发送全部命令 | SCRIPT LOAD 缓存复用 |
| **集群支持** | 必须在同一个槽位 | 必须在同一个槽位 |
| **复杂度** | 简单 | 中等 |
| **典型场景** | 简单原子写入、批量操作 | 库存扣减、限流、分布式锁释放 |

**选型建议**：
- 简单的"多条命令一起执行" → **事务**
- 需要"读-判-写"条件逻辑 → **Lua 脚本**
- 高频复用的复杂逻辑 → **SCRIPT LOAD + EVALSHA**

---

## 代码文件说明

| 文件 | 类型 | 用途 |
|------|------|------|
| `Code/01-transaction-demo.redis` | 命令脚本 | 事务演示：MULTI/EXEC/DISCARD、命令错误 vs 运行时错误、WATCH 乐观锁库存扣减 |
| `Code/02-lua-script-demo.redis` | 命令脚本 | Lua 演示：EVAL 基础、redis.call、KEYS/ARGV、SCRIPT LOAD + EVALSHA、条件判断 |
| `Code/03-lua-inventory.lua` | Lua 脚本 | 完整的原子库存扣减脚本，可用 `redis-cli --eval` 执行 |

执行方式：

```bash
# 在 Redis 目录下
redis-cli < "Day08 - 事务与Lua脚本/Code/01-transaction-demo.redis"

# 执行独立 Lua 脚本（注意 KEYS 和 ARGV 的传参方式）
redis-cli --eval "Day08 - 事务与Lua脚本/Code/03-lua-inventory.lua" stock:product:1001 , 1
```

---

## 关键知识点总结

### 事务命令速查

| 命令 | 语义 | 注意点 |
|------|------|--------|
| `MULTI` | 开启事务 | 返回 OK，后续命令入队 |
| `EXEC` | 执行队列 | 自动 UNWATCH |
| `DISCARD` | 取消事务 | 自动 UNWATCH |
| `WATCH k1 k2` | 乐观锁监控 | 必须在 MULTI 之前 |
| `UNWATCH` | 主动取消监控 | EXEC/DISCARD 后无需手动调用 |

### Lua 语法速查

```lua
-- 变量
local stock = tonumber(redis.call('GET', KEYS[1]) or 0)

-- 条件
if stock >= amount then
    redis.call('DECRBY', KEYS[1], amount)
    return 1
else
    return 0
end

-- 循环
for i, k in ipairs(KEYS) do
    -- 遍历所有 key
end

-- 返回多种类型
return "string"        -- 字符串
return 1               -- 整数
return {1, 2, 3}       -- 数组
return nil             -- 空
return {err = "msg"}   -- 错误对象
```

### 事务 vs Lua 对比表

| 维度 | 事务 | Lua |
|------|------|-----|
| 条件判断 | ❌ | ✅ |
| 网络往返 | 多次 | 1 次 |
| 错误处理 | 不回滚 | pcall 容错 |
| 复用 | ❌ | SCRIPT LOAD |
| 适用场景 | 简单原子 | 复杂条件逻辑 |

### Redis 事务 ACID 分析表

| 特性 | Redis 事务 | MySQL InnoDB |
|------|------------|-------------|
| 原子性 | 部分满足（不回滚） | 完全满足（支持回滚） |
| 一致性 | 满足 | 满足 |
| 隔离性 | 满足（单线程） | 多级别（默认 RR） |
| 持久性 | 取决于持久化配置 | 完全满足（redo log） |

---

## 实战练习

### 练习 1：用事务批量初始化商品数据

需求：用 `MULTI/EXEC` 一次性初始化 5 个商品的库存，并为每个商品设置 1 小时过期时间（模拟"上架后 1 小时未售自动下架"）。

提示：
```redis
MULTI
SET stock:product:2001 100 EX 3600
SET stock:product:2002 50 EX 3600
...
EXEC
```

要求：
1. 用一个事务完成所有初始化
2. 验证所有 key 都正确设置（用 `MGET` 和 `TTL` 检查）
3. 思考：为什么这里用事务比逐条 SET 好？

### 练习 2：用 Lua 实现限流计数器（固定窗口）

需求：写一个 Lua 脚本，实现"每个用户每分钟最多调用 API 100 次"的限流。

参数约定：
- `KEYS[1]` = `rate:limit:{user_id}:{minute}`（例如 `rate:limit:u1:202607281430`）
- `ARGV[1]` = 限制次数（100）
- `ARGV[2]` = 时间窗口秒数（60）

逻辑：
1. 用 `INCR` 增加计数
2. 如果是第一次（计数为 1），用 `EXPIRE` 设置 60 秒过期
3. 如果计数 > 100，返回 0（拒绝）
4. 否则返回 1（允许）

测试：
```bash
# 编写脚本文件 rate-limit.lua
redis-cli --eval rate-limit.lua rate:limit:u1:202607281430 , 100 60
```

### 练习 3：对比事务与 Lua 在库存扣减上的表现

需求：分别用两种方式实现"扣减库存，库存不足返回失败"：

**方式 A（事务 + WATCH 乐观锁）**：在 redis-cli 中模拟，体会"读-判-写"需要客户端循环重试的繁琐。

**方式 B（Lua 脚本）**：直接使用本章 `03-lua-inventory.lua`，对比代码简洁度。

思考题：
1. 为什么高并发场景下 WATCH 重试次数可能飙升？
2. Lua 脚本为什么能彻底避免重试？
3. 如果 Lua 脚本执行时间过长，会带来什么问题？

---

**下一章**：[Day09 - 持久化机制](../Day09%20-%20持久化机制/README.md) — 探讨 Redis 如何把内存数据安全地落到磁盘。
