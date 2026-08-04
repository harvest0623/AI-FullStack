import { Injectable, Inject, Scope, REQUEST } from '@nestjs/common';
import { Request } from 'express';

/**
 * REQUEST 作用域服务：每个 HTTP 请求新建一个实例。
 *
 * 注意：
 * 1. REQUEST 作用域服务可以注入 @Inject(REQUEST) 获取当前请求对象，
 *    这是 DEFAULT 作用域无法做到的（DEFAULT 作用域下 REQUEST 还不存在）。
 * 2. 由于每个请求都要新建实例，性能开销明显大于 DEFAULT，
 *    仅在需要按请求隔离状态（如多租户上下文、请求级追踪 ID）时使用。
 * 3. REQUEST 作用域注入链向上传播：注入它的所有上游 Provider 也会被
 *    强制降级为 REQUEST 作用域，进而影响整条依赖链的性能。
 */
@Injectable({ scope: Scope.REQUEST })
export class RequestScopedService {
  private readonly instanceId: number;
  private readonly requestId: string;

  constructor(@Inject(REQUEST) private readonly request: Request) {
    this.instanceId = Math.floor(Math.random() * 10_000);
    // 从请求头读取或生成一个追踪 ID，方便观察每个请求得到独立实例
    this.requestId =
      (this.request.headers['x-request-id'] as string | undefined) ??
      `req-${Date.now()}`;
  }

  describe(): string {
    return `[RequestScopedService] instanceId=${this.instanceId}, requestId=${this.requestId}, url=${this.request.url}`;
  }
}
