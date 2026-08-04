import { Controller, Get } from '@nestjs/common';
import { DefaultService } from './default.service';
import { RequestScopedService } from './request-scoped.service';
import { TransientService } from './transient.service';

/**
 * 作用域对比演示控制器。
 *
 * 三条路由分别调用三种作用域的服务：
 *   - /scope/default      多次访问返回的 instanceId 不变（单例）
 *   - /scope/request      每次 HTTP 请求 instanceId 都不同（请求级隔离）
 *   - /scope/transient    同一请求内多次注入也是不同实例
 *   - /scope              一次性返回三种作用域的对比结果
 */
@Controller('scope')
export class ScopeDemoController {
  // 同一控制器中注入两次 TransientService，验证“每次注入都新建实例”
  constructor(
    private readonly defaultService: DefaultService,
    private readonly requestScopedService: RequestScopedService,
    private readonly transientA: TransientService,
    private readonly transientB: TransientService,
  ) {}

  @Get('default')
  default() {
    return { label: 'DEFAULT', info: this.defaultService.describe() };
  }

  @Get('request')
  request() {
    return { label: 'REQUEST', info: this.requestScopedService.describe() };
  }

  @Get('transient')
  transient() {
    return {
      label: 'TRANSIENT',
      // 同一请求内注入两次：两个实例 id 必然不同
      transientA: this.transientA.describe(),
      transientB: this.transientB.describe(),
      sameInstance: this.transientA === this.transientB,
    };
  }

  @Get()
  compare() {
    return {
      message: '对比三种作用域实例',
      default: this.defaultService.describe(),
      request: this.requestScopedService.describe(),
      transientA: this.transientA.describe(),
      transientB: this.transientB.describe(),
      tips: [
        'DEFAULT：刷新页面 instanceId 不变',
        'REQUEST：每次刷新 instanceId 都变',
        'TRANSIENT：transientA 与 transientB 的 instanceId 永远不同',
      ],
    };
  }
}
