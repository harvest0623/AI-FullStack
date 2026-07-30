/**
 * Day07 - 类型拓宽（Widening）与 as const 收窄
 *
 * 本文件演示：
 * 1. 字面量在 let 上拓宽为基础类型
 * 2. null / undefined 在 let 上拓宽为 any
 * 3. 对象属性的拓宽
 * 4. as const 让推断保持最窄字面量类型 + readonly
 * 5. as const 在联合枚举中的实际应用
 */

export {};   // 将本文件标记为模块，避免与其他示例文件的顶层声明冲突

// ============================================================
// 1. 字面量在 let 上拓宽
// ============================================================

console.log('--- 字面量拓宽 ---');

// 字面量赋值给 let -> 拓宽为基础类型
let n = 1;          // number（不是 1）
let s = 'hello';    // string（不是 'hello'）
let b = true;       // boolean（不是 true）

// 拓宽后可以重新赋值为同类其他值
n = 100;            // ✅
s = 'world';        // ✅
b = false;           // ✅
console.log('拓宽后可重新赋值 =>', n, s, b);

// const 不拓宽
const nc = 1;       // 1   （字面量类型）
const sc = 'hello'; // 'hello'
// nc = 100;        // ❌ const 不可重新赋值


// ============================================================
// 2. null / undefined 在 let 上拓宽为 any
// ============================================================

console.log('\n--- null / undefined 拓宽 ---');

// ⚠️ 陷阱：let x = null 推断为 any
let x = null;       // any   —— null 被拓宽
x = 1;              // ✅ 没报错（x 是 any）
x = 'oops';         // ✅ 也没报错（x 是 any）
x = { foo: 'bar' }; // ✅ 仍然没报错
console.log('let x = null 拓宽为 any =>', x);

// 这种“无声的 any”是类型安全的漏洞，应该显式标注：
let safeValue: number | null = null;
// safeValue = 'oops';     // ❌ 编译报错
safeValue = 42;             // ✅
console.log('显式标注后安全 =>', safeValue);

// const 保持 null
const y = null;     // null   —— const 不拓宽
// y = 1;            // ❌


// ============================================================
// 3. 对象属性也会拓宽
// ============================================================

console.log('\n--- 对象属性拓宽 ---');

const obj = {
  count: 0,         // number（字面量 0 拓宽）
  label: 'demo',    // string（字面量 'demo' 拓宽）
};
// 推断：{ count: number; label: string }

obj.count = 100;    // ✅ 属性类型是 number
obj.label = 'hi';   // ✅
console.log('对象属性可改值 =>', obj);

// 注意：const 只锁 obj 本身的绑定，不锁内部属性
// obj = { count: 1, label: 'x' };   // ❌ const 不可重新赋值
// 但 obj.count = ... 是合法的


// ============================================================
// 4. as const：让推断保持最窄字面量类型 + readonly
// ============================================================

console.log('\n--- as const 收窄 ---');

const cfg = {
  host: 'localhost',     // 拓宽为 string
  port: 3000,            // 拓宽为 number
  mode: 'production',    // 拓宽为 string
  features: ['sso'],     // string[]
};
console.log('不加 as const =>', cfg);

const cfgConst = {
  host: 'localhost',
  port: 3000,
  mode: 'production',
  features: ['sso'],
} as const;
// 推断：
// {
//   readonly host: 'localhost';
//   readonly port: 3000;
//   readonly mode: 'production';
//   readonly features: readonly ['sso'];
// }

console.log('加 as const 后 features 是元组 =>', cfgConst.features);
// cfgConst.host = 'x';     // ❌ readonly
// cfgConst.port = 8080;    // ❌ readonly
// cfgConst.features.push('audit');   // ❌ readonly 元组没有 push


// ============================================================
// 5. as const 在联合枚举中的实战
// ============================================================

console.log('\n--- as const 实现联合枚举 ---');

// 用 as const 对象 + 类型提取，等价于字符串枚举
const TaskStatus = {
  Pending:  'pending',
  Running:  'running',
  Done:     'done',
  Failed:   'failed',
} as const;

// 提取值的联合类型
type TaskStatusValue = typeof TaskStatus[keyof typeof TaskStatus];
// 'pending' | 'running' | 'done' | 'failed'

// 提取键的联合类型
type TaskStatusKey = keyof typeof TaskStatus;
// 'Pending' | 'Running' | 'Done' | 'Failed'

function describe(s: TaskStatusValue): string {
  switch (s) {
    case TaskStatus.Pending:  return '待处理';
    case TaskStatus.Running:  return '执行中';
    case TaskStatus.Done:     return '已完成';
    case TaskStatus.Failed:   return '失败';
  }
}

// 用法与字符串枚举几乎一致，但有运行时对象可用
console.log('describe(Pending) =>', describe(TaskStatus.Pending));
console.log('describe(Done)    =>', describe(TaskStatus.Done));
console.log('describe("done")  =>', describe('done'));   // ✅ 字面量 'done' 自动满足联合

// 运行时遍历
console.log('所有状态值 =>', Object.values(TaskStatus));
console.log('所有状态键 =>', Object.keys(TaskStatus) as TaskStatusKey[]);


// ============================================================
// 6. as const 配合数组实现“常量表”
// ============================================================

console.log('\n--- as const 实现常量表 ---');

// 想要一个“键 -> 值”映射，同时类型层面取到所有键的联合
const ERROR_CODES = {
  BadRequest:    400,
  Unauthorized:  401,
  NotFound:      404,
  ServerError:   500,
} as const;

type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];
// 400 | 401 | 404 | 500

function explain(code: ErrorCode): string {
  // 反查名字（as const 对象不会自动反向映射，但可以手写）
  const entry = (Object.entries(ERROR_CODES) as [string, ErrorCode][]).find(
    ([, v]) => v === code,
  );
  return entry ? `${entry[0]}(${entry[1]})` : `未知(${code})`;
}

console.log('explain(404) =>', explain(404));   // NotFound(404)
console.log('explain(500) =>', explain(500));   // ServerError(500)
// explain(200);   // ❌ 200 不在 ErrorCode 联合中


// ============================================================
// 7. widening 小结
// ============================================================

/*
拓宽规则速查：

| 字面量              | 拓宽后类型
|---------------------|------------
| 1 / 2 / 3 ...        | number
| 'hello'              | string
| true / false         | boolean
| null                 | any（strictNullChecks 下仍拓宽为 any）
| undefined            | any（同上）

防止拓宽的方法：
1. 用 const 替代 let                —— 锁定字面量类型
2. 用 as const 断言                 —— 让 let / 对象也保持字面量
3. 显式类型注解                     —— 直接指定想要的类型

何时该警惕拓宽：
- let x = null 时             —— 必然得到 any，应该显式标注
- 对象字面量赋值后属性可变时    —— 若想要不可变，加 as const
- 数组字面量混合字面量时        —— 想要元组而非 T[]，加 as const
*/

console.log('\n--- type-widening.ts 执行完毕 ---');
