import { forwardRef, Inject, Injectable } from '@nestjs/common';
import { ServiceA } from './service-a.service';

/**
 * ServiceB 是循环依赖的另一半：注入 ServiceA。
 *
 * 注意：两端都需要用 @Inject(forwardRef(() => ServiceA))，
 * 缺一不可，否则容器在解析时仍会因找不到目标而抛出 Nest can't resolve dependencies 错误。
 *
 * 另一种方案：模块级 forwardRef
 *  @Module({ imports: [forwardRef(() => OtherModule)] })
 * 用于跨模块循环依赖，思路一致：让模块加载顺序可延迟。
 */
@Injectable()
export class ServiceB {
  constructor(
    @Inject(forwardRef(() => ServiceA)) private readonly serviceA: ServiceA,
  ) {}

  whoAmI(): string {
    return 'I am ServiceB';
  }

  callA(): string {
    return `ServiceB -> ${this.serviceA.whoAmI()}`;
  }
}
