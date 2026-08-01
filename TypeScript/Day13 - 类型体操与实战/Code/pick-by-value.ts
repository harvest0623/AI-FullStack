/**
 * Day13 - 类型体操实战 02：键的筛选与修饰
 *
 * 本文件实现并演示按“值的类型”操作键的工具类型：
 * 1. PickByValue<T, V>：按值类型挑选键（保留键名 + 类型）
 * 2. KeysOfType<T, V>  ：只取“值为某类型”的键名联合
 * 3. Optional<T, K>    ：把指定键变可选（其余键保持原样）
 *
 * 核心套路：映射类型 + as 重映射 + 条件类型 + never 过滤。
 */

export {};

// ============================================================
// 1. PickByValue<T, V>：按值类型筛选字段
// ============================================================

// 三件套套路：
//  - [K in keyof T]             遍历所有键
//  - as T[K] extends V ? K : never  键重映射：值类型匹配则保留原键名，否则丢弃
//  - T[K]                        值类型保持不变
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};

// 反向：排除值类型为 V 的字段
type OmitByValue<T, V> = {
  [K in keyof T as T[K] extends V ? never : K]: T[K];
};

// 演示模型
interface FormState {
  id: number;
  name: string;
  email: string;
  age: number;
  active: boolean;
  tags: string[];      // 注意：string[] 不 extends string，会被剔除
}

type StringFields = PickByValue<FormState, string>;
// { name: string; email: string }
const sf: StringFields = { name: 'Alice', email: 'a@x.com' };
console.log('[PickByValue] string =>', sf);

type NumberFields = PickByValue<FormState, number>;
// { id: number; age: number }
const nf: NumberFields = { id: 1, age: 28 };
console.log('[PickByValue] number =>', nf);

type NonStringFields = OmitByValue<FormState, string>;
// { id: number; age: number; active: boolean; tags: string[] }
const nsf: NonStringFields = { id: 1, age: 28, active: true, tags: [] };
console.log('[OmitByValue] =>', nsf);

// ⚠️ 常见陷阱：string[] 与 string 的 extends 关系
// string[] extends string  →  false（数组不是字符串）
// string extends string[]  →  false
// 所以 PickByValue<FormState, string> 不会包含 tags


// ============================================================
// 2. KeysOfType<T, V>：找出值为某类型的键名联合
// ============================================================

// 与 PickByValue 的差异：只返回键名联合，不返回对象类型
// 实现：用条件类型 + 分布式（ keyof T 是联合，会自动分发 ）
type KeysOfType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T];

// 工作原理拆解：
//  1. { [K in keyof T]: T[K] extends V ? K : never } 构造一个映射类型，
//     每个键要么保留为字面量 K，要么变为 never
//  2. [keyof T] 索引访问取所有值的联合，never 在联合中自动消失
//  最终得到“满足条件的键名”的联合类型

type StringKeys = KeysOfType<FormState, string>;
// 'name' | 'email'
type NumberKeys = KeysOfType<FormState, number>;
// 'id' | 'age'

// 应用：约束函数参数只能是 string 类型字段
function updateStringField<T, K extends KeysOfType<T, string>>(
  obj: T,
  key: K,
  value: T[K] extends string ? string : never,
): T {
  return { ...obj, [key]: value };
}

const form: FormState = {
  id: 1, name: 'Alice', email: 'a@x.com', age: 28, active: true, tags: ['x'],
};
const updated = updateStringField(form, 'name', 'Bob');
// updateStringField(form, 'id', 999);   // ❌ 'id' 不是 KeysOfType<FormState, string>
// updateStringField(form, 'name', 999); // ❌ value 必须是 string
console.log('[KeysOfType] updated =>', updated);


// ============================================================
// 3. Optional<T, K>：把指定键变可选
// ============================================================

// 思路：用两个映射类型组合
//  - Pick<T, K> 部分变可选（用 -? 不行，得用 +?）
//  - Omit<T, K> 部分保持原样
//  最后用 & 交叉合并
type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// 展开形式（更直观）：
//   Omit<T, K>              → 其余字段保持必填
//   Partial<Pick<T, K>>     → 指定字段变可选
//   &                       → 合并（同名字段交叉，可选性会保留）

interface User {
  id: number;
  name: string;
  email: string;
  avatar: string;
}

// 只让 email 和 avatar 可选
type UserCreate = Optional<User, 'email' | 'avatar'>;
// { id: number; name: string; email?: string; avatar?: string }

const u1: UserCreate = { id: 1, name: 'Alice' };              // ✅ email/avatar 都可省
const u2: UserCreate = { id: 2, name: 'Bob', email: 'b@x.com' };
console.log('[Optional] u1 =>', u1);
console.log('[Optional] u2 =>', u2);

// 进阶：Mandatory<T, K> 反向操作，把可选字段强制变必填
type Mandatory<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>;

interface Item {
  id: number;
  name?: string;       // 默认可选
  desc?: string;
}

type StrictItem = Mandatory<Item, 'name'>;
// { id: number; desc?: string; name: string }
const it: StrictItem = { id: 1, name: 'foo' };
console.log('[Mandatory] =>', it);


// ============================================================
// 4. 综合实战：表单字段分类与动态校验
// ============================================================

interface SignupForm {
  username: string;
  password: string;
  age: number;
  agreeTerms: boolean;
  referralCode?: string;
}

// 需求 1：分别挑出 string / number / boolean 字段，便于按类型批量校验
type StrFields  = PickByValue<SignupForm, string>;
type NumFields  = PickByValue<SignupForm, number>;
type BoolFields = PickByValue<SignupForm, boolean>;

const strCheck: StrFields  = { username: 'u', password: 'p' };
const numCheck: NumFields  = { age: 18 };
const boolCheck: BoolFields = { agreeTerms: true };
console.log('[实战] 按类型分组的字段 =>', { strCheck, numCheck, boolCheck });

// 需求 2：创建用户时 referralCode 必填（已知来源用户）
type SignupWithReferral = Mandatory<SignupForm, 'referralCode'>;
const signup1: SignupWithReferral = {
  username: 'u', password: 'p', age: 18, agreeTerms: true, referralCode: 'ABC',
};
console.log('[实战] 必填 referralCode =>', signup1);

// 需求 3：批量更新时所有字段都可省
type SignupPatch = Optional<SignupForm, keyof SignupForm>;
const patch: SignupPatch = {};   // 全部可省，合法
console.log('[实战] 全字段可选 patch =>', patch);


console.log('\n--- pick-by-value.ts 执行完毕 ---');
