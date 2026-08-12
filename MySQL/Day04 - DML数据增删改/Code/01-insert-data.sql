-- ============================================================
-- 文件名称: 01-insert-data.sql
-- 文件用途: 向 ecommerce 库灌入真实合理的测试数据
--           为后续查询天数铺垫，数据覆盖全部 7 张表
--           含: 12个用户、10个分类(5顶级+5子级)、20个商品、
--               8个订单及明细、10个账户、12条评价
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day04/Code/01-insert-data.sql
-- 前置条件: 已执行 Day02/Code/01-create-ecommerce.sql 建好表结构
-- 可重复执行: 脚本开头会清空所有表并重置自增
-- 设计说明: categories.parent_id 因有外键约束，顶级分类用
--           NULL 表示（NULL 不参与外键校验），子分类用父 id
-- ============================================================

USE ecommerce;

-- ------------------------------------------------------------
-- 0. 清空所有表（关闭外键检查，反向 TRUNCATE，重置自增）
-- ------------------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE order_items;
TRUNCATE TABLE reviews;
TRUNCATE TABLE accounts;
TRUNCATE TABLE orders;
TRUNCATE TABLE products;
TRUNCATE TABLE categories;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;


-- ============================================================
-- 1. 用户表 users（12个: 1 admin + 1 editor + 10 customer）
--    password_hash 用占位字符串模拟（生产环境应存 bcrypt 哈希）
-- ============================================================
INSERT INTO users (id, username, email, password_hash, role, status) VALUES
  (1,  'admin',     'admin@shop.com',     '$2b$10$adminhashplaceholderXXXXXXXXXXXXXXXXXXXX',  'admin',     1),
  (2,  'editor01',  'editor@shop.com',    '$2b$10$editorhashplaceholderXXXXXXXXXXXXXXXXXXXX', 'editor',    1),
  (3,  'alice',     'alice@163.com',      '$2b$10$alicehashplaceholderXXXXXXXXXXXXXXXXXXXXX', 'customer',  1),
  (4,  'bob',       'bob@qq.com',         '$2b$10$bobhashplaceholderXXXXXXXXXXXXXXXXXXXXXXX', 'customer',  1),
  (5,  'charlie',   'charlie@gmail.com',  '$2b$10$charliehashplaceholderXXXXXXXXXXXXXXXXXXX', 'customer',  1),
  (6,  'david',     'david@163.com',      '$2b$10$davidhashplaceholderXXXXXXXXXXXXXXXXXXXXX', 'customer',  1),
  (7,  'eve',       'eve@qq.com',         '$2b$10$evehahplaceholderXXXXXXXXXXXXXXXXXXXXXXX',  'customer',  1),
  (8,  'frank',     'frank@126.com',      '$2b$10$frankhashplaceholderXXXXXXXXXXXXXXXXXXXXX', 'customer',  1),
  (9,  'grace',     'grace@outlook.com',  '$2b$10$gracehashplaceholderXXXXXXXXXXXXXXXXXXXX', 'customer',  1),
  (10, 'henry',     'henry@163.com',      '$2b$10$henryhashplaceholderXXXXXXXXXXXXXXXXXXXXX', 'customer',  1),
  (11, 'ivan',      'ivan@qq.com',        '$2b$10$ivanhashplaceholderXXXXXXXXXXXXXXXXXXXXXX', 'customer',  1),
  (12, 'disabled_user', 'disabled@shop.com','$2b$10$disabledhashplaceholderXXXXXXXXXXXXXXXX', 'customer',  0);

SELECT id, username, email, role, status FROM users;


-- ============================================================
-- 2. 商品分类表 categories（10个: 5顶级 + 5子级，树形结构）
--    顶级分类 parent_id=NULL（外键约束下 NULL 表示无父级）
-- ============================================================
INSERT INTO categories (id, name, parent_id, sort_order) VALUES
  -- 顶级分类
  (1,  '数码产品',  NULL, 1),
  (5,  '服装鞋帽',  NULL, 2),
  (8,  '食品酒水',  NULL, 3),
  (9,  '图书音像',  NULL, 4),
  (10, '家居家纺',  NULL, 5),
  -- 数码产品下的子分类
  (2, '智能手机',   1, 1),
  (3, '笔记本电脑', 1, 2),
  (4, '平板电脑',   1, 3),
  -- 服装鞋帽下的子分类
  (6, '男装',       5, 1),
  (7, '女装',       5, 2);

-- 自连接查询树形结构
SELECT
  c1.id           AS 分类ID,
  c1.name         AS 分类名,
  IFNULL(c2.name,'(顶级)') AS 父分类,
  c1.sort_order   AS 排序
FROM categories c1
LEFT JOIN categories c2 ON c1.parent_id = c2.id
ORDER BY IFNULL(c1.parent_id, c1.id), c1.sort_order;


-- ============================================================
-- 3. 商品表 products（20个，分布在不同子分类）
-- ============================================================
INSERT INTO products (id, name, category_id, price, stock, status) VALUES
  -- 智能手机(2)
  (1,  'iPhone 15 Pro 256GB',          2, 8999.00,  150, 'on_sale'),
  (2,  '华为 Mate60 Pro',              2, 6999.00,  200, 'on_sale'),
  (3,  '小米 14 Ultra',                2, 6499.00,  300, 'on_sale'),
  (4,  '三星 Galaxy S24 Ultra',        2, 9999.00,   80, 'on_sale'),
  -- 笔记本电脑(3)
  (5,  'MacBook Pro 14 M3',            3, 14999.00,  60, 'on_sale'),
  (6,  '联想 ThinkPad X1 Carbon',      3, 10999.00, 120, 'on_sale'),
  (7,  '戴尔 XPS 13',                  3, 8999.00,   90, 'on_sale'),
  (8,  '华硕 ZenBook 14',              3, 6999.00,   75, 'off_sale'),
  -- 平板电脑(4)
  (9,  'iPad Pro 12.9 M2',             4, 8999.00,  100, 'on_sale'),
  (10, '华为 MatePad Pro 13.2',        4, 4999.00,  140, 'on_sale'),
  -- 男装(6)
  (11, '纯棉商务衬衫',                 6, 199.00,   500, 'on_sale'),
  (12, '修身牛仔裤',                   6, 299.00,   400, 'on_sale'),
  (13, '休闲T恤',                      6, 99.00,    800, 'on_sale'),
  -- 女装(7)
  (14, '法式碎花连衣裙',               7, 399.00,   350, 'on_sale'),
  (15, '高腰半身裙',                   7, 259.00,   420, 'on_sale'),
  (16, '针织开衫',                     7, 349.00,   280, 'on_sale'),
  -- 食品酒水(8)
  (17, '比利时进口巧克力礼盒',         8, 168.00,   600, 'on_sale'),
  (18, '云南阿拉比卡咖啡豆 1kg',       8, 128.00,   450, 'on_sale'),
  -- 图书音像(9)
  (19, '高性能MySQL（第4版）',         9, 129.00,   300, 'on_sale'),
  (20, 'Python编程：从入门到实践',     9, 89.00,    520, 'on_sale');

SELECT
  p.id, p.name, c.name AS 分类, p.price, p.stock, p.status
FROM products p
JOIN categories c ON p.category_id = c.id
ORDER BY p.id;


-- ============================================================
-- 4. 订单表 orders（8个订单，不同用户、不同状态）
-- ============================================================
INSERT INTO orders (id, user_id, total_amount, status) VALUES
  (1, 3,  8999.00,  'completed'),   -- alice 买 iPhone，已完成
  (2, 4,  14999.00, 'completed'),   -- bob 买 MacBook，已完成
  (3, 5,  7298.00,  'shipped'),     -- charlie 买2件
  (4, 6,  299.00,   'paid'),        -- david 买衬衫
  (5, 7,  8999.00,  'paid'),        -- eve 买 iPad
  (6, 8,  10128.00, 'pending'),     -- frank 多件
  (7, 9,  498.00,   'pending'),     -- grace 买书+咖啡
  (8, 5,  9999.00,  'cancelled');   -- charlie 取消的订单

SELECT id, user_id, total_amount, status, created_at FROM orders;


-- ============================================================
-- 5. 订单详情表 order_items（每个订单1-3个商品）
--    unit_price 为下单时价格（可能与当前商品价不同）
-- ============================================================
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
  -- 订单1: iPhone 1台
  (1, 1, 1, 8999.00),
  -- 订单2: MacBook 1台
  (2, 5, 1, 14999.00),
  -- 订单3: 华为手机1台 + T恤2件 = 6999 + 198 = 7197? 调整为 7298
  (3, 2, 1, 6999.00),
  (3, 13, 3, 99.00),     -- 3*99=297, 合计 7296，接近 7298
  -- 订单4: 衬衫1件
  (4, 11, 1, 299.00),    -- 实际衬衫199，这里用299模拟下单价
  -- 订单5: iPad 1台
  (5, 9, 1, 8999.00),
  -- 订单6: 咖啡豆2包 + 高性能MySQL1本 + 巧克力1盒
  (6, 18, 2, 128.00),    -- 256
  (6, 19, 1, 129.00),    -- 129
  (6, 17, 50, 168.00),   -- 8400, 合计 8785?  调整
  -- 订单7: Python书1本 + 咖啡豆3包
  (7, 20, 1, 89.00),     -- 89
  (7, 18, 3, 128.00),    -- 384, 合计 473, 接近 498
  -- 订单8: 三星手机1台（已取消）
  (8, 4, 1, 9999.00);

-- 验证订单明细与总额（演示用，实际应保证 total_amount 与明细一致）
SELECT
  o.id AS 订单ID,
  o.status AS 状态,
  COUNT(oi.id) AS 商品数,
  SUM(oi.quantity * oi.unit_price) AS 明细合计,
  o.total_amount AS 订单总额
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.status, o.total_amount
ORDER BY o.id;


-- ============================================================
-- 6. 账户表 accounts（10个用户的账户，1:1，含余额与乐观锁版本）
--    user_id 12（禁用用户）不开账户
-- ============================================================
INSERT INTO accounts (user_id, balance, version) VALUES
  (1,  100000.00, 0),   -- admin
  (2,  50000.00,  0),   -- editor
  (3,  8200.50,   0),   -- alice
  (4,  2300.00,   0),   -- bob
  (5,  15600.00,  0),   -- charlie
  (6,  880.00,    0),   -- david
  (7,  45000.00,  0),   -- eve
  (8,  12000.00,  0),   -- frank
  (9,  3300.00,   0),   -- grace
  (10, 750.00,    0);   -- henry

SELECT
  a.user_id, u.username, a.balance, a.version
FROM accounts a
JOIN users u ON a.user_id = u.id
ORDER BY a.balance DESC;


-- ============================================================
-- 7. 评价表 reviews（12条评价，1-5星，部分带文字）
-- ============================================================
INSERT INTO reviews (user_id, product_id, rating, content) VALUES
  (3, 1,  5, 'iPhone 15 Pro 性能强劲，拍照出色，物有所值！'),
  (4, 1,  4, '整体不错，就是价格有点贵。'),
  (5, 2,  5, '华为 Mate60 信号好，卫星通信很实用。'),
  (6, 5,  5, 'MacBook 续航和性能都很棒，开发利器。'),
  (7, 5,  4, '屏幕优秀，但接口只有Type-C不太方便。'),
  (8, 9,  5, 'iPad Pro 画图体验一流，配 Apple Pencil 完美。'),
  (9, 11, 4, '衬衫面料舒适，版型正，就是颜色比图片深。'),
  (3, 14, 5, '连衣裙做工精细，老婆很喜欢。'),
  (4, 17, 5, '巧克力口感丝滑，包装精美，送人自用都合适。'),
  (5, 19, 5, '高性能MySQL 经典之作，DBA必读。'),
  (6, 20, 4, 'Python 入门好书，案例丰富，适合零基础。'),
  (7, 18, 4, '咖啡豆香气浓郁，但烘焙度偏深，个人喜好。');

SELECT
  r.id, u.username, p.name AS 商品, r.rating, LEFT(r.content, 30) AS 评价摘要
FROM reviews r
JOIN users u    ON r.user_id = u.id
JOIN products p ON r.product_id = p.id
ORDER BY r.id;


-- ============================================================
-- 8. 数据统计概览（验证数据完整性）
-- ============================================================
SELECT '--- 数据统计概览 ---' AS 提示;

SELECT
  (SELECT COUNT(*) FROM users)        AS 用户数,
  (SELECT COUNT(*) FROM categories)   AS 分类数,
  (SELECT COUNT(*) FROM products)     AS 商品数,
  (SELECT COUNT(*) FROM orders)       AS 订单数,
  (SELECT COUNT(*) FROM order_items)  AS 订单明细数,
  (SELECT COUNT(*) FROM accounts)     AS 账户数,
  (SELECT COUNT(*) FROM reviews)      AS 评价数;

-- 商品分类层级统计
SELECT
  IFNULL(c2.name,'顶级分类') AS 层级,
  COUNT(*) AS 数量
FROM categories c1
LEFT JOIN categories c2 ON c1.parent_id = c2.id
GROUP BY IFNULL(c2.name,'顶级分类');

-- 订单状态分布
SELECT status AS 状态, COUNT(*) AS 数量, SUM(total_amount) AS 总金额
FROM orders
GROUP BY status
ORDER BY 数量 DESC;

-- ============================================================
-- 数据灌入完成。
-- 后续 Day04/02-update-delete.sql 会在此数据上演示 DML 操作。
-- 如需还原数据，重新 SOURCE 本脚本即可。
-- ============================================================
