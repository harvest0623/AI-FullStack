import {
  CanActivate,
  ExecutionContext,
  Injectable,
  ForbiddenException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Request } from 'express';
import { PERMISSIONS_KEY } from '../common/reflector.constants';

/**
 * PermissionGuard —— 细粒度权限守卫（授权层 / 细粒度）
 *
 * 职责：基于「权限字符串」做授权决策。它和 RolesGuard 的分工：
 *   - RolesGuard       粗粒度：按角色名匹配（admin / editor）
 *   - PermissionGuard  细粒度：按权限字符串匹配（article:create / article:delete）
 *
 * 为什么需要细粒度：
 *   - 角色变更频繁时改代码成本高：原本 editor 不能删，业务说要让 editor 也能删，
 *     若用 @Roles('editor') 写死，要么把删接口改成 @Roles('admin','editor')，
 *     要么改数据库角色权限映射。
 *   - 而用 @Permissions('article:delete') 声明后，
 *     只需在权限表里给 editor 角色加上 article:delete 权限即可，代码不动。
 *
 * 配合 @Permissions('article:create') 装饰器使用：
 *   装饰器把要求写入元数据 PERMISSIONS_KEY，
 *   守卫读取后与 req.user.permissions 做交集。
 *
 * 校验语义（「或」语义）：
 *   路由要求 ['article:create']，用户拥有 ['article:read', 'article:create']
 *   → 交集非空 → 放行
 *   路由要求 ['article:delete']，用户只有 ['article:read']
 *   → 交集为空 → 403 Forbidden
 *
 * 与 RolesGuard 的执行顺序（见 app.module.ts 注册顺序）：
 *   全局 AuthGuard → 全局 RolesGuard → 全局 PermissionGuard → 控制器
 *   三层守卫职责单一，依次收窄，便于单元测试与替换。
 */
@Injectable()
export class PermissionGuard implements CanActivate {
  constructor(private readonly reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    // ① 读取路由要求的权限集合（方法级优先，类级兜底）
    const requiredPermissions = this.reflector.getAllAndOverride<string[]>(
      PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()],
    );

    // ② 没标 @Permissions 表示不限制权限，放行（角色层已校验过）
    if (!requiredPermissions || requiredPermissions.length === 0) {
      return true;
    }

    // ③ 从 req.user 拿到当前用户
    const request = context.switchToHttp().getRequest<Request>();
    const user = request.user;

    if (!user) {
      throw new ForbiddenException('用户未认证，无法进行权限校验');
    }

    // ④ 权限交集判断
    const hasPermission = user.permissions.some((perm) =>
      requiredPermissions.includes(perm),
    );

    if (!hasPermission) {
      throw new ForbiddenException(
        `缺少权限：${requiredPermissions.join(',')}，当前权限：${user.permissions.join(',')}`,
      );
    }

    return true;
  }
}
