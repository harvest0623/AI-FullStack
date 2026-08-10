# Day12 - 配置管理与环境变量

配置不硬编码是 [12-Factor App](https://12factor.net/zh_cn/config) 的核心原则之一：环境差异（开发、测试、生产）应当通过环境变量注入，而不是把值写死在代码里。NestJS 通过官方包 `@nestjs/config` 提供了一套类型安全、可校验、可分模块管理的环境变量方案，让 `process.env` 从"散落的字符串"变成一棵有结构、有类型、有默认值、有启动期校验的配置树。本章把这条链路从 .env 文件加载 → Joi 校验 → 命名空间注册 → ConfigService 注入 → 业务层读取完整走通，并为 Day13（数据库接入）与 Day14（JWT 鉴权）做好配置铺垫。

---

## 学习目标

完成本章后，你应能：

- 用一句话说清 12-Factor App 中"配置"的定义，以及为什么不能把密码、端口、第三方密钥写进代码
- 描述 dotenv 的加载机制，以及 `NODE_ENV` 如何决定 `.env` 文件的优先级
- 列举 `ConfigModule.forRoot()` 至少 5 个关键选项及作用：`isGlobal` / `envFilePath` / `load` / `cache` / `expandVariables` / `validationSchema`
- 用 `registerAs()` 创建命名空间配置，并通过 `configService.get('database.host')` 读取嵌套值
- 用 `Joi` 编写校验 Schema，让缺失或非法的环境变量在启动期立即报错（fail fast）
- 设计 `.env` / `.env.development` / `.env.production` 多环境方案，并理解 `.env.example` 在团队协作中的作用
- 在 Service 与动态模块中注入 `ConfigService` 读取配置，写出强类型访问代码
- 总结配置分层的最佳实践：应用层 / 数据库层 / 第三方服务层分离，敏感信息不入库

---

## 理论知识讲解

### 1. 环境变量与 .env 文件

#### 1.1 什么是环境变量

环境变量是操作系统级别的键值对，进程启动时由父进程或 shell 注入到 `process.env` 中。在 Node.js 里可以这样读取：

```typescript
const port = process.env.PORT;            // 字符串 '3000'
const portNum = Number(process.env.PORT); // 数字 3000
```

环境变量的优势：

- 同一份代码可以在不同环境跑出不同行为（端口、数据库地址、日志级别）
- 敏感信息（数据库密码、JWT 密钥）不进入代码仓库
- 部署平台（Docker / K8s / CI/CD）原生支持注入环境变量

#### 1.2 NODE_ENV 的特殊地位

`NODE_ENV` 是 Node.js 生态约定俗成的环境标识，常见取值：

| 值 | 含义 | 典型行为 |
|---|---|---|
| `development` | 开发环境 | 开启 source map、synchronize、详细日志 |
| `production` | 生产环境 | 压缩产物、关闭 sync、日志精简 |
| `test` | 测试环境 | 使用内存数据库、关闭外部依赖 |

很多库会自动根据 `NODE_ENV` 切换行为：Express 在 production 下启用压缩、NestJS 在 production 下不输出启动 banner。所以**第一件事就是确保 `NODE_ENV` 被正确设置**。

#### 1.3 dotenv 的加载机制

Node.js 默认不会读取 `.env` 文件，需要借助 `dotenv` 库。其工作机制：

1. 启动时读取 `.env` 文件，按 `KEY=VALUE` 解析
2. 把解析结果写入 `process.env`
3. **已存在的环境变量不会被覆盖**（即系统注入的优先级高于 `.env`）

`@nestjs/config` 内部已经集成了 dotenv，所以我们不需要手动 `require('dotenv')`，只要在 `ConfigModule.forRoot()` 里配置即可。

#### 1.4 .env 文件加载优先级

`@nestjs/config` 的 `envFilePath` 支持数组，规则是：

- 数组中**靠后的文件优先级更高**（会覆盖前面的同名变量）
- 系统环境变量（OS 注入）优先级**始终最高**，不会被任何 `.env` 文件覆盖

常见组合：

```typescript
envFilePath: [
  '.env',                                    // 基础配置（最低优先级）
  `.env.${process.env.NODE_ENV || 'development'}`, // 环境特定覆盖
]
```

例如 `NODE_ENV=production` 时，会先加载 `.env`，再用 `.env.production` 覆盖，最后用 CI/CD 注入的系统变量再次覆盖。

---

### 2. @nestjs/config 模块

#### 2.1 安装

```bash
npm install @nestjs/config joi
```

- `@nestjs/config`：NestJS 官方配置包，封装 dotenv + 命名空间 + 校验
- `joi`：Schema 校验库（也可用 `@hapi/joi`，但官方推荐直接用 `joi`）

#### 2.2 ConfigModule.forRoot

最小可用配置：

```typescript
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';

@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true })],
})
export class AppModule {}
```

注册后即可在任何地方注入 `ConfigService`：

```typescript
constructor(private readonly config: ConfigService) {}

const port = this.config.get<string>('PORT');
```

#### 2.3 ConfigService 基础用法

```typescript
// 读取扁平环境变量
const port = configService.get<string>('APP_PORT');

// 带默认值
const port = configService.get<number>('APP_PORT', 3000);

// 读取嵌套配置（需配合 load 注册）
const host = configService.get<string>('database.host');
```

注意点：
- 不指定泛型时返回 `any`，强烈建议显式声明泛型
- 第二个参数是默认值，当配置不存在时返回
- 数字、布尔类型要手动转换或借助命名空间配置

---

### 3. forRoot 关键选项详解

#### 3.1 isGlobal

```typescript
ConfigModule.forRoot({ isGlobal: true })
```

设为 `true` 后，`ConfigModule` 注册为全局模块，**任何模块都可以直接注入 `ConfigService` 而无需在 `imports` 中再次声明**。绝大多数项目都建议开启，否则每个业务模块都要重复 import。

#### 3.2 envFilePath

```typescript
envFilePath: ['.env', `.env.${process.env.NODE_ENV}`]
```

支持字符串或字符串数组。数组靠后的优先级更高，便于"基础配置 + 环境覆盖"的组合。

#### 3.3 load（加载自定义配置文件）

```typescript
import { configuration } from './config/configuration';

ConfigModule.forRoot({
  load: [configuration],
})
```

`load` 接收一个函数数组，每个函数返回一个对象。返回值会被合并到 `configService` 内部，使扁平的 `process.env` 变成嵌套的配置树。例如：

```typescript
// configuration.ts
export const configuration = () => ({
  app: { port: parseInt(process.env.APP_PORT || '3000', 10) },
  database: { host: process.env.DATABASE_HOST || 'localhost' },
});

// app.module.ts
import { configuration } from './config/configuration';
ConfigModule.forRoot({ load: [configuration] });

// 业务代码读取
configService.get<number>('app.port');
configService.get<string>('database.host');
```

#### 3.4 cache

```typescript
ConfigModule.forRoot({ cache: true })
```

缓存解析结果，避免每次 `get()` 都重新解析 `.env`。默认就是开启的，通常无需手动设置。

#### 3.5 expandVariables

```typescript
ConfigModule.forRoot({ expandVariables: true })
```

支持在 `.env` 文件里引用其他变量：

```bash
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=secret
# 引用上面的变量
DATABASE_URL=postgresql://$DATABASE_USERNAME:$DATABASE_PASSWORD@localhost:5432/db
```

适合减少重复配置，但调试时要注意变量解析顺序。

---

### 4. ConfigService 读取嵌套配置

#### 4.1 通过点号路径

```typescript
configService.get<string>('database.host');   // 'localhost'
configService.get<number>('database.port');   // 5432
configService.get<boolean>('database.sync');  // false
```

#### 4.2 整块读取（推荐 + 泛型）

```typescript
import { DatabaseConfig } from './config/config.interface';

const db = configService.get<DatabaseConfig>('database');
console.log(db.host, db.port, db.url);
```

整块读取配合 TypeScript 接口，既能减少 `get()` 调用次数，又能拿到完整类型提示。

#### 4.3 默认值兜底

```typescript
const port = configService.get<number>('app.port', 3000);
```

第二个参数是默认值。即便 `.env` 缺失，也能保证业务逻辑继续运行（除非 Joi 把它声明为 required）。

---

### 5. 自定义配置文件

把所有配置塞在一个 `configuration.ts` 里在小项目里没问题，但项目一大就会变成几百行的"配置怪兽"。最佳实践是按职责拆分到 `src/config/` 下：

```
src/config/
├── configuration.ts        # 根配置（兜底）
├── app.config.ts           # 应用配置（端口、前缀、环境）
├── database.config.ts      # 数据库配置
├── jwt.config.ts           # JWT 配置
├── validation.schema.ts    # Joi 校验 schema
└── config.interface.ts     # 强类型接口
```

每个文件只关心自己那一块，修改时影响范围明确。然后在 `app.module.ts` 里统一 `load`：

```typescript
ConfigModule.forRoot({
  load: [configuration, appConfig, databaseConfig, jwtConfig],
})
```

---

### 6. 配置命名空间 registerAs

`registerAs` 是 `@nestjs/config` 提供的工厂函数，用来创建一个**带名字的配置块**。

```typescript
// database.config.ts
import { registerAs } from '@nestjs/config';

export const databaseConfig = registerAs('database', () => ({
  host: process.env.DATABASE_HOST || 'localhost',
  port: parseInt(process.env.DATABASE_PORT || '5432', 10),
}));
```

注册后：

```typescript
configService.get<string>('database.host');   // 自动找到 registerAs('database') 的返回值
```

#### registerAs 相比直接写在 configuration.ts 的优势

| 维度 | 直接写 configuration.ts | registerAs |
|---|---|---|
| 文件组织 | 所有配置挤一起 | 每块一个文件，职责清晰 |
| 类型推断 | 需手动声明接口 | `ConfigType<typeof databaseConfig>` 自动推断 |
| Lazy 加载 | 全部一次性加载 | 可按需引入 |
| 可测试性 | mock 整个 process.env | mock 单个命名空间即可 |

#### ConfigType 自动推断类型

```typescript
import { ConfigType } from '@nestjs/config';
import { databaseConfig } from './config/database.config';

constructor(
  @Inject(databaseConfig.KEY) private db: ConfigType<typeof databaseConfig>,
) {}
```

这种方式比 `configService.get<DatabaseConfig>('database')` 更"DI 友好"，单元测试时直接 mock token 即可。本 Day 的代码采用 `ConfigService.get` 的方式作为入门示例，进阶可改成 `@Inject(token.KEY)`。

---

## 配置 Schema 校验

### 为什么需要校验

没有校验时，最常见的几种事故：

1. 同事把 `APP_PORT` 写成 `3o00`（字母 o），程序运行到 `app.listen('3o00')` 才崩
2. 生产环境忘配 `JWT_SECRET`，部署后第一天才发现登录全失败
3. `DATABASE_URL` 写错前缀（`postgres://` vs `postgresql://`），连接失败但报错信息不明

`@nestjs/config` 集成 Joi 后，可以在**应用启动的那一刻**就把这些问题暴露出来，符合 fail fast 原则。

### 用 Joi 编写校验 Schema

```typescript
// validation.schema.ts
import * as Joi from 'joi';

export const validationSchema = Joi.object({
  NODE_ENV: Joi.string()
    .valid('development', 'production', 'test')
    .default('development'),

  APP_PORT: Joi.number().port().default(3000),

  DATABASE_URL: Joi.string()
    .pattern(/^postgresql:\/\//)
    .message('DATABASE_URL 必须以 postgresql:// 开头'),

  JWT_SECRET: Joi.string().min(16).required().messages({
    'string.empty': 'JWT_SECRET 不能为空',
    'string.min': 'JWT_SECRET 至少 16 个字符',
    'any.required': 'JWT_SECRET 是必填项',
  }),
});
```

### 在 forRoot 中使用

```typescript
ConfigModule.forRoot({
  validationSchema,
  validationOptions: {
    abortEarly: false,      // 一次性报告所有错误
    allowUnknown: true,     // 允许 .env 中有 schema 未声明的字段
    stripUnknown: false,    // 不删除未声明字段（保留原值）
  },
})
```

### 启动报错示例

如果 `.env` 里 `JWT_SECRET` 留空，启动时会看到类似输出：

```
Error: Config validation error: {
  "JWT_SECRET": "JWT_SECRET 不能为空"
}
```

应用直接退出，不会进入 `bootstrap()` 的后续逻辑。这是 fail fast 的精髓——**问题在最早暴露的位置被发现，而不是拖到运行时**。

### 常见校验场景

| 场景 | Joi 写法 |
|---|---|
| 端口必须是合法端口 | `Joi.number().port()` |
| 枚举取值 | `Joi.string().valid('a', 'b')` |
| 必填 | `Joi.string().required()` |
| 最小长度 | `Joi.string().min(32)` |
| URL 格式 | `Joi.string().pattern(/^postgresql:\/\//)` |
| 布尔值 | `Joi.boolean()` |
| 数字范围 | `Joi.number().min(1).max(65535)` |
| 默认值 | `Joi.string().default('localhost')` |

---

## 多环境配置

### 文件命名约定

```
.env                # 默认 / 兜底
.env.development    # 开发环境覆盖
.env.production     # 生产环境覆盖
.env.test           # 测试环境覆盖
```

### envFilePath 切换策略

```typescript
ConfigModule.forRoot({
  envFilePath: [
    '.env',
    `.env.${process.env.NODE_ENV || 'development'}`,
  ],
})
```

启动命令决定加载哪个文件：

```bash
NODE_ENV=development npm run start:dev     # 加载 .env + .env.development
NODE_ENV=production  npm run start:prod    # 加载 .env + .env.production
NODE_ENV=test        npm run test          # 加载 .env + .env.test
```

### .gitignore 规则

```gitignore
# 环境变量（含密钥，禁止提交）
.env
.env.*
!.env.example
```

关键约定：

- `.env` 与 `.env.*` 一律不提交到 git
- 只提交 `.env.example`，作为团队协作的"配置契约"
- 新成员 `cp .env.example .env` 后填入自己的值

### 生产环境密钥从哪来

**不要**把生产密钥写进 `.env.production` 然后提交到 git。正确做法：

- CI/CD 平台的 Secrets（GitHub Actions / GitLab CI）
- 容器编排配置（K8s Secret / Docker Compose `environment:`）
- 配置中心（Vault / AWS Secrets Manager / 阿里云 KMS）

`.env.production` 只放非敏感的"环境参数"（端口、日志级别），敏感字段用占位符 `REPLACE_VIA_CI_SECRET`。

---

## ConfigService 注入实战

### Service 中注入

```typescript
@Injectable()
export class ArticlesService {
  constructor(private readonly configService: ConfigService) {}

  getAppInfo() {
    const port = this.configService.get<number>('app.port', 3000);
    const env  = this.configService.get<string>('app.env', 'development');
    return { port, env };
  }
}
```

由于 `ConfigModule` 已 `isGlobal: true`，`ArticlesModule` 不需要在 `imports` 里再次声明 `ConfigModule`。

### 数据库连接配置（为 Day13 铺垫）

动态模块 / Provider 工厂中也可以注入 `ConfigService`：

```typescript
@Module({
  providers: [
    {
      provide: 'DATABASE_CONFIG',
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        host: config.get<string>('database.host'),
        port: config.get<number>('database.port'),
        username: config.get<string>('database.username'),
        password: config.get<string>('database.password'),
        database: config.get<string>('database.database'),
        synchronize: config.get<boolean>('database.sync'),
      }),
    },
  ],
})
export class DatabaseModule {}
```

Day13 会在此基础上接入 TypeORM 的 `TypeOrmModule.forRootAsync()`，结构完全一致。

### JWT 密钥（为 Day14 铺垫）

```typescript
const secret    = configService.get<string>('jwt.secret');
const expiresIn = configService.get<string>('jwt.expiresIn');
```

Day14 会用这两个值配置 `JwtModule.registerAsync()`。

---

## 配置最佳实践

### 1. 配置分层

按职责拆分，避免一个文件几百行：

```
src/config/
├── app.config.ts          # 应用本身（端口、前缀、环境）
├── database.config.ts     # 数据库
├── jwt.config.ts          # 鉴权
├── redis.config.ts        # 缓存（按需）
├── third-party.config.ts  # 第三方服务（OSS、SMS、支付）
└── validation.schema.ts   # 统一校验
```

### 2. 强类型配置接口

为每个命名空间声明接口：

```typescript
export interface DatabaseConfig {
  host: string;
  port: number;
  username: string;
  password: string;
  database: string;
  url: string;
  sync: boolean;
}

const db = configService.get<DatabaseConfig>('database');
// 此处 db.host 是 string，db.port 是 number，编译期就能发现类型错误
```

### 3. 敏感信息不入库

| 类型 | 是否可提交 git | 例子 |
|---|---|---|
| 非敏感参数 | ✅ 可以 | `APP_PORT`、`LOG_LEVEL`、`APP_PREFIX` |
| 敏感参数 | ❌ 不可以 | `JWT_SECRET`、`DATABASE_PASSWORD`、第三方 API Key |

团队约定：

- `.env.example` 写明需要哪些变量，敏感字段用占位符
- 真实密钥由 CI/CD 或运维平台注入
- 日志中绝不打印密码明文（只打印长度或前 4 位）

### 4. 配置默认值

两层兜底：

```typescript
// 第一层：registerAs 工厂里的 || 默认值
host: process.env.DATABASE_HOST || 'localhost',

// 第二层：get() 的第二个参数
configService.get<string>('database.host', 'localhost');
```

但要避免"默认值掩盖问题"——必填项应当用 Joi `.required()` 强制声明，而不是给一个看起来合理的默认值。

### 5. 配置只读，禁止运行时修改

`ConfigService` 不提供 `set()` 方法，配置一旦加载就不可变。如果业务需要"可变配置"，应当使用专门的配置中心（如 Apollo / Nacos）或数据库表，而不是污染 `process.env`。

---

## 关键知识点总结

| 知识点 | 一句话记忆 |
|---|---|
| 12-Factor App | 配置 = 环境变量，代码与配置分离 |
| dotenv 机制 | 启动期把 `.env` 注入 `process.env`，OS 变量优先 |
| `NODE_ENV` | 决定加载哪个 `.env.*` 文件，影响库的行为 |
| `ConfigModule.forRoot` | 注册配置模块，控制加载、校验、缓存策略 |
| `isGlobal: true` | 让 ConfigService 在任意模块直接注入 |
| `load: [fn]` | 把扁平 env 变成嵌套配置树 |
| `registerAs('name')` | 创建命名空间配置，类型友好、职责清晰 |
| `configService.get<T>('a.b')` | 点号路径读取嵌套值，第二参数为默认值 |
| `validationSchema` | Joi 校验，启动期 fail fast |
| `envFilePath` 数组 | 靠后的文件优先级更高，便于环境覆盖 |
| `.gitignore` | `.env` 不入库，`.env.example` 入库 |
| 配置分层 | app / database / jwt / 第三方 各自独立文件 |

---

## 实战练习

### 练习 1：新增 Redis 配置命名空间

目标：在 `src/config/` 下新增 `redis.config.ts`，使用 `registerAs('redis')` 暴露 `host`、`port`、`password`、`db` 四个字段，并在 `app.module.ts` 的 `load` 数组中注册。然后在 `validation.schema.ts` 中加上对应的 Joi 校验（端口必须是数字，host 必填）。

提示：

- 参照 `database.config.ts` 的写法
- 在 `config.interface.ts` 中加 `RedisConfig` 接口
- 在 `.env.example` 中补 `REDIS_HOST` / `REDIS_PORT` 等条目

### 练习 2：让校验更严格

目标：把 `JWT_SECRET` 的最小长度从 16 提升到 32，并新增校验：`APP_PORT` 必须在 1024-65535 之间（避免使用系统保留端口）。

提示：

- Joi 写法：`Joi.number().port().min(1024).max(65535)`
- 启动时用错误的 `.env` 测试，确认报错信息是否清晰

### 练习 3：用 @Inject(token.KEY) 替换 ConfigService.get

目标：在 `ArticlesService` 中改用 `@Inject(appConfig.KEY)` 注入应用配置，类型用 `ConfigType<typeof appConfig>`。对比两种写法的差异。

提示：

```typescript
import { Inject } from '@nestjs/common';
import { ConfigType } from '@nestjs/config';
import { appConfig } from '../config/app.config';

constructor(
  @Inject(appConfig.KEY) private app: ConfigType<typeof appConfig>,
) {}

getAppInfo() {
  return this.app;  // 直接是对象，无需 get('app')
}
```

注意要在 `ArticlesModule` 的 `imports` 里 `ConfigModule.forFeature(appConfig)`，或者保持根模块 `load` 注册即可（视 NestJS 版本而定）。

---

## 项目结构

```
Day12 - 配置管理与环境变量/
├── README.md                       # 本章文档
└── Code/
    ├── .env                        # 默认（开发）配置（不入 git）
    ├── .env.development            # 开发环境覆盖
    ├── .env.production             # 生产环境覆盖
    ├── .env.example                # 配置模板（入 git）
    ├── nest-cli.json
    ├── package.json
    ├── tsconfig.json
    ├── tsconfig.build.json
    └── src/
        ├── main.ts                 # 启动入口，从 ConfigService 读端口
        ├── app.module.ts           # ConfigModule.forRoot 配置
        ├── config/
        │   ├── configuration.ts        # 根配置加载函数
        │   ├── app.config.ts           # registerAs('app')
        │   ├── database.config.ts      # registerAs('database')
        │   ├── jwt.config.ts           # registerAs('jwt')
        │   ├── validation.schema.ts    # Joi 校验 schema
        │   └── config.interface.ts     # 强类型接口
        ├── database/
        │   └── database.module.ts      # 演示动态模块读取配置
        └── articles/
            ├── articles.module.ts
            ├── articles.controller.ts  # GET /config-demo 调试接口
            └── articles.service.ts     # 注入 ConfigService 演示
```

## 运行方式

```bash
cd "Day12 - 配置管理与环境变量/Code"
npm install

# 开发模式（默认加载 .env + .env.development）
npm run start:dev

# 生产模式（需先 build，再设置 NODE_ENV 启动）
npm run build
NODE_ENV=production node dist/main
```

启动后访问调试接口：

```bash
curl http://localhost:3000/api/v1/articles/config-demo
```

预期响应（脱敏后的配置快照）：

```json
{
  "app": { "name": "nest-day12-config-demo", "port": 3000, "prefix": "api/v1", "env": "development" },
  "jwt": { "expiresIn": "1h", "refreshExpiresIn": "7d", "secretLength": 41 },
  "databaseUrl": "postgresql://postgres:postgres@localhost:5432/nest_day12_dev"
}
```

## 与后续章节的关系

- **Day13**：在本章 `database` 命名空间基础上接入 TypeORM，`TypeOrmModule.forRootAsync()` 直接复用 `ConfigService.get('database.host')` 等字段
- **Day14**：在本章 `jwt` 命名空间基础上接入 `@nestjs/jwt`，签发与校验 JWT
- **Day15+**：日志、链路追踪、限流等中间件都会从 `app` 命名空间读取配置

配置管理是后续所有"接入外部依赖"章节的地基，本章把它彻底打通后，后面只需专注业务逻辑。
