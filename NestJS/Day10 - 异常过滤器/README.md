# Day10 - 异常过滤器

异常过滤器是 NestJS 请求链路的最后一道防线。当 Controller、Service、Pipe、Guard、Interceptor 任何一处抛出异常时，过滤器负责统一捕获、记录日志、并把异常转换成结构化的错误响应。没有过滤器，前端会收到 Express 默认的纯文本错误或 500 状态码，既无法精细分支处理，也容易泄露实现细节。本章把"抛出异常 → 捕获异常 → 格式化响应"这条链路完整走通，并设计一套可扩展的自定义异常体系。

---

## 学习目标

完成本章后，你应能：

- 用一句话讲清异常过滤器在请求链路中的位置，以及它和 Pipe / Interceptor 的边界
- 列举 NestJS 内置的 HttpException 子类，知道每个子类对应哪个 HTTP 状态码
- 手写 `throw new HttpException(message, statusCode)` 与 `throw new NotFoundException(msg)` 两种抛出方式
- 实现 `ExceptionFilter` 接口，用 `@Catch()` 指定捕获的异常类型
- 用 `ArgumentsHost.switchToHttp()` 取出 Request / Response，手动 `res.status().json()` 返回错误响应
- 区分方法级、控制器级、全局级三种过滤器注册方式，知道 `useGlobalFilters` 与 `APP_FILTER` 的取舍
- 设计自己的业务异常体系：BusinessException 基类 + 领域异常子类 + 错误码枚举
- 设计统一错误响应格式 `{ code, message, details, timestamp, path }`，并解释 `code` 为何要与 HTTP 状态码解耦
- 说明异常过滤器与拦截器 `catchError` 的分工边界

---

## 理论知识讲解

### 1. NestJS 异常处理体系

NestJS 的异常处理分两层：

```
请求 ─► Middleware ─► Guard ─► Interceptor(before) ─► Pipe ─► Controller
                                                                    │
                                                                    ▼
                                                              抛出异常
                                                                    │
              ┌─────────────────────────────────────────────────────┤
              ▼                                                     │
        内置异常层                                                   │
   (默认处理 HttpException，                                     │
    返回 { statusCode, message, error })                            │
              │                                                     │
              ▼                                                     │
       自定义异常过滤器 (ExceptionFilter)  ◄─────────────────────────┘
       (按 @Catch 类型分发，统一格式化)
              │
              ▼
       响应返回前端
```

**内置异常层**：NestJS 自带一个全局异常处理器，专门捕获 `HttpException` 及其子类，把它们转换成 `{ statusCode, message, error }` 格式响应。其他未捕获异常会直接返回 500。

**自定义异常过滤器**：用户实现的 `ExceptionFilter`，可以覆盖默认行为，捕获更多异常类型，统一响应格式。一旦注册了自定义过滤器，匹配到的异常就由它处理，不再走内置层。

> 关键认知：过滤器只负责"异常已经发生"后的收尾工作，它不能阻止异常被抛出，也不能"修复"异常让请求继续。

### 2. HttpException 及其子类

NestJS 在 `@nestjs/common` 里提供了一组现成的异常类，都继承自 `HttpException`：

| 内置异常类 | HTTP 状态码 | 典型场景 |
|-----------|------------|---------|
| `BadRequestException` | 400 | 请求参数格式错误 |
| `UnauthorizedException` | 401 | 未登录、token 失效 |
| `NotFoundException` | 404 | 资源不存在 |
| `ForbiddenException` | 403 | 已登录但无权限 |
| `ConflictException` | 409 | 唯一约束冲突（重复注册） |
| `PayloadTooLargeException` | 413 | 上传文件超限 |
| `UnprocessableEntityException` | 422 | 语义错误（参数格式对但语义不对） |
| `InternalServerErrorException` | 500 | 服务端内部错误 |
| `NotImplementedException` | 501 | 接口未实现 |
| `BadGatewayException` | 502 | 上游服务异常 |
| `ServiceUnavailableException` | 503 | 服务不可用 |
| `GatewayTimeoutException` | 504 | 上游超时 |

#### 2.1 抛出异常的方式

```typescript
// 方式一：直接用 HttpException，手动传 status code
throw new HttpException('用户不存在', 404);

// 方式二：用子类，status code 已内置
throw new NotFoundException('用户不存在');
throw new BadRequestException('邮箱格式错误');

// 方式三：用子类 + 对象 response
throw new BadRequestException({
  message: ['邮箱格式错误', '密码不能为空'],
  error: 'Validation Failed',
});

// 方式四：在 Service 中根据业务条件抛出
if (!user) {
  throw new NotFoundException(`用户 ${id} 不存在`);
}
```

#### 2.2 异常的默认响应格式

不写任何自定义过滤器时，NestJS 内置层会把 `HttpException` 转成如下 JSON：

```json
{
  "statusCode": 404,
  "message": "用户不存在",
  "error": "Not Found"
}
```

这个格式能用，但不够友好：
- 没有业务错误码，前端只能靠 `message` 字符串匹配（脆弱）
- 没有时间戳、请求路径，排查问题不便
- `error` 字段是 HTTP 标准短语（"Not Found"），不携带业务信息

所以我们自己设计一套统一格式，详见第 8 节。

### 3. 异常过滤器 ExceptionFilter

#### 3.1 ExceptionFilter 接口

```typescript
export interface ExceptionFilter<T = any> {
  catch(exception: T, host: ArgumentsHost): void;
}
```

只需实现一个 `catch` 方法。`exception` 是被捕获的异常实例，`host` 是上下文对象。

#### 3.2 @Catch() 装饰器

`@Catch()` 决定过滤器能捕获哪些异常类型：

```typescript
@Catch(HttpException)              // 只捕获 HttpException 及其子类
export class HttpExceptionFilter implements ExceptionFilter { ... }

@Catch(BusinessException)          // 只捕获 BusinessException 及其子类
export class BusinessExceptionFilter implements ExceptionFilter { ... }

@Catch()                           // 不传参数 = 捕获所有异常（兜底）
export class AllExceptionsFilter implements ExceptionFilter { ... }
```

类型匹配规则：`exception instanceof CatchType`。子类也算。NestJS 会按 `@Catch` 类型自动分发，过滤器内部不用手动判断类型再 re-throw。

#### 3.3 ArgumentsHost

`ArgumentsHost` 是 NestJS 跨协议的上下文抽象。HTTP 场景下，用它取出 Express 的 Request / Response：

```typescript
@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  catch(exception: HttpException, host: ArgumentsHost) {
    // switchToHttp() 返回 HttpContext
    // getRequest() / getResponse() 返回 Express 的 req / res
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status = exception.getStatus();
    response.status(status).json({ ... });
  }
}
```

> 提示：`ArgumentsHost` 还能 `switchToWs()` / `switchToRpc()`，让同一套过滤器适配 HTTP / WebSocket / gRPC。本章只演示 HTTP。

#### 3.4 Response 对象操作

注意必须显式调用 `res.status().json()` 把响应发出去。否则请求会一直挂起直到超时。

```typescript
response
  .status(404)              // 设置 HTTP 状态码
  .json({                   // 发送 JSON 响应
    code: 'ARTICLE_NOT_FOUND',
    message: '文章不存在',
    timestamp: new Date().toISOString(),
    path: request.url,
  });
```

### 4. 过滤器应用方式

NestJS 提供三种注册位置，优先级从高到低：

```
方法级  >  控制器级  >  全局级
```

#### 4.1 方法级

只对单条路由生效：

```typescript
@Get('special')
@UseFilters(new HttpExceptionFilter())
specialHandler() { ... }
```

#### 4.2 控制器级

对整个控制器的所有路由生效：

```typescript
@Controller('articles')
@UseFilters(HttpExceptionFilter)
export class ArticlesController { ... }
```

#### 4.3 全局级

对整个应用生效，有两种写法：

**写法一：`app.useGlobalFilters`（在 main.ts）**

```typescript
app.useGlobalFilters(
  new AllExceptionsFilter(),
  new HttpExceptionFilter(),
  new BusinessExceptionFilter(),
);
```

- 优点：简单直接
- 缺点：过滤器实例是手动 `new` 出来的，**无法注入依赖**

**写法二：`APP_FILTER` 令牌（在 Module 的 providers）**

```typescript
import { APP_FILTER } from '@nestjs/core';

@Module({
  providers: [
    { provide: APP_FILTER, useClass: AllExceptionsFilter },
    { provide: APP_FILTER, useClass: HttpExceptionFilter },
    { provide: APP_FILTER, useClass: BusinessExceptionFilter },
  ],
})
export class AppModule {}
```

- 优点：NestJS 容器实例化过滤器，**支持 DI**（可以注入 Logger、Config、Service 等）
- 缺点：写法稍繁琐

> 推荐：生产环境用 `APP_FILTER`，方便 DI；快速原型用 `useGlobalFilters`。本项目演示采用 `APP_FILTER`。

#### 4.4 多个全局过滤器的执行顺序

`APP_FILTER` 注册顺序 = 洋葱模型的层叠顺序：

```
先注册  =  外层（兜底，最后被到达）
后注册  =  内层（贴近 handler，最先被到达）
```

因此注册顺序为：`All → Http → Business`，让 `BusinessExceptionFilter` 在最内层优先处理业务异常。配合 `@Catch(具体类型)`，三类异常各自走对应过滤器，互不干扰。

### 5. 自定义异常体系

#### 5.1 设计动机

NestJS 内置的 `HttpException` 只携带 HTTP 语义信息（状态码 + message），但实际业务中：
- 同一个 HTTP 404 可能是"用户不存在"或"文章不存在"或"订单不存在"
- 前端需要根据**业务码**而非 HTTP 状态码做不同处理（跳转、提示、重试）
- 业务码需要集中管理，避免散落在各处硬编码字符串

#### 5.2 三层结构

```
Error
  └─ BusinessException              业务异常基类（带 errorCode / httpStatus / details）
       ├─ UserNotFoundException     用户域
       ├─ ArticleNotFoundException  文章域
       ├─ ArticleLockedException    文章域
       └─ ValidationException       校验域
```

#### 5.3 错误码枚举

```typescript
export enum ExceptionCode {
  USER_NOT_FOUND = 'USER_NOT_FOUND',
  ARTICLE_NOT_FOUND = 'ARTICLE_NOT_FOUND',
  ARTICLE_LOCKED = 'ARTICLE_LOCKED',
  VALIDATION_FAILED = 'VALIDATION_FAILED',
  // ...
}

// 业务码 → 默认 HTTP 状态码的映射表
export const DEFAULT_HTTP_STATUS: Record<ExceptionCode, number> = {
  [ExceptionCode.USER_NOT_FOUND]: 404,
  [ExceptionCode.ARTICLE_NOT_FOUND]: 404,
  [ExceptionCode.ARTICLE_LOCKED]: 423,
  [ExceptionCode.VALIDATION_FAILED]: 400,
  // ...
};
```

#### 5.4 业务异常基类

```typescript
export class BusinessException extends Error {
  readonly errorCode: ExceptionCode;
  readonly httpStatus: number;
  readonly details?: unknown;

  constructor(
    errorCode: ExceptionCode,
    message?: string,
    options?: { httpStatus?: number; details?: unknown; cause?: unknown },
  ) {
    super(message ?? errorCode, { cause: options?.cause });
    this.name = this.constructor.name;
    this.errorCode = errorCode;
    this.httpStatus = options?.httpStatus ?? DEFAULT_HTTP_STATUS[errorCode] ?? 500;
    this.details = options?.details;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
```

> **为什么不继承 HttpException？** 有意为之——避免被 `@Catch(HttpException)` 抢先捕获。业务异常只走 `@Catch(BusinessException)`，保证 errorCode 不被默认格式吞掉。

#### 5.5 领域异常子类

```typescript
export class ArticleNotFoundException extends BusinessException {
  constructor(articleId: string | number) {
    super(ExceptionCode.ARTICLE_NOT_FOUND, `文章不存在: ${articleId}`, {
      details: { articleId },
    });
  }
}

// Service 里使用
if (!article) {
  throw new ArticleNotFoundException(id);   // 比 throw new BusinessException('ARTICLE_NOT_FOUND', ...) 清晰
}
```

### 6. 过滤器分工

三个全局过滤器各司其职：

| 过滤器 | @Catch 参数 | 职责 | 典型异常 |
|--------|------------|------|---------|
| `BusinessExceptionFilter` | `BusinessException` | 把业务码 + httpStatus 转成统一响应 | `ArticleNotFoundException` |
| `HttpExceptionFilter` | `HttpException` | 把内置异常的默认格式改成统一格式 | `NotFoundException`、`BadRequestException` |
| `AllExceptionsFilter` | （无参数） | 兜底所有未捕获异常，返回 500 | `TypeError`、数据库错误 |

执行流程：

```
异常被抛出
   │
   ▼
NestJS 按 @Catch 类型查找匹配的过滤器
   │
   ├─ 是 BusinessException? ─► BusinessExceptionFilter  ─► 返回 { code: 业务码, ... }
   │
   ├─ 是 HttpException?     ─► HttpExceptionFilter      ─► 返回 { code: HTTP_xxx, ... }
   │
   └─ 其他?                 ─► AllExceptionsFilter      ─► 返回 { code: INTERNAL_ERROR, ... } + 500
```

> 关键：由于每个过滤器都用 `@Catch` 指定了具体类型，NestJS 自动按类型分发，过滤器内部不需要 `if (e instanceof X) re-throw` 这种判断。

### 7. 统一错误响应格式设计

所有过滤器最终都返回这种格式：

```typescript
interface ErrorResponseDto {
  code: string;          // 业务错误码，前端据此分支处理
  message: string;       // 面向用户的提示，可直接展示
  details?: unknown;     // 附加细节（校验字段、引用 ID 等），可选
  timestamp: string;     // ISO 时间字符串，便于排查
  path: string;          // 触发异常的请求路径
}
```

#### 7.1 为什么 code 与 HTTP 状态码解耦

```
HTTP 404  ←  USER_NOT_FOUND        (跳转登录页)
HTTP 404  ←  ARTICLE_NOT_FOUND     (跳转列表页)
HTTP 404  ←  ORDER_NOT_FOUND       (跳转订单列表)
```

- HTTP 状态码：粗粒度的传输层语义，给浏览器/网关/监控系统用
- 业务 code：细粒度的业务语义，给前端逻辑用

同一个 404 在前端可以有三种不同处理，靠 `code` 字段区分。反过来，同一个 `USER_NOT_FOUND` 在不同接口下可能想返回不同 HTTP 状态码（404 或 422），也可以通过 `httpStatus` 字段灵活配置。

#### 7.2 实际响应示例

业务异常：

```json
{
  "code": "ARTICLE_NOT_FOUND",
  "message": "文章不存在: 99",
  "details": { "articleId": 99 },
  "timestamp": "2025-07-26T08:00:00.000Z",
  "path": "/api/v1/articles/99"
}
```

HTTP 异常：

```json
{
  "code": "HTTP_403",
  "message": "只有管理员可以删除文章",
  "details": { "error": "Forbidden" },
  "timestamp": "2025-07-26T08:00:00.000Z",
  "path": "/api/v1/articles/1"
}
```

兜底异常：

```json
{
  "code": "INTERNAL_ERROR",
  "message": "服务器内部错误，请稍后重试",
  "details": { "name": "Error", "message": "数据库连接超时: ECONNECTIONTIMEOUT" },
  "timestamp": "2025-07-26T08:00:00.000Z",
  "path": "/api/v1/articles/demo/risky"
}
```

### 8. 异常过滤器 vs 拦截器的异常处理

拦截器也能用 `catchError` 捕获异常，二者如何分工？

| 维度 | 异常过滤器 | 拦截器 catchError |
|------|-----------|------------------|
| 触发时机 | 异常已被抛出，请求链路结束 | RxJS 流中的错误，可以"恢复" |
| 能否恢复 | 不能，只能格式化后返回 | 能，可以 `switchMap` 回正常流继续返回成功响应 |
| 能否修改成功响应 | 不能 | 能（拦截器同时管 before/after） |
| 跨协议支持 | HTTP / WS / RPC 通用（通过 ArgumentsHost） | 主要用于 HTTP |
| 典型用法 | 统一错误格式、记录日志、脱敏堆栈 | 重试、降级、缓存兜底、链路追踪 |

**经验法则**：

- 只是格式化错误响应 → 用过滤器
- 需要把错误"恢复"成成功响应（如降级返回缓存数据）→ 用拦截器
- 两者可以共存：拦截器先处理可恢复的，过滤器兜底不可恢复的

```typescript
// 拦截器：捕获后返回降级数据（请求"成功"了）
@Injectable()
export class FallbackInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler) {
    return next.handle().pipe(
      catchError((err) => {
        if (err instanceof ServiceUnavailableException) {
          return of({ data: [], fallback: true });  // 返回空数组，状态码 200
        }
        throw err;  // 不可恢复，继续抛出，交给过滤器
      }),
    );
  }
}
```

---

## 关键知识点总结

### 内置异常类速查表

| 异常类 | 状态码 | 触发场景 |
|--------|--------|---------|
| `BadRequestException` | 400 | 参数格式错误 |
| `UnauthorizedException` | 401 | 未登录 |
| `ForbiddenException` | 403 | 无权限 |
| `NotFoundException` | 404 | 资源不存在 |
| `ConflictException` | 409 | 唯一约束冲突 |
| `PayloadTooLargeException` | 413 | 文件过大 |
| `UnprocessableEntityException` | 422 | 语义错误 |
| `InternalServerErrorException` | 500 | 服务器错误 |
| `NotImplementedException` | 501 | 接口未实现 |
| `BadGatewayException` | 502 | 上游异常 |
| `ServiceUnavailableException` | 503 | 服务不可用 |
| `GatewayTimeoutException` | 504 | 上游超时 |

### HTTP 状态码对照表

| 状态码 | 名称 | 含义 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 204 | No Content | 成功但无内容返回 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 已认证但无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 413 | Payload Too Large | 请求体过大 |
| 422 | Unprocessable Entity | 语义错误 |
| 423 | Locked | 资源被锁定 |
| 500 | Internal Server Error | 服务器内部错误 |
| 502 | Bad Gateway | 上游网关错误 |
| 503 | Service Unavailable | 服务暂不可用 |
| 504 | Gateway Timeout | 网关超时 |

### 过滤器三连问

1. **为什么需要统一格式？** 前端可以用同一套逻辑处理所有错误，靠 `code` 字段分支。
2. **为什么业务异常不继承 HttpException？** 避免被 `@Catch(HttpException)` 抢先捕获，保证业务码不丢失。
3. **为什么需要兜底过滤器？** 数据库错误、第三方 SDK 异常等不可预期，必须统一返回 500 而非暴露堆栈。

---

## 实战练习

### 练习 1：扩展业务异常体系

在 `src/exceptions/` 下新增：

1. `OrderNotFoundException`（订单不存在，映射 404）
2. `InsufficientBalanceException`（余额不足，映射 422）
3. 在 `ExceptionCode` 枚举里补充对应错误码

然后新增 `orders.controller.ts`，提供两个接口触发上述异常，验证响应格式。

### 练习 2：让过滤器支持 DI

把 `AllExceptionsFilter` 改造成依赖注入 `LoggerService`（自定义的，非内置 Logger）：

1. 在 `AllExceptionsFilter` 构造函数里注入 `LoggerService`
2. 在 `AppModule` 里把 `LoggerService` 注册为 provider
3. 验证过滤器能正确调用 `loggerService.error(...)`

> 提示：必须用 `APP_FILTER` 注册（`useGlobalFilters` 不支持 DI）。

### 练习 3：用拦截器实现降级

新增 `FallbackInterceptor`，对 `ServiceUnavailableException` 做降级处理：

1. 在 `ArticlesService` 里新增一个会抛 `ServiceUnavailableException` 的方法
2. 拦截器捕获该异常后返回 `{ data: [], fallback: true }`，状态码 200
3. 对比：不挂拦截器时走过滤器返回 503，挂了拦截器后返回 200 + 降级数据

---

## 本章代码结构

```
Day10 - 异常过滤器/
├── Code/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.build.json
│   ├── nest-cli.json
│   └── src/
│       ├── main.ts                              # 启动入口，演示 useGlobalFilters（注释对照）
│       ├── app.module.ts                        # 根模块，APP_FILTER 注册三个全局过滤器
│       ├── common/
│       │   └── error-response.dto.ts            # 统一错误响应 DTO
│       ├── exceptions/
│       │   ├── exception-code.constants.ts      # 业务错误码枚举 + HTTP 映射表
│       │   ├── business.exception.ts            # 业务异常基类
│       │   └── domain.exceptions.ts             # 领域异常子类（UserNotFound 等）
│       ├── filters/
│       │   ├── http-exception.filter.ts         # 捕获 HttpException
│       │   ├── all-exceptions.filter.ts         # 兜底捕获所有异常
│       │   └── business-exception.filter.ts     # 捕获业务异常
│       └── articles/
│           ├── articles.controller.ts           # 演示抛出业务异常 + 方法级过滤器
│           ├── articles.service.ts              # 业务异常抛出示例
│           └── articles.module.ts
└── README.md
```

### 运行方式

```bash
cd "Day10 - 异常过滤器/Code"
npm install
npm run start:dev
```

### 体验路径

| 请求 | 触发异常 | 命中过滤器 | 响应 |
|------|---------|-----------|------|
| `GET /api/v1/articles/99` | ArticleNotFoundException | BusinessExceptionFilter | 404 + ARTICLE_NOT_FOUND |
| `PATCH /api/v1/articles/2 {"title":"x"}` | ArticleLockedException | BusinessExceptionFilter | 423 + ARTICLE_LOCKED |
| `POST /api/v1/articles/1/publish {}` | ValidationException | BusinessExceptionFilter | 400 + VALIDATION_FAILED |
| `GET /api/v1/articles/demo/search?title=不存在` | NotFoundException | HttpExceptionFilter | 404 + HTTP_404 |
| `DELETE /api/v1/articles/1` | ForbiddenException | HttpExceptionFilter | 403 + HTTP_403 |
| `GET /api/v1/articles/demo/risky` | 原生 Error | AllExceptionsFilter | 500 + INTERNAL_ERROR |
| `GET /api/v1/articles/demo/method-filter` | （无异常） | 方法级 HttpExceptionFilter | 200（过滤器不触发） |
