import type { Response } from 'express';
import type { ApiResponse } from '../types';

/**
 * 统一响应封装
 * --------------------------------------------------------
 * 把所有响应都收敛到统一结构 { code, message, data, errorType, requestId, timestamp }，
 * 前端可以根据 code 判断成功失败，根据 errorType 区分错误类型。
 *
 * 设计要点：
 * - sendSuccess 使用泛型 <T>，让 data 的类型在调用点被推断
 * - 所有响应都附带 timestamp（ISO 字符串），便于排查时序问题
 * - requestId 由日志中间件生成，贯穿响应链路
 */

/**
 * 成功响应
 * @example
 *   sendSuccess(res, article, '文章详情', req.requestId);
 *   sendSuccess(res, list, '查询成功');    // 不带 requestId 也可
 */
export function sendSuccess<T>(
  res: Response,
  data: T,
  message = 'OK',
  requestId?: string,
): Response {
  const body: ApiResponse<T> = {
    code: 0,
    message,
    data,
    requestId,
    timestamp: new Date().toISOString(),
  };
  return res.json(body);
}

/**
 * 错误响应
 * @example
 *   sendError(res, 404, '文章不存在', 'NOT_FOUND', undefined, req.requestId);
 */
export function sendError(
  res: Response,
  statusCode: number,
  message: string,
  errorType?: string,
  details?: unknown,
  requestId?: string,
): Response {
  const body: ApiResponse = {
    code: statusCode,
    message,
    data: details,
    errorType,
    requestId,
    timestamp: new Date().toISOString(),
  };
  return res.status(statusCode).json(body);
}
