import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { LoggerService } from '../common/logger.service';

// ============================================================
// 日志中间件（类形态，演示 DI 注入）
// ------------------------------------------------------------
// 与函数中间件的核心差异：
//   1. @Injectable 装饰器声明可被 DI 容器管理
//   2. 实现 NestMiddleware 接口的 use(req, res, next) 方法
//   3. 通过构造函数注入 LoggerService（函数中间件无法做到）
//
// 演示要点：
//   - 进入时打印 → + method + url + ip
//   - res.on('finish') 在响应结束时打印 ← + status + 耗时
//   - 这就是经典的「洋葱模型」外层中间件，next() 后还能拿到 res 的事件
// ============================================================

@Injectable()
export class LoggerMiddleware implements NestMiddleware {
  // 构造函数注入：与 Provider 注入方式完全一致
  constructor(private readonly logger: LoggerService) {}

  use(req: Request, res: Response, next: NextFunction): void {
    const { method, originalUrl, ip } = req;
    const startTime = Date.now();

    this.logger.log(`→ ${method} ${originalUrl} from ${ip}`, 'HTTP');

    // finish 事件在响应发送给客户端后触发，此时 res.statusCode 已确定
    res.on('finish', () => {
      const duration = Date.now() - startTime;
      const { statusCode } = res;
      this.logger.log(
        `← ${method} ${originalUrl} ${statusCode} ${duration}ms`,
        'HTTP',
      );
    });

    next();
  }
}
