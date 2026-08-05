import {
  Injectable,
  NestMiddleware,
  UnauthorizedException,
} from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { LoggerService } from '../common/logger.service';

// ============================================================
// 鉴权中间件：函数形态 vs 类形态对比
// ------------------------------------------------------------
// 函数中间件：
//   - 轻量、零依赖，适合纯逻辑判断
//   - 无法访问 DI 容器
//   - 错误处理需手动 res.status().json() 返回
//
// 类中间件：
//   - 可注入 Service（DB、Cache、Logger 等）
//   - 抛出异常会被 NestJS 异常过滤器统一处理
//   - 适合需要查询数据库或调用业务服务的复杂鉴权
// ============================================================

// ─── 函数中间件 1：基础登录态校验 ───────────────────────────
// 通过请求头 x-auth-token 校验，未通过则直接 res.status(401).json()
export function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const token = req.headers['x-auth-token'];
  if (!token) {
    res.status(401).json({ message: 'Unauthorized: token missing' });
    return; // 不调用 next()，请求链终止
  }
  if (token !== 'secret-token') {
    res.status(401).json({ message: 'Unauthorized: invalid token' });
    return;
  }
  next();
}

// ─── 函数中间件 2：管理员角色校验 ───────────────────────────
// 通过请求头 x-user-role 校验，仅 admin 可访问
export function adminAuthMiddleware(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const role = req.headers['x-user-role'];
  if (role !== 'admin') {
    res.status(403).json({ message: 'Forbidden: admin role required' });
    return;
  }
  next();
}

// ─── 类中间件：与函数中间件等价的逻辑，但可注入 LoggerService ───
@Injectable()
export class AuthMiddleware implements NestMiddleware {
  constructor(private readonly logger: LoggerService) {}

  use(req: Request, res: Response, next: NextFunction): void {
    const token = req.headers['x-auth-token'];
    if (!token) {
      this.logger.warn(`Auth failed (no token) from ${req.ip}`, 'AUTH');
      // 类中间件抛异常会被全局 ExceptionFilter 捕获并返回标准错误响应
      throw new UnauthorizedException('Token missing');
    }
    if (token !== 'secret-token') {
      this.logger.warn(`Auth failed (invalid token) from ${req.ip}`, 'AUTH');
      throw new UnauthorizedException('Invalid token');
    }
    this.logger.log(
      `Auth passed for ${req.method} ${req.originalUrl}`,
      'AUTH',
    );
    next();
  }
}
