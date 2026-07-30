/**
 * Day04 - 函数与泛型
 * function-overload.ts：函数重载完整示例、重载顺序、重载与联合类型的取舍
 *
 * 运行：npx ts-node function-overload.ts
 */
export {};

// ============================================================
// 1. 函数重载：多个签名 + 实现
// ============================================================

// 重载签名 1：传入字符串，返回字符串长度
function format(input: string): number;
// 重载签名 2：传入数字，返回带千分位的字符串
function format(input: number): string;
// 重载签名 3：传入布尔值，返回 0/1
function format(input: boolean): 0 | 1;
// 实现签名（对外不可见，只用于内部实现）
//   实现签名参数必须是所有重载签名的"超集"，且最宽
function format(input: string | number | boolean): number | string | 0 | 1 {
  if (typeof input === 'string') {
    return input.length;
  }
  if (typeof input === 'number') {
    return input.toLocaleString('en-US');
  }
  return input ? 1 : 0;
}

// 调用方只能看到重载签名，看不到实现签名
const r1: number = format('hello'); // 5
const r2: string = format(1234567); // '1,234,567'
const r3: 0 | 1 = format(true); // 1

console.log('--- 1. 基本函数重载 ---');
console.log("format('hello') =", r1);
console.log('format(1234567) =', r2);
console.log('format(true) =', r3);

// ============================================================
// 2. 重载顺序：更具体的签名必须放在前面
// ============================================================

// ✅ 正确顺序：字面量类型在前，宽类型在后
function parse(input: 'true'): true;
function parse(input: 'false'): false;
function parse(input: string): boolean;
function parse(input: string): boolean {
  return input === 'true';
}

console.log('\n--- 2. 重载顺序 ---');
console.log("parse('true') =", parse('true')); // true
console.log("parse('anything') =", parse('anything')); // false

// ❌ 错误顺序示例（如果取消注释会编译失败）：
// function badParse(input: string): boolean;
// function badParse(input: 'true'): true;   // 错误：更具体的签名应在更宽的签名之前
// function badParse(input: string): boolean {
//   return input === 'true';
// }

// ============================================================
// 3. 不同参数数量的重载
// ============================================================

function makeArray(): never[];
function makeArray(length: number): number[];
function makeArray(length: number, fill: string): string[];
function makeArray(length?: number, fill?: string): number[] | string[] {
  if (length === undefined) {
    return [];
  }
  if (fill === undefined) {
    return Array.from({ length }, (_, i) => i);
  }
  return Array.from({ length }, () => fill);
}

console.log('\n--- 3. 不同参数数量的重载 ---');
console.log('makeArray() =', makeArray());
console.log('makeArray(3) =', makeArray(3));
console.log("makeArray(3, 'x') =", makeArray(3, 'x'));

// ============================================================
// 4. 重载 vs 联合类型：何时选哪个
// ============================================================

// 场景 A：返回类型与参数类型有"映射关系" → 用重载
//   例如：传 string 返回 number，传 number 返回 string —— 这种"互换"只能用重载

// ❌ 联合类型做不到的：返回类型随入参类型收窄
//   function badFormat(input: string | number): number | string {
//     return typeof input === 'string' ? input.length : input.toString();
//   }
//   const x: number = badFormat('hi');  // ❌ TS 只知道返回 number | string，无法收窄

// 场景 B：所有入参返回同一种类型 → 用联合类型更简洁
function len(input: string | Array<unknown>): number {
  return input.length;
}

console.log('\n--- 4. 重载 vs 联合类型 ---');
console.log("len('hello') =", len('hello')); // 5
console.log('len([1,2,3]) =', len([1, 2, 3])); // 3

// 场景 C：参数为对象，结构差异较大 → 用重载更清晰
function createUser(name: string): { name: string; role: 'guest' };
function createUser(name: string, role: 'admin' | 'user'): { name: string; role: 'admin' | 'user' };
function createUser(name: string, role?: 'admin' | 'user'): { name: string; role: string } {
  return { name, role: role ?? 'guest' };
}

console.log('createUser("Tom") =', createUser('Tom'));
console.log('createUser("Tom", "admin") =', createUser('Tom', 'admin'));

// ============================================================
// 5. 重载中的 this 类型
// ============================================================

class StringBuilder {
  private parts: string[] = [];

  // 链式调用：每个重载都返回 this，子类调用时也能保留子类类型
  append(s: string): this;
  append(n: number): this;
  append(value: string | number): this {
    this.parts.push(String(value));
    return this;
  }

  build(): string {
    return this.parts.join('');
  }
}

console.log('\n--- 5. 重载中的 this 类型 ---');
const sb = new StringBuilder();
const result = sb.append('Hello').append(' ').append(2024).build();
console.log('StringBuilder result =', result); // 'Hello 2024'

// ============================================================
// 6. 函数类型兼容性：参数数量、返回值兼容
// ============================================================

// 6.1 参数数量：参数少的函数可以赋给参数多的函数类型（"少参数兼容多参数"）
type Handler = (a: number, b: number) => number;
const oneArg: Handler = (a) => a * 2; // ✅ 只用第一个参数，第二参数未使用也兼容
const zeroArg: Handler = () => 0; // ✅ 全部参数都不使用也兼容

console.log('\n--- 6. 函数类型兼容性 ---');
console.log('oneArg(3, 4) =', oneArg(3, 4)); // 6
console.log('zeroArg(3, 4) =', zeroArg(3, 4)); // 0

// 6.2 返回值兼容：返回类型必须是目标类型的子类型
type NumReturner = () => { x: number };
type SubReturner = () => { x: number; y: number }; // 多了 y 字段，是子类型

const subRet: SubReturner = () => ({ x: 1, y: 2 });
const numRet: NumReturner = subRet; // ✅ 子类型可赋给父类型（结构兼容）

console.log('numRet() =', numRet()); // { x: 1, y: 2 }

// 6.3 参数逆变：参数类型必须是目标参数类型的"父类型"（或同类型）
//   注：TS 默认是双变的（bivariant），strictFunctionTypes 开启后才严格逆变
type AnimalHandler = (a: { name: string }) => void;
type DogHandler = (a: { name: string; bark(): void }) => void;
//   以下赋值在 strictFunctionTypes 下会报错，因为 DogHandler 的参数更具体
//   const dh: DogHandler = (a) => {}; const ah: AnimalHandler = dh; // ❌ 严格模式下错误

console.log('\n[function-overload.ts] 全部示例执行完毕。');
