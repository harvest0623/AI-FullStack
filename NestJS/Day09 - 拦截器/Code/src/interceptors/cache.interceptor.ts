import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import { Observable, of, tap } from 'rxjs';

/**
 * CacheInterceptor —— 基于内存的简单缓存拦截器
 *
 * 演示点：
 * 1. 命中缓存时使用 of(cachedData) 直接返回，根本不调用 next.handle()
 * 2. 未命中时通过 tap 在数据返回后写入缓存
 * 3. 仅对 GET 请求生效
 *
 * 局限：内存缓存，进程重启即失效；不适合多实例部署。
 * 生产环境建议替换为 Redis 等分布式缓存。
 */
@Injectable()
export class CacheInterceptor implements NestInterceptor {
  private readonly cache = new Map<string, { data: any; expireAt: number }>();
  private readonly ttl = 10_000; // 缓存有效期 10 秒

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const key = request.url;

    // 非 GET 请求不缓存
    if (request.method !== 'GET') {
      return next.handle();
    }

    const cached = this.cache.get(key);
    const now = Date.now();

    // 命中缓存且未过期：直接返回，跳过 handler
    if (cached && cached.expireAt > now) {
      console.log(`🎯 命中缓存：${key}`);
      return of(cached.data);
    }

    // 未命中：先执行 handler，再写入缓存
    return next.handle().pipe(
      tap((data) => {
        console.log(`💾 写入缓存：${key}`);
        this.cache.set(key, { data, expireAt: now + this.ttl });
      }),
    );
  }
}
