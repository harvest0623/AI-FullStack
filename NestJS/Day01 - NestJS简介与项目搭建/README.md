# Day01 - NestJS 简介与项目搭建

> 本章节我们将认识 NestJS——一个深度拥抱 TypeScript 的 Node.js 服务端框架，理解它如何用装饰器、依赖注入与模块化把后端工程从「拼装中间件」升级为「架构化协作」，并完成从 CLI 安装、项目脚手架到第一个可运行应用的完整闭环。

---

## 目录

- [一、本章简介](#一本章简介)
- [二、学习目标](#二学习目标)
- [三、理论知识](#三理论知识)
  - [3.1 NestJS 是什么](#31-nestjs-是什么)
  - [3.2 为什么选择 NestJS](#32-为什么选择-nestjs)
  - [3.3 NestJS 与 Express 的对比](#33-nestjs-与-express-的对比)
  - [3.4 核心概念总览](#34-核心概念总览)
  - [3.5 请求生命周期概览](#35-请求生命周期概览)
- [四、环境搭建](#四环境搭建)
- [五、第一个 NestJS 应用](#五第一个-nestjs-应用)
- [六、nest CLI 常用命令](#六nest-cli-常用命令)
- [七、tsconfig 与 nest-cli.json 配置说明](#七tsconfig-与-nest-clijson-配置说明)
- [八、与 TypeScript 板块的衔接](#八与-typescript-板块的衔接)
- [九、关键知识点总结](#九关键知识点总结)
- [十、实战练习](#十实战练习)

---

## 一、本章简介

如果你写过 Express，大概率经历过这样的阶段：项目初期一个 `app.js` 串起所有路由，三个月后变成几十个 `router.use(...)`、几百行中间件、Service 与 Controller 边界模糊、依赖之间靠 `require` 互相拉扯。Express 本身只是一个「HTTP 抽象层」，它给你 `req`/`res` 与中间件管线，但**架构全靠自己摸索**。

**NestJS** 是一个基于 TypeScript 的 Node.js 服务端应用框架，由 Kamil Myśliwiec 在 2017 年开源。它的定位正是补齐 Express 缺失的那一层「架构」：

- 用 **OOP（面向对象）** 组织代码单元：Controller、Service、Module 都是类。
- 用 **FP（函数式）** 与 **FRP（响应式编程）** 处理异步流：拦截器底层是 RxJS 的 `Observable`。
- 用 **装饰器** 声明意图：`@Controller()`、`@Get()`、`@Injectable()`、`@Module()` 都是声明式 API。
- 用 **依赖注入（DI）** 装配组件：Service 不再手动 `new`，由 IoC 容器按需注入。

NestJS 的设计哲学深受 **Angular** 影响——模块化、DI、装饰器、`forRoot` 动态模块等概念几乎一脉相承。但与 Angular 不同的是，NestJS 默认跑在 **Express** 之上（也可一键切换到 **Fastify**），它并不重新发明 HTTP 层，而是把 HTTP 层封装成可替换的适配器（`@nestjs/platform-express` / `@nestjs/platform-fastify`），把精力集中在架构与工程实践上。

本章目标是建立对 NestJS 的整体认知，搭好本地开发环境，并跑通第一个应用。从 Day02 起我们会逐个深入核心组件。

---

## 二、学习目标

完成本节内容后，你应当能够：

1. **说清楚 NestJS 是什么**：能用自己的话讲明白「基于 TS 的后端框架」「融合 OOP/FP/FRP」「装饰器驱动 + 依赖注入」「借鉴 Angular」「默认基于 Express 可换 Fastify」五个要点。
2. **解释 NestJS 与 Express 的关系与差异**：知道 NestJS 不是 Express 的替代品而是「架构层」，能从架构、类型、中间件、工具链、学习曲线五个维度做对比。
3. **列举八大核心组件的职责**：Module / Controller / Provider / Middleware / Guard / Pipe / Interceptor / ExceptionFilter 一句话讲清各自定位。
4. **画出请求生命周期链路**：从请求进入到响应返回，按顺序列出中间件 → 守卫 → 拦截器（前）→ 管道 → 控制器 → 拦截器（后）→ 异常过滤器 → 响应。
5. **独立搭建 NestJS 开发环境**：全局安装 `@nestjs/cli`，用 `nest new` 创建项目，理解 package manager / git / strict mode 三个选项的含义。
6. **读懂项目结构与配置文件**：能解释 `src/`、`test/`、`package.json`、`tsconfig.json`、`tsconfig.build.json`、`nest-cli.json` 各自的作用。
7. **理解第一个应用的运行流程**：从 `main.ts` 的 `bootstrap()` → `NestFactory.create()` → `app.listen()`，到 `AppModule` → `AppController` → `AppService` 的调用链。
8. **熟练使用 nest CLI 脚手架**：能用 `nest g resource/controller/service/module` 生成代码骨架，用 `nest start --watch` 启动热重载。

---

## 三、理论知识

### 3.1 NestJS 是什么

**定位**

NestJS 是一个**渐进式**的 Node.js 服务端框架，目标是提供「开箱即用的应用架构」。它不重新实现 HTTP 层，而是在 HTTP 适配器（Express/Fastify）之上构建一整套面向对象的组件模型：

```
┌─────────────────────────────────────────────┐
│              你的业务代码（Controller/Service）              │
├─────────────────────────────────────────────┤
│  NestJS 核心：DI 容器 / 模块系统 / 装饰器 / 生命周期钩子       │
├─────────────────────────────────────────────┤
│  HTTP 适配器：@nestjs/platform-express 或 platform-fastify    │
├─────────────────────────────────────────────┤
│      Express（默认）              Fastify（可选）              │
└─────────────────────────────────────────────┘
```

**设计哲学：借鉴 Angular**

NestJS 几乎把 Angular 的核心思想搬到了后端：

| 概念 | Angular | NestJS |
| --- | --- | --- |
| 模块 | `@NgModule` | `@Module` |
| 依赖注入 | `Injector`、`Provider` | 同名概念，几乎一致 |
| 装饰器风格 | `@Component`、`@Injectable` | `@Controller`、`@Injectable` |
| 动态模块 | `forRoot` | `forRoot` / `forRootAsync` |
| 元数据反射 | `reflect-metadata` | 同样基于 `reflect-metadata` |

如果你写过 Angular，NestJS 几乎零学习成本；如果你没写过，NestJS 也是认识这套架构思想的最简入门路径——它比 Angular 简单，又比 Express 完整。

**与 Express / Koa 的关系**

NestJS **不是** Express 的竞品，而是它的「架构外壳」：

- Express / Koa 提供 HTTP 抽象与中间件管线，但不规定如何组织代码。
- NestJS 默认使用 `@nestjs/platform-express`，把 Express 实例封装在内部；你也可以一行命令切到 Fastify（性能更好，但生态略小）换取 2-3 倍的吞吐。
- 几乎所有 Express 中间件（如 `helmet`、`compression`、`morgan`）都能在 NestJS 中通过 `app.use()` 直接复用。

一句话：**Express 是引擎，NestJS 是底盘 + 车身 + 仪表盘**。

### 3.2 为什么选择 NestJS

| 优势 | 说明 |
| --- | --- |
| **开箱即用的架构** | 项目脚手架自带 Controller/Service/Module 分层、单元测试骨架、ESLint + Prettier 配置，无需自行约定目录结构。新人接手项目第一天就能找到「这个接口在哪」。 |
| **TypeScript 原生支持** | NestJS 源码本身就是 TS 编写，所有 API 都有精确类型；不需要 `@types/*` 补丁，DTO、Entity、Service 全链路类型安全。 |
| **装饰器与依赖注入** | `@Injectable()` 标注的 Service 自动由 IoC 容器管理，构造函数声明依赖即可注入。手动 `new` 与单例管理彻底消失。 |
| **模块化** | `@Module()` 把相关 Controller/Provider 聚合，`imports`/`exports` 控制可见性，天然支持特性模块、共享模块、全局模块。 |
| **生态丰富** | 官方维护 30+ 模块：`@nestjs/typeorm`、`@nestjs/mongoose`、`@nestjs/jwt`、`@nestjs/passport`、`@nestjs/swagger`、`@nestjs/schedule`、`@nestjs/microservices`、`@nestjs/graphql`、`@nestjs/bull`……开箱即用，风格统一。 |
| **企业级特性** | 内置异常体系、统一响应拦截、配置管理、日志抽象、健康检查（`@nestjs/terminus`）、命令行代码生成（`nest g`）、E2E 测试支持，直接对标 Spring Boot。 |
| **可替换的 HTTP 引擎** | Express 与 Fastify 双适配器，业务代码无需改动，仅 `main.ts` 改一行即可切换。 |

### 3.3 NestJS 与 Express 的对比

| 维度 | Express | NestJS |
| --- | --- | --- |
| **架构** | 无内置架构，自由拼装中间件 | 强约束架构：Module / Controller / Service / Provider 分层 |
| **类型支持** | 需 `@types/express`，类型弱 | 原生 TS，全链路类型安全 |
| **中间件** | `app.use(fn)`，函数式 | 函数式 + 类中间件（`@Injectable` + `NestModule.configure`），可注入依赖 |
| **依赖注入** | 无，需手动 `new` 或自建容器 | 内置 IoC 容器，构造函数注入 |
| **路由** | `app.get('/x', handler)` 命令式 | `@Controller('x')` + `@Get()` 装饰器声明式 |
| **错误处理** | 中间件兜底，自行约定 | 内置异常体系（`HttpException`）+ `@Catch()` 过滤器 |
| **工具链** | 无官方 CLI | `@nestjs/cli`：项目脚手架、代码生成、热重载、构建、迁移 |
| **学习曲线** | 平缓（30 分钟跑通） | 较陡（需理解 DI / 装饰器 / 模块），但上手后开发效率高 |
| **生态** | 中间件海量但风格不一 | 官方模块统一风格，社区 `awesome-nestjs` 整理 |
| **适合场景** | 小项目、原型、中间件二次开发 | 中大型后端、企业应用、AI 应用 BFF、微服务 |

一句话总结：**Express 是工具箱，NestJS 是工程流水线**。小项目用 Express 灵活，中大型项目用 NestJS 省心。

### 3.4 核心概念总览

NestJS 由八大核心组件构成，本章只做一句话总览，详细机制在 Day02-Day10 逐个展开。

| 组件 | 一句话职责 | 详解天数 |
| --- | --- | --- |
| **Module 模块** | 用 `@Module()` 聚合一组 Controller/Provider，是组织代码的边界，`exports` 决定对外可见性 | Day04 |
| **Controller 控制器** | 用 `@Controller()` 声明，负责接收 HTTP 请求、调用 Service、返回响应，**不写业务逻辑** | Day02 |
| **Provider 提供者** | 用 `@Injectable()` 声明，可被注入的任何东西（Service / Repository / Config / Value），是 DI 的基本单元 | Day03 |
| **Middleware 中间件** | 在路由处理前执行的函数，能修改 `req`/`res`、终止请求，与 Express 中间件语义一致 | Day06 |
| **Guard 守卫** | 负责授权决策（能否访问），返回 `boolean`，`false` 则请求被拒，是 RBAC 的落地点 | Day08 |
| **Pipe 管道** | 作用于参数，做数据转换（如 `string → number`）或数据校验（如 DTO 校验） | Day07 |
| **Interceptor 拦截器** | AOP 切面，包裹方法前后逻辑（日志、缓存、响应转换、超时），基于 RxJS `Observable` | Day09 |
| **ExceptionFilter 异常过滤器** | 捕获未处理异常，统一错误响应格式，是异常的最后一道防线 | Day10 |

> 这八个组件都是**类**，都通过装饰器声明，都能被 DI 容器注入——这就是 NestJS「一切皆 Provider」的统一性。

### 3.5 请求生命周期概览

理解请求生命周期是理解 NestJS 的钥匙。一次 HTTP 请求从进入到响应返回，会按以下顺序穿过各组件：

```
请求进入
   │
   ▼
① 中间件 Middleware（Day06）         ← 能修改 req/res、可终止请求
   │
   ▼
② 守卫 Guard（Day08）                 ← 授权决策，返回 false 直接 403
   │
   ▼
③ 拦截器（前置）Interceptor（Day09）  ← AOP 前置逻辑，如开始计时
   │
   ▼
④ 管道 Pipe（Day07）                  ← 参数级校验与转换
   │
   ▼
⑤ 控制器方法 Handler                 ← 业务逻辑（调用 Service）
   │
   ▼
⑥ 拦截器（后置）Interceptor（Day09）  ← AOP 后置逻辑，包装响应
   │
   ▼
⑦ 异常过滤器 ExceptionFilter（Day10） ← 仅当上述任一环节抛异常时触发
   │
   ▼
响应返回
```

关键记忆点：

- **中间件最早**：在路由匹配后、守卫之前。
- **守卫早于拦截器**：先判断「能不能进」，再决定要不要包裹逻辑。
- **拦截器包裹管道与控制器**：`before` 在管道前，`after` 在控制器返回后。
- **管道只处理参数**：不包裹方法，不做 AOP。
- **过滤器最后兜底**：任何环节抛出异常都会被它捕获。

> Day06-Day10 会逐个深入每个组件的实现细节与执行顺序验证。

---

## 四、环境搭建

### 4.1 前置条件：Node.js 与 TypeScript 检查

NestJS 10+ 要求 Node.js 16+，推荐 18 LTS 或更高。同时你应当已完成 TypeScript 板块（至少 Day01-Day09），熟悉装饰器、类、泛型。

```bash
# 检查 Node.js 版本（需 18+）
node -v
# v18.x 或更高

# 检查 npm 版本
npm -v
# 9.x 或更高

# 检查 TypeScript 全局是否可用（可选，项目内会自带）
tsc --version
# Version 5.x.x
```

> 本章 `Code/` 目录已自带 `typescript`、`@nestjs/cli` 等 devDependencies，无需全局安装 TS 即可运行。

### 4.2 全局安装 @nestjs/cli

`@nestjs/cli` 是 NestJS 官方命令行工具，提供项目脚手架、代码生成、热重载、构建等能力：

```bash
npm install -g @nestjs/cli

# 验证
nest --version
# 10.x.x

# 查看所有命令
nest --help
```

> 也可以不全局安装，直接用 `npx @nestjs/cli new project-name`，但全局安装后日常使用更顺手。

### 4.3 用 nest new 创建项目

```bash
nest new my-nest-app
```

CLI 会依次询问三个选项：

| 选项 | 说明 | 推荐 |
| --- | --- | --- |
| **package manager** | 选 `npm` / `yarn` / `pnpm`，决定后续 `npm install` / `yarn` / `pnpm install` 的工具 | `npm`（最通用）或 `pnpm`（更快、磁盘省） |
| **git** | 是否初始化 git 仓库（生成 `.git/` 与初始 commit） | `Yes` |
| **strict mode** | 是否启用 TS `strict: true`（同时 `noImplicitAny`、`strictNullChecks` 等全部开启） | `Yes`（新项目必开） |

也可以用命令行参数跳过交互：

```bash
nest new my-nest-app --package-manager npm --skip-git --strict
```

执行完成后会生成如下结构：

```
my-nest-app/
├── src/
│   ├── app.controller.ts
│   ├── app.controller.spec.ts
│   ├── app.module.ts
│   ├── app.service.ts
│   └── main.ts
├── test/
│   ├── app.e2e-spec.ts
│   └── jest-e2e.json
├── .eslintrc.js
├── .gitignore
├── .prettierrc
├── nest-cli.json
├── package.json
├── package-lock.json
├── README.md
├── tsconfig.json
└── tsconfig.build.json
```

### 4.4 项目结构详解

| 路径 | 作用 |
| --- | --- |
| `src/` | 源码目录，所有业务代码都在这里。入口是 `main.ts` |
| `src/main.ts` | 应用入口，`bootstrap()` 函数创建应用并监听端口 |
| `src/app.module.ts` | 根模块，组装整个应用的 Controller 与 Provider |
| `src/app.controller.ts` | 根控制器，演示最小路由 |
| `src/app.service.ts` | 根服务，演示 `@Injectable` 与构造函数注入 |
| `src/app.controller.spec.ts` | 控制器单元测试示例（Jest） |
| `test/` | E2E 测试目录，使用 `supertest` 启动真实应用并发请求 |
| `package.json` | 依赖与脚本（`start` / `start:dev` / `start:debug` / `build` / `lint` / `test`） |
| `tsconfig.json` | TypeScript 编译配置（开发期，含 `strict`、装饰器开关） |
| `tsconfig.build.json` | 构建期配置，继承 `tsconfig.json` 并排除测试文件 |
| `nest-cli.json` | NestJS CLI 配置（源码根、入口、编译选项、生成器选项） |
| `.eslintrc.js` | ESLint 配置，含 `@typescript-eslint` 规则集 |
| `.prettierrc` | Prettier 格式化规则 |

> 本章 `Code/` 目录是一份精简骨架，保留了 `src/` 与四个配置文件，去掉 `test/` 与 lint 配置以聚焦核心。运行方式与官方脚手架完全一致。

---

## 五、第一个 NestJS 应用

下面逐文件讲解第一个 NestJS 应用的运行流程。所有文件位于 `Code/src/`。

### 5.1 main.ts —— 启动入口

```typescript
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  // 1. NestFactory.create 接收一个根模块，返回应用实例
  //    底层会调用 platform-express 创建 Express app 并装配 DI 容器
  const app = await NestFactory.create(AppModule);

  // 2. 全局前缀：所有路由自动加上 /api 前缀
  //    例如 @Get('users') 实际路径是 /api/users
  //    便于前端统一代理、与静态资源分流
  app.setGlobalPrefix('api');

  // 3. CORS：跨域资源共享，前端分离开发必备
  //    生产环境应配置具体的 origin 白名单而非 true
  app.enableCors();

  // 4. 全局 ValidationPipe：自动用 class-validator 校验 DTO
  //    后续 Day07 会详细讲解，这里先注册为后续铺垫
  //    启用后所有 @Body() 参数会自动按 DTO 类的装饰器校验
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,        // 自动剔除 DTO 上未声明的属性
      forbidNonWhitelisted: true, // 出现未声明属性直接报错
      transform: true,        // 自动把普通对象转为 DTO 类实例
    }),
  );

  // 5. 监听端口
  await app.listen(3000);
}
bootstrap();
```

**核心 API**：

- `NestFactory.create(AppModule)`：以根模块为入口创建应用。底层会实例化所有 Provider、解析模块依赖图、装配 DI 容器。
- `app.setGlobalPrefix('api')`：所有路由加 `/api` 前缀。
- `app.enableCors()`：启用 CORS（跨域）。
- `app.useGlobalPipes(new ValidationPipe(...))`：注册全局校验管道。
- `app.listen(3000)`：监听端口，启动 HTTP 服务。

### 5.2 app.module.ts —— 根模块

```typescript
import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';

@Module({
  imports: [],            // 引入其他模块（当前应用最简，无外部模块）
  controllers: [AppController],  // 注册控制器
  providers: [AppService],       // 注册 Provider（Service/Repository/Value/Factory）
})
export class AppModule {}
```

**`@Module()` 装饰器**接收一个对象，四个核心字段：

| 字段 | 作用 |
| --- | --- |
| `imports` | 引入其他模块，获取它们 `exports` 出的 Provider |
| `controllers` | 注册本模块的控制器，NestJS 会自动实例化并绑定路由 |
| `providers` | 注册本模块的 Provider，由 DI 容器管理 |
| `exports` | 把本模块的 Provider 暴露给其他模块使用 |

`AppModule` 是**根模块**，整个应用只有一个根模块，被 `main.ts` 的 `NestFactory.create()` 直接消费。所有特性模块（如 `UserModule`、`ArticleModule`）通过 `imports` 挂载到根模块上，形成模块树。

### 5.3 app.controller.ts —— 根控制器

```typescript
import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';

@Controller()            // 类装饰器：声明这是一个控制器，可加路由前缀如 @Controller('users')
export class AppController {
  // 构造函数注入：DI 容器看到 AppService 类型参数，自动注入实例
  constructor(private readonly appService: AppService) {}

  @Get()                 // 方法装饰器：声明 GET 路由，路径默认为控制器前缀
  getHello(): string {
    return this.appService.getHello();   // 调用 Service，控制器不做业务逻辑
  }
}
```

**两个关键装饰器**：

- `@Controller(prefix?)`：标记类为控制器，`prefix` 是该控制器下所有路由的公共前缀。例如 `@Controller('users')` + `@Get('me')` 对应 `GET /users/me`。
- `@Get(path?)` / `@Post()` / `@Put()` / `@Delete()` / `@Patch()`：声明 HTTP 方法路由。

**构造函数注入**：`constructor(private readonly appService: AppService)` 是 NestJS 最常见的注入方式。TS 的参数属性语法（`private readonly` 修饰符）会自动声明并赋值类属性，配合 `emitDecoratorMetadata` 让 DI 容器能从元数据读到「需要 `AppService` 类型」。

### 5.4 app.service.ts —— 根服务

```typescript
import { Injectable } from '@nestjs/common';

@Injectable()            // 标记为可注入：DI 容器会管理它的实例化与生命周期
export class AppService {
  getHello(): string {
    return 'Hello NestJS! Welcome to Day01.';
  }
}
```

**`@Injectable()` 装饰器**告诉 NestJS：这个类可以被 DI 容器实例化并注入到其他类中。任何想被注入的类（Service、Repository、Guard、Pipe、Interceptor、Filter、Middleware）都要加这个装饰器。

**Service 的职责**：承载业务逻辑。Controller 只做请求响应映射，所有数据访问、计算、外部调用都下沉到 Service。这种分层让 Service 可被多个 Controller 复用，也便于单元测试。

### 5.5 启动并访问

```bash
cd "Day01 - NestJS简介与项目搭建/Code"
npm install              # 安装依赖（首次）
npm run start            # 启动生产模式（编译后运行）

# 或开发模式（热重载）
npm run start:dev
```

看到 `Nest application successfully started` 后，访问：

```bash
# 全局前缀是 /api，控制器无前缀，路由为空
curl http://localhost:3000/api
# Hello NestJS! Welcome to Day01.

# 浏览器打开
open http://localhost:3000/api
```

> 如果去掉 `app.setGlobalPrefix('api')`，访问 `http://localhost:3000/` 即可。

---

## 六、nest CLI 常用命令

`nest` CLI 是日常开发的瑞士军刀，能生成代码骨架、启动服务、构建产物。

### 6.1 项目级命令

```bash
nest new <project-name>           # 创建新项目
nest new my-app --strict          # 启用 TS strict 模式
nest new my-app --package-manager pnpm   # 指定包管理器
nest new my-app --skip-git        # 不初始化 git
```

### 6.2 代码生成命令

`nest generate <schematic> <name>`（简写 `nest g <schematic> <name>`）按 NestJS 约定生成文件并自动注册到对应模块。

| 命令 | 生成内容 | 文件路径 |
| --- | --- | --- |
| `nest g resource articles` | **完整资源**：Controller + Service + Module + DTO + Entity + 测试 | `src/articles/` |
| `nest g controller users` | 控制器类 + 单元测试 | `src/users/users.controller.ts` |
| `nest g service users` | Service 类 + 单元测试 | `src/users/users.service.ts` |
| `nest g module users` | 模块类（自动注册到上层模块 `imports`） | `src/users/users.module.ts` |
| `nest g guard auth` | 守卫类 | `src/auth/auth.guard.ts` |
| `nest g pipe validation` | 管道类 | `src/validation/validation.pipe.ts` |
| `nest g interceptor logging` | 拦截器类 | `src/logging/logging.interceptor.ts` |
| `nest g filter http-exception` | 异常过滤器类 | `src/http-exception/http-exception.filter.ts` |
| `nest g middleware logger` | 中间件类 | `src/logger/logger.middleware.ts` |
| `nest g decorator roles` | 自定义装饰器 | `src/roles/roles.decorator.ts` |

`nest g resource <name>` 是最常用的命令，一行生成完整 CRUD 脚手架（含 RESTful 路由、DTO、Service、模块注册），适合快速搭建业务模块。

### 6.3 启动与构建命令

```bash
nest start                  # 编译并启动（默认执行 dist/main.js）
nest start --watch           # 热重载：文件变更自动重启（开发最常用）
nest start --debug           # 调试模式，启动 --inspect 等待调试器
nest build                   # 编译到 dist/
```

也可以用 npm 脚本（脚手架默认生成）：

```bash
npm run start                # = nest start
npm run start:dev            # = nest start --watch
npm run start:debug          # = nest start --debug --watch
npm run build                # = nest build
npm run lint                 # = eslint "{src,apps,libs,test}/**/*.ts"
npm run test                 # = jest
npm run test:e2e             # = jest --config ./test/jest-e2e.json
```

> 本章 `Code/package.json` 已配置好上述脚本，进入 `Code/` 目录即可使用。

---

## 七、tsconfig 与 nest-cli.json 配置说明

### 7.1 tsconfig.json —— TypeScript 编译配置

NestJS 项目对 `tsconfig.json` 有几个**必须开启**的选项，缺一不可：

```jsonc
{
  "compilerOptions": {
    "module": "commonjs",                 // Node 项目用 CommonJS
    "declaration": true,                  // 生成 .d.ts，便于库发布
    "removeComments": true,               // 移除注释
    "emitDecoratorMetadata": true,        // 关键！DI 容器靠它读取参数类型
    "experimentalDecorators": true,       // 关键！启用装饰器语法
    "allowSyntheticDefaultImports": true, // 允许 import x from 'cjs'
    "target": "ES2021",                   // 编译目标 JS 版本（Node 16+ 推荐 ES2021）
    "sourceMap": true,                    // 生成 source map，便于调试
    "outDir": "./dist",                   // 编译产物输出目录
    "baseUrl": "./",                      // 模块解析基准
    "incremental": true,                  // 增量编译，加快速度
    "skipLibCheck": true,                 // 跳过 .d.ts 检查
    "strictNullChecks": true,             // 严格 null 检查
    "noImplicitAny": true,                // 禁止隐式 any
    "strictBindCallApply": true,          // 严格 bind/call/apply
    "forceConsistentCasingInFileNames": true, // 强制文件名大小写一致
    "noFallthroughCasesInSwitch": true    // switch 必须有 break/return
  }
}
```

**两个对 NestJS 至关重要的选项**：

- `experimentalDecorators: true`：启用 TS 装饰器语法（TC39 标准装饰器暂未完全替代实验性装饰器，NestJS 仍依赖实验性版本）。
- `emitDecoratorMetadata: true`：让 TS 在编译时把类型信息写入元数据。DI 容器正是通过 `Reflect.getMetadata('design:paramtypes', AppController)` 读到「构造函数参数是 `[AppService]`」，从而知道要注入什么。如果关掉它，构造函数注入会直接报错。

> 这两个选项对应 TS Day09 装饰器章节的 `reflect-metadata` 实验，本章 `Code/tsconfig.json` 已开启。

### 7.2 tsconfig.build.json —— 构建配置

```json
{
  "extends": "./tsconfig.json",        // 继承开发配置
  "exclude": ["node_modules", "test", "dist", "**/*spec.ts"]  // 排除测试文件
}
```

构建产物不需要包含测试文件，`tsconfig.build.json` 通过 `exclude` 排除 `*.spec.ts` 与 `test/` 目录。`nest build` 命令默认使用此配置。

### 7.3 nest-cli.json —— NestJS CLI 配置

```json
{
  "$schema": "https://json.schemastore.org/nest-cli",
  "collection": "@nestjs/schematics",
  "sourceRoot": "src",
  "compilerOptions": {
    "deleteOutDir": true
  }
}
```

| 字段 | 作用 |
| --- | --- |
| `$schema` | JSON Schema，让 IDE 智能提示配置项 |
| `collection` | 代码生成器使用的 schematic 集合，`@nestjs/schematics` 是官方集合 |
| `sourceRoot` | 源码根目录，CLI 在此目录扫描文件变化 |
| `compilerOptions.deleteOutDir` | 构建前删除 `dist/`，避免残留旧产物 |

`nest-cli.json` 还可以配置 monorepo、多应用、webpack/tsc 编译器切换、生成器默认行为等。本章使用最简配置，Day12 配置管理会再深入。

---

## 八、与 TypeScript 板块的衔接

NestJS 是 TypeScript 板块的**集大成者**。如果你按本系列顺序学完 TS 板块再来看 NestJS，会发现几乎每个核心概念都能在 TS 板块找到原型：

### 8.1 装饰器（TS Day09）

NestJS 的一切都基于装饰器。回顾 TS Day09 学到的四类装饰器：

| TS Day09 概念 | NestJS 中的对应 |
| --- | --- |
| 类装饰器 `function Log(target)` | `@Controller()`、`@Module()`、`@Injectable()`、`@Global()` 都是类装饰器工厂 |
| 方法装饰器 `(target, key, desc)` | `@Get()`、`@Post()`、`@UseGuards()`、`@HttpCode()` |
| 属性装饰器 `(target, key)` | `@Inject()` 属性注入 |
| 参数装饰器 `(target, key, idx)` | `@Param()`、`@Query()`、`@Body()`、`@Headers()` |
| `reflect-metadata` | DI 容器读取 `design:paramtypes` 元数据决定注入什么 |
| `mini-controller.ts` 实验 | NestJS 控制器就是这个实验的工业级版本 |
| `mini-di-container.ts` 实验 | NestJS IoC 容器就是这个实验的完整实现 |

如果你在 TS Day09 的 `mini-di-container.ts` 里手动实现过简易 IoC，那 NestJS 的 `@Injectable` + 构造函数注入对你来说一点都不神秘——只是把「手写容器」换成了「框架内置容器」。

### 8.2 类与面向对象（TS Day06）

NestJS 的所有组件都是**类**：

- `AppController` 是类，构造函数注入 `AppService`（TS Day06 的「参数属性」语法 `private readonly appService: AppService`）。
- Service 通常用 `public`/`private` 控制可见性（TS Day06 的访问修饰符）。
- 抽象基类与接口在 NestJS 中常用于定义 Repository 契约、Guard 通用逻辑（TS Day06 的 `abstract class`、`implements`）。
- 泛型 Repository 模式 `Repository<T>` 在 TypeORM 集成中大量使用（TS Day06 的 `generic-class.ts`）。

### 8.3 泛型（TS Day04）

NestJS 中泛型无处不在：

- `NestInterceptor<T, R>`：拦截器接口，`T` 是响应类型，`R` 是转换后类型。
- `Repository<T>`：TypeORM 的实体仓储。
- `ExecutionContext` 切换到 HTTP/RPC/GQL 时返回不同类型（`switchToHttp()` 返回 `HttpContext`）。
- 自定义 `BaseService<T>` 抽象公共 CRUD 逻辑，子类指定实体类型。

```typescript
// 泛型在 NestJS 中的典型用法（后续 Day 会展开）
abstract class BaseService<T> {
  abstract findAll(): Promise<T[]>;
  abstract findOne(id: string): Promise<T>;
}
```

### 8.4 其他 TS 板块衔接

- **Day01 类型系统**：NestJS 的 DTO、Entity 都是 `interface` / `class`，依赖 `strict` 模式。
- **Day02 基础类型**：参数装饰器的返回类型（`@Param() id: string`）。
- **Day03 接口**：`CanActivate`、`NestInterceptor`、`ExceptionFilter`、`NestMiddleware` 都是接口。
- **Day05 联合类型**：`HttpStatus` 枚举与字面量联合、`Scope` 枚举。
- **Day08 工具类型**：`Partial<T>`、`Pick<T,K>`、`Omit<T,K>` 在 DTO 继承中常用。
- **Day09 reflect-metadata**：DI 容器的元数据反射原理。
- **Day14 TS + Node**：`@types/node`、CommonJS 模块解析。
- **Day15 TS + Express**：NestJS 默认基于 Express，`@Req()` / `@Res()` 装饰器返回的就是 Express 的 `Request` / `Response`。

> 一句话：**TS 板块是地基，NestJS 是地基上的精装房**。地基越扎实，精装房住得越舒服。

---

## 九、关键知识点总结

- **NestJS 是基于 TS 的 Node.js 后端框架**：融合 OOP / FP / FRP 三种范式，装饰器驱动，依赖注入是灵魂。
- **设计哲学借鉴 Angular**：模块、DI、装饰器、动态模块（`forRoot`）几乎一脉相承，但比 Angular 简单。
- **与 Express 的关系**：NestJS 不是 Express 的竞品，而是它的「架构外壳」。默认基于 Express，可一键切到 Fastify。一句话：**Express 是引擎，NestJS 是底盘 + 车身 + 仪表盘**。
- **八大核心组件**：Module / Controller / Provider / Middleware / Guard / Pipe / Interceptor / ExceptionFilter，都是类，都通过装饰器声明，都能被 DI 注入。
- **请求生命周期**：中间件 → 守卫 → 拦截器（前）→ 管道 → 控制器 → 拦截器（后）→ 异常过滤器 → 响应。
- **环境搭建**：Node 18+ → `npm i -g @nestjs/cli` → `nest new` → `npm run start:dev`。
- **项目结构**：`src/`（业务）+ `test/`（E2E）+ 四个配置文件（`package.json`、`tsconfig.json`、`tsconfig.build.json`、`nest-cli.json`）。
- **入口流程**：`main.ts` 的 `bootstrap()` 调用 `NestFactory.create(AppModule)` 创建应用，`app.listen(3000)` 监听端口。
- **核心装饰器**：`@Module()`、`@Controller()`、`@Injectable()`、`@Get()` 等都是声明式 API，配合 `reflect-metadata` 实现 DI。
- **tsconfig 两个必开项**：`experimentalDecorators` 与 `emitDecoratorMetadata`，缺一不可。
- **nest CLI 是开发瑞士军刀**：`nest new` 建项目、`nest g resource` 生成 CRUD 骨架、`nest start --watch` 热重载。
- **与 TS 板块的衔接**：TS Day09 装饰器是 NestJS 的直接基础、Day06 类是组件的载体、Day04 泛型在拦截器与 Repository 中无处不在。

---

## 十、实战练习

以下三个练习建议按顺序完成。所有代码基于 `Code/` 目录，运行方式见第五节。

### 练习一：扩展根控制器，新增 `/api/health` 健康检查路由

**任务描述**

1. 在 `AppController` 中新增一个 `getHealth()` 方法，用 `@Get('health')` 装饰。
2. 在 `AppService` 中新增 `getHealth()` 方法，返回一个对象 `{ status: 'ok', uptime: <秒>, timestamp: <ISO 字符串> }`。
   - `uptime` 用 `process.uptime()` 取秒数（`Math.floor`）。
   - `timestamp` 用 `new Date().toISOString()`。
3. 启动服务，访问 `http://localhost:3000/api/health`，应返回类似：

   ```json
   {
     "status": "ok",
     "uptime": 12,
     "timestamp": "2025-01-01T08:00:00.000Z"
   }
   ```

**验证**

```bash
curl http://localhost:3000/api/health
```

**思考题**：NestJS 会自动把返回的对象序列化为 JSON，无需 `JSON.stringify`。这与你写过的 Express 有何不同？

### 练习二：拆分模块，新建 `HealthModule`

**任务描述**

1. 用 `nest g module health` 生成 `HealthModule`（或手动创建文件）。
2. 把练习一中的健康检查逻辑迁移到 `HealthController` 与 `HealthService`（位于 `src/health/` 目录）。
3. 在 `AppModule` 的 `imports` 中注册 `HealthModule`。
4. 路由保持 `GET /api/health`，验证迁移后行为不变。

**验证**

```bash
curl http://localhost:3000/api/health   # 仍然返回健康检查 JSON
curl http://localhost:3000/api          # 仍然返回 Hello NestJS
```

**思考题**：`HealthModule` 没有 `exports`，`AppModule` 还能用 `HealthService` 吗？为什么？

### 练习三：用 `nest g resource` 生成 CRUD 资源并跑通

**任务描述**

1. 在 `Code/` 目录执行：

   ```bash
   nest g resource articles
   ```

   选择 `REST API` 传输层。

2. 观察生成的 `src/articles/` 目录结构，找到 Controller / Service / Module / DTO。
3. 启动服务，用 `curl` 测试 CRUD 接口：

   ```bash
   curl -X POST http://localhost:3000/api/articles \
        -H "Content-Type: application/json" \
        -d '{"title":"Hello","content":"First article"}'

   curl http://localhost:3000/api/articles
   ```

4. 观察 `ValidationPipe` 是否生效：故意多发一个未声明的字段（如 `"foo":"bar"`），应收到 400 错误。

**验证**

- `GET /api/articles` 返回空数组或模拟数据。
- `POST /api/articles` 带未声明字段返回 400，带正确字段返回 201。

**思考题**：`nest g resource` 生成的 Service 数据存储在哪里？是真实数据库还是内存？为什么 Day01 不直接接数据库？

---

## 下节预告

下一节 **Day02** 将进入 **控制器与路由系统**：`@Controller` 路由前缀、`@Get/@Post/@Put/@Delete/@Patch` 方法装饰器、`@Param` 路径参数、`@Query` 查询参数、`@Body` 请求体、`@Headers` 请求头、`@HttpCode` 状态码、路由通配符与子路由。我们将把本章的「Hello」应用扩展成一个真正能接收多种参数的 RESTful 控制器。
