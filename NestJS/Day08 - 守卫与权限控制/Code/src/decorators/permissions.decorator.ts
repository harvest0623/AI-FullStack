import { SetMetadata } from '@nestjs/common';
import { PERMISSIONS_KEY } from '../common/reflector.constants';

/**
 * @Permissions('article:create', 'article:delete') —— 细粒度权限声明装饰器
 *
 * 作用：把路由要求的最小权限集合写入元数据，
 * 由 PermissionGuard 通过 Reflector 读取后做「权限交集」判断。
 *
 * 与 @Roles 的区别：
 *   角色是「粗粒度」的：admin / editor / visitor
 *   权限是「细粒度」的：article:create / article:delete / user:read
 *
 *   细粒度权限的好处：
 *   - 角色变更不影响代码（admin 能否删文章由权限决定，不由角色名决定）
 *   - 一个用户可以同时拥有「editor」角色和「article:delete」权限
 *   - 适合多业务线、多租户、权限常调整的复杂系统
 *
 * 命名约定（推荐）：
 *   资源:动作，如 article:create / article:read / user:delete
 *   动词统一用 create / read / update / delete / list / export
 *
 * 校验语义（见 permission.guard.ts）：
 *   「用户权限集合 ∩ 路由要求权限集合」非空 → 放行；否则 403。
 *   即「或」语义：拥有任一被允许的权限即可通过。
 *
 * 使用示例：
 *   @Post()
 *   @Permissions('article:create')
 *   create(@Body() body) { ... }
 *
 *   @Delete(':id')
 *   @Permissions('article:delete')
 *   remove(@Param('id') id: string) { ... }
 */
export const Permissions = (...permissions: string[]) =>
  SetMetadata(PERMISSIONS_KEY, permissions);
