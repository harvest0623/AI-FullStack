-- ============================================================
-- 文件名称: 02-constraints-demo.sql
-- 文件用途: 演示 MySQL 各类约束的行为与报错
--           独立使用 constraint_demo 库，不影响 ecommerce
--           含: 主键 / 非空 / 唯一 / 默认 / CHECK / 外键级联
--           故意插入违反约束的数据，观察报错信息
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day03/Code/02-constraints-demo.sql
-- 注意:    本脚本含故意失败的 INSERT，注释掉的语句需手动
--           取消注释观察报错；默认严格模式下越界会报错
-- ============================================================

-- ------------------------------------------------------------
-- 0. 准备独立演示库
-- ------------------------------------------------------------
DROP DATABASE IF EXISTS constraint_demo;
CREATE DATABASE constraint_demo DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE constraint_demo;


-- ============================================================
-- 一、PRIMARY KEY 主键约束
-- ============================================================

DROP TABLE IF EXISTS pk_demo;
CREATE TABLE pk_demo (
  id    BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  name  VARCHAR(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='主键演示';

INSERT INTO pk_demo (name) VALUES ('张三'), ('李四'), ('王五');

-- 演示主键唯一: 重复 id 报错
-- INSERT INTO pk_demo (id, name) VALUES (1, '赵六');
-- ERROR 1062 (23000): Duplicate entry '1' for key 'PRIMARY'

-- 演示主键非空: id 为 NULL 报错
-- INSERT INTO pk_demo (id, name) VALUES (NULL, '钱七');
-- ERROR 1048 (23000): Column 'id' cannot be null

-- 自增特性: 不填 id 自动+1
INSERT INTO pk_demo (name) VALUES ('自动ID');
SELECT * FROM pk_demo;


-- ============================================================
-- 二、NOT NULL 非空约束
-- ============================================================

DROP TABLE IF EXISTS notnull_demo;
CREATE TABLE notnull_demo (
  id       BIGINT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL COMMENT '用户名必填',
  nickname VARCHAR(50) NULL     COMMENT '昵称可空'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='非空演示';

INSERT INTO notnull_demo (username, nickname) VALUES ('alice', '小A');
INSERT INTO notnull_demo (username, nickname) VALUES ('bob', NULL);
INSERT INTO notnull_demo (username) VALUES ('charlie');  -- nickname 取默认 NULL

-- 演示 NOT NULL 违反
-- INSERT INTO notnull_demo (username) VALUES (NULL);
-- ERROR 1048 (23000): Column 'username' cannot be null

-- ⚠️ 空字符串不是 NULL，能通过 NOT NULL
INSERT INTO notnull_demo (username) VALUES ('');
SELECT id, username, nickname, username = '' AS 是否空串, username IS NULL AS 是否NULL
FROM notnull_demo;


-- ============================================================
-- 三、UNIQUE 唯一约束
-- ============================================================

DROP TABLE IF EXISTS unique_demo;
CREATE TABLE unique_demo (
  id    BIGINT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱唯一',
  phone VARCHAR(20)           COMMENT '手机号可空'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='唯一约束演示';

INSERT INTO unique_demo (email, phone) VALUES
  ('a@x.com', '13800000001'),
  ('b@x.com', '13800000002');

-- 演示唯一约束违反
-- INSERT INTO unique_demo (email, phone) VALUES ('a@x.com', '13800000003');
-- ERROR 1062 (23000): Duplicate entry 'a@x.com' for key 'email'

-- ⚠️ UNIQUE 允许多个 NULL（NULL 不参与唯一性比较）
INSERT INTO unique_demo (email, phone) VALUES ('c@x.com', NULL);
INSERT INTO unique_demo (email, phone) VALUES ('d@x.com', NULL);
SELECT id, email, phone FROM unique_demo;
-- 两条 phone=NULL 都成功插入


-- ============================================================
-- 四、DEFAULT 默认值约束
-- ============================================================

DROP TABLE IF EXISTS default_demo;
CREATE TABLE default_demo (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  status     TINYINT NOT NULL DEFAULT 1 COMMENT '状态默认1',
  role       VARCHAR(20) NOT NULL DEFAULT 'customer' COMMENT '角色默认customer',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间默认当前',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间自动刷新'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='默认值演示';

-- 只插部分列，其余取默认值
INSERT INTO default_demo (status) VALUES (5);

SELECT * FROM default_demo;
-- role='customer', created_at/updated_at=当前时间

-- 8.0 支持表达式默认值
DROP TABLE IF EXISTS default_expr_demo;
CREATE TABLE default_expr_demo (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  qty         INT NOT NULL DEFAULT 1,
  price       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  -- 注意: 表达式默认值需用括号包裹
  total       DECIMAL(10,2) AS (qty * price) STORED COMMENT '计算列',
  created_date DATE NOT NULL DEFAULT (CURRENT_DATE) COMMENT '默认当前日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表达式默认值与计算列';

INSERT INTO default_expr_demo (qty, price) VALUES (3, 9.99);
SELECT * FROM default_expr_demo;
-- total 自动 = 3 * 9.99 = 29.97


-- ============================================================
-- 五、CHECK 检查约束（MySQL 8 真正支持）
-- ============================================================

DROP TABLE IF EXISTS check_demo;
CREATE TABLE check_demo (
  id      BIGINT AUTO_INCREMENT PRIMARY KEY,
  age     TINYINT NOT NULL,
  score   DECIMAL(5,2) NOT NULL,
  -- 列级 CHECK
  CONSTRAINT chk_age   CHECK (age BETWEEN 0 AND 150),
  CONSTRAINT chk_score CHECK (score >= 0 AND score <= 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CHECK约束演示';

-- 合法数据
INSERT INTO check_demo (age, score) VALUES (25, 88.5), (18, 100), (60, 0);

-- 演示 CHECK 违反: 年龄 200 超范围
-- INSERT INTO check_demo (age, score) VALUES (200, 50);
-- ERROR 3819 (HY000): Check constraint 'chk_age' is violated.

-- 演示 CHECK 违反: 分数 150 超范围
-- INSERT INTO check_demo (age, score) VALUES (30, 150);
-- ERROR 3819 (HY000): Check constraint 'chk_score' is violated.

SELECT * FROM check_demo;

-- 查看 CHECK 约束定义
SELECT
  constraint_name AS 约束名,
  check_clause    AS 检查表达式
FROM information_schema.check_constraints
WHERE constraint_schema = 'constraint_demo';


-- ============================================================
-- 六、FOREIGN KEY 外键与级联策略
-- ============================================================

-- 6.1 建父表 department
DROP TABLE IF EXISTS emp;
DROP TABLE IF EXISTS dept;

CREATE TABLE dept (
  id   BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门表(父)';

INSERT INTO dept (name) VALUES ('技术部'), ('市场部'), ('财务部');

-- 6.2 建子表 emp，演示四种级联策略
CREATE TABLE emp (
  id        BIGINT AUTO_INCREMENT PRIMARY KEY,
  name      VARCHAR(50) NOT NULL,
  dept_id   BIGINT NOT NULL,
  mentor_id BIGINT NULL,
  -- ON DELETE CASCADE: 删部门，该部门员工一起删
  FOREIGN KEY (dept_id) REFERENCES dept(id) ON DELETE CASCADE ON UPDATE CASCADE,
  -- ON DELETE SET NULL: 删导师，徒弟的 mentor_id 置 NULL
  FOREIGN KEY (mentor_id) REFERENCES emp(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工表(子)';

-- 插入员工（含师徒关系）
INSERT INTO emp (name, dept_id, mentor_id) VALUES
  ('老板', 1, NULL),       -- id=1, 技术部, 无导师
  ('张三', 1, 1),          -- id=2, 技术部, 导师=老板
  ('李四', 2, 1),          -- id=3, 市场部, 导师=老板
  ('王五', 1, 2);          -- id=4, 技术部, 导师=张三

SELECT id, name, dept_id, mentor_id FROM emp;

-- 6.3 演示外键约束: 插入不存在的 dept_id 报错
-- INSERT INTO emp (name, dept_id) VALUES ('赵六', 999);
-- ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails

-- 6.4 演示 ON DELETE CASCADE: 删技术部(id=1)，该部门员工一起删
SELECT '删除前' AS 阶段, id, name, dept_id FROM emp;
DELETE FROM dept WHERE id = 1;
SELECT '删除后' AS 阶段, id, name, dept_id FROM emp;
-- 老板、张三、王五(都在技术部)被级联删除，李四(市场部)保留

-- 6.5 演示 ON DELETE SET NULL: 删导师(id=1已删，用李四 id=3)
-- 重新插数据
INSERT INTO dept (name) VALUES ('技术部');
INSERT INTO emp (name, dept_id, mentor_id) VALUES
  ('新老板', (SELECT id FROM dept WHERE name='技术部'), NULL),
  ('新张三', (SELECT id FROM dept WHERE name='技术部'), (SELECT id FROM emp WHERE name='新老板'));

SELECT id, name, mentor_id FROM emp WHERE name LIKE '新%';

-- 删导师(新老板)，徒弟的 mentor_id 置 NULL
DELETE FROM emp WHERE name = '新老板';
SELECT id, name, mentor_id FROM emp WHERE name LIKE '新%';
-- 新张三的 mentor_id 变为 NULL

-- 6.6 演示 ON DELETE RESTRICT: 父表被引用时禁止删除
-- 重建一对关系演示 RESTRICT
DROP TABLE IF EXISTS child_restrict;
DROP TABLE IF EXISTS parent_restrict;
CREATE TABLE parent_restrict (id BIGINT PRIMARY KEY, name VARCHAR(50)) ENGINE=InnoDB;
CREATE TABLE child_restrict (
  id BIGINT PRIMARY KEY,
  pid BIGINT NOT NULL,
  FOREIGN KEY (pid) REFERENCES parent_restrict(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

INSERT INTO parent_restrict (id, name) VALUES (1, '父A');
INSERT INTO child_restrict (id, pid) VALUES (1, 1);

-- 子表有引用时，删父表报错
-- DELETE FROM parent_restrict WHERE id = 1;
-- ERROR 1451 (23000): Cannot delete or update a parent row: a foreign key constraint fails

-- 先删子表记录，再删父表才成功
DELETE FROM child_restrict WHERE pid = 1;
DELETE FROM parent_restrict WHERE id = 1;
SELECT 'RESTRICT删除成功' AS 结果;


-- ============================================================
-- 七、AUTO_INCREMENT 行为
-- ============================================================

DROP TABLE IF EXISTS auto_inc_demo;
CREATE TABLE auto_inc_demo (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50)
) ENGINE=InnoDB AUTO_INCREMENT=1000 COMMENT='自增起始值演示';
-- AUTO_INCREMENT=1000 让自增从 1000 开始

INSERT INTO auto_inc_demo (name) VALUES ('第一条'), ('第二条');
SELECT * FROM auto_inc_demo;
-- id 从 1000, 1001 开始

-- LAST_INSERT_ID() 返回本次连接最后插入的自增ID
SELECT LAST_INSERT_ID() AS 最近自增ID;
-- 注意: 多行插入时返回第一条的 ID

-- 查看自增变量
SHOW TABLE STATUS LIKE 'auto_inc_demo'\G
-- Auto_increment 字段显示下一个自增值

-- 演示自增间隙: 删除后再插，ID 不连续
DELETE FROM auto_inc_demo WHERE id = 1001;
INSERT INTO auto_inc_demo (name) VALUES ('第三条');
SELECT * FROM auto_inc_demo;
-- 新记录 id=1002（不会复用 1001）


-- ============================================================
-- 八、约束命名规范演示
-- ============================================================

DROP TABLE IF EXISTS naming_demo;
CREATE TABLE naming_demo (
  id       BIGINT AUTO_INCREMENT PRIMARY KEY,                    -- pk_naming_demo (自动)
  email    VARCHAR(100) NOT NULL,
  username VARCHAR(50)  NOT NULL,
  age      TINYINT      NOT NULL,
  dept_id  BIGINT       NOT NULL,
  -- 显式命名约束，便于后续管理
  CONSTRAINT uk_naming_email    UNIQUE (email),
  CONSTRAINT uk_naming_username UNIQUE (username),
  CONSTRAINT chk_naming_age     CHECK (age >= 18),
  CONSTRAINT fk_naming_dept     FOREIGN KEY (dept_id) REFERENCES dept(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='约束命名规范演示';

-- 约束命名约定:
--   主键:    pk_表名
--   唯一键:  uk_表名_列名
--   外键:    fk_表名_父表名
--   检查:    chk_表名_列名
--   默认:    无需命名

SELECT
  constraint_name AS 约束名,
  constraint_type AS 约束类型,
  table_name      AS 表名
FROM information_schema.table_constraints
WHERE table_schema = 'constraint_demo' AND table_name = 'naming_demo'
ORDER BY constraint_type;


-- ============================================================
-- 九、综合: 约束违规错误码速查
-- ============================================================
-- 通过注释列出常见约束违规错误，供查阅
--
-- 1062 (23000): Duplicate entry '...' for key 'PRIMARY'/'uk_...'   主键/唯一键重复
-- 1048 (23000): Column '...' cannot be null                         NOT NULL 违反
-- 1452 (23000): Cannot add or update a child row (外键插入)         外键父行不存在
-- 1451 (23000): Cannot delete or update a parent row (外键删除)     外键子行引用中
-- 3819 (HY000): Check constraint '...' is violated.                 CHECK 违反
-- 1264 (22003): Out of range value for column '...'                 数值越界
-- 1265 (01000): Data truncated for column '...'                     ENUM非法值


-- ============================================================
-- 清理（可选）
-- ============================================================
-- DROP DATABASE IF EXISTS constraint_demo;

-- ============================================================
-- 约束演示完毕。
-- 核心结论:
--   1. 主键 = 唯一 + 非空，每表一个
--   2. NOT NULL: 空字符串不等于 NULL，能通过 NOT NULL
--   3. UNIQUE: 允许多个 NULL
--   4. CHECK: 8.0 真正校验，5.7 仅解析不校验
--   5. 外键级联: CASCADE(级联) / RESTRICT(禁止) / SET NULL(置空) / NO ACTION
--   6. AUTO_INCREMENT: 有间隙，不回填，LAST_INSERT_ID() 取最近ID
--   7. 约束命名: pk_/uk_/fk_/chk_ 前缀便于管理
-- ============================================================
