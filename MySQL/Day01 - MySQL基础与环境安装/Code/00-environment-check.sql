-- ============================================================
-- 文件名称: 00-environment-check.sql
-- 文件用途: MySQL 环境检查脚本
--           查看版本、字符集、存储引擎、关键系统变量
--           用于确认 MySQL 8.0+ 环境是否就绪
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day01/Code/00-environment-check.sql
--           或在命令行: mysql -u root -p < 00-environment-check.sql
-- ============================================================

-- ------------------------------------------------------------
-- 1. 查看 MySQL 服务器版本（确认 8.0+）
-- ------------------------------------------------------------
SELECT VERSION() AS mysql_version,
       @@version_comment AS version_comment,
       @@version_compile_os AS compile_os,
       @@version_compile_machine AS machine;

-- ------------------------------------------------------------
-- 2. 查看当前登录用户与数据库
-- ------------------------------------------------------------
SELECT CURRENT_USER() AS current_user,
       USER() AS connect_user,
       DATABASE() AS current_database;

-- ------------------------------------------------------------
-- 3. 查看所有数据库（系统库 + 用户库）
--    information_schema / mysql / performance_schema / sys 为系统库
-- ------------------------------------------------------------
SHOW DATABASES;

-- ------------------------------------------------------------
-- 4. 查看支持的存储引擎
--    InnoDB 应为 DEFAULT（8.0 默认）
--    Support 取值: DEFAULT / YES / NO / DISABLED
-- ------------------------------------------------------------
SHOW ENGINES;

-- ------------------------------------------------------------
-- 5. 查看字符集相关变量（关键: character_set_server / character_set_database）
--    8.0 默认 utf8mb4，5.7 默认 latin1
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'character%';

-- ------------------------------------------------------------
-- 6. 查看校对集相关变量
--    utf8mb4_0900_ai_ci 为 8.0 默认（ai=口音不敏感, ci=大小写不敏感）
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'collation%';

-- ------------------------------------------------------------
-- 7. 查看时区与时间（TIMESTAMP 受时区影响）
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'time_zone';
SELECT NOW() AS server_now,
       UTC_TIMESTAMP() AS utc_now,
       @@system_time_zone AS system_tz;

-- ------------------------------------------------------------
-- 8. 查看 SQL 模式（影响数据校验严格度）
--    8.0 默认: STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,
--             ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION
-- ------------------------------------------------------------
SELECT @@sql_mode AS sql_mode;

-- ------------------------------------------------------------
-- 9. 查看默认存储引擎与数据目录
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'default_storage_engine';
SHOW VARIABLES LIKE 'datadir';

-- ------------------------------------------------------------
-- 10. 查看最大连接数与当前连接数
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'max_connections';
SHOW STATUS LIKE 'Threads_connected';

-- ------------------------------------------------------------
-- 11. 查看 MySQL 支持的所有字符集（截取前 10 个观察）
--     utf8mb4 最大字符长度=4，而 utf8（实为 utf8mb3）=3
-- ------------------------------------------------------------
SELECT charset AS 字符集,
       description AS 描述,
       maxlen AS 最大字节长度
FROM information_schema.CHARACTER_SETS
ORDER BY charset
LIMIT 10;

-- ------------------------------------------------------------
-- 12. 查看 utf8mb4 对应的校对集
-- ------------------------------------------------------------
SELECT collation_name AS 校对集,
       charset_name AS 字符集,
       is_default AS 是否默认
FROM information_schema.COLLATIONS
WHERE charset_name = 'utf8mb4';

-- ------------------------------------------------------------
-- 13. 查看自动提交设置（事务相关，Day 后续详讲）
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'autocommit';

-- ------------------------------------------------------------
-- 14. 查看 sql_safe_updates（安全更新模式）
--     为 ON 时，禁止无 WHERE/无键的 UPDATE/DELETE，避免误删全表
-- ------------------------------------------------------------
SHOW VARIABLES LIKE 'sql_safe_updates';

-- ------------------------------------------------------------
-- 15. 客户端连接信息摘要（\s 等价命令的 SQL 版）
-- ------------------------------------------------------------
SELECT
  @@hostname AS 主机名,
  @@port AS 端口,
  @@version AS 版本,
  @@default_storage_engine AS 默认引擎,
  @@character_set_server AS 服务器字符集,
  @@character_set_database AS 数据库字符集,
  @@collation_server AS 服务器校对集;

-- ============================================================
-- 环境检查完毕。
-- 若版本 >= 8.0、默认引擎 = InnoDB、字符集 = utf8mb4，则环境合格。
-- ============================================================
