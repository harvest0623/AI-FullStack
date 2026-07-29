/**
 * Day03 - 函数类型 Function Types
 * 主题：三种写法、调用签名 call signature、构造签名 construct signature
 * 运行：npx ts-node function-types.ts
 */

console.log('=== 1. 函数类型的三种写法 ===\n');

// 写法 1：type 箭头函数语法（最常用）
type Mapper<T, U> = (value: T, index: number) => U;

// 写法 2：interface + 调用签名
interface Reducer<T> {
  (acc: T, current: T): T;
}

// 写法 3：内联函数类型字面量（最常见的函数参数场景）
function run(fn: (x: number) => number, input: number): number {
  return fn(input);
}

const double: Mapper<number, number> = (v) => v * 2;
const sum: Reducer<number> = (acc, cur) => acc + cur;

console.log('[Mapper] double(5,0) =', double(5, 0));
console.log('[Reducer] sum(3,4) =', sum(3, 4));
console.log('[inline] run(x => x + 1, 9) =', run((x) => x + 1, 9));

console.log('\n=== 2. 调用签名 Call Signature（带属性的函数）===\n');

// 当一个函数【本身】还需要挂载属性时（如 jQuery 的 $、可重置的 counter），
// 必须用调用签名——type 箭头语法做不到挂属性
interface Counter {
  (): number;          // 调用签名
  reset(): void;       // 挂载的方法
  count: number;       // 挂载的属性
}

function createCounter(): Counter {
  const counter = function () {
    return ++counter.count;
  } as Counter;
  counter.count = 0;
  counter.reset = () => {
    counter.count = 0;
  };
  return counter;
}

const cnt = createCounter();
console.log('[Counter] 调用1 =', cnt());
console.log('[Counter] 调用2 =', cnt());
console.log('[Counter] 调用3 =', cnt());
console.log('[Counter] count 属性 =', cnt.count);
cnt.reset();
console.log('[Counter] reset 后调用 =', cnt());

console.log('\n=== 3. 构造签名 Construct Signature ===\n');

// 当类型需要被 new 调用（即作为类/构造函数）时，用 new 签名
interface PointCtor {
  new (x: number, y: number): Point2D;
  origin: Point2D;     // 静态属性
}

class Point2D {
  static origin: Point2D = new Point2D(0, 0);
  constructor(public x: number, public y: number) {}
  toString() {
    return `(${this.x}, ${this.y})`;
  }
}

// PointCtor 描述了 Point2D 构造函数的形状
const PCtor: PointCtor = Point2D;
console.log('[Construct] PointCtor.origin =', PCtor.origin.toString());

// 工厂：用构造签名约束"接收一个构造函数并实例化"
function instantiate<C extends new (...args: any[]) => any>(
  ctor: C,
  ...args: any[]
): InstanceType<C> {
  return new ctor(...args);
}

const p = instantiate(Point2D, 10, 20);
console.log('[Construct] instantiate(Point2D, 10, 20) =', p.toString());

console.log('\n=== 4. 调用签名 + 构造签名 共存（jQuery 风格）===\n');

// interface 可同时描述"普通调用"和"new 调用"，
// 这是 type 箭头语法做不到的——常用于 jQuery 风格的 $ 函数
interface Dollar {
  (selector: string): string[];                  // $('div') → 选择器结果
  new (selector: string): { selector: string };  // new $('div') → 包装对象
  ajax(url: string): Promise<string>;            // $.ajax
}

// 最小实现：用 new.target 区分"普通调用"和"new 调用"
function makeDollar(): Dollar {
  const fn: any = function (selector: string) {
    if (new.target) {
      return { selector };
    }
    return [selector, selector];
  };
  fn.ajax = (url: string) => Promise.resolve(`response from ${url}`);
  return fn as Dollar;
}

const $ = makeDollar();
console.log('[Hybrid] $("div") 普通调用 =', $('div'));
console.log('[Hybrid] new $("div") new 调用 =', new $('div'));
$.ajax('https://example.com').then((r) =>
  console.log('[Hybrid] $.ajax() 异步结果 =', r)
);

console.log('\n=== 5. 函数重载签名 ===\n');

// interface / type 都可以描述重载，但实现签名要对所有重载兼容
interface Format {
  (value: number): string;
  (value: Date): string;
}

const format: Format = (value: number | Date) => {
  if (typeof value === 'number') return `num:${value}`;
  return `date:${value.toISOString().slice(0, 10)}`;
};
console.log('[Overload] format(42) =', format(42));
console.log('[Overload] format(new Date()) =', format(new Date()));
