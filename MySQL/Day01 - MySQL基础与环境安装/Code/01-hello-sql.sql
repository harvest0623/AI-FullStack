-- ============================================================
-- 文件名称: 01-hello-sql.sql
-- 文件用途: 第一个 SQL 示例脚本
--           用临时库 hello_demo 演示完整的"建库→建表→插入→
--           查询→更新→删除→删表→删库"流程，不影响 ecommerce 库
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day01/Code/01-hello-sql.sql
-- ============================================================

-- ------------------------------------------------------------
-- 1. 创建并使用临时演示库（带 IF NOT EXISTS 防止报错）
-- ------------------------------------------------------------
DROP DATABASE IF EXISTS hello_demo;
CREATE DATABASE hello_demo DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hello_demo;

-- ------------------------------------------------------------
-- 2. 创建第一张表 greeting（问候语表）
--    演示: 主键 + 自增 + NOT NULL + DEFAULT + 注释
-- ------------------------------------------------------------
DROP TABLE IF EXISTS greeting;
CREATE TABLE greeting (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  name        VARCHAR(50) NOT NULL COMMENT '称呼',
  message     VARCHAR(200) NOT NULL DEFAULT 'Hello, MySQL!' COMMENT '问候内容',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='第一个示例表';

-- ------------------------------------------------------------
-- 3. 插入数据（单行 + 多行批量插入）
-- ------------------------------------------------------------
INSERT INTO greeting (name, message) VALUES ('World', 'Hello, World!');

INSERT INTO greeting (name, message) VALUES
  ('MySQL',   'Hello, MySQL!'),
  ('Day01',   '今天开始学 MySQL 基础'),
  ('Docker',  '环境已用 Docker 部署完成'),
  ('Trae',    '用 Trae IDE 编写 SQL 真高效');

-- ------------------------------------------------------------
-- 4. 查询全部数据（\G 纵向显示在命令行查看更清晰）
-- ------------------------------------------------------------
SELECT * FROM greeting;

-- ------------------------------------------------------------
-- 5. 条件查询 + 排序
-- ------------------------------------------------------------
SELECT id, name, message
FROM greeting
WHERE id > 1
ORDER BY id DESC;

-- ------------------------------------------------------------
-- 6. 更新数据（带 WHERE，避免全表更新）
-- ------------------------------------------------------------
UPDATE greeting SET message = '已更新: 你好，MySQL 8.0!' WHERE name = 'MySQL';

SELECT name, message FROM greeting WHERE name = 'MySQL';

-- ------------------------------------------------------------
-- 7. 删除数据（带 WHERE，避免全表删除）
-- ------------------------------------------------------------
DELETE FROM greeting WHERE name = 'Day01';

SELECT COUNT(*) AS remaining_rows FROM greeting;

-- ------------------------------------------------------------
-- 8. 查看表结构
-- ------------------------------------------------------------
DESC greeting;
SHOW CREATE TABLE greeting\G

-- ------------------------------------------------------------
-- 9. 修改表结构（加列、删列演示，DDL 在 Day02 详讲）
-- ------------------------------------------------------------
ALTER TABLE greeting ADD COLUMN lang VARCHAR(10) NOT NULL DEFAULT 'zh' COMMENT '语言';

DESC greeting;

ALTER TABLE greeting DROP COLUMN lang;

DESC greeting;

-- ------------------------------------------------------------
-- 10. 清空表数据（TRUNCATE 重置自增，DELETE 不重置）
-- ------------------------------------------------------------
TRUNCATE TABLE greeting;

SELECT * FROM greeting;

-- ------------------------------------------------------------
-- 11. 删表、删库，清理演示环境
-- ------------------------------------------------------------
DROP TABLE IF EXISTS greeting;
DROP DATABASE IF EXISTS hello_demo;

SHOW DATABASES LIKE 'hello_demo';

-- ============================================================
-- 第一个 SQL 流程跑通: 库→表→增→查→改→删→清→删
-- 至此 MySQL 环境已可用，可进入 Day02 的 DDL 学习。
-- ============================================================
