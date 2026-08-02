# TypeScript 全栈学习指南

> 系统化掌握 TypeScript 类型系统，为 NestJS 后端与 AI 全栈开发奠定类型安全基础
>
> 共 15 天，覆盖从类型基础到工程化实战的完整知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是全栈学习系列的**类型安全基石**。TypeScript 既是前端工程化的标配（Vue 3 / React 全家桶深度依赖），也是后端 NestJS 框架的核心语言，更是 AI 应用后端服务（LangChain.js、向量数据结构约束、Schema 校验）的类型保障。

**学习目标**：完成本板块后，你应能：
- 熟练运用 TS 类型系统描述任意数据结构与函数签名
- 理解并手写常见工具类型，掌握类型体操基本技法
- 配置生产级 tsconfig，搭建 TS 工程化项目
- 用 TS 重写 Node.js 与 Express 应用，打通前后端类型链路
- 为学习 NestJS（依赖装饰器 + DI + 类型系统）扫清全部障碍

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 代码示例 + 实战练习
- 紧扣工程化视角，多处铺垫 NestJS、Zod、LangChain.js 等生态
- 所有代码可在 Node 18+ 与 TS 5+ 直接运行，已实测通过
- 每天开头直接进入章节简介，不做多余定位

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| JavaScript 基础 | 熟练 | ES6+ 语法、闭包、原型链、class、Promise、async/await |
| Node.js 基础 | 完成 NodeJS 板块 | 模块系统、fs/http/crypto 等核心模块（Day14-15 需要） |
| 命令行操作 | 基础 | 能用终端执行 npm 命令、配置环境变量 |
| 类型系统概念 | 了解即可 | 有其他静态类型语言（Java/C#/Go）经验更佳，但不强制 |

**环境准备**：
- Node.js 18 LTS 或更高
- TypeScript 5.0+（各 Day 的 `package.json` 已声明）
- VS Code（TS 支持最佳）
- 推荐扩展：TypeScript Vue Plugin、Prettier、ESLint

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                  TypeScript 全栈学习路线（15天）                  │
└─────────────────────────────────────────────────────────────────┘

阶段一：类型基础（Day01-Day05）
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  Day01 简介  │  Day02 基础  │  Day03 接口  │  Day04 函数  │  Day05 联合  │
│  与环境      │  类型系统    │  与类型别名  │  与泛型      │  与交叉类型  │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │              │
       ▼              ▼              ▼              ▼              ▼
阶段二：面向对象与高级类型（Day06-Day09）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Day06 类    │  Day07 枚举  │  Day08 高级  │  Day09 装饰  │
│  与 OOP      │  与类型推断  │  类型与工具  │  器与元数据  │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
阶段三：工程化（Day10-Day12）
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  Day10 模块与命名空间│  Day11 类型声明 d.ts │  Day12 tsconfig 工程化│
└──────────┬───────────┴──────────┬───────────┴──────────┬───────────┘
           │                      │                      │
           ▼                      ▼                      ▼
阶段四：进阶与实战（Day13-Day15）
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  Day13 类型体操与实战│  Day14 TS 与 Node.js │  Day15 TS 与 Express  │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

---

## 每日内容详表

### 阶段一：类型基础

#### Day01 - TypeScript简介与环境搭建
- **核心**：JS 类型困境、TS 是 JS 超集、类型擦除、tsc 编译器、tsconfig.json、ts-node/tsx 运行器
- **代码**：`hello.ts` / `types-vs-js.ts` / `tsconfig.json` / `compile-and-run.md`
- **重点**：为后续所有天数铺垫环境与工作流

#### Day02 - 基础类型系统
- **核心**：原始类型、数组、元组、any/unknown/never/void、字面量类型、类型断言、let vs const 推断、类型收窄初步
- **代码**：`primitive-types.ts` / `array-tuple.ts` / `any-unknown-never.ts` / `literal-types.ts` / `type-assertion.ts` / `type-narrowing.ts`
- **重点**：any vs unknown 的安全性差异、never 的穷尽检查

#### Day03 - 接口与类型别名
- **核心**：interface、type alias、两者深度对比、索引签名、函数类型、结构化类型、多余属性检查
- **代码**：`interface-basic.ts` / `type-alias.ts` / `interface-vs-type.ts` / `index-signature.ts` / `function-types.ts` / `structural-typing.ts`
- **重点**：声明合并（interface 可 / type 不可）、何时用哪个

#### Day04 - 函数与泛型
- **核心**：函数类型注解、可选/默认/剩余参数、this 类型、函数重载、泛型函数、泛型约束 extends、keyof 约束
- **代码**：`function-types.ts` / `function-overload.ts` / `generic-basic.ts` / `generic-constraints.ts` / `generic-repository.ts`
- **重点**：泛型是 TS 类型系统灵魂，为 NestJS 依赖注入铺垫

#### Day05 - 联合类型与交叉类型
- **核心**：联合 `|`、交叉 `&`、可辨识联合、类型收窄（typeof/instanceof/in/等值/switch/truthy）、自定义类型守卫 `x is Type`、never 穷尽检查
- **代码**：`union-types.ts` / `intersection-types.ts` / `discriminated-union.ts` / `typeof-narrowing.ts` / `custom-guard.ts` / `exhaustive-check.ts`
- **重点**：可辨识联合是 TS 处理状态机的最佳模式

---

### 阶段二：面向对象与高级类型

#### Day06 - 类与面向对象
- **核心**：class、访问修饰符（public/private/protected/#私有字段）、readonly、参数属性、getter/setter、静态成员、抽象类、继承、implements、泛型类
- **代码**：`class-basic.ts` / `access-modifiers.ts` / `parameter-properties.ts` / `getters-setters.ts` / `abstract-class.ts` / `inheritance-implements.ts` / `static-members.ts` / `generic-class.ts`
- **重点**：`private` 编译期私有 vs `#` 运行时私有

#### Day07 - 枚举与类型推断
- **核心**：数字/字符串/异构枚举、const enum、反向映射、enum vs 联合字面量 vs as const、类型推断机制、类型拓宽、const 断言、上下文类型
- **代码**：`numeric-enum.ts` / `string-enum.ts` / `const-enum.ts` / `enum-vs-union.ts` / `type-inference.ts` / `type-widening.ts` / `best-common-type.ts`
- **重点**：现代项目推荐 `as const` 替代 enum

#### Day08 - 高级类型与工具类型
- **核心**：keyof/typeof/索引访问、映射类型、条件类型、infer、分布式条件类型、内置工具类型（Partial/Required/Readonly/Pick/Omit/Record/Exclude/Extract/ReturnType 等）、模板字面量类型
- **代码**：`keyof-typeof.ts` / `mapped-types.ts` / `conditional-types.ts` / `utility-types.ts` / `custom-utility.ts` / `template-literal.ts`
- **重点**：TS 类型系统的精髓所在

#### Day09 - 装饰器与元数据
- **核心**：装饰器概念与历史、四种装饰器（类/方法/属性/参数）、装饰器工厂、执行顺序、reflect-metadata、emitDecoratorMetadata
- **代码**：`class-decorator.ts` / `method-decorator.ts` / `property-decorator.ts` / `parameter-decorator.ts` / `decorator-factory.ts` / `reflect-metadata-demo.ts` / `mini-di-container.ts` / `mini-controller.ts`
- **重点**：NestJS 的核心机制，理解装饰器就理解 NestJS 一半

---

### 阶段三：工程化

#### Day10 - 模块与命名空间
- **核心**：ES Modules、类型导出 import type、模块解析策略（classic/node/node16/nodenext/bundler）、命名空间 namespace、声明合并、三斜线指令、barrel file
- **代码**：`math-utils.ts` / `string-utils.ts` / `index.ts` / `namespace-demo.ts` / `declaration-merging.ts` / `import-type.ts` / `module-resolution.md`
- **重点**：现代项目优先用 ES Modules，namespace 仅用于 .d.ts

#### Day11 - 类型声明与d.ts
- **核心**：.d.ts 本质、@types 组织、declare 关键字、模块扩增（扩展 Express.Request）、全局声明、process.env 类型扩展
- **代码**：`global-declare.d.ts` / `module-declare.d.ts` / `express-augment.d.ts` / `env.d.ts` / `third-party-types.md` / `use-declare.ts`
- **重点**：模块扩增是扩展第三方库类型的常用手法

#### Day12 - tsconfig工程化配置
- **核心**：tsconfig 结构、extends 继承、compilerOptions 全配置（target/module/strict 全家桶/输出/paths/项目引用）、多环境配置组合、构建工具集成
- **代码**：`tsconfig.base.json` / `tsconfig.dev.json` / `tsconfig.prod.json` / `tsconfig.strict-demo.json` / `paths-demo.ts` / `project-references-demo.md` / `build-scripts.md`
- **重点**：strict 全家桶必须开、paths 运行时解析问题

---

### 阶段四：进阶与实战

#### Day13 - 类型体操与实战
- **核心**：DeepPartial/DeepReadonly、MyPick/MyOmit/MyRecord 手写、字符串类型操作（CamelCase/KebabCase）、Path<T> 生成对象路径、类型安全路由与事件系统
- **代码**：`deep-types.ts` / `pick-by-value.ts` / `my-utility.ts` / `string-operations.ts` / `type-safe-router.ts` / `type-safe-events.ts` / `object-path.ts`
- **重点**：类型体操的边界，可读性 vs 类型安全的取舍

#### Day14 - TypeScript与Node.js
- **核心**：@types/node、TS 运行 Node 的方式（tsc/ts-node/tsx）、CommonJS vs ESM 在 TS 中的处理、用 TS 重写 fs/http/crypto、错误处理类型化（unknown）、异步类型化
- **代码**：`fs-typed.ts` / `http-server-typed.ts` / `crypto-typed.ts` / `error-handling.ts` / `async-typed.ts` / `esm-vs-cjs.ts` / `project-structure.md`
- **重点**：ESM 中 `__dirname` 的替代、useUnknownInCatchVariables

#### Day15 - TypeScript与Express
- **核心**：@types/express、Request/Response 泛型、扩展 Request 对象、中间件类型化、分层架构（types/routes/services/middlewares/utils）、DTO 模式、与 NestJS 的衔接
- **代码**：`types/index.ts` / `types/express.d.ts` / `middlewares/*.ts` / `utils/response.ts` / `routes/articles.ts` / `services/article-service.ts` / `app.ts` / `server.ts`
- **重点**：本应用的分层正是 NestJS 控制器/服务/中间件的雏形

---

## 目录结构

```
TypeScript/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - TypeScript简介与环境搭建/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天代码示例
│       ├── hello.ts
│       ├── types-vs-js.ts
│       ├── tsconfig.json
│       ├── package.json
│       └── compile-and-run.md
├── Day02 - 基础类型系统/
│   ├── README.md
│   └── Code/
│       └── ...
├── ...（Day03-Day14 同构）...
└── Day15 - TypeScript与Express/
    ├── README.md
    └── Code/
        ├── app.ts
        ├── server.ts
        ├── tsconfig.json
        ├── package.json
        ├── types/
        │   ├── index.ts
        │   └── express.d.ts
        ├── middlewares/
        ├── routes/
        ├── services/
        └── utils/
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内
- 需要依赖的天数在 `Code/` 下有 `package.json` 与 `tsconfig.json`
- Day15 采用分层架构，`Code/` 下有 `types/` `routes/` `services/` `middlewares/` `utils/` 子目录

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 5-6 小时 | 约 2-3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 5-6 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **先读后写**：每天先通读 README，理解概念后再动手跑代码
2. **动手验证**：每个 `.ts` 文件都要用 `ts-node` 运行，观察类型推断结果
3. **改写实验**：在示例基础上做修改，故意写错类型观察编译报错
4. **善用 IDE**：鼠标悬停查看类型推断结果、用 F12 跳转定义、看错误提示
5. **完成实战**：每天 README 末尾的实战练习是巩固知识的关键

### 阶段性检查点

完成每个阶段后，应能回答以下问题：

- **阶段一完成后**：能否为任意 API 响应写出准确的 TS 类型？
- **阶段二完成后**：能否手写一个泛型 Repository 并用装饰器实现迷你 DI？
- **阶段三完成后**：能否配置生产级 tsconfig 并为无类型 JS 库编写 .d.ts？
- **阶段四完成后**：能否用 TS 重写一个完整 Express 应用并打通前后端类型链路？

---

## 如何运行代码

### 基础运行（Day01-Day13）

```bash
cd "Day01 - TypeScript简介与环境搭建/Code"
npm install                          # 安装 typescript / ts-node / @types/node
npx ts-node hello.ts                  # 直接运行 TS
npx tsc --noEmit                      # 仅类型检查不输出
npx tsc hello.ts && node hello.js     # 编译后运行
```

### 现代运行器（推荐 tsx）

```bash
npx tsx hello.ts                      # 比 ts-node 更快，ESM 友好
npx tsx watch hello.ts                # 热重载
```

### Express 项目（Day15）

```bash
cd "Day15 - TypeScript与Express/Code"
npm install                           # 安装 express + @types/express + ts 依赖
npx tsx server.ts                     # 启动服务
# 按注释中的 curl 命令测试各路由
```

### 类型检查工作流

```bash
npx tsc --noEmit                      # 全量类型检查（CI 必备）
npx tsc --noEmit --watch              # 增量监听
```

### Windows 用户注意

- PowerShell 中 `curl` 是 `Invoke-WebRequest` 别名，建议用 `curl.exe` 或 Git Bash
- 路径分隔符为 `\`，但 TS 的 `paths` 配置用 `/`
- 文件名大小写敏感（`forceConsistentCasingInFileNames: true`）

---

## 知识点速查

### TS 类型系统核心概念速查表

| 概念 | 一句话解释 | 对应天数 |
|------|----------|---------|
| 类型擦除 | TS 编译后类型信息全部移除，运行时是纯 JS | Day01 |
| 结构化类型 | 只看结构不看名字，结构相同即兼容（鸭式辩型） | Day03 |
| 多余属性检查 | 对象字面量直接赋值时检查多余字段，变量中转可绕过 | Day03 |
| 泛型约束 extends | 限制泛型参数必须满足某条件 | Day04 |
| 可辨识联合 | 用公共字面量字段判别联合类型分支 | Day05 |
| 类型守卫 x is T | 自定义函数谓词，告诉 TS 收窄类型 | Day05 |
| never 穷尽检查 | default 分支赋值给 never，漏处理分支编译报错 | Day05 |
| 参数属性 | 构造函数参数前加修饰符自动赋值（`constructor(public x: string)`） | Day06 |
| 映射类型 | `[K in keyof T]` 遍历键生成新类型 | Day08 |
| 条件类型 | `T extends U ? X : Y` 类型层面的三元 | Day08 |
| infer | 在条件类型中推断类型变量 | Day08 |
| 分布式条件类型 | 裸类型参数自动分发到联合成员 | Day08 |
| 模板字面量类型 | `` `${A}${B}` `` 类型层面的字符串拼接 | Day08 |
| 装饰器 | AOP 思想，给类/方法/属性/参数附加行为 | Day09 |
| 模块扩增 | `declare module` 扩展已有库的类型 | Day11 |
| 声明合并 | 同名 interface/function/namespace 自动合并 | Day10、Day11 |
| strict 全家桶 | 8 项严格检查的总开关，生产必开 | Day12 |
| 类型拓宽 | 字面量赋值给 let 后拓宽为基础类型 | Day07 |

### 常用工具类型速查

| 工具类型 | 作用 | 来源 |
|---------|------|------|
| Partial\<T\> | 所有属性变可选 | 内置 |
| Required\<T\> | 所有属性变必填 | 内置 |
| Readonly\<T\> | 所有属性变只读 | 内置 |
| Pick\<T,K\> | 挑选指定键 | 内置 |
| Omit\<T,K\> | 排除指定键 | 内置 |
| Record\<K,T\> | 构造键值对类型 | 内置 |
| Exclude\<T,U\> | 从联合排除 | 内置 |
| Extract\<T,U\> | 从联合提取 | 内置 |
| NonNullable\<T\> | 排除 null/undefined | 内置 |
| ReturnType\<T\> | 提取函数返回值类型 | 内置 |
| Parameters\<T\> | 提取函数参数类型元组 | 内置 |
| Awaited\<T\> | 递归解包 Promise | 内置 |
| DeepPartial\<T\> | 递归可选（自定义） | Day13 |
| DeepReadonly\<T\> | 递归只读（自定义） | Day13 |
| Path\<T\> | 生成对象所有路径（自定义） | Day13 |

### 常用命令速查

```bash
# 安装与初始化
npm install -g typescript             # 全局安装 tsc
tsc --init                            # 生成 tsconfig.json
npm install typescript ts-node @types/node --save-dev

# 编译与运行
tsc file.ts                           # 编译为 JS
tsc                                   # 按 tsconfig 编译
tsc --noEmit                          # 仅类型检查
ts-node file.ts                       # 直接运行 TS
tsx file.ts                           # 现代运行器（更快）
tsx watch file.ts                     # 热重载

# 严格性检查
tsc --strict                          # 临时开启严格模式检查
tsc --noImplicitAny                   # 检查隐式 any

# 调试
tsc --traceResolution                 # 查看模块解析过程
tsc --explainFiles                    # 解释文件为何被编译
```

### tsconfig 核心配置速查

```jsonc
{
  "compilerOptions": {
    // 目标与模块
    "target": "ES2022",               // 编译目标
    "module": "commonjs",             // 模块系统（Node 项目）/ "NodeNext"（ESM）
    "moduleResolution": "node",       // 模块解析策略 / "bundler"
    "lib": ["ES2022"],                // 类型库

    // 严格性（生产必开）
    "strict": true,                   // 严格总开关（含以下 8 项）
    "noImplicitAny": true,            // 禁止隐式 any
    "strictNullChecks": true,         // null/undefined 不能赋给其他类型
    "strictFunctionTypes": true,      // 函数参数逆变检查
    "strictPropertyInitialization": true, // 类属性必须初始化
    "noImplicitThis": true,           // this 必须有明确类型
    "useUnknownInCatchVariables": true, // catch 的 e 是 unknown

    // 输出
    "outDir": "./dist",               // 输出目录
    "rootDir": "./src",               // 源码根目录
    "sourceMap": true,                // 生成 sourcemap
    "declaration": true,              // 生成 .d.ts
    "removeComments": true,           // 移除注释

    // 模块解析
    "esModuleInterop": true,          // 兼容 CommonJS 默认导入
    "resolveJsonModule": true,         // 可 import JSON
    "baseUrl": ".",                    // 路径基准
    "paths": { "@/*": ["src/*"] },    // 路径别名

    // 高级
    "skipLibCheck": true,              // 跳过 .d.ts 检查（提速）
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,           // 单文件编译兼容
    "experimentalDecorators": true,    // 装饰器（Day09/NestJS 必需）
    "emitDecoratorMetadata": true      // 装饰器元数据（NestJS 依赖注入必需）
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **NestJS** | 直接基于 Day09 装饰器 + Day06 类 + Day04 泛型，是 TS 板块的最大受益者 |
| **MySQL** | TS 的类型系统配合 ORM（Prisma/TypeORM）实现类型安全查询 |
| **Redis** | 类型化的缓存接口设计 |
| **LangChain.js** | TS 类型让 LLM 链路调用、工具定义类型安全 |
| **RAG** | 向量数据结构、文档元数据的类型约束 |
| **Agent** | 工具调用的输入输出类型、消息协议类型 |
| **Docker** | Day14 的项目结构 + tsconfig 可直接用于构建 TS 镜像 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [TypeScript 官方手册](https://www.typescriptlang.org/zh/docs/handbook/intro.html) - 官方权威教程
- [TypeScript 中文文档](https://www.tslang.cn/docs/home.html) - 中文翻译
- [TypeScript Playground](https://www.typescriptlang.org/play) - 在线运行 TS 并查看编译结果
- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/) - 社区经典深入指南
- [Type Challenges](https://github.com/type-challenges/type-challenges) - 类型体操练习题
- [NestJS 官方文档](https://docs.nestjs.com/) - 后续 NestJS 板块的前置

---

## 贡献与反馈

> 本学习手册为原创内容，如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用类型武装你的全栈之路！**