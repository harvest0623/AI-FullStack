/**
 * Day09 - 迷你依赖注入容器（mini DI Container）
 *
 * 用到的能力：
 *   - 类装饰器 @Injectable()：标记该类可被容器管理
 *   - 构造函数参数装饰器 @Inject(token)：指定参数对应哪个 Provider
 *   - emitDecoratorMetadata：读取 design:paramtypes 自动推断构造函数参数类型
 *
 * 这是 NestJS Provider / Injectable 系统的最小内核：
 *   1. 注册：container.register(token, Class)
 *   2. 解析：container.resolve(token) 时：
 *        a. 读 design:paramtypes 拿到构造函数形参类型
 *        b. 若有 @Inject 元数据，优先用显式 token 覆盖
 *        c. 递归 resolve 每个依赖
 *        d. new 出实例并缓存（单例）
 */

import 'reflect-metadata';

// ---------- 元数据 key ----------
const INJECTABLE_KEY = Symbol('di:injectable');
const INJECT_KEY = Symbol('di:inject');

// ---------- 装饰器 ----------
function Injectable(): ClassDecorator {
  return function (target: any) {
    Reflect.defineMetadata(INJECTABLE_KEY, true, target);
    return target;
  };
}

function Inject(token: string): ParameterDecorator {
  return function (target: any, _propertyKey: string | symbol | undefined, parameterIndex: number) {
    // 在构造函数（target）上保存 { index: token } 映射
    const map: Record<number, string> =
      Reflect.getOwnMetadata(INJECT_KEY, target) ?? {};
    map[parameterIndex] = token;
    Reflect.defineMetadata(INJECT_KEY, map, target);
  };
}

// ---------- 容器 ----------
type Provider<T = any> = { token: string; useClass: new (...args: any[]) => T };

class Container {
  private providers = new Map<string, Provider>();
  private instances = new Map<string, any>();

  register<T>(token: string, useClass: new (...args: any[]) => T) {
    if (!Reflect.getMetadata(INJECTABLE_KEY, useClass)) {
      throw new Error(`[Container] ${useClass.name} 未标记 @Injectable()`);
    }
    this.providers.set(token, { token, useClass });
  }

  resolve<T>(token: string): T {
    if (this.instances.has(token)) return this.instances.get(token);

    const provider = this.providers.get(token);
    if (!provider) throw new Error(`[Container] 未注册 token: ${token}`);

    const { useClass } = provider;
    // ① 读 design:paramtypes（需要 emitDecoratorMetadata）
    const paramTypes: any[] = Reflect.getMetadata('design:paramtypes', useClass) ?? [];
    // ② 读 @Inject 元数据，覆盖显式 token
    const injectMap: Record<number, string> =
      Reflect.getOwnMetadata(INJECT_KEY, useClass) ?? {};

    const args = paramTypes.map((type, index) => {
      const explicitToken = injectMap[index];
      if (explicitToken) return this.resolve(explicitToken);

      // 没有 @Inject 时，用类型本身作为 token
      const depProvider = [...this.providers.values()].find((p) => p.useClass === type);
      if (!depProvider) {
        throw new Error(`[Container] 找不到 ${useClass.name} 第 ${index} 个参数的 Provider（类型：${type?.name}）`);
      }
      return this.resolve(depProvider.token);
    });

    const instance = new useClass(...args);
    this.instances.set(token, instance); // 单例缓存
    return instance;
  }
}

// ---------- 使用示例 ----------

@Injectable()
class LoggerService {
  log(msg: string) {
    console.log(`[Logger] ${msg}`);
  }
}

@Injectable()
class CacheService {
  private store = new Map<string, any>();
  set(k: string, v: any) {
    this.store.set(k, v);
  }
  get(k: string) {
    return this.store.get(k);
  }
}

@Injectable()
class DatabaseService {
  constructor(private logger: LoggerService) {}

  query(sql: string): any[] {
    this.logger.log(`SQL: ${sql}`);
    return [{ id: 1, name: 'Alice' }];
  }
}

// 接口场景：用 token 字符串 + @Inject 表达"我要这个抽象"
interface IConfig {
  port: number;
}

@Injectable()
class ProdConfig implements IConfig {
  port = 3000;
}

@Injectable()
class UserService {
  constructor(
    private db: DatabaseService,
    private cache: CacheService,
    @Inject('IConfig') private config: IConfig,
  ) {}

  getUser(id: number) {
    const cached = this.cache.get(`user:${id}`);
    if (cached) {
      console.log(`[UserService] 命中缓存 user:${id}`);
      return cached;
    }
    const rows = this.db.query(`SELECT * FROM users WHERE id=${id}`);
    this.cache.set(`user:${id}`, rows[0]);
    return rows[0];
  }

  describe() {
    console.log(`[UserService] 运行端口 ${this.config.port}`);
  }
}

// ---------- 装配 ----------
const container = new Container();
container.register('Logger', LoggerService);
container.register('Cache', CacheService);
container.register('Database', DatabaseService);
container.register('IConfig', ProdConfig);
container.register('UserService', UserService);

const userService = container.resolve<UserService>('UserService');
userService.describe();                  // [UserService] 运行端口 3000
console.log('第一次查询：', userService.getUser(1));
// [Logger] SQL: ...
console.log('第二次查询：', userService.getUser(1)); // 命中缓存

// 验证单例：再次 resolve 拿到的应是同一实例
const same = container.resolve<UserService>('UserService');
console.log('单例验证：', userService === same); // true

console.log('\n[mini-di-container.ts] 运行结束');
