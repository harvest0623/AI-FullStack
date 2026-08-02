import type { Request, Response, NextFunction, RequestHandler } from 'express';

/**
 * 异步错误包装器
 * --------------------------------------------------------
 * Express 4 不会自动捕获 async 中间件 / 路由处理函数抛出的 Promise rejection
 * （Express 5 已修复，但目前生产仍以 Express 4 为主）
 *
 * 用 asyncHandler 包一层后，rejection 会被 .catch(next) 转交给错误处理中间件，
 * 业务代码只需 throw new AppError(...)，无需手写 try/catch。
 *
 * 类型设计要点：
 * - asyncHandler 设计为泛型函数，让调用点的 Request 泛型参数（如 { id: string }）
 *   能被 TS 自动推断并透传到返回的 RequestHandler，保证 router.get(path, handler) 类型匹配
 * - 调用方仍需在处理函数内显式标注 req 的泛型类型（如 Request<{ id: string }>），
 *   以便精确约束 req.params / req.body / req.query
 */

type AsyncRequestHandler<
  P = any,
  ResBody = any,
  ReqBody = any,
  ReqQuery = any,
> = (
  req: Request<P, ResBody, ReqBody, ReqQuery>,
  res: Response<ResBody>,
  next: NextFunction,
) => Promise<unknown> | unknown;

export function asyncHandler<
  P = any,
  ResBody = any,
  ReqBody = any,
  ReqQuery = any,
>(
  fn: AsyncRequestHandler<P, ResBody, ReqBody, ReqQuery>,
): RequestHandler<P, ResBody, ReqBody, ReqQuery> {
  return (req, res, next) => {
    // Promise.resolve 把同步返回值也包装成 Promise，统一走 catch
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
