/**
 * Day04 - 函数与泛型
 * generic-basic.ts：泛型函数 identity/first/merge、显式指定 vs 推断、多类型参数
 *
 * 运行：npx ts-node generic-basic.ts
 */
export {};

// ============================================================
// 1. 泛型的动机：没有泛型时只能 any 或重复定义
// ============================================================

// 1.1 不用泛型：any 牺牲类型安全
function unsafeIdentity(arg: any): any {
  return arg;
}
const unsafe = unsafeIdentity('ts');
// unsafe 是 any，编译器不知道有没有 .toUpperCase()
// console.log(unsafe.toUpperCase()); // 运行时才报错

// 1.2 不用泛型：为每个类型重复定义
function numIdentity(arg: number): number {
  return arg;
}
function strIdentity(arg: string): string {
  return arg;
}
// 重复劳动，且无法覆盖未来新增类型

// 1.3 泛型：在类型层面"参数化"
function identity<T>(arg: T): T {
  return arg;
}
// 一个函数，应对所有类型，且保留入参与出参的类型关联

console.log('--- 1. 泛型的动机 ---');
console.log('unsafeIdentity("ts") =', unsafeIdentity('ts'));
console.log('numIdentity(42) =', numIdentity(42));
console.log('identity<string>("ts") =', identity<string>('ts'));

// ============================================================
// 2. 显式指定类型参数 vs 类型推断
// ============================================================

// 2.1 类型推断：编译器从参数推断 T
const inferred = identity(42); // T 推断为 number，inferred 类型为 number
// const wrong: string = inferred; // ❌ 不能把 number 赋给 string

// 2.2 显式指定：在某些场景必须显式
//   - 参数推断不出 T（如 T 只用于返回值）
//   - 推断结果过于具体，需要更宽
const explicit = identity<string>('hello'); // 显式指定 T = string

// 2.3 推断会"取最具体"：当传入字面量时，T 可能被推断为字面量类型
function box<T>(value: T): { value: T } {
  return { value };
}
const boxed = box('ts'); // T 推断为 string，不是 'ts'（除非 const 上下文）

console.log('\n--- 2. 显式指定 vs 类型推断 ---');
console.log('inferred =', inferred);
console.log('explicit =', explicit);
console.log('boxed =', boxed);

// ============================================================
// 3. 多类型参数 <T, U>
// ============================================================

// 3.1 两个独立类型参数
function pair<T, U>(first: T, second: U): [T, U] {
  return [first, second];
}

// 3.2 三类型参数（命名约定 T/U/V）
function triple<T, U, V>(a: T, b: U, c: V): [T, U, V] {
  return [a, b, c];
}

// 3.3 类型参数命名约定
//   T (Type)       —— 第一个类型参数
//   U / V          —— 第二、第三个
//   K (Key)        —— 用于键
//   V (Value)      —— 用于值
//   E (Element)    —— 用于元素
//   R (Return)     —— 用于返回值
//   S / T          —— 用于状态机

function mapEntry<K, V>(key: K, value: V): { key: K; value: V } {
  return { key, value };
}

console.log('\n--- 3. 多类型参数 ---');
console.log('pair(1, "ts") =', pair(1, 'ts'));
console.log('triple(true, 42, "x") =', triple(true, 42, 'x'));
console.log('mapEntry("id", 100) =', mapEntry('id', 100));

// ============================================================
// 4. identity 经典函数
// ============================================================

// identity 是 FP 中最简单的"恒等函数"，常用于占位、默认回调
const identityArrow = <T>(arg: T): T => arg;

// 在 .tsx 文件中箭头函数泛型要写成 <T,> 防止被当作 JSX，
// 但在 .ts 文件中 <T> 即可
console.log('\n--- 4. identity 函数 ---');
console.log('identityArrow(42) =', identityArrow(42));
console.log('identityArrow({ a: 1 }) =', identityArrow({ a: 1 }));

// ============================================================
// 5. first 函数：取数组第一个元素
// ============================================================

function first<T>(arr: T[]): T | undefined {
  return arr[0];
}

const firstNum = first([1, 2, 3]); // 类型推断为 number | undefined
const firstStr = first(['a', 'b']); // string | undefined
const firstEmpty = first<number>([]); // undefined（显式 T = number）

console.log('\n--- 5. first 函数 ---');
console.log('first([1,2,3]) =', firstNum);
console.log("first(['a','b']) =", firstStr);
console.log('first<number>([]) =', firstEmpty);

// ============================================================
// 6. merge 函数：合并两个对象
// ============================================================

// 用泛型 + 交叉类型，保留两个对象的全部字段
function merge<T extends object, U extends object>(a: T, b: U): T & U {
  return { ...a, ...b };
}

const merged = merge({ name: 'Alice' }, { age: 30 });
// merged 类型：{ name: string } & { age: number }，访问 name 和 age 都安全
console.log('\n--- 6. merge 函数 ---');
console.log('merged =', merged);
console.log('merged.name =', merged.name, '| merged.age =', merged.age);

// ============================================================
// 7. 泛型函数作为参数类型
// ============================================================

// 把泛型函数本身作为参数传入
function applyFunc<T>(fn: (arg: T) => T, value: T): T {
  return fn(value);
}

const doubled = applyFunc((x: number) => x * 2, 21);
const repeated = applyFunc((s: string) => s + s, 'ab');

console.log('\n--- 7. 泛型函数作为参数 ---');
console.log('applyFunc double 21 =', doubled); // 42
console.log("applyFunc repeat 'ab' =", repeated); // 'abab'

// ============================================================
// 8. 泛型默认值 <T = string>
// ============================================================

// 默认类型参数：未显式传入 T 时使用默认值
function createContainer<T = string>(value: T): { value: T } {
  return { value };
}

const defaultContainer = createContainer('hello'); // T 默认为 string
const customContainer = createContainer<number>(42); // 显式传入 number

console.log('\n--- 8. 泛型默认值 ---');
console.log('defaultContainer =', defaultContainer);
console.log('customContainer =', customContainer);

// ============================================================
// 9. 泛型数组与只读数组
// ============================================================

function reverse<T>(arr: readonly T[]): T[] {
  // arr 是只读的，无法原地反转；返回新数组
  return [...arr].reverse();
}

const original = [1, 2, 3] as const;
const reversed = reverse(original); // T 推断为 1 | 2 | 3，返回 (1|2|3)[]
console.log('\n--- 9. 泛型只读数组 ---');
console.log('original =', original);
console.log('reversed =', reversed);

console.log('\n[generic-basic.ts] 全部示例执行完毕。');
