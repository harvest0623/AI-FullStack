/**
 * Express.Request 类型扩展
 *
 * Day14 的认证链路里：
 *   - LocalStrategy 验证完账号密码后把 user 挂到 req.user
 *   - JwtStrategy 解析 token 后把 user 挂到 req.user
 *   - JwtAuthGuard / RolesGuard / @CurrentUser() 都从 req.user 读取身份
 *
 * 由于 Express 内置的 Request 类型并不包含 user 字段，
 * 必须通过 `declare module 'express'` 进行声明合并，
 * 否则 TypeScript 编译期会报 "Property 'user' does not exist on type 'Request'"。
 *
 * 文件名必须以 .d.ts 结尾，NestJS 默认会把 src/**/*.ts 纳入编译范围，
 * 因此无需在 tsconfig 显式 include 即可生效。
 */

import { Request } from 'express';
import { JwtPayload } from '../auth/strategies/jwt.strategy';

declare module 'express' {
  interface Request {
    /**
     * 当前登录用户身份。
     * 在登录前的公开路由（/auth/register、/auth/login）中为 undefined。
     * 经 LocalStrategy / JwtStrategy 校验通过后被挂载。
     */
    user?: JwtPayload;
  }
}
