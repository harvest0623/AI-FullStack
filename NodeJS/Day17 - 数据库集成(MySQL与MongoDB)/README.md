# Day17 - 数据库集成（MySQL 与 MongoDB）

> 前端工程师习惯了 localStorage / IndexedDB / Redux 这些“内存级”存储，一旦要构建真正可用的 AI 应用——存储用户对话历史、持久化向量元数据、记录模型推理日志、维护文档知识库——就必须直面**服务端数据库**。本篇聚焦 Node.js 后端两大主流数据库的集成：关系型的 **MySQL**（用 `mysql2`）与文档型的 **MongoDB**（用 `mongoose`）。你将理解两者的本质差异、连接池为何是生产必备、参数化查询如何杜绝 SQL 注入、mongoose 的 Schema/Model/Connection 三层架构，以及在 Express 中如何用 Repository 模式把数据访问层干净地隔离出来。掌握本篇后，你就具备了为 AI 应用落地持久化层的能力。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 关系型 vs 文档型：MySQL 与 MongoDB 对比](#21-关系型-vs-文档型mysql-与-mongodb-对比)
  - [2.2 连接池：为什么不能每次请求新建连接](#22-连接池为什么不能每次请求新建连接)
  - [2.3 ORM/ODM 与原生 driver 的取舍](#23-ormodm-与原生-driver-的取舍)
- [三、MySQL 集成（mysql2）](#三mysql-集成mysql2)
  - [3.1 mysql2 vs mysql 包](#31-mysql2-vs-mysql-包)
  - [3.2 创建连接池 createPool](#32-创建连接池-createpool)
  - [3.3 pool.execute vs pool.query](#33-poolexecute-vs-poolquery)
  - [3.4 参数化 CRUD](#34-参数化-crud)
  - [3.5 事务：getConnection + beginTransaction/commit/rollback](#35-事务getconnection--begintransactioncommitrollback)
  - [3.6 SQL 注入防御](#36-sql-注入防御)
- [四、MongoDB 集成（mongoose）](#四mongodb-集成mongoose)
  - [4.1 mongoose 三层架构](#41-mongoose-三层架构)
  - [4.2 连接 mongoose.connect](#42-连接-mongooseconnect)
  - [4.3 定义 Schema](#43-定义-schema)
  - [4.4 Model CRUD](#44-model-crud)
  - [4.5 关联 populate](#45-关联-populate)
  - [4.6 聚合 aggregate](#46-聚合-aggregate)
  - [4.7 连接事件与连接池配置](#47-连接事件与连接池配置)
- [五、在 Express 中的集成模式](#五在-express-中的集成模式)
  - [5.1 DAO / Repository 模式](#51-dao--repository-模式)
  - [5.2 分层调用：Service 调 DAO](#52-分层调用service-调-dao)
  - [5.3 连接单例](#53-连接单例)
  - [5.4 错误处理：数据库错误转 HTTP 状态码](#54-错误处理数据库错误转-http-状态码)
- [六、数据建模最佳实践](#六数据建模最佳实践)
- [七、AI 全栈场景](#七ai-全栈场景)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说清 MySQL（关系型）与 MongoDB（文档型）在数据模型、Schema、事务、JOIN、索引、扩展方式与适用场景上的核心差异，能根据业务特征选型。
2. 解释连接池的工作原理，理解“每次请求新建 TCP 连接”的开销，能用 `mysql2.createPool` 与 mongoose `maxPoolSize` 配置连接池。
3. 权衡 ORM/ODM 与原生 driver 的利弊，知道何时该用 mongoose、何时该回退到原生 MongoDB driver。
4. 用 `mysql2/promise` 创建连接池，区分 `pool.execute`（prepared statement，防注入）与 `pool.query`（普通查询）的适用场景。
5. 写出参数化的 SELECT/INSERT/UPDATE/DELETE，并理解为什么“字符串拼接 SQL”是高危动作。
6. 用 `pool.getConnection` + `beginTransaction`/`commit`/`rollback` 实现事务，知道事务内为何必须复用同一连接。
7. 理解 mongoose 的 Connection / Schema / Model 三层架构，能定义带校验、索引、时间戳的 Schema。
8. 用 mongoose Model 完成 CRUD、`populate` 关联查询、`aggregate` 聚合管道。
9. 在 Express 中用 DAO/Repository 模式封装数据访问层，实现 Service → Repository 分层，并把数据库错误映射为合适的 HTTP 状态码。
10. 为 AI 应用的典型场景（对话历史、向量元数据、知识库、推理日志）设计合适的数据模型。

---

## 二、理论知识讲解

### 2.1 关系型 vs 文档型：MySQL 与 MongoDB 对比

数据库选型是架构设计的第一步。理解两者差异，才能避免“拿着锤子找钉子”。

| 维度 | MySQL（关系型 RDBMS） | MongoDB（文档型 Document） |
|------|----------------------|---------------------------|
| **数据模型** | 二维表（行/列），所有行结构一致 | BSON 文档（类 JSON），同一集合内文档结构可不同（灵活 schema） |
| **Schema** | 强制 schema，建表时定义列类型/约束，改表需 `ALTER TABLE` | 默认动态 schema，字段可随时增减；可用 mongoose 在应用层加 schema 约束 |
| **事务** | 原生支持 ACID 事务（InnoDB 引擎），跨表多行事务成熟稳定 | 4.0+ 支持多文档事务（副本集），4.4+ 支持分片事务；单文档操作天然原子 |
| **JOIN** | 强项，`INNER/LEFT JOIN` 可关联多表，适合强关联数据 | 弱项，无原生 JOIN；用 `populate`/`$lookup` 在应用或聚合层模拟，关联多了性能差 |
| **索引** | B+Tree 索引、唯一索引、联合索引、全文索引；索引建在磁盘 | B-Tree、复合索引、文本索引、地理索引、TTL 索引；支持单字段/多键索引 |
| **扩展方式** | 主要纵向扩展（加 CPU/内存），分库分表成本高 | 原生支持分片（sharding），横向扩展友好，适合海量数据 |
| **查询语言** | SQL（声明式，标准化） | MongoDB Query Language（JSON 风格，API 化） |
| **存储格式** | 行存，磁盘紧凑，适合结构化数据 | BSON，类 JSON，适合半结构化/嵌套数据 |
| **适用场景** | 强一致性事务（金融/订单）、关系复杂、查询模式稳定 | 数据结构多变、读写量大、嵌套深、水平扩展需求强（内容、日志、向量元数据） |
| **AI 场景倾向** | 用户账户、订单、计费等强一致业务 | 对话历史、文档知识库、推理日志、向量元数据等灵活数据 |

一句话选型口诀：**强一致 + 强关联 + 事务 → MySQL；灵活结构 + 高吞吐 + 易扩展 → MongoDB。** 很多 AI 应用会两者并用：MySQL 管账户与计费，MongoDB 存对话与知识库。

### 2.2 连接池：为什么不能每次请求新建连接

前端工程师容易忽略连接的成本。建立一条数据库连接远不是“new 一个对象”那么简单：

1. **TCP 三次握手**：客户端与数据库服务器建立 TCP 连接（1 个 RTT）。
2. **数据库握手与鉴权**：MySQL 协议握手、发送用户名密码、校验权限（额外 1~2 个 RTT）。
3. **SSL/TLS 协商**（若启用）：又是几个 RTT。

整个过程在局域网也要 **10~50ms**，跨可用区更高。如果每个 HTTP 请求都新建连接，相当于每个请求都白白多花几十毫秒，QPS 一高就把数据库的连接数打满（MySQL 默认 `max_connections=151`）。

**连接池**的思路很简单：

- 启动时预先建立 N 条连接，放在池子里。
- 请求到来时，从池里“借”一条连接用，用完“归还”，而非关闭。
- 池满时新请求排队等待（而非报错），空闲连接定期保活。

这样把“建连成本”摊薄到启动期，运行期每次请求只承担“借还”的微秒级开销。**生产环境必须用连接池，这是硬性要求。**

| 配置项 | mysql2 | mongoose |
|--------|--------|----------|
| 最大连接数 | `connectionLimit`（默认 10） | `maxPoolSize`（默认 100） |
| 等待策略 | `waitForConnections: true` 排队 | 自动排队 |
| 空闲超时 | `idleTimeout` | `socketTimeoutMS` 等 |
| Node 单进程建议值 | 10~20 | 10~50（按并发量调） |

> 经验：连接池不是越大越好。连接太多会压垮数据库（每个连接占内存，且争抢锁），反而降低吞吐。一般“应用并发量 ≈ 连接数”即可。

### 2.3 ORM/ODM 与原生 driver 的取舍

| 方案 | 代表 | 优点 | 缺点 |
|------|------|------|------|
| **原生 driver** | `mysql2`、`mongodb`（原生） | 性能最优、零魔法、SQL/MQL 透明可控 | 无 Schema 约束、手写查询多、关联/迁移要自己搞 |
| **ORM/ODM** | `mongoose`、`Sequelize`、`Prisma` | Schema 校验、关联封装、迁移工具、类型友好 | 性能略损、有学习曲线、复杂查询需回退原生 |

取舍原则：

- **MongoDB 强烈推荐 mongoose**：MongoDB 无 schema 是双刃剑，mongoose 在应用层补上校验/钩子/关联，几乎无成本，生态最成熟。
- **MySQL 视团队而定**：小项目用 `mysql2` 原生 + 参数化即可，足够轻量；中大型项目、需要类型安全与迁移管理时再上 Prisma/Sequelize。
- **复杂查询回退原生**：任何 ORM 都有覆盖不到的场景，mongoose 提供 `Model.collection` / `aggregate`，Sequelize 提供 `sequelize.query`，必要时直接写 SQL/MQL。

本篇 MySQL 用原生 `mysql2`（聚焦连接池/事务/防注入这些底层能力），MongoDB 用 `mongoose`（聚焦 Schema/Model/populate 这些工程化能力），覆盖两种主流姿势。

---

## 三、MySQL 集成（mysql2）

### 3.1 mysql2 vs mysql 包

Node 生态有两个主流 MySQL 客户端：

| 包 | 状态 | Promise | Prepared Statements | 性能 |
|----|------|---------|---------------------|------|
| `mysql` | 维护模式（不再加新特性） | 需自己 `util.promisify` | ❌ 不支持 | 基准 |
| `mysql2` | 活跃维护 | ✅ 内置 `mysql2/promise` | ✅ `execute` 原生支持 | 比 mysql 快 ~20% |

`mysql2` 是 `mysql` 的现代化分支，API 大体兼容，但**额外支持 Promise 与 prepared statements**，是新项目的不二之选。本篇统一用 `mysql2`。

```js
// ❌ 回调风格（旧）
const mysql = require('mysql2');
mysql.createConnection(...).query(sql, (err, rows) => { ... });

// ✅ Promise 风格（推荐）
const mysql = require('mysql2/promise'); // 注意子路径
const [rows] = await pool.execute('SELECT * FROM users WHERE id = ?', [id]);
```

### 3.2 创建连接池 createPool

```js
const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host: '127.0.0.1',
  port: 3306,
  user: 'day17',
  password: 'day17pass',
  database: 'day17_demo',
  waitForConnections: true, // 池满时排队等待
  connectionLimit: 10,      // 最大连接数
  queueLimit: 0,            // 等待队列上限（0=不限）
  charset: 'utf8mb4',       // 必须 utf8mb4 才能存 emoji
});
```

要点：

- **配置走环境变量**，绝不硬编码密码（用 `dotenv` 加载 `.env`）。
- `connectionLimit` 根据 DB 的 `max_connections` 与应用并发量设，单进程 10~20 足够。
- `pool.execute(...)` 会自动借连接、执行、归还，**无需手动 `getConnection`/`release`**——除非你要用事务（见 3.5）。
- `charset: 'utf8mb4'` 是存中文/emoji 的前提，`utf8` 在 MySQL 中是 3 字节截断版，会踩坑。

### 3.3 pool.execute vs pool.query

这是 `mysql2` 最容易混淆的两套 API：

| 方法 | 底层机制 | 参数处理 | 防注入 | 适用场景 |
|------|---------|---------|--------|---------|
| `pool.execute` | 先 `PREPARE` 模板，再 `EXECUTE` 传参 | 参数作为“值”绑定，不参与 SQL 解析 | ✅ 天然防注入 | 含用户输入的 DML（INSERT/UPDATE/DELETE/SELECT） |
| `pool.query` | 直接发送整条 SQL 文本 | 参数被转义后**拼接**进 SQL 字符串 | ⚠️ 依赖 driver 转义 | DDL、固定 SQL、一次性大查询 |

```js
// ✅ 推荐：含用户输入一律用 execute
const [rows] = await pool.execute(
  'SELECT * FROM users WHERE username = ?',
  [userInput]
);

// DDL/固定 SQL 用 query 即可
await pool.query('CREATE TABLE IF NOT EXISTS ...');
```

经验法则：**只要 SQL 里有 `?` 占位符绑定用户输入，就用 `execute`**；只有完全静态的语句才用 `query`。

### 3.4 参数化 CRUD

四类基本操作的标准写法（全部参数化）：

```js
// INSERT
const [result] = await pool.execute(
  'INSERT INTO users (username, email) VALUES (?, ?)',
  ['alice', 'alice@example.com']
);
console.log(result.insertId); // 自增主键

// SELECT（返回 [rows, fields]）
const [rows] = await pool.execute(
  'SELECT id, username FROM users WHERE id = ?',
  [userId]
);

// UPDATE
const [result] = await pool.execute(
  'UPDATE users SET email = ? WHERE id = ?',
  ['new@example.com', userId]
);
console.log(result.affectedRows); // 受影响行数

// DELETE
const [result] = await pool.execute(
  'DELETE FROM users WHERE id = ?',
  [userId]
);
```

> 注意 `IN (?)` 不能直接传数组，`mysql2` 对数组占位符支持有限。常见做法是用 `IN (?, ?, ?)` 动态生成占位符，或用 `query` + 数组（`mysql2` 会展开）。

### 3.5 事务：getConnection + beginTransaction/commit/rollback

事务是关系型数据库的王牌。经典转账场景：A 扣钱 + B 加钱必须原子，否则资金会凭空消失或凭空产生。

**关键认知**：事务内的多条语句必须**复用同一条连接**。如果用 `pool.execute`，每条语句可能拿到不同连接，事务边界就失效了。所以事务必须手动 `getConnection`。

```js
async function transfer(from, to, amount) {
  const conn = await pool.getConnection(); // 借一条独占连接
  try {
    await conn.beginTransaction();          // 开启事务

    await conn.execute('UPDATE accounts SET balance = balance - ? WHERE name = ?', [amount, from]);
    await conn.execute('UPDATE accounts SET balance = balance + ? WHERE name = ?', [amount, to]);

    await conn.commit();                    // 全部成功 → 提交
  } catch (err) {
    await conn.rollback();                  // 任一失败 → 回滚
    throw err;
  } finally {
    conn.release();                         // 务必归还连接！否则泄漏直至池满
  }
}
```

事务模板四步走（背下来）：

1. `getConnection` 借独占连接。
2. `beginTransaction` 开启。
3. 业务 SQL 全部成功 → `commit`；任一失败 → `rollback`。
4. `finally` 里 `release` 归还连接。

补充：

- 事务要尽量**短**，长时间持有连接会占满连接池。
- 并发转账要加**行锁**（`SELECT ... FOR UPDATE`）防止脏读/丢失更新。
- 只有 **InnoDB** 引擎支持事务，建表务必 `ENGINE=InnoDB`。

完整转账示例见 `Code/mysql-transaction.js`。

### 3.6 SQL 注入防御

SQL 注入是 OWASP Top 10 常客，本质是**把用户输入当作 SQL 代码执行**。

```js
const userInput = "alice'; DROP TABLE users; --";

// ❌ 致命错误：字符串拼接
const sql = `SELECT * FROM users WHERE username = '${userInput}'`;
// 实际执行：SELECT * FROM users WHERE username = 'alice'; DROP TABLE users; --'
// 后果：users 表被删

// ✅ 正解：参数化查询（? 占位符）
const [rows] = await pool.execute(
  'SELECT * FROM users WHERE username = ?',
  [userInput]
);
// userInput 整体被当作“用户名值”，不会被解析为多条语句
```

防御铁律：

1. **永远不要把用户输入拼进 SQL**，无论多“安全”的转义函数都不如参数化。
2. 一律用 `pool.execute` + `?` 占位符，参数由 driver 安全绑定。
3. 表名/列名无法用占位符（占位符只能绑定“值”），若必须动态拼接表名，**用白名单校验**，不要直接拼用户输入。
4. 数据库账号**最小权限**：应用账号别给 `DROP`/`GRANT`，即便被注入也降低爆炸半径。

---

## 四、MongoDB 集成（mongoose）

### 4.1 mongoose 三层架构

mongoose 是 MongoDB 的 ODM（Object Document Mapper），用三层抽象组织代码：

| 层 | 作用 | 类比 MySQL |
|----|------|-----------|
| **Connection** | 管理到 MongoDB 的连接（单例），监听连接事件 | 连接池 |
| **Schema** | 定义文档结构：字段名、类型、校验、索引、钩子、时间戳 | DDL/建表 |
| **Model** | 由 Schema 编译而成的类，提供 CRUD 静态方法，对应一个 collection | Table + DAO |

```
mongoose.connect(uri)          → Connection（全局单例）
new Schema({...})              → 定义结构
mongoose.model('User', schema) → Model（操作 users 集合）
new User({...}).save()         → Document（一条具体文档）
```

### 4.2 连接 mongoose.connect

```js
const mongoose = require('mongoose');

// 监听连接事件（排查问题必备）
mongoose.connection.on('connected', () => console.log('Mongo 已连接'));
mongoose.connection.on('disconnected', () => console.warn('Mongo 断开'));
mongoose.connection.on('error', (err) => console.error('Mongo 错误', err));

await mongoose.connect('mongodb://127.0.0.1:27017/day17_demo', {
  maxPoolSize: 20,              // 连接池大小
  serverSelectionTimeoutMS: 5000, // 5s 连不上就报错
});
```

要点：

- **mongoose 6+ 默认已启用** `useNewUrlParser`/`useUnifiedTopology`，**无需再传**这些旧选项（传了会报警告）。
- `maxPoolSize` 控制连接池大小，默认 100，Node 单进程建议 10~50。
- `serverSelectionTimeoutMS` 控制连接超时，避免服务挂起。
- URI 格式：`mongodb://[user:pass@]host[:port]/dbname`，云端用 `mongodb+srv://...`。

### 4.3 定义 Schema

Schema 是 mongoose 的核心，它在应用层补上了 MongoDB 缺失的“结构约束”：

```js
const userSchema = new Schema({
  username: {
    type: String,
    required: [true, '用户名必填'],  // required 带自定义错误
    unique: true,                    // 唯一索引
    trim: true,                      // 自动去首尾空白
    minlength: 3,
    maxlength: 30,
  },
  email: {
    type: String,
    required: true,
    lowercase: true,
    match: [/^[\w.+-]+@[\w-]+\.[\w.-]+$/, '邮箱格式不正确'], // 正则校验
    index: true,                     // 普通索引
  },
  role: {
    type: String,
    enum: ['admin', 'editor', 'viewer'], // 枚举校验
    default: 'viewer',
  },
  age: {
    type: Number,
    validate: {                       // 自定义校验器
      validator: (v) => v === null || (v >= 0 && v <= 150),
      message: '年龄必须在 0~150 之间',
    },
  },
}, {
  timestamps: true,   // 自动加 createdAt / updatedAt
  strict: true,       // 未声明字段不保存
});

const User = mongoose.model('User', userSchema);
```

Schema 支持的能力清单：

- **字段类型**：`String`/`Number`/`Date`/`Boolean`/`ObjectId`/`Array`/`Mixed`/`Map`/`Buffer`/`Decimal128`。
- **校验**：`required`、`minlength`/`maxlength`、`min`/`max`、`enum`、`match`、自定义 `validate`。
- **索引**：`unique: true`（唯一）、`index: true`（普通）、`index: 'text'`（全文）、复合索引用 `schema.index({ a: 1, b: -1 })`。
- **默认值**：`default: 值` 或 `default: () => Date.now()`（函数形式每次求值）。
- **时间戳**：`timestamps: true` 自动维护 `createdAt`/`updatedAt`，等价 MySQL 的 `DEFAULT CURRENT_TIMESTAMP` + `ON UPDATE CURRENT_TIMESTAMP`。
- **钩子**：`pre('save', fn)`/`post('save', fn)` 等，可在保存前后插入逻辑（加密密码、发事件）。
- **虚拟字段**：`schema.virtual('xxx').get(...)` 定义派生字段，不入库。
- **实例/静态方法**：`schema.methods.xxx` / `schema.statics.xxx`。

### 4.4 Model CRUD

```js
// Create
const user = await User.create({ username: 'alice', email: 'a@b.com' });
// 或
const u = new User({ username: 'alice' });
await u.save();

// Read
const all = await User.find({ role: 'admin' }).sort({ createdAt: -1 }).limit(10);
const one = await User.findOne({ email: 'a@b.com' });
const byId = await User.findById(id);

// Update
const updated = await User.findByIdAndUpdate(id, { $set: { age: 30 } }, { new: true, runValidators: true });
const res = await User.updateOne({ username: 'alice' }, { $inc: { loginCount: 1 } });
const found = await User.findOneAndUpdate({ email: 'a@b.com' }, { age: 31 }, { new: true });

// Delete
await User.deleteOne({ _id: id });
await User.findByIdAndDelete(id);
```

关键点：

- `findByIdAndUpdate` 默认返回**旧文档**，加 `{ new: true }` 才返回更新后的。
- `{ runValidators: true }` 让 update 也跑 Schema 校验（默认 update 不校验）。
- MongoDB 更新操作符：`$set`/`$inc`/`$push`/`$pull`/`$unset`，**不要**传整个文档覆盖（会清空未传字段）。
- 查询链式：`find().sort().skip().limit().select().populate().lean()`，`lean()` 返回纯 JS 对象，更快。

### 4.5 关联 populate

MongoDB 无原生 JOIN，mongoose 用 `populate` 在应用层“联表”：Schema 里存 ObjectId 引用，查询时用 populate 替换成完整文档。

```js
// Schema 定义引用
const articleSchema = new Schema({
  author: { type: Schema.Types.ObjectId, ref: 'User', required: true },
});

// 查询时 populate
const article = await Article.findById(id).populate('author', 'username role -_id');
// article.author 从 ObjectId 变成完整 User 文档（只含 username/role，排除 _id）

// 多层 populate
await Article.find().populate({
  path: 'author',
  populate: { path: 'friends' },
});
```

`populate` 原理是**二次查询**：先查 articles，拿到 author 的 ObjectId 列表，再 `User.find({ _id: { $in: [...] } })`。所以它不是“免费 JOIN”，关联多了会 N+1，必要时用 `$lookup` 聚合或反范式优化。

### 4.6 聚合 aggregate

聚合管道（aggregation pipeline）是 MongoDB 的强大武器，类似 SQL 的 `GROUP BY` + 子查询，但用“管道阶段”表达：

```js
const stats = await Article.aggregate([
  { $match: { deleted: { $ne: true } } },        // 过滤（WHERE）
  { $group: { _id: '$author', count: { $sum: 1 } } }, // 分组统计
  { $lookup: { from: 'users', localField: '_id', foreignField: '_id', as: 'author' } }, // JOIN
  { $unwind: '$author' },                          // 展开数组
  { $sort: { count: -1 } },                        // 排序
  { $project: { username: '$author.username', count: 1 } }, // 投影（SELECT）
]);
```

常用阶段：`$match`（过滤）、`$group`（分组）、`$lookup`（关联）、`$unwind`（展开数组）、`$project`（投影）、`$sort`/`$limit`/`$skip`、`$count`、`$bucket`。AI 场景里用聚合统计“每用户对话次数”“模型调用耗时分布”很顺手。

### 4.7 连接事件与连接池配置

```js
const conn = mongoose.connection;
conn.readyState; // 0=disconnected 1=connected 2=connecting 3=disconnecting

conn.on('connected', () => {});
conn.on('disconnected', () => {}); // 网络抖动会触发，mongoose 会自动重连
conn.on('error', (err) => {});
conn.on('reconnected', () => {});

await mongoose.connect(uri, {
  maxPoolSize: 20,            // 连接池大小
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,     // socket 空闲超时
  heartbeatFrequencyMS: 10000, // 心跳间隔
});
```

生产建议：

- 监听 `disconnected`/`error` 事件并告警，连接断了用户请求会全挂。
- 优雅关闭时 `await mongoose.disconnect()`，别让进程直接退出留下半开连接。
- `readyState` 可用于健康检查接口（`/health` 返回 DB 状态）。

---

## 五、在 Express 中的集成模式

### 5.1 DAO / Repository 模式

把所有“直接碰数据库”的代码收拢到 Repository 类，上层只调接口，不关心底层是 MySQL 还是 MongoDB：

```js
// 接口约定（语言无关）
class ArticleRepository {
  async findAll(opts) {}
  async findById(id) {}
  async create(data) {}
  async update(id, data) {}
  async softDelete(id) {}
}

// Mongo 实现
class MongoArticleRepository extends ArticleRepository {
  async findAll({ limit = 20, offset = 0 } = {}) {
    return this.model.find().populate('author').skip(offset).limit(limit).lean();
  }
  // ...
}

// MySQL 实现（接口一致）
class MysqlArticleRepository extends ArticleRepository {
  async findAll({ limit = 20, offset = 0 } = {}) {
    const [rows] = await this.pool.execute(
      'SELECT a.*, u.username FROM articles a LEFT JOIN users u ON u.id = a.author_id LIMIT ? OFFSET ?',
      [limit, offset]
    );
    return rows;
  }
}
```

好处：

1. **可切换底层**：换数据库只改 Repository 实现，Service/Controller 零改动。
2. **可测试**：单测时注入内存版 Repository，无需真实 DB。
3. **逻辑集中**：SQL/查询不再散落在各路由，维护成本低。

### 5.2 分层调用：Service 调 DAO

典型 Express 应用四层结构：

```
Router → Controller → Service → Repository → Database
  路由      HTTP 解析    业务逻辑    数据访问
```

- **Controller**：解析 `req.body`/`req.params`，调 Service，组装 HTTP 响应。**不写业务逻辑，不碰 DB**。
- **Service**：业务逻辑（校验、组合多个 Repository、事务编排）。**不碰 HTTP 对象**。
- **Repository**：纯数据访问，每个实体一个类。

```js
// Controller
async function createArticle(req, res) {
  const article = await articleService.create(req.body); // 调 Service
  res.status(201).json({ data: article });
}

// Service
class ArticleService {
  async create(data) {
    if (!data.title) throw new ValidationError('title 必填');
    return this.repo.create(data); // 调 Repository
  }
}
```

### 5.3 连接单例

数据库连接是昂贵资源，**全局只建一个**：

```js
// db.js —— 连接单例
const mongoose = require('mongoose');
let connected = false;

async function connect() {
  if (connected) return mongoose.connection;
  await mongoose.connect(process.env.MONGO_URI);
  connected = true;
  return mongoose.connection;
}

module.exports = { connect, conn: mongoose.connection };
```

mysql2 的 `pool` 同理：模块级 `const pool = mysql.createPool(...)` 全进程共享。**不要在请求处理函数里 `createPool`/`createConnection`**，那是连接泄漏的万恶之源。

### 5.4 错误处理：数据库错误转 HTTP 状态码

数据库抛的错误是技术细节，不能直接丢给前端。需要在错误中间件里映射成合适的 HTTP 状态码：

| 数据库错误 | HTTP 状态码 | 含义 |
|-----------|------------|------|
| mongoose `CastError`（_id 格式错） | 400 | 请求参数格式错误 |
| mongoose `ValidationError`（校验失败） | 422 | 请求体不合法 |
| 唯一约束冲突（mongoose code 11000 / MySQL 1062） | 409 | 资源冲突 |
| 资源不存在（自定义 NotFoundError） | 404 | 找不到 |
| 连接断开/超时 | 503 | 服务暂不可用 |
| 其它未识别 | 500 | 服务器内部错误 |

```js
function toHttpError(err) {
  if (err.name === 'CastError') return { status: 400, message: '参数格式错误' };
  if (err.name === 'ValidationError') return { status: 422, message: err.message };
  if (err.code === 11000) return { status: 409, message: '唯一约束冲突' };
  if (err.code === 'NOT_FOUND') return { status: 404, message: err.message };
  return { status: 500, message: '服务器内部错误' };
}

app.use((err, req, res, next) => {
  const { status, message } = toHttpError(err);
  res.status(status).json({ code: status, message });
});
```

完整示例见 `Code/server.js` 与 `Code/repository-pattern.js`。

---

## 六、数据建模最佳实践

### MySQL 表设计

1. **主键**：每表必有主键，优先 `BIGINT AUTO_INCREMENT` 或 UUID（分布式场景）。避免用业务字段（手机号）做主键。
2. **字段类型**：能用 `TINYINT`/`SMALLINT` 就别用 `INT`；字符串定长用 `CHAR`、变长用 `VARCHAR` 并给合理长度；时间统一 `TIMESTAMP` 或 `DATETIME`。
3. **索引**：
   - 主键自动建索引。
   - 高频 `WHERE`/`JOIN`/`ORDER BY` 字段建索引。
   - 联合索引遵循**最左前缀**原则，把区分度高的列放前面。
   - 索引不是越多越好——写操作要维护索引，索引过多拖慢 INSERT/UPDATE。
4. **外键**：强关联数据用外键保证完整性，但高并发场景为性能常去掉外键、由应用层保证。
5. **字符集**：统一 `utf8mb4`，否则存 emoji/生僻字会报错。
6. **引擎**：事务用 InnoDB，MyISAM 已不推荐。

### MongoDB：嵌入式 vs 引用式

MongoDB 文档可嵌套，建模有两条路线：

| 方式 | 写法 | 适用场景 | 优缺点 |
|------|------|---------|--------|
| **嵌入式**（Embed） | 文档内嵌子文档数组 | 1 对少、子文档随父文档一起读、不单独查询 | 读快（一次查询拿全）、写简单；但子文档无限增长会超 16MB 限制 |
| **引用式**（Reference） | 存 ObjectId，查询时 populate | 1 对多/多对多、子文档需独立查询/更新 | 节省空间、子文档可复用；但需二次查询，关联多时慢 |

经验：

- **优先嵌入式**，除非子文档会无限增长或需独立访问。
- 博客文章的“评论”若量小且总一起读 → 嵌入；若评论上千条需分页 → 引用。
- 用户与文章（1 对多、文章独立查询）→ 引用（Article 存 author: ObjectId）。

### 时间戳 createdAt / updatedAt

- MySQL：`created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`，`updated_at TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`。
- mongoose：`{ timestamps: true }` 自动维护。
- 时间戳是审计/排查/排序的基础设施，**几乎每张表/每个 collection 都该有**。

### 软删除 vs 硬删除

| 方式 | 实现 | 优点 | 缺点 |
|------|------|------|------|
| **硬删除** | `DELETE FROM` / `deleteOne` | 释放空间、简单 | 不可恢复，审计/合规风险 |
| **软删除** | 加 `deleted` 字段，查询过滤 `WHERE deleted = 0` | 可恢复、保留审计、符合 GDPR“可撤销” | 查询要记得过滤、占用存储 |

实践：

- **业务数据优先软删除**（用户、文章、订单），尤其 AI 应用的对话历史——用户删了还能恢复，也便于分析。
- 软删除要配合**查询钩子自动过滤**（mongoose `pre('find')` 加 `deleted: { $ne: true }`），否则忘加过滤就是 bug。
- 定期清理过期软删除数据（TTL 索引或定时任务），避免无限膨胀。

---

## 七、AI 全栈场景

数据库在 AI 应用里的典型落地点：

### 1. 用户对话历史

- **特征**：结构灵活（消息有 role/content/token_count/metadata，不同模型字段不同）、写入频繁、按用户+会话分片读、需支持长上下文回溯。
- **选型**：MongoDB 更合适——消息结构多变，嵌套 `messages: [{role, content, ts}]` 自然，按 `userId`/`sessionId` 建索引，TTL 索引自动清理过期会话。
- **建模**：`Conversation { userId, sessionId, messages: [...], createdAt }`，或每个 message 一条文档（便于分页与检索）。

### 2. 向量元数据

- **特征**：向量本身通常存专用向量库（Milvus/Pinecone/pgvector），但**元数据**（原文片段、来源文档、chunk 偏移、标签）存关系或文档库。
- **选型**：MongoDB 存灵活元数据，或 PostgreSQL+pgvector 一体化。MySQL 8 也支持向量，但生态较弱。
- **建模**：`Chunk { docId, content, vectorId（外部向量库 ID）, metadata: {...} }`。

### 3. 文档知识库

- **特征**：文档结构异构（PDF/Markdown/网页提取后字段不同）、需存原文+分块+处理状态。
- **选型**：MongoDB 适合异构文档；若强关联（文档-章节-块多层且需事务）可用 MySQL。
- **建模**：`Document { title, source, status, chunks: [{text, embedding, metadata}] }`（嵌入）或引用。

### 4. 模型推理日志

- **特征**：写多读少、结构灵活（不同模型入参出参不同）、需按时间/用户/模型聚合统计（耗时、token、成本）。
- **选型**：MongoDB 写入吞吐高、结构灵活，配合 `aggregate` 做统计；超大量可上时序库或 ClickHouse。
- **建模**：`InferenceLog { userId, model, promptTokens, completionTokens, latencyMs, cost, createdAt }`，按 `createdAt` 建 TTL 自动过期。

> 这些场景几乎都倾向 MongoDB，正是 AI 应用偏爱文档库的原因。但账户/计费/权限仍走 MySQL——强一致事务不可妥协。

---

## 八、关键知识点总结

1. **选型**：强一致事务+强关联 → MySQL；灵活结构+高吞吐+易扩展 → MongoDB；AI 应用常两者并用。
2. **连接池是生产必备**：`mysql2` 用 `createPool({connectionLimit})`，mongoose 用 `maxPoolSize`，避免每请求新建 TCP 连接。
3. **mysql2 优于 mysql**：内置 Promise（`mysql2/promise`）与 prepared statements（`execute`）。
4. **`execute` vs `query`**：含用户输入一律 `execute`（防注入）；DDL/固定 SQL 用 `query`。
5. **事务四步**：`getConnection` → `beginTransaction` → 业务 SQL → `commit`/`rollback`，`finally` 里 `release`；事务内必须复用同一连接。
6. **SQL 注入防御**：永不字符串拼接，一律参数化；表名用白名单；账号最小权限。
7. **mongoose 三层**：Connection（单例连接）→ Schema（结构+校验+索引+时间戳）→ Model（CRUD）。
8. **populate 不是免费 JOIN**：本质二次查询，关联多时用 `$lookup` 或反范式。
9. **Repository 模式**：数据访问收拢到 Repository 类，上层 Service 调接口，底层可切 MySQL/Mongo。
10. **错误映射**：CastError→400、ValidationError→422、唯一冲突→409、NotFound→404、连接断→503。
11. **建模**：MySQL 重索引/外键/主键；MongoDB 优先嵌入式、必要时引用；时间戳与软删除是基础设施。
12. **AI 场景**：对话历史/向量元数据/知识库/推理日志多用 MongoDB；账户计费用 MySQL。

---

## 九、实战练习

### 练习 1：参数化查询与注入防御

在 `Code/mysql-pool.js` 基础上：

1. 新增 `users` 表的 `findByUsername(username)` 函数，用 `pool.execute` 参数化查询。
2. 构造一个恶意输入 `' OR '1'='1`，验证参数化查询能正确返回空结果（而非全表泄露）。
3. 故意写一版字符串拼接的版本（注释掉），对比说明为什么拼接会被注入。

**验收**：恶意输入返回 0 行；能口头解释占位符为何能防注入。

### 练习 2：转账事务与并发安全

扩展 `Code/mysql-transaction.js`：

1. 模拟“余额不足”场景，确认 `rollback` 后双方余额不变。
2. 新增 `concurrentTransfer()`：用 `Promise.all` 同时发起两笔从同一账户转出的转账，总额超过余额。观察是否会出现负数（提示：用 `SELECT ... FOR UPDATE` 行锁避免）。
3. 把 `transfer` 改成“先收款后扣款”顺序，思考顺序对死锁的影响。

**验收**：余额不足时正确回滚；并发场景下余额不会变负。

### 练习 3：Repository 模式 + Express CRUD

基于 `Code/server.js` 与 `Code/repository-pattern.js`：

1. 启动本地 MongoDB（`docker run -d --name mongo -p 27017:27017 mongo:7`），`npm install` 后 `npm start`。
2. 用 `curl`（见 server.js 顶部注释）完成：创建用户 → 创建文章 → 列表查询 → 详情查询（populate 作者）→ 更新 → 软删除。
3. 新增 `GET /api/articles/:id` 返回 404 的测试：请求一个不存在的 id，确认返回 `code: 404`。
4. 进阶：再实现一个 `MysqlArticleRepository`（参考 repository-pattern.js），通过环境变量 `REPO=mysql` 切换底层，验证 Controller 代码无需改动。

**验收**：完整跑通 CRUD；切换 Repository 实现时路由代码零改动；错误状态码正确。
