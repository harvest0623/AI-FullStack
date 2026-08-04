import 'reflect-metadata';
import { Logger } from '@nestjs/common';

/**
 * ============================================================
 *  迷你 IoC 容器（教学用，展示 NestJS DI 的本质原理）
 * ============================================================
 *
 * 这一段呼应 TypeScript 板块 Day09 的 mini-di-container。
 * NestJS 的 DI 容器本质上做的事情就是：
 *   1. 维护一个 Token → Provider 描述 的注册表
 *   2. 解析 Token 时根据 Provider 描述去实例化（useClass / useValue / useFactory）
 *   3. 利用 reflect-metadata 读取构造函数参数的类型元数据，递归解析依赖
 *   4. 默认单例缓存（DEFAULT 作用域）
 *
 * 本文件实现一个最小可用版本：
 *   - 支持 useClass / useValue / useFactory
 *   - 支持构造函数注入
 *   - 支持单例缓存
 *   - 不支持作用域、循环依赖、属性注入（留给读者练习）
 */

// Provider 描述：注册时的三种形态
type Provider<T = any> =
  | { provide: any; useValue: T }
  | { provide: any; useClass: new (...args: any[]) => T }
  | { provide: any; useFactory: (...args: any[]) => T | Promise<T>; inject?: any[] };

const DESIGN_PARAMTYPES = 'design:paramtypes';

export class MiniIocContainer {
  private readonly providers = new Map<any, Provider>();
  private readonly instances = new Map<any, any>();
  private readonly logger = new Logger('MiniIocContainer');

  /** 注册一个或多个 Provider */
  register(...list: Provider[]): this {
    for (const p of list) {
      if (this.providers.has(p.provide)) {
        throw new Error(`Token 已注册: ${String(p.provide)}`);
      }
      this.providers.set(p.provide, p);
    }
    return this;
  }

  /** 根据 Token 解析实例（默认单例） */
  async resolve<T>(token: any): Promise<T> {
    // 命中单例缓存
    if (this.instances.has(token)) {
      return this.instances.get(token) as T;
    }

    const provider = this.providers.get(token);
    if (!provider) {
      throw new Error(`找不到 Token: ${String(token)}`);
    }

    let instance: T;

    if ('useValue' in provider) {
      instance = provider.useValue as T;
    } else if ('useClass' in provider) {
      const ctor = provider.useClass;
      // 关键：用 reflect-metadata 读取构造函数参数的类型
      const paramTypes: any[] =
        Reflect.getMetadata(DESIGN_PARAMTYPES, ctor) ?? [];
      const args = await Promise.all(
        paramTypes.map((t) => this.resolve(t)),
      );
      instance = new ctor(...args);
    } else if ('useFactory' in provider) {
      // 工厂函数支持异步
      const deps = await Promise.all(
        (provider.inject ?? []).map((t) => this.resolve(t)),
      );
      instance = (await provider.useFactory(...deps)) as T;
    } else {
      throw new Error(`未知的 Provider 形态: ${String(token)}`);
    }

    this.instances.set(token, instance);
    this.logger.log(`已解析: ${String(token)}`);
    return instance;
  }
}

// ============================================================
//  示例：用迷你容器组装一套小型业务
// ============================================================

interface LoggerService {
  log(msg: string): void;
}

class ConsoleLoggerService implements LoggerService {
  log(msg: string): void {
    // eslint-disable-next-line no-console
    console.log(`[mini-ioc] ${msg}`);
  }
}

class ConfigService {
  getConfig() {
    return { appName: 'MiniIocDemo', port: 3000 };
  }
}

class UserService {
  constructor(
    private readonly logger: LoggerService,
    private readonly config: ConfigService,
  ) {}

  greet(name: string): string {
    this.logger.log(`greet 被调用，配置：${JSON.stringify(this.config.getConfig())}`);
    return `Hello, ${name}! (from ${this.config.getConfig().appName})`;
  }
}

/**
 * 运行迷你 IoC 演示，main.ts 中会调用一次。
 * 不依赖 NestJS 容器，纯 reflect-metadata 实现。
 */
export async function runMiniIocDemo(): Promise<void> {
  const container = new MiniIocContainer();

  // 注册：Logger 用抽象 Token（Symbol），其余用类作 Token
  const LOGGER_TOKEN = Symbol('LOGGER');
  container.register(
    { provide: LOGGER_TOKEN, useClass: ConsoleLoggerService },
    { provide: ConfigService, useClass: ConfigService },
    { provide: UserService, useClass: UserService },
  );

  // 因为 UserService 的构造函数参数类型是 LoggerService（接口），
  // 而 TS 编译后接口元数据丢失，emitDecoratorMetadata 写入的是 Object，
  // 这里手动把 UserService 的第一个参数元数据改为 LOGGER_TOKEN，模拟 NestJS @Inject
  Reflect.defineMetadata(
    DESIGN_PARAMTYPES,
    [LOGGER_TOKEN, ConfigService],
    UserService,
  );

  const userService = await container.resolve(UserService);
  // eslint-disable-next-line no-console
  console.log(userService.greet('NestJS'));
}
