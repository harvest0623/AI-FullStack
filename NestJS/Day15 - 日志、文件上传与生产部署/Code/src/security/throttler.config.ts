import { ThrottlerModuleAsyncOptions } from '@nestjs/throttler';
import { ConfigService } from '@nestjs/config';

/**
 * Throttler 限流配置说明
 * ------------------------------------------------------------
 * @nestjs/throttler 通过内存或 Redis 存储请求计数，对单 IP 做 QPS 限制。
 *
 * 工作原理：
 *   1. ThrottlerGuard 作为全局守卫拦截每个请求
 *   2. 在固定时间窗口（TTL）内累计计数
 *   3. 超过 limit 时返回 429 Too Many Requests
 *
 * 关键 API：
 *   - ThrottlerModule.forRoot / forRootAsync：注册全局配置
 *   - ThrottlerGuard：守卫类，通过 APP_GUARD 注册为全局
 *   - @Throttle({ default: { limit: 3, ttl: 10000 } })：装饰器细粒度覆盖
 *   - @SkipThrottle()：跳过限流（如内部健康检查）
 *
 * 配置项：
 *   - ttl：时间窗口，毫秒（v5+ 默认 ms）
 *   - limit：该窗口内允许的最大请求数
 *   - skipIf：函数，返回 true 时跳过限流
 *   - name：限流策略名，便于多策略组合（如 default / strict）
 *
 * 注册方式一（同步）：
 *   ThrottlerModule.forRoot([{ ttl: 60000, limit: 100 }]);
 *
 * 注册方式二（异步，从配置读取）：
 *   ThrottlerModule.forRootAsync({
 *     inject: [ConfigService],
 *     useFactory: buildThrottlerOptions,
 *   });
 *
 * 在 AppModule 里通过 APP_GUARD 注册全局守卫：
 *   providers: [{ provide: APP_GUARD, useClass: ThrottlerGuard }]
 *
 * 多策略示例（登录接口更严格）：
 *   @Throttle({ auth: { limit: 5, ttl: 60000 } })  // 命名策略
 *   @Post('login')
 *   login() { ... }
 *
 * 分布式部署注意：
 *   - 默认存储是内存 Map，多实例之间不共享
 *   - 生产环境多副本时建议用 @nestjs/throttler-storage-redis，
 *     通过 Redis 共享计数，避免单机限流被穿透
 */
export const throttlerAsyncOptions: ThrottlerModuleAsyncOptions = {
  inject: [ConfigService],
  useFactory: (config: ConfigService) => [
    {
      name: 'default',
      ttl: config.get<number>('THROTTLE_TTL', 60000),
      limit: config.get<number>('THROTTLE_LIMIT', 100),
    },
  ],
};

/**
 * 上述配置对象可在 AppModule 中直接使用：
 *
 *   @Module({
 *     imports: [
 *       ThrottlerModule.forRootAsync(throttlerAsyncOptions),
 *     ],
 *   })
 *
 * 本 Demo 的 AppModule 内联了 useFactory 写法（等价），
 * 本文件作为"配置说明与可复用模块"的参考。
 */
