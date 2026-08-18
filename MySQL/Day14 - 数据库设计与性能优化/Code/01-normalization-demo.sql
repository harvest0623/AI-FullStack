-- ============================================================
-- 文件名称: 01-normalization-demo.sql
-- 文件用途: 数据库范式与反范式演示脚本
--           1. 反例表（违反 1NF/2NF/3NF）
--           2. 拆分到 1NF（列原子性）
--           3. 拆分到 2NF（消除部分依赖）
--           4. 拆分到 3NF（消除传递依赖）
--           5. 反范式：冗余字段提升查询性能
--           6. 范式 vs 反范式 SELECT 对比
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day14 - 数据库设计与性能优化/Code/01-normalization-demo.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 0. 清理旧表（保证可重复执行）
-- ============================================================
DROP TABLE IF EXISTS bad_order_detail;
DROP TABLE IF EXISTS nf1_order_detail;
DROP TABLE IF EXISTS nf2_order_detail;
DROP TABLE IF EXISTS nf2_products;
DROP TABLE IF EXISTS nf3_order_detail;
DROP TABLE IF EXISTS nf3_products;
DROP TABLE IF EXISTS nf3_categories;
DROP TABLE IF EXISTS denorm_order_detail;

-- ============================================================
-- 1. 反例表：违反三大范式的"屎山"设计
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 创建反例表
--     违反 1NF：address 列含"省市区"（可拆分）
--     违反 2NF：联合主键 (order_id, product_id)，但 product_name/product_price 只依赖 product_id
--     违反 3NF：product_category_name 依赖 product_category_id，category_id 依赖 product_id，传递依赖
--     违反 3NF：user_email 依赖 user_id，user_id 依赖 order_id，传递依赖
-- ------------------------------------------------------------
CREATE TABLE bad_order_detail (
    order_id               BIGINT,
    product_id             INT,
    quantity               INT,
    unit_price             DECIMAL(10,2),
    product_name           VARCHAR(100),    -- 只依赖 product_id（违反 2NF）
    product_price          DECIMAL(10,2),   -- 只依赖 product_id（违反 2NF）
    product_category_id    INT,             -- 只依赖 product_id（违反 2NF）
    product_category_name  VARCHAR(50),     -- 依赖 category_id，传递依赖（违反 3NF）
    user_id                INT,             -- 依赖 order_id（这部分 OK）
    user_name              VARCHAR(50),     -- 依赖 user_id，传递依赖（违反 3NF）
    user_email             VARCHAR(100),    -- 依赖 user_id，传递依赖（违反 3NF）
    user_address           VARCHAR(200),    -- 含省市区，可拆分（违反 1NF）
    PRIMARY KEY (order_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='反例表：违反三大范式';

-- ------------------------------------------------------------
-- 1.2 插入示例数据（重复冗余明显）
--     注意：同一个 product_name/category_name 在不同订单中重复存储
-- ------------------------------------------------------------
INSERT INTO bad_order_detail VALUES
(1001, 1, 2, 99.00, 'iPhone 15', 99.00, 1, '手机数码', 1, 'alice', 'alice@x.com', '北京市海淀区中关村'),
(1001, 2, 1, 199.00, 'AirPods Pro', 199.00, 1, '手机数码', 1, 'alice', 'alice@x.com', '北京市海淀区中关村'),
(1002, 1, 1, 99.00, 'iPhone 15', 99.00, 1, '手机数码', 2, 'bob', 'bob@x.com', '上海市浦东新区张江'),
(1002, 3, 3, 59.00, '手机壳', 59.00, 2, '配件', 2, 'bob', 'bob@x.com', '上海市浦东新区张江'),
(1003, 2, 2, 199.00, 'AirPods Pro', 199.00, 1, '手机数码', 3, 'carol', 'carol@x.com', '广州市天河区珠江新城');

-- ------------------------------------------------------------
-- 1.3 查看反例表：冗余严重
--     问题：
--     - alice 的信息在 order 1001 的两条明细中重复
--     - iPhone 15 的商品信息在 1001、1002 中重复
--     - 手机数码分类名在三处重复
--     - 修改商品名要更新多行，易不一致
-- ------------------------------------------------------------
SELECT * FROM bad_order_detail;

-- ============================================================
-- 2. 拆分到 1NF：列的原子性
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 把 user_address 拆为 province / city / district / street
--     其他问题暂不处理，仅解决 1NF 违反
-- ------------------------------------------------------------
CREATE TABLE nf1_order_detail (
    order_id               BIGINT,
    product_id             INT,
    quantity               INT,
    unit_price             DECIMAL(10,2),
    product_name           VARCHAR(100),
    product_price          DECIMAL(10,2),
    product_category_id    INT,
    product_category_name  VARCHAR(50),
    user_id                INT,
    user_name              VARCHAR(50),
    user_email             VARCHAR(100),
    province               VARCHAR(50),   -- 拆分后的省
    city                   VARCHAR(50),   -- 市
    district               VARCHAR(50),   -- 区
    street                 VARCHAR(100),  -- 街道
    PRIMARY KEY (order_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='1NF：地址拆分';

INSERT INTO nf1_order_detail VALUES
(1001, 1, 2, 99.00, 'iPhone 15', 99.00, 1, '手机数码', 1, 'alice', 'alice@x.com', '北京市', '北京市', '海淀区', '中关村'),
(1001, 2, 1, 199.00, 'AirPods Pro', 199.00, 1, '手机数码', 1, 'alice', 'alice@x.com', '北京市', '北京市', '海淀区', '中关村'),
(1002, 1, 1, 99.00, 'iPhone 15', 99.00, 1, '手机数码', 2, 'bob', 'bob@x.com', '上海市', '上海市', '浦东新区', '张江'),
(1002, 3, 3, 59.00, '手机壳', 59.00, 2, '配件', 2, 'bob', 'bob@x.com', '上海市', '上海市', '浦东新区', '张江'),
(1003, 2, 2, 199.00, 'AirPods Pro', 199.00, 1, '手机数码', 3, 'carol', 'carol@x.com', '广州市', '广州市', '天河区', '珠江新城');

-- 验证 1NF：每列不可再分
SELECT order_id, product_id, user_name, province, city, district, street
FROM nf1_order_detail;

-- ============================================================
-- 3. 拆分到 2NF：消除部分依赖
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 把只依赖 product_id 的列拆到 products 表
--     order_detail 只保留 (order_id, product_id, quantity, unit_price, user_*)
--     注意：unit_price 虽然与 product_price 相关，但记录的是"下单时价格"，
--           应保留在 order_detail 中（这是历史快照，不是冗余）
-- ------------------------------------------------------------
CREATE TABLE nf2_products (
    product_id          INT PRIMARY KEY,
    product_name        VARCHAR(100),
    product_price       DECIMAL(10,2),
    product_category_id INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='2NF：商品表';

CREATE TABLE nf2_order_detail (
    order_id     BIGINT,
    product_id   INT,
    quantity     INT,
    unit_price   DECIMAL(10,2),   -- 下单时单价快照，保留
    user_id      INT,
    user_name    VARCHAR(50),
    user_email   VARCHAR(100),
    province     VARCHAR(50),
    city         VARCHAR(50),
    district     VARCHAR(50),
    street       VARCHAR(100),
    PRIMARY KEY (order_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='2NF：订单明细（仅依赖联合主键的列）';

INSERT INTO nf2_products VALUES
(1, 'iPhone 15', 99.00, 1),
(2, 'AirPods Pro', 199.00, 1),
(3, '手机壳', 59.00, 2);

INSERT INTO nf2_order_detail VALUES
(1001, 1, 2, 99.00, 1, 'alice', 'alice@x.com', '北京市', '北京市', '海淀区', '中关村'),
(1001, 2, 1, 199.00, 1, 'alice', 'alice@x.com', '北京市', '北京市', '海淀区', '中关村'),
(1002, 1, 1, 99.00, 2, 'bob', 'bob@x.com', '上海市', '上海市', '浦东新区', '张江'),
(1002, 3, 3, 59.00, 2, 'bob', 'bob@x.com', '上海市', '上海市', '浦东新区', '张江'),
(1003, 2, 2, 199.00, 3, 'carol', 'carol@x.com', '广州市', '广州市', '天河区', '珠江新城');

-- ------------------------------------------------------------
-- 3.2 查询需要 JOIN 商品表
--     商品信息不再冗余存储，修改商品名只需改 products 一行
-- ------------------------------------------------------------
SELECT
    od.order_id,
    od.product_id,
    p.product_name,
    p.product_price,
    od.quantity,
    od.unit_price
FROM nf2_order_detail od
JOIN nf2_products p ON p.product_id = od.product_id;

-- ============================================================
-- 4. 拆分到 3NF：消除传递依赖
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 把分类信息拆到 categories 表
--     把用户信息拆到 users 表
--     order_detail 只保留外键引用
-- ------------------------------------------------------------
CREATE TABLE nf3_categories (
    category_id   INT PRIMARY KEY,
    category_name VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='3NF：分类表';

CREATE TABLE nf3_products (
    product_id          INT PRIMARY KEY,
    product_name        VARCHAR(100),
    product_price       DECIMAL(10,2),
    product_category_id INT,
    CONSTRAINT fk_prod_cat FOREIGN KEY (product_category_id) REFERENCES nf3_categories(category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='3NF：商品表';

CREATE TABLE nf3_order_detail (
    order_id     BIGINT,
    product_id   INT,
    quantity     INT,
    unit_price   DECIMAL(10,2),
    user_id      INT,             -- 仅保留外键，不再存 user_name/email/address
    PRIMARY KEY (order_id, product_id),
    CONSTRAINT fk_od_prod FOREIGN KEY (product_id) REFERENCES nf3_products(product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='3NF：订单明细（无传递依赖）';

INSERT INTO nf3_categories VALUES
(1, '手机数码'),
(2, '配件');

INSERT INTO nf3_products VALUES
(1, 'iPhone 15', 99.00, 1),
(2, 'AirPods Pro', 199.00, 1),
(3, '手机壳', 59.00, 2);

INSERT INTO nf3_order_detail VALUES
(1001, 1, 2, 99.00, 1),
(1001, 2, 1, 199.00, 1),
(1002, 1, 1, 99.00, 2),
(1002, 3, 3, 59.00, 2),
(1003, 2, 2, 199.00, 3);

-- ------------------------------------------------------------
-- 4.2 完整查询需要三表 JOIN
--     但每条信息只存一处，修改无冗余风险
-- ------------------------------------------------------------
SELECT
    od.order_id,
    od.product_id,
    p.product_name,
    p.product_price,
    c.category_name,
    od.quantity,
    od.unit_price,
    od.user_id
FROM nf3_order_detail od
JOIN nf3_products p     ON p.product_id = od.product_id
JOIN nf3_categories c   ON c.category_id = p.product_category_id;

-- ============================================================
-- 5. 反范式：冗余字段提升查询性能
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 场景：订单列表页要显示商品名、用户名
--     3NF 下每次查都要 JOIN products + users
--     高并发时 JOIN 开销大
--     反范式：在 order_detail 冗余 product_name 与 user_name
--     代价：商品改名时需同步更新所有历史订单（或接受历史快照）
-- ------------------------------------------------------------
CREATE TABLE denorm_order_detail (
    order_id       BIGINT,
    product_id     INT,
    quantity       INT,
    unit_price     DECIMAL(10,2),
    product_name   VARCHAR(100),   -- 冗余字段（下单时快照）
    user_id        INT,
    user_name      VARCHAR(50),    -- 冗余字段（下单时快照）
    PRIMARY KEY (order_id, product_id),
    INDEX idx_user(user_id),
    INDEX idx_product(product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='反范式：冗余商品名与用户名';

INSERT INTO denorm_order_detail VALUES
(1001, 1, 2, 99.00,  'iPhone 15',    1, 'alice'),
(1001, 2, 1, 199.00, 'AirPods Pro',  1, 'alice'),
(1002, 1, 1, 99.00,  'iPhone 15',    2, 'bob'),
(1002, 3, 3, 59.00,  '手机壳',        2, 'bob'),
(1003, 2, 2, 199.00, 'AirPods Pro',  3, 'carol');

-- ------------------------------------------------------------
-- 5.2 反范式查询：无需 JOIN，单表直出
-- ------------------------------------------------------------
SELECT order_id, product_id, product_name, quantity, unit_price, user_id, user_name
FROM denorm_order_detail;

-- ============================================================
-- 6. 范式 vs 反范式 SELECT 对比
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 范式（3NF）查询：需 2 个 JOIN
--     优势：数据无冗余，改名只改一处
--     劣势：JOIN 开销
-- ------------------------------------------------------------
EXPLAIN
SELECT od.order_id, p.product_name, od.quantity, od.unit_price
FROM nf3_order_detail od
JOIN nf3_products p ON p.product_id = od.product_id;

-- ------------------------------------------------------------
-- 6.2 反范式查询：单表
--     优势：无 JOIN，查询快
--     劣势：商品名冗余，改名需同步多处
-- ------------------------------------------------------------
EXPLAIN
SELECT order_id, product_name, quantity, unit_price
FROM denorm_order_detail;

-- ------------------------------------------------------------
-- 6.3 对比要点：
--     - 范式查询的 EXPLAIN 中有 2 行（2 张表），type 可能是 ref/eq_ref
--     - 反范式查询只有 1 行，type 是 index/ALL
--     - 反范式省了 JOIN，但增加了存储与更新成本
-- ============================================================

-- ============================================================
-- 7. 反范式另一种场景：冗余统计字段
-- ============================================================

-- ------------------------------------------------------------
-- 7.1 在 products 表加 sold_count 字段（已存在的 ecommerce.products 没有）
--     创建演示表展示思路
-- ------------------------------------------------------------
DROP TABLE IF EXISTS denorm_products;
CREATE TABLE denorm_products (
    id          INT PRIMARY KEY,
    name        VARCHAR(100),
    price       DECIMAL(10,2),
    sold_count  INT DEFAULT 0 COMMENT '冗余销量字段，由触发器或定时任务维护'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='反范式：冗余销量';

INSERT INTO denorm_products(id, name, price) VALUES
(1, 'iPhone 15', 99.00),
(2, 'AirPods Pro', 199.00),
(3, '手机壳', 59.00);

-- ------------------------------------------------------------
-- 7.2 范式下查销量 Top 3：需 JOIN + GROUP BY + ORDER BY
--     数据量大时慢
-- ------------------------------------------------------------
SELECT p.id, p.name, COALESCE(SUM(od.quantity), 0) AS sold
FROM denorm_products p
LEFT JOIN nf3_order_detail od ON od.product_id = p.id
GROUP BY p.id, p.name
ORDER BY sold DESC
LIMIT 3;

-- ------------------------------------------------------------
-- 7.3 反范式下查销量 Top 3：直接读冗余字段
--     先用上面的查询结果更新 sold_count
-- ------------------------------------------------------------
UPDATE denorm_products p
SET sold_count = (
    SELECT COALESCE(SUM(od.quantity), 0)
    FROM nf3_order_detail od
    WHERE od.product_id = p.id
);

SELECT id, name, sold_count
FROM denorm_products
ORDER BY sold_count DESC
LIMIT 3;

-- ------------------------------------------------------------
-- 7.4 对比执行计划
-- ------------------------------------------------------------
EXPLAIN
SELECT p.id, p.name, COALESCE(SUM(od.quantity), 0) AS sold
FROM denorm_products p
LEFT JOIN nf3_order_detail od ON od.product_id = p.id
GROUP BY p.id, p.name
ORDER BY sold DESC
LIMIT 3;

EXPLAIN
SELECT id, name, sold_count
FROM denorm_products
ORDER BY sold_count DESC
LIMIT 3;

-- ============================================================
-- 8. 清理演示表（可选）
-- ============================================================
-- 如需保留演示表，注释掉以下语句
-- DROP TABLE IF EXISTS bad_order_detail;
-- DROP TABLE IF EXISTS nf1_order_detail;
-- DROP TABLE IF EXISTS nf2_order_detail;
-- DROP TABLE IF EXISTS nf2_products;
-- DROP TABLE IF EXISTS nf3_order_detail;
-- DROP TABLE IF EXISTS nf3_products;
-- DROP TABLE IF EXISTS nf3_categories;
-- DROP TABLE IF EXISTS denorm_order_detail;
-- DROP TABLE IF EXISTS denorm_products;

-- ============================================================
-- 范式演示完毕。
-- 关键结论：
--   1) 1NF：列原子性（地址拆省市区）
--   2) 2NF：联合主键表中，非主键列完全依赖整个主键（拆商品表）
--   3) 3NF：消除传递依赖（拆分类表、用户表）
--   4) 反范式：为读性能冗余字段，代价是更新成本
--   5) 历史快照（如下单时单价）不算冗余，是必要字段
--   6) 选择范式还是反范式，看读写比例与一致性要求
-- ============================================================
