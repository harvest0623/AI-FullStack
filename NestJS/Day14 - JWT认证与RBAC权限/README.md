# Day14 - JWT 认证与 RBAC 权限

认证（authentication，回答「你是谁」）与授权（authorization，回答「你能做什么」）是后端安全的两大支柱。在 NestJS 生态里，把它们落地为可工程化复用的标准方案，绕不开三件套：**JWT**（无状态令牌）、**Passport**（策略化的认证中间件）、**RBAC**（基于角色的访问控制）。本章把这三者串成一条完整链路——从注册时用 bcrypt 哈希密码、登录时用 LocalStrategy 校验账号密码并签发 JWT，到访问受保护资源时用 JwtStrategy 解析 token、用 Refresh Token 续期、用黑名单实现登出，最后复用 Day08 的 RolesGuard 完成 RBAC 授权。

Day14 是 Day08「守卫与权限控制」的进阶篇：Day08 用硬编码 token 演示了守卫与 RBAC 的机制骨架，本章把那个「假认证」替换成「真 JWT」，让整套体系具备生产可用性。

---

## 学习目标

完成本章后，你应能：

- 用一句话区分「认证」与「授权」，并指出 JWT、Passport、RBAC 分别属于哪一环
- 解释 Session 与 JWT 的差异：有状态 vs 无状态、可撤销性、横向扩展能力
- 画出 JWT 的三段结构（`header.payload.signature`）并说明每段的作用与编码方式
- 说明为什么必须用 bcrypt 而非 MD5/SHA256 哈希密码，并理解 salt rounds 的取舍
- 用 `@nestjs/jwt` 的 `register` 与 `registerAsync` 两种方式配置 JwtModule，并指出何时必须用后者
- 用 `@nestjs/passport` + `PassportStrategy` 基类实现 LocalStrategy 与 JwtStrategy，理解 `validate` 方法的返回值如何变成 `req.user`
- 解释 `AuthGuard('jwt')` / `AuthGuard('local')` 的工作原理，并能基于它做扩展（黑名单、限流）
- 设计 Refresh Token 机制：access token 短期 + refresh token 长期，并说明为什么 refresh 时必须重新读 DB 而非直接信任 payload
- 复用 Day08 的 `@Roles` + `RolesGuard`，与 JwtAuthGuard 串联成「认证 → 授权」两层守卫
- 区分 RBAC0 三层模型，并在路由级 / 资源级 / 字段级三种权限粒度间做取舍

---

## 理论知识讲解

### 1. 认证 vs 授权

| 维度 | 认证 Authentication | 授权 Authorization |
|------|---------------------|---------------------|
| 解决的问题 | 你是谁？ | 你能做什么？ |
| 典型问题 | 这把 token 是真的吗？属于谁？ | 这个用户能访问 `/admin` 吗？能删除文章吗？ |
| 在 NestJS 中的载体 | LocalStrategy / JwtStrategy / AuthGuard | RolesGuard / PermissionGuard |
| 失败状态码 | `401 Unauthorized` | `403 Forbidden` |
| 产出 | `req.user` 挂载用户身份 | 布尔决策：放行 / 拒绝 |

**守卫的语义偏向授权，但认证也可以用守卫实现**——本章的 `JwtAuthGuard` 既做认证（解析 token）又把结果挂到 `req.user`，为后续的授权守卫提供输入。这种「认证守卫 + 授权守卫」分层是 NestJS 推荐的工程实践，源自 Day08 的设计延续。

> 一句话记忆：认证回答「你是谁」，授权回答「你能干什么」；401 是「不知道你是谁」，403 是「知道你是谁但你不能干这个」。

### 2. Session vs JWT

#### 2.1 有状态 vs 无状态

| 维度 | Session（有状态） | JWT（无状态） |
|------|------------------|----------------|
| 状态存储 | 服务端内存 / Redis | 客户端持有，服务端不存 |
| 标识形式 | `sessionId`（随机字符串） | JWT 字符串（自包含 payload） |
| 校验方式 | 查 session 存储 | 校验签名 + 过期时间 |
| 撤销能力 | 直接删 session 即可立即下线 | 难，需维护黑名单 |
| 横向扩展 | 需共享 session 存储（如 Redis） | 天然支持，任意节点都能验签 |
| 安全敏感度 | session id 不含业务信息 | payload 可被解码（仅签名防篡改） |

#### 2.2 JWT 三段结构

一个 JWT 长这样（用 `.` 分三段）：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsInVzZXJuYW1lIjoiYWRtaW4iLCJyb2xlcyI6WyJhZG1pbiJdLCJ0eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzAwMDAwMDAwLCJleHAiOjE3MDAwMDA5MDB9.K7gN1xVlmZW3pX4...
└──────────── header ───────────┘└──────────────────── payload ────────────────────────────────────────┘└──── signature ────┘
```

| 段 | 内容 | 编码 | 作用 |
|----|------|------|------|
| header | `{"alg":"HS256","typ":"JWT"}` | Base64URL | 声明签名算法与 token 类型 |
| payload | `{"sub":1,"username":"admin",...,"exp":1700000900}` | Base64URL | 业务身份信息 + 标准声明（`iat`/`exp`/`sub`） |
| signature | `HMAC-SHA256(base64(header) + "." + base64(payload), secret)` | 二进制 | 防篡改：改了任何一段都对不上签名 |

**关键认知**：
- payload 是 **Base64 编码而非加密**，任何人都能解码看到内容。**绝不在 payload 里放密码、密钥、敏感个人信息**。
- signature 只防篡改，不防读取。要保密需配合 JWE（JSON Web Encryption）。
- 服务端验签时只需 `JWT_SECRET`，无需查 DB，这是「无状态」的核心来源。

### 3. 密码哈希：bcrypt

#### 3.1 为什么不用 MD5 / SHA256

| 哈希算法 | 类型 | 速度 | 是否加盐 | 安全性 |
|---------|------|------|---------|--------|
| MD5 | 快哈希 | 极快（GPU 千万次/秒） | 需手动 | **不可用于密码**，彩虹表可秒破 |
| SHA256 | 快哈希 | 很快 | 需手动 | 同上，密码场景不安全 |
| bcrypt | 慢哈希 | 故意慢（可调） | 内置自动加盐 | **推荐**，专门为密码设计 |
| argon2 | 慢哈希 | 可调 | 内置 | 现代首选，但 bcrypt 已足够 |

密码哈希的核心矛盾：**用户密码弱（短、有规律），但哈希要难爆破**。快哈希让攻击者拿到哈希后能用字典 + GPU 每秒试千万次；慢哈希把每次尝试成本从纳秒拉到毫秒，让暴力破解不可行。

#### 3.2 salt rounds

bcrypt 的 cost factor 写作 `saltRounds`，意义是 `2^saltRounds` 次哈希迭代：

| saltRounds | 迭代次数 | 单次耗时（参考） | 适用场景 |
|-----------|---------|------------------|---------|
| 8 | 256 | ~10ms | 仅演示 |
| 10 | 1024 | ~60ms | 开发演示（本章使用） |
| 12 | 4096 | ~250ms | 生产推荐 |
| 14 | 16384 | ~1s | 高安全场景 |

每增加 1，时间翻倍。**生产环境推荐 12 起步**，登录 RT 仍可接受，但爆破成本指数级上升。

#### 3.3 bcrypt 哈希字符串结构

bcrypt 哈希结果自带算法版本、salt、cost factor 与哈希本体：

```
$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
└┘└┘└┘└──────────── salt (22 字符) ───────────┘└──────── 哈希本体 (31 字符) ────────┘
 │ │ │
 │ │ └── cost factor = 10
 │ └── 算法版本：2a / 2b / 2y
 └── bcrypt 标识
```

因此**无需在数据库单独维护 salt 字段**——`bcrypt.compare(plain, hashed)` 会从 hashed 字符串里解析出 salt 与 cost，用相同参数重新哈希 plain 再比对。这是 bcrypt 相比「手动 salt + SHA256」的工程优势。

### 4. @nestjs/jwt

`@nestjs/jwt` 是 NestJS 对 `jsonwebtoken` 的封装，提供 `JwtModule` 与 `JwtService`。

#### 4.1 JwtModule.register vs registerAsync

```typescript
// 同步：secret 在编译期就已知（不适合从 .env 读）
JwtModule.register({
  secret: 'hardcoded-secret',
  signOptions: { expiresIn: '15m' },
});

// 异步：依赖 ConfigService 等 Provider 时必须用这个
JwtModule.registerAsync({
  imports: [ConfigModule],
  inject: [ConfigService],
  useFactory: (config: ConfigService) => ({
    secret: config.get<string>('JWT_SECRET'),
    signOptions: { expiresIn: config.get<string>('JWT_EXPIRES_IN') },
  }),
});
```

**何时必须用 `registerAsync`**：当配置依赖其他 Provider（ConfigService、数据库、远程配置中心）时，模块加载阶段这些 Provider 还未就绪，必须用工厂函数延迟求值。生产项目一律用 `registerAsync`。

#### 4.2 JwtService 核心方法

| 方法 | 作用 | 典型用法 |
|------|------|---------|
| `sign(payload, options?)` | 用 secret 签发 JWT | 登录后返回 token |
| `verifyAsync<T>(token, options?)` | 异步校验签名 + 过期，返回 payload | refresh token 校验 |
| `decode(token)` | 仅 Base64 解码 payload，不验签 | 调试用，生产慎用 |

`sign` 与 `verify` 是配套的：用同一 secret 签发与校验。`verifyAsync` 失败会抛 `JsonWebTokenError` 或 `TokenExpiredError`，需要 try/catch 转成业务异常。

### 5. @nestjs/passport 与策略模式

Passport 是 Node 生态最流行的认证中间件库，采用**策略模式**：每种认证方式（local、jwt、google、github、oauth2……）封装成一个 Strategy 类，统一接口让上层无感切换。

`@nestjs/passport` 做的事：
1. 提供 `PassportStrategy` 基类，自定义策略继承它即可
2. 提供 `AuthGuard(name)` 工厂，根据策略名触发对应策略
3. 在守卫触发时自动调用策略的 `validate` 方法，并把返回值挂到 `req.user`

#### 5.1 PassportStrategy 基类

```typescript
@Injectable()
export class MyStrategy extends PassportStrategy(Strategy, 'my-strategy-name') {
  constructor() {
    super({ /* 策略配置 */ });
  }

  async validate(...args): Promise<any> {
    // 校验逻辑，返回值会被挂到 req.user
  }
}
```

`PassportStrategy(Strategy, name)` 接收两个参数：
- `Strategy`：passport-xxx 包提供的策略类（如 `passport-local` 的 `Strategy`、`passport-jwt` 的 `Strategy`）
- `name`：策略注册名，`AuthGuard(name)` 据此触发。可省略，默认取策略包内置名（local / jwt）

### 6. LocalStrategy：用户名密码登录

```typescript
@Injectable()
export class LocalStrategy extends PassportStrategy(Strategy, 'local') {
  constructor(private authService: AuthService) {
    super(); // 默认从 req.body.username / password 读取
  }

  async validate(username: string, password: string): Promise<JwtPayload> {
    const user = await this.authService.validateUser(username, password);
    if (!user) throw new UnauthorizedException('用户名或密码错误');
    return user; // 挂到 req.user
  }
}
```

**关键点**：
- `super()` 默认从 `req.body.username` / `req.body.password` 读取，可通过 `super({ usernameField: 'email' })` 改字段
- `validate` 返回值会被 Passport 挂到 `req.user`，供后续守卫与控制器使用
- 失败抛 `UnauthorizedException` → 401，由异常过滤器转成响应
- **不区分「用户不存在」与「密码错误」**，避免攻击者通过响应差异枚举用户名

### 7. JwtStrategy：解析 token

```typescript
@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy, 'jwt') {
  constructor(configService: ConfigService) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: configService.get<string>('JWT_SECRET'),
    });
  }

  async validate(payload: JwtPayload): Promise<JwtPayload> {
    if (payload.type && payload.type !== 'access') {
      throw new UnauthorizedException('请使用 access token');
    }
    return { sub: payload.sub, username: payload.username, ... };
  }
}
```

**与 LocalStrategy 的对比**：

| 维度 | LocalStrategy | JwtStrategy |
|------|---------------|-------------|
| 输入 | username + password（请求体） | JWT（Authorization 头） |
| 校验 | 查 DB + bcrypt 比对 | 校验签名 + 过期时间 |
| 触发场景 | 登录（一次性） | 访问受保护资源（每次请求） |
| 性能 | 较慢（bcrypt 故意慢） | 很快（HMAC-SHA256） |
| 失败原因 | 账号密码错 | 签名错 / 过期 / 黑名单 |

**关键认知**：`validate(payload)` 收到的 payload 是已经验签通过的，不需要再校验签名。它的职责是「从 payload 提取出业务身份并返回」，相当于把 JWT 的解码结果转成 `req.user`。

### 8. AuthGuard('jwt') / AuthGuard('local')

```typescript
@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {}
```

`AuthGuard(name)` 是 `@nestjs/passport` 提供的工厂，返回一个守卫类，触发名为 `name` 的策略。它做了三件事：
1. 调用策略的 `authenticate` 方法
2. 把策略 `validate` 的返回值挂到 `req.user`
3. 失败时抛 `UnauthorizedException`，成功时放行

**为什么我们要再封装一层 `JwtAuthGuard` 而非直接 `@UseGuards(AuthGuard('jwt'))`**？
- 命名更直观
- 留扩展位（本章扩展了黑名单校验）
- 与 `LocalAuthGuard` 形成对称命名

### 9. Refresh Token 机制

#### 9.1 双 token 设计

| token 类型 | 有效期 | 用途 | 存储位置 |
|-----------|--------|------|---------|
| access token | 短期（15min ~ 1h） | 访问受保护资源 | 内存 / localStorage |
| refresh token | 长期（7d ~ 30d） | 换取新 access token | httpOnly cookie / 安全存储 |

#### 9.2 为什么不直接签一个超长 access token？

- **泄露窗口**：access token 一旦泄露，攻击者可在有效期内任意冒用。短期 token 把泄露窗口压到分钟级。
- **刷新频率**：长 access token 让用户不必频繁输密码，但代价是泄露风险高。
- **风控集中**：refresh token 只走 `/auth/refresh` 一个端点，便于做频率限制、IP 校验、设备指纹等风控。

#### 9.3 refresh 时必须重读 DB

```typescript
// ❌ 危险：直接信任 payload
async refreshToken(refreshToken: string) {
  const payload = await this.jwtService.verifyAsync(refreshToken);
  return this.generateTokens(payload); // 用旧 payload 签新 token
}

// ✅ 正确：用 sub 重查 DB
async refreshToken(refreshToken: string) {
  const payload = await this.jwtService.verifyAsync(refreshToken);
  const user = this.usersService.findById(payload.sub); // 拿最新身份
  return this.generateTokens({ sub: user.id, roles: user.roles, ... });
}
```

若用户在 refresh token 有效期内被撤销 admin 角色，直接信任 payload 会让攻击者继续以 admin 身份操作 7 天。**每次 refresh 都重读 DB** 是闭门安全实践。

---

## RBAC 权限模型

### 1. RBAC0：用户-角色-权限三层模型

```
┌────────┐      属于      ┌────────┐      包含      ┌────────────┐
│  User  │ ────────────▶ │  Role  │ ────────────▶ │ Permission │
└────────┘                └────────┘                └────────────┘
   alice                    admin                     article:read
                                                       article:create
                                                       article:update
                                                       article:delete
                                                       user:manage
```

| 层 | 例子 | 说明 |
|----|------|------|
| 用户 User | `alice` | 真实主体，被赋予若干角色 |
| 角色 Role | `admin` / `editor` / `visitor` | 权限的集合，便于批量授权 |
| 权限 Permission | `article:create` | 最细粒度的操作许可 |

**RBAC0 是 RBAC 家族的基础**。RBAC1 加角色继承（admin 继承 editor），RBAC2 加角色互斥 / 数量约束，RBAC3 = RBAC1 + RBAC2。本章实现的是 RBAC0，已能覆盖 90% 业务场景。

### 2. @Roles 装饰器 + RolesGuard 复用（Day08）

Day08 设计的 `@Roles('admin')` + 全局 `RolesGuard` 在本章**原样复用**，仅一处隐式变化：`req.user` 的来源从「硬编码 token 映射」变成「JwtStrategy 解析 JWT」。

```typescript
// common/decorators/roles.decorator.ts
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);

// common/roles.guard.ts
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}
  canActivate(context: ExecutionContext): boolean {
    const required = this.reflector.getAllAndOverride<string[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (!required?.length) return true;
    const user = context.switchToHttp().getRequest().user;
    return user.roles.some((r: string) => required.includes(r));
  }
}

// auth.controller.ts
@UseGuards(JwtAuthGuard)   // 认证层
@Roles('admin')            // 授权声明
@Get('admin-only')
adminOnly(@CurrentUser() user: JwtPayload) { ... }
// 全局 RolesGuard 自动跑，校验 user.roles 是否覆盖 ['admin']
```

### 3. 角色 vs 权限的取舍

| 维度 | 角色校验 `@Roles('admin')` | 权限校验 `@Permissions('article:create')` |
|------|---------------------------|------------------------------------------|
| 粒度 | 粗 | 细 |
| 灵活性 | 改角色需重新部署 | 改角色 → 权限映射可在线调整 |
| 表达力 | 「能不能进这个接口」 | 「能不能做这个操作」 |
| 适用 | 大类划分（admin / user） | 细粒度业务（文章增删改查） |

**实践建议**：路由级用角色（`@Roles('admin')`），细粒度操作用权限（`@Permissions('article:delete')`）。两者可以共存，Day08 已展示组合用法。

### 4. 权限粒度

| 粒度 | 实现 | 例子 | 复杂度 |
|------|------|------|--------|
| 路由级 | `@Roles` / `@Permissions` 装饰器 | 只有 admin 能访问 `/admin/dashboard` | 低 |
| 资源级 | 守卫内查 DB 校验「作者是否本人」 | 编辑文章时校验 `article.authorId === user.id` | 中 |
| 字段级 | 序列化时按权限过滤字段 | 普通用户看不到 `user.email`，admin 可以 | 高 |

本章实现的是**路由级**。资源级与字段级通常配合拦截器（Day09 的 `ExcludePasswordInterceptor` 是字段级雏形）与业务服务层完成。

---

## 完整认证流程实战

### 项目结构

```
src/
├── main.ts                          启动入口
├── app.module.ts                    根模块（注册 ConfigModule + AuthModule + UsersModule + 全局 RolesGuard）
├── auth/
│   ├── auth.module.ts               JwtModule.registerAsync + Passport + 策略 Provider
│   ├── auth.controller.ts           register / login / profile / refresh / logout / admin-only
│   ├── auth.service.ts              signUp / validateUser / generateTokens / refreshToken / logout
│   ├── strategies/
│   │   ├── local.strategy.ts        用户名密码 → 校验 → req.user
│   │   └── jwt.strategy.ts          JWT → 验签 → req.user
│   ├── guards/
│   │   ├── jwt-auth.guard.ts        AuthGuard('jwt') + 黑名单扩展
│   │   └── local-auth.guard.ts      AuthGuard('local')
│   └── decorators/
│       └── current-user.decorator.ts  @CurrentUser() 参数装饰器
├── users/
│   ├── users.module.ts              导出 UsersService
│   ├── users.service.ts             CRUD + bcrypt 哈希
│   ├── user.entity.ts               User / SafeUser 类型定义
│   └── dto/
│       ├── register-user.dto.ts     注册请求体
│       └── login-user.dto.ts        登录请求体
└── common/
    ├── roles.guard.ts               全局授权守卫（复用 Day08）
    ├── decorators/
    │   └── roles.decorator.ts       @Roles() 装饰器
    └── express.d.ts                 Request.user 类型扩展
```

### 1. 注册：POST /auth/register

**请求**：
```bash
curl -X POST http://localhost:3000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"alice","password":"Pass1234","roles":["editor"]}'
```

**流程**：
1. `ValidationPipe` 校验 `RegisterUserDto`（用户名 3-20 字符、密码 6-32 字符）
2. `AuthController.register` → `AuthService.signUp` → `UsersService.create`
3. `UsersService.create` 用 `bcrypt.hash(password, 10)` 哈希密码
4. 检查用户名唯一性，冲突抛 `ConflictException` → 409
5. 摊平 roles → permissions（admin 全权限、editor 读+写、visitor 只读）
6. 入内存「表」，返回 `SafeUser`（剥离 password）

**响应**：
```json
{
  "id": 2,
  "username": "alice",
  "roles": ["editor"],
  "permissions": ["article:read", "article:create", "article:update"],
  "createdAt": 1700000000000
}
```

### 2. 登录：POST /auth/login

**请求**：
```bash
curl -X POST http://localhost:3000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"alice","password":"Pass1234"}'
```

**流程**：
1. `ValidationPipe` 校验 `LoginUserDto`
2. `LocalAuthGuard` 触发 `LocalStrategy.validate(username, password)`
3. `LocalStrategy` 调用 `AuthService.validateUser`：
   - `UsersService.findByUsername` 查用户
   - `UsersService.validatePassword` → `bcrypt.compare(plain, hashed)`
   - 失败返回 null → 抛 `UnauthorizedException` → 401
4. 校验通过 → user 挂到 `req.user` → `AuthController.login`
5. `AuthService.login` → `generateTokens`：分别签发 access + refresh token
6. 返回 `TokenResponse`

**响应**：
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

### 3. 受保护资源：GET /auth/profile

**请求**：
```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
     http://localhost:3000/auth/profile
```

**流程**：
1. `JwtAuthGuard.canActivate` 先做黑名单校验
2. 委托 `AuthGuard('jwt')` → `JwtStrategy`：
   - `ExtractJwt.fromAuthHeaderAsBearerToken()` 从请求头取 token
   - 用 `JWT_SECRET` 验签 + 校验过期
   - 调用 `validate(payload)`，校验 `type === 'access'`，返回 `JwtPayload`
3. user 挂到 `req.user` → `@CurrentUser() user` 注入
4. 控制器返回 user

**响应**：
```json
{
  "sub": 2,
  "username": "alice",
  "roles": ["editor"],
  "permissions": ["article:read", "article:create", "article:update"],
  "type": "access"
}
```

### 4. 刷新 token：POST /auth/refresh

**请求**：
```bash
curl -X POST http://localhost:3000/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token":"<REFRESH_TOKEN>"}'
```

**流程**：
1. 不挂 `JwtAuthGuard`（access token 可能已过期，入口不依赖它）
2. `AuthController.refresh` 取 `refresh_token` 字段 → `AuthService.refreshToken`
3. `JwtService.verifyAsync` 校验签名 + 过期
4. 校验 `type === 'refresh'`，防止 access token 也来刷新
5. 校验黑名单
6. **重读 DB** 拿最新角色权限（防止权限被撤销后仍生效）
7. 重新签发 token 对

**响应**：与 `/auth/login` 相同的 `TokenResponse`。

### 5. 登出：POST /auth/logout

**请求**：
```bash
curl -X POST -H "Authorization: Bearer <ACCESS_TOKEN>" \
     http://localhost:3000/auth/logout
```

**流程**：
1. `JwtAuthGuard` 校验 access token
2. `AuthController.logout` 从 Authorization 头取原始 token
3. `AuthService.logout` 把 token 加入内存黑名单 `Set`
4. 后续用同一 token 访问 `/auth/profile` 时，`JwtAuthGuard` 在黑名单校验阶段直接抛 401

**响应**：
```json
{ "message": "已登出" }
```

> **黑名单局限**：本章用进程内 `Set` 实现，多实例部署不共享、重启清空、不会自动过期。生产实践用 Redis `SET` + `EXPIRE`，TTL 设为 token 剩余有效期。

---

## 与 Day08 守卫的衔接

Day08 搭建了「认证 → 授权 → 细粒度权限」的三层守卫骨架，但认证层是简化版（硬编码 token → user 映射）。本章做了一次「原地升级」：

| Day08 | Day14 | 衔接方式 |
|-------|-------|---------|
| `AuthGuard`（硬编码 token） | `JwtAuthGuard`（真 JWT） | **替代**：同样把 user 挂到 `req.user`，下游守卫无感 |
| `RolesGuard` | `RolesGuard` | **复用**：仅 `req.user` 来源变化，守卫逻辑原样 |
| `PermissionGuard` | （未实现） | 留给读者练习，可仿照 RolesGuard 扩展 |
| `@Roles('admin')` | `@Roles('admin')` | **复用**：装饰器与元数据 Key 完全不变 |
| `@Public()` 白名单 | （未实现） | 本章用「不挂守卫」表达公开路由，更直观 |
| 硬编码 token 映射 | `LocalStrategy` + `JwtStrategy` | **新增**：从假认证变真认证 |
| 全局 `APP_GUARD` 注册 | 全局 `APP_GUARD` 只注册 `RolesGuard` | **调整**：认证守卫按需挂载，因为 login 走 local、profile 走 jwt，不能一刀切 |

**核心设计原则**：守卫之间通过 `req.user` 解耦，认证层的升级不影响授权层。这种「黑盒替换」能力是分层架构的最大价值。

---

## 关键知识点总结

### JWT 结构图

```
                  JWT 三段结构
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   header.payload.signature                                       │
│                                                                  │
│   ┌────────┐   ┌─────────────────┐   ┌──────────────────────┐  │
│   │ header │ . │    payload      │ . │      signature       │  │
│   ├────────┤   ├─────────────────┤   ├──────────────────────┤  │
│   │ alg    │   │ sub / username  │   │ HMAC-SHA256(         │  │
│   │ typ    │   │ roles / perms   │   │   base64(header) +   │  │
│   │        │   │ type / iat / exp│   │   "." +              │  │
│   │        │   │                 │   │   base64(payload),   │  │
│   │        │   │                 │   │   JWT_SECRET         │  │
│   │        │   │                 │   │ )                    │  │
│   └────────┘   └─────────────────┘   └──────────────────────┘  │
│   Base64URL    Base64URL            二进制                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

   签发：JwtService.sign(payload, { secret, expiresIn })
   校验：JwtService.verifyAsync(token)  →  payload / 抛错
   解码：JwtService.decode(token)       →  payload（不验签，仅调试）
```

### Passport 策略速查表

| 策略 | 包 | 触发方式 | 输入 | 输出 | validate 签名 |
|------|----|---------|------|------|--------------|
| local | passport-local | `AuthGuard('local')` | req.body.username/password | user 挂 req.user | `(username, password) => user` |
| jwt | passport-jwt | `AuthGuard('jwt')` | Authorization: Bearer token | payload 挂 req.user | `(payload) => user` |
| google | passport-google-oauth20 | `AuthGuard('google')` | OAuth 回调 code | profile 挂 req.user | `(accessToken, refreshToken, profile) => user` |
| github | passport-github | `AuthGuard('github')` | OAuth 回调 code | profile 挂 req.user | `(accessToken, refreshToken, profile) => user` |
| oauth2 | passport-oauth2 | `AuthGuard('oauth2')` | OAuth 回调 code | profile 挂 req.user | `(accessToken, refreshToken, profile) => user` |

### 关键文件速查

| 文件 | 关键点 |
|------|--------|
| `auth.module.ts` | `JwtModule.registerAsync` 注入 ConfigService 读 `.env` |
| `auth.service.ts` | `generateTokens` 同时签 access + refresh；`refreshToken` 重读 DB |
| `local.strategy.ts` | `super()` 默认从 body 读 username/password，不查 session |
| `jwt.strategy.ts` | `secretOrKey` 必须与签发端一致；`validate` 收到的 payload 已验签 |
| `jwt-auth.guard.ts` | 扩展 `AuthGuard('jwt')` 加黑名单校验 |
| `users.service.ts` | `bcrypt.hash(plain, 10)` 与 `bcrypt.compare(plain, hashed)` 配对 |
| `roles.guard.ts` | 与 Day08 完全一致，仅 `req.user` 来源不同 |

### 安全清单

- [x] 密码用 bcrypt 哈希，saltRounds ≥ 10
- [x] JWT_SECRET 不进代码仓库，从 `.env` 读
- [x] payload 不含敏感信息（密码、密钥、身份证号）
- [x] access token 短期，refresh token 长期
- [x] refresh 时重读 DB 拿最新身份
- [x] 登出有黑名单（生产用 Redis）
- [ ] HTTPS 强制（生产部署必须）
- [ ] refresh token 走 httpOnly cookie（防 XSS 偷取）
- [ ] 限流：`/auth/login` 与 `/auth/refresh` 必须限流防爆破

---

## 实战练习

### 练习 1：实现 `@Permissions` 装饰器与 `PermissionGuard`

参照 `@Roles` + `RolesGuard` 的设计，实现细粒度权限校验：

1. 在 `common/decorators/permissions.decorator.ts` 中实现 `@Permissions('article:create', 'article:delete')`
2. 在 `common/permission.guard.ts` 中实现 `PermissionGuard`，从 `req.user.permissions` 与路由要求做交集
3. 在 `auth.controller.ts` 中新增 `@Permissions('user:manage')` 保护的路由，验证只有 admin 能访问

**验收**：用 `visitor` 角色访问该路由应返回 403，且响应 message 含「缺少权限 user:manage」。

### 练习 2：用 Redis 替换内存黑名单

本章的黑名单是进程内 `Set`，多实例部署不共享、重启清空。把它替换成 Redis 实现：

1. 安装 `ioredis` 与 `@nestjs-modules/ioredis`
2. 在 `auth.service.ts` 中注入 Redis 客户端
3. `logout` 时执行 `redis.set('jwt:blacklist:' + token, '1', 'EX', remainingSeconds)`
4. `isBlacklisted` 改为 `redis.get('jwt:blacklist:' + token)`

**验收**：登出后访问 `/auth/profile` 返回 401；等 token 过期后 Redis 自动清理该 key。

### 练习 3：access token 自动续期中间件

实现「滑动续期」：当 access token 还剩 5 分钟过期时，在响应头自动塞一个新 token，前端无感刷新。

1. 实现一个 `AutoRefreshInterceptor`（参考 Day09 拦截器）
2. 在响应前检查 `req.user.exp`，若 < 5 分钟，签发新 token 放 `X-New-Access-Token` 响应头
3. 前端拦截响应头，若有则替换本地 token

**验收**：在 token 过期前 5 分钟内访问 `/auth/profile`，响应头能看到 `X-New-Access-Token`。

---

完成本章后，你已掌握 NestJS 认证授权的完整工程方案：bcrypt 哈希、JWT 签发与校验、Passport 策略模式、Refresh Token 机制、RBAC 三层模型、与守卫的分层衔接。这套方案可直接迁移到生产项目，下一章将在其基础上扩展 OAuth2 第三方登录与双因素认证。
