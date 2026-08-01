# Day11 - 类型声明与d.ts

> `.d.ts` 声明文件是 JS 生态与 TS 类型系统之间的桥梁。海量 npm 包仍以纯 JS 编写、不带任何类型信息，直接在 TS 项目中 `import` 会触发 `TS7016` 报错。声明文件的出现让这些「无类型」的 JS 库获得完整的类型支持——它只描述「值的样子」而不含任何运行时实现，编译期被完全擦除，零运行时开销。本篇系统讲解 `.d.ts` 的本质、三种类型来源（库自带 / `@types` 组织 / 手写）、`declare` 关键字家族、模块扩增（Module Augmentation）扩展 Express.Request 等经典场景，以及全局变量与 `process.env` 的类型补全，打通 TS 与 JS 生态共存的最后一公里。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、.d.ts 声明文件的本质](#二dts-声明文件的本质)
- [三、类型声明的三种来源](#三类型声明的三种来源)
  - [3.1 库自带类型](#31-库自带类型)
  - [3.2 @types 组织（DefinitelyTyped）](#32-types-组织definitelytyped)
  - [3.3 自己编写](#33-自己编写)
- [四、@types 安装机制](#四types-安装机制)
  - [4.1 自动加载](#41-自动加载)
  - [4.2 typeRoots 配置](#42-typeroots-配置)
  - [4.3 types 白名单](#43-types-白名单)
  - [4.4 声明优先级](#44-声明优先级)
- [五、全局声明 vs 模块声明](#五全局声明-vs-模块声明)
- [六、declare 关键字详解](#六declare-关键字详解)
  - [6.1 declare var / let / const](#61-declare-var--let--const)
  - [6.2 declare function](#62-declare-function)
  - [6.3 declare class](#63-declare-class)
  - [6.4 declare namespace](#64-declare-namespace)
  - [6.5 declare module](#65-declare-module)
- [七、模块扩增 Module Augmentation](#七模块扩增-module-augmentation)
- [八、声明合并的实际应用](#八声明合并的实际应用)
- [九、全局变量的类型声明](#九全局变量的类型声明)
- [十、三斜线指令在 .d.ts 中的使用](#十三斜线指令在-dts-中的使用)
- [十一、编写声明文件实战](#十一编写声明文件实战)
- [十二、常见问题](#十二常见问题)
- [十三、关键知识点总结](#十三关键知识点总结)
- [十四、实战练习](#十四实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 解释 `.d.ts` 声明文件的本质：只含类型不含实现、类型擦除后不生成 JS、为 JS 代码补充类型。
2. 区分类型声明的三种来源：库自带（`package.json` 的 `types` / `typings` 字段）、`@types` 组织（DefinitelyTyped）、自己编写。
3. 描述 `@types` 的安装与自动加载机制：`node_modules/@types/` 自动扫描、`typeRoots` 与 `types` 配置的作用。
4. 区分「全局声明」与「模块声明」：无 `import/export` 的 `.d.ts` 是全局脚本，有 `import/export` 或 `declare module` 的是模块声明。
5. 熟练使用 `declare` 关键字家族：`declare var/let/const`、`declare function`、`declare class`、`declare namespace`、`declare module`。
6. 用 `declare module` 扩展第三方模块（模块扩增），为已有库追加类型——如扩展 Express 的 `Request.user`。
7. 掌握声明合并的实际应用：扩展 `Express.Request`、扩展 `express-session.Session`、扩展 Vue 自定义组件。
8. 为全局变量写类型声明：`window` 自定义属性、`process.env` 自定义变量、全局自定义函数。
9. 理解三斜线指令在 `.d.ts` 中的作用，并知道现代项目何时该用 `tsconfig` 替代（呼应 Day10）。
10. 独立为无类型的 JS 模块、全局变量、`.env` 环境变量编写 `.d.ts` 声明文件。

---

## 二、.d.ts 声明文件的本质

`.d.ts` 文件是 TypeScript 的**声明文件**（Declaration File），它与 `.ts` 文件的根本区别在于：

| 维度 | `.ts` 文件 | `.d.ts` 文件 |
|------|-----------|-------------|
| 内容 | 类型 + 实现 | **只有类型，没有实现** |
| 编译产物 | 生成 `.js` | **不生成任何 JS**（类型擦除后为空） |
| 用途 | 业务代码 / 库源码 | 为 JS 代码补充类型描述 |
| `function foo() { ... }` | ✅ 有函数体 | ❌ 只能有 `declare function foo(): ...`（无函数体） |
| `const x = 1` | ✅ 值初始化 | ❌ 只能有 `declare const x: number` |

**核心特征：只描述「值的样子」，不提供「值本身」。**

```ts
// ✅ .d.ts 文件中的合法写法：只有签名，没有实现
declare function add(a: number, b: number): number;
declare const APP_VERSION: string;

// ❌ .d.ts 文件中的非法写法：包含实现
// function add(a: number, b: number) { return a + b; }   // Error: Implementation not allowed
// const APP_VERSION = '1.0.0';                            // Error: Initializer not allowed
```

由于 `.d.ts` 只含类型信息，编译后**不产生任何 JS 输出**，运行时零开销。这使得它成为「为 JS 库补充类型」的完美载体——既不改变库的运行时行为，又让 TS 项目获得完整的类型检查与智能提示。

---

## 三、类型声明的三种来源

当你在 TS 项目中 `import` 一个第三方库时，TS 会按以下三种来源依次查找类型：

### 3.1 库自带类型

现代库（尤其是用 TS 编写的库）直接在发布包内携带 `.d.ts` 文件，通过 `package.json` 的 `types` 或 `typings` 字段声明入口：

```jsonc
// node_modules/axios/package.json
{
  "main": "index.js",
  "types": "index.d.ts"      // ← TS 自动识别此字段
}
```

`types` 与 `typings` 是同义词，前者是新名后者是旧名。一旦库自带类型，TS 直接使用，**即使安装了 `@types/xxx` 也会被忽略**。

典型代表：`axios`、`vue`、`zod`、`dayjs`、`rxjs`。

### 3.2 @types 组织（DefinitelyTyped）

对于纯 JS 编写且未自带类型的库，社区在 [DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped) 仓库维护类型补丁，以 `@types/xxx` 的包名发布到 npm：

```bash
# lodash 本身是纯 JS，不带类型；安装 @types/lodash 补充类型
npm install --save-dev @types/lodash

# Express 是纯 JS，需要 @types/express
npm install --save-dev @types/express

# Node.js 内置 API（process、Buffer、__dirname 等）也需要 @types/node
npm install --save-dev @types/node
```

典型代表：`@types/lodash`、`@types/express`、`@types/node`、`@types/react`。

### 3.3 自己编写

当 `@types/xxx` 不存在，或类型不满足项目需求时，在项目内自建 `.d.ts`：

```ts
// types/legacy-lib.d.ts
declare module 'legacy-lib' {
  export function doSomething(input: string): number;
  export const VERSION: string;
}
```

这是兜底方案，适用于内部 JS 工具、无类型的旧库、或需要扩展已有类型的情况。

---

## 四、@types 安装机制

### 4.1 自动加载

TS 编译器**默认扫描** `node_modules/@types/` 目录下的所有子目录，把它们作为类型声明自动纳入程序。安装 `@types/xxx` 后**无需任何 `import` 或 `/// <reference`**，对应库立即获得类型：

```bash
npm install --save-dev @types/lodash
# 安装后，import _ from 'lodash' 立即有完整类型，无需额外配置
```

### 4.2 typeRoots 配置

`typeRoots` 控制 TS 从哪些目录自动加载 `@types` 包：

```jsonc
{
  "compilerOptions": {
    // 默认值：["./node_modules/@types"]
    // 显式配置后会「替换」默认值，而非追加
    "typeRoots": [
      "./node_modules/@types",
      "./src/types"
    ]
  }
}
```

> ⚠️ 配置 `typeRoots` 会**替换**默认的 `./node_modules/@types`。若要保留默认行为，必须显式写出 `"./node_modules/@types"`。

### 4.3 types 白名单

默认加载 `@types/` 下的**所有**包。用 `types` 字段可白名单限制：

```jsonc
{
  "compilerOptions": {
    "types": ["node", "lodash", "express"]
  }
}
```

| 配置方式 | 行为 |
|----------|------|
| 不配置 `types` | 加载 `@types/` 下的全部包（默认） |
| `"types": []` | 不自动加载任何 `@types` 包（极简模式） |
| `"types": ["node"]` | 只加载 `@types/node`，其余忽略 |

> 💡 **实践建议**：中小型项目不配置 `types`，让所有已安装的 `@types` 自动生效；大型项目可用 `types` 白名单减少全局类型污染、加速编译。

### 4.4 声明优先级

当多个来源同时存在时：

```
库自带类型（package.json types 字段）  >  @types/xxx  >  项目内自定义 .d.ts
```

- 库自带类型优先级最高，`@types/xxx` 即使安装了也会被忽略。
- `@types/xxx` 仅对「不带类型」的库生效。
- 项目内 `declare module 'xxx'` 是最后的兜底方案。

---

## 五、全局声明 vs 模块声明

`.d.ts` 文件同样遵循 Day10 讲过的「脚本 vs 模块」规则：

| 文件特征 | 角色 | 声明作用域 |
|----------|------|-----------|
| 无顶层 `import` / `export` / `declare module` | **全局脚本** | 全局，任何文件可用 |
| 有顶层 `import` / `export` / `declare module` | **模块** | 需 `import` 才可用 |

### 全局声明（脚本文件）

```ts
// global-declare.d.ts —— 无 import/export，是全局脚本
// 以下声明全局生效，任何 .ts 文件无需 import 即可使用

declare const APP_VERSION: string;           // 全局常量
declare function gtag(...): void;             // 全局函数
interface Window { __APP_NAME__: string; }    // 扩展 Window（声明合并）
```

### 模块声明（模块文件）

```ts
// module-declare.d.ts —— 含 declare module，是模块声明
declare module 'fictional-utils' {
  export function formatNumber(value: number): string;
  export const VERSION: string;
}

// 使用方需 import 才能获得类型
// import { formatNumber } from 'fictional-utils';
```

> ⚠️ **关键区别**：`declare module 'xxx'` 内的 `export` 只在 `import 'xxx'` 时可见；全局脚本中的 `declare` 则全局可见，无需 import。

---

## 六、declare 关键字详解

`declare` 是 `.d.ts` 文件的核心关键字，告诉 TS「这个值已存在于运行时，只需描述它的类型」。

### 6.1 declare var / let / const

声明已存在的全局变量。三者区别与 JS 一致：`const` 不可重新赋值，`var` / `let` 可重新赋值。

```ts
declare const APP_VERSION: string;      // 全局常量（构建工具注入）
declare var __DEV__: boolean;           // 全局变量（可重新赋值）
declare let __APP_CONFIG__: {           // 全局变量（块级作用域语义）
  apiBase: string;
  timeout: number;
};
```

### 6.2 declare function

声明已存在的全局函数，只写签名不写函数体。

```ts
// Google Analytics 的 gtag 函数（由 <script> 注入全局）
declare function gtag(
  command: 'config' | 'event' | 'set' | 'consent',
  targetIdOrEventName: string,
  params?: Record<string, unknown>
): void;

// 使用：gtag('config', 'GA-XXXX', { page_title: 'home' });
```

### 6.3 declare class

声明已存在的全局构造函数（类），描述其构造签名、实例方法与静态方法。

```ts
declare class LegacyModal {
  constructor(options: { title?: string; content: string });
  open(): void;
  close(): void;
  static create(options: { content: string }): LegacyModal;
}

// 使用：const modal = new LegacyModal({ content: 'hello' });
```

### 6.4 declare namespace

声明已存在的全局命名空间对象，适合组织一组相关的全局成员。

```ts
declare namespace AppConfig {
  const version: string;
  const env: 'development' | 'production';

  interface FeatureFlags {
    newDashboard: boolean;
    darkMode: boolean;
  }

  function getFeatureFlags(): FeatureFlags;
}

// 使用：AppConfig.version / AppConfig.getFeatureFlags()
```

### 6.5 declare module

声明一个模块的类型。这是 `.d.ts` 中最灵活、也最常用的形式：

```ts
// 为无类型的 JS 库补充类型
declare module 'fictional-utils' {
  export function formatNumber(value: number): string;
  export const VERSION: string;
}

// 通配符声明：让 TS 认识非 JS 资源
declare module '*.css' {
  const classes: Record<string, string>;
  export default classes;
}

declare module '*.svg' {
  const src: string;
  export default src;
}
```

`declare module` 的另一个重要用途是**模块扩增**——扩展已有模块的类型，详见第七节。

---

## 七、模块扩增 Module Augmentation

模块扩增是 `.d.ts` 最强大的能力之一：通过再次 `declare module 'xxx'` 并声明同名 interface，给已有库**追加**类型成员，而不修改库的源码。

### 核心原理

```ts
// 假设 express-serve-static-core 已有 Request 接口（来自 @types/express）
declare module 'express-serve-static-core' {
  interface Request {
    user?: AuthUser;    // ← 追加 user 字段，触发声明合并
  }
}
```

两次 `declare module 'express-serve-static-core'` 中的 `interface Request` 会**声明合并**，最终 `Request` 同时拥有原有字段和新增的 `user` 字段。

### 关键特征

| 维度 | 说明 |
|------|------|
| 语法 | 再次 `declare module 'xxx'`，内部声明同名 interface |
| 合并规则 | interface 成员取并集（与 Day10 声明合并规则一致） |
| 影响范围 | 全项目所有 `import` 该模块的代码都看到扩展后的类型 |
| 是否修改原库 | ❌ 不修改，纯类型层面扩展 |

### 经典场景：扩展 Express.Request

```ts
// express-augment.d.ts
declare module 'express-serve-static-core' {
  interface AuthUser {
    id: string;
    name: string;
    roles: string[];
  }

  interface Request {
    user?: AuthUser;    // 追加 user 字段
  }
}
```

```ts
// auth.ts —— 使用扩展后的类型
import type { RequestHandler } from 'express-serve-static-core';

const authMiddleware: RequestHandler = (req, res, next) => {
  // req.user 类型为 AuthUser | undefined，类型安全！
  if (req.user) {
    console.log(req.user.name);   // ✅ 有类型提示
  }
  next();
};
```

> 💡 **为何扩增 `express-serve-static-core` 而非 `express`**：Express 的 `Request` 接口实际定义在 `express-serve-static-core` 包中，`@types/express` 只是从该包 re-export。要扩展 `Request`，需扩增其定义源头。

---

## 八、声明合并的实际应用

声明合并在工程中有三大经典场景：

### 8.1 扩展 Express.Request

最经典的 Node.js 后端场景：认证中间件把用户挂到 `req.user`。

```ts
// types/express.d.ts
declare module 'express-serve-static-core' {
  interface Request {
    user?: {
      id: string;
      name: string;
      roles: string[];
    };
  }
}
```

### 8.2 扩展 express-session Session

```ts
// types/session.d.ts
declare module 'express-session' {
  interface Session {
    userId?: string;
    captcha?: string;
    cart?: Array<{ productId: string; quantity: number }>;
  }
}

// 使用：req.session.userId = 'u-1001';   // ✅ 类型安全
```

### 8.3 扩展 Vue 自定义组件

Vue 3 + TS 项目中，用 `declare module '@vue/runtime-core'` 扩展组件选项或全局属性：

```ts
// types/vue.d.ts
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $api: {
      get(url: string): Promise<unknown>;
      post(url: string, body: unknown): Promise<unknown>;
    };
  }

  interface ComponentCustomOptions {
    requiresAuth?: boolean;
  }
}

// 使用：const { $api } = getCurrentInstance()!.appContext.config.globalProperties;
```

---

## 九、全局变量的类型声明

### 9.1 window 自定义属性

浏览器项目中，第三方 SDK 常通过 `window.xxx` 挂载全局对象。在 `.d.ts` 全局脚本中扩展 `Window` 接口：

```ts
// global-declare.d.ts —— 无 import/export，是全局脚本
interface Window {
  __APP_NAME__: string;
  __BROWSER_INFO__?: {
    name: string;
    version: string;
    isMobile: boolean;
  };
  wx?: {
    config(config: Record<string, unknown>): void;
    ready(callback: () => void): void;
  };
}
```

```ts
// 使用：window.__APP_NAME__、window.__BROWSER_INFO__ 均有类型
// 无需 import，全局生效
```

> ⚠️ 同样可以扩展 `Document`、`HTMLElement` 等内置接口。

### 9.2 process.env 自定义变量

`@types/node` 已定义 `NodeJS.ProcessEnv` 接口（索引签名 `[key: string]: string | undefined`）。通过声明合并追加项目特定变量：

```ts
// env.d.ts
declare namespace NodeJS {
  interface ProcessEnv {
    readonly NODE_ENV: 'development' | 'production' | 'test';
    readonly DATABASE_URL: string;       // 必填，类型为 string（非 undefined）
    readonly JWT_SECRET: string;
    readonly PORT?: string;              // 可选
    readonly LOG_LEVEL?: 'debug' | 'info' | 'warn' | 'error';
  }
}
```

```ts
// 使用
const dbUrl = process.env.DATABASE_URL;     // 类型：string（非 undefined）
const env = process.env.NODE_ENV;           // 类型：'development' | 'production' | 'test'
const port = process.env.PORT ?? '3000';    // 类型：string
```

### 9.3 全局自定义函数

由 `<script>` 标签或内部 SDK 挂载的全局函数：

```ts
// global-declare.d.ts
declare function gtag(
  command: 'config' | 'event' | 'set',
  targetId: string,
  params?: Record<string, unknown>
): void;

declare function track(event: string, properties?: Record<string, unknown>): void;
```

```ts
// 使用：无需 import，直接调用
gtag('config', 'GA-XXXX', { page_title: 'home' });
track('button_click', { id: 'submit' });
```

---

## 十、三斜线指令在 .d.ts 中的使用

三斜线指令（`/// <reference ... />`）是 TS 早期的依赖声明方式（详见 Day10）。在 `.d.ts` 文件中仍会遇到三种形式：

```ts
/// <reference path="./other-types.d.ts" />   // 引入指定文件
/// <reference types="node" />                 // 引入 @types/node
/// <reference lib="ES2020" />                 // 引入 ES2020 标准库
```

### 现代项目的替代方案

| 三斜线指令 | 现代替代方案 |
|-----------|-------------|
| `/// <reference path="..." />` | `import` 语句 |
| `/// <reference types="node" />` | tsconfig 的 `types: ["node"]` |
| `/// <reference lib="ES2020" />` | tsconfig 的 `lib: ["ES2020"]` |

### 何时仍需三斜线

仅在「独立分发的 `.d.ts` 文件」中可能需要——例如发布到 npm 的类型补丁包，无法依赖消费者的 tsconfig 配置。项目内的 `.d.ts` 文件通常已被 `include` 纳入，无需显式三斜线引用。

---

## 十一、编写声明文件实战

### 11.1 为无类型的 JS 模块写 .d.ts

**场景**：项目依赖一个纯 JS 编写的 `fictional-utils` 库，无自带类型，也无 `@types/fictional-utils`。

```ts
// module-declare.d.ts
declare module 'fictional-utils' {
  export interface FormatOptions {
    precision?: number;
    locale?: string;
  }

  export type ValueType = 'number' | 'string' | 'boolean';

  export function formatNumber(value: number, options?: FormatOptions): string;
  export function formatDate(date: Date, locale?: string): string;
  export function clamp(value: number, min: number, max: number): number;
  export function detectType(value: unknown): ValueType;

  export const VERSION: string;
}
```

**为本地 JS 文件写声明**：若项目内有 `utils.js`，在旁边创建 `utils.d.ts`（同名），TS 自动关联：

```ts
// utils.d.ts（与 utils.js 同目录）
export function formatNumber(value: number, options?: FormatOptions): string;
export const VERSION: string;
```

### 11.2 为全局变量与 window 属性写声明

```ts
// global-declare.d.ts —— 全局脚本（无 import/export）

// 构建工具注入的全局常量
declare const APP_VERSION: string;
declare const IS_PRODUCTION: boolean;

// 全局函数（由 <script> 注入）
declare function gtag(command: 'config' | 'event', id: string, params?: Record<string, unknown>): void;

// 扩展 window（声明合并）
interface Window {
  __APP_NAME__: string;
  __BROWSER_INFO__?: { name: string; version: string; isMobile: boolean };
}

// 全局命名空间
declare namespace AppConfig {
  const version: string;
  function refresh(): Promise<void>;
}
```

### 11.3 扩展 Express 的 Request 对象（最经典场景）

```ts
// express-augment.d.ts
declare module 'express-serve-static-core' {
  interface AuthUser {
    id: string;
    name: string;
    email: string;
    roles: string[];
    loginAt: Date;
  }

  interface Request {
    user?: AuthUser;
  }
}
```

```ts
// auth.ts —— 使用扩展后的 Request
import type { RequestHandler } from 'express-serve-static-core';

const authMiddleware: RequestHandler = (req, res, next) => {
  const token = req.headers['authorization'];
  if (!token) {
    res.status(401).json({ error: 'No token' });
    return;
  }
  req.user = { id: 'u-1', name: 'Alice', email: 'a@b.com', roles: ['admin'], loginAt: new Date() };
  next();
};
```

### 11.4 为 .env 的环境变量补充类型

```ts
// env.d.ts
declare namespace NodeJS {
  interface ProcessEnv {
    readonly NODE_ENV: 'development' | 'production' | 'test';
    readonly DATABASE_URL: string;
    readonly JWT_SECRET: string;
    readonly PORT?: string;
    readonly LOG_LEVEL?: 'debug' | 'info' | 'warn' | 'error';
  }
}

// Vite 项目的 import.meta.env 类型
interface ImportMetaEnv {
  readonly VITE_API_BASE: string;
  readonly VITE_APP_TITLE: string;
  readonly VITE_CDN_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

---

## 十二、常见问题

### Q1：TS7016 - Could not find a declaration file

```
TS7016: Could not find a declaration file for module 'xxx'.
```

**原因**：导入的库既无自带类型，也未安装 `@types/xxx`。

**解决方案**（按优先级）：

1. 安装对应的 `@types` 包：`npm install --save-dev @types/xxx`
2. 若 `@types/xxx` 不存在，自建 `declare module 'xxx'` 声明文件
3. 临时绕过：在 `.ts` 文件顶部加 `// @ts-ignore`（不推荐，治标不治本）
4. 全局绕过：tsconfig 加 `"noImplicitAny": false`（强烈不推荐，丧失类型安全）

### Q2：@types 版本与库版本如何对齐

`@types/xxx` 的版本号应与 `xxx` 库的版本号尽量一致：

```bash
# 查看库版本
npm list lodash          # lodash@4.17.21

# 安装对应版本的 @types
npm install --save-dev @types/lodash@4.14.0   # 大版本对齐
```

若 `@types` 版本与库版本差异过大，可能出现类型与实际 API 不符（如方法签名变了、新增的 API 没有类型）。此时可：

- 升级 / 降级 `@types/xxx` 到匹配版本
- 在项目内用 `declare module` 覆盖有问题的部分

### Q3：声明优先级冲突

**现象**：库自带了类型，但你想用 `@types/xxx` 的另一套类型，或想用自己的 `.d.ts` 覆盖。

**规则**：`库自带 > @types > 自定义`，高优先级总是覆盖低优先级。

**自定义覆盖已有类型**：用 `declare module` 增殖（augmentation）只能**追加**成员，不能**覆盖**已有成员。若需覆盖，需调整 tsconfig 的 `paths` 把自己的 `.d.ts` 优先于 `node_modules` 解析。

### Q4：.d.ts 文件不被 TS 识别

**排查清单**：

1. 检查 tsconfig 的 `include` 是否覆盖 `.d.ts` 文件（`*.ts` 通配符包含 `.d.ts`）。
2. 检查文件是否在 `include` / `files` 指定的目录内。
3. 检查是否有 `exclude` 把目录排除了。
4. 全局 `.d.ts`（无 import/export）的声明全局生效；模块 `.d.ts`（含 `declare module`）需 `import` 才生效。

---

## 十三、关键知识点总结

1. **`.d.ts` 本质**：只含类型不含实现，编译后不生成 JS，为 JS 代码补充类型描述，运行时零开销。
2. **三种来源**：库自带（`types` / `typings` 字段）> `@types` 组织（DefinitelyTyped）> 自己编写。
3. **`@types` 自动加载**：`node_modules/@types/` 下的所有包默认自动加载，无需 `import` 或 `reference`。
4. **`typeRoots`**：控制自动加载的根目录，配置后**替换**默认值而非追加。
5. **`types` 白名单**：限制只加载指定的 `@types` 包，减少全局污染。
6. **全局 vs 模块**：无 `import/export` 的 `.d.ts` 是全局脚本（声明全局生效）；有 `declare module` 的是模块声明（需 `import` 才可用）。
7. **`declare` 关键字家族**：`var/let/const`（变量）、`function`（函数）、`class`（类）、`namespace`（命名空间）、`module`（模块）。
8. **`declare module` 双重用途**：为无类型库补充类型（ambient module）+ 扩展已有库类型（module augmentation）。
9. **模块扩增**：再次 `declare module 'xxx'` + 同名 interface 触发声明合并，给已有库追加成员（如 Express.Request.user）。
10. **声明合并应用**：扩展 Express.Request、express-session.Session、Vue ComponentCustomProperties。
11. **window / process.env 扩展**：在全局 `.d.ts` 中用 `interface Window` / `declare namespace NodeJS { interface ProcessEnv }` 声明合并追加自定义成员。
12. **通配符声明**：`declare module '*.css'` / `'*.svg'` 让 TS 认识非 JS 资源导入。
13. **三斜线指令**：在 `.d.ts` 中声明依赖，现代项目用 tsconfig 的 `types` / `lib` 替代；仅独立分发的 `.d.ts` 仍可能需要。
14. **常见报错 TS7016**：库无类型时安装 `@types/xxx` 或自建 `declare module`。

---

## 十四、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现。

### 练习 1：为无类型 JS 库编写声明（对应 `module-declare.d.ts`）

假设有一个纯 JS 编写的 `math-lib` 库，其 API 如下：

```js
// math-lib.js
exports.add = (a, b) => a + b;
exports.subtract = (a, b) => a - b;
exports.factorial = (n) => { /* 阶乘 */ };
exports.PI = 3.14159;
exports.Operations = { ADD: 'add', SUB: 'subtract' };
```

要求：

1. 编写 `math-lib.d.ts`，为上述 API 补充完整类型。
2. `factorial` 接收非负整数，返回正整数；传入负数时抛异常（用 JSDoc 标注 `@throws`）。
3. `Operations` 应是一个常量对象，键值均为字符串字面量类型。
4. 编写消费代码，验证类型提示与检查生效。

### 练习 2：扩展 Express.Request 与 Response（对应 `express-augment.d.ts`）

1. 用 `declare module 'express-serve-static-core'` 给 `Request` 追加 `traceId: string` 字段（用于链路追踪）。
2. 给 `Response` 追加 `sendSuccess<T>(data: T, message?: string): this` 与 `sendError(code: number, message: string): this` 方法。
3. 编写一个中间件，从请求头读取 `x-trace-id` 赋值给 `req.traceId`，并在响应中调用 `res.sendSuccess`。
4. 思考：如果 `traceId` 声明为必填（非 `?`），中间件未设置时会有什么问题？

### 练习 3：为全局变量与环境变量补充类型（对应 `global-declare.d.ts` / `env.d.ts`）

1. 项目通过 `webpack DefinePlugin` 注入了 `__APP_VERSION__`（string）、`__BUILD_TIME__`（string，ISO 日期）、`__DEBUG__`（boolean）三个全局常量。编写 `.d.ts` 声明它们。
2. 扩展 `window`，添加 `window.__featureFlags__`（对象，含 `newDashboard: boolean`、`darkMode: boolean`）和 `window.__track__(event: string, data?: Record<string, unknown>): void` 方法。
3. 扩展 `NodeJS.ProcessEnv`，声明 `MONGO_URI`（必填 string）、`REDIS_URL`（可选 string）、`ENV`（`'dev' | 'staging' | 'prod'`）三个环境变量。
4. 编写消费代码，验证拼写错误会被 TS 拦截（如 `process.env.MONG_URI` 应报错）。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/global-declare.d.ts` | 全局变量（`declare const/var/let`）、window 属性（`interface Window` 声明合并）、全局函数（`declare function`）、全局命名空间（`declare namespace`）、全局类（`declare class`） |
| `Code/module-declare.d.ts` | `declare module 'fictional-utils'` 为无类型 JS 库补充类型、通配符声明（`*.css` / `*.svg` / `*.png` / `*.json`）、本地 `.d.ts` 编写说明 |
| `Code/express-augment.d.ts` | 模块扩增：扩展 Express.Request 添加 `user` 字段、扩展 Response 添加 `sendSuccess` / `sendError`、扩展 express-session Session |
| `Code/env.d.ts` | 扩展 `NodeJS.ProcessEnv`（NODE_ENV / DATABASE_URL / JWT_SECRET 等）、扩展 `ImportMetaEnv`（Vite 的 VITE_xxx 变量）、三斜线指令说明 |
| `Code/use-declare.ts` | 消费上述四个 `.d.ts` 的演示：全局变量安全访问、模块声明 `import type` 消费、Express 中间件类型安全、process.env 类型检查 |
| `Code/third-party-types.md` | `@types` 安装机制、`typeRoots` / `types` 配置、声明优先级、查看库自带类型的方法 |

运行方式（需先在 `Code/` 目录执行 `npm install`）：

```bash
cd Code
npm install
npx ts-node use-declare.ts    # 运行声明消费演示
npm run type-check            # 全量类型检查（不输出文件）
```

---

> 📚 **延伸阅读**
> - TS 官方手册：[Declaration Files](https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html)
> - TS 官方手册：[Declaration Reference](https://www.typescriptlang.org/docs/handbook/declaration-files/by-example.html)
> - TS 官方手册：[Module Augmentation](https://www.typescriptlang.org/docs/handbook/declaration-merging.html#module-augmentation)
> - TS 官方手册：[Library Structures](https://www.typescriptlang.org/docs/handbook/declaration-files/templates.html)
> - DefinitelyTyped 仓库：[github.com/DefinitelyTyped/DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped)
> - TS 配置参考：[typeRoots 与 types](https://www.typescriptlang.org/tsconfig#types)
