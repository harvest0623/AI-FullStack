/**
 * Day08 - 自定义工具类型实战
 *
 * 本文件实现并演示几个高频自定义工具类型：
 * 1. DeepPartial<T>：递归把所有嵌套字段变为可选
 * 2. DeepReadonly<T>：递归把所有嵌套字段变为只读
 * 3. Mutable<T>：去掉 readonly（非递归）
 * 4. PickByValue<T, V>：按值类型筛选字段
 * 5. GetReturnType<T>：从（可能联合的）函数类型提取返回值
 * 6. PromiseValue<T>：递归展开 Promise，拿到 resolve 值
 * 7. 综合实战：表单状态建模
 */

export {};

// ============================================================
// 1. DeepPartial<T>：递归可选
// ============================================================

// 普通 Partial 只做“一层”，嵌套对象仍是必填
type ShallowPartial<T> = { [K in keyof T]?: T[K] };

// 递归版：如果字段是对象，再进入一层做 Partial
type DeepPartial<T> = T extends object
  ? { [K in keyof T]?: DeepPartial<T[K]> }
  : T;

// 演示对比
interface Settings {
  theme: string;
  layout: {
    sidebar: boolean;
    panel: {
      width: number;
      height: number;
    };
  };
  version: number;
}

type ShallowPartialSettings = ShallowPartial<Settings>;
// { theme?: string; layout?: { sidebar: boolean; panel: { width: number; height: number } }; ... }
// 嵌套的 panel 仍必填

type DeepPartialSettings = DeepPartial<Settings>;
// { theme?: string; layout?: { sidebar?: boolean; panel?: { width?: number; height?: number } }; ... }

// 使用：表单 patch 时只填一层都合法
const patch: DeepPartialSettings = {
  theme: 'dark',
  layout: {
    panel: { width: 200 },   // 只改 panel.width，不必填 height
  },
};
console.log('[DeepPartial] =>', JSON.stringify(patch));


// ============================================================
// 2. DeepReadonly<T>：递归只读
// ============================================================

type DeepReadonly<T> = T extends object
  ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
  : T;

type FrozenSettings = DeepReadonly<Settings>;
// 所有层级的字段都是 readonly

const fs: FrozenSettings = {
  theme: 'dark',
  layout: { sidebar: true, panel: { width: 100, height: 50 } },
  version: 1,
};
// fs.theme = 'light';           // ❌
// fs.layout.sidebar = false;    // ❌
// fs.layout.panel.width = 200;  // ❌
console.log('[DeepReadonly] =>', JSON.stringify(fs));


// 注意：DeepReadonly 对函数与数组的特殊行为
// - 数组：T extends object 时会走 object 分支，结果可能是 readonly 属性集合而非 ReadonlyArray
//   生产实现通常需要额外分支处理，例如：
type DeepReadonlyStrict<T> =
  T extends (...args: any[]) => any ? T :
  T extends Array<infer U> ? ReadonlyArray<DeepReadonlyStrict<U>> :
  T extends object ? { readonly [K in keyof T]: DeepReadonlyStrict<T[K]> } :
  T;

type Arr = DeepReadonlyStrict<number[]>;
// readonly number[]
const arr: Arr = [1, 2, 3];
// arr.push(4);   // ❌ readonly
console.log('[DeepReadonlyStrict] =>', arr);


// ============================================================
// 3. Mutable<T>：去掉 readonly（非递归）
// ============================================================

type Mutable<T> = { -readonly [K in keyof T]: T[K]; };

interface ReadOnlyConfig {
  readonly host: string;
  readonly port: number;
  readonly debug: boolean;
}

type EditableConfig = Mutable<ReadOnlyConfig>;
// { host: string; port: number; debug: boolean }

const editable: EditableConfig = { host: '0.0.0.0', port: 8080, debug: true };
editable.port = 9090;   // ✅ 不再 readonly
console.log('[Mutable] =>', editable);

// 递归版 Mutable（去掉所有层 readonly）
type DeepMutable<T> =
  T extends (...args: any[]) => any ? T :
  T extends Array<infer U> ? Array<DeepMutable<U>> :
  T extends object ? { -readonly [K in keyof T]: DeepMutable<T[K]> } :
  T;

type DeepFrozen = DeepReadonlyStrict<Settings>;
type Thawed = DeepMutable<DeepFrozen>;
const thawed: Thawed = {
  theme: 'dark',
  layout: { sidebar: true, panel: { width: 100, height: 50 } },
  version: 1,
};
thawed.layout.panel.width = 200;   // ✅ 全部解冻
console.log('[DeepMutable] =>', JSON.stringify(thawed));


// ============================================================
// 4. PickByValue<T, V>：按值类型筛选字段
// ============================================================

// 思路：用映射类型 + as 重映射 + 条件类型过滤键
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};

interface FormState {
  name: string;
  age: number;
  email: string;
  active: boolean;
  score: number;
  tags: string[];
}

// 只挑出 string 类型字段
type StringFields = PickByValue<FormState, string>;
// { name: string; email: string }

const sf: StringFields = { name: 'Alice', email: 'a@x.com' };
console.log('[PickByValue] string =>', sf);

// 只挑出 number 类型字段
type NumberFields = PickByValue<FormState, number>;
// { age: number; score: number }

const nf: NumberFields = { age: 28, score: 100 };
console.log('[PickByValue] number =>', nf);

// 反向：OmitByValue（排除值类型为 V 的字段）
type OmitByValue<T, V> = {
  [K in keyof T as T[K] extends V ? never : K]: T[K];
};

type NonStringFields = OmitByValue<FormState, string>;
// { age: number; active: boolean; score: number; tags: string[] }
// 注意 tags: string[] 不 extends string，所以保留
const nsf: NonStringFields = { age: 28, active: true, score: 100, tags: [] };
console.log('[OmitByValue] =>', nsf);


// 进阶：只保留“值是非空类型（排除 null/undefined）”的字段
// 判断逻辑：原始类型 T[K] 是否能赋给去 null 后的类型 NonNullable<T[K]>
//   - 若 T[K] 含 null/undefined，则 T[K] 不 extends NonNullable<T[K]>，过滤掉
//   - 若 T[K] 是非空类型，则两者相等，保留
type NonNullableFields<T> = {
  [K in keyof T as T[K] extends NonNullable<T[K]> ? K : never]: T[K];
};

interface OptionalForm {
  a: string;
  b: string | null;
  c: number | undefined;
  d: boolean;
}

type RequiredOnly = NonNullableFields<OptionalForm>;
// { a: string; d: boolean }   ← b/c 含 null/undefined 被剔除
const ro: RequiredOnly = { a: 'x', d: true };
console.log('[NonNullableFields] =>', ro);


// ============================================================
// 5. GetReturnType<T>：从（可能联合的）函数类型提取返回值
// ============================================================

// 普通版（等价内置 ReturnType）
type GetReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

function loadUser() { return { id: 1, name: 'Alice' }; }
type LoadedUser = GetReturnType<typeof loadUser>;
// { id: number; name: string }

const lu: LoadedUser = { id: 1, name: 'Alice' };
console.log('[GetReturnType] =>', lu);


// 分发版：对函数联合类型，分别提取每个成员的返回值，再联合
type GetReturnTypes<T> = T extends (...args: any[]) => any ? ReturnType<T> : never;

type Fns = (() => number) | (() => string) | (() => boolean);
type AllReturns = GetReturnTypes<Fns>;
// number | string | boolean（分布式分别提取）

const ar: AllReturns = 42;
console.log('[GetReturnTypes 分布式] =>', ar);


// ============================================================
// 6. PromiseValue<T>：递归展开 Promise，拿到 resolve 值
// ============================================================

// 等价于内置 Awaited<T>，但自定义实现可加深对 infer + 递归条件类型的理解
type PromiseValue<T> = T extends Promise<infer U>
  ? U extends Promise<unknown>
    ? PromiseValue<U>
    : U
  : T;

type P1 = PromiseValue<Promise<number>>;                    // number
type P2 = PromiseValue<Promise<Promise<string>>>;           // string
type P3 = PromiseValue<Promise<Promise<Promise<boolean>>>>; // boolean
type P4 = PromiseValue<number>;                              // number（非 Promise 原样返回）

console.log('[PromiseValue] =>',
  1 as P1, '|', 's' as P2, '|', true as P3, '|', 2 as P4);


// 实战：从异步函数签名反推“最终值类型”
async function fetchArticle() {
  return { id: 1, title: 'TS', content: '...', author: { name: 'Bob' } };
}

type Article = PromiseValue<ReturnType<typeof fetchArticle>>;
// { id: number; title: string; content: string; author: { name: string } }

const art: Article = { id: 1, title: 'TS', content: '...', author: { name: 'Bob' } };
console.log('[PromiseValue 实战] =>', JSON.stringify(art));


// ============================================================
// 7. 综合实战：表单状态建模
// ============================================================

// 模型：一个带嵌套字段的表单状态
interface ProfileForm {
  username: string;
  password: string;
  profile: {
    displayName: string;
    avatar: string;
    bio: string;
  };
  preferences: {
    theme: 'dark' | 'light';
    language: 'en' | 'zh';
  };
}

// 场景 1：初始化时所有字段都允许 undefined（表单未填）
type InitialForm = DeepPartial<ProfileForm>;
const initial: InitialForm = {
  username: undefined,
  profile: { displayName: undefined },
};
console.log('[实战 DeepPartial] initial =>', JSON.stringify(initial, null, 0));


// 场景 2：提交后存入 store，全字段冻结（不可修改）
type StoredForm = DeepReadonlyStrict<ProfileForm>;
const stored: StoredForm = {
  username: 'alice',
  password: '***',
  profile: { displayName: 'Alice', avatar: 'a.png', bio: 'Hi' },
  preferences: { theme: 'dark', language: 'en' },
};
// stored.username = 'bob';               // ❌
// stored.profile.displayName = 'Bob';    // ❌
console.log('[实战 DeepReadonly] stored =>', JSON.stringify(stored, null, 0).slice(0, 80) + '...');


// 场景 3：从 store 读出后转为可编辑副本
type EditableForm = DeepMutable<StoredForm>;
const draft: EditableForm = JSON.parse(JSON.stringify(stored));
draft.username = 'bob';
draft.profile.displayName = 'Bob';
draft.preferences.theme = 'light';
console.log('[实战 DeepMutable] draft =>', JSON.stringify(draft, null, 0).slice(0, 80) + '...');


// 场景 4：校验时只关心 string 字段
type StringProfileFields = PickByValue<ProfileForm, string>;
// { username: string; password: string }   ← profile/preferences 是对象，被剔除
const spf: StringProfileFields = { username: 'alice', password: '***' };
console.log('[实战 PickByValue] =>', spf);


// 场景 5：异步加载后类型推导
async function loadProfile(): Promise<ProfileForm> {
  return {
    username: 'alice',
    password: '***',
    profile: { displayName: 'Alice', avatar: 'a.png', bio: 'Hi' },
    preferences: { theme: 'dark', language: 'en' },
  };
}
type LoadedProfile = PromiseValue<ReturnType<typeof loadProfile>>;
// ProfileForm

loadProfile().then((lp: LoadedProfile) => {
  console.log('[实战 PromiseValue] =>', lp.username, '|', lp.preferences.theme);
});


console.log('\n--- custom-utility.ts 执行完毕 ---');
