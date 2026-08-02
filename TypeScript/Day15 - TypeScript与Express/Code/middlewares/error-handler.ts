import type { ErrorRequestHandler } from 'express';
import { AppError } from '../types';
import { sendError } from '../utils/response';

/**
 * 全局错误处理中间件
 * --------------------------------------------------------
 * 类型签名：ErrorRequestHandler —— Express 专门为「错误处理中间件」定义的类型
 * 必须有 4 个参数 (err, req, res, next)，Express 通过参数数量识别它为错误处理器
 *
 * 处理策略：
 * 1. AppError（含子类）：业务错误，使用其自带的 statusCode / code / details
 * 2. 带 statusCode 属性的错误（如 express.json() 抛出的 SyntaxError）：按其状态码返回
 * 3. 其它 Error：未预期错误，统一 500，并打印完整堆栈便于排查
 *
 * 注意：错误处理中间件必须放在所有路由之后注册（见 app.ts）
 */
export const errorHandler: ErrorRequestHandler = (err, req, res, _next) => {
  // 1. 业务错误：自定义 AppError 体系
  if (err instanceof AppError) {
    return sendError(
      res,
      err.statusCode,
      err.message,
      err.code,
      err.details,
      req.requestId,
    );
  }

  // 2. Express 内置错误（如 body-parser 的 SyntaxError）携带 statusCode
  //    这类错误通常有暴露给客户端的价值（如 400 JSON 解析失败）
  if (typeof err === 'object' && 'statusCode' in err && typeof err.statusCode === 'number') {
    const status = err.statusCode;
    const isClientError = status >= 400 && status < 500;
    if (isClientError) {
      const message = err instanceof Error ? err.message : '请求格式错误';
      console.warn('[客户端错误]', message);
      return sendError(
        res,
        status,
        message,
        'BAD_REQUEST',
        undefined,
        req.requestId,
      );
    }
  }

  // 3. 未捕获的错误，打印堆栈用于排查，但不暴露给客户端
  console.error('[未捕获错误]', err);
  return sendError(
    res,
    500,
    '服务器内部错误',
    'INTERNAL_ERROR',
    undefined,
    req.requestId,
  );
};
