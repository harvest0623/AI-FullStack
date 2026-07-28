/**
 * Day17 - Express 应用集成 mongoose，实现 /api/articles CRUD
 *
 * 架构分层：
 *   server.js（Controller/路由）→ ArticleRepository（DAO）→ mongoose → MongoDB
 *
 * 包含能力：
 *   - 启动时连接 MongoDB，连接失败打印友好错误并退出
 *   - GET    /api/articles          列表（分页 ?limit=&offset=）
 *   - GET    /api/articles/:id      详情（populate 作者）
 *   - POST   /api/articles          创建
 *   - PUT    /api/articles/:id      更新
 *   - DELETE /api/articles/:id      软删除
 *   - 统一错误处理：数据库错误 → 合适的 HTTP 状态码
 *   - /health 健康检查（含 DB 连接状态）
 *
 * ----------------------------------------------------------------------------
 * 环境准备：
 *   1) 启动本地 MongoDB（见 mongoose-crud.js 顶部注释），最快方式：
 *        docker run -d --name mongo -p 27017:27017 mongo:7
 *   2) npm install
 *   3) npm start   或   node server.js
 *
 * curl 测试命令（另开终端执行）：
 *
 *   # 健康检查
 *   curl http://localhost:3000/health
 *
 *   # 先创建一个用户（用 mongoose 的 User 模型；这里提供便捷接口）
 *   curl -X POST http://localhost:3000/api/users \
 *     -H "Content-Type: application/json" \
 *     -d "{\"username\":\"alice\",\"email\":\"alice@example.com\",\"role\":\"admin\"}"
 *
 *   # 创建文章（author 填上一步返回的 userId）
 *   curl -X POST http://localhost:3000/api/articles \
 *     -H "Content-Type: application/json" \
 *     -d "{\"title\":\"第一篇文章\",\"content\":\"hello\",\"author\":\"<userId>\",\"tags\":[\"demo\"]}"
 *
 *   # 文章列表
 *   curl "http://localhost:3000/api/articles?limit=10&offset=0"
 *
 *   # 文章详情
 *   curl http://localhost:3000/api/articles/<articleId>
 *
 *   # 更新文章
 *   curl -X PUT http://localhost:3000/api/articles/<articleId> \
 *     -H "Content-Type: application/json" \
 *     -d "{\"title\":\"新标题\",\"viewCount\":10}"
 *
 *   # 软删除文章
 *   curl -X DELETE http://localhost:3000/api/articles/<articleId>
 *
 * ----------------------------------------------------------------------------
 */

const express = require('express');
const { mongoose, User, Article } = require('./mongoose-model');
const { MongoArticleRepository } = require('./repository-pattern');

const app = express();
const PORT = process.env.PORT || 3000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/day17_demo';

// ---------------------------------------------------------------------------
// 全局中间件
// ---------------------------------------------------------------------------
app.use(express.json({ limit: '1mb' }));
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl}`);
  next();
});

// ---------------------------------------------------------------------------
// 数据访问层：单例 Repository
// ---------------------------------------------------------------------------
// 全局只创建一个 repo 实例（连接池由 mongoose 内部管理，天然单例）
const articleRepo = new MongoArticleRepository(Article);

// ---------------------------------------------------------------------------
// 工具：统一响应 + 错误转 HTTP 状态码
// ---------------------------------------------------------------------------
function ok(res, data, status = 200) {
  res.status(status).json({ code: 0, message: 'ok', data });
}

// 把数据库/业务错误映射到合适的 HTTP 状态码
//   - mongoose CastError（_id 格式错）→ 400
//   - ValidationError（字段校验失败）→ 422
//   - 自定义 NotFoundError → 404
//   - 其它未识别 → 500
function toHttpError(err) {
  if (err.name === 'CastError') return { status: 400, message: '参数格式错误' };
  if (err.name === 'ValidationError') return { status: 422, message: err.message };
  if (err.code === 'NOT_FOUND') return { status: 404, message: err.message };
  if (err.code === 11000) return { status: 409, message: '唯一约束冲突' };
  return { status: 500, message: '服务器内部错误' };
}

// 包装 async 路由，自动把 throw 的错误转给错误中间件
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// ---------------------------------------------------------------------------
// 健康检查（含 DB 连接状态）
// ---------------------------------------------------------------------------
app.get('/health', (req, res) => {
  // mongoose.connection.readyState：0=disconnected 1=connected 2=connecting 3=disconnecting
  const dbState = mongoose.connection.readyState;
  const dbStatus = ['disconnected', 'connected', 'connecting', 'disconnecting'][dbState] || 'unknown';
  res.json({
    status: dbState === 1 ? 'ok' : 'degraded',
    db: dbStatus,
    timestamp: new Date().toISOString(),
  });
});

// ---------------------------------------------------------------------------
// 用户接口（仅为方便测试文章的 author 而提供）
// ---------------------------------------------------------------------------
app.post(
  '/api/users',
  asyncHandler(async (req, res) => {
    const user = await User.create(req.body);
    ok(res, user, 201);
  })
);

// ---------------------------------------------------------------------------
// /api/articles CRUD
// ---------------------------------------------------------------------------
app.get(
  '/api/articles',
  asyncHandler(async (req, res) => {
    const limit = Math.min(Number(req.query.limit) || 20, 100); // 上限 100 防滥用
    const offset = Math.max(Number(req.query.offset) || 0, 0);
    const list = await articleRepo.findAll({ limit, offset });
    ok(res, { list, limit, offset });
  })
);

app.get(
  '/api/articles/:id',
  asyncHandler(async (req, res) => {
    const doc = await articleRepo.findById(req.params.id);
    if (!doc) {
      const err = new Error('文章不存在');
      err.code = 'NOT_FOUND';
      throw err;
    }
    ok(res, doc);
  })
);

app.post(
  '/api/articles',
  asyncHandler(async (req, res) => {
    const { title, content, author, tags } = req.body;
    if (!title || !author) {
      const err = new Error('title 与 author 必填');
      err.code = 'VALIDATION';
      err.name = 'ValidationError';
      throw err;
    }
    const created = await articleRepo.create({ title, content, author, tags });
    ok(res, created, 201);
  })
);

app.put(
  '/api/articles/:id',
  asyncHandler(async (req, res) => {
    const updated = await articleRepo.update(req.params.id, req.body);
    if (!updated) {
      const err = new Error('文章不存在');
      err.code = 'NOT_FOUND';
      throw err;
    }
    ok(res, updated);
  })
);

app.delete(
  '/api/articles/:id',
  asyncHandler(async (req, res) => {
    const deleted = await articleRepo.softDelete(req.params.id);
    if (!deleted) {
      const err = new Error('文章不存在');
      err.code = 'NOT_FOUND';
      throw err;
    }
    ok(res, { deleted: true });
  })
);

// ---------------------------------------------------------------------------
// 404 兜底
// ---------------------------------------------------------------------------
app.use((req, res) => {
  res.status(404).json({ code: 404, message: `路由不存在: ${req.method} ${req.originalUrl}`, data: null });
});

// ---------------------------------------------------------------------------
// 统一错误处理中间件（4 个参数，Express 据此识别为错误处理器）
// ---------------------------------------------------------------------------
app.use((err, req, res, next) => {
  const { status, message } = toHttpError(err);
  console.error('[ERROR]', err.name, '-', err.message);
  res.status(status).json({
    code: status,
    message,
    data: null,
  });
});

// ---------------------------------------------------------------------------
// 启动：先连数据库，再监听端口
// ---------------------------------------------------------------------------
// 关键：数据库连接失败时不要启动 HTTP 服务，避免“服务在但所有请求都 500”。
// mongoose 6+ 默认已启用 useNewUrlParser/useUnifiedTopology，无需显式传。
async function start() {
  try {
    mongoose.connection.on('disconnected', () => console.warn('[Mongo] 连接断开'));
    mongoose.connection.on('error', (err) => console.error('[Mongo] 错误:', err.message));

    await mongoose.connect(MONGO_URI, {
      maxPoolSize: 20,
      serverSelectionTimeoutMS: 5000,
    });
    console.log('[Mongo] 数据库连接成功 ✓');

    app.listen(PORT, () => {
      console.log(`[Server] 服务已启动: http://localhost:${PORT}`);
      console.log('[Server] 测试命令见本文件顶部注释');
    });
  } catch (err) {
    console.error('\n[启动失败] 无法连接 MongoDB，服务未启动。');
    console.error('  原因:', err.message);
    console.error('\n  快速启动 MongoDB：');
    console.error('    docker run -d --name mongo -p 27017:27017 mongo:7');
    console.error('  或修改环境变量 MONGO_URI 指向已存在的实例。');
    process.exit(1);
  }
}

start();
