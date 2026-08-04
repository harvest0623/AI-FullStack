import { Controller, Get } from '@nestjs/common';
import { ServiceA } from './service-a.service';
import { ServiceB } from './service-b.service';

/**
 * 循环依赖演示控制器。
 *
 * 通过 /circular 路由触发 A 与 B 的互相调用，
 * 验证 forwardRef 确实打破了循环依赖的解析死锁。
 */
@Controller('circular')
export class CircularRefController {
  constructor(
    private readonly serviceA: ServiceA,
    private readonly serviceB: ServiceB,
  ) {}

  @Get()
  show() {
    return {
      aCallB: this.serviceA.callB(),
      bCallA: this.serviceB.callA(),
      sameA:
        'forwardRef 让 A 和 B 在容器中各自只创建了一个实例，互相持有引用',
      tips: [
        'forwardRef 仅是权宜之计，重构时应考虑抽出第三者中介服务',
        '跨模块循环依赖用 @Module({ imports: [forwardRef(() => OtherModule)] })',
      ],
    };
  }
}
