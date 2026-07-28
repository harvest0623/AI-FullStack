/**
 * Day17 - DAO / Repository 模式：封装数据访问层
 *
 * 核心思想：
 *   把所有“直接操作数据库”的代码收拢到 Repository 类中，
 *   上层 Service 只调用 repo.findAll() / repo.create() 等接口，
 *   完全不关心底层是 MySQL 还是 MongoDB。
 *
 * 分层结构（典型 Express 应用）：
 *   Router → Controller → Service → Repository → Database
 *     - Router：路由分发
 *     - Controller：解析 HTTP 请求/响应，调用 Service
 *     - Service：业务逻辑（校验、组合多个 repo、事务编排）
 *     - Repository：纯数据访问，每个实体一个类
 *
 * 好处：
 *   1. 切换数据库只改 Repository 实现，Service/Controller 不动
 *   2. 单元测试时可注入内存版 Repository，无需真实 DB
 *   3. 数据访问逻辑集中，避免 SQL/查询散落在各路由里
 *
 * 本文件同时提供 MongoArticleRepository（mongoose 实现）
 * 与 MysqlArticleRepository（mysql2 实现）两个实现，演示“可切换”思路。
 *
 * 环境准备：
 *   - MongoDB：见 mongoose-crud.js 顶部注释
 *   - MySQL：  见 mysql-pool.js 顶部注释（需建 articles 表）
 *
 * 运行：node repository-pattern.js  （默认跑 Mongo 实现）
 *       set REPO=mysql && node repository-pattern.js  （跑 MySQL 实现）
 */

const { mongoose, Article: ArticleModel } = require('./mongoose-model');
const mysql = require('mysql2/promise');

// ===========================================================================
// 接口约定（用 JSDoc 描述，TS 项目中会定义为 interface）
// ===========================================================================
/**
 * @typedef {Object} ArticleDTO
 * @property {string} title
 * @property {string} content
 * @property {string} authorId
 * @property {string[]} tags
 */

// ===========================================================================
// 实现 A：基于 mongoose 的 ArticleRepository
// ===========================================================================
class MongoArticleRepository {
  constructor(model = ArticleModel) {
    this.model = model;
  }

  async findAll({ limit = 20, offset = 0 } = {}) {
    // populate 关联作者，分页用 limit/offset
    return this.model
      .find()
      .populate('author', 'username role -_id')
      .sort({ createdAt: -1 })
      .skip(offset)
      .limit(limit)
      .lean(); // lean() 返回普通 JS 对象而非 Mongoose Document，更快
  }

  async findById(id) {
    return this.model.findById(id).populate('author', 'username role -_id').lean();
  }

  async create(data) {
    const doc = await this.model.create(data);
    return doc.toObject();
  }

  async update(id, data) {
    // new: true 返回更新后文档；runValidators 重跑 Schema 校验
    return this.model.findByIdAndUpdate(id, data, { new: true, runValidators: true }).lean();
  }

  async softDelete(id) {
    // 软删除：仅置标记，不真正移除
    return this.model.findByIdAndUpdate(id, { deleted: true }, { new: true }).lean();
  }

  async hardDelete(id) {
    const res = await this.model.deleteOne({ _id: id });
    return res.deletedCount > 0;
  }
}

// ===========================================================================
// 实现 B：基于 mysql2 的 ArticleRepository
// ===========================================================================
// 对比要点：
//   - 接口与 Mongo 实现完全一致（findAll/findById/create/update...）
//   - 内部用 prepared statement 防注入
//   - 关联查询用 LEFT JOIN（对应 Mongo 的 populate）
//   - 软删除用 deleted 字段，查询时 WHERE deleted = 0
class MysqlArticleRepository {
  constructor(pool) {
    this.pool = pool;
  }

  async _ensureTable() {
    await this.pool.execute(`
      CREATE TABLE IF NOT EXISTS articles (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        title      VARCHAR(200) NOT NULL,
        content    TEXT,
        author_id  INT NOT NULL,
        view_count INT NOT NULL DEFAULT 0,
        deleted    TINYINT(1) NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    `);
  }

  async findAll({ limit = 20, offset = 0 } = {}) {
    // LEFT JOIN 实现“关联查询”，对应 mongoose 的 populate
    const [rows] = await this.pool.execute(
      `SELECT a.id, a.title, a.content, a.view_count, a.created_at,
              u.username, u.role
       FROM articles a
       LEFT JOIN users u ON u.id = a.author_id
       WHERE a.deleted = 0
       ORDER BY a.created_at DESC
       LIMIT ? OFFSET ?`,
      [limit, offset]
    );
    return rows;
  }

  async findById(id) {
    const [rows] = await this.pool.execute(
      `SELECT a.*, u.username, u.role
       FROM articles a
       LEFT JOIN users u ON u.id = a.author_id
       WHERE a.id = ? AND a.deleted = 0`,
      [id]
    );
    return rows[0] || null;
  }

  async create(data) {
    const [res] = await this.pool.execute(
      'INSERT INTO articles (title, content, author_id) VALUES (?, ?, ?)',
      [data.title, data.content || '', data.authorId]
    );
    // MySQL 无 populate，需再查一次拿关联信息
    return this.findById(res.insertId);
  }

  async update(id, data) {
    // 动态拼接 SET 子句，字段名来自白名单（非用户输入），值用占位符
    const fields = [];
    const values = [];
    if (data.title !== undefined) { fields.push('title = ?'); values.push(data.title); }
    if (data.content !== undefined) { fields.push('content = ?'); values.push(data.content); }
    if (data.viewCount !== undefined) { fields.push('view_count = ?'); values.push(data.viewCount); }
    if (fields.length === 0) return this.findById(id);

    values.push(id);
    await this.pool.execute(`UPDATE articles SET ${fields.join(', ')} WHERE id = ?`, values);
    return this.findById(id);
  }

  async softDelete(id) {
    await this.pool.execute('UPDATE articles SET deleted = 1 WHERE id = ?', [id]);
    return this.findById(id);
  }

  async hardDelete(id) {
    const [res] = await this.pool.execute('DELETE FROM articles WHERE id = ?', [id]);
    return res.affectedRows > 0;
  }
}

// ===========================================================================
// 工厂函数：根据环境变量选择实现
// ===========================================================================
// 这是“可切换底层”的关键：上层只拿到一个 IArticleRepository 接口，
// 不关心是 Mongo 还是 MySQL。
function createArticleRepository() {
  if (process.env.REPO === 'mysql') {
    const pool = mysql.createPool({
      host: process.env.MYSQL_HOST || '127.0.0.1',
      user: process.env.MYSQL_USER || 'day17',
      password: process.env.MYSQL_PASSWORD || 'day17pass',
      database: process.env.MYSQL_DB || 'day17_demo',
      connectionLimit: 10,
    });
    return new MysqlArticleRepository(pool);
  }
  return new MongoArticleRepository();
}

// ===========================================================================
// 演示：用统一接口跑一遍 CRUD（默认 Mongo 实现）
// ===========================================================================
async function demo() {
  const repo = createArticleRepository();

  // 若是 MySQL 实现，先确保表存在
  if (repo instanceof MysqlArticleRepository) {
    await repo._ensureTable();
    console.log('[Repo] 使用 MySQL 实现');
  } else {
    // Mongo 实现需先连接
    await mongoose.connect(process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/day17_demo', {
      maxPoolSize: 20,
      serverSelectionTimeoutMS: 5000,
    });
    console.log('[Repo] 使用 Mongo 实现');
  }

  const created = await repo.create({ title: 'DAO 模式示例', content: '统一接口', authorId: '1' });
  console.log('[create]', created.title || created.id);

  const list = await repo.findAll({ limit: 5 });
  console.log('[findAll] 条数 =', list.length);

  console.log('\n[完成] repository-pattern.js 演示结束');
  await mongoose.disconnect();
}

demo().catch((err) => {
  console.error('[错误]', err.message);
  console.error('  若连接失败，请参考对应文件顶部注释准备 MySQL 或 MongoDB。');
  process.exit(1);
});

// 导出类与工厂，供 server.js 使用
module.exports = {
  MongoArticleRepository,
  MysqlArticleRepository,
  createArticleRepository,
};
