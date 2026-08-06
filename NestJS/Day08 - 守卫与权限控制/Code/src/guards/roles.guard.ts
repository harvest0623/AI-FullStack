import {
  CanActivate,
  ExecutionContext,
  Injectable,
  ForbiddenException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Request } from 'express';
import { ROLES_KEY } from '../common/reflector.constants';

/**
 * RolesGuard —— 角色守卫（授权层 / 粗粒度）
 *
 * 职责：基于「角色」做授权决策。它和 AuthGuard 的分工：
 *   - AuthGuard   解决「认证」：你是谁？（把 user 挂到 req.user）
 *   - RolesGuard  解决「授权」：你能干什么？（user.roles 是否覆盖路由要求）
 *
 * 配合 @Roles('admin', 'editor') 装饰器使用：
 *   装饰器把要求写入元数据 ROLES_KEY，
 *   守卫运行时通过 Reflector 读出来与 req.user.roles 做交集。
 *
 * 校验语义（「或」语义）：
 *   路由要求 ['admin', 'editor']，用户拥有 ['editor']
 *   → 交集非空 → 放行
 *   路由要求 ['admin']，用户拥有 ['visitor']
 *   → 交集为空 → 403 Forbidden
 *
 * Reflector 读取元数据的三种写法对比：
 *   - get<T>(key, target)              单点读取
 *   - getAllAndOverride<T>(key, [t1, t2]) 方法级优先，覆盖类级
 *   - getAllAndMerge<T>(key, [t1, t2])   方法级与类级合并（去重）
 *
 * 这里用 getAllAndOverride：
 *   方法上标了 @Roles 就用方法的；
 *   方法没标则回退到类上的 @Roles；
 *   都没标 → requiredRoles = undefined，跳过校验（仅做认证）。
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

    // ② 没标 @Roles 表示该路由不限制角色，放行（认证已由 AuthGuard 兜底）
    if (!requiredRoles || requiredRoles.length === 0) {
      return true;
    }

    // ③ 从 req.user 拿到当前用户（AuthGuard 已挂载）
    const request = context.switchToHttp().getRequest<Request>();
    const user = request.user;

    // 理论上 AuthGuard 在前已保证 user 存在，这里做防御性校验
    if (!user) {
      throw new ForbiddenException('用户未认证，无法进行角色校验');
    }

    // ④ 角色交集判断：用户角色集合 ∩ 路由要求角色集合
    const hasRole = user.roles.some((role) => requiredRoles.includes(role));

    if (!hasRole) {
      throw new ForbiddenException(
        `当前角色 ${user.roles.join(',')} 无权访问，要求角色：${requiredRoles.join(',')}`,
      );
    }

    return true;
  }
}
