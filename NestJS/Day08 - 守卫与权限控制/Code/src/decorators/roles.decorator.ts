import { SetMetadata } from '@nestjs/common';
import { ROLES_KEY } from '../common/reflector.constants';

/**
 * @Roles('admin', 'editor') —— 角色声明装饰器
 *
 * 作用：把路由要求的最小角色集合写入元数据，
 * 由全局 RolesGuard 通过 Reflector 读取后做「角色交集」判断。
 *
 * 设计要点：
 * - 内部就是 @SetMetadata(ROLES_KEY, roles) 的一层薄封装
 * - 接收可变参数，调用形式自然：@Roles('admin') 或 @Roles('admin', 'editor')
 * - 不传角色 = 不做角色校验（仍然受 AuthGuard 约束）
 *
 * 校验语义（见 roles.guard.ts）：
 *   「用户角色集合 ∩ 路由要求角色集合」非空 → 放行；否则 403。
 *   也就是「或」语义：用户拥有任意一个被允许的角色即可。
 *
 * 使用示例：
 *   @Get('list')
 *   @Roles('admin', 'editor')
 *   findAll() { ... }
 */
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);
