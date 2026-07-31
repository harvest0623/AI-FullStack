# Day08 - 高级类型与工具类型

> 本篇聚焦 TypeScript 类型系统的“高阶能力”：**高级类型**（`keyof` / `typeof` / 索引访问 / 映射类型 / 条件类型 / `infer` / 模板字面量类型）与**工具类型**（内置的 `Partial` / `Pick` / `Omit` / `Record` / `ReturnType` 等以及自定义工具类型）。如果说前几章学的还是“如何描述一个值的形状”，那么本章学的是“如何用一个类型生成另一个类型”——也就是**类型层面的编程**。高级类型是 TS 类型系统的精髓，工具类型则是日常开发中复用频率最高的“类型变换利器”，掌握它们你才能写出真正类型安全且不重复的代码。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解 - 类型查询与索引](#二理论知识讲解---类型查询与索引)
  - [2.1 keyof T：获取类型的所有键](#21-keyof-t获取类型的所有键)
  - [2.2 typeof T：从值推导类型](#22-typeof-t从值推导类型)
  - [2.3 索引访问类型 T\[K\]](#23-索引访问类型-tk)
  - [2.4 T\[number\]：获取数组/元组元素类型](#24-tnumber获取数组元组元素类型)
- [三、理论知识讲解 - 映射类型 Mapped Types](#三理论知识讲解---映射类型-mapped-types)
  - [3.1 基本语法 \[K in keyof T\]](#31-基本语法-k-in-keyof-t)
  - [3.2 修改可选性 +? / -?](#32-修改可选性--)
  - [3.3 修改只读性 +readonly / -readonly](#33-修改只读性-readonly--readonly)
  - [3.4 键重映射 as](#34-键重映射-as)
  - [3.5 过滤键（用 never 跳过）](#35-过滤键用-never-跳过)
- [四、理论知识讲解 - 条件类型 Conditional Types](#四理论知识讲解---条件类型-conditional-types)
  - [4.1 语法 T extends U ? X : Y](#41-语法-t-extends-u--x--y)
  - [4.2 分布式条件类型](#42-分布式条件类型)
  - [4.3 infer 关键字](#43-infer-关键字)
  - [4.4 infer 提取函数/构造函数类型](#44-infer-提取函数构造函数类型)
- [五、内置工具类型速览表](#五内置工具类型速览表)
- [六、自定义工具类型实战](#六自定义工具类型实战)
- [七、模板字面量类型 Template Literal Types](#七模板字面量类型-template-literal-types)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 用 `keyof T` 取出类型的所有键的联合，并配合 `K extends keyof T` 约束泛型参数，写出类型安全的属性访问器。
2. 用 `typeof` 把“值空间”的对象/函数/常量映射到“类型空间”，以对象字面量为单一数据源同时提供值与类型。
3. 用索引访问类型 `T[K]` 取出对象某属性的类型，并用 `T[number]` 取出数组/元组的元素类型，甚至从 `as const` 元组反推字面量联合。
4. 写出映射类型 `[K in keyof T]: ...`，并熟练使用 `+?` / `-?` / `+readonly` / `-readonly` 修饰符增删可选性与只读性。
5. 用键重映射 `as` 实现批量改名、加前缀、大小写转换，并用 `never` 过滤键。
6. 读懂并写出条件类型 `T extends U ? X : Y`，理解“裸类型参数”导致的分布式行为，能用 `[T]` 包裹阻止分发。
7. 用 `infer` 在条件类型中推断类型变量，实现 `ReturnType` / `Parameters` / `InstanceType` / `Awaited` 等价物。
8. 熟记内置工具类型按类别分组（属性修饰 / 对象构造 / 函数相关 / 字符串操作），并在合适场景选型。
9. 自手实现 `DeepPartial` / `DeepReadonly` / `Mutable` / `PickByValue` / `GetReturnType` / `PromiseValue` 等高频自定义工具类型。
10. 用模板字面量类型 `` `${prefix}${string}` `` 拼接字符串字面量，并结合 `keyof` + `as` 生成 `getXxx` / `setXxx` 方法名集合。

---

## 二、理论知识讲解 - 类型查询与索引

### 2.1 keyof T：获取类型的所有键

`keyof T` 是“类型查询操作符”，它把对象类型 `T` 的所有键提取为一个**联合类型**。这是后续映射类型、条件类型的基础原料。

```ts
interface User {
  id: number;
  name: string;
  email: string;
  age?: number;          // 可选属性的键也会进入 keyof 结果
  readonly role: string; // readonly 修饰不影响 keyof
}

type UserKeys = keyof User;
// 等价于：'id' | 'name' | 'email' | 'age' | 'role'
```

`keyof` 最常见的应用是**约束泛型参数**，让“键必须是对象真实存在的属性”：

```ts
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const alice: User = { id: 1, name: 'Alice', email: 'a@x.com', role: 'admin' };
getProperty(alice, 'id');     // ✅ 返回 number
// getProperty(alice, 'phone'); // ❌ 'phone' 不是 User 的键
```

几个细节值得记牢：

- `keyof` 对**索引签名**返回 `string | number`（JS 对象 key 会自动转字符串）。
- `keyof` 对**数组**返回 `number | 'length' | 'push' | 'pop' | ...`（数字索引 + 原型方法名）。
- 用 `K extends keyof T` 约束后，`T[K]` 就能精确表达“对应字段的类型”，这是类型安全访问的核心模式。

### 2.2 typeof T：从值推导类型

`typeof` 与 `keyof` 方向相反：它从**值空间**反推**类型空间**。当你已经有一个常量/对象/函数，想直接复用它的类型而不愿手写一遍时，`typeof` 是最直接的武器。

```ts
const config = {
  host: 'localhost',
  port: 3000,
  retries: 3,
  debug: true,
};

type AppConfig = typeof config;
// 等价于：{ host: string; port: number; retries: number; debug: boolean }
```

一个高频模式是：以**对象字面量作为单一数据源**，同时提供“值”与“字面量类型”：

```ts
const HTTP_STATUS = {
  OK: 200,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
} as const;                       // as const 把值固化为字面量类型

type HttpStatus = typeof HTTP_STATUS;
type OkValue = HttpStatus['OK'];  // 200（字面量类型，而非宽泛的 number）
```

`typeof` 还能拿函数签名与构造函数类型：

```ts
function greet(name: string, age?: number): string { return `Hi ${name}`; }
type GreetFn = typeof greet;      // (name: string, age?: number) => string

class Point { constructor(public x: number, public y: number) {} }
type PointCtor = typeof Point;    // 构造函数类型，可 new
type PointInstance = Point;       // 实例类型直接用类名
```

> 💡 **AI 场景联想**：调用大模型时常有一份默认配置对象，用 `typeof config` 拿到类型，既避免重复定义，又能让 `as const` 保留字面量联合以便后续做穷尽校验。

### 2.3 索引访问类型 T[K]

`T[K]` 让你在类型空间里“按 key 取属性类型”，就像运行时 `obj[key]` 一样。`K` 可以是单个键，也可以是键的**联合**。

```ts
interface Article {
  title: string;
  author: { name: string; email: string };   // 嵌套结构
  tags: string[];
  publishedAt: Date | null;
}

type TitleType  = Article['title'];                  // string
type AuthorType = Article['author'];                 // { name: string; email: string }
type Mixed      = Article['title' | 'tags'];         // string | string[]

// 链式嵌套索引
type AuthorName = Article['author']['name'];         // string
type TagsElem   = Article['tags'][number];           // string
```

索引访问是 `getProperty<T, K extends keyof T>(obj: T, key: K): T[K]` 这类强类型取值器能正确推断返回值的根本原因——`T[K]` 把“键和值类型”的对应关系保留到了类型层面。

### 2.4 T[number]：获取数组/元组元素类型

`T[number]` 是索引访问的一个特例：用 `number` 作为索引，取出数组/元组的**元素类型**。

```ts
type StrArrElem = string[][number];        // string
type NumArrElem = number[][number];        // number

// 元组：返回所有位置元素类型的联合
type Tuple3 = [string, number, boolean];
type TupleElem = Tuple3[number];           // string | number | boolean

// 配合 as const：从运行时常量数组反推字面量联合
const PALETTE = ['red', 'green', 'blue'] as const;
type Palette = typeof PALETTE;             // readonly ['red', 'green', 'blue']
type Color = Palette[number];              // 'red' | 'green' | 'blue'
```

这一模式常用来**替代手写 enum**：把可选项写成 `as const` 数组，再用 `typeof` + `[number]` 反推联合类型，既保留了运行时数据，又得到了类型约束。

```ts
const ROLES = ['admin', 'editor', 'viewer'] as const;
type Role = typeof ROLES[number];          // 'admin' | 'editor' | 'viewer'

function grant(role: Role) { /* ... */ }
grant('admin');   // ✅
// grant('owner'); // ❌ 'owner' 不在联合中
```

> 📌 更多示例见 `Code/keyof-typeof.ts`。

---

## 三、理论知识讲解 - 映射类型 Mapped Types

映射类型让你“遍历一个类型的所有键，对每个键的值类型做变换”，本质上是**类型层面的 `map`**。

### 3.1 基本语法 `[K in keyof T]`

```ts
type Identity<T> = { [K in keyof T]: T[K] };     // 恒等映射
type Promisified<T> = { [K in keyof T]: Promise<T[K]> };   // 每个字段包成 Promise
type Arrayified<T> = { [K in keyof T]: ReadonlyArray<T[K]> };
```

`[K in keyof T]` 读作“对 `T` 的每个键 `K`”，冒号后是新类型。这是 TS 最具表达力的语法之一——一行就能描述“把对象所有字段类型统一变换”的操作。

### 3.2 修改可选性 `+?` / `-?`

在键修饰位置加减 `?`，可以批量增删可选性：

```ts
type MyPartial<T>  = { [K in keyof T]?: T[K] };   // +? 所有字段变可选（等价内置 Partial）
type MyRequired<T> = { [K in keyof T]-?: T[K] };  // -? 所有字段变必填（等价内置 Required）
```

`+?` 可省略为 `?`，`-?` 则显式表示“去除可选”。`MyRequired<User>` 会让原本可选的 `age?` 也变成必填。

### 3.3 修改只读性 `+readonly` / `-readonly`

同理，`readonly` 修饰也能批量增删：

```ts
type MyReadonly<T> = { readonly [K in keyof T]: T[K] };      // +readonly（等价内置 Readonly）
type Mutable<T>    = { -readonly [K in keyof T]: T[K] };     // -readonly 去掉只读（非内置）
```

`Mutable<T>` 不是内置工具类型，但工程中极常用——把外部传入的冻结配置转成可编辑副本时几乎必写。

### 3.4 键重映射 `as`

TS 4.1 引入的 `as` 子句，允许在映射时**重命名键**。配合 `Capitalize` / `Lowercase` 等内置字符串工具，可以批量改名：

```ts
// 给所有键加前缀
type Prefixed<T, P extends string> = {
  [K in keyof T as `${P}${Capitalize<string & K>}`]: T[K];
};
// Prefixed<User, 'user'> => { userId; userName; userEmail; ... }

// 生成 getter 方法签名
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};
// Getters<User> => { getId: () => number; getName: () => string; ... }
```

`as` 后面是一个返回新键名的表达式，通常用模板字面量类型拼接。

### 3.5 过滤键（用 `never` 跳过）

在 `as` 子句里返回 `never`，表示**该键被丢弃**。配合条件类型，可以按“值的类型”筛选字段：

```ts
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};

interface MixedBag { id: number; name: string; age: number; active: boolean; tags: string[]; }
type StringFields = PickByValue<MixedBag, string>;   // { name: string; email: string }
type NumberFields = PickByValue<MixedBag, number>;   // { id: number; age: number }
```

这个“键重映射 + 条件类型 + never”的三件套，是自定义工具类型的核心套路，`Omit` / `PickByValue` / `Methods<T>` 等都可以用它实现。

> 📌 更多示例见 `Code/mapped-types.ts`。

---

## 四、理论知识讲解 - 条件类型 Conditional Types

条件类型让类型能“根据条件分支选择”，是类型层面 `if/else` 的等价物，也是 `infer` 的载体。

### 4.1 语法 `T extends U ? X : Y`

```ts
type IsString<T> = T extends string ? true : false;

type A1 = IsString<string>;     // true
type A2 = IsString<number>;     // false
type A3 = IsString<'hello'>;    // true（字面量类型也是 string 的子类型）
```

条件类型可以嵌套，形成“多重判断”：

```ts
type Serialize<T> =
  T extends string  ? `string:${T}` :
  T extends number  ? `number:${T}` :
  T extends boolean ? `bool:${T}` :
  T extends undefined ? 'undef' :
  `other:${string & T}`;
```

### 4.2 分布式条件类型

**关键规则**：当被检查的类型是**裸类型参数**（即直接是 `T`，没有被包裹）时，如果传入的是联合类型，会**自动分发**到每个成员上分别求值，最后再联合：

```ts
type ToArray<T> = T extends unknown ? T[] : never;

type D1 = ToArray<string | number>;
// 分发：ToArray<string> | ToArray<number> = string[] | number[]
// 而不是 (string | number)[]
```

这一行为既是“特性”也是“坑”。经典应用是 `Exclude` / `Extract`：

```ts
type MyExclude<T, U> = T extends U ? never : T;     // 等价内置 Exclude
type MyExtract<T, U> = T extends U ? T : never;      // 等价内置 Extract

type Roles = 'admin' | 'editor' | 'viewer' | 'guest';
type NonGuest = MyExclude<Roles, 'guest'>;           // 'admin' | 'editor' | 'viewer'
```

若想**阻止分发**，用方括号把类型参数包裹起来，让它不再是“裸”的：

```ts
type ToArrayNoDistribute<T> = [T] extends [unknown] ? T[] : never;
type D2 = ToArrayNoDistribute<string | number>;     // (string | number)[]
```

### 4.3 `infer` 关键字

`infer` 在 `extends` 右侧声明一个“待推断的类型变量”，匹配成功后可在分支里使用。它让条件类型从“判断”升级为“提取”：

```ts
type ElementOf<T> = T extends Array<infer E> ? E : never;
type El1 = ElementOf<string[]>;          // string
type El2 = ElementOf<[string, number]>;  // string | number

// 递归推断嵌套 Promise 的最终值
type UnwrapPromise<T> = T extends Promise<infer U> ? UnwrapPromise<U> : T;
type P = UnwrapPromise<Promise<Promise<string>>>;   // string
```

`infer` 配合递归，能展开任意深度的嵌套结构，这是 `Awaited<T>` 的实现原理。

### 4.4 `infer` 提取函数/构造函数类型

`infer` 最实用的场景是从函数签名中提取参数与返回值类型——内置的 `Parameters` / `ReturnType` / `ConstructorParameters` / `InstanceType` 全都基于此：

```ts
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
type MyParameters<T> = T extends (...args: infer P) => any ? P : never;
type MyInstanceType<T> = T extends new (...args: any[]) => infer I ? I : never;
type MyConstructorParams<T> = T extends new (...args: infer P) => any ? P : never;
```

注意几个细节：

- `infer R` 写在返回值位置 → 提取返回值类型。
- `infer P` 写在 `...args` 位置 → 提取参数元组。
- `new (...args) => infer I` → 提取构造函数的实例类型。
- `infer` 可以出现在元组的任意位置：`T extends [infer F, ...unknown[]] ? F : never` 提取首元素；`T extends [...unknown[], infer L] ? L : never` 提取尾元素。

> 📌 更多示例见 `Code/conditional-types.ts`。

---

## 五、内置工具类型速览表

TS 内置了一批高频工具类型，按用途分为四类。下表是日常开发速查表，**`Mutable<T>` 非内置**，标注为自定义。

### 属性修饰类

| 工具类型 | 作用 | 示例 |
|---------|------|------|
| `Partial<T>` | 所有字段变可选 | `Partial<User>` → `{ id?: number; ... }` |
| `Required<T>` | 所有字段变必填（含原本可选的） | `Required<User>` → `age: number`（不再可选） |
| `Readonly<T>` | 所有字段变只读 | `Readonly<User>` → 无法赋值 |
| `Mutable<T>` ⚠️非内置 | 去掉所有 readonly | `Mutable<FrozenConfig>` → 可写字段 |

### 对象构造类

| 工具类型 | 作用 | 示例 |
|---------|------|------|
| `Pick<T, K>` | 从 T 中挑选指定键 | `Pick<User, 'id' \| 'name'>` → `{ id; name }` |
| `Omit<T, K>` | 从 T 中排除指定键 | `Omit<User, 'email'>` → 去掉 email |
| `Record<K, T>` | 构造键为 K、值为 T 的对象 | `Record<'a' \| 'b', number>` → `{ a: number; b: number }` |
| `Exclude<T, U>` | 从联合 T 中排除可赋给 U 的成员 | `Exclude<'a' \| 'b' \| 'c', 'a'>` → `'b' \| 'c'` |
| `Extract<T, U>` | 从联合 T 中提取可赋给 U 的成员 | `Extract<string \| number, string>` → `string` |
| `NonNullable<T>` | 从 T 中排除 null 与 undefined | `NonNullable<string \| null>` → `string` |

### 函数相关类

| 工具类型 | 作用 | 示例 |
|---------|------|------|
| `Parameters<T>` | 函数参数元组类型 | `Parameters<(a: number, b: string) => void>` → `[number, string]` |
| `ReturnType<T>` | 函数返回值类型 | `ReturnType<() => User>` → `User` |
| `ConstructorParameters<T>` | 构造函数参数元组 | `ConstructorParameters<typeof Point>` → `[number, number]` |
| `InstanceType<T>` | 构造函数实例类型 | `InstanceType<typeof Point>` → `Point` |
| `Awaited<T>` | 递归展开 Promise 的最终值 | `Awaited<Promise<Promise<number>>>` → `number` |

### 字符串操作类

| 工具类型 | 作用 | 示例 |
|---------|------|------|
| `Uppercase<S>` | 字面量转大写 | `Uppercase<'hi'>` → `'HI'` |
| `Lowercase<S>` | 字面量转小写 | `Lowercase<'Hi'>` → `'hi'` |
| `Capitalize<S>` | 首字母大写 | `Capitalize<'foo'>` → `'Foo'` |
| `Uncapitalize<S>` | 首字母小写 | `Uncapitalize<'Foo'>` → `'foo'` |

> 📌 全部内置工具类型的逐一演示见 `Code/utility-types.ts`。

---

## 六、自定义工具类型实战

内置工具类型覆盖了“一层”变换，但真实工程常需要递归或按值筛选，这时就得手写自定义工具类型。

### DeepPartial：递归可选

普通 `Partial` 只做一层，嵌套对象仍是必填。递归版用条件类型判断“字段是否为对象”，再进入一层做 `Partial`：

```ts
type DeepPartial<T> = T extends object
  ? { [K in keyof T]?: DeepPartial<T[K]> }
  : T;
```

典型用途：表单 patch 时只填嵌套对象的某一层，无需补全整个结构。

### DeepReadonly：递归只读

同理递归加 `readonly`，注意对数组需要特殊处理为 `ReadonlyArray`：

```ts
type DeepReadonly<T> =
  T extends (...args: any[]) => any ? T :
  T extends Array<infer U> ? ReadonlyArray<DeepReadonly<U>> :
  T extends object ? { readonly [K in keyof T]: DeepReadonly<T[K]> } :
  T;
```

把对象存入 store 后冻结，防止后续误改，是它的典型场景。

### Mutable：去掉 readonly

```ts
type Mutable<T> = { -readonly [K in keyof T]: T[K] };
```

递归版 `DeepMutable` 只需在上述分支结构里把 `{ -readonly ... }` 套进去。

### PickByValue：按值类型筛选字段

用“键重映射 + 条件类型 + never”三件套：

```ts
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};
```

反向 `OmitByValue` 只需把条件取反。进阶版 `NonNullableFields<T>` 只保留“值是非空类型”的字段，判断逻辑是 `T[K] extends NonNullable<T[K]>`（原始类型能否赋给去 null 后的类型）。

### GetReturnType：从函数类型提取返回值

```ts
type GetReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
```

对函数联合类型，想分别提取每个成员的返回值再联合，需要让条件类型**分发**——保持 `T` 为裸类型参数即可：

```ts
type GetReturnTypes<T> = T extends (...args: any[]) => any ? ReturnType<T> : never;
type R = GetReturnTypes<(() => number) | (() => string)>;   // number | string
```

### PromiseValue：递归展开 Promise

等价于内置 `Awaited<T>`，但手写一遍能加深对 `infer` + 递归条件类型的理解：

```ts
type PromiseValue<T> = T extends Promise<infer U>
  ? U extends Promise<unknown>
    ? PromiseValue<U>
    : U
  : T;
```

实战中常配合 `ReturnType` 从异步函数签名反推“最终值类型”：

```ts
async function fetchArticle() { return { id: 1, title: 'TS' }; }
type Article = PromiseValue<ReturnType<typeof fetchArticle>>;   // { id: number; title: string }
```

> 📌 全部实现与综合实战见 `Code/custom-utility.ts`。

---

## 七、模板字面量类型 Template Literal Types

模板字面量类型把 JS 的模板字符串语法搬到了类型空间，让我们能拼接、匹配字符串字面量。

### 基本拼接

```ts
type Greeting = `hello ${string}`;          // 任意以 "hello " 开头的字符串
type Margin = `margin-${'top' | 'right' | 'bottom' | 'left'}`;   // 4 种联合
type BtnClass = `btn-${'sm' | 'md' | 'lg'}-${'red' | 'green' | 'blue'}`;  // 9 种笛卡尔积
```

多个联合拼接会产生**笛卡尔积**，一行就能枚举出大量合法字面量。

### 结合 Uppercase / Capitalize

```ts
type Field = 'name' | 'age' | 'email';
type ConstName = `CONFIG_${Uppercase<Field>}`;    // 'CONFIG_NAME' | 'CONFIG_AGE' | 'CONFIG_EMAIL'
```

### 结合 keyof + as 生成 getter / setter 名

这是模板字面量类型最经典的用法：为一个对象类型自动生成所有 getter/setter 方法签名集合。

```ts
interface User { id: number; name: string; email: string; }

type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};
type Setters<T> = {
  [K in keyof T as `set${Capitalize<string & K>}`]: (value: T[K]) => void;
};
type Accessors<T> = Getters<T> & Setters<T>;

// Accessors<User> 既有 getId/getName/getEmail，也有 setId/setName/setEmail
```

进一步可以扩展到事件名（`${Module}.${Action}`）、路由路径（`/api/${string}`）、CSS 类名（`col-${Breakpoint}-${Span}`）等场景。配合条件类型与 `infer`，还能实现 `SnakeToCamel` 这类字符串模式匹配转换：

```ts
type SnakeToCamel<S extends string> =
  S extends `${infer Head}_${infer Tail}`
    ? `${Head}${Capitalize<SnakeToCamel<Tail>>}`
    : S;
type C = SnakeToCamel<'user_id_card'>;   // 'userIdCard'
```

> 📌 更多示例（含强类型 fetch、事件监听器、CSS 类名生成）见 `Code/template-literal.ts`。

---

## 八、关键知识点总结

1. **`keyof T`** 取出类型的键联合，配合 `K extends keyof T` 约束泛型参数，是类型安全属性访问的基石。
2. **`typeof T`** 从值反推类型，常配合 `as const` 保留字面量，实现“值与类型同源”。
3. **`T[K]` 索引访问** 可单键、可联合键、可链式嵌套；`T[number]` 取数组/元组元素类型。
4. **映射类型 `[K in keyof T]: ...`** 是类型层面的 `map`，一行描述“对所有字段统一变换”。
5. **`+?` / `-?` / `+readonly` / `-readonly`** 四个修饰符分别增删可选性与只读性；`Mutable<T>` 非内置但极常用。
6. **键重映射 `as`** 可批量改名（加前缀、大小写转换），返回 `never` 则过滤键——这是 `PickByValue` 等工具的实现核心。
7. **条件类型 `T extends U ? X : Y`** 是类型层面的 `if/else`；裸类型参数对联合会**自动分发**，用 `[T]` 包裹可阻止分发。
8. **`infer`** 在条件类型中提取类型变量，是 `ReturnType` / `Parameters` / `InstanceType` / `Awaited` 的统一实现机制。
9. **内置工具类型四类**：属性修饰、对象构造、函数相关、字符串操作；记不住时查速览表，用时按场景选型。
10. **自定义工具类型**：`DeepPartial` / `DeepReadonly` 需要递归 + 对数组/函数特殊处理；`PickByValue` 用键重映射 + 条件类型 + never。
11. **模板字面量类型** `` `${a}${b}` `` 拼接字面量，多联合产生笛卡尔积；配合 `keyof` + `as` 可自动生成 `getXxx` / `setXxx` 方法名集合。
12. **同目录多文件**：每个 `.ts` 文件加 `export {}` 成为独立模块，可避免顶层声明（同名 interface / class / type）跨文件冲突与意外声明合并。

---

## 九、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：类型安全的属性访问器（对应 `keyof-typeof.ts`）

定义一个 `Book` 接口（含 `title` / `author` / `pageCount` / `tags` 等字段），实现：

1. `getProperty<T, K extends keyof T>(obj: T, key: K): T[K]`，要求传入不存在的键时编译报错。
2. 用 `typeof` + `as const` 定义一个 `STATUSES = ['draft', 'published', 'archived'] as const`，反推 `Status` 联合类型，并实现 `nextStatus(s: Status): Status` 做状态流转。
3. 用 `T[number]` 提取 `Book['tags']` 的元素类型。

**进阶**：写一个 `pickFields<T, K extends keyof T>(obj: T, keys: K[]): Pick<T, K>`，从对象中挑选多个字段返回新对象，要求返回类型精确为 `Pick<T, K>` 而非宽泛的 `Partial<T>`。

### 练习 2：自定义工具类型（对应 `custom-utility.ts`）

实现以下自定义工具类型并编写测试用例验证：

1. `DeepMutable<T>`：递归去掉所有层级的 `readonly`（参考 `DeepReadonly` 的反向实现）。
2. `PickByValue<T, V>` 与 `OmitByValue<T, V>`：按值类型筛选/排除字段。
3. `Getters<T>`：为对象类型生成所有 getter 方法签名集合（用 `keyof` + `as` + `Capitalize`）。
4. `PromiseValue<T>`：递归展开 `Promise` 拿到最终值类型（不使用内置 `Awaited`）。

**进阶**：实现 `NonNullableFields<T>`，只保留“值类型不含 `null` / `undefined`”的字段。提示：判断条件是 `T[K] extends NonNullable<T[K]>`，思考为什么是这个方向而不是反向。

### 练习 3：模板字面量类型建模（对应 `template-literal.ts`）

1. 定义一个 `EventMap` 接口（如 `click: { x: number; y: number }; change: { value: string }; ...`），用模板字面量类型 + 映射类型生成 `on${Capitalize<K>}` 形式的监听器类型，并实现一个强类型 `on(event, handler)` 函数，要求 handler 的参数类型必须严格匹配 `EventMap[K]`。
2. 用模板字面量类型定义一组 API 路径字面量（如 `/users` / `/users/${number}` / `/posts/${number}/comments`），并实现一个 `api<P extends ApiPath>(path: P, params: ApiParams<P>): Promise<ApiResponse<P>>` 函数，让参数与返回值类型随路径自动推断。

**进阶**：实现 `SnakeToCamel<S>`，把 `'user_id_card'` 这样的 snake_case 字面量转成 `'userIdCard'`（提示：用 `infer` 模式匹配 `${Head}_${Tail}` 并递归）。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/keyof-typeof.ts` | keyof / typeof / 索引访问 T[K] / T[number] / 强类型 get-set 访问器 |
| `Code/mapped-types.ts` | 映射类型语法、+/-修饰符、键重映射 as、过滤键（never） |
| `Code/conditional-types.ts` | 条件类型、分布式条件类型、infer 提取函数/构造函数类型 |
| `Code/utility-types.ts` | 全部内置工具类型按四类逐一演示 |
| `Code/custom-utility.ts` | DeepPartial / DeepReadonly / Mutable / PickByValue / GetReturnType / PromiseValue |
| `Code/template-literal.ts` | 模板字面量拼接、大小写工具、结合 keyof+as 生成 getter/setter、强类型 fetch |

运行方式（需先在 `Code/` 目录执行 `npm install`）：

```bash
cd Code
npm install
npx ts-node keyof-typeof.ts
npx ts-node mapped-types.ts
npx ts-node conditional-types.ts
npx ts-node utility-types.ts
npx ts-node custom-utility.ts
npx ts-node template-literal.ts
```

或使用 `package.json` 中预置的脚本：

```bash
npm run keyof        # 等价于 ts-node keyof-typeof.ts
npm run mapped
npm run conditional
npm run utility
npm run custom
npm run template
npm run type-check   # 全量类型检查（不输出文件）
```

---

> 📚 **延伸阅读**
> - TS 官方手册：[Indexed Access Types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html)
> - TS 官方手册：[Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
> - TS 官方手册：[Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)
> - TS 官方手册：[Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html)
> - TS 官方手册：[Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)
> - TS 4.1 Release Notes：键重映射 `as` 与模板字面量类型
> - TS 4.7 Release Notes：`infer extends` 与实例化表达式
> - 社区类型体操：[type-challenges](https://github.com/type-challenges/type-challenges)
