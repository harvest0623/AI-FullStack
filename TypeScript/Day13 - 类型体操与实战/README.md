# Day13 - 类型体操与实战

> 类型体操（Type Gymnastics）是 TypeScript 类型系统的高级运用方式：把“类型”当作一门可计算的图灵完备语言，通过条件类型、`infer` 推断、映射类型、模板字面量与递归，在“不写任何运行时代码”的前提下，让编译器替我们解决一组原本需要运行时校验的类型问题。Day08 我们打下了高级类型的地基——`keyof`、映射类型、条件类型、`infer`、模板字面量；本章把这些原料组合起来，去解一组真正的工程题：递归地变换嵌套结构、按值类型筛选键、从字符串里反向构造类型、让路由参数 / 事件系统 / 对象路径访问都获得编译期强校验。类型体操不是炫技，它是“把错误前置到编译期”的最后一公里。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识 - 类型编程核心能力回顾](#二理论知识---类型编程核心能力回顾)
  - [2.1 条件类型 + infer](#21-条件类型--infer)
  - [2.2 映射类型 + as 重映射](#22-映射类型--as-重映射)
  - [2.3 模板字面量类型](#23-模板字面量类型)
  - [2.4 递归类型](#24-递归类型)
  - [2.5 元组与数组的类型操作](#25-元组与数组的类型操作)
- [三、经典类型体操实现](#三经典类型体操实现)
  - [DeepPartial / DeepReadonly / Mutable / DeepMutable](#deeppartial--deepreadonly--mutable--deepmutable)
  - [PickByValue / KeysOfType / Optional](#pickbyvalue--keysoftype--optional)
  - [MyPick / MyOmit / MyRecord / MyReturnType](#mypick--myomit--myrecord--myreturntype)
  - [TupleToUnion / UnionToTuple](#tupletounion--uniontotuple)
  - [Join / CamelCase / KebabCase / SnakeCase](#join--camelcase--kebabcase--snakecase)
  - [Path\<T\> 与 IsEqual](#patht-与-isequal)
- [四、类型体操实战场景](#四类型体操实战场景)
  - [4.1 类型安全的路由参数](#41-类型安全的路由参数)
  - [4.2 类型安全的事件系统](#42-类型安全的事件系统)
  - [4.3 类型安全的 SQL 查询构造器（简化版）](#43-类型安全的-sql-查询构造器简化版)
  - [4.4 类型安全的对象路径访问](#44-类型安全的对象路径访问)
- [五、类型体操的边界与陷阱](#五类型体操的边界与陷阱)
- [六、关键知识点总结](#六关键知识点总结)
- [七、实战练习](#七实战练习)

---

## 一、学习目标

完成本章后，你应当能够：

1. 把“条件类型 + `infer` + 递归”作为标准三件套，写出对任意嵌套深度都成立的工具类型（`DeepPartial` / `DeepReadonly` / `DeepMutable`）。
2. 理解“键重映射 `as` + 条件类型 + `never`”这一过滤套路，能用它实现 `PickByValue` / `KeysOfType` / `OmitByValue`。
3. 不借助内置工具类型，从零手写 `Pick` / `Omit` / `Record` / `ReturnType` / `Parameters` / `Awaited`，并能解释每行实现原理。
4. 用模板字面量类型 + `infer` 模式匹配做字符串层面的递归变换：`Join` / `Split` / `CamelCase` / `KebabCase` / `SnakeCase` / `ReplaceAll`。
5. 用 `Path<T>` 把对象结构“扁平化”为所有点分路径联合，并用 `Get<T, P>` 反推路径对应的值类型，运行时实现一个类型安全的 `get(obj, 'a.b.c')`。
6. 从 `'/users/:id'` 这类路径字符串里提取参数键、构造 `params` 类型，实现一个路由处理器签名自动推断的路由器。
7. 用泛型 + `keyof` + 索引访问把 `EventMap` 当作“事件字典”，让 `on` / `off` / `emit` 三件套全部类型安全。
8. 知道类型体操的边界在哪里：何时该用 `any` / `unknown` 放过、如何调试难以理解的类型错误、何时该优先考虑可读性而非极致类型安全。

---

## 二、理论知识 - 类型编程核心能力回顾

本章对 Day08 已介绍的能力做一次“体操视角”的浓缩回顾，重点放在“如何把它们组合起来”而非“语法本身”。

### 2.1 条件类型 + infer

`T extends U ? X : Y` 是类型层面的 `if/else`；`infer R` 写在 `extends` 右侧声明一个待推断变量。组合起来，条件类型从“判断”升级为“提取”。

```ts
// 提取数组元素类型
type ElementOf<T> = T extends Array<infer E> ? E : never;

// 提取函数返回值
type ReturnOf<T> = T extends (...args: any[]) => infer R ? R : never;
```

体操中几乎所有“从已有类型里挖一块出来”的需求都用这个模式：
- `infer` 写在返回值位置 → 提取返回值
- `infer` 写在 `...args` 位置 → 提取参数元组
- `infer` 写在模板字面量中段 → 提取字符串前后缀
- `infer` 配合递归 → 展开任意深度嵌套（如 `Awaited` 展开多层 `Promise`）

> 💡 关键陷阱：当 `T` 是“裸类型参数”且传入联合时，条件类型会**自动分发**到每个成员。多数时候这是好事（`Exclude` / `Extract` 依赖此行为），但若想“整体判断联合”，需要用 `[T] extends [U]` 包一层阻止分发。

### 2.2 映射类型 + as 重映射

`[K in keyof T]: NewType` 是类型层面的 `map`，遍历对象所有键统一变换值类型。`as` 子句把“键”本身也变成可变换的对象，配合 `never` 还能过滤键。

```ts
// 给所有键加前缀
type Prefixed<T, P extends string> = {
  [K in keyof T as `${P}${Capitalize<string & K>}`]: T[K];
};

// 按值类型筛选键（核心三件套）
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};
```

“键重映射 + 条件类型 + `never`”是自定义工具类型的万能套路：键名要变 → 用模板字面量；键要不要留 → 用条件类型返回 `K` 或 `never`。

### 2.3 模板字面量类型

`` `${a}${b}` `` 把字符串拼接搬到了类型空间。两种用法：
1. **拼接**：把多个联合做笛卡尔积，一次性枚举大量合法字面量。
2. **模式匹配**：配合 `infer` 在条件类型里“切字符串”。

```ts
// 拼接：4 种 margin 字面量
type Margin = `margin-${'top' | 'right' | 'bottom' | 'left'}`;

// 模式匹配：切分 snake_case 的首段
type FirstSegment<S> = S extends `${infer Head}_${string}` ? Head : S;
```

字符串体操（`CamelCase` / `KebabCase` / `Join` / `Split`）本质就是“模板字面量 + `infer` + 递归”的组合：每轮匹配切下一段，递归处理剩下部分。

### 2.4 递归类型

TS 类型系统是图灵完备的（且支持递归），因此可以在类型层面写“循环”：
- `DeepPartial<T>` 递归进入嵌套对象
- `Awaited<T>` 递归展开 `Promise`
- `Path<T>` 递归遍历对象所有键
- `CamelCase<S>` 递归处理剩余字符串

> ⚠️ TS 对递归深度有上限（默认约 50 层栈、模板字面量长度上限 10000 字符左右），过深会触发 `Type instantiation is excessively deep` 错误。常用做法是显式传入 `Depth` 计数器提前收口。

### 2.5 元组与数组的类型操作

| 操作 | 写法 | 说明 |
|------|------|------|
| 取元素联合 | `T[number]` | 元组返回所有位置类型的联合；数组返回元素类型 |
| 解构首尾 | `[infer F, ...infer R]` / `[..., infer L]` | 配合 `infer` 在元组上做模式匹配 |
| 追加 | `[...T, V]` | 把 `V` 拼到元组末尾 |
| 元组↔联合 | `T[number]` 与 `UnionToTuple` | 后者 TS 无原生支持，只能近似（见 3.4） |

```ts
type First<T extends readonly unknown[]> = T extends readonly [infer F, ...unknown[]] ? F : never;
type Last<T extends readonly unknown[]>  = T extends readonly [...unknown[], infer L] ? L : never;
type Push<T extends readonly unknown[], V> = [...T, V];
```

`TupleToUnion` 用 `T[number]` 即可；反过来 `UnionToTuple` 没有官方解，社区用函数参数逆变 hack，但顺序不稳定，**生产代码不应依赖其顺序**。

---

## 三、经典类型体操实现

> 全部实现与可运行示例见 `Code/` 目录下对应文件。

### DeepPartial / DeepReadonly / Mutable / DeepMutable

`DeepPartial<T>` 把所有层级字段变可选。朴素 `Partial` 只做一层，嵌套对象的子字段仍必填；递归版用条件类型判断“字段是否为对象”，再进入一层。

```ts
type DeepPartial<T> = T extends object
  ? { [K in keyof T]?: DeepPartial<T[K]> }
  : T;
```

`DeepReadonly<T>` 与之同构，但需要特判**函数**与**数组**：函数本身不可变应原样返回；数组走 `object` 分支会丢失 `push`/`pop` 原型方法，要转成 `ReadonlyArray`。

```ts
type DeepReadonly<T> =
  T extends (...args: any[]) => any ? T :
  T extends Array<infer U> ? ReadonlyArray<DeepReadonly<U>> :
  T extends object ? { readonly [K in keyof T]: DeepReadonly<T[K]> } :
  T;
```

`Mutable<T>` 是 `Readonly<T>` 的反向，用 `-readonly` 修饰符：

```ts
type Mutable<T> = { -readonly [K in keyof T]: T[K] };
```

`DeepMutable<T>` 与 `DeepReadonly` 对称——把对象分支的 `readonly` 换成 `-readonly` 即可。两者互为近似逆运算：`DeepMutable<DeepReadonly<T>>` 在结构上等于 `T`（但 `DeepMutable` 不区分“业务只读”与“类型只读”）。

📎 完整代码：`Code/deep-types.ts`

### PickByValue / KeysOfType / Optional

`PickByValue<T, V>` 按“值类型”挑选键，是“映射 + as + 条件类型 + never”三件套最直接的应用：

```ts
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};
```

`KeysOfType<T, V>` 只返回键名联合，不返回对象类型。实现思路是“先构造一个值是键名或 `never` 的映射类型，再用 `[keyof T]` 取所有值联合”，`never` 在联合中自动消失：

```ts
type KeysOfType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T];
```

`Optional<T, K>` 把“指定键”变可选，其余键保持原样。思路是 `Omit + Partial<Pick>` 拼接：

```ts
type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
```

反向 `Mandatory<T, K>` 用 `Required<Pick<T, K>>` 强制把可选变必填。

> ⚠️ 常见陷阱：`string[] extends string` 是 `false`（数组不是字符串的子类型）。所以 `PickByValue<{ tags: string[] }, string>` 不会包含 `tags` 字段——这往往与直觉相反。

📎 完整代码：`Code/pick-by-value.ts`

### MyPick / MyOmit / MyRecord / MyReturnType

手写内置工具类型，理解每行原理：

```ts
type MyPick<T, K extends keyof T> = { [P in K]: T[P] };

// 写法 A：as + 条件类型过滤键
type MyOmit<T, K extends keyof T> = {
  [P in keyof T as P extends K ? never : P]: T[P];
};

// 写法 B：Pick + Exclude 组合（内置 Omit 即此实现）
type MyOmitByPick<T, K extends keyof T> = MyPick<T, Exclude<keyof T, K>>;

type MyRecord<K extends string | number | symbol, T> = { [P in K]: T };

type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
type MyParameters<T> = T extends (...args: infer P) => any ? P : never;

// 递归展开 Promise（等价 Awaited，简化版）
type MyAwaited<T> = T extends Promise<infer U>
  ? U extends Promise<unknown> ? MyAwaited<U> : U
  : T;
```

`MyRecord` 的“完整性校验”值得注意：`Record<'a' | 'b', number>` 要求对象同时存在 `a` 与 `b` 两个键，缺一不可——这来自 `[P in K]` 把联合全部展开为映射键。

📎 完整代码：`Code/my-utility.ts`

### TupleToUnion / UnionToTuple

`TupleToUnion` 极简单——`T[number]` 取元组元素类型的联合：

```ts
type TupleToUnion<T extends readonly unknown[]> = T[number];
// TupleToUnion<['a', 'b', 'c']> = 'a' | 'b' | 'c'
```

`UnionToTuple` 是反向操作，但 **TS 类型系统没有“有序联合”概念**，无法稳定地把联合按确定顺序转为元组。社区 hack 利用“函数参数逆变”取出联合的“最后一个成员”，反复套用即可得到一个顺序，但**顺序不稳定**且实现晦涩：

```ts
type UnionToIntersection<U> =
  (U extends unknown ? (x: U) => void : never) extends (x: infer I) => void ? I : never;

type LastOfUnion<U> =
  UnionToIntersection<U extends unknown ? (x: U) => void : never> extends (x: infer L) => void ? L : never;

type UnionToTupleRec<U, Last = LastOfUnion<U>> =
  [U] extends [never] ? [] : [...UnionToTupleRec<Exclude<U, Last>>, Last];
```

**工程建议**：若需要“有序常量集合 + 联合类型”，直接用 `as const` 元组，再用 `T[number]` 反推联合，不要依赖 `UnionToTuple` 的顺序。

📎 完整代码：`Code/my-utility.ts`

### Join / CamelCase / KebabCase / SnakeCase

字符串体操统一套路：模板字面量 + `infer` 模式匹配 + 递归。

```ts
// 用分隔符拼接字符串元组
type Join<T extends readonly string[], Sep extends string> =
  T extends readonly [infer F extends string, ...infer R extends string[]]
    ? R extends [] ? F : `${F}${Sep}${Join<R, Sep>}`
    : '';

// snake/kebab → camelCase
type CamelCase<S extends string> =
  S extends `${infer Head}_${infer Char}${infer Tail}`
    ? `${Head}${Uppercase<Char>}${CamelCase<Tail>}`
    : S extends `${infer Head}-${infer Char}${infer Tail}`
      ? `${Head}${Uppercase<Char>}${CamelCase<Tail>}`
      : S;

// camel → kebab（线性递归版，避免指数级复杂度）
type KebabCaseImpl<S extends string> =
  S extends `${infer First}${infer Rest}`
    ? First extends Uppercase<First>
      ? First extends Lowercase<First>           // 数字/符号（大小写相等）
        ? `${First}${KebabCaseImpl<Rest>}`        // 不分词，原样拼接
        : `-${Lowercase<First>}${KebabCaseImpl<Rest>}`  // 大写字母：前加 -
      : `${First}${KebabCaseImpl<Rest>}`          // 小写字母：原样拼接
    : S;

type DropLeadingSep<S extends string, Sep extends string> =
  S extends `${Sep}${infer R}` ? R : S;
type KebabCase<S extends string> = DropLeadingSep<KebabCaseImpl<S>, '-'>;
```

`SnakeCase<S>` 与 `KebabCase` 同构，只是分隔符换成 `_`。

注意 `KebabCase` 的两个关键技巧：
1. **线性递归**：每轮只取首字符 `First`，递归处理 `Rest`，避免对 `Head` 与 `Tail` 同时递归导致复杂度指数级爆炸（早期 `Head + Upper + Tail` 三元写法在长字符串上会触发 `Type instantiation is excessively deep`）。
2. **数字/符号识别**：`First extends Uppercase<First>` 识别“大写字母”，再用 `First extends Lowercase<First>` 排除“数字/符号”（因为数字 `1 extends Uppercase<1>` 也是 true，但数字大小写相等 → 两个判断同时成立时即为非字母字符）。

`ReplaceAll<S, From, To>` 也是同类套路，递归替换直到无法匹配为止。

📎 完整代码：`Code/string-operations.ts`

### Path<T> 与 IsEqual

`Path<T>` 把对象结构“扁平化”为所有点分路径联合（`'a' | 'a.b' | 'a.b.c'`），是 `get(obj, 'a.b.c')` 类型安全的基础。递归遍历每个键，生成“键本身”+“键 + 子路径”：

```ts
type Path<T, Depth extends number = 5> = [Depth] extends [0]
  ? never
  : T extends object
    ? T extends Array<any> ? never
    : T extends (...args: any[]) => any ? never
    : {
        [K in keyof T & string]:
          | K
          | `${K}.${Path<T[K], Decrement<Depth>>}`;
      }[keyof T & string]
    : never;
```

`Depth` 计数器防止无限递归。`Decrement` 用条件类型枚举实现数字递减。

`Get<T, P>` 是 `Path` 的对偶：把路径字符串按 `.` 切分，逐层索引访问：

```ts
type Get<T, P extends string> =
  P extends `${infer Head}.${infer Tail}`
    ? Head extends keyof T ? Get<T[Head], Tail> : never
    : P extends keyof T ? T[P] : never;
```

`IsEqual<A, B>` 是类型层面判等。不能直接用 `A extends B`——联合会分发，`any` 会吞掉一切。经典 hack 是双向 `extends` + 元组包裹阻止分发：

```ts
type IsEqual<A, B> =
  [A] extends [B]
    ? [B] extends [A] ? true : false
    : false;
```

这个写法对 `any` 也能拒绝（`IsEqual<any, string>` 是 `false`），是社区公认的“最稳判等”实现之一。

📎 完整代码：`Code/object-path.ts`

---

## 四、类型体操实战场景

### 4.1 类型安全的路由参数

需求：从 `'/users/:id'` 这类路径字符串里提取参数键，构造 `params` 类型，让 `add(path, handler)` 的 handler 自动获得正确的 params 类型。

```ts
// 提取 :param 形式的参数键
type ExtractRouteParams<S extends string> =
  S extends `${infer _Pre}:${infer Param}/${infer Rest}`
    ? Param | ExtractRouteParams<`/${Rest}`>
    : S extends `${infer _Pre}:${infer Param}` ? Param : never;

// 构造 params 对象类型
type RouteParams<S extends string> = { [K in ExtractRouteParams<S>]: string };

// 路由处理器
type RouteHandler<Path extends string> = (params: RouteParams<Path>) => void;
```

注册时 `Path` 是字面量类型，handler 的 `params` 自动推断为 `{ id: string }`、`{ postId: string; commentId: string }` 或 `{}`（无参数）。运行时把 `:name` 模式转成捕获组正则匹配 fullPath，回填 params。

进阶：可以用 `ApiMap` 把“方法 + 路径”联合成键（如 `'GET /users/:id'`），实现一个静态查表的 dispatcher——endpoint 字符串和 params 类型一一对应，编译期校验完整性。

📎 完整代码：`Code/type-safe-router.ts`

### 4.2 类型安全的事件系统

需求：实现一个 `EventEmitter`，`on` / `off` / `emit` 三件套全部类型安全——事件名和载荷类型必须严格匹配预定义的 `EventMap`。

```ts
interface AppEvents {
  'user:login':  { userId: string; loginAt: Date };
  'message:new': { messageId: string; content: string; from: string };
  'ready':       undefined;
}

class TypedEmitter<Events extends Record<string, any>> {
  on<K extends keyof Events>(event: K, handler: (payload: Events[K]) => void): this { /* ... */ }
  off<K extends keyof Events>(event: K, handler: (payload: Events[K]) => void): this { /* ... */ }
  emit<K extends keyof Events>(
    event: K,
    ...args: Events[K] extends undefined ? [] : [payload: Events[K]]
  ): this { /* ... */ }
}
```

`emit` 的 `...args` 用了条件类型：无载荷事件（`Events[K] extends undefined`）参数为空元组 `[]`，有载荷事件参数为 `[payload]`。这样 `emit('ready')` 合法，`emit('user:login', { ... })` 也合法，但参数类型错就编译报错。

进阶：用模板字面量类型从对象类型自动生成 `'change:<field>'` 事件字典，让 store 字段变更事件也获得类型推断。

📎 完整代码：`Code/type-safe-events.ts`

### 4.3 类型安全的 SQL 查询构造器（简化版）

需求：构造器接收表名与列名联合，`select` / `where` 方法只接受预定义的列名，最终生成的 SQL 字符串类型也精确。

```ts
interface Schema {
  users: { id: number; name: string; age: number };
  posts: { id: number; title: string; authorId: number };
}

// 表名联合
type Table = keyof Schema;

// 某张表的列名联合
type Columns<T extends Table> = keyof Schema[T];

class QueryBuilder<T extends Table> {
  constructor(private table: T) {}
  select<C extends Columns<T>>(...cols: C[]): this { /* ... */ return this; }
  where<C extends Columns<T>>(col: C, value: Schema[T][C]): this { /* ... */ return this; }
}

new QueryBuilder('users')
  .select('id', 'name')           // ✅ 列名合法
  // .select('title')             // ❌ 'title' 不在 users 表
  .where('age', 18);              // ✅ age 是 number，value 必须是 number
  // .where('name', 18);          // ❌ name 是 string，不接受 number
```

这里的关键是 `Schema[T][C]`——通过两层索引访问精确得到“某张表某个列的值类型”，让 `where` 的 value 参数与列类型一一对应。完整实现可作为练习扩展。

### 4.4 类型安全的对象路径访问

需求：实现 `get(obj, 'a.b.c')`，路径字符串必须是对象真实存在的点分路径，返回值类型由路径自动推断。这是 `Path<T>` + `Get<T, P>` 的直接落地：

```ts
function get<T extends object, P extends Path<T>>(obj: T, path: P): Get<T, P> | undefined {
  const segments = path.split('.');
  let current: any = obj;
  for (const seg of segments) {
    if (current == null) return undefined;
    current = current[seg];
  }
  return current as Get<T, P>;
}

const tree = { id: 1, profile: { contact: { email: 'a@x.com' } } };
get(tree, 'id');                       // number
get(tree, 'profile.contact.email');    // string
// get(tree, 'profile.unknown');       // ❌ 编译报错：路径不存在
```

运行时按 `.` 切分逐层访问，遇到 `null`/`undefined` 中途返回 `undefined` 不抛错。类型层面，路径合法性由 `P extends Path<T>` 约束，返回类型由 `Get<T, P>` 自动推断——是 lodash.get / ramda.path 的“类型加强版”。

📎 完整代码：`Code/object-path.ts`

---

## 五、类型体操的边界与陷阱

类型体操强大但有边界，盲目追求“类型极致安全”会得不偿失。下面是工程中最常踩的几个坑：

### 可读性 vs 类型安全

类型体操的代码可读性远低于普通 TS——一行 `DeepReadonly` 实现，没学过条件类型的人完全看不懂。**团队代码**应优先选择“能看懂”的实现，把体操封装到工具类型里，调用方只看到名字和注释。一个原则：**类型定义可以复杂，但调用点必须简单**。

### 编译时间成本

复杂的递归类型会显著拖慢编译速度。`Path<T>` 在大型对象上展开可能产生几百个字面量联合，IDE 的语言服务会变卡。监控指标：
- 单文件 `tsc --noEmit` 时间
- IDE 类型提示延迟

如果某个工具类型让 `tsc` 时间从 2 秒涨到 30 秒，就该考虑：
- 加 `Depth` 计数器限制递归深度
- 把动态推断拆成静态声明
- 用 `@ts-ignore` 在边缘场景放过

### 何时该用 any / unknown 放过

不要为了消灭每一个 `any` 而写出比业务代码还长的类型体操。合理的放过场景：

1. **第三方库类型不完整**：用 `any` 或 `unknown` 包一层，写注释说明。
2. **动态元编程**：`JSON.parse` 返回 `any` 是合理的——你无法静态推断字符串。
3. **类型体操过度复杂**：如果 `Path<T>` 实现要 30 行还搞不定嵌套 5 层，不如退一步用 `string` + 运行时校验。
4. **测试代码 / 原型代码**：快速验证想法时 `any` 完全合理。

`unknown` 是比 `any` 更安全的退路——它强制你在使用前做类型收窄，不会悄悄传播。

### 调试类型错误的方法

类型体操的错误信息往往极长，难以定位。几个实用技巧：

1. **临时 `type _Debug = T`**：把推断过程中的中间类型赋给一个别名，IDE 悬停可看展开结果。
2. **简化输入**：把泛型参数临时换成具体类型（如把 `<T>` 换成 `<User>`），看推断在哪一步走错。
3. **分步验证**：把递归类型拆成多层，每层单独测试：`type Step1 = ...; type Step2 = Step1 extends ... ? ... : ...`。
4. **看 `never` 出现位置**：`never` 通常意味着模式匹配失败——检查 `infer` 位置和 `extends` 方向。
5. **`extends` 方向**：`A extends B ? X : Y` 中 A 必须能赋给 B 才进 X 分支。判断“联合成员类型”用 `T extends U`（分发），判断“整体相等”用 `[T] extends [U]`（阻止分发）。
6. **TS Playground**：把可疑片段贴到 [TypeScript Playground](https://www.typescriptlang.org/play)，开启 `noErrorTruncation` 看完整错误信息。

---

## 六、关键知识点总结

1. **递归型工具类型**：`DeepPartial` / `DeepReadonly` / `DeepMutable` 用“条件类型 + 递归”遍历嵌套结构；`DeepReadonly` 需特判函数与数组，避免破坏函数和数组原型方法。
2. **键重映射三件套**：`[K in keyof T as T[K] extends V ? K : never]: T[K]` 是“按值类型过滤键”的万能套路，`PickByValue` / `OmitByValue` 都基于此。
3. **`KeysOfType<T, V>`**：用映射 + 索引访问取出键名联合，`never` 在联合中自动消失。
4. **`Optional<T, K>`**：`Omit + Partial<Pick>` 组合，把指定键变可选；反向 `Mandatory` 用 `Required<Pick>`。
5. **手写内置工具**：`MyPick` / `MyOmit` / `MyRecord` / `MyReturnType` / `MyParameters` / `MyAwaited` 全部基于“映射类型 + 条件类型 + `infer` + 递归”实现。
6. **`TupleToUnion` 容易，`UnionToTuple` 难**：前者用 `T[number]`，后者 TS 无原生支持，社区 hack 顺序不稳定，**生产代码不应依赖其顺序**。
7. **字符串体操统一套路**：模板字面量 + `infer` 模式匹配 + 递归。`Join` / `Split` / `CamelCase` / `KebabCase` / `SnakeCase` / `ReplaceAll` 全部同构。
8. **`KebabCase` 判断技巧**：用**线性递归**（每轮只取首字符 `First` + 递归 `Rest`）避免对 `Head`/`Tail` 同时递归导致复杂度爆炸；用 `First extends Uppercase<First>` 识别大写字母，再用 `First extends Lowercase<First>` 排除数字/符号（数字大小写相等，两个判断同时成立即为非字母字符）。
9. **`Path<T>` + `Get<T, P>`**：前者把对象结构扁平化为路径联合，后者按路径反推值类型。配 `Depth` 计数器防递归爆栈。
10. **`IsEqual<A, B>`**：用 `[A] extends [B]` + `[B] extends [A]` 双向判断 + 元组包裹阻止分发，对 `any` 也能拒绝。
11. **类型安全路由**：`ExtractRouteParams<S>` 用模板字面量 + `infer` 从 `:param` 提取参数键，构造 `RouteParams<S>` 让 handler 自动获得 params 类型。
12. **类型安全事件**：`EventMap` 当事件字典，`on/off/emit` 用 `keyof` + 索引访问约束；`emit` 用条件类型区分“有/无载荷”对应不同参数元组。
13. **类型体操的边界**：可读性 > 类型安全；递归深度有上限，复杂类型拖慢编译；合理使用 `any` / `unknown` 放过第三方库、动态元编程、原型代码；调试用临时 `type _Debug = T` + 简化输入 + 分步验证。

---

## 七、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：递归型工具类型组合（对应 `deep-types.ts`）

1. 实现 `DeepReadonly<T>` 的严格版，要求正确处理 `Date`、`RegExp`、`Map`、`Set` 等内置引用类型（提示：用 `T extends Date | RegExp | Map<any, any> | Set<any>` 特判，原样返回）。
2. 实现 `DeepPartial` 与 `DeepReadonly` 的合体版 `DeepOptionalReadonly<T>`，让所有层级字段既可选又只读，并思考：先递归 `Partial` 再递归 `Readonly`，还是合并到一个映射类型里？两者效果有何差别？
3. 实现 `DeepNonNullable<T>`：递归把所有层级的 `null | undefined` 都去掉。

**进阶**：实现 `DeepOmit<T, K>`，从 `T` 中递归地按点分路径 `K`（如 `'a.b.c'`）删除指定字段。提示：把 `K` 按 `.` 切分，递归处理，最后一层用 `Omit`。

### 练习 2：字符串类型体操（对应 `string-operations.ts`）

1. 实现 `Trim<S>`、`TrimLeft<S>`、`TrimRight<S>`：去除字符串字面量两端/左/右的空白（提示：用 `` ` ${infer S}` `` 模式匹配空格字符）。
2. 实现 `PascalCase<S>`：把任意输入（camelCase / snake_case / kebab-case）转成 PascalCase（首字母大写），如 `'user_id_card' → 'UserIdCard'`、`'myVarName' → 'MyVarName'`。
3. 实现 `ParseUrlParams<S>`：从 URL 字符串提取 query 参数键，如 `ParseUrlParams<'?a=1&b=2&c=3'>` 得到 `'a' | 'b' | 'c'`（提示：用 `infer` 模式匹配 `&` 分隔的字段）。

**进阶**：实现 `StringToTuple<S>`，把字符串字面量按字符切分为元组，如 `'abc' → ['a', 'b', 'c']`。再实现 `TupleToString<T>`，把字符元组拼回字符串。两者互为逆运算。

### 练习 3：综合实战（对应 `type-safe-router.ts` / `object-path.ts`）

1. 扩展类型安全路由器，支持通配符 `*` 和可选参数 `:param?`，并让 `RouteParams<S>` 正确反映可选参数为 `string | undefined`。
2. 实现 `set<T, P extends Path<T>, V>(obj: T, path: P, value: V): T`，按路径设置值，要求 `value` 类型必须匹配 `Get<T, P>`。注意：`set` 的不可变实现需要深拷贝，运行时实现可与 `get` 对照编写。
3. 实现类型安全的 SQL 查询构造器（见 4.3）：定义一个 `Schema` 接口描述多张表，实现 `QueryBuilder<T>` 的 `select` / `where` / `orderBy` / `limit` 方法，所有列名和值类型都强校验，最终 `build()` 返回类型安全的 `{ sql: string; params: any[] }`。

**进阶**：实现 `DeepKeyOf<T>`，返回对象所有点分路径的键名联合（与 `Path<T>` 类似，但只包含叶子路径，即值为基础类型的路径）。提示：在 `Path` 实现基础上，把“键本身”选项去掉，只保留“键 + 子路径”，并在基础类型处停止。

---

## 配套代码

| 文件 | 内容 | 运行命令 |
|------|------|----------|
| `Code/deep-types.ts` | DeepPartial / DeepReadonly / Mutable / DeepMutable 实现 + 状态管理实战 | `npm run deep` |
| `Code/pick-by-value.ts` | PickByValue / KeysOfType / Optional / Mandatory 实现 | `npm run pick` |
| `Code/my-utility.ts` | MyPick / MyOmit / MyRecord / MyReturnType / MyParameters / MyAwaited / TupleToUnion / UnionToTuple | `npm run utility` |
| `Code/string-operations.ts` | Join / Split / CamelCase / KebabCase / SnakeCase / Replace / ReplaceAll | `npm run string` |
| `Code/type-safe-router.ts` | 类型安全路由系统：路径参数提取、RouteHandler、Router、ApiMap dispatcher | `npm run router` |
| `Code/type-safe-events.ts` | 类型安全事件系统：TypedEmitter + on/off/emit/once + 派生事件 | `npm run events` |
| `Code/object-path.ts` | Path\<T\> + Get\<T, P\> + 类型安全 get + IsEqual | `npm run path` |

运行方式（需先在 `Code/` 目录执行 `npm install`）：

```bash
cd Code
npm install
npm run type-check   # 全量类型检查（不输出文件）
npm run deep         # 运行单个文件
npm run pick
npm run utility
npm run string
npm run router
npm run events
npm run path
```

> 💡 纯类型体操的“类型层面验证”由 `tsc --noEmit` 完成；含运行时演示的文件可用 `ts-node` 直接执行，会打印类型推断结果与运行时行为对照。

---

## 配套代码说明

- 所有 `.ts` 文件首行均加 `export {}` 使其成为独立模块，避免顶层声明跨文件冲突。
- `tsconfig.json` 启用 `strict: true`，所有类型推断在严格模式下成立。
- 类型体操的核心是“类型层面”，但每个文件都配了运行时演示，让 `ts-node` 能跑、能打印——便于验证类型推断与运行行为是否一致。
- 若在 IDE 中遇到 `Type instantiation is excessively deep` 错误，可适当调小 `Path<T>` 的 `Depth` 参数（默认 5）。

---

> 📚 **延伸阅读**
> - TS 官方手册：[Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)
> - TS 官方手册：[Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
> - TS 官方手册：[Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html)
> - 类型体操练习场：[type-challenges](https://github.com/type-challenges/type-challenges)
> - type-fest 工具类型库：[sindresorhus/type-fest](https://github.com/sindresorhus/type-fest)
> - 教程：[Type-Level Programming in TypeScript](https://type-level-typescript.com/)
