# Day 04 · 函数与泛型

> 运行环境：Node.js 18+ · TypeScript 5.4+ · ts-node 10.9+

> 函数是 JavaScript 中的一等公民（first-class citizen）——可以作为参数传递、作为返回值、赋值给变量；而泛型则是 TypeScript 类型系统的灵魂，它把"类型"本身也变成可参数化的存在，让一个函数/类/接口能够同时保持类型安全与复用性。本节从函数类型注解出发，一路推进到函数重载与 `this` 类型，再以泛型函数、泛型约束、`keyof` 操作符直至 `Repository<T>` 模式收尾，为后续 NestJS + TypeORM 的实战打下类型层面最关键的地基。

---

## 📑 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解 · 函数部分](#二理论知识讲解--函数部分)
  - [2.1 函数类型注解](#21-函数类型注解)
  - [2.2 可选参数、默认值与剩余参数](#22-可选参数默认值与剩余参数)
  - [2.3 `this` 类型：`noImplicitThis` 与 `ThisType`](#23-this-类型noimplicitthis-与-thistype)
  - [2.4 函数重载 overload](#24-函数重载-overload)
  - [2.5 函数类型兼容性](#25-函数类型兼容性)
- [三、理论知识讲解 · 泛型部分](#三理论知识讲解--泛型部分)
  - [3.1 泛型的动机](#31-泛型的动机)
  - [3.2 泛型函数语法与命名约定](#32-泛型函数语法与命名约定)
  - [3.3 显式指定 vs 类型推断](#33-显式指定-vs-类型推断)
  - [3.4 多类型参数 `<T, U>`](#34-多类型参数-t-u)
  - [3.5 泛型约束 `extends`](#35-泛型约束-extends)
  - [3.6 泛型在类与接口中的应用](#36-泛型在类与接口中的应用)
  - [3.7 泛型默认值 `<T = string>`](#37-泛型默认值-t--string)
  - [3.8 条件类型中的泛型](#38-条件类型中的泛型)
- [四、泛型实战](#四泛型实战)
- [五、常见陷阱](#五常见陷阱)
- [六、关键知识点总结](#六关键知识点总结)
- [七、实战练习](#七实战练习)
- [八、配套代码](#八配套代码)

---

## 一、学习目标

完成本节内容后，你将能够：

1. **为函数写出完整类型注解**：参数类型、返回值类型、箭头函数类型、`void`/`never` 的语义边界。
2. **熟练使用可选参数、默认值、剩余参数**，并知道何时省略类型注解、何时必须显式。
3. **理解 `this` 类型在严格模式下的意义**：能用 `this: T` 显式注解、能用 `ThisType<T>` 标注对象字面量方法上下文。
4. **写出符合 TS 规范的函数重载**：掌握"多签名 + 实现"模式、签名顺序、与联合类型的取舍。
5. **解释泛型为何是类型层面的参数化**，能用 `<T>(arg: T): T` 写出 `identity`/`first`/`merge` 等经典函数。
6. **使用 `extends` 约束泛型**，理解 `keyof` + 索引访问类型 `T[K]` 组合，能实现 `getProperty<T, K extends keyof T>` 这一类型安全访问器。
7. **使用泛型默认值** `<T = string>`，理解默认参数对类型推断的影响。
8. **设计一个 `Repository<T>` 泛型仓储**，理解它为何是 NestJS + TypeORM 的核心抽象。

---

## 二、理论知识讲解 · 函数部分

### 2.1 函数类型注解

#### 参数类型与返回值类型

TS 中函数声明的类型注解最直接的写法：

```ts
function add(a: number, b: number): number {
  return a + b;
}
```

`a: number`、`b: number` 是参数类型，`): number` 是返回值类型。返回值类型通常可以省略由 `return` 推断，但**显式声明有"防止实现写错返回值"的好处**——尤其在重构时。

#### `void` vs `never`

| 返回值类型 | 语义 | 典型场景 |
| --- | --- | --- |
| `void` | 函数无返回值（或返回 `undefined`/`null` 也允许） | 日志、副作用函数 |
| `never` | 函数永远不会"正常返回"——要么 `throw`，要么死循环 | 抛错函数、`assertUnreachable` 守卫 |

```ts
function log(msg: string): void {
  console.log(msg);
}

function fail(msg: string): never {
  throw new Error(msg);
}
```

`never` 是任何类型的子类型（bottom type），常用于穷尽检查（exhaustive check）：

```ts
function assertUnreachable(x: never): never {
  throw new Error(`Unexpected: ${JSON.stringify(x)}`);
}
```

#### 箭头函数与函数类型字面量

```ts
const square = (x: number): number => x * x;

// 用类型别名描述"函数本身的形状"
type MathOp = (a: number, b: number) => number;
const multiply: MathOp = (a, b) => a * b; // 参数类型由 MathOp 推断
```

也支持用 `interface` 描述函数类型（少见但合法）：

```ts
interface Formatter { (input: string): string }
const toUpper: Formatter = (s) => s.toUpperCase();
```

### 2.2 可选参数、默认值与剩余参数

#### 可选参数 `?`

```ts
function greet(name: string, greeting?: string): string {
  return `${greeting ?? 'Hello'}, ${name}!`;
}
```

- 可选参数 `greeting?: string` 在函数内部的实际类型是 `string | undefined`。
- **可选参数必须放在必填参数之后**——这是 JS 调用约定决定的。

#### 默认值

```ts
function welcome(name: string, prefix: string = 'Mr.'): string {
  return `Welcome, ${prefix} ${name}`;
}

// 默认值参数也可以省略类型注解，让 TS 从默认值推断
function buildUser(name: string, country = 'CN') { /* ... */ } // country: string
```

#### 默认值与可选参数的关系

> **默认值参数即使不写 `?`，调用时也可不传**，行为等价于可选参数。

| 写法 | 类型 | 调用方可省略？ | 函数内是否需要判空？ |
| --- | --- | --- | --- |
| `greeting?: string` | `string \| undefined` | ✅ | ✅ 需要 |
| `greeting = 'Hi'` | `string`（默认值填充后非空） | ✅ | ❌ 不需要 |
| `greeting: string` | `string` | ❌ | ❌ |

**经验法则**：能写默认值就别写可选参数，让默认值兜底，函数体逻辑更简洁。

#### 默认值与显式类型注解

当默认值与目标类型不一致时**必须显式声明类型**，否则会被推断为字面量类型：

```ts
function parseId(id: string, base: number = 10): number {
  return parseInt(id, base); // base 必须显式 number，否则默认字面量 10 的类型推断为 10
}
```

#### 剩余参数 `...rest: T[]`

```ts
function sum(...nums: number[]): number {
  return nums.reduce((acc, n) => acc + n, 0);
}

// 元组化的剩余参数：固定数量但不同类型
function invoke<T1, T2>(fn: (a: T1, b: T2) => void, ...args: [T1, T2]): void {
  fn(args[0], args[1]);
}
```

### 2.3 `this` 类型：`noImplicitThis` 与 `ThisType`

JS 的 `this` 是运行时绑定的，TS 无法静态推断时，默认推断为 `any`。开启 `noImplicitThis`（或 `strict`）后，未注解的 `this` 会报错。

#### 显式 `this` 参数

```ts
interface Person { name: string; age: number }
const alice: Person = { name: 'Alice', age: 30 };

function describeSelf(this: Person, prefix: string): string {
  return `${prefix}: ${this.name}, ${this.age} years old`;
}

describeSelf.call(alice, 'Info'); // ✅
// describeSelf('Info'); // ❌ this 未绑定
```

- `this` 是**第一个参数且仅类型层面**，运行时不会出现在调用参数中。
- 必须用 `.call()` / `.apply()` 或作为对象方法调用。

#### `this: void` 表示"不依赖 this"

```ts
function freeFunction(this: void, x: number): number {
  return x * 2;
}
freeFunction(5); // ✅ 可直接调用，因为函数承诺不使用 this
```

#### `ThisType<T>` 工具

`ThisType<T>` 不产生任何属性，仅在对象字面量方法中**标记 `this` 的推断来源**：

```ts
const counter = {
  count: 0,
  increment() { this.count++; }, // this: { count: number } —— 由对象字面量推断
} satisfies CounterStore & ThisType<{ count: number }>;
```

> ⚠️ `ThisType<T>` 仅在 `noImplicitThis` 开启时生效。

### 2.4 函数重载 overload

当一个函数需要**根据不同入参返回不同类型**时，单签名 + 联合类型无法表达"返回类型随入参收窄"的语义，这时需要重载。

#### 多签名 + 实现的写法

```ts
function format(input: string): number;            // 重载签名 1
function format(input: number): string;            // 重载签名 2
function format(input: boolean): 0 | 1;            // 重载签名 3
function format(input: string | number | boolean): number | string | 0 | 1 {
  // 实现签名（对外不可见）
  if (typeof input === 'string') return input.length;
  if (typeof input === 'number') return input.toLocaleString('en-US');
  return input ? 1 : 0;
}

const n: number = format('hello');   // ✅ 5
const s: string = format(1234567);   // ✅ '1,234,567'
```

#### 重载顺序：更具体的签名在前

```ts
function parse(input: 'true'): true;       // ✅ 字面量在前
function parse(input: 'false'): false;
function parse(input: string): boolean;    // 宽类型在后
function parse(input: string): boolean {
  return input === 'true';
}
```

TS 自上而下匹配，**第一个能匹配上的签名胜出**。如果宽类型在前，字面量签名永远不会被选中——TS 会警告 `This overload signature is not callable`。

#### 实现签名必须是所有重载的"超集"

实现签名的参数类型必须是所有重载签名的联合（或父类型），否则实现体内某个分支拿不到对应类型。

#### 重载 vs 联合类型的取舍

| 场景 | 推荐方式 |
| --- | --- |
| 返回类型随入参**类型**变化（`string → number`、`number → string`） | ✅ 重载 |
| 返回类型随入参**值**变化（`'true' → true`） | ✅ 重载 |
| 所有入参返回同一种类型 | ✅ 联合类型更简洁 |
| 入参对象结构差异大 | ✅ 重载更清晰 |

### 2.5 函数类型兼容性

TS 的函数兼容性遵循**结构子类型**规则：

#### 参数数量兼容

> 参数**少**的函数可以赋给参数**多**的函数类型。

```ts
type Handler = (a: number, b: number) => number;
const oneArg: Handler = (a) => a * 2; // ✅ 第二参数未使用也兼容
const zeroArg: Handler = () => 0;     // ✅
```

#### 返回值兼容

> 返回类型必须是目标返回类型的**子类型**。

```ts
type NumReturner = () => { x: number };
type SubReturner = () => { x: number; y: number };

const subRet: SubReturner = () => ({ x: 1, y: 2 });
const numRet: NumReturner = subRet; // ✅ 子类型赋给父类型
```

#### 参数逆变

> 严格模式（`strictFunctionTypes`）下，函数参数类型必须是目标参数类型的**父类型**。

```ts
// strictFunctionTypes 下：
type AnimalHandler = (a: { name: string }) => void;
type DogHandler = (a: { name: string; bark(): void }) => void;

const dh: DogHandler = (a) => a.bark();
const ah: AnimalHandler = dh; // ❌ 严格模式报错（参数逆变）
```

不开启 `strictFunctionTypes` 时是双变（bivariant）——更宽松但更不安全。

---

## 三、理论知识讲解 · 泛型部分

### 3.1 泛型的动机

#### 没有泛型时只能 `any` 或重复定义

```ts
// 方案 A：any 牺牲类型安全
function unsafeIdentity(arg: any): any {
  return arg;
}
const x = unsafeIdentity('ts');
// x 是 any，编译器不知道有没有 .toUpperCase()

// 方案 B：为每个类型重复定义
function numIdentity(arg: number): number { return arg; }
function strIdentity(arg: string): string { return arg; }
// 重复劳动，且无法覆盖未来类型
```

#### 泛型实现"类型层面的参数化"

```ts
function identity<T>(arg: T): T {
  return arg;
}
```

`<T>` 是**类型参数**——它代表"某种类型，但具体是哪种由调用方决定"。泛型把类型本身变成参数，让一个函数应对所有类型，**同时保留入参与出参的类型关联**——这是 `any` 做不到的。

### 3.2 泛型函数语法与命名约定

#### 基本语法

```ts
function identity<T>(arg: T): T {
  return arg;
}

// 箭头函数
const identityArrow = <T>(arg: T): T => arg;
```

> ⚠️ 在 `.tsx` 文件中，箭头函数的 `<T>` 会被当作 JSX 标签开头，需要写成 `<T,>` 或 `<T extends unknown>` 来消歧义。`.ts` 文件无此问题。

#### 类型参数命名约定

| 命名 | 含义 | 典型场景 |
| --- | --- | --- |
| `T` | Type（第一个类型参数） | 通用 |
| `U`、`V` | 第二、第三个类型参数 | 多类型参数 |
| `K` | Key | 对象键访问、`keyof` |
| `V` | Value | Map、字典 |
| `E` | Element | 数组元素 |
| `R` | Return | 函数返回类型 |
| `S`、`T` | State / Type | 状态机 |

单字母并非强制，但**社区惯例**如此——读开源代码时几乎都按这套约定。

### 3.3 显式指定 vs 类型推断

```ts
// 类型推断：编译器从参数推断 T
const inferred = identity(42); // T = number

// 显式指定：当推断不出，或推断结果需要更宽
const explicit = identity<string>('hello');
```

**何时必须显式？**

1. 参数推断不出 `T`（如 `T` 只用于返回值）。
2. 推断结果过于具体，需要更宽。
3. 推断为联合类型时需要锁定单一分支。

### 3.4 多类型参数 `<T, U>`

```ts
function pair<T, U>(first: T, second: U): [T, U] {
  return [first, second];
}

function triple<T, U, V>(a: T, b: U, c: V): [T, U, V] {
  return [a, b, c];
}

function mapEntry<K, V>(key: K, value: V): { key: K; value: V } {
  return { key, value };
}
```

类型参数可以有任意多个，但**多到 3 个以上时通常说明抽象设计有问题**——可考虑用对象参数代替。

### 3.5 泛型约束 `extends`

#### 约束 T 必须有某属性

```ts
interface HasLength { length: number }
function logLength<T extends HasLength>(arg: T): number {
  return arg.length; // ✅ 至少有 length
}

logLength('hello');        // 5
logLength([1, 2, 3]);      // 3
logLength({ length: 10 }); // 10
// logLength(123);         // ❌ number 没有 length
```

#### 约束为特定类型

```ts
function sumOrConcat<T extends number | string>(a: T, b: T): number | string {
  if (typeof a === 'number' && typeof b === 'number') return a + b;
  return String(a) + String(b);
}
```

#### `keyof` 约束（最经典）

```ts
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { id: 1, name: 'Alice', email: 'a@x.com' };
const id = getProperty(user, 'id');    // 类型：number
const name = getProperty(user, 'name'); // 类型：string
// getProperty(user, 'phone'); // ❌ 'phone' 不是 keyof user
```

`K extends keyof T` 的含义：**`K` 必须是 `T` 的某个键**。配合索引访问类型 `T[K]`，实现"按 key 取值且返回类型与 key 对应"的类型安全访问器。这是 TS 类型体操中最常用、最有用的模式之一。

#### 多层约束（交叉类型组合）

```ts
type StringLike = HasLength & { toString(): string };
function stringify<T extends StringLike>(value: T): string {
  return `[len=${value.length}] ${value.toString()}`;
}
```

### 3.6 泛型在类与接口中的应用

> 此处只演示，详细在 Day06 展开。

#### 泛型接口

```ts
interface Box<T> { value: T }

interface IRepository<T extends Entity> {
  save(entity: T): Promise<T>;
  findById(id: T['id']): Promise<T | null>;
}
```

#### 泛型类

```ts
class Container<T> {
  constructor(public value: T) {}
  map<U>(fn: (x: T) => U): Container<U> {
    return new Container(fn(this.value));
  }
}
```

#### Class Type 约束：`new (...args) => T`

```ts
function instantiate<T>(Ctor: new () => T): T {
  return new Ctor();
}

class Logger { log() { /* ... */ } }
const logger = instantiate(Logger); // T 推断为 Logger
```

这是**工厂模式**和**依赖注入容器**的核心写法，NestJS 的 `@Injectable()` 解析就基于此。

### 3.7 泛型默认值 `<T = string>`

```ts
interface Box<T = string> { value: T }

const strBox: Box = { value: 'hello' };       // T 默认 string
const numBox: Box<number> = { value: 42 };    // 显式覆盖

// 默认值可以引用前面的类型参数
interface KVPair<K = string, V = unknown> {
  key: K; value: V;
}
```

适用场景：**类型参数有"合理默认值"**，多数调用方不需要显式指定。

### 3.8 条件类型中的泛型

> 为 Day08 铺垫，此处只简介。

```ts
// 类型层面的 if-else：T extends U ? X : Y
type IsString<T> = T extends string ? true : false;
type A1 = IsString<string>;  // true
type A2 = IsString<number>;  // false

// infer 在条件类型中"提取"类型
type ElementType<T> = T extends (infer E)[] ? E : never;
type E1 = ElementType<string[]>; // string

// 标准库 ReturnType 的实现
type ReturnType<F> = F extends (...args: never[]) => infer R ? R : never;
```

`infer` 关键字只能在 `extends` 子句右侧使用，它**声明并提取**一个类型变量，是类型体操的核心工具。

---

## 四、泛型实战

### 4.1 `identity` 函数

```ts
function identity<T>(arg: T): T {
  return arg;
}
```

最简单的恒等函数，常用于占位、默认回调。

### 4.2 `first` 函数：取数组首元素

```ts
function first<T>(arr: T[]): T | undefined {
  return arr[0];
}

const n = first([1, 2, 3]); // number | undefined
const s = first(['a', 'b']); // string | undefined
```

注意返回类型 `T | undefined`——空数组的 `arr[0]` 是 `undefined`。

### 4.3 `merge` 函数：合并两个对象

```ts
function merge<T extends object, U extends object>(a: T, b: U): T & U {
  return { ...a, ...b };
}

const merged = merge({ name: 'Alice' }, { age: 30 });
// 类型：{ name: string } & { age: number }
merged.name; // ✅ string
merged.age;  // ✅ number
```

`T extends object` 约束避免传入 `null` / 原始值，交叉类型 `T & U` 让返回值保留两个对象的全部字段。

### 4.4 `getProperty`：`keyof` + 泛型约束经典案例

```ts
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { id: 1, name: 'Alice', email: 'a@x.com' };
const name = getProperty(user, 'name');  // string
const id = getProperty(user, 'id');      // number
// getProperty(user, 'phone');  // ❌ 'phone' 不是 keyof typeof user
```

`K extends keyof T` 限定 `key` 必须是 `obj` 的真实键；`T[K]` 让返回类型与 `key` 对应——这是**类型安全访问器**的标配写法，也是 `lodash.get`、`ramda.prop` 等库的类型签名灵魂。

### 4.5 `Repository<T>` 模式：为 NestJS 铺垫

```ts
interface Entity { id: string | number }

interface IRepository<T extends Entity> {
  save(entity: T): Promise<T>;
  findById(id: T['id']): Promise<T | null>;
  find(predicate?: (e: T) => boolean): Promise<T[]>;
  delete(id: T['id']): Promise<boolean>;
}

class InMemoryRepository<T extends Entity> implements IRepository<T> {
  private storage = new Map<T['id'], T>();
  async save(e: T) { this.storage.set(e.id, e); return e; }
  async findById(id: T['id']) { return this.storage.get(id) ?? null; }
  // ...
}

const userRepo: IRepository<User> = new InMemoryRepository<User>();
const postRepo: IRepository<Post> = new InMemoryRepository<Post>();
```

关键设计：

- `T extends Entity` 约束每个实体都有 `id`。
- `T['id']` 用索引访问类型对齐 Map 键与实体 id 类型——`User.id` 是 `number`，`Post.id` 是 `string`，类型自动跟随。
- 真实场景下 `save/find` 落库到 MySQL/MongoDB，NestJS 的 `@InjectRepository(User)` 本质就是这个工厂的依赖注入版本。

---

## 五、常见陷阱

### 🚫 陷阱 1：泛型推断为 `unknown` / `any`

```ts
function parse<T>(input: string): T {
  return JSON.parse(input); // ❌ JSON.parse 返回 any，强转 T 是不安全的
}

const x = parse<number>('not a number'); // 运行时 x 是 NaN，但类型上是 number
```

**正解**：要么用 `unknown` + 类型守卫，要么用泛型 + 类型守卫：

```ts
function parse<T>(input: string, guard: (v: unknown) => v is T): T {
  const v = JSON.parse(input);
  if (!guard(v)) throw new Error('Invalid');
  return v;
}
```

### 🚫 陷阱 2：过度使用泛型

```ts
// ❌ 没必要的泛型
function log<T>(value: T): void { console.log(value); }

// ✅ 直接用 any 或 unknown
function log(value: unknown): void { console.log(value); }
```

**判断标准**：类型参数 `T` 是否在**多个位置**出现并需要保持关联？只在单处出现 `T` 的泛型通常是"装饰性泛型"，应改用 `unknown`。

### 🚫 陷阱 3：泛型约束太宽

```ts
// ❌ 约束等于没约束
function process<T extends any>(value: T): T { return value; }

// ❌ 约束太宽，类型安全度不够
function getLength<T extends { [key: string]: any }>(obj: T): number {
  return Object.keys(obj).length;
}
```

**正解**：让约束尽可能精确——`extends HasLength`、`extends Entity`、`extends keyof T`。

### 🚫 陷阱 4：箭头函数泛型在 `.tsx` 中报错

```tsx
// .tsx 文件
const identity = <T>(arg: T): T => arg; // ❌ <T> 被当作 JSX
const identity = <T,>(arg: T): T => arg; // ✅ 加逗号消歧义
const identity = <T extends unknown>(arg: T): T => arg; // ✅ 加约束
```

### 🚫 陷阱 5：重载签名顺序错误

```ts
// ❌ 宽签名在前，具体签名永远不会被选中
function parse(input: string): boolean;
function parse(input: 'true'): true;  // ❌ 不可达
```

**正解**：具体签名在前，宽签名在后。

### 🚫 陷阱 6：实现签名对外可见

```ts
function format(input: string): number;
function format(input: number): string;
function format(input: string | number): number | string { /* ... */ }

// 实现签名（参数联合、返回联合）对外不可见，
// 调用方只能匹配重载签名，不会拿到 string | number 的联合返回类型。
```

---

## 六、关键知识点总结

### ✅ 必须记住的 10 条

1. **函数返回值类型**：能省略但不建议，`void` 表示无返回值，`never` 表示永不返回（`throw` 或死循环）。
2. **默认值参数优于可选参数**：默认值会让参数非空，函数体不用判空。
3. **剩余参数**：`...rest: T[]` 收集剩余实参，元组化的剩余参数能表达不同类型。
4. **`this: T` 显式注解**：必须用 `.call()` 或作为对象方法调用，第一个参数仅类型层面。
5. **`ThisType<T>`**：仅标记对象字面量方法的 `this` 来源，本身不产生属性，需 `noImplicitThis` 开启。
6. **函数重载**：多签名在前、实现签名在后；实现签名对外不可见；具体签名必须在宽签名之前。
7. **泛型 `<T>` 是类型参数**：保留入参与出参的类型关联，是 `any` 无法替代的核心机制。
8. **`extends` 约束**：约束泛型必须满足某个结构（`HasLength`、`Entity`、`keyof T`）。
9. **`keyof` + `T[K]`**：组合实现类型安全的属性访问器，是类型体操最常用模式。
10. **泛型默认值 `<T = string>`**：合理默认时让调用方少写类型参数。

### 🚫 常见误区

| 误区 | 正解 |
| --- | --- |
| 泛型就是 any 的语法糖 | 泛型保留类型关联，any 抹除一切 |
| 默认值参数不可省略 | 默认值参数调用时可省略，等价可选 |
| 重载签名越多越好 | 重载用于"返回类型随入参变化"，没必要的重载应该用联合类型 |
| `<T>` 越多越好 | 超过 3 个类型参数通常说明抽象设计有问题 |
| `this: void` 等于 `this: undefined` | `void` 在此表示"承诺不使用 this" |
| 泛型约束必须用 interface | 可以用任何类型，包括交叉类型、字面量类型 |

### 🎯 学习心法

> **泛型是函数的"类型重载"，函数是数据的"行为重载"**。当你写 `function identity<T>(arg: T): T` 时，你正在做的事是：把"函数对某种类型的数据做什么"和"具体是什么类型"解耦——前者是函数体，后者是 `<T>`，调用方填空。理解这一点，你就能从 `identity` 一路走到 `Repository<T>`、`useState<T>`、`createSlice<T>`，看到所有泛型 API 背后同一个骨架。

---

## 七、实战练习

### 练习 1：实现类型安全的 `pick` 函数

**目标**：实现 `pick<T, K extends keyof T>(obj: T, keys: K[]): Pick<T, K>`，从对象中按 keys 取出子集。

**要求**：

1. 函数签名必须用泛型 + `keyof` 约束。
2. 返回类型必须是 `Pick<T, K>`（标准库工具类型）。
3. 任意传入 `obj = { a: 1, b: 'x', c: true }`，`pick(obj, ['a', 'c'])` 返回 `{ a: 1, c: true }`。
4. 传入 `obj` 上不存在的 key 必须编译报错。

**提示**：参考 `Code/generic-constraints.ts` 中的 `pick` 实现，自己改写一版用 `reduce` 的版本。

### 练习 2：用函数重载实现 `formatDate`

**目标**：实现一个 `formatDate` 函数，根据入参类型返回不同类型：

- 传 `Date` 实例 → 返回 `'YYYY-MM-DD'` 字符串。
- 传 `number`（时间戳）→ 返回 `'YYYY-MM-DD HH:mm'` 字符串。
- 传 `string`（ISO 字符串）→ 返回 `Date` 实例。

**要求**：

1. 用三个重载签名 + 一个实现签名。
2. 重载顺序：字面量 / 具体类型在前，宽类型在后（如果需要）。
3. 不允许使用 `any`，实现签名用联合类型。
4. 调用 `formatDate(new Date())` 应得到 `string`（且为 `'YYYY-MM-DD'`），调用 `formatDate(Date.now())` 应得到 `'YYYY-MM-DD HH:mm'`，调用 `formatDate('2024-01-01T00:00:00Z')` 应得到 `Date`。

**提示**：参考 `Code/function-overload.ts` 中的 `format` 示例。

### 练习 3：实现泛型 `Cache<T>` 类

**目标**：实现一个泛型缓存类，支持 `set` / `get` / `has` / `delete`，并支持可选的过期时间。

**要求**：

1. 用 `class Cache<T>`，构造时可选传入 `defaultTtl: number`（毫秒）。
2. `set(key: string, value: T, ttl?: number): void`，未传 `ttl` 时用 `defaultTtl`。
3. `get(key: string): T | undefined`，过期返回 `undefined` 并清除条目。
4. `has(key: string): boolean`，过期返回 `false`。
5. 用 `Map` 内部存储，并维护 `{ value: T; expireAt: number }` 元数据。
6. 写一个 `User` 实体，构造 `Cache<User>` 与 `Cache<string>` 两个实例，验证类型安全。

**提示**：参考 `Code/generic-repository.ts` 中的 `InMemoryRepository<T>`，结构类似但增加 TTL 字段。

---

## 八、配套代码

| 文件 | 内容 |
| --- | --- |
| `Code/function-types.ts` | 函数类型注解、可选/默认/剩余参数、`this` 类型、`ThisType` |
| `Code/function-overload.ts` | 函数重载完整示例、重载顺序、与联合类型的取舍、函数兼容性 |
| `Code/generic-basic.ts` | `identity` / `first` / `merge`、显式 vs 推断、多类型参数、默认值 |
| `Code/generic-constraints.ts` | `extends` 约束、`keyof` 约束、`getProperty` 经典案例、条件类型预览 |
| `Code/generic-repository.ts` | 泛型 `Repository<T>` 模式、按 `keyof` 查询、依赖注入预告 |

### 运行方式

```bash
cd "Day04 - 函数与泛型/Code"
npm install                 # 安装 typescript / ts-node / @types/node
npx ts-node function-types.ts
npx ts-node function-overload.ts
npx ts-node generic-basic.ts
npx ts-node generic-constraints.ts
npx ts-node generic-repository.ts

# 或通过 npm scripts
npm run function-types
npm run generic-repository
```

### 已内置的 `tsconfig.json`

项目已内置 `tsconfig.json`，开启了 `strict` + `noImplicitThis` + `strictFunctionTypes`，确保所有代码在严格模式下通过类型检查：

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "strict": true,
    "noImplicitThis": true,
    "strictFunctionTypes": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "ts-node": { "transpileOnly": true }
}
```

- 运行 `npm run typecheck` 可执行 `tsc --noEmit` 做完整类型检查。
- `ts-node` 配置了 `transpileOnly: true` 以加速运行，类型错误由 `npm run typecheck` 单独把关。
- 每个 `.ts` 文件顶部都有 `export {};`，使其成为 ES 模块，避免全局类型声明跨文件冲突。

---

**下一节预告**：Day 05 将进入 TypeScript 的高级类型——联合类型、交叉类型、字面量类型、字面量收窄、`typeof` / `instanceof` / `in` 类型守卫、可辨识联合（discriminated union），并铺垫 `mapped types` 与 `template literal types`，为类型体操打基础。
