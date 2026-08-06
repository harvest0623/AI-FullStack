import { SetMetadata } from '@nestjs/common';
import { IS_PUBLIC_KEY } from '../common/reflector.constants';

/**
 * @Public() —— 公开路由白名单装饰器
 *
 * 作用：把路由标记为「不需要登录」，
 * 让全局 AuthGuard 在校验 token 之前先放行该路由。
 *
 * 为什么需要它：
 *   当 AuthGuard 注册成全局守卫（APP_GUARD）后，
 *   所有路由默认都要登录。但登录、注册、健康检查、
 *   文档预览等路由必须公开，否则会陷入「鸡生蛋」：
 *   没登录拿不到 token，没 token 又登录不了。
 *
 * 实现思路（见 auth.guard.ts）：
 *   1. 装饰器把 IS_PUBLIC_KEY = true 写入元数据
 *   2. AuthGuard canActivate 开头先 Reflector 读取
 *   3. 命中 @Public() 直接 return true，跳过 token 校验
 *
 * 注意：@Public() 只跳过「认证」，不跳过「授权」。
 * 如果该路由还标了 @Roles，理论上不会被触发，
 * 但仍建议保持职责单一，公开路由不要混用 @Roles。
 *
 * 使用示例：
 *   @Get('health')
 *   @Public()
 *   health() { return { ok: true }; }
 */
export const Public = () => SetMetadata(IS_PUBLIC_KEY, true);
