# Day05 - 联合类型与交叉类型

> 本篇聚焦 TypeScript 中“组合类型”的两块基石：**联合类型（Union）**与**交叉类型（Intersection）**，以及让 TS 真正“智能”的关键能力——**类型收窄（Type Narrowing）**。联合类型表达“或”语义，交叉类型表达“与”语义；而类型收窄则让编译器能够沿着控制流逐步把宽类型“切”成窄类型，使我们在享受类型安全的同时不必写大量重复的类型断言。掌握这三者，你才能优雅地建模真实世界里的状态机、API 响应、外部数据校验等场景。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解 - 联合类型](#二理论知识讲解---联合类型)
  - [2.1 联合类型 | 的含义](#21-联合类型--的含义)
  - [2.2 字面量联合实现状态枚举](#22-字面量联合实现状态枚举)
  - [2.3 联合类型的公共属性](#23-联合类型的公共属性)
  - [2.4 可辨识联合 Discriminated Union](#24-可辨识联合-discriminated-union)
- [三、理论知识讲解 - 交叉类型](#三理论知识讲解---交叉类型)
  - [3.1 交叉类型 & 的含义](#31-交叉类型--的含义)
  - [3.2 交叉类型实现 mixin 模式](#32-交叉类型实现-mixin-模式)
  - [3.3 交叉类型的字段冲突](#33-交叉类型的字段冲突)
  - [3.4 交叉类型与 Object.assign 的对应关系](#34-交叉类型与-objectassign-的对应关系)
- [四、联合 vs 交叉对比](#四联合-vs-交叉对比)
- [五、理论知识讲解 - 类型收窄](#五理论知识讲解---类型收窄)
  - [5.1 typeof 守卫](#51-typeof-守卫)
  - [5.2 instanceof 守卫](#52-instanceof-守卫)
  - [5.3 in 守卫](#53-in-守卫)
  - [5.4 等值收窄](#54-等值收窄)
  - [5.5 可辨识联合的 switch 收窄](#55-可辨识联合的-switch-收窄)
  - [5.6 truthy 收窄](#56-truthy-收窄)
  - [5.7 自定义类型守卫函数](#57-自定义类型守卫函数)
  - [5.8 类型收窄与控制流分析](#58-类型收窄与控制流分析)
  - [5.9 never 与穷尽检查](#59-never-与穷尽检查)
- [六、实战模式](#六实战模式)
- [七、关键知识点总结](#七关键知识点总结)
- [八、实战练习](#八实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 准确描述联合类型 `|` 与交叉类型 `&` 的语义差异，并能在“或”与“与”场景下正确选型。
2. 用字面量联合类型替代枚举，表达有限状态集合，并解释其在树摇与可读性上的优势。
3. 说出联合类型“只能访问公共属性”的限制来源，并能用类型收窄访问各自特有属性。
4. 设计可辨识联合（discriminated union），用 `type` / `kind` 字段做判别，配合 switch 完成建模。
5. 用交叉类型实现 mixin 模式，并能预测字段冲突时类型如何退化（取交集或 `never`）。
6. 在 `if/else`、三目、`switch`、提前 `return` 等控制流中识别类型收窄的发生时机。
7. 熟练使用 `typeof` / `instanceof` / `in` / 等值 / truthy 五类内置守卫。
8. 编写带 `x is Type` 谓词的自定义守卫函数，用于校验 `unknown` 类型的外部数据。
9. 用 `never` 类型实现穷尽检查，让“新增分支未处理”变成编译期错误而非运行时 bug。

---

## 二、理论知识讲解 - 联合类型

### 2.1 联合类型 `|` 的含义

联合类型表达 **“或”关系**：一个值只要属于其中任意一个成员类型，就满足该联合类型。`|` 读作“或”，而不是“按位或”。

```ts
type UserId = number | string;

function printUserId(id: UserId) {
  console.log(id);
}

printUserId(1001);       // ✅ number
printUserId('U-1001');   // ✅ string
// printUserId(true);    // ❌ boolean 不在联合中
```

理解上有两个要点：

1. **取值只需“命中其一”**。`number | string` 不是“同时是 number 和 string”，而是“要么 number，要么 string”。`number & string` 才是“同时”。
2. **联合类型是对“值空间”的并集**。它表达的是运行时这个变量可能是什么样子，而非把多个类型“揉”成一个新对象。

联合可以无限扩展成员：

```ts
type Mixed = number | string | boolean | null | undefined;
```

> 💡 **AI 场景联想**：调用大模型时，token 计数可能是 `number`（成功）或 `string`（错误描述）。用 `number | string` 表达返回值，比 `any` 安全得多。

### 2.2 字面量联合实现状态枚举

把联合类型的成员限定为**字面量**，就得到了一种比 `enum` 更轻量的“状态枚举”：

```ts
type TaskStatus = 'pending' | 'running' | 'success' | 'failed';

function describe(s: TaskStatus): string {
  switch (s) {
    case 'pending':  return '等待执行';
    case 'running':  return '执行中';
    case 'success':  return '已完成';
    case 'failed':   return '执行失败';
  }
}
```

字面量联合相比 `enum` 的优势：

| 特性 | 字面量联合 | `enum` |
|------|-----------|--------|
| 编译产物 | 零运行时开销（纯类型） | 会生成对象 |
| 树摇友好 | ✅ 完全可消除 | ❌ 部分场景留运行时对象 |
| 跨文件复用 | 通过 `import type` 即可 | 需 `export enum` |
| 字符串字面量联合 | ✅ 直接可读 | 需 `enum` + reverse mapping |
| 数字自增 | ❌ 需手写 | ✅ 自动 |

字面量还可以**混合不同类型**：

```ts
type Answer = 'yes' | 'no' | 0 | 1;
type Align = 'left' | 'center' | 'right';
```

### 2.3 联合类型的公共属性

这是联合类型最容易被忽略的“坑”：**对一个联合类型的值，只能访问所有成员共有的属性/方法**。

```ts
function process(value: string | number) {
  value.toString();   // ✅ 两者都有 toString
  value.valueOf();    // ✅ 两者都有 valueOf

  // value.toFixed(2);      // ❌ number 有，string 没有
  // value.toUpperCase();   // ❌ string 有，number 没有
}
```

原因不难理解：编译器无法保证运行时这个值到底是哪个分支，所以只能让你调用“无论如何都安全”的成员。要访问各自特有的方法，必须先做**类型收窄**：

```ts
function process(value: string | number) {
  if (typeof value === 'string') {
    console.log(value.toUpperCase());   // 已收窄为 string
  } else {
    console.log(value.toFixed(2));      // 已收窄为 number
  }
}
```

对象类型的联合同样受此限制：

```ts
interface Bird { kind: 'bird'; fly(): void; layEgg(): void; }
interface Fish { kind: 'fish'; swim(): void; layEgg(): void; }

type Pet = Bird | Fish;

function handle(pet: Pet) {
  pet.layEgg();   // ✅ 公共方法
  // pet.fly();   // ❌
  // pet.swim();  // ❌
}
```

### 2.4 可辨识联合 Discriminated Union

为了让 TS 能更可靠地收窄，社区总结出一种模式：**每个成员都带一个同名的字面量字段**作为“身份证”，这就是可辨识联合。

```ts
interface Circle    { type: 'circle';    radius: number; }
interface Square    { type: 'square';    side: number; }
interface Rectangle { type: 'rectangle'; width: number; height: number; }

type Shape = Circle | Square | Rectangle;

function area(s: Shape): number {
  switch (s.type) {
    case 'circle':    return Math.PI * s.radius ** 2;
    case 'square':    return s.side ** 2;
    case 'rectangle': return s.width * s.height;
  }
}
```

判别字段（也叫 discriminator / tag）的几个约定：

- **字段名常见为 `type` / `kind` / `_tag` / `discriminator`**，React Actions 用 `type`，K8s 资源用 `kind`。
- **必须用字面量类型**（如 `'circle'`），不能用 `string`，否则无法区分。
- **TS 会针对字面量判别字段做特殊优化**：等值比较时能直接收窄到对应成员。

可辨识联合是 TS 中最强大的建模工具之一，Redux 的 action、状态机的状态、API 响应的成功/失败分支，都可以用它表达。

---

## 三、理论知识讲解 - 交叉类型

### 3.1 交叉类型 `&` 的含义

交叉类型表达**“与”关系**：一个值必须**同时满足所有成员类型**。`A & B` 意味着“既有 A 的全部属性，又有 B 的全部属性”。

```ts
interface HasName { name: string; }
interface HasAge  { age: number;  }
interface HasEmail{ email: string;}

type Person = HasName & HasAge & HasEmail;

const alice: Person = { name: 'Alice', age: 28, email: 'alice@example.com' };
// const bob: Person = { name: 'Bob', age: 30 };   // ❌ 缺少 email
```

注意：

1. 交叉类型是对“属性集合”的**并集**（同时具备），但语义上读作“与”——“既要 A 又要 B”。
2. 交叉类型只用于**对象/结构类型**；对原始类型做交叉往往得到 `never`（见 3.3）。

### 3.2 交叉类型实现 mixin 模式

mixin 的本质是“给一个对象叠加额外能力”，这与交叉类型的语义完全吻合：

```ts
type Timestamped<T>   = T & { createdAt: Date; updatedAt: Date };
type SoftDeletable<T> = T & { deletedAt: Date | null; isDeleted: boolean };
type Traceable<T>     = T & { traceId: string };

interface Article { id: number; title: string; content: string; }

// 通过交叉叠加，得到带“时间戳 + 软删除 + 链路追踪”的文章实体
type ArticleEntity = Traceable<SoftDeletable<Timestamped<Article>>>;
```

函数式 mixin 同样基于此模式：

```ts
function withTimestamp<T extends object>(base: T): T & { createdAt: Date } {
  return { ...base, createdAt: new Date() };
}

function withLogger<T extends object>(base: T): T & { log(): void } {
  return { ...base, log() { console.log('[log]', JSON.stringify(base)); } };
}

const enriched = withLogger(withTimestamp({ host: 'localhost', port: 3000 }));
```

### 3.3 交叉类型的字段冲突

当交叉的多个类型**同名字段类型不同**时，TS 会按“取交集”的规则推导：

| 同名字段类型 | 交叉结果 | 说明 |
|--------------|----------|------|
| `string & string` | `string` | 完全相同，无冲突 |
| `string \| number` & `string` | `string` | 取交集 |
| `string` & `number` | `never` | 完全不兼容，退化为 never |
| 方法签名不同但兼容 | 函数重载 | 形成重载集合 |

```ts
interface A { value: string | number; }
interface B { value: string; }
type AB = A & B;   // AB['value'] = (string | number) & string = string
const ab: AB = { value: 'hello' };
// const ab2: AB = { value: 1 };  // ❌

interface X { flag: string; }
interface Y { flag: number; }
type XY = X & Y;
// XY['flag'] = string & number = never，无法赋任何值
```

冲突结果是 `never` 时，意味着该字段“理论上存在但无值可填”，几乎等同于设计错误，应当通过重命名字段规避。

### 3.4 交叉类型与 Object.assign 的对应关系

交叉类型在**类型层面**做的事，正好对应 `Object.assign` 在**运行时**做的事——把多个对象合并成一个：

```ts
const withName = { name: 'Carol' };
const withAge  = { age: 30 };
const withRole = { role: 'admin' };

// 运行时合并
const merged = Object.assign({}, withName, withAge, withRole);

// 类型层面合并
type MergedType = typeof withName & typeof withAge & typeof withRole;
const typed: MergedType = merged;   // 结构兼容
```

合并默认配置与用户配置时，这一对应关系尤为好用：

```ts
function makeConfig(def: DefaultConfig, user: Required<UserConfig>): FinalConfig {
  return { ...def, ...user };   // 展开运算符等价于 Object.assign
}
```

---

## 四、联合 vs 交叉对比

| 维度 | 联合类型 `A | B` | 交叉类型 `A & B` |
|------|-----------------|------------------|
| **语义** | 或关系：属于其一即可 | 与关系：必须同时满足 |
| **符号** | `\|`（管道符） | `&`（与号） |
| **值空间** | 并集（取值范围更宽） | 交集（取值范围更窄，要求更严） |
| **属性空间** | 交集（只能访问共有属性） | 并集（拥有所有属性） |
| **典型场景** | 状态枚举、API 成功/失败、可能为 null | mixin、配置合并、能力叠加 |
| **同名字段冲突** | 必须收窄后访问 | 取类型交集，可能退化为 `never` |
| **可访问属性** | 所有成员的公共属性 | 所有成员的属性之和 |
| **记忆口诀** | “或”——取值是其中之一 | “与”——属性要全都有 |

> 📌 一句话记忆：**联合让“值”变多但让“可用属性”变少；交叉让“属性”变多但让“合法值”变少。**

---

## 五、理论知识讲解 - 类型收窄

类型收窄是 TS “智能”的核心：编译器会沿着控制流（`if`/`else`/三目/`switch`/`return`）逐步把一个**宽类型**收缩为更具体的**窄类型**。下面逐一介绍常见守卫。

### 5.1 typeof 守卫

`typeof` 返回的字符串集合是有限的：

```
'string' | 'number' | 'boolean' | 'undefined' | 'object' | 'function' | 'symbol' | 'bigint'
```

```ts
function padLeft(value: string, padding: string | number) {
  if (typeof padding === 'number') {
    return ' '.repeat(padding) + value;   // padding: number
  }
  return padding + value;                  // padding: string
}
```

**两个坑要牢记**：

1. `typeof null === 'object'`，不是 `'null'`。判 null 必须用 `=== null`。
2. `typeof NaN === 'number'`。判 NaN 必须用 `Number.isNaN`。

```ts
function inspect(x: string | number | null) {
  if (typeof x === 'object') {
    // ⚠️ x 在此为 number 之外...实际上 null 也会进来！
    if (x === null) return 'null';
  }
  // ...
}
```

### 5.2 instanceof 守卫

`instanceof` 用于判断“是否为某个类的实例”，常用于错误类型、自定义类：

```ts
class ValidationError extends Error {
  constructor(public field: string, message: string) { super(message); }
}
class NetworkError extends Error {
  constructor(public statusCode: number, message: string) { super(message); }
}

function report(err: ValidationError | NetworkError) {
  if (err instanceof ValidationError) {
    return `[校验] ${err.field}：${err.message}`;
  }
  return `[网络] HTTP ${err.statusCode}：${err.message}`;
}
```

注意：`instanceof` 依赖原型链，跨 iframe / 跨 realm 时可能失效；对 plain object（`{}`）也无效，应改用 `in` 守卫或自定义守卫。

### 5.3 in 守卫

`in` 判断属性是否存在于对象上，对**接口/对象字面量联合**特别好用：

```ts
interface Fish { swim(): void; }
interface Bird { fly(): void;  }

function move(a: Fish | Bird) {
  if ('swim' in a) {
    a.swim();    // a 收窄为 Fish
  } else {
    a.fly();     // a 收窄为 Bird
  }
}
```

`in` 也能判断可选属性：

```ts
interface Config { host: string; port?: number; }
function read(c: Config) {
  if ('port' in c) console.log(c.port);   // 收窄为含 port 的 Config
}
```

### 5.4 等值收窄

用 `===` / `!==` 与字面量比较，TS 也会收窄：

```ts
type TriState = 'on' | 'off' | 'standby';

function describe(s: TriState) {
  if (s === 'on')  return '开启';      // s: 'on'
  if (s === 'off') return '关闭';      // s: 'off'
  return '待机';                         // s 自动收窄为 'standby'
}
```

`=== null` / `!== undefined` 是过滤可空类型的标准手段：

```ts
function safeLength(s: string | null | undefined) {
  if (s === null || s === undefined) return 0;
  return s.length;   // s: string
}
```

### 5.5 可辨识联合的 switch 收窄

这是工程中最常见、最推荐的收窄模式：

```ts
type Shape =
  | { type: 'circle';    radius: number }
  | { type: 'square';    side: number }
  | { type: 'rectangle'; width: number; height: number };

function area(s: Shape) {
  switch (s.type) {
    case 'circle':    return Math.PI * s.radius ** 2;
    case 'square':    return s.side ** 2;
    case 'rectangle': return s.width * s.height;
  }
}
```

`switch` 相比 `if` 链更易读，也方便配合穷尽检查（见 5.9）。

### 5.6 truthy 收窄

`if (x)` 会把 `x` 收窄为“truthy”的取值，自动排除所有 falsy 值（`false` / `0` / `''` / `null` / `undefined` / `NaN`）：

```ts
function printName(name: string | null | undefined) {
  if (name) {
    console.log(name.toUpperCase());   // 排除了 null / undefined / ''
  }
}
```

**注意盲区**：truthy 收窄会把 `0` 和 `''` 也排除掉。如果你的业务里 `0` 是合法值，必须用 `=== null` / `=== undefined` 精确判断，不能依赖 truthy。

```ts
function process(v: number | string | null) {
  if (v) {
    // v: number | string（但 0 和 '' 不会进来）
  } else {
    // v: number | '' | null
  }
}
```

### 5.7 自定义类型守卫函数

当判断逻辑较复杂或需要复用时，可以用 `parameterName is Type` 谓词定义守卫函数：

```ts
function isString(x: unknown): x is string {
  return typeof x === 'string';
}

function isUserDTO(x: unknown): x is UserDTO {
  if (typeof x !== 'object' || x === null) return false;
  return typeof (x as any).id === 'number'
      && typeof (x as any).name === 'string';
}

const parsed: unknown = JSON.parse(json);
if (isUserDTO(parsed)) {
  console.log(parsed.name);   // 收窄为 UserDTO
}
```

`is` 谓词的本质是**对编译器的一个承诺**：函数返回 `true` 时，参数就是指定类型。守卫函数把“判断逻辑 + 类型收窄”封装成可复用单元，是校验 `unknown` 外部数据的标准武器。

### 5.8 类型收窄与控制流分析

TS 的控制流分析（Control Flow Analysis, CFA）会在以下结构中传播收窄结果：

| 结构 | 收窄行为 |
|------|----------|
| `if (cond) { A } else { B }` | A 分支按 cond 为真收窄，B 分支按 cond 为假收窄 |
| `cond ? A : B` | 同上 |
| `switch (x) { case 'a': ... }` | 每个 case 内按匹配字面量收窄 |
| `if (cond) return ...;` | 提前返回后，后续代码按 cond 为假收窄 |
| `if (cond) throw ...;` | 抛错后，后续代码按 cond 为假收窄 |
| `const x = y;` | `const` 具有确定性，等值收窄更激进 |
| 闭包内 | 默认不传播（除非 `const`），因为闭包可能在收窄后再次调用 |

提前 `return` 是非常实用的写法：

```ts
function pickValue(v: string | number | null): string {
  if (v === null) return '空';       // 之后 v 不再是 null
  return typeof v === 'string' ? `S:${v}` : `N:${v.toFixed(0)}`;
}
```

### 5.9 never 与穷尽检查

`never` 表示“永远不会出现的值”。利用它，可以把“忘记处理某个分支”变成**编译期错误**：

```ts
function assertNever(x: never): never {
  throw new Error(`未处理的分支：${JSON.stringify(x)}`);
}

function area(s: Shape): number {
  switch (s.type) {
    case 'circle':    return Math.PI * s.radius ** 2;
    case 'square':    return s.side ** 2;
    case 'rectangle': return s.width * s.height;
    default:
      return assertNever(s);   // 若遗漏 case，s 不是 never，编译报错
  }
}
```

原理：当所有 case 都被处理时，`default` 分支不可达，`s` 的类型被收窄为 `never`；若遗漏了某个 `case`，`s` 仍是某个具体类型，赋给 `never` 形参就会报错。

这种“穷尽检查（exhaustive check）”是大型项目中防止漏处理分支的利器——新增一个联合成员后，所有遗漏的 `switch` 都会立刻被编译器标红。

---

## 六、实战模式

### 模式 1：API 响应联合类型（成功 / 失败）

把“成功”与“失败”建模为可辨识联合，避免 `data` 与 `error` 都可选的模糊类型：

```ts
type ApiResult<T> =
  | { status: 'success'; data: T; }
  | { status: 'error';   error: string; code: number };

function handle<T>(res: ApiResult<T>) {
  switch (res.status) {
    case 'success':
      return res.data;     // T
    case 'error':
      throw new Error(`${res.code}: ${res.error}`);
  }
}
```

### 模式 2：可辨识联合实现状态机

每个状态自带各自的“负载字段”，状态流转通过赋新对象完成：

```ts
type AppState =
  | { status: 'idle' }
  | { status: 'loading'; startedAt: number }
  | { status: 'success'; data: unknown }
  | { status: 'error'; message: string };

function render(state: AppState): string {
  switch (state.status) {
    case 'idle':     return '点击开始';
    case 'loading':  return `加载中（${Date.now() - state.startedAt}ms）`;
    case 'success':  return `成功：${JSON.stringify(state.data)}`;
    case 'error':    return `出错：${state.message}`;
  }
}
```

### 模式 3：自定义守卫校验外部数据

外部数据（`fetch` 返回、`JSON.parse` 结果）类型都是 `unknown`，用守卫逐步“证明”其结构：

```ts
function isRecord(x: unknown): x is Record<string, unknown> {
  return typeof x === 'object' && x !== null && !Array.isArray(x);
}

function isUserDTO(x: unknown): x is UserDTO {
  if (!isRecord(x)) return false;
  return typeof x.id === 'number'
      && typeof x.name === 'string'
      && (x.email === undefined || typeof x.email === 'string');
}

const parsed: unknown = JSON.parse(json);
if (isUserDTO(parsed)) {
  console.log(parsed.name);   // 安全访问
}
```

这一模式在生产中可进一步抽象为 zod / io-ts 等运行时校验库，但理解手写守卫的原理是使用这些库的前提。

---

## 七、关键知识点总结

1. **联合 `|` = 或关系**：取值属于其一即可；对联合值只能访问所有成员的公共属性。
2. **交叉 `&` = 与关系**：必须同时满足所有类型；属性是各类型之和。
3. **字面量联合**替代 `enum` 表达状态集合，零运行时开销、树摇友好。
4. **可辨识联合**：每个成员带同名字面量判别字段，配合 `switch` 是 TS 最强的建模工具之一。
5. **交叉类型的字段冲突**：同名不同类型时取交集，完全不兼容则退化为 `never`。
6. **交叉类型 ↔ `Object.assign` / 展开运算符**：类型层面的合并对应运行时的合并。
7. **类型收窄**：编译器沿控制流把宽类型切成窄类型，是 TS “智能”的核心。
8. **五类内置守卫**：`typeof` / `instanceof` / `in` / 等值（`===`）/ truthy。
9. **自定义守卫**：`x is Type` 谓词，是校验 `unknown` 外部数据的标准武器。
10. **never 与穷尽检查**：`default` 分支把值赋给 `never`，让漏处理分支变成编译期错误。
11. **truthy 收窄的盲区**：会排除 `0` 与 `''`，业务上需要保留时改用 `=== null` / `=== undefined`。
12. **控制流分析覆盖范围**：`if/else`、三目、`switch`、提前 `return`/`throw` 都会收窄，但闭包内默认不传播。

---

## 八、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：联合类型与字面量状态（对应 `union-types.ts`）

定义一个 `HttpStatus = 200 | 404 | 500 | 503` 的字面量联合，并实现 `explain(code: HttpStatus): string` 函数，返回对应的中文描述（如 `200 -> OK`）。然后尝试传入 `401`，观察编译器报错。

**进阶**：把 `HttpStatus` 改为 `{ code: 200; message: 'OK' } | { code: 404; message: 'Not Found' } | ...` 的可辨识联合，编写 `describe(c: HttpStatus): string`，让 TS 在 `switch (c.code)` 中自动收窄并访问 `c.message`。

### 练习 2：交叉类型实现 mixin（对应 `intersection-types.ts`）

定义三个 mixin 工厂函数：

- `withTimestamp<T>(base: T): T & { createdAt: Date }`
- `withLogger<T>(base: T): T & { log(msg: string): void }`
- `withTags<T>(base: T): T & { tags: string[] }`

对一个 `{ title: string }` 对象依次叠加三个 mixin，得到一个同时具备 `title` / `createdAt` / `log` / `tags` 的类型。要求：

1. 不写任何类型断言。
2. 调用 `log` 和访问 `tags` 都通过类型检查。
3. 思考：若两个 mixin 都定义了同名字段 `id: string` 与 `id: number`，最终类型会是什么？

### 练习 3：可辨识联合 + 穷尽检查（对应 `discriminated-union.ts` 与 `exhaustive-check.ts`）

定义一个可辨识联合 `Result`，表达一个推理任务的状态：

```ts
type Result =
  | { type: 'pending' }
  | { type: 'running'; progress: number }      // progress: 0~1
  | { type: 'success'; tokens: number }
  | { type: 'failed'; error: string };
```

要求：

1. 实现 `summarize(r: Result): string`，用 `switch (r.type)` 处理每个分支，并在 `default` 中用 `assertNever(r)` 做穷尽检查。
2. 在 `summarize` 中故意删掉 `'failed'` 分支，观察 `assertNever(r)` 报错信息。
3. 新增一个 `{ type: 'cancelled'; reason: string }` 成员，观察 TS 在何处提示你需要补全代码。
4. 编写一个自定义守卫 `isSuccess(r: unknown): r is { type: 'success'; tokens: number }`，用它校验一段 `JSON.parse` 出来的 `unknown` 数据。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/union-types.ts` | 联合类型、字面量联合状态、公共属性访问限制 |
| `Code/intersection-types.ts` | 交叉类型、mixin 模式、字段冲突 |
| `Code/discriminated-union.ts` | 可辨识联合（Shape 类型、type 字段判别、switch 收窄、状态机） |
| `Code/typeof-narrowing.ts` | typeof / in / instanceof / 等值 / truthy 守卫 |
| `Code/custom-guard.ts` | 自定义类型守卫 `x is Type`、外部数据校验 |
| `Code/exhaustive-check.ts` | `never` 穷尽检查、忘记处理分支时编译报错 |

运行方式（需先在 `Code/` 目录执行 `npm install`）：

```bash
cd Code
npm install
npx ts-node union-types.ts
npx ts-node intersection-types.ts
npx ts-node discriminated-union.ts
npx ts-node typeof-narrowing.ts
npx ts-node custom-guard.ts
npx ts-node exhaustive-check.ts
```

或使用 `package.json` 中预置的脚本：

```bash
npm run union        # 等价于 ts-node union-types.ts
npm run intersection
npm run discriminated
npm run narrowing
npm run guard
npm run exhaustive
npm run type-check   # 全量类型检查（不输出文件）
```

---

> 📚 **延伸阅读**
> - TS 官方手册：[Unions and Intersection Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#union-types)
> - TS 官方手册：[Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
> - TS 官方手册：[Type Guards](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#using-type-predicates)
> - TypeScript 5.x Release Notes：控制流分析增强与 `never` 相关改进
> - 社区模式：[Discriminated Unions](https://basarat.gitbook.io/typescript/type-system/discriminated-unions)
