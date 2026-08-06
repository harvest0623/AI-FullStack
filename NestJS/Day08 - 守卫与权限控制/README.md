# Day08 - 守卫与权限控制

守卫（Guard）是 NestJS 在路由处理之前做**授权决策**的组件：它根据当前请求携带的身份信息与目标路由的权限要求，返回一个 `boolean`——`true` 放行进入控制器，`false` 直接抛出 `403 Forbidden`。在 RBAC（基于角色的访问控制）体系中，守卫是把「认证 → 授权 → 细粒度权限」串成链路的核心：它读取控制器或方法上由装饰器声明的角色 / 权限要求，与已登录用户身份做交集判断，从而在不侵入业务代码的前提下完成访问控制。

本章把守卫从概念到落地完整走一遍：先讲清 `CanActivate` 接口与 `ExecutionContext`，再用 `Reflector` + 自定义装饰器把权限声明做成声明式 API，最后用 `Auth / Roles / Permission` 三个全局守卫搭出一套可扩展的 RBAC 骨架。

---

## 学习目标

完成本章后，你应能：

- 用一句话讲清「认证」与「授权」的差异，并指出守卫负责哪一环
- 实现 `CanActivate` 接口，正确返回 `boolean | Promise<boolean> | Observable<boolean>`
- 用 `ExecutionContext` 的 `switchToHttp / switchToRpc / getType` 在不同协议下取到正确的请求上下文
- 区分中间件、守卫、管道、拦截器的执行时机，并说明守卫为什么必须运行在管道之前
- 用三种粒度注册守卫：方法级 `@UseGuards`、控制器级、全局级 `APP_GUARD`，并指出 `useGlobalGuards` 与 `APP_GUARD` 在 DI 上的差异
- 用 `@SetMetadata` + `Reflector` 在路由上声明自定义权限元数据，并封装为 `@Roles` / `@Permissions` 装饰器
- 实现一个简化版 `AuthGuard`，从请求头解析 token 并把用户身份挂到 `req.user`
- 用 `@Public()` 装饰器为全局守卫打白名单，让登录、健康检查等路由跳过认证
- 画出 RBAC0 三层模型，并能针对业务场景在「角色」与「权限」两种粒度间做取舍
- 说出多守卫的执行顺序：全局 → 控制器级 → 方法级，且任一守卫返回 `false` 即短路

---

## 理论知识讲解

### 1. 守卫概念：授权而非认证

很多人把「登录」和「权限」混为一谈，但二者职责分明：

| 概念 | 解决的问题 | 典型问题 | 在 NestJS 中的载体 |
|------|----------|---------|------------------|
| 认证 Authentication | 你是谁？ | token 是否有效？能否解出用户身份？ | `AuthGuard`、Passport 策略 |
| 授权 Authorization | 你能做什么？ | 这个用户能否访问 `/admin`？能否删除文章？ | `RolesGuard`、`PermissionGuard` |

**守卫的语义就是授权**：它假设身份已经被认证（典型场景是 `AuthGuard` 已经把用户挂到 `req.user`），专注于「这个身份能不能进入这个路由」。

> 一句话记忆：认证回答「你是谁」，授权回答「你能干什么」，守卫负责后者。

#### 1.1 守卫的返回值

`CanActivate.canActivate` 的返回值决定请求命运：

```typescript
canActivate(context: ExecutionContext): boolean | Promise<boolean> | Observable<boolean>
```

- 返回 `true`：请求继续向下流转（后续守卫 → 管道 → 拦截器 → 控制器）
- 返回 `false`：NestJS 直接抛 `HttpException`，状态码默认 `403 Forbidden`
- 抛异常：抛出更精确的异常（如 `UnauthorizedException` → 401），由异常过滤器接管

生产实践里更推荐**抛异常而非返回 false**，因为 `403` 无法区分「未登录」与「无权限」，而 `401` / `403` 的语义对前端更友好。

### 2. CanActivate 接口

```typescript
export interface CanActivate {
  canActivate(
    context: ExecutionContext,
  ): boolean | Promise<boolean> | Observable<boolean>;
}
```

实现守卫只需做两件事：

1. 实现 `CanActivate` 接口
2. 标注 `@Injectable()`（如果要用 DI 注入 `Reflector`）

```typescript
@Injectable()
export class SimpleGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    return request.headers['x-api-key'] === 'secret';
  }
}
```

返回类型支持同步 / Promise / Observable，覆盖了异步校验场景：

- `boolean`：纯同步判断
- `Promise<boolean>`：查数据库、调外部权限服务
- `Observable<boolean>`：响应式场景，如基于 RxJS 的策略组合

### 3. ExecutionContext 详解

`ExecutionContext` 是 NestJS 跨协议抽象出来的「请求上下文」——同一份守卫代码可以同时跑在 HTTP、WebSocket、gRPC 上。它继承自 `ArgumentsHost`，并增加了「反射」能力。

| 方法 | 返回 | 用途 |
|------|------|------|
| `switchToHttp()` | `HttpArgumentsHost` | 取 `Request / Response / Next` |
| `switchToWs()` | `WsArgumentsHost` | 取 WebSocket `client / data` |
| `switchToRpc()` | `RpcArgumentsHost` | 取 gRPC `context / data` |
| `getType<T>()` | `'http' \| 'ws' \| 'rpc'` | 运行时识别协议类型 |
| `getClass()` | `Function` | 当前控制器类 |
| `getHandler()` | `Function` | 当前将被调用的方法 |

#### 3.1 HTTP 协议下取请求对象

```typescript
canActivate(context: ExecutionContext): boolean {
  const ctx = context.switchToHttp();
  const request = ctx.getRequest<Request>();   // Express.Request
  const response = ctx.getResponse<Response>();
  const next = ctx.getNext();                  // 不常用，守卫一般不调 next
  return !!request.headers['authorization'];
}
```

#### 3.2 协议无关写法

```typescript
canActivate(context: ExecutionContext): boolean {
  if (context.getType() === 'http') {
    const req = context.switchToHttp().getRequest();
    return !!req.headers['authorization'];
  }
  if (context.getType() === 'ws') {
    const client = context.switchToWs().getClient();
    return !!client.handshake?.headers?.authorization;
  }
  if (context.getType() === 'rpc') {
    const metadata = context.switchToRpc().getContext();
    return metadata.get('authorization')?.length > 0;
  }
  return false;
}
```

#### 3.3 getClass / getHandler：元数据读取入口

`getHandler()` 返回当前路由方法，`getClass()` 返回控制器类。它们是 `Reflector` 读取元数据的钥匙——因为 `@SetMetadata` 写入的元数据是挂在「方法」或「类」上的，必须通过这两个引用才能取到。

```typescript
const requiredRoles = this.reflector.getAllAndOverride<string[]>(
  ROLES_KEY,
  [context.getHandler(), context.getClass()],
);
```

### 4. 守卫与中间件的区别

中间件、守卫、管道、拦截器都「在控制器之前」执行，很容易混淆。它们的差异不仅在于职责，更在于**执行时机**与**作用范围**：

| 组件 | 职责 | 执行时机 | 作用范围 | 典型用法 |
|------|------|---------|---------|---------|
| 中间件 | 通用预处理 | 路由匹配之后、守卫之前 | 模块级 / 全局 | 日志、CORS、body 解析 |
| 守卫 | 授权决策 | 中间件之后、**管道之前** | 全局 / 控制器 / 方法 | RBAC、API Key 校验 |
| 拦截器 | 横切增强 | 守卫之后、控制器前后各一次 | 全局 / 控制器 / 方法 | 日志、缓存、序列化 |
| 管道 | 参数转换 / 校验 | 路由参数绑定之后、控制器之前 | 参数级 | DTO 校验、类型转换 |

#### 4.1 为什么守卫必须在管道之前

管道会执行参数校验（如 `ValidationPipe` 检查 DTO 字段），而校验属于业务逻辑——**未授权的请求根本不该走到参数校验环节**，否则既浪费算力，又可能通过校验错误消息泄露内部结构。所以 NestJS 把守卫放在管道之前：守卫不通过，管道与控制器根本不会执行。

#### 4.2 为什么不直接用中间件做授权

中间件偏底层，能拿到 `req` / `res` 但拿不到「即将执行的控制器方法」与「装饰器元数据」。也就是说，中间件**无法读取 `@Roles('admin')` 这种声明式权限**，只能写硬编码的路径白名单：

```typescript
// 中间件写法（不推荐，权限与代码耦合）
if (req.path.startsWith('/admin') && !userIsAdmin(req)) {
  return res.status(403).end();
}

// 守卫写法（推荐，权限声明式）
@Get('dashboard')
@Roles('admin')
dashboard() { ... }
```

---

## 守卫的应用方式

### 1. 方法级：`@UseGuards(RolesGuard)`

```typescript
@Get('admin')
@UseGuards(RolesGuard)
adminOnly() { ... }
```

仅作用于当前方法。适合「该模块大部分路由公开，只有少数需要鉴权」的场景。

### 2. 控制器级：`@UseGuards(JwtAuthGuard) @Controller()`

```typescript
@Controller('articles')
@UseGuards(JwtAuthGuard)
export class ArticlesController { ... }
```

作用于整个控制器，控制器内所有方法都被守卫保护。适合「整组路由都需要登录」的场景。

### 3. 全局级：`useGlobalGuards` vs `APP_GUARD`

#### 3.1 `app.useGlobalGuards`（在 `main.ts` 中）

```typescript
const app = await NestFactory.create(AppModule);
app.useGlobalGuards(new AuthGuard(new Reflector()));
```

- 守卫实例由我们手动 `new`，**不经过 DI 容器**
- 无法注入 `Reflector`、无法使用 `REQUEST` 作用域 Provider
- 适合纯函数式守卫，或简单脚本

#### 3.2 `APP_GUARD`（在模块 `providers` 中）

```typescript
@Module({
  providers: [
    { provide: APP_GUARD, useClass: AuthGuard },
    { provide: APP_GUARD, useClass: RolesGuard },
    { provide: APP_GUARD, useClass: PermissionGuard },
  ],
})
export class AppModule {}
```

- 守卫由 Nest DI 容器创建，**自动注入 `Reflector`**
- 支持作用域、依赖链、模块边界
- **生产项目一律推荐这种**
- 多个 `APP_GUARD` 按注册顺序执行

> 关键差异：`useGlobalGuards` 不支持 DI，`APP_GUARD` 支持 DI。本章 Demo 三个守卫全部走 `APP_GUARD`。

---

## Reflector 反射器与元数据

### 1. `@SetMetadata` 写入元数据

```typescript
@SetMetadata('roles', ['admin'])
@Get('dashboard')
dashboard() { ... }
```

`@SetMetadata` 是底层装饰器，把任意键值对写入方法或类的元数据。但直接用有两个问题：

- 字符串 key 容易写错
- 没有类型提示，调用方不知道该传什么类型

### 2. `Reflector` 读取元数据

```typescript
@Injectable()
export class RolesGuard {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const roles = this.reflector.get<string[]>('roles', context.getHandler());
    // ...
  }
}
```

`Reflector` 由 DI 容器注入，提供三种读取策略：

| 方法 | 行为 |
|------|------|
| `get<T>(key, target)` | 单点读取，从指定 target 读 |
| `getAllAndOverride<T>(key, [t1, t2])` | 方法级优先，没命中再回退类级 |
| `getAllAndMerge<T>(key, [t1, t2])` | 方法级与类级合并（去重） |

#### 2.1 `getAllAndOverride` vs `getAllAndMerge`

```typescript
// getAllAndOverride：方法上有就用方法的，没有才用类上的
// 类上 @Roles('admin')，方法上 @Roles('editor') → 取 ['editor']
this.reflector.getAllAndOverride(ROLES_KEY, [
  context.getHandler(),
  context.getClass(),
]);

// getAllAndMerge：方法与类的角色合并去重
// 类上 @Roles('admin')，方法上 @Roles('editor') → 取 ['admin', 'editor']
this.reflector.getAllAndMerge(ROLES_KEY, [
  context.getHandler(),
  context.getClass(),
]);
```

### 3. 自定义装饰器 `@Roles` 封装 `@SetMetadata`

```typescript
// roles.decorator.ts
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);

// articles.controller.ts
@Get('dashboard')
@Roles('admin', 'editor')
dashboard() { ... }
```

封装带来的好处：

- **类型安全**：`roles: string[]` 让调用方明确知道该传什么
- **可读性**：`@Roles('admin')` 比 `@SetMetadata('roles', ['admin'])` 直观
- **集中管理 key**：`ROLES_KEY` 常量集中在一处，杜绝魔法字符串

---

## 实战守卫实现

本章 Demo 实现了四个核心组件，构成完整的 RBAC 骨架。

### 1. `AuthGuard`：基础鉴权守卫

```typescript
@Injectable()
export class AuthGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    // ① 优先检查 @Public() 元数据
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (isPublic) return true;

    // ② 取请求头 token
    const request = context.switchToHttp().getRequest();
    const token = this.extractBearerToken(request.headers['authorization']);
    if (!token) throw new UnauthorizedException();

    // ③ 校验 token 并把用户挂到 req.user
    const user = this.mockUsers[token];
    if (!user) throw new UnauthorizedException();
    request.user = user;
    return true;
  }
}
```

设计要点：

- 检查 `@Public()` 放在最前，命中即跳过 token 校验
- token 解析失败抛 `401 Unauthorized`，区分「未登录」与「无权限」
- 用户身份挂到 `req.user`，供后续守卫与控制器复用
- 真实项目用 JWT 解签替换 mock 查表（Day14 展开）

### 2. `RolesGuard`：角色守卫

```typescript
canActivate(context: ExecutionContext): boolean {
  const requiredRoles = this.reflector.getAllAndOverride<string[]>(
    ROLES_KEY,
    [context.getHandler(), context.getClass()],
  );
  if (!requiredRoles) return true;  // 没标 @Roles 就放行

  const user = context.switchToHttp().getRequest().user;
  const hasRole = user.roles.some(role => requiredRoles.includes(role));
  if (!hasRole) throw new ForbiddenException();
  return true;
}
```

校验语义是「或」语义：用户拥有路由要求的**任意一个**角色即可通过。

### 3. `@Public()` + 全局白名单

```typescript
// public.decorator.ts
export const Public = () => SetMetadata(IS_PUBLIC_KEY, true);

// AuthGuard 开头检查
const isPublic = this.reflector.getAllAndOverride(IS_PUBLIC_KEY, [...]);
if (isPublic) return true;
```

为什么需要 `@Public()`：当 `AuthGuard` 注册成全局守卫，**所有路由默认都要登录**。但登录、注册、健康检查等路由必须公开，否则陷入「没登录拿不到 token，没 token 又登录不了」的死循环。

### 4. `PermissionGuard`：细粒度权限守卫

```typescript
canActivate(context: ExecutionContext): boolean {
  const required = this.reflector.getAllAndOverride<string[]>(
    PERMISSIONS_KEY,
    [context.getHandler(), context.getClass()],
  );
  if (!required) return true;

  const user = context.switchToHttp().getRequest().user;
  const hasPermission = user.permissions.some(p => required.includes(p));
  if (!hasPermission) throw new ForbiddenException();
  return true;
}
```

与 `RolesGuard` 的差异：

| 维度 | RolesGuard | PermissionGuard |
|------|-----------|----------------|
| 粒度 | 粗（角色名） | 细（权限字符串） |
| 装饰器 | `@Roles('admin')` | `@Permissions('article:create')` |
| 调整成本 | 改代码 | 改数据库权限表 |
| 适用场景 | 角色少且稳定 | 权限常调整、多业务线 |

---

## RBAC 权限模型

### 1. RBAC0：用户-角色-权限三层模型

RBAC0 是 RBAC 系列最基础的模型，几乎所有权限系统都从它起步：

```
┌────────┐   拥有    ┌────────┐   拥有    ┌──────────────┐
│  用户  │ ───────▶ │  角色  │ ───────▶ │     权限      │
│ User   │          │ Role   │          │  Permission  │
└────────┘          └────────┘          └──────────────┘
   │                                            ▲
   └──────────── 直接挂载（细粒度场景）──────────┘
```

- **用户**：`{ id, username, roles: [], permissions: [] }`
- **角色**：`admin / editor / visitor`，角色下挂一组权限
- **权限**：`article:create / article:delete / user:read`，按「资源:动作」命名

### 2. 角色 vs 权限的取舍

| 场景 | 推荐粒度 | 原因 |
|------|---------|------|
| 后台管理系统、角色少且稳定 | 角色 | 实现简单，写 `@Roles('admin')` 就够了 |
| SaaS、多租户、权限常调整 | 权限 | 改数据库不改代码，支持租户自定义角色 |
| 复杂业务、需要细到按钮 | 权限 + 角色 | 角色做粗筛，权限做细筛 |

实战经验：

- 别一开始就上 RBAC1 / RBAC2（角色继承、角色互斥），多数项目 RBAC0 就够用
- 「权限」命名要统一，推荐 `资源:动作`，如 `article:create`
- 数据库设计时角色与权限多对多，用户与角色多对多，用户也可直接挂权限（绕过角色）

### 3. 装饰器驱动的权限声明

NestJS 的精髓在于「声明式权限」：把权限要求写在路由上，由守卫读取后做决策，业务代码完全无感。

```typescript
@Post()
@Roles('admin', 'editor')           // 粗粒度：admin 或 editor 都能进
@Permissions('article:create')      // 细粒度：必须有创建权限
create(@Body() body) { ... }
```

这种写法的好处：

- **权限与代码同位置**：读路由就知道权限要求，无需翻配置文件
- **可测试**：守卫与控制器解耦，单测时可以单独测守卫
- **可扩展**：新增权限要求只需加装饰器，守卫逻辑不变

---

## 守卫执行顺序

### 1. 同一请求内多守卫的顺序

NestJS 守卫执行顺序遵循「全局 → 控制器级 → 方法级」，且：

- **全局守卫**按 `APP_GUARD` 注册顺序执行（先注册先执行）
- **控制器级与方法级**守卫按 `@UseGuards` 中参数顺序执行
- **任一守卫返回 `false` 或抛异常即短路**，后续守卫不执行

本章 Demo 的执行链：

```
请求进入
   │
   ▼
[全局] AuthGuard          ← 解析 token，挂 req.user
   │ 返回 true
   ▼
[全局] RolesGuard        ← 检查 @Roles 元数据，与 user.roles 交集
   │ 返回 true
   ▼
[全局] PermissionGuard   ← 检查 @Permissions 元数据，与 user.permissions 交集
   │ 返回 true
   ▼
管道 / 拦截器 / 控制器
```

### 2. 短路示例

```typescript
// 用户携带 token-visitor 访问 DELETE /articles/123

AuthGuard          → true（token 有效，user = visitor）
RolesGuard         → true（路由未标 @Roles，放行）
PermissionGuard   → false（路由要求 article:delete，visitor 没有）
                  ↓
                  抛 ForbiddenException(403)
                  控制器不会执行
```

### 3. 三层职责分离的价值

| 守卫 | 职责 | 改造场景 |
|------|------|---------|
| AuthGuard | 认证 | JWT 替换 mock token，只改这一处 |
| RolesGuard | 粗粒度授权 | 新增角色时只改数据库，代码不动 |
| PermissionGuard | 细粒度授权 | 给 editor 加 article:delete 权限只改权限表 |

---

## 关键知识点总结

1. **守卫负责授权而非认证**：认证解决「你是谁」，授权解决「能干什么」
2. **返回 `false` 抛 `403`，抛异常更精确**：用 `UnauthorizedException` (401) / `ForbiddenException` (403) 区分语义
3. **`CanActivate` 三种返回类型**：`boolean | Promise<boolean> | Observable<boolean>`，覆盖同步 / 异步 / 响应式
4. **`ExecutionContext` 跨协议**：`switchToHttp / switchToWs / switchToRpc` + `getType()` 让守卫可在 HTTP / WS / gRPC 复用
5. **守卫在管道之前**：未授权请求不进入参数校验，避免算力浪费与信息泄露
6. **三种注册粒度**：方法级 `@UseGuards`、控制器级、全局级
7. **`useGlobalGuards` vs `APP_GUARD`**：前者不支持 DI，后者支持 DI，生产项目用后者
8. **`Reflector` 三种读取策略**：`get` 单点 / `getAllAndOverride` 方法级优先 / `getAllAndMerge` 合并
9. **自定义装饰器封装 `@SetMetadata`**：类型安全 + 集中管理 key
10. **`@Public()` 跳过全局守卫**：登录、注册、健康检查路由必须白名单
11. **RBAC0 三层模型**：用户 → 角色 → 权限，角色粗粒度、权限细粒度
12. **多守卫按注册顺序执行**：先全局后局部，任一返回 `false` 即短路
13. **三层守卫职责单一**：Auth / Roles / Permission 各司其职，可独立替换与测试

---

## 实战练习

### 练习 1：实现一个「工作时间限制」守卫

实现 `WorkingHoursGuard`，要求请求时间必须在工作日 09:00–18:00 之间，否则返回 `403`。

要求：

- 用 `ExecutionContext.switchToHttp().getRequest()` 取请求时间（无则用 `new Date()`）
- 注册为控制器级守卫，仅作用于 `ArticlesController`
- 提供一个 `@OvertimeAllowed()` 装饰器，标了的方法不受工作时间限制（参考 `@Public()` 实现）

### 练习 2：扩展 `@Roles` 支持权限合并语义

当前 `RolesGuard` 用 `getAllAndOverride`，类上的角色会被方法覆盖。改为 `getAllAndMerge`，让类与方法的角色合并去重。

要求：

- 修改 `roles.guard.ts`，把 `getAllAndOverride` 换成 `getAllAndMerge`
- 在 `ArticlesController` 上加 `@Roles('admin')`，在某个方法上加 `@Roles('editor')`
- 测试：admin 角色用户能否访问带 `@Roles('editor')` 的方法（应该可以，因为合并后是 `['admin', 'editor']`）

### 练习 3：实现「权限 AND 语义」

当前 `PermissionGuard` 是「或」语义——拥有任一权限即可。请扩展一个 `@RequireAllPermissions()` 装饰器与对应守卫，要求用户必须**同时拥有**所有声明的权限才能访问。

要求：

- 新增 `REQUIRE_ALL_PERMISSIONS_KEY` 常量
- 新增 `@RequireAllPermissions('article:read', 'article:delete')` 装饰器
- 修改 `PermissionGuard`：优先读取 `REQUIRE_ALL_PERMISSIONS_KEY`，命中则用 `every` 替代 `some` 做校验
- 提供测试路由：`DELETE /articles/:id/force` 要求同时拥有 `article:delete` 和 `article:force_delete` 权限

---

## 项目结构

```
Day08 - 守卫与权限控制/
├── Code/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.build.json
│   ├── nest-cli.json
│   └── src/
│       ├── main.ts                          # 启动入口，演示守卫注册两种方式
│       ├── app.module.ts                    # 根模块，APP_GUARD 注册三个全局守卫
│       ├── articles/
│       │   ├── articles.controller.ts       # 演示 @Roles / @Public / @Permissions
│       │   └── articles.module.ts
│       ├── guards/
│       │   ├── auth.guard.ts                # 认证守卫（解析 token → req.user）
│       │   ├── roles.guard.ts               # 角色守卫（@Roles 粗粒度）
│       │   └── permission.guard.ts           # 权限守卫（@Permissions 细粒度）
│       ├── decorators/
│       │   ├── roles.decorator.ts           # @Roles('admin')
│       │   ├── public.decorator.ts          # @Public()
│       │   └── permissions.decorator.ts     # @Permissions('article:create')
│       └── common/
│           ├── reflector.constants.ts       # 元数据 key 常量 + AuthUser 类型
│           └── express.d.ts                 # 扩展 Express.Request.user
└── README.md
```

## 运行方式

```bash
cd "Day08 - 守卫与权限控制/Code"
npm install
npm run start:dev
```

启动后访问 http://localhost:3000 ，按 `main.ts` 中的提示用 `curl` 测试各类路由。

### 测试示例

```bash
# 公开路由（无需 token）
curl http://localhost:3000/articles/health

# 任意已登录用户
curl -H "Authorization: Bearer token-admin" http://localhost:3000/articles

# admin 才能访问
curl -H "Authorization: Bearer token-editor" http://localhost:3000/articles/admin/dashboard  # 403
curl -H "Authorization: Bearer token-admin" http://localhost:3000/articles/admin/dashboard

# article:create 权限（editor 也有）
curl -X POST -H "Authorization: Bearer token-editor" \
     -H "Content-Type: application/json" \
     -d '{"title":"hello"}' http://localhost:3000/articles

# article:delete 权限（仅 admin）
curl -X DELETE -H "Authorization: Bearer token-visitor" http://localhost:3000/articles/1  # 403
curl -X DELETE -H "Authorization: Bearer token-admin" http://localhost:3000/articles/1
```
