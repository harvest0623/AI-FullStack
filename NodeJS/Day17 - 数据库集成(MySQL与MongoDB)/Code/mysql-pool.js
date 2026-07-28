/**
 * Day17 - mysql2 连接池与 Promise 风格查询示例
 *
 * 演示内容：
 *   1. createPool 创建连接池（connectionLimit / host / user / password / database）
 *   2. pool.execute（prepared statement，防 SQL 注入）vs pool.query（普通查询）的区别
 *   3. SELECT / INSERT / UPDATE / DELETE 参数化查询
 *   4. SQL 注入防御演示（错误写法 vs 正确写法）
 *
 * ----------------------------------------------------------------------------
 * 环境准备（运行前必读）：
 *
 * 1) 本机需安装并启动 MySQL 服务（5.7+ 或 8.x 均可）。
 *    - Windows: 可用 MySQL Installer 或 scoop install mysql
 *    - macOS:   brew install mysql && brew services start mysql
 *    - Linux:   sudo apt install mysql-server && sudo systemctl start mysql
 *
 * 2) 建库建账号（用 root 登录 mysql 后执行）：
 *
 *    CREATE DATABASE day17_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
 *    CREATE USER 'day17'@'%' IDENTIFIED BY 'day17pass';
 *    GRANT ALL PRIVILEGES ON day17_demo.* TO 'day17'@'%';
 *    FLUSH PRIVILEGES;
 *
 * 3) 若你的账号/密码/端口不同，请修改下方 pool 配置或用环境变量覆盖：
 *    set MYSQL_HOST=127.0.0.1
 *    set MYSQL_USER=day17
 *    set MYSQL_PASSWORD=day17pass
 *    set MYSQL_DB=day17_demo
 *
 * 4) 安装依赖： npm install
 * 5) 运行：     node mysql-pool.js
 *
 * 若本机没有 MySQL，运行会打印友好错误并退出，不会崩溃。
 * ----------------------------------------------------------------------------
 */

const mysql = require('mysql2/promise'); // 注意：引入 promise 版本，而非回调版 mysql2

// ---------------------------------------------------------------------------
// 1. 创建连接池
// ---------------------------------------------------------------------------
// 为什么用连接池？
//   每次 createConnection 都要建立 TCP 三次握手 + MySQL 握手鉴权，开销 10~50ms。
//   连接池预先建立 N 条连接并复用，请求到来时借出、用完归还，避免反复建连。
//   connectionLimit 是“最大空闲+在用连接数”，建议根据数据库 max_connections 与
//   应用并发量调整，常见 10~20。Node 单进程不宜过大，避免压垮 DB。
const pool = mysql.createPool({
  host: process.env.MYSQL_HOST || '127.0.0.1',
  port: Number(process.env.MYSQL_PORT || 3306),
  user: process.env.MYSQL_USER || 'day17',
  password: process.env.MYSQL_PASSWORD || 'day17pass',
  database: process.env.MYSQL_DB || 'day17_demo',
  waitForConnections: true, // 池满时排队等待，而非立即报错
  connectionLimit: 10, // 最大连接数
  queueLimit: 0, // 等待队列无上限（0 = 不限）
  charset: 'utf8mb4',
  // 命名参数占位符风格，默认 unnamed(?)
  // 也可用 namedPlaceholders: true 启用 :name 风格
});

// ---------------------------------------------------------------------------
// 友好的连接失败处理：启动时做一次 ping，失败则给出明确提示
// ---------------------------------------------------------------------------
async function ensureConnection() {
  try {
    const conn = await pool.getConnection();
    await conn.ping();
    conn.release();
    console.log('[MySQL] 连接池就绪 ✓');
  } catch (err) {
    console.error('[MySQL] 连接失败，请检查 MySQL 服务是否启动、账号密码是否正确。');
    console.error('  错误码:', err.code);
    console.error('  原始信息:', err.message);
    console.error('\n  提示：参考本文件顶部注释完成“建库建账号”步骤。');
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// 2. 建表（DDL 用 pool.execute，无外部输入，安全）
// ---------------------------------------------------------------------------
async function initSchema() {
  const ddl = `
    CREATE TABLE IF NOT EXISTS users (
      id         INT AUTO_INCREMENT PRIMARY KEY,
      username   VARCHAR(50)  NOT NULL UNIQUE,
      email      VARCHAR(120) NOT NULL,
      balance    INT          NOT NULL DEFAULT 0,
      created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  `;
  await pool.execute(ddl);
  console.log('[Schema] 表 users 已就绪');
}

// ---------------------------------------------------------------------------
// 3. INSERT / SELECT / UPDATE / DELETE 参数化查询
// ---------------------------------------------------------------------------
async function crudDemo() {
  // 清空旧数据，便于重复运行
  await pool.execute('DELETE FROM users');

  // ---- INSERT：? 占位符按顺序绑定参数（prepared statement）----
  // pool.execute 会先 PREPARE 再 EXECUTE，参数被当作“值”而非 SQL 文本，
  // 因此天然防注入，不需要手动转义。
  await pool.execute(
    'INSERT INTO users (username, email, balance) VALUES (?, ?, ?)',
    ['alice', 'alice@example.com', 1000]
  );
  await pool.execute(
    'INSERT INTO users (username, email, balance) VALUES (?, ?, ?)',
    ['bob', 'bob@example.com', 500]
  );

  // ---- SELECT：返回 [rows, fields]，Promise 风格直接 await ----
  const [rows] = await pool.execute('SELECT id, username, email, balance FROM users WHERE username = ?', ['alice']);
  console.log('[SELECT] alice =', rows[0]);

  // ---- UPDATE ----
  await pool.execute('UPDATE users SET balance = balance + ? WHERE username = ?', [100, 'alice']);
  const [updated] = await pool.execute('SELECT balance FROM users WHERE username = ?', ['alice']);
  console.log('[UPDATE] alice 新余额 =', updated[0].balance);

  // ---- DELETE ----
  await pool.execute('DELETE FROM users WHERE username = ?', ['bob']);
  const [left] = await pool.execute('SELECT COUNT(*) AS n FROM users');
  console.log('[DELETE] 剩余用户数 =', left[0].n);
}

// ---------------------------------------------------------------------------
// 4. pool.execute vs pool.query 区别
// ---------------------------------------------------------------------------
async function executeVsQuery() {
  // pool.execute：使用 prepared statement
  //   - 服务端先 PREPARE 模板，再 EXECUTE 传参
  //   - 参数绝不参与 SQL 解析，防注入
  //   - 同一模板可缓存执行计划，多次调用更高效
  const [r1] = await pool.execute('SELECT 1 + ? AS sum', [2]);
  console.log('[execute] 1 + 2 =', r1[0].sum);

  // pool.query：直接发送整条 SQL（参数会被转义后拼接）
  //   - 无 prepared 开销，单次调用略快
  //   - 但参数是“转义后字符串拼接”，安全性依赖 driver 实现
  //   - 适合 DDL、固定 SQL、或一次性大查询
  const [r2] = await pool.query('SELECT 1 + ? AS sum', [2]);
  console.log('[query] 1 + 2 =', r2[0].sum);

  // 经验法则：凡含用户输入的 DML，一律用 execute；DDL/固定 SQL 用 query 即可。
}

// ---------------------------------------------------------------------------
// 5. SQL 注入防御演示（仅作反面教材，运行时不会真正执行危险写法）
// ---------------------------------------------------------------------------
async function injectionDefense() {
  const evilInput = "alice'; DROP TABLE users; --";

  // ❌ 错误写法：字符串拼接 —— 千万别这么干！
  // const bad = `SELECT * FROM users WHERE username = '${evilInput}'`;
  // 拼接后变成： SELECT * FROM users WHERE username = 'alice'; DROP TABLE users; --'
  // 后果：整张表被删。永远不要把用户输入拼进 SQL。

  // ✅ 正确写法：参数化查询
  const [safe] = await pool.execute(
    'SELECT * FROM users WHERE username = ?',
    [evilInput] // 整个字符串被当作一个“用户名值”，不会被执行为多条 SQL
  );
  console.log('[防注入] 查询恶意输入返回行数 =', safe.length, '（应为 0，因为没人叫这个名字）');
}

// ---------------------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------------------
(async () => {
  await ensureConnection();
  await initSchema();
  await crudDemo();
  await executeVsQuery();
  await injectionDefense();
  console.log('\n[完成] mysql-pool.js 演示结束');
  await pool.end(); // 关闭池，释放所有连接，进程退出
})().catch((err) => {
  console.error('[未捕获错误]', err);
  process.exit(1);
});
