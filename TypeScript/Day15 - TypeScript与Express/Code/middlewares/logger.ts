import type { RequestHandler } from 'express';
import { randomUUID } from 'crypto';

/**
 * 日志中间件
 * --------------------------------------------------------
 * 类型签名：RequestHandler —— Express 的标准中间件类型
 * 职责：
 * 1. 为每个请求生成 requestId，挂载到 req 上（类型来自 express.d.ts 扩展）
 * 2. 监听响应结束事件，记录方法 / 路径 / 状态码 / 耗时
 *
 * 由于 express.d.ts 中已通过 declaration merging 扩展了 Request，
 * 这里访问 req.requestId 不会报类型错误。
 */
export const logger: RequestHandler = (req, res, next) => {
  // 没有上游传入的 requestId 时主动生成
  req.requestId = (req.headers['x-request-id'] as string | undefined) ?? randomUUID();

  const start = Date.now();

  // finish 事件在 res.end 之后触发，此时 statusCode 已确定
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(
      `[${req.requestId}] ${req.method} ${req.originalUrl} -> ${res.statusCode} ${duration}ms`,
    );
  });

  next();
};
