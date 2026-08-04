import { Injectable, Scope } from '@nestjs/common';

/**
 * DEFAULT 作用域服务（默认值，单例）
 *
 * 整个应用生命周期内，IoC 容器只创建一个实例，
 * 所有注入它的消费者共享同一份状态。
 *
 * 适用：无状态服务、纯函数式工具、配置读取、日志服务等。
 * 优点：性能最佳，无重复实例化开销。
 */
@Injectable({ scope: Scope.DEFAULT })
export class DefaultService {
  private readonly createdAt: number;
  private instanceId = 0;

  constructor() {
    this.createdAt = Date.now();
    this.instanceId = Math.floor(Math.random() * 10_000);
    // 注意：DEFAULT 作用域下，本构造函数在整个应用只会被调用一次
  }

  describe(): string {
    return `[DefaultService] instanceId=${this.instanceId}, createdAt=${this.createdAt}`;
  }
}
