# Day03 - 数据类型与约束

## 本章简介

如果说 DDL 定义了数据库的“骨架”，那么数据类型与约束就是骨架上的“血肉”与“规则”。数据类型决定了每一列能存什么、占多少空间、精度如何；约束则规定了数据必须满足的规则，是数据库层面保证数据完整性的最后一道防线。

类型选错（如用 FLOAT 存金额导致精度丢失），约束缺失（如缺 NOT NULL 导致脏数据），都会在业务运行后暴露出难以修复的问题。本章系统讲解 MySQL 的全部数据类型与七大约束，并通过实验脚本让你直观看到类型差异与约束违规的报错行为。

## 学习目标

- 掌握整数、浮点、定点、字符串、日期时间、JSON、ENUM/SET 各类数据类型
- 理解 FLOAT 精度问题，掌握 DECIMAL 在金额场景的必要性
- 区分 CHAR 与 VARCHAR、DATETIME 与 TIMESTAMP 的存储差异
- 掌握 PRIMARY KEY / NOT NULL / UNIQUE / DEFAULT / CHECK / FOREIGN KEY / AUTO_INCREMENT 七大约束
- 理解外键级联策略 CASCADE / RESTRICT / SET NULL / NO ACTION 的区别
- 能根据业务场景选择合适的数据类型与约束

## 理论知识讲解

### 一、数据类型

#### 1. 整数类型

| 类型 | 字节 | 有符号范围 | 无符号范围（UNSIGNED） |
| --- | --- | --- | --- |
| TINYINT | 1 | -128 ~ 127 | 0 ~ 255 |
| SMALLINT | 2 | -32768 ~ 32767 | 0 ~ 65535 |
| MEDIUMINT | 3 | -8388608 ~ 8388607 | 0 ~ 16777215 |
| INT | 4 | -2^31 ~ 2^31-1 | 0 ~ 2^32-1 |
| BIGINT | 8 | -2^63 ~ 2^63-1 | 0 ~ 2^64-1 |

- **UNSIGNED**：无符号，让正数范围翻倍。状态、库存等非负字段可用。
- **显示宽度**：如 `INT(11)`，8.0 已弱化，仅 `ZEROFILL` 时有意义；**8.0 ZEROFILL 已弃用**。
- **选择原则**：主键用 `BIGINT`；状态枚举用 `TINYINT`；不确定就用 `INT`。

```sql
CREATE TABLE t (
  status TINYINT UNSIGNED COMMENT '0-255足够',
  id     BIGINT AUTO_INCREMENT PRIMARY KEY
);
```

#### 2. 浮点与定点

| 类型 | 字节 | 说明 |
| --- | --- | --- |
| FLOAT | 4 | 单精度近似值，约 7 位有效数字 |
| DOUBLE | 8 | 双精度近似值，约 15 位有效数字 |
| DECIMAL(M,D) | M+2 | 定点精确值，M 总位数(≤65)，D 小数位 |

**核心要点**：`FLOAT` / `DOUBLE` 是**近似值**（IEEE 754），累加会产生误差，**绝对不能用来存金额**。

```sql
-- 演示精度问题
SELECT 0.1 + 0.2 = 0.3 AS float比较;           -- 0（不相等）
SELECT CAST(0.1 AS DECIMAL(10,2)) + CAST(0.2 AS DECIMAL(10,2)) = 0.3 AS decimal比较;  -- 1
```

| 场景 | 推荐类型 | 理由 |
| --- | --- | --- |
| 货币金额 | `DECIMAL(10,2)` | 精确，无误差 |
| 科学计算 | `DOUBLE` | 范围大，可接受误差 |
| 百分比 | `DECIMAL(5,2)` | 0.00 ~ 999.99 |
| 大金额（加密货币） | `DECIMAL(20,8)` | 高精度 |

#### 3. 字符串类型

| 类型 | 最大长度 | 存储方式 | 适用场景 |
| --- | --- | --- | --- |
| CHAR(N) | N 字符（≤255） | 定长，不足补空格 | 定长编码、哈希值 |
| VARCHAR(N) | N 字符（行总 65535） | 变长，存实际长度+1-2字节 | 大部分字符串 |
| TINYTEXT | 255 字节 | 变长，不能有默认值 | 短文本 |
| TEXT | 64KB | 变长 | 文章正文 |
| MEDIUMTEXT | 16MB | 变长 | 长文档 |
| LONGTEXT | 4GB | 变长 | 超长文本 |
| BLOB 系列 | 同 TEXT | 二进制 | 图片、文件（不建议存DB） |

**CHAR vs VARCHAR**：

| 维度 | CHAR(10) | VARCHAR(10) |
| --- | --- | --- |
| 存储 'abc' | 占 10 字符位 | 占 3 字符 + 长度字节 |
| 尾部空格 | 检索时去除 | 保留 |
| 检索速度 | 略快（定长） | 略慢 |
| 空间 | 浪费 | 节省 |

> 经验：90% 场景用 VARCHAR；只有定长编码（如 MD5 的 32 位十六进制、国家代码 2 位）才用 CHAR。

#### 4. 枚举与集合

| 类型 | 语义 | 内部存储 | 示例 |
| --- | --- | --- | --- |
| ENUM('a','b','c') | 单选 | 整数 1/2/3 | `status ENUM('draft','on_sale')` |
| SET('a','b','c') | 多选 | 位图 1/2/4 | `perms SET('read','write','del')` |

```sql
CREATE TABLE t (
  status ENUM('draft','on_sale','off_sale'),   -- 只能取三者之一
  perms  SET('read','write','delete')          -- 可组合: 'read,write'
);

INSERT INTO t VALUES ('on_sale', 'read,write');
-- ENUM 'on_sale' 内部存 2
-- SET 'read,write' 内部存 3 (1+2)
```

> ENUM/SET 节省空间，但修改枚举值需 ALTER TABLE。互联网项目常用 TINYINT + 业务字典替代 ENUM，灵活性更高。

#### 5. 日期时间类型

| 类型 | 字节 | 范围 | 说明 |
| --- | --- | --- | --- |
| DATE | 3 | 1000-01-01 ~ 9999-12-31 | 仅日期 |
| TIME | 3 | -838:59:59 ~ 838:59:59 | 仅时间 |
| YEAR | 1 | 1901 ~ 2155 | 年份 |
| DATETIME | 8 | 1000-01-01 ~ 9999-12-31 | 日期时间，**与时区无关** |
| TIMESTAMP | 4 | 1970-01-01 ~ 2038-01-19 | 时间戳，**受时区影响**，自动更新 |

**DATETIME vs TIMESTAMP**：

| 维度 | DATETIME | TIMESTAMP |
| --- | --- | --- |
| 字节 | 8 | 4 |
| 范围 | 大（到 9999 年） | 小（2038 年问题） |
| 时区 | 不转换 | 存储 UTC，读取按会话时区转换 |
| 自动更新 | 需手动设 `ON UPDATE` | 支持 `DEFAULT CURRENT_TIMESTAMP ON UPDATE` |
| 适用 | 历史日期、出生日期 | 记录创建/更新时间 |

```sql
-- 经典时间列模式
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
```

#### 6. JSON 类型

MySQL 8 大幅增强 JSON 支持，适合存半结构化数据（配置、标签、扩展属性）。

| 操作 | 函数/语法 |
| --- | --- |
| 提取（带引号） | `JSON_EXTRACT(j, '$.key')` 或 `j->'$.key'` |
| 提取（去引号） | `j->>'$.key'` |
| 构造数组 | `JSON_ARRAY(1,2,3)` |
| 构造对象 | `JSON_OBJECT('k','v')` |
| 修改 | `JSON_SET(j, '$.k', val)` |
| 包含判断 | `JSON_CONTAINS(j, '"val"')` |
| 转表 | `JSON_TABLE(j, ...)` |

```sql
-- 提取与查询
SELECT j->>'$.name' AS 姓名, j->>'$.addr.city' AS 城市
FROM users WHERE JSON_CONTAINS(j->'$.tags', '"vip"');
```

#### 7. 类型选择原则速查表

| 业务场景 | 推荐类型 | 理由 |
| --- | --- | --- |
| 主键 | BIGINT AUTO_INCREMENT | 范围大，自增 |
| 状态/枚举 | TINYINT 或 ENUM | 节省空间 |
| 金额 | DECIMAL(10,2) | 精确无误差 |
| 用户名/邮箱 | VARCHAR(50)/(100) | 变长灵活 |
| 密码哈希 | VARCHAR(255) | 兼容各算法 |
| 文章正文 | TEXT/MEDIUMTEXT | 按长度选 |
| 创建/更新时间 | TIMESTAMP | 自动更新 |
| 出生日期 | DATE | 仅日期 |
| 布尔值 | TINYINT(1) | MySQL 无真正 BOOL |
| 标签/扩展属性 | JSON | 半结构化 |
| IP 地址 | VARCHAR(45) 或 INT UNSIGNED | IPv6 用 VARCHAR |
| 国家代码 | CHAR(2) | 定长 |

### 二、约束

#### 1. PRIMARY KEY 主键

- **特性**：唯一 + 非空，每表只能一个。
- **建议**：用 `BIGINT AUTO_INCREMENT` 代理主键，不使用业务字段（如手机号）作主键。

```sql
id BIGINT AUTO_INCREMENT PRIMARY KEY
```

#### 2. NOT NULL 非空

- **特性**：不允许 NULL。
- **关键**：空字符串 `''` 不是 NULL，能通过 NOT NULL；`0` 也不是 NULL。

```sql
-- '' 通过 NOT NULL，但业务上可能仍是脏数据
INSERT INTO t (username) VALUES ('');  -- 成功
```

> 设计原则：能用 NOT NULL 就 NOT NULL，NULL 会带来三值逻辑复杂度与索引问题。

#### 3. UNIQUE 唯一约束

- **特性**：列值唯一，但**允许多个 NULL**（NULL 不参与比较）。
- **与主键区别**：一张表只能一个主键，但可有多个 UNIQUE。

```sql
email VARCHAR(100) NOT NULL UNIQUE  -- 列级
-- 或
CONSTRAINT uk_users_email UNIQUE (email)  -- 表级，推荐命名
```

#### 4. DEFAULT 默认值

- **特性**：插入未指定列时取默认值。
- **特殊**：`CURRENT_TIMESTAMP` 可用于时间列；8.0 支持表达式默认值（需括号）。

```sql
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
qty INT NOT NULL DEFAULT 1,
created_date DATE NOT NULL DEFAULT (CURRENT_DATE)  -- 8.0 表达式
```

#### 5. CHECK 检查约束

- **8.0 真正校验**：5.7 仅解析不生效，8.0 起会真正检查。
- **语法**：`CHECK (条件表达式)`。

```sql
CONSTRAINT chk_age CHECK (age BETWEEN 0 AND 150),
CONSTRAINT chk_balance CHECK (balance >= 0)
```

#### 6. FOREIGN KEY 外键

- **作用**：保证子表外键值在父表存在，维护引用完整性。
- **级联策略**：

| 策略 | ON DELETE 行为 | ON UPDATE 行为 |
| --- | --- | --- |
| CASCADE | 删父行，子行一起删 | 改父主键，子外键跟着改 |
| RESTRICT | 子行引用中，禁止删父 | 禁止改父主键 |
| NO ACTION | 同 RESTRICT（标准SQL） | 同 RESTRICT |
| SET NULL | 子外键置 NULL（需可空） | 子外键置 NULL |
| SET DEFAULT | 8.0 不支持 | 不支持 |

```sql
FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE RESTRICT ON UPDATE CASCADE
```

> **何时用外键**：传统业务系统、强一致性场景用；互联网高并发场景常不用外键（影响插入性能、死锁风险），改由应用层保证一致性。本教程 ecommerce 为教学完整保留外键。

#### 7. AUTO_INCREMENT 自增

- **特性**：每表一个，必须是键的一部分；默认从 1 开始，步长 1。
- **间隙**：删除记录后，自增值不复用，产生间隙。
- **起始值**：`CREATE TABLE ... AUTO_INCREMENT=1000`。
- **获取最近 ID**：`LAST_INSERT_ID()` 返回当前连接最近一次插入的自增 ID。

```sql
-- 多行插入时，LAST_INSERT_ID() 返回第一行的 ID
INSERT INTO t (name) VALUES ('a'),('b'),('c');
SELECT LAST_INSERT_ID();  -- 返回 'a' 的 ID，不是 'c' 的
```

#### 8. 约束命名规范

| 约束类型 | 命名前缀 | 示例 |
| --- | --- | --- |
| 主键 | pk_ | pk_users |
| 唯一键 | uk_ | uk_users_email |
| 外键 | fk_ | fk_orders_user_id |
| 检查 | chk_ | chk_balance_nonneg |
| 默认 | 无需命名 | — |

> 显式命名便于后续 `ALTER TABLE ... DROP CONSTRAINT` 管理；MySQL 自动生成的名字难记忆。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01-data-types-demo.sql` | 在 `type_demo` 库演示各数据类型（数值/字符串/日期/JSON/ENUM/SET） |
| `Code/02-constraints-demo.sql` | 在 `constraint_demo` 库演示七大约束，含故意违规的报错案例 |
| `README.md` | 本章理论文档 |

执行方式：

```sql
-- 数据类型演示（独立库，不影响 ecommerce）
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day03/Code/01-data-types-demo.sql;

-- 约束演示（独立库，含故意失败的语句需手动取消注释观察报错）
mysql> SOURCE d:/Coding/AI-FullStack/MySQL/Day03/Code/02-constraints-demo.sql;
```

> `02-constraints-demo.sql` 中故意违反约束的 INSERT 已注释，需手动取消注释观察报错信息。

## 关键知识点总结

### 1. 数据类型速查表

| 类别 | 类型 | 关键点 |
| --- | --- | --- |
| 整数 | TINYINT/SMALLINT/MEDIUMINT/INT/BIGINT | 1/2/3/4/8 字节，主键用 BIGINT |
| 浮点 | FLOAT/DOUBLE | 近似值，禁存金额 |
| 定点 | DECIMAL(M,D) | 精确值，金额必选 |
| 字符串 | CHAR/VARCHAR | 定长 vs 变长，默认 VARCHAR |
| 大文本 | TEXT 系列 | 64KB ~ 4GB |
| 二进制 | BLOB 系列 | 不建议存 DB |
| 枚举 | ENUM | 单选，内部整数 |
| 集合 | SET | 多选，内部位图 |
| 日期 | DATE/TIME/YEAR | 单一维度 |
| 时间 | DATETIME/TIMESTAMP | 8字节无时区 / 4字节有时区 |
| 半结构 | JSON | 8.0 增强，支持 ->> 与 JSON_TABLE |

### 2. 约束速查表

| 约束 | 关键字 | 作用 | 命名前缀 |
| --- | --- | --- | --- |
| 主键 | PRIMARY KEY | 唯一+非空 | pk_ |
| 非空 | NOT NULL | 禁止 NULL | — |
| 唯一 | UNIQUE | 唯一，允许多NULL | uk_ |
| 默认 | DEFAULT | 默认值 | — |
| 检查 | CHECK | 8.0 真正校验 | chk_ |
| 外键 | FOREIGN KEY | 引用完整性 | fk_ |
| 自增 | AUTO_INCREMENT | 自增（须为键） | — |

### 3. 外键级联策略速查

| 策略 | 删父行 | 用途 |
| --- | --- | --- |
| CASCADE | 子行一起删 | 强从属（订单→明细） |
| RESTRICT | 禁止删 | 防误删（被引用的父） |
| SET NULL | 子外键置NULL | 弱关联（员工→导师） |
| NO ACTION | 同 RESTRICT | 标准 SQL 写法 |

### 4. 常见约束违规错误码

| 错误码 | 含义 |
| --- | --- |
| 1062 | 主键/唯一键重复 |
| 1048 | NOT NULL 违反 |
| 1452 | 外键父行不存在 |
| 1451 | 外键子行引用中，禁止删父 |
| 3819 | CHECK 约束违反 |
| 1264 | 数值越界 |
| 1265 | ENUM 非法值 |

## 实战练习

1. **金额精度实验**
   - 创建表 `t1(amount_float FLOAT, amount_dec DECIMAL(10,2))`。
   - 插入 `0.1` 并连续累加 10 次，对比两列结果与 `10 * 0.1` 是否相等。
   - 思考：为什么电商订单金额必须用 DECIMAL？

2. **约束违规实验**
   - 创建一张 `accounts(id, user_id UNIQUE, balance DECIMAL CHECK(balance>=0))`。
   - 依次执行：插入合法数据、插入重复 user_id、插入负数 balance、插入 NULL user_id，记录每个报错码。
   - 将 `balance` 改为允许负数（删 CHECK），重新插入负数，验证约束已失效。

3. **外键级联实验**
   - 创建 `father(id PK)` 和 `child(id PK, fid FK REFERENCES father(id) ON DELETE CASCADE)`。
   - 插入父记录 1、2，子记录 (1,1)、(2,2)、(3,1)。
   - 删除父记录 1，观察哪些子记录被级联删除。
   - 把级联策略改为 `ON DELETE RESTRICT`，重复实验，观察删父时的报错。
