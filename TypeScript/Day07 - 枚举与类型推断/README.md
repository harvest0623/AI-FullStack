# Day07 - 枚举与类型推断

> 本篇聚焦 TypeScript 中两个让代码“既严谨又简洁”的机制：**枚举（enum）** 与 **类型推断（Type Inference）**。枚举为我们提供了一组带名字的常量集合，让魔法数字与字符串获得语义；类型推断则是 TS 真正“智能”的核心机制——当省去注解时，编译器会沿着声明位置、控制流、上下文反向推导出最合适的类型。理解推断的边界，才能既享受“少写注解”的便利，又避免“推断过宽 / 过窄”带来的隐患。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解 - 枚举](#二理论知识讲解---枚举)
  - [2.1 数字枚举：默认递增与自定义初始值](#21-数字枚举默认递增与自定义初始值)
  - [2.2 反向映射：enum[key] = value 与 enum[value] = key](#22-反向映射enumkey--value-与-enumvalue--key)
  - [2.3 字符串枚举：字面量字符串、无反向映射](#23-字符串枚举字面量字符串无反向映射)
  - [2.4 异构枚举 heterogeneous enum：数字与字符串混合（不推荐）](#24-异构枚举-heterogeneous-enum数字与字符串混合不推荐)
  - [2.5 枚举成员类型与联合枚举](#25-枚举成员类型与联合枚举)
  - [2.6 const enum：编译时内联与 isolatedModules 限制](#26-const-enum编译时内联与-isolatedmodules-限制)
  - [2.7 枚举的运行时对象：Object.keys / values / entries](#27-枚举的运行时对象objectkeys--values--entries)
  - [2.8 枚举 vs 联合字面量类型 vs as const](#28-枚举-vs-联合字面量类型-vs-as-const)
  - [2.9 枚举的典型使用场景](#29-枚举的典型使用场景)
- [三、理论知识讲解 - 类型推断（重点）](#三理论知识讲解---类型推断重点)
  - [3.1 类型推断的层次](#31-类型推断的层次)
  - [3.2 let 推断宽类型，const 推断字面量类型](#32-let-推断宽类型const-推断字面量类型)
  - [3.3 数组推断：元素联合、空数组与 const 断言元组](#33-数组推断元素联合空数组与-const-断言元组)
  - [3.4 对象字面量与解构推断](#34-对象字面量与解构推断)
  - [3.5 上下文类型 contextual typing](#35-上下文类型-contextual-typing)
  - [3.6 控制流分析 CFA 与类型收窄](#36-控制流分析-cfa-与类型收窄)
  - [3.7 类型拓宽 widening](#37-类型拓宽-widening)
  - [3.8 const 断言 as const：让推断最窄](#38-const-断言-as-const让推断最窄)
  - [3.9 最佳通用类型 best common type](#39-最佳通用类型-best-common-type)
- [四、类型推断实战：何时省略、何时显式标注](#四类型推断实战何时省略何时显式标注)
- [五、关键知识点总结](#五关键知识点总结)
- [六、实战练习](#六实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 准确描述数字枚举与字符串枚举在编译产物与反向映射上的差异。
2. 解释 `enum` 在运行时是真实对象、而 `const enum` 是编译期内联的原因。
3. 说出 `isolatedModules` 下 `const enum` 的限制，并知道如何用 `as const` 替代。
4. 在枚举、字面量联合、`as const` 三者之间根据“可读性 / 树摇 / 反向映射”三个维度做出选型。
5. 描述类型推断的四个层次：变量声明、函数返回值、结构化对象、解构。
6. 区分 `let` 推断宽类型与 `const` 推断字面量类型的行为差异，并知道何时会发生类型拓宽。
7. 识别上下文类型（contextual typing）在事件处理器、回调函数中的作用。
8. 用 `as const` 让推断结果收窄到最窄字面量类型，并使对象变为 `readonly`。
9. 解释数组推断中的“最佳通用类型”规则，能预测混合元素数组的推断结果。
10. 在工程中判断何时该省略注解、何时必须显式标注（公共 API、复杂签名）。

---

## 二、理论知识讲解 - 枚举

枚举（`enum`）是 TS 为数不多的“既 additions 类型又 additions 运行时”的语法。它把一组相关的常量打包成有名字的集合，避免代码里出现 `0` `1` `2` 这类无语义的魔法数字。

### 2.1 数字枚举：默认递增与自定义初始值

数字枚举是最常见的形式。不给初始值时，第一个成员默认为 `0`，后续成员依次加 1：

```ts
enum Direction {
  Up,      // 0
  Down,    // 1
  Left,    // 2
  Right,   // 3
}

Direction.Up;     // 0
Direction.Right;  // 3
```

可以给任意成员指定初始值，未指定初始值的后续成员从前一个 +1 开始递增：

```ts
enum HttpStatus {
  Ok            = 200,
  Created       = 201,
  BadRequest    = 400,
  Unauthorized  = 401,
  NotFound      = 404,
  InternalError = 500,
}

// 不连续也无妨
enum Permission {
  Read    = 1,
  Write   = 2,
  Execute = 4,
  Admin   = 8,
}
```

> 💡 位运算枚举（`1, 2, 4, 8, ...`）常用于权限位掩码，可用 `Read | Write` 表示同时具备读和写权限。

### 2.2 反向映射：enum[key] = value 与 enum[value] = key

数字枚举除了正向访问 `Direction.Up === 0`，还支持**反向映射**：用值反查键名。

```ts
Direction[0];   // 'Up'
Direction[3];   // 'Right'

const name = Direction[Direction.Up];   // 'Up'
```

反向映射的底层原理是 TS 为数字枚举生成的运行时对象同时写入了两组键：

```js
// 编译产物（简化）
var Direction;
(function (Direction) {
  Direction[Direction['Up'] = 0] = 'Up';
  Direction[Direction['Down'] = 1] = 'Down';
  // ...
})(Direction || (Direction = {}));
```

注意这种 `(obj[k] = v) = k` 的写法利用了赋值表达式的返回值——把 `v` 作为键、`k` 作为值再写一次。

### 2.3 字符串枚举：字面量字符串、无反向映射

字符串枚举的每个成员必须显式给一个字符串字面量，**没有自动递增**：

```ts
enum Env {
  Dev   = 'development',
  Test  = 'test',
  Prod  = 'production',
}

Env.Dev;   // 'development'
```

字符串枚举**没有反向映射**：

```ts
// Env['development'];   // ❌ undefined，编译期也会报错
```

字符串枚举的优势在于序列化：调试时看到的是 `'production'` 而不是 `2`，日志可读性强。代价是占更多内存、不能反查名字。

### 2.4 异构枚举 heterogeneous enum：数字与字符串混合（不推荐）

数字与字符串可以混在一个枚举里，称为异构枚举：

```ts
enum Mixed {
  No   = 0,
  Yes  = 'YES',
}
```

**强烈不推荐**使用异构枚举。原因：

1. 反向映射规则混乱（只有数字成员会生成反向映射）。
2. 阅读时需要不断切换心智模型。
3. 几乎没有合理的使用场景。需要“混合”时，应该拆成两个枚举或改用字面量联合。

### 2.5 枚举成员类型与联合枚举

当所有枚举成员都是**字面量**（数字字面量或字符串字面量）时，枚举本身成为一个**联合类型**，每个成员成为它自己的**字面量类型**：

```ts
enum ShapeKind {
  Circle,    // 0
  Square,    // 1
}

interface Shape {
  kind: ShapeKind.Circle;   // 字面量类型，不只是 ShapeKind
  radius: number;
}

// kind 只能是 ShapeKind.Circle，传 ShapeKind.Square 会报错
const s: Shape = { kind: ShapeKind.Circle, radius: 10 };
```

更实用的场景是“联合枚举”作为判别字段：

```ts
enum TaskState {
  Pending,
  Running,
  Done,
}

function describe(state: TaskState): string {
  switch (state) {
    case TaskState.Pending: return '待处理';
    case TaskState.Running: return '处理中';
    case TaskState.Done:    return '已完成';
  }
}
```

每个 `case` 内 `state` 都被收窄为对应的字面量成员类型。

### 2.6 const enum：编译时内联与 isolatedModules 限制

`const enum` 是一种特殊形态：编译时**完全内联**，不生成运行时对象：

```ts
const enum Color {
  Red,
  Green,
  Blue,
}

const c = Color.Red;
// 编译后：const c = 0;   （没有任何 Color 对象！）
```

优点：

- 零运行时开销，体积更小。
- 编译期就能完成所有访问。

但 `const enum` 在跨文件 + `isolatedModules: true`（vite/esbuild/swc/babel 等默认开启）时会有问题：编译器无法假设其他文件导出的 `const enum` 真的存在，会直接报错或退化为普通 `enum`。

```ts
// file-a.ts
export const enum Mode { Read, Write }

// file-b.ts  ——  在 isolatedModules 下：
import { Mode } from './file-a';
const m = Mode.Read;   // ⚠️ 部分工具链下会编译错误或行为不一致
```

> 📌 **推荐做法**：在新项目中用 `as const` 对象替代 `const enum`（见 2.8），避免 `isolatedModules` 兼容性陷阱。除非项目全用 `tsc` 编译，否则慎用 `const enum`。

### 2.7 枚举的运行时对象：Object.keys / values / entries

普通 `enum` 在运行时是**真实存在的对象**，可以用 `Object.keys` / `values` / `entries` 遍历：

```ts
enum Role {
  Guest = 0,
  User  = 1,
  Admin = 2,
}

// 数字枚举既有正向键也有反向键
Object.keys(Role);
// ['0', '1', '2', 'Guest', 'User', 'Admin']

Object.values(Role);
// [0, 1, 2, 'Guest', 'User', 'Admin']   —— 数字 + 字符串混在一起

// 过滤出“名字键”
const names = Object.keys(Role).filter((k) => isNaN(Number(k)));
// ['Guest', 'User', 'Admin']
```

字符串枚举只有名字键，没有反向键：

```ts
enum Env { Dev = 'dev', Prod = 'prod' }
Object.keys(Env);   // ['Dev', 'Prod']   —— 干净
```

这也是字符串枚举更适合做“配置常量”的原因之一。

### 2.8 枚举 vs 联合字面量类型 vs as const

表达“有限常量集合”有三种主流写法：

```ts
// ① enum
enum StatusA { Pending, Running, Done }

// ② 字面量联合
type StatusB = 'pending' | 'running' | 'done';

// ③ as const 对象
const StatusC = {
  Pending: 'pending',
  Running: 'running',
  Done:    'done',
} as const;
type StatusCValue = typeof StatusC[keyof typeof StatusC];
// 'pending' | 'running' | 'done'
```

三者对比：

| 维度 | `enum` | 字面量联合 | `as const` 对象 |
|------|--------|------------|----------------|
| 运行时产物 | 真实对象（数字枚举带反向映射） | 零运行时开销 | 一个普通只读对象 |
| 树摇友好 | ❌ 整体保留 | ✅ 类型可消除 | ✅ 对象可被打包工具优化 |
| 反向映射 | ✅ 数字枚举支持 | ❌ | ❌（可手写） |
| `isolatedModules` 兼容 | 普通枚举可用，`const enum` 受限 | ✅ | ✅ |
| 自增能力 | ✅ 数字枚举支持 | ❌ | ❌ |
| 跨文件复用 | `export enum` | `import type` | 普通 `import` |
| 调试可读性 | 数字枚举差（看到 `2`） | 字符串联合最好 | 字符串值时好 |

社区共识：**新项目优先用 `as const` 对象 + 联合类型**，既享受类型安全，又有运行时对象可用，且不踩 `isolatedModules` 的坑。

### 2.9 枚举的典型使用场景

- **HTTP 状态码**：`enum HttpStatus { Ok = 200, NotFound = 404, ... }`。
- **角色权限**：`enum Role { Guest, User, Admin }` 或位掩码 `enum Permission { Read = 1, Write = 2, Execute = 4 }`。
- **环境配置**：`enum Env { Dev, Test, Prod }`，更倾向用字符串值便于日志可读。
- **状态机状态**：可辨识联合的判别字段（与 `type` 字段同义）。
- **协议常量**：消息类型、事件名、错误码等。

> ⚠️ 枚举的“自增”特性是把双刃剑：新增成员若插在中间，会让所有后续成员的数字值偏移，可能破坏持久化数据。涉及序列化的枚举应该显式赋值且永不调整顺序。

---

## 三、理论知识讲解 - 类型推断（重点）

类型推断是 TS 的“自动挡”：当你不写注解时，编译器根据上下文反推类型。它的存在让 TS 比 Java / C# 这类“处处显式注解”的语言写起来更轻盈。

### 3.1 类型推断的层次

TS 的推断覆盖四个层次：

| 层次 | 触发位置 | 示例 |
|------|----------|------|
| 变量声明 | `let` / `const` / `var` 初始化 | `let x = 1` 推断 `number` |
| 函数返回值 | `return` 表达式 | `function f() { return 1 }` 推断返回 `number` |
| 结构化对象 | 对象字面量初始化 | `const p = { x: 1, y: 2 }` |
| 解构 | 数组 / 对象解构 | `const { x } = point` |

```ts
let count = 10;              // number
const pi = 3.14;             // 3.14（字面量）
function add(a: number, b: number) { return a + b; }   // 返回 number
const point = { x: 0, y: 0 };   // { x: number; y: number }
const { x } = point;         // number
```

### 3.2 let 推断宽类型，const 推断字面量类型

这是类型推断最基础的规则：

```ts
let n = 1;       // number   —— let 可重新赋值，所以推断宽类型
const c = 1;     // 1        —— const 不可变，推断字面量类型

let s = 'hi';    // string
const s2 = 'hi'; // 'hi'

let b = true;    // boolean
const b2 = true; // true
```

原因：`let` 声明的变量可能被重新赋值为同类的其他值，所以 TS 选择“宽类型”保留弹性；`const` 一旦确定就不能改，TS 可以放心推断到字面量级别。

**例外：对象 / 数组的 const**

```ts
const arr = [1, 2, 3];     // number[]   —— 元素仍是 number，不是 1|2|3
const obj = { x: 1 };      // { x: number }
obj.x = 2;                 // ✅ 合法，因为 obj 的属性不是 readonly
```

`const` 只锁住变量本身的绑定，不锁住内部属性。要让属性也变成字面量类型，需要 `as const`（见 3.8）。

### 3.3 数组推断：元素联合、空数组与 const 断言元组

数组推断有三种典型场景：

```ts
// ① 同类型元素 -> T[]
const nums = [1, 2, 3];           // number[]

// ② 混合类型 -> 联合元素数组 (T | U)[]
const mixed = [1, 'two', true];   // (number | string | boolean)[]

// ③ 空数组 -> any[]，随后赋值会反向收窄
const empty = [];                 // any[]
empty.push(1);                    // 推断收窄为 number[]？需视上下文
```

空数组的推断会“随赋值演化”，但在严格模式下，跨函数边界后会被固化为 `any[]` 或最后一个 push 的类型。建议**显式标注空数组类型**：

```ts
const arr: number[] = [];
```

`as const` 让数组推断为**只读元组**：

```ts
const pair = [1, 'two'] as const;
// 类型：readonly [1, 'two']
// pair[0] -> 1（字面量）
// pair[1] -> 'two'（字面量）
// pair.push(3);   // ❌ readonly
```

### 3.4 对象字面量与解构推断

对象字面量的推断遵循“属性：推断类型”：

```ts
const user = {
  id: 1,
  name: 'Alice',
  roles: ['admin', 'user'],
};
// 推断：{ id: number; name: string; roles: string[] }
```

解构会按属性推断出独立变量：

```ts
const { id, name } = user;
// id: number
// name: string

const [first, ...rest] = [1, 2, 3];
// first: number, rest: number[]
```

**重命名 + 默认值**：

```ts
const { name: userName = 'anonymous' } = user;
// userName: string
```

### 3.5 上下文类型 contextual typing

通常的类型推断是“从右向左”（由值推类型），上下文类型则是“从左向右”——**由变量被期待的类型反向约束右侧表达式**。

最典型的例子是事件处理器：

```ts
// button 是 HTMLButtonElement，addEventListener 期待 (ev: MouseEvent) => any
document.querySelector('button')?.addEventListener('click', (e) => {
  // e 自动推断为 MouseEvent，无需显式注解！
  console.log(e.currentTarget);
});

// 期望 string 类型的回调参数
const names: string[] = ['Alice', 'Bob'];
names.forEach((s) => {
  // s 自动推断为 string
  console.log(s.toUpperCase());
});
```

上下文类型让回调函数几乎不用手写参数注解。常见的触发场景：

- DOM 事件：`addEventListener('click', e => ...)` -> `MouseEvent`。
- 数组方法：`arr.map((x, i) => ...)` -> 元素类型 + `number`。
- Promise：`Promise<T>.then(value => ...)` -> `T`。
- 函数参数的函数类型：`type Fn = (x: number) => void; const f: Fn = (x) => x + 1;`。

### 3.6 控制流分析 CFA 与类型收窄

TS 编译器会沿控制流（`if` / `else` / `return` / `switch` / 三目 / 短路）逐步收窄类型（已在 Day05 详细介绍过）。这里只回顾与“推断”相关的点：

```ts
function f(x: string | number) {
  if (typeof x === 'string') {
    return x.length;        // x 收窄为 string，返回 number
  }
  return x.toFixed(0);      // x 收窄为 number，返回 string
  // 推断返回类型：number | string
}
```

CFA 让“局部位置的窄类型”能反作用于整体推断结果（如函数返回值类型）。

### 3.7 类型拓宽 widening

类型拓宽（widening）指 `let` / 可变位置上的字面量被“拓宽”为基础类型。常见的拓宽关系：

| 字面量 | 拓宽后 |
|--------|--------|
| `'hi'` | `string` |
| `1` | `number` |
| `true` | `boolean` |
| `null` | `any`（在严格模式 `strictNullChecks` 下保持 `null`，但 `let x = null` 仍会被拓宽为 `any`） |
| `undefined` | `any`（同上） |

```ts
let n = 1;          // number（字面量 1 被拓宽）
let s = 'hello';    // string
let b = true;       // boolean

let x = null;       // any   —— null 在 let 上拓宽为 any
const y = null;     // null  —— const 保留
```

**`null` 赋值给 `let` 拓宽为 `any`** 是个常见陷阱：

```ts
let value = null;       // any
value = 1;              // ✅ 没报错，因为 value 是 any
value = 'oops';         // ✅ 也没报错

// 想要严格约束，应该显式标注：
let strict: number | null = null;
// strict = 'oops';     // ❌
```

### 3.8 const 断言 as const：让推断最窄

`as const` 是“反向拓宽”的开关——把推断结果从宽类型“按住”在最窄的字面量类型：

```ts
const status = 'pending';        // 'pending'   （const 已经够窄）
let s = 'pending' as const;      // 'pending'   （as const 让 let 也保持字面量）

const cfg = {
  host: 'localhost',
  port: 3000,
  roles: ['admin', 'user'],
} as const;
// 推断：
// {
//   readonly host: 'localhost';
//   readonly port: 3000;
//   readonly roles: readonly ['admin', 'user'];
// }
```

`as const` 做了三件事：

1. 所有字面量保持字面量类型（不拓宽）。
2. 所有属性变 `readonly`。
3. 数组变 `readonly` 元组。

典型用途是构造“联合枚举的运行时对象”：

```ts
const Status = {
  Pending: 'pending',
  Running: 'running',
  Done:    'done',
} as const;

type Status = typeof Status[keyof typeof Status];
// 'pending' | 'running' | 'done'

function update(s: Status) { /* ... */ }
update(Status.Pending);     // ✅
// update('foo');           // ❌
```

### 3.9 最佳通用类型 best common type

数组字面量的元素类型不一定相同，TS 需要选一个“能涵盖所有元素的最低公共父类型”——这就是**最佳通用类型**。

```ts
const a = [1, 2, 3];                  // number[]
const b = [1, 'two', true];           // (number | string | boolean)[]

class Animal { name: string; }
class Dog extends Animal { bark(): void {} }
class Cat extends Animal { meow(): void {} }

const pets = [new Dog(), new Cat()];  // Dog[] ? Cat[] ? Animal[] ?
// 实际推断：(Dog | Cat)[]   —— 不自动找公共父类 Animal
```

注意：TS **不会自动找“最紧凑的公共父类”**，而是取所有元素类型的联合。如果想要 `Animal[]`，需要显式标注：

```ts
const pets: Animal[] = [new Dog(), new Cat()];
```

这一规则在处理混合类型数组时要特别留意，否则会在后续 `.map` 中得到联合类型而非基类。

---

## 四、类型推断实战：何时省略、何时显式标注

类型推断是“自动挡”，但“自动挡”不代表永远不需要手动操作。下面是工程中的取舍准则。

### 4.1 可以放心省略注解的场景

- **局部变量初始化**：`const count = arr.length;` —— 显然是 `number`。
- **回调函数参数**：`arr.map(x => x * 2)` —— 上下文类型已约束。
- **简单函数返回值**：`function add(a, b) { return a + b; }` —— 返回类型可由 `return` 推出。
- **解构**：`const { name } = user;` —— 跟随源对象属性类型。

### 4.2 必须显式标注的场景

- **公共 API / 库导出函数**：返回类型是契约的一部分，不应被实现细节牵着走。
  ```ts
  export function parseConfig(s: string): Config { /* ... */ }
  ```
- **复杂签名**：泛型约束、重载、可辨识联合的判别函数。
- **可能推断过宽的场景**：
  ```ts
  const arr = [];              // any[]，应该写 const arr: number[] = [];
  let value = null;            // any，应该写 let value: string | null = null;
  ```
- **希望锁定接口、防止实现“悄悄”改返回类型**：
  ```ts
  function getUser(id: number): User { /* ... */ }
  // 实现里若返回了 Partial<User>，会立刻报错
  ```

### 4.3 推断的反模式

```ts
// ❌ 反模式 1：依赖推断把 any 漏出来
function f(x) { return x.toFixed(2); }   // 参数 x 是 any（noImplicitAny 下会报错）

// ❌ 反模式 2：让混合数组推断成联合
const list = [1, '2', 3];                // (number | string)[]
list.map(x => x * 2);                    // ❌ string 不能 * 2

// ✅ 正确：拆分类型或显式约束
const nums: number[] = [1, 2, 3];
```

### 4.4 一条经验法则

> **内部代码相信推断；边界代码显式标注。** 函数内部的局部变量、临时计算可以靠推断；函数签名（参数 + 返回值）、对外导出的类型、跨模块的契约，必须显式标注，把推断结果“钉死”成契约。

---

## 五、关键知识点总结

1. **数字枚举**默认从 `0` 递增，可自定义初始值；支持**反向映射** `enum[value] = key`。
2. **字符串枚举**必须显式赋值，**没有反向映射**，但序列化可读性强。
3. **异构枚举**（数字 + 字符串混合）不推荐，行为复杂。
4. **联合枚举**：当所有成员都是字面量时，枚举本身成为联合类型，每个成员成为字面量类型。
5. **const enum** 编译时内联、不生成运行时对象，但 `isolatedModules` 下跨文件使用受限。
6. **普通 enum 是运行时真实对象**，可 `Object.keys/values/entries` 遍历；数字枚举既有正向键也有反向键。
7. **enum vs 字面量联合 vs as const**：新项目优先 `as const` 对象，兼顾类型安全与运行时可用性。
8. **类型推断四层次**：变量声明、函数返回值、结构化对象、解构。
9. **let 推断宽类型**，**const 推断字面量类型**；const 对象的属性仍可变。
10. **空数组推断为 `any[]`**，跨函数边界前可能随赋值演化，建议显式标注。
11. **上下文类型 contextual typing**：函数参数根据调用位置反推类型，让回调免注解。
12. **控制流分析 CFA** 让局部收窄反作用于函数返回值等整体推断。
13. **类型拓宽 widening**：字面量在 `let` 上拓宽为基础类型；`null` / `undefined` 拓宽为 `any`。
14. **as const** 是反向拓宽：保持字面量类型 + 全部 `readonly` + 数组变元组。
15. **最佳通用类型**：数组元素取联合而非公共父类，需要父类时显式标注。
16. **何时显式标注**：公共 API、复杂签名、可能推断过宽的边界场景。

---

## 六、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：用三种方式表达 HTTP 状态码（对应 `enum-vs-union.ts`）

分别用 `enum`、字面量联合、`as const` 对象三种方式，表达 `200 | 201 | 400 | 404 | 500` 这五个 HTTP 状态码，并各自实现 `describe(code): string` 返回中文名（如 `200 -> OK`）。要求：

1. 每种方式都能让 `describe(401)` 在编译期报错。
2. 用 `Object.keys` 在运行时列出所有合法状态码（思考：哪种方式最方便？哪种最不便？）。
3. 思考：如果未来要新增 `503`，三种方式分别要改哪些代码？

### 练习 2：观察 `as const` 对推断的影响（对应 `type-widening.ts`）

定义一个对象：

```ts
const config = {
  env: 'production',
  port: 3000,
  features: ['sso', 'audit'],
};
```

要求：

1. 不加 `as const`，写出 `typeof config` 的完整类型。
2. 加上 `as const`，再写出 `typeof config` 的完整类型。
3. 编写一个 `function getEnv(): 'production' | 'development'`，分别用两种 `config` 实现它，观察哪种能直接 `return config.env`，哪种需要断言。
4. 思考：如果 `features` 后续要 `push('logging')`，加 `as const` 后还能 push 吗？如何取舍？

### 练习 3：最佳通用类型与混合数组（对应 `best-common-type.ts`）

定义一个简单继承层级：

```ts
class Animal { constructor(public name: string) {} speak() { return `${this.name} 发出声音`; } }
class Dog extends Animal { speak() { return `${this.name} 汪汪`; } }
class Cat extends Animal { speak() { return `${this.name} 喵喵`; } }
```

要求：

1. 写 `const pets = [new Dog('A'), new Cat('B')]`，鼠标悬停查看推断类型，确认是否为 `(Dog | Cat)[]`。
2. 调用 `pets.map(p => p.speak())`，确认是否每个 `p` 都能访问 `speak`（为什么能？）。
3. 现在加上 `class Bird extends Animal { fly(): void {} }`，让 `pets` 包含一只 `Bird`。`pets.map(p => p.fly?.())` 能通过类型检查吗？
4. 把 `const pets` 显式标注为 `Animal[]`，对比推断结果与显式标注在 `p.fly` 调用上的差异，思考“何时该显式标注父类型”。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/numeric-enum.ts` | 数字枚举、自定义初始值、反向映射演示 |
| `Code/string-enum.ts` | 字符串枚举、无反向映射、联合枚举成员类型 |
| `Code/const-enum.ts` | const enum 编译时内联、与普通 enum 编译产物对比 |
| `Code/enum-vs-union.ts` | enum vs 联合字面量 vs as const 三种方式对比 |
| `Code/type-inference.ts` | let/const 推断、数组推断、对象推断、上下文类型 |
| `Code/type-widening.ts` | 类型拓宽演示、null 赋值拓宽、as const 收窄 |
| `Code/best-common-type.ts` | 数组元素联合、公共父类型推断 |

运行方式（需先在 `Code/` 目录执行 `npm install`）：

```bash
cd Code
npm install
npx ts-node numeric-enum.ts
npx ts-node string-enum.ts
npx ts-node const-enum.ts
npx ts-node enum-vs-union.ts
npx ts-node type-inference.ts
npx ts-node type-widening.ts
npx ts-node best-common-type.ts
```

或使用 `package.json` 中预置的脚本：

```bash
npm run numeric       # 等价于 ts-node numeric-enum.ts
npm run string        # 字符串枚举
npm run const         # const enum
npm run vs            # 三种方式对比
npm run inference     # 类型推断
npm run widening      # 类型拓宽
npm run bct           # 最佳通用类型
npm run type-check    # 全量类型检查（不输出文件）
```

---

> 📚 **延伸阅读**
> - TS 官方手册：[Enums](https://www.typescriptlang.org/docs/handbook/enums.html)
> - TS 官方手册：[Type Inference](https://www.typescriptlang.org/docs/handbook/type-inference.html)
> - TS 官方手册：[Literal Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-types)
> - TS Wiki：[Const Enums and isolatedModules](https://www.typescriptlang.org/docs/handbook/enums.html#const-enums)
> - 社区讨论：[Enum vs Union Type vs as const](https://github.com/microsoft/TypeScript/issues/26818)
> - TypeScript 5.x Release Notes：`isolatedModules` 与 `const enum` 行为的更新
