-- ============================================================
-- 文件名称: 01-create-index.sql
-- 文件用途: 为 ecommerce 各表创建索引（主键/唯一/普通/联合/前缀）
--           对比建索引前后 EXPLAIN 输出，直观感受索引对查询的影响
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day10 - 索引与执行计划/Code/01-create-index.sql
-- 前置条件: ecommerce 库及 7 张表已存在（Day02-Day04 已创建）
-- ============================================================

USE ecommerce;

-- ============================================================
-- 第一部分：建索引前的"全表扫描"现状
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 查看 products 表当前索引（仅有主键聚簇索引）
-- ------------------------------------------------------------
SHOW INDEX FROM products;

-- ------------------------------------------------------------
-- 1.2 在无 name 索引时查询商品：type 应为 ALL（全表扫描）
--     重点看 type=ALL、key=NULL、rows=全表行数
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE name = 'iPhone 15 Pro';

-- ------------------------------------------------------------
-- 1.3 在无 category_id 索引时按分类查询：type 应为 ALL
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE category_id = 5;

-- ------------------------------------------------------------
-- 1.4 在无 user_id 索引时查询用户订单：type 应为 ALL
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM orders WHERE user_id = 100;


-- ============================================================
-- 第二部分：创建各类索引
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 普通索引：products(name)
--     加速按商品名等值/前缀匹配查询
-- ------------------------------------------------------------
CREATE INDEX idx_products_name ON products(name);
-- 等价写法：
-- ALTER TABLE products ADD INDEX idx_products_name (name);

-- ------------------------------------------------------------
-- 2.2 联合索引：products(category_id, status)
--     典型场景：按分类 + 状态筛选商品（如"手机分类下在售商品"）
--     遵循最左前缀原则：可命中 WHERE category_id=? 也可命中 WHERE category_id=? AND status=?
-- ------------------------------------------------------------
CREATE INDEX idx_products_cat_status ON products(category_id, status);

-- ------------------------------------------------------------
-- 2.3 联合索引（含排序列）：products(category_id, status, price)
--     在前两者基础上纳入 price，支持 ORDER BY price 免 filesort
--     注意：等值列在前、范围/排序列在后的设计原则
-- ------------------------------------------------------------
CREATE INDEX idx_products_cat_status_price ON products(category_id, status, price);

-- ------------------------------------------------------------
-- 2.4 联合索引：orders(user_id, created_at)
--     场景：查某用户某时间段的订单，按时间倒序
--     user_id 等值在前、created_at 范围/排序在后
-- ------------------------------------------------------------
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at);

-- ------------------------------------------------------------
-- 2.5 普通索引：order_items(order_id)
--     场景：按订单号查明细，是 JOIN 高频列
-- ------------------------------------------------------------
CREATE INDEX idx_order_items_order_id ON order_items(order_id);

-- ------------------------------------------------------------
-- 2.6 普通索引：reviews(product_id)
--     场景：商品评价列表，按商品查评价
-- ------------------------------------------------------------
CREATE INDEX idx_reviews_product_id ON reviews(product_id);

-- ------------------------------------------------------------
-- 2.7 唯一索引：users(email)
--     业务上 email 不能重复，UNIQUE 既加速又防重
-- ------------------------------------------------------------
CREATE UNIQUE INDEX uk_users_email ON users(email);

-- ------------------------------------------------------------
-- 2.8 前缀索引：users(username(20))
--     场景：username 是 VARCHAR(50)，只索引前 20 字符节省空间
--     注意：前缀索引不支持覆盖索引
-- ------------------------------------------------------------
CREATE INDEX idx_users_username_prefix ON users(username(20));

-- ------------------------------------------------------------
-- 2.9 普通索引：reviews(product_id, rating)
--     联合索引，支持按商品 + 评分筛选
-- ------------------------------------------------------------
CREATE INDEX idx_reviews_product_rating ON reviews(product_id, rating);

-- ------------------------------------------------------------
-- 2.10 函数索引（MySQL 8.0+）：users 上对 LOWER(email) 建索引
--      让 WHERE LOWER(email)=? 走索引
--      注意：若已建 uk_users_email，这里演示用，实际可不必重复
-- ------------------------------------------------------------
-- CREATE INDEX idx_users_lower_email ON users((LOWER(email)));


-- ============================================================
-- 第三部分：建索引后验证
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 查看 products 表全部索引
--     应能看到 PRIMARY、idx_products_name、idx_products_cat_status、idx_products_cat_status_price
-- ------------------------------------------------------------
SHOW INDEX FROM products;

-- ------------------------------------------------------------
-- 3.2 重新 EXPLAIN 查询 name='iPhone 15 Pro'
--     对比 1.2：type 应从 ALL → ref，key 应显示 idx_products_name
--     重点看 type=ref、key=idx_products_name、rows 大幅下降
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE name = 'iPhone 15 Pro';

-- ------------------------------------------------------------
-- 3.3 重新 EXPLAIN 查询 category_id=5
--     对比 1.3：type 应从 ALL → ref
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE category_id = 5;

-- ------------------------------------------------------------
-- 3.4 EXPLAIN 联合索引命中两列：category_id=? AND status=?
--     key=idx_products_cat_status，key_len 应包含 category_id + status 两列长度
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE category_id = 5 AND status = 'on_sale';

-- ------------------------------------------------------------
-- 3.5 EXPLAIN 联合索引命中三列：category_id=? AND status=? AND price>?
--     key=idx_products_cat_status_price，key_len 应最大
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products
WHERE category_id = 5 AND status = 'on_sale' AND price > 1000;

-- ------------------------------------------------------------
-- 3.6 EXPLAIN 订单查询命中联合索引
--     对比 1.4：type 应从 ALL → ref
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM orders WHERE user_id = 100;

-- ------------------------------------------------------------
-- 3.7 EXPLAIN 范围查询：某用户某时间段订单
--     type 应为 range，key=idx_orders_user_created
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM orders
WHERE user_id = 100
  AND created_at BETWEEN '2024-01-01' AND '2024-06-30';

-- ------------------------------------------------------------
-- 3.8 EXPLAIN 唯一索引等值查询：type 应为 const
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM users WHERE email = 'alice@example.com';

-- ------------------------------------------------------------
-- 3.9 EXPLAIN 主键等值查询：type 应为 const
-- ------------------------------------------------------------
EXPLAIN SELECT * FROM products WHERE id = 1;

-- ------------------------------------------------------------
-- 3.10 查看 ANALYZE TABLE 更新统计信息（建索引后建议执行一次）
--      让优化器基于最新统计信息选择执行计划
-- ------------------------------------------------------------
ANALYZE TABLE products;
ANALYZE TABLE orders;
ANALYZE TABLE users;
ANALYZE TABLE order_items;
ANALYZE TABLE reviews;


-- ============================================================
-- 第四部分：索引维护操作演示
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 创建一个用于演示删除的临时索引
-- ------------------------------------------------------------
CREATE INDEX idx_products_price ON products(price);

-- ------------------------------------------------------------
-- 4.2 查看该索引存在
-- ------------------------------------------------------------
SHOW INDEX FROM products WHERE Key_name = 'idx_products_price';

-- ------------------------------------------------------------
-- 4.3 删除该索引（两种等价写法）
-- ------------------------------------------------------------
DROP INDEX idx_products_price ON products;
-- 等价：ALTER TABLE products DROP INDEX idx_products_price;

-- ------------------------------------------------------------
-- 4.4 不可见索引演示（8.0+）：让索引对优化器"暂时失效"
--     场景：上线前验证"删了某索引是否真的不影响业务"
-- ------------------------------------------------------------
CREATE INDEX idx_products_stock ON products(stock);

-- 让 idx_products_stock 不可见（仍维护，但优化器不选）
ALTER TABLE products ALTER INDEX idx_products_stock SET INVISIBLE;

-- EXPLAIN 应不再选 idx_products_stock（key=NULL 或选其他索引）
EXPLAIN SELECT * FROM products WHERE stock = 100;

-- 恢复可见
ALTER TABLE products ALTER INDEX idx_products_stock SET VISIBLE;

-- 现在又能走索引了
EXPLAIN SELECT * FROM products WHERE stock = 100;

-- 验证完删除
DROP INDEX idx_products_stock ON products;


-- ============================================================
-- 第五部分：小结
-- ============================================================
-- 通过本脚本可观察到：
-- 1. 建索引前 type=ALL（全表扫描），建索引后 type=ref/range/const
-- 2. 联合索引可命中多列，通过 key_len 长度判断命中几列
-- 3. 唯一索引等值查询 type=const，是性能最好的查询之一
-- 4. 不可见索引是删除前的灰度验证手段
--
-- 下一步：执行 02-explain-examples.sql 深入学习 EXPLAIN 各字段
-- ============================================================
