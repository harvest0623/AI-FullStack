import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import { map, Observable } from 'rxjs';

/**
 * ExcludePasswordInterceptor —— 响应字段过滤拦截器
 *
 * 演示点：
 * 1. 使用 map 操作符在响应阶段对数据进行"脱敏"
 * 2. 递归处理数组与对象，剔除敏感字段（如 password）
 * 3. 典型场景：用户接口返回前去除 password / salt / token
 *
 * 提示：更通用的做法是用 @Exclude() + ClassSerializerInterceptor，
 * 这里手写实现是为了演示拦截器的工作原理。
 */
@Injectable()
export class ExcludePasswordInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(map((data) => this.stripPassword(data)));
  }

  private stripPassword(data: any): any {
    if (data === null || data === undefined) {
      return data;
    }

    if (Array.isArray(data)) {
      return data.map((item) => this.stripPassword(item));
    }

    if (typeof data === 'object') {
      const { password, ...rest } = data;
      return rest;
    }

    return data;
  }
}
