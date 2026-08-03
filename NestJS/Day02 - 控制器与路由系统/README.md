# Day02 - 控制器与路由系统

## 本章简介

控制器（Controller）是 NestJS 处理 HTTP 请求的入口。它本身不承载业务逻辑，只负责两件事：**接收请求**（解析路径参数、查询参数、请求体、请求头等）和**返回响应**（设置状态码、序列化返回值、必要时手动操作响应对象）。控制器的路由前缀与方法装饰器共同构成了 URL 到处理函数的映射表，而真正涉及数据计算、数据库读写、外部服务调用的逻辑都应下沉到 Service 层。

本章将从最基础的 `@Controller` 装饰器开始，逐一讲解 HTTP 方法装饰器、路由参数、查询参数、请求体、请求头、原始请求/响应对象、状态码、重定向、路由通配符等核心能力，再结合 RESTful 设计原则讨论路由的最佳实践。

## 学习目标

- 理解控制器在 NestJS 架构中的职责边界，明确"控制器薄、服务厚"的设计原则。
- 掌握 `@Controller` 与 HTTP 方法装饰器（`@Get`、`@Post`、`@Put`、`@Patch`、`@Delete`、`@All`、`@Head`、`@Options`）的用法。
- 熟练使用 `@Param`、`@Query`、`@Body`、`@Headers`、`@Req`、`@Res` 等参数装饰器。
- 能够通过 `@HttpCode`、`@Redirect` 自定义状态码与重定向行为。
- 理解 NestJS 默认平台 Express 的 Request/Response 与 NestJS 抽象层的关系，并学会扩展 Request 类型。
- 能够独立设计符合 RESTful 规范、支持版本化的路由结构。

## 理论知识讲解

### 1. `@Controller` 装饰器

`@Controller` 用于声明一个类为控制器，可选参数作为**路由前缀**：

```ts
@Controller('articles')
export class ArticlesController {}
```

此时该控制器内部所有路由都会以 `/articles` 开头。配合 `main.ts` 中 `app.setGlobalPrefix('api/v1')` 设置的全局前缀，最终路径形如 `/api/v1/articles`。路由前缀可以把同一类资源的所有接口收敛到一起，既清晰又便于权限统一管控。

> 注意：前缀只是一个字符串拼接，不会自动加 `/`，NestJS 会处理边界情况，但你仍需保证不要写 `@Controller('/articles')` 与 `@Controller('articles')` 混用。

### 2. HTTP 方法装饰器

NestJS 提供了与 HTTP 方法一一对应的装饰器：

| 装饰器 | HTTP 方法 | 典型用途 |
| --- | --- | --- |
| `@Get` | GET | 资源读取，幂等 |
| `@Post` | POST | 资源创建 |
| `@Put` | PUT | 全量更新，幂等 |
| `@Patch` | PATCH | 部分更新 |
| `@Delete` | DELETE | 资源删除 |
| `@All` | 任意方法 | 通用兜底、健康检查 |
| `@Head` | HEAD | 只返回响应头，常用于资源探测 |
| `@Options` | OPTIONS | CORS 预检、能力声明 |

```ts
@Get('list')
findAll() { ... }

@Post()
create() { ... }
```

### 3. 路由参数 `@Param`

路径中以 `:` 开头的片段是动态参数，通过 `@Param` 注入：

```ts
@Get(':id')
findOne(@Param('id') id: string) {
  return { id: Number(id) };
}
```

需要一次性拿到所有路径参数时，使用无参 `@Param()`：

```ts
@Get(':id/comments/:commentId')
findComment(@Param() params: { id: string; commentId: string }) {
  return params;
}
```

> 路径参数始终是 `string`，需要手动转换类型。Day07 引入 `class-validator` 的 `transform: true` 后，可由 `ValidationPipe` 自动转换。

### 4. 查询参数 `@Query`

查询参数（URL 中 `?` 后面的部分）通过 `@Query` 注入：

```ts
// 单个查询参数
@Get('search')
search(@Query('keyword') keyword: string) { ... }

// 全部查询参数
@Get()
findAll(@Query() query: QueryArticleDto) {
  return { page: query.page, pageSize: query.pageSize };
}
```

### 5. 请求体 `@Body`

POST/PUT/PATCH 通常携带请求体，通过 `@Body` 注入，并配合 DTO 类型约束结构：

```ts
@Post()
create(@Body() body: CreateArticleDto) {
  return body;
}
```

DTO 是普通的 TypeScript 类，Day07 会引入 `class-validator` 装饰器实现自动校验。

### 6. 请求头 `@Headers`

```ts
@Get('export')
exportAll(
  @Headers() headers: Record<string, string>,
  @Headers('authorization') auth: string,
) {
  return { hasAuth: !!auth, userAgent: headers['user-agent'] };
}
```

注意：HTTP 请求头字段名是大小写不敏感的，Express 会统一转为小写。

### 7. 请求与响应 `@Req` / `@Res`

| 装饰器 | 别名 | 说明 |
| --- | --- | --- |
| `@Req()` | `@Request()` | 注入底层平台的 Request 对象 |
| `@Res()` | `@Response()` | 注入底层平台的 Response 对象 |

```ts
@Post('raw')
rawHandler(@Req() req: Request, @Res() res: Response) {
  res.json({ method: req.method, url: req.originalUrl });
}
```

**关键陷阱**：一旦在方法签名中使用 `@Res()`（不传参数），NestJS 会认为你将自行处理响应，框架的**拦截器、序列化（SerializeOptions）、`@Header` 等后续能力都会失效**，必须显式调用 `res.send()` / `res.json()` 返回响应，否则请求会挂起直至超时。如果只是想读响应对象而不接管它，可以使用 `@Res({ passthrough: true })`。

### 8. 状态码 `@HttpCode`

- 默认情况下，`@Post` 返回 `201 Created`，其它方法返回 `200 OK`。
- 通过 `@HttpCode(204)` 自定义状态码：

```ts
@Delete(':id')
@HttpCode(204)
remove(@Param('id') id: string) {}
```

推荐使用 `HttpStatus` 枚举（`HttpStatus.NO_CONTENT`）以提升可读性。

### 9. 重定向 `@Redirect`

```ts
@Get('redirect/docs')
@Redirect('https://docs.nestjs.com/controllers', 302)
redirectToDocs() {}
```

方法返回值可覆盖装饰器参数，返回 `{ url: string, statusCode: number }` 即可实现动态重定向。

### 10. 路由通配符

Express 底层支持基于正则的通配符：

```ts
@Get('ab*cd')
wildcardMatch() { ... }
```

`abcd`、`ab_xyz_cd`、`ab123cd` 均可命中。**仅用于兜底匹配，不要在生产路由中滥用**，否则会让路由表难以维护。

### 11. 子路由前缀组合

`@Controller('articles')` 与 `@Get(':id')` 组合后，路径是 `/articles/:id`。这种分层组合让同一资源的所有接口前缀一致，便于版本化与权限管控：

```ts
@Controller('articles')
export class ArticlesController {
  @Get()          // GET /articles
  @Get(':id')     // GET /articles/:id
  @Post()         // POST /articles
  @Put(':id')     // PUT /articles/:id
}
```

> **静态路由必须在动态路由之前声明**：如果 `@Get(':id')` 写在 `@Get('search')` 前面，访问 `/articles/search` 会被 `:id` 命中，`id` 等于字符串 `"search"`。

## 请求与响应对象详解

### Express 的 Request/Response 与 NestJS 的关系

NestJS 默认基于 Express，控制器的 `@Req()` 拿到的就是 `express.Request`，`@Res()` 拿到的就是 `express.Response`。NestJS 在此基础上做了一层抽象，便于未来切换到 Fastify 等其它平台：

- NestJS 推荐**直接返回对象/字符串**，框架会自动调用 `res.json()` / `res.send()` 完成序列化，并自动应用拦截器。
- 只有在需要操作响应头、流式写入、SSE 等场景才直接使用 `@Res()`。

### 自定义 Request 类型扩展

当中间件、守卫给 `req` 注入额外字段时，TypeScript 会因类型缺失而报错。可通过 `declare module 'express'` 进行声明合并（见 `src/common/express.d.ts`）：

```ts
declare module 'express' {
  interface Request {
    user?: RequestUser;
  }
}
```

这样在控制器中 `req.user` 就拥有强类型。本项目的扩展为 Day14（认证与授权）做铺垫：守卫解析 JWT 后会把用户信息挂到 `req.user`。

### 响应返回值

NestJS 会根据返回值自动选择序列化方式：

- 返回对象/数组 → 自动 `JSON.stringify` + `Content-Type: application/json`
- 返回字符串 → 直接作为响应体
- 返回 `undefined`（如 `@HttpCode(204)` 的删除接口） → 不返回响应体

### 异步控制器

控制器方法是支持 `async/await` 的，框架会自动等待 Promise resolve：

```ts
@Get()
async findAll() {
  const data = await someAsyncOperation();
  return { data };
}
```

也可以直接返回 Observable 或 Promise，NestJS 会自动订阅/等待。

## 路由设计最佳实践

### RESTful 风格路由

RESTful 的核心是用 HTTP 方法表达"做什么"，用 URL 路径表达"对谁做"：

| 操作 | 方法 | 路径 | 状态码 |
| --- | --- | --- | --- |
| 列表 | GET | `/articles` | 200 |
| 详情 | GET | `/articles/:id` | 200 |
| 创建 | POST | `/articles` | 201 |
| 全量更新 | PUT | `/articles/:id` | 200 |
| 部分更新 | PATCH | `/articles/:id` | 200 |
| 删除 | DELETE | `/articles/:id` | 204 |

参考本项目 `src/users/users.controller.ts` 的标准实现。

### 路由前缀与版本化

版本化是接口演进的常用手段。两种常见方案：

1. **全局前缀**：`app.setGlobalPrefix('api/v1')`，所有路由统一带版本号，本项目采用此方式。
2. **控制器级别版本**：`@Controller({ path: 'articles', version: '1' })` + `app.enableVersioning()`，适合多版本共存的场景。

### 控制器薄、服务厚

控制器应该保持极薄，只做三件事：

1. 接收并校验请求参数（DTO）。
2. 调用 Service 方法完成业务。
3. 把 Service 返回的结果交回框架序列化。

数据库读写、外部 API 调用、复杂业务规则都应该下沉到 Service（Day04 引入）。这样做的好处：控制器易测试、Service 可复用、业务逻辑与传输协议解耦。

## 关键知识点总结

- **控制器职责**：路由映射 + 请求/响应映射，不写业务逻辑。
- **路由前缀**：`@Controller('articles')` + 全局前缀 `api/v1` 共同拼出最终 URL。
- **参数装饰器**：`@Param`（路径参数）、`@Query`（查询参数）、`@Body`（请求体）、`@Headers`（请求头）、`@Req`/`@Res`（原始对象）。
- **路径参数恒为 string**：需要手动转换或借助 `ValidationPipe` 自动转换。
- **`@Res()` 陷阱**：使用后会失去 NestJS 拦截器能力，必须显式 `res.send()`/`res.json()`，或使用 `@Res({ passthrough: true })` 保留框架能力。
- **状态码**：默认 GET/PUT/PATCH/DELETE 为 200，POST 为 201，可用 `@HttpCode` 覆盖，推荐 `HttpStatus` 枚举。
- **静态路由优先**：动态路由 `:id` 必须放在静态路由之后。
- **Request 类型扩展**：`declare module 'express'` 声明合并，为后续中间件/守卫挂载字段做铺垫。
- **RESTful 设计**：方法语义化、路径表达资源、状态码语义化。
- **版本化**：`setGlobalPrefix('api/v1')` 是最简单的方案，复杂场景用 `enableVersioning`。

## 实战练习

### 练习 1：扩展文章查询接口

在 `ArticlesController` 中新增一个 `GET /articles/paginated` 接口，要求：

- 使用 `@Query()` 接收 `page`、`pageSize`、`keyword` 三个参数。
- 返回结构包含 `page`、`pageSize`、`total`、`data`（构造 2-3 条假数据即可）。
- 思考：把这个接口放在 `@Get(':id')` 之前还是之后？为什么？

### 练习 2：实现标签管理子路由

为 `ArticlesController` 新增以下路由，演示**多级路径参数**与**子前缀**：

- `POST /articles/:id/tags`：给文章添加标签，接收 `@Body() { tags: string[] }`。
- `DELETE /articles/:id/tags/:tag`：删除文章的指定标签，使用两个 `@Param`。
- 返回适当的 `HttpStatus`（推荐 201 与 204）。

### 练习 3：自定义 Request 扩展验证

参考 `src/common/express.d.ts`，完成以下任务：

1. 在该文件中再扩展一个 `reqId: string` 字段，模拟请求链路追踪 ID。
2. 在 `ArticlesController` 中新增 `GET /articles/trace` 接口，通过 `@Req()` 读取 `req.reqId` 并返回。
3. 思考：在没有中间件主动赋值的情况下，`req.reqId` 会是什么值？这种类型扩展的副作用是什么？

---

> 本章节代码位于 `Code/` 目录，进入该目录后执行 `npm install` 安装依赖，再执行 `npm run start:dev` 即可启动服务，访问 `http://localhost:3000/api/v1/articles` 与 `http://localhost:3000/api/v1/users` 体验全部路由。
