// app.js - 组合应用: 自定义错误抛出与捕获 + morgan + winston + 请求 ID 贯穿
//
// 运行:
//   cd "Code"
//   npm install
//   npm start
//   访问 http://localhost:3000
//
// ===== curl 测试命令 =====
//
// 1) 正常请求 (200):
//    curl http://localhost:3000/
//
// 2) 触发 404 (路由不存在):
//    curl http://localhost:3000/no-such-route
//
// 3) 触发 404 业务错误 (资源不存在, 走 NotFoundError):
//    curl http://localhost:3000/api/users/0
//
// 4) 触发 400 参数校验错误 (name 为空):
//    curl -X POST http://localhost:3000/api/users ^
//      -H "Content-Type: application/json" ^
//      -d "{\"name\":\"\",\"email\":\"a\"}"
//
// 5) 触发 401 未授权 (缺少 Authorization 头):
//    curl http://localhost:3000/api/secret
//
// 6) 触发 500 同步错误 (程序 bug, 非 async):
//    curl http://localhost:3000/api/crash
//
// 7) 触发 500 异步错误 (Promise reject, 由 asyncHandler 捕获):
//    curl http://localhost:3000/api/async-crash
//
// 8) 自定义请求 ID 透传 (响应头会回显 X-Request-Id):
//    curl -i -H "X-Request-Id: my-trace-001" http://localhost:3000/

'use strict';

const express = require('express');
const morgan = require('morgan');

const logger = require('./logger');
const requestId = require('./request-id');
const asyncHandler = require('./async-handler');
const { notFoundHandler, errorHandler } = require('./error-middleware');
const {
  NotFoundError,
  ValidationError,
  UnauthorizedError
} = require('./custom-errors');

const app = express();

// ---- 基础中间件 ----
// 请求 ID 中间件放最前: 即便后续 express.json() 解析失败抛错, 该错误也能带上 requestId,
// 保证"全链路可追踪" —— 包括请求体解析阶段发生的错误.
app.use(requestId);

// 解析 JSON 请求体 (内部若解析失败会抛 SyntaxError, 会被错误中间件捕获为 400)
app.use(express.json());

// ---- morgan HTTP 请求日志, 输出流到 winston ----
// 自定义 token: 把 req.id 带进 morgan 日志行
morgan.token('requestId', (req) => req.id || '-');
const morganFormat =
  process.env.NODE_ENV === 'production'
    ? 'combined'
    : ':method :url :status :response-time ms - :requestId';

// morgan 的输出默认写 process.stdout, 这里改写到 winston, 统一走日志体系
const morganStream = {
  write: (line) => logger.info(line.trim(), { source: 'morgan' })
};
app.use(morgan(morganFormat, { stream: morganStream }));

// ---- 业务路由 ----

// 首页: 返回接口清单
app.get('/', (req, res) => {
  req.log.info('访问首页');
  res.json({
    name: 'Day14 错误处理与日志记录',
    endpoints: [
      'GET /',
      'GET /api/users/:id   (id=0 触发 404 业务错误)',
      'POST /api/users      (缺 name/email 触发 400)',
      'GET /api/secret      (无 Authorization 触发 401)',
      'GET /api/crash       (同步 500)',
      'GET /api/async-crash (异步 500)'
    ],
    requestId: req.id
  });
});

// 演示 NotFoundError: 主动抛出业务错误, 转交错误中间件
app.get('/api/users/:id', (req, res, next) => {
  const { id } = req.params;
  if (id === '0') {
    return next(new NotFoundError(`用户 ${id} 不存在`, { context: { userId: id } }));
  }
  res.json({ id, name: '示例用户' });
});

// 演示 ValidationError: 控制器层 try/catch + next(err) 转发
app.post('/api/users', (req, res, next) => {
  try {
    const { name, email } = req.body || {};
    if (!name || String(name).trim() === '') {
      throw new ValidationError('name 不能为空', { context: { field: 'name' } });
    }
    if (!email || !String(email).includes('@')) {
      throw new ValidationError('email 格式不正确', {
        context: { field: 'email', value: email }
      });
    }
    res.status(201).json({ id: Date.now(), name, email });
  } catch (err) {
    next(err);
  }
});

// 演示 UnauthorizedError
app.get('/api/secret', (req, res, next) => {
  const token = req.get('Authorization');
  if (!token) {
    return next(new UnauthorizedError('缺少 Authorization 头'));
  }
  res.json({ secret: '这是一个需要鉴权的资源' });
});

// 演示同步 500: 模拟一个意外的程序 bug (非操作型错误)
app.get('/api/crash', (req, res, next) => {
  try {
    const data = null;
    // 故意触发 TypeError: Cannot read properties of null (reading 'value')
    const value = data.value; // eslint-disable-line no-unused-vars
    res.json({ value });
  } catch (err) {
    // 标记为非操作型错误, 错误中间件将以 5xx 处理并触发 error 级日志
    err.statusCode = 500;
    err.code = 'INTERNAL_ERROR';
    err.isOperational = false;
    next(err);
  }
});

// 演示异步 500: Promise reject 由 asyncHandler 自动转 next(err)
// 这是 AI 接口编排(调用大模型/外部服务)的高频场景
app.get(
  '/api/async-crash',
  asyncHandler(async (req, res) => {
    // 模拟调用下游服务超时失败
    await new Promise((resolve, reject) => {
      setTimeout(() => reject(new Error('下游服务调用超时')), 100);
    });
    res.json({ ok: true }); // 不会执行到
  })
);

// ---- 错误处理 ----
// 顺序很关键: 404 必须在所有业务路由之后, errorHandler 必须最后注册
app.use(notFoundHandler);
app.use(errorHandler);

// ---- 进程级兜底 (请求之外的异常, 防止进程静默崩溃) ----
// 未处理的 Promise 拒绝: 记录日志. 生产环境建议优雅退出并由进程管理器重启.
process.on('unhandledRejection', (reason) => {
  logger.error('unhandledRejection', {
    reason: reason && reason.stack ? reason.stack : String(reason)
  });
});

// 未捕获的同步异常: 进程状态已不可靠, 记录后退出, 交给 PM2 / Docker / k8s 重启
process.on('uncaughtException', (err) => {
  logger.error('uncaughtException', { stack: err.stack });
  process.exit(1);
});

// ---- 启动 ----
const PORT = process.env.PORT || 3000;
if (require.main === module) {
  app.listen(PORT, () => {
    logger.info(`Server running at http://localhost:${PORT}`, {
      env: process.env.NODE_ENV || 'development'
    });
  });
}

module.exports = app;
