-- ============================================================
-- 文件用途: Day07 - 自连接（Self Join）演示
--           演示：categories 树形结构自连接、查分类及父分类名
--                 分类层级、商品关联分类等多场景
--           基于 ecommerce 库
-- 执行方式: mysql> source 本文件路径
-- ============================================================

USE ecommerce;

-- ============================================================
-- 1. 自连接基础：categories 表的 parent_id
-- ============================================================

-- categories 表结构：
--   id          分类ID
--   name        分类名
--   parent_id   父分类ID（0 表示顶级分类）
--   sort_order  排序

-- 1.1 先看一下原始数据
SELECT id, name, parent_id, sort_order FROM categories ORDER BY id LIMIT 30;

-- 1.2 自连接：查每个分类及其父分类名
--     同一张表用两个不同别名：c（子分类）、p（父分类）
SELECT
    c.id AS 分类ID,
    c.name AS 分类名,
    c.parent_id AS 父分类ID,
    p.name AS 父分类名
FROM categories c
LEFT JOIN categories p ON c.parent_id = p.id;
-- LEFT JOIN：顶级分类 parent_id=0 无父分类，仍保留（父分类名为 NULL）

-- 1.3 处理顶级分类的 NULL（用 IFNULL 替换为可读文字）
SELECT
    c.id AS 分类ID,
    c.name AS 分类名,
    IFNULL(p.name, '顶级分类') AS 父分类名
FROM categories c
LEFT JOIN categories p ON c.parent_id = p.id
ORDER BY c.id;

-- 1.4 用 INNER JOIN 对比（顶级分类会被过滤掉）
SELECT
    c.id AS 分类ID,
    c.name AS 分类名,
    p.name AS 父分类名
FROM categories c
INNER JOIN categories p ON c.parent_id = p.id;
-- 顶级分类 parent_id=0，找不到 id=0 的分类，被过滤
-- 结论：查树形结构推荐 LEFT JOIN

-- ============================================================
-- 2. 只查顶级分类
-- ============================================================

-- 2.1 查所有顶级分类（parent_id = 0）
SELECT
    id,
    name,
    sort_order
FROM categories
WHERE parent_id = 0
ORDER BY sort_order;

-- 2.2 查每个顶级分类下的子分类（自连接）
SELECT
    p.id AS 父分类ID,
    p.name AS 父分类名,
    c.id AS 子分类ID,
    c.name AS 子分类名,
    c.sort_order
FROM categories p
INNER JOIN categories c ON c.parent_id = p.id
WHERE p.parent_id = 0
ORDER BY p.sort_order, c.sort_order;
-- 只显示有子分类的顶级分类（INNER JOIN）

-- 2.3 查每个顶级分类及其子分类（LEFT JOIN，含无子分类的顶级分类）
SELECT
    p.id AS 父分类ID,
    p.name AS 父分类名,
    c.id AS 子分类ID,
    c.name AS 子分类名
FROM categories p
LEFT JOIN categories c ON c.parent_id = p.id
WHERE p.parent_id = 0
ORDER BY p.sort_order, c.sort_order;

-- ============================================================
-- 3. 统计每个父分类下的子分类数
-- ============================================================

-- 3.1 每个父分类的子分类数量
SELECT
    p.id AS 父分类ID,
    p.name AS 父分类名,
    COUNT(c.id) AS 子分类数
FROM categories p
LEFT JOIN categories c ON c.parent_id = p.id
GROUP BY p.id, p.name
ORDER BY 子分类数 DESC;

-- 3.2 只查有子分类的父分类（HAVING）
SELECT
    p.id AS 父分类ID,
    p.name AS 父分类名,
    COUNT(c.id) AS 子分类数
FROM categories p
INNER JOIN categories c ON c.parent_id = p.id
GROUP BY p.id, p.name
HAVING COUNT(c.id) >= 1
ORDER BY 子分类数 DESC;

-- ============================================================
-- 4. 商品 + 分类 + 父分类（三表连接，含两次自连接）
-- ============================================================

-- 4.1 查商品及其所属分类与父分类
SELECT
    p.id AS 商品ID,
    p.name AS 商品名,
    p.price AS 价格,
    c.id AS 分类ID,
    c.name AS 分类名,
    IFNULL(pc.name, '顶级分类') AS 父分类名
FROM products p
INNER JOIN categories c ON p.category_id = c.id
LEFT JOIN categories pc ON c.parent_id = pc.id
ORDER BY p.id
LIMIT 30;
-- 连接顺序：products → categories（子） → categories（父）
-- 同一张 categories 表用了两次，用不同别名区分

-- 4.2 按父分类统计商品数
SELECT
    IFNULL(pc.name, '顶级分类') AS 父分类名,
    COUNT(p.id) AS 商品数
FROM products p
INNER JOIN categories c ON p.category_id = c.id
LEFT JOIN categories pc ON c.parent_id = pc.id
GROUP BY pc.name
ORDER BY 商品数 DESC;

-- ============================================================
-- 5. 自连接的其他场景：同级分类
-- ============================================================

-- 5.1 查询每个分类的兄弟分类（同 parent_id 的其他分类）
--     排除自己（c1.id <> c2.id）
SELECT
    c1.name AS 分类名,
    c2.name AS 兄弟分类
FROM categories c1
INNER JOIN categories c2
    ON c1.parent_id = c2.parent_id
    AND c1.id <> c2.id
ORDER BY c1.parent_id, c1.id, c2.id
LIMIT 30;

-- 5.2 查询每个分类的兄弟分类数
SELECT
    c1.id,
    c1.name,
    COUNT(c2.id) AS 兄弟数
FROM categories c1
LEFT JOIN categories c2
    ON c1.parent_id = c2.parent_id
    AND c1.id <> c2.id
GROUP BY c1.id, c1.name
ORDER BY 兄弟数 DESC;

-- ============================================================
-- 6. 分类树层级展开（仅二级，多级需递归查询）
-- ============================================================

-- 6.1 二级分类树：父分类 + 子分类
SELECT
    p.id AS 一级ID,
    p.name AS 一级分类,
    c.id AS 二级ID,
    c.name AS 二级分类,
    c.sort_order
FROM categories p
INNER JOIN categories c ON c.parent_id = p.id
ORDER BY p.sort_order, c.sort_order;
-- 注意：仅支持两级分类。若分类层级不固定（三级、四级...），
--       MySQL 8 可用递归 CTE（WITH RECURSIVE），详见 Day09 函数章节。

-- 6.2 查询"孤立分类"（parent_id 指向不存在的分类）
--     数据异常排查场景
SELECT
    c.id,
    c.name,
    c.parent_id
FROM categories c
LEFT JOIN categories p ON c.parent_id = p.id
WHERE c.parent_id <> 0 AND p.id IS NULL;
-- 若有结果，说明存在 parent_id 指向已删除分类的脏数据

-- ============================================================
-- 7. 商品分类层级汇总
-- ============================================================

-- 7.1 按一级分类统计商品数与销售额
SELECT
    IFNULL(pc.name, '顶级分类') AS 一级分类,
    COUNT(DISTINCT p.id) AS 商品数,
    COUNT(DISTINCT oi.order_id) AS 销售记录数,
    SUM(oi.quantity * oi.unit_price) AS 销售额
FROM products p
INNER JOIN categories c ON p.category_id = c.id
LEFT JOIN categories pc ON c.parent_id = pc.id
LEFT JOIN order_items oi ON oi.product_id = p.id
GROUP BY pc.name
ORDER BY 销售额 DESC;
-- 注意：LEFT JOIN order_items 是为了包含未销售的商品
--      销售额为 NULL 表示无销售

-- 7.2 按二级分类统计商品数
SELECT
    IFNULL(pc.name, '顶级分类') AS 一级分类,
    c.name AS 二级分类,
    COUNT(p.id) AS 商品数,
    ROUND(AVG(p.price), 2) AS 平均价
FROM products p
INNER JOIN categories c ON p.category_id = c.id
LEFT JOIN categories pc ON c.parent_id = pc.id
GROUP BY pc.name, c.name
ORDER BY 一级分类, 商品数 DESC;

-- ============================================================
-- 8. 自连接综合示例
-- ============================================================

-- 8.1 查询"有子分类且子分类下有商品"的父分类
SELECT DISTINCT
    p.id AS 父分类ID,
    p.name AS 父分类名,
    COUNT(DISTINCT c.id) AS 子分类数,
    COUNT(DISTINCT pr.id) AS 商品数
FROM categories p
INNER JOIN categories c ON c.parent_id = p.id
INNER JOIN products pr ON pr.category_id = c.id
GROUP BY p.id, p.name
ORDER BY 商品数 DESC;

-- 8.2 查询每个分类的完整路径（一级 > 二级）
SELECT
    c.id,
    CONCAT(IFNULL(pc.name, ''), ' > ', c.name) AS 分类路径,
    c.sort_order
FROM categories c
LEFT JOIN categories pc ON c.parent_id = pc.id
ORDER BY pc.sort_order, c.sort_order;
-- 用 CONCAT 拼接出可读的分类路径
-- 顶级分类显示为 " > 手机数码"（前面为空）
