/**
 * Day09 - 装饰器工厂（Decorator Factory）
 *
 * 直接写 @Log 时，Log 本身就是装饰器函数；
 * 写 @RequireRole('admin') 时，RequireRole 是"工厂函数"，它被调用一次，
 * 返回的函数才是真正的装饰器。
 *
 * 工厂签名：(...args) => Decorator
 * 执行时机：工厂在类定义时立即求值，返回的装饰器随即执行。
 */

// ---------- 1. 工厂基本形态：可传参的方法装饰器 ----------
function RequireRole(role: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const original = descriptor.value;
    descriptor.value = function (this: any, currentUser: { role: string }, ...rest: any[]) {
      if (currentUser.role !== role) {
        throw new Error(`[权限] 需要 ${role} 角色，当前为 ${currentUser.role}`);
      }
      return original.apply(this, rest);
    };
  };
}

class OrderService {
  @RequireRole('admin')
  deleteOrder(id: number) {
    console.log(`已删除订单 ${id}`);
    return true;
  }

  @RequireRole('user')
  viewOrder(id: number) {
    console.log(`查看订单 ${id}`);
    return true;
  }
}

const order = new OrderService();
const alice = { role: 'admin' };
const bob = { role: 'user' };

order.deleteOrder.call(order, alice, 1001);  // OK
order.viewOrder.call(order, bob, 1001);       // OK
try {
  order.deleteOrder.call(order, bob, 1001); // 抛错
} catch (e) {
  console.log((e as Error).message);
}

// ---------- 2. 工厂 + 类装饰器：把配置"注入"到类上 ----------
function Defaults(config: Record<string, any>) {
  return function <T extends new (...args: any[]) => any>(Base: T): T {
    return class extends Base {
      config = config;
    };
  };
}

@Defaults({ timeout: 3000, retries: 3 })
class HttpClient {}
const http = new HttpClient() as HttpClient & { config: Record<string, any> };
console.log(http.config); // { timeout: 3000, retries: 3 }

// ---------- 3. 工厂 + 属性装饰器：带参校验 ----------
const RULE_KEY = 'property:rule';

function MaxLength(n: number) {
  return function (target: any, propertyKey: string) {
    Reflect.defineMetadata(RULE_KEY, { max: n }, target, propertyKey);
  };
}

function Min(n: number) {
  return function (target: any, propertyKey: string) {
    // 多次装饰：用 list 累积
    const list: any[] = Reflect.getOwnMetadata(RULE_KEY, target, propertyKey) ?? [];
    list.push({ min: n });
    Reflect.defineMetadata(RULE_KEY, list, target, propertyKey);
  };
}

class ArticleForm {
  @MaxLength(100)
  title: string = '';

  @Min(0)
  @Min(10) // 测试同属性多个装饰器
  views: number = 0;
}

console.log(Reflect.getOwnMetadata(RULE_KEY, ArticleForm.prototype, 'title')); // { max: 100 }
console.log(Reflect.getOwnMetadata(RULE_KEY, ArticleForm.prototype, 'views')); // [{ min: 10 }, { min: 0 }]

// ---------- 4. 多个装饰器工厂并存：求值与执行顺序 ----------
function A(label: string) {
  console.log(`  工厂 A(${label}) 求值`);
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    console.log(`  装饰器 A(${label}) 执行`);
  };
}
function B(label: string) {
  console.log(`  工厂 B(${label}) 求值`);
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    console.log(`  装饰器 B(${label}) 执行`);
  };
}

console.log('\n--- 装饰器求值与执行顺序 ---');
class Demo {
  @A('top')
  @B('bottom')
  hello() {}
}
// 输出顺序：
//   工厂 A(top) 求值
//   工厂 B(bottom) 求值
//   装饰器 B(bottom) 执行
//   装饰器 A(top) 执行
// 即：工厂按书写顺序（自上而下）求值，装饰器本体按自下而上执行（洋葱模型）

// ---------- 5. 通用工厂：根据位置返回不同装饰器 ----------
function Trace(label: string): MethodDecorator & PropertyDecorator & ClassDecorator {
  // 一个工厂可以"伪装"成多种装饰器——因为前几个参数签名是兼容的
  return function (target: any, propertyKey?: string | symbol, descriptor?: PropertyDescriptor) {
    if (propertyKey === undefined) {
      // 类装饰器
      console.log(`[Trace:${label}] 类 ${target.name}`);
    } else if (descriptor === undefined) {
      // 属性装饰器
      console.log(`[Trace:${label}] 属性 ${String(propertyKey)}`);
    } else {
      // 方法装饰器
      console.log(`[Trace:${label}] 方法 ${String(propertyKey)}`);
    }
  } as any;
}

@Trace('class')
class Traced {
  @Trace('property')
  name: string = '';

  @Trace('method')
  hello() {}
}

console.log('\n[decorator-factory.ts] 运行结束');
