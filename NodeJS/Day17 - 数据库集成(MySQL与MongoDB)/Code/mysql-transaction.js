/**
 * Day17 - mysql2 事务演示：A 向 B 转账
 *
 * 事务核心：ACID（原子性/一致性/隔离性/持久性）
 *   转账场景中，“扣钱”和“加钱”必须同时成功或同时失败，
 *   否则可能出现“扣了 A 的钱却没到 B 账上”的资金丢失。
 *
 * 事务模板（必须背下来）：
 *   const conn = await pool.getConnection();   // 借一条独占连接
 *   try {
 *     await conn.beginTransaction();            // 开启事务
 *     ... 多条 SQL ...
 *     await conn.commit();                      // 全部成功 → 提交
 *   } catch (err) {
 *     await conn.rollback();                    // 任一失败 → 回滚
 *     throw err;
 *   } finally {
 *     conn.release();                           // 归还连接（务必释放，否则泄漏）
 *   }
 *
 * 关键点：
 *   - 事务内的多条 SQL 必须使用【同一个连接】conn，而非 pool。
 *     若用 pool.execute，每条语句可能拿到不同连接，事务边界失效！
 *   - 事务期间该连接被独占，其他请求无法复用，故事务要尽量短。
 *   - InnoDB 引擎才支持事务，MyISAM 不支持（建表时注意 ENGINE=InnoDB）。
 *
 * 环境准备：同 mysql-pool.js 顶部注释（需先建库建账号）。
 * 运行：node mysql-transaction.js
 */

const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host: process.env.MYSQL_HOST || '127.0.0.1',
  port: Number(process.env.MYSQL_PORT || 3306),
  user: process.env.MYSQL_USER || 'day17',
  password: process.env.MYSQL_PASSWORD || 'day17pass',
  database: process.env.MYSQL_DB || 'day17_demo',
  waitForConnections: true,
  connectionLimit: 10,
  charset: 'utf8mb4',
});

// ---------------------------------------------------------------------------
// 初始化：建表 + 准备两个账户
// ---------------------------------------------------------------------------
async function setup() {
  await pool.execute(`
    CREATE TABLE IF NOT EXISTS accounts (
      id      INT AUTO_INCREMENT PRIMARY KEY,
      name    VARCHAR(50) NOT NULL UNIQUE,
      balance INT         NOT NULL DEFAULT 0 CHECK (balance >= 0)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  `);
  await pool.execute('DELETE FROM accounts');
  await pool.execute('INSERT INTO accounts (name, balance) VALUES (?, ?), (?, ?)', [
    'alice', 1000,
    'bob', 1000,
  ]);
  const [rows] = await pool.execute('SELECT name, balance FROM accounts ORDER BY name');
  console.log('[初始] 余额：', rows.map((r) => `${r.name}=${r.balance}`).join(', '));
}

// ---------------------------------------------------------------------------
// 转账事务：from → to，金额 amount
// ---------------------------------------------------------------------------
async function transfer(from, to, amount) {
  // 1. 从池中借出一条【独占连接】，事务期间一直用它
  const conn = await pool.getConnection();
  try {
    // 2. 开启事务（底层：START TRANSACTION）
    await conn.beginTransaction();

    // 3. 锁定并查询付款方余额（FOR UPDATE 行锁，防止并发修改）
    const [senders] = await conn.execute(
      'SELECT balance FROM accounts WHERE name = ? FOR UPDATE',
      [from]
    );
    if (senders.length === 0) throw new Error(`账户不存在: ${from}`);
    if (senders[0].balance < amount) throw new Error(`余额不足: ${from} 仅剩 ${senders[0].balance}`);

    // 4. 扣款
    await conn.execute(
      'UPDATE accounts SET balance = balance - ? WHERE name = ?',
      [amount, from]
    );

    // 5. 收款
    await conn.execute(
      'UPDATE accounts SET balance = balance + ? WHERE name = ?',
      [amount, to]
    );

    // 6. 全部成功 → 提交（持久化到磁盘）
    await conn.commit();
    console.log(`[成功] ${from} → ${to} 转账 ${amount}`);
  } catch (err) {
    // 7. 任一步失败 → 回滚，前面已执行的 UPDATE 全部撤销
    await conn.rollback();
    console.log(`[回滚] ${from} → ${to} 转账失败：${err.message}`);
    throw err;
  } finally {
    // 8. 无论成功失败，都要释放连接，否则连接泄漏直至池满
    conn.release();
  }
}

// ---------------------------------------------------------------------------
// 查询最终余额
// ---------------------------------------------------------------------------
async function showBalances() {
  const [rows] = await pool.execute('SELECT name, balance FROM accounts ORDER BY name');
  console.log('[最终] 余额：', rows.map((r) => `${r.name}=${r.balance}`).join(', '));
  return rows;
}

// ---------------------------------------------------------------------------
// 主流程：演示一次成功转账 + 一次失败回滚
// ---------------------------------------------------------------------------
(async () => {
  try {
    await setup();

    // 场景一：正常转账 alice → bob 300
    await transfer('alice', 'bob', 300);
    await showBalances();
    // 预期：alice=700, bob=1300

    // 场景二：余额不足，触发回滚
    try {
      await transfer('bob', 'alice', 99999);
    } catch (e) {
      // 已在 transfer 内 rollback 并打印，这里吞掉避免中断流程
    }
    await showBalances();
    // 预期：余额不变，仍为 alice=700, bob=1300（事务回滚生效）

    console.log('\n[完成] mysql-transaction.js 演示结束');
  } catch (err) {
    console.error('[错误]', err.code || err.message);
    console.error('\n  若连接失败，请参考 mysql-pool.js 顶部注释完成环境准备。');
  } finally {
    await pool.end();
  }
})();
