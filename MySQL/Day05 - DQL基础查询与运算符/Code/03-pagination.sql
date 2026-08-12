-- ============================================================
-- 文件用途: Day05 - 分页查询演示
--           演示：LIMIT 两种语法、分页公式、深分页问题预告
--           基于 ecommerce 库
-- 执行方式: mysql> source 本文件路径
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. LIMIT 基础：取前 N 条
-- ============================================================

-- 1.1 取前 3 条商品
SELECT id, name, price FROM products LIMIT 3;

-- 1.2 取价格最高的 5 件商品（必须配合 ORDER BY）
SELECT id, name, price
FROM products
ORDER BY price DESC
LIMIT 5;

-- 1.3 取最新注册的 3 个用户
SELECT id, username, created_at
FROM users
ORDER BY created_at DESC
LIMIT 3;

-- ============================================================
-- 2. LIMIT 的两种分页语法
-- ============================================================

-- 2.1 语法一：LIMIT offset, size  （偏移量, 每页条数）
--     第 1 页：offset=0, size=10
SELECT id, name, price FROM products
ORDER BY id LIMIT 0, 10;

-- 2.2 语法二：LIMIT size OFFSET offset（每页条数 OFFSET 偏移量）
--     第 1 页：size=10, offset=0
SELECT id, name, price FROM products
ORDER BY id LIMIT 10 OFFSET 0;

-- 2.3 两种写法完全等价，推荐第一种（更简洁）

-- ============================================================
-- 3. 分页公式演示：LIMIT (page-1)*size, size
-- ============================================================

-- 假设每页 10 条

-- 第 1 页：offset = (1-1)*10 = 0
SELECT id, name, price FROM products ORDER BY id LIMIT 0, 10;

-- 第 2 页：offset = (2-1)*10 = 10
SELECT id, name, price FROM products ORDER BY id LIMIT 10, 10;

-- 第 3 页：offset = (3-1)*10 = 20
SELECT id, name, price FROM products ORDER BY id LIMIT 20, 10;

-- 第 5 页：offset = (5-1)*10 = 40
SELECT id, name, price FROM products ORDER BY id LIMIT 40, 10;

-- ============================================================
-- 4. 实战分页：商品列表分页
-- ============================================================

-- 4.1 商品列表第 1 页（每页 15 条，按价格降序）
SELECT id, name, price, stock, status
FROM products
WHERE status = 'on_sale'
ORDER BY price DESC
LIMIT 0, 15;

-- 4.2 商品列表第 2 页
SELECT id, name, price, stock, status
FROM products
WHERE status = 'on_sale'
ORDER BY price DESC
LIMIT 15, 15;

-- 4.3 商品列表第 3 页
SELECT id, name, price, stock, status
FROM products
WHERE status = 'on_sale'
ORDER BY price DESC
LIMIT 30, 15;

-- ============================================================
-- 5. 订单分页：按时间倒序
-- ============================================================

-- 5.1 第 1 页（每页 20 条）
SELECT id, user_id, total_amount, status, created_at
FROM orders
ORDER BY created_at DESC
LIMIT 0, 20;

-- 5.2 第 2 页
SELECT id, user_id, total_amount, status, created_at
FROM orders
ORDER BY created_at DESC
LIMIT 20, 20;

-- ============================================================
-- 6. 深分页问题演示
-- ============================================================

-- 6.1 浅分页（前几页）性能正常
--     MySQL 扫描 offset+size = 10 行，丢弃前 0 行
SELECT id, name FROM products ORDER BY id LIMIT 0, 10;

-- 6.2 中等深度分页：第 100 页
--     MySQL 扫描 1000 行，丢弃前 990 行，返回 10 行
SELECT id, name FROM products ORDER BY id LIMIT 990, 10;

-- 6.3 深分页：第 1000 页（假设数据足够多）
--     MySQL 仍要扫描 10000 行，丢弃前 9990 行，仅返回 10 行
--     offset 越大，浪费的扫描越多，性能越差
SELECT id, name FROM products ORDER BY id LIMIT 9990, 10;

-- 6.4 深分页优化方案一：游标分页（记住上一页的最大 id）
--     假设上一页最后一条 id = 100，下一页直接从 100 之后取
--     优点：无论第几页都只扫描 size 行
--     缺点：只能"上一页/下一页"，不能直接跳转到任意页
SELECT id, name FROM products WHERE id > 100 ORDER BY id LIMIT 10;

-- 6.5 深分页优化方案二：延迟关联（先查主键再回表）
--     先用覆盖索引查出主键，再 JOIN 取需要的列
--     详情见 Day10 索引与 Day14 优化
SELECT p.*
FROM products p
INNER JOIN (
    SELECT id FROM products ORDER BY id LIMIT 9990, 10
) t ON p.id = t.id;

-- ============================================================
-- 7. 获取总条数（用于分页前端显示总页数）
-- ============================================================

-- 7.1 用 COUNT(*) 获取商品总数（Day06 详讲聚合函数）
SELECT COUNT(*) AS 商品总数 FROM products;

-- 7.2 获取在售商品总数
SELECT COUNT(*) AS 在售商品数 FROM products WHERE status = 'on_sale';

-- 7.3 前端分页需要：总条数 + 当前页数据（两条查询配合）
--     总条数：SELECT COUNT(*) FROM products WHERE status='on_sale';
--     当前页：SELECT id, name, price FROM products WHERE status='on_sale' ORDER BY price DESC LIMIT 0, 15;

-- ============================================================
-- 8. LIMIT 与 NULL 排序的配合
-- ============================================================

-- 8.1 查询未删除用户，按注册时间倒序，取第 1 页（每页 10 条）
SELECT id, username, email, created_at, deleted_at
FROM users
WHERE deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 0, 10;

-- 8.2 第 2 页
SELECT id, username, email, created_at, deleted_at
FROM users
WHERE deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 10, 10;

-- ============================================================
-- 9. 分页公式速查
-- ============================================================

-- 公式：LIMIT (page - 1) * size, size
--
-- | page | size | offset | LIMIT 写法     |
-- |------|------|--------|----------------|
-- | 1    | 10   | 0      | LIMIT 0, 10    |
-- | 2    | 10   | 10     | LIMIT 10, 10   |
-- | 3    | 10   | 20     | LIMIT 20, 10   |
-- | 5    | 20   | 80     | LIMIT 80, 20   |
-- | 10   | 15   | 135    | LIMIT 135, 15  |
--
-- 注意：
-- 1. page 从 1 开始（不是 0），offset 从 0 开始
-- 2. LIMIT 必须配合 ORDER BY，否则分页结果顺序不确定
-- 3. 数据频繁变化时，深分页可能出现重复或遗漏（游标分页更稳定）
