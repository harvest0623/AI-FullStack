// error-middleware.js - Express 错误处理中间件
// 包含: notFoundHandler (404) + errorHandler (统一错误处理).
// 配合 custom-errors.js / logger.js 使用.

'use strict';

const logger = require('./logger');

/**
 * notFoundHandler - 404 中间件
 * 当所有业务路由都未匹配时, 会"落入"这里.
 * 我们构造一个带 statusCode/code 的错误, 转发给统一错误中间件, 保持响应格式一致.
 *
 * 必须放在所有业务路由之后、errorHandler 之前.
 */
function notFoundHandler(req, res, next) {
  const err = new Error(`未找到路由: ${req.method} ${req.originalUrl}`);
  err.statusCode = 404;
  err.code = 'NOT_FOUND';
  err.isOperational = true;
  next(err);
}

/**
 * errorHandler - 统一错误处理中间件
 *
 * 关键点:
 *  1. 必须是 (err, req, res, next) 四个参数, Express 靠"参数个数 === 4"识别为错误中间件.
 *     哪怕 next 没用到, 也不能省略, 否则会被当成普通中间件, 永远收不到 err.
 *  2. 区分 4xx 客户端错误 / 5xx 服务端错误, 采用不同日志级别:
 *       - 5xx 记 error (含完整堆栈与上下文), 应触发告警.
 *       - 4xx 记 warn (用户失误, 量大, 不必告警).
 *  3. 统一响应格式: { code, message, details, requestId, timestamp }.
 *  4. 敏感信息脱敏: 仅开发环境返回堆栈, 生产环境不返回堆栈.
 *  5. 优先用挂载在 req 上的子 logger (带 requestId), 保证错误日志可被链路追踪.
 *
 * 必须放在所有路由与 notFoundHandler 之后, 作为"最后"注册的中间件.
 */
// next 参数保留以保持四参数签名, Express 据此识别错误中间件
// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  // 兜底默认值 (应对原生 Error / 第三方抛错未带 statusCode 的情况)
  // 注意: Express/body-parser 等抛出的错误用 err.status (非 statusCode), 故两者都读
  const statusCode = err.statusCode || err.status || 500;
  const code = err.code || (statusCode >= 500 ? 'INTERNAL_ERROR' : 'BAD_REQUEST');
  const isOperational = err.isOperational !== false;
  const requestId = req.id || req.requestId || null;

  // 选择 logger: 优先用请求级子 logger (自动带 requestId), 否则用全局
  const log = req.log || logger;

  if (statusCode >= 500) {
    // 服务端错误: 完整记录堆栈与上下文
    log.error('服务器错误', {
      errName: err.name,
      message: err.message,
      stack: err.stack,
      path: req.originalUrl,
      method: req.method,
      isOperational
    });
  } else {
    // 客户端错误: warn 级别即可
    log.warn('客户端错误', {
      errName: err.name,
      message: err.message,
      code,
      statusCode,
      path: req.originalUrl,
      method: req.method
    });
  }

  // 统一响应体
  const body = {
    code,
    message: err.message || '服务器内部错误',
    details: err.context || undefined,
    requestId,
    timestamp: new Date().toISOString()
  };

  // 开发环境附加堆栈, 便于调试; 生产环境脱敏, 不泄露内部实现
  if (process.env.NODE_ENV !== 'production') {
    body.stack = err.stack;
  }

  res.status(statusCode).json(body);
}

module.exports = {
  notFoundHandler,
  errorHandler
};
