/**
 * Day09 - 方法装饰器（MethodDecorator）
 *
 * 签名：(target, propertyKey, descriptor: TypedPropertyDescriptor<T>) => TypedPropertyDescriptor<T> | void
 * - target：静态方法时为类的构造函数；实例方法时为原型对象（Class.prototype）
 * - propertyKey：方法名（string | symbol）
 * - descriptor：属性描述符，descriptor.value 即方法本身
 * - 返回值：返回新描述符会替换原描述符
 */

// ---------- 工具：复用原方法做切面 ----------
function Log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`[Log] 调用 ${propertyKey}，参数：${JSON.stringify(args)}`);
    const start = Date.now();
    const result = original.apply(this, args);
    const cost = Date.now() - start;
    console.log(`[Log] ${propertyKey} 返回：${JSON.stringify(result)}，耗时 ${cost}ms`);
    return result;
  };
}

class Calculator {
  @Log
  add(a: number, b: number): number {
    return a + b;
  }

  @Log
  async fetchData(url: string): Promise<string> {
    return `data-from-${url}`;
  }
}

const c = new Calculator();
c.add(1, 2);
c.fetchData('/api/x').then((r) => console.log('最终：', r));

// ---------- 修改 descriptor：把方法只读化 ----------
function ReadOnly(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  descriptor.writable = false;
  console.log(`[ReadOnly] ${propertyKey} 已不可重写`);
}

class Config {
  @ReadOnly
  env() {
    return 'production';
  }
}

const cfg = new Config();
// 在严格模式下，下面的赋值会抛错：
// (cfg as any).env = () => 'dev';   // TypeError: Cannot assign to read only property 'env'
console.log(cfg.env());

// ---------- 返回新描述符替换原描述符 ----------
function Once(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  const cache = new WeakMap<object, any>();

  // 返回新的 descriptor 替换原来的
  return {
    ...descriptor,
    value: function (this: any, ...args: any[]) {
      if (cache.has(this)) {
        console.log(`[Once] 命中缓存 ${propertyKey}`);
        return cache.get(this);
      }
      const result = original.apply(this, args);
      cache.set(this, result);
      return result;
    },
  };
}

class HeavyService {
  callCount = 0;

  @Once
  expensive() {
    this.callCount++;
    console.log(`[HeavyService] 真实计算第 ${this.callCount} 次`);
    return Math.random() * 1000;
  }
}

const h = new HeavyService();
console.log('第一次：', h.expensive());
console.log('第二次：', h.expensive()); // 命中缓存
console.log('第三次：', h.expensive()); // 命中缓存

// ---------- 静态方法 vs 实例方法的 target ----------
function WhoAreYou(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  // 实例方法：target 是原型对象（Repo.prototype）
  // 静态方法：target 是构造函数本身（Repo）
  console.log(`[WhoAreYou] ${propertyKey} 的 target 是 ${
    target === Repo.prototype ? '原型(实例方法)' : '构造函数(静态方法)'
  }`);
}

class Repo {
  @WhoAreYou
  findOne() {}

  @WhoAreYou
  static create() {}
}

console.log('\n[method-decorator.ts] 运行结束');
