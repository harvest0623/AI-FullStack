// async-handler.js - 异步错误包装器
// 配合 app.js 中的 async 路由使用
//
// 背景:
//   Express 4 不会自动捕获 async 函数内抛出的 rejection,
//   若路由 handler 是 async 且内部抛错/await 的 Promise reject,
//   该 rejection 会变成 unhandledRejection 而非进入错误中间件链.
//   两种正确姿势:
//     a) 手动 try/catch + next(err);
//     b) 用包装器自动把 rejected Promise 转成 next(err) —— 即本文件.

'use strict';

/**
 * asyncHandler: 包装 async 路由/中间件, 捕获其 rejected Promise 并交给 Express 错误链.
 *
 * 用法:
 *   const asyncHandler = require('./async-handler');
 *   router.get('/x', asyncHandler(async (req, res, next) => {
 *     const data = await someAsyncWork();
 *     res.json(data);
 *   }));
 *
 * 说明: 即便 handler 没用到 next, 签名仍保留三个参数, 与 Express 中间件一致.
 */
function asyncHandler(fn) {
  return (req, res, next) => {
    // Promise.resolve 保证无论 fn 返回 Promise 还是普通值都能统一处理
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

module.exports = asyncHandler;
