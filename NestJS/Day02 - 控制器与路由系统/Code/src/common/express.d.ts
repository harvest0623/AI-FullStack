/**
 * Express.Request 类型扩展
 *
 * 在 NestJS 默认的 Express 平台中，
 * 控制器通过 @Req() 注入的 Request 对象就是 Express 的 Request。
 * 当我们需要在中间件、守卫、拦截器中给 req 注入额外字段时，
 * 就需要通过 declare module 扩展 Request 类型，
 * 否则 TypeScript 会报错 "Property 'user' does not exist on type 'Request'"。
 *
 * 该文件为 Day14（认证与授权）做铺垫：
 * - 守卫（Guard）在通过 JWT 校验后，会把解析出的用户信息挂到 req.user
 * - 后续控制器通过 @Req() 即可拿到强类型的 user 信息
 *
 * 使用方式：
 *   @Get('profile')
 *   getProfile(@Req() req: Request) {
 *     return req.user; // 这里访问 user 不会报类型错误
 *   }
 *
 * 注意：必须以 .d.ts 结尾，并且要被 tsconfig 包含进编译范围，
 * 否则类型扩展不会生效。NestJS 默认 src/**/*.ts 都会被编译。
 */

import { Request } from 'express';

/**
 * 自定义用户信息载体
 *
 * 这里只定义最常用的字段，
 * 实际项目中可根据业务模型扩展。
 */
export interface RequestUser {
  id: number;
  username: string;
  email: string;
  /** 用户角色，用于 RBAC 权限控制 */
  roles: string[];
}

declare module 'express' {
  interface Request {
    /**
     * 当前登录用户信息。
     * 在未登录的路由中该字段为 undefined。
     */
    user?: RequestUser;
  }
}
