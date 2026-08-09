/**
 * 统一错误响应 DTO
 *
 * 所有异常过滤器最终都返回这种格式，让前端可以用同一套逻辑处理：
 * - code:       业务错误码（字符串常量），用于前端国际化与分支判断
 * - message:    面向用户的提示信息
 * - details:    额外细节（校验字段错误、引用 ID 等），可选
 * - timestamp:  ISO 时间字符串，便于排查
 * - path:       触发异常的请求路径
 *
 * 设计要点：code 与 HTTP 状态码解耦。
 * 例如用户不存在与文章不存在都返回 404，但 code 分别是
 * USER_NOT_FOUND 和 ARTICLE_NOT_FOUND，前端可据此跳转不同页面。
 */
export interface ErrorResponseDto {
  /** 业务错误码，字符串常量，详见 ExceptionCode 枚举 */
  code: string;

  /** 面向用户的错误提示，可直接展示在前端 */
  message: string;

  /** 附加细节，如校验失败的字段列表；可选 */
  details?: unknown;

  /** ISO 时间字符串，例如 2025-01-01T00:00:00.000Z */
  timestamp: string;

  /** 触发异常的请求路径，例如 /api/v1/articles/99 */
  path: string;
}
