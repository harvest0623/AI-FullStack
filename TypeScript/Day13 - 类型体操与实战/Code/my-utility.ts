/**
 * Day13 - 类型体操实战 03：手写内置工具类型
 *
 * 本文件手写实现 TS 内置的高频工具类型，理解其内部原理：
 * 1. MyPick<T, K>      ：从 T 中挑选指定键
 * 2. MyOmit<T, K>      ：从 T 中排除指定键（两种写法）
 * 3. MyRecord<K, T>    ：构造键为 K、值为 T 的对象
 * 4. MyReturnType<T>   ：提取函数返回值类型
 * 5. MyParameters<T>   ：提取函数参数元组
 * 6. MyAwaited<T>      ：递归展开 Promise（提取最终值）
 * 7. TupleToUnion<T>   ：元组 → 联合
 * 8. UnionToTuple<T>   ：联合 → 元组（TS 限制，仅近似实现）
 *
 * 阅读建议：先看类型签名，再看测试用例验证行为，最后回看实现细节。
 */

export {};

// ============================================================
// 1. MyPick<T, K>：挑选指定键
// ============================================================

// 原理：映射类型遍历“K 中的键”，从 T 中取出对应类型
//  - K extends keyof T   约束 K 只能是 T 的键子集
//  - [P in K]: T[P]      遍历 K，每个键取 T 中的类型
type MyPick<T, K extends keyof T> = {
  [P in K]: T[P];
};

interface User {
  id: number;
  name: string;
  email: string;
  age: number;
}

type UserBrief = MyPick<User, 'id' | 'name'>;
// { id: number; name: string }
const brief: UserBrief = { id: 1, name: 'Alice' };
console.log('[MyPick] =>', brief);

// MyPick 的边界：传入非 T 的键会编译报错
// type Bad = MyPick<User, 'phone'>;   // ❌ 'phone' 不在 keyof User 中


// ============================================================
// 2. MyOmit<T, K>：排除指定键
// ============================================================

// 写法 A：用 as 重映射 + 条件类型过滤键（推荐，最直观）
type MyOmit<T, K extends keyof T> = {
  [P in keyof T as P extends K ? never : P]: T[P];
};

// 写法 B：用 Pick + Exclude 组合（内置 Omit 即采用此实现）
type MyOmitByPick<T, K extends keyof T> = MyPick<T, Exclude<keyof T, K>>;

type UserPublic = MyOmit<User, 'email' | 'age'>;
// { id: number; name: string }
const pub: UserPublic = { id: 1, name: 'Alice' };
console.log('[MyOmit A] =>', pub);

type UserPublicB = MyOmitByPick<User, 'email' | 'age'>;
const pubB: UserPublicB = { id: 1, name: 'Alice' };
console.log('[MyOmit B] =>', pubB);


// ============================================================
// 3. MyRecord<K, T>：构造键值对象
// ============================================================

// 原理：映射类型遍历“键联合 K”，每个键都赋类型 T
//  - K extends string | number | symbol   Record 内置约束
//  - [P in K]: T                          遍历 K，每个键都是 T 类型
type MyRecord<K extends string | number | symbol, T> = {
  [P in K]: T;
};

type Role = 'admin' | 'editor' | 'viewer';
type RolePerms = MyRecord<Role, string[]>;

const perms: RolePerms = {
  admin: ['read', 'write', 'delete'],
  editor: ['read', 'write'],
  viewer: ['read'],
};
console.log('[MyRecord] =>', perms);

// 注意：Record 的“完整性校验”
// const bad: RolePerms = { admin: ['read'] };   // ❌ 缺 editor/viewer
// 完整性来自 K 的联合被 [P in K] 全部展开


// ============================================================
// 4. MyReturnType<T>：提取函数返回值
// ============================================================

// 原理：infer R 写在返回值位置，匹配后取 R
//  - T extends (...args: any[]) => infer R   匹配“任意参数的函数”
//  - ? R : never                              取出返回值类型
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

function loadUser() {
  return { id: 1, name: 'Alice', roles: ['admin'] as const };
}

type LoadedUser = MyReturnType<typeof loadUser>;
// { id: number; name: string; roles: readonly ['admin'] }
const lu: LoadedUser = { id: 1, name: 'Alice', roles: ['admin'] };
console.log('[MyReturnType] =>', lu);


// ============================================================
// 5. MyParameters<T>：提取函数参数元组
// ============================================================

// 原理：infer P 写在 ...args 位置，匹配后取 P（元组类型）
type MyParameters<T> = T extends (...args: infer P) => any ? P : never;

function greet(name: string, age: number, isAdmin: boolean) {
  return `${name}/${age}`;
}

type GreetParams = MyParameters<typeof greet>;
// [name: string, age: number, isAdmin: boolean]
const params: GreetParams = ['Alice', 28, true];
console.log('[MyParameters] =>', params, '| greet =>', greet(...params));


// ============================================================
// 6. MyAwaited<T>：递归展开 Promise
// ============================================================

// 原理：用 infer U 提取 Promise 的值类型，若 U 仍是 Promise 则递归
// 注意 TS 5+ 内置 Awaited 还会处理 thenable，这里简化为仅识别 Promise
type MyAwaited<T> = T extends Promise<infer U>
  ? U extends Promise<unknown>
    ? MyAwaited<U>        // 嵌套 Promise → 继续递归
    : U                   // 已是最终值 → 取出
  : T;                    // 非 Promise → 原样返回

type A1 = MyAwaited<Promise<number>>;                          // number
type A2 = MyAwaited<Promise<Promise<string>>>;                 // string
type A3 = MyAwaited<Promise<Promise<Promise<boolean>>>>;       // boolean
type A4 = MyAwaited<number>;                                   // number

console.log('[MyAwaited] =>',
  0 as A1, '|', '' as A2, '|', true as A3, '|', 0 as A4);

// 实战：从 async 函数反推“最终返回值类型”
async function fetchProfile() {
  return { id: 1, name: 'Alice', avatar: 'a.png' };
}
type Profile = MyAwaited<ReturnType<typeof fetchProfile>>;
const profile: Profile = { id: 1, name: 'Alice', avatar: 'a.png' };
console.log('[MyAwaited 实战] =>', profile);


// ============================================================
// 7. TupleToUnion<T>：元组 → 联合
// ============================================================

// 原理：T[number] 索引访问取元组所有元素类型的联合
type TupleToUnion<T extends readonly unknown[]> = T[number];

const PALETTE = ['red', 'green', 'blue'] as const;
type Palette = TupleToUnion<typeof PALETTE>;
// 'red' | 'green' | 'blue'

const c: Palette = 'red';
// const bad: Palette = 'yellow';   // ❌
console.log('[TupleToUnion] =>', c);

// 数字元组也成立
type Mixed = TupleToUnion<[string, number, boolean]>;
// string | number | boolean
const m: Mixed = 42;
console.log('[TupleToUnion] mixed =>', m);


// ============================================================
// 8. UnionToTuple<T>：联合 → 元组（TS 限制，仅近似）
// ============================================================

// ⚠️ 重要说明：
// TS 类型系统“联合类型是无序的”，不存在官方 API 把联合按确定顺序转为元组。
// 社区 hack 利用“函数参数逆变”可以提取联合的“最后一个成员”，
// 反复套用即可得到一个顺序，但顺序不稳定且实现晦涩，生产环境应避免使用。
//
// 此处给出一种常见 hack 写法作为“了解”用途：

// 步骤 1：取联合的“最后一个成员”
type LastOfUnion<U> =
  UnionToIntersection<U extends unknown ? (x: U) => void : never> extends (x: infer L) => void
    ? L
    : never;

// UnionToIntersection：把联合转交叉（利用函数参数逆变）
type UnionToIntersection<U> =
  (U extends unknown ? (x: U) => void : never) extends (x: infer I) => void
    ? I
    : never;

// 步骤 2：从联合中“弹出”最后一个成员，递归收集成元组
//   Push<Acc, Last> 把 Last 追加到元组末尾
type Push<T extends readonly unknown[], V> = [...T, V];

type UnionToTupleRec<U, Last = LastOfUnion<U>> =
  [U] extends [never]                // 联合已空 → 返回空元组
    ? []
    : Push<UnionToTupleRec<Exclude<U, Last>>, Last>;

// 测试：能转，但顺序不保证（取决于编译器内部实现）
type TupleFromUnion = UnionToTupleRec<'a' | 'b' | 'c'>;
// 可能是 ['a', 'b', 'c'] 也可能是 ['c', 'b', 'a']，顺序不稳定
const tfu: TupleFromUnion = ['c', 'b', 'a'] as unknown as TupleFromUnion;
console.log('[UnionToTuple] (顺序不保证) =>', tfu);

// 工程建议：
//  - 若需要“有序的常量集合 + 联合类型”：直接用 as const 元组，再用 T[number] 反推联合
//  - 切勿依赖 UnionToTuple 的顺序


console.log('\n--- my-utility.ts 执行完毕 ---');
