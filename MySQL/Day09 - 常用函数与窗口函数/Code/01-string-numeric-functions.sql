-- ============================================================
-- 文件名称: 01-string-numeric-functions.sql
-- 文件用途: 字符串函数与数值函数演示
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day09 - 常用函数与窗口函数/Code/01-string-numeric-functions.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 一、字符串拼接函数
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 CONCAT：拼接字符串，任一参数为 NULL 则结果为 NULL
-- ------------------------------------------------------------
SELECT CONCAT('Hello', ' ', 'MySQL') AS greeting;
SELECT CONCAT(username, ' (', email, ')') AS display
FROM users
LIMIT 3;

-- 演示 NULL 影响：含 NULL 拼接结果为 NULL
SELECT CONCAT('a', NULL, 'b') AS with_null;

-- ------------------------------------------------------------
-- 1.2 CONCAT_WS：用分隔符拼接，自动跳过 NULL
--     WS = With Separator
-- ------------------------------------------------------------
SELECT CONCAT_WS('-', '2026', '07', '27') AS date_str;
SELECT CONCAT_WS(' | ', username, email, NULL) AS user_info
FROM users
LIMIT 3;

-- ============================================================
-- 二、长度函数：字节 vs 字符
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 LENGTH 返回字节数，CHAR_LENGTH 返回字符数
--     utf8mb4 下一个中文占 3~4 字节，但只算 1 个字符
-- ------------------------------------------------------------
SELECT LENGTH('MySQL')        AS byte_en,
       CHAR_LENGTH('MySQL')   AS char_en,
       LENGTH('中文')         AS byte_cn,
       CHAR_LENGTH('中文')    AS char_cn;

-- 应用于商品名长度统计
SELECT name,
       LENGTH(name)       AS bytes_len,
       CHAR_LENGTH(name)  AS char_len
FROM products
LIMIT 5;

-- ============================================================
-- 三、截取与查找
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 SUBSTRING / SUBSTR：截取子串（位置从 1 开始）
-- ------------------------------------------------------------
SELECT SUBSTRING('Hello MySQL', 7)      AS from_7;      -- MySQL
SELECT SUBSTRING('Hello MySQL', 1, 5)   AS first_5;     -- Hello
SELECT SUBSTRING('Hello MySQL', -5)     AS last_5;      -- MySQL（负数从末尾算）

-- ------------------------------------------------------------
-- 3.2 LEFT / RIGHT：从左/右取 n 个字符
-- ------------------------------------------------------------
SELECT LEFT('Hello', 2)  AS l2,    -- He
       RIGHT('Hello', 3) AS r3;    -- llo

-- 截取商品名前 10 个字符（防止过长）
SELECT id, LEFT(name, 10) AS short_name FROM products LIMIT 5;

-- ------------------------------------------------------------
-- 3.3 LOCATE / INSTR：查找子串位置（从 1 开始，找不到为 0）
-- ------------------------------------------------------------
SELECT LOCATE('l', 'Hello')      AS pos1,   -- 3
       LOCATE('x', 'Hello')      AS pos2,   -- 0
       INSTR('Hello', 'll')      AS pos3;   -- 3

-- 查找邮箱中 @ 的位置
SELECT email, LOCATE('@', email) AS at_pos
FROM users
LIMIT 3;

-- ------------------------------------------------------------
-- 3.4 SUBSTRING_INDEX：按分隔符取前 N 段（常用！）
--     N 为正取左边，N 为负取右边
-- ------------------------------------------------------------
SELECT SUBSTRING_INDEX('a@b.com', '@', 1)  AS user_part,   -- a
       SUBSTRING_INDEX('a@b.com', '@', -1) AS domain_part;  -- b.com

-- 提取邮箱用户名和域名
SELECT email,
       SUBSTRING_INDEX(email, '@', 1)  AS email_user,
       SUBSTRING_INDEX(email, '@', -1) AS email_domain
FROM users
LIMIT 5;

-- ============================================================
-- 四、去空格与替换
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 TRIM / LTRIM / RTRIM：去两端/左/右空格
-- ------------------------------------------------------------
SELECT TRIM('  hello  ')  AS trim_both,   -- hello
       LTRIM('  hello  ') AS ltrim_only,   -- hello  
       RTRIM('  hello  ') AS rtrim_only;   --   hello

-- TRIM 还能去指定字符
SELECT TRIM(BOTH '0' FROM '00012300') AS trim_zero;  -- 123

-- ------------------------------------------------------------
-- 4.2 REPLACE：替换所有匹配
-- ------------------------------------------------------------
SELECT REPLACE('a-b-c-d', '-', '_') AS replaced;  -- a_b_c_d

-- 隐藏邮箱域名（脱敏）
SELECT REPLACE(email, SUBSTRING_INDEX(email, '@', -1), '***.com') AS masked_email
FROM users
LIMIT 3;

-- ============================================================
-- 五、大小写转换与填充
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 UPPER / LOWER：大小写转换
-- ------------------------------------------------------------
SELECT UPPER('Hello') AS up, LOWER('Hello') AS low;

-- 用户名统一转小写对比
SELECT username, LOWER(username) AS lower_name FROM users LIMIT 3;

-- ------------------------------------------------------------
-- 5.2 LPAD / RPAD：左/右填充到指定长度
--     常用于订单号补零、固定宽度展示
-- ------------------------------------------------------------
SELECT LPAD('5', 3, '0')  AS lpad_demo,   -- 005
       RPAD('5', 3, '*')  AS rpad_demo;   -- 5**

-- 订单号补零到 8 位
SELECT id, LPAD(id, 8, '0') AS order_no, total_amount
FROM orders
LIMIT 5;

-- ------------------------------------------------------------
-- 5.3 REPEAT / REVERSE
-- ------------------------------------------------------------
SELECT REPEAT('ab', 3) AS repeated,   -- ababab
       REVERSE('Hello') AS reversed;  -- olleH

-- ============================================================
-- 六、数值函数
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 ROUND：四舍五入
-- ------------------------------------------------------------
SELECT ROUND(3.1415, 2)  AS r2,    -- 3.14
       ROUND(3.1415, 0)  AS r0,    -- 3
       ROUND(3.5)        AS r_def, -- 4（默认 0 位）
       ROUND(-3.5)       AS r_neg; -- -4

-- 价格打 8 折后保留 2 位
SELECT name, price, ROUND(price * 0.8, 2) AS discount_price
FROM products
LIMIT 5;

-- ------------------------------------------------------------
-- 6.2 CEIL / FLOOR：向上/向下取整
-- ------------------------------------------------------------
SELECT CEIL(3.1)  AS ceil_demo,   -- 4
       CEIL(-3.1) AS ceil_neg,    -- -3
       FLOOR(3.9) AS floor_demo,  -- 3
       FLOOR(-3.9) AS floor_neg;  -- -4

-- 库存按每箱 10 件计算需要的箱数（向上取整）
SELECT name, stock, CEIL(stock / 10) AS boxes_needed
FROM products
WHERE stock > 0
LIMIT 5;

-- ------------------------------------------------------------
-- 6.3 ABS / MOD / SIGN
-- ------------------------------------------------------------
SELECT ABS(-10)    AS abs_demo,   -- 10
       MOD(10, 3)  AS mod_demo,   -- 1
       10 % 3      AS mod_op,     -- 1（等价写法）
       SIGN(-5)    AS sign_neg,   -- -1
       SIGN(0)     AS sign_zero,  -- 0
       SIGN(5)     AS sign_pos;   -- 1

-- ------------------------------------------------------------
-- 6.4 TRUNCATE：截断到指定位数（不四舍五入）
-- ------------------------------------------------------------
SELECT TRUNCATE(3.1415, 2) AS t2,    -- 3.14
       ROUND(3.1415, 2)    AS r2;    -- 3.14（此处相同，但 3.145 不同）

SELECT TRUNCATE(3.999, 0) AS t_zero,  -- 3
       ROUND(3.999, 0)    AS r_zero;  -- 4

-- ------------------------------------------------------------
-- 6.5 POWER / SQRT
-- ------------------------------------------------------------
SELECT POWER(2, 10) AS pow_demo,  -- 1024
       SQRT(16)     AS sqrt_demo; -- 4

-- ------------------------------------------------------------
-- 6.6 RAND：0~1 随机数
-- ------------------------------------------------------------
SELECT RAND() AS r1, RAND() AS r2;

-- 随机抽取 3 件商品
SELECT id, name, price
FROM products
ORDER BY RAND()
LIMIT 3;

-- 模拟 1~100 随机整数
SELECT FLOOR(1 + RAND() * 100) AS random_int;

-- ============================================================
-- 七、综合应用
-- ============================================================

-- ------------------------------------------------------------
-- 7.1 生成用户脱敏邮箱与展示名
--     用 SUBSTRING + LPAD + CONCAT 实现
-- ------------------------------------------------------------
SELECT id,
       username,
       CONCAT(
           LEFT(email, 2),
           '****',
           SUBSTRING(email, LOCATE('@', email))
       ) AS masked_email
FROM users
LIMIT 5;

-- ------------------------------------------------------------
-- 7.2 商品价格区间统计：用 ROUND 分桶
--     按 100 元一档统计商品数量
-- ------------------------------------------------------------
SELECT FLOOR(price / 100) * 100 AS price_bucket_start,
       FLOOR(price / 100) * 100 + 100 AS price_bucket_end,
       COUNT(*) AS product_cnt
FROM products
GROUP BY FLOOR(price / 100)
ORDER BY price_bucket_start;

-- ============================================================
-- 字符串与数值函数演示完毕。
-- 要点：LENGTH 看字节、CHAR_LENGTH 看字符；
--       SUBSTRING_INDEX 是处理分隔符字符串的利器；
--       LPAD/RPAD 常用于编号补零；
--       ROUND 四舍五入、TRUNCATE 截断、CEIL/FLOOR 取整。
-- ============================================================
