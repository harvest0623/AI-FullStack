/**
 * Day03 - interface vs type 深度对比
 * 主题：声明合并、扩展方式、类型计算能力、何时用哪个
 * 运行：npx ts-node interface-vs-type.ts
 */

console.log('=== 1. 声明合并 Declaration Merging ===\n');

// interface 同名声明会自动合并——这是 interface 独有的特性
// 真实应用：给第三方库扩展类型、给 Vue 的 ComponentCustomProperties 补字段
// （给全局 Window 扩展也是这个机制，但需要在 declare global 块内做）

interface ServerConfig {
  host: string;
  port: number;
}
interface ServerConfig {
  timeout?: number;   // 第二次声明会自动合并进来
}
interface ServerConfig {
  retry: number;      // 第三次再合并一个
}

// 等价于一次性声明 host / port / timeout / retry 四个字段
const cfg: ServerConfig = {
  host: '0.0.0.0',
  port: 8080,
  timeout: 3000,
  retry: 3,
};
console.log('[声明合并] ServerConfig =', cfg);

// type 同名会直接报错：Duplicate identifier
// type Foo = { a: number };
// type Foo = { b: number };   // ❌ TS2300: Duplicate identifier 'Foo'

console.log('\n=== 2. 扩展方式对比 ===\n');

// interface 用 extends，可以多继承
interface Animal {
  name: string;
}
interface Bear extends Animal {     // 单继承
  honey: boolean;
}
interface Dog extends Animal {      // 另一个继承
  bark(): void;
}
interface Husky extends Dog, Bear { // 多继承
  sled?: boolean;
}

const h: Husky = {
  name: 'Max',
  honey: false,
  bark: () => console.log('  [Husky] 汪汪！'),
  sled: true,
};
h.bark();
console.log('[interface extends] Husky =', h);

// type 用 & 交叉类型实现"扩展"
type TAnimal = { name: string };
type TBear = TAnimal & { honey: boolean };
type TDog = TAnimal & { bark(): void };
type THusky = TDog & TBear & { sled?: boolean };

const th: THusky = {
  name: 'Rex',
  honey: false,
  bark: () => console.log('  [type &] 汪汪！'),
  sled: false,
};
th.bark();
console.log('[type &] THusky =', th);

console.log('\n=== 3. 类型计算能力对比 ===\n');

// ❌ interface 无法表达"联合 / 元组 / 条件 / 映射"等类型级运算
// interface ID = number | string;                              // 语法错误（interface 不能用 =）
// interface Frozen<T> { [K in keyof T]: T[K] }                  // 映射类型在 interface 中非法
// interface IsString<T> = T extends string ? true : false;      // 语法错误

// ✅ type 可以做类型级编程
type Nullable<T> = T | null;
type Frozen<T> = { readonly [K in keyof T]: T[K] };
type IsString<T> = T extends string ? true : false;
type UserKeys = keyof { id: number; name: string };   // 'id' | 'name'

// 实际使用
type FrozenUser = Frozen<{ id: number; name: string }>;
const fu: FrozenUser = { id: 1, name: 'Bob' };
// fu.id = 2;   // ❌ readonly
console.log('[Frozen] fu =', fu);

type Check1 = IsString<'hi'>;   // true
type Check2 = IsString<42>;     // false
const c1: Check1 = true;
const c2: Check2 = false;
console.log('[条件类型] Check1 =', c1, ', Check2 =', c2);

const k1: UserKeys = 'id';
const k2: UserKeys = 'name';
console.log('[keyof] k1 =', k1, ', k2 =', k2);

console.log('\n=== 4. 命名规范差异 ===\n');

// 约定（非强制）：
// - interface 描述"对象形状 / 类契约" → 用 PascalCase 名词，如 User、Repository
// - type 描述"联合 / 工具 / 别名" → 可用 PascalCase 泛型名，如 Nullable<T>、ID、Status

// 库作者惯例：React、Vue 的 public API 类型优先用 interface，便于社区扩展合并
type Status = 'idle' | 'loading' | 'success' | 'error';   // 联合用 type
interface RequestState<T> {                                // 对象形状用 interface
  status: Status;
  data?: T;
  error?: Error;
}

const state: RequestState<string[]> = { status: 'loading' };
console.log('[命名规范] state =', state);

console.log('\n=== 5. 何时用哪个（决策树）===\n');

// 1) 对象形状 / 类 implements / 需要被外部扩展合并 → interface
// 2) 联合 | / 交叉 & / 元组 / 基本类型别名 / 条件 / 映射 / 工具类型 → type
// 3) 团队统一即可，混用最常见——React + TS 项目里两者都会大量出现

// 综合示例：一个典型的 API 资源类型设计
interface Resource<T> {
  id: string;
  attributes: T;
  relationships?: Record<string, unknown>;
}
type ArticleResource = Resource<{
  title: string;
  body: string;
  tags: string[];
}>;

const article: ArticleResource = {
  id: 'art-1',
  attributes: { title: 'TS 指南', body: '...', tags: ['ts'] },
};
console.log('[综合] article =', article);
