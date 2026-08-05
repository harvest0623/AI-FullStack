import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { randomUUID } from 'crypto';

// ============================================================
// 请求 ID 注入中间件
// ------------------------------------------------------------
// 演示要点：
//   1. 修改 req 对象（这是 Express 中间件最典型的能力）
//   2. 优先复用客户端传入的 x-request-id，便于跨服务链路追踪
//   3. 把 requestId 回写到响应头，客户端可关联日志
//   4. 后续中间件、控制器通过 req.requestId 都能拿到（依赖类型扩展）
//
// 类型扩展见 src/common/express.d.ts，否则 TypeScript 会报错
// "Property 'requestId' does not exist on type 'Request'"
// ============================================================

@Injectable()
export class RequestIdMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction): void {
    // 优先使用客户端传入的请求 ID，便于分布式链路追踪
    const incoming = req.headers['x-request-id'];
    const requestId =
      (typeof incoming === 'string' && incoming) || randomUUID();

    // 把 requestId 挂到 req 上，后续中间件/控制器都能读到
    req.requestId = requestId;

    // 回写到响应头，方便客户端在日志中关联
    res.setHeader('x-request-id', requestId);

    next();
  }
}
