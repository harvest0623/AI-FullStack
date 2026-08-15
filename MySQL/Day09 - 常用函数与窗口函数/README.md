# Day09 - 常用函数与窗口函数

函数让 SQL 具备数据加工能力——从拼接字符串、格式化日期，到条件判断、类型转换，函数把"原始数据"加工成"业务可用信息"。而窗口函数（Window Function）是 MySQL 8.0 最重磅的特性之一，它能在不减少行数的前提下做"跨行计算"，让"分组排名""累计求和""取上下行"这类曾经需要子查询或自连接才能实现的需求变得极其简洁。本天系统讲解字符串、数值、日期、流程控制、类型转换、JSON 函数，并重点突破窗口函数。

## 学习目标

- 熟练使用字符串函数：CONCAT、LENGTH/CHAR_LENGTH、SUBSTRING、TRIM、REPLACE、UPPER/LOWER、LPAD/RPAD、SUBSTRING_INDEX 等
- 熟练使用数值函数：ROUND、CEIL、FLOOR、RAND、ABS、MOD、TRUNCATE 等
- 熟练使用日期时间函数：NOW、CURDATE、DATE_FORMAT、STR_TO_DATE、DATE_ADD/DATE_SUB、DATEDIFF、TIMESTAMPDIFF、LAST_DAY 等
- 掌握流程控制函数：IF、IFNULL、NULLIF、COALESCE、CASE WHEN（简单 CASE 与搜索 CASE）
- 掌握类型转换：CAST、CONVERT 及常见目标类型
- 了解 JSON 函数：JSON_EXTRACT(->)、JSON_UNQUOTE(->>)、JSON_OBJECT、JSON_ARRAY、JSON_CONTAINS
- **重点掌握窗口函数**：ROW_NUMBER、RANK、DENSE_RANK、NTILE、LAG、LEAD、聚合类窗口、FIRST_VALUE/LAST_VALUE、窗口框架
- 理解窗口函数与 GROUP BY 聚合的本质区别

---

## 理论知识讲解

### 1. 字符串函数

| 函数 | 作用 | 示例 |
|------|------|------|
| `CONCAT(s1, s2, ...)` | 拼接字符串，任一为 NULL 则结果 NULL | `CONCAT('a','b')` → `ab` |
| `CONCAT_WS(sep, s1, s2, ...)` | 用分隔符拼接，自动跳过 NULL | `CONCAT_WS('-','a',NULL,'b')` → `a-b` |
| `LENGTH(s)` | 字符串**字节数** | `LENGTH('中')` → 3（utf8mb4） |
| `CHAR_LENGTH(s)` | 字符串**字符数** | `CHAR_LENGTH('中')` → 1 |
| `SUBSTRING(s, pos, len)` / `SUBSTR` | 截取子串（pos 从 1 开始） | `SUBSTRING('hello',2,3)` → `ell` |
| `TRIM(s)` / `LTRIM` / `RTRIM` | 去两端/左/右空格 | `TRIM(' a ')` → `a` |
| `REPLACE(s, old, new)` | 替换所有匹配 | `REPLACE('a-b-c','-','_')` → `a_b_c` |
| `UPPER(s)` / `LOWER(s)` | 转大写/小写 | `UPPER('abc')` → `ABC` |
| `LEFT(s, n)` / `RIGHT(s, n)` | 从左/右取 n 个字符 | `LEFT('hello',2)` → `he` |
| `LPAD(s, len, pad)` / `RPAD` | 左/右填充到指定长度 | `LPAD('5',3,'0')` → `005` |
| `REPEAT(s, n)` | 重复 n 次 | `REPEAT('ab',2)` → `abab` |
| `REVERSE(s)` | 反转字符串 | `REVERSE('abc')` → `cba` |
| `LOCATE(sub, s)` / `INSTR(s, sub)` | 查找子串位置（从 1 开始，找不到为 0） | `LOCATE('l','hello')` → 3 |
| `SUBSTRING_INDEX(s, delim, count)` | 按分隔符取前 N 段 | `SUBSTRING_INDEX('a@b.com','@',1)` → `a` |

> **LENGTH vs CHAR_LENGTH**：中文等字符在 utf8mb4 下占 3~4 字节，故 `LENGTH('中文')` 可能是 6，而 `CHAR_LENGTH('中文')` 是 2。判断字符数用后者。

```sql
-- 拼接用户展示名：username (email)
SELECT CONCAT(username, ' (', email, ')') AS display FROM users LIMIT 3;

-- 用 LPAD 给订单号补零到 8 位
SELECT LPAD(id, 8, '0') AS order_no, total_amount FROM orders LIMIT 3;

-- SUBSTRING_INDEX 提取邮箱用户名部分
SELECT email, SUBSTRING_INDEX(email, '@', 1) AS email_user FROM users LIMIT 3;
```

### 2. 数值函数

| 函数 | 作用 | 示例 |
|------|------|------|
| `ROUND(x, d)` | 四舍五入到 d 位小数 | `ROUND(3.1415, 2)` → 3.14 |
| `CEIL(x)` / `CEILING(x)` | 向上取整 | `CEIL(3.1)` → 4 |
| `FLOOR(x)` | 向下取整 | `FLOOR(3.9)` → 3 |
| `RAND()` | 返回 0~1 随机浮点 | `RAND()` → 0.3724 |
| `ABS(x)` | 绝对值 | `ABS(-5)` → 5 |
| `MOD(n, m)` | 取余（等价 `n % m`） | `MOD(10, 3)` → 1 |
| `TRUNCATE(x, d)` | 截断到 d 位小数（不四舍五入） | `TRUNCATE(3.1415, 2)` → 3.14 |
| `SIGN(x)` | 符号（-1/0/1） | `SIGN(-5)` → -1 |
| `POWER(x, y)` | 幂运算 | `POWER(2, 10)` → 1024 |
| `SQRT(x)` | 平方根 | `SQRT(16)` → 4 |

```sql
-- 价格打 8 折后保留 2 位
SELECT name, ROUND(price * 0.8, 2) AS discount_price FROM products LIMIT 3;

-- 随机抽取 3 件商品
SELECT id, name FROM products ORDER BY RAND() LIMIT 3;
```

### 3. 日期时间函数

| 函数 | 作用 | 示例 |
|------|------|------|
| `NOW()` / `CURRENT_TIMESTAMP` | 当前日期时间 | `2026-07-27 14:30:00` |
| `CURDATE()` / `CURRENT_DATE` | 当前日期 | `2026-07-27` |
| `CURTIME()` | 当前时间 | `14:30:00` |
| `YEAR(d)` / `MONTH(d)` / `DAY(d)` | 取年/月/日 | `YEAR(NOW())` → 2026 |
| `DAYNAME(d)` | 星期英文名 | `DAYNAME(NOW())` → Monday |
| `DATE_FORMAT(d, fmt)` | 格式化日期 | `DATE_FORMAT(NOW(), '%Y-%m-%d')` |
| `STR_TO_DATE(s, fmt)` | 字符串转日期 | `STR_TO_DATE('2026-01-01','%Y-%m-%d')` |
| `DATE_ADD(d, INTERVAL n unit)` | 日期加 | `DATE_ADD(NOW(), INTERVAL 7 DAY)` |
| `DATE_SUB(d, INTERVAL n unit)` | 日期减 | `DATE_SUB(NOW(), INTERVAL 1 MONTH)` |
| `DATEDIFF(d1, d2)` | 相差天数（d1-d2） | `DATEDIFF('2026-07-27','2026-01-01')` |
| `TIMESTAMPDIFF(unit, d1, d2)` | 相差指定单位 | `TIMESTAMPDIFF(MONTH, d1, d2)` |
| `LAST_DAY(d)` | 当月最后一天 | `LAST_DAY('2026-02-10')` → 2026-02-28 |
| `UNIX_TIMESTAMP(d)` | 转时间戳 | `UNIX_TIMESTAMP(NOW())` |
| `FROM_UNIXTIME(ts)` | 时间戳转日期 | `FROM_UNIXTIME(1690000000)` |

**常用格式符**：`%Y` 年(4位)、`%m` 月(01-12)、`%d` 日、`%H` 时(24h)、`%i` 分、`%s` 秒、`%W` 星期名、`%j` 年内第几天。

```sql
-- 订单创建时间格式化为中文样式
SELECT id, DATE_FORMAT(created_at, '%Y年%m月%d日 %H:%i') AS 创建时间
FROM orders LIMIT 3;

-- 7 天前到现在的订单
SELECT COUNT(*) FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY);

-- 订单距今多少天
SELECT id, DATEDIFF(NOW(), created_at) AS 距今天数 FROM orders LIMIT 3;
```

### 4. 流程控制函数

| 函数 | 作用 | 示例 |
|------|------|------|
| `IF(expr, a, b)` | expr 为真返回 a，否则 b | `IF(price>100,'贵','平')` |
| `IFNULL(a, b)` | a 为 NULL 返回 b，否则 a | `IFNULL(email,'未填')` |
| `NULLIF(a, b)` | a=b 返回 NULL，否则 a | `NULLIF(score, 0)` |
| `COALESCE(a, b, c, ...)` | 返回第一个非 NULL 值 | `COALESCE(nickname, email, '匿名')` |
| `CASE WHEN ... THEN ... ELSE ... END` | 多条件分支 | 见下 |

**CASE WHEN 两种形式**：

```sql
-- 搜索 CASE（推荐，更灵活）
SELECT name, price,
       CASE
           WHEN price < 50  THEN '低价'
           WHEN price < 200 THEN '中价'
           ELSE '高价'
       END AS price_level
FROM products;

-- 简单 CASE（按等值匹配）
SELECT name, status,
       CASE status
           WHEN 'draft'   THEN '草稿'
           WHEN 'on_sale' THEN '在售'
           WHEN 'off_sale' THEN '下架'
           ELSE '未知'
       END AS status_cn
FROM products;
```

```sql
-- COALESCE：依次取昵称、邮箱、用户名作为展示名
SELECT id, COALESCE(NULL, email, username, '匿名') AS display FROM users LIMIT 3;

-- IFNULL：账户余额为 NULL 时显示 0
SELECT user_id, IFNULL(balance, 0) AS balance FROM accounts LIMIT 3;
```

### 5. 类型转换

| 函数 | 作用 |
|------|------|
| `CAST(expr AS type)` | 把 expr 转为 type |
| `CONVERT(expr, type)` | 同 CAST，语法不同 |

**常见目标类型**：`SIGNED` / `UNSIGNED`（整数）、`CHAR`（字符串）、`DATE`、`DATETIME`、`TIME`、`DECIMAL(m,n)`、`JSON`、`BINARY`。

```sql
-- 字符串数字转整数
SELECT CAST('123' AS SIGNED) + 1 AS result;

-- 字符串转日期
SELECT CAST('2026-07-27' AS DATE) AS d;

-- 价格转为 2 位小数
SELECT name, CAST(price AS DECIMAL(10,2)) AS price FROM products LIMIT 3;

-- CONVERT 写法
SELECT CONVERT('456', SIGNED) AS n;
```

### 6. JSON 函数（简介）

MySQL 8 原生支持 JSON 类型与一组函数：

| 函数 | 作用 |
|------|------|
| `JSON_EXTRACT(j, path)` | 按 path 取值，简写 `->` |
| `JSON_UNQUOTE(j)` | 去掉 JSON 字符串的引号，简写 `->>` |
| `JSON_OBJECT(k, v, ...)` | 构造 JSON 对象 |
| `JSON_ARRAY(v, ...)` | 构造 JSON 数组 |
| `JSON_CONTAINS(j, val, path)` | 判断是否包含某值 |

```sql
-- 构造 JSON
SELECT JSON_OBJECT('name', 'Alice', 'age', 30) AS j;

-- 取值（假设某 JSON 列 cfg 存 {"role":"admin","level":5}）
-- SELECT cfg->'$.role', cfg->>'$.level' FROM ...;
```

### 7. 窗口函数（重点）

#### 7.1 概念

窗口函数（Window Function）在不减少行数的前提下做"跨行计算"。与 `GROUP BY` 聚合不同：GROUP BY 把多行**合并成一行**，窗口函数保留**每一行**并附加计算结果。

| 维度 | GROUP BY 聚合 | 窗口函数 |
|------|--------------|---------|
| 结果行数 | 减少为分组数 | 保持原行数 |
| 用途 | 汇总统计 | 明细 + 统计兼得 |
| 语法 | `SUM(col) ... GROUP BY ...` | `SUM(col) OVER (...)` |

#### 7.2 语法

```sql
函数() OVER (
    [PARTITION BY 列1, 列2, ...]   -- 分组（类似 GROUP BY，但不合并行）
    [ORDER BY 列3]                  -- 组内排序
    [ROWS BETWEEN 起始 AND 结束]    -- 窗口框架
)
```

#### 7.3 排序类窗口函数

| 函数 | 作用 |
|------|------|
| `ROW_NUMBER()` | 行号，不重复（1,2,3,4） |
| `RANK()` | 并列后跳号（1,2,2,4） |
| `DENSE_RANK()` | 并列不跳号（1,2,2,3） |
| `NTILE(n)` | 把数据均分 n 组，返回组号 |

```sql
-- 每个分类内按价格降序排名（三种排名对比）
SELECT name, category_id, price,
       ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY price DESC) AS rn,
       RANK()       OVER (PARTITION BY category_id ORDER BY price DESC) AS rk,
       DENSE_RANK() OVER (PARTITION BY category_id ORDER BY price DESC) AS drk
FROM products;
```

#### 7.4 偏移类窗口函数

| 函数 | 作用 |
|------|------|
| `LAG(列, n, 默认值)` | 取当前行**之前**第 n 行的值 |
| `LEAD(列, n, 默认值)` | 取当前行**之后**第 n 行的值 |

```sql
-- 每个用户订单按时间排序，对比上一笔订单金额变化
SELECT user_id, created_at, total_amount,
       LAG(total_amount, 1, 0) OVER (PARTITION BY user_id ORDER BY created_at) AS prev_amount,
       total_amount - LAG(total_amount, 1, 0) OVER (PARTITION BY user_id ORDER BY created_at) AS diff
FROM orders;
```

#### 7.5 聚合类窗口函数

`SUM`、`AVG`、`COUNT`、`MAX`、`MIN` 都可作为窗口函数，加 `OVER` 即可。

```sql
-- 每个分类的商品数与该商品在分类内的价格占比
SELECT name, category_id, price,
       SUM(price) OVER (PARTITION BY category_id) AS cat_total,
       ROUND(price / SUM(price) OVER (PARTITION BY category_id) * 100, 2) AS pct
FROM products;
```

#### 7.6 FIRST_VALUE / LAST_VALUE / NTH_VALUE

| 函数 | 作用 |
|------|------|
| `FIRST_VALUE(列)` | 窗口内第一行的值 |
| `LAST_VALUE(列)` | 窗口内最后一行的值（注意框架范围） |
| `NTH_VALUE(列, n)` | 窗口内第 n 行的值 |

> `LAST_VALUE` 默认框架是 `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`，要取"分组最后"需改为 `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`。

#### 7.7 窗口框架

框架定义窗口的"行范围"：

| 写法 | 含义 |
|------|------|
| `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | 从组首到当前行（累计） |
| `ROWS BETWEEN N PRECEDING AND CURRENT ROW` | 当前及前 N 行 |
| `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` | 整组所有行 |
| `RANGE BETWEEN ...` | 按值范围（较少用） |

**累计求和经典场景**：

```sql
-- 按日期累计订单金额
SELECT DATE(created_at) AS d, total_amount,
       SUM(total_amount) OVER (ORDER BY DATE(created_at)
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative
FROM orders;
```

#### 7.8 窗口函数 vs GROUP BY 聚合

| 需求 | 推荐方案 |
|------|---------|
| 每个分类商品数 | GROUP BY |
| 每个分类内商品按价格排名 | 窗口 ROW_NUMBER |
| 每个用户累计消费 | GROUP BY |
| 每个用户消费按月累计 | 窗口 SUM OVER |
| 每个用户取最近一笔订单 | 窗口 ROW_NUMBER + 过滤 |

---

## 代码文件说明

| 文件 | 内容 |
|------|------|
| `Code/01-string-numeric-functions.sql` | 字符串函数与数值函数演示 |
| `Code/02-date-functions.sql` | 日期时间函数：格式化、加减、差值 |
| `Code/03-control-functions.sql` | 流程控制函数：IF/CASE/IFNULL/COALESCE/CAST |
| `Code/04-window-functions.sql` | 窗口函数：排名、偏移、聚合、累计、按分类排名 |

执行方式：

```bash
mysql> USE ecommerce;
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day09 - 常用函数与窗口函数/Code/04-window-functions.sql;
```

---

## 关键知识点总结

### 函数分类速查表

| 类别 | 高频函数 |
|------|---------|
| 字符串 | CONCAT, CONCAT_WS, LENGTH, CHAR_LENGTH, SUBSTRING, TRIM, REPLACE, UPPER, LOWER, LEFT, RIGHT, LPAD, RPAD, SUBSTRING_INDEX, LOCATE |
| 数值 | ROUND, CEIL, FLOOR, RAND, ABS, MOD, TRUNCATE, POWER, SQRT, SIGN |
| 日期 | NOW, CURDATE, DATE_FORMAT, STR_TO_DATE, DATE_ADD, DATE_SUB, DATEDIFF, TIMESTAMPDIFF, LAST_DAY, YEAR/MONTH/DAY |
| 流程控制 | IF, IFNULL, NULLIF, COALESCE, CASE WHEN |
| 类型转换 | CAST, CONVERT |
| JSON | JSON_EXTRACT(->), JSON_UNQUOTE(->>), JSON_OBJECT, JSON_ARRAY, JSON_CONTAINS |

### 窗口函数速查表

| 函数 | 类别 | 典型场景 |
|------|------|---------|
| `ROW_NUMBER()` | 排序 | 唯一行号、取每组前 N |
| `RANK()` | 排序 | 并列跳号排名 |
| `DENSE_RANK()` | 排序 | 并列不跳号排名 |
| `NTILE(n)` | 排序 | 均分 n 桶（四分位等） |
| `LAG(col, n)` | 偏移 | 取上一行（环比） |
| `LEAD(col, n)` | 偏移 | 取下一行（环比） |
| `SUM() OVER` | 聚合 | 累计求和、分组占比 |
| `AVG() OVER` | 聚合 | 移动平均、组均值 |
| `COUNT() OVER` | 聚合 | 组内总数 |
| `MAX()/MIN() OVER` | 聚合 | 组内极值 |
| `FIRST_VALUE()` | 取值 | 组内第一个 |
| `LAST_VALUE()` | 取值 | 组内最后一个（注意框架） |

### 窗口函数记忆口诀

- **PARTITION BY** = 分组（不合并行）
- **ORDER BY** = 组内排序
- **ROWS BETWEEN** = 窗口范围
- 累计求和 = `SUM OVER (ORDER BY ... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`
- 取前 N = `ROW_NUMBER() OVER (...) ` 再 `WHERE rn <= N`

---

## 实战练习

### 练习 1：商品价格分级与邮箱用户名提取

用 `CASE WHEN` 给每件商品打价格分级（<50 低价，50-200 中价，>200 高价），并用 `SUBSTRING_INDEX` 从 email 提取用户名部分（@ 前），最后用 `CONCAT` 拼出"用户名-商品名-分级"展示串。

### 练习 2：每个分类的销量 Top 3 商品

用窗口函数 `ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY 销量 DESC)` 给每个分类的商品按销量（来自 order_items 的 SUM(quantity)）排名，取每个分类前 3。提示：先用派生表或 CTE 算出每个商品的销量，再用窗口函数排名。

### 练习 3：用户消费的月度累计

统计每个用户按月累计的消费总额。输出：user_id、月份、当月消费、累计消费。提示：先按 `user_id` 和 `DATE_FORMAT(created_at, '%Y-%m')` 聚合每月消费，再用 `SUM() OVER (PARTITION BY user_id ORDER BY 月份 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` 求累计。
