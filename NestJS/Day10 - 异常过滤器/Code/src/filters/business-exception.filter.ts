import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { BusinessException } from '../exceptions/business.exception';
import { ErrorResponseDto } from '../common/error-response.dto';

/**
 * 业务异常过滤器
 *
 * 只捕获自定义的 BusinessException 及其子类。
 * 职责：把业务错误码 + httpStatus 转换成统一响应格式。
 *
 * 与 HttpExceptionFilter 互不重叠：
 *   - BusinessException 不继承 HttpException（详见 business.exception.ts）
 *   - 所以 HttpExceptionFilter 的 @Catch(HttpException) 收不到它
 *   - 业务异常只走这条专门的处理路径，业务码不会丢失
 *
 * 典型触发：
 *   throw new ArticleNotFoundException(99);
 *   throw new ValidationException('邮箱已存在', { field: 'email' });
 */
@Catch(BusinessException)
export class BusinessExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(BusinessExceptionFilter.name);

  catch(exception: BusinessException, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const body: ErrorResponseDto = {
      code: exception.errorCode,
      message: exception.message,
      details: exception.details,
      timestamp: new Date().toISOString(),
      path: request.url,
    };

    // 业务异常通常是预期内的"软错误"，用 warn 而非 error
    this.logger.warn(
      `${request.method} ${request.url} -> ${exception.httpStatus} ${exception.errorCode}: ${exception.message}`,
    );

    response.status(exception.httpStatus).json(body);
  }
}
