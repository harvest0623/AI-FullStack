# Day 03 - 接口与类型别名

TypeScript 描述对象形状有两大主力——`interface` 与 `type`。前者更"面向对象"，强调可扩展、可合并；后者更"函数式"，能表达联合、交叉、条件、映射等类型级运算。本章把两者的语法、能力边界、决策准则一次讲透，并配合结构化类型、多余属性检查、函数签名等核心机制，让你写出的类型既能挡住 bug，又不会变成"类型债"。

---

## 一、学习目标

完成本章后，你应当能够：

1. 用 `interface` 描述对象形状，正确使用可选属性 `?`、只读属性 `readonly` 与多余属性检查。
2. 用 `type` 别名定义对象、联合、交叉、元组、函数类型，并理解它与 `interface` 的本质差异。
3. 在 `interface extends` / `type &` / 声明合并 / 条件类型 / 映射类型 之间做出正确取舍。
4. 用索引签名 `[key: string]: T` 与 `Record<string, T>` 描述动态键对象，并知晓两者各自的局限。
5. 用调用签名、构造签名约束"函数对象"与"可 new 的类"，写出 jQuery 风格的混合类型。
6. 理解结构化类型、鸭式辩型、赋值兼容规则，以及函数参数的逆变特性。
7. 为 API 响应、配置对象、DTO 设计出"既精确又可扩展"的类型层。

---

## 二、理论知识讲解

### 2.1 接口 interface

`interface` 是 TS 描述对象形状最经典的工具——它只声明"有哪些字段、字段是什么类型"，不参与运行时（编译后完全擦除）。

#### 基本定义

```ts
interface User {
  id: number;
  name: string;
  email: string;
}

const alice: User = { id: 1, name: 'Alice', email: 'alice@example.com' };
```

字段顺序无关紧要，TS 只看"形状是否匹配"。

#### 可选属性 `?`

在属性名后加 `?` 表示该字段可缺省：

```ts
interface Article {
  title: string;
  tags?: string[];       // 可选
  publishedAt?: Date;    // 可选
}

const a: Article = { title: 'TS 入门' };   // 合法
```

读取可选属性时要先做 narrowing，否则 `.length` 等访问会触发 `Object is possibly undefined`。

#### 只读属性 `readonly`

`readonly` 修饰的属性只能在初始化时赋值，之后不可改：

```ts
interface Repo {
  readonly owner: string;
  readonly name: string;
  stars: number;
}

const repo: Repo = { owner: 'torvalds', name: 'linux', stars: 100000 };
// repo.owner = 'linus';   // ❌ TS2540
repo.stars++;              // ✅ stars 不是 readonly
```

> **陷阱**：`readonly` 是【浅层】的——只锁属性本身，不递归到嵌套对象。`win.size.width = 1024` 仍可改。需要深度不可变时用 `Readonly<T>` 或自定义 `DeepReadonly<T>`。

#### 多余属性检查 Excess Property Checking

当【对象字面量】直接赋值给一个有明确类型的变量时，TS 会额外做一道"多余属性检查"——字面量里出现目标类型没有的字段就报错：

```ts
interface LoginPayload {
  username: string;
  password: string;
}

// ❌ 多了 remember
// const bad: LoginPayload = { username: 'bob', password: '123456', remember: true };
```

这是【字面量专属】的额外保护，目的是挡住"拼错字段名"这类低级错误。详见 [2.9 节](#29-多余属性检查再探)。

### 2.2 类型别名 type alias

`type` 给一个【类型】起名字，能力比 `interface` 更宽：除了对象形状，还能别名基本类型、联合、交叉、元组、函数等。

```ts
type ID = number | string;
type Point = [number, number];
type Callback = (err: Error | null, data?: unknown) => void;

type User = {
  id: number;
  name: string;
  email: string;
};
```

描述对象形状时，`type` 与 `interface` 表面几乎等价——可选 `?`、只读 `readonly`、多余属性检查规则全部一致：

```ts
type Article = {
  readonly title: string;
  tags?: string[];
};
```

#### type 独有的扩展：交叉类型 `&`

`interface` 用 `extends` 扩展，`type` 用 `&` 做交叉：

```ts
type Timestamps = { createdAt: Date; updatedAt: Date };
type Note = { title: string; content: string } & Timestamps;

const note: Note = {
  title: '日记',
  content: '今天学了 type 别名',
  createdAt: new Date(),
  updatedAt: new Date(),
};
```

### 2.3 interface vs type 深度对比

| 维度 | `interface` | `type` |
| --- | --- | --- |
| **基本用途** | 描述对象 / 函数 / 类形状 | 别名任何类型（含基本、联合、交叉、元组） |
| **扩展方式** | `extends`，支持多继承 `interface A extends B, C` | `&` 交叉类型 `type A = B & C` |
| **声明合并** | ✅ 同名自动合并（独有的特性） | ❌ 同名报 `Duplicate identifier` |
| **联合类型** | ❌ 不能表达 `A \| B` | ✅ `type A = B \| C` |
| **交叉类型** | ❌ 只能 `extends` | ✅ `type A = B & C` |
| **元组类型** | ❌ 无法描述 | ✅ `type Pair = [number, string]` |
| **条件类型** | ❌ 不支持 `T extends U ? X : Y` | ✅ 支持 |
| **映射类型** | ❌ `{ [K in keyof T]: ... }` 非法 | ✅ 支持 |
| **`keyof` / `infer`** | ❌ 不能在内部使用 | ✅ 可用于类型级编程 |
| **可被 `implements`** | ✅ 类可以 `implements` | ✅ 类可以 `implements`（对象字面量形式） |
| **类型计算能力** | 弱（仅静态形状） | 强（可写工具类型、递归类型） |
| **错误提示可读性** | 通常更友好（具名形状） | 联合/交叉展开后可能很长 |
| **第三方扩展** | ✅ 通过声明合并给库补字段 | ❌ 无法合并，只能重新 `&` |
| **命名规范** | PascalCase 名词（`User`、`Repository`） | PascalCase（`Nullable<T>`、`ID`、`Status`） |
| **何时优先用** | 对象形状、可被外部扩展合并 | 联合 / 交叉 / 工具类型 / 元组 / 基本类型别名 |

#### 声明合并示例

```ts
interface ServerConfig { host: string; port: number }
interface ServerConfig { timeout?: number }   // 自动合并进来
interface ServerConfig { retry: number }      // 再合并

const cfg: ServerConfig = { host: '0.0.0.0', port: 8080, retry: 3 };
```

#### 类型计算能力示例

```ts
// ❌ interface 做不到——以下均为语法错误
// interface ID = number | string;                              // interface 不能用 =
// interface Frozen<T> { [K in keyof T]: T[K] }                 // 映射类型非法
// interface IsString<T> = T extends string ? true : false;     // 语法错误

// ✅ type 可以
type Nullable<T> = T | null;
type Frozen<T> = { readonly [K in keyof T]: T[K] };
type IsString<T> = T extends string ? true : false;
type UserKeys = keyof { id: number; name: string };   // 'id' | 'name'
```

#### 决策准则

> **对象形状优先 `interface`，联合/交叉/工具类型用 `type`。**
>
> - 描述对外暴露的对象 API、可能被社区扩展的库类型 → `interface`
> - 描述联合（`'idle' | 'loading' | 'success'`）、元组、工具类型 → `type`
> - 团队混用最常见，React + TS 项目里两者都会大量出现，保持一致即可

### 2.4 索引签名

当对象的 key 是动态的、且所有 value 类型一致时，用索引签名：

```ts
interface Scores {
  [subject: string]: number;
}

const s: Scores = { math: 90, english: 85 };
```

#### 索引签名 + 已知属性

可以同时声明已知属性和索引签名，但**已知属性的类型必须兼容索引签名的 value 类型**：

```ts
interface Locale {
  lang: string;           // 已知属性
  [key: string]: string;  // 索引签名——lang 也是 string，兼容
}

// ❌ 报错：count: number 与 [key: string]: string 不兼容
// interface Bad { count: number; [key: string]: string }
```

#### 字符串索引与数字索引共存规则

JS 中 `obj[0]` 实际上是用字符串 `'0'` 查的，所以 TS 要求：**数字索引的 value 类型必须是字符串索引 value 类型的子类型**。

```ts
interface Dictionary {
  [key: string]: string;
  [key: number]: string;    // ✅ 同类型，兼容
}

// ❌ number 不是 string 的子类型
// interface BadDict { [key: string]: string; [key: number]: number }
```

#### 索引签名 vs `Record<string, T>`

`Record<K, V>` 是 TS 内置工具类型，本质是索引签名的语法糖：

```ts
interface IScores { [k: string]: number }
type RScores = Record<string, number>;
// 两者几乎等价
```

`Record` 的优势在于**可以用联合类型作为 key**，比索引签名更精确：

```ts
type HttpStatus = 200 | 404 | 500;
type StatusText = Record<HttpStatus, string>;

const statusText: StatusText = {
  200: 'OK',
  404: 'Not Found',
  500: 'Internal Server Error',
};
// 索引签名做不到：[k: 200 | 404 | 500] 非法
```

#### 索引签名的局限

1. **value 类型只能统一一个 T**，无法区分不同 key 的不同类型——读取后类型被"抹平"为联合。
2. **无法表达"key 必须是某些值之一"**——这一点 `Record<联合, V>` 解决了。
3. **value 是对象时需要写完整形状**，否则丢失字段类型。

需要"精确的若干 key + 各自的 value 类型"时，直接写 `interface` / 对象 `type` 才最精确：

```ts
interface PreciseConfig {
  host: string;
  port: number;     // 一定是 number，不会丢失
  debug: boolean;
}
```

### 2.5 函数类型

TS 描述函数类型有三种写法，外加调用签名与构造签名两个高级特性。

#### 三种写法

```ts
// 写法 1：type 箭头函数语法（最常用）
type Mapper<T, U> = (value: T, index: number) => U;

// 写法 2：interface + 调用签名
interface Reducer<T> {
  (acc: T, current: T): T;
}

// 写法 3：内联函数类型字面量
function run(fn: (x: number) => number, input: number): number {
  return fn(input);
}
```

#### 调用签名 Call Signature

当一个函数本身还需要挂载属性时（如 jQuery 的 `$`、可重置的 `counter`），必须用调用签名——`type` 箭头语法做不到挂属性：

```ts
interface Counter {
  (): number;          // 调用签名
  reset(): void;       // 挂载的方法
  count: number;       // 挂载的属性
}
```

#### 构造签名 Construct Signature

当类型需要被 `new` 调用（即作为类/构造函数）时，用 `new` 签名：

```ts
interface PointCtor {
  new (x: number, y: number): Point2D;
  origin: Point2D;     // 静态属性
}

// 用构造签名约束"工厂"——接收一个构造函数并实例化
function instantiate<C extends new (...args: any[]) => any>(
  ctor: C,
  ...args: any[]
): InstanceType<C> {
  return new ctor(...args);
}
```

`interface` 可同时描述"普通调用"和 `new` 调用——这是 `type` 箭头语法做不到的，常用于 jQuery 风格的 `$` 函数（既可调用又可 `new`）。

### 2.6 可索引类型

`string` 索引与 `number` 索引可在同一个 `interface` 中共存，规则见 [2.4 节](#24-索引签名)。

| 索引类型 | 用途 | 限制 |
| --- | --- | --- |
| `[key: string]: T` | 字典、配置表、缓存 | value 必须统一类型 |
| `[key: number]: T` | 数组、按 ID 索引的列表 | 必须是 string 索引的子类型 |
| `Record<K, V>` | 精确 key 的查表 | K 必须是 `string \| number \| symbol` 联合 |

### 2.7 接口继承

`interface` 用 `extends` 支持多继承，覆盖属性时需保持兼容（子类型不能比父类型"更窄"）：

```ts
interface Animal { name: string }
interface Bear extends Animal { honey: boolean }
interface Dog extends Animal { bark(): void }
interface Husky extends Dog, Bear { sled?: boolean }   // 多继承
```

#### 覆盖属性需兼容

```ts
interface Base { info: { name: string } }
interface Derived extends Base {
  info: { name: string; age: number };   // ✅ 子类型，更具体
}

// ❌ 反过来不允许：父类型 info 有 name，子类型 info 去掉 name 会报错
// interface Bad extends Base { info: { age: number } }
```

### 2.8 类型兼容性

TS 是**结构化类型系统**（structural typing）——只看"形状"不看"名字"。这就是著名的**鸭式辩型**（duck typing）：走起来像鸭子、叫起来像鸭子，那就是鸭子。

#### 鸭式辩型

```ts
interface User { name: string; age: number }
interface Person { name: string; age: number }

const u: User = { name: 'Alice', age: 30 };
const p: Person = u;     // ✅ 形状一致，名字不同也行
```

#### 赋值兼容规则

- **超集 → 子集**：拥有更多字段的对象可以赋给字段更少的目标（多出来的字段不影响）。
- **子集 → 超集**：不行，会缺字段。

```ts
interface Employee { name: string; age: number; salary: number }
const emp: Employee = { name: 'Bob', age: 25, salary: 8000 };

const u2: User = emp;    // ✅ Employee 是 User 的超集
// const emp2: Employee = u;   // ❌ 缺 salary
```

类的实例同样走结构化兼容——`class Cat` 的实例只要有 `name` 和 `age`，就能赋给 `User`。

#### 函数参数：协变与逆变

函数赋值时的兼容规则：

| 维度 | 规则 | 记忆 |
| --- | --- | --- |
| 返回值 | 源返回类型必须是目标返回类型的**子类型** | 协变（一起变窄） |
| 参数 | 源参数类型必须是目标参数类型的**超类型** | 逆变（反方向变窄） |

通俗记忆：**能接收更"宽"参数的函数，能赋给要求更"窄"参数的位置**——因为它能处理任何窄类型。

```ts
type Sub = { name: string; age: number };   // 窄
type Sup = { name: string };                // 宽

type NeedSub = (x: Sub) => void;
type HaveSup = (x: Sup) => void;

const haveSup: HaveSup = (x) => console.log(x.name);
const needSub: NeedSub = haveSup;   // ✅ 逆变
```

> **注**：方法简写（`log(x: T): void`）默认是双变量（bivariant）的，函数属性（`log: (x: T) => void`）在 `strictFunctionTypes` 下才是严格逆变。日常代码记住"宽函数可赋给窄位置"即可。

### 2.9 多余属性检查再探

[2.1 节](#21-接口-interface)提到多余属性检查只对**对象字面量直接赋值**触发。三种绕过方式：

```ts
interface LoginPayload { username: string; password: string }

// ❌ 字面量直接赋值，多了字段 → 报错
// const bad: LoginPayload = { username: 'bob', password: '123456', remember: true };

// 绕过 1：变量中转——TS 只对字面量做检查，变量走结构化兼容
const raw = { username: 'bob', password: '123456', remember: true };
const bypassed: LoginPayload = raw;   // ✅

// 绕过 2：类型断言
const asserted: LoginPayload = {
  username: 'bob', password: '123456', remember: true,
} as LoginPayload;

// 绕过 3：在目标类型上加索引签名（不推荐，丢失精确性）
// interface LoginPayload { username: string; password: string; [k: string]: unknown }
```

| 触发场景 | 是否检查 | 原因 |
| --- | --- | --- |
| 字面量直接赋值给变量 | ✅ 检查 | 防拼错字段名 |
| 字面量直接作为函数参数 | ✅ 检查 | 同上 |
| 变量中转后赋值 | ❌ 不检查 | 走结构化兼容 |
| 类型断言 `as T` | ❌ 不检查 | 程序员明确声明 |
| 加索引签名 `[k: string]: unknown` | ❌ 不检查 | 任意 key 都被允许 |

---

## 三、实战模式

### 3.1 API 响应类型

后端 API 响应通常有"包裹层 + 数据 + 错误"三件套，用 `interface` 描述最直观：

```ts
// 统一响应包裹
interface ApiResponse<T> {
  code: number;            // 业务码：0 成功，非 0 失败
  message: string;
  data: T | null;          // 失败时为 null
  traceId: string;         // 链路追踪 ID
}

// 分页响应
interface Paginated<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
}

// 业务实体
interface Article {
  id: string;
  title: string;
  body: string;
  tags: string[];
  authorId: string;
  publishedAt: Date | null;
}

// 组合：分页文章响应
type ArticleListResponse = ApiResponse<Paginated<Article>>;
```

> **要点**：包裹层用 `interface`（便于声明合并扩展业务字段），组合后的具体响应类型用 `type`（一次性别名，无需扩展）。

### 3.2 配置对象类型

配置对象的特点：字段多、大多可选、有默认值、可能被外部扩展。用 `interface` 便于声明合并：

```ts
interface AppConfig {
  port: number;
  host: string;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  cors?: {
    origins: string[];
    credentials: boolean;
  };
  cache?: {
    ttl: number;          // 秒
    driver: 'memory' | 'redis';
  };
}

const config: AppConfig = {
  port: 8080,
  host: '0.0.0.0',
  logLevel: 'info',
  cors: { origins: ['https://example.com'], credentials: true },
};

// 第三方插件可以通过声明合并补字段
interface AppConfig {
  pluginX?: { enabled: boolean };
}
```

> **要点**：嵌套对象用 `interface` 内联形状即可；若嵌套层级深且复用多，再抽出独立 `interface`。

### 3.3 DTO 类型设计

DTO（Data Transfer Object）是跨进程传输的"瘦"对象。设计原则：**精确、扁平、可序列化**。

```ts
// 入参 DTO——用 type + 联合表达"二选一"字段
type CreateArticleDTO = {
  title: string;
  body: string;
  tags?: string[];
  // 二选一：要么指定 authorId，要么指定 authorEmail
} & (
  | { authorId: string; authorEmail?: never }
  | { authorId?: never; authorEmail: string }
);

// 出参 DTO——用 interface 描述，便于前端扩展
interface ArticleDTO {
  id: string;
  title: string;
  summary: string;        // 不返回完整 body，节省带宽
  tags: string[];
  author: { id: string; name: string };
  publishedAt: string;    // ISO 字符串，不是 Date——便于 JSON 序列化
}

// 更新 DTO——所有字段可选，Partial 工具类型
type UpdateArticleDTO = Partial<Pick<ArticleDTO, 'title' | 'summary' | 'tags'>>;
```

> **设计要点**：
> - DTO 不要直接复用领域实体（如 `Article` 含 `Date`、`Buffer` 等不可序列化字段）
> - 出参用 `interface` 便于前端扩展；入参用 `type + 联合` 表达精确约束
> - 字段名与后端 JSON 一致，避免运行时映射层

---

## 四、关键知识点总结

1. **`interface` 与 `type` 描述对象形状时几乎等价**：可选 `?`、只读 `readonly`、多余属性检查规则一致。
2. **`interface` 独有声明合并**：同名 `interface` 自动合并，常用于扩展第三方库类型。
3. **`type` 独有类型级编程**：联合 `|`、交叉 `&`、元组、条件类型、映射类型、`keyof` / `infer` 全部只能用 `type`。
4. **扩展方式**：`interface extends`（含多继承）vs `type &`（交叉）。
5. **决策准则**：对象形状 / 可被外部扩展 → `interface`；联合 / 工具类型 / 元组 / 基本类型别名 → `type`。
6. **索引签名**：`[key: string]: T` 描述动态键；与 `Record<string, T>` 等价，但 `Record` 可用联合 key 更精确。
7. **数字索引必须是字符串索引的子类型**：因为 JS 中 `obj[0]` 实际查的是 `'0'`。
8. **函数三件套**：箭头语法 `type Fn = (x) => R`、调用签名 `(x): R`（可挂属性）、构造签名 `new (x): R`（可 `new`）。
9. **结构化类型 + 鸭式辩型**：只看形状不看名字，超集可赋给子集，类实例同样适用。
10. **多余属性检查只对字面量直接赋值触发**：变量中转、类型断言、加索引签名三种绕过方式。
11. **函数兼容**：返回值协变、参数逆变；方法简写默认双变量，`strictFunctionTypes` 下严格逆变。

---

## 五、实战练习

### 练习 1：设计一个用户管理 API 的类型层

**目标**：基于本章知识，为下列 RESTful 接口设计 TS 类型。

接口清单：

- `GET /users/:id` → 返回单个用户
- `GET /users?page=1&pageSize=20` → 分页返回用户列表
- `POST /users` → 创建用户
- `PATCH /users/:id` → 部分更新用户
- `DELETE /users/:id` → 删除（返回空 data）

**要求**：

1. 定义 `User` 实体（含 `id`、`name`、`email`、`role: 'admin' | 'editor' | 'viewer'`、`createdAt`）。
2. 用 `ApiResponse<T>` 包裹所有响应，`data` 失败时为 `null`。
3. 用 `Paginated<T>` 描述列表响应。
4. 用 `Partial<T>` + `Pick` 描述 `UpdateUserDTO`，确保 `id` / `createdAt` 不可改。
5. 用 `type + 联合 + never` 让 `CreateUserDTO` 中 `email` 与 `phone` 二选一。

**参考位置**：在 `Code/` 目录下新建 `exercise-user-api.ts`，参考 [3.1](#31-api-响应类型)、[3.3](#33-dto-类型设计) 节的模式实现。

**验收**：

- `npx tsc --noEmit exercise-user-api.ts` 无报错。
- 故意写一个 `UpdateUserDTO` 含 `id` 字段的对象，应报类型错误。

### 练习 2：体验声明合并与类型计算

**目标**：对比 `interface` 与 `type` 在扩展场景下的差异。

**步骤**：

1. 定义 `interface Window { __APP_VERSION__: string }`，再定义同名 `interface Window` 加 `__DEBUG__: boolean`，验证两者自动合并。
2. 尝试用 `type` 定义同名类型两次，观察 `Duplicate identifier` 报错。
3. 用 `type` 实现 `DeepReadonly<T>`，把一个嵌套对象类型 `Tree` 全部字段变成只读，验证 `t.left.value = 99` 报错。
4. 用 `Record<'a' | 'b' | 'c', number>` 创建一个精确键的字典，故意漏掉 `'c'`，观察报错。

**验收**：

- 能用一句话说清"声明合并"和"交叉类型"的区别。
- 能用一句话说清"索引签名"和"`Record<联合, V>`"的区别。

### 练习 3：结构化类型与多余属性检查

**目标**：通过实际赋值验证结构化类型与多余属性检查的边界。

**步骤**：

1. 定义 `interface Point2D { x: number; y: number }`。
2. 尝试 `const p: Point2D = { x: 1, y: 2, z: 3 }`，确认报"多余属性"错误。
3. 改用变量中转：`const raw = { x: 1, y: 2, z: 3 }; const p: Point2D = raw;`，验证通过。
4. 定义 `interface Employee { name: string; dept: string }`，验证 `Employee` 可赋给 `interface Person { name: string }`，反向不行。
5. 实现一个 `greet(p: { name: string })` 函数，分别用字面量和变量传 `{ name: 'A', age: 1 }`，观察多余属性检查的差异。

**验收**：

- 能列出多余属性检查的 3 种绕过方式。
- 能用"协变 / 逆变"解释为什么 `(x: Sup) => void` 能赋给 `(x: Sub) => void`。

---

## 六、参考与延伸阅读

- [TypeScript Handbook: Interfaces](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [TypeScript Handbook: Type Aliases](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-aliases)
- [TypeScript Handbook: Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
- [TypeScript Handbook: Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)
- [TypeScript Handbook: Declaration Merging](https://www.typescriptlang.org/docs/handbook/declaration-merging.html)
- [TypeScript: Type Compatibility（结构化类型）](https://www.typescriptlang.org/docs/handbook/type-compatibility.html)

---

> 下一天预告：**Day 04 - 泛型与工具类型**。我们将拆解 `<T>` 的本质、泛型约束 `extends`、`keyof` / `infer` 的进阶用法，并手写 `Partial` / `Pick` / `Omit` / `ReturnType` 等内置工具类型，把"类型级编程"从概念变成肌肉记忆。
