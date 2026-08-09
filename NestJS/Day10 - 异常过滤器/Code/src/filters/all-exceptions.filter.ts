import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { ErrorResponseDto } from '../common/error-response.dto';

/**
 * 兜底过滤器
 *
 * @Catch() 不传参数 = 捕获所有异常。
 * 放在过滤器链的最外层，捕获所有未被特定过滤器处理的异常：
 *   - 数据库连接错误（TypeORM 的 QueryFailedError）
 *   - 第三方服务超时（AxiosError）
 *   - 未预期的编程错误（TypeError / ReferenceError）
 *   - 任何 throw 出来但不是 HttpException / BusinessException 的东西
 *
 * 兜底原则：
 *   1. 完整堆栈写日志，方便后端排查
 *   2. 对前端只返回友好提示 + 500 状态码，不泄露堆栈和实现细节
 *   3. 非生产环境可以在 details 里附带 name + message，便于联调
 */
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger(AllExceptionsFilter.name);

  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    // 完整堆栈进日志，不返回给前端
    const stack =
      exception instanceof Error ? exception.stack : String(exception);
    this.logger.error(
      `未捕获异常: ${request.method} ${request.url}`,
      stack,
    );

    // 非生产环境附带错误名 + message，方便前端联调
    const isProd = process.env.NODE_ENV === 'production';
    const details = isProd
      ? undefined
      : {
          name: exception instanceof Error ? exception.name : typeof exception,
          message:
            exception instanceof Error ? exception.message : String(exception),
        };

    const body: ErrorResponseDto = {
      code: 'INTERNAL_ERROR',
      message: '服务器内部错误，请稍后重试',
      details,
      timestamp: new Date().toISOString(),
      path: request.url,
    };

    response.status(500).json(body);
  }
}
