// primitive-types.ts
// 演示 TypeScript 的所有原始类型，以及 let / const 的类型推断差异

console.log('===== 1. 原始类型 =====');

// string 字符串
const username: string = 'trae';
const greeting: string = `Hello, ${username}`;
console.log('string：', username, '| 模板字符串：', greeting);

// number 数字（整数 / 浮点 / 二进制 / 八进制 / 十六进制 统一为 number，没有 int/float 之分）
const age: number = 28;
const pi: number = 3.14159;
const hex: number = 0xff;
const binary: number = 0b1010;
const octal: number = 0o744;
console.log('number：', age, pi, 'hex=', hex, 'binary=', binary, 'octal=', octal);

// boolean 布尔
const isOnline: boolean = true;
const isAdmin: boolean = false;
console.log('boolean：isOnline=', isOnline, 'isAdmin=', isAdmin);

// null 与 undefined（在 strictNullChecks 下需显式声明，否则可隐式赋给其他类型）
const empty: null = null;
const nothing: undefined = undefined;
console.log('null：', empty, '| undefined：', nothing);

// symbol 唯一符号（每次 Symbol() 都返回全新且唯一的值，常用作对象私有键）
const uniqueKey: symbol = Symbol('id');
const anotherKey: symbol = Symbol('id');
console.log('symbol 两次 Symbol("id") 是否相等：', uniqueKey === anotherKey); // false

// bigint 大整数（ES2020+，字面量以 n 结尾，可精确表示超过 Number.MAX_SAFE_INTEGER 的值）
const big: bigint = 9007199254740991n;
const bigger: bigint = 2n ** 64n;
console.log('bigint：MAX_SAFE_INTEGER=', big, '| 2^64=', bigger);

console.log('\n===== 2. let vs const 类型推断差异 =====');

// 2.1 let 推断为「宽类型」
//   let count = 10;     等价于  let count: number = 10;
//   因为变量后续可被重新赋值为任意 number，TS 选择最宽的 number
let count = 10;
count = 20;
count = 99.9;
let message = 'hi';   // 推断为 string（宽类型）
message = 'hello';
console.log('let 推断宽类型 → count=', count, 'message=', message);

// 2.2 const 推断为「字面量类型」
//   因为绑定不可变，TS 把类型精确到具体的字面量值
//   const MAX = 10;     等价于  const MAX: 10     = 10;    （字面量类型 10）
//   const TITLE = 'TS'; 等价于  const TITLE: 'TS' = 'TS';  （字面量类型 'TS'）
//   const FLAG = true;  等价于  const FLAG: true  = true;  （字面量类型 true）
const MAX = 10;
const TITLE = 'TS';
const FLAG = true;
console.log('const 推断字面量类型 → MAX=', MAX, 'TITLE=', TITLE, 'FLAG=', FLAG);

// 2.3 字面量类型可被字面量类型校验
//   下面的函数只接受「字面量类型 10」，能直观看出 let / const 推断差异
function onlyTen(n: 10) {
  console.log('接收字面量类型 10：', n);
}
onlyTen(MAX);       // ✅ OK：MAX 推断为字面量类型 10
// onlyTen(count);  // ❌ 报错：count 推断为 number，不能赋给字面量类型 10

// 2.4 对象属性：const 只锁「绑定」，不锁「内部属性」
//   const 让变量名无法重新赋值，但对象内部属性仍然可变
const config = { port: 3000 };
config.port = 4000;  // ✅ OK：对象内部属性仍可修改
// config = { port: 5000 }; // ❌ 报错：无法重新分配 const 变量
console.log('const 对象内部属性仍可变 → config.port=', config.port);

console.log('\n===== 3. 原始类型的运行时 typeof 行为 =====');

// typeof 在运行时返回字符串，可用于类型守卫（见 type-narrowing.ts）
const samples: unknown[] = ['str', 100, true, null, undefined, Symbol(), 10n];
for (const s of samples) {
  console.log('值=', String(s), '| typeof=', typeof s);
}
