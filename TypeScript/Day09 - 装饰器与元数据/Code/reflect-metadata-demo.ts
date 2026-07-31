/**
 * Day09 - reflect-metadata 与设计时类型信息
 *
 * 需要：
 *   1. npm i reflect-metadata（devDependencies 已含）
 *   2. tsconfig 开启 emitDecoratorMetadata，TS 才会自动注入：
 *      - design:type       属性/方法的类型
 *      - design:paramtypes 方法/类的形参类型数组
 *      - design:returntype 方法的返回值类型
 *
 * 关键事实：
 *   - 这三个 key 是字符串字面量，由 TS 编译器在 __decorate 调用旁自动插入 __metadata 调用
 *   - 只有被装饰的目标才会被注入；未装饰的方法/属性拿不到这些元数据
 */

import 'reflect-metadata';

// ---------- 1. 元数据反射的基本 API ----------
const META = 'custom:meta';

class MetaDemo {
  // 用 defineMetadata 直接写入自定义元数据
}

Reflect.defineMetadata(META, { author: 'day09' }, MetaDemo);
Reflect.defineMetadata(META, 'hello', MetaDemo.prototype, 'greet');

console.log('类元数据：', Reflect.getMetadata(META, MetaDemo));
console.log('属性元数据：', Reflect.getMetadata(META, MetaDemo.prototype, 'greet'));
console.log('是否存在：', Reflect.hasMetadata(META, MetaDemo));            // true
console.log('自身是否有：', Reflect.hasOwnMetadata(META, MetaDemo));        // true

// getOwnMetadata vs getMetadata：前者不沿原型链
class Child extends MetaDemo {}
console.log('子类沿链查找：', Reflect.getMetadata(META, Child));            // { author: 'day09' }
console.log('子类自身（不含链）：', Reflect.getOwnMetadata(META, Child));    // undefined

// ---------- 2. design:type ----------
// 注：TS 只有在属性/方法存在装饰器时才会注入 design:type
function Inspect(target: any, propertyKey: string) {
  const type = Reflect.getMetadata('design:type', target, propertyKey);
  console.log(`[design:type] ${propertyKey} → ${type?.name ?? type}`);
}

class Sample {
  @Inspect id: number = 0;
  @Inspect name: string = '';
  @Inspect active: boolean = false;
  @Inspect createdAt: Date = new Date();
  @Inspect callback: (() => void) = () => {};
  @Inspect mixed: number | string = 0; // 联合类型运行时只能拿到 Object
}

// ---------- 3. design:paramtypes（方法） ----------
function InspectMethod(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const types = Reflect.getMetadata('design:paramtypes', target, propertyKey);
  console.log(
    `[design:paramtypes] ${propertyKey} → ${types?.map((t: any) => t?.name).join(', ') ?? '无'}`,
  );
  const ret = Reflect.getMetadata('design:returntype', target, propertyKey);
  console.log(`[design:returntype] ${propertyKey} → ${ret?.name ?? ret}`);
}

class UserService {
  @InspectMethod
  findUser(id: number, name: string): User {
    return { id, name };
  }

  @InspectMethod
  async notify(userId: number, msg: string): Promise<void> {
    console.log(`notify ${userId}: ${msg}`);
  }
}

interface User {
  id: number;
  name: string;
}

// ---------- 4. design:paramtypes（构造函数） ----------
// 类装饰器可以读取构造函数的 paramtypes —— 这是 NestJS DI 的根基
function ShowCtorParams<T extends new (...args: any[]) => any>(Base: T): T {
  const types = Reflect.getMetadata('design:paramtypes', Base);
  console.log(
    `[design:paramtypes] ${Base.name} 构造函数 → ${types?.map((t: any) => t?.name).join(', ') ?? '无'}`,
  );
  return Base;
}

class LoggerService {}
class DatabaseService {}

@ShowCtorParams
class AppService {
  constructor(
    private logger: LoggerService,
    private db: DatabaseService,
    private port: number,
  ) {}
}
// 输出：[design:paramtypes] AppService 构造函数 → LoggerService, DatabaseService, Number
// 这正是 NestJS 容器要的"我该按什么顺序注入哪些 Provider"清单

// ---------- 5. 边界情况：未装饰的目标拿不到元数据 ----------
class NoDecorator {
  name: string = '';
  greet() {}
}
console.log('\n未装饰的属性：', Reflect.getMetadata('design:type', NoDecorator.prototype, 'name'));        // undefined
console.log('未装饰的方法：', Reflect.getMetadata('design:paramtypes', NoDecorator.prototype, 'greet'));   // undefined

// ---------- 6. 自定义 metadata key 的工程化封装 ----------
const META_KEYS = {
  inject: 'di:inject',
  injectable: 'di:injectable',
  route: 'http:route',
  param: 'http:param',
} as const;

// 把字符串 key 集中管理，避免散落魔法字符串，是 NestJS 内部源码的做法
console.log('\n集中管理的 keys：', META_KEYS);

console.log('\n[reflect-metadata-demo.ts] 运行结束');
