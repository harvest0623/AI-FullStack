/**
 * Day04 - 函数与泛型
 * function-types.ts：函数类型注解、可选/默认/剩余参数、this 类型
 *
 * 运行：npx ts-node function-types.ts
 */
export {};

// ============================================================
// 1. 函数类型注解
// ============================================================

// 1.1 函数声明：参数类型 + 返回值类型
function add(a: number, b: number): number {
  return a + b;
}

// 1.2 没有返回值的函数：void
function log(message: string): void {
  console.log(message);
  // return undefined; // void 允许显式 return undefined，但通常省略
}

// 1.3 永不返回的函数：never
function throwError(message: string): never {
  throw new Error(message);
}

function infiniteLoop(): never {
  while (true) {}
}

// 1.4 函数类型字面量（描述"函数本身的形状"）
type MathOp = (a: number, b: number) => number;

const multiply: MathOp = (a, b) => a * b; // 参数类型由 MathOp 推断
const subtract: MathOp = function (a, b) {
  return a - b;
};

// 1.5 箭头函数类型注解
//   完整写法：(参数: 类型): 返回值类型 => 表达式
const square = (x: number): number => x * x;

// 1.6 用 interface 描述函数类型（少见但合法）
interface StringFormatter {
  (input: string): string;
}
const toUpper: StringFormatter = (s) => s.toUpperCase();

console.log('--- 1. 函数类型注解 ---');
console.log('add(1, 2) =', add(1, 2));
console.log('multiply(3, 4) =', multiply(3, 4));
console.log('square(5) =', square(5));
console.log('toUpper("ts") =', toUpper('ts'));

// ============================================================
// 2. 可选参数 ?
// ============================================================

// 2.1 可选参数必须放在必填参数之后
function greet(name: string, greeting?: string): string {
  return `${greeting ?? 'Hello'}, ${name}!`;
}

// 2.2 可选参数的类型实际上是 string | undefined
function describe(opt?: string): string {
  // opt 在此处类型为 string | undefined
  return opt === undefined ? '(empty)' : opt;
}

console.log('\n--- 2. 可选参数 ---');
console.log(greet('TypeScript')); // Hello, TypeScript!
console.log(greet('TS', 'Hi')); // Hi, TS!
console.log('describe() =', describe());

// ============================================================
// 3. 默认值 & 默认值与可选的关系
// ============================================================

// 3.1 默认值
function welcome(name: string, prefix: string = 'Mr.'): string {
  return `Welcome, ${prefix} ${name}`;
}

// 3.2 有默认值的参数可以省略类型注解（推断为字面量类型 + undefined 后被收窄）
//   注意：默认值参数即使省略 ?，调用时也可不传，行为等价于可选参数
function createPoint(x = 0, y = 0): [number, number] {
  return [x, y];
}

// 3.3 默认值参数的类型注解：通常省略，让 TS 从默认值推断
//   下面 country 推断为 string（默认 'CN'）
function buildUser(name: string, country = 'CN') {
  return { name, country };
}

// 3.4 默认值 + 显式类型注解（当默认值与目标类型不一致时必须显式）
function parseId(id: string, base: number = 10): number {
  return parseInt(id, base);
}

console.log('\n--- 3. 默认值 ---');
console.log(welcome('Smith')); // Welcome, Mr. Smith
console.log(welcome('Jones', 'Dr.')); // Welcome, Dr. Jones
console.log('createPoint() =', createPoint()); // [0, 0]
console.log('buildUser("Alice") =', buildUser('Alice'));
console.log('parseId("ff", 16) =', parseId('ff', 16)); // 255

// ============================================================
// 4. 剩余参数 ...rest: T[]
// ============================================================

// 4.1 数值型剩余参数
function sum(...nums: number[]): number {
  return nums.reduce((acc, n) => acc + n, 0);
}

// 4.2 字符串型剩余参数
function joinStrs(separator: string, ...parts: string[]): string {
  return parts.join(separator);
}

// 4.3 剩余参数与元组类型：把多个具体类型作为剩余参数
function invoke<T1, T2>(fn: (a: T1, b: T2) => void, ...args: [T1, T2]): void {
  fn(args[0], args[1]);
}

console.log('\n--- 4. 剩余参数 ---');
console.log('sum(1, 2, 3, 4) =', sum(1, 2, 3, 4));
console.log('joinStrs("-", "a", "b", "c") =', joinStrs('-', 'a', 'b', 'c'));
invoke((a: number, b: string) => console.log('invoke:', a, b), 42, 'ts');

// ============================================================
// 5. this 类型
// ============================================================

// 5.1 noImplicitThis 场景：未注解的 this 默认为 any，strict 模式下会报错
//   解决方式：显式声明 this 参数（必须是第一个参数，且不参与调用）

interface Person {
  name: string;
  age: number;
}

const person = { name: 'Alice', age: 30 };

// 显式 this 参数：调用时不需要传 this，由调用对象自动填充
function describeSelf(this: Person, prefix: string): string {
  return `${prefix}: ${this.name}, ${this.age} years old`;
}

// 调用必须用 .call() 或作为对象方法
console.log('\n--- 5. this 类型 ---');
console.log(describeSelf.call(person, 'Info')); // Info: Alice, 30 years old

// 5.2 把函数挂到对象上作为方法
const obj = { name: 'Bob', age: 25, describeSelf };
obj.describeSelf('Profile'); // OK：this 被推断为 obj

// 5.3 this: void 表示"此函数不会通过 this 访问上下文"
//   常用于自由函数（顶层函数）显式声明不依赖 this
function freeFunction(this: void, x: number): number {
  return x * 2;
}
console.log('freeFunction(5) =', freeFunction(5));

// 5.4 ThisType<T> 工具：标记对象字面量的 this 类型
//   仅在 strict 模式或 noImplicitThis 开启时生效
type CounterStore = {
  count: number;
  increment(): void;
  decrement(): void;
  reset(): void;
};

// ThisType 不产生属性，只影响对象内方法的 this 推断
const counter: CounterStore & ThisType<{ count: number }> = {
  count: 0,
  increment() {
    this.count++; // 此处 this 被推断为 { count: number }
  },
  decrement() {
    this.count--;
  },
  reset() {
    this.count = 0;
  },
};

counter.increment();
counter.increment();
counter.decrement();
console.log('counter.count after ops =', counter.count); // 1

console.log('\n[function-types.ts] 全部示例执行完毕。');
