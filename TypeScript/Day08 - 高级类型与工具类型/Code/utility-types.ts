/**
 * Day08 - 内置工具类型 Utility Types 速览
 *
 * 本文件逐一演示 TS 内置的全部常用工具类型，按四类组织：
 * 1. 属性修饰类：Partial / Required / Readonly / Mutable（自定义）
 * 2. 对象构造类：Pick / Omit / Record / Exclude / Extract / NonNullable
 * 3. 函数相关类：Parameters / ReturnType / ConstructorParameters / InstanceType / Awaited
 * 4. 字符串操作类：Uppercase / Lowercase / Capitalize / Uncapitalize
 */

interface User {
  id: number;
  name: string;
  email: string;
  age?: number;
  readonly role: string;
}

export {};

// ============================================================
// 1. 属性修饰类
// ============================================================

// --- Partial<T>：把所有字段变成可选 ---
type PartialUser = Partial<User>;
// { id?: number; name?: string; email?: string; age?: number; role?: string; }

const patch: PartialUser = { name: 'Bob' };
console.log('[Partial] =>', patch);


// --- Required<T>：把所有字段变成必填（包括原本可选的） ---
type RequiredUser = Required<User>;
// { id: number; name: string; email: string; age: number; role: string; }

const full: RequiredUser = { id: 1, name: 'Alice', email: 'a@x.com', age: 28, role: 'admin' };
console.log('[Required] =>', full);


// --- Readonly<T>：把所有字段变成 readonly ---
type ReadonlyUser = Readonly<User>;
const frozen: ReadonlyUser = { id: 2, name: 'Carol', email: 'c@x.com', role: 'editor' };
// frozen.id = 3;   // ❌ 只读
console.log('[Readonly] =>', frozen);


// --- Mutable<T>（非内置，自定义）：去掉所有 readonly ---
type Mutable<T> = { -readonly [K in keyof T]: T[K]; };

interface FrozenConfig { readonly host: string; readonly port: number; }
type MutableConfig = Mutable<FrozenConfig>;
// { host: string; port: number }

const cfg: MutableConfig = { host: '0.0.0.0', port: 8080 };
cfg.port = 9090;   // ✅ 可写
console.log('[Mutable(自定义)] =>', cfg);


// ============================================================
// 2. 对象构造类
// ============================================================

// --- Pick<T, K>：从 T 中挑选指定键组成新类型 ---
type UserBasic = Pick<User, 'id' | 'name'>;
// { id: number; name: string; }

const ub: UserBasic = { id: 1, name: 'Dave' };
console.log('[Pick] =>', ub);


// --- Omit<T, K>：从 T 中排除指定键组成新类型 ---
type UserPublic = Omit<User, 'email' | 'role'>;
// { id: number; name: string; age?: number; }

const up: UserPublic = { id: 2, name: 'Eve' };
console.log('[Omit] =>', up);


// --- Record<K, T>：构造键为 K、值为 T 的对象类型 ---
type Role = 'admin' | 'editor' | 'viewer';
type RolePerms = Record<Role, string[]>;

const perms: RolePerms = {
  admin:  ['read', 'write', 'delete'],
  editor: ['read', 'write'],
  viewer: ['read'],
};
console.log('[Record] =>', perms);


// --- Exclude<T, U>：从联合 T 中排除可赋给 U 的成员 ---
type AllRoles = 'admin' | 'editor' | 'viewer' | 'guest';
type NonGuest = Exclude<AllRoles, 'guest'>;
// 'admin' | 'editor' | 'viewer'

const ng: NonGuest = 'editor';
console.log('[Exclude] =>', ng);


// --- Extract<T, U>：从联合 T 中提取可赋给 U 的成员 ---
type Mixed = string | number | boolean | null | undefined;
type OnlyNumOrStr = Extract<Mixed, string | number>;
// string | number

const ons: OnlyNumOrStr = 42;
console.log('[Extract] =>', ons);


// --- NonNullable<T>：从 T 中排除 null 和 undefined ---
type Maybe<T> = T | null | undefined;
type DefiniteString = NonNullable<Maybe<string>>;
// string

const ds: DefiniteString = 'hello';
console.log('[NonNullable] =>', ds);


// ============================================================
// 3. 函数相关类
// ============================================================

// --- Parameters<T>：以元组形式获取函数的参数类型 ---
function greet(name: string, age: number, opts?: { verbose: boolean }): string {
  return `${name}(${age})`;
}
type GreetParams = Parameters<typeof greet>;
// [name: string, age: number, opts?: { verbose: boolean }]

const gp: GreetParams = ['Alice', 28];
console.log('[Parameters] =>', JSON.stringify(gp), '|', greet(...gp));


// --- ReturnType<T>：获取函数的返回值类型 ---
function makeUser() {
  return { id: 1, name: 'Bob', roles: ['admin'] as const };
}
type MakeUserReturn = ReturnType<typeof makeUser>;
// { id: number; name: string; roles: readonly ['admin'] }

const mr: MakeUserReturn = makeUser();
console.log('[ReturnType] =>', JSON.stringify(mr));


// --- ConstructorParameters<T>：获取构造函数的参数类型 ---
class Point {
  constructor(public x: number, public y: number, public label?: string) {}
}
type PointCtorParams = ConstructorParameters<typeof Point>;
// [x: number, y: number, label?: string]

const pcparams: PointCtorParams = [3, 4, 'P1'];
console.log('[ConstructorParameters] =>', pcparams, '|', new Point(...pcparams));


// --- InstanceType<T>：获取构造函数的实例类型 ---
type PointInstance = InstanceType<typeof Point>;
// Point

const pi: PointInstance = new Point(5, 6);
console.log('[InstanceType] =>', pi);


// --- Awaited<T>：递归展开 Promise，获取最终 resolve 的值类型 ---
type AsyncValue = Awaited<Promise<Promise<Promise<number>>>>;
// number

type ApiResponse = Awaited<Promise<{ ok: boolean; data: string }>>;
// { ok: boolean; data: string }

const av: AsyncValue = 42;
const ar: ApiResponse = { ok: true, data: 'hello' };
console.log('[Awaited] =>', 'val:', av, '| api:', JSON.stringify(ar));


// ============================================================
// 4. 字符串操作类
// ============================================================

// --- Uppercase<S>：把字符串字面量类型转大写 ---
type Upper = Uppercase<'hello world'>;     // 'HELLO WORLD'
console.log('[Uppercase] =>', 'HELLO WORLD' as Upper);


// --- Lowercase<S>：把字符串字面量类型转小写 ---
type Lower = Lowercase<'TypeScript'>;      // 'typescript'
console.log('[Lowercase] =>', 'typescript' as Lower);


// --- Capitalize<S>：首字母大写 ---
type Cap = Capitalize<'typescript'>;       // 'Typescript'
console.log('[Capitalize] =>', 'Typescript' as Cap);


// --- Uncapitalize<S>：首字母小写 ---
type Uncap = Uncapitalize<'TypeScript'>;   // 'typeScript'
console.log('[Uncapitalize] =>', 'typeScript' as Uncap);


// 综合应用：生成 GET_X / SET_X 字面量联合
type Field = 'name' | 'age' | 'email';
type Getter = `get${Capitalize<Field>}`;    // 'getName' | 'getAge' | 'getEmail'
type Setter = `set${Capitalize<Field>}`;    // 'setName' | 'setAge' | 'setEmail'

const g: Getter = 'getName';
const s: Setter = 'setEmail';
console.log('[字符串+Capitalize] =>', g, '|', s);


// ============================================================
// 5. 综合实战：API 更新场景的工具类型组合
// ============================================================

interface Article {
  id: number;
  title: string;
  content: string;
  tags: string[];
  authorId: number;
  updatedAt: Date;
}

// 5.1 创建文章时的输入：不需要 id / updatedAt（服务端生成）
type CreateArticleInput = Omit<Article, 'id' | 'updatedAt'>;
const createInput: CreateArticleInput = {
  title: 'TS 进阶',
  content: '...',
  tags: ['ts'],
  authorId: 1,
};
console.log('[实战 Omit] CreateArticleInput =>', JSON.stringify(createInput, null, 0).slice(0, 80) + '...');


// 5.2 更新文章时的输入：所有字段可选，但 id 仍必填（用于定位）
type UpdateArticleInput = Pick<Article, 'id'> & Partial<Omit<Article, 'id'>>;
const updateInput: UpdateArticleInput = { id: 1, title: 'TS 进阶（修订）' };
console.log('[实战 Pick+Partial] UpdateArticleInput =>', JSON.stringify(updateInput));


// 5.3 列表查询返回的精简版（不含正文）
type ArticleSummary = Pick<Article, 'id' | 'title' | 'tags' | 'updatedAt'>;
const summary: ArticleSummary = {
  id: 1,
  title: 'TS 进阶',
  tags: ['ts'],
  updatedAt: new Date(),
};
console.log('[实战 Pick] ArticleSummary =>', JSON.stringify(summary, null, 0).slice(0, 80) + '...');


// 5.4 用 Record 描述权限映射表
type Action = 'read' | 'write' | 'delete';
type Resource = 'article' | 'comment' | 'user';
type PermissionMatrix = Record<Resource, Record<Action, boolean>>;

const matrix: PermissionMatrix = {
  article: { read: true, write: true, delete: false },
  comment: { read: true, write: true, delete: true },
  user:    { read: true, write: false, delete: false },
};
console.log('[实战 Record] PermissionMatrix =>',
  'article.delete:', matrix.article.delete,
  '| user.write:', matrix.user.write);


// 5.5 用 Exclude + NonNullable 处理 API 响应联合
type ApiResponse2<T> =
  | { status: 'ok'; data: T }
  | { status: 'error'; error: string }
  | { status: 'loading' };

type SuccessPayload = Extract<ApiResponse2<number>, { status: 'ok' }>['data'];
// number

const payload: SuccessPayload = 200;
console.log('[实战 Extract] SuccessPayload =>', payload);


console.log('\n--- utility-types.ts 执行完毕 ---');
