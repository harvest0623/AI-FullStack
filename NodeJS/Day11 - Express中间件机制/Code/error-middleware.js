/**
 * error-middleware.js
 * 错误处理中间件：演示同步错误与 async 错误，含 asyncHandler 包装器
 * 运行: node error-middleware.js  (端口 3002)
 *
 * 核心知识点：
 *   - Express 4 不会自动捕获 async 函数中的 Promise reject
 *   - 同步抛出的错误会被自动捕获并进入错误处理中间件
 *   - async 错误必须手动 next(err)，或用 asyncHandler 包装器
 *   - Express 5 已自动捕获 async 错误
 */

const express = require('express');
const app = express();

// ============ asyncHandler 包装器 ============
// 作用：捕获 async 路由函数中的 Promise reject，转发给错误处理中间件
// Express 4 必须用这个，否则 async 错误会变成 UnhandledPromiseRejection
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

// ============ 路由演示 ============

// 1. 正常路由
app.get('/ok', (req, res) => {
  res.json({ message: '一切正常' });
});

// 2. 同步错误：直接 throw，Express 会自动捕获并跳到错误处理中间件
app.get('/sync-error', (req, res) => {
  throw new Error('同步抛出的错误 - Express 自动捕获');
});

// 3. 手动 next(err)：可以附带自定义状态码
app.get('/manual-error', (req, res, next) => {
  const err = new Error('手动通过 next(err) 触发的错误');
  err.status = 418; // I'm a teapot
  next(err);
});

// 4. 【反面教材】未包装的 async 错误
//    Express 4 不会捕获这个错误！会导致 UnhandledPromiseRejection
//    注意：实际项目绝不要这样写，这里仅为对比演示
app.get('/async-error-bad', async (req, res, next) => {
  await new Promise(resolve => setTimeout(resolve, 50));
  throw new Error('async 错误 - 未包装，Express 4 无法捕获（反面教材）');
});

// 5. 【正确做法】用 asyncHandler 包装的 async 错误
app.get('/async-error-good', asyncHandler(async (req, res, next) => {
  await new Promise(resolve => setTimeout(resolve, 50));
  throw new Error('async 错误 - 已用 asyncHandler 包装，将被正确捕获');
}));

// 6. 异步操作中手动 next(err)
app.get('/async-next-error', asyncHandler(async (req, res, next) => {
  await new Promise(resolve => setTimeout(resolve, 50));
  const err = new Error('业务校验失败：参数不合法');
  err.status = 400;
  next(err);
}));

// ============ 404 处理（放在错误处理之前）============
app.use((req, res, next) => {
  res.status(404).json({ error: '资源不存在', path: req.originalUrl });
});

// ============ 错误处理中间件 ============
// 必须有 4 个参数 (err, req, res, next)，Express 据此识别为错误处理器
// 必须放在所有路由 / 中间件之后
app.use((err, req, res, next) => {
  const status = err.status || 500;
  console.error(`[错误处理中间件] ${status} - ${err.message}`);

  res.status(status).json({
    error: err.message,
    status: status,
    // 生产环境不返回堆栈，避免信息泄露
    stack: process.env.NODE_ENV === 'production' ? undefined : err.stack
  });

  // 注意：如果 next(err) 之后还有需要处理的逻辑，可以继续调用 next()
  // 但通常错误处理是终点，不再调用 next
});

// ============ 全局未捕获 Promise 异常兜底（仅作演示）============
process.on('unhandledRejection', (reason) => {
  console.error('[全局未捕获的 Promise Reject]', reason);
});

// ============ 启动 ============
app.listen(3002, () => {
  console.log('error-middleware 服务启动: http://localhost:3002');
  console.log('\n测试命令:');
  console.log('  # 正常');
  console.log('  curl http://localhost:3002/ok');
  console.log('  # 同步错误（自动捕获，返回 500）');
  console.log('  curl http://localhost:3002/sync-error');
  console.log('  # 手动 next(err)（返回 418）');
  console.log('  curl http://localhost:3002/manual-error');
  console.log('  # 正确包装的 async 错误（返回 500）');
  console.log('  curl http://localhost:3002/async-error-good');
  console.log('  # async 中手动 next(err)（返回 400）');
  console.log('  curl http://localhost:3002/async-next-error');
  console.log('  # 404');
  console.log('  curl http://localhost:3002/not-exist');
});
