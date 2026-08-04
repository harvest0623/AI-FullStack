# Day03 - 提供者与服务

## 本章简介

Provider 是 NestJS 依赖注入体系的基本单元。任何可被容器管理、可被注入到其他类的"东西"，都可以是一个 Provider——Service 是其中最常见的形态，但远不止于此。配置对象、数据库连接实例、Mock 实现、工厂产物，都能以 Provider 的身份进入 DI 容器。

理解 Provider，本质上是理解三件事：**Token（用什么找）、注册（怎么放进容器）、注入（怎么取出来）**。一旦这三层关系理顺，NestJS 的依赖注入体系就不再神秘，后续的 Guard、Pipe、Interceptor、Filter 都建立在同一套机制之上。

本章将围绕 Provider 的注册方式、Token 体系、Service 模式展开，配合可运行的 Articles 模块与 Demo 控制器，把 useClass / useValue / useFactory / useExisting 四种注册方式与三种 Token 类型全部走一遍。

---

## 学习目标

读完本章并完成代码实操后，你应能：

- 准确说出 Provider 的定义，并能列举至少 4 种可作 Provider 的"东西"
- 解释 `@Injectable` 装饰器的作用，以及它为何不负责"注册"
- 独立使用简写、`useClass`、`useValue`、`useFactory`、`useExisting` 五种方式注册 Provider
- 区分类 Token、字符串 Token、Symbol Token 的差异，知道何时必须用 `@Inject`
- 实现 Service 之间的依赖注入，并理解循环依赖的成因与 `forwardRef` 的定位
- 从可测试性、单一职责、配置驱动三个角度，说明 DI 带来的工程价值
- 在 `providers` 数组与全局模块之间，为 Provider 选择合适的注册位置

---

## 理论知识讲解

### 1. Provider 概念

Provider 是"可被注入的东西"。在 NestJS 的 DI 容器里，它由两部分构成：

- **Token**：用来在容器中查找 Provider 的标识
- **值**：实际被注入的实例或对象

只要是"能被外部消费的依赖"，都可以成为 Provider。常见形态：

| 形态 | 例子 | 注册方式 |
|------|------|---------|
| Service 类 | `ArticlesService`、`LoggerService` | `useClass` 或简写 |
| Repository | TypeORM 的 `Repository<Entity>` | `useClass`（由 `forFeature` 自动注册） |
| 配置对象 | `appConfig`、`.env` 解析结果 | `useValue` |
| 值 / Mock | `{ send: () => ... }` | `useValue` |
| 工厂产物 | 数据库连接、缓存客户端 | `useFactory` |
| 别名 | 同一实例的另一个 Token | `useExisting` |

> 关键认知：Provider 不等于 Service。Service 是 Provider 的一种，配置、Mock、工厂产物同样可以是 Provider。

### 2. `@Injectable` 装饰器

`@Injectable` 声明一个**类**可被 DI 容器管理。它的作用是**打标记**，告诉 NestJS："这个类可以作为候选依赖被注入到别处"。

需要强调两个边界：

- `@Injectable` **不负责注册**。一个类即便标了 `@Injectable`，只要没在某个模块的 `providers` 中出现，容器就不知道它的存在。
- `@Injectable` **不指定 Token**。Token 由注册时的 `provide` 字段决定，与装饰器无关。

```ts
import { Injectable } from '@nestjs/common';

@Injectable()
export class LoggerService {
  log(msg: string) { console.log(msg); }
}
```

只要在某个模块里写了 `providers: [LoggerService]`，容器就会在需要 `LoggerService` 时实例化并注入它。

### 3. Service 模式

Service 是 Provider 最常见的形态，承担业务逻辑。NestJS 的工程约定：

- **Controller 只做 HTTP 映射**：解析参数、返回响应，不含业务逻辑
- **Service 承载业务逻辑**：数据组装、规则校验、外部调用
- **Service 之间可以互相注入**：上层 Service 注入下层 Service，复用逻辑

```ts
@Controller('articles')
export class ArticlesController {
  // 控制器只调用 Service，不自己处理数据
  constructor(private readonly articles: ArticlesService) {}

  @Get()
  findAll() {
    return this.articles.findAll();
  }
}

@Injectable()
export class ArticlesService {
  // Service 注入其他 Service
  constructor(private readonly logger: LoggerService) {}
}
```

这种分层让控制器薄、服务厚，业务变更不需要动路由层，单元测试也只需替换 Service 实现。

### 4. 注册 Provider 的五种写法

NestJS 在模块的 `providers` 数组中接受五种注册形式：

#### 4.1 简写：直接写类名

```ts
@Module({
  providers: [ArticlesService, LoggerService],
})
```

等价于 `{ provide: ArticlesService, useClass: ArticlesService }`。最常用，适合"Token 与实现是同一个类"的场景。

#### 4.2 `useClass`：基于类的提供者

```ts
@Module({
  providers: [
    {
      provide: NotificationSender,   // 抽象类作为 Token
      useClass: EmailSender,         // 具体子类作为实现
    },
  ],
})
```

允许 Token 与实现分离，是"面向接口编程"的落地方式。把 `useClass` 改成 `SmsSender`，所有注入 `NotificationSender` 的地方自动切换实现。

#### 4.3 `useValue`：值提供者

```ts
@Module({
  providers: [
    {
      provide: 'CONFIG',
      useValue: { port: 3000, env: 'dev' },
    },
    {
      provide: 'MOCK_SENDER',
      useValue: { send: () => 'mocked' },
    },
  ],
})
```

适合配置对象、Mock 实现、常量。值本身已经是成品，容器不再实例化。

#### 4.4 `useFactory`：工厂提供者

```ts
@Module({
  providers: [
    {
      provide: 'DB_CONN',
      useFactory: async (config: AppConfig) => {
        const conn = await connectToDb(config.dbHost);
        return conn;
      },
      inject: [CONFIG_TOKEN],   // 声明工厂依赖的 Token
    },
  ],
})
```

工厂函数返回最终的 Provider 值。两个特性让它不可替代：

- **可异步**：返回 Promise，容器会 await
- **可依赖**：`inject` 数组声明依赖，容器先解析依赖再调用工厂

适合"创建过程需要等待 / 需要读取其他 Provider"的场景，如数据库连接、Redis 客户端、动态配置。

#### 4.5 `useExisting`：别名提供者

```ts
@Module({
  providers: [
    LoggerService,
    {
      provide: 'LOGGER_ALIAS',
      useExisting: LoggerService,   // 指向同一实例
    },
  ],
})
```

让多个 Token 指向同一个实例，常用于"老接口兼容"或"语义化别名"。注入 `'LOGGER_ALIAS'` 与注入 `LoggerService` 拿到的是**同一个对象**。

### 5. Provider Token

Token 是容器查找 Provider 的钥匙。NestJS 支持三种 Token：

#### 5.1 类作为 Token

```ts
providers: [LoggerService]
// 注入：构造函数参数类型即 Token
constructor(private logger: LoggerService) {}
```

TypeScript 的 `emitDecoratorMetadata` 会把参数类型写入元数据，NestJS 据此匹配 Token。**类 Token 不需要 `@Inject`**。

#### 5.2 字符串 Token

```ts
providers: [
  { provide: 'CONFIG', useValue: {...} },
]
// 注入：必须用 @Inject 显式指定
constructor(@Inject('CONFIG') private config: AppConfig) {}
```

字符串 Token 灵活但有冲突风险——两个模块都用 `'CONFIG'` 会互相覆盖。**推荐把字符串 Token 抽成常量集中管理**（本项目放在 `token.constants.ts`）。

#### 5.3 Symbol Token

```ts
export const APP_INFO_TOKEN = Symbol('APP_INFO');

providers: [
  { provide: APP_INFO_TOKEN, useValue: {...} },
]
// 注入：必须用 @Inject
constructor(@Inject(APP_INFO_TOKEN) private info: AppInfo) {}
```

`Symbol` 全局唯一，从根本上消除命名冲突，适合对隔离性要求高的内部 Provider。

### 6. `@Inject` 装饰器

`@Inject(Token)` 用于在构造函数参数上显式指定 Token。规则很简洁：

| Token 类型 | 是否需要 `@Inject` |
|-----------|------------------|
| 类 | 否（TypeScript 元数据自动推断） |
| 字符串 | **是** |
| Symbol | **是** |

```ts
constructor(
  private logger: LoggerService,                       // 类 Token，省略 @Inject
  @Inject(CONFIG_TOKEN) private config: AppConfig,      // 字符串 Token
  @Inject(APP_INFO_TOKEN) private info: AppInfo,        // Symbol Token
) {}
```

> 经验法则：能用类 Token 就用类 Token，元数据自动推断最省事；只有当 Provider 是值 / 工厂产物 / 别名时，才退而使用字符串或 Symbol Token。

### 7. 三种 Provider 类型详解

#### 7.1 `useClass`：基于类的提供者（最常见）

- **适用场景**：业务 Service、Repository、可替换实现的策略类
- **生命周期**：容器首次需要时实例化，默认单例（`Scope.DEFAULT`）
- **依赖注入**：构造函数参数会被容器递归解析

```ts
@Injectable()
class EmailSender extends NotificationSender { ... }

@Module({
  providers: [
    { provide: NotificationSender, useClass: EmailSender },
  ],
})
```

切换实现只改 `useClass` 一行，调用方零改动——这是 DI 最直接的红利。

#### 7.2 `useValue`：值提供者

- **适用场景**：配置对象、常量、Mock 实现、测试替身
- **特点**：容器不实例化，直接注入已有的对象
- **常见误用**：把"需要根据环境动态生成"的值硬编码进来——这种情况应该用 `useFactory`

```ts
// 配置对象
{ provide: CONFIG_TOKEN, useValue: { port: 3000 } }

// Mock 实现（测试场景）
{ provide: ArticlesService, useValue: { findAll: () => mockData } }
```

测试时用 `useValue` 替换真实 Service，是 NestJS 单元测试的核心套路。

#### 7.3 `useFactory`：工厂提供者

- **适用场景**：异步初始化、依赖其他 Provider、根据条件返回不同实现
- **关键字段**：`useFactory`（函数）+ `inject`（依赖 Token 数组）
- **异步支持**：函数返回 Promise，容器会等待其 resolve

```ts
{
  provide: DATABASE_CONNECTION_TOKEN,
  useFactory: async (config: AppConfig) => {
    const conn = await createDbConnection(config.dbHost);
    return conn;
  },
  inject: [CONFIG_TOKEN],
}
```

`inject` 中声明的 Token 会按顺序作为参数传入工厂函数。本项目中 `database.factory.ts` 演示了完整流程：工厂依赖 `CONFIG_TOKEN`，先读取配置再异步建立连接。

---

## Service 之间的依赖

### Service A 注入 Service B

Service 之间通过构造函数注入建立依赖关系，与控制器注入 Service 完全一致。

```ts
@Injectable()
export class LoggerService {
  log(msg: string) { console.log(msg); }
}

@Injectable()
export class ArticlesService {
  // ArticlesService 依赖 LoggerService
  constructor(private readonly logger: LoggerService) {}

  findAll() {
    this.logger.log('查询文章');
    return [...];
  }
}
```

本项目中 `ArticlesService` 同时注入了 `LoggerService`（Service 间依赖）和 `CONFIG_TOKEN` / `DATABASE_CONNECTION_TOKEN`（值与工厂产物），三种 Token 一并演示。

### 循环依赖简介

当 Service A 依赖 Service B，同时 Service B 又依赖 Service A 时，会形成循环依赖。容器无法决定先实例化谁，启动会抛错。

```ts
@Injectable()
class ServiceA {
  constructor(private b: ServiceB) {}  // A → B
}

@Injectable()
class ServiceB {
  constructor(private a: ServiceA) {}  // B → A  ⚠️ 循环依赖
}
```

NestJS 提供 `forwardRef` 打破循环：让容器延迟解析某一侧的依赖。

```ts
@Injectable()
class ServiceB {
  constructor(@Inject(forwardRef(() => ServiceA)) private a: ServiceA) {}
}
```

> 循环依赖通常意味着设计有问题——优先考虑拆分共同依赖到第三个 Service。`forwardRef` 的详细用法与作用域配合留到 Day05 深入展开。

---

## 依赖注入的实战价值

### 1. 可测试性

通过 `useValue` 或测试专用模块替换真实实现，让单元测试不依赖外部资源（数据库、第三方 API）。

```ts
// 测试时替换 ArticlesService 为 Mock
const moduleRef = await Test.createTestingModule({
  providers: [
    ArticlesController,
    { provide: ArticlesService, useValue: { findAll: () => mockData } },
  ],
}).compile();
```

被测对象（控制器）的代码完全不变，依赖的实现被无缝替换——这就是"控制反转"在测试层面的红利。

### 2. 单一职责

每个 Service 只负责一块业务，依赖通过注入获取而非自己 `new`。文件之间耦合降低，修改一个 Service 不会牵连其他。

```
ArticlesController   →   ArticlesService   →   LoggerService
       ↑                     ↑                    ↑
   只做路由              只做文章业务         只做日志
```

### 3. 配置驱动（useValue / useFactory 切换实现）

同一个 Token，在不同环境下注册不同实现，业务代码完全不变：

```ts
// 生产环境
@Module({
  providers: [
    { provide: NotificationSender, useClass: EmailSender },
  ],
})
class ProdModule {}

// 测试环境
@Module({
  providers: [
    { provide: NotificationSender, useValue: mockSender },
  ],
})
class TestModule {}
```

调用方始终注入 `NotificationSender`，环境差异被压缩到注册层。配合 `@nestjs/config` 的 `forRoot` 与动态模块，可以实现非常灵活的环境切换。

---

## 注册 Provider 的位置

### 1. 模块的 `providers` 数组（最常见）

```ts
@Module({
  providers: [ArticlesService, LoggerService],
})
export class ArticlesModule {}
```

注册的 Provider **仅在当前模块内可见**。要让其他模块使用，必须 `exports`：

```ts
@Module({
  providers: [LoggerService],
  exports: [LoggerService],   // 导出后才可被导入方使用
})
export class CommonModule {}
```

### 2. 全局模块

给模块加上 `@Global()`，其 `exports` 中的 Provider 对**所有模块**可见，无需重复 import：

```ts
@Global()
@Module({
  providers: [LoggerService],
  exports: [LoggerService],
})
export class CommonModule {}
```

> 全局模块适合放通用基础设施（日志、配置、缓存），业务模块仍应使用普通模块以保持隔离。全局模块的滥用会让依赖关系隐式化，反而增加心智负担。

---

## 关键知识点总结

### Provider 注册方式速查表

| 写法 | 语法 | 适用场景 | 是否需要 `@Inject` |
|------|------|---------|-------------------|
| 简写 | `providers: [Foo]` | Token 与实现同类的 Service | 否（类 Token） |
| `useClass` | `{ provide: IFoo, useClass: Foo }` | 抽象类/接口切换实现 | 否（类 Token） |
| `useValue` | `{ provide: 'CONFIG', useValue: {...} }` | 配置、常量、Mock | **是** |
| `useFactory` | `{ provide: 'DB', useFactory, inject }` | 异步初始化、依赖其他 Provider | **是** |
| `useExisting` | `{ provide: 'ALIAS', useExisting: Foo }` | 别名，指向同一实例 | **是** |

### Token 类型速查表

| Token 类型 | 写法 | `@Inject` | 风险 |
|----------|------|---------|------|
| 类 | `LoggerService` | 否 | 无（推荐） |
| 字符串 | `'CONFIG'` | **是** | 命名冲突 |
| Symbol | `Symbol('X')` | **是** | 无（最安全） |

### 五条心智模型

1. **Provider = Token + 值**：注册时决定 Token 与值，注入时按 Token 查找
2. **`@Injectable` ≠ 注册**：只打标记，注册必须在 `providers` 数组
3. **类 Token 自动推断**：TypeScript 元数据让构造函数注入无需 `@Inject`
4. **`useFactory` 解决动态依赖**：异步 + 依赖其他 Provider 时别用 `useValue`
5. **模块边界决定可见性**：跨模块必须 `exports` + `imports`，或用 `@Global`

### 一句话回顾每种写法

- 简写：`providers: [ArticlesService]`
- useClass：`{ provide: NotificationSender, useClass: EmailSender }`
- useValue：`{ provide: CONFIG_TOKEN, useValue: appConfig }`
- useFactory：`{ provide: DB_TOKEN, useFactory: async (c) => ..., inject: [CONFIG_TOKEN] }`
- useExisting：`{ provide: SENDER_ALIAS_TOKEN, useExisting: NotificationSender }`

---

## 实战练习

### 练习 1：用 `useValue` 注入一个开关

为 `ArticlesService` 增加一个"是否开启审计日志"的开关 Provider：

1. 在 `token.constants.ts` 中新增 `AUDIT_ENABLED_TOKEN`
2. 用 `useValue` 注册为 `true`
3. 在 `ArticlesService.create()` 中根据该值决定是否调用 `logger.log`
4. 启动后通过 `curl -X POST http://localhost:3000/api/articles -H "Content-Type: application/json" -d '{"title":"hi","content":"world"}'` 验证日志输出

**预期**：把 `useValue` 改为 `false` 后，创建文章时不再打印审计日志，但其他日志照常。

### 练习 2：用 `useFactory` 切换发送器

新增一个 `notification.service.ts`，依赖 `NotificationSender`：

1. 在 `AppModule` 中把 `useClass: EmailSender` 改为 `useClass: SmsSender`
2. 用 `useFactory` 实现一个版本：根据 `CONFIG_TOKEN.environment` 决定使用 `EmailSender` 还是 `SmsSender`

   ```ts
   {
     provide: NotificationSender,
     useFactory: (config: AppConfig) =>
       config.environment === 'production'
         ? new EmailSender()
         : new SmsSender(),
     inject: [CONFIG_TOKEN],
   }
   ```
3. 访问 `GET http://localhost:3000/api/demo`，验证控制台输出与预期一致

### 练习 3：用 `useExisting` 制造别名

为 `LoggerService` 创建一个 `'LOGGER_ALIAS'` 的别名 Token：

1. 在 `token.constants.ts` 中新增 `LOGGER_ALIAS_TOKEN`
2. 在 `ArticlesModule` 中用 `useExisting` 注册别名
3. 在 `ArticlesService` 中**同时**注入 `LoggerService`（类 Token）和 `'LOGGER_ALIAS'`（字符串 Token）
4. 在构造函数里打印 `this.logger === this.aliasLogger`，应为 `true`

**思考**：如果 `useExisting` 指向一个**未注册**的 Token 会发生什么？把 `LoggerService` 从 `providers` 中移除后启动应用，观察报错信息。

---

## 配套代码

本章代码位于 `Code/` 目录，结构如下：

```
Code/
├── package.json
├── tsconfig.json
├── tsconfig.build.json
├── nest-cli.json
└── src/
    ├── main.ts                          # 应用启动入口
    ├── app.module.ts                    # 根模块：演示全部注册方式 + DemoController
    ├── articles/
    │   ├── articles.module.ts           # 文章模块：useClass / useValue / useFactory
    │   ├── articles.controller.ts       # 注入 ArticlesService
    │   └── articles.service.ts          # 注入 LoggerService + CONFIG + DB
    ├── common/
    │   └── logger.service.ts            # @Injectable 日志服务
    └── config/
        ├── config.provider.ts           # useValue 配置对象
        ├── database.factory.ts          # useFactory 异步工厂
        └── token.constants.ts           # 字符串 / Symbol Token 常量
```

### 运行方式

```bash
cd "Day03 - 提供者与服务/Code"
npm install
npm run start:dev
```

### 验证接口

```bash
# 文章接口
curl http://localhost:3000/api/articles
curl http://localhost:3000/api/articles/1
curl -X POST http://localhost:3000/api/articles ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"hi\",\"content\":\"world\"}"

# Provider 演示接口（验证 useExisting 同一实例、useFactory 工厂产物）
curl http://localhost:3000/api/demo
```

访问 `/api/demo` 应返回类似：

```json
{
  "cache": "value",
  "appInfo": { "name": "NestJS Day03", "version": "1.0.0" },
  "sameInstance": true
}
```

`sameInstance: true` 即验证了 `useExisting` 让两个 Token 指向同一实例。
