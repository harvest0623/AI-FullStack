import { Injectable, Scope } from '@nestjs/common';

/**
 * TRANSIENT 作用域服务：每次注入都新建一个实例。
 *
 * 与 REQUEST 的区别：
 *  - REQUEST：每个 HTTP 请求一个实例，同一请求内多次注入共享。
 *  - TRANSIENT：每次注入都是全新实例，与请求边界无关。
 *
 * 适用：临时计算单元、不可变值对象、需要严格隔离状态的小工具。
 * 注意：性能开销最大，谨慎使用。
 */
@Injectable({ scope: Scope.TRANSIENT })
export class TransientService {
  private readonly instanceId: number;
  private readonly createdAt: number;

  constructor() {
    this.instanceId = Math.floor(Math.random() * 10_000);
    this.createdAt = Date.now();
  }

  describe(): string {
    return `[TransientService] instanceId=${this.instanceId}, createdAt=${this.createdAt}`;
  }
}
