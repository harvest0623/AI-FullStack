-- ============================================================
-- 文件名称: 01-create-ecommerce.sql
-- 文件用途: 创建电商示例数据库 ecommerce 及全部 7 张表
--           这是本学习板块的基础库，后续所有天数都基于此库
--           包含完整约束、注释、引擎、字符集
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day02/Code/01-create-ecommerce.sql
-- 表清单:   users / categories / products / orders /
--           order_items / accounts / reviews
-- 外键依赖: users→categories(自)→products→orders→order_items
--           accounts→users, reviews→users+products
-- 删表顺序: 反向，避免外键约束报错
-- ============================================================

-- ------------------------------------------------------------
-- 0. 创建数据库（utf8mb4 + utf8mb4_unicode_ci）
-- ------------------------------------------------------------
DROP DATABASE IF EXISTS ecommerce;
CREATE DATABASE IF NOT EXISTS ecommerce
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ecommerce;

-- ------------------------------------------------------------
-- 1. 删除旧表（按外键依赖反向顺序，保证可重复执行）
-- ------------------------------------------------------------
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

-- ------------------------------------------------------------
-- 2. 用户表 users
--    角色 admin/editor/customer；status 0禁用 1正常；软删除 deleted_at
-- ------------------------------------------------------------
CREATE TABLE users (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
  username      VARCHAR(50)  NOT NULL UNIQUE COMMENT '用户名',
  email         VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
  password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
  role          ENUM('admin','editor','customer') NOT NULL DEFAULT 'customer' COMMENT '角色',
  status        TINYINT NOT NULL DEFAULT 1 COMMENT '0=禁用 1=正常',
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  deleted_at    TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ------------------------------------------------------------
-- 3. 商品分类表 categories（自连接树形结构）
--    parent_id=0 表示顶级分类；自引用外键 ON DELETE RESTRICT
-- ------------------------------------------------------------
CREATE TABLE categories (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '分类ID',
  name        VARCHAR(100) NOT NULL COMMENT '分类名称',
  parent_id   BIGINT NULL DEFAULT 0 COMMENT '0=顶级分类',
  sort_order  INT NOT NULL DEFAULT 0 COMMENT '排序值，越小越靠前',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品分类表（自连接树形）';

-- ------------------------------------------------------------
-- 4. 商品表 products
--    状态 draft/on_sale/off_sale；价格 DECIMAL(10,2) 精确存储
-- ------------------------------------------------------------
CREATE TABLE products (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '商品ID',
  name        VARCHAR(200) NOT NULL COMMENT '商品名称',
  category_id BIGINT NOT NULL COMMENT '分类ID',
  price       DECIMAL(10,2) NOT NULL COMMENT '售价',
  stock       INT NOT NULL DEFAULT 0 COMMENT '库存',
  status      ENUM('draft','on_sale','off_sale') NOT NULL DEFAULT 'draft' COMMENT '状态',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品表';

-- ------------------------------------------------------------
-- 5. 订单表 orders
--    状态 pending/paid/shipped/completed/cancelled/refunded
-- ------------------------------------------------------------
CREATE TABLE orders (
  id           BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '订单ID',
  user_id      BIGINT NOT NULL COMMENT '下单用户ID',
  total_amount DECIMAL(10,2) NOT NULL COMMENT '订单总金额',
  status       ENUM('pending','paid','shipped','completed','cancelled','refunded') NOT NULL DEFAULT 'pending' COMMENT '订单状态',
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

-- ------------------------------------------------------------
-- 6. 订单详情表 order_items
--    order_id 级联删除（删订单则明细一起删）
--    product_id RESTRICT（有订单引用时禁止删商品）
-- ------------------------------------------------------------
CREATE TABLE order_items (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
  order_id   BIGINT NOT NULL COMMENT '订单ID',
  product_id BIGINT NOT NULL COMMENT '商品ID',
  quantity   INT NOT NULL COMMENT '购买数量',
  unit_price DECIMAL(10,2) NOT NULL COMMENT '成交单价',
  FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE  ON UPDATE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单详情表';

-- ------------------------------------------------------------
-- 7. 账户表 accounts（转账场景）
--    1:1 关系（user_id UNIQUE）；version 乐观锁版本号
-- ------------------------------------------------------------
CREATE TABLE accounts (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '账户ID',
  user_id    BIGINT NOT NULL UNIQUE COMMENT '用户ID(1对1)',
  balance    DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '余额',
  version    INT NOT NULL DEFAULT 0 COMMENT '乐观锁版本号',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账户表（转账场景）';

-- ------------------------------------------------------------
-- 8. 评价表 reviews
--    rating 1-5 星；content 可空
-- ------------------------------------------------------------
CREATE TABLE reviews (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '评价ID',
  user_id    BIGINT NOT NULL COMMENT '评价用户ID',
  product_id BIGINT NOT NULL COMMENT '被评价商品ID',
  rating     TINYINT NOT NULL COMMENT '1-5星',
  content    TEXT NULL COMMENT '评价内容',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品评价表';

-- ------------------------------------------------------------
-- 9. 验证建表结果
-- ------------------------------------------------------------
SHOW TABLES;

-- 查看每张表引擎与字符集
SELECT
  table_name  AS 表名,
  engine      AS 引擎,
  table_collation AS 校对集,
  table_rows  AS 估算行数,
  table_comment AS 注释
FROM information_schema.tables
WHERE table_schema = 'ecommerce'
ORDER BY table_name;

-- ------------------------------------------------------------
-- 10. 验证外键约束
-- ------------------------------------------------------------
SELECT
  table_name       AS 子表,
  column_name      AS 子列,
  constraint_name  AS 约束名,
  referenced_table_name  AS 父表,
  referenced_column_name AS 父列,
  delete_rule      AS 删除策略,
  update_rule      AS 更新策略
FROM information_schema.key_column_usage
WHERE table_schema = 'ecommerce'
  AND referenced_table_name IS NOT NULL
ORDER BY table_name;

-- ============================================================
-- 建库完成。
-- 共 7 张表: users / categories / products / orders /
--           order_items / accounts / reviews
-- 后续 Day03 类型约束、Day04 数据增删改均基于此库。
-- ============================================================
