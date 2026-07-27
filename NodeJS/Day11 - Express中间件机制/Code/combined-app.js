/**
 * combined-app.js
 * 组合以上所有中间件的完整 Express 应用
 * 运行: npm start  或  node combined-app.js  (端口 3005)
 *
 * 中间件加载顺序（非常重要）：
 *   CORS -> 请求体解析(含大小限制) -> 日志(耗时) -> 限流 -> 路由 -> 404 -> 错误处理
 *
 * 为什么是这个顺序？
 *   - CORS 必须最先，确保预检 OPTIONS 能被正确响应
 *   - 请求体解析在业务路由前，否则 req.body 为空
 *   - 日志在解析后，可记录请求体信息（此处仅记录方法和路径）
 *   - 限流在日志后，便于记录被拒请求
 *   - 路由居中
 *   - 404 兜底（未匹配路由）
 *   - 错误处理放最后，捕获所有 next(err)
 */

const express = require('express');
const app = express();

// ============ 1. CORS 中间件（必须最先）============
function corsMiddleware(options = {}) {
  const {
    origin = '*',
    methods = 'GET,POST,PUT,DELETE,OPTIONS',
    allowedHeaders = 'Content-Type,Authorization',
    maxAge = 86400
  } = options;
  return (req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Methods', methods);
    res.setHeader('Access-Control-Allow-Headers', allowedHeaders);
    res.setHeader('Access-Control-Max-Age', maxAge);
    // 预检请求直接返回
    if (req.method === 'OPTIONS') {
      return res.status(204).end();
    }
    next();
  };
}
app.use(corsMiddleware({ origin: 'http://localhost:8080' }));

// ============ 2. 请求体解析中间件 + 大小限制 ============
// 限制 JSON / urlencoded 请求体最大 10kb，防止超大请求拖垮服务
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ extended: true, limit: '10kb' }));

// ============ 3. 日志中间件（记录请求耗时）============
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(
      `[${new Date().toISOString()}] ${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms`
    );
  });
  next();
});

// ============ 4. 限流中间件（每 IP 每分钟 30 次）============
function rateLimitMiddleware(options = {}) {
  const { windowMs = 60 * 1000, max = 60, message = '请求过于频繁，请稍后再试' } = options;
  const store = new Map();
  const cleaner = setInterval(() => {
    const now = Date.now();
    for (const [ip, record] of store) {
      if (now > record.resetTime) store.delete(ip);
    }
  }, windowMs);
  cleaner.unref();

  return (req, res, next) => {
    const ip = req.ip || 'unknown';
    const now = Date.now();
    let record = store.get(ip);
    if (!record || now > record.resetTime) {
      record = { count: 0, resetTime: now + windowMs };
      store.set(ip, record);
    }
    record.count++;
    res.setHeader('X-RateLimit-Limit', max);
    res.setHeader('X-RateLimit-Remaining', Math.max(0, max - record.count));
    if (record.count > max) {
      const retryAfter = Math.ceil((record.resetTime - now) / 1000);
      res.setHeader('Retry-After', retryAfter);
      return res.status(429).json({ error: message, retryAfter });
    }
    next();
  };
}
app.use(rateLimitMiddleware({ windowMs: 60 * 1000, max: 30 }));

// ============ 5. asyncHandler 包装器 ============
// 捕获 async 路由中的 Promise reject，转发给错误处理中间件
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

// ============ 6. 鉴权中间件 ============
const VALID_TOKEN = 'Bearer my-secret-token-2024';
function authMiddleware(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader) {
    return res.status(401).json({ error: '未提供 Authorization token' });
  }
  if (authHeader !== VALID_TOKEN) {
    return res.status(401).json({ error: 'token 无效或已过期' });
  }
  req.user = { id: 1, name: 'AI全栈工程师', role: 'admin' };
  next();
}

// ============ 7. 公开路由 ============
app.get('/', (req, res) => {
  res.json({ message: 'Day11 Express 中间件组合实战 - 公开首页' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

// ============ 8. 受保护路由分组（挂载鉴权中间件）============
app.use('/api', authMiddleware);

app.get('/api/profile', (req, res) => {
  res.json({ user: req.user });
});

// 条件中间件示例：仅 /api/admin 开头路由额外校验角色
function requireAdmin(req, res, next) {
  if (req.user && req.user.role === 'admin') {
    return next();
  }
  return res.status(403).json({ error: '需要管理员权限' });
}
app.use('/api/admin', requireAdmin);

app.get('/api/admin/dashboard', (req, res) => {
  res.json({ message: '管理员面板', user: req.user });
});

// async 路由 - 使用 asyncHandler 包装
app.get('/api/async-task', asyncHandler(async (req, res) => {
  // 模拟异步操作（如查数据库、调用 AI 接口）
  await new Promise(resolve => setTimeout(resolve, 200));
  res.json({ user: req.user, task: '异步任务完成' });
}));

// 演示 async 错误（会被 asyncHandler 捕获 -> next(err) -> 错误处理中间件）
app.get('/api/fail', asyncHandler(async (req, res) => {
  await new Promise(resolve => setTimeout(resolve, 100));
  throw new Error('业务逻辑失败：模拟资源不存在');
}));

// POST 路由 - 受请求体大小限制保护
app.post('/api/data', asyncHandler(async (req, res) => {
  res.json({ received: req.body, user: req.user });
}));

// ============ 9. 404 兜底 ============
app.use((req, res, next) => {
  res.status(404).json({ error: '资源不存在', path: req.originalUrl });
});

// ============ 10. 错误处理中间件（必须放最后，4 个参数）============
app.use((err, req, res, next) => {
  // 请求体过大错误（express.json 抛出）
  if (err.type === 'entity.too.large') {
    return res.status(413).json({ error: '请求体过大，超过 10kb 限制' });
  }
  // JSON 解析错误
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ error: '请求体 JSON 格式错误' });
  }

  const status = err.status || 500;
  console.error(`[错误处理] ${status} - ${err.message}`);
  res.status(status).json({
    error: err.message,
    status: status,
    stack: process.env.NODE_ENV === 'production' ? undefined : err.stack
  });
});

// ============ 启动 ============
const PORT = 3005;
app.listen(PORT, () => {
  console.log(`\ncombined-app 服务启动: http://localhost:${PORT}\n`);
  console.log('========== curl 测试命令 ==========\n');

  console.log('# 1. 公开路由');
  console.log(`curl http://localhost:${PORT}/`);
  console.log(`curl http://localhost:${PORT}/health\n`);

  console.log('# 2. 鉴权路由 - 无 token（应返回 401）');
  console.log(`curl http://localhost:${PORT}/api/profile\n`);

  console.log('# 3. 鉴权路由 - 带 token（应返回 200）');
  console.log(`curl -H "Authorization: Bearer my-secret-token-2024" http://localhost:${PORT}/api/profile\n`);

  console.log('# 4. 条件中间件 - 管理员路由');
  console.log(`curl -H "Authorization: Bearer my-secret-token-2024" http://localhost:${PORT}/api/admin/dashboard\n`);

  console.log('# 5. async 路由（耗时约 200ms）');
  console.log(`curl -H "Authorization: Bearer my-secret-token-2024" http://localhost:${PORT}/api/async-task\n`);

  console.log('# 6. async 错误（应返回 500）');
  console.log(`curl -H "Authorization: Bearer my-secret-token-2024" http://localhost:${PORT}/api/fail\n`);

  console.log('# 7. POST + 请求体');
  console.log(`curl -X POST -H "Authorization: Bearer my-secret-token-2024" -H "Content-Type: application/json" -d '{"k":"v"}' http://localhost:${PORT}/api/data\n`);

  console.log('# 8. 请求体过大（>10kb，应返回 413）');
  console.log(`curl -X POST -H "Authorization: Bearer my-secret-token-2024" -H "Content-Type: application/json" -d "{\\"k\\":\\"$(python -c "print('x'*11000)")\\"}" http://localhost:${PORT}/api/data\n`);

  console.log('# 9. 404 兜底');
  console.log(`curl http://localhost:${PORT}/not-exist\n`);

  console.log('# 10. CORS 预检');
  console.log(`curl -X OPTIONS -H "Origin: http://localhost:8080" -H "Access-Control-Request-Method: POST" http://localhost:${PORT}/api/data -i\n`);

  console.log('# 11. 限流（连续请求 35 次，观察第 31 次起返回 429）');
  console.log(`1..35 | ForEach-Object { curl http://localhost:${PORT}/ -UseBasicParsing | Select-Object StatusCode }\n`);

  console.log('==================================\n');
});
