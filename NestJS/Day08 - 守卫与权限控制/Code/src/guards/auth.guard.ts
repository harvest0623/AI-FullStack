import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
  Logger,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Request } from 'express';
import { IS_PUBLIC_KEY, AuthUser } from '../common/reflector.constants';

/**
 * AuthGuard —— 基础鉴权守卫（认证层）
 *
 * 职责：验证请求方「是不是它声称的那个人」—— 也就是 authentication。
 * 注意是「认证」不是「授权」：
 *   - 认证：你是谁？（token 是否有效、能解出哪个用户）
 *   - 授权：你能做什么？（这个用户是否有权限访问该路由） ← 留给 RolesGuard / PermissionGuard
 *
 * 简化说明：
 *   真实项目里 token 是 JWT，需要 @nestjs/jwt + Passport 解签（Day14 展开）。
 *   本章为聚焦守卫流程，用「硬编码 token → 用户」映射模拟：
 *   - 请求头 Authorization: Bearer <token>
 *   - 在 mockUsers 表里查 token，命中则把用户挂到 req.user
 *   - 未带 token / token 无效 → 抛 401 Unauthorized
 *
 * 注册方式（见 app.module.ts）：
 *   通过 APP_GUARD 注册为全局守卫，所有路由默认都要登录。
 *   标了 @Public() 的路由在守卫入口直接 return true 放行。
 *
 * 执行顺序（同一请求内多守卫）：
 *   全局 AuthGuard → 全局 RolesGuard → 全局 PermissionGuard → 控制器方法
 */
@Injectable()
export class AuthGuard implements CanActivate {
  private readonly logger = new Logger(AuthGuard.name);

  /**
   * Mock 用户表：token → 用户身份
   * 真实项目里这份数据由数据库 + JWT payload 提供。
   * 这里设计三类用户覆盖 RBAC 全部场景：
   *   - admin：拥有所有权限
   *   - editor：能写能改，不能删
   *   - visitor：只能读
   */
  private readonly mockUsers: Record<string, AuthUser> = {
    'token-admin': {
      id: 1,
      username: 'admin',
      roles: ['admin'],
      permissions: [
        'article:read',
        'article:create',
        'article:update',
        'article:delete',
      ],
    },
    'token-editor': {
      id: 2,
      username: 'editor',
      roles: ['editor'],
      permissions: ['article:read', 'article:create', 'article:update'],
    },
    'token-visitor': {
      id: 3,
      username: 'visitor',
      roles: ['visitor'],
      permissions: ['article:read'],
    },
  };

  // Reflector 由 NestJS 注入，用于读取 @SetMetadata 写入的元数据
  constructor(private readonly reflector: Reflector) {}

  /**
   * canActivate 返回值决定请求是否放行：
   *   true  → 继续后续管道（pipe / interceptor / controller）
   *   false → 直接抛 403 Forbidden（这里我们用异常更精确）
   *   抛异常 → 异常过滤器接管，可以返回 401 / 403 / 4xx
   */
  async canActivate(context: ExecutionContext): Promise<boolean> {
    // ① 优先检查 @Public() 元数据：命中则跳过 token 校验
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(), // 方法级元数据优先
      context.getClass(), // 再回退到控制器级
    ]);
    if (isPublic) {
      return true;
    }

    // ② 从 ExecutionContext 取出底层 Express Request
    const request = context.switchToHttp().getRequest<Request>();

    // ③ 读取 Authorization 头并解析 Bearer token
    const authHeader = request.headers['authorization'] || '';
    const token = this.extractBearerToken(authHeader);

    if (!token) {
      // 没带 token 或格式不对 → 401 认证失败
      throw new UnauthorizedException('缺少有效的 Authorization 头');
    }

    // ④ token 命中 mock 用户表则挂到 req.user，供后续守卫与控制器使用
    const user = this.mockUsers[token];
    if (!user) {
      throw new UnauthorizedException('无效的 token');
    }

    // 挂载用户身份（express.d.ts 已扩展 Request.user 类型）
    request.user = user;

    this.logger.debug(
      `[认证通过] user=${user.username} roles=${user.roles.join(',')} path=${request.path}`,
    );

    return true;
  }

  /**
   * 解析 "Bearer <token>" 格式。
   * - 不带 Bearer 前缀视为非法格式
   * - 真实项目里 JWT 也用同样的 Bearer 协议
   */
  private extractBearerToken(authHeader: string): string | null {
    if (!authHeader) return null;
    const [scheme, token] = authHeader.split(' ');
    if (scheme !== 'Bearer' || !token) return null;
    return token;
  }
}
