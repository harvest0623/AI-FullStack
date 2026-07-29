// any-unknown-never.ts
// 对比 any / unknown / never 三种特殊类型，演示 unknown 必须收窄、never 的穷尽检查

console.log('===== 1. any：放弃类型检查（不推荐） =====');

// any 关闭类型检查，可任意操作，编译期不报错，但运行时可能崩
let anything: any = 'hello';
anything = 100;           // ✅ OK：any 接受任意值
anything = { a: 1 };      // ✅ OK
// ✅ 编译期不报错（any 屏蔽了类型检查），但运行时 anything 是对象，没有 toUpperCase → 抛错
try {
  anything.toUpperCase();
} catch (e) {
  console.log('any 让编译期通过，但运行时抛错：', (e as Error).message);
}
console.log('any 的当前值：', anything);

// any 的危害：会悄悄「传染」给其他变量
function unsafeProcess(data: any) {
  // 任何类型错误都被 any 屏蔽，调试时找不到问题源头
  return data.foo.bar.baz;
}
console.log('any 传染：', unsafeProcess({ foo: { bar: { baz: '隐患被掩盖' } } }));

console.log('\n===== 2. unknown：安全的 any（推荐） =====');

// unknown 是 any 的安全版：可以接收任意值，但「使用前必须先收窄」
let uncertain: unknown = 'hello';
uncertain = 100;
uncertain = { a: 1 };

// uncertain.toUpperCase(); // ❌ 报错：'uncertain' 是 'unknown' 类型，不能直接调用方法

// 必须先「类型收窄」才能使用
// 方式一：typeof 守卫
if (typeof uncertain === 'string') {
  console.log('unknown 经 typeof 收窄为 string：', uncertain.toUpperCase());
}

// 方式二：instanceof 守卫
class User { constructor(public name: string) {} }
let maybeUser: unknown = new User('Trae');
if (maybeUser instanceof User) {
  console.log('unknown 经 instanceof 收窄为 User：', maybeUser.name);
}

// 方式三：类型断言（需谨慎，本质是开发者负责）
const asserted = (uncertain as string).length;
console.log('unknown 通过断言使用：', asserted);

console.log('\n===== 3. any vs unknown 安全性深度对比 =====');

// 3.1 把 unknown 赋给具体类型 → 报错（强制收窄，安全）
let u: unknown = 'x';
// const s: string = u; // ❌ 报错：不能将类型 "unknown" 分配给类型 "string"

// 把 any 赋给具体类型 → 不报错（隐患悄悄引入）
let a: any = 'x';
const s2: string = a;   // ✅ OK（危险：编译期通过，运行时若 a 不是 string 会出错）
console.log('any 静默赋值给 string：', s2);

// unknown 必须先收窄，才能真正进入「具体类型」的世界
const s3: string = typeof u === 'string' ? u : '';
console.log('unknown 收窄后才能赋值给 string：', s3);

// 3.2 在函数签名中：unknown 强制调用方收窄
function safeParse(value: unknown): string {
  // 调用方传入 unknown，函数内部必须先收窄
  if (typeof value === 'string') return value;
  return String(value);
}
console.log('safeParse("hi")：', safeParse('hi'));
console.log('safeParse(123)：', safeParse(123));

console.log('\n===== 4. never：永不出现的值 =====');

// 4.1 函数永不返回（抛错 / 无限循环），返回类型为 never
function throwError(msg: string): never {
  throw new Error(msg);
}

function infiniteLoop(): never {
  while (true) {}
}

// 4.2 never 可赋给任何类型（因为它永远不会出现）
//   但任何值都不能赋给 never（除了 never 自身）
// const n: never = 1; // ❌ 报错：不能将类型 "1" 分配给类型 "never"

// 演示：throw 表达式的类型是 never，因此可赋给任意类型（编译期通过，运行时仍会抛错）
try {
  const unreachable: string = throwError('boom'); // ✅ 编译期 OK：never 可赋给 string
  console.log('这行永远不会执行：', unreachable);
} catch (e) {
  console.log('throwError 运行时抛错（符合预期）：', (e as Error).message);
}
console.log('结论：never 可赋给任意类型（编译期通过）');

// 4.3 never 用于穷尽检查（exhaustive check）—— 这是 never 最实用的场景
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'square'; size: number }
  | { kind: 'triangle'; base: number; height: number };

function area(s: Shape): number {
  switch (s.kind) {
    case 'circle':
      return Math.PI * s.radius ** 2;
    case 'square':
      return s.size ** 2;
    case 'triangle':
      return 0.5 * s.base * s.height;
    default:
      // 若新增 type 成员却没在 switch 中处理，s 会被推断为「该成员类型」而非 never
      // 此时 `const _exhaustive: never = s;` 会报错，强制开发者补全分支
      const _exhaustive: never = s;
      return _exhaustive;
  }
}

console.log('area(circle, r=2)：', area({ kind: 'circle', radius: 2 }).toFixed(2));
console.log('area(square, s=3)：', area({ kind: 'square', size: 3 }));
console.log('area(triangle, b=4, h=5)：', area({ kind: 'triangle', base: 4, height: 5 }));

console.log('\n===== 5. void：无返回值 =====');

// void 表示函数不返回任何值（注意：与 undefined 不同，void 表达「调用方不应使用返回值」）
function logMessage(msg: string): void {
  console.log('[log]', msg);
  // 不需要 return，或 return; / return undefined; 都行
}
logMessage('void 表示调用方不应使用返回值');

console.log('\n===== 6. object：非原始值 =====');

// object 表示「非原始类型」，即除 string/number/boolean/symbol/bigint/null/undefined 之外的类型
function createObject(obj: object): void {
  console.log('接收对象：', Object.keys(obj));
}
createObject({ a: 1 });
createObject([1, 2, 3]);
createObject(new Map());
// createObject('str');   // ❌ 报错：string 是原始类型
// createObject(100);     // ❌ 报错：number 是原始类型

// 注意：object 与 {} 不同，{} 表示「非 null 非 undefined 的任意值」，更宽松
const emptyObj: {} = 'str'; // ✅ OK：{} 接受任何非 null/undefined 值
console.log('{} 类型接受字符串：', emptyObj);
