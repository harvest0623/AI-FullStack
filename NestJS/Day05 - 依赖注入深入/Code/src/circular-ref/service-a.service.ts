import { forwardRef, Inject, Injectable } from '@nestjs/common';
import { ServiceB } from './service-b.service';

/**
 * 循环依赖演示：ServiceA 注入 ServiceB，而 ServiceB 又注入 ServiceA。
 *
 * 当容器实例化 A 时需要先有 B，实例化 B 时又需要 A，
 * 形成 A → B → A 的径向依赖，容器无法决定先创建谁。
 *
 * 解决方案：在参数级使用 @Inject(forwardRef(() => ServiceB))
 *   - forwardRef 接收一个返回 Token 的工厂函数
 *   - 容器先创建 A，把 A 的引用占住，等 B 真正需要时再回填
 *
 * 重要：循环依赖是设计缺陷的信号，能用第三方中介服务拆开就别用 forwardRef。
 */
@Injectable()
export class ServiceA {
  constructor(
    @Inject(forwardRef(() => ServiceB)) private readonly serviceB: ServiceB,
  ) {}

  whoAmI(): string {
    return 'I am ServiceA';
  }

  // 调用 B 的方法，验证双向注入确实成功
  callB(): string {
    return `ServiceA -> ${this.serviceB.whoAmI()}`;
  }
}
