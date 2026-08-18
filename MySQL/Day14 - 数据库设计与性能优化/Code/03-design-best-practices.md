# 数据库设计最佳实践

> 本文档配套 `Day14 - 数据库设计与性能优化`，汇总数据库设计中的命名规范、字段设计、索引规范、主键选择、ER 建模步骤与常见反模式。可作为团队 Code Review 的检查清单。

---

## 1. 命名规范

### 1.1 通用原则

| 原则 | 说明 |
|------|------|
| 一致性 | 全库统一风格，不混用驼峰与下划线 |
| 可读性 | 见名知意，避免无意义缩写 |
| 简洁性 | 长度适中，不冗余 |
| 可搜索 | 用前缀分组（如 `order_*`、`user_*`） |

### 1.2 各对象命名规范

| 对象 | 规范 | 示例 | 反例 |
|------|------|------|------|
| 库名 | 小写下划线，业务名 | `ecommerce`、`user_center` | `Ecommerce`、`eCom` |
| 表名 | 小写下划线，单数名词 | `user`、`order_item` | `users`、`OrderItem`、`tbl_user` |
| 列名 | 小写下划线 | `created_at`、`total_amount` | `CreatedAt`、`createTime` |
| 主键 | `id` 或 `表名_id` | `id`、`user_id` | `pk`、`ID` |
| 外键 | `引用表名_id` | `user_id`、`product_id` | `uid`、`pid` |
| 索引 | `idx_列名` / `uk_列名` | `idx_user_id`、`uk_email` | `index1`、`i_uid` |
| 联合索引 | `idx_列1_列2` | `idx_status_created` | `idx1` |
| 唯一索引 | `uk_列名` | `uk_email` | `uniq_email`、`uq_email` |
| 主键索引 | `pk_列名` 或默认 `PRIMARY` | `pk_id` | - |
| 视图 | `v_名称` | `v_user_summary` | `view_user` |
| 存储过程 | `sp_名称` | `sp_transfer` | `proc_transfer` |
| 函数 | `fn_名称` | `fn_calc_price` | `func_calc` |
| 触发器 | `trg_表名_动作` | `trg_user_after_update` | `trg1` |
| 事件 | `evt_名称` | `evt_clean_logs` | `event1` |

### 1.3 字段命名细则

| 字段类型 | 命名 | 示例 |
|---------|------|------|
| 布尔/状态标记 | `is_xxx` / `has_xxx` | `is_active`、`has_paid` |
| 时间戳 | `_at` / `_time` / `_date` | `created_at`、`expired_at`、`birth_date` |
| 金额 | `_amount` / `_price` / `_fee` | `total_amount`、`unit_price` |
| 数量 | `_count` / `_qty` / `_num` | `order_count`、`quantity` |
| 状态 | `status` / `_state` | `status`、`order_state` |
| 类型 | `_type` / `_kind` | `user_type`、`payment_kind` |
| 描述 | `description` / `remark` / `comment` | `description`、`remark` |

### 1.4 禁用关键字

避免与 SQL 保留字冲突：

```
order, group, user, key, desc, asc, range, status（部分场景）,
type, name（部分场景）, index, table, database, view, ...
```

> `order` 是 SQL 保留字，订单表建议用 `orders` 或加反引号 `` `order` ``。本项目用 `orders` 规避。

---

## 2. 字段设计规范

### 2.1 数据类型选择

| 业务场景 | 推荐类型 | 避免 | 原因 |
|---------|---------|------|------|
| 主键 | BIGINT AUTO_INCREMENT | INT（数据量大时溢出） | BIGINT 范围足够 |
| 金额 | DECIMAL(10,2) | FLOAT/DOUBLE | 浮点有精度损失 |
| 短字符串 | VARCHAR(N) | CHAR(N) | VARCHAR 节省空间 |
| 长文本 | TEXT / MEDIUMTEXT | VARCHAR(10000) | 超长用 TEXT |
| 布尔 | TINYINT(1) | BOOLEAN | MySQL BOOLEAN 实为 TINYINT(1) |
| 枚举 | ENUM 或 TINYINT + 字典表 | VARCHAR | 节省空间，约束值域 |
| 时间戳 | DATETIME / TIMESTAMP | VARCHAR 存时间 | 失去时间运算能力 |
| JSON | JSON | TEXT 存 JSON 串 | JSON 类型支持函数查询 |
| 唯一标识 | CHAR(36) UUID / BIGINT 雪花 | VARCHAR | 定长更高效 |

### 2.2 NULL 的处理

**原则：能用默认值就不用 NULL**

| 场景 | 默认值 |
|------|------|
| 字符串 | `''`（空串） |
| 数值 | `0` |
| 布尔 | `0`（false） |
| 时间 | `'1970-01-01 00:00:00'` 或不设默认（强制必填） |

**为什么避免 NULL**：
- NULL 比较需用 `IS NULL`，`=` 永远返回 NULL
- NULL 影响索引效率（NULL 值单独处理）
- 聚合函数忽略 NULL（COUNT(列) 不计 NULL 行）
- NULL 占用额外字节（1 字节标记）

**例外**：`deleted_at` 这类"可选时间戳"用 NULL 表示"未删除"是合理的。

### 2.3 必备字段

每张业务表至少包含：

```sql
CREATE TABLE xxx (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    -- 业务字段...
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at   DATETIME    NULL     DEFAULT NULL COMMENT '软删除时间，NULL 表示未删除'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表说明';
```

### 2.4 字段长度评估

| 字段 | 推荐长度 | 说明 |
|------|---------|------|
| 用户名 | VARCHAR(32) | 大多数平台 20 字符够 |
| 邮箱 | VARCHAR(128) | RFC 规范最长 320，实际 128 够 |
| 手机号 | CHAR(11) | 中国手机号定长 11 位 |
| 密码哈希 | CHAR(60) | bcrypt 输出固定 60 字符 |
| URL | VARCHAR(512) | 长链接可能很长 |
| 短描述 | VARCHAR(255) | 列表页展示用 |
| 长描述 | TEXT | 详情页富文本 |

> **不要盲目 VARCHAR(255)**：长度影响索引大小与内存占用，按业务实际评估。

### 2.5 枚举与字典表

**小范围固定枚举**：用 ENUM 或 TINYINT

```sql
-- 方式 1：ENUM（修改需 ALTER TABLE）
status ENUM('draft', 'on_sale', 'off_sale') NOT NULL DEFAULT 'draft'

-- 方式 2：TINYINT + 注释（推荐，扩展性好）
status TINYINT NOT NULL DEFAULT 0 COMMENT '0=draft 1=on_sale 2=off_sale'
```

**大范围可扩展枚举**：用字典表

```sql
CREATE TABLE order_status_dict (
    code    TINYINT PRIMARY KEY,
    name    VARCHAR(20),
    description VARCHAR(100)
);

INSERT INTO order_status_dict VALUES
(0, 'pending',   '待支付'),
(1, 'paid',      '已支付'),
(2, 'shipped',   '已发货'),
(3, 'completed', '已完成'),
(4, 'cancelled', '已取消'),
(5, 'refunded',  '已退款');
```

---

## 3. 索引规范

### 3.1 索引设计原则

1. **主键必有**：每张表必须有主键，推荐自增 BIGINT
2. **外键建索引**：所有 JOIN / WHERE 用的外键列建索引
3. **查询条件建索引**：高频 WHERE 条件列建索引
4. **排序字段建索引**：高频 ORDER BY 列考虑联合索引
5. **联合索引优先**：多列查询用联合索引，遵循最左前缀
6. **避免冗余**：有 `(a, b, c)` 就不必再建 `(a, b)`、`(a)`
7. **避免过多**：单表索引不超过 5-6 个，写多场景更少

### 3.2 联合索引顺序原则

```
等值查询列在前，范围查询列在后
区分度高的列在前，区分度低的列在后
最常用的列在前
```

```sql
-- 场景：WHERE status = 'paid' AND created_at > '2025-07-01'
-- status 是等值，created_at 是范围
-- 索引顺序：(status, created_at)
CREATE INDEX idx_status_created ON orders(status, created_at);

-- 反例：(created_at, status) 范围在后会断开 status 的索引使用
```

### 3.3 索引命名

| 类型 | 前缀 | 示例 |
|------|------|------|
| 普通索引 | `idx_` | `idx_user_id` |
| 唯一索引 | `uk_` | `uk_email` |
| 主键 | `pk_` 或默认 `PRIMARY` | `pk_id` |
| 全文索引 | `ft_` | `ft_content` |
| 联合索引 | `idx_列1_列2` | `idx_uid_status` |

### 3.4 何时建索引

| 场景 | 建议 |
|------|------|
| 主键 | 必建 |
| 外键 | 必建 |
| 唯一约束（邮箱、手机号） | 建 UNIQUE |
| 高频 WHERE 条件 | 建 |
| 高频 JOIN ON 列 | 建 |
| 高频 ORDER BY 列 | 考虑联合索引 |
| 低基数列（性别、状态） | 不单独建，放联合索引 |
| 大表 LIKE '%xx%' | 不建（左模糊失效），用全文索引 |
| 频繁更新的列 | 少建（索引维护成本高） |
| 小表（< 1000 行） | 不建（全表扫更快） |

### 3.5 索引失效场景

```sql
-- 1. 函数包裹
WHERE YEAR(created_at) = 2025              -- 失效
WHERE created_at >= '2025-01-01'           -- 生效

-- 2. 隐式类型转换
WHERE status = 1   -- status 是 VARCHAR    -- 失效
WHERE status = '1'                         -- 生效

-- 3. 左模糊
WHERE name LIKE '%abc%'                    -- 失效
WHERE name LIKE 'abc%'                     -- 生效

-- 4. OR 两边不全有索引
WHERE a = 1 OR b = 2  -- 只有 a 有索引     -- 失效

-- 5. != / NOT IN
WHERE status != 'paid'                     -- 可能失效（优化器判断）

-- 6. 联合索引非最左前缀
-- 索引 (a, b, c)
WHERE b = 1 AND c = 2                      -- 失效（缺 a）
WHERE a = 1 AND c = 2                      -- 部分生效（只用 a）
WHERE a = 1 AND b = 2 AND c = 3            -- 全部生效
```

---

## 4. 主键选择

### 4.1 三种方案对比

| 方案 | 类型 | 优点 | 缺点 | 适用 |
|------|------|------|------|------|
| 自增 | BIGINT AUTO_INCREMENT | 索引友好、占用小、易读 | 单点、易爬虫、分布式难 | 单库单表 |
| UUID | CHAR(36) | 全局唯一、无中心 | 占用大、索引碎片、不可读 | 需合并数据 |
| 雪花 | BIGINT | 全局唯一、趋势递增、占用小 | 依赖时钟、需配置 worker | 分布式 |

### 4.2 推荐策略

- **单库**：自增 BIGINT
- **分布式**：雪花算法（Twitter Snowflake 或变种）
- **对外暴露**：用单独的 `uuid` 字段（如 `share_uuid`），不暴露自增 ID 防爬虫

### 4.3 雪花算法结构

```
| 1 bit 符号 | 41 bit 时间戳 | 10 bit 机器ID | 12 bit 序列号 |
```

- 64 位整数，趋势递增
- 每毫秒每机器可生成 4096 个 ID
- 全局唯一

---

## 5. ER 建模步骤

### 5.1 建模流程

```
1. 识别实体 → 2. 识别关系 → 3. 识别属性 → 4. 确定基数 → 5. 落地为表 → 6. 加索引
```

### 5.2 详细步骤

**步骤 1：识别实体**

从需求文档中找名词：
- "用户下单购买商品" → 用户、订单、商品
- "商品属于分类" → 商品、分类
- "用户写评价" → 用户、评价、商品

**步骤 2：识别关系**

| 关系 | 实体对 | 类型 |
|------|------|------|
| 下单 | 用户 ↔ 订单 | 1:N |
| 包含 | 订单 ↔ 商品 | N:M（通过 order_items） |
| 属于 | 商品 ↔ 分类 | N:1 |
| 评价 | 用户 ↔ 商品 | N:M（通过 reviews） |

**步骤 3：识别属性**

每个实体列属性：
- 用户：id, username, email, role, status, created_at
- 商品：id, name, category_id, price, stock, status, created_at
- 订单：id, user_id, total_amount, status, created_at
- 订单明细：order_id, product_id, quantity, unit_price

**步骤 4：确定基数**

| 关系 | 基数 | 落地方式 |
|------|------|---------|
| 用户 1:N 订单 | 一个用户多订单 | orders 加 user_id 外键 |
| 订单 N:M 商品 | 多对多 | 建 order_items 中间表 |
| 分类 1:N 商品 | 一个分类多商品 | products 加 category_id 外键 |
| 用户 N:M 商品（评价） | 多对多 | 建 reviews 中间表 |

**步骤 5：落地为表**

```sql
-- 实体表
users(id, username, email, ...)
categories(id, name, parent_id, ...)
products(id, name, category_id, price, ...)
orders(id, user_id, total_amount, ...)

-- 关系表（N:M 中间）
order_items(order_id, product_id, quantity, unit_price)  -- 联合主键
reviews(id, user_id, product_id, rating, content, ...)
```

**步骤 6：加索引**

```sql
-- 外键索引
CREATE INDEX idx_orders_user_id    ON orders(user_id);
CREATE INDEX idx_products_cat_id   ON products(category_id);
CREATE INDEX idx_order_items_oid   ON order_items(order_id);
CREATE INDEX idx_order_items_pid   ON order_items(product_id);

-- 查询索引
CREATE INDEX idx_orders_status     ON orders(status);
CREATE INDEX idx_products_status   ON products(status);
CREATE UNIQUE INDEX uk_users_email ON users(email);
```

### 5.3 ER 图示例

```
┌──────────┐         ┌──────────┐         ┌──────────────┐
│  users   │ 1     N │  orders  │ 1     N │ order_items  │
│ 用户     │─────────│ 订单     │─────────│ 订单明细     │
└────┬─────┘         └──────────┘         └──────┬───────┘
     │ N                                          │ N
     │                                            │
     │ M                                          │
┌────┴─────┐                                  ┌───┴──────┐
│ reviews  │             N                1   │ products │
│ 评价     │───────────────────────────────────│ 商品     │
└──────────┘              M:1                 └────┬─────┘
                                                    │ N
                                                    │
                                              ┌─────┴──────┐
                                              │ categories │
                                              │ 分类       │
                                              └────────────┘
```

---

## 6. 常见反模式与避坑

### 6.1 反模式：一列存多值

```sql
-- 反例：tag_ids 存逗号分隔的 ID
article(id, title, tag_ids)  -- tag_ids = "1,2,3,5"

-- 查询"含标签 3 的文章"需 LIKE，无法走索引
SELECT * FROM article WHERE FIND_IN_SET(3, tag_ids);
```

**正确做法**：建中间表

```sql
article(id, title)
tag(id, name)
article_tag(article_id, tag_id)  -- 联合主键
```

### 6.2 反模式：实体属性扩展（EAV）

```sql
-- 反例：把所有属性塞成 key-value
product_attr(id, product_id, attr_name, attr_value)
-- attr_name = 'color', attr_value = 'red'
-- attr_name = 'size',  attr_value = 'XL'
```

**问题**：查询需多次自连接，类型丢失（attr_value 都是 VARCHAR）。

**正确做法**：固定属性用列，可变属性用 JSON

```sql
products(id, name, price, color, size, ...)  -- 固定属性
products(id, name, price, attrs JSON)        -- 可变属性用 JSON
```

### 6.3 反模式：用业务编码做主键

```sql
-- 反例：用订单号做主键
orders(order_no PRIMARY KEY, ...)  -- order_no = 'ORD20250727001'
```

**问题**：
- 业务编码可能变（改格式需迁移）
- 字符串主键索引效率低于数值
- 跨表关联占用大

**正确做法**：自增 ID 做主键，业务编码做唯一索引

```sql
orders(id PRIMARY KEY, order_no UNIQUE, ...)
```

### 6.4 反模式：软删除字段当查询条件

```sql
-- 反例：每个查询都要带 deleted_at IS NULL
SELECT * FROM users WHERE deleted_at IS NULL AND role = 'admin';
SELECT * FROM orders WHERE deleted_at IS NULL AND status = 'paid';
```

**问题**：易遗漏，且影响索引。

**正确做法**：
- 团队约定所有查询必带软删除条件
- 或用视图封装 `CREATE VIEW v_active_users AS SELECT * FROM users WHERE deleted_at IS NULL`
- 或用 ORM 的全局过滤器（如 Hibernate `@Where(clause = "deleted_at IS NULL")`）

### 6.5 反模式：过度外键

```sql
-- 反例：所有关联都建外键约束
FOREIGN KEY (user_id) REFERENCES users(id)
FOREIGN KEY (product_id) REFERENCES products(id)
FOREIGN KEY (category_id) REFERENCES categories(id)
```

**问题**：
- 写性能下降（每次写都校验）
- 分库分表时外键失效
- 数据迁移困难

**正确做法**：互联网项目通常不用外键约束，靠应用层保证一致性；金融等强一致场景可用。

### 6.6 反模式：时间字段用 VARCHAR

```sql
-- 反例
created_at VARCHAR(20)  -- '2025-07-27 10:00:00'
```

**问题**：失去时间运算能力（DATE_ADD、DATEDIFF）、排序错乱、占空间。

**正确做法**：用 DATETIME 或 TIMESTAMP

```sql
created_at DATETIME
```

### 6.7 反模式：金额用 FLOAT/DOUBLE

```sql
-- 反例
price FLOAT
total_amount DOUBLE
```

**问题**：浮点有精度损失，`0.1 + 0.2 = 0.30000000000000004`。

**正确做法**：用 DECIMAL

```sql
price DECIMAL(10,2)
total_amount DECIMAL(12,2)
```

### 6.8 反模式：表无注释、字段无注释

```sql
-- 反例
CREATE TABLE t1 (
    c1 INT,
    c2 VARCHAR(50),
    c3 DATETIME
);
```

**正确做法**：表与字段都加 COMMENT

```sql
CREATE TABLE user_account (
    id       BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id  INT NOT NULL COMMENT '用户ID',
    balance  DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '账户余额',
    version  INT NOT NULL DEFAULT 0 COMMENT '乐观锁版本号',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户账户表';
```

---

## 7. Code Review 检查清单

提交 SQL 变更时，逐项检查：

### 7.1 表结构

- [ ] 表名符合命名规范（小写下划线、单数）
- [ ] 有表级 COMMENT
- [ ] 使用 InnoDB 引擎
- [ ] 字符集 utf8mb4
- [ ] 有主键（推荐 BIGINT AUTO_INCREMENT）
- [ ] 含 created_at / updated_at
- [ ] 软删除场景含 deleted_at

### 7.2 字段

- [ ] 每个字段有 COMMENT
- [ ] 类型选择合理（金额用 DECIMAL、时间用 DATETIME）
- [ ] 避免NULL（用默认值）
- [ ] 长度按业务评估（不盲目 255）
- [ ] 枚举用 TINYINT + 注释 或 ENUM

### 7.3 索引

- [ ] 外键列建索引
- [ ] 高频查询列建索引
- [ ] 联合索引顺序合理（等值在前、范围在后）
- [ ] 无冗余索引
- [ ] 索引命名规范（idx_ / uk_）

### 7.4 SQL

- [ ] 避免 SELECT *（只查需要的列）
- [ ] WHERE 条件索引列不加函数
- [ ] 类型匹配（避免隐式转换）
- [ ] 大表分页用游标或延迟关联
- [ ] 子查询优先改 JOIN
- [ ] OR 改 UNION ALL
- [ ] 大事务拆小

### 7.5 安全

- [ ] 无 SQL 注入风险（参数化查询）
- [ ] 敏感字段加密存储（密码用 bcrypt）
- [ ] 不在日志打印敏感数据
- [ ] 应用账号最小权限

---

## 8. 参考资源

- [MySQL 8.0 官方文档 - Data Types](https://dev.mysql.com/doc/refman/8.0/en/data-types.html)
- [MySQL 8.0 官方文档 - CREATE TABLE](https://dev.mysql.com/doc/refman/8.0/en/create-table.html)
- [High Performance MySQL, 4th Edition](https://www.oreilly.com/library/view/high-performance-mysql/9781492077660/)
- [阿里 Java 开发手册（数据库篇）](https://github.com/alibaba/p3c)
- [美团 SQL 优化规范](https://tech.meituan.com/)

---

> **最后一句话**：好的设计让性能自然而来。多花一小时在设计上，能省十小时在优化上。
