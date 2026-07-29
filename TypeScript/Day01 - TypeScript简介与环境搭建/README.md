# Day01 - TypeScript 简介与环境搭建

> 本章节我们将认识 TypeScript 这门「带类型的 JavaScript」，理解它为何能成为大型工程与 AI 全栈后端的默认选择，并完成从安装、配置到编写第一个 TS 程序的完整闭环。

---

## 目录

- [一、本章简介](#一本章简介)
- [二、学习目标](#二学习目标)
- [三、理论知识](#三理论知识)
  - [3.1 JavaScript 的类型困境](#31-javascript-的类型困境)
  - [3.2 TypeScript 是什么](#32-typescript-是什么)
  - [3.3 TS 与 JS 的关系](#33-ts-与-js-的关系)
  - [3.4 类型系统的价值](#34-类型系统的价值)
  - [3.5 TS 生态现状](#35-ts-生态现状)
  - [3.6 在 AI 全栈中的定位](#36-在-ai-全栈中的定位)
- [四、环境搭建](#四环境搭建)
- [五、第一个 TS 程序](#五第一个-ts-程序)
- [六、tsconfig.json 速览](#六tsconfigjson-速览)
- [七、开发工作流](#七开发工作流)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、本章简介

在 AI 全栈开发中，前端、后端、模型服务、数据管线常常需要协同演进。当代码规模从「一个脚本」膨胀到「几十个模块、上百个接口」时，纯 JavaScript 的动态类型会变成最大的不确定性来源——一个字段名拼错，可能在调用方运行了三个月后才暴露。

**TypeScript**（简称 TS）通过在 JavaScript 之上叠加一层**静态类型系统**，把大量本应在运行时爆发的错误前移到编译时，让 IDE 拥有精确的智能提示，让团队协作有了「可执行的契约」。它不改变 JS 的运行语义，却能显著提升大型项目的可维护性。

本章目标是建立对 TS 的整体认知并搭好本地开发环境，为后续类型语法（Day02 起）、NestJS 后端（中期）、LangChain.js 类型安全链路（后期）打好地基。

---

## 二、学习目标

完成本节内容后，你应当能够：

1. **说清楚 TypeScript 是什么**：能用自己的话讲明白「JS 的超集」「静态类型」「编译时检查」「渐进式类型」四个概念，并解释为什么 TS 不是一门全新的语言。
2. **理解 TS 与 JS 的关系**：知道 `tsc` 编译器做什么、什么是类型擦除（type erasure），理解「TS 是开发期工具，运行时仍是 JS」。
3. **列举类型系统的实际价值**：从编译期错误、IDE 提示、代码自文档化、重构安全、团队协作五个维度说明类型带来的收益。
4. **独立搭建 TS 开发环境**：完成全局/本地安装、`tsconfig.json` 生成、VS Code 配置，并能用 `tsc --version` 验证。
5. **编写并运行第一个 TS 程序**：掌握 `tsc hello.ts` 编译 + `node hello.js` 运行、`ts-node` 直接运行、`tsx` 现代运行器三种方式。
6. **看懂基础 tsconfig.json**：理解 `target` / `module` / `strict` / `outDir` / `rootDir` / `lib` 等关键配置项的语义，知道 `strict: true` 为什么重要。

---

## 三、理论知识

### 3.1 JavaScript 的类型困境

JavaScript 是一门**动态弱类型**语言，这给它带来了灵活性，也带来了四个在大型工程中反复发作的痛点。

**痛点一：动态类型的代价**

```js
// 一个函数签名什么都接受，运行时才暴露问题
function processUser(user) {
  return user.profile.age + 1;
}

processUser(null);             // TypeError: Cannot read properties of null
processUser({ profile: {} });  // NaN，悄悄传播
processUser({ profile: { age: '20' } }); // '201'，字符串拼接
```

调用方完全不知道 `user` 应该长什么样，必须靠阅读函数体或文档才能推断，文档一旦过期就成了误导。

**痛点二：运行时才发现错误**

JS 没有编译阶段（V8 的 JIT 是即时编译，不做类型检查），所有类型错误只能在代码**真正执行到那一行**时才暴露。一个 `if` 分支里的错误，可能要等线上某次异常请求才会触发，CI/CD 完全无法拦截。

**痛点三：重构困难**

想把 `user.name` 改成 `user.fullName`，在 JS 项目里只能全局文本搜索 `name`——但 `name` 可能出现在无数无关上下文里（变量名、表单字段、HTML 属性）。改完一处，不敢确定有没有遗漏，只能靠人工测试与祈祷。

**痛点四：IDE 提示弱**

在纯 JS 项目中，IDE 对 `obj.xxx` 的补全只能依赖运行时推断或 JSDoc 注释，且无法保证准确。一个 `getUser()` 返回的对象，输入 `.` 后 IDE 可能什么也提示不出来，只能 `console.log` 看一眼。

### 3.2 TypeScript 是什么

TypeScript 是微软在 2012 年开源的编程语言，官方定义只有一句话：

> TypeScript is JavaScript with syntax for types.
> TypeScript 就是「带类型语法的 JavaScript」。

它的四个核心特征：

- **JS 的超集**：任何合法的 JS 代码都是合法的 TS 代码（`.js` 直接重命名为 `.ts` 通常即可编译）。这意味着迁移成本极低，可以「一个文件一个文件」地引入。
- **静态类型**：类型信息在**写代码时**就标注好，由编译器在**编译时**检查，而不是等到运行时。
- **编译时检查**：`tsc` 编译器会扫描类型错误，绝大多数低级错误（拼写、参数缺失、类型不匹配）在构建阶段就被拦截。
- **渐进式类型系统**：你可以从「完全无类型」开始，逐步给关键函数、接口、模型补类型，未标注的部分会被推断为 `any` 并放过。这让 TS 既能服务从零开始的新项目，也能接纳历史 JS 遗产。

一句话总结：**TS 把 JS 当作运行目标，额外提供了一套开发期可见、运行时消失的类型约束**。

### 3.3 TS 与 JS 的关系

理解 TS 与 JS 关系的关键是「编译」与「类型擦除」两个概念。

```
   hello.ts  ──[ tsc 编译器 ]──>  hello.js  ──[ node 运行时 ]──>  输出
   （带类型）        │            （纯 JS）
                    │
                    └──> 类型错误在此暴露（编译失败则不产出 .js）
```

**tsc 编译器**

`tsc`（TypeScript Compiler）做两件事：

1. **类型检查**：根据类型标注与推断，检查代码是否违反类型规则。违反则报错，可中断编译。
2. **类型擦除 + 转译**：把 `.ts` 中的类型注解**全部去掉**，并根据 `tsconfig.json` 的 `target` 把新版语法（如 `enum`、装饰器）转译为目标 JS 版本。

**类型擦除（type erasure）**

类型只存在于**开发期与编译期**，运行时的 JS 引擎看不到任何类型信息：

```ts
// TypeScript 源码
interface User { name: string; age: number; }
const u: User = { name: 'Alice', age: 30 };
```

编译后：

```js
// 生成的 JavaScript
const u = { name: 'Alice', age: 30 };
```

`interface User` 与 `: User` 注解**完全消失**。这意味着：

- TS 不会带来任何运行时性能开销（不像某些语言需要类型标记）。
- TS 也无法在运行时根据 interface 做判断——`typeof u === 'User'` 是不可能的。需要运行时校验请用 `zod`、`class-validator` 等库（后续章节会讲）。

### 3.4 类型系统的价值

类型系统不是「为了写更多代码」，而是「为了少写 bug、少看文档、少返工」。具体收益可从五个维度衡量。

**1. 编译时拦截错误**

拼写错误、参数缺失、字段不存在、null 解引用、类型不兼容——这些过去要靠运行时炸出来的错误，现在 `tsc` 一过就拦截。CI 上的 `tsc --noEmit` 是一道零成本的防线。

**2. IDE 智能提示**

类型是 IDE 的「地图」。有了类型，输入 `user.` 时 IDE 能精确列出所有可用字段并标注类型；调用函数时能显示参数名与可选性；重命名时能精确替换引用而非文本。VS Code 对 TS 的支持是一等公民，开箱即用。

**3. 代码自文档化**

一个带类型的函数签名本身就是文档：

```ts
function chunk(text: string, size: number): string[] { ... }
```

无需注释，读者立刻知道：入参是字符串和数字，返回字符串数组。当接口用 `interface` 定义后，整个数据结构也是自描述的。

**4. 团队协作契约**

多人协作时，模块边界的类型签名就是「可执行的契约」。后端改了返回结构，前端调用处立即红线报错，不需要靠口头同步或文档维护。这一价值在 AI 全栈项目中尤其关键——模型返回结构、向量库字段、Prompt 模板都需要稳定的契约。

**5. 重构安全**

类型系统让「全局重命名」「修改字段类型」「提取函数」等重构操作变得可验证。改完一处后 `tsc` 会列出所有受影响的位置，逐个修复后编译通过即可基本保证正确性，远比 JS 项目的「祈祷式重构」可靠。

### 3.5 TS 生态现状

TS 已是前端与 Node.js 后端的事实标准，主流框架对其都有**一等公民**级别的支持。

| 框架 / 生态 | TS 支持情况 |
| --- | --- |
| **React** | 官方提供 `@types/react`、`@types/react-dom`，CRA / Vite / Next.js 默认 TS 模板 |
| **Vue 3** | 源码本身用 TS 重写，Composition API 完整类型推导，`<script setup lang="ts">` 是推荐写法 |
| **Angular** | 自诞生起就基于 TS，DI、装饰器、RxJS 全部强类型 |
| **NestJS** | Node 后端框架，原生 TS，整个生态（ORM、微服务、GraphQL）围绕类型设计 |
| **Express / Koa** | 通过 `@types/express`、`@types/koa` 获得类型，可逐步迁移 |
| **LangChain.js / LlamaIndex.TS** | LLM 应用框架，全部 API 用 TS 定义，Chain 与 Tool 输入输出强约束 |
| **Prisma / Drizzle / TypeORM** | 现代 ORM，从 schema 自动生成精确类型，查询结果类型安全 |

**DefinitelyTyped**

历史上 JS 库本身不带类型，社区维护了一个名为 [DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped) 的仓库，统一以 `@types/xxx` 包的形式发布到 npm。例如 `@types/express`、`@types/node`、`@types/lodash`。如今主流库已自带类型（如 Vue、NestJS、Prisma），只有老牌 JS 库仍依赖 `@types`。

### 3.6 在 AI 全栈中的定位

在 AI 全栈架构中，TS 不只是「写后端用的语言」，而是连接前后端与模型层的**类型骨架**。

**1. NestJS 后端**

NestJS 是 Node 生态中架构最完整的后端框架，原生 TS，模块化、依赖注入、装饰器风格类似 Spring Boot。在 AI 应用中，NestJS 常用于搭建 BFF / API Gateway：鉴权、限流、Prompt 模板管理、对接向量库、转发模型流式响应。整个链路的 DTO、Entity、Service 全部类型安全。

**2. LangChain.js 类型安全**

LangChain.js 把 LLM 调用抽象为 Chain / Tool / Memory / Retriever 等组件，每个组件都有明确的输入输出类型。例如自定义 Tool 时：

```ts
const weatherTool = new DynamicStructuredTool({
  name: 'get_weather',
  description: '查询某城市天气',
  schema: z.object({ city: z.string() }),  // 输入 schema 即类型
  func: async ({ city }) => { /* ... */ return { city, temp: 25 }; },
});
```

LLM 给出的工具调用参数会被严格按 `schema` 校验，错误参数在调用前就被拦截，避免模型幻觉导致下游崩溃。

**3. 向量数据结构约束**

RAG 系统中，文档切片（chunk）、向量（embedding）、元数据（metadata）都有固定结构。用 TS 定义后，存入向量库前可确保字段齐全、维度匹配：

```ts
interface DocumentChunk {
  id: string;
  content: string;
  embedding: number[];   // 维度由模型固定，如 1536
  metadata: {
    source: string;
    page: number;
    createdAt: Date;
  };
}
```

这种约束让数据管线在编译期就排除「字段写错」「维度不一致」等常见 bug。

简言之：**Python 负责「训模型」，TypeScript 负责「用模型」并打通前后端的全链路类型**。

---

## 四、环境搭建

以下步骤适用于 Windows / macOS / Linux，命令在 PowerShell、bash、zsh 中通用。

### 4.1 前置条件

确保已安装 Node.js 18+ 与 npm 9+（参考 NodeJS Day01）。验证：

```bash
node -v   # v18.x 或更高
npm -v    # 9.x 或更高
```

### 4.2 安装 TypeScript

TypeScript 有两种安装方式。

**方式一：全局安装（便于命令行直接用 `tsc`）**

```bash
npm install -g typescript
```

验证：

```bash
tsc --version
# Version 5.x.x
```

适合学习阶段随手编译单文件。生产项目不推荐全局安装，因为不同项目可能需要不同 TS 版本。

**方式二：项目本地安装（推荐）**

在项目目录中：

```bash
npm init -y
npm install -D typescript
```

安装后通过 `npx tsc --version` 调用本地版本。这样 `package.json` 锁定了 TS 版本，团队成员环境一致。

> 本章 `Code/package.json` 已包含 `typescript`、`ts-node`、`@types/node` 三项 devDependencies，进入 `Code/` 目录执行 `npm install` 即可。

### 4.3 VS Code 插件

VS Code 自带 TS 语言服务（内置 `tsserver`），无需额外装插件即可获得语法高亮、补全、错误提示。推荐补充：

- **TypeScript Vue Plugin (Volar)**：Vue 3 + TS 项目必装。
- **ESLint**：配合 `@typescript-eslint` 做风格检查（后续章节细讲）。
- **Prettier**：代码格式化，与 TS 完美兼容。

若要切换 VS Code 使用的 TS 版本：`Ctrl+Shift+P` → `TypeScript: Select TypeScript Version` → 选择「Use Workspace Version」即可用项目本地的 TS。

### 4.4 生成 tsconfig.json

在项目根目录执行：

```bash
tsc --init
```

会生成一份带详细注释的 `tsconfig.json`，包含所有可配置项。本章 `Code/` 目录已提供一份精简版可直接使用，关键配置在 [第六节](#六tsconfigjson-速览) 详解。

---

## 五、第一个 TS 程序

下面这个程序位于 `Code/hello.ts`，演示了类型注解、接口、函数三种最基础的 TS 语法。

```ts
// 定义一个接口：描述 User 对象的形状
interface User {
  id: number;
  name: string;
  age: number;
  email?: string;   // 可选属性
}

// 带类型注解的函数：参数与返回值都标注
function formatUser(user: User): string {
  return `[${user.id}] ${user.name}, ${user.age} 岁`;
}

const alice: User = { id: 1, name: 'Alice', age: 28 };
console.log(formatUser(alice));
```

### 5.1 编译并运行（最基础方式）

```bash
# 1. 编译：TS -> JS
tsc hello.ts
# 产出 hello.js（与源文件同目录）

# 2. 运行
node hello.js
```

`hello.js` 是去掉所有类型注解后的纯 JS，可直接由 Node 执行。这种方式最直观，能让你看清「TS 编译为 JS」这一事实。

### 5.2 使用 ts-node 直接运行

每次改完都要先 `tsc` 再 `node` 太繁琐。`ts-node` 在内存中完成编译并立即运行，无需产出 `.js` 文件：

```bash
# 安装（已在 Code/package.json 中作为 devDependency）
npm install -D ts-node

# 直接运行 .ts
npx ts-node hello.ts
```

适合开发调试与脚本类任务。注意 `ts-node` 启动稍慢（需即时编译），不适合生产环境。

### 5.3 使用 tsx 现代运行器

`tsx` 是基于 esbuild 的更快的 TS 运行器，启动速度比 `ts-node` 快一个数量级，且支持 ESM 与 watch 模式：

```bash
npm install -D tsx

npx tsx hello.ts
```

新项目推荐优先使用 `tsx`。`ts-node` 生态成熟仍可用，但 `tsx` 已成为社区新主流。

---

## 六、tsconfig.json 速览

`tsconfig.json` 是 TS 项目的「编译指南」，告诉 `tsc`：编译哪些文件、编译成什么版本、开启哪些严格检查。本章 `Code/tsconfig.json` 的核心配置：

```json
{
  "compilerOptions": {
    "target": "ES2022",       // 编译目标 JS 版本
    "module": "commonjs",     // 模块系统：commonjs / esnext / nodenext
    "strict": true,           // 开启所有严格类型检查
    "outDir": "./dist",       // 编译产物输出目录
    "rootDir": ".",           // 源码根目录
    "lib": ["ES2022"],        // 可用的内置类型库
    "esModuleInterop": true,  // 兼容 CommonJS 与 ESM 互导
    "skipLibCheck": true,     // 跳过 .d.ts 检查，加快编译
    "forceConsistentCasingInFileNames": true
  },
  "include": ["*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

逐项说明：

| 配置项 | 作用 |
| --- | --- |
| `target` | 编译产物的 JS 版本。`ES2022` 支持顶层 await、`#private`、`Object.hasOwn` 等现代特性。Node 18+ 推荐至少 `ES2022`。 |
| `module` | 模块系统。Node 项目常用 `commonjs`；若 `package.json` 设了 `"type": "module"` 则用 `nodenext` 或 `esnext`。 |
| `strict` | **开启所有严格检查的总开关**。等价于同时开启 `noImplicitAny`、`strictNullChecks`、`strictFunctionTypes`、`strictBindCallApply`、`strictPropertyInitialization`、`noImplicitThis`、`alwaysStrict`、`useUnknownInCatchVariables`。新项目务必打开。 |
| `outDir` | 编译产物输出目录。源码与产物分离，便于 `.gitignore` 排除 `dist/`。 |
| `rootDir` | 源码根目录，决定 `outDir` 内的目录结构。 |
| `lib` | 告诉 TS 编译器「运行环境里有哪些内置 API」。`["ES2022"]` 表示可用 `Promise.allSettled`、`Array.at` 等；Node 项目还需 `["ES2022"]` 配合 `@types/node` 提供 `process`、`fs` 等全局类型。 |
| `esModuleInterop` | 让 `import express from 'express'`（默认导出）能正确工作于 CommonJS 模块，避免 `require` 风格写法。 |
| `skipLibCheck` | 跳过 `.d.ts` 文件的类型检查，加快大项目编译速度。 |
| `forceConsistentCasingInFileNames` | 强制文件名大小写一致，避免在 macOS（默认不区分大小写）开发、在 Linux（区分大小写）部署时翻车。 |

### strict 模式为什么重要

`strict: true` 是 TS 项目质量的「地基」。关闭它，TS 退化为「带类型标注的 JS」，大量错误会以 `any` 形式溜过去。开启后：

- `noImplicitAny`：禁止隐式 `any`，函数参数必须显式标注或可推断。
- `strictNullChecks`：`null` 与 `undefined` 不再能赋给任意类型，必须显式处理。这是消除 `Cannot read properties of null` 类错误的最关键开关。
- `strictPropertyInitialization`：类的属性必须在构造函数中初始化，否则报错。
- `useUnknownInCatchVariables`：`catch (e)` 中 `e` 默认是 `unknown` 而非 `any`，强制你做类型收窄后再使用。

**关于 Day12 的铺垫**：本系列 Day12 会专门深入 `strict` 模式下每一项的语义、典型报错与修复模式。本章只需知道「新项目一律开 `strict: true`」即可。

---

## 七、开发工作流

日常 TS 开发有四种主流工作流，按场景选用。

### 7.1 tsc --watch（监听模式）

```bash
tsc --watch
# 或简写
tsc -w
```

`tsc` 监听所有源文件变化，每次保存自动重新编译到 `outDir`。适合需要看编译产物的场景（如调试编译结果、CI 模拟）。配合另一个终端 `node dist/hello.js` 或 `nodemon dist/hello.js` 运行。

### 7.2 ts-node 直接运行

```bash
npx ts-node hello.ts
```

无需产出 `.js`，开发调试最直接。改完代码需重新执行命令。可通过 `--watch`（需装 `ts-node-dev`）实现热重载：

```bash
npm install -D ts-node-dev
npx ts-node-dev --respawn hello.ts
```

### 7.3 tsx 运行与 watch

```bash
# 直接运行
npx tsx hello.ts

# 监听模式（文件变化自动重跑）
npx tsx watch hello.ts
```

`tsx watch` 是当前最推荐的 TS 脚本开发方式：启动快、原生 watch、支持 ESM。

### 7.4 配合 nodemon

若项目用 `nodemon` 统一管理进程重启，可以让 `nodemon` 监听 `.ts` 文件并调用 `ts-node` 或 `tsx`：

```json
{
  "scripts": {
    "dev": "nodemon --exec tsx src/index.ts",
    "dev:ts-node": "nodemon --exec ts-node src/index.ts"
  }
}
```

`nodemon` 提供更精细的监听配置（`ignore`、`delay`、`verbose`），适合中大型项目。

### 工作流选型建议

| 场景 | 推荐 |
| --- | --- |
| 学习单文件、看编译产物 | `tsc hello.ts && node hello.js` |
| 日常脚本开发 | `tsx watch hello.ts` |
| 中型项目开发 | `nodemon --exec tsx src/index.ts` |
| CI / 生产构建 | `tsc --noEmit`（类型检查）+ `tsc`（产出） |
| 调试编译输出 | `tsc --watch` + `node dist/xxx.js` |

---

## 八、关键知识点总结

- **TS = JS + 类型语法**：JS 的超集，所有合法 JS 都是合法 TS；类型在编译期被擦除，运行时仍是纯 JS。
- **tsc 做两件事**：类型检查 + 转译（类型擦除 + target 降级）。
- **类型擦除**：`interface`、类型注解、泛型在生成的 JS 中**完全消失**，运行时无法依赖它们做判断。
- **类型系统的五大价值**：编译期错误、IDE 提示、自文档化、团队契约、重构安全。
- **渐进式类型**：可以从无类型 JS 逐步迁移，未标注的部分退化为 `any`。
- **生态事实标准**：React / Vue3 / Angular / NestJS / LangChain.js / Prisma 全部原生 TS。
- **环境搭建**：`npm install -D typescript`（项目本地，推荐）或 `npm install -g typescript`（学习用）；`tsc --init` 生成 `tsconfig.json`。
- **三种运行方式**：`tsc + node`（看产物）、`ts-node`（开发调试）、`tsx`（现代运行器，最快）。
- **tsconfig 三件套**：`target`（编译目标）、`module`（模块系统）、`strict`（严格总开关）。
- **strict 必开**：新项目一律 `strict: true`，是类型安全的最低门槛；Day12 会逐项详解。
- **AI 全栈中的角色**：NestJS 后端骨架、LangChain.js 类型约束、向量数据结构契约，是打通前后端与模型层的类型骨架。

---

## 九、实战练习

以下三个练习相互独立，建议按顺序完成。所有代码位于 `Code/` 目录，环境就绪后即可运行。

### 练习一：hello.ts —— 第一个 TS 程序

**任务描述**

打开 `Code/hello.ts`，阅读已有代码（接口、函数、类型注解）。然后在该文件末尾追加：

1. 定义一个 `Book` 接口，字段：`title: string`、`price: number`、`tags?: string[]`（可选）。
2. 写一个函数 `summarize(book: Book): string`，返回形如 `《<title>》 - ￥<price> [标签1, 标签2]` 的字符串；若无 tags 则输出 `[无标签]`。
3. 创建一本测试书并调用 `summarize`，结果用 `console.log` 打印。

**验证**

```bash
cd Code
npx tsx hello.ts
```

预期输出包含 `《Deep Learning》 - ￥99 [AI, 入门]` 之类的字符串。

### 练习二：types-vs-js.ts —— 体会类型带来的错误前移

**任务描述**

打开 `Code/types-vs-js.ts`，文件中已用注释形式列出若干「故意写错的类型错误」。请：

1. 逐行取消注释，观察 VS Code 红线与 `tsc --noEmit` 报错信息，理解每个错误的原因。
2. 在文件末尾**新增**一个正确版本：定义一个 `Vector3` 接口（`x`、`y`、`z` 均为 `number`），写一个 `length(v: Vector3): number` 函数计算向量长度，并调用一次打印结果。
3. 调用 `length` 时故意少传一个参数，观察 TS 报什么错，再修正。

**验证**

```bash
cd Code
npx tsc --noEmit types-vs-js.ts   # 应当无错误
npx tsx types-vs-js.ts             # 应当打印向量长度
```

### 练习三：tsconfig 实验 —— 体会 strict 模式

**任务描述**

1. 在 `Code/` 目录新建 `strict-test.ts`，写一个**没有类型注解**的函数：

   ```ts
   function greet(name) {
     return 'Hello, ' + name.toUpperCase();
   }
   greet(123);   // 故意传错类型
   ```

2. 先保持 `tsconfig.json` 中 `strict: true`，运行 `npx tsc --noEmit`，记录报错信息。
3. 把 `strict` 改为 `false`，再次运行 `npx tsc --noEmit`，对比报错数量与严重程度。
4. 实验结束后**恢复** `strict: true`，删除 `strict-test.ts`（避免污染示例）。

**思考题**

- `strict: false` 时 `name` 被推断为什么类型？为什么传 `123` 不报错？
- 这对运行时行为有什么影响？

**验证**

```bash
cd Code
npx tsc --noEmit strict-test.ts
```

---

## 下节预告

下一节 **Day02** 将进入 **TypeScript 基础类型与类型注解**：原始类型、数组、元组、`any` / `unknown` / `never` / `void` 的区别、字面量类型与联合类型、类型别名 `type` 与接口 `interface` 的取舍，并在 `strict` 模式下编写第一组类型安全的工具函数。
