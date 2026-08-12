-- ============================================================
-- 文件用途: Day05 - 运算符演示
--           演示：比较运算符、逻辑运算符、IN、BETWEEN、LIKE、REGEXP、IS NULL、<=>
--           重点演示 NULL 的三值逻辑
--           基于 ecommerce 库
-- 执行方式: mysql> source 本文件路径
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. 比较运算符：= <> < > <= >=
-- ============================================================

-- 1.1 等于：查询管理员用户
SELECT id, username, role FROM users WHERE role = 'admin';

-- 1.2 不等于（两种写法等价）
SELECT id, username, role FROM users WHERE role <> 'customer';
SELECT id, username, role FROM users WHERE role != 'customer';

-- 1.3 大于 / 小于：价格大于 500 的商品
SELECT id, name, price FROM products WHERE price > 500;

-- 1.4 大于等于 / 小于等于
SELECT id, name, price FROM products WHERE price <= 100;
SELECT id, name, stock FROM products WHERE stock >= 100;

-- 1.5 日期比较：2025 年之后创建的订单
SELECT id, user_id, total_amount, created_at
FROM orders
WHERE created_at >= '2025-01-01';

-- ============================================================
-- 2. 逻辑运算符：AND OR NOT
-- ============================================================

-- 2.1 AND：在售且库存大于 0 的商品
SELECT id, name, status, stock
FROM products
WHERE status = 'on_sale' AND stock > 0;

-- 2.2 OR：管理员或编辑
SELECT id, username, role FROM users WHERE role = 'admin' OR role = 'editor';

-- 2.3 NOT：非已取消的订单
SELECT id, status FROM orders WHERE NOT status = 'cancelled';

-- 2.4 优先级陷阱：NOT > AND > OR
--     不加括号时：
--     role='admin' OR role='editor' AND status=1
--     等价于 role='admin' OR (role='editor' AND status=1)
SELECT id, username, role, status
FROM users
WHERE role = 'admin' OR role = 'editor' AND status = 1;

-- 2.5 推荐写法：用括号显式分组，避免依赖默认优先级
SELECT id, username, role, status
FROM users
WHERE (role = 'admin' OR role = 'editor') AND status = 1;

-- 2.6 复合条件：在售且（价格 > 100 或库存 > 50）
SELECT id, name, price, stock, status
FROM products
WHERE status = 'on_sale' AND (price > 100 OR stock > 50);

-- ============================================================
-- 3. 范围运算符 BETWEEN ... AND
-- ============================================================

-- 3.1 价格在 100 到 1000 之间（含两端）
SELECT id, name, price FROM products
WHERE price BETWEEN 100 AND 1000;

-- 3.2 等价写法用 >= AND <=
SELECT id, name, price FROM products
WHERE price >= 100 AND price <= 1000;

-- 3.3 反向：不在该范围
SELECT id, name, price FROM products
WHERE price NOT BETWEEN 100 AND 1000;

-- 3.4 日期范围：2025 年 1 月的订单
SELECT id, created_at, total_amount
FROM orders
WHERE created_at BETWEEN '2025-01-01' AND '2025-01-31 23:59:59';

-- 3.5 字符串范围（按字典序）：用户名在 a 到 m 之间
SELECT id, username FROM users
WHERE username BETWEEN 'a' AND 'm';

-- ============================================================
-- 4. 集合运算符 IN
-- ============================================================

-- 4.1 查询指定状态的订单
SELECT id, status, total_amount
FROM orders
WHERE status IN ('paid', 'shipped', 'completed');

-- 4.2 等价写法用多个 OR（IN 更简洁）
SELECT id, status, total_amount
FROM orders
WHERE status = 'paid' OR status = 'shipped' OR status = 'completed';

-- 4.3 反向：不在此集合
SELECT id, status FROM orders
WHERE status NOT IN ('cancelled', 'refunded');

-- 4.4 IN 配合数字
SELECT id, rating FROM reviews
WHERE rating IN (5, 4);

-- ============================================================
-- 5. 模糊匹配 LIKE
-- ============================================================

-- 5.1 % 通配符：任意多个字符（含 0 个）
--     以 'admin' 开头的用户名
SELECT id, username FROM users WHERE username LIKE 'admin%';

-- 5.2 含 '@gmail' 的邮箱
SELECT id, email FROM users WHERE email LIKE '%@gmail%';

-- 5.3 以 '.com' 结尾的邮箱
SELECT id, email FROM users WHERE email LIKE '%.com';

-- 5.4 _ 通配符：任意单个字符（必须正好 1 个）
--     第二个字符是 'o' 的用户名
SELECT id, username FROM users WHERE username LIKE '_o%';

-- 5.5 长度等于 5 的用户名（5 个下划线）
SELECT id, username FROM users WHERE username LIKE '_____';

-- 5.6 通配符转义 ESCAPE：当字符串本身包含 % 或 _ 时
--     假设商品名含 '50%' 字样，需要把 % 当普通字符
SELECT id, name FROM products WHERE name LIKE '%50\\%%' ESCAPE '\\';
--     解释：第一个 % 是通配符；\\% 是被转义的字面 %；最后一个 % 又是通配符

-- 5.7 转义下划线 _：查商品名中含 'pro_1' 的
SELECT id, name FROM products WHERE name LIKE '%pro\\_1%' ESCAPE '\\';

-- ============================================================
-- 6. 正则表达式 REGEXP / RLIKE
-- ============================================================

-- 6.1 REGEXP 是部分匹配（只要字符串中存在匹配子串就为真）
--     含数字的用户名
SELECT id, username FROM users WHERE username REGEXP '[0-9]';

-- 6.2 以字母开头、后跟数字结尾
SELECT id, username FROM users WHERE username REGEXP '^[a-zA-Z]+[0-9]+$';

-- 6.3 邮箱以 .com 或 .cn 结尾（注意点要转义）
SELECT id, email FROM users WHERE email REGEXP '\\.(com|cn)$';

-- 6.4 评价内容含中文"好"或"差"
SELECT id, content FROM reviews WHERE content REGEXP '好|差';

-- 6.5 RLIKE 是 REGEXP 的别名，效果相同
SELECT id, username FROM users WHERE username RLIKE '^[a-z]';

-- 6.6 对比 LIKE 与 REGEXP 的差异
--     LIKE 不加通配符时是精确匹配子串失败
SELECT 'hello world' LIKE 'world';            -- 0（false，LIKE 默认全字符串匹配）
SELECT 'hello world' LIKE '%world%';          -- 1（true，加 % 才匹配子串）
SELECT 'hello world' REGEXP 'world';         -- 1（true，REGEXP 默认部分匹配）

-- ============================================================
-- 7. 空值判断 IS NULL / IS NOT NULL
-- ============================================================

-- 7.1 正确：查询未软删除的用户（deleted_at 为 NULL）
SELECT id, username, deleted_at
FROM users
WHERE deleted_at IS NULL;

-- 7.2 正确：查询已软删除的用户
SELECT id, username, deleted_at
FROM users
WHERE deleted_at IS NOT NULL;

-- 7.3 错误示范：用 = NULL 永远查不到数据
SELECT id, username FROM users WHERE deleted_at = NULL;     -- 永远返回空
SELECT id, username FROM users WHERE deleted_at <> NULL;    -- 永远返回空

-- ============================================================
-- 8. NULL 三值逻辑演示
-- ============================================================

-- 8.1 NULL 与任何值比较结果都是 NULL（不是 true 也不是 false）
SELECT NULL = 1 AS `NULL=1`;        -- NULL
SELECT NULL = NULL AS `NULL=NULL`;  -- NULL
SELECT NULL <> 1 AS `NULL<>1`;      -- NULL
SELECT NULL + 1 AS `NULL+1`;        -- NULL（算术运算也返回 NULL）

-- 8.2 IS NULL 才是判断 NULL 的正确方式
SELECT NULL IS NULL AS `判断NULL`;        -- 1 (true)
SELECT NULL IS NOT NULL AS `判断非NULL`;  -- 0 (false)

-- 8.3 NULL 在逻辑运算中的传播
--     AND: 任一为 NULL，结果可能为 NULL
SELECT (1 = 1) AND (NULL IS NULL) AS `T AND T`;   -- 1 (true)
SELECT (1 = 2) AND (NULL IS NULL) AS `F AND T`;   -- 0 (false)
SELECT (1 = 1) AND (NULL = 1)    AS `T AND N`;   -- NULL
--     OR: 任一为 true，结果为 true；否则可能为 NULL
SELECT (1 = 1) OR (NULL = 1)     AS `T OR N`;    -- 1 (true)
SELECT (1 = 2) OR (NULL = 1)     AS `F OR N`;    -- NULL

-- ============================================================
-- 9. NULL 安全等于 <=>
-- ============================================================

-- 9.1 <=> 与 = 的区别
SELECT NULL = NULL AS `用等于`;     -- NULL（不是 true！）
SELECT NULL <=> NULL AS `用安全等于`; -- 1 (true)

SELECT 1 = 1 AS `普通等于`;          -- 1
SELECT 1 <=> 1 AS `安全等于`;        -- 1

-- 9.2 实战：查 deleted_at 为 NULL 的用户（与 IS NULL 等价）
SELECT id, username FROM users WHERE deleted_at <=> NULL;

-- 9.3 实战：查 deleted_at 不为 NULL 的用户
SELECT id, username FROM users WHERE NOT (deleted_at <=> NULL);

-- ============================================================
-- 10. NULL 处理函数
-- ============================================================

-- 10.1 IFNULL(a, b)：a 为 NULL 则返回 b
SELECT
    id,
    username,
    IFNULL(deleted_at, '未删除') AS 删除状态
FROM users
LIMIT 10;

-- 10.2 COALESCE(a, b, c, ...)：返回第一个非 NULL 的参数
SELECT
    id,
    username,
    COALESCE(deleted_at, 'active') AS 状态
FROM users
LIMIT 10;

-- 10.3 NULLIF(a, b)：a=b 时返回 NULL，否则返回 a
--     用于排除某个特定值（比如把 status=0 当作 NULL 处理）
SELECT
    id,
    username,
    NULLIF(status, 0) AS 状态或NULL
FROM users
LIMIT 10;

-- ============================================================
-- 11. 综合示例
-- ============================================================

-- 11.1 查询：在售状态、价格在 50-500 之间、库存大于 0、名称含"手机"的商品
SELECT id, name, price, stock, status
FROM products
WHERE status = 'on_sale'
  AND price BETWEEN 50 AND 500
  AND stock > 0
  AND name LIKE '%手机%'
ORDER BY price DESC
LIMIT 10;

-- 11.2 查询：已支付或已发货的订单，且总金额大于 500
SELECT id, user_id, status, total_amount, created_at
FROM orders
WHERE status IN ('paid', 'shipped')
  AND total_amount > 500
ORDER BY total_amount DESC;
