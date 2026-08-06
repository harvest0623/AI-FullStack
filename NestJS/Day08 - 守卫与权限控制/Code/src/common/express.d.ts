/**
 * Express.Request 类型扩展
 *
 * 在 NestJS 默认的 Express 平台中，
 * 控制器通过 @Req() 注入的 Request 对象就是 Express 的 Request。
 * 当我们需要在中间件、守卫、拦截器中给 req 注入额外字段时，
 * 就需要通过 declare module 扩展 Request 类型，
 * 否则 TypeScript 会报错 "Property 'user' does not exist on type 'Request'"。
 *
 * 本文件配合 Day08 的 AuthGuard 使用：
 * - AuthGuard 解析请求头 token 后，把用户信息挂到 req.user
 * - 后续 RolesGuard / PermissionGuard 从 req.user 读取角色与权限
 * - 控制器通过 @Req() 也能拿到强类型的 user 信息
 *
 * 使用方式：
 *   @Get('profile')
 *   @UseGuards(AuthGuard)
 *   getProfile(@Req() req: Request) {
 *     return req.user; // 这里访问 user 不会报类型错误
 *   }
 *
 * 注意：必须以 .d.ts 结尾，并且要被 tsconfig 包含进编译范围，
 * 否则类型扩展不会生效。NestJS 默认 src/**/*.ts 都会被编译。
 */

import { Request } from 'express';
import { AuthUser } from './reflector.constants';

declare module 'express' {
  interface Request {
    /**
     * 当前登录用户信息。
     * 在未登录或 @Public() 路由中该字段为 undefined。
     */
    user?: AuthUser;
  }
}
