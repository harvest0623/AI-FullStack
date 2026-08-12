-- ============================================================
-- 文件名称: 01-data-types-demo.sql
-- 文件用途: 演示 MySQL 各类数据类型的存储与查询特性
--           独立使用 type_demo 库，不影响 ecommerce
--           含: 整数/浮点定点/字符串/日期时间/JSON/ENUM/SET
--           重点展示: FLOAT 精度问题、VARCHAR vs CHAR、
--                     TIMESTAMP 自动更新、JSON 操作
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day03/Code/01-data-types-demo.sql
-- ============================================================

-- ------------------------------------------------------------
-- 0. 准备独立演示库
-- ------------------------------------------------------------
DROP DATABASE IF EXISTS type_demo;
CREATE DATABASE type_demo DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE type_demo;


-- ============================================================
-- 一、整数类型
-- ============================================================

DROP TABLE IF EXISTS int_demo;
CREATE TABLE int_demo (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  c_tinyint   TINYINT  COMMENT '1字节 -128~127',
  c_smallint  SMALLINT COMMENT '2字节',
  c_mediumint MEDIUMINT COMMENT '3字节',
  c_int       INT       COMMENT '4字节',
  c_bigint    BIGINT    COMMENT '8字节',
  c_uint      TINYINT UNSIGNED COMMENT '无符号 0~255',
  c_zerofill  INT(8) ZEROFILL COMMENT '8.0 ZEROFILL 已弃用，仅兼容'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='整数类型演示';

INSERT INTO int_demo (c_tinyint, c_smallint, c_mediumint, c_int, c_bigint, c_uint)
VALUES (127, 32767, 8388607, 2147483647, 9223372036854775807, 255);

-- 演示无符号范围：插入 200 成功（UNSIGNED 范围 0-255）
INSERT INTO int_demo (c_tinyint, c_uint) VALUES (0, 200);

-- 演示越界：TINYINT 最大 127，插入 128 报错（严格模式）
-- INSERT INTO int_demo (c_tinyint) VALUES (128);  -- ERROR 1264

SELECT * FROM int_demo;

-- 查看各类型字节占用
SELECT
  c_tinyint   AS tinyint值,
  c_uint      AS uint值,
  c_zerofill  AS zerofill值
FROM int_demo
WHERE id = 1;


-- ============================================================
-- 二、浮点 vs 定点（金额存储的核心问题）
-- ============================================================

DROP TABLE IF EXISTS decimal_demo;
CREATE TABLE decimal_demo (
  id      BIGINT AUTO_INCREMENT PRIMARY KEY,
  c_float   FLOAT         COMMENT '4字节近似值',
  c_double  DOUBLE        COMMENT '8字节近似值',
  c_decimal DECIMAL(10,2) COMMENT '精确值，存金额必选'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='浮点定点对比';

INSERT INTO decimal_demo (c_float, c_double, c_decimal)
VALUES (0.1, 0.1, 0.1),
       (0.2, 0.2, 0.2),
       (1234567.89, 1234567.89, 1234567.89);

-- ⚠️ FLOAT/DOUBLE 是近似值，累加会有精度误差
SELECT
  c_float,
  c_double,
  c_decimal,
  c_float + 0.1 + 0.1 AS float_累加,    -- 可能不等于 0.3
  c_decimal + 0.1 + 0.1 AS decimal_累加  -- 精确等于 0.3
FROM decimal_demo
WHERE id = 1;

-- 演示金额计算：FLOAT 存大额金额会丢失精度
SELECT
  c_float   AS float金额,
  c_double  AS double金额,
  c_decimal AS decimal金额
FROM decimal_demo WHERE id = 3;
-- 观察 c_float 与 c_decimal 是否完全一致


-- ============================================================
-- 三、字符串类型: CHAR vs VARCHAR
-- ============================================================

DROP TABLE IF EXISTS str_demo;
CREATE TABLE str_demo (
  id       BIGINT AUTO_INCREMENT PRIMARY KEY,
  c_char   CHAR(10)    COMMENT '定长10字符，不足补空格',
  c_varchar VARCHAR(10) COMMENT '变长，最多10字符',
  c_text   TEXT        COMMENT '大文本，最多约64KB',
  c_blob   BLOB        COMMENT '二进制大对象'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='字符串类型演示';

INSERT INTO str_demo (c_char, c_varchar, c_text) VALUES
  ('abc', 'abc', '这是一段文本'),
  ('1234567890', '1234567890', '正好10个字符');

-- CHAR(10) 存储 'abc' 实际占 10 字符位（尾部补空格），VARCHAR(10) 占 3 字符位
SELECT
  id,
  c_char          AS char值,
  c_varchar       AS varchar值,
  CHAR_LENGTH(c_char)   AS char字符数,
  CHAR_LENGTH(c_varchar) AS varchar字符数,
  LENGTH(c_char)        AS char字节数,
  LENGTH(c_varchar)     AS varchar字节数
FROM str_demo;

-- 演示 CHAR 尾部空格被自动去除（检索时），VARCHAR 保留
INSERT INTO str_demo (c_char, c_varchar) VALUES ('hello   ', 'hello   ');
SELECT
  CONCAT('[', c_char, ']')    AS char_带括号,
  CONCAT('[', c_varchar, ']') AS varchar_带括号
FROM str_demo WHERE id = 3;
-- CHAR 检索时尾部空格被删除，VARCHAR 保留


-- ============================================================
-- 四、ENUM 与 SET
-- ============================================================

DROP TABLE IF EXISTS enum_set_demo;
CREATE TABLE enum_set_demo (
  id     BIGINT AUTO_INCREMENT PRIMARY KEY,
  c_enum ENUM('draft','on_sale','off_sale') COMMENT '枚举单选',
  c_set  SET('read','write','delete') COMMENT '集合多选'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ENUM/SET演示';

INSERT INTO enum_set_demo (c_enum, c_set) VALUES
  ('draft', 'read'),
  ('on_sale', 'read,write'),
  ('off_sale', 'read,write,delete');

-- ENUM 内部用整数存储: draft=1, on_sale=2, off_sale=3
-- SET 内部用位图: read=1, write=2, delete=4
SELECT
  id,
  c_enum            AS enum值,
  c_set             AS set值,
  c_enum + 0        AS enum内部整数,
  c_set + 0         AS set内部位图
FROM enum_set_demo;

-- 演示非法枚举值（严格模式报错）
-- INSERT INTO enum_set_demo (c_enum) VALUES ('unknown'); -- ERROR 1265


-- ============================================================
-- 五、日期时间类型
-- ============================================================

DROP TABLE IF EXISTS date_demo;
CREATE TABLE date_demo (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  c_date        DATE        COMMENT '日期 YYYY-MM-DD',
  c_time        TIME        COMMENT '时间 HH:MM:SS',
  c_year        YEAR        COMMENT '年份 YYYY',
  c_datetime    DATETIME    COMMENT '日期时间，8字节，与时区无关',
  c_timestamp   TIMESTAMP   COMMENT '时间戳，4字节，受时区影响',
  c_ts_auto     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '自动更新时间戳'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日期时间演示';

INSERT INTO date_demo (c_date, c_time, c_year, c_datetime, c_timestamp, c_ts_auto)
VALUES ('2026-07-27', '14:30:00', 2026, '2026-07-27 14:30:00', '2026-07-27 14:30:00', '2026-07-27 14:30:00');

SELECT * FROM date_demo;

-- 演示 TIMESTAMP 自动更新（UPDATE 时 c_ts_auto 自动刷新）
SELECT NOW() AS 更新前时间;
SELECT c_ts_auto AS 更新前 FROM date_demo WHERE id = 1;

-- 间隔几秒后执行更新
UPDATE date_demo SET c_time = '15:00:00' WHERE id = 1;

SELECT c_time, c_ts_auto FROM date_demo WHERE id = 1;
-- c_ts_auto 自动变为当前时间，无需手动设置

-- DATETIME vs TIMESTAMP 范围对比
-- DATETIME: 1000-01-01 ~ 9999-12-31
-- TIMESTAMP: 1970-01-01 ~ 2038-01-19（2038 问题）
SELECT
  c_datetime  AS datetime值,
  c_timestamp AS timestamp值,
  UNIX_TIMESTAMP(c_timestamp) AS timestamp_秒数
FROM date_demo WHERE id = 1;


-- ============================================================
-- 六、JSON 类型（MySQL 8 增强）
-- ============================================================

DROP TABLE IF EXISTS json_demo;
CREATE TABLE json_demo (
  id   BIGINT AUTO_INCREMENT PRIMARY KEY,
  c_json JSON COMMENT 'JSON 文档'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='JSON 演示';

-- 插入 JSON
INSERT INTO json_demo (c_json) VALUES
  ('{"name":"张三","age":28,"tags":["vip","active"],"addr":{"city":"北京"}}'),
  ('{"name":"李四","age":35,"tags":["normal"],"addr":{"city":"上海"}}');

-- 查询整个 JSON
SELECT id, c_json FROM json_demo;

-- JSON_EXTRACT 或 -> 提取字段
SELECT
  id,
  JSON_EXTRACT(c_json, '$.name')   AS 姓名_extract,
  c_json->'$.name'                 AS 姓名_箭头,
  c_json->'$.age'                  AS 年龄,
  c_json->'$.addr.city'            AS 城市,
  c_json->'$.tags[0]'              AS 首个标签
FROM json_demo;

-- ->> 去掉引号（返回纯字符串）
SELECT
  c_json->>'$.name'  AS 姓名_去引号,
  c_json->>'$.addr.city' AS 城市_去引号
FROM json_demo;

-- JSON_ARRAY / JSON_OBJECT 构造
SELECT
  JSON_ARRAY(1, 'a', TRUE, NULL)         AS 数组,
  JSON_OBJECT('name','王五','age',40)     AS 对象;

-- JSON_CONTAINS 检查包含
SELECT c_json->>'$.name' AS 姓名
FROM json_demo
WHERE JSON_CONTAINS(c_json->'$.tags', '"vip"');

-- 修改 JSON: JSON_SET
UPDATE json_demo
SET c_json = JSON_SET(c_json, '$.age', 29, '$.email', 'zs@example.com')
WHERE c_json->>'$.name' = '张三';

SELECT c_json FROM json_demo WHERE c_json->>'$.name' = '张三';

-- JSON_TABLE 把 JSON 转表（8.0 新增）
SELECT jt.name, jt.age, jt.city
FROM json_demo,
JSON_TABLE(c_json, '$'
  COLUMNS (
    name VARCHAR(50) PATH '$.name',
    age  INT         PATH '$.age',
    city VARCHAR(50) PATH '$.addr.city'
  )
) AS jt;


-- ============================================================
-- 七、类型选择原则速查（通过查询展示当前库各列类型）
-- ============================================================
SELECT
  table_name  AS 表,
  column_name AS 列,
  data_type   AS 类型,
  column_type AS 完整类型,
  is_nullable AS 允许空,
  column_default AS 默认值,
  column_comment AS 注释
FROM information_schema.columns
WHERE table_schema = 'type_demo'
ORDER BY table_name, ordinal_position;

-- ============================================================
-- 清理（可选）：注释下面两行可保留演示数据
-- ============================================================
-- DROP DATABASE IF EXISTS type_demo;

-- ============================================================
-- 数据类型演示完毕。
-- 核心结论:
--   1. 金额用 DECIMAL，不用 FLOAT/DOUBLE
--   2. 字符串默认 VARCHAR，定长用 CHAR
--   3. 时间用 TIMESTAMP(自动更新) 或 DATETIME(范围大)
--   4. ENUM 单选、SET 多选，内部都是整数
--   5. JSON 适合存半结构化数据，8.0 支持 ->> 与 JSON_TABLE
-- ============================================================
