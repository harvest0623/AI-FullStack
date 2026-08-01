# Day12 - tsconfig 工程化配置

> `tsconfig.json` 是 TypeScript 工程化的核心，一份配置决定了「编译目标、模块系统、严格性、产物布局、路径别名、项目引用」等几乎所有工程行为。它的可配置项表面上有上百个，但官方推荐与社区实践中真正高频使用的不到 20 个——抓住这 20 个，剩下的查文档即可。本篇按「结构 → 严格性 → 别名 → 引用 → 多环境 → 构建 → 陷阱」的脉络，把 tsconfig 工程化拆成可执行的知识块，并配以 `Code/` 目录下的四份 tsconfig 示例，让你能在真实项目里立刻落地。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解 - tsconfig.json 结构](#二理论知识讲解---tsconfigjson-结构)
  - [2.1 顶层字段总览](#21-顶层字段总览)
  - [2.2 extends 继承与官方预设](#22-extends-继承与官方预设)
  - [2.3 include / exclude / glob 模式](#23-include--exclude--glob-模式)
- [三、compilerOptions 核心配置详解](#三compileroptions-核心配置详解)
  - [3.1 目标与模块](#31-目标与模块)
  - [3.2 严格性 strict 全家桶](#32-严格性-strict-全家桶)
  - [3.3 输出](#33-输出)
  - [3.4 模块解析](#34-模块解析)
  - [3.5 JSX（前端相关简述）](#35-jsx前端相关简述)
  - [3.6 实验性](#36-实验性)
  - [3.7 高级](#37-高级)
- [四、严格模式深度解读](#四严格模式深度解读)
- [五、路径别名配置实战](#五路径别名配置实战)
- [六、项目引用 Project References](#六项目引用-project-references)
- [七、多环境配置组合](#七多环境配置组合)
- [八、常用构建工具集成](#八常用构建工具集成)
- [九、常见配置陷阱](#九常见配置陷阱)
- [十、关键知识点总结](#十关键知识点总结)
- [十一、实战练习](#十一实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说出 `tsconfig.json` 的顶层字段（`compilerOptions` / `include` / `exclude` / `extends` / `files` / `references` / `watchOptions`）各自承担的职责。
2. 使用 `extends` 继承 `@tsconfig/recommended`、`@tsconfig/node18` 等官方预设，并在此基础上叠加项目专属配置。
3. 用 `include` / `exclude` / glob 模式精确控制哪些文件参与编译，并解释 `**/*`、`*`、`?` 的差异。
4. 按「目标与模块、严格性、输出、模块解析、JSX、实验性、高级」七个分组，逐一说明 `compilerOptions` 中高频配置项的作用与典型取值。
5. 列举 `strict` 全家桶的 8 个子项，说明每项关闭后会引入何种风险，并解释为什么生产环境必须开启 `strict`。
6. 配置 `baseUrl` 与 `paths` 实现路径别名，并说明 `tsc` 产物为何需要 `tsc-alias` / bundler / `tsconfig-paths` 才能在运行时解析。
7. 使用 `references` + `composite` 拆分 monorepo，通过 `tsc --build` 实现增量编译。
8. 用 `tsconfig.base.json` + `tsconfig.dev.json` + `tsconfig.prod.json` 组合出多环境配置，并理解继承时的覆盖语义。
9. 在 `tsc --watch` / `tsc-watch` / `ts-node-dev` / `nodemon` / webpack / esbuild / vite 之间做出正确选型。
10. 识别并规避常见配置陷阱：`target` 与 `lib` 不匹配、`moduleResolution` 选错、`paths` 运行时不生效、`declaration` 与 `emitDecoratorMetadata` 冲突。

---

## 二、理论知识讲解 - tsconfig.json 结构

### 2.1 顶层字段总览

`tsconfig.json` 是项目根目录下的「编译入口清单」。它共有 7 个常用顶层字段：

| 字段 | 作用 | 是否必填 |
| --- | --- | --- |
| `compilerOptions` | 编译器配置，决定类型检查规则与产物形态 | 几乎必填 |
| `include` | 参与「编译 + 类型检查」的文件 glob 数组 | 与 `files` 二选一 |
| `exclude` | 从 `include` 中剔除的 glob 数组（默认含 `node_modules`、`outDir`、`bower_components`） | 可选 |
| `extends` | 继承另一份 tsconfig，覆盖语义为「子覆盖父」 | 可选 |
| `files` | 精确列出参与编译的文件路径数组（适合小型声明库） | 与 `include` 二选一 |
| `references` | 项目引用数组，每项 `{ "path": "./sub" }` 指向子项目 tsconfig | 可选 |
| `watchOptions` | `--watch` 模式下的文件监听策略（如轮询间隔、目录排除） | 可选 |

一个最小可用的 tsconfig：

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "strict": true
  },
  "include": ["src/**/*.ts"]
}
```

要点：

- `include` 与 `files` 互斥；二者都缺省时 tsc 默认包含当前目录下所有 `.ts` / `.tsx` 文件（递归）。
- `exclude` 只能剔除 `include` 范围内的文件，对 `files` 显式列出的文件无效。
- `references` 写在 `compilerOptions` 之外，描述的是「构建顺序依赖」而非「import 关系」。
- `tsconfig.json` 支持注释（`//` 与 `/* */`），因为 TS 解析它时会走 JSON5 宽松模式；其他工具（如 ESLint）若读取失败可改名为 `tsconfig.jsonc`。

### 2.2 extends 继承与官方预设

`extends` 让你把公共配置抽到 `tsconfig.base.json`，子配置只声明差异项。继承规则：

- 子配置的 `compilerOptions` 按「逐字段覆盖」合并到父配置；对象类型（如 `paths`）整体替换，不深合并。
- `include` / `exclude` / `files` 不继承，子配置需自行声明。
- `extends` 可链式继承（A extends B extends C），但实际项目建议控制在两层以内。

官方维护的预设包（通过 npm 安装即可 `extends`）：

| 包名 | 适用场景 | 关键设置 |
| --- | --- | --- |
| `@tsconfig/recommended` | 通用推荐基线 | `target: ES2022`、`strict: true`、`moduleResolution: Bundler` |
| `@tsconfig/node18` / `node20` | Node 18 / 20 项目 | `target` 与 `module` 对齐 Node 支持版本 |
| `@tsconfig/next` | Next.js 项目 | `jsx: preserve`、`module: ESNext`、`moduleResolution: Bundler` |
| `@tsconfig/create-react-app` | CRA 项目 | `jsx: react-jsx`、`lib` 含 DOM |
| `@tsconfig/strictest` | 最严格基线 | 在 `strict` 之上叠加 `noUncheckedIndexedAccess` 等 |

```jsonc
// 继承官方预设
{
  "extends": "@tsconfig/node18/tsconfig.json",
  "compilerOptions": {
    "outDir": "./dist"
  },
  "include": ["src/**/*.ts"]
}
```

### 2.3 include / exclude / glob 模式

`include` 与 `exclude` 支持 glob 通配符：

| 模式 | 含义 |
| --- | --- |
| `*` | 匹配单层任意字符（不跨 `/`） |
| `?` | 匹配单个任意字符 |
| `**` | 跨多层目录匹配 |
| `{a,b}` | 匹配 `a` 或 `b`（部分版本支持） |

示例：

```jsonc
{
  "include": [
    "src/**/*.ts",        // src 下所有 .ts（递归）
    "src/**/*.tsx",       // src 下所有 .tsx
    "types/**/*.d.ts"     // 自定义类型声明
  ],
  "exclude": [
    "node_modules",
    "dist",
    "**/*.spec.ts",       // 排除单测文件
    "**/*.test.ts",
    "e2e/**"              // 排除 e2e
  ]
}
```

要点：

- 默认 `exclude` 包含 `node_modules`、`outDir`（若设了 `outDir`）、`bower_components`、`jspm_packages`。
- glob 区分大小写受 `forceConsistentCasingInFileNames` 影响；该选项不影响 glob 匹配本身，只影响文件路径大小写一致性检查。
- `.d.ts` 文件若在 `include` 范围内会被当作「源文件」参与编译；通常应让全局 `.d.ts` 在 `include` 中但 `noEmit` 或放到 `typeRoots`。

---

## 三、compilerOptions 核心配置详解

按「目标与模块、严格性、输出、模块解析、JSX、实验性、高级」七个分组讲解。完整字段表见 [TSConfig Reference](https://www.typescriptlang.org/tsconfig/)。

### 3.1 目标与模块

| 字段 | 常用取值 | 作用 |
| --- | --- | --- |
| `target` | `ES5` / `ES2020` / `ES2022` / `ESNext` | 编译产物 JS 的**语法目标**；高于目标的语法（如 `async` 在 ES5）会被降级转译 |
| `module` | `CommonJS` / `ESNext` / `NodeNext` / `Preserve` | 产物的**模块系统**；`CommonJS` 输出 `require`，`ESNext` 输出 `import` |
| `moduleResolution` | `Node` / `Node16` / `NodeNext` / `Bundler` / `Classic` | 模块解析策略；决定 `import 'x'` 如何映射到磁盘文件 |
| `lib` | `DOM` / `ES2022` / `DOM.Iterable` / `ScriptHost` | 注入的类型声明库；**只影响类型层**，不注入运行时 polyfill |

关键区别：

- `target` 改的是「**输出语法**」（如 `class` 是否被降级为构造函数）。
- `lib` 改的是「**类型层可用 API**」（如 `Promise` / `Array.prototype.at` 是否可被识别）。
- 二者独立：你可以 `target: ES5` + `lib: ["ES2022", "DOM"]`，让产物降级但类型层能用 ES2022 API（前提是运行环境有 polyfill）。

`moduleResolution` 选型速查：

| 取值 | 适用 | 行为特点 |
| --- | --- | --- |
| `Node` | Node 项目（CommonJS） | 经典 Node 解析，兼容绝大多数库 |
| `Node16` / `NodeNext` | Node 16+ 原生 ESM | 强制 `import` 路径带 `.js` 后缀，区分 CJS/ESM |
| `Bundler` | webpack / vite / esbuild | 假设 bundler 接管解析，宽松允许省略后缀、`paths` 等 |
| `Classic` | 旧 TS < 4.7 | 已不推荐，仅用于了解历史 |

### 3.2 严格性 strict 全家桶

`strict: true` 是一个**总开关**，等价于一次性开启下列 8 个子项。生产环境必须开，理由见第四节。

| 子项 | 作用 |
| --- | --- |
| `noImplicitAny` | 禁止隐式 any；函数参数、变量无法推断时报错 |
| `strictNullChecks` | `null` / `undefined` 不能赋给非可空类型；可空成员访问前必须收窄 |
| `strictFunctionTypes` | 函数参数检查改为逆变，禁止不安全赋值 |
| `strictBindCallApply` | `bind` / `call` / `apply` 按签名严格校验参数 |
| `strictPropertyInitialization` | class 字段必须在构造函数中赋值 |
| `noImplicitThis` | 函数体内 `this` 不能隐式为 any |
| `alwaysStrict` | 产物每个文件顶部加 `'use strict'` |
| `useUnknownInCatchVariables` | `catch (e)` 中 `e` 类型为 `unknown` |

```jsonc
{
  "compilerOptions": {
    "strict": true,
    // 显式列出仅作教学对照；strict 已包含以下 8 项
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "useUnknownInCatchVariables": true
  }
}
```

`Code/tsconfig.strict-demo.json` 中以注释逐项说明了「关闭后果」与「典型坑」，可对照阅读。

### 3.3 输出

| 字段 | 作用 |
| --- | --- |
| `outDir` | 产物根目录；tsc 会保留 `rootDir` 下的目录结构 |
| `rootDir` | 源码根；超出此目录的文件会触发 `TS6059` 报错 |
| `sourceMap` | 生成 `.js.map`，断点调试必备 |
| `declaration` | 为每个 `.ts` 生成 `.d.ts`；库/SDK 必开 |
| `declarationMap` | 生成 `.d.ts.map`，库使用者可跳转到源码 |
| `removeComments` | 产物移除注释，减小体积 |
| `noEmit` | 只做类型检查不产出；常与 bundler 配合 |
| `emitDeclarationOnly` | 仅输出 `.d.ts`，JS 由 bundler 产出（库常见） |

```jsonc
{
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src",
    "sourceMap": true,
    "declaration": true,
    "declarationMap": true,
    "removeComments": true
  }
}
```

### 3.4 模块解析

| 字段 | 作用 |
| --- | --- |
| `baseUrl` | 非相对模块名的解析基准目录（如 `import 'utils/x'`） |
| `paths` | 路径别名映射；key 是 glob，value 是相对 `baseUrl` 的路径数组 |
| `typeRoots` | 默认 `["./node_modules/@types"]`；自定义可加上 `./types` |
| `types` | 显式限定加载的 `@types/*` 包；不设则自动加载全部 |
| `esModuleInterop` | 允许 `import fs from 'fs'` 默认导入 CJS 模块 |
| `allowSyntheticDefaultImports` | 类型层允许对 CJS 模块使用默认导入（不产出兼容代码） |
| `resolveJsonModule` | 允许 `import data from './x.json'` 并自动推断类型 |

`paths` 示例：

```jsonc
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*":        ["src/*"],
      "@config/*":  ["src/config/*"],
      "@utils/*":   ["src/utils/*"]
    }
  }
}
```

注意：`paths` 仅影响**类型层与 tsc 编译期的解析**，不会修改产物 JS 中的 `require` / `import` 路径。运行时如何解析见第五节。

### 3.5 JSX（前端相关简述）

| 取值 | 行为 |
| --- | --- |
| `preserve` | 保留 `.tsx` 中的 JSX 语法，输出 `.jsx`；交给 babel/swc/vite 处理 |
| `react` | 用 `React.createElement` 转译；产物含 `react` 引用 |
| `react-jsx` | React 17+ 新 JSX 转换，无需 `import React` |
| `react-jsxdev` | 同上 + 开发期附带 `__source` / `__self` 调试信息 |
| `react-native` | 保留 JSX，输出 `.js` |

前端项目通常配合 `jsx: "react-jsx"` + `moduleResolution: "Bundler"` + `lib: ["DOM", "DOM.Iterable", "ES2022"]`。

### 3.6 实验性

| 字段 | 作用 |
| --- | --- |
| `experimentalDecorators` | 启用 stage-1 装饰器（TS 老式实现） |
| `emitDecoratorMetadata` | 装饰器目标类型被 `Reflect.metadata` 写入元数据；NestJS / TypeORM 强依赖 |

```jsonc
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  }
}
```

⚠️ 见第九节陷阱：`emitDecoratorMetadata` 与新版 `declaration` 在某些场景下有副作用。

### 3.7 高级

| 字段 | 作用 |
| --- | --- |
| `isolatedModules` | 强制每个文件可独立编译；禁止跨文件 `const enum` 内联，强制使用 `import type` |
| `skipLibCheck` | 跳过所有 `.d.ts` 类型检查以加速编译；仅类型层，不影响业务代码 |
| `forceConsistentCasingInFileNames` | 强制文件名大小写一致；跨平台协作（macOS 大小写不敏感、Linux 敏感）必备 |
| `incremental` | 启用增量编译，缓存到 `.tsbuildinfo` |
| `tsBuildInfoFile` | 自定义 `.tsbuildinfo` 路径，便于 `.gitignore` 管理 |
| `noEmitOnError` | 类型错误时不产出 JS；生产 CI 卡口必备 |

```jsonc
{
  "compilerOptions": {
    "isolatedModules": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "incremental": true,
    "tsBuildInfoFile": "./.tsbuildinfo/app.tsbuildinfo"
  }
}
```

---

## 四、严格模式深度解读

`strict: true` 是 TS 团队推荐的默认基线，也是新项目应该坚守的底线。本节回答三个问题：**为什么开、关了会怎样、有哪些常见借口**。

### 4.1 严格模式的实战价值

- **把运行时错误前置到编译期**：`strictNullChecks` 让「空指针」在编译期被拦截；`noImplicitAny` 让「参数错位」在编译期暴露。
- **让重构可被类型系统保护**：`strictFunctionTypes` 让回调签名变更的影响范围被精确追踪。
- **降低团队协作成本**：新人改老代码时，严格模式会强制其处理边界情况，而不是默默引入 bug。
- **库作者必开**：未开 strict 的库导出的 `.d.ts` 会带 `any`，污染使用方的类型链。

### 4.2 关闭某一项的常见借口与坑

| 关闭项 | 借口 | 真实坑 |
| --- | --- | --- |
| `strictNullChecks` | 「项目里有大量 `null` 返回值，改起来太烦」 | `JSON.parse` / `Array.find` / `Map.get` 的 `undefined` 被静默吞掉，运行时 `TypeError: Cannot read property 'x' of undefined` |
| `noImplicitAny` | 「第三方库没类型，加 `any` 省事」 | `any` 沿调用链扩散，类型系统对该代码路径完全失效；重构时类型检查无法发现错误 |
| `strictPropertyInitialization` | 「用 DI 框架注入属性，构造函数里赋值不方便」 | 应该用 `!` 断言或 `declare` 字段，而不是关掉整个选项；关闭后未初始化字段在运行时为 `undefined` |
| `strictFunctionTypes` | 「事件回调签名不匹配」 | 真实风险：回调收到比预期「更窄」的类型，访问不存在的方法崩溃 |
| `useUnknownInCatchVariables` | 「`e.message` 不能直接访问太麻烦」 | 第三方库可能 `throw 'string'` 或 `throw { code: 1 }`，`e.message` 为 `undefined`；正确做法是 `if (e instanceof Error)` 收窄 |

### 4.3 生产必须开 strict 的核心理由

1. **安全底线**：未开 strict 的代码相当于「带类型注解的 JavaScript」，类型系统的保护大幅失效。
2. **性能无关**：strict 只影响编译期类型检查，**不影响产物体积与运行时性能**。关掉它换不来任何运行时收益。
3. **迁移成本递增**：项目越往后，引入 strict 的成本越高（遗留 any / null 越多）。新项目第一天就开 strict，长期收益最大。
4. **库的传染性**：未开 strict 的库导出的 `.d.ts` 会带 `any`，使用方开 strict 也无法防御。

### 4.4 进阶严格项（不在 strict 内）

生产环境推荐在 strict 基础上额外开启：

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,             // 未使用的局部变量报错
    "noUnusedParameters": true,         // 未使用的函数参数报错（_ 前缀豁免）
    "noImplicitReturns": true,          // 函数所有分支必须 return
    "noFallthroughCasesInSwitch": true, // switch case 必须显式 break
    "noUncheckedIndexedAccess": true,   // arr[i] 类型为 T | undefined
    "exactOptionalPropertyTypes": true  // 可选属性不能被显式赋 undefined
  }
}
```

`@tsconfig/strictest` 预设已包含上述全部，可直接 `extends`。

---

## 五、路径别名配置实战

### 5.1 配置 paths

`Code/tsconfig.dev.json` 与 `Code/tsconfig.prod.json` 中均配置了：

```jsonc
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*":        ["src/*"],
      "@config/*":  ["src/config/*"],
      "@utils/*":   ["src/utils/*"]
    }
  }
}
```

- `baseUrl` 是 `paths` value 的解析基准；不设 `baseUrl` 时 `paths` 仍生效（基于 tsconfig 所在目录）。
- value 是**数组**，可写多个候选路径，按顺序匹配。
- 别名 key 必须以 `*` 或精确名结尾；`@utils/logger` 命中 `@utils/*` 后，`*` 部分被替换到 value 的 `*` 位置。

### 5.2 业务代码使用别名

`Code/paths-demo.ts` 中演示了别名的使用方式与迁移思路：

```ts
// 迁移前（相对路径，深层级易错）
import { config } from '../../config';
import { logger } from '../../utils/logger';

// 迁移后（别名，文件移动无需改 import）
import { config } from '@config';
import { logger } from '@utils/logger';
```

### 5.3 运行时如何解析别名

**关键事实：`tsc` 编译不会在产物 JS 中替换 `@/*` 别名**。产物 JS 中仍然保留 `require('@/utils/logger')`，Node 原生无法解析，会抛 `MODULE_NOT_FOUND`。运行时解析必须借助以下工具之一：

| 工具 | 适用场景 | 工作方式 |
| --- | --- | --- |
| `ts-node` 内置 paths 解析 | 开发期直跑源码 | 读取 tsconfig 的 `paths`，运行时映射 |
| `tsc-alias` | 编译产物后处理 | 扫描 `dist/**/*.js`，把别名替换为相对路径 |
| `tsconfig-paths` | 运行时注册 require hook | `node -r tsconfig-paths/register dist/main.js` |
| bundler（webpack/vite/esbuild） | 打包场景 | 各自的 `resolve.alias` 配置 |

`Code/paths-demo.ts` 末尾与 `Code/build-scripts.md` 第四节给出了完整的命令对照，此处不重复。

### 5.4 别名的取舍

- **小项目**：别名收益有限，相对路径足够；引入别名反而增加工具链复杂度。
- **中大型项目**：别名能显著降低跨目录引用的心智成本，是值得的投入。
- **库项目**：发布到 npm 的库不应依赖别名（使用者环境不可控），用 bundler 在发布前把别名替换为相对路径。

---

## 六、项目引用 Project References

Project References 是 TS 提供的「多 tsconfig 编排」机制，用于把一个大型项目拆成多个互相引用的子项目。完整说明见 `Code/project-references-demo.md`，本节给出要点速览。

### 6.1 核心字段

```jsonc
// solution root（tsconfig.json）
{
  "files": [],
  "references": [
    { "path": "./packages/shared" },
    { "path": "./packages/server" }
  ]
}
```

```jsonc
// packages/shared/tsconfig.json（被引用方）
{
  "compilerOptions": {
    "composite": true,          // 必须开
    "declaration": true,        // composite 强制
    "rootDir": "./src",
    "outDir": "./dist"
  },
  "include": ["src/**/*.ts"]
}
```

### 6.2 三大价值

1. **增量编译**：`tsc --build` 仅重新编译发生变化的子项目，大型 monorepo 构建时间从分钟级降到秒级。
2. **强制模块边界**：子项目只能 `import` 被引用方的公开导出，配合 ESLint 可强制架构分层。
3. **独立编译目标**：`web` 子项目可 `target: ES2020` + `module: ESNext`，`server` 子项目可 `target: ES2022` + `module: CommonJS`，互不干扰。

### 6.3 构建命令

```bash
tsc --build               # 增量构建
tsc --build --force       # 全量重建
tsc --build --clean       # 清理产物与 .tsbuildinfo
tsc --build --watch       # 监听模式
```

### 6.4 何时不该用

- 单包小型项目：单 tsconfig 即可，引入 references 是过度工程化。
- 仅想加速单项目编译：先试 `incremental: true`，收益不足再上 references。

---

## 七、多环境配置组合

实际项目通常需要「开发 / 测试 / 生产」三套配置。最佳实践是抽出一个 base，子配置继承并叠加差异。

### 7.1 目录布局

```
Code/
├── tsconfig.base.json        # 公共约束（strict、target、module）
├── tsconfig.dev.json         # extends base + sourceMap + watch + paths
├── tsconfig.prod.json        # extends base + declaration + outDir
├── tsconfig.strict-demo.json # 教学用 strict 全家桶对照
└── tsconfig.test.json        # （可选）extends base + 测试相关
```

### 7.2 继承覆盖语义

- 子配置的 `compilerOptions` 按「逐字段覆盖」合并到父配置。
- 对象类型字段（如 `paths`、`lib`）**整体替换**，不深合并；若 dev 想保留 base 的 `paths` 并新增，需完整复制。
- `include` / `exclude` / `files` **不继承**，子配置需自行声明。

### 7.3 本仓库的继承链

```
tsconfig.base.json          （strict + ES2022 + CommonJS）
   ↑ extends
   ├── tsconfig.dev.json    （+ sourceMap + watch + paths）
   └── tsconfig.prod.json   （+ declaration + removeComments + outDir）
```

- base 只放「所有环境都应遵守」的约束：严格性、目标、模块、文件名一致性。
- base 不放 `outDir` / `sourceMap` / `declaration` 等环境相关字段，避免子配置被迫覆盖。
- dev 与 prod 的 `paths` 各自声明，确保别名独立可控。

### 7.4 调用方式

```bash
tsc -p tsconfig.dev.json  --noEmit       # 开发期类型检查
tsc -p tsconfig.dev.json  --watch        # 开发期 watch
tsc -p tsconfig.prod.json                # 生产构建
tsc -p tsconfig.prod.json --noEmit       # CI 卡口
```

---

## 八、常用构建工具集成

完整命令对照见 `Code/build-scripts.md`，本节给出选型决策树。

### 8.1 选型决策树

```
是否需要打包？
├── 否（纯 Node 后端）
│   ├── 开发期：ts-node-dev --transpile-only src/main.ts
│   ├── 生产构建：tsc -p tsconfig.prod.json && tsc-alias -p tsconfig.prod.json
│   └── 运行：node dist/main.js
│
└── 是（前端 / 库 / 需要 tree-shake）
    ├── 类型检查：tsc --noEmit（独立于打包）
    ├── 打包转译：bundler 接管
    │   ├── 前端 SPA：vite / webpack
    │   ├── 库：tsup / microbundle / rollup + esbuild
    │   └── 极速 CLI 工具：esbuild 直接 build
    └── paths 别名：由 bundler 的 resolve.alias 处理，无需 tsc-alias
```

### 8.2 watch 工具对比

| 工具 | 是否带类型检查 | 是否自动重启 | 适用 |
| --- | --- | --- | --- |
| `tsc --watch` | ✅ | ❌（仅编译） | 仅需 watch 编译，启动另开 nodemon |
| `tsc-watch` | ✅ | ✅（onSuccess） | 后端 Node 项目，编译成功后跑产物 |
| `ts-node-dev` | ❌（transpile-only） | ✅ | 开发期源码直跑热重启，启动极快 |
| `nodemon` + `ts-node` | 可选 | ✅ | 灵活度最高，可对接任意启动命令 |

### 8.3 与 bundler 的分工原则

主流推荐分工：

- **类型检查**：`tsc --noEmit`（CI / husky 钩子，独立于打包流程）
- **打包转译**：bundler（esbuild / vite / webpack）

这样既享受 bundler 的速度，又保留 tsc 的完整类型检查。`vite build` 默认不做类型检查，需在 `package.json` 中显式跑 `tsc --noEmit && vite build`。

---

## 九、常见配置陷阱

### 9.1 target 与 lib 不匹配

**症状**：`target: ES5` 但代码里用了 `Promise` / `Array.prototype.at`，类型层报错 `Property 'at' does not exist`；或 `target: ES2022` 但运行环境是 IE11，产物跑不起来。

**根因**：`target` 决定输出语法，`lib` 决定类型层可用 API；两者独立。

**对策**：

```jsonc
{
  "compilerOptions": {
    "target": "ES5",                    // 产物降级
    "lib": ["ES2022", "DOM"],           // 类型层允许 ES2022 API（需运行环境有 polyfill）
    "downlevelIteration": true          // 允许 for...of / 展开符降级
  }
}
```

并在运行环境引入 core-js 等 polyfill。

### 9.2 moduleResolution 选错

**症状**：`moduleResolution: "Node16"` 下 `import './foo'` 报错「不存在的扩展名」；`moduleResolution: "Bundler"` 下却用 `tsc` 直接编译产出 CJS。

**根因**：

- `Node16` / `NodeNext` 强制 `import` 路径带 `.js` 后缀（即使源文件是 `.ts`）。
- `Bundler` 假设 bundler 接管解析，宽松允许省略后缀，但**不应与 tsc 直接编译搭配**。

**对策**：

- 纯 Node + CommonJS：`module: "CommonJS"` + `moduleResolution: "Node"`。
- 纯 Node + 原生 ESM：`module: "NodeNext"` + `moduleResolution: "NodeNext"`，import 路径写 `.js`。
- webpack / vite / esbuild：`moduleResolution: "Bundler"`，类型检查用 `tsc --noEmit`，不直接 `tsc` 产出。

### 9.3 paths 运行时不生效

**症状**：tsconfig 配了 `paths`，IDE 跳转正常，`tsc` 编译通过，但运行 `node dist/main.js` 抛 `Cannot find module '@/utils/logger'`。

**根因**：`tsc` 不会在产物 JS 中替换 `@/*` 别名，Node 原生无法解析。

**对策**（任选其一）：

```bash
# 方案 1：tsc-alias 后处理产物
tsc -p tsconfig.prod.json && tsc-alias -p tsconfig.prod.json

# 方案 2：运行时注册 tsconfig-paths
node -r tsconfig-paths/register dist/main.js

# 方案 3：用 bundler（webpack/vite/esbuild）打包，alias 在 bundler 配置
```

### 9.4 declaration 与 emitDecoratorMetadata 冲突

**症状**：NestJS 项目开启 `emitDecoratorMetadata` + `declaration: true`，生成 `.d.ts` 时部分构造函数参数类型为 `{}` 或 `any`，使用方拿到的类型丢失。

**根因**：`emitDecoratorMetadata` 依赖 `Reflect.metadata`，在 `.d.ts` 生成阶段对部分泛型 / 复杂类型推断不稳定，会退化。

**对策**：

- 库项目：若该库被 NestJS 风格 DI 消费，避免同时开 `emitDecoratorMetadata` 与 `declaration`；改用 `ts-loader` 或 `@swc/core` 在使用方侧生成元数据。
- 应用项目：保留 `emitDecoratorMetadata`，但 `declaration` 仅在 `tsc --noEmit` 时关闭，发布前另起 `tsconfig.build.json` 不开 `emitDecoratorMetadata` 重新生成 `.d.ts`。

### 9.5 其他高频陷阱

- **`skipLibCheck` 不是免死金牌**：它跳过的是 `.d.ts` 检查，业务代码报错仍会被检查；不要把 `skipLibCheck` 当成「关掉类型检查」。
- **`composite` 必须配 `declaration`**：开 `composite` 时 `declaration` 被强制为 `true`，无法关闭。
- **`references` 不等于 import**：tsconfig 里写 `references` 只声明构建顺序依赖，业务代码仍需 `import` 才能使用对方导出。
- **`strict: false` 与子项显式开启**：`strict: false` 时，单独开启 `strictNullChecks: true` 是合法的；但子项默认值会被 `strict: false` 重置为 `false`，必须显式声明。
- **`forceConsistentCasingInFileNames` 与 git**：git 默认大小写不敏感（macOS / Windows），`forceConsistentCasingInFileNames` 只在 TS 编译期检查，不能修复已入库的大小写不一致；需配合 `git config core.ignorecase false` 与重命名提交。

---

## 十、关键知识点总结

### 10.1 核心配置速查表

| 类别 | 字段 | 推荐值（Node 后端） | 推荐值（前端 bundler） |
| --- | --- | --- | --- |
| 目标 | `target` | `ES2022` | `ES2020` / `ESNext` |
| 模块 | `module` | `CommonJS` / `NodeNext` | `ESNext` / `Preserve` |
| 解析 | `moduleResolution` | `Node` / `NodeNext` | `Bundler` |
| 类型库 | `lib` | `["ES2022"]` | `["DOM", "DOM.Iterable", "ES2022"]` |
| 严格 | `strict` | `true` | `true` |
| 默认导入 | `esModuleInterop` | `true` | `true` |
| JSON | `resolveJsonModule` | `true` | `true` |
| 大小写 | `forceConsistentCasingInFileNames` | `true` | `true` |
| 跳过 lib 检查 | `skipLibCheck` | `true` | `true` |
| 独立编译 | `isolatedModules` | `true` | `true` |
| 产物目录 | `outDir` | `./dist` | 由 bundler 决定 |
| 源码根 | `rootDir` | `./src` | `./src` |
| 调试 | `sourceMap` | dev `true` / prod `false` | 由 bundler 决定 |
| 类型声明 | `declaration` | 库 `true` / 应用 `false` | 库 `true` / 应用 `false` |
| 别名 | `paths` | `{"@/*": ["src/*"]}` | `{"@/*": ["src/*"]}` |
| 增量 | `incremental` | `true` | `true` |
| 监听 | `watchOptions` | 可选 | 可选 |

### 10.2 七个必须记住的要点

1. **`strict: true` 是底线**，不是可选项；生产不开 strict 等于「带类型注解的 JS」。
2. **`target` 改语法，`lib` 改类型 API**；二者独立，配合 polyfill 使用。
3. **`moduleResolution` 必须与 `module` 匹配**；Node 用 `Node`，原生 ESM 用 `NodeNext`，bundler 用 `Bundler`。
4. **`paths` 仅类型层生效**；运行时必须靠 `tsc-alias` / `tsconfig-paths` / bundler 处理。
5. **`extends` 是覆盖不是合并**；对象字段整体替换，`include` 不继承。
6. **Project References 用 `tsc --build`**；不要用裸 `tsc` 编译 references 项目。
7. **类型检查与打包解耦**；`tsc --noEmit` 做类型检查，bundler 做转译打包，各司其职。

### 10.3 推荐最小基线（Node 后端）

```jsonc
// tsconfig.base.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "moduleResolution": "Node",
    "lib": ["ES2022"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

---

## 十一、实战练习

### 练习一：多环境配置组合（基础）

**目标**：基于本仓库的 `tsconfig.base.json`，新增一份 `tsconfig.test.json`，满足：

1. 继承 `tsconfig.base.json`。
2. `outDir` 为 `./dist/test`，`sourceMap: true`。
3. `include` 包含 `src/**/*.ts` 与 `tests/**/*.ts`。
4. `types` 显式限定为 `["node", "jest"]`（即使未装 jest 也可写，仅作配置练习）。
5. 在 `package.json` 中新增 `type-check:test` 脚本调用该配置。

**验证**：执行 `npx tsc -p tsconfig.test.json --noEmit` 不报错（无源码时也会通过）。

**提示**：

- `extends` 不继承 `include`，需完整声明。
- `types` 显式列出后，未列出的 `@types/*` 不会被自动加载。

### 练习二：路径别名从配置到运行（进阶）

**目标**：在 `Code/` 下创建以下文件结构，让 `paths` 别名在「ts-node 直跑」与「tsc + tsc-alias 编译产物」两条路径都能跑通：

```
Code/
└── src/
    ├── utils/
    │   └── math.ts        # export const add = (a, b) => a + b;
    └── main.ts            # import { add } from '@/utils/math'; console.log(add(1, 2));
```

**要求**：

1. 修改 `tsconfig.dev.json` 的 `paths`，让 `@/*` 映射到 `src/*`。
2. 用 `npx ts-node -T src/main.ts` 运行，验证 ts-node 内置 paths 解析生效。
3. 用 `npx tsc -p tsconfig.prod.json && npx tsc-alias -p tsconfig.prod.json` 编译，再用 `node dist/prod/main.js` 运行，验证别名已被替换为相对路径。

**验证**：

- 步骤 2 输出 `3`。
- 步骤 3 检查 `dist/prod/main.js` 中 `require('@/utils/math')` 已被替换为 `require('./utils/math')`。

**提示**：

- `tsconfig.prod.json` 的 `rootDir` 是 `./src`，源码必须放 `src/` 下。
- `tsc-alias` 默认读取 `tsconfig.json`，需用 `-p` 指定 `tsconfig.prod.json`。

### 练习三：strict 全家桶对照实验（深度）

**目标**：通过逐项关闭 strict 子项，观察类型检查行为变化。

**步骤**：

1. 复制 `tsconfig.strict-demo.json` 为 `tsconfig.strict-loose.json`，把 `strict` 设为 `false`，但保留所有子项为 `true`。
2. 写一段「问题代码」`strict-probe.ts`：

   ```ts
   function greet(name) {           // noImplicitAny 触发点
     return 'hello ' + name;
   }

   const u: { name: string } = JSON.parse('{}') as any;
   console.log(u.name.length);      // strictNullChecks 失守

   class User {
     name: string;                  // strictPropertyInitialization 触发点
   }

   try {
     throw { code: 1 };
   } catch (e) {
     console.log(e.code);           // useUnknownInCatchVariables 触发点
   }
   ```

3. 分别用 `tsconfig.strict-demo.json`（strict:true）与 `tsconfig.strict-loose.json`（strict:false）跑 `tsc --noEmit`，对比报错数量与位置。
4. 在 `tsconfig.strict-loose.json` 中逐项关闭某个子项（如 `strictNullChecks: false`），观察哪些报错消失、哪些保留，记录关闭代价。

**验证**：

- `strict:true` 下 `strict-probe.ts` 至少报 4 处错。
- 关闭某项后，对应的报错消失，但代码运行时风险仍在。

**提示**：

- `strict: false` 时子项默认被重置为 `false`，必须显式写 `true` 才能保留。
- 实验完毕后删除 `strict-probe.ts` 与 `tsconfig.strict-loose.json`，不要入库。
