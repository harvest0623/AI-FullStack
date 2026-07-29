# Day02 - 基础类型系统

> TypeScript 的类型系统是「静态类型检查」的根基。本章我们将系统掌握 TS 中所有基础类型：原始类型、数组与元组、特殊类型（any / unknown / never / void / object）、字面量类型、类型断言，以及 `let` 与 `const` 的类型推断差异，并初步接触「类型收窄」机制。掌握这些，你就能写出第一份「在编译期就被类型系统保护」的 TS 代码。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 静态类型 vs 动态类型 vs 渐进式类型](#21-静态类型-vs-动态类型-vs-渐进式类型)
  - [2.2 原始类型](#22-原始类型)
  - [2.3 数组类型](#23-数组类型)
  - [2.4 元组类型 Tuple](#24-元组类型-tuple)
  - [2.5 特殊类型：any / unknown / never / void / object](#25-特殊类型any--unknown--never--void--object)
  - [2.6 any vs unknown 深度对比](#26-any-vs-unknown-深度对比)
  - [2.7 null 与 undefined](#27-null-与-undefined)
  - [2.8 字面量类型](#28-字面量类型)
  - [2.9 类型断言](#29-类型断言)
  - [2.10 类型断言 vs 类型转换](#210-类型断言-vs-类型转换)
  - [2.11 let vs const 的类型推断](#211-let-vs-const-的类型推断)
- [三、类型收窄初步](#三类型收窄初步)
- [四、常见陷阱](#四常见陷阱)
- [五、关键知识点总结](#五关键知识点总结)
- [六、实战练习](#六实战练习)
- [下节预告](#下节预告)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **辨析三种类型系统**：能说清楚「静态类型 / 动态类型 / 渐进式类型」三者差异，并解释 TypeScript 为何属于「渐进式类型」——既能在编译期做严格检查，又能与无类型的 JS 代码共存。
2. **准确使用所有原始类型**：掌握 `string / number / boolean / null / undefined / symbol / bigint` 七种原始类型的声明与边界，能解释 `number` 为何没有 `int / float` 之分、`bigint` 与 `number` 为何不能混算。
3. **区分数组与元组**：能写出 `T[]` 与 `Array<T>` 两种等价写法、`readonly T[]` 与 `ReadonlyArray<T>` 的只读数组，并能用元组表达「固定长度 + 每位独立类型」的结构，掌握命名元组、可选元素、rest 元素。
4. **掌握五个特殊类型的语义**：能讲清楚 `any`（放弃检查）、`unknown`（安全版 any）、`never`（永不出现）、`void`（无返回值）、`object`（非原始值）各自的使用场景与陷阱。
5. **理解字面量类型与联合字面量**：能用 `'idle' | 'loading' | 'success' | 'error'` 这种联合字面量模拟状态机，并知道它与 `enum` 的取舍。
6. **正确使用类型断言**：掌握 `as`、`<T>value`、`!`、`as unknown as T` 四种断言语法，并能区分「断言」与「转换」——断言只影响编译期，转换才在运行时改变值。
7. **理解 let 与 const 的推断差异**：能解释 `let x = 10` 推断为 `number` 而 `const x = 10` 推断为字面量类型 `10` 的原因。
8. **初步掌握类型收窄**：能用 `typeof`、`truthy`、`== null` 三种收窄方式让联合类型在分支内自动变窄，为 Day05 详讲铺垫。

---

## 二、理论知识

### 2.1 静态类型 vs 动态类型 vs 渐进式类型

要理解 TypeScript 的定位，先要分清三种类型系统。

**动态类型（Dynamic Typing）**

- 代表语言：JavaScript、Python、Ruby。
- 特点：类型检查发生在**运行时**，变量没有固定类型，值有类型。
- 示例：JS 中 `let x = 1; x = 'hello';` 完全合法，`x` 的类型跟随赋值变化。
- 优点：灵活、写起来快。
- 缺点：类型错误往往在生产环境才暴露（如 `undefined.foo`），重构时没有保护网。

**静态类型（Static Typing）**

- 代表语言：Java、C#、Rust、Go。
- 特点：类型检查发生在**编译期**，变量声明时必须明确类型，且不可变。
- 示例：Java 中 `int x = 1; x = "hello";` 编译期就报错。
- 优点：编译期就能发现大量错误，IDE 智能提示与重构更可靠。
- 缺点：写起来相对繁琐，纯静态语言与动态生态（如 JS 庞大的 npm）难以互通。

**渐进式类型（Gradual Typing）**

- 代表语言：**TypeScript**、Python + type hints、Flow。
- 特点：**类型是可选的**，可以逐步添加。已加类型的部分接受严格检查，未加类型的部分回退到 `any` 放过检查。
- TS 的具体表现：
  - 一个 `.ts` 文件里，你可以完全不写类型注解，它就是一份合法的 JS。
  - 你也可以逐步给变量、函数、参数加类型，TS 会在编译期检查。
  - 通过 `strict` 系列配置，你可以把检查严格度从「几乎不查」一路调到「比 Java 还严」。

一句话定位：

> **TypeScript = JavaScript + 可选的静态类型层**。它不改变 JS 的运行时行为，只在编译期做类型检查，然后擦除类型注解、输出纯 JS。

```
┌──────────────────────────────────────────────┐
│              你的 TypeScript 代码             │
│        （带类型注解，可选但推荐）              │
├──────────────────────────────────────────────┤
│   tsc / ts-node 编译器：类型检查 + 类型擦除   │
├──────────────────────────────────────────────┤
│         输出的纯 JavaScript 代码              │
│      （运行时完全没有类型信息）               │
├──────────────────────────────────────────────┤
│            Node.js / 浏览器执行               │
└──────────────────────────────────────────────┘
```

### 2.2 原始类型

TypeScript 沿用 JavaScript 的 7 种原始类型，每种都对应一个类型关键字：

| 类型 | 关键字 | 字面量示例 | 说明 |
| --- | --- | --- | --- |
| 字符串 | `string` | `'hi'`、`` `template` `` | 单引号、双引号、模板字符串都属此类 |
| 数字 | `number` | `10`、`3.14`、`0xff`、`0b1010` | 整数 / 浮点 / 进制统一为 number，**没有 int / float 之分** |
| 布尔 | `boolean` | `true`、`false` | 只有这两个字面量 |
| 空 | `null` | `null` | 表示「有意为之的空」 |
| 未定义 | `undefined` | `undefined` | 表示「尚未赋值」 |
| 符号 | `symbol` | `Symbol('id')` | 每次调用返回全新唯一值，常用作对象私有键 |
| 大整数 | `bigint` | `9007199254740991n` | ES2020+，字面量以 `n` 结尾，可精确表示超过 `Number.MAX_SAFE_INTEGER` 的值 |

声明示例：

```ts
let username: string = 'trae';
let age: number = 28;
let isOnline: boolean = true;
let empty: null = null;
let nothing: undefined = undefined;
let key: symbol = Symbol('id');
let big: bigint = 9007199254740991n;
```

几个容易踩坑的点：

- **`number` 与 `bigint` 不能混算**：`1 + 1n` 会报错，必须显式转换 `BigInt(1) + 1n` 或 `Number(1n) + 1`（后者可能丢精度）。
- **`symbol` 每次都唯一**：`Symbol('id') === Symbol('id')` 为 `false`，因此不能用 `===` 比较「同描述」的 symbol，只能用 `Symbol.for('id')` 注册全局 symbol。
- **`null` 与 `undefined` 是独立类型**：在 `strictNullChecks` 开启时，`null` 只能赋给 `null` 类型变量，`undefined` 只能赋给 `undefined` 类型变量，详见 [2.7 节](#27-null-与-undefined)。

> 对应代码：[`Code/primitive-types.ts`](./Code/primitive-types.ts) 第 1 节。

### 2.3 数组类型

TS 中表达「同类型元素的有序列表」有两种等价写法：

```ts
// 写法一：T[]（推荐，更简洁）
const scores: number[] = [90, 85, 92];
const names: string[] = ['Alice', 'Bob'];

// 写法二：Array<T>（泛型写法，二者完全等价）
const temps: Array<number> = [36.5, 37.0];
const flags: Array<boolean> = [true, false];
```

二者没有任何运行时差异，纯粹是语法风格。社区习惯：**简单类型用 `T[]`，复杂泛型类型用 `Array<T>`**（后者在某些链式泛型场景可读性更好）。

**只读数组**

```ts
// readonly T[] 与 ReadonlyArray<T> 等价
const readonlyScores: readonly number[] = [90, 85, 92];
const frozenNames: ReadonlyArray<string> = ['Alice', 'Bob'];

readonlyScores.push(100); // ❌ 报错：readonly 数组上不存在 push
readonlyScores[0] = 100;  // ❌ 报错：索引签名只允许读取
```

只读数组的赋值方向是「单向安全」的：

```ts
const mutableArr: number[] = [1, 2, 3];
const immutableArr: readonly number[] = mutableArr; // ✅ 可变 → 只读 OK
const backToMutable: number[] = immutableArr;       // ❌ 只读 → 可变 报错
```

这符合「更严格的类型可以接收更宽松的值，反之不行」的子类型规则。

> 对应代码：[`Code/array-tuple.ts`](./Code/array-tuple.ts) 第 1、2 节。

### 2.4 元组类型 Tuple

元组（Tuple）表达「**固定长度、每个位置类型独立**」的数组结构，是数组的「精确版」。

```ts
// 数组：所有元素同类型，长度任意
const arr: number[] = [1, 2, 3, 4];

// 元组：每个位置类型独立，长度固定
const point: [number, number] = [10, 20];
const httpStatus: [number, string] = [404, 'Not Found'];
```

**命名元组（带标签）**

在类型位置加标签，仅作为文档提示，运行时无影响，但能显著提升可读性：

```ts
const namedPoint: [x: number, y: number] = [10, 20];
const httpResponse: [status: number, body: string] = [200, 'OK'];
```

IDE 悬浮在 `namedPoint` 上时，会显示 `[x: number, y: number]`，比纯 `[number, number]` 清楚得多。

**可选元素**

末尾元素可用 `?` 标记为可选：

```ts
const optTuple1: [number, string?] = [1];
const optTuple2: [number, string?] = [1, 'two'];
```

**rest 元素（剩余元素）**

用 `...T[]` 表示「若干个同类型元素」，适合「前缀固定 + 后续任意数量」的场景：

```ts
const pairs: [string, ...number[]] = ['scores', 90, 85, 92];
const leading: [number, number, ...string[]] = [1, 2, 'a', 'b', 'c'];

// 函数参数中也很常见：固定前缀 + 任意数量后续
function logCall(id: string, ...rest: [timestamp: number, ...args: string[]]) {
  /* ... */
}
logCall('req-001', 1700000000, 'GET', '/api/users', '200');
```

**元组 vs 数组的取舍**：能用元组准确表达的，就别用 `any[]` 或 `(string | number)[]`。后者会让 TS 失去对每个位置的精确检查。

> 对应代码：[`Code/array-tuple.ts`](./Code/array-tuple.ts) 第 3-7 节。

### 2.5 特殊类型：any / unknown / never / void / object

这五个特殊类型是 TS 类型系统的「角落」场景，理解它们能解决大量「为什么报错 / 为什么不报错」的疑问。

**any：放弃类型检查**

```ts
let anything: any = 'hello';
anything = 100;             // ✅ OK
anything.toUpperCase();     // ✅ 编译期不报错（运行时若 anything 是数字会抛错）
```

`any` 是「**我放弃，你想怎样就怎样**」的逃生舱。它能让你绕过所有检查，但也把所有错误推迟到运行时。**应尽量避免使用**。

**unknown：安全版 any**

```ts
let uncertain: unknown = 'hello';
uncertain.toUpperCase(); // ❌ 报错：unknown 不能直接调用方法

if (typeof uncertain === 'string') {
  uncertain.toUpperCase(); // ✅ OK：收窄后才能用
}
```

`unknown` 是「**我接受任何值，但你使用前必须先证明它的类型**」的安全版本。它能接收任意值（和 `any` 一样），但**不能直接使用**——必须先通过 `typeof`、`instanceof`、断言等方式「收窄」。

**never：永不出现的值**

`never` 表示「**这个值永远不会出现**」。最常见于两类场景：

```ts
// 1. 函数永不返回（抛错或无限循环）
function throwError(msg: string): never {
  throw new Error(msg);
}

// 2. 穷尽检查（exhaustive check）
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'square'; size: number };

function area(s: Shape): number {
  switch (s.kind) {
    case 'circle': return Math.PI * s.radius ** 2;
    case 'square': return s.size ** 2;
    default:
      // 若新增 type 成员却没处理，s 会是非 never 类型，这里报错
      const _exhaustive: never = s;
      return _exhaustive;
  }
}
```

`never` 可赋给任何类型（因为它永不出现），但任何值都不能赋给 `never`（除 `never` 自身）。

**void：无返回值**

```ts
function logMessage(msg: string): void {
  console.log(msg);
  // 不需要 return
}
```

`void` 表示「**函数不返回有意义的值**」。注意它与 `undefined` 的区别：`void` 是「调用方不应使用返回值」的契约，`undefined` 是「返回值为 undefined」的具体类型。在 `strict` 模式下，`void` 函数可以 `return undefined` 但不能 `return 1`。

**object：非原始值**

```ts
function createObject(obj: object): void { /* ... */ }

createObject({ a: 1 });      // ✅
createObject([1, 2, 3]);     // ✅
createObject(new Map());     // ✅
createObject('str');         // ❌ string 是原始类型
createObject(100);           // ❌ number 是原始类型
```

`object` 表示「**非原始类型**」，即除 `string / number / boolean / symbol / bigint / null / undefined` 之外的类型。它和 `{}` 不同——`{}` 表示「非 null 非 undefined 的任意值」，连 `'str'` 都接受，更宽松。

> 对应代码：[`Code/any-unknown-never.ts`](./Code/any-unknown-never.ts) 全文。

### 2.6 any vs unknown 深度对比

`any` 与 `unknown` 是 TS 类型系统的「顶层类型」（top type）——它们都能接收任意值。但二者在「**赋值方向**」与「**使用方式**」上截然相反，这是 TS 类型安全的核心区别。

**对比一：赋值给其他类型**

```ts
let a: any = 'x';
let u: unknown = 'x';

const s1: string = a; // ✅ OK：any 静默赋给 string（隐患）
const s2: string = u; // ❌ 报错：unknown 不能赋给 string（强制收窄）
```

- `any` 是「**双向开放**」：既能接收任意值，也能赋给任意类型变量。这导致类型错误悄悄传染。
- `unknown` 是「**单向开放**」：能接收任意值，但**只能赋给 `unknown` 或 `any`**，不能赋给具体类型。这强制调用方在使用前收窄。

**对比二：直接使用**

```ts
let a: any = 'x';
let u: unknown = 'x';

a.toUpperCase(); // ✅ OK：any 上什么方法都能调（运行时可能崩）
u.toUpperCase(); // ❌ 报错：unknown 上不能调任何方法
```

- `any` 关闭了所有检查，可以任意操作。
- `unknown` 必须先收窄（`typeof`、`instanceof`、断言）才能使用。

**对比三：函数签名中的传染性**

```ts
// 危险：any 会传染到返回值
function unsafeParse(data: any): any {
  return data.foo.bar;
}
const r1 = unsafeParse('hello'); // r1 是 any，后续 r1.anything 都不报错

// 安全：unknown 强制收窄
function safeParse(data: unknown): unknown {
  if (typeof data === 'object' && data !== null && 'foo' in data) {
    return (data as { foo: { bar: string } }).foo.bar;
  }
  return null;
}
const r2 = safeParse('hello'); // r2 是 unknown，必须收窄才能用
```

**结论**：需要「能接收任意值」时，**优先用 `unknown`，禁用 `any`**。仅在以下场景才考虑 `any`：

- 迁移老 JS 代码，临时跳过类型检查。
- 与无类型定义的第三方库交互（更好的做法是写 `.d.ts` 声明文件）。
- 临时调试，需要快速绕过类型系统。

> 对应代码：[`Code/any-unknown-never.ts`](./Code/any-unknown-never.ts) 第 3 节。

### 2.7 null 与 undefined

`null` 与 `undefined` 在 JS 中是两个独立值，在 TS 中也是两个独立类型。它们的行为受 `strictNullChecks` 编译选项影响极大。

**未开启 strictNullChecks（默认旧行为）**

```ts
let x: number = 1;
x = null;      // ✅ OK：null 可赋给任何类型
x = undefined; // ✅ OK：undefined 可赋给任何类型
```

这种宽松行为会导致大量「`Cannot read property of null`」运行时错误，TS 形同虚设。

**开启 strictNullChecks（推荐，strict 模式默认包含）**

```ts
let x: number = 1;
x = null;      // ❌ 报错：null 不能赋给 number
x = undefined; // ❌ 报错：undefined 不能赋给 number

// 必须显式声明联合类型
let y: number | null = 1;
y = null;      // ✅ OK
```

**可选参数与 undefined 的关系**

在函数参数中，`?` 标记的可选参数等价于「该参数类型联合 `undefined`」：

```ts
function greet(name?: string) {
  // name 的类型是 string | undefined
  if (name === undefined) {
    return 'Hello, stranger';
  }
  return 'Hello, ' + name;
}

// 等价写法
function greet2(name: string | undefined) {
  /* ... */
}
```

但要注意：`?: string` 与 `: string | undefined` 在调用时有细微差异——前者允许「不传参数」，后者要求「必须传参数（可以是 undefined）」。

**null 与 undefined 的区别（语义层面）**

- `null`：表示「**有意为之的空**」。例如用户主动清空了一个字段。
- `undefined`：表示「**尚未赋值**」。例如声明了变量但没赋值、函数没返回值、对象属性不存在。

社区习惯：**能用 `undefined` 就别用 `null`**，因为 `undefined` 是「未赋值」的自然状态，`null` 需要显式赋值，容易遗漏处理。但与后端 API 交互时，JSON 规范不含 `undefined`，只有 `null`，所以接口字段经常用 `null`。

### 2.8 字面量类型

字面量类型（Literal Types）把类型「**精确到具体的值**」。这是 TS 区别于很多静态类型语言的特色，也是它表达力强大的来源之一。

**字符串字面量类型**

```ts
type Direction = 'up' | 'down' | 'left' | 'right';
function move(d: Direction) { /* ... */ }

move('up');      // ✅
move('north');   // ❌ 报错：'north' 不在联合类型中
```

**数字字面量类型**

```ts
type Dice = 1 | 2 | 3 | 4 | 5 | 6;
type HttpStatus = 200 | 201 | 400 | 404 | 500;
```

**布尔字面量类型**

`boolean` 本质就是 `true | false` 的联合，因此 `true` 与 `false` 各自也是字面量类型：

```ts
type AlwaysTrue = true;
const t: AlwaysTrue = true;
const f: AlwaysTrue = false; // ❌ 报错

// 实际应用：锁定配置属性为固定值
interface StrictConfig {
  readonly strict: true;       // 此属性只能是 true
  readonly mode: 'production'; // 此属性只能是 'production'
}
```

**联合字面量模拟状态机**

这是字面量类型最实用的场景——用联合字面量代替 `enum`，类型更精确、调试更友好、tree-shaking 更彻底：

```ts
type RequestStatus = 'idle' | 'loading' | 'success' | 'error';

interface RequestState {
  status: RequestStatus;
  data?: string;
  error?: string;
}

function render(state: RequestState): string {
  switch (state.status) {
    case 'idle':    return '等待发起请求...';
    case 'loading': return '加载中...';
    case 'success': return `成功：${state.data}`;
    case 'error':   return `失败：${state.error}`;
  }
}
```

**字面量类型 vs enum 的取舍**

| 维度 | 字面量联合 | enum |
| --- | --- | --- |
| 运行时代码 | 无（纯类型，编译后消失） | 有（生成对象） |
| 调试友好性 | 值就是字符串本身，console 可读 | 数字 enum 显示数字，需反向映射 |
| 导入导出 | 无需导入，直接用字符串字面量 | 必须导入 enum 才能用 |
| 反向映射 | 不支持 | 数字 enum 支持（`Color[0]` 反查名） |
| 推荐 | **优先使用** | 仅在需要反向映射或命名空间时 |

> 对应代码：[`Code/literal-types.ts`](./Code/literal-types.ts) 全文。

### 2.9 类型断言

类型断言（Type Assertion）是「**告诉编译器：我比你更清楚这个值的类型**」的机制。它有四种语法形态。

**as 语法（推荐）**

```ts
const value: unknown = 'hello, ts';
const strLen = (value as string).length;
```

**尖括号语法 `<T>value`**

```ts
const v: unknown = 100;
const num = <number>v;
```

与 `as` 等价，但在 `.tsx`（React）文件中会与 JSX 标签冲突，因此 **`.tsx` 必须用 `as`**。建议统一用 `as`。

**非空断言 `!`**

```ts
const cache = new Map<string, string>();
cache.set('id', 'trae-001');

const id: string | undefined = cache.get('id');
console.log(id!.toUpperCase()); // ! 断言 id 一定非空
```

`!` 是后缀操作符，断言「**这个值不是 null / undefined**」。常用于 Map.get、数组首元素、可选属性链式访问。**注意：它只是「告诉编译器别管」，运行时若真为 null 仍会抛错。**

**双重断言 `as unknown as T`**

当两个类型「重叠不足」时，TS 会拒绝直接断言：

```ts
const raw: string = 'raw';
const fake: number = raw as number; // ❌ 报错：string 与 number 重叠不足

// 通过 unknown 中转：先断言为 unknown，再断言为目标类型
const fake2: number = raw as unknown as number; // ✅ OK
```

双重断言本质是「**绕过 TS 的安全检查**」，属于逃生舱中的逃生舱，应极度谨慎。

> 对应代码：[`Code/type-assertion.ts`](./Code/type-assertion.ts) 第 1-4 节。

### 2.10 类型断言 vs 类型转换

这是初学者最容易混淆的概念，必须严格区分：

| 维度 | 类型断言 | 类型转换 |
| --- | --- | --- |
| 发生时机 | **编译期** | **运行时** |
| 是否改变值 | **不改变**，运行时值完全不变 | **改变**，运行时产生新值 |
| 语法 | `value as T`、`<T>value` | `Number(value)`、`String(value)`、`parseInt()` |
| 风险 | 若断言错误，运行时仍按原值处理，可能崩 | 转换是显式的，可控 |

```ts
const input: unknown = '42';

// 断言：编译期假装是 number，运行时仍是 string
const asserted = input as number;
typeof asserted; // 'string'

// 转换：运行时真正变成 number
const converted = Number(input);
typeof converted; // 'number'，值是 42
```

**常见错误**：以为断言会做转换。

```ts
const jsonStr: unknown = '"42"';        // JSON 字符串，内容是 "42"
const assertedNum = jsonStr as number;  // ❌ 危险：运行时仍是 string
assertedNum.toFixed();                  // 运行时抛错

// 正确做法：先 JSON.parse 解析，再 Number 转换
const realNum = Number(JSON.parse(jsonStr)); // 42，真正的 number
```

**断言的合理使用场景**：

1. 处理 `JSON.parse` 的返回值（其返回 `any`，应先断言为 `unknown` 再收窄）。
2. DOM 查询（`document.querySelector('#btn') as HTMLButtonElement`，开发者确认元素类型）。
3. 联合类型中「跳过判别字段直接断言为某分支」（需开发者负责正确性）。

**断言的不合理使用**：

- 用 `as unknown as T` 绕过类型检查，掩盖真正的类型不匹配。
- 用 `!` 断言一个实际上可能为 null 的值，逃避 `if` 判断。

> 对应代码：[`Code/type-assertion.ts`](./Code/type-assertion.ts) 第 5、6 节。

### 2.11 let vs const 的类型推断

TS 对 `let` 与 `const` 声明的变量会推断出**不同**的类型，这是初学者常感困惑的点。

**let 推断为「宽类型」**

```ts
let count = 10;       // 推断为 number（等价于 let count: number = 10）
count = 20;           // ✅ OK
count = 99.9;         // ✅ OK

let message = 'hi';   // 推断为 string
message = 'hello';    // ✅ OK
```

因为 `let` 变量后续可被重新赋值为**任意同类型值**，TS 选择最宽的类型（如 `number` 而非 `10`），保证后续赋值合法。

**const 推断为「字面量类型」**

```ts
const MAX = 10;       // 推断为 10（字面量类型，等价于 const MAX: 10 = 10）
const TITLE = 'TS';   // 推断为 'TS'
const FLAG = true;    // 推断为 true

MAX = 20;             // ❌ 报错：const 不可重新赋值
```

因为 `const` 变量**绑定不可变**，TS 把类型精确到具体的字面量值。这让字面量类型校验成为可能：

```ts
function onlyTen(n: 10) { /* ... */ }

const MAX = 10;
let count = 10;

onlyTen(MAX);    // ✅ OK：MAX 推断为字面量类型 10
onlyTen(count);  // ❌ 报错：count 推断为 number，不能赋给字面量类型 10
```

**对象属性的例外：const 只锁「绑定」，不锁「内部属性」**

```ts
const config = { port: 3000 };
config.port = 4000;        // ✅ OK：对象内部属性仍可变
config = { port: 5000 };   // ❌ 报错：const 不可重新赋值
```

要让对象属性也只读，需要用 `as const` 断言（后续章节详讲）：

```ts
const config = { port: 3000 } as const;
config.port = 4000; // ❌ 报错：port 是只读字面量属性
```

> 对应代码：[`Code/primitive-types.ts`](./Code/primitive-types.ts) 第 2 节。

---

## 三、类型收窄初步

类型收窄（Type Narrowing）是 TS 在「**控制流分支内**」自动把联合类型「变窄」到具体类型的能力。这是 TS 类型系统真正强大的地方——它让你无需显式断言，就能在 `if`、`switch`、循环内获得精确的类型。

本节只做初步介绍，Day05 会详讲。这里先掌握三种最基本的收窄方式。

**1. typeof 守卫**

```ts
function padLeft(value: string | number, padding: string | number): string {
  if (typeof padding === 'number') {
    // 此处 padding 收窄为 number（排除了 string）
    return ' '.repeat(padding) + value;
  }
  // 此处 padding 收窄为 string
  return padding + value;
}
```

`typeof` 守卫能区分 `string / number / boolean / symbol / bigint / undefined / object / function` 八种类型。注意 `null` 的 `typeof` 返回 `'object'`（历史遗留 bug），所以 `typeof` **不能**用来区分 `null`。

**2. truthy 收窄**

在 `if (x)` 中，TS 会排除所有 falsy 值（`null / undefined / '' / 0 / false / NaN`）：

```ts
function printAll(values: Array<string | null | undefined>) {
  for (const v of values) {
    if (v) {
      // v 收窄为 string（排除了 null / undefined / ''）
      console.log(v.toUpperCase());
    } else {
      // v 仍为 string | null | undefined
      console.log('falsy:', v);
    }
  }
}
```

注意：truthy 收窄会**误伤空字符串 `''` 和数字 `0`**——如果你的业务逻辑里它们是合法值，就不能用 truthy 收窄，应改用显式 `=== null` 或 `=== undefined`。

**3. == null 收窄**

`== null` 是 TS 中**唯一推荐的 `==` 用法**，因为它能同时匹配 `null` 和 `undefined`：

```ts
function greet(name: string | null | undefined): string {
  if (name == null) {
    // 同时排除 null 和 undefined
    return 'Hello, stranger';
  }
  // name 收窄为 string
  return 'Hello, ' + name.toUpperCase();
}
```

对比 `=== null`：只能排除 `null`，不能排除 `undefined`，往往需要再写一个 `=== undefined` 判断。

> 对应代码：[`Code/type-narrowing.ts`](./Code/type-narrowing.ts) 全文。

---

## 四、常见陷阱

### 陷阱一：any 的滥用

```ts
// ❌ 坏味道：返回 any，调用方拿到 any 后一切检查都失效
function fetchUser(id: string): any {
  return JSON.parse(apiResponse);
}

const user = fetchUser('001');
user.name.toUpperCase();    // 不报错，但 user 可能是 null
user.foo.bar.baz;           // 不报错，但 foo 可能不存在
```

**正确做法**：用 `unknown` 强制收窄，或定义接口。

```ts
interface User { name: string; age: number; }
function fetchUser(id: string): unknown {
  return JSON.parse(apiResponse);
}

const raw = fetchUser('001');
if (typeof raw === 'object' && raw !== null && 'name' in raw) {
  const user = raw as User;
  user.name.toUpperCase(); // ✅ 安全
}
```

### 陷阱二：断言的滥用

```ts
// ❌ 坏味道：用双重断言绕过检查，掩盖类型不匹配
const data = JSON.parse(rawJson) as unknown as UserData;

// ❌ 坏味道：用 ! 逃避 null 检查
const el = document.querySelector('#app')!.innerHTML;
```

**正确做法**：断言只用于「你比编译器更清楚类型」的场景，且优先用收窄而非断言。

```ts
const el = document.querySelector('#app');
if (el) {
  el.innerHTML = '...'; // 收窄后安全使用
}
```

### 陷阱三：数组合并的类型推断

合并不同类型数组时，TS 会推断出**联合类型数组**，而非你想要的「各取所需」：

```ts
const a = [1, 2, 3];      // number[]
const b = ['a', 'b'];     // string[]
const merged = [...a, ...b]; // (string | number)[]

merged[0].toFixed(); // ❌ 报错：string | number 上不存在 toFixed
```

**正确做法**：明确写出元组或显式类型。

```ts
const merged: [...number[], ...string[]] = [...a, ...b]; // 元组
// 或显式声明
const merged2: Array<number | string> = [...a, ...b];
```

### 陷阱四：空数组推断为 any[]

未指定类型的空数组，TS 会推断为 `any[]`（在 `noImplicitAny` 关闭时），这是隐性 `any` 的最大来源之一：

```ts
const arr = [];        // 推断为 any[]（隐患：后续 push 什么都接受）
arr.push(1);
arr.push('hello');
arr.push({ foo: 1 });  // 全部 OK，类型系统形同虚设

const n: number = arr[0]; // 推断为 any，悄悄传染
```

**正确做法**：声明数组时**必须显式指定元素类型**。

```ts
const arr: number[] = [];
arr.push(1);
arr.push('hello'); // ❌ 报错：string 不能赋给 number
```

### 陷阱五：truthy 收窄误伤空字符串与 0

```ts
function process(value: string | number) {
  if (value) {
    // value 收窄为 string | number（排除了 '' 和 0）
    // 但若 0 是合法输入，这里会漏处理！
  }
}
```

**正确做法**：业务上若 `0` 或 `''` 是合法值，用显式判断。

```ts
function process(value: string | number) {
  if (typeof value === 'string' && value !== '') { /* ... */ }
  if (typeof value === 'number' && !Number.isNaN(value)) { /* ... */ }
}
```

---

## 五、关键知识点总结

### 类型对照表

| 类型 | 关键字 / 语法 | 作用 | 典型场景 |
| --- | --- | --- | --- |
| 字符串 | `string` | 文本 | 名字、描述、URL |
| 数字 | `number` | 数值（整数 / 浮点 / 进制统一） | 计数、价格、坐标 |
| 布尔 | `boolean` | 真假 | 开关、状态 |
| 空 | `null` | 有意为之的空 | 显式标记「无值」 |
| 未定义 | `undefined` | 尚未赋值 | 可选参数、未初始化 |
| 符号 | `symbol` | 唯一标识 | 对象私有键 |
| 大整数 | `bigint` | 超过 MAX_SAFE_INTEGER 的整数 | 大数计算、加密 |
| 数组 | `T[]` / `Array<T>` | 同类型元素的有序列表 | 列表数据 |
| 只读数组 | `readonly T[]` / `ReadonlyArray<T>` | 不可变数组 | 配置、常量 |
| 元组 | `[T1, T2, ...]` | 固定长度、每位独立类型 | 坐标、键值对、HTTP 响应 |
| 命名元组 | `[x: number, y: number]` | 带标签的元组 | 提升可读性 |
| 任意（危险） | `any` | 放弃检查 | 老代码迁移、临时调试 |
| 任意（安全） | `unknown` | 接收任意值但必须收窄 | API 边界、JSON.parse |
| 永不出现 | `never` | 永不返回 / 穷尽检查 | throw、exhaustive check |
| 无返回值 | `void` | 函数不返回有意义值 | 回调、副作用函数 |
| 非原始值 | `object` | 排除 7 种原始类型 | 接收任意对象 |
| 字面量类型 | `'a' \| 'b'` / `1 \| 2` / `true` | 精确到具体值 | 状态机、固定取值 |

### 断言语法对照表

| 语法 | 名称 | 用途 | 适用文件 |
| --- | --- | --- | --- |
| `value as T` | as 断言 | 把类型断言为 T | `.ts` / `.tsx` 通用 |
| `<T>value` | 尖括号断言 | 等价 as | 仅 `.ts`，`.tsx` 与 JSX 冲突 |
| `value!` | 非空断言 | 断言非 null / undefined | 通用 |
| `value as unknown as T` | 双重断言 | 绕过重叠检查 | 通用（极度谨慎） |

### let vs const 推断对照表

| 声明 | 字面量 `10` | 推断类型 | 说明 |
| --- | --- | --- | --- |
| `let x = 10` | 可重新赋值 | `number` | 推断为宽类型，保证后续赋值合法 |
| `const x = 10` | 不可重新赋值 | `10`（字面量） | 推断为字面量类型，精确到值 |
| `let s = 'hi'` | 可重新赋值 | `string` | 宽类型 |
| `const s = 'hi'` | 不可重新赋值 | `'hi'` | 字面量类型 |
| `const obj = { a: 1 }` | 绑定不可变，属性可变 | `{ a: number }` | 属性仍是宽类型 |
| `const obj = { a: 1 } as const` | 全部只读 | `{ readonly a: 1 }` | 属性也变字面量类型 |

### 核心结论速记

- **TS 是渐进式类型**：类型可选，编译期检查，运行时擦除。
- **`unknown` 优于 `any`**：需要「能接收任意值」时一律用 `unknown`，强制收窄。
- **`never` 用于穷尽检查**：在 `switch` 的 `default` 分支用 `const _: never = x;` 防止遗漏分支。
- **字面量联合优于 enum**：除非需要反向映射，否则用 `'idle' | 'loading' | ...`。
- **断言 ≠ 转换**：断言只在编译期，转换才在运行时改变值。
- **const 推断字面量类型**：这是字面量类型校验的基础，配合 `typeof` 可提取。
- **空数组必须显式类型**：`const arr = []` 是隐性 `any[]`，必须 `const arr: T[] = []`。
- **`== null` 是唯一推荐的 `==`**：同时排除 `null` 和 `undefined`。

---

## 六、实战练习

以下三个练习相互独立，建议按顺序完成。每个练习对应 `Code/` 目录下一个 `.ts` 文件，可通过 `npx ts-node 文件名.ts` 或 `npm run <脚本名>` 运行验证。

### 练习一：basic-types-quiz.ts —— 原始类型与推断

**任务描述**

编写一个脚本 `basic-types-quiz.ts`，完成：

1. 声明七个变量分别对应七种原始类型（`string / number / boolean / null / undefined / symbol / bigint`），并显式标注类型。
2. 演示 `let` 与 `const` 的推断差异：用 `let` 声明 `count = 10`、用 `const` 声明 `MAX = 10`，然后定义一个 `onlyTen(n: 10)` 函数，分别尝试调用（`onlyTen(MAX)` 应通过、`onlyTen(count)` 应报错，把报错的调用注释掉并写明原因）。
3. 用 `console.log` 输出每个变量的值与 `typeof` 结果。

**预期输出示例**

```
string: traer (typeof: string)
number: 28 (typeof: number)
boolean: true (typeof: boolean)
null: null (typeof: object)
undefined: undefined (typeof: undefined)
symbol: Symbol(id) (typeof: symbol)
bigint: 9007199254740991n (typeof: bigint)
let count 推断为 number, const MAX 推断为字面量 10
onlyTen(MAX) 调用成功: 10
```

**运行方式**

```bash
cd Code
npx ts-node basic-types-quiz.ts
```

### 练习二：safe-parse.ts —— unknown 收窄实战

**任务描述**

编写一个脚本 `safe-parse.ts`，完成：

1. 模拟从 API 拿到的 JSON 字符串：`const raw = '{"name":"Trae","age":28,"role":"admin"}'`。
2. 用 `JSON.parse` 解析（返回 `any`），立即用 `as unknown` 转为 `unknown`。
3. 编写一个类型守卫函数 `isUser(obj: unknown): obj is { name: string; age: number; role: string }`，用 `typeof`、`in` 操作符逐字段校验。
4. 调用守卫函数收窄后，安全访问 `name.toUpperCase()`、`age + 1`、`role`，并输出。
5. 再用一段非法 JSON（如 `'{"name":"Trae"}'`，缺 `age`）测试守卫函数应返回 `false`，并输出「数据格式不合法」。

**预期输出示例**

```
合法数据：
  name = TRAE
  age  = 29
  role = admin
非法数据（缺 age）：数据格式不合法
```

**运行方式**

```bash
cd Code
npx ts-node safe-parse.ts
```

### 练习三：request-state.ts —— 联合字面量状态机

**任务描述**

编写一个脚本 `request-state.ts`，完成：

1. 用联合字面量定义请求状态：`type Status = 'idle' | 'loading' | 'success' | 'error'`。
2. 定义 `interface State { status: Status; data?: string; error?: string }`。
3. 编写 `describe(s: State): string` 函数，用 `switch (s.status)` 返回不同描述：
   - `idle` → 「等待发起请求」
   - `loading` → 「加载中...」
   - `success` → 「成功：{data}」
   - `error` → 「失败：{error}」
4. 在 `default` 分支用 `const _: never = s;` 做穷尽检查。
5. 测试四种状态各调用一次，并验证：若新增一个 `'cancelled'` 状态到 `Status` 但不处理，`default` 分支会编译报错（把改动注释起来说明）。

**预期输出示例**

```
[idle]    等待发起请求
[loading] 加载中...
[success] 成功：用户列表
[error]   失败：网络超时
```

**运行方式**

```bash
cd Code
npx ts-node request-state.ts
```

---

## 下节预告

下一节 **Day03** 将进入 **接口与类型别名**：深入 `interface` 与 `type` 的差异与取舍、可选属性与只读属性、索引签名、函数类型定义、类型合并（声明合并）、以及如何为第三方库编写 `.d.ts` 声明文件，为后续「泛型」与「高级类型」打下基础。
