# Day06 - NestJS 中间件机制

## 本章简介

NestJS 的中间件机制建立在 Express 中间件基础之上，但额外引入了**依赖注入（DI）能力**，使中间件可以像 Provider 一样被注入和复用。中间件是请求处理链路的第一站，在路由处理器之前执行，能够访问 `req` 与 `res`，可以修改它们、提前终结请求链路，或通过 `next()` 把控制权交给下一个中间件。

本章将系统讲解 NestJS 中间件的两种形态、三种注册方式、链式执行顺序，并结合日志、鉴权、请求 ID 注入、请求计时等场景进行实战。

---

## 学习目标

- 理解中间件概念与请求处理模型
- 区分 NestJS 中间件与原生 Express 中间件的核心差异
- 掌握函数中间件与类中间件的编写方式
- 掌握应用级、路由级、模块级三种注册方式
- 理解 `forRoutes` 的多种路径匹配模式与 `exclude` 排除规则
- 学会编写日志、鉴权、请求 ID 注入、请求计时等常见中间件
- 理解中间件、守卫、拦截器三者的分工边界

---

## 1. 理论知识讲解

### 1.1 中间件概念

中间件是在路由处理器之前执行的函数，签名固定为 `(req, res, next) => void`。它能完成以下任务：

- 执行任何代码（日志、计时、统计）
- 修改请求对象（`req`）与响应对象（`res`）
- 终结请求-响应循环（如直接 `res.send()` 返回 401）
- 调用堆栈中的下一个中间件（`next()`）

**关键约束**：如果当前中间件没有终结请求，就必须调用 `next()`，否则请求会被永久挂起，客户端将一直等待直到超时。

### 1.2 NestJS 中间件 vs Express 中间件

| 维度 | Express 中间件 | NestJS 中间件 |
|------|---------------|---------------|
| 函数形态 | 支持 | 支持 |
| 类形态 | 不支持 | 支持 |
| 依赖注入 | 不支持 | 支持 |
| 路由匹配 | 字符串 / 正则 | 字符串 / 对象 / 控制器类 |
| 模块作用域 | 全局 | 可按模块隔离（`configure`） |
| 异常处理 | 需手写 try/catch | 配合 ExceptionFilter 自动捕获 |

NestJS 中间件最大的进化是：通过 `@Injectable()` + `NestMiddleware` 接口，让中间件也能像 Service 一样注入依赖。这意味着鉴权中间件可以注入 `UserService`、缓存中间件可以注入 `CacheService`，业务复用性显著提升。

### 1.3 函数中间件

最轻量的写法，与 Express 完全兼容。当中间件无外部依赖时优先使用：

```typescript
import { Request, Response, NextFunction } from 'express';

export function logger(req: Request, res: Response, next: NextFunction) {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
}
```

### 1.4 类中间件

需要 `@Injectable()` 装饰器，并实现 `NestMiddleware` 接口的 `use(req, res, next)` 方法。类中间件最大优势是可以通过构造函数注入依赖：

```typescript
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { LoggerService } from '../common/logger.service';

@Injectable()
export class LoggerMiddleware implements NestMiddleware {
  // 构造函数注入：与 Provider 注入方式完全一致
  constructor(private readonly logger: LoggerService) {}

  use(req: Request, res: Response, next: NextFunction) {
    this.logger.log(`${req.method} ${req.originalUrl}`);
    next();
  }
}
```

---

## 2. 中间件应用方式

### 2.1 应用级中间件

通过 `app.use()` 注册，对**每一个进入应用的请求**都执行。常用场景：helmet、CORS、body-parser、自定义全局日志。

```typescript
// main.ts
import { NestFactory } from '@nestjs/core';
import { json, urlencoded } from 'express';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // 应用级中间件：Body 解析
  app.use(json());
  app.use(urlencoded({ extended: true }));

  // 应用级中间件：CORS
  app.enableCors();

  await app.listen(3000);
}
bootstrap();
```

**注意**：`app.use()` 注册的是函数中间件，无法访问 NestJS DI 容器。如果需要 DI，请改用类中间件 + `configure().forRoutes('*')`。

### 2.2 路由级中间件 - 模块 configure

NestJS 推荐**通过模块的 `configure(consumer)` 方法注册路由级中间件**。模块需要实现 `NestModule` 接口：

```typescript
import { Module, NestModule, MiddlewareConsumer } from '@nestjs/common';
import { LoggerMiddleware } from './middleware/logger.middleware';
import { ArticlesModule } from './articles/articles.module';

@Module({
  imports: [ArticlesModule],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(LoggerMiddleware)
      .forRoutes('articles');
  }
}
```

### 2.3 关于"方法级中间件"的澄清

需要明确说明：**NestJS 中间件没有 `@Use()` 装饰器**。这与守卫（`@UseGuards`）、拦截器（`@UseInterceptors`）、管道（`@UsePipes`）、过滤器（`@UseFilters`）不同——这四类都有方法级装饰器，但**中间件没有**。

如果需要把中间件绑定到**特定路由**，必须通过 `configure().forRoutes({ path, method })` 显式指定路径与方法：

```typescript
consumer
  .apply(AuthMiddleware)
  .forRoutes({ path: 'articles/:id', method: RequestMethod.DELETE });
```

**为什么没有 `@Use()` 装饰器？**

NestJS 的中间件机制直接复用 Express 的中间件栈，而 Express 中间件本来就是通过路由匹配注册的，不是通过装饰器。NestJS 选择保持这种底层语义，使中间件与 Express 生态兼容（如 helmet、cors、morgan 等）。

**实践建议**：如果业务需要"方法级"的横切逻辑（鉴权、参数校验、响应转换），优先考虑：
- **守卫**（Day08）：用于授权判断
- **拦截器**（Day09）：用于 AOP、响应转换
- **管道**（Day07）：用于参数校验与转换

而非中间件。

### 2.4 forRoutes 路径匹配

`forRoutes` 支持三种匹配方式：

```typescript
import { RequestMethod } from '@nestjs/common';

// 1. 字符串路径：匹配所有以 articles 开头的路由
consumer.apply(LoggerMiddleware).forRoutes('articles');

// 2. 对象路径：精确匹配方法 + 路径
consumer.apply(LoggerMiddleware).forRoutes({
  path: 'articles/:id',
  method: RequestMethod.GET,
});

// 3. 控制器类：匹配该控制器所有路由
import { ArticlesController } from './articles/articles.controller';
consumer.apply(LoggerMiddleware).forRoutes(ArticlesController);

// 4. 通配符：匹配所有路由（用于全局效果但需 DI 时）
consumer.apply(LoggerMiddleware).forRoutes('*');
```

### 2.5 exclude 排除路由

`exclude` 可在 `apply()` 与 `forRoutes()` 之间排除特定路由不应用中间件：

```typescript
consumer
  .apply(AuthMiddleware)
  .exclude(
    { path: 'articles/public', method: RequestMethod.GET },
    'articles/healthcheck',
  )
  .forRoutes(ArticlesController);
```

`exclude` 既可接受 `{ path, method }` 对象，也可接受字符串路径。**调用顺序必须是 `apply → exclude → forRoutes`**，否则不生效。

---

## 3. 中间件执行顺序与链式调用

中间件按 `apply()` 中的注册顺序依次执行。`next()` 调用前是「进入阶段」，调用后是「离开阶段」，形成经典的**洋葱模型**：

```typescript
function mw1(req, res, next) {
  console.log('mw1 进入');
  next();
  console.log('mw1 离开');
}

function mw2(req, res, next) {
  console.log('mw2 进入');
  next();
  console.log('mw2 离开');
}

// 注册：consumer.apply(mw1, mw2).forRoutes('*')
// 执行顺序：
// mw1 进入
//   mw2 进入
//     (路由处理器执行)
//   mw2 离开
// mw1 离开
```

**链式注册多个中间件**有两种方式：

```typescript
// 方式一：apply 一次传多个
consumer.apply(mw1, mw2, mw3).forRoutes('*');

// 方式二：链式调用（适用于不同 forRoutes 范围）
consumer
  .apply(mw1, mw2).forRoutes('*')
  .apply(mw3).forRoutes('articles');
```

如果某个中间件不调用 `next()`，请求链终止，后续中间件与路由处理器都不会执行。这是**提前终止请求**的常用手段（如鉴权失败直接返回 401）。

---

## 4. 常见中间件场景

### 4.1 日志中间件
记录每个请求的方法、URL、IP、状态码、耗时。这是生产环境**最基础**的可观测性手段。

### 4.2 鉴权中间件（基础版）
校验请求头 `x-auth-token`，不通过则返回 401。**完整版鉴权**（基于 JWT、策略模式、装饰器元数据）请使用守卫，详见 Day08。

### 4.3 请求 ID 注入
为每个请求生成唯一 UUID 写入 `req.requestId`，便于日志关联与分布式追踪。同时回写到响应头 `x-request-id`，方便客户端关联。

### 4.4 CORS
跨域资源共享。NestJS 提供 `app.enableCors(options)`，底层会自动注册 CORS 中间件，**无需手写**。

### 4.5 Body 解析
`app.use(json())`、`app.use(urlencoded({ extended: true }))`，用于解析 JSON 与 URL 编码的请求体。NestJS 默认开启，需要自定义时通过 `NestFactory.create(app, { bodyParser: false })` 关闭默认行为后再 `app.use()` 注册自定义版本。

### 4.6 请求计时
通过 `res.on('finish')` 在响应结束时计算总耗时，用于性能监控与慢请求告警。

---

## 5. 中间件 vs 守卫 vs 拦截器

| 维度 | 中间件 | 守卫 | 拦截器 |
|------|--------|------|--------|
| 执行时机 | 路由前（最早） | 中间件之后、拦截器之前 | 守卫之后、路由处理器前后 |
| 核心职责 | 修改 req/res、日志、CORS、Body 解析 | 授权判断（是否允许访问） | AOP、响应转换、缓存、超时 |
| 是否能访问路由元数据 | 否 | 是（`Reflector`） | 是（`Reflector`） |
| 返回值影响 | 终止请求 | 返回 `false` 阻止请求 | 包装 / 转换响应 |
| 抛出异常 | 需手写 try/catch | 异常过滤器捕获 | 异常过滤器捕获 |
| 抽象层级 | 底层（Express 风格） | 中层（业务授权） | 高层（AOP） |
| 装饰器支持 | ❌ 无 `@Use()` | ✅ `@UseGuards()` | ✅ `@UseInterceptors()` |

**简单记忆**：中间件偏底层、守卫偏授权、拦截器偏 AOP。

**选择建议**：
- 需要修改 `req`/`res` 或集成 Express 生态 → 中间件
- 需要基于角色/权限决定能否访问 → 守卫
- 需要在响应返回前后做统一处理 → 拦截器

---

## 6. 关键知识点总结

- 中间件是请求处理链路的**第一站**，先于守卫、拦截器、管道执行
- NestJS 中间件支持**函数**与**类**两种形态；类中间件可注入依赖（DI）
- 类中间件需 `@Injectable()` + 实现 `NestMiddleware` 接口的 `use()` 方法
- 三种注册方式：
  - 应用级：`app.use()`（无 DI）
  - 路由级：`consumer.apply().forRoutes()`（有 DI）
  - 全局但有 DI：`consumer.apply(class).forRoutes('*')`
- **NestJS 中间件没有 `@Use()` 装饰器**，per-route 绑定必须通过 `forRoutes({ path, method })`
- `forRoutes` 支持：字符串路径、对象 `{ path, method }`、控制器类、通配符 `*`
- `exclude` 必须在 `apply` 与 `forRoutes` 之间调用
- 多个中间件按注册顺序执行，**洋葱模型**，`next()` 传递控制权
- 中间件偏底层、守卫偏授权、拦截器偏 AOP

---

## 7. 实战练习

### 任务一：实现慢请求告警中间件

在已有 `LoggerMiddleware` 基础上，新增 `SlowRequestMiddleware`，仅当请求耗时超过 500ms 时打印警告日志。

**提示**：
- 在 `use()` 中记录 `Date.now()` 作为开始时间
- 监听 `res.on('finish')` 计算耗时
- 超过阈值时调用 `LoggerService.warn()`

**验证**：故意写一个 `await new Promise(r => setTimeout(r, 600))` 的接口测试。

### 任务二：实现基于角色的简易鉴权中间件

- 在请求头读取 `x-user-role` 字段
- 对 `DELETE /articles/:id` 要求 `role === 'admin'`，否则返回 403
- 对其他 `/articles` 路由要求任意已登录用户（`role` 存在即可）

**提示**：
- 在 `configure()` 中使用 `forRoutes({ path: 'articles/:id', method: RequestMethod.DELETE })` 精确匹配
- 函数中间件通过 `res.status(403).json(...)` 返回错误
- 思考：与 Day08 守卫相比，这种实现有什么局限性？（提示：无法访问路由元数据，无法用装饰器声明所需角色）

### 任务三：扩展 Express.Request 类型

自定义 `UserAgentMiddleware`：
- 解析 `req.headers['user-agent']` 写入 `req.userAgent`
- 在 `express.d.ts` 中扩展 `Request` 接口添加 `userAgent?: string` 字段
- 在控制器方法中通过 `@Req() req` 读取 `req.userAgent` 并返回

**验证**：使用 `curl -H "User-Agent: MyTestClient/1.0" http://localhost:3000/api/articles`，应能在响应中看到解析后的 UA 字符串。
