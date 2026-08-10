import {
  CanActivate,
  ExecutionContext,
  Injectable,
  ForbiddenException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Request } from 'express';
import { ROLES_KEY } from './decorators/roles.decorator';

/**
 * RolesGuard —— 角色守卫（授权层 / 粗粒度，复用自 Day08）
 *
 * 与 Day08 的差异仅在于「req.user 的来源」：
 *   Day08：简化版 AuthGuard 用硬编码 token 映射挂载 user
 *   Day14：JwtStrategy 解析 JWT 后挂载 user（shape = JwtPayload）
 *
 * 守卫本身只关心 req.user.roles 是否覆盖路由要求，
 * 对 user 来源完全透明，因此可以原样复用。
 *
 * 工作流程：
 *   1. Reflector 读出 @Roles(...) 声明的角色集合（方法级优先，类级兜底）
 *   2. 没标 @Roles → 不做角色校验，放行
 *   3. 标了 → 用 user.roles 与 requiredRoles 做交集
 *   4. 交集为空 → 403 Forbidden
 *
 * 注意：本守卫依赖前置的 JwtAuthGuard / LocalAuthGuard 已经把 user 挂到 req.user。
 *       如果路由未挂任何认证守卫而仅挂了 RolesGuard，user 为 undefined 会抛 ForbiddenException。
 *       这种「认证缺失」语义应交由 JwtAuthGuard 抛 401，故此处仅防御性兜底。
 */
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private readonly reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    // ① 读取路由要求的角色集合（方法级优先，类级兜底）
    const requiredRoles = this.reflector.getAllAndOverride<string[]>(
      ROLES_KEY,
      [context.getHandler(), context.getClass()],
    );

    // ② 没标 @Roles 表示该路由不限制角色，放行
    if (!requiredRoles || requiredRoles.length === 0) {
      return true;
    }

    // ③ 从 req.user 拿到当前用户（JwtAuthGuard / LocalAuthGuard 已挂载）
    const request = context.switchToHttp().getRequest<Request>();
    const user = request.user;

    if (!user) {
      throw new ForbiddenException('用户未认证，无法进行角色校验');
    }

    // ④ 角色交集判断
    const hasRole = user.roles?.some((role: string) =>
      requiredRoles.includes(role),
    );

    if (!hasRole) {
      throw new ForbiddenException(
        `当前角色 [${(user.roles ?? []).join(',')}] 无权访问，要求角色：${requiredRoles.join(',')}`,
      );
    }

    return true;
  }
}
