import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';

// ============================================================
// 请求计时中间件
// ------------------------------------------------------------
// 演示要点：
//   1. 使用 process.hrtime.bigint() 高精度计时（纳秒）
//   2. res.on('finish') 在响应发送完毕后触发
//   3. 与 LoggerMiddleware 类似，但只关心耗时，便于做性能监控
//
// 为什么用 hrtime.bigint() 而不是 Date.now()：
//   - hrtime 不受系统时钟回拨影响
//   - 精度更高（纳秒级），适合短接口性能对比
//   - 转毫秒：Number(ns) / 1_000_000
// ============================================================

@Injectable()
export class TimerMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction): void {
    const startNs = process.hrtime.bigint();

    res.on('finish', () => {
      const durationNs = process.hrtime.bigint() - startNs;
      const durationMs = Number(durationNs) / 1_000_000;
      console.log(
        `[Timer] ${req.method} ${req.originalUrl} - ${durationMs.toFixed(2)}ms`,
      );
    });

    next();
  }
}
