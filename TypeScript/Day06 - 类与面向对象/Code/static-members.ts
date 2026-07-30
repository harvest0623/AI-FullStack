/**
 * Day06 - 静态成员 static：属性、方法、代码块、单例模式
 *
 * 本文件演示：
 * 1. 静态属性与静态方法
 * 2. 静态方法内 this 指向类本身，不能访问实例字段
 * 3. 静态代码块 static {} 做静态初始化
 * 4. 静态成员的继承
 * 5. 用静态成员实现单例模式
 * 6. 工厂方法：用静态方法做构造分发
 */

// ============================================================
// 1. 静态属性与静态方法
// ============================================================

class MathUtil {
  static readonly PI = 3.14159;          // 静态只读属性
  static readonly VERSION = '1.0.0';
  static instanceCount = 0;              // 静态可变属性

  constructor() {
    MathUtil.instanceCount++;            // 通过类名访问静态属性
  }

  static square(x: number): number {     // 静态方法
    return x * x;
  }

  static cube(x: number): number {
    return MathUtil.square(x) * x;       // 静态方法内通过类名调静态方法
  }

  static max<T>(a: T, b: T): T {         // 静态泛型方法
    return a > b ? a : b;
  }
}

// 静态成员通过类名访问，不需要实例化
console.log('PI:', MathUtil.PI);
console.log('square(5):', MathUtil.square(5));
console.log('cube(3):', MathUtil.cube(3));
console.log('max(1, 2):', MathUtil.max(1, 2));

// ❌ 静态成员不能通过实例访问
// const m = new MathUtil();
// m.PI;
// m.square(5);


// ============================================================
// 2. 静态方法内 this 指向类本身
// ============================================================

class Counter {
  static total = 0;
  count = 0;                             // 实例字段

  constructor() {
    Counter.total++;
  }

  increment(): void {
    this.count++;                        // 实例方法内 this 是实例
  }

  static showTotal(): void {
    // this 在静态方法内指向类本身
    console.log('  静态方法内 this === Counter:', this === Counter);
    console.log('  当前已创建实例数:', this.total);   // ✅ 访问静态属性

    // ❌ 静态方法内不能访问实例字段
    // console.log(this.count);
  }
}

new Counter();
new Counter();
new Counter();
Counter.showTotal();                     // 当前已创建实例数: 3


// ============================================================
// 3. 静态代码块 static {}：静态初始化
// ============================================================

class ConfigLoader {
  // 私有静态字段：在 static 块中赋值，对外通过只读 getter 暴露
  // （useDefineForClassFields: true 下，static readonly 字段不可在 static 块中赋值，
  //   所以用“私有字段 + 只读 getter”模式实现等价的“只读 + 静态初始化”语义）
  private static _settings: Record<string, string>;
  private static _buildTime: number;

  // 静态代码块：在类被求值时执行一次，可访问私有静态字段
  static {
    console.log('  [static block] 初始化 ConfigLoader...');
    const env = process.env.NODE_ENV ?? 'dev';
    ConfigLoader._settings = {
      env,
      apiKey: process.env.API_KEY ?? `default-key-for-${env}`,
      region: process.env.REGION ?? 'cn-north-1',
    };
  }

  // 一个类可以有多个 static 块，按出现顺序执行
  static {
    ConfigLoader._buildTime = Date.now();
    console.log('  [static block] BUILD_TIME 已记录');
  }

  // 只读 getter：对外暴露不可变的静态配置
  static get SETTINGS(): Record<string, string> {
    return ConfigLoader._settings;
  }

  static get BUILD_TIME(): number {
    return ConfigLoader._buildTime;
  }

  static get(key: string): string | undefined {
    return ConfigLoader._settings[key];
  }
}

console.log('env:', ConfigLoader.get('env'));
console.log('region:', ConfigLoader.get('region'));
console.log('build time:', new Date(ConfigLoader.BUILD_TIME).toISOString());


// ============================================================
// 4. 静态成员的继承
// ============================================================

class BaseRepo {
  static entityName = 'base';

  static describe(): string {
    return `Repository for ${this.entityName}`;
    // ⚠️ 这里的 this 在静态方法内是“调用该方法的对象”
    // 子类调用时，this 指向子类，所以多态生效
  }
}

class UserRepo extends BaseRepo {
  static override entityName = 'user';   // 覆盖静态属性
}

console.log(BaseRepo.describe());        // Repository for base
console.log(UserRepo.describe());        // Repository for user（多态）


// ============================================================
// 5. 单例模式：私有构造函数 + 静态访问点
// ============================================================

class Logger {
  private static instance: Logger;
  private logs: string[] = [];

  // 私有构造函数：禁止外部 new
  private constructor() {
    console.log('  [Logger] 初始化单例实例');
  }

  // 静态访问点：懒加载
  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  log(msg: string): void {
    const time = new Date().toISOString();
    this.logs.push(`[${time}] ${msg}`);
  }

  show(): void {
    console.log('  日志条数:', this.logs.length);
    this.logs.slice(-3).forEach((l) => console.log('  ', l));
  }
}

const loggerA = Logger.getInstance();
const loggerB = Logger.getInstance();
console.log('单例验证（A === B）:', loggerA === loggerB);   // true

loggerA.log('启动应用');
loggerA.log('收到请求');
loggerB.log('处理完成');
loggerA.show();
// 即使通过 loggerB 调用 log，也写入同一份日志，因为是同一个实例


// ============================================================
// 6. 工厂方法：用静态方法做构造分发
// ============================================================

interface Animal {
  speak(): string;
}

class Dog implements Animal {
  speak(): string { return '汪汪'; }
}
class Cat implements Animal {
  speak(): string { return '喵喵'; }
}
class Duck implements Animal {
  speak(): string { return '嘎嘎'; }
}

class AnimalFactory {
  // 私有构造：阻止实例化工厂本身
  private constructor() {}

  // 用注册表把字符串映射到构造函数
  private static registry = new Map<string, new () => Animal>([
    ['dog', Dog],
    ['cat', Cat],
    ['duck', Duck],
  ]);

  // 静态工厂方法
  static create(kind: string): Animal {
    const Ctor = AnimalFactory.registry.get(kind);
    if (!Ctor) {
      throw new Error(`未知动物类型：${kind}`);
    }
    return new Ctor();
  }

  // 支持动态注册
  static register(kind: string, Ctor: new () => Animal): void {
    AnimalFactory.registry.set(kind, Ctor);
  }
}

console.log(AnimalFactory.create('dog').speak());
console.log(AnimalFactory.create('cat').speak());

// 动态注册新类型
class Rabbit implements Animal {
  speak(): string { return '吱吱'; }
}
AnimalFactory.register('rabbit', Rabbit);
console.log(AnimalFactory.create('rabbit').speak());

try {
  AnimalFactory.create('unknown');
} catch (e) {
  console.log('工厂拦截:', (e as Error).message);
}


// ============================================================
// 7. 静态成员常用于：工具函数、常量、缓存
// ============================================================

class Cache {
  private static store = new Map<string, { value: unknown; expireAt: number }>();

  private constructor() {}

  static set(key: string, value: unknown, ttlMs: number = 60000): void {
    Cache.store.set(key, { value, expireAt: Date.now() + ttlMs });
  }

  static get<T>(key: string): T | undefined {
    const entry = Cache.store.get(key);
    if (!entry) return undefined;
    if (Date.now() > entry.expireAt) {
      Cache.store.delete(key);
      return undefined;
    }
    return entry.value as T;
  }

  static clear(): void {
    Cache.store.clear();
  }
}

Cache.set('user:1', { name: 'Alice' }, 5000);
console.log('缓存命中:', Cache.get<{ name: string }>('user:1'));
console.log('缓存未命中:', Cache.get('user:2'));


console.log('\n--- static-members.ts 执行完毕 ---');

export {};
