import {
  CallHandler,
  ExecutionContext,
  Injectable,
  Logger,
  NestInterceptor,
} from '@nestjs/common';
import { Observable, tap } from 'rxjs';

/**
 * LoggingInterceptor —— 日志与耗时拦截器
 *
 * 演示点：
 * 1. next.handle() 之前的代码 = before 阶段（方法执行前）
 * 2. tap 操作符 = after 阶段（方法执行后），只读取数据不修改
 * 3. 通过 Date.now() 计算 handler 的执行耗时
 */
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger(LoggingInterceptor.name);

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url } = request;
    const handlerName = context.getHandler().name; // 当前被拦截的控制器方法名
    const now = Date.now();

    this.logger.log(`➡️  [${method}] ${url} -> ${handlerName}() 开始执行`);

    return next.handle().pipe(
      // tap 是"副作用"操作符，能拿到流中数据但不会改变数据
      tap(() => {
        const cost = Date.now() - now;
        this.logger.log(`⬅️  [${method}] ${url} <- ${handlerName}() 耗时 ${cost}ms`);
      }),
    );
  }
}
