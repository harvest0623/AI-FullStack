/**
 * 异步错误包装器（Async Handler）
 *
 * 背景：Express 4 不会自动捕获 async/await 中抛出的 Promise rejection，
 *      如果路由函数里忘了 try/catch，rejection 会被吞掉，请求挂起直到超时。
 *
 * 作用：把异步路由处理函数包一层，把 rejected promise 自动转发给
 *      Express 的错误处理中间件（四参数中间件）。
 *
 * 用法：
 *   router.get('/', asyncHandler(async (req, res) => {
 *     const data = await someAsyncOp(); // 抛错会被自动捕获
 *     success(res, data);
 *   }));
 *
 * @param {Function} fn - 异步路由处理函数 (req, res, next) => Promise
 * @returns {Function} 包装后的同步处理函数
 */
function asyncHandler(fn) {
  return (req, res, next) => {
    // Promise.resolve 包一层，兼容 fn 返回非 Promise 的情况
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

module.exports = { asyncHandler };
