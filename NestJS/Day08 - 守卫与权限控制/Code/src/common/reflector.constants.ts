/**
 * Reflector 元数据 Key 常量
 *
 * 在 NestJS 中，守卫读取控制器 / 方法上的自定义元数据，
 * 几乎都通过 Reflector + @SetMetadata 完成。
 * 元数据 Key 是字符串时极易写错（拼写、大小写），
 * 也无法获得类型提示。把 Key 收拢到一个常量文件集中管理，
 * 是生产项目里推荐的做法。
 *
 * 设计原则：
 * - Key 名与导出常量名保持一致，便于全局检索
 * - 用 const enum / as const 让 TS 把它当作字面量类型推导
 * - 装饰器与守卫必须引用同一份常量，杜绝魔法字符串
 */

/**
 * @Roles('admin') 装饰器写入的元数据 Key。
 * 值类型：string[]，表示该路由要求用户具备的任一角色。
 */
export const ROLES_KEY = 'roles';

/**
 * @Public() 装饰器写入的元数据 Key。
 * 值类型：true，标记该路由为公开路由，跳过全局 AuthGuard。
 */
export const IS_PUBLIC_KEY = 'isPublic';

/**
 * @Permissions('article:create') 装饰器写入的元数据 Key。
 * 值类型：string[]，表示该路由要求用户具备的任一细粒度权限。
 */
export const PERMISSIONS_KEY = 'permissions';

/**
 * 模拟用户身份，用于 AuthGuard 解析 token 后挂到 req.user。
 *
 * 真实项目里这份数据来自 JWT payload（Day14 会展开），
 * 这里为演示守卫与 RBAC 流程，临时用硬编码 token 映射。
 */
export interface AuthUser {
  id: number;
  username: string;
  /** RBAC0 中的「角色」层 */
  roles: string[];
  /** RBAC0 中的「权限」层，比角色更细粒度 */
  permissions: string[];
}
