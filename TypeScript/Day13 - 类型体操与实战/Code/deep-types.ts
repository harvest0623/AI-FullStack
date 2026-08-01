/**
 * Day13 - 类型体操实战 01：递归型 Deep 工具类型
 *
 * 本文件实现并演示三个最经典的“递归型”工具类型：
 * 1. DeepPartial<T>：递归把所有层级属性变可选
 * 2. DeepReadonly<T>：递归把所有层级属性变只读（含数组/函数特判）
 * 3. Mutable<T> / DeepMutable<T>：去除 readonly（一层 / 递归）
 *
 * 这些类型是类型体操“递归 + 条件分支”最直接的练手题，
 * 也是工程中最高频的自定义工具类型（表单 patch、状态冻结/解冻）。
 */

export {};

// ============================================================
// 1. DeepPartial<T>：递归可选
// ============================================================

// 普通 Partial 只做一层：嵌套对象的子字段仍必填
type ShallowPartial<T> = { [K in keyof T]?: T[K] };

// 递归版：字段是对象时继续进入一层做 Partial
//  - T extends object 分支：处理对象，对每个键递归
//  - 否则原样返回（基础类型 string/number/boolean 等无需处理）
//  - 注意：函数也 extends object，会被走 object 分支，但不影响功能（函数属性本就少见）
type DeepPartial<T> = T extends object
  ? { [K in keyof T]?: DeepPartial<T[K]> }
  : T;

// 演示模型：带多层嵌套的配置
interface AppConfig {
  name: string;
  version: number;
  database: {
    host: string;
    port: number;
    options: {
      timeout: number;
      reconnect: boolean;
    };
  };
}

type ShallowPartialApp = ShallowPartial<AppConfig>;
// { name?: string; version?: number; database?: { host; port; options: { timeout; reconnect } } }
// 嵌套的 options 内部字段仍必填

type DeepPartialApp = DeepPartial<AppConfig>;
// { name?: string; version?: number; database?: { host?: string; port?: number; options?: { timeout?: number; reconnect?: boolean } } }

// 实战场景：表单 patch 时只填部分嵌套字段，无需补全整棵树
const patch: DeepPartialApp = {
  name: 'my-app',
  database: {
    options: { timeout: 5000 },   // 只改 timeout，reconnect 可省略
  },
};
console.log('[DeepPartial] patch =>', JSON.stringify(patch));


// ============================================================
// 2. DeepReadonly<T>：递归只读
// ============================================================

// 朴素版：与 DeepPartial 同构，仅加 readonly
type DeepReadonlyNaive<T> = T extends object
  ? { readonly [K in keyof T]: DeepReadonlyNaive<T[K]> }
  : T;

// 严格版：特判函数与数组，避免：
//  - 函数被错误地只读化为对象（函数本身不可变，应原样保留）
//  - 数组走 object 分支后会丢失 push/pop 等原型方法（应转为 ReadonlyArray）
type DeepReadonly<T> =
  T extends (...args: any[]) => any           // 函数：原样返回
    ? T
    : T extends Array<infer U>                // 数组：递归元素后包成 ReadonlyArray
      ? ReadonlyArray<DeepReadonly<U>>
      : T extends object                      // 普通对象：每个字段递归只读
        ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
        : T;                                  // 基础类型：原样返回

type FrozenApp = DeepReadonly<AppConfig>;

const frozen: FrozenApp = {
  name: 'app',
  version: 1,
  database: { host: 'localhost', port: 5432, options: { timeout: 3000, reconnect: true } },
};

// 全部只读，以下赋值都会编译报错：
// frozen.name = 'x';                    // ❌
// frozen.database.port = 3306;          // ❌
// frozen.database.options.timeout = 0;  // ❌
console.log('[DeepReadonly] frozen =>', JSON.stringify(frozen));

// 数组特判效果对比
type NumbersArr = DeepReadonly<number[]>;
// readonly number[]（push/pop 不可用）
const arr: NumbersArr = [1, 2, 3];
// arr.push(4);   // ❌ Property 'push' does not exist on readonly number[]
console.log('[DeepReadonly] arr =>', arr);


// ============================================================
// 3. Mutable<T>：去除 readonly（一层）
// ============================================================

// 用 -readonly 修饰符批量去掉只读
type Mutable<T> = { -readonly [K in keyof T]: T[K] };

interface ReadOnlyPoint {
  readonly x: number;
  readonly y: number;
}

type EditablePoint = Mutable<ReadOnlyPoint>;
// { x: number; y: number }

const p: EditablePoint = { x: 1, y: 2 };
p.x = 100;   // ✅ 已可写
console.log('[Mutable] point =>', p);


// ============================================================
// 4. DeepMutable<T>：递归去除所有层 readonly
// ============================================================

// 与 DeepReadonly 对称：保持函数/数组特判，对象分支用 -readonly
type DeepMutable<T> =
  T extends (...args: any[]) => any
    ? T
    : T extends Array<infer U>
      ? Array<DeepMutable<U>>
      : T extends object
        ? { -readonly [K in keyof T]: DeepMutable<T[K]> }
        : T;

// 互相转换演示：Frozen 解冻后与原类型一致
type ThawedApp = DeepMutable<FrozenApp>;

const thawed: ThawedApp = JSON.parse(JSON.stringify(frozen));
thawed.name = 'app-v2';
thawed.database.options.timeout = 9999;   // ✅ 深层也可写
console.log('[DeepMutable] thawed =>', JSON.stringify(thawed));

// 互逆性验证：DeepMutable<DeepReadonly<T>> ≈ T
type RoundTrip = DeepMutable<DeepReadonly<AppConfig>>;
const rt: RoundTrip = {
  name: 'rt',
  version: 0,
  database: { host: 'h', port: 1, options: { timeout: 1, reconnect: false } },
};
console.log('[RoundTrip] =>', JSON.stringify(rt));


// ============================================================
// 5. 综合实战：状态管理器的“冻结 → 编辑 → 提交”流程
// ============================================================

interface UserState {
  readonly id: number;            // 业务上禁止修改
  name: string;
  profile: {
    readonly email: string;       // 业务上禁止修改
    bio: string;
  };
}

// 场景 1：从服务端拉到的数据放入 store，整体冻结
type FrozenState = DeepReadonly<UserState>;
const stored: FrozenState = {
  id: 1,
  name: 'Alice',
  profile: { email: 'a@x.com', bio: 'Hi' },
};

// 场景 2：进入编辑模式，深拷贝并解冻
type EditableState = DeepMutable<FrozenState>;
const draft: EditableState = JSON.parse(JSON.stringify(stored));
draft.name = 'Bob';
draft.profile.bio = 'Hello';
// draft.id = 2;            // ❌ 类型层面仍可写——
// DeepMutable 不区分“业务只读”与“类型只读”，这是它的边界
console.log('[实战] draft =>', JSON.stringify(draft));

// 场景 3：仅接受部分字段更新（如 PATCH 语义）
type UserPatch = DeepPartial<EditableState>;
const patch2: UserPatch = { profile: { bio: 'Updated bio' } };
console.log('[实战] patch =>', JSON.stringify(patch2));


console.log('\n--- deep-types.ts 执行完毕 ---');
