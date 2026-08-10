# NestJS 全栈学习指南

> 系统化掌握 NestJS 框架，从装饰器到依赖注入、从控制器到微服务，构建生产级后端架构能力
>
> 共 15 天，覆盖 NestJS 全部核心机制与工程化实战

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

本板块是 AI 全栈学习系列的**后端架构核心**。NestJS 是基于 TypeScript 的 Node.js 服务端框架，融合了 OOP（面向对象）、FP（函数式）、FRP（响应式编程）三种范式，深度依赖装饰器与依赖注入，与 Spring Boot / Angular 的设计哲学一脉相承。

NestJS 既是 Express 的进阶形态，也是构建 AI 应用后端（LangChain.js 服务化、Agent 编排、RAG 检索服务、向量数据库访问层）的工业级框架。

**学习目标**：完成本板块后，你应能：
- 理解 NestJS 的依赖注入机制与模块化架构，能设计可扩展的服务层
- 熟练运用控制器、提供者、中间件、守卫、管道、拦截器、异常过滤器七大核心组件
- 集成 TypeORM/Prisma 实现类型安全的数据库访问
- 实现 JWT 认证、RBAC 权限控制、Swagger 文档自动生成
- 掌握配置管理、日志体系、文件上传、定时任务等生产实践

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 代码示例 + 实战练习
- 紧扣 TypeScript 板块的知识衔接（装饰器 Day09、类 Day06、泛型 Day04）
- 所有代码可在 Node 18+ 与 NestJS 10+ 环境运行
- 每天开头直接进入章节简介，不做多余定位

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| TypeScript | 熟练 | 装饰器、类、泛型、工具类型（必须完成 TS 板块） |
| Node.js | 熟练 | 异步编程、模块系统、HTTP、Express（必须完成 NodeJS 板块） |
| Express | 熟练 | 中间件、路由、请求响应周期（NodeJS 板块 Day10-14） |
| RESTful API | 熟悉 | HTTP 方法语义、状态码、URI 设计 |
| 数据库基础 | 了解 | SQL 基础、ORM 概念（Day13 需要） |

**环境准备**：
- Node.js 18 LTS 或更高
- NestJS CLI：`npm i -g @nestjs/cli`
- TypeScript 5.0+
- VS Code（推荐 Volar / ESLint / Prettier 扩展）
- 可选：本地 MySQL 8+ 或 Docker（Day13、Day14 需要）

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                   NestJS 全栈学习路线（15天）                     │
└─────────────────────────────────────────────────────────────────┘

阶段一：核心基础（Day01-Day05）
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  Day01 简介  │  Day02 控制器│  Day03 提供者│  Day04 模块  │  Day05 依赖  │
│  与搭建      │  与路由      │  与服务      │  系统        │  注入深入    │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │              │
       ▼              ▼              ▼              ▼              ▼
阶段二：请求处理链路（Day06-Day10）
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  Day06 中间件│  Day07 管道  │  Day08 守卫  │  Day09 拦截  │  Day10 异常  │
│  机制        │  与校验      │  与权限       │  器          │  过滤器      │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │              │
       ▼              ▼              ▼              ▼              ▼
阶段三：数据与文档（Day11-Day13）
┌──────────────────────┬──────────────────────┬──────────────────────┐
│  Day11 DTO 与 Swagger │  Day12 配置管理      │  Day13 数据库集成     │
│  文档自动生成         │  与环境变量          │  TypeORM 与 Prisma    │
└──────────┬───────────┴──────────┬───────────┴──────────┬───────────┘
           │                      │                      │
           ▼                      ▼                      ▼
阶段四：认证授权（Day14）
┌──────────────────────────────────────────────────────┐
│  Day14 JWT 认证与 RBAC 权限模型                       │
│  （Passport / 策略 / 角色 / 装饰器配合 Guard）        │
└──────────────────────────────────────────────────────┘
           │
           ▼
阶段五：生产实践（Day15）
┌──────────────────────────────────────────────────────┐
│  Day15 日志体系、文件上传、定时任务与生产部署          │
│  （Logger / Multer / Schedule / Docker / 测试）       │
└──────────────────────────────────────────────────────┘
```

---

## 每日内容详表

### 阶段一：核心基础

#### Day01 - NestJS简介与项目搭建
- **核心**：NestJS 定位与设计哲学、与 Express/Koa 的差异、装饰器驱动架构、nest CLI、项目结构、main.ts 启动流程、tsconfig 与 nest-cli.json
- **代码**：`hello-nest/` 项目骨架、`main.ts`、`app.module.ts`、`app.controller.ts`、`app.service.ts`
- **重点**：NestJS 是 TS 板块 Day09 装饰器的集大成者

#### Day02 - 控制器与路由系统
- **核心**：`@Controller`、`@Get/@Post/@Put/@Delete/@Patch`、路由参数 `@Param`、查询参数 `@Query`、请求体 `@Body`、请求头 `@Headers`、`@Req/@Res`、状态码 `@HttpCode`、路由通配符、子路由
- **代码**：`articles.controller.ts`、`users.controller.ts`、路由参数演示
- **重点**：控制器只做路由与请求响应映射，业务逻辑下沉到 Service

#### Day03 - 提供者与服务
- **核心**：Provider 概念、`@Injectable` 装饰器、Service 模式、值提供者 `useValue`、类提供者 `useClass`、工厂提供者 `useFactory`、别名提供者、`@Inject` 装饰器
- **代码**：`articles.service.ts`、`logger.provider.ts`、`config.factory.ts`
- **重点**：Provider 是 DI 的基本单元，理解 Token 是关键

#### Day04 - 模块系统
- **核心**：`@Module` 装饰器、`imports/exports/providers/controllers`、根模块 AppModule、特性模块 FeatureModule、共享模块 Shared Module、全局模块 `@Global`、动态模块 `forRoot/forRootAsync`
- **代码**：`app.module.ts`、`articles.module.ts`、`database.module.ts`
- **重点**：模块是组织代码的边界，exports 决定可见性

#### Day05 - 依赖注入深入
- **核心**：IoC 容器原理、DI 三种注入方式（构造函数/属性/参数）、作用域 `Scope.DEFAULT/REQUEST/TRANSIENT`、循环依赖 `forwardRef`、自定义 Provider Token、`useFactory` 异步初始化、基于 Class/Value/Symbol 的 Token
- **代码**：`di-demo/` 完整示例、`request-scoped.service.ts`、`forward-ref-demo.ts`
- **重点**：理解 DI 容器是 NestJS 的灵魂，为后续 Guard/Interceptor/Filter 的注入铺垫

---

### 阶段二：请求处理链路

#### Day06 - 中间件机制
- **核心**：NestJS 中间件 vs Express 中间件、`@Injectable` 中间件、`NestModule.configure`、应用级/路由级/方法级中间件、函数中间件 vs 类中间件、中间件执行顺序
- **代码**：`logger.middleware.ts`、`auth.middleware.ts`、`app.module.ts` configure
- **重点**：中间件在守卫/管道之前执行，能修改 req/res

#### Day07 - 管道与数据校验
- **核心**：Pipe 的作用（数据转换 + 数据校验）、`@UsePipes`、内置 Pipe（ValidationPipe/ParseIntPipe/ParseUUIDPipe/DefaultValuePipe）、参数级/方法级/全局级 Pipe、class-validator + class-transformer、自定义 Pipe
- **代码**：`validation.pipe.ts`、`create-article.dto.ts`、`parse-int.pipe.ts`
- **依赖**：class-validator、class-transformer
- **重点**：ValidationPipe + DTO 是类型安全请求体的标准方案

#### Day08 - 守卫与权限控制
- **核心**：Guard 的作用（授权而非认证）、`@Injectable` 实现 `CanActivate`、`ExecutionContext`、`@UseGuards`、全局 Guard、反射器 `Reflector`、自定义装饰器 `@SetMetadata`、`@Roles` 装饰器配合 RolesGuard
- **代码**：`auth.guard.ts`、`roles.guard.ts`、`roles.decorator.ts`、`public.decorator.ts`
- **重点**：Guard 是 RBAC 的落地点，为 Day14 JWT 认证铺垫

#### Day09 - 拦截器
- **核心**：Interceptor 的作用（AOP）、`NestInterceptor` 接口、`Observable/RxJS` 基础、`tap/map/catchError` 操作符、响应转换拦截器、缓存拦截器、超时拦截器、日志拦截器、执行顺序（Guard → Interceptor before → Pipe → Handler → Interceptor after）
- **代码**：`logging.interceptor.ts`、`transform.interceptor.ts`、`timeout.interceptor.ts`、`cache.interceptor.ts`
- **依赖**：rxjs
- **重点**：Interceptor 是 AOP 的核心，能包装响应/处理异常/记录耗时

#### Day10 - 异常过滤器
- **核心**：NestJS 异常体系、`HttpException` 及其子类、自定义异常、`@Catch` 装饰器、`ExceptionFilter` 接口、`@UseFilters`、全局过滤器、过滤器与拦截器的异常处理分工、统一响应错误格式
- **代码**：`http-exception.filter.ts`、`all-exceptions.filter.ts`、`business.exception.ts`、`error-response.dto.ts`
- **重点**：过滤器是异常的最后一道防线，统一错误响应格式

---

### 阶段三：数据与文档

#### Day11 - DTO与Swagger文档
- **核心**：DTO 模式、请求 DTO 与响应 DTO、`@nestjs/swagger`、`@ApiTags/@ApiOperation/@ApiResponse`、`@ApiProperty`、`ApiPropertyOptional`、Swagger UI 访问、DTO 复用与继承
- **代码**：`create-article.dto.ts`、`article.entity.ts`、`articles.controller.ts`（Swagger 装饰器）、`main.ts`（Swagger 配置）
- **依赖**：@nestjs/swagger
- **重点**：DTO 是请求/响应的契约，Swagger 让契约可见

#### Day12 - 配置管理与环境变量
- **核心**：`@nestjs/config`、`ConfigModule.forRoot`、`ConfigService`、环境变量加载、`.env` 文件、配置 Schema 校验（Joi）、命名空间配置、按环境配置、动态模块 `forRoot` 与 `forRootAsync`
- **代码**：`.env`、`config/schema.ts`、`app.module.ts`、`database.config.ts`
- **依赖**：@nestjs/config、joi（可选）
- **重点**：配置不硬编码，环境变量是 12-Factor App 的核心

#### Day13 - 数据库集成(TypeORM与Prisma)
- **核心**：
  - TypeORM：`@nestjs/typeorm`、`TypeOrmModule.forRoot/forFeature`、`@Entity`、`@Column`、`@PrimaryGeneratedColumn`、Repository 模式、关系映射（OneToOne/OneToMany/ManyToMany）、迁移 migrations
  - Prisma：`prisma` Client、`PrismaService` 封装、`prisma/schema.prisma`、类型安全查询、与 TypeORM 对比
- **代码**：`typeorm-demo/`、`prisma-demo/` 双方案对比
- **依赖**：@nestjs/typeorm、typeorm、@prisma/client
- **重点**：TypeORM 装饰器风格契合 NestJS，Prisma 类型推断更强

---

### 阶段四：认证授权

#### Day14 - JWT认证与RBAC权限
- **核心**：`@nestjs/jwt`、`@nestjs/passport`、JwtStrategy、本地策略 LocalStrategy（用户名密码登录）、JWT 签发与校验、`@UseGuards(JwtAuthGuard)`、`AuthGuard` 通用守卫、RBAC 模型（角色 + 权限）、`@Roles` 装饰器 + RolesGuard、密码哈希 bcrypt、Refresh Token 机制
- **代码**：`auth.module.ts`、`jwt.strategy.ts`、`local.strategy.ts`、`auth.service.ts`、`auth.controller.ts`、`roles.guard.ts`、`users.service.ts`
- **依赖**：@nestjs/jwt、@nestjs/passport、passport、passport-jwt、passport-local、bcrypt
- **重点**：Passport 策略模式是认证的标准方案

---

### 阶段五：生产实践

#### Day15 - 日志、文件上传与生产部署
- **核心**：
  - 日志：内置 `Logger` 类、自定义 Logger、winston 集成、按级别/按模块输出
  - 文件上传：`@nestjs/platform-express` + Multer、`@UploadedFile`、磁盘存储 vs 内存存储、文件校验
  - 定时任务：`@nestjs/schedule`、`@Cron`/`@Interval`/`@Timeout`
  - 队列速览：`@nestjs/bull`、Redis 任务队列（简介）
  - 部署：Dockerfile 多阶段构建、健康检查 `@nestjs/terminus`、压缩 helmet、生产配置
- **代码**：`logger/`、`upload.controller.ts`、`tasks.service.ts`、`Dockerfile`、`health.controller.ts`
- **依赖**：@nestjs/schedule、@nestjs/platform-express、multer、@nestjs/terminus
- **重点**：生产化是最后一公里，日志 + 健康检查 + 容器化必备

---

## 目录结构

```
NestJS/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - NestJS简介与项目搭建/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天代码示例
│       ├── package.json
│       ├── tsconfig.json
│       ├── nest-cli.json
│       └── src/
│           ├── main.ts
│           ├── app.module.ts
│           ├── app.controller.ts
│           └── app.service.ts
├── Day02 - 控制器与路由系统/
│   ├── README.md
│   └── Code/
│       └── src/
│           └── ...
├── ...（Day03-Day14 同构）...
└── Day15 - 日志、文件上传与生产部署/
    ├── README.md
    └── Code/
        ├── package.json
        ├── tsconfig.json
        ├── nest-cli.json
        ├── src/
        │   ├── logger/
        │   ├── upload/
        │   ├── tasks/
        │   └── health/
        └── Dockerfile
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，采用 NestJS 标准的 `src/` 目录结构
- 每个 Day 的 `Code/` 下有 `package.json`、`tsconfig.json`、`nest-cli.json`
- 多模块演示时在 `src/` 下分子目录

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 6-8 小时 | 约 2-3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 5-7 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **先读后写**：每天先通读 README，理解概念后再动手跑代码
2. **对照 TS 板块**：Day09 装饰器、Day06 类、Day04 泛型是 NestJS 的直接基础，遇到疑惑随时回看
3. **善用 nest CLI**：用 `nest g resource articles` 等脚手架命令生成代码骨架
4. **调试技巧**：用 `nest start --watch` 热重载，配合 VS Code 调试器
5. **完成实战**：每天 README 末尾的实战练习是巩固知识的关键

### 阶段性检查点

完成每个阶段后，应能回答以下问题：

- **阶段一完成后**：能否解释依赖注入的工作原理与模块间的可见性规则？
- **阶段二完成后**：能否画出一次请求经过中间件→守卫→拦截器→管道→控制器→拦截器→异常过滤器的完整链路？
- **阶段三完成后**：能否为应用集成数据库并自动生成 Swagger 文档？
- **阶段四完成后**：能否实现一个完整的注册登录 + 角色权限控制系统？
- **阶段五完成后**：能否把应用 Docker 化并加上健康检查与生产日志？

---

## 如何运行代码

### 基础运行（所有 Day）

```bash
cd "Day01 - NestJS简介与项目搭建/Code"
npm install                          # 安装 @nestjs 全家桶
npm run start                        # 启动服务（默认 3000 端口）
npm run start:dev                    # 热重载开发模式
npm run start:debug                  # 调试模式
npm run build                        # 编译到 dist/
npm run lint                         # ESLint 检查
```

### 访问服务

```bash
# 服务启动后
curl http://localhost:3000/            # 测试根路由
curl http://localhost:3000/articles    # 测试业务路由

# Swagger 文档（Day11+）
open http://localhost:3000/api-docs
```

### 需要外部服务（Day13、Day14）

```bash
# Day13 需要 MySQL，可用 Docker 快速启动
docker run -d --name mysql -e MYSQL_ROOT_PASSWORD=123456 -e MYSQL_DATABASE=nest_demo -p 3306:3306 mysql:8

# 或使用 Prisma（自带 SQLite，无需额外服务）
```

### 调试技巧

```bash
# VS Code 调试：在 .vscode/launch.json 配置
{
  "type": "node",
  "request": "launch",
  "name": "Debug NestJS",
  "runtimeArgs": ["--nolazy", "-r", "ts-node/register", "-r", "tsconfig-paths/register", "src/main.ts"],
  "sourceMaps": true
}

# Chrome DevTools 调试
nest start --debug --watch
```

### Windows 用户注意

- PowerShell 中 `curl` 是 `Invoke-WebRequest` 别名，建议用 `curl.exe` 或 Git Bash
- 路径分隔符为 `\`，但 TS 的 `paths` 配置用 `/`
- 文件名大小写敏感（`forceConsistentCasingInFileNames: true`）
- 跨平台环境变量用 `cross-env`

---

## 知识点速查

### NestJS 核心概念速查表

| 概念 | 一句话解释 | 对应天数 |
|------|----------|---------|
| 装饰器驱动 | 一切皆装饰器：@Controller/@Module/@Injectable/@Get 等 | Day01、TS Day09 |
| 依赖注入 | 容器自动实例化并注入依赖，无需手动 new | Day03、Day05 |
| Provider | 可被注入的任何东西（Service/Repository/Config/Value） | Day03 |
| 模块 | 组织代码的边界，exports 决定对外可见性 | Day04 |
| 中间件 | 在路由处理前执行的函数，能修改 req/res | Day06 |
| 管道 | 数据转换 + 数据校验，作用于参数 | Day07 |
| 守卫 | 授权决策（能否访问），返回 boolean | Day08 |
| 拦截器 | AOP，包装方法前后逻辑（日志/缓存/响应转换） | Day09 |
| 异常过滤器 | 异常的最后一道防线，统一错误响应 | Day10 |
| DTO | 数据传输对象，请求/响应的契约 | Day11 |
| 动态模块 | 可接收配置的模块（forRoot/forRootAsync） | Day04、Day12 |
| 作用域 | DEFAULT（单例）/ REQUEST（每请求）/ TRANSIENT（每次注入） | Day05 |
| ExecutionContext | 执行上下文，区分 HTTP/RPC/GQL 场景 | Day08、Day09 |
| Reflector | 反射器，读取 @SetMetadata 设置的元数据 | Day08 |

### 请求处理链路顺序

```
请求进入
   │
   ▼
中间件 Middleware（Day06）         ← 能修改 req/res、终止请求
   │
   ▼
守卫 Guard（Day08）                 ← 授权决策，返回 false 则 403
   │
   ▼
拦截器（before）Interceptor（Day09）← AOP 前置逻辑
   │
   ▼
管道 Pipe（Day07）                  ← 参数校验与转换
   │
   ▼
控制器方法 Handler                 ← 业务逻辑
   │
   ▼
拦截器（after）Interceptor（Day09） ← AOP 后置逻辑，包装响应
   │
   ▼
异常过滤器 ExceptionFilter（Day10） ← 捕获未处理异常
   │
   ▼
响应返回
```

### 常用装饰器速查

| 装饰器 | 作用 | 类别 |
|--------|------|------|
| `@Module()` | 声明模块 | 类装饰器 |
| `@Controller()` | 声明控制器，指定路由前缀 | 类装饰器 |
| `@Injectable()` | 声明可注入（Provider/Service/Guard/Pipe/Interceptor/Filter/Middleware） | 类装饰器 |
| `@Get/@Post/@Put/@Delete/@Patch` | HTTP 方法路由 | 方法装饰器 |
| `@Param()` | 路径参数 | 参数装饰器 |
| `@Query()` | 查询字符串参数 | 参数装饰器 |
| `@Body()` | 请求体 | 参数装饰器 |
| `@Headers()` | 请求头 | 参数装饰器 |
| `@Req()/@Request()` | 原始请求对象 | 参数装饰器 |
| `@Res()/@Response()` | 原始响应对象 | 参数装饰器 |
| `@HttpCode()` | 自定义状态码 | 方法装饰器 |
| `@UseGuards()` | 应用守卫 | 方法/类装饰器 |
| `@UseInterceptors()` | 应用拦截器 | 方法/类装饰器 |
| `@UsePipes()` | 应用管道 | 方法/类装饰器 |
| `@UseFilters()` | 应用异常过滤器 | 方法/类装饰器 |
| `@Inject()` | 注入指定 Token 的 Provider | 参数/属性装饰器 |
| `@SetMetadata()` | 设置元数据 | 方法装饰器 |
| `@Global()` | 声明全局模块 | 类装饰器 |
| `@Catch()` | 声明捕获的异常类型 | 类装饰器（Filter） |

### 常用命令速查

```bash
# Nest CLI
npm i -g @nestjs/cli                   # 全局安装 CLI
nest new project-name                  # 创建新项目
nest g resource articles               # 生成完整资源（controller/service/module/dto/entity）
nest g controller users                # 生成控制器
nest g service users                   # 生成服务
nest g module users                    # 生成模块
nest g guard auth                      # 生成守卫
nest g pipe validation                 # 生成管道
nest g interceptor logging             # 生成拦截器
nest g filter http-exception           # 生成过滤器
nest g middleware logger               # 生成中间件
nest g decorator roles                  # 生成自定义装饰器

# 运行
npm run start                          # 启动
npm run start:dev                      # 热重载
npm run start:debug                    # 调试模式
npm run build                          # 编译
npm run test                           # 单元测试
npm run test:e2e                       # E2E 测试
```

### Provider 注册方式速查

```typescript
// 1. 类提供者（最常见）
{ provide: ArticlesService, useClass: ArticlesService }

// 2. 值提供者
{ provide: 'CONFIG', useValue: { port: 3000 } }

// 3. 工厂提供者（可异步）
{ provide: 'DB_CONN', useFactory: async (config: ConfigService) => {...}, inject: [ConfigService] }

// 4. 别名提供者
{ provide: 'Logger', useExisting: AppLogger }

// 5. 简写（直接写类，等价于 useClass）
providers: [ArticlesService]
```

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **MySQL** | Day13 的 TypeORM/Prisma 是数据库访问层，深化索引/事务/性能优化 |
| **Redis** | Day15 的队列、缓存、Session 存储，与 Bull/Cache 模块配合 |
| **Docker** | Day15 的 Dockerfile 实战化，多服务编排（应用 + DB + Redis） |
| **Linux** | Day15 的生产部署、Nginx 反向代理、进程管理 |
| **WebSocket** | NestJS Gateway + @WebSocketServer，实时通信进阶 |
| **微服务** | @nestjs/microservices，Redis/RabbitMQ/NATS 传输层 |
| **GraphQL** | @nestjs/graphql，代码优先 vs Schema 优先 |
| **LLM / RAG / Agent** | NestJS 作为 AI 应用后端框架，封装 LLM 调用、向量检索、Agent 编排 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [NestJS 官方文档](https://docs.nestjs.com/) - 最权威的教程，强烈推荐按顺序通读
- [NestJS 中文文档](https://docs.nestjs.cn/) - 中文翻译
- [NestJS 官方示例](https://github.com/nestjs/nest/tree/master/sample) - 官方维护的示例代码集
- [Awesome NestJS](https://github.com/nestjs/awesome-nestjs) - 社区资源汇总
- [TypeORM 官方文档](https://typeorm.io/) - Day13 数据库集成参考
- [Prisma 官方文档](https://www.prisma.io/docs/) - Day13 数据库集成参考
- [Passport.js](http://www.passportjs.org/) - Day14 认证策略参考

---

## 贡献与反馈

本学习手册为原创内容，参考 GitHub 优质仓库的文档风格但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用 NestJS 武装你的后端架构能力！**
