/**
 * Day09 - 类装饰器（ClassDecorator）
 *
 * 类装饰器签名：(constructor: T) => T | void
 * - 参数 target：被装饰类本身的构造函数
 * - 返回值：若返回一个新的构造函数，会用它替换原类；返回 void 则保留原类
 *
 * 两种典型用法：
 *   1. 直接修改/扩展原型（不返回新构造函数）
 *   2. 返回一个继承自原类的新构造函数（替换构造函数）
 */

// ---------- 用法 1：在原型上叠加方法（不返回值） ----------
function ApiClass(target: Function) {
  // target 就是被装饰类的构造函数本身
  target.prototype.endpoint = '/api';
  target.prototype.fetchAll = function () {
    console.log(`[GET] ${this.endpoint}`);
  };
}

@ApiClass
class UserService {
  endpoint?: string;
  fetchAll?: () => void;
  constructor(public name: string) {}
}

const svc = new UserService('users');
console.log(svc.name);      // users
svc.fetchAll!();            // [GET] /api
console.log((svc as any).endpoint); // /api

// ---------- 用法 2：返回新构造函数（替换原类） ----------
function Timestamped<T extends new (...args: any[]) => any>(Base: T) {
  return class extends Base {
    createdAt = new Date();
    updatedAt = new Date();

    touch() {
      this.updatedAt = new Date();
    }

    describe() {
      return `创建于 ${this.createdAt.toISOString()}`;
    }
  };
}

@Timestamped
class Article {
  constructor(public title: string) {}
}

const a = new Article('装饰器入门');
console.log(a.title);              // 装饰器入门
console.log(a.describe());         // 创建于 ...
a.touch();
console.log(a.updatedAt.toISOString());

// 注意：@Timestamped 后 a 实际是子类实例
console.log(a instanceof Article); // true（子类继承自 Article）

// ---------- 用法 3：通过继承组合多个类装饰器 ----------
function Sealed(constructor: Function) {
  Object.seal(constructor);
  Object.seal(constructor.prototype);
  console.log(`[Sealed] 已冻结 ${constructor.name}`);
}

function Logged<T extends new (...args: any[]) => any>(Base: T) {
  return class extends Base {
    constructor(...args: any[]) {
      console.log(`[Logged] 实例化 ${Base.name}，参数：${JSON.stringify(args)}`);
      super(...args);
    }
  };
}

// 多个类装饰器：从下到上执行本体（先执行 @Logged，再执行 @Sealed）
@Sealed
@Logged
class Product {
  constructor(public sku: string, public price: number) {}
}

const p = new Product('A-001', 99.9);
console.log(p.sku, p.price);

// ---------- 用法 4：通过元数据"贴标签"（不做行为修改，仅供框架读取） ----------
const CLASS_META = 'class:tag';

function Controller(prefix: string) {
  return function <T extends new (...args: any[]) => any>(Base: T): T {
    Reflect.defineMetadata(CLASS_META, { prefix }, Base);
    return Base; // 返回原类，仅贴元数据
  };
}

@Controller('/users')
class UserController {}

console.log(Reflect.getMetadata(CLASS_META, UserController)); // { prefix: '/users' }

console.log('\n[class-decorator.ts] 运行结束');
