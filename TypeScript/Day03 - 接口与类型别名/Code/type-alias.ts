/**
 * Day03 - type 别名基础演示
 * 主题：type 定义、与 interface 基本等价的场景、type 独有的能力
 * 运行：npx ts-node type-alias.ts
 */

console.log('=== 1. type 定义对象形状（与 interface 表面等价）===\n');

// type 给一个【类型】起名字，可以别名基本类型、联合、对象、函数、元组……
// 描述对象形状时，与 interface 几乎可以互换
type User = {
  id: number;
  name: string;
  email: string;
};

const alice: User = { id: 1, name: 'Alice', email: 'alice@example.com' };
console.log('[type User] alice =', alice);

// 可选、只读 在 type 中写法完全一致
type Article = {
  readonly title: string;
  tags?: string[];
};

const a: Article = { title: 'TS 入门' };
console.log('[type Article] a =', a);

console.log('\n=== 2. type 独有能力：别名基本类型 / 联合 / 元组 ===\n');

// 这些是 interface 做不到的——interface 只能描述"对象/函数形状"
type ID = number | string;        // 联合类型
type Point = [number, number];    // 元组类型
type Callback = (err: Error | null, data?: unknown) => void;  // 函数类型

const id1: ID = 100;
const id2: ID = 'abc-100';
console.log('[type ID] id1 =', id1, ', id2 =', id2);

const p: Point = [10, 20];
console.log('[type Point] p =', p);

const cb: Callback = (err, data) => {
  if (err) console.log('[type Callback] err =', err.message);
  else console.log('[type Callback] data =', data);
};
cb(null, { ok: true });

console.log('\n=== 3. type 的扩展：交叉类型 & ===\n');

// interface 用 extends 扩展，type 用 & 做交叉
type Timestamps = {
  createdAt: Date;
  updatedAt: Date;
};

type Note = {
  title: string;
  content: string;
} & Timestamps;   // 把 Timestamps 的字段"合并"进 Note

const note: Note = {
  title: '日记',
  content: '今天学了 type 别名',
  createdAt: new Date(),
  updatedAt: new Date(),
};
console.log('[type Note & Timestamps] note =', note);

console.log('\n=== 4. type 与 interface 在对象场景的等价性 ===\n');

// 以下两种写法对编译器来说【几乎等价】——都能描述同样的对象形状
interface IUser { id: number; name: string }
type TUser = { id: number; name: string };

const u1: IUser = { id: 1, name: 'I' };
const u2: TUser = { id: 2, name: 'T' };

// 结构化类型：两者形状一致，互相赋值合法
const u3: TUser = u1;   // ✅ IUser → TUser
const u4: IUser = u2;   // ✅ TUser → IUser
console.log('[等价性] u3 =', u3, ', u4 =', u4);

console.log('\n=== 5. type 的类型计算能力（interface 做不到）===\n');

// 条件类型 + 映射类型——type 别名独有的"类型级编程"
type Nullable<T> = T | null;
type UserName = Nullable<string>;   // string | null

const n1: UserName = 'Alice';
const n2: UserName = null;
console.log('[Nullable] n1 =', n1, ', n2 =', n2);

// 把对象所有属性变成 readonly（映射类型）
type Frozen<T> = { readonly [K in keyof T]: T[K] };
type FrozenUser = Frozen<IUser>;

const fu: FrozenUser = { id: 1, name: 'Bob' };
// fu.id = 2;   // ❌ readonly
console.log('[Frozen] fu =', fu);

// 提取对象的所有 key 作为联合类型
type UserKeys = keyof IUser;   // 'id' | 'name'
const k1: UserKeys = 'id';
const k2: UserKeys = 'name';
console.log('[keyof] k1 =', k1, ', k2 =', k2);

// 条件类型：根据输入类型"分支"
type IsString<T> = T extends string ? true : false;
type Check1 = IsString<'hi'>;   // true
type Check2 = IsString<42>;     // false
const c1: Check1 = true;
const c2: Check2 = false;
console.log('[条件类型] Check1 =', c1, ', Check2 =', c2);
