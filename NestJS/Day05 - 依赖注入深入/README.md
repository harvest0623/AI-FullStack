# Day05 - 依赖注入深入

依赖注入（Dependency Injection，简称 DI）是 NestJS 的灵魂。控制器不必自己 `new` 出 Service，Service 不必自己 `new` 出 Repository，所有对象的创建与装配都交给一个统一的容器完成——这就是控制反转（IoC）。理解 IoC 容器的工作原理，才能写出松耦合、易测试、可扩展的代码；理解作用域、Token、循环依赖这些细节，才能在生产环境中避免那些“能跑但很慢”或“偶尔报错”的隐性陷阱。

本章把 Day03 提过的 Provider 概念向下扎根一寸：从“怎么用”到“为什么这样用”，并手写一个迷你 IoC 容器呼应 TypeScript 板块的 `mini-di-container`，把抽象的“容器”变成可见的几十行代码。

---

## 学习目标

完成本章后，你应能：

- 用一句话讲清 IoC 与 DI 的关系，以及它们解决了“手动 new”的哪些痛点
- 画出 NestJS 容器从注册到解析的完整流程，说清 Token、注册表、实例化、单例缓存各自的角色
- 区分三种注入方式，并解释为什么构造函数注入是推荐写法
- 列举四种 Provider Token，知道何时必须使用 `@Inject`
- 说出 DEFAULT / REQUEST / TRANSIENT 三种作用域的实例化时机与性能差异，以及作用域注入链的传播规律
- 用 `forwardRef` 解决循环依赖，并指出何时应重构而非依赖 `forwardRef`
- 用 `useFactory` 编写异步 Provider 处理数据库连接等初始化场景
- 不依赖 NestJS，纯用 `reflect-metadata` 写出一个支持构造函数注入的迷你 IoC 容器

---

## 理论知识讲解

### 1. IoC 控制反转与 DI 依赖注入

**IoC（Inversion of Control，控制反转）** 是一种设计原则：把“对象创建”与“依赖装配”的控制权从业务代码中**反转**给一个外部容器。**DI（Dependency Injection，依赖注入）** 则是实现 IoC 的具体手段之一——由容器把依赖**注入**到需要它的对象中。

> 一句话区分：IoC 是思想（谁负责创建），DI 是手段（怎么把依赖送进去）。

#### 1.1 手动 new 的痛点

假设没有容器，一个 ArticleController 要依赖 ArticleService，ArticleService 又要依赖 ArticleRepository 与 Logger：

```typescript
// 没有 IoC：业务代码自己组装整条依赖链
const logger = new ConsoleLogger();
const repository = new ArticleRepository(logger);
const service = new ArticleService(repository, logger);
const controller = new ArticleController(service);

// 改造需求：把 ConsoleLogger 换成 FileLogger
// → 必须回到每一处 new，逐行修改；测试时也无法方便地替换为 mock
```

这种写法的核心问题：

| 问题 | 表现 |
|------|------|
| 强耦合 | 调用方写死了具体实现类，换实现要改调用方 |
| 装配代码重复 | 每个入口都要重复写一遍 new 链 |
| 难以测试 | 单元测试时无法注入 mock，只能连真实依赖一起跑 |
| 生命周期难管 | 单例还是多例？谁来缓存？谁来销毁？到处自己管 |
| 循环依赖死锁 | A new B、B new A，构造函数直接爆栈 |

#### 1.2 为什么需要 IoC

把“创建谁、用什么实现、何时缓存”这些决策上交给容器后：

- **调用方只声明依赖**：`constructor(private service: ArticleService)`，至于这个 service 是哪个实现、从哪来，由容器决定
- **替换实现改一处即可**：把 `{ provide: ArticleService, useClass: ArticleServiceImpl }` 改成 `useClass: MockArticleService`，全局生效
- **测试友好**：测试模块里注册 mock Provider，业务代码一行不动
- **生命周期统一管理**：单例缓存、请求级隔离、销毁钩子都由容器兜底
- **循环依赖可被检测与打破**：容器能识别循环并通过 `forwardRef` 延迟解析

### 2. IoC 容器工作原理

不论 NestJS 还是 Spring，IoC 容器的核心模型都是同一套。理解这五个概念，就理解了所有 DI 框架：

```
┌─────────────────────────────────────────────────────────────┐
│                     IoC 容器工作流程                         │
└─────────────────────────────────────────────────────────────┘

  ① 注册 Register
     providers: [ArticleService, { provide: 'CONFIG', useValue: {...} }]
                              │
                              ▼
  ┌──────────────────────────────────────────┐
  │  ② 注册表 Registry（Token → Provider 描述）│
  │    ArticleService  → { useClass: ... }    │
  │    'CONFIG'        → { useValue: {...} }  │
  │    Symbol('LOGGER')→ { useFactory: ... }  │
  └──────────────────────────────────────────┘
                              │
                              ▼  ③ 解析 Resolve（按 Token 查表）
  ┌──────────────────────────────────────────┐
  │  ④ 实例化 Instantiate                     │
  │     - useClass:   new Ctor(...依赖)       │
  │     - useValue:   直接返回常量            │
  │     - useFactory: 调用工厂（可 async）    │
  │     递归解析构造函数参数的依赖             │
  └──────────────────────────────────────────┘
                              │
                              ▼  ⑤ 缓存 / 注入
  ┌──────────────────────────────────────────┐
  │  生命周期管理 Lifecycle                   │
  │    DEFAULT   → 缓存单例，下次直接返回     │
  │    REQUEST   → 按请求缓存，请求结束销毁   │
  │    TRANSIENT → 不缓存，每次注入都新建     │
  └──────────────────────────────────────────┘
```

五个核心概念：

1. **注册表（Registry）**：一个 `Map<Token, ProviderDescriptor>`，应用启动时根据 `@Module().providers` 收集
2. **Token**：Provider 在容器中的“身份证”，可以是类、字符串、Symbol、抽象类
3. **解析（Resolve）**：消费者声明依赖后，容器按 Token 在注册表里查 Provider 描述
4. **实例化（Instantiate）**：根据 Provider 描述（`useClass` / `useValue` / `useFactory`）创建实例，并递归解析其构造函数参数
5. **生命周期（Lifecycle）**：决定实例是否被缓存、缓存多久、何时销毁

### 3. NestJS 的 DI 容器

NestJS 的 DI 容器能“自动”知道一个构造函数需要哪些依赖，靠的是 TypeScript 的两项编译选项加上 `reflect-metadata` 这个 polyfill：

```json
// tsconfig.json
{
  "compilerOptions": {
    "emitDecoratorMetadata": true,   // 编译时把类型信息写成元数据
    "experimentalDecorators": true   // 启用装饰器语法
  }
}
```

```typescript
// reflect-metadata 提供运行时读写元数据的能力
import 'reflect-metadata';

@Injectable()
class ArticleService {
  constructor(
    private readonly repo: ArticleRepository, // ← 类型被写进元数据
    private readonly logger: LoggerService,   // ← 类型被写进元数据
  ) {}
}

// 容器内部大致等价于：
const paramTypes = Reflect.getMetadata('design:paramtypes', ArticleService);
// → [ArticleRepository, LoggerService]
// 容器拿着这两个 Token 去注册表查 Provider，递归解析
```

**关键点**：

- `emitDecoratorMetadata` 只在类**有装饰器**时才写入元数据，所以 `@Injectable()` 不是装饰性的，它是元数据写入的触发条件之一
- 接口（`interface`）在编译后消失，元数据里只会留下 `Object`。因此**注入接口必须用 `@Inject(Token)` 显式指定 Token**，无法靠类型推断
- `reflect-metadata` 是 polyfill，必须在应用入口（`main.ts` 顶部）`import 'reflect-metadata'`

### 4. 三种注入方式

NestJS 支持三种把依赖送进类的方式，推荐程度从高到低：

#### 4.1 构造函数注入（推荐）

```typescript
@Injectable()
export class ArticleController {
  constructor(private readonly service: ArticleService) {}
}
```

- **优点**：依赖在构造时就绪，不可变（`readonly`），便于单元测试时直接 `new`，依赖关系一目了然
- **缺点**：依赖很多时构造函数会变长（这本身是信号——类职责过重了）
- **NestJS 默认**：控制器、Provider、Guard、Pipe、Interceptor、Filter 全部走这条路径

#### 4.2 属性注入（不推荐）

```typescript
@Injectable()
export class ArticleController {
  @Inject(ArticleService)
  private service!: ArticleService; // 不能用 readonly，且实例化后还要再赋值
}
```

- **缺点**：依赖在构造完成后才被注入，构造函数里访问会得到 `undefined`；不可变性丢失；测试时需要先实例化再反射赋值
- **NestJS 限制**：属性注入必须显式写 `@Inject(Token)`，因为 `design:type` 元数据对于接口类型同样不可靠
- **何时用**：极少数继承场景，子类想复用父类的依赖而又不想重写构造函数

#### 4.3 参数注入与 `@Inject` 装饰器

```typescript
@Injectable()
export class ArticleController {
  constructor(
    private readonly service: ArticleService,                       // 类 Token 可省略 @Inject
    @Inject('CONFIG') private readonly config: AppConfig,           // 字符串 Token 必须 @Inject
    @Inject(LOGGER_KEY) private readonly logger: ILogger,           // Symbol Token 必须 @Inject
    @Inject(CacheProvider) private readonly cache: CacheProvider,   // 抽象类 Token 推荐 @Inject
  ) {}
}
```

**`@Inject(Token)` 的两个用途**：

1. **注入非类 Token**：字符串、Symbol 这类 Token 无法靠类型推断，必须显式声明
2. **注入抽象类/接口**：当注入类型是抽象类但运行时实现不同，或类型元数据不可靠时，显式声明更安全

> 经验法则：能用类型推断就用类型推断（少写代码），推断不出来（接口/字符串/Symbol）才上 `@Inject`。

### 5. Provider Token 详解

Token 是 Provider 在容器中的身份证。NestJS 支持四种：

| Token 类型 | 写法 | 适用场景 | 是否需 `@Inject` |
|-----------|------|---------|-----------------|
| 类 Token | `{ provide: Foo, useClass: Foo }` 或简写 `Foo` | 最常见，注入具体类 | 否（类型推断） |
| 字符串 Token | `{ provide: 'CONFIG', useValue: {...} }` | 配置常量、第三方对象 | 是 |
| Symbol Token | `{ provide: Symbol('X'), useValue: {...} }` | 替代字符串，避免命名冲突 | 是 |
| 抽象类 Token | `{ provide: AbstractFoo, useClass: FooImpl }` | 面向接口编程，便于替换实现 | 推荐显式 |

**字符串 Token 的陷阱**：字符串没有作用域，两个不同模块都可能注册 `'CONFIG'`，后者覆盖前者且无任何编译期提示。**Symbol 天然唯一**，即使描述相同也不会冲突，是替代字符串 Token 的最佳实践。

```typescript
// 字符串 Token：危险，全局命名空间
export const CONFIG_TOKEN = 'CONFIG'; // 别的模块也可能叫 'CONFIG'

// Symbol Token：安全，即使描述相同也是不同 Symbol
export const CONFIG_TOKEN = Symbol('CONFIG');
```

**抽象类 Token 的价值**：面向接口编程。注册时用抽象类作 Token，`useClass` 指向具体实现；消费端只依赖抽象类，换实现只改注册一处：

```typescript
// 注册
{ provide: CacheProvider, useClass: RedisCacheProvider }
// 消费端（不知道也不关心是 Redis 还是 Memory）
constructor(private readonly cache: CacheProvider) {}

// 切换实现：只改一行
{ provide: CacheProvider, useClass: MemoryCacheProvider }
```

### 6. `@Inject` 装饰器回顾

`@Inject(Token)` 用在构造函数参数或属性上，显式告诉容器“这个位置要注入哪个 Token 的实例”。两种典型用法：

```typescript
// 用法 1：注入非类 Token
@Inject('CONFIG') private readonly config: AppConfig
@Inject(LOGGER_KEY) private readonly logger: ILogger

// 用法 2：注入抽象类，类型与 Token 都是抽象类
@Inject(CacheProvider) private readonly cache: CacheProvider
```

注意 `@Inject` 接收的是 **Token 本身**，不是字符串名。`@Inject(CacheProvider)` 传的是类引用，不是 `'CacheProvider'` 这个字符串。

---

## 作用域 Scope

NestJS 提供三种 Provider 作用域，决定实例化的时机与缓存策略。通过 `@Injectable({ scope: Scope.XXX })` 声明。

### 1. DEFAULT（默认，单例）

```typescript
@Injectable() // 等价于 { scope: Scope.DEFAULT }
export class DefaultService {}
```

- **实例化时机**：应用启动时（懒实例化在首次注入时）
- **缓存策略**：整个应用共享一个实例，容器缓存
- **性能**：最佳，无重复实例化开销
- **适用**：无状态服务、配置读取、日志、Repository、工具类
- **默认值**：不写 `scope` 就是 DEFAULT

### 2. REQUEST（每请求）

```typescript
@Injectable({ scope: Scope.REQUEST })
export class RequestScopedService {
  constructor(@Inject(REQUEST) private readonly request: Request) {}
}
```

- **实例化时机**：每个 HTTP 请求到来时新建，请求结束后销毁
- **缓存策略**：单请求内共享，跨请求隔离
- **性能**：明显差于 DEFAULT，每个请求都要重建实例与依赖链
- **适用**：多租户上下文、请求级追踪 ID、按请求隔离的缓存
- **特殊能力**：可注入 `@Inject(REQUEST)` 拿到当前请求对象（DEFAULT 做不到）

### 3. TRANSIENT（每次注入）

```typescript
@Injectable({ scope: Scope.TRANSIENT })
export class TransientService {}
```

- **实例化时机**：每次注入都新建
- **缓存策略**：完全不缓存
- **性能**：开销最大
- **适用**：不可变值对象、严格隔离状态的小工具
- **与 REQUEST 区别**：REQUEST 按“请求”隔离，TRANSIENT 按“注入点”隔离

### 4. 作用域注入链（重要）

**REQUEST 作用域会向上传播**：如果一个 REQUEST 作用域的 Provider 被另一个 Provider 注入，那上游 Provider 也会被强制降级为 REQUEST 作用域。整条依赖链都会每请求重建。

```
Controller (默认每请求实例化)
    └── 注入 ServiceA（DEFAULT）
          └── 注入 ServiceB（REQUEST）  ← 这一行让 ServiceA 也变成 REQUEST
                └── 注入 ServiceC（DEFAULT）  ← ServiceC 仍是单例
```

**性能警示**：不要为了“图方便”把整个应用都标成 REQUEST。只在真正需要请求级隔离的 Provider 上用 REQUEST，并让它尽量靠近依赖链末端，避免污染上游。

### 5. 三种作用域对比表

| 维度 | DEFAULT | REQUEST | TRANSIENT |
|------|---------|---------|-----------|
| 实例化时机 | 应用启动 / 首次注入 | 每个请求 | 每次注入 |
| 缓存范围 | 整个应用 | 单个请求 | 不缓存 |
| 实例数量 | 1 | N（请求数） | M（注入次数） |
| 性能开销 | 最低 | 较高 | 最高 |
| 可注入 `REQUEST` | 否 | 是 | 否 |
| 典型场景 | 无状态服务、配置、日志 | 多租户、请求级追踪 | 不可变值对象 |
| 注入链传播 | 不传播 | 向上传播 | 不传播 |

---

## 循环依赖

### 1. 径向依赖问题

当 A 注入 B，B 又注入 A 时，容器在实例化时陷入死循环：

```
容器要创建 A
  → A 需要 B，去创建 B
    → B 需要 A，去创建 A
      → A 需要 B，去创建 B
        → ... 无限递归
```

容器无法决定先创建谁，最终抛出 `Nest can't resolve dependencies of X` 错误。

### 2. forwardRef 解决

`forwardRef` 接收一个返回 Token 的工厂函数，让容器**延迟**解析某个依赖：先创建 A 并把 A 的引用占住，等 B 真正需要 A 时再回填。

```typescript
// 参数级 forwardRef（同一模块内）
@Injectable()
export class ServiceA {
  constructor(
    @Inject(forwardRef(() => ServiceB)) private readonly b: ServiceB,
  ) {}
}

@Injectable()
export class ServiceB {
  constructor(
    @Inject(forwardRef(() => ServiceA)) private readonly a: ServiceA,
  ) {}
}
```

跨模块循环依赖用**模块级 forwardRef**：

```typescript
@Module({
  imports: [forwardRef(() => ModuleB)],
})
export class ModuleA {}
```

### 3. 何时应避免循环依赖

`forwardRef` 是权宜之计，不是设计目标。循环依赖往往是**职责划分不清**的信号。重构方向：

- **抽出第三者中介服务**：把 A 和 B 都需要的共同逻辑下沉到 ServiceC，让 A 和 B 都依赖 C，而不是互相依赖
- **事件解耦**：A 不直接调 B，而是发事件，B 监听事件，用 EventBus / EventEmitter 解耦
- **重新切分模块边界**：循环依赖常常是模块拆分过细或过粗导致的，重新审视边界

> 经验：能用第三者中介拆开就别用 `forwardRef`。代码里出现 `forwardRef` 时，把它当成一个“待重构”的标记。

---

## 异步 Provider

### 1. useFactory 返回 Promise

有些依赖必须在应用启动时异步初始化：建立数据库连接池、连接 Redis、从远程拉取配置。NestJS 的 `useFactory` 可以返回 Promise，容器会等待其 resolve 后才把结果作为实例注入。

```typescript
{
  provide: DATABASE_CONNECTION,
  useFactory: async (config: ConfigService) => {
    const connection = await createTypeOrmConnection(config);
    return connection;
  },
  inject: [ConfigService], // 工厂自身的依赖
}
```

**关键点**：

- 容器在应用 `listen` 之前等待所有异步 Provider 完成，因此消费者注入时拿到的已是就绪对象
- `inject` 数组声明工厂自身的依赖，容器会先解析它们再传给工厂
- 异步 Provider 默认仍是 DEFAULT 作用域（单例），不会每次请求重建

### 2. 数据库连接初始化场景

```typescript
// 典型场景：TypeORM 连接
{
  provide: 'DATA_SOURCE',
  useFactory: async () => {
    const dataSource = new DataSource({
      type: 'mysql',
      host: 'localhost',
      // ...
    });
    return dataSource.initialize(); // 返回 Promise<DataSource>
  },
}
```

真实项目里通常用 `TypeOrmModule.forRootAsync({ useFactory })`，本质与上面的写法等价，只是封装了一层。

---

## 自定义 DI 实战：手写迷你 IoC 容器

呼应 TypeScript 板块 Day09 的 `mini-di-container`，这里实现一个最小可用版本，展示 NestJS DI 的本质原理。完整代码见 `src/mini-ioc/mini-container.ts`。

```typescript
import 'reflect-metadata';

type Provider =
  | { provide: any; useValue: any }
  | { provide: any; useClass: new (...args: any[]) => any }
  | { provide: any; useFactory: (...args: any[]) => any; inject?: any[] };

export class MiniIocContainer {
  private providers = new Map<any, Provider>();
  private instances = new Map<any, any>();

  register(...list: Provider[]): this {
    for (const p of list) this.providers.set(p.provide, p);
    return this;
  }

  async resolve<T>(token: any): Promise<T> {
    if (this.instances.has(token)) return this.instances.get(token); // 单例缓存
    const provider = this.providers.get(token);
    if (!provider) throw new Error(`找不到 Token: ${String(token)}`);

    let instance: any;
    if ('useValue' in provider) {
      instance = provider.useValue;
    } else if ('useClass' in provider) {
      const ctor = provider.useClass;
      // 关键：用 reflect-metadata 读取构造函数参数类型
      const paramTypes: any[] =
        Reflect.getMetadata('design:paramtypes', ctor) ?? [];
      const args = await Promise.all(
        paramTypes.map((t) => this.resolve(t)), // 递归解析依赖
      );
      instance = new ctor(...args);
    } else if ('useFactory' in provider) {
      const deps = await Promise.all(
        (provider.inject ?? []).map((t) => this.resolve(t)),
      );
      instance = await provider.useFactory(...deps);
    }
    this.instances.set(token, instance); // 缓存单例
    return instance;
  }
}
```

这几十行代码涵盖了 NestJS DI 的核心：

- **注册表**：`providers` Map
- **Token**：Map 的 key
- **解析**：`resolve` 方法按 Token 查表
- **实例化**：`useClass` 走 `new` + 递归解析参数，`useValue` 直接返回，`useFactory` 调用工厂
- **单例缓存**：`instances` Map
- **类型元数据**：`Reflect.getMetadata('design:paramtypes', ctor)`

NestJS 的真实容器在此基础上还做了：作用域、循环依赖检测、属性注入、动态模块、生命周期钩子（`OnModuleInit` 等）。但骨架就是上面这几十行。

运行 `npm run start` 时，`main.ts` 会调用 `runMiniIocDemo()`，在终端打印出迷你容器解析 `UserService` 的全过程，可对照控制台输出理解每一步。

---

## 关键知识点总结

### 作用域对比表

| 作用域 | 装饰器写法 | 实例化时机 | 缓存 | 性能 | 注入链传播 |
|--------|-----------|-----------|------|------|-----------|
| DEFAULT | `@Injectable()` | 启动 / 首次注入 | 应用级单例 | 最低 | 不传播 |
| REQUEST | `@Injectable({ scope: Scope.REQUEST })` | 每请求 | 请求级 | 较高 | 向上传播 |
| TRANSIENT | `@Injectable({ scope: Scope.TRANSIENT })` | 每次注入 | 不缓存 | 最高 | 不传播 |

### Token 类型对比表

| Token 类型 | 注册示例 | 注入写法 | 需 `@Inject` | 优势 | 风险 |
|-----------|---------|---------|-------------|------|------|
| 类 | `{ provide: Foo, useClass: Foo }` | `constructor(s: Foo)` | 否 | 类型安全，自动推断 | 无法面向接口 |
| 字符串 | `{ provide: 'CONFIG', useValue: {...} }` | `@Inject('CONFIG')` | 是 | 简单直观 | 命名冲突 |
| Symbol | `{ provide: Symbol('X'), useValue: {...} }` | `@Inject(KEY)` | 是 | 天然唯一 | 调试时不可读 |
| 抽象类 | `{ provide: AbstractFoo, useClass: FooImpl }` | `@Inject(AbstractFoo)` | 推荐 | 面向接口，可替换 | 需多写一个抽象类 |

### Provider 注册方式速查

```typescript
// 1. 简写（等价于 useClass，最常见）
providers: [ArticleService]

// 2. useClass：面向接口
{ provide: CacheProvider, useClass: RedisCacheProvider }

// 3. useValue：注入常量
{ provide: 'CONFIG', useValue: { port: 3000 } }

// 4. useFactory：动态/异步初始化
{ provide: 'DB', useFactory: async (cfg) => connect(cfg), inject: [ConfigService] }

// 5. useExisting：别名，让两个 Token 共享实例
{ provide: InMemoryCacheProvider, useExisting: CacheProvider }
```

### 注入方式速查

```typescript
// 构造函数注入（推荐）
constructor(private readonly service: ArticleService) {}

// 属性注入（不推荐）
@Inject(ArticleService) service!: ArticleService;

// 参数注入 + @Inject（非类 Token 必需）
constructor(@Inject('CONFIG') private config: AppConfig) {}
```

### forwardRef 速查

```typescript
// 参数级：同一模块内循环依赖
@Inject(forwardRef(() => ServiceB)) private b: ServiceB

// 模块级：跨模块循环依赖
@Module({ imports: [forwardRef(() => ModuleB)] })
```

---

## 实战练习

### 练习 1：作用域观察实验

启动项目后，连续访问三次 `GET /scope`：

```bash
curl http://localhost:3000/scope
curl http://localhost:3000/scope
curl http://localhost:3000/scope
```

观察返回 JSON 中各 `instanceId` 的变化：

- `default.instanceId` 三次是否相同？为什么？
- `request.instanceId` 三次是否相同？为什么？
- `transientA` 与 `transientB` 在同一次请求内是否相同？为什么？

**进阶**：在 `RequestScopedService` 的 `describe()` 里加上 `Date.now()` 输出，验证“同一请求内多次访问 `this.requestScopedService` 返回的是同一实例”。

### 练习 2：用 Symbol Token 替换字符串 Token

参考 `src/token-demo/token.constants.ts`：

1. 新增一个字符串 Token `CACHE_TTL_TOKEN = 'CACHE_TTL'` 与对应的 `useValue: 60`
2. 在 `TokenDemoController` 里用 `@Inject('CACHE_TTL')` 注入并返回
3. 故意在另一个控制器也注册一个 `'CACHE_TTL'` 但 `useValue: 120`，观察是否产生冲突
4. 把字符串 Token 改为 Symbol Token，验证冲突消失

**目标**：体会字符串 Token 的命名冲突风险，养成用 Symbol 替代的习惯。

### 练习 3：重构循环依赖

当前 `ServiceA` 与 `ServiceB` 互相注入，靠 `forwardRef` 打破死锁。请按以下步骤重构：

1. 新建 `SharedContextService`，把 A 和 B 都需要互相调用的逻辑下沉到这个服务
2. 让 `ServiceA` 和 `ServiceB` 都注入 `SharedContextService`，去掉 `forwardRef`
3. 验证 `/circular` 路由仍能正常返回，但代码里不再有任何 `forwardRef`

**目标**：体会“第三者中介”模式如何消除循环依赖，理解 `forwardRef` 是设计缺陷的信号。

---

## 本章代码导航

| 文件 | 演示内容 |
|------|---------|
| `src/main.ts` | 启动入口，触发迷你 IoC 演示 |
| `src/app.module.ts` | 根模块，集中注册四种 Provider 写法 |
| `src/scope-demo/` | 三种作用域对比（DEFAULT / REQUEST / TRANSIENT） |
| `src/token-demo/` | 四种 Token 注入（类 / 字符串 / Symbol / 抽象类） |
| `src/circular-ref/` | forwardRef 解决循环依赖 |
| `src/async-provider/` | useFactory 异步初始化数据库连接 |
| `src/mini-ioc/` | 手写迷你 IoC 容器，展示 DI 本质 |

运行方式：

```bash
cd "Day05 - 依赖注入深入/Code"
npm install
npm run start:dev

# 另开终端测试
curl http://localhost:3000/scope
curl http://localhost:3000/token
curl http://localhost:3000/circular
curl http://localhost:3000/async-db
```

---

## 后续衔接

本章把 DI 的“为什么”与“怎么做”讲透后，Day06 起进入请求处理链路（中间件 → 守卫 → 拦截器 → 管道 → 异常过滤器）。这五大组件**全部都是 `@Injectable`**，全部由容器注入——理解了本章，后续章节中 `@Injectable()` 才不再是黑盒，而是“又一个被容器管理的 Provider”。

Day13 数据库集成会用 `TypeOrmModule.forRootAsync({ useFactory })` 异步初始化连接池，正是本章异步 Provider 的工业级应用；Day14 JWT 认证的 Passport 策略也是被容器注入的 Provider。DI 是 NestJS 一切机制的底座。
