/**
 * Day11 - express-augment.d.ts
 *
 * 模块扩增 Module Augmentation：扩展 Express.Request 添加 user 字段。
 *
 * 这是真实工程中最经典的「声明合并」场景：
 * 认证中间件会把用户信息挂到 req.user 上，但 @types/express 原生不含 user 字段。
 * 通过 declare module 'express-serve-static-core' 给 Request 接口追加成员，
 * 所有路由处理函数都能安全地访问 req.user。
 *
 * ──────────────────────────────────────────────────────────
 * 文件结构说明：
 * Part 1 是「基础类型模拟」，真实项目里这部分由 @types/express 提供，不需要自己写。
 * Part 2 是「模块扩增」，这是你在项目里实际要写的部分。
 * 两段 declare module 同名，触发声明合并，user 字段被追加到 Request 接口。
 * ──────────────────────────────────────────────────────────
 */

// ============================================================
// Part 1：模拟 @types/express 提供的基础类型（真实项目不需要自己写这段）
// ============================================================
//
// Express 的类型体系核心在 'express-serve-static-core' 模块。
// @types/express 通过 package.json 的 types 字段导出这些类型。
// 这里为了演示自包含，先声明一份最小化的基础类型。

declare module 'express-serve-static-core' {
  // Express 原生的 Request 接口（精简版，仅保留常用字段）
  interface Request {
    body: unknown;
    params: Record<string, string>;
    query: Record<string, string | string[]>;
    headers: Record<string, string | string[] | undefined>;
    method: string;
    url: string;
    path: string;
    ip: string;
    cookies: Record<string, string | undefined>;
  }

  // Express 原生的 Response 接口（精简版）
  interface Response {
    status(code: number): this;
    json(body: unknown): this;
    send(body: unknown): this;
    end(): this;
    setHeader(name: string, value: string): this;
    cookie(name: string, value: string, options?: Record<string, unknown>): this;
  }

  // NextFunction：Express 中间件链的下一个处理函数
  interface NextFunction {
    (err?: unknown): void;
  }

  // RequestHandler：标准的 Express 中间件 / 路由处理函数签名
  type RequestHandler = (
    req: Request,
    res: Response,
    next: NextFunction
  ) => void;
}


// ============================================================
// Part 2：模块扩增 Module Augmentation（项目中实际要写的部分）
// ============================================================
//
// 关键点：
// 1. 再次 declare module 'express-serve-static-core'，与 Part 1 同名
// 2. 内部声明同名 interface Request，触发「声明合并」
// 3. 合并后 Request 同时拥有原字段 + 新增的 user 字段
//
// 在真实项目中，你只需写 Part 2 这一段，Part 1 由 @types/express 提供。

declare module 'express-serve-static-core' {
  // 认证后挂载到 req.user 的用户信息类型
  interface AuthUser {
    id: string;
    name: string;
    email: string;
    roles: string[];
    loginAt: Date;
    avatarUrl?: string;
  }

  // 扩展 Request：追加 user 字段（可选，因为未认证路由的 req 没有 user）
  interface Request {
    user?: AuthUser;
  }

  // 也可以同时扩展 Response（如挂载统一的发送方法）
  interface Response {
    // 统一的成功响应格式
    sendSuccess<T>(data: T, message?: string): this;
    // 统一的错误响应格式
    sendError(code: number, message: string): this;
  }
}


// ============================================================
// 补充：扩展 express-session 的 Session（另一个常见场景）
// ============================================================
//
// 如果项目用了 express-session，req.session 默认类型不含业务字段。
// 同样用模块扩增的方式扩展：

declare module 'express-session' {
  // Session 是 express-session 提供的接口，这里通过声明合并追加字段
  interface Session {
    // 登录态：保存用户 ID
    userId?: string;
    // 验证码
    captcha?: string;
    // 上次访问时间
    lastVisitedAt?: number;
    // 购物车（未登录用户也能用）
    cart?: Array<{ productId: string; quantity: number }>;
  }
}
