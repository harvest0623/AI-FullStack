import { ExceptionCode, DEFAULT_HTTP_STATUS } from './exception-code.constants';

/**
 * 业务异常基类
 *
 * 与 NestJS 内置 HttpException 的关键区别：
 *   - HttpException 直接对应 HTTP 语义，构造时已知 statusCode
 *   - BusinessException 携带业务错误码（errorCode），与 HTTP 解耦
 *   - 由 BusinessExceptionFilter 负责把业务码映射成 HTTP 状态码
 *
 * 为什么不继承 HttpException？
 *   这是有意为之——让 @Catch(HttpException) 不会误捕业务异常，
 *   业务异常只被 @Catch(BusinessException) 捕获，分工清晰。
 *   如果继承 HttpException，HttpExceptionFilter 会抢先捕获，
 *   业务码信息可能被默认响应格式吞掉。
 *
 * 使用方式：
 *   throw new BusinessException(ExceptionCode.INTERNAL_ERROR, '出了点问题');
 *   throw new BusinessException(ExceptionCode.BAD_REQUEST, '参数错误', {
 *     details: { field: 'email' },
 *   });
 */
export class BusinessException extends Error {
  /** 业务错误码，前端据此分支处理 */
  readonly errorCode: ExceptionCode;

  /** 映射到的 HTTP 状态码 */
  readonly httpStatus: number;

  /** 附带细节，如校验失败的字段错误数组 */
  readonly details?: unknown;

  constructor(
    errorCode: ExceptionCode,
    message?: string,
    options?: {
      /** 覆盖默认 HTTP 状态码 */
      httpStatus?: number;
      /** 附带细节 */
      details?: unknown;
      /** 原始错误，用于 cause 链 */
      cause?: unknown;
    },
  ) {
    // 默认 message 取错误码本身，保证有可读字符串
    super(message ?? errorCode, { cause: options?.cause });

    this.name = this.constructor.name;
    this.errorCode = errorCode;
    this.httpStatus =
      options?.httpStatus ?? DEFAULT_HTTP_STATUS[errorCode] ?? 500;
    this.details = options?.details;

    // 修复 TS 编译到 ES5 时继承 Error 的原型链问题
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
