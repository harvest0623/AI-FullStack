# Day04 - 模块系统

模块（Module）是 NestJS 组织应用代码的最小边界。一个模块不仅划清了"哪些 Controller、Provider、DTO、Entity 属于同一个业务领域"，更关键的是它通过 `imports` 与 `exports` 两个字段决定了 Provider 在应用中的可见性。当应用从 demo 演示走向真实业务时，决定代码可维护性的不是某个 Service 写得多优雅，而是模块边界是否清晰、依赖是否单向可控。本章系统讲解 `@Module` 装饰器、特性模块、共享模块、全局模块、重新导出、动态模块的设计与实现，并给出一份可在 NestJS 10+ 直接运行的最小工程示例。

---

## 目录

- [学习目标](#学习目标)
- [一、理论知识](#一理论知识)
  - [1.1 @Module 装饰器四个核心字段](#11-module-装饰器四个核心字段)
  - [1.2 根模块 AppModule](#12-根模块-appmodule)
  - [1.3 特性模块 Feature Module](#13-特性模块-feature-module)
  - [1.4 共享模块 Shared Module](#14-共享模块-shared-module)
  - [1.5 全局模块 @Global](#15-全局模块-global)
  - [1.6 重新导出 Re-export](#16-重新导出-re-export)
  - [1.7 exports 的本质](#17-exports-的本质)
- [二、动态模块 Dynamic Module](#二动态模块-dynamic-module)
  - [2.1 静态模块 vs 动态模块](#21-静态模块-vs-动态模块)
  - [2.2 forRoot / forRootAsync / forFeature 模式](#22-forroot--forrootasync--forfeature-模式)
  - [2.3 动态模块的返回值结构](#23-动态模块的返回值结构)
  - [2.4 自定义动态模块实现](#24-自定义动态模块实现)
- [三、模块组织最佳实践](#三模块组织最佳实践)
- [四、模块与依赖注入的关系](#四模块与依赖注入的关系)
- [五、关键知识点总结](#五关键知识点总结)
- [六、实战练习](#六实战练习)

---

## 学习目标

完成本章后，你应当能够：

- 准确说出 `@Module` 装饰器四个字段（`imports` / `providers` / `controllers` / `exports`）各自的作用与适用场景。
- 区分根模块、特性模块、共享模块、全局模块，并能依据业务领域拆分模块。
- 通过 `exports` 控制 Provider 的跨模块可见性，避免出现"内部 Service 被外部直接访问"的反模式。
- 理解动态模块的运行机制，能独立实现一个 `forRoot({ isGlobal })` 风格的迷你 ConfigModule。
- 在工程中应用"模块内自治、模块间只暴露 Service"的最佳实践。

---

## 一、理论知识

### 1.1 @Module 装饰器四个核心字段

`@Module()` 装饰器接收一个 `ModuleMetadata` 对象，NestJS 在启动阶段会读取这个对象，把它编译成内部的 DI 容器注册表。它有四个核心字段：

| 字段 | 类型 | 作用 | 典型成员 |
| --- | --- | --- | --- |
| `imports` | `Array<Type \| DynamicModule>` | 声明当前模块依赖的其他模块。被引入模块的 `exports` 中暴露的 Provider 会进入当前模块的可见范围。 | `DatabaseModule`、`ConfigModule.forRoot(...)` |
| `providers` | `Array<Provider>` | 在当前模块 DI 容器中注册的 Provider。这些 Provider 默认只在当前模块可见，除非通过 `exports` 暴露。 | `ArticlesService`、`{ provide: 'TOKEN', useValue: ... }` |
| `controllers` | `Array<Type>` | 当前模块要实例化的 Controller 集合。NestJS 路由注册依赖此字段。 | `ArticlesController` |
| `exports` | `Array<Type \| string \| DynamicModule>` | 决定 `providers` 中的哪些 Provider 对外可见。一旦导出，`imports` 此模块的模块就能注入这些 Provider。 | `ArticlesService` |

> 关键认知：`providers` 是"模块内部的私有注册表"，`exports` 是"模块对外的 API"。这就像 TypeScript 里的 `private` 与 `public`。

### 1.2 根模块 AppModule

NestJS 应用至少有一个根模块 `AppModule`。它是整个应用依赖图的入口：

- `main.ts` 中通过 `NestFactory.create(AppModule)` 引导应用。
- `AppModule` 的 `imports` 聚合所有特性模块、共享模块、动态模块。
- 根模块本身通常不写业务逻辑，只做"装配"。

```ts
// src/app.module.ts
@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    CommonModule,
    ArticlesModule,
    UsersModule,
  ],
})
export class AppModule {}
```

### 1.3 特性模块 Feature Module

特性模块按**业务领域**划分，把同一领域的 Controller、Service、DTO、Entity 装进同一个模块。典型划分如 `ArticlesModule`、`UsersModule`、`AuthModule`。

特性模块的核心原则：**自治**。它对外只暴露 Service，不暴露 Controller、DTO、Entity 等内部实现细节。

```ts
@Module({
  controllers: [ArticlesController],
  providers: [ArticlesService],
  exports: [ArticlesService], // 只暴露 Service
})
export class ArticlesModule {}
```

### 1.4 共享模块 Shared Module

被多个模块 `import` 的模块就是共享模块。它通过 `exports` 把通用 Provider 暴露给所有引入方。

典型场景：日志服务、分页工具、自定义拦截器等。

```ts
@Module({
  providers: [LoggerService],
  exports: [LoggerService], // 暴露给所有 import 它的模块
})
export class CommonModule {}
```

### 1.5 全局模块 @Global

共享模块的痛点是"每个用到它的模块都要 import 一次"。当 Provider 真正全局通用（日志、配置、缓存）时，可以用 `@Global()` 装饰器把它注册成全局模块：

- 全局模块的 `exports` 一旦注册，**全应用可见**，无需再 `imports`。
- 只在"真正全局通用"的场景使用，否则会破坏模块边界。

```ts
@Global()
@Module({
  providers: [LoggerService],
  exports: [LoggerService],
})
export class CommonModule {}
```

在 `AppModule` 中 `imports: [CommonModule]` 一次，即可在任意 Service 构造函数里注入 `LoggerService`。

### 1.6 重新导出 Re-export

`imports` 中的模块可以被再次 `exports`，这种模式叫重新导出（Re-export）。常见用法是：A 模块聚合了 B 模块的能力，对外只暴露一个聚合接口。

```ts
@Module({
  imports: [DatabaseModule],
  exports: [DatabaseModule], // 把 DatabaseModule 再导出
})
export class CoreModule {}
```

引入 `CoreModule` 的模块相当于同时引入了 `DatabaseModule`。这种模式在第三方库内部经常出现，业务侧尽量少用，避免依赖图变得难懂。

### 1.7 exports 的本质

`exports` 的本质是**控制 Provider 的可见范围**：

- Provider 默认是"模块私有"的。
- 一旦被 `exports`，它在 `imports` 此模块的模块中可见。
- 全局模块的 `exports` 在整个应用可见。
- `exports` 既可以导出 `providers` 中注册的具体类，也可以导出 Token（字符串 / Symbol）。

`exports` 不是"复制 Provider"，它只是声明可见性。DI 容器中始终只有一份实例（默认是单例，与 scope 有关）。

---

## 二、动态模块 Dynamic Module

### 2.1 静态模块 vs 动态模块

**静态模块**：`@Module()` 装饰器在编译期就确定所有元数据，无法在运行时根据配置调整。

```ts
@Module({ providers: [LoggerService], exports: [LoggerService] })
export class CommonModule {}
```

**动态模块**：通过一个工厂方法返回模块元数据，可以在运行时根据传入的配置动态生成 `providers` / `exports` / `imports`。

```ts
@Module({})
export class ConfigModule {
  static forRoot(options: ConfigModuleOptions): DynamicModule {
    return {
      module: ConfigModule,
      providers: [{ provide: ConfigService, useValue: new ConfigService(options) }],
      exports: [ConfigService],
      global: options.isGlobal ?? false,
    };
  }
}
```

### 2.2 forRoot / forRootAsync / forFeature 模式

NestJS 生态约定了一套动态模块命名规范，以 `TypeOrmModule` 为例：

| 方法 | 用途 | 典型调用位置 |
| --- | --- | --- |
| `forRoot(config)` | 配置一次性的全局配置（数据库连接）。整个应用只调用一次。 | `AppModule` |
| `forRootAsync({ inject, useFactory })` | 当配置依赖其他 Provider（如 ConfigService）时使用异步工厂。 | `AppModule` |
| `forFeature([Entity])` | 在某个特性模块中注册特定 Entity 对应的 Repository。每个特性模块调用一次。 | `ArticlesModule` |

```ts
@Module({
  imports: [
    TypeOrmModule.forRoot({ type: 'mysql', ... }),          // 全局连接
    TypeOrmModule.forRootAsync({                            // 异步版本
      inject: [ConfigService],
      useFactory: (config) => ({ type: 'mysql', url: config.get('DB_URL') }),
    }),
  ],
})
export class AppModule {}

@Module({
  imports: [TypeOrmModule.forFeature([ArticleEntity])],     // 局部 Repository
})
export class ArticlesModule {}
```

### 2.3 动态模块的返回值结构

动态模块的方法返回一个 `DynamicModule` 对象，其核心字段：

```ts
interface DynamicModule {
  module: Type;            // 必填，动态模块本身
  providers?: Provider[];  // 动态注册的 Provider
  exports?: Array<Type | string>; // 动态暴露的 Provider
  imports?: Array<Type | DynamicModule>; // 动态引入的依赖
  global?: boolean;        // 是否注册为全局模块
}
```

把 `DynamicModule` 放进任意模块的 `imports` 数组，NestJS 会展开它并合并到 DI 容器。

### 2.4 自定义动态模块实现

本章 `Code/` 中实现了一份迷你版 `ConfigModule.forRoot({ isGlobal })`：

```ts
// src/config/config.module.ts
@Module({})
export class ConfigModule {
  static forRoot(options: ConfigModuleOptions = {}): DynamicModule {
    const configService = new ConfigService(options);
    return {
      module: ConfigModule,
      providers: [{ provide: ConfigService, useValue: configService }],
      exports: [ConfigService],
      global: options.isGlobal ?? false,
    };
  }
}
```

调用方：

```ts
@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true })],
})
export class AppModule {}
```

`isGlobal: true` 后，`ConfigService` 在全应用可见，无需在每个特性模块再 import 一次。

---

## 三、模块组织最佳实践

1. **按业务领域分模块**：`ArticlesModule`、`UsersModule`、`AuthModule` 而不是 `ControllersModule`、`ServicesModule`。
2. **模块内自治**：一个模块目录下包含 `controller`、`service`、`dto`、`entity`，对外只暴露必要的 Service。
3. **模块间通过 exports 暴露 Service**：跨模块注入走 `imports` + `exports`，绝不直接 import 内部 Provider。
4. **common 模块放共享工具**：日志、分页、过滤器、拦截器等放在 `CommonModule`，必要时 `@Global()`。
5. **根模块只做装配**：`AppModule` 不写业务，只负责把特性模块和共享模块拼装起来。
6. **避免循环依赖**：如果 A import B、B import A，说明模块边界划错了，需要把公共部分抽到 C 模块。

---

## 四、模块与依赖注入的关系

模块的 `providers` 字段本质上是 **DI 容器的注册表**：

- 当 NestJS 启动时，遍历 `AppModule` 及其 `imports` 递归构建一棵模块树。
- 每个模块的 `providers` 注册到该模块的 DI 容器，`exports` 决定哪些 Provider 可向上传递。
- 注入一个 Provider 时，NestJS 从当前模块的可见 Provider 集合中查找；找不到就报 `Nest can't resolve dependencies`。
- 默认 scope 是 `DEFAULT`（单例），整个模块实例共享一个 Provider。

理解这一点后，很多报错都能瞬间定位：例如 `UsersModule` 想注入 `ArticlesService`，但忘记 `imports: [ArticlesModule]`，就会报"无法解析依赖"。

---

## 五、关键知识点总结

### @Module 字段速查表

| 字段 | 作用 | 默认值 |
| --- | --- | --- |
| `imports` | 引入其他模块（含动态模块），获取其 exports 暴露的 Provider | `[]` |
| `providers` | 当前模块内部注册的 Provider，默认私有 | `[]` |
| `controllers` | 当前模块要实例化的 Controller | `[]` |
| `exports` | 暴露给其他模块的 Provider | `[]` |

### 动态模块模式速查

| 方法 | 何时调用 | 调用频率 | 是否全局 |
| --- | --- | --- | --- |
| `forRoot(options)` | 应用启动配置全局 Provider | 1 次 | 看返回的 `global` |
| `forRootAsync(options)` | 全局 Provider 配置依赖其他 Provider | 1 次 | 看返回的 `global` |
| `forFeature(entities)` | 在特性模块中注册局部 Provider | 每个特性模块 1 次 | 通常不全局 |

### 可见性规则三句话

1. 模块内 Provider 默认私有，只有放进 `exports` 才对外可见。
2. 跨模块注入必须通过 `imports` 引入对方模块。
3. `@Global()` 模块的 `exports` 在全应用可见，无需重复 `imports`。

---

## 六、实战练习

### 练习 1：把 LoggerService 改为非全局

将 `CommonModule` 上的 `@Global()` 移除，在 `ArticlesModule` 与 `UsersModule` 的 `imports` 中显式引入。观察 `LoggerService` 注入失败与成功的两种状态。

### 练习 2：让 UsersModule 注入 ArticlesService

本章代码已演示 `UsersModule` `imports: [ArticlesModule]` 并在 `UsersService` 注入 `ArticlesService`。请补充一个 `GET /users/:id/articles` 接口，返回该用户最近的文章（数据可以 mock）。

### 练习 3：扩展 ConfigModule 支持 forRootAsync

参照 `TypeOrmModule.forRootAsync` 的写法，为 `ConfigModule` 增加静态方法 `forRootAsync({ inject, useFactory })`，使其可以异步加载配置。提示：返回的 `providers` 用 `{ provide: ConfigService, useFactory, inject }` 形式注册。

---

## 运行示例代码

```bash
cd "Day04 - 模块系统/Code"
npm install
npm run start:dev
```

预期输出包含：

- `LoggerService` 在 `ArticlesService`、`UsersService` 中被注入（全局模块生效）。
- `ConfigService` 在 `ArticlesService` 中被读取（动态模块 `isGlobal: true` 生效）。
- `UsersService` 调用 `ArticlesService.findAll()`（跨模块注入生效）。
