/**
 * Day04 - 函数与泛型
 * generic-constraints.ts：extends 约束、keyof 约束、getProperty 经典案例、泛型默认值
 *
 * 运行：npx ts-node generic-constraints.ts
 */
export {};

// ============================================================
// 1. 没有约束的问题：泛型 T 默认可以是任何东西
// ============================================================

// 没有约束时，T 上没有任何已知属性，连 .length 都访问不了
// function badLength<T>(arg: T): number {
//   return arg.length; // ❌ Property 'length' does not exist on type 'T'
// }

// ============================================================
// 2. extends 约束：要求 T 必须有某属性
// ============================================================

// 2.1 约束为"具有 length 属性"
interface HasLength {
  length: number;
}
function logLength<T extends HasLength>(arg: T): number {
  return arg.length; // ✅ T 至少有 length 属性
}

console.log('--- 2. extends 约束 ---');
console.log('logLength("hello") =', logLength('hello')); // 5
console.log('logLength([1,2,3]) =', logLength([1, 2, 3])); // 3
console.log('logLength({ length: 10 }) =', logLength({ length: 10 })); // 10
// logLength(123); // ❌ number 没有 length 属性

// 2.2 约束为"具有特定字段"
interface WithId {
  id: number | string;
}
function findById<T extends WithId>(items: T[], id: number | string): T | undefined {
  return items.find((it) => it.id === id);
}

const users = [
  { id: 1, name: 'Alice' },
  { id: 2, name: 'Bob' },
  { id: 3, name: 'Carol' },
];
const found = findById(users, 2);
console.log('findById(users, 2) =', found);

// ============================================================
// 3. 约束为特定类型（基类约束）
// ============================================================

// 约束 T 必须是 number 或 string 的子类型
function sumOrConcat<T extends number | string>(a: T, b: T): number | string {
  if (typeof a === 'number' && typeof b === 'number') {
    return a + b;
  }
  return String(a) + String(b);
}

console.log('\n--- 3. 约束为特定类型 ---');
console.log('sumOrConcat(1, 2) =', sumOrConcat(1, 2)); // 3
console.log("sumOrConcat('a', 'b') =", sumOrConcat('a', 'b')); // 'ab'

// ============================================================
// 4. keyof 约束：getProperty 经典案例
// ============================================================

// 4.1 keyof 操作符：取出对象类型的所有键的联合类型
type User = { id: number; name: string; email: string };
type UserKey = keyof User; // 'id' | 'name' | 'email'

// 4.2 经典签名：getProperty<T, K extends keyof T>
//   含义：K 必须是 T 的某个键，返回 T[K] 即该键对应的值类型
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user: User = { id: 1, name: 'Alice', email: 'alice@x.com' };
const userId = getProperty(user, 'id'); // 类型推断为 number
const userName = getProperty(user, 'name'); // 类型推断为 string
const userEmail = getProperty(user, 'email'); // 类型推断为 string
// getProperty(user, 'phone'); // ❌ 'phone' 不是 User 的键

console.log('\n--- 4. getProperty 经典案例 ---');
console.log("getProperty(user, 'id') =", userId);
console.log("getProperty(user, 'name') =", userName);
console.log("getProperty(user, 'email') =", userEmail);

// 4.3 应用：类型安全的对象遍历
function pick<T, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> {
  const result = {} as Pick<T, K>;
  keys.forEach((k) => {
    result[k] = obj[k];
  });
  return result;
}

const picked = pick(user, ['id', 'name']);
// picked 类型：{ id: number; name: string }
console.log('pick(user, ["id","name"]) =', picked);

// ============================================================
// 5. keyof + 索引类型：动态访问属性
// ============================================================

// 索引访问类型 T[K] 是 keyof 约束的"另一半"
interface Product {
  sku: string;
  price: number;
  tags: string[];
}

function getField<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const product: Product = { sku: 'A001', price: 99.9, tags: ['new', 'hot'] };
const price: number = getField(product, 'price');
const tags: string[] = getField(product, 'tags');
console.log('\n--- 5. 索引访问类型 T[K] ---');
console.log('price =', price);
console.log('tags =', tags);

// ============================================================
// 6. 泛型默认值 <T = string>
// ============================================================

// 默认类型参数：调用时未指定则用默认
interface Box<T = string> {
  value: T;
}

const strBox: Box = { value: 'hello' }; // T 默认 string
const numBox: Box<number> = { value: 42 }; // 显式 number

// 默认值还可以引用前面的类型参数
interface KVPair<K = string, V = unknown> {
  key: K;
  value: V;
}

const defaultKV: KVPair = { key: 'name', value: 'Alice' }; // K=string, V=unknown
const numKV: KVPair<number, number> = { key: 1, value: 100 };
// 注意：默认值参数引用前面参数时要写在后面
// interface Bad<V, K = V> {}  // ✅ K 默认为 V

console.log('\n--- 6. 泛型默认值 ---');
console.log('strBox =', strBox);
console.log('numBox =', numBox);
console.log('defaultKV =', defaultKV);
console.log('numKV =', numKV);

// ============================================================
// 7. 多层约束：T 既要有 length 又要是 object
// ============================================================

// 使用交叉类型组合多个约束
type StringLike = HasLength & {
  toString(): string;
};

function stringify<T extends StringLike>(value: T): string {
  return `[len=${value.length}] ${value.toString()}`;
}

console.log('\n--- 7. 多层约束 ---');
console.log('stringify("hello") =', stringify('hello'));
console.log('stringify([1,2,3]) =', stringify([1, 2, 3]));

// ============================================================
// 8. Class Type 约束：new (...args) => T
// ============================================================

// 经典工厂模式：传入一个类，实例化它
function instantiate<T>(Ctor: new () => T): T {
  return new Ctor();
}

class Logger {
  log(msg: string) {
    console.log('[Logger]', msg);
  }
}

class Timer {
  start = Date.now();
  elapsed() {
    return Date.now() - this.start;
  }
}

const logger = instantiate(Logger);
const timer = instantiate(Timer);

console.log('\n--- 8. Class Type 约束 ---');
logger.log('Hello from generic factory');
console.log('timer.elapsed() =', timer.elapsed(), 'ms');

// ============================================================
// 9. 条件类型中的泛型（为 Day08 铺垫）
// ============================================================

// 条件类型语法：T extends U ? X : Y
// 这是 TS 类型层面的"if-else"，依赖泛型参数

type IsString<T> = T extends string ? true : false;

type A1 = IsString<string>; // true
type A2 = IsString<number>; // false
type A3 = IsString<'hello'>; // true（字面量是 string 的子类型）

// infer 关键字：在条件类型中"提取"类型参数
type ElementType<T> = T extends (infer E)[] ? E : never;

type E1 = ElementType<string[]>; // string
type E2 = ElementType<number[]>; // number

// ReturnType：提取函数返回类型（标准库内置）
type ReturnOf<F> = F extends (...args: never[]) => infer R ? R : never;
type R1 = ReturnOf<() => number>; // number
type R2 = ReturnOf<(x: string) => boolean>; // boolean

console.log('\n--- 9. 条件类型中的泛型 ---');
// 条件类型在编译期求值，运行时无法 console.log
// 这里只演示类型定义，类型本身不会出现在运行时
const checkA1: A1 = true;
const checkA2: A2 = false;
console.log('IsString<string> =', checkA1);
console.log('IsString<number> =', checkA2);

const e1: E1 = 'hello';
const e2: E2 = 42;
console.log('ElementType<string[]> =', e1);
console.log('ElementType<number[]> =', e2);

console.log('\n[generic-constraints.ts] 全部示例执行完毕。');
