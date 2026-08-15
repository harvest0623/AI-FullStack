-- ============================================================
-- 文件名称: 02-date-functions.sql
-- 文件用途: 日期时间函数演示：格式化、加减、差值
-- 执行方式: mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day09 - 常用函数与窗口函数/Code/02-date-functions.sql
-- ============================================================

USE ecommerce;

-- ============================================================
-- 一、获取当前日期时间
-- ============================================================

-- ------------------------------------------------------------
-- 1.1 NOW / CURRENT_TIMESTAMP：当前日期时间
--     CURDATE / CURRENT_DATE：当前日期
--     CURTIME：当前时间
-- ------------------------------------------------------------
SELECT NOW()              AS now_dt,
       CURRENT_TIMESTAMP  AS now_ts,
       CURDATE()          AS today,
       CURRENT_DATE       AS today2,
       CURTIME()          AS now_time;

-- ------------------------------------------------------------
-- 1.2 UTC 时间
-- ------------------------------------------------------------
SELECT UTC_TIMESTAMP() AS utc_now,
       NOW() AS local_now;

-- ============================================================
-- 二、提取日期各部分
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 YEAR / MONTH / DAY / HOUR / MINUTE / SECOND
-- ------------------------------------------------------------
SELECT NOW() AS now_dt,
       YEAR(NOW())   AS y,
       MONTH(NOW())  AS m,
       DAY(NOW())    AS d,
       HOUR(NOW())   AS h,
       MINUTE(NOW()) AS mi,
       SECOND(NOW()) AS s;

-- ------------------------------------------------------------
-- 2.2 DAYNAME / MONTHNAME / DAYOFWEEK / DAYOFYEAR
-- ------------------------------------------------------------
SELECT NOW() AS now_dt,
       DAYNAME(NOW())     AS day_name,    -- Monday
       MONTHNAME(NOW())   AS month_name,  -- July
       DAYOFWEEK(NOW())   AS dow,         -- 2（周日=1）
       DAYOFYEAR(NOW())   AS doy;         -- 年内第几天

-- 应用于订单表
SELECT id,
       created_at,
       YEAR(created_at)   AS order_year,
       MONTH(created_at)  AS order_month,
       DAYNAME(created_at) AS order_weekday
FROM orders
LIMIT 5;

-- ============================================================
-- 三、日期格式化 DATE_FORMAT
-- ============================================================

-- ------------------------------------------------------------
-- 3.1 常用格式符
--     %Y 四位年、%y 两位年、%m 月(01-12)、%c 月(1-12)
--     %d 日、%H 时(24h)、%h 时(12h)、%i 分、%s 秒
--     %W 星期名、%M 月份名、%j 年内第几天
-- ------------------------------------------------------------
SELECT DATE_FORMAT(NOW(), '%Y-%m-%d')              AS date_std,
       DATE_FORMAT(NOW(), '%Y年%m月%d日')           AS date_cn,
       DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')     AS datetime_std,
       DATE_FORMAT(NOW(), '%W, %M %d %Y')          AS date_en,
       DATE_FORMAT(NOW(), '%H:%i:%s')              AS time_only;

-- 订单创建时间格式化为中文样式
SELECT id,
       DATE_FORMAT(created_at, '%Y年%m月%d日 %H:%i') AS 创建时间,
       total_amount
FROM orders
LIMIT 5;

-- ------------------------------------------------------------
-- 3.2 按月份统计订单数（用 DATE_FORMAT 分组）
-- ------------------------------------------------------------
SELECT DATE_FORMAT(created_at, '%Y-%m') AS order_month,
       COUNT(*) AS order_cnt,
       SUM(total_amount) AS total_amount
FROM orders
GROUP BY DATE_FORMAT(created_at, '%Y-%m')
ORDER BY order_month;

-- ============================================================
-- 四、字符串转日期 STR_TO_DATE
-- ============================================================

-- ------------------------------------------------------------
-- 4.1 STR_TO_DATE：按格式把字符串解析为日期
-- ------------------------------------------------------------
SELECT STR_TO_DATE('2026-07-27', '%Y-%m-%d')            AS d1,
       STR_TO_DATE('27/07/2026', '%d/%m/%Y')            AS d2,
       STR_TO_DATE('2026年07月27日 14时30分', '%Y年%m月%d日 %H时%i分') AS d3;

-- 解析失败返回 NULL（格式不匹配）
SELECT STR_TO_DATE('2026-07-27', '%d/%m/%Y') AS parse_fail;

-- ============================================================
-- 五、日期加减 DATE_ADD / DATE_SUB
-- ============================================================

-- ------------------------------------------------------------
-- 5.1 DATE_ADD：日期加（INTERVAL n 单位）
--     单位：SECOND/MINUTE/HOUR/DAY/WEEK/MONTH/QUARTER/YEAR
-- ------------------------------------------------------------
SELECT NOW() AS now_dt,
       DATE_ADD(NOW(), INTERVAL 1 DAY)    AS tomorrow,
       DATE_ADD(NOW(), INTERVAL 7 DAY)    AS week_later,
       DATE_ADD(NOW(), INTERVAL 1 MONTH)  AS month_later,
       DATE_ADD(NOW(), INTERVAL 1 YEAR)   AS year_later;

-- ------------------------------------------------------------
-- 5.2 DATE_SUB：日期减
-- ------------------------------------------------------------
SELECT NOW() AS now_dt,
       DATE_SUB(NOW(), INTERVAL 1 DAY)   AS yesterday,
       DATE_SUB(NOW(), INTERVAL 1 MONTH) AS month_ago,
       DATE_SUB(NOW(), INTERVAL 1 YEAR)  AS year_ago;

-- ------------------------------------------------------------
-- 5.3 也可用 + INTERVAL 写法（等价）
-- ------------------------------------------------------------
SELECT NOW() + INTERVAL 1 DAY AS plus_one_day,
       NOW() - INTERVAL 1 DAY AS minus_one_day;

-- ------------------------------------------------------------
-- 5.4 实战：查询最近 7 天的订单
-- ------------------------------------------------------------
SELECT id, user_id, total_amount, created_at
FROM orders
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY created_at DESC;

-- 查询最近 30 天的订单数
SELECT COUNT(*) AS orders_30d
FROM orders
WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

-- ============================================================
-- 六、日期差值
-- ============================================================

-- ------------------------------------------------------------
-- 6.1 DATEDIFF：两个日期相差天数（d1 - d2）
-- ------------------------------------------------------------
SELECT DATEDIFF('2026-07-27', '2026-01-01') AS days_diff,   -- 207
       DATEDIFF('2026-01-01', '2026-07-27') AS days_neg;    -- -207

-- 订单距今多少天
SELECT id, created_at, DATEDIFF(NOW(), created_at) AS days_ago
FROM orders
ORDER BY created_at
LIMIT 5;

-- ------------------------------------------------------------
-- 6.2 TIMESTAMPDIFF：按指定单位计算差值
--     单位：MICROSECOND/SECOND/MINUTE/HOUR/DAY/WEEK/MONTH/QUARTER/YEAR
--     注意参数顺序：TIMESTAMPDIFF(unit, d1, d2) = d2 - d1
-- ------------------------------------------------------------
SELECT TIMESTAMPDIFF(DAY,   '2026-01-01', '2026-07-27') AS diff_days,
       TIMESTAMPDIFF(MONTH, '2026-01-01', '2026-07-27') AS diff_months,
       TIMESTAMPDIFF(YEAR,  '2026-01-01', '2026-07-27') AS diff_years,
       TIMESTAMPDIFF(HOUR,  '2026-07-27 08:00:00', '2026-07-27 14:30:00') AS diff_hours;

-- 用户注册距今多少个月
SELECT id, username, created_at,
       TIMESTAMPDIFF(MONTH, created_at, NOW()) AS months_since_register
FROM users
ORDER BY created_at
LIMIT 5;

-- ============================================================
-- 七、LAST_DAY 与当月信息
-- ============================================================

-- ------------------------------------------------------------
-- 7.1 LAST_DAY：返回当月最后一天
-- ------------------------------------------------------------
SELECT LAST_DAY('2026-02-10') AS feb_last,   -- 2026-02-28（2026 非闰年）
       LAST_DAY('2026-07-15') AS jul_last,   -- 2026-07-31
       LAST_DAY(NOW())        AS this_month_last;

-- ------------------------------------------------------------
-- 7.2 计算当月剩余天数
-- ------------------------------------------------------------
SELECT DATEDIFF(LAST_DAY(NOW()), NOW()) AS days_left_this_month;

-- ============================================================
-- 八、UNIX 时间戳
-- ============================================================

-- ------------------------------------------------------------
-- 8.1 UNIX_TIMESTAMP：日期转时间戳（秒）
--     FROM_UNIXTIME：时间戳转日期
-- ------------------------------------------------------------
SELECT UNIX_TIMESTAMP() AS current_ts,
       UNIX_TIMESTAMP(NOW()) AS now_ts,
       FROM_UNIXTIME(1690000000) AS ts_to_date,
       FROM_UNIXTIME(1690000000, '%Y-%m-%d %H:%i:%s') AS ts_formatted;

-- ============================================================
-- 九、综合应用
-- ============================================================

-- ------------------------------------------------------------
-- 9.1 订单时效分析：下单至今的天数与状态
-- ------------------------------------------------------------
SELECT id,
       user_id,
       status,
       created_at,
       DATEDIFF(NOW(), created_at) AS days_since_order,
       CASE
           WHEN DATEDIFF(NOW(), created_at) > 30 THEN '超期'
           WHEN DATEDIFF(NOW(), created_at) > 7  THEN '近期'
           ELSE '新鲜'
       END AS freshness
FROM orders
ORDER BY created_at
LIMIT 10;

-- ------------------------------------------------------------
-- 9.2 按星期几统计订单量（看哪天订单最多）
-- ------------------------------------------------------------
SELECT DAYNAME(created_at) AS weekday,
       DAYOFWEEK(created_at) AS dow,
       COUNT(*) AS order_cnt
FROM orders
GROUP BY DAYNAME(created_at), DAYOFWEEK(created_at)
ORDER BY dow;

-- ------------------------------------------------------------
-- 9.3 商品上架天数与"上架满月"标记
-- ------------------------------------------------------------
SELECT id, name, created_at,
       DATEDIFF(NOW(), created_at) AS days_on_shelf,
       IF(DATEDIFF(NOW(), created_at) >= 30, '满月', '未满月') AS milestone
FROM products
ORDER BY created_at
LIMIT 10;

-- ============================================================
-- 日期时间函数演示完毕。
-- 要点：DATE_FORMAT 格式化、STR_TO_DATE 解析；
--       DATE_ADD/DATE_SUB 加减、INTERVAL 指定单位；
--       DATEDIFF 算天数、TIMESTAMPDIFF 算任意单位；
--       LAST_DAY 取月末、UNIX_TIMESTAMP 与时间戳互转。
-- ============================================================
