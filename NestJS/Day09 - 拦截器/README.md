# Day09 - 拦截器

## 本章简介

拦截器（Interceptor）是 NestJS 实现 **AOP（Aspect-Oriented Programming，面向切面编程）** 的核心机制。它允许我们在不修改业务方法本身的前提下，于方法执行**前后**插入横切逻辑——例如打印日志、统计耗时、统一响应格式、缓存结果、超时控制、异常转换、字段脱敏等。

与中间件只能"在请求前"介入不同，拦截器天然拥有"前 + 后"两个切入点：`next.handle()` 之前的代码在方法执行**前**运行，之后的 RxJS 操作符则在方法返回的 `Observable` 上挂载**后置处理**。这种能力使拦截器成为 NestJS 中表达"横切关注点"最优雅的工具。

---

## 学习目标

- 理解 AOP 思想，掌握拦截器在 NestJS 中的角色定位
- 掌握 `NestInterceptor` 接口与 `intercept(context, next)` 方法签名
- 掌握 RxJS 基础：`Observable`、`Observer`、操作符，理解 `next.handle()` 返回的是 Observable
- 熟练运用 `tap`、`map`、`catchError`、`timeout` 等常用操作符
- 能够独立实现日志、统一响应、缓存、超时、异常转换、字段过滤六类经典拦截器
- 区分方法级、控制器级、全局级三种注册方式，并理解 `APP_INTERCEPTOR` 为何能支持依赖注入
- 理解多拦截器"洋葱模型"嵌套执行顺序
- 能够清晰区分拦截器与中间件、守卫、管道、异常过滤器在请求链路中的分工

---

## 理论知识讲解

### 1. 拦截器概念：AOP 思想落地

**AOP（面向切面编程）** 的核心思想是：把与主业务逻辑无关、但又横跨多个模块的"横切关注点"（cross-cutting concerns）抽离出来，集中管理。常见的横切关注点包括：

- 日志记录
- 性能监控
- 权限校验
- 事务管理
- 缓存
- 异常处理
- 响应格式化

在 NestJS 中，拦截器正是 AOP 的标准实现载体。它能在方法执行**前后**插入逻辑，统一处理响应、异常与缓存，从而避免业务控制器被这些重复代码污染。

### 2. NestInterceptor 接口

每个拦截器都需要实现 `NestInterceptor` 接口，它只要求一个方法：

```typescript
export interface NestInterceptor<T = any, R = any> {
  intercept(context: ExecutionContext, next: CallHandler<T>): Observable<R> | Promise<Observable<R>>;
}
```

- **`ExecutionContext`**：执行上下文，可获取当前请求、响应、被调用的控制器类与方法等。`context.switchToHttp().getRequest()` 可拿到 Express 的 Request 对象。
- **`CallHandler`**：调用处理器，`next.handle()` 会触发真正的路由处理器执行，并返回一个 `Observable`。
- **返回值**：必须返回一个 `Observable`，框架会订阅它并把数据写回客户端。

### 3. RxJS 基础

拦截器的"后置处理"完全建立在 **RxJS** 响应式编程之上。理解几个核心概念是看懂拦截器的关键：

| 概念 | 说明 |
| --- | --- |
| **Observable（可观察对象）** | 一个"数据流"，可以被订阅。`next.handle()` 返回的就是 Observable |
| **Observer（观察者）** | 订阅者，提供 `next`、`error`、`complete` 三个回调 |
| **Operator（操作符）** | 对流进行加工的纯函数，通过 `pipe()` 串联 |
| **Subscription（订阅）** | 订阅关系句柄，可用于取消订阅 |

NestJS 会自动订阅拦截器返回的 Observable，把 `next` 通知中的数据作为响应体，把 `error` 通知交给异常过滤器处理。

### 4. 常用操作符速览

| 操作符 | 作用 | 在拦截器中的典型场景 |
| --- | --- | --- |
| `tap` | 执行副作用，**不改变**流中数据 | 打印日志、统计耗时、写入缓存 |
| `map` | 转换流中数据 | 统一响应格式包装、字段脱敏 |
| `catchError` | 捕获 `error` 通知，可返回新流或重新抛出 | 异常转换、降级处理、异常上报 |
| `timeout` | 在指定时间内未发出数据则抛 `TimeoutError` | 接口超时控制 |
| `mergeMap` / `switchMap` | 把数据映射为新 Observable 并展平 | 异步降级、链式请求 |
| `finalize` | 流结束（无论成功或出错）时执行 | 释放资源、记录结束日志 |

> ⚠️ 注意：`map` 只处理 `next` 通知，**不会**捕获异常；异常需要用 `catchError`。

### 5. 拦截器执行模型

拦截器的执行分为三个阶段，理解这个模型是掌握拦截器的关键：

```
[ before ] → [ handler ] → [ after ]
     ↑              ↑             ↑
 next.handle()  控制器方法   订阅 Observable
 之前的代码                  后执行的 RxJS 操作符
```

- **before**：`next.handle()` 之前的同步代码，在路由处理器执行**前**运行。
- **handler**：`next.handle()` 内部调用真正的路由处理器（控制器方法）。
- **after**：`next.handle()` 返回的 Observable 被 RxJS 操作符加工后的处理逻辑，在路由处理器返回数据**后**执行。

一个直观的代码模板：

```typescript
intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
  // ===== before 阶段 =====
  const start = Date.now();
  console.log('请求开始');

  return next.handle().pipe(
    // ===== after 阶段 =====
    tap(() => console.log(`耗时 ${Date.now() - start}ms`)),
  );
}
```

---

## 拦截器应用方式

NestJS 提供三种粒度来注册拦截器。

### 1. 方法级

把 `@UseInterceptors()` 放在具体路由方法上，只影响该路由：

```typescript
@Get()
@UseInterceptors(LoggingInterceptor)
findAll() {
  return this.articles;
}
```

### 2. 控制器级

把 `@UseInterceptors()` 放在 `@Controller()` 上方，对该控制器内所有路由生效：

```typescript
@Controller('articles')
@UseInterceptors(LoggingInterceptor)
export class ArticlesController { ... }
```

### 3. 全局级

全局级有两种写法，区别在于**是否支持依赖注入**：

**方式 A：`app.useGlobalInterceptors()`**

```typescript
// main.ts
const app = await NestFactory.create(AppModule);
app.useGlobalInterceptors(new LoggingInterceptor());
```

- ✅ 简单直接
- ❌ 拦截器实例在 Nest 容器之外，**无法注入 Service**

**方式 B：`APP_INTERCEPTOR` token（推荐）**

```typescript
// app.module.ts
import { APP_INTERCEPTOR } from '@nestjs/core';

@Module({
  providers: [
    { provide: APP_INTERCEPTOR, useClass: TransformInterceptor },
  ],
})
export class AppModule {}
```

- ✅ 完全支持依赖注入，拦截器可 `constructor` 注入任意 Provider
- ✅ 便于单元测试时替换
- ✅ 生命周期由 Nest 容器管理

> 💡 两种方式可以共存。`useGlobalInterceptors` 的拦截器会先于 `APP_INTERCEPTOR` 注册的执行。

---

## 经典拦截器实现

### 1. LoggingInterceptor：日志与耗时

```typescript
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger(LoggingInterceptor.name);

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url } = request;
    const handlerName = context.getHandler().name;
    const now = Date.now();

    this.logger.log(`➡️  [${method}] ${url} -> ${handlerName}() 开始执行`);

    return next.handle().pipe(
      // tap：只读副作用，不改数据
      tap(() => {
        this.logger.log(`⬅️  [${method}] ${url} <- ${handlerName}() 耗时 ${Date.now() - now}ms`);
      }),
    );
  }
}
```

**核心要点**：
- `next.handle()` 之前记录开始时间 = before 阶段
- `tap` 不改变数据，只用来执行副作用 = after 阶段
- `context.getHandler().name` 获取当前控制器方法名

### 2. TransformInterceptor：统一响应格式

```typescript
@Injectable()
export class TransformInterceptor<T> implements NestInterceptor<T, ResponseDto<T>> {
  intercept(context: ExecutionContext, next: CallHandler<T>): Observable<ResponseDto<T>> {
    return next.handle().pipe(
      // map：将原始数据转换为统一格式
      map((data) => ({ code: 200, message: '请求成功', data })),
    );
  }
}
```

**返回效果**：

```json
// 控制器返回 [{ id: 1, title: "..." }]
// 经过 TransformInterceptor 后：
{
  "code": 200,
  "message": "请求成功",
  "data": [{ "id": 1, "title": "..." }]
}
```

**核心要点**：
- `map` 能对流中的数据做同步转换
- 异常走的是 `error` 通知，不会进入 `map`，因此不会影响异常过滤器的工作

### 3. CacheInterceptor：基于内存的缓存

```typescript
@Injectable()
export class CacheInterceptor implements NestInterceptor {
  private readonly cache = new Map<string, { data: any; expireAt: number }>();
  private readonly ttl = 10_000; // 10 秒

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const key = request.url;

    if (request.method !== 'GET') return next.handle();

    const cached = this.cache.get(key);
    if (cached && cached.expireAt > Date.now()) {
      return of(cached.data); // 命中缓存，直接返回，不执行 handler
    }

    return next.handle().pipe(
      tap((data) => {
        this.cache.set(key, { data, expireAt: Date.now() + this.ttl });
      }),
    );
  }
}
```

**核心要点**：
- 命中缓存时用 `of(cachedData)` 创建新 Observable，**完全跳过** `next.handle()`
- 这是拦截器"短路"请求的经典模式
- 生产环境应替换为 Redis 等分布式缓存，避免多实例数据不一致

### 4. TimeoutInterceptor：超时控制

```typescript
@Injectable()
export class TimeoutInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      timeout(3000),
      catchError((err) => {
        if (err instanceof TimeoutError) {
          return throwError(() => new RequestTimeoutException('请求超时'));
        }
        return throwError(() => err);
      }),
    );
  }
}
```

**核心要点**：
- `timeout(3000)` 让 Observable 在 3 秒内没有发出值时抛出 `TimeoutError`
- `catchError` 捕获后转为 NestJS 内置的 `RequestTimeoutException`（HTTP 408）
- 其他异常原样抛出，不吞掉非超时错误

### 5. ErrorInterceptor：异常转换

```typescript
@Injectable()
export class ErrorInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      catchError((err) => {
        if (err instanceof HttpException) {
          return throwError(() => err); // 业务异常，保留原样
        }
        // 未知异常：屏蔽内部细节，统一返回 500
        return throwError(() => new InternalServerErrorException('服务器内部错误'));
      }),
    );
  }
}
```

**核心要点**：
- `catchError` 能拦截流中的 `error` 通知，做"异常转换"
- 业务异常（HttpException）保持原状，不影响已有业务语义
- 未知异常统一包装为 500，防止内部堆栈泄露给客户端
- 还可在此处接入 Sentry、ELK 等异常上报系统

### 6. ExcludePasswordInterceptor：响应字段过滤

```typescript
@Injectable()
export class ExcludePasswordInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      map((data) => this.stripPassword(data)),
    );
  }

  private stripPassword(data: any): any {
    if (Array.isArray(data)) return data.map((item) => this.stripPassword(item));
    if (data && typeof data === 'object') {
      const { password, ...rest } = data;
      return rest;
    }
    return data;
  }
}
```

**核心要点**：
- 使用 `map` 对响应数据做结构化处理
- 利用解构赋值 `const { password, ...rest } = data` 剔除敏感字段
- 递归处理数组与嵌套对象

> 💡 生产环境更推荐使用 `ClassSerializerInterceptor` + `@Exclude()` 装饰器，声明式且类型安全。本例手写实现只为演示拦截器原理。

---

## 拦截器与拦截器链：洋葱模型

当多个拦截器同时作用于同一路由时，它们会以**洋葱模型**嵌套执行：

```
请求方向 →
┌──────────────────────────────┐
│  Interceptor A  (before)     │
│  ┌──────────────────────────┐│
│  │  Interceptor B  (before) ││
│  │  ┌──────────────────────┐││
│  │  │   Controller 方法    │││
│  │  └──────────────────────┘││
│  │  Interceptor B  (after)  ││
│  └──────────────────────────┘│
│  Interceptor A  (after)     │
└──────────────────────────────┘
← 响应方向
```

**规则**：先注册的拦截器先进入 before 阶段，后进入 after 阶段（LIFO）。

注册顺序（以 `APP_INTERCEPTOR` 为例）：

```typescript
providers: [
  { provide: APP_INTERCEPTOR, useClass: A }, // 最外层
  { provide: APP_INTERCEPTOR, useClass: B }, // 中间层
]
```

执行顺序：`A before → B before → handler → B after → A after`

---

## 拦截器 vs 中间件 vs 守卫 vs 管道

| 维度 | 中间件 | 守卫 | 拦截器 | 管道 |
| --- | --- | --- | --- | --- |
| **职责** | 请求预处理、日志、CORS | 权限认证、角色判断 | 响应转换、缓存、超时、异常转换 | 数据校验与类型转换 |
| **执行时机** | 守卫之前 | 拦截器之前 | 管道前后都有介入 | 控制器方法之前 |
| **能否访问路由元数据** | ❌ | ✅（`Reflector`） | ✅（`ExecutionContext`） | ✅（`PipeTransform`） |
| **能否修改响应** | ❌（只能预处理） | ❌（只能放行/拒绝） | ✅（`map`、`catchError`） | ❌（只改输入） |
| **能否短路请求** | ✅（不调 `next()`） | ✅（抛异常） | ✅（不调 `next.handle()`） | ✅（抛异常） |
| **异常处理** | 手动 try/catch | 抛 HttpException | `catchError` 操作符 | 抛异常 |
| **RxJS 支持** | ❌ | ❌ | ✅ 核心依赖 | ❌ |
| **典型场景** | 日志、CORS、body 解析 | JWT 验证、RBAC | 统一响应格式、缓存、超时 | DTO 校验、ParseIntPipe |

---

## 完整请求链路回顾

一个完整的 HTTP 请求在 NestJS 中经历的完整链路如下：

```
客户端请求
  │
  ▼
┌──────────────────────┐
│  1. 中间件 (Middleware) │  ← 日志、CORS、body 解析等
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  2. 守卫 (Guard)       │  ← 权限认证、角色判断；不通过直接抛 403
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  3. 拦截器 before      │  ← next.handle() 之前的代码
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  4. 管道 (Pipe)        │  ← 参数校验、类型转换；不通过直接抛 400
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  5. 控制器方法         │  ← 业务逻辑执行
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  6. 拦截器 after       │  ← RxJS 操作符处理响应数据
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  7. 异常过滤器         │  ← 捕获链路中任何未处理的异常，返回友好格式
│  (Exception Filter)   │
└──────────┬───────────┘
           ▼
      客户端响应
```

**关键记忆口诀**：中间件 → 守卫 → 拦截器前 → 管道 → 控制器 → 拦截器后 → 异常过滤器

---

## 关键知识点总结

1. **拦截器 = AOP 在 NestJS 的实现**，拥有 before / after 两个切入点
2. **`next.handle()` 返回 Observable**，所有后置处理都通过 RxJS 操作符完成
3. **`tap` 不改数据，`map` 改数据，`catchError` 处理异常**——三大核心操作符
4. **缓存拦截器可以"短路"**：不调用 `next.handle()`，直接 `of(data)` 返回
5. **`APP_INTERCEPTOR` 支持依赖注入**，`useGlobalInterceptors` 不支持
6. **多拦截器按洋葱模型嵌套**：先进后出（before LIFO → handler → after FIFO）
7. **`map` 不会处理异常**，异常走 `error` 通知，需要 `catchError` 捕获
8. **拦截器 vs 中间件**：中间件只能"前置"，拦截器能"前置 + 后置"
9. **拦截器 vs 守卫**：守卫决定"能不能进"，拦截器决定"进来后怎么包装"
10. **拦截器 vs 管道**：管道处理"输入"，拦截器处理"输出"

---

## 实战练习

### 练习一：实现请求限流拦截器

实现一个 `ThrottleInterceptor`，限制同一 IP 在指定时间窗口内的请求次数：

- 使用 `Map<string, { count: number; resetAt: number }>` 存储请求计数
- 默认限制：同一 IP 10 秒内最多 5 次请求
- 超出限制时抛出 `TooManyRequestsException`（HTTP 429）
- 在响应头中添加 `X-RateLimit-Remaining` 剩余次数

**提示**：在 `intercept` 的 before 阶段检查计数，决定是否放行。

### 练习二：实现响应压缩拦截器

实现一个 `CompressInterceptor`，对大于 1KB 的 JSON 响应做简化处理：

- 如果响应数据中有 `description` 字段，且内容超过 100 字符，截断为 100 字符并追加 `...`
- 如果响应数据是数组，且长度超过 20 条，只保留前 20 条并在响应中添加 `truncated: true` 标记
- 使用 `map` 操作符处理

**提示**：递归遍历对象，对 `description` 字段做截断处理。

### 练习三：组合拦截器实现完整请求追踪

实现一个 `TraceInterceptor`，为每个请求生成唯一 `traceId`：

- 在 before 阶段生成 `traceId`（可使用 `crypto.randomUUID()` 或简单的递增 ID）
- 将 `traceId` 附加到 `request` 对象上，方便后续中间件/守卫/日志读取
- 在 after 阶段通过 `map` 在响应体中添加 `traceId` 字段
- 在 `tap` 中打印包含 `traceId` 的日志

**提示**：可以结合 `LoggingInterceptor` 的模式，在同一个拦截器中完成日志与追踪。
