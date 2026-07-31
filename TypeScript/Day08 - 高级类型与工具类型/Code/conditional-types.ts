/**
 * Day08 - 条件类型 Conditional Types
 *
 * 本文件演示：
 * 1. 语法 T extends U ? X : Y
 * 2. 分布式条件类型（裸类型参数自动分发）
 * 3. infer 关键字：在条件类型中推断类型变量
 * 4. infer 提取函数返回值 / 参数 / 构造函数实例类型
 * 5. 综合实战
 */

export {};

// ============================================================
// 1. 语法 T extends U ? X : Y
// ============================================================

// 类似 JS 三目运算符，但在“类型空间”求值
type IsString<T> = T extends string ? true : false;

type A1 = IsString<string>;     // true
type A2 = IsString<number>;     // false
type A3 = IsString<'hello'>;    // true（字面量类型也是 string 的子类型）
type A4 = IsString<string | number>;   // boolean（分布式，见下文）

console.log('[基础] IsString =>',
  true as A1, false as A2, true as A3);


// 类型约束 vs 条件类型：
// - T extends U 写在泛型参数里 → “约束”（不通过编译会报错）
// - T extends U ? X : Y 写在类型别名里 → “条件”（返回 true/false 分支）

// 实战：根据入参类型决定返回类型
type Unwrap<T> = T extends Array<infer U> ? U : T;
// 如果是数组，返回元素类型；否则原样返回

type E1 = Unwrap<string[]>;     // string
type E2 = Unwrap<number[]>;     // number
type E3 = Unwrap<string>;       // string（非数组，原样）

console.log('[基础] Unwrap =>', 'elem:', 'x' as E1, '| same:', 'y' as E3);


// 嵌套条件类型：根据不同类型选择不同的转换
type Serialize<T> =
  T extends string ? `string:${T}` :
  T extends number ? `number:${T}` :
  T extends boolean ? `bool:${T}` :
  T extends undefined ? 'undef' :
  `other:${string & T}`;

type S1 = Serialize<'ts'>;          // `string:ts`
type S2 = Serialize<42>;            // `number:42`
type S3 = Serialize<true>;          // `bool:true`
type S4 = Serialize<undefined>;     // 'undef'

console.log('[基础] Serialize =>',
  'string:ts' as S1,
  '| number:42' as S2,
  '| bool:true' as S3,
  '| undef' as S4);


// ============================================================
// 2. 分布式条件类型（distributive conditional types）
// ============================================================

// 关键规则：当条件类型的“被检查类型”是“裸类型参数”时，
// 如果传入的是联合类型，会自动分发到每个成员上分别求值，最后再联合起来

type ToArray<T> = T extends unknown ? T[] : never;

type D1 = ToArray<string | number>;
// 等价于：ToArray<string> | ToArray<number>
//       = string[] | number[]
// 而不是：(string | number)[]

const d1: D1 = ['a', 'b'];     // ✅ 满足 string[]
const d1b: D1 = [1, 2, 3];     // ✅ 满足 number[]
console.log('[分布式] ToArray<string|number> =>',
  JSON.stringify(d1), '|', JSON.stringify(d1b));


// 对比：用方括号包裹阻止分发（非裸类型参数）
type ToArrayNoDistribute<T> = [T] extends [unknown] ? T[] : never;

type D2 = ToArrayNoDistribute<string | number>;
// 不分发，整体求值：(string | number)[]

const d2: D2 = ['a', 1, 'b', 2];   // ✅ 混合元素也合法
console.log('[分布式] ToArrayNoDistribute =>', JSON.stringify(d2));


// 经典应用：从联合中过滤掉某些类型（等价于内置 Exclude<T,U>）
type MyExclude<T, U> = T extends U ? never : T;

type Roles = 'admin' | 'editor' | 'viewer' | 'guest';
type NonGuestRoles = MyExclude<Roles, 'guest'>;
// 分发过程：
//   'admin'  extends 'guest' ? never : 'admin'  → 'admin'
//   'editor' extends 'guest' ? never : 'editor' → 'editor'
//   'viewer' extends 'guest' ? never : 'viewer' → 'viewer'
//   'guest'  extends 'guest' ? never : 'guest'  → never
// 联合结果（never 自动消失）：'admin' | 'editor' | 'viewer'

const r: NonGuestRoles = 'admin';
console.log('[分布式] MyExclude =>', r);


// 经典应用：从联合中提取某些类型（等价于内置 Extract<T,U>）
type MyExtract<T, U> = T extends U ? T : never;

type StringOrNum = string | number | boolean | null;
type OnlyString = MyExtract<StringOrNum, string>;     // string
type OnlyNumOrBool = MyExtract<StringOrNum, number | boolean>;   // number | boolean

const os: OnlyString = 'hello';
const onb: OnlyNumOrBool = 42;
console.log('[分布式] MyExtract =>', os, '|', onb);


// 分发到 never 时直接返回 never（特殊情况）
type ToArrayNever = ToArray<never>;     // never，而不是 never[]
console.log('[分布式] ToArray<never> =>', 'never（不进入分支）');


// ============================================================
// 3. infer 关键字：在条件类型中推断类型变量
// ============================================================

// infer 在 extends 右侧声明一个“待推断的变量”，匹配成功后可在分支里使用

// 3.1 推断数组元素类型
type ElementOf<T> = T extends Array<infer E> ? E : never;

type El1 = ElementOf<string[]>;       // string
type El2 = ElementOf<number[]>;       // number
type El3 = ElementOf<[string, number]>;   // string | number
console.log('[infer] ElementOf =>', 'str:', 'a' as El1, '| num:', 1 as El2);


// 3.2 推断元组第一个/最后一个元素
type FirstOf<T extends readonly unknown[]> =
  T extends readonly [infer F, ...unknown[]] ? F : never;

type LastOf<T extends readonly unknown[]> =
  T extends readonly [...unknown[], infer L] ? L : never;

type Tup = [string, number, boolean];
type F1 = FirstOf<Tup>;    // string
type L1 = LastOf<Tup>;     // boolean
console.log('[infer] First/Last =>', 'first:', 's' as F1, '| last:', true as L1);


// 3.3 推断 Promise 内部值（递归展开嵌套 Promise）
type UnwrapPromise<T> = T extends Promise<infer U> ? UnwrapPromise<U> : T;

type P1 = UnwrapPromise<Promise<number>>;                       // number
type P2 = UnwrapPromise<Promise<Promise<string>>>;              // string
type P3 = UnwrapPromise<Promise<Promise<Promise<boolean>>>>;    // boolean
console.log('[infer] UnwrapPromise =>',
  1 as P1, '|', 's' as P2, '|', true as P3);


// ============================================================
// 4. infer 提取函数返回值 / 参数 / 构造函数实例类型
// ============================================================

// 4.1 提取函数返回值类型（等价于内置 ReturnType<T>）
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

function fetchUser() { return { id: 1, name: 'Alice' }; }
type FetchUserReturn = MyReturnType<typeof fetchUser>;
// { id: number; name: string }

const fr: FetchUserReturn = { id: 1, name: 'Alice' };
console.log('[infer] ReturnType =>', JSON.stringify(fr));


// 4.2 提取函数参数类型（等价于内置 Parameters<T>）
type MyParameters<T> = T extends (...args: infer P) => any ? P : never;

function add(a: number, b: number, c: number = 0): number { return a + b + c; }
type AddParams = MyParameters<typeof add>;
// [a: number, b: number, c?: number]

const ap: AddParams = [1, 2];
console.log('[infer] Parameters =>', JSON.stringify(ap));


// 4.3 提取函数第一个参数类型
type FirstParameter<T> = T extends (first: infer F, ...rest: any[]) => any ? F : never;

function greet(name: string, age: number) { return `${name}(${age})`; }
type GreetFirst = FirstParameter<typeof greet>;   // string
console.log('[infer] FirstParameter =>', 'Alice' as GreetFirst);


// 4.4 提取构造函数的实例类型（等价于内置 InstanceType<T>）
type MyInstanceType<T> = T extends new (...args: any[]) => infer I ? I : never;

class Queue<T> {
  private items: T[] = [];
  push(x: T) { this.items.push(x); }
  pop(): T | undefined { return this.items.shift(); }
}

type QueueInstance = MyInstanceType<typeof Queue>;   // Queue<unknown>

const qi: QueueInstance = new Queue();
qi.push(1);
console.log('[infer] InstanceType =>', 'pop:', qi.pop());

// 注意：上面的 typeof Queue 实际上不能带 <number>，注释行仅为说明


// 4.5 提取构造函数参数类型（等价于内置 ConstructorParameters<T>）
type MyConstructorParams<T> = T extends new (...args: infer P) => any ? P : never;

class Point {
  constructor(public x: number, public y: number, public label?: string) {}
}

type PointCtorParams = MyConstructorParams<typeof Point>;
// [x: number, y: number, label?: string]

const pp: PointCtorParams = [3, 4];
console.log('[infer] ConstructorParameters =>', JSON.stringify(pp), '|', new Point(...pp));


// 4.6 提取 async 函数的返回 Promise 内部类型
type AsyncReturnType<T> = T extends (...args: any[]) => Promise<infer R> ? R : never;

async function loadConfig() {
  return { host: 'localhost', port: 3000 } as const;
}

type ConfigType = AsyncReturnType<typeof loadConfig>;
// { readonly host: 'localhost'; readonly port: 3000 }

const cfg: ConfigType = { host: 'localhost', port: 3000 };
console.log('[infer] AsyncReturnType =>', JSON.stringify(cfg));


// ============================================================
// 5. 综合实战
// ============================================================

// 5.1 类型安全的 Event Emitter
interface EventMap {
  click: { x: number; y: number };
  change: { value: string };
  submit: { formId: string };
}

type EventKey = keyof EventMap;

// on 函数：handler 的参数类型必须严格匹配 EventMap[K]
function on<K extends EventKey>(event: K, handler: (payload: EventMap[K]) => void) {
  console.log(`[实战] 注册事件 ${event}`);
  // 模拟立即触发一次
  if (event === 'click') {
    handler({ x: 10, y: 20 } as EventMap[K]);
  } else if (event === 'change') {
    handler({ value: 'hello' } as EventMap[K]);
  } else if (event === 'submit') {
    handler({ formId: 'F1' } as EventMap[K]);
  }
}

on('click',  (p) => console.log('  click:', p.x, p.y));
on('change', (p) => console.log('  change:', p.value));
on('submit', (p) => console.log('  submit:', p.formId));
// on('click', (p: { value: string }) => {});   // ❌ handler 参数类型不匹配


// 5.2 提取 Promise 链最终值
type AwaitedValue<T> = T extends Promise<infer U>
  ? U extends Promise<unknown>
    ? AwaitedValue<U>
    : U
  : T;

type Chain1 = AwaitedValue<Promise<Promise<Promise<number>>>>;   // number
type Chain2 = AwaitedValue<string>;                             // string
type Chain3 = AwaitedValue<Promise<string[]>>;                  // string[]
console.log('[实战] AwaitedValue =>',
  1 as Chain1, '|', 's' as Chain2, '|', ['a'] as Chain3);


// 5.3 根据类型分派默认值
type DefaultValue<T> =
  T extends string ? '' :
  T extends number ? 0 :
  T extends boolean ? false :
  T extends Array<unknown> ? [] :
  T extends object ? {} :
  null;

function defaultFor<T>(): DefaultValue<T> {
  return null as DefaultValue<T>;
}

const dvStr = defaultFor<string>();         // ''
const dvNum = defaultFor<number>();         // 0
const dvBool = defaultFor<boolean>();       // false
const dvArr = defaultFor<string[]>();       // []
const dvObj = defaultFor<{ a: 1 }>();       // {}
console.log('[实战] DefaultValue =>',
  JSON.stringify(dvStr),
  '|', JSON.stringify(dvNum),
  '|', JSON.stringify(dvBool),
  '|', JSON.stringify(dvArr),
  '|', JSON.stringify(dvObj));


console.log('\n--- conditional-types.ts 执行完毕 ---');
