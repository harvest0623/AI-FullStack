# Day10 - 模块与命名空间

> TypeScript 的模块系统建立在 ES Modules 之上，额外增加了「类型导出」能力——`export type` / `import type` 让类型与值可以同文件共存，却又能在编译期被精确擦除。与之相对，命名空间（namespace）是 ES Modules 普及前的旧时代全局组织方式，如今仅剩 `.d.ts` 全局声明与旧库迁移两块自留地。本篇聚焦模块解析策略、类型导入导出、barrel file、声明合并、三斜线指令等工程核心概念，理清「何时用模块、何时用命名空间」的选型边界，为后续用 TS 组织真实项目代码打下地基。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解 - ES Modules 回顾](#二理论知识讲解---es-modules-回顾)
  - [2.1 import / export 基础](#21-import--export-基础)
  - [2.2 默认导出 vs 命名导出](#22-默认导出-vs-命名导出)
  - [2.3 重命名 as](#23-重命名-as)
  - [2.4 聚合导出 re-export](#24-聚合导出-re-export)
- [三、理论知识讲解 - TS 的类型导出](#三理论知识讲解---ts-的类型导出)
  - [3.1 export type / export interface](#31-export-type--export-interface)
  - [3.2 类型与值同文件导出](#32-类型与值同文件导出)
  - [3.3 import type 与 isolatedModules](#33-import-type-与-isolatedmodules)
- [四、模块解析策略](#四模块解析策略)
  - [4.1 五种策略对比](#41-五种策略对比)
  - [4.2 TS 5 推荐选择](#42-ts-5-推荐选择)
  - [4.3 解析查找顺序](#43-解析查找顺序)
  - [4.4 baseUrl 与 paths 别名](#44-baseurl-与-paths-别名)
- [五、命名空间 namespace](#五命名空间-namespace)
  - [5.1 旧时代的全局组织方式](#51-旧时代的全局组织方式)
  - [5.2 命名空间嵌套](#52-命名空间嵌套)
  - [5.3 跨文件命名空间](#53-跨文件命名空间)
  - [5.4 命名空间 vs 模块](#54-命名空间-vs-模块)
- [六、声明合并 Declaration Merging](#六声明合并-declaration-merging)
- [七、三斜线指令](#七三斜线指令)
- [八、模块与全局](#八模块与全局)
- [九、模块组织最佳实践](#九模块组织最佳实践)
- [十、tsconfig 模块配置速览](#十tsconfig-模块配置速览)
- [十一、关键知识点总结](#十一关键知识点总结)
- [十二、实战练习](#十二实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说出 ES Modules 的 `import` / `export`、默认导出与命名导出、`as` 重命名、re-export 聚合导出的语法与语义。
2. 区分 TS 的「类型导出」与「值导出」，并在 `isolatedModules` 下正确使用 `export type` / `import type`。
3. 列举 `classic` / `node` / `node16` / `nodenext` / `bundler` 五种模块解析策略的适用场景，并说明 TS 5 的推荐选择。
4. 配置 tsconfig 的 `baseUrl` 与 `paths`，用路径别名替代冗长的相对路径。
5. 理解 `namespace` 的定义、嵌套与跨文件引用（`/// <reference path`），并说明其运行时限制。
6. 在「现代 ES Modules」与「namespace」之间做出正确选型，避免在业务代码中滥用 namespace。
7. 解释声明合并的规则：同名的 `interface` / `function` / `namespace` 如何合并，以及合并带来的风险。
8. 区分「脚本文件」与「模块文件」的作用域差异，理解为何「无 import/export 的文件是全局的」。
9. 设计 barrel file（`index.ts`）聚合模块导出，并掌握循环依赖的处理思路。

---

## 二、理论知识讲解 - ES Modules 回顾

### 2.1 import / export 基础

ES Modules（ESM）是 JS 的官方模块系统，TS 完全兼容并扩展之。一个文件只要存在顶层 `import` 或 `export`，就是「模块」；否则是「脚本」（全局作用域，见第八节）。

```ts
// math.ts
export function add(a: number, b: number): number { return a + b; }
export const PI = 3.14159;

// main.ts
import { add, PI } from './math';
console.log(add(1, 2), PI);
```

要点：

- `export` 标记的成员是对外公开的「命名导出」，未 export 的成员外部无法访问。
- 模块自身作用域隔离，不会污染全局。
- 导入路径在 `Node` / `CommonJS` 下可省略扩展名；在 `NodeNext` / 原生 ESM 下需写全 `.js`（即使源文件是 `.ts`）。

### 2.2 默认导出 vs 命名导出

```ts
// logger.ts —— 默认导出（每个模块最多一个）
export default function log(msg: string) { console.log(msg); }

// 用法：默认导入不需要花括号，名字可任意
import log from './logger';
import whatever from './logger';   // 同样合法
```

```ts
// math.ts —— 命名导出
export function add(a: number, b: number) { return a + b; }

// 用法：必须用花括号，名字必须对得上
import { add } from './math';
```

对比：

| 维度 | 默认导出 | 命名导出 |
|------|----------|----------|
| 数量 | 每模块 1 个 | 任意多个 |
| 导入语法 | `import x from` | `import { x } from` |
| 重命名 | 导入时随意起名 | 需用 `as` 显式重命名 |
| 重构友好 | ❌ 改名不报错 | ✅ 改名会同步报错 |
| 推荐度 | 单一主入口时可用 | 工程首选 |

社区共识：**优先命名导出**，默认导出仅用于「模块最主力的那个 API」。React 的 `Component`、Vue 的 `createApp` 这类适合默认导出；工具函数集合用命名导出。

### 2.3 重命名 as

```ts
import { add as plus } from './math';      // 导入时重命名
export { add as plus } from './math';      // re-export 时重命名
```

常用于避免命名冲突、对齐团队命名规范。

### 2.4 聚合导出 re-export

「barrel file」（通常是 `index.ts`）把多个模块的导出集中重新导出，外部只需从一个入口导入：

```ts
// utils/index.ts
export { add, subtract } from './math-utils';
export { capitalize, slugify } from './string-utils';
export type { MathOptions } from './math-utils';
```

```ts
// 外部
import { add, capitalize, type MathOptions } from './utils';
```

价值：缩短导入路径、隐藏内部目录结构。代价：可能引入「未使用但被打包」的代码（需打包器树摇配合）。

---

## 三、理论知识讲解 - TS 的类型导出

### 3.1 export type / export interface

TS 在 ESM 之上新增了「类型导出」——类型与值可以同文件共存：

```ts
// math-utils.ts
export type MathOperation = 'add' | 'subtract' | 'multiply' | 'divide';
export interface MathOptions { precision?: number; }

export function add(a: number, b: number) { return a + b; }   // 值导出
```

类型导出在编译后会被完全擦除，不产生运行时代码。

### 3.2 类型与值同文件导出

推荐类型与其紧密相关的实现放同一文件，避免过早拆 `types.ts`：

```ts
// user.ts
export interface User { id: number; name: string; }                  // 类型
export function createUser(name: string): User {                     // 值
  return { id: Date.now(), name };
}
```

只有当类型被多个异构模块共享、且实现互相独立时，才单独抽 `types.ts`。

### 3.3 import type 与 isolatedModules

`isolatedModules: true` 模拟单文件编译器（Babel / esbuild / swc / ts-node `transpileOnly`）的行为：每个文件独立编译，**无法跨文件推断某个名字是类型还是值**。因此「仅类型」的导入必须显式标注：

```ts
// ✅ 显式声明仅导入类型，编译器可直接擦除
import type { MathOptions } from './math-utils';

// ✅ 混合导入：用 inline type 标记
import { add, type MathOptions } from './math-utils';

// ❌ isolatedModules 下报错：re-export 类型必须用 export type
export { MathOptions } from './math-utils';

// ✅ 正确
export type { MathOptions } from './math-utils';
```

`import type` 导入的名字只能出现在「类型位置」，不能作为值使用：

```ts
import type { User } from './user';
const u: User = { id: 1, name: 'Alice' };   // ✅ 类型位置
// const x = User;   // ❌ 值位置，报错
```

> 💡 **何时必开 isolatedModules**：项目使用 Babel / esbuild / swc / Vite / ts-node `transpileOnly` 时强制开启，让 `tsc` 的类型检查与单文件编译器行为一致。现代脚手架（如 Vite）默认开启。

---

## 四、模块解析策略

### 4.1 五种策略对比

| 策略 | `moduleResolution` | 适用场景 | 关键行为 |
|------|---------------------|----------|----------|
| `classic` | `classic` | 旧版 TS | 仅按相对路径查找，不识别 `node_modules`，已弃用 |
| `node` | `Node` | Node CJS 项目 | 模拟 `require`：先同名文件、再目录 `index`、再 `node_modules` |
| `node16` | `Node16` | Node 16+ | 支持 `package.json` `exports`，区分 ESM/CJS 严格语义 |
| `nodenext` | `NodeNext` | Node 现代 | 等同 `node16`，指向最新 Node 解析规则 |
| `bundler` | `Bundler` | Vite/webpack/esbuild | TS 5 新增，模拟打包器，不强制扩展名，支持 `paths`，前端首选 |

### 4.2 TS 5 推荐选择

- **前端打包项目**：`module: ESNext` + `moduleResolution: Bundler`
- **Node CommonJS**：`module: CommonJS` + `moduleResolution: Node`
- **Node ESM**：`module: NodeNext` + `moduleResolution: NodeNext`

### 4.3 解析查找顺序

对 `import { add } from './math-utils'`（Node 策略）：

1. 尝试 `./math-utils.ts` → 命中
2. 否则 `./math-utils.tsx` / `./math-utils.d.ts`
3. 否则 `./math-utils/index.ts`（目录 + index）

对裸导入 `import _ from 'lodash'`：沿目录树向上查找 `node_modules/lodash`，命中后按 `package.json` 的 `main` / `types` 定位入口。

### 4.4 baseUrl 与 paths 别名

```jsonc
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@utils/*": ["./src/utils/*"]
    }
  }
}
```

```ts
// 别名导入，替代 '../../../utils/math'
import { add } from '@utils/math';
```

注意：`paths` 是 TS **编译期** 解析能力，运行时（Node / 打包器）需要额外配置（Vite 的 `resolve.alias`、Node 的 `tsconfig-paths` 等）。详见 `Code/module-resolution.md`。

---

## 五、命名空间 namespace

### 5.1 旧时代的全局组织方式

namespace 是 TS 早期（ES Modules 落地前）组织代码的手段：用一个对象把一组相关声明包起来，挂到全局。

```ts
namespace App {
  export const VERSION = '1.0.0';
  export function bootstrap() { /* ... */ }
}

App.bootstrap();
```

注意：`namespace` 内部必须用 `export` 才能被外部访问，与模块的 `export` 语义一致。

### 5.2 命名空间嵌套

```ts
namespace App {
  export namespace UI {
    export function render(name: string) { return `<div>${name}</div>`; }
  }
}

App.UI.render('hello');
```

⚠️ 子命名空间不要与全局对象同名（如 `App.Math` 会遮蔽全局 `Math`，导致内部 `Math.PI` 解析错误）。

### 5.3 跨文件命名空间

同名的 namespace 在多个文件中声明会自动合并。配合三斜线指令声明依赖：

```ts
// file-a.ts
namespace Validation {
  export function isEmail(s: string) { return /@/.test(s); }
}

// file-b.ts
/// <reference path="./file-a.ts" />
namespace Validation {
  export function isPhone(s: string) { return /^1\d{10}$/.test(s); }
}
// 此处 Validation.isEmail 与 Validation.isPhone 都可用（类型层面）
```

⚠️ **运行时限制**：在 CommonJS / ESM 下，每个文件是独立模块，跨文件的 namespace「值」在运行时不可达。`/// <reference path` 仅提供「类型可见性」，不产生运行时引用。现代代码应改用 `import`。

### 5.4 命名空间 vs 模块

| 维度 | namespace | ES Modules |
|------|-----------|------------|
| 作用域 | 全局（脚本文件） | 文件级隔离 |
| 依赖声明 | `/// <reference path>` | `import` |
| 运行时合并 | 仅限全局脚本 / concatenation | 标准模块系统 |
| 树摇 | ❌ 困难 | ✅ 友好 |
| 现代推荐 | ❌ 仅 `.d.ts` / 旧库迁移 | ✅ 首选 |

结论：**新项目一律用 ES Modules，namespace 仅用于 `.d.ts` 全局声明与旧库迁移**。

---

## 六、声明合并 Declaration Merging

同名声明的合并规则：

| 声明类型 | 是否可合并 | 合并行为 |
|----------|------------|----------|
| `interface` | ✅ | 成员并集；同名且签名相同的函数成员冲突，后定义覆盖 |
| `function` | ✅ | 形成重载集合 |
| `namespace` | ✅ | 成员并集 |
| `namespace` + `interface` | ✅ | interface 进入 namespace，作为其类型成员 |
| `namespace` + `function` | ✅ | namespace 作为 function 的属性添加 |
| `type alias` | ❌ | 不能合并，重名直接报错 |
| `class` | 部分 | 类不能与同名类合并，但可与 interface / namespace 合并 |

```ts
interface Box { width: number; }
interface Box { height: number; }
// Box = { width: number; height: number }   成员并集

function fmt(n: number): string;
function fmt(s: string): string;
function fmt(x: number | string): string { return String(x); }
// fmt 形成重载集合

namespace Validation { export const A = 1; }
namespace Validation { export const B = 2; }
// Validation = { A: 1, B: 2 }
```

⚠️ 风险：声明合并对「全局类型」有传染性——任何第三方库扩展 `Window` / `String` 等全局 interface 都会影响全局类型推导，难以追踪。库作者应谨慎使用，业务代码一般不要合并。

---

## 七、三斜线指令

`/// <reference path="..." />` 是 TS 早期的依赖声明方式，告诉编译器「编译本文件前先把目标文件纳入程序」：

```ts
/// <reference path="./declaration-merging.ts" />
/// <reference types="node" />
/// <reference lib="ES2020" />
```

现代项目应：

- 用 `import` 替代 `/// <reference path`
- 用 `tsconfig.json` 的 `types` / `lib` 替代 `/// <reference types` / `lib`

仅在维护老 `.d.ts` 文件时可能遇到三斜线指令。

---

## 八、模块与全局

| 文件特征 | 角色 | 作用域 |
|----------|------|--------|
| 有顶层 `import` 或 `export` | 模块 | 文件级隔离 |
| 无顶层 `import` / `export` | 脚本 | 全局作用域 |

```ts
// script.ts —— 脚本，声明位于全局
const x = 1;
console.log(x);
```

```ts
// module.ts —— 模块，x 仅本文件可见
export const x = 1;
```

> ⚠️ **常见坑**：在严格项目里，误把本应是模块的文件写成了脚本，导致全局污染或类型冲突。建议每个 `.ts` 文件至少有一个 `export`（哪怕是 `export {}`）以明确为模块。

```ts
// 显式声明为空模块，避免被当成脚本
export {};
```

---

## 九、模块组织最佳实践

### 9.1 一文件一模块

文件名即模块名，一个文件聚焦一组相关功能。避免单文件塞多个不相关模块。

### 9.2 Barrel file 聚合

用 `index.ts` 聚合导出，对外隐藏目录结构：

```
utils/
  math-utils.ts
  string-utils.ts
  index.ts          ← barrel
```

### 9.3 类型与实现同文件

类型与其实现紧耦合时同文件，避免过早拆 `types.ts`。仅在多模块共享独立类型时才拆。

### 9.4 循环依赖处理

循环依赖（A → B → A）是模块地狱的根源。处理手段：

1. **重构拆分**：把 A、B 共同依赖的部分提到 C，让 A → C、B → C。
2. **延迟导入**：在函数内部 `import`（运行时再解析），打破顶层循环。
3. **接口反转**：用接口 + 依赖注入替代直接 import。

```ts
// 延迟导入示例
async function loadModule() {
  const { heavy } = await import('./heavy');   // 动态 import，运行时再解析
  heavy();
}
```

---

## 十、tsconfig 模块配置速览

> Day12 会详解 tsconfig，这里先铺垫与「模块」相关的核心字段。

```jsonc
{
  "compilerOptions": {
    "module": "CommonJS",            // 输出模块格式：CommonJS / ESNext / NodeNext
    "moduleResolution": "Node",      // 解析策略：Node / NodeNext / Bundler
    "baseUrl": ".",                  // 路径别名基准
    "paths": { "@/*": ["./src/*"] }, // 别名映射
    "isolatedModules": true,         // 单文件编译模式，要求 import type
    "esModuleInterop": true,         // 兼容 CJS 默认导入
    "resolveJsonModule": true        // 允许 import json
  }
}
```

| 字段 | 作用 | Day10 选用 |
|------|------|------------|
| `module` | 编译输出格式 | `CommonJS`（ts-node 友好） |
| `moduleResolution` | 解析策略 | `Node` |
| `baseUrl` + `paths` | 路径别名 | 已配置 `@/*` |
| `isolatedModules` | 单文件编译约束 | `true` |

---

## 十一、关键知识点总结

1. **模块 vs 脚本**：有顶层 import/export 即为模块（文件作用域），否则为脚本（全局作用域）。
2. **命名导出优先**：默认导出仅用于单一主入口，命名导出利于重构与树摇。
3. **TS 类型导出**：`export type` / `export interface` 编译后被擦除，与值导出可同文件共存。
4. **import type**：`isolatedModules` 下的硬性要求，标记「仅类型」导入；re-export 类型必须用 `export type`。
5. **模块解析策略**：前端用 `Bundler`，Node CJS 用 `Node`，Node ESM 用 `NodeNext`。
6. **paths 别名**：编译期解析，运行时需打包器或 `tsconfig-paths` 配合。
7. **namespace 是旧时代产物**：现代项目用 ES Modules，namespace 仅限 `.d.ts` 与旧库迁移。
8. **跨文件 namespace 运行时不可达**：`/// <reference path` 只提供类型可见性，不产生运行时引用。
9. **声明合并**：同名 `interface` / `function` / `namespace` 合并；`type alias` 不可合并；全局 interface 合并有传染风险。
10. **三斜线指令**：旧式依赖声明，现代项目用 `import` + tsconfig 替代。
11. **barrel file**：`index.ts` 聚合导出，缩短路径、隐藏结构。
12. **循环依赖**：优先重构拆分，其次延迟导入 / 接口反转。

---

## 十二、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：拆分模块 + barrel 聚合（对应 `math-utils.ts` / `string-utils.ts` / `index.ts`）

创建三个文件：

- `validator.ts`：导出 `isEmail` / `isPhone` 函数与 `Validator` 类型
- `formatter.ts`：导出 `formatDate` / `formatCurrency` 函数与 `FormatOptions` 接口
- `index.ts`：barrel，聚合 re-export 上述两模块的命名导出与类型导出

要求：

1. `index.ts` 在 `isolatedModules` 下能通过 `tsc --noEmit`。
2. 写一个 `consumer.ts`，仅从 `./index` 导入，调用全部 4 个函数并使用 2 个类型。
3. 思考：如果 `validator.ts` 同时有默认导出，barrel 如何把它重新命名导出？

### 练习 2：import type 与 isolatedModules（对应 `import-type.ts`）

定义一个 `shape.ts`，导出 `Shape` 类型（可辨识联合）、`area` 函数、`Circle` / `Square` 接口。

要求：

1. 在 `consumer.ts` 中分别用 `import type`、inline `type` 修饰符、普通 `import` 三种方式导入这些成员。
2. 故意写一行 `export { Shape } from './shape'`，观察 `isolatedModules` 下的报错，并改为正确写法。
3. 验证 `import type` 导入的名字不能出现在值位置。

### 练习 3：声明合并与命名空间（对应 `declaration-merging.ts` / `namespace-demo.ts`）

1. 定义两个同名的 `interface Config`，分别含 `host` / `port` 与 `debug` / `logLevel`，验证合并后拥有全部字段。
2. 定义两个同名的 `namespace Store`，分别导出 `get` / `set`，验证合并后两个方法都可用。
3. 用 `/// <reference path` 让 `main.ts` 引用 `store.ts` 的全局 namespace，尝试在**类型位置**使用其类型；思考为什么运行时不能直接调用其方法。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/math-utils.ts` | 命名导出、默认导出、类型导出（`MathOperation` / `MathOptions`） |
| `Code/string-utils.ts` | 另一工具模块的命名 / 默认 / 类型导出 |
| `Code/index.ts` | Barrel file，re-export math-utils 与 string-utils（含 `export type`） |
| `Code/namespace-demo.ts` | namespace 定义、嵌套、跨文件引用（`/// <reference path`） |
| `Code/declaration-merging.ts` | interface / function / namespace 声明合并 |
| `Code/import-type.ts` | `import type`、inline `type`、`isolatedModules` 下的 re-export 要求 |
| `Code/module-resolution.md` | 五种模块解析策略说明、`paths` 别名配置示例 |

运行方式（需先在 `Code/` 目录执行 `npm install`）：

```bash
cd Code
npm install
npx ts-node math-utils.ts
npx ts-node string-utils.ts
npx ts-node index.ts
npx ts-node declaration-merging.ts
npx ts-node namespace-demo.ts
npx ts-node import-type.ts
```

或使用 `package.json` 中预置的脚本：

```bash
npm run math         # 等价于 ts-node math-utils.ts
npm run string
npm run barrel
npm run merging
npm run namespace
npm run import-type
npm run type-check   # 全量类型检查（不输出文件）
```

---

> 📚 **延伸阅读**
> - TS 官方手册：[Modules](https://www.typescriptlang.org/docs/handbook/2/modules.html)
> - TS 官方手册：[Modules Reference](https://www.typescriptlang.org/docs/handbook/modules-reference.html)
> - TS 官方手册：[Namespaces](https://www.typescriptlang.org/docs/handbook/2/namespaces.html)
> - TS 官方手册：[Declaration Merging](https://www.typescriptlang.org/docs/handbook/declaration-merging.html)
> - TS 官方手册：[Type Imports and Exports](https://www.typescriptlang.org/docs/handbook/2/type-modifiers.html)
> - TS 官方手册：[Module Resolution](https://www.typescriptlang.org/docs/handbook/module-resolution.html)
> - TS 5 Release Notes：`moduleResolution: bundler` 与 `--module: preserve`
