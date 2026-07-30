/**
 * Day07 - 类型推断（Type Inference）
 *
 * 本文件演示：
 * 1. let / const 推断的差异
 * 2. 数组推断：同类型元素、混合元素、空数组、as const 元组
 * 3. 对象字面量与解构推断
 * 4. 上下文类型 contextual typing：函数参数根据调用位置推断
 * 5. 函数返回值推断（结合控制流收窄）
 */

export {};   // 将本文件标记为模块，避免与其他示例文件的顶层声明冲突

// ============================================================
// 1. let 推断宽类型，const 推断字面量类型
// ============================================================

console.log('--- let vs const 推断 ---');

// let：可重新赋值 -> 推断宽类型
let n = 1;          // number
let s = 'hi';       // string
let b = true;       // boolean

// const：不可变 -> 推断字面量类型
const nc = 1;       // 1   （字面量）
const sc = 'hi';    // 'hi'
const bc = true;    // true

console.log('let n = 1     =>', typeof n, n);     // number 1
console.log('const nc = 1  =>', typeof nc, nc);   // number 1（运行时仍是 number，类型层面是字面量 1）

// const 对象的属性仍可变
const obj = { x: 1 };      // { x: number }
obj.x = 2;                 // ✅ 合法
console.log('const obj 的属性可变 =>', obj);   // { x: 2 }

// const 数组元素仍可变
const arr = [1, 2, 3];     // number[]
arr.push(4);               // ✅ 合法
console.log('const arr 可 push =>', arr);     // [1, 2, 3, 4]


// ============================================================
// 2. 数组推断
// ============================================================

console.log('\n--- 数组推断 ---');

// 同类型元素 -> T[]
const nums = [1, 2, 3];                       // number[]
console.log('nums         =>', nums);

// 混合类型 -> 联合元素数组
const mixed = [1, 'two', true];               // (number | string | boolean)[]
console.log('mixed        =>', mixed);

// 空数组 -> any[]，建议显式标注！
const empty: number[] = [];                   // 显式约束为 number[]
empty.push(1);
console.log('empty        =>', empty);

// as const 让数组推断为只读元组
const pair = [1, 'two'] as const;             // readonly [1, 'two']
console.log('pair (元组)  =>', pair);
// pair.push(3);   // ❌ readonly 元组没有 push


// ============================================================
// 3. 对象字面量与解构推断
// ============================================================

console.log('\n--- 对象与解构推断 ---');

const user = {
  id: 1,
  name: 'Alice',
  roles: ['admin', 'user'],
  meta: { created: Date.now() },
};
// 推断：{ id: number; name: string; roles: string[]; meta: { created: number } }

// 解构出独立变量
const { id, name } = user;
console.log('解构 id   =>', id, typeof id);    // 1 number
console.log('解构 name =>', name, typeof name); // Alice string

// 解构 + 默认值
const { age = 18 } = user as { age?: number };
console.log('解构带默认值 =>', age);            // 18

// 数组解构
const [first, ...rest] = [10, 20, 30];
console.log('数组解构 first =>', first);        // 10
console.log('数组解构 rest  =>', rest);         // [20, 30]

// 重命名解构
const { name: userName = 'anonymous' } = user;
console.log('重命名解构 =>', userName);          // Alice


// ============================================================
// 4. 上下文类型 contextual typing
// ============================================================

console.log('\n--- 上下文类型 ---');

// 4.1 数组方法回调：参数类型由数组元素类型决定
const names: string[] = ['Alice', 'Bob', 'Carol'];
const upper = names.map((s) => s.toUpperCase());   // s 自动推断为 string
console.log('map 推断 s   =>', upper);              // ['ALICE', 'BOB', 'CAROL']

// 4.2 forEach 回调：第二个参数 index 自动推断为 number
names.forEach((s, i) => {
  console.log(`  forEach 上下文 => [${i}] ${s}`);
});

// 4.3 Promise.then：value 类型由 Promise<T> 决定
Promise.resolve(42).then((value) => {
  // value 自动推断为 number
  console.log('Promise 上下文 => value =', value, '| value * 2 =', value * 2);
});

// 4.4 函数类型注解触发上下文类型
type Formatter = (x: number) => string;
const fmt: Formatter = (x) => `数值：${x.toFixed(2)}`;   // x 自动推断为 number
console.log('函数类型注解触发 =>', fmt(3.14159));

// 4.5 事件处理器上下文（DOM 示例）
// 在 Node 环境下 document 不存在，这里用类型模拟
type ClickHandler = (e: { target: HTMLElement; type: string }) => void;
const onClick: ClickHandler = (e) => {
  // e 自动推断为 { target: HTMLElement; type: string }
  console.log('事件处理器上下文 =>', e.type, 'on', e.target.tagName);
};
onClick({ target: { tagName: 'BUTTON' } as HTMLElement, type: 'click' });


// ============================================================
// 5. 函数返回值推断（结合控制流收窄）
// ============================================================

console.log('\n--- 函数返回值推断 ---');

// 返回值类型由 return 表达式推出
function add(a: number, b: number) {
  return a + b;     // 返回 number
}
console.log('add 返回类型推断 =>', add(1, 2));

// 不同分支返回不同类型 -> 推断为联合类型
function describe(x: string | number) {
  if (typeof x === 'string') {
    return `S:${x}`;     // string
  }
  return x.toFixed(0);   // string
  // 推断返回类型：string
}
console.log('describe 返回类型 =>', describe('hi'), describe(3.14));

// 多分支返回不同类型时
function classify(x: number | null) {
  if (x === null) return 'empty';   // string
  if (x > 0)     return x;          // number
  return false;                      // boolean
  // 推断返回类型：string | number | boolean
}
console.log('classify 返回联合 =>', classify(null), classify(5), classify(-1));


// ============================================================
// 6. 推断的反模式
// ============================================================

console.log('\n--- 推断的反模式（需显式标注）---');

// ❌ 反模式：依赖推断漏出 any
// function f(x) { return x.toFixed(2); }   // noImplicitAny 下会报错

// ❌ 反模式：混合数组推断成联合，map 时报错
const list = [1, '2', 3];              // (number | string)[]
// list.map(x => x * 2);               // ❌ string 不能 * 2
list.forEach((x) => {
  if (typeof x === 'number') {
    console.log('  混合数组收窄后 =>', x * 2);
  } else {
    console.log('  字符串分支 =>', x);
  }
});

// ✅ 正确：拆分类型或显式约束
const numsOnly: number[] = [1, 2, 3];
const doubled = numsOnly.map((x) => x * 2);
console.log('显式标注后 map =>', doubled);


console.log('\n--- type-inference.ts 执行完毕 ---');
