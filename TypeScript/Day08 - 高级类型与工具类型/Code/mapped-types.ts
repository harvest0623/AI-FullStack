/**
 * Day08 - 映射类型 Mapped Types
 *
 * 本文件演示：
 * 1. 基本语法 [K in keyof T]: ...
 * 2. 修改可选性 +? / -?
 * 3. 修改只读性 +readonly / -readonly
 * 4. 键重映射 as（key remapping via as）
 * 5. 过滤键（用 never 跳过）
 */

export {};

// ============================================================
// 1. 基本语法 [K in keyof T]: ...
// ============================================================

interface User {
  id: number;
  name: string;
  email: string;
  age?: number;
}

// 最简单的映射：保持结构不变（恒等映射）
type Identity<T> = {
  [K in keyof T]: T[K];
};

type IdentityUser = Identity<User>;
// 与 User 完全等价

// 把每个字段的类型包装成 Promise
type Promisified<T> = {
  [K in keyof T]: Promise<T[K]>;
};

type PromisifiedUser = Promisified<User>;
// { id: Promise<number>; name: Promise<string>; email: Promise<string>; age?: Promise<number> }

// 把每个字段的类型包成只读数组
type Arrayified<T> = {
  [K in keyof T]: ReadonlyArray<T[K]>;
};

type ArrayifiedUser = Arrayified<User>;
// { id: readonly number[]; name: readonly string[]; ... }

// 演示：实际使用 Promisified
async function fakeFetchUser(): Promise<PromisifiedUser> {
  return {
    id: Promise.resolve(1),
    name: Promise.resolve('Alice'),
    email: Promise.resolve('a@x.com'),
    age: Promise.resolve(28),
  };
}

fakeFetchUser().then(async (u) => {
  console.log('[基础映射] Promisified =>',
    'id:', await u.id,
    '| name:', await u.name,
    '| email:', await u.email,
    '| age:', await u.age);
});


// ============================================================
// 2. 修改可选性 +? / -?
// ============================================================

// +? ：把所有字段标记为可选（等价于内置 Partial<T>）
type MyPartial<T> = {
  [K in keyof T]?: T[K];       // 等价于 [K in keyof T]+?: T[K]
};

type PartialUser = MyPartial<User>;
// { id?: number; name?: string; email?: string; age?: number }

const patch: PartialUser = { name: 'Bob' };   // 只填一个字段也合法
console.log('[+?] PartialUser patch =>', patch);


// -? ：把所有字段标记为必填（等价于内置 Required<T>）
type MyRequired<T> = {
  [K in keyof T]-?: T[K];
};

type RequiredUser = MyRequired<User>;
// { id: number; name: string; email: string; age: number }  ← age 也变成必填

const full: RequiredUser = { id: 2, name: 'Bob', email: 'b@x.com', age: 30 };
console.log('[-?] RequiredUser =>', full);


// 组合：仅对“原本可选的字段”取必填，保留其他字段原样
type RequiredOptionals<T> = {
  [K in keyof T as {} extends Pick<T, K> ? K : never]-?: T[K];
} & {
  [K in keyof T as {} extends Pick<T, K> ? never : K]: T[K];
};

type UserRequiredOptionals = RequiredOptionals<User>;
// age 变为必填，其余保持原样


// ============================================================
// 3. 修改只读性 +readonly / -readonly
// ============================================================

// +readonly：把所有字段标记为只读（等价于内置 Readonly<T>）
type MyReadonly<T> = {
  readonly [K in keyof T]: T[K];     // 等价于 [+readonly K in keyof T]: T[K]
};

type ReadonlyUser = MyReadonly<User>;

const frozen: ReadonlyUser = { id: 3, name: 'Carol', email: 'c@x.com' };
// frozen.id = 4;   // ❌ 只读
console.log('[+readonly] ReadonlyUser =>', frozen);


// -readonly：去掉所有 readonly 修饰（等价于自定义 Mutable<T>）
type Mutable<T> = {
  -readonly [K in keyof T]: T[K];
};

interface FrozenConfig {
  readonly host: string;
  readonly port: number;
}

type MutableConfig = Mutable<FrozenConfig>;
// { host: string; port: number }  ← 不再 readonly

const cfg: MutableConfig = { host: '0.0.0.0', port: 8080 };
cfg.port = 9090;   // ✅ 可写
console.log('[-readonly] MutableConfig =>', cfg);


// ============================================================
// 4. 键重映射 as（key remapping via as）
// ============================================================

// as 把原键名重写为新字符串。常用于：批量改名、加前缀/后缀、大小写转换

// 4.1 给所有键加前缀 "user_"
type Prefixed<T, P extends string> = {
  [K in keyof T as `${P}${Capitalize<string & K>}`]: T[K];
};

type PrefixedUser = Prefixed<User, 'user'>;
// { userId: number; userName: string; userEmail: string; userAge?: number }

const pu: PrefixedUser = {
  userId: 4,
  userName: 'Dave',
  userEmail: 'd@x.com',
};
console.log('[as 重映射] PrefixedUser =>', pu);


// 4.2 把所有键转小写
type LowercaseKeys<T> = {
  [K in keyof T as Lowercase<string & K>]: T[K];
};

interface PascalCase {
  FirstName: string;
  LastName: string;
}
type CamelCase = LowercaseKeys<PascalCase>;
// { firstname: string; lastname: string }

const cc: CamelCase = { firstname: 'Eve', lastname: 'F' };
console.log('[as 重映射] LowercaseKeys =>', cc);


// 4.3 键不变，但类型转换（如全部包成 getter 函数）
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

type UserGetters = Getters<User>;
// { getId: () => number; getName: () => string; getEmail: () => string; getAge?: () => number }

const ug: UserGetters = {
  getId: () => 5,
  getName: () => 'Frank',
  getEmail: () => 'f@x.com',
  getAge: () => 40,
};
console.log('[as 重映射] Getters =>',
  'id:', ug.getId(),
  '| name:', ug.getName(),
  '| email:', ug.getEmail(),
  '| age:', ug.getAge!());


// 4.4 键重映射 + 类型联合：把同构对象转成“键值对”联合
// 关键：末尾加 [keyof T]，把“每个字段都是 { key, value }”的对象，
// 收拢成“键值对的联合类型”
type KeyValuePair<T> = {
  [K in keyof T]: { key: K; value: T[K] };
}[keyof T];

type UserKeyValue = KeyValuePair<User>;
// { key: 'id'; value: number } | { key: 'name'; value: string } | { key: 'email'; value: string } | { key: 'age'; value: number }

// 用 NonNullable 过滤掉可选字段索引时引入的 undefined
const pairs: NonNullable<UserKeyValue>[] = [
  { key: 'id', value: 1 },
  { key: 'name', value: 'Alice' },
  { key: 'email', value: 'a@x.com' },
];
console.log('[as 重映射] KeyValue =>',
  pairs.map(p => `${p.key}=${JSON.stringify(p.value)}`).join(', '));


// ============================================================
// 5. 过滤键（用 never 跳过）
// ============================================================

// 在 as 子句里返回 never，表示该键被丢弃
// 配合条件类型实现“按键的类型筛选”

// 5.1 只保留 string 类型的字段
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};

interface MixedBag {
  id: number;
  name: string;
  email: string;
  age: number;
  active: boolean;
  tags: string[];
}

type StringFields<T> = PickByValue<T, string>;
// 只有 name / email 满足“字段类型 extends string”

const sf: StringFields<MixedBag> = {
  name: 'Alice',
  email: 'a@x.com',
};
console.log('[过滤键] StringFields =>', sf);

type NumberFields<T> = PickByValue<T, number>;
// 只有 id / age 满足
const nf: NumberFields<MixedBag> = { id: 1, age: 28 };
console.log('[过滤键] NumberFields =>', nf);


// 5.2 只保留“值为函数”的字段（提取方法集合）
type Methods<T> = {
  [K in keyof T as T[K] extends Function ? K : never]: T[K];
};

class Counter {
  count = 0;                       // 属性
  increment(): void { this.count++; }   // 方法
  decrement(): void { this.count--; }   // 方法
  get value(): number { return this.count; }
}

type CounterMethods = Methods<Counter>;
// { increment: () => void; decrement: () => void }   ← 仅方法
const cm: CounterMethods = {
  increment: () => {},
  decrement: () => {},
};
console.log('[过滤键] CounterMethods =>', Object.keys(cm).join(', '));


// 5.3 排除特定键（自定义 Omit 的另一种写法）
type ExcludeKeys<T, K extends keyof any> = {
  [P in keyof T as P extends K ? never : P]: T[P];
};

type UserWithoutPII = ExcludeKeys<User, 'email' | 'age'>;
// { id: number; name: string }

const u: UserWithoutPII = { id: 6, name: 'Grace' };
console.log('[过滤键] ExcludeKeys =>', u);


// 5.4 只保留可选字段（实用模式）
type OptionalKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? K : never;
}[keyof T];

type UserOptionalKeys = OptionalKeys<User>;   // 'age'
console.log('[过滤键] OptionalKeys =>', 'age' as UserOptionalKeys);

type PickOptional<T> = Pick<T, OptionalKeys<T>>;
type UserOptionals = PickOptional<User>;   // { age?: number }
const opt: UserOptionals = { age: 50 };
console.log('[过滤键] PickOptional =>', opt);


console.log('\n--- mapped-types.ts 执行完毕 ---');
