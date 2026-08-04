import { Module } from '@nestjs/common';
import { ScopeDemoController } from './scope-demo/scope-demo.controller';
import { DefaultService } from './scope-demo/default.service';
import { RequestScopedService } from './scope-demo/request-scoped.service';
import { TransientService } from './scope-demo/transient.service';
import {
  TokenDemoController,
  InMemoryCacheProvider,
} from './token-demo/token-demo.controller';
import {
  APP_CONFIG_TOKEN,
  AppConfig,
  LOGGER_KEY,
  ILogger,
  CacheProvider,
} from './token-demo/token.constants';
import { CircularRefController } from './circular-ref/circular-ref.controller';
import { ServiceA } from './circular-ref/service-a.service';
import { ServiceB } from './circular-ref/service-b.service';
import { AsyncProviderController } from './async-provider/async-provider.controller';
import {
  DATABASE_CONNECTION,
  DatabaseConnection,
  createDatabaseConnection,
} from './async-provider/database-connection.provider';

/**
 * Day05 根模块。
 *
 * 集中演示四种核心机制：
 *   1. 三种作用域（DEFAULT / REQUEST / TRANSIENT）—— 见 scope-demo/
 *   2. 四种 Token 注入（类 / 字符串 / Symbol / 抽象类）—— 见 token-demo/
 *   3. forwardRef 解决循环依赖 —— 见 circular-ref/
 *   4. useFactory 异步初始化 —— 见 async-provider/
 *
 * Provider 注册写法对照表：
 *   简写：     providers: [FooService]                          等价于 useClass
 *   useClass: { provide: FooService, useClass: FooServiceImpl } 面向接口
 *   useValue: { provide: 'CONFIG', useValue: {...} }            注入常量
 *   useFactory: { provide: 'DB', useFactory: async () => {} }   异步初始化
 *   useExisting: { provide: 'Logger', useExisting: AppLogger }  别名
 */
@Module({
  imports: [],
  controllers: [
    ScopeDemoController,
    TokenDemoController,
    CircularRefController,
    AsyncProviderController,
  ],
  providers: [
    // ---------- 作用域演示 ----------
    DefaultService,
    RequestScopedService,
    TransientService,

    // ---------- Token 演示 ----------
    // 字符串 Token：注入常量配置
    {
      provide: APP_CONFIG_TOKEN,
      useValue: {
        port: 3000,
        env: 'dev' as const,
        featureFlags: { newDashboard: true },
      } satisfies AppConfig,
    },
    // Symbol Token：注入一个实现 ILogger 接口的对象
    {
      provide: LOGGER_KEY,
      useValue: {
        log(message: string) {
          // eslint-disable-next-line no-console
          console.log(`[ILogger:${LOGGER_KEY.toString()}] ${message}`);
        },
        error(message: string) {
          // eslint-disable-next-line no-console
          console.error(`[ILogger:${LOGGER_KEY.toString()}] ${message}`);
        },
      } satisfies ILogger,
    },
    // 抽象类 Token：注册时用抽象类，useClass 指向具体实现
    { provide: CacheProvider, useClass: InMemoryCacheProvider },
    // 类 Token 通过 useExisting 别名指向抽象类 Token，让两个 Token 共享同一实例
    { provide: InMemoryCacheProvider, useExisting: CacheProvider },

    // ---------- 循环依赖演示 ----------
    ServiceA,
    ServiceB,

    // ---------- 异步 Provider 演示 ----------
    {
      provide: DATABASE_CONNECTION,
      useFactory: async (): Promise<DatabaseConnection> => {
        return createDatabaseConnection();
      },
    },
  ],
})
export class AppModule {}
