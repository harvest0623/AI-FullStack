# Day10 - 索引与执行计划

> 索引是数据库性能优化的第一手段，看懂 EXPLAIN 是工程师的必备技能。当一张表的数据量从一万行涨到一千万行时，决定查询是 10 毫秒还是 10 秒的不是 SQL 写得多优雅，而是这条查询能否走上索引、走的是哪种索引、走了索引之后还要不要回表。本章从 B+Tree 的物理结构讲起，覆盖索引分类、最左前缀、覆盖索引、索引下推、EXPLAIN 字段全解与索引失效场景，把"看懂执行计划"这件事彻底打通。

---

## 目录

- [一、本章简介](#一本章简介)
- [二、学习目标](#二学习目标)
- [三、理论知识](#三理论知识)
  - [3.1 为什么需要索引](#31-为什么需要索引)
  - [3.2 B+Tree 索引原理](#32-btree-索引原理)
  - [3.3 聚簇索引 vs 二级索引](#33-聚簇索引-vs-二级索引)
  - [3.4 索引类型全景](#34-索引类型全景)
  - [3.5 创建与删除索引](#35-创建与删除索引)
  - [3.6 EXPLAIN 执行计划字段详解](#36-explain-执行计划字段详解)
  - [3.7 最左前缀原则](#37-最左前缀原则)
  - [3.8 索引失效场景](#38-索引失效场景)
  - [3.9 覆盖索引与回表](#39-覆盖索引与回表)
  - [3.10 索引下推 ICP](#310-索引下推-icp)
  - [3.11 索引设计原则](#311-索引设计原则)
- [四、代码文件说明](#四代码文件说明)
- [五、关键知识点总结](#五关键知识点总结)
- [六、实战练习](#六实战练习)

---

## 一、本章简介

写过业务代码的人大多经历过这样的场景：本地开发时查询秒回，上了生产突然慢到超时；DBA 给你甩过来一张 EXPLAIN 截图，说"这条 SQL 全表扫描了，加个索引"。然后你照着网上的文章 `CREATE INDEX idx_xxx ON tbl(col)`，速度确实上来了，但说不清为什么上来了，也说不清下一次为什么又慢了。

索引这件事的难点不在于"加索引"这个动作，而在于：

1. **理解索引的物理形态**——它不是一张表，而是 B+Tree 这种数据结构，理解结构才能理解为什么范围查询友好、为什么最左前缀成立。
2. **看懂 EXPLAIN**——这是 MySQL 给你的"诊断报告"，`type`、`key`、`key_len`、`Extra` 四个字段浓缩了优化器的全部决策。
3. **判断索引是否被命中**——同样一个 `WHERE`，写法不同可能走索引也可能不走，背后是函数包裹、隐式转换、OR 短路等一系列坑。
4. **设计而非堆砌**——索引不是越多越好，每多一个索引就多一份 B+Tree 维护成本，写性能随之下降。

本章按照"原理 → 类型 → 语法 → 执行计划 → 失效场景 → 设计原则"的顺序展开，所有演示基于 `ecommerce` 库，配套三个 SQL 脚本可在 MySQL 8.0+ 直接 `source` 执行。

---

## 二、学习目标

完成本章后，你应当能够：

1. **解释 B+Tree 为何被 MySQL 选中**：能从叶子节点链表、磁盘 IO 次数、范围查询友好三个角度对比 B+Tree 与 B 树、Hash、红黑树。
2. **区分聚簇索引与二级索引**：知道 InnoDB 的主键索引就是数据本身，二级索引的叶子节点存的是主键值，理解"回表"的代价。
3. **列举七种索引类型并说明适用场景**：主键 / 唯一 / 普通 / 联合 / 全文 / 前缀 / 函数索引（外加不可见索引）。
4. **用三种语法创建/删除索引**：`CREATE INDEX`、`ALTER TABLE ... ADD INDEX`、`DROP INDEX`，并知道 `USING BTREE` 的默认值。
5. **逐字段解读 EXPLAIN 输出**：`id`、`select_type`、`table`、`type`、`possible_keys`、`key`、`key_len`、`ref`、`rows`、`filtered`、`Extra` 共 11 个字段。
6. **判断 `type` 字段的优劣**：能背出 `system > const > eq_ref > ref > range > index > ALL` 的优劣序，并知道 `ALL` 是全表扫描必须优化。
7. **识别 `Extra` 的告警信号**：`Using filesort` 与 `Using temporary` 出现时要警惕，`Using index` 是覆盖索引的好信号。
8. **应用最左前缀原则**：给定联合索引 `(a,b,c)`，能立即判断 `WHERE b=?` / `WHERE a=? AND c=?` / `WHERE a=? AND b>?` 各能用到几列。
9. **列举至少六种索引失效场景**：函数包裹列、隐式类型转换、`LIKE '%xxx'`、OR 短路、`!=`、`IS NOT NULL`、数据类型不匹配。
10. **解释覆盖索引与索引下推 ICP**：知道 `Using index` 为何避免回表，知道 ICP 如何把过滤条件下推到存储引擎层减少回表次数。
11. **为一张真实业务表设计索引**：能根据区分度、排序分组需求、写性能取舍，给出合理的联合索引方案。

---

## 三、理论知识

### 3.1 为什么需要索引

**全表扫描 vs 索引查找**

假设 `products` 表有 1000 万行，我们要查 `name = 'iPhone 15 Pro'`：

- **无索引**：MySQL 只能从第一行扫到最后一行，逐行比较 `name` 字段。1000 万次磁盘 IO，耗时秒级起步。
- **有索引**：MySQL 在 B+Tree 上走一次树形查找，约 3~4 次磁盘 IO（树高 3~4 层）即可定位到叶子节点，再通过主键回表取数据，毫秒级返回。

**类比书的目录**

索引就是数据库的"目录"。一本 1000 页的技术书，要找"索引"这个概念：

- 没目录：从第 1 页翻到第 1000 页。
- 有目录：在目录里查到"索引"在第 387 页，直接翻过去。

索引的代价：

| 代价 | 说明 |
|------|------|
| 空间 | 每个索引是一棵独立的 B+Tree，占额外磁盘空间 |
| 写性能 | INSERT / UPDATE / DELETE 需同步维护索引树，写变慢 |
| 优化器选择成本 | 索引越多，优化器选择执行计划的代价越高 |

所以索引是**用空间换时间、用读性能换写性能**的权衡，不是越多越好。

---

### 3.2 B+Tree 索引原理

**B+树结构**

InnoDB 的索引采用 B+Tree（B 加树，不是 B 减树）。其核心特征：

```
                    [10 | 20 | 30]              ← 根节点（非叶子，只存键值用于路由）
                   /     |      |     \
              [1|5]  [10|15]  [20|25]  [30|35]   ← 中间节点（非叶子）
              /  \    /  \    /  \    /  \
           叶子  叶子 叶子 叶子 叶子 叶子 叶子 叶子  ← 叶子节点（存数据 + 主键）
             ↔    ↔    ↔    ↔    ↔    ↔    ↔    ← 双向链表
```

| 节点类型 | 存储内容 | 作用 |
|---------|---------|------|
| 根节点（root） | 键值 + 子节点指针 | 查找入口，常驻内存 |
| 中间节点 | 键值 + 子节点指针 | 路由分层 |
| 叶子节点 | 完整数据行（聚簇）或主键值（二级） | 实际数据存储 |
| 叶子间链表 | 前驱/后继指针 | 范围查询顺时针扫描 |

**B+Tree 的四大优势**

1. **叶子节点存数据，非叶子节点只存键值**：单个非叶子节点能容纳更多键值，树更矮。1000 万行的表，B+Tree 树高通常只有 3~4 层，意味着定位一行只需 3~4 次磁盘 IO。
2. **叶子节点形成双向链表**：范围查询 `WHERE id BETWEEN 100 AND 200` 只需定位到 id=100 的叶子节点，然后沿链表顺时针扫描到 id=200 即可，无需回根节点重走。
3. **数据天然有序**：插入时按顺序落到叶子节点，适合 `ORDER BY`、`GROUP BY`、`DISTINCT`。
4. **查询性能稳定**：任何一次查询都要走到叶子节点，路径长度相同，性能可预测。

**为什么 MySQL 选 B+Tree（vs B树 / Hash / 红黑树）**

| 数据结构 | 范围查询 | 磁盘 IO | 适用场景 | 为何 InnoDB 不用 |
|---------|---------|---------|---------|------------------|
| **B+Tree** | 极友好（叶子链表） | 少（树矮） | 通用 OLTP | ✅ 选它 |
| B Tree | 不友好（数据散落各节点） | 多（树高） | 早期文件系统 | 范围查询差、单节点数据少导致树更高 |
| Hash | 不支持 | 1 次（O(1)） | 等值查询（MEMORY 引擎） | 不支持范围、排序、模糊匹配 |
| 红黑树 | 不友好 | 多（树高 = log₂N，比 B+Tree 高得多） | 内存数据结构 | 树太高，磁盘 IO 次数多 |

B+Tree 是磁盘友好的数据结构：**用"矮胖"的形态把磁盘 IO 次数压到常数级**。

---

### 3.3 聚簇索引 vs 二级索引

**聚簇索引（Clustered Index）**

InnoDB 的聚簇索引把**索引和数据行存在同一棵 B+Tree**——叶子节点直接存完整数据行。一张表只能有一个聚簇索引，默认是主键。

```
聚簇索引（主键 id）
                [10 | 20]
               /          \
         [1|5|8]         [10|15|18]      ← 非叶子节点存主键值
         /  |  \         /  |  \
       叶子 叶子 叶子    叶子 叶子 叶子
        ↓   ↓   ↓        ↓   ↓   ↓
       [id=1, 完整行] [id=10, 完整行]    ← 叶子节点 = 真实数据行
```

**二级索引（Secondary Index）**

非主键索引都是二级索引。叶子节点**不存完整数据行，只存索引列值 + 主键值**。查到主键后还要再回聚簇索引取数据，这就是"回表"。

```
二级索引 idx_name（在 name 列上）
            ['iPhone' | 'Xiaomi']
           /                    \
      ['Honor']              ['OPPO']        ← 非叶子节点存 name 值
       /      \               /     \
    叶子     叶子           叶子    叶子
     ↓        ↓              ↓       ↓
  [name='Honor', id=3]  [name='OPPO', id=7]  ← 叶子节点 = (索引列, 主键值)
                                                  要取完整行？拿 id 回聚簇索引查
```

**对比表**

| 维度 | 聚簇索引 | 二级索引 |
|------|---------|---------|
| 数量 | 每表 1 个 | 可多个 |
| 叶子节点存什么 | 完整数据行 | 索引列值 + 主键值 |
| 默认按什么建 | 主键（无主键则用唯一非空索引，再无则隐藏 ROWID） | 用户指定列 |
| 查询是否需要回表 | 不需要 | 通常需要（除非覆盖索引） |
| 插入顺序影响 | 按主键顺序插入最快（顺序 IO） | 影响小 |
| 二级索引大小 | — | 通常比聚簇索引小（叶子节点紧凑） |

**为什么主键推荐用自增 INT/BIGINT**

聚簇索引按主键有序组织。若主键是 UUID 这种无序字符串，每次插入都落到 B+Tree 中间位置，导致**页分裂**（page split）：原叶子页满了，要拆成两页，写放大严重。自增主键永远追加到末尾，顺序写，性能最佳。

---

### 3.4 索引类型全景

| 索引类型 | 关键字 | 特点 | 典型场景 |
|---------|--------|------|---------|
| 主键索引 | `PRIMARY KEY` | 聚簇索引、唯一、非空、每表 1 个 | `users.id` |
| 唯一索引 | `UNIQUE` | 值唯一，允许 NULL，可有多个 | `users.email` |
| 普通索引 | `INDEX` / `KEY` | 仅加速查询，无约束 | `products.name` |
| 联合索引 | `INDEX(a, b, c)` | 多列组合，遵循最左前缀 | `(category_id, status, price)` |
| 全文索引 | `FULLTEXT` | 倒排索引，MATCH AGAINST 检索 | 文章正文、商品描述 |
| 前缀索引 | `INDEX(col(10))` | 对字符串前 N 字符建索引 | 长 VARCHAR 节省空间 |
| 函数索引 | `INDEX((EXPR))` | MySQL 8.0+，对表达式建索引 | `WHERE LOWER(email)=?` |
| 不可见索引 | `INVISIBLE` | 8.0+，优化器忽略，调试用 | 上线前验证索引移除影响 |

**详解每种类型**

**① 主键索引（PRIMARY KEY）**

```sql
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  ...
);
-- 或建表后追加
ALTER TABLE users ADD PRIMARY KEY (id);
```

InnoDB 中主键即聚簇索引。没有显式主键时，InnoDB 会选第一个所有列都 NOT NULL 的 UNIQUE 索引；都没有就用隐藏的 6 字节 `DB_ROW_ID` 建聚簇索引（这个隐藏列对你不可见）。

**② 唯一索引（UNIQUE）**

```sql
CREATE UNIQUE INDEX uk_email ON users(email);
-- 或
ALTER TABLE users ADD UNIQUE KEY uk_email (email);
```

唯一索引除了加速查询，还强制列值唯一（NULL 除外，允许多个 NULL）。`INSERT` 重复值会报错 `Duplicate entry`。

**③ 普通索引（INDEX / KEY）**

```sql
CREATE INDEX idx_name ON products(name);
-- KEY 是 INDEX 的同义词
ALTER TABLE products ADD KEY idx_name (name);
```

最朴素的索引，无约束，只加速查询。

**④ 联合索引（Composite Index）**

```sql
CREATE INDEX idx_cat_status_price ON products(category_id, status, price);
```

多列组合成一个 B+Tree，排序规则是"先按第一列排，相同再按第二列排，以此类推"。能命中几列取决于**最左前缀原则**（详见 3.7）。

**⑤ 全文索引（FULLTEXT）**

```sql
CREATE FULLTEXT INDEX ft_name_desc ON products(name, description);

-- 使用 MATCH AGAINST 查询
SELECT * FROM products
WHERE MATCH(name, description) AGAINST('iPhone 电池' IN NATURAL LANGUAGE MODE);
```

底层是**倒排索引**（inverted index），分词后记录每个词出现在哪些行。适合长文本检索，比 `LIKE '%xxx%'` 高效得多。中文需配合 `ngram` 分词器：

```sql
-- 建表时指定分词器
CREATE TABLE articles (
  id BIGINT PRIMARY KEY,
  content TEXT,
  FULLTEXT KEY ft_content (content) WITH PARSER ngram
);
```

**⑥ 前缀索引**

```sql
-- 对 email 前 10 个字符建索引
CREATE INDEX idx_email_prefix ON users(email(10));
```

长字符串（如 VARCHAR(255)）整列建索引浪费空间。前缀索引只索引前 N 个字符，节省空间，但**不支持覆盖索引**（无法用前缀索引完全避免回表，因为无法判断剩余字符是否真的匹配）。

前缀长度选择：选择区分度接近全列的长度。

```sql
-- 计算不同前缀长度的区分度
SELECT
  COUNT(DISTINCT LEFT(email, 5))  / COUNT(*) AS sel_5,
  COUNT(DISTINCT LEFT(email, 7))  / COUNT(*) AS sel_7,
  COUNT(DISTINCT LEFT(email, 10)) / COUNT(*) AS sel_10,
  COUNT(DISTINCT email)           / COUNT(*) AS sel_full
FROM users;
-- 选择 sel 接近 sel_full 的最小长度
```

**⑦ 函数索引（MySQL 8.0+）**

```sql
-- 对表达式建索引
CREATE INDEX idx_lower_email ON users((LOWER(email)));

-- 此后该查询能命中索引
SELECT * FROM users WHERE LOWER(email) = 'alice@example.com';
```

函数索引专门解决"函数包裹列导致索引失效"问题。也可以用于 JSON 路径表达式：

```sql
CREATE INDEX idx_data_age ON users((CAST(data->'$.age' AS UNSIGNED)));
```

**⑧ 不可见索引（Invisible Index，8.0+）**

```sql
-- 让索引对优化器不可见（但仍维护）
ALTER TABLE products ALTER INDEX idx_name SET INVISIBLE;

-- 优化器不再选它，EXPLAIN 验证
EXPLAIN SELECT * FROM products WHERE name = 'iPhone';

-- 验证无影响后真正删除
ALTER TABLE products DROP INDEX idx_name;

-- 或恢复可见
ALTER TABLE products ALTER INDEX idx_name SET VISIBLE;
```

不可见索引是"删除索引前的灰度验证"——让索引暂时失效，观察业务是否真的不需要它，避免误删导致线上故障。

---

### 3.5 创建与删除索引

**三种创建方式**

```sql
-- 方式一：CREATE INDEX（最常用）
CREATE [UNIQUE | FULLTEXT] INDEX idx_name ON tbl(col) [USING BTREE];

-- 方式二：ALTER TABLE ADD INDEX
ALTER TABLE tbl ADD [INDEX | UNIQUE | KEY] idx_name (col);

-- 方式三：建表时直接声明
CREATE TABLE tbl (
  id BIGINT PRIMARY KEY,
  name VARCHAR(100),
  INDEX idx_name (name)
);
```

**删除索引**

```sql
-- 方式一
DROP INDEX idx_name ON tbl;

-- 方式二
ALTER TABLE tbl DROP INDEX idx_name;
```

**查看索引**

```sql
SHOW INDEX FROM products;        -- 列出表所有索引
SHOW CREATE TABLE products\G     -- 看建表语句含索引定义
```

`SHOW INDEX` 关键列：

| 列 | 含义 |
|----|------|
| `Table` | 表名 |
| `Non_unique` | 0=唯一索引，1=非唯一 |
| `Key_name` | 索引名（PRIMARY 即主键） |
| `Seq_in_index` | 该列在联合索引中的位置（1=第一列） |
| `Column_name` | 列名 |
| `Collation` | A=升序，NULL=降序或非排序 |
| `Cardinality` | 区分度估算值（越大越好） |
| `Index_type` | BTREE / FULLTEXT / HASH |

**USING BTREE 说明**

```sql
CREATE INDEX idx_name ON products(name) USING BTREE;
```

InnoDB 默认就是 BTREE，可省略。MEMORY 引擎支持 HASH，但 InnoDB 内部"自适应哈希索引"由引擎自动管理，无需手动指定 HASH。

---

### 3.6 EXPLAIN 执行计划字段详解

`EXPLAIN` 是 MySQL 优化器给出的"执行计划说明书"。用法：

```sql
EXPLAIN SELECT * FROM products WHERE category_id = 5;
-- 或更详细（含 warning 显示优化器改写后的 SQL）
EXPLAIN FORMAT=TREE SELECT * FROM products WHERE category_id = 5;
```

输出字段（共 12 列）：

| 字段 | 含义 | 重要性 |
|------|------|--------|
| `id` | 查询序号 | 中 |
| `select_type` | 查询类型 | 中 |
| `table` | 表名 | 低 |
| `partitions` | 分区（无分区时为 NULL） | 低 |
| `type` | 访问类型 | **高** |
| `possible_keys` | 可能用到的索引 | 中 |
| `key` | 实际用到的索引 | **高** |
| `key_len` | 索引使用的字节数 | **高** |
| `ref` | 索引比较的列或常量 | 中 |
| `rows` | 预估扫描行数 | **高** |
| `filtered` | 过滤后剩余比例（百分比） | 中 |
| `Extra` | 额外信息 | **高** |

**逐字段详解**

**① id（查询序号）**

- `id` 相同：从上往下顺序执行（一组联表查询）。
- `id` 不同：`id` 越大越先执行（子查询先于外层）。
- `id` 为 NULL：通常是 UNION 临时表或 DERIVED 派生表。

```
EXPLAIN SELECT * FROM orders WHERE user_id =
  (SELECT id FROM users WHERE email = 'a@b.com');
-- 外层 orders 的 id=1，子查询 users 的 id=2，先执行 id=2
```

**② select_type（查询类型）**

| 值 | 含义 |
|----|------|
| `SIMPLE` | 简单查询，无子查询/UNION |
| `PRIMARY` | 复杂查询的最外层 |
| `SUBQUERY` | 子查询中的第一个 SELECT |
| `DERIVED` | 派生表（FROM 子句的子查询） |
| `UNION` | UNION 中的第二个及之后 SELECT |
| `UNION RESULT` | UNION 的临时结果表 |
| `DEPENDENT SUBQUERY` | 依赖外层的子查询（相关子查询） |

**③ table（表名）**

显示当前行涉及哪张表。派生表会显示 `<derivedN>`，UNION 结果显示 `<union1,2>`。

**④ type（访问类型，最重要）**

按性能从好到差排序：

| type | 含义 | 触发条件 | 评级 |
|------|------|---------|------|
| `system` | 表只有一行（系统表） | `SELECT * FROM mysql.proxies_priv` | 极好 |
| `const` | 通过主键或唯一索引等值查询，最多返回 1 行 | `WHERE id=1` 或 `WHERE email='x'`（email 唯一） | 极好 |
| `eq_ref` | 联表时被驱动表用主键或唯一索引等值匹配 | `JOIN ON a.id=b.id` | 极好 |
| `ref` | 通过普通索引等值查询，可能多行 | `WHERE category_id=5`（有索引） | 好 |
| `range` | 索引范围扫描 | `BETWEEN`、`>`、`<`、`IN` | 较好 |
| `index` | 扫描整棵索引树（不回表） | `SELECT COUNT(*)` 或只查索引列 | 一般 |
| `ALL` | 全表扫描 | 无索引或索引失效 | **差，必优化** |

**评判标准**：至少要达到 `range` 级别，`ref` 及以上为佳，`ALL` 必须优化。

**⑤ possible_keys（可能用到的索引）**

优化器认为"理论上"可以走的索引列表。可能为 NULL（无可用索引）。

**⑥ key（实际用到的索引）**

优化器最终选择的索引。可能不在 `possible_keys` 里（优化器有覆盖索引优化）。若为 NULL 表示没用索引（全表扫描）。

**⑦ key_len（索引使用的字节数）**

**判断联合索引用了几列的关键字段**。计算规则：

| 类型 | 字节数 |
|------|--------|
| TINYINT | 1 |
| SMALLINT | 2 |
| INT | 4 |
| BIGINT | 8 |
| CHAR(N) utf8mb4 | 4N |
| VARCHAR(N) utf8mb4 | 4N + 2（长度标记） |
| DATE | 3 |
| DATETIME | 5（8.0） |
| TIMESTAMP | 4 |

若列允许 NULL，额外 +1 字节（NULL 标记）。

例：联合索引 `idx(cat_id, status, price)`，列定义为 `category_id INT NOT NULL, status VARCHAR(20) NOT NULL, price DECIMAL(10,2)`：

- 只用 `category_id`：key_len = 4
- 用 `category_id + status`：key_len = 4 + (4×20+2) = 86
- 用 `category_id + status + price`：key_len = 4 + 82 + 5 = 91

**⑧ ref（索引比较的列）**

显示哪个列或常量与 `key` 列比较。常见值：`const`（常量）、`db.tbl.col`（联表列）、`func`（函数结果）。

**⑨ rows（预估扫描行数）**

优化器基于统计信息估算的"需要扫描的行数"。**注意是扫描行数，不是结果行数**。越接近结果集大小越好。

**⑩ filtered（过滤比例）**

扫描 `rows` 行后，经过 WHERE 过滤后剩余的百分比。100% 表示扫描的行全部命中，10% 表示 90% 是无效扫描。`rows × filtered / 100` 才是真正的结果估算。

**⑪ Extra（额外信息，极重要）**

| 值 | 含义 | 是否需优化 |
|----|------|-----------|
| `Using index` | 覆盖索引，不回表 | ✅ 好 |
| `Using where` | 用 WHERE 过滤（通常配合回表） | 正常 |
| `Using index condition` | 索引下推 ICP | 较好 |
| `Using filesort` | 额外排序（无法用索引顺序） | ⚠️ 优化 |
| `Using temporary` | 用临时表（GROUP BY / DISTINCT 常见） | ⚠️ 优化 |
| `Using join buffer` | 联表无索引用 Block Nested Loop | ⚠️ 优化 |
| `Using MRR` | 多范围读优化 | 好 |
| `Impossible WHERE` | WHERE 恒假（如 `1=0`） | 检查 SQL |
| `No tables used` | 无 FROM 子句 | 正常 |

`Using filesort` 与 `Using temporary` 出现任一时都要警惕，尤其是大数据量场景。

---

### 3.7 最左前缀原则

**联合索引的存储顺序**

联合索引 `(a, b, c)` 在 B+Tree 中按 `a → b → c` 字典序排序：

```
(a=1,b=1,c=1) (a=1,b=1,c=2) (a=1,b=2,c=1) (a=1,b=2,c=5)
(a=2,b=1,c=1) (a=2,b=1,c=3) (a=2,b=3,c=2) (a=3,b=1,c=1)
```

**最左前缀原则**

联合索引能从最左列开始连续命中。遇到范围查询（`>`、`<`、`BETWEEN`、`LIKE 'x%'`）后停止匹配后续列。

给定 `INDEX(a, b, c)`：

| 查询条件 | 能否命中索引 | 命中几列 | 说明 |
|---------|-------------|---------|------|
| `WHERE a=?` | ✅ | 1 列 | 最左列直接命中 |
| `WHERE a=? AND b=?` | ✅ | 2 列 | 连续命中 |
| `WHERE a=? AND b=? AND c=?` | ✅ | 3 列 | 全命中 |
| `WHERE a=? AND c=?` | ✅ | 1 列 | 跳过 b，c 无法用索引（但 ICP 可下推 c） |
| `WHERE b=?` | ❌ | 0 列 | 缺最左列 a |
| `WHERE b=? AND c=?` | ❌ | 0 列 | 缺最左列 a |
| `WHERE c=?` | ❌ | 0 列 | 缺最左列 a |
| `WHERE a=? AND b>?` | ✅ | 2 列（a 等值 + b 范围） | b 走范围，c 无法命中 |
| `WHERE a=? AND b>? AND c=?` | ✅ | 2 列 | b 是范围，c 无法命中索引（除非 ICP） |
| `WHERE a=? AND b IN (...)` | ✅ | 2 列 | IN 在 8.0+ 多次优化下视为多个等值 |
| `WHERE a=? AND b=? ORDER BY c` | ✅ | 2 列 + 排序免 filesort | a、b 等值后数据已按 c 排序 |

**索引列顺序选择原则**

1. **等值查询列在前，范围查询列在后**：范围查询之后的列无法走索引。
2. **区分度高的列在前**：能快速缩小扫描范围。但若区分度差不多，优先把等值查询的列放前面。
3. **排序分组列优先**：`ORDER BY`、`GROUP BY` 的列若在联合索引中且顺序一致，可免 filesort。

反例：`WHERE status=? AND created_at>?`，若建 `(status, created_at)` 则完美命中；若建 `(created_at, status)` 则 `created_at` 范围查询后 `status` 无法走索引。

---

### 3.8 索引失效场景

**① 函数包裹列**

```sql
-- 索引失效
WHERE YEAR(created_at) = 2024
WHERE LOWER(email) = 'a@b.com'
WHERE LEFT(name, 3) = 'iPhone'

-- 改写为可走索引的形式
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'
WHERE email = 'a@b.com'                    -- 应用层保证大小写
WHERE name LIKE 'iPhone%'
```

或用函数索引：`CREATE INDEX idx_year ON orders((YEAR(created_at)));`

**② 隐式类型转换**

```sql
-- products.category_id 是 INT，传字符串导致隐式转换，索引失效
WHERE category_id = '5'        -- 字符串 → 函数 CAST，索引失效

-- 正确写法
WHERE category_id = 5          -- 类型匹配，走索引
```

**③ LIKE 前导通配符**

```sql
WHERE name LIKE '%iPhone%'     -- 左模糊，索引失效
WHERE name LIKE 'iPhone%'      -- 右模糊，可走索引（最左前缀）
WHERE name LIKE '%iPhone'      -- 左模糊，索引失效
```

解决全文检索用 FULLTEXT 索引或 ES。

**④ OR 条件短路**

```sql
-- 若 name 有索引而 status 无索引，OR 导致整体不走索引
WHERE name = 'iPhone' OR status = 'on_sale'

-- 改写为 UNION ALL
SELECT * FROM products WHERE name = 'iPhone'
UNION ALL
SELECT * FROM products WHERE status = 'on_sale' AND name <> 'iPhone';
```

若 OR 两侧列都有索引，MySQL 8.0+ 可用 Index Merge 优化。

**⑤ != / <> / NOT IN**

```sql
WHERE status != 'draft'        -- 通常不走索引（扫描范围太大）
WHERE status NOT IN ('draft','off_sale')
```

`!=` 命中行数可能超过全表 50%，优化器会判断走索引还不如全表扫描。

**⑥ IS NOT NULL**

```sql
WHERE deleted_at IS NOT NULL   -- 通常不走索引
WHERE deleted_at IS NULL       -- 通常可走索引（若 NULL 占少数）
```

**⑦ 数据类型不匹配**

```sql
-- orders.status 是 ENUM/VARCHAR，传入数值
WHERE status = 1               -- 隐式转换，索引失效
WHERE status = 'paid'          -- 类型一致，走索引
```

**⑧ 字符集不一致**

联表时两表字符集不同（如 utf8 与 utf8mb4）会导致索引失效，走 Block Nested Loop。统一字符集可解决。

**⑨ 优化器认为全表扫描更快**

数据量很小（如几百行）或索引区分度极低（如 `status` 只有 2 个值），优化器可能主动放弃索引。可用 `FORCE INDEX(idx_name)` 强制：

```sql
SELECT * FROM products FORCE INDEX(idx_name) WHERE name = 'iPhone';
```

---

### 3.9 覆盖索引与回表

**回表（Table Lookup by Primary Key）**

二级索引的叶子节点只存"索引列 + 主键"。若查询需要其他列，必须拿主键回到聚簇索引取完整行，这个过程叫"回表"。

```sql
-- 假设 idx_name 在 name 列上
SELECT name, price, stock FROM products WHERE name = 'iPhone';

-- 执行流程：
-- 1. 在 idx_name 树上找到 name='iPhone' 的叶子节点 → 得到 id=10
-- 2. 回到聚簇索引（主键树）按 id=10 取完整行 → 得到 price、stock
-- 3. 返回结果
```

回表是随机 IO（主键值不连续），代价高。若查询要返回 1 万行，就要回表 1 万次。

**覆盖索引（Covering Index）**

若查询的列全部在索引中（包括主键），无需回表，直接从索引树返回数据。`Extra` 字段显示 `Using index`。

```sql
-- 联合索引 idx_name_status(name, status)
SELECT name, status FROM products WHERE name = 'iPhone';
-- Extra: Using index   ← 覆盖索引，不回表
```

**为什么 `SELECT *` 是反模式**

`SELECT *` 必然要返回所有列，二级索引无法覆盖，必然回表。业务中只查需要的列，能命中覆盖索引就命中。

---

### 3.10 索引下推 ICP

**Index Condition Pushdown（5.6+）**

在没有 ICP 之前，存储引擎按索引取出所有满足"最左前缀"的行，回表后由 Server 层用 WHERE 的其余条件过滤。ICP 把"其余条件"下推到存储引擎层，在索引上先过滤，减少回表次数。

**示例**

联合索引 `idx(name, status)`，查询：

```sql
SELECT * FROM products WHERE name LIKE 'iPhone%' AND status = 'on_sale';
```

- **无 ICP**：存储引擎按 `name LIKE 'iPhone%'` 取出所有 iPhone 开头的行（可能 100 行），逐行回表取完整数据，Server 层再用 `status='on_sale'` 过滤（剩 10 行）。
- **有 ICP**：存储引擎取出 iPhone 开头的行后，先在索引上用 `status='on_sale'` 过滤（剩 10 行），只对这 10 行回表。

`Extra` 显示 `Using index condition`。

**ICP 适用条件**

- 联合索引中"最左前缀"用尽后还有剩余列可用于过滤。
- 剩余列不能用于索引查找（如范围查询后的列），但可以用于条件判断。

---

### 3.11 索引设计原则

**该不该建索引**

| 场景 | 建议 |
|------|------|
| 频繁出现在 WHERE 中的列 | ✅ 建 |
| 频繁出现在 ORDER BY / GROUP BY 中的列 | ✅ 建 |
| 联表 JOIN 的连接列 | ✅ 建 |
| 区分度极低（如 status 只有 2 值） | ❌ 不建，性价比低 |
| 频繁更新的列 | ⚠️ 慎建，写性能影响大 |
| 大字段（TEXT/BLOB） | ❌ 不建，用前缀索引 |
| 数据量很小（<1000 行） | ❌ 不建，全表扫描够快 |

**联合索引设计顺序**

1. 等值查询的列放前面
2. 区分度高的列放前面（在等值前提下）
3. 范围查询的列放最后
4. 排序/分组的列尽量纳入索引

**避免过度索引**

- 单表索引数量建议不超过 5~6 个。
- 联合索引列数建议不超过 5 列。
- 重复索引（如已有 `(a,b)` 又建 `(a)`）应删除。
- 长期不用的索引应删除（可用 `sys.schema_unused_indexes` 查看）。

**索引命名规范**

| 前缀 | 含义 | 示例 |
|------|------|------|
| `pk_` | 主键 | `pk_users` |
| `uk_` | 唯一索引 | `uk_email` |
| `idx_` | 普通索引 | `idx_name` |
| `ft_` | 全文索引 | `ft_content` |

---

## 四、代码文件说明

本章配套三个 SQL 脚本，均位于 `Code/` 目录下，可在 MySQL 8.0+ 直接 `source` 执行：

| 文件 | 内容 | 关键演示 |
|------|------|---------|
| `01-create-index.sql` | 为 ecommerce 各表创建索引 | 主键/唯一/普通/联合/前缀索引，对比建索引前后 EXPLAIN |
| `02-explain-examples.sql` | EXPLAIN 各字段演示 | 构造 const/ref/range/index/ALL 等 type，演示 Using index / Using filesort / Using temporary |
| `03-index-failure.sql` | 索引失效场景演示 | 函数包裹、隐式转换、LIKE 前导%、OR、!= 等，用 EXPLAIN 对比 |

**执行顺序建议**：先 `01` 建好索引，再 `02` 看 EXPLAIN 演示（依赖索引存在），最后 `03` 看失效场景。

**前置依赖**：本脚本假设 `ecommerce` 库及 7 张表已存在（Day02-Day04 创建）。若尚未建库，请先执行 Day02 的 `01-create-ecommerce.sql` 与 Day04 的 `01-insert-data.sql`。

---

## 五、关键知识点总结

### EXPLAIN `type` 速查表

| type | 性能 | 触发场景 | 优化建议 |
|------|------|---------|---------|
| `system` | ⭐⭐⭐⭐⭐ | 系统表单行 | — |
| `const` | ⭐⭐⭐⭐⭐ | 主键/唯一索引等值 | — |
| `eq_ref` | ⭐⭐⭐⭐⭐ | JOIN 用主键/唯一索引等值 | — |
| `ref` | ⭐⭐⭐⭐ | 普通索引等值 | — |
| `range` | ⭐⭐⭐ | 索引范围（BETWEEN/>/IN） | — |
| `index` | ⭐⭐ | 全索引扫描 | 检查是否可用范围 |
| `ALL` | ⭐ | 全表扫描 | **必加索引** |

### EXPLAIN `Extra` 速查表

| Extra | 含义 | 是否需优化 |
|-------|------|-----------|
| `Using index` | 覆盖索引 | ✅ 理想 |
| `Using index condition` | 索引下推 ICP | ✅ 较好 |
| `Using where` | Server 层过滤 | 正常 |
| `Using filesort` | 额外排序 | ⚠️ 排序列加索引 |
| `Using temporary` | 临时表 | ⚠️ GROUP BY 列加索引 |
| `Using join buffer` | 无索引联表 | ⚠️ JOIN 列加索引 |
| `Impossible WHERE` | WHERE 恒假 | 检查 SQL |

### 索引失效清单

| # | 场景 | 示例 | 解决 |
|---|------|------|------|
| 1 | 函数包裹列 | `YEAR(created_at)=2024` | 改写为范围 / 函数索引 |
| 2 | 隐式类型转换 | `category_id='5'`（列是 INT） | 类型匹配 |
| 3 | LIKE 左模糊 | `LIKE '%iPhone'` | 改右模糊 / FULLTEXT |
| 4 | OR 短路 | `name=? OR status=?`（status 无索引） | UNION 改写 / 补索引 |
| 5 | != / <> | `status != 'draft'` | 改 IN 列举正向值 |
| 6 | IS NOT NULL | `deleted_at IS NOT NULL` | 难优化，业务规避 |
| 7 | 类型不匹配 | `status=1`（列是 VARCHAR） | 传字符串 `'1'` |
| 8 | 字符集不一致 | JOIN 时 utf8 vs utf8mb4 | 统一字符集 |
| 9 | 最左前缀缺失 | 索引(a,b) 查 `WHERE b=?` | 加索引(b) 或改查询 |
| 10 | 优化器主动放弃 | 数据量小或区分度低 | FORCE INDEX 强制 |

### 索引设计原则

1. **等值在前，范围在后**
2. **区分度高的列在前**
3. **排序分组列纳入索引**
4. **单表索引不超过 5~6 个**
5. **联合索引列数不超过 5 列**
6. **避免重复索引与冗余索引**
7. **长字符串用前缀索引**
8. **函数包裹列用函数索引（8.0+）**
9. **删除索引前先设 INVISIBLE 验证**
10. **定期用 `sys.schema_unused_indexes` 清理无用索引**

---

## 六、实战练习

### 练习一：为订单查询设计联合索引

**场景**：运营后台频繁执行以下查询，请设计合适的联合索引并验证。

```sql
-- 查询 A：某用户某时间段的已支付订单
SELECT id, total_amount, created_at
FROM orders
WHERE user_id = 100
  AND status = 'paid'
  AND created_at BETWEEN '2024-01-01' AND '2024-06-30'
ORDER BY created_at DESC;

-- 查询 B：按状态分页查所有订单
SELECT id, status, total_amount
FROM orders
WHERE status = 'paid'
ORDER BY created_at DESC
LIMIT 20;
```

**要求**：
1. 分析两个查询能否共用一个联合索引。
2. 写出索引创建语句。
3. 用 EXPLAIN 验证 `type`、`key`、`key_len`、`Extra`。
4. 思考：为什么查询 A 中 `status='paid'` 放在 `created_at` 范围之前？

### 练习二：诊断慢查询

**场景**：以下 SQL 在 1000 万行 products 表上慢到 8 秒，请诊断并优化。

```sql
SELECT name, price, LEFT(description, 50) AS short_desc
FROM products
WHERE category_id = 5
  AND status != 'draft'
  AND YEAR(created_at) = 2024
ORDER BY price DESC
LIMIT 20;
```

**要求**：
1. 用 EXPLAIN 分析，指出至少 3 个索引失效点。
2. 改写 SQL（不改业务语义）使其能走索引。
3. 设计合适的联合索引。
4. 给出优化后的 EXPLAIN 预期结果（type、key、Extra）。

### 练习三：覆盖索引实战

**场景**：商品列表页只需要展示名称、价格、库存，当前查询如下：

```sql
SELECT name, price, stock FROM products WHERE category_id = 5;
```

**要求**：
1. 设计一个让该查询命中覆盖索引的联合索引。
2. 用 EXPLAIN 验证 `Extra` 出现 `Using index`。
3. 对比 `SELECT *` 与 `SELECT name, price, stock` 的 EXPLAIN 差异（`Extra` 字段）。
4. 思考：为什么主键 `id` 不需要在联合索引中也能命中覆盖索引？

---

> 本章是性能优化的起点。下一章 Day11 我们进入事务与锁机制，理解 ACID 如何保证数据一致性，以及高并发下的并发控制策略。
