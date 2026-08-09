import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
  RequestTimeoutException,
} from '@nestjs/common';
import { Observable, throwError, TimeoutError } from 'rxjs';
import { catchError, timeout } from 'rxjs/operators';

/**
 * TimeoutInterceptor —— 超时控制拦截器
 *
 * 演示点：
 * 1. 使用 rxjs 的 timeout 操作符设置超时阈值（毫秒）
 * 2. 超时后 RxJS 抛出 TimeoutError，用 catchError 捕获
 * 3. 将 TimeoutError 转换为 NestJS 的 RequestTimeoutException（HTTP 408）
 *
 * 测试：访问 GET /articles/slow/5000 会触发超时（默认 3000ms）
 */
@Injectable()
export class TimeoutInterceptor implements NestInterceptor {
  private readonly timeoutMs = 3000;

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      timeout(this.timeoutMs),
      catchError((err) => {
        if (err instanceof TimeoutError) {
          return throwError(
            () => new RequestTimeoutException('请求超时，请稍后再试'),
          );
        }
        return throwError(() => err);
      }),
    );
  }
}
