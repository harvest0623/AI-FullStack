import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import { map, Observable } from 'rxjs';
import { ResponseDto } from '../common/response.dto';

/**
 * TransformInterceptor —— 统一响应格式拦截器
 *
 * 将控制器返回的原始数据统一包装成：
 * {
 *   "code": 200,
 *   "message": "请求成功",
 *   "data": <原数据>
 * }
 *
 * 使用 map 操作符：能对流中的数据进行转换
 * 注意：异常响应不会被 map 捕获，因为异常会以 error 通知形式流过 Observable
 */
@Injectable()
export class TransformInterceptor<T>
  implements NestInterceptor<T, ResponseDto<T>>
{
  intercept(
    context: ExecutionContext,
    next: CallHandler<T>,
  ): Observable<ResponseDto<T>> {
    return next.handle().pipe(
      map((data) => ResponseDto.success(data)),
    );
  }
}
