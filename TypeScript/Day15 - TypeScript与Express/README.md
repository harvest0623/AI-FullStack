# Day15 - TypeScript 与 Express

> 本篇把 TypeScript 类型系统真正「搬到」后端：用 TS 重写一个分层 Express 应用，把路由、服务、中间件、错误处理、响应封装全部类型化，让编译器帮你挡住前端到数据库链路上的低级错误。这是进入 NestJS 之前最后一次「亲手写底层」的实战——你会亲手实现 routes/services/middlewares 三层结构，再过几天回头看 NestJS，会发现它的 Controller / Provider / Guard / Pipe 只是把这些手工拼装换成装饰器 + 依赖注入自动装配而已。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 @types/express：让 Express 拥抱 TS](#21-typesexpress让-express-拥抱-ts)
  - [2.2 Express 的 TS 类型核心：Request / Response / NextFunction](#22-express-的-ts-类型核心request--response--nextfunction)
  - [2.3 扩展 Request 对象：declare module 模块增强](#23-扩展-request-对象declare-module-模块增强)
  - [2.4 express.Router 的泛型应用与路由参数类型](#24-expressrouter-的泛型应用与路由参数类型)
  - [2.5 中间件的类型签名：RequestHandler / ErrorRequestHandler](#25-中间件的类型签名requesthandler--errorrequesthandler)
  - [2.6 自定义 Error 类与错误处理中间件类型化](#26-自定义-error-类与错误处理中间件类型化)
- [三、用 TS 重写完整 Express 应用（分层架构）](#三用-ts-重写完整-express-应用分层架构)
  - [3.1 项目目录结构](#31-项目目录结构)
  - [3.2 types/：DTO、接口、自定义错误](#32-typesdto接口自定义错误)
  - [3.3 middlewares/：类型化中间件](#33-middlewares类型化中间件)
  - [3.4 utils/：响应封装与异步包装](#34-utils响应封装与异步包装)
  - [3.5 services/：业务逻辑层](#35-services业务逻辑层)
  - [3.6 routes/：类型化路由](#36-routes类型化路由)
  - [3.7 app.ts 与 server.ts：入口与启动](#37-appts-与-serverts入口与启动)
- [四、类型安全实践](#四类型安全实践)
  - [4.1 DTO 模式：前后端契约的代码化](#41-dto-模式前后端契约的代码化)
  - [4.2 TS 类型校验 + 运行时校验：Zod 简介](#42-ts-类型校验--运行时校验zod-简介)
  - [4.3 异步错误包装器 asyncHandler 的类型签名](#43-异步错误包装器-asyn handler-的类型签名)
  - [4.4 统一响应封装的泛型设计](#44-统一响应封装的泛型设计)
- [五、与 NestJS 的衔接](#五与-nestjs-的衔接)
- [六、关键知识点总结](#六关键知识点总结)
- [七、实战练习](#七实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 说出 `@types/express` 提供的核心类型（`Request` / `Response` / `NextFunction` / `RequestHandler` / `ErrorRequestHandler` / `Express`）及其各自用途。
2. 写出 `Request<TParams, TResBody, TReqBody, TReqQuery>` 四个泛型参数的含义，并在路由处理函数中正确应用。
3. 通过 `declare module 'express-serve-static-core'` 扩展 `Request` 接口，添加 `user` / `requestId` 等自定义字段，并解释为什么扩展的是 `express-serve-static-core` 而不是 `express`。
4. 区分 `RequestHandler` 与 `ErrorRequestHandler` 两种中间件签名，并解释为什么错误处理中间件必须有 4 个参数。
5. 设计自定义 Error 类继承体系（`AppError` → `NotFoundError` / `ValidationError` / `UnauthorizedError`），并用 `instanceof` 在错误处理中间件中分支处理。
6. 实现一个分层 Express 应用：`types` / `routes` / `services` / `middlewares` / `utils` 各司其职，类型在层与层之间显式流动。
7. 写出泛型 `sendSuccess<T>` 与 `asyncHandler` 的类型签名，理解它们如何同时保证调用点类型安全与内部实现简洁。
8. 用 DTO（Data Transfer Object）模式隔离内部模型与对外契约，避免数据库字段直接暴露给前端。
9. 解释 TS 类型校验（编译期）与 Zod 运行时校验（运行期）的互补关系，并能给出一个最小可运行的 Zod 校验示例。
10. 描述本应用的分层结构与 NestJS 的 Controller / Provider / Middleware / Pipe / Guard 的对应关系，为进入 NestJS 做好心智铺垫。

---

## 二、理论知识讲解

### 2.1 @types/express：让 Express 拥抱 TS

Express 本身是用纯 JS 写的，自身不携带任何类型信息。要在 TS 项目里安全使用 Express，需要安装它的类型声明包：

```bash
npm install express
npm install -D @types/express
```

`@types/express` 来自 DefinitelyTyped 社区维护，它为 Express 的所有导出补上了类型声明，让你能拿到这些关键类型：

| 类型 | 来源 | 用途 |
|------|------|------|
| `Request` | `express-serve-static-core` | 表示 HTTP 请求，包含 `params` / `body` / `query` / `headers` 等 |
| `Response` | `express-serve-static-core` | 表示 HTTP 响应，包含 `json()` / `status()` / `send()` 等 |
| `NextFunction` | `express-serve-static-core` | 调用 `next()` 把控制权交给下一个中间件 |
| `RequestHandler` | `express-serve-static-core` | 标准中间件函数签名 `(req, res, next) => void` |
| `ErrorRequestHandler` | `express-serve-static-core` | 错误处理中间件签名 `(err, req, res, next) => void` |
| `Express` | `express` | 应用实例类型，`express()` 的返回值 |
| `Router` | `express-serve-static-core` | 路由器类型，`express.Router()` 的返回值 |

> 💡 注意一个常被忽略的细节：`Request` / `Response` 等核心接口**实际定义在 `express-serve-static-core` 这个包里**，`express` 只是 re-export。这一点在「扩展 Request 类型」时会变得至关重要——`declare module` 必须指向真正的定义位置才能生效。

### 2.2 Express 的 TS 类型核心：Request / Response / NextFunction

`Request` 是 `@types/express` 最常被定制化的类型，它的完整签名（简化版）如下：

```ts
interface Request<
  P = ParamsDictionary,         // 路由参数类型，如 { id: string }
  ResBody = any,                // 响应体类型
  ReqBody = any,                // 请求体类型
  ReqQuery = ParsedQs,          // 查询字符串类型
> extends http.IncomingMessage {
  params: P;
  body: ReqBody;
  query: ParsedQuery<ReqQuery>;
  headers: IncomingHttpHeaders;
  // ... 还有 user / requestId 等扩展字段
}
```

四个泛型参数的含义与典型用法：

| 位置 | 泛型 | 含义 | 示例 |
|------|------|------|------|
| 1 | `P` (Params) | 路由路径参数 | `Request<{ id: string }>` |
| 2 | `ResBody` | 响应体类型（约束 `res.json(...)` 的参数） | `Request<{}, ArticleDTO>` |
| 3 | `ReqBody` | 请求体类型（约束 `req.body`） | `Request<{}, unknown, CreateArticleDTO>` |
| 4 | `ReqQuery` | 查询字符串类型（约束 `req.query`） | `Request<{}, unknown, unknown, ArticleListQuery>` |

`Response<ResBody>` 也有一个泛型参数，表示响应体类型，但实际项目中往往让统一响应封装接管，很少在路由层显式标注。

`NextFunction` 比较简单：`() => void`，但配合 `next(err)` 可以传递错误。

> ⚠️ 路由参数永远是 `string`：即使路径写成 `/:id`，`req.params.id` 的类型仍是 `string`。如果你定义 `Request<{ id: number }>`，TS 不会报错，但运行时 `req.params.id` 仍是字符串，需要手动 `Number()` 转换并校验——这是新手最常踩的坑。

### 2.3 扩展 Request 对象：declare module 模块增强

Express 的 `Request` 类型只覆盖标准 HTTP 字段。真实业务里我们经常需要往 `req` 上挂自定义字段，最常见的两类：

- **`req.user`**：鉴权中间件解析 token 后挂载的当前用户
- **`req.requestId`**：链路追踪 ID，用于关联同一次请求的所有日志

TS 通过 **模块增强（declaration merging）** 让你「在不动 `@types/express` 源码的前提下，给已有接口追加字段」：

```ts
// types/express.d.ts
import type { RequestUser } from './index';

declare module 'express-serve-static-core' {
  interface Request {
    user?: RequestUser;
    requestId?: string;
  }
}
```

几个关键点：

1. **扩展的是 `express-serve-static-core`，不是 `express`**：因为 `Request` 接口的真正定义在前者，对 `express` 模块做 `declare module` 不生效。
2. **字段建议设为可选（`?:`）**：因为并不是所有路由都经过鉴权 / 日志中间件，强必填会导致健康检查等公共路由报错。
3. **声明文件需被 `tsconfig.json` 的 `include` 覆盖**：本项目的 `include: ["*.ts", "**/*.ts"]` 已经覆盖所有子目录，无需额外配置。
4. **只要项目里有任何一个文件 `import` 了该声明涉及的模块，模块增强就会在整个项目生效**——这是 declaration merging 的全局性特征。

这种模式在 NestJS 中也会用到：`@nestjs/platform-express` 内部就用 `declare module` 扩展了 Request；自定义装饰器（如 `@CurrentUser()`）本质上也是在装饰「被扩展过的 req」。

### 2.4 express.Router 的泛型应用与路由参数类型

`express.Router()` 返回一个 `Router` 实例，可以挂载一组路由并整体 `app.use('/api/articles', router)` 注册。Router 没有顶层泛型参数，**每个路由方法（`router.get` / `router.post` / ...）自己有泛型**：

```ts
router.get(
  '/:id',
  asyncHandler(async (req: Request<{ id: string }>, res: Response) => {
    //               ↑ 路由参数泛型，约束 req.params
    const id = Number(req.params.id);  // TS 知道 req.params.id 是 string
    // ...
  }),
);
```

实践建议：

1. **路由参数始终声明为 `string`**：哪怕路径是 `/api/articles/:id`，`req.params.id` 在运行时也是字符串。
2. **请求体泛型对应 DTO 类型**：`Request<P, ResBody, CreateArticleDTO>` 让 `req.body` 自动推断为 `CreateArticleDTO`，访问未定义字段会报错。
3. **查询参数泛型对应 Query 类型**：注意 `query` 原始值都是 `string | string[] | ParsedQs | ParsedQs[]`，应在 DTO 里写 `page?: string` 而不是 `page?: number`，再在服务层显式转换。
4. **`Record<string, never>` 表示无参数**：当路由没有路径参数时，写 `Request<Record<string, never>, ...>` 比 `Request<{}>` 更严格——后者等价于 `ParamsDictionary`，可能漏过未声明的参数。

### 2.5 中间件的类型签名：RequestHandler / ErrorRequestHandler

Express 中间件本质是函数，TS 为它提供了两种类型别名：

```ts
type RequestHandler<
  P = ParamsDictionary,
  ResBody = any,
  ReqBody = any,
  ReqQuery = ParsedQs,
> = (req: Request<P, ResBody, ReqBody, ReqQuery>, res: Response<ResBody>, next: NextFunction) => void;

type ErrorRequestHandler<
  P = ParamsDictionary,
  ResBody = any,
  ReqBody = any,
  ReqQuery = ParsedQs,
> = (err: any, req: Request<P, ResBody, ReqBody, ReqQuery>, res: Response<ResBody>, next: NextFunction) => void;
```

两者的差异只有「第一个参数是不是 `err`」：

| 类型 | 参数数量 | 触发条件 | 注册方式 |
|------|---------|---------|---------|
| `RequestHandler` | 3 个 `(req, res, next)` | 正常中间件 / 路由 | `app.use(handler)` / `app.get(path, handler)` |
| `ErrorRequestHandler` | 4 个 `(err, req, res, next)` | 前面有 `next(err)` 被调用 | `app.use(errorHandler)`（必须 4 参数） |

> ⚠️ **Express 用「参数个数」识别错误处理中间件**：如果你写的中间件恰好是 4 个参数但没用 `ErrorRequestHandler` 类型，Express 也会把它当作错误处理器；反过来，如果你声明了 4 参数但只用了 3 个，Express 不会识别。TS 类型在这里的作用是「防止你手滑少写一个参数」。

```ts
// 正确：标准中间件
export const logger: RequestHandler = (req, res, next) => { /* ... */ next(); };

// 正确：错误处理中间件
export const errorHandler: ErrorRequestHandler = (err, req, res, _next) => {
  if (err instanceof AppError) { /* ... */ }
};
```

### 2.6 自定义 Error 类与错误处理中间件类型化

Express 默认错误处理只会返回 500 + 堆栈，无法区分「业务错误」与「系统错误」。工程化做法是：

1. 定义 `AppError` 基类，携带 `statusCode` / `code` / `details`。
2. 派生 `NotFoundError` / `ValidationError` / `UnauthorizedError` 等子类，固定状态码。
3. 错误处理中间件用 `instanceof` 分支，业务错误按 `statusCode` 返回，未捕获错误一律 500。

```ts
export class AppError extends Error {
  public readonly statusCode: number;
  public readonly code: string;
  public readonly details?: unknown;

  constructor(message: string, statusCode = 500, code = 'INTERNAL_ERROR', details?: unknown) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
    // 关键：修复 ES5 target 下子类 instanceof 失效问题
    Object.setPrototypeOf(this, new.target.prototype);
    Error.captureStackTrace?.(this, this.constructor);
  }
}
```

**几个容易踩的坑**：

1. **`Object.setPrototypeOf(this, new.target.prototype)`**：TS 编译到 ES5 时，`class extends Error` 的 `instanceof` 会失效（这是 V8 的老 bug）。这一行手动修复原型链，是 `instanceof AppError` 在错误处理中间件能正确分支的前提。
2. **`Error.captureStackTrace?.(this, this.constructor)`**：可选链兼容非 V8 环境，避免在 Safari 等浏览器报错（Node 端可省略）。
3. **`name = this.constructor.name`**：让 `NotFoundError` 的 `err.name` 是 `'NotFoundError'` 而不是 `'Error'`，便于日志区分。
4. **错误处理中间件必须是 4 参数**：Express 5 改成了「async 中间件抛错自动捕获」，但目前主流仍是 Express 4，4 参数约定不变。

---

## 三、用 TS 重写完整 Express 应用（分层架构）

### 3.1 项目目录结构

```
Code/
├── types/
│   ├── index.ts              # DTO、接口、自定义 Error 类
│   └── express.d.ts          # 扩展 Express.Request，增加 user / requestId
├── middlewares/
│   ├── logger.ts             # 类型化日志中间件 (RequestHandler)
│   ├── auth.ts               # 鉴权 + 角色守卫 (扩展 Request.user)
│   ├── error-handler.ts      # 错误处理中间件 (ErrorRequestHandler)
│   └── async-handler.ts      # 异步包装器 (把 rejection 转 next(err))
├── utils/
│   └── response.ts           # 统一响应封装 sendSuccess<T> / sendError
├── services/
│   └── article-service.ts    # 业务逻辑层 (implements IArticleService)
├── routes/
│   └── articles.ts           # 类型化文章路由 (Request 泛型 + DTO)
├── app.ts                    # 应用入口 (挂载中间件 + 路由)
├── server.ts                 # 启动服务 (含 curl 测试命令)
├── package.json
└── tsconfig.json
```

这是一个典型的「按职责分层」结构，每一层只依赖下一层：

```
HTTP 请求
   ↓
middlewares（日志 / 鉴权）         ← 横切关注点
   ↓
routes（路由分发 + DTO 校验入口）   ← 表现层
   ↓
services（业务逻辑）                ← 业务层
   ↓
types（类型契约中心）               ← 类型层，被所有层共享
   ↓
HTTP 响应（经 utils/response 统一封装）
```

### 3.2 types/：DTO、接口、自定义错误

`types/index.ts` 是整个应用的「类型契约中心」，被所有层共享。它包含四部分：

1. **领域模型** `Article`：描述数据库实体形态，含 `authorId` 等内部字段。
2. **DTO** `CreateArticleDTO` / `UpdateArticleDTO` / `ArticleDTO` / `PaginatedDTO<T>`：接口入参 / 出参契约，**剥离内部字段**（如 `authorId` 不应暴露给前端）。
3. **服务接口** `IArticleService`：服务层契约，所有方法返回 Promise，便于未来切换异步存储；在 NestJS 中此类会被标注 `@Injectable()`，由 Controller 通过构造函数注入。
4. **自定义 Error 体系** `AppError` + 子类：让错误处理中间件能按类型分支返回合适状态码。

```ts
// DTO 示例：请求体 vs 响应体
export interface CreateArticleDTO {
  title: string;
  content: string;
}

export type ArticleDTO = Omit<Article, 'authorId'>;  // 响应剥离 authorId
export type UpdateArticleDTO = Partial<Pick<Article, 'title' | 'content'>>;
```

> 💡 DTO 的关键价值：让前端永远看不到 `authorId` / `createdAt` 等内部字段，哪怕后端模型新增内部字段，对外契约也不会被破坏。这正是「契约驱动开发」的核心。

### 3.3 middlewares/：类型化中间件

四个中间件全部用 `RequestHandler` 或 `ErrorRequestHandler` 标注，让类型在「中间件链」中流动：

| 文件 | 类型签名 | 职责 |
|------|---------|------|
| `logger.ts` | `RequestHandler` | 生成 `requestId`，记录请求方法 / 路径 / 状态码 / 耗时 |
| `auth.ts` | `RequestHandler`（含工厂 `requireRole`） | 解析 token 挂载 `req.user`，或基于角色拦截 |
| `error-handler.ts` | `ErrorRequestHandler` | 按错误类型分支返回 4xx / 5xx |
| `async-handler.ts` | `(fn) => RequestHandler` | 把 async 函数的 rejection 转 `next(err)` |

`async-handler.ts` 是最值得细看的一个——它被设计为**泛型函数**，让调用点的 `Request<{ id: string }>` 等泛型参数能被 TS 自动推断并透传到返回的 `RequestHandler`，保证 `router.get(path, handler)` 类型匹配。内部把 Promise 的 rejection 转给 `next`：

```ts
type AsyncRequestHandler<
  P = any, ResBody = any, ReqBody = any, ReqQuery = any,
> = (
  req: Request<P, ResBody, ReqBody, ReqQuery>,
  res: Response<ResBody>,
  next: NextFunction,
) => Promise<unknown> | unknown;

export function asyncHandler<
  P = any, ResBody = any, ReqBody = any, ReqQuery = any,
>(
  fn: AsyncRequestHandler<P, ResBody, ReqBody, ReqQuery>,
): RequestHandler<P, ResBody, ReqBody, ReqQuery> {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
```

> ⚠️ **为什么不能用 `Parameters<RequestHandler>` 反向推导参数元组？** 因为 `RequestHandler` 默认泛型是 `ParamsDictionary`，而路由处理函数往往显式标注了更具体的 `Request<{ id: string }>`，函数参数逆变会导致赋值失败（TS2345）。必须把 asyncHandler 写成泛型函数让 TS 主动推断泛型参数。

这样路由层就可以写：

```ts
router.get('/:id', asyncHandler(async (req, res) => {
  const article = await articleService.getById(Number(req.params.id));
  sendSuccess(res, article);
}));
```

业务里 `throw new NotFoundError(...)` 就能被错误处理中间件自动接住，不需要 try/catch 包裹。

### 3.4 utils/：响应封装与异步包装

`utils/response.ts` 提供两个泛型函数：

```ts
export function sendSuccess<T>(res: Response, data: T, message = 'OK', requestId?: string): Response;
export function sendError(res: Response, statusCode: number, message: string, errorType?: string, details?: unknown, requestId?: string): Response;
```

**设计要点**：

1. `sendSuccess` 用泛型 `<T>`，让 `data` 的类型在调用点被推断（`sendSuccess(res, article)` 中 `T = ArticleDTO`），避免重复标注。
2. 成功响应 `code = 0`，失败响应 `code = HTTP 状态码`，前端用 `code === 0` 判断成功。
3. 所有响应都附 `timestamp` 与 `requestId`，便于排查时序问题与日志关联。
4. `sendError` 把 `errorType`（如 `'NOT_FOUND'`）单独抽出，让前端能区分不同错误类型并做差异化提示（如 `VALIDATION_ERROR` 高亮表单字段、`UNAUTHORIZED` 跳登录页）。

### 3.5 services/：业务逻辑层

`services/article-service.ts` 是分层架构的业务层，特点：

1. **`implements IArticleService`**：强制实现所有契约方法，类型层保证不漏。
2. **所有方法返回 Promise**：即便现在是同步内存数组，未来切换到数据库时无需改 Controller。
3. **运行时校验保留在服务层**：TS 类型只在编译期有效，运行时仍需 `if (!input.title?.trim()) throw new ValidationError(...)`。
4. **`toDTO()` 私有方法**：把领域模型 `Article` 转换为 DTO `ArticleDTO`，剥离 `authorId`，保证内部字段不外泄。

```ts
export class ArticleService implements IArticleService {
  async create(input: CreateArticleDTO, authorId: string): Promise<ArticleDTO> {
    if (!input.title?.trim()) throw new ValidationError('title 不能为空');
    // ...
    return this.toDTO(article);
  }
  private toDTO(a: Article): ArticleDTO {
    const { authorId: _authorId, ...dto } = a;
    return dto;
  }
}
```

### 3.6 routes/：类型化路由

`routes/articles.ts` 演示如何在路由层应用四个 Request 泛型：

```ts
router.get(
  '/',
  asyncHandler(
    async (
      req: Request<Record<string, never>, unknown, unknown, ArticleListQuery>,
      res: Response,
    ) => {
      const result = await articleService.list(req.query);
      sendSuccess(res, result, '文章列表', req.requestId);
    },
  ),
);

router.post(
  '/',
  auth,  // 鉴权中间件
  asyncHandler(
    async (req: Request<Record<string, never>, unknown, CreateArticleDTO>, res: Response) => {
      if (!req.user) throw new ValidationError('用户信息缺失');
      const article = await articleService.create(req.body, req.user.id);
      sendSuccess(res, article, '创建成功', req.requestId);
    },
  ),
);
```

注意几个细节：

1. **`Record<string, never>`** 表示「无路径参数」，比 `{}` 更严格。
2. **`req.body` 自动推断为 `CreateArticleDTO`**：访问 `req.body.foo` 会报错。
3. **`req.user.id` 类型安全**：因为 `auth.ts` 与 `express.d.ts` 共同保证 `req.user` 的类型。
4. **路由参数 `:id` 始终是 string**：路由内 `Number(req.params.id)` 转换 + `Number.isNaN` 校验。

### 3.7 app.ts 与 server.ts：入口与启动

`app.ts` 负责组装：基础中间件 → 健康检查 → 业务路由 → 404 兜底 → 错误处理。注意中间件**注册顺序就是请求处理顺序**，错误处理必须放最后：

```ts
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(logger);

app.get('/health', ...);                    // 健康检查
app.use('/api/articles', articlesRouter);   // 业务路由

app.use(notFoundHandler);                   // 404 兜底（必须放业务路由后）
app.use(errorHandler);                      // 错误处理（必须 4 参数 + 放最后）
```

`server.ts` 只负责调用 `app.listen(PORT)` 并打印 curl 测试命令，让用户启动后能直接复制测试。

---

## 四、类型安全实践

### 4.1 DTO 模式：前后端契约的代码化

DTO（Data Transfer Object）的本质是「接口入参 / 出参的显式契约」。它解决三个问题：

1. **隔离内部模型与对外契约**：数据库可能有 `authorId` / `deletedAt` / `version` 等字段，但前端只需要 `id` / `title` / `content` / `createdAt`。
2. **避免破坏性变更**：内部模型新增字段不会影响前端；反过来，前端契约变更必须显式改 DTO，CI 类型检查能立刻发现受影响的路由。
3. **文档化**：DTO 本身就是接口文档，配合 OpenAPI / Swagger 可以自动生成接口文档。

```ts
// 领域模型：含内部字段
interface Article {
  id: number;
  title: string;
  content: string;
  authorId: string;       // 内部字段
  createdAt: string;
  updatedAt: string;
}

// 响应 DTO：剥离内部字段
type ArticleDTO = Omit<Article, 'authorId'>;

// 请求 DTO：只接受用户应填写的字段
interface CreateArticleDTO {
  title: string;
  content: string;
}
```

进阶模式：用 `Pick` / `Omit` / `Partial` 派生 DTO，让 DTO 永远跟随领域模型变化：

```ts
type ArticleDTO = Omit<Article, 'authorId'>;
type UpdateArticleDTO = Partial<Pick<Article, 'title' | 'content'>>;
type ArticleListDTO = PaginatedDTO<ArticleDTO>;  // 复用泛型分页
```

### 4.2 TS 类型校验 + 运行时校验：Zod 简介

TS 类型只在编译期存在，运行时会被完全擦除。这意味着：

```ts
interface CreateArticleDTO {
  title: string;
  content: string;
}

router.post('/', (req: Request<{}, unknown, CreateArticleDTO>, res) => {
  // TS 认为 req.body.title 是 string
  // 但运行时如果客户端发来 { "title": 123 }，req.body.title 就是 123
  // 而且 JSON 反序列化不会校验类型
});
```

**Zod** 是 TS 生态最流行的运行时校验库，它把「类型定义」与「校验规则」合并为一个 schema，再用 `z.infer<typeof schema>` 反向推导出 TS 类型：

```ts
import { z } from 'zod';

const createArticleSchema = z.object({
  title: z.string().min(1, 'title 不能为空').max(100),
  content: z.string().min(1, 'content 不能为空'),
});

// 类型自动从 schema 推导，无需手写 interface
type CreateArticleDTO = z.infer<typeof createArticleSchema>;

router.post('/', (req, res) => {
  const result = createArticleSchema.safeParse(req.body);
  if (!result.success) {
    throw new ValidationError('参数校验失败', result.error.flatten());
  }
  const data: CreateArticleDTO = result.data;  // 类型安全的已校验数据
  // ...
});
```

Zod 的价值在于**「单一数据源」**：schema 既是运行时校验规则，又是 TS 类型来源，永远不会出现「类型说有，运行时没有」的脱节。本篇代码示例未集成 Zod（保留为练习），实战中推荐用 Zod 替代手写校验。NestJS 中可以用 `nestjs-zod` 或官方推荐的 `class-validator + class-transformer`（后者基于装饰器，与 NestJS 风格更一致）。

### 4.3 异步错误包装器 asyncHandler 的类型签名

Express 4 不会自动捕获 async 中间件抛出的 Promise rejection——这是新手最常踩的坑：

```ts
// ❌ 这样写，throw 抛出的 rejection 不会被错误处理中间件接住
router.get('/:id', async (req, res) => {
  const article = await service.getById(Number(req.params.id));
  res.json(article);
});
```

`asyncHandler` 的作用就是把 `(req, res, next) => Promise<T>` 包装成标准 `(req, res, next) => void`，并把 rejection 转 `next(err)`：

```ts
type AsyncRequestHandler<
  P = any, ResBody = any, ReqBody = any, ReqQuery = any,
> = (
  req: Request<P, ResBody, ReqBody, ReqQuery>,
  res: Response<ResBody>,
  next: NextFunction,
) => Promise<unknown> | unknown;

export function asyncHandler<
  P = any, ResBody = any, ReqBody = any, ReqQuery = any,
>(
  fn: AsyncRequestHandler<P, ResBody, ReqBody, ReqQuery>,
): RequestHandler<P, ResBody, ReqBody, ReqQuery> {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
```

类型设计要点：

1. **asyncHandler 设计为泛型函数**：让调用点的 `Request<{ id: string }>` 等泛型参数能被 TS 自动推断并透传到返回的 `RequestHandler`，保证 `router.get(path, handler)` 类型匹配。
2. **不能用 `Parameters<RequestHandler>` 反向推导参数元组**：因为 `RequestHandler` 默认泛型是 `ParamsDictionary`，而路由处理函数往往显式标注了更具体的 `Request<{ id: string }>`，函数参数逆变会导致赋值失败。
3. **返回值 `Promise<unknown> | unknown`** 兼容同步与异步函数。
4. **`Promise.resolve` 把同步返回值也包成 Promise**，统一走 `.catch(next)`，不需要 `if (result instanceof Promise)`。
5. **Express 5 已自动支持 async rejection**，但生产环境仍以 Express 4 为主，这个包装器在 NestJS 中也有等价物（`@nestjs/platform-express` 内部已处理）。

### 4.4 统一响应封装的泛型设计

`sendSuccess<T>` 用泛型让 `data` 的类型在调用点自动推断，避免重复标注：

```ts
export function sendSuccess<T>(
  res: Response,
  data: T,
  message = 'OK',
  requestId?: string,
): Response {
  const body: ApiResponse<T> = {
    code: 0,
    message,
    data,
    requestId,
    timestamp: new Date().toISOString(),
  };
  return res.json(body);
}

// 调用：T 自动推断为 ArticleDTO
sendSuccess(res, article, '文章详情', req.requestId);
// 调用：T 自动推断为 PaginatedDTO<ArticleDTO>
sendSuccess(res, paginated, '文章列表', req.requestId);
```

`ApiResponse<T>` 是统一响应体：

```ts
export interface ApiResponse<T = unknown> {
  code: number;          // 0=成功，非0=HTTP状态码
  message: string;
  data?: T;              // 成功时的数据 / 失败时的错误详情
  errorType?: string;    // 失败时的错误标识（如 'NOT_FOUND'）
  requestId?: string;    // 链路追踪 ID
  timestamp: string;
}
```

这样前端可以用一个统一的 `parseResponse<T>(raw): ApiResponse<T>` 工具函数处理所有响应，类型层直接拿到 `data: T`，无需手写类型断言。

---

## 五、与 NestJS 的衔接

本篇所有分层结构，几乎都能在 NestJS 中找到一一对应的角色：

| 本篇结构 | NestJS 对应 | 关系 |
|---------|------------|------|
| `routes/articles.ts` | `@Controller('articles')` + `@Get/@Post/@Put/@Delete` | 路由层 → 控制器层。NestJS 用装饰器声明路由，无需手写 `router.get` |
| `services/article-service.ts` | `@Injectable() class ArticleService` | 业务层 → Provider。NestJS 通过 IoC 容器自动装配，无需手写 `new` |
| `middlewares/logger.ts` | `@Injectable() implements NestMiddleware` | 横切中间件 → Nest Middleware |
| `middlewares/auth.ts` | `@Injectable() implements CanActivate` 的 Guard | 鉴权 → Guard。NestJS 用 `@UseGuards(AuthGuard)` 标注 |
| `middlewares/error-handler.ts` | `@Catch(AppError) implements ExceptionFilter` | 错误处理 → Exception Filter |
| `utils/response.ts` | `@Injectable() implements NestInterceptor` | 响应封装 → Interceptor |
| `middlewares/async-handler.ts` | NestJS 自动处理 | NestJS 内部已自动捕获 async rejection，无需手写 |
| `types/express.d.ts` 扩展 Request | `@nestjs/platform-express` 内部已扩展 + `@Req()` 装饰器 | Request 扩展 → 装饰器封装 |
| DTO + Zod | `class-validator` + `ValidationPipe` | 校验 → Pipe |

可以看到：**NestJS 不是新东西，而是把本篇的手工分层「升级」为装饰器 + 依赖注入的自动装配**。

具体衔接点：

1. **Day09 的装饰器是 NestJS 的命脉**：`@Controller` / `@Get` / `@Injectable` / `@Inject` 本质都是 `Reflect.defineMetadata` 贴标签，由 NestJS 启动时扫描元数据驱动路由与装配。
2. **本篇的 `IArticleService` 接口**：在 NestJS 中，Controller 通过构造函数注入 `ArticleService`，由 `emitDecoratorMetadata` 把类型信息写入 `design:paramtypes`，容器据此递归解析依赖（详见 Day09 的迷你 DI 容器）。
3. **本篇的 DTO 模式**：NestJS 推荐 `class-validator` + `class-transformer`，但 `zod` 同样可用（`nestjs-zod` 包），二者思路完全一致——把校验规则与类型绑定在一起。
4. **本篇的统一响应封装**：在 NestJS 中通常用 Interceptor 实现，把 Controller 返回值统一包装成 `{ code, message, data }`，业务代码无需手写 `sendSuccess`。
5. **本篇的 asyncHandler**：NestJS 已经内置——它的路由调度器会自动捕获 async rejection 并交给 ExceptionFilter，业务里直接 `throw new NotFoundException()` 即可。

一句话总结：**本篇是 NestJS 的「去魔法版」**——你亲手写了 routes / services / middlewares / 错误处理，再过几天看 NestJS 的 Controller / Provider / Guard / Pipe / Filter，会发现它们的本质与本篇完全一致，只是用装饰器与依赖注入把这些手工拼装自动化了。

---

## 六、关键知识点总结

1. **`@types/express`**：Express 自身不带类型，靠 `@types/express` 补充 `Request` / `Response` / `NextFunction` / `RequestHandler` / `ErrorRequestHandler` / `Express` / `Router` 等类型。
2. **核心接口定义在 `express-serve-static-core`**：`Request` / `Response` 等接口的真正定义在前者，`express` 只是 re-export；扩展 Request 时 `declare module` 必须指向 `express-serve-static-core`。
3. **`Request<P, ResBody, ReqBody, ReqQuery>` 四个泛型**：分别约束路由参数 / 响应体 / 请求体 / 查询字符串，让 `req.params` / `req.body` / `req.query` 全部类型安全。
4. **路由参数永远是 string**：`req.params.id` 类型是 `string`，需手动 `Number()` 转换并校验。
5. **`declare module` 模块增强**：扩展 `Request` 接口添加 `user` / `requestId` 等自定义字段；增强是全局性的，整个项目生效；字段建议设为可选。
6. **`RequestHandler` vs `ErrorRequestHandler`**：前者 3 参数 `(req, res, next)`，后者 4 参数 `(err, req, res, next)`；Express 用参数个数识别错误处理中间件。
7. **自定义 Error 体系**：`AppError` 基类携带 `statusCode` / `code` / `details`，子类 `NotFoundError` / `ValidationError` / `UnauthorizedError` 固定状态码；错误处理中间件用 `instanceof` 分支。
8. **`Object.setPrototypeOf` 修复 instanceof**：TS 编译到 ES5 时 `class extends Error` 的 `instanceof` 会失效，必须手动修复原型链。
9. **DTO 模式**：用 `Pick` / `Omit` / `Partial` 派生请求 / 响应 DTO，隔离内部模型与对外契约，避免破坏性变更。
10. **TS 类型 vs 运行时校验**：TS 类型只在编译期有效，运行时需 Zod / class-validator 等校验库补充；Zod 用 `z.infer` 把 schema 反向推导为类型，实现「单一数据源」。
11. **`asyncHandler` 包装器**：Express 4 不会自动捕获 async rejection，需手动包装；asyncHandler 必须设计为**泛型函数**让调用点的 Request 泛型参数（如 `{ id: string }`）能被 TS 自动推断并透传到返回的 RequestHandler，不能用 `Parameters<RequestHandler>` 反向推导（会因函数参数逆变导致 TS2345）；Express 5 已内置。
12. **统一响应封装 `sendSuccess<T>`**：用泛型让 `data` 类型在调用点推断；统一响应体 `{ code, message, data, errorType, requestId, timestamp }` 让前端能统一处理。
13. **分层架构**：types（类型契约）← middlewares（横切）← routes（表现层）← services（业务层）；类型在层间显式流动，每层只依赖下一层。
14. **与 NestJS 的衔接**：routes → Controller、services → Provider(@Injectable)、middlewares → Middleware / Guard / Filter / Interceptor、DTO + 校验 → Pipe；NestJS 用装饰器 + DI 把本篇的手工分层自动化。
15. **去魔法视角**：NestJS 不是新东西，是「本篇分层 + Day09 装饰器 + DI 容器」的工业级整合；理解了这两章，NestJS 只是套壳。

---

## 七、实战练习

> 以下练习配套 `Code/` 目录下的示例文件，建议先自己写，再对照参考实现扩展。

### 练习 1：集成 Zod 做运行时校验（对应 `routes/articles.ts` + `services/article-service.ts`）

在现有代码基础上：

1. 安装 `zod`：`npm install zod`。
2. 在 `types/index.ts` 同级新建 `schemas/article.schema.ts`，定义 `createArticleSchema` 与 `updateArticleSchema`，要求 `title` 长度 1–100、`content` 长度 1–10000。
3. 用 `z.infer<typeof createArticleSchema>` 替换 `types/index.ts` 中的 `CreateArticleDTO`，让类型从 schema 自动推导（删除原 interface，避免双重维护）。
4. 在 `routes/articles.ts` 的 POST / PUT 路由内调用 `schema.safeParse(req.body)`，校验失败抛 `ValidationError`，错误详情用 `result.error.flatten()` 返回给前端。
5. 移除 `services/article-service.ts` 中重复的 `if (!input.title?.trim())` 校验（schema 已覆盖）。

**进阶**：把 schema 校验封装成一个 `validate(schema, source: 'body' | 'query' | 'params')` 中间件工厂，让路由层只需 `router.post('/', auth, validate(createArticleSchema, 'body'), asyncHandler(...))`。

### 练习 2：扩展用户路由与权限守卫（对应 `routes/` + `middlewares/auth.ts`）

1. 新建 `services/user-service.ts`，实现 `list` / `getById` / `create` / `remove` 四个方法（用内存数组）。
2. 新建 `routes/users.ts`，定义 GET `/api/users` / GET `/api/users/:id` / POST `/api/users`（仅 admin 可调用）/ DELETE `/api/users/:id`（仅 admin 可调用）。
3. 在 `routes/users.ts` 中使用 `requireRole('admin')` 守卫保护 POST / DELETE 路由。
4. 在 `app.ts` 注册 `/api/users` 路由。
5. 测试：用 `user-token` 调用 POST `/api/users`，应当返回 403；用 `admin-token` 调用应当成功。

**进阶**：把 `requireRole` 改成支持多角色 `requireRole('admin', 'editor')`，并用 `@nestjs/passport` 的设计思路（Strategy + Guard）重新组织 `auth.ts`，让 token 验证逻辑可插拔。

### 练习 3：实现文章列表的多条件过滤与排序（对应 `services/article-service.ts`）

扩展 `ArticleListQuery`，新增字段：

```ts
export interface ArticleListQuery {
  page?: string;
  pageSize?: string;
  keyword?: string;
  authorId?: string;        // 新增：按作者过滤
  sortBy?: 'createdAt' | 'title';  // 新增：排序字段
  order?: 'asc' | 'desc';  // 新增：排序方向
}
```

在 `services/article-service.ts` 的 `list` 方法中：

1. 实现 `authorId` 过滤。
2. 实现 `sortBy` + `order` 排序，默认 `createdAt` + `desc`。
3. 校验 `sortBy` 必须是 `'createdAt' | 'title'` 之一，否则抛 `ValidationError`。
4. 校验 `order` 必须是 `'asc' | 'desc'` 之一。

测试命令：

```bash
curl "http://localhost:3000/api/articles?sortBy=title&order=asc"
curl "http://localhost:3000/api/articles?authorId=1&sortBy=createdAt&order=desc"
curl "http://localhost:3000/api/articles?sortBy=invalid"   # 应返回 400
```

**进阶**：把 `sortBy` + `order` 校验用 Zod 实现，让校验规则与类型绑定；思考如何把分页 / 排序逻辑抽成一个通用的 `buildPagination(query)` 工具函数复用到所有列表接口（提示：泛型 `<T extends Record<string, unknown>>` + `keyof T` 约束可排序字段）。

---

## 配套代码

| 文件 | 内容 |
|------|------|
| `Code/types/index.ts` | 领域模型、DTO、服务接口、`ApiResponse`、自定义 Error 体系（`AppError` / `NotFoundError` / `ValidationError` / `UnauthorizedError` / `ForbiddenError`） |
| `Code/types/express.d.ts` | 通过 `declare module 'express-serve-static-core'` 扩展 `Request`，增加 `user` / `requestId` 字段 |
| `Code/middlewares/logger.ts` | 类型化日志中间件（`RequestHandler`），生成 `requestId` 并记录请求耗时 |
| `Code/middlewares/auth.ts` | 鉴权中间件 + `requireRole` 角色守卫工厂，挂载 `req.user` |
| `Code/middlewares/error-handler.ts` | 类型化错误处理中间件（`ErrorRequestHandler`），按 `AppError` 子类分支 |
| `Code/middlewares/async-handler.ts` | 异步错误包装器，把 Promise rejection 转 `next(err)` |
| `Code/utils/response.ts` | 统一响应封装 `sendSuccess<T>` / `sendError` |
| `Code/services/article-service.ts` | 文章业务逻辑层，`implements IArticleService`，输入输出类型约束 |
| `Code/routes/articles.ts` | 类型化文章路由，应用 `Request<P, ResBody, ReqBody, ReqQuery>` 四泛型 |
| `Code/app.ts` | 应用入口，按顺序挂载基础中间件 / 健康检查 / 业务路由 / 404 / 错误处理 |
| `Code/server.ts` | 启动服务，打印 curl 测试命令 |
| `Code/package.json` | 项目依赖与脚本（express + @types/express + tsx + ts-node + typescript） |
| `Code/tsconfig.json` | Express 项目推荐的 TS 配置（strict + CommonJS + Node 模块解析） |

运行方式（需先在 `Code/` 目录执行 `npm install`）：

```bash
cd Code
npm install            # 安装 express + @types/express + tsx + ts-node + typescript

# 开发模式（文件变更自动重启）
npm run dev

# 单次启动
npm start

# 类型检查（不输出文件）
npm run type-check

# 编译为 dist/
npm run build
```

启动后控制台会打印 11 条 curl 测试命令，可直接复制测试以下场景：

- 健康检查
- 文章列表 / 详情 / 关键词搜索
- 创建文章（带鉴权 / 无鉴权 / 参数校验失败）
- 更新 / 删除文章
- 404 兜底
- 错误处理（404 / 401 / 400 / 500）

可用 token：

| Token | 角色 | 可访问路由 |
|-------|------|-----------|
| `admin-token` | admin | 全部 |
| `user-token` | user | 不受限的 GET / 需鉴权的 POST / PUT / DELETE（无角色守卫时） |

---

> 📚 **延伸阅读**
> - Express 官方文档：[expressjs.com](https://expressjs.com/)
> - `@types/express` 源码：[DefinitelyTyped / express](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/express)
> - `express-serve-static-core` 类型定义：[DefinitelyTyped / express-serve-static-core](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/express-serve-static-core)
> - TS Handbook - Module Augmentation：[TypeScript: Module Augmentation](https://www.typescriptlang.org/docs/handbook/declaration-merging.html#module-augmentation)
> - Zod 官方文档：[zod.dev](https://zod.dev/)
> - NestJS 官方文档：[Controllers](https://docs.nestjs.com/controllers) / [Providers](https://docs.nestjs.com/providers) / [Middleware](https://docs.nestjs.com/middleware) / [Exception Filters](https://docs.nestjs.com/exception-filters) / [Guards](https://docs.nestjs.com/guards) / [Pipes](https://docs.nestjs.com/pipes)
> - class-validator（NestJS 推荐校验库）：[github.com/typestack/class-validator](https://github.com/typestack/class-validator)
> - 前序章节回顾：[Day09 - 装饰器与元数据](../Day09%20-%20装饰器与元数据/README.md)（装饰器 + reflect-metadata 是 NestJS 的命脉）
