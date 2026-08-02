/**
 * Day15 - 扩展 Express 的 Request 类型
 * --------------------------------------------------------
 * Express 默认的 Request 类型只包含标准 HTTP 字段，
 * 真实业务中我们经常需要往 req 上挂载自定义字段（如 req.user、req.requestId）。
 *
 * 通过 TS 的「模块增强（declaration merging）」可以扩展 Request 接口，
 * 让所有中间件 / 路由处理函数都能类型安全地读取这些自定义字段。
 *
 * 关键点：扩展 'express-serve-static-core' 而非 'express' 模块，
 * 因为 Request 接口实际定义在前者，后者只是 re-export。
 */

import type { RequestUser } from './index';

declare module 'express-serve-static-core' {
  interface Request {
    /** 鉴权中间件挂载的当前用户；未鉴权时为 undefined */
    user?: RequestUser;
    /** 链路追踪 ID，由日志中间件生成，贯穿整条请求处理链 */
    requestId?: string;
  }
}
