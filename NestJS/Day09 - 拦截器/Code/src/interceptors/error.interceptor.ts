import {
  CallHandler,
  ExecutionContext,
  HttpException,
  Injectable,
  InternalServerErrorException,
  Logger,
  NestInterceptor,
} from '@nestjs/common';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

/**
 * ErrorInterceptor —— 异常转换拦截器
 *
 * 演示点：
 * 1. catchError 捕获流中的 error 通知，可以做"异常转换"
 * 2. 已知的 HttpException 原样抛出，保留业务语义
 * 3. 未知异常（数据库错误、类型错误等）统一包装为 500
 * 4. 在这里还能做"异常上报"（如发送到 Sentry / ELK）
 *
 * 注意：catchError 必须返回一个新的 Observable，通常用 throwError 重新抛出。
 */
@Injectable()
export class ErrorInterceptor implements NestInterceptor {
  private readonly logger = new Logger(ErrorInterceptor.name);

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      catchError((err) => {
        // 已经是 HttpException：保留原始状态码与消息
        if (err instanceof HttpException) {
          this.logger.warn(`业务异常：${err.message}`);
          return throwError(() => err);
        }

        // 未知异常：记录完整堆栈，对外屏蔽细节
        this.logger.error(`未捕获异常：${err.message}`, err.stack);
        return throwError(
          () => new InternalServerErrorException('服务器内部错误，请稍后再试'),
        );
      }),
    );
  }
}
