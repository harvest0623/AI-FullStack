/**
 * @Roles() 角色装饰器（复用 Day08 设计）
 *
 * 通过 @SetMetadata 把路由要求的最小角色集合写入元数据，
 * 由全局 RolesGuard 通过 Reflector 读取后做「角色交集」判断。
 *
 * 校验语义（或语义）：
 *   用户角色 ∩ 路由要求角色 ≠ ∅ → 放行；否则 403。
 *   即用户只要拥有任意一个被允许的角色即可通过。
 *
 * 使用示例：
 *   @Get('dashboard')
 *   @Roles('admin', 'editor')
 *   dashboard() { ... }
 */

import { SetMetadata } from '@nestjs/common';

/** 元数据 Key：@Roles 写入的角色集合（string[]） */
export const ROLES_KEY = 'roles';

export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);
