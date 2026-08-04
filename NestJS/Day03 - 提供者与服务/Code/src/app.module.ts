// ============================================================
// AppModule：根模块
// ------------------------------------------------------------
// 集中演示 NestJS 全部 Provider 注册方式：
//   1. 简写：直接写类名，等价于 { provide: X, useClass: X }
//   2. useClass：基于抽象类/接口的实现切换
//   3. useValue：值提供者（mock、配置对象）
//   4. useFactory：工厂提供者（可异步、可依赖其他 Provider）
//   5. useExisting：别名提供者（多个 Token 指向同一实例）
//   6. Token 类型：类 Token / 字符串 Token / Symbol Token
// ============================================================

import { Controller, Get, Inject, Module } from '@nestjs/common';
import { ArticlesModule } from './articles/articles.module';
import {
  APP_INFO_TOKEN,
  CACHE_CLIENT_TOKEN,
  MOCK_SENDER_TOKEN,
  SENDER_ALIAS_TOKEN,
} from './config/token.constants';

// ============================================================
// useClass 演示：抽象类作为 Token，子类作为实现
// ------------------------------------------------------------
// 通过修改 useClass 一行即可切换实现，调用方代码不变。
// 这是"面向接口编程"在 NestJS 中的落地方式。
// ============================================================
abstract class NotificationSender {
  abstract send(to: string, message: string): void;
}

class EmailSender extends NotificationSender {
  send(to: string, message: string): void {
    console.log(`[Email] → ${to}: ${message}`);
  }
}

class SmsSender extends NotificationSender {
  send(to: string, message: string): void {
    console.log(`[SMS] → ${to}: ${message}`);
  }
}

// ============================================================
// useValue 演示：mock 对象
// ------------------------------------------------------------
// 测试时常用 useValue 替换真实实现，无需改动业务代码。
// ============================================================
const mockSender: NotificationSender = {
  send: (to, message) => console.log(`[Mock] → ${to}: ${message}`),
};

// ============================================================
// useFactory 演示：异步工厂返回缓存客户端
// ------------------------------------------------------------
// 工厂可异步初始化（建立连接、读取配置），并通过 inject
// 数组声明对其他 Provider 的依赖。
// ============================================================
interface CacheClient {
  get(key: string): string | null;
  set(key: string, value: string): void;
}

async function createCacheClient(): Promise<CacheClient> {
  await new Promise((resolve) => setTimeout(resolve, 50));
  const store = new Map<string, string>();
  return {
    get: (key) => store.get(key) ?? null,
    set: (key, value) => void store.set(key, value),
  };
}

// ============================================================
// 演示控制器：注入上述各类 Provider，验证效果
// ------------------------------------------------------------
// 类 Token 用构造函数注入，字符串 / Symbol Token 必须用 @Inject
// ============================================================
@Controller('demo')
class DemoController {
  constructor(
    // 类作为 Token：构造函数注入即可
    private readonly sender: NotificationSender,
    // 字符串 Token：必须 @Inject
    @Inject(MOCK_SENDER_TOKEN)
    private readonly mockSender: NotificationSender,
    @Inject(CACHE_CLIENT_TOKEN) private readonly cache: CacheClient,
    // useExisting 别名：与 sender 是同一实例
    @Inject(SENDER_ALIAS_TOKEN)
    private readonly aliasSender: NotificationSender,
    // Symbol Token：必须 @Inject
    @Inject(APP_INFO_TOKEN)
    private readonly appInfo: { name: string; version: string },
  ) {}

  @Get()
  run(): Record<string, unknown> {
    this.sender.send('user@example.com', 'useClass 注入');
    this.mockSender.send('user@example.com', 'useValue mock');
    this.cache.set('demo', 'value');

    return {
      cache: this.cache.get('demo'),
      appInfo: this.appInfo,
      // useExisting 指向同一实例，应为 true
      sameInstance: this.sender === this.aliasSender,
    };
  }
}

@Module({
  imports: [ArticlesModule],
  controllers: [DemoController],
  providers: [
    // ① 简写：直接写类名（此处未用，ArticlesModule 中已演示）

    // ② useClass：基于抽象类的实现切换
    //    切换到 SmsSender 只需修改 useClass 一行
    {
      provide: NotificationSender,
      useClass: EmailSender,
    },

    // ③ useValue：值提供者（mock、配置对象）
    {
      provide: MOCK_SENDER_TOKEN,
      useValue: mockSender,
    },

    // ④ useFactory：工厂提供者，可异步、可依赖其他 Provider
    //    inject 数组声明工厂函数参数对应的 Token
    {
      provide: CACHE_CLIENT_TOKEN,
      useFactory: async () => createCacheClient(),
      inject: [],
    },

    // ⑤ useExisting：别名提供者
    //    SENDER_ALIAS_TOKEN 与 NotificationSender 指向同一实例
    {
      provide: SENDER_ALIAS_TOKEN,
      useExisting: NotificationSender,
    },

    // ⑥ Symbol Token：全局唯一，从根本上避免字符串命名冲突
    {
      provide: APP_INFO_TOKEN,
      useValue: { name: 'NestJS Day03', version: '1.0.0' },
    },
  ],
})
export class AppModule {}
