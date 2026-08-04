import { Controller, Get, Inject, Injectable } from '@nestjs/common';
import {
  APP_CONFIG_TOKEN,
  AppConfig,
  LOGGER_KEY,
  ILogger,
  CacheProvider,
} from './token.constants';

/**
 * 抽象类 Token 的具体实现：基于内存的 Map 实现 CacheProvider。
 * 注册到容器时 Token 用的是抽象类本身，注入时也用抽象类。
 */
@Injectable()
export class InMemoryCacheProvider extends CacheProvider {
  private readonly store = new Map<string, unknown>();

  get(key: string): unknown {
    return this.store.get(key);
  }

  set(key: string, value: unknown): void {
    this.store.set(key, value);
  }
}

/**
 * Token 注入演示控制器。
 *
 * 演示四种 Token 的注入方式：
 *   1. 类 Token —— 通过构造函数参数的类型自动推断（最常见）
 *   2. 字符串 Token —— 必须使用 @Inject(字符串Token)
 *   3. Symbol Token —— 必须使用 @Inject(SymbolToken)
 *   4. 抽象类 Token —— 类型写抽象类，Token 也是抽象类
 *
 * 关键点：当 Token 不是类（字符串/Symbol）或不是参数类型本身时，
 * 必须使用 @Inject() 装饰器显式指定 Token，否则容器无法通过
 * reflect-metadata 推断出正确的 Token。
 */
@Controller('token')
export class TokenDemoController {
  constructor(
    // 1. 类 Token：直接通过 TS 类型推断（emitDecoratorMetadata 自动写入元数据）
    private readonly cache: InMemoryCacheProvider,
    // 2. 字符串 Token：必须 @Inject
    @Inject(APP_CONFIG_TOKEN) private readonly config: AppConfig,
    // 3. Symbol Token：必须 @Inject
    @Inject(LOGGER_KEY) private readonly logger: ILogger,
    // 4. 抽象类 Token：类型写抽象类，Token 也是抽象类
    @Inject(CacheProvider) private readonly cacheByAbstract: CacheProvider,
  ) {}

  @Get()
  showAll() {
    this.logger.log('访问 /token 路由');
    this.cache.set('lastVisit', new Date().toISOString());

    return {
      classToken: {
        concreteImpl: this.cache.constructor.name,
        // 通过 useExisting 让 InMemoryCacheProvider 与 CacheProvider 共享同一实例
        sameInstanceWithAbstract: this.cache === this.cacheByAbstract,
      },
      stringToken: {
        token: APP_CONFIG_TOKEN,
        value: this.config,
      },
      symbolToken: {
        token: LOGGER_KEY.toString(),
        loggerType: this.logger.constructor.name,
      },
      abstractClassToken: {
        token: CacheProvider.name,
        concreteImpl: this.cacheByAbstract.constructor.name,
      },
      tips: [
        '类 Token 与抽象类 Token 都可走 TS 类型推断',
        '字符串与 Symbol Token 必须显式 @Inject',
        '抽象类 Token 是面向接口编程的关键',
      ],
    };
  }
}
