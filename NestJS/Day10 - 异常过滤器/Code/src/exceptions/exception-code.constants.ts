/**
 * 业务错误码常量枚举
 *
 * 命名规范：<DOMAIN>_<RESULT>，全大写下划线分隔。
 *
 * 为什么需要业务码：
 *   HTTP 状态码数量有限（404 / 400 / 403 ...），无法区分同一状态码下的
 *   不同业务原因。前端需要更细粒度的码来判断如何提示、跳转、重试。
 *
 * 业务码与 HTTP 状态码的关系：
 *   - 一个业务码通常对应一个固定的 HTTP 状态码（见 DEFAULT_HTTP_STATUS）
 *   - 但同一个 HTTP 状态码可以对应多个业务码
 *     例：404 可以是 USER_NOT_FOUND / ARTICLE_NOT_FOUND / ORDER_NOT_FOUND
 *   - 这种"多对一"映射让前端处理更精细
 */
export enum ExceptionCode {
  // ---------- 通用错误 ----------
  /** 服务器内部错误，未预期的异常 */
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  /** 请求参数错误 */
  BAD_REQUEST = 'BAD_REQUEST',

  // ---------- 用户域 ----------
  /** 用户不存在 */
  USER_NOT_FOUND = 'USER_NOT_FOUND',
  /** 用户已存在（注册冲突） */
  USER_ALREADY_EXISTS = 'USER_ALREADY_EXISTS',

  // ---------- 文章域 ----------
  /** 文章不存在 */
  ARTICLE_NOT_FOUND = 'ARTICLE_NOT_FOUND',
  /** 文章被锁定，无法修改 */
  ARTICLE_LOCKED = 'ARTICLE_LOCKED',

  // ---------- 校验 ----------
  /** 业务校验失败（手动校验，区别于 DTO 自动校验） */
  VALIDATION_FAILED = 'VALIDATION_FAILED',

  // ---------- 权限 ----------
  /** 未登录或 token 失效 */
  UNAUTHORIZED = 'UNAUTHORIZED',
  /** 已登录但无权限 */
  FORBIDDEN = 'FORBIDDEN',
}

/**
 * 业务码到 HTTP 状态码的默认映射表。
 *
 * 自定义异常在构造时可以覆盖这个默认值——
 * 例如同一个 ARTICLE_LOCKED 在不同上下文下可能想返回 409 而非 423。
 */
export const DEFAULT_HTTP_STATUS: Record<ExceptionCode, number> = {
  [ExceptionCode.INTERNAL_ERROR]: 500,
  [ExceptionCode.BAD_REQUEST]: 400,

  [ExceptionCode.USER_NOT_FOUND]: 404,
  [ExceptionCode.USER_ALREADY_EXISTS]: 409,

  [ExceptionCode.ARTICLE_NOT_FOUND]: 404,
  [ExceptionCode.ARTICLE_LOCKED]: 423,

  [ExceptionCode.VALIDATION_FAILED]: 400,

  [ExceptionCode.UNAUTHORIZED]: 401,
  [ExceptionCode.FORBIDDEN]: 403,
};
