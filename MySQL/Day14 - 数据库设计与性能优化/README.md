# Day14 - 数据库设计与性能优化

好的设计让性能自然而来：一张遵守三大范式、字段类型合理、索引精准的表，写查询时几乎不会慢。性能优化是设计、索引、SQL、架构的综合功夫——没有银弹，只有方法论。本章把数据库设计（范式、反范式、ER 建模、命名规范）与性能优化（慢查询日志、EXPLAIN、SQL 优化技巧、分库分表）整合在一起，作为整个 MySQL 板块的收官。

## 学习目标

- 理解三大范式（1NF/2NF/3NF）与 BCNF，能识别表中的范式违反
- 掌握反范式设计的场景与权衡，知道何时冗余字段
- 能用 ER 建模表达实体关系，并落地为表结构
- 掌握命名规范、主键设计、字段设计的工程实践
- 能开启慢查询日志并用 EXPLAIN 定位慢 SQL
- 掌握常见 SQL 优化技巧：避免 SELECT *、深分页、JOIN、子查询、IN vs EXISTS
- 了解读写分离、分库分表（垂直/水平）、缓存层等架构优化
- 理解 ORM N+1 问题与连接池配置
- 建立性能优化方法论：先定位再优化、避免过早优化

---

## 理论知识讲解

### 1. 数据库设计

#### 1.1 三大范式

**第一范式 1NF：列的原子性**

每一列都不可再分。例如"地址"列若写成"北京市海淀区中关村"，违反 1NF（可拆为省、市、区、街道）。

```
违反 1NF：
| id | name | address(省+市+区) |
拆分后：
| id | name | province | city | district |
```

**第二范式 2NF：非主键列完全依赖主键**

在 1NF 基础上，所有非主键列必须**完全依赖**整个主键（针对联合主键）。例如订单明细表 `(order_id, product_id, quantity, product_name)`，`product_name` 只依赖 `product_id` 不依赖 `order_id`，违反 2NF。

```
违反 2NF（联合主键 order_id+product_id）：
| order_id | product_id | quantity | product_name | product_price |
拆分后：
order_items(order_id, product_id, quantity)   -- 主键 (order_id, product_id)
products(product_id, product_name, product_price)  -- 主键 product_id
```

**第三范式 3NF：非主键列直接依赖主键，无传递依赖**

在 2NF 基础上，非主键列不能依赖其他非主键列。例如员工表 `(emp_id, dept_id, dept_name)`，`dept_name` 依赖 `dept_id`，`dept_id` 依赖 `emp_id`，存在传递依赖，违反 3NF。

```
违反 3NF（传递依赖）：
| emp_id | emp_name | dept_id | dept_name |
拆分后：
employees(emp_id, emp_name, dept_id)
departments(dept_id, dept_name)
```

#### 1.2 BCNF（巴斯-科德范式）

在 3NF 基础上，每个决定因素都必须是候选键。比 3NF 更严格，实际项目中 3NF 已足够。

#### 1.3 反范式

反范式是**为性能而冗余**。范式消除冗余，但有时冗余能极大提升查询性能：

| 场景 | 反范式做法 | 收益 |
|------|----------|------|
| 订单冗余商品名 | order_items 加 product_name 列 | 查订单明细不用 JOIN products |
| 用户冗余消费总额 | users 加 total_spent 列 | 不用每次 SUM(orders) |
| 商品冗余销量 | products 加 sold_count 列 | 排行榜不用 GROUP BY order_items |
| 评论冗余用户名 | reviews 加 username 列 | 显示评论不用 JOIN users |

**何时遵循范式、何时反范式**：

- **写多读少** → 遵循范式（避免冗余字段多处更新）
- **读多写少** → 适度反范式（用冗余换查询速度）
- **强一致性** → 遵循范式（冗余字段容易不一致）
- **报表统计** → 反范式或物化视图（预计算）

#### 1.4 ER 建模

ER（Entity-Relationship）建模用图形表达数据结构：

- **实体**：矩形，如"用户""商品"
- **属性**：椭圆，如"用户名""价格"
- **关系**：菱形，如"下单""评价"

**基数（关系数量）**：

| 类型 | 说明 | 示例 |
|------|------|------|
| 1:1 | 一对一 | 用户 ↔ 账户 |
| 1:N | 一对多 | 用户 → 订单 |
| N:M | 多对多 | 商品 ↔ 订单（通过 order_items） |

ER 图落地为表：
- 1:1：任一方加外键 + UNIQUE
- 1:N：N 方加外键
- N:M：建中间表，含两方外键（联合主键）

#### 1.5 命名规范

| 对象 | 规范 | 示例 |
|------|------|------|
| 表名 | 小写下划线，业务含义清晰 | `order_items`、`user_account` |
| 列名 | 小写下划线，不缩写 | `created_at`、`total_amount` |
| 主键 | `id` 或 `表名_id` | `id`、`user_id` |
| 外键 | `引用表名_id` | `user_id`、`product_id` |
| 索引 | `idx_列名` / `uk_列名` / `pk_列名` | `idx_user_id`、`uk_email` |
| 布尔字段 | `is_xxx` / `has_xxx` | `is_active`、`has_paid` |
| 时间字段 | `_at` / `_time` / `_date` | `created_at`、`expired_at` |

**单数 vs 复数**：表名建议单数（`user` 而非 `users`），但业界两种都有人用，团队统一即可。

#### 1.6 主键设计

| 方案 | 优点 | 缺点 | 适用 |
|------|------|------|------|
| 自增 INT/BIGINT | 索引友好、占用小、易读 | 单点、易爬虫 | 单库单表 |
| UUID | 全局唯一、无中心 | 占用大（36 字符）、索引碎片 | 分布式、需合并 |
| 雪花算法 Snowflake | 全局唯一、趋势递增、占用小（8 字节） | 依赖时钟、需配置 worker | 分布式 |

> **实践建议**：单库用自增 BIGINT；分布式用雪花算法；UUID 仅在需合并数据时用。

#### 1.7 字段设计

- **避免 NULL**：NULL 比较与索引都麻烦，用默认值（0、空串、'1970-01-01'）
- **时间戳必加**：`created_at` + `updated_at`，至少加 `created_at`
- **软删除字段**：`deleted_at` 或 `is_deleted`，避免物理删除丢数据
- **金额用 DECIMAL**：`DECIMAL(10,2)` 而非 FLOAT/DOUBLE
- **状态用枚举**：`status ENUM('draft','on_sale')` 或 TINYINT + 字典表
- **文本长度评估**：VARCHAR 长度按实际业务上限设，别盲目 255

---

### 2. 性能优化

#### 2.1 慢查询日志

```sql
-- 查看是否开启
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
SHOW VARIABLES LIKE 'slow_query_log_file';

-- 开启
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;            -- 超过 1 秒算慢
SET GLOBAL log_queries_not_using_indexes = ON;  -- 未用索引也记录
```

```bash
# 用 mysqldumpslow 分析
mysqldumpslow -s t -t 10 /var/log/mysql/slow.log
```

#### 2.2 EXPLAIN 优化回顾（呼应 Day10）

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 1;
```

关键列：

| 列 | 关注点 |
|----|------|
| `type` | system > const > eq_ref > ref > range > index > ALL，至少要 range |
| `key` | 实际用的索引，NULL 表示没走索引 |
| `rows` | 预估扫描行数，越少越好 |
| `Extra` | Using index（覆盖索引）、Using filesort（文件排序）、Using temporary（临时表） |

#### 2.3 SQL 优化技巧

**避免 SELECT *，只查需要的列（覆盖索引）**

```sql
-- 差：SELECT * 会导致回表
SELECT * FROM users WHERE id = 1;

-- 好：只查需要的列，若 (id, username) 有联合索引则覆盖索引
SELECT id, username FROM users WHERE id = 1;
```

**WHERE 避免函数包裹索引列**

```sql
-- 差：函数包裹导致索引失效
SELECT * FROM orders WHERE YEAR(created_at) = 2025;
SELECT * FROM users WHERE LEFT(username, 3) = 'tom';

-- 好：改用范围
SELECT * FROM orders WHERE created_at >= '2025-01-01' AND created_at < '2026-01-01';
SELECT * FROM users WHERE username LIKE 'tom%';
```

**避免隐式类型转换**

```sql
-- 差：user_id 是 INT，传字符串导致隐式转换，索引失效
SELECT * FROM orders WHERE user_id = '1';

-- 好：类型匹配
SELECT * FROM orders WHERE user_id = 1;
```

**LIMIT 深分页优化**

```sql
-- 差：OFFSET 大时需扫描前面所有行
SELECT * FROM orders ORDER BY id LIMIT 100000, 10;

-- 方案 1：延迟关联
SELECT o.* FROM orders o
INNER JOIN (SELECT id FROM orders ORDER BY id LIMIT 100000, 10) t
ON o.id = t.id;

-- 方案 2：子查询
SELECT * FROM orders WHERE id > (SELECT id FROM orders ORDER BY id LIMIT 100000, 1)
ORDER BY id LIMIT 10;

-- 方案 3：游标分页（记住上一页最后一条 id）
SELECT * FROM orders WHERE id > 100010 ORDER BY id LIMIT 10;
```

**JOIN 优化：小表驱动大表**

```sql
-- 好：小表（users）驱动大表（orders），MySQL 自动选驱动表
-- 确保 ON 列有索引
SELECT u.username, o.id
FROM users u
JOIN orders o ON o.user_id = u.id   -- orders.user_id 必须有索引
WHERE u.role = 'admin';
```

**子查询优化：改写为 JOIN**

```sql
-- 差：相关子查询，每行执行一次
SELECT * FROM products p
WHERE p.id IN (SELECT product_id FROM order_items WHERE quantity > 10);

-- 好：改写为 JOIN + DISTINCT
SELECT DISTINCT p.* FROM products p
JOIN order_items oi ON oi.product_id = p.id
WHERE oi.quantity > 10;
```

**IN vs EXISTS 选择**

```sql
-- IN：子查询结果集小、外层表大时用 IN
SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE role = 'admin');

-- EXISTS：外层表小、子查询表大时用 EXISTS
SELECT * FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```

**OR 改写为 UNION ALL**

```sql
-- 差：OR 可能不走索引
SELECT * FROM orders WHERE user_id = 1 OR status = 'paid';

-- 好：UNION ALL，两个子查询各走各自索引
SELECT * FROM orders WHERE user_id = 1
UNION ALL
SELECT * FROM orders WHERE status = 'paid' AND user_id <> 1;
```

**COUNT(*) vs COUNT(列)**

```sql
-- COUNT(*)：统计行数，不关心 NULL，MySQL 优化过，最快
SELECT COUNT(*) FROM users;

-- COUNT(列)：统计该列非 NULL 行数，若列允许 NULL 则结果不同
SELECT COUNT(email) FROM users;

-- 注意：COUNT(1) 与 COUNT(*) 性能相当，没必要刻意用 COUNT(1)
```

#### 2.4 索引优化回顾

- **联合索引顺序**：把等值查询列放前，范围查询列放后
- **覆盖索引**：查询列都在索引中，避免回表
- **避免冗余索引**：有 `(a, b, c)` 就不必再建 `(a, b)` 单独索引
- **避免索引失效**：函数包裹、隐式转换、左模糊 `LIKE '%xx'`、OR、!= 都可能失效

---

### 3. 架构优化

#### 3.1 读写分离

```
应用 ──写──> 主库 ──binlog──> 从库1
                                从库2  ←──读── 应用
                                从库3
```

- 主库负责写，从库负责读
- 写少读多场景收益大
- 注意主从延迟带来的"写后读不到"问题

#### 3.2 分库分表

| 类型 | 说明 | 适用 |
|------|------|------|
| 垂直分库 | 按业务拆库（用户库、订单库、商品库） | 业务边界清晰 |
| 垂直分表 | 按列拆表（热列冷列分表） | 表列数过多 |
| 水平分表 | 按行拆表（按 ID 哈希、按时间范围） | 单表数据量过大 |

**分片策略**：

- **哈希分片**：`user_id % N`，数据均匀，但扩容麻烦
- **范围分片**：按时间/ID 范围，易扩容，但易热点
- **一致性哈希**：扩容时迁移少

**ShardingSphere**：Apache 顶级项目，提供 JDBC 与 Proxy 两种模式的分库分表中间件。

#### 3.3 缓存层

```
应用 → Redis 缓存 → MySQL
       ↑ 命中直接返回
       ↓ 未命中查 DB 后回填
```

- 热点数据放 Redis
- 缓存一致性：先更新 DB，再删缓存（Cache Aside）
- 缓存穿透/击穿/雪崩的防护（详见 Redis 板块）

#### 3.4 与应用层的配合

**ORM N+1 问题**

```python
# 差：N+1 查询（查一次列表 + N 次查关联）
users = User.objects.all()
for u in users:
    print(u.profile.bio)  # 每次循环都查一次 profile 表

# 好：JOIN / 预加载
users = User.objects.select_related('profile').all()
```

**连接池配置**

- `maximumPoolSize`：连接池上限，通常 = `(CPU 核数 * 2) + 磁盘数`
- `minimumIdle`：最小空闲连接，与 max 相等避免抖动
- `connectionTimeout`：获取连接超时，建议 30s
- `idleTimeout`：空闲连接超时，建议 10 分钟

**慢 SQL 监控**

- Druid（Java）：内置慢 SQL 统计
- PMM / Prometheus + Grafana：可视化监控
- 阿里云 RDS 慢 SQL 告警

---

### 4. 性能优化方法论

```
┌─────────────────────────────────────────────────────┐
│                性能优化流程                           │
├─────────────────────────────────────────────────────┤
│  1. 监控告警（慢日志 + APM）                          │
│         ↓                                            │
│  2. 定位慢 SQL（mysqldumpslow / EXPLAIN）            │
│         ↓                                            │
│  3. 分析根因（索引失效？数据量大？SQL 写法？）         │
│         ↓                                            │
│  4. 优化方案（加索引 / 改写 SQL / 反范式 / 分表）     │
│         ↓                                            │
│  5. 压测验证（同等数据量对比前后耗时）                │
│         ↓                                            │
│  6. 上线观察（持续监控，避免回退）                    │
└─────────────────────────────────────────────────────┘
```

**三条原则**：

1. **先定位再优化**：不要凭感觉优化，用 EXPLAIN 与慢日志说话
2. **避免过早优化**：先跑起来，遇到瓶颈再优化，否则浪费时间且增加复杂度
3. **压测验证**：优化后必须用同等数据量压测，否则可能是"假优化"

---

## 关键知识点总结

### 三大范式速查

| 范式 | 要求 | 一句话 | 反例 |
|------|------|------|------|
| 1NF | 列不可分 | 每列原子性 | "地址"列含省市区 |
| 2NF | 完全依赖主键 | 非主键列依赖整个主键 | 联合主键表中部分列只依赖主键一部分 |
| 3NF | 无传递依赖 | 非主键列直接依赖主键 | A→B→C，C 通过 B 间接依赖 A |
| BCNF | 决定因素必须是候选键 | 比 3NF 更严 | 主键子集决定其他主键子集 |

### SQL 优化清单

| 优化点 | 做法 |
|------|------|
| 避免 SELECT * | 只查需要的列，争取覆盖索引 |
| 索引列不加函数 | 改用范围/前缀 |
| 类型匹配 | 避免 `WHERE int_col = '1'` |
| 深分页 | 延迟关联 / 游标分页 |
| JOIN | 小表驱动大表，ON 列建索引 |
| 子查询 | 改写为 JOIN |
| IN vs EXISTS | 小驱动大用 IN，大驱动小用 EXISTS |
| OR | 改 UNION ALL |
| COUNT | 用 COUNT(*)，不用 COUNT(列)（除非要排除 NULL） |
| LIMIT | 大 OFFSET 用游标或延迟关联 |

### 分库分表对比表

| 类型 | 维度 | 优点 | 缺点 | 适用 |
|------|------|------|------|------|
| 垂直分库 | 按业务 | 业务隔离、降低单库压力 | 跨库 JOIN 难 | 业务边界清晰 |
| 垂直分表 | 按列 | 热列集中、IO 减少 | 管理复杂 | 表列数多 |
| 水平分表 | 按行 | 单表数据量降低 | 跨表查询难、扩容痛 | 单表数据量 > 1000 万 |

### 性能优化流程

```
监控 → 定位 → 分析 → 优化 → 压测 → 上线
```

---

## 代码文件说明

| 文件 | 内容 |
|------|------|
| `Code/01-normalization-demo.sql` | 范式演示：用一个反例表逐级拆分到 3NF，再演示反范式冗余字段提升查询，带 SELECT 对比 |
| `Code/02-slow-query-optimization.sql` | 慢查询优化演示：构造慢查询 → EXPLAIN 分析 → 加索引/改写 SQL → 再 EXPLAIN 对比，含深分页与子查询改 JOIN |
| `Code/03-design-best-practices.md` | 数据库设计最佳实践文档：命名规范、字段设计、索引规范、主键选择、ER 建模步骤、常见反模式 |

执行方式：

```sql
mysql> USE ecommerce;
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day14 - 数据库设计与性能优化/Code/01-normalization-demo.sql
```

---

## 实战练习

### 练习一：识别并修复范式违反

下面这张"订单明细表"违反了哪些范式？请拆分到 3NF，并写出拆分后的表结构。

```
order_detail(order_id, product_id, quantity, unit_price,
             product_name, product_category_id, product_category_name,
             user_id, user_name, user_email)
主键：(order_id, product_id)
```

### 练习二：慢查询优化实战

构造一个查询：在 `orders` 表上做 `WHERE status = 'paid' AND created_at LIKE '2025-07-%'`，先 EXPLAIN 看执行计划，然后：

1. 分析为什么慢（`LIKE` 左模糊？无索引？）
2. 改写为范围查询
3. 创建合适的联合索引 `(status, created_at)`
4. 再 EXPLAIN 对比 `type` 与 `rows`

### 练习三：反范式设计

场景：电商首页需要展示"商品销量 Top 10"。当前实现是 `SELECT product_id, SUM(quantity) FROM order_items GROUP BY product_id ORDER BY ... LIMIT 10`，订单量大时很慢。请用反范式思路设计一个 `product_stats` 表（含 `sold_count` 字段），并说明如何用触发器或定时任务维护它。
