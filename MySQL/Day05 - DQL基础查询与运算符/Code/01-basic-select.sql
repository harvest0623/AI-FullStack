-- ============================================================
-- 文件用途: Day05 - SELECT 基础查询演示
--           演示：查列、SELECT *、列别名 AS、表别名、DISTINCT、ORDER BY、LIMIT
--           基于 ecommerce 库，假设 Day04 已灌入测试数据
-- 执行方式: mysql> source 本文件路径
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. SELECT 基础：查列 vs SELECT *
-- ============================================================

-- 1.1 查询所有列（开发期调试可用，生产代码不推荐）
SELECT * FROM users;

-- 1.2 查询指定列（推荐：明确意图、节省带宽）
SELECT id, username, email, role
FROM users;

-- 1.3 仅查询商品的关键字段
SELECT id, name, price, stock, status
FROM products;

-- ============================================================
-- 2. 列别名 AS
-- ============================================================

-- 2.1 使用 AS 给列起别名（推荐写法，可读性好）
SELECT
    username AS 用户名,
    email    AS 邮箱,
    role     AS 角色
FROM users;

-- 2.2 省略 AS（效果相同，但可读性稍差）
SELECT username 用户名, email 邮箱 FROM users;

-- 2.3 给计算列起名（计算列原本没有名字，必须用别名才能引用）
SELECT
    name,
    price,
    stock,
    price * stock AS 库存总价值
FROM products;

-- 2.4 别名含特殊字符时用反引号包裹
SELECT name AS `商品名称`, price AS `单价(元)` FROM products LIMIT 3;

-- ============================================================
-- 3. 表别名
-- ============================================================

-- 3.1 给表起短别名，多表查询时常用（Day07 会大量使用）
SELECT u.id, u.username, u.role
FROM users AS u
WHERE u.role = 'customer';

-- 3.2 省略 AS
SELECT u.id, u.username
FROM users u
WHERE u.status = 1;

-- ============================================================
-- 4. DISTINCT 去重
-- ============================================================

-- 4.1 单列去重：查询所有出现过的用户角色
SELECT DISTINCT role FROM users;

-- 4.2 多列去重：DISTINCT 作用于 (role, status) 组合，不是只作用于 role
SELECT DISTINCT role, status FROM users;

-- 4.3 查询所有下过订单的用户 id（去重）
SELECT DISTINCT user_id FROM orders;

-- 4.4 查询订单的所有不同状态
SELECT DISTINCT status FROM orders;

-- 4.5 对比：不加 DISTINCT 与加 DISTINCT 的差异
SELECT user_id, status FROM orders ORDER BY user_id LIMIT 10;          -- 含重复
SELECT DISTINCT user_id, status FROM orders ORDER BY user_id LIMIT 10; -- 去重

-- ============================================================
-- 5. ORDER BY 排序
-- ============================================================

-- 5.1 默认升序（ASC 可省略）
SELECT id, name, price FROM products ORDER BY price;

-- 5.2 显式升序
SELECT id, name, price FROM products ORDER BY price ASC;

-- 5.3 降序
SELECT id, name, price FROM products ORDER BY price DESC;

-- 5.4 多列排序：先按 status 升序，再按 price 降序
SELECT id, name, status, price
FROM products
ORDER BY status ASC, price DESC;

-- 5.5 按别名排序（WHERE 不能用别名，ORDER BY 可以）
SELECT name, price, stock, price * stock AS 总价值
FROM products
ORDER BY 总价值 DESC;

-- 5.6 按表达式排序
SELECT name, price, stock
FROM products
ORDER BY price * stock DESC;

-- 5.7 NULL 在排序中的位置：默认 NULL 最小
--     升序时 NULL 在最前，降序时 NULL 在最后
SELECT id, username, deleted_at
FROM users
ORDER BY deleted_at ASC;   -- NULL 排最前

SELECT id, username, deleted_at
FROM users
ORDER BY deleted_at DESC;  -- NULL 排最后

-- 5.8 按列序号排序（不推荐，可读性差，列顺序变更会出错）
SELECT name, price, stock FROM products ORDER BY 2 DESC;  -- 等价于 ORDER BY price DESC

-- ============================================================
-- 6. LIMIT 限制返回行数
-- ============================================================

-- 6.1 取前 N 条：取价格最高的 3 件商品
SELECT id, name, price
FROM products
ORDER BY price DESC
LIMIT 3;

-- 6.2 LIMIT 必须配合 ORDER BY，否则结果顺序不确定
--     （不写 ORDER BY 时 MySQL 不保证返回顺序）
SELECT id, name FROM products LIMIT 5;

-- 6.3 取最新注册的 5 个用户
SELECT id, username, created_at
FROM users
ORDER BY created_at DESC
LIMIT 5;

-- ============================================================
-- 7. 综合示例：SELECT + WHERE + ORDER BY + LIMIT
-- ============================================================

-- 7.1 查询在售商品中价格最高的 5 件
SELECT id, name, price, stock, status
FROM products
WHERE status = 'on_sale'
ORDER BY price DESC
LIMIT 5;

-- 7.2 查询未被软删除的普通消费者，按注册时间倒序取前 10 条
SELECT id, username, email, created_at
FROM users
WHERE role = 'customer'
  AND status = 1
  AND deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 10;
