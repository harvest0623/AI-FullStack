-- ============================================================
-- 文件名称: 02-alter-table.sql
-- 文件用途: 演示 ALTER TABLE 各类表结构修改操作
--           含: 加列 / 改列类型 / 改列名 / 删列 / 改表名 /
--               加索引 / 删索引 / 改字符集 / 加约束
--           每步带 SELECT 或 DESC 验证，全部基于 ecommerce 库
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day02/Code/02-alter-table.sql
-- 注意:    本脚本会修改 ecommerce 表结构，建议执行后可重新
--           source 01-create-ecommerce.sql 还原结构
-- ============================================================

USE ecommerce;

-- ============================================================
-- 演示一: ADD COLUMN 加列
-- ============================================================

-- 1.1 给 users 加一列 phone（手机号）
ALTER TABLE users
  ADD COLUMN phone VARCHAR(20) NULL COMMENT '手机号' AFTER email;

DESC users;
-- 应能看到 phone 列位于 email 之后

-- 1.2 给 products 加列: sku 编码、销量、是否推荐
ALTER TABLE products
  ADD COLUMN sku        VARCHAR(50)  NOT NULL DEFAULT '' COMMENT 'SKU编码',
  ADD COLUMN sold_count INT          NOT NULL DEFAULT 0  COMMENT '销量',
  ADD COLUMN is_hot     TINYINT(1)   NOT NULL DEFAULT 0  COMMENT '是否热销 0/1';

DESC products;

-- 1.3 给 orders 加收货地址、备注
ALTER TABLE orders
  ADD COLUMN shipping_address VARCHAR(300) NULL COMMENT '收货地址',
  ADD COLUMN remark           VARCHAR(200) NULL COMMENT '订单备注';

DESC orders;


-- ============================================================
-- 演示二: MODIFY COLUMN 改列类型/位置/默认值（不改列名）
-- ============================================================

-- 2.1 把 users.phone 长度从 20 改为 32
ALTER TABLE users MODIFY COLUMN phone VARCHAR(32) NULL COMMENT '手机号(扩展)';

DESC users;

-- 2.2 把 products.sku 默认值改为 NULL，且允许空
ALTER TABLE products MODIFY COLUMN sku VARCHAR(50) NULL DEFAULT NULL COMMENT 'SKU编码(可空)';

DESC products;

-- 2.3 把 orders.remark 移到 status 之后（FIRST / AFTER col）
ALTER TABLE orders MODIFY COLUMN remark VARCHAR(200) NULL COMMENT '订单备注' AFTER status;

DESC orders;


-- ============================================================
-- 演示三: CHANGE COLUMN 同时改列名 + 类型
-- ============================================================

-- 3.1 把 products.is_hot 改名为 is_featured，类型不变
ALTER TABLE products CHANGE COLUMN is_hot is_featured TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否推荐 0/1';

DESC products;

-- 3.2 把 orders.remark 改名为 buyer_remark，类型扩展为 TEXT
ALTER TABLE orders CHANGE COLUMN remark buyer_remark TEXT NULL COMMENT '买家备注';

DESC orders;


-- ============================================================
-- 演示四: DROP COLUMN 删列
-- ============================================================

-- 4.1 删除 users.phone（演示完恢复）
ALTER TABLE users DROP COLUMN phone;

DESC users;

-- 4.2 删除 products.sold_count
ALTER TABLE products DROP COLUMN sold_count;

DESC products;


-- ============================================================
-- 演示五: RENAME TO 改表名（演示完恢复）
-- ============================================================

-- 5.1 把 reviews 改名为 product_reviews
ALTER TABLE reviews RENAME TO product_reviews;

SHOW TABLES LIKE 'product%';

-- 5.2 改回原名
ALTER TABLE product_reviews RENAME TO reviews;

SHOW TABLES LIKE 'reviews';


-- ============================================================
-- 演示六: ADD INDEX / DROP INDEX 索引操作
-- ============================================================

-- 6.1 给 products.name 加普通索引
ALTER TABLE products ADD INDEX idx_product_name (name);

-- 6.2 给 orders 加复合索引 (user_id, status)
ALTER TABLE orders ADD INDEX idx_order_user_status (user_id, status);

-- 6.3 给 products.category_id 加索引
ALTER TABLE products ADD INDEX idx_product_category (category_id);

-- 查看索引
SHOW INDEX FROM products;
SHOW INDEX FROM orders;

-- 6.4 删除索引
ALTER TABLE products DROP INDEX idx_product_name;
ALTER TABLE orders   DROP INDEX idx_order_user_status;
ALTER TABLE products DROP INDEX idx_product_category;

SHOW INDEX FROM products;
SHOW INDEX FROM orders;

-- 6.5 也可用 CREATE INDEX / DROP INDEX 语法（等价）
CREATE INDEX idx_product_name ON products(name);
DROP INDEX idx_product_name ON products;


-- ============================================================
-- 演示七: ADD CONSTRAINT 添加约束（唯一约束 / 主键 / 外键）
-- ============================================================

-- 7.1 给 products.sku 加唯一索引（允许 NULL，NULL 不参与唯一性）
ALTER TABLE products ADD UNIQUE INDEX uk_product_sku (sku);

SHOW INDEX FROM products;

-- 7.2 给 accounts.balance 加 CHECK 约束（余额不能为负，MySQL 8 真正支持）
ALTER TABLE accounts
  ADD CONSTRAINT chk_balance_nonnegative CHECK (balance >= 0);

-- 查看约束
SELECT
  table_name      AS 表名,
  constraint_name AS 约束名,
  constraint_type AS 约束类型
FROM information_schema.table_constraints
WHERE table_schema = 'ecommerce'
  AND constraint_type = 'CHECK';


-- ============================================================
-- 演示八: ALTER 修改表选项（引擎、字符集、注释）
-- ============================================================

-- 8.1 修改表注释
ALTER TABLE products COMMENT='商品表（含SKU与销量）';

SHOW TABLE STATUS LIKE 'products'\G

-- 8.2 修改表字符集（演示用，ecommerce 本身已是 utf8mb4）
-- ALTER TABLE products CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


-- ============================================================
-- 演示九: ADD COLUMN 加带默认值与表达式的列（8.0 支持表达式默认值）
-- ============================================================

-- 9.1 给 products 加创建日期列，默认当前日期
ALTER TABLE products
  ADD COLUMN list_date DATE NOT NULL DEFAULT (CURRENT_DATE) COMMENT '上架日期';

DESC products;

SELECT
  column_name        AS 列名,
  column_default     AS 默认值,
  column_comment     AS 注释
FROM information_schema.columns
WHERE table_schema = 'ecommerce' AND table_name = 'products' AND column_name = 'list_date';


-- ============================================================
-- 演示十: 综合验证 - 最终表结构概览
-- ============================================================

-- 查看 ecommerce 所有表当前结构概要
SELECT
  t.table_name  AS 表名,
  t.table_comment AS 表注释,
  COUNT(c.column_name) AS 列数
FROM information_schema.tables t
JOIN information_schema.columns c
  ON t.table_schema = c.table_schema AND t.table_name = c.table_name
WHERE t.table_schema = 'ecommerce'
GROUP BY t.table_name, t.table_comment
ORDER BY t.table_name;

-- 查看每张表的索引数量
SELECT
  table_name  AS 表名,
  COUNT(DISTINCT index_name) AS 索引数
FROM information_schema.statistics
WHERE table_schema = 'ecommerce'
GROUP BY table_name
ORDER BY table_name;

-- ============================================================
-- 还原提示:
-- 本脚本对 ecommerce 表结构做了若干修改（加列、改名等）。
-- 如需还原到 Day02 初始结构，请重新执行:
--   SOURCE 01-create-ecommerce.sql
-- ============================================================
