// custom-errors.js - 自定义错误类体系
// 配合 app.js / error-middleware.js 使用
//
// 设计目标:
//   1. 业务代码只抛出"语义化"的自定义错误, 不在控制器里拼 statusCode / code 字符串.
//   2. 统一携带 statusCode(HTTP 状态码) 与 code(业务错误码), 便于错误中间件统一处理.
//   3. 携带 context 额外上下文(如哪个字段出错), 便于排查与回写 details.
//   4. isOperational 标记"操作型错误"(可预期) vs "程序 bug"(不可预期), 影响日志级别与告警策略.

'use strict';

/**
 * AppError - 所有业务自定义错误的基类
 * 继承自原生 Error, 额外携带:
 *  - statusCode:   HTTP 状态码 (4xx / 5xx)
 *  - code:         业务错误码 (字符串, 便于程序判断, 如 'USER_NOT_FOUND')
 *  - context:      额外上下文信息 (如 { field: 'email' })
 *  - isOperational: 是否为可预期的操作型错误 (默认 true)
 *                   false 表示程序 bug, 应触发告警, 与"用户操作失误"区分开
 */
class AppError extends Error {
  constructor(message, options = {}) {
    super(message);

    // 子类名自动作为 name, 便于日志中辨认
    this.name = this.constructor.name;

    this.statusCode = options.statusCode || 500;
    this.code = options.code || 'INTERNAL_ERROR';
    this.context = options.context || {};
    this.isOperational = options.isOperational !== false; // 默认 true

    // 让堆栈指向子类构造调用处, 而不是 AppError 自身
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

/**
 * NotFoundError - 资源未找到 (404)
 * 用于: 查询不到记录、路由不存在等
 */
class NotFoundError extends AppError {
  constructor(message = '资源未找到', options = {}) {
    super(message, {
      statusCode: 404,
      code: 'NOT_FOUND',
      ...options
    });
  }
}

/**
 * ValidationError - 参数校验失败 (400)
 * 用于: 请求体缺字段、格式不合法等
 */
class ValidationError extends AppError {
  constructor(message = '参数校验失败', options = {}) {
    super(message, {
      statusCode: 400,
      code: 'VALIDATION_ERROR',
      ...options
    });
  }
}

/**
 * UnauthorizedError - 未授权 (401)
 * 用于: 缺少 token、token 过期/无效, 用户需要先登录
 */
class UnauthorizedError extends AppError {
  constructor(message = '未授权，请先登录', options = {}) {
    super(message, {
      statusCode: 401,
      code: 'UNAUTHORIZED',
      ...options
    });
  }
}

/**
 * ForbiddenError - 禁止访问 (403)
 * 用于: 已登录但无权限访问该资源 (区别于 401 的"未登录")
 */
class ForbiddenError extends AppError {
  constructor(message = '禁止访问', options = {}) {
    super(message, {
      statusCode: 403,
      code: 'FORBIDDEN',
      ...options
    });
  }
}

module.exports = {
  AppError,
  NotFoundError,
  ValidationError,
  UnauthorizedError,
  ForbiddenError
};
