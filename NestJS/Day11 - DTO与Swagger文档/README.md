# Day11 - DTO 与 Swagger 文档

DTO（Data Transfer Object）是请求与响应之间的数据契约：它规定了客户端必须传哪些字段、每个字段的类型与取值范围，也规定了服务端会返回哪些字段、绝不返回哪些字段。Swagger（OpenAPI）则把这份契约可视化成可交互的 API 文档——前端工程师不用读源码、不用反复问后端，打开 `/api-docs` 就能看清每个接口的请求体、响应体、状态码，甚至直接在浏览器里发起请求验证。本章把"DTO 设计 → 装饰器元数据 → Swagger 文档生成"这条链路完整走通，让代码本身成为唯一的 API 真相来源。

---

## 学习目标

完成本章后，你应能：

- 用一句话讲清 DTO 与 Entity 的边界，知道为什么"请求 DTO""响应 DTO"要分开
- 列举 `@nestjs/mapped-types` 的四个派生工具（`PartialType` / `PickType` / `OmitType` / `IntersectionType`）的用法与适用场景
- 解释 `class-transformer` 的 `plainToInstance` 在请求/响应转换中的作用
- 在 `main.ts` 用 `DocumentBuilder` + `SwaggerModule.createDocument` + `SwaggerModule.setup` 三步挂载 Swagger UI
- 在控制器上正确使用 `@ApiTags` / `@ApiOperation` / `@ApiResponse` / `@ApiParam` / `@ApiQuery` / `@ApiBody` / `@ApiBearerAuth`
- 在 DTO 字段上用 `@ApiProperty` / `@ApiPropertyOptional` 描述字段，包括 `required` / `example` / `description` / `enum` / `minimum` / `maximum`
- 配置 Bearer Token 认证，让 Swagger UI 右上角出现 "Authorize" 按钮
- 为分页查询、错误响应、枚举字段等场景写出完整的文档化代码

---

## 理论知识讲解 - DTO 部分

### 1. DTO 模式回顾

**DTO（Data Transfer Object）** 是一种专门用于"在层与层之间传递数据"的简单对象。在 NestJS 中，它通常表现为一个被 `class-validator` 与 `@nestjs/swagger` 装饰器修饰的 TypeScript class。

DTO 与 Entity 的关键区别：

| 维度 | Entity | DTO |
|------|--------|-----|
| 表达的是 | 数据库模型 | API 契约 |
| 字段依据 | 数据库表结构 | 接口语义 |
| 是否含敏感字段 | 通常含（如 `password`、`isDeleted`） | 按接口需求决定（响应 DTO 通常不含敏感字段） |
| 是否含主键 | 含（如 `id`） | 请求 DTO 不含，响应 DTO 含 |
| 是否含时间戳 | 含（`createdAt` / `updatedAt`） | 请求 DTO 不含，响应 DTO 含 |
| 装饰器 | TypeORM `@Column` / Prisma schema | `@IsString` / `@ApiProperty` |

#### 1.1 请求 DTO vs 响应 DTO

**请求 DTO** 描述客户端应该传什么：

```typescript
export class CreateUserDto {
  @ApiProperty({ example: 'alice' })
  @IsString()
  @MinLength(3)
  username: string;

  @ApiProperty({ example: 'p@ssw0rd123' })
  @IsString()
  @MinLength(6)
  password: string;   // 创建用户需要密码
}
```

**响应 DTO** 描述服务端会返回什么：

```typescript
export class UserResponseDto extends OmitType(CreateUserDto, ['password']) {
  @ApiProperty()
  id: number;

  @ApiProperty()
  createdAt: string;
  // 没有 password —— 永远不返回密码
}
```

把两者分开的核心动机：

- **安全**：响应 DTO 可以显式剔除 `password`、`isDeleted`、`internalNote` 等字段
- **解耦**：数据库加字段不会自动泄漏到 API；API 加字段不会强制改数据库
- **可演进**：请求 DTO 可以加 `@IsOptional()` 字段做兼容，不影响已有客户端

### 2. class-validator 装饰器回顾（呼应 Day07）

Day07 已经详细讲过 `class-validator` 的常用装饰器，这里只做速查表回顾，重点是它们如何与 `@ApiProperty` 协同：

| class-validator | 含义 | 对应 Swagger 自动识别 |
|----------------|------|---------------------|
| `@IsString()` | 必须是字符串 | `type: String` |
| `@IsInt()` | 必须是整数 | `type: Number` |
| `@IsEmail()` | 必须是邮箱 | `format: 'email'` |
| `@IsEnum(Role)` | 必须是枚举成员 | `enum: Role` |
| `@IsArray()` | 必须是数组 | `type: []` |
| `@MinLength(3)` / `@MaxLength(100)` | 字符串长度 | `minLength` / `maxLength` |
| `@Min(0)` / `@Max(1000)` | 数值范围 | `minimum` / `maximum` |
| `@IsOptional()` | 字段可选 | `required: false`（即 `@ApiPropertyOptional`） |

> 关键认知：当你在 `main.ts` 启用 `ValidationPipe` 后，DTO 上的 class-validator 装饰器同时承担"运行时校验"和"文档元数据"两个角色。`@nestjs/swagger` 会读取这些元数据自动生成 schema，你只需要再用 `@ApiProperty` 补充人类可读的 `description` / `example` 即可。

### 3. class-transformer 的 plainToInstance

`class-transformer` 提供的 `plainToInstance`（旧版叫 `plainToClass`）把一个普通 JS 对象转换成某个 class 的实例。它在 NestJS 里有两个典型场景：

#### 3.1 请求体自动转换（由 ValidationPipe 完成）

当 `ValidationPipe` 开启 `transform: true` 后，传入的普通 JSON 对象会被自动 `plainToInstance(CreateUserDto, body)` 转成 DTO 实例。这样控制器方法拿到的 `dto` 不只是结构匹配的 plain object，而是真正的 `CreateUserDto` 实例：

```typescript
@Post()
create(@Body() dto: CreateUserDto) {
  // dto instanceof CreateUserDto === true
  // dto 上的 @IsString 等装饰器都可被 reflect-metadata 读取
  console.log(dto.constructor.name); // 'CreateUserDto'
}
```

#### 3.2 响应 DTO 转换（手动调用）

服务端返回响应时，如果想强制按响应 DTO 的结构序列化（比如自动剥离 `password`），可以手动调用：

```typescript
import { plainToInstance } from 'class-transformer';

findOne(id: number) {
  const user = this.userRepo.findById(id);  // Entity 含 password
  return plainToInstance(UserResponseDto, user, {
    excludeExtraneousValues: true,  // 只输出 @Expose 标记的字段
  });
}
```

> 提示：本章 Demo 为了让代码更直观，没有用 `plainToInstance` + `@Exclude`，而是用解构 `const { password, ...rest } = user` 做剥离。生产代码推荐用 `class-transformer` 的方案，更不易遗漏字段。

### 4. DTO 继承与复用：PartialType / PickType / OmitType / IntersectionType

`@nestjs/mapped-types` 提供四个派生工具，避免重复定义相似 DTO：

| 工具 | 作用 | 典型场景 |
|------|------|---------|
| `PartialType(Base)` | 全部字段变可选 | PATCH 部分更新 |
| `PickType(Base, ['id', 'name'])` | 选取指定字段 | 改密码 DTO 只需 `password` |
| `OmitType(Base, ['password'])` | 剔除指定字段 | 响应 DTO 隐藏敏感字段 |
| `IntersectionType(A, B)` | 合并多个 DTO | 分页查询 = 分页基类 + 过滤条件 |

#### 4.1 CreateUserDto → UpdateUserDto

```typescript
// 更新用户时不允许改 username（唯一标识），其余字段全部可选
export class UpdateUserDto extends PartialType(
  OmitType(CreateUserDto, ['username'] as const),
) {}
```

派生类自动继承父类的所有装饰器（class-validator 与 Swagger 的），不需要重复写 `@IsString` / `@ApiProperty`。

#### 4.2 分页查询的 IntersectionType 复用

把分页字段抽到 `PaginationDto` 基类，所有资源的查询 DTO 都用它组合：

```typescript
// src/common/pagination.dto.ts
export class PaginationDto {
  @ApiPropertyOptional({ default: 1, minimum: 1 })
  @IsOptional() @IsInt() @Min(1) page?: number = 1;

  @ApiPropertyOptional({ default: 10, minimum: 1, maximum: 100 })
  @IsOptional() @IsInt() @Min(1) @Max(100) pageSize?: number = 10;
}

// src/articles/dto/query-article.dto.ts
export class QueryArticleDto extends IntersectionType(
  PaginationDto,
  class {
    @ApiPropertyOptional({ enum: ArticleStatus })
    @IsOptional() @IsEnum(ArticleStatus) status?: ArticleStatus;

    @ApiPropertyOptional()
    @IsOptional() @IsString() keyword?: string;
  },
) {}
```

`articles` / `users` / `orders` 都可以同样继承 `PaginationDto`，避免每个资源的查询 DTO 都重复声明 `page` / `pageSize`。

### 5. 响应 DTO 的派生：OmitType / PickType / IntersectionType

响应 DTO 通常从"完整模型"派生：

```typescript
// 响应 DTO 隐藏 password（基于 CreateUserDto 派生）
export class UserResponseDto extends OmitType(CreateUserDto, ['password']) {
  @ApiProperty() id: number;
  @ApiProperty() createdAt: string;
}

// 列表场景只需要 id 和 title（PickType）
export class ArticleListItemDto extends PickType(ArticleResponseDto, [
  'id', 'title', 'status', 'createdAt',
] as const) {}

// 详情 + 作者信息（IntersectionType）
export class ArticleDetailDto extends IntersectionType(ArticleResponseDto, UserResponseDto) {}
```

---

## 理论知识讲解 - Swagger 部分

### 1. @nestjs/swagger 安装与配置

```bash
npm install @nestjs/swagger
```

集成只需三步，全部写在 `main.ts`：

```typescript
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';

// 1. 用 DocumentBuilder 构建文档元信息
const config = new DocumentBuilder()
  .setTitle('My API')
  .setDescription('API 描述')
  .setVersion('1.0.0')
  .addBearerAuth()           // 启用 Bearer 认证
  .addTag('文章', '文章相关接口') // 预定义分组
  .build();

// 2. 基于 AppModule 扫描装饰器元数据，生成 OpenAPI 文档对象
const document = SwaggerModule.createDocument(app, config);

// 3. 把 Swagger UI 挂到 /api-docs 路径
SwaggerModule.setup('api-docs', app, document);
```

启动后访问 `http://localhost:3000/api-docs` 即可看到 Swagger UI；访问 `http://localhost:3000/api-docs-json` 可拿到原始 OpenAPI JSON（可导入 Postman / Apifox）。

#### 工作原理

NestJS 启动时为每个控制器与 DTO 收集装饰器元数据（依赖 `reflect-metadata`）；`SwaggerModule.createDocument` 读取这些元数据按 OpenAPI 3 规范组装 JSON；`setup` 把 JSON 挂到 `/api-docs-json`，并把 Swagger UI 静态资源挂到 `/api-docs`。

### 2. 控制器装饰器

| 装饰器 | 作用域 | 用途 |
|--------|--------|------|
| `@ApiTags('文章')` | 类 | 把控制器归到"文章"分组 |
| `@ApiOperation({ summary, description })` | 方法 | 描述接口用途 |
| `@ApiResponse({ status, description, type })` | 方法 | 描述某个状态码的响应 |
| `@ApiOkResponse` / `@ApiCreatedResponse` | 方法 | 200 / 201 响应（`@ApiResponse` 的快捷方式） |
| `@ApiNotFoundResponse` / `@ApiBadRequestResponse` | 方法 | 404 / 400 响应（快捷方式） |
| `@ApiHeader({ name, description })` | 方法/类 | 描述请求头 |
| `@ApiQuery({ name, type, enum })` | 方法 | 描述查询参数（@Query() 整体接收时可不加） |
| `@ApiParam({ name, type })` | 方法 | 描述路径参数（@Param() 整体接收时可不加） |
| `@ApiBody({ type })` | 方法 | 描述请求体（@Body() 整体接收时可不加） |
| `@ApiBearerAuth()` | 方法/类 | 标记需要 Bearer Token 认证 |

> 关键原则：当用 `@Body() dto: SomeDto` 整体接收 DTO 时，Swagger 会自动读取 DTO 的 `@ApiProperty` 生成请求体 schema，**不需要**再写 `@ApiBody`。`@ApiBody` 主要用于"请求体不是某个 DTO 全部"或"需要为接口单独说明字段"的场景。

### 3. DTO 装饰器

| 装饰器 | 用途 |
|--------|------|
| `@ApiProperty({ description, example, ... })` | 必填字段 |
| `@ApiPropertyOptional({ ... })` | 可选字段 |

常用选项：

```typescript
@ApiProperty({
  description: '文章标题',
  example: 'NestJS 入门',
  minLength: 3,
  maxLength: 100,
  minimum: 0,         // 数值下限
  maximum: 1000,
  default: 'draft',
  enum: ArticleStatus,// 枚举字段
  type: [String],     // 数组字段类型
  format: 'email',    // 字符串格式
  deprecated: true,   // 标记为已废弃
})
title: string;
```

### 4. 认证配置：addBearerAuth + @ApiBearerAuth

#### 4.1 在 DocumentBuilder 中配置 Bearer 认证方案

```typescript
const config = new DocumentBuilder()
  .addBearerAuth(
    {
      type: 'http',
      scheme: 'bearer',
      bearerFormat: 'JWT',
      description: '输入 JWT token',
    },
    'access-token',  // 安全方案的 name（可选，默认 'bearer'）
  )
  .build();
```

#### 4.2 在控制器/方法上标记需要认证

```typescript
@ApiBearerAuth()              // 用默认 name 'bearer'
@ApiBearerAuth('access-token') // 用自定义 name
@Controller('articles')
export class ArticlesController { ... }
```

挂上 `@ApiBearerAuth` 后，Swagger UI 右上角会出现 "Authorize" 按钮；填入 token 后所有标记的接口会自动在请求头加上 `Authorization: Bearer <token>`。

### 5. 访问 Swagger UI

| 路径 | 内容 |
|------|------|
| `http://localhost:3000/api-docs` | Swagger UI（交互式文档） |
| `http://localhost:3000/api-docs-json` | OpenAPI 3 原始 JSON |

---

## Swagger 实战

### 1. 完整的 Articles CRUD 文档化

`ArticlesController` 演示了 7 个接口的完整文档化：

| 方法 | 路径 | 装饰器组合 |
|------|------|-----------|
| GET | `/articles` | `@ApiOperation` + `@ApiOkResponse(type=ArticleListResponseDto)` |
| GET | `/articles/:id` | `@ApiOperation` + `@ApiParam` + `@ApiOkResponse` + `@ApiNotFoundResponse` |
| POST | `/articles` | `@ApiOperation` + `@ApiBody(type=CreateArticleDto)` + `@ApiCreatedResponse` + `@ApiBadRequestResponse` |
| PATCH | `/articles/:id` | `@ApiOperation` + `@ApiParam` + `@ApiBody(type=UpdateArticleDto)` + `@ApiOkResponse` + `@ApiNotFoundResponse` |
| DELETE | `/articles/:id` | `@ApiOperation` + `@ApiParam` + `@ApiNotFoundResponse`（204 无响应体） |
| POST | `/articles/:id/publish` | 演示独立的 `PublishArticleDto` 请求体 |

关键代码片段（创建接口）：

```typescript
@Post()
@HttpCode(HttpStatus.CREATED)
@ApiOperation({
  summary: '创建文章',
  description: '需要登录，请求体需通过 class-validator 校验。',
})
@ApiBody({ description: '文章内容', type: CreateArticleDto })
@ApiCreatedResponse({ description: '创建成功', type: ArticleResponseDto })
@ApiBadRequestResponse({ description: '请求参数校验失败' })
@ApiUnauthorizedResponse({ description: '未登录或 token 失效' })
create(@Body() dto: CreateArticleDto) {
  return this.articlesService.create(dto);
}
```

### 2. 分页查询 DTO 的文档化

`QueryArticleDto` 用 `IntersectionType(PaginationDto, ...)` 组合分页与过滤字段：

```typescript
export class QueryArticleDto extends IntersectionType(
  PaginationDto,
  class {
    @ApiPropertyOptional({ description: '关键词搜索', example: 'NestJS' })
    @IsOptional() @IsString() keyword?: string;

    @ApiPropertyOptional({ enum: ArticleStatus, example: ArticleStatus.PUBLISHED })
    @IsOptional() @IsEnum(ArticleStatus) status?: ArticleStatus;

    @ApiPropertyOptional({ enum: ArticleSortField, default: ArticleSortField.CREATED_AT })
    @IsOptional() @IsEnum(ArticleSortField) sort?: ArticleSortField;

    @ApiPropertyOptional({ enum: SortOrder, default: SortOrder.DESC })
    @IsOptional() @IsEnum(SortOrder) order?: SortOrder;
  },
) {}
```

在 Swagger UI 中你会看到 6 个查询参数（`page` / `pageSize` / `keyword` / `status` / `sort` / `order`），每个都有示例值和合法枚举提示。

### 3. 错误响应的文档化

每个接口都显式声明可能出现的错误响应：

```typescript
@Get(':id')
@ApiOperation({ summary: '获取文章详情' })
@ApiOkResponse({ description: '文章详情', type: ArticleResponseDto })
@ApiNotFoundResponse({ description: '文章不存在' })  // 404
findOne(@Param('id', ParseIntPipe) id: number) { ... }
```

`@ApiNotFoundResponse` / `@ApiBadRequestResponse` / `@ApiUnauthorizedResponse` 都是 `@ApiResponse({ status: ... })` 的快捷方式。需要自定义状态码时直接用 `@ApiResponse`：

```typescript
@ApiResponse({ status: 423, description: '文章被锁定，无法修改' })
@ApiResponse({ status: 429, description: '请求频率超限' })
```

### 4. 枚举字段的文档化

把枚举传给 `@ApiPropertyOptional` / `@ApiProperty` 的 `enum` 选项，Swagger UI 会渲染成下拉框：

```typescript
@ApiPropertyOptional({
  description: '文章状态',
  enum: ArticleStatus,             // ← 传枚举本身
  default: ArticleStatus.DRAFT,
  example: ArticleStatus.DRAFT,
})
@IsOptional()
@IsEnum(ArticleStatus)
status?: ArticleStatus;
```

效果：用户在 Swagger UI 看到 `status` 字段时，下拉框只有 `draft` / `published` / `archived` 三个合法选项，传错值直接被前端校验拦下，避免发请求浪费往返。

---

## DTO 与 Entity 的分离原则

```
HTTP 请求 ─► [请求 DTO] ─► Controller ─► Service ─► [Entity] ─► Database
                                              │
                                              ▼
                                          [Entity]
                                              │
                                              ▼
                                          Service 转换
                                              │
                                              ▼
HTTP 响应 ◄─ [响应 DTO] ◄─ Controller ◄────────┘
```

**三层模型**：

| 层 | 角色 | 字段依据 |
|----|------|---------|
| 请求 DTO | 客户端 → 服务端的契约 | 接口语义（创建接口需要哪些字段） |
| Entity | 服务端内部 + 数据库模型 | 数据库表结构 |
| 响应 DTO | 服务端 → 客户端的契约 | 接口语义（前端需要看到哪些字段） |

**Service 的转换职责**：

```typescript
@Injectable()
export class ArticlesService {
  create(dto: CreateArticleDto): ArticleResponseDto {
    // 1. 请求 DTO → Entity（加 id、时间戳、默认值）
    const entity = {
      id: this.nextId++,
      ...dto,
      status: dto.status ?? ArticleStatus.DRAFT,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.articles.push(entity);

    // 2. Entity → 响应 DTO（剥离内部字段）
    return this.toResponse(entity);
  }

  private toResponse(entity: ArticleEntity): ArticleResponseDto {
    const { authorId, ...rest } = entity;  // 剥离 authorId
    return rest as ArticleResponseDto;
  }
}
```

**为什么不让控制器直接返回 Entity？**

1. **安全风险**：Entity 通常含 `password` / `isDeleted` / `internalNote` 等字段，直接返回会泄漏
2. **耦合扩大**：数据库加字段会自动改变 API 响应结构，破坏前端兼容
3. **测试困难**：响应结构受 Entity 影响，难以稳定断言
4. **文档失真**：Swagger 无法准确描述响应结构，文档与实际不一致

---

## 关键知识点总结

### Swagger 装饰器速查表

| 装饰器 | 作用域 | 用途 |
|--------|--------|------|
| `@ApiTags('名')` | 类 | 接口分组 |
| `@ApiOperation({ summary, description })` | 方法 | 接口说明 |
| `@ApiBody({ type })` | 方法 | 请求体（整体 DTO 接收时可省略） |
| `@ApiParam({ name, type, example })` | 方法 | 路径参数 |
| `@ApiQuery({ name, type, enum })` | 方法 | 查询参数（整体 DTO 接收时可省略） |
| `@ApiHeader({ name, description })` | 方法/类 | 请求头 |
| `@ApiResponse({ status, description, type })` | 方法 | 任意状态码响应 |
| `@ApiOkResponse` | 方法 | 200 响应 |
| `@ApiCreatedResponse` | 方法 | 201 响应 |
| `@ApiBadRequestResponse` | 方法 | 400 响应 |
| `@ApiUnauthorizedResponse` | 方法 | 401 响应 |
| `@ApiNotFoundResponse` | 方法 | 404 响应 |
| `@ApiBearerAuth()` | 方法/类 | 标记需要 Bearer 认证 |
| `@ApiProperty({ description, example, ... })` | DTO 字段 | 必填字段 |
| `@ApiPropertyOptional({ ... })` | DTO 字段 | 可选字段 |
| `@ApiExtension('x-xxx', value)` | 任意 | 扩展字段（如 `x-codeSamples`） |

### `@ApiProperty` 常用选项

| 选项 | 类型 | 用途 |
|------|------|------|
| `description` | string | 字段说明 |
| `example` | any | 示例值 |
| `default` | any | 默认值 |
| `enum` | Enum | 枚举合法值 |
| `type` | Type \| [Type] | 字段类型（数组用 `[Type]`） |
| `format` | string | 字符串格式（`'email'` / `'uuid'` / `'date-time'`） |
| `minimum` / `maximum` | number | 数值范围 |
| `minLength` / `maxLength` | number | 字符串长度 |
| `required` | boolean | 是否必填（默认 true） |
| `deprecated` | boolean | 是否废弃 |
| `readOnly` | boolean | 只读（仅响应） |
| `writeOnly` | boolean | 只写（仅请求） |

### mapped-types 速查表

| 工具 | 签名 | 语义 | 典型场景 |
|------|------|------|---------|
| `PartialType(Base)` | 全字段可选 | PATCH 更新 | `UpdateUserDto extends PartialType(CreateUserDto)` |
| `PickType(Base, ['id'])` | 选取字段 | 列表项 | `ArticleListItemDto extends PickType(ArticleResponseDto, ['id','title'])` |
| `OmitType(Base, ['password'])` | 剔除字段 | 响应隐藏敏感 | `UserResponseDto extends OmitType(CreateUserDto, ['password'])` |
| `IntersectionType(A, B)` | 合并字段 | 复用组合 | `QueryDto extends IntersectionType(PaginationDto, FilterDto)` |

### 三大原则

1. **代码即文档**：DTO 上的装饰器同时驱动运行时校验与文档生成，永远不要手写独立的 API 文档
2. **请求与响应分离**：永远不要用同一个 DTO 同时描述请求与响应，敏感字段会泄漏
3. **复用而非重复**：用 `mapped-types` 派生新 DTO，避免"加字段忘改 UpdateDto"的脏数据

---

## 实战练习

### 练习 1：为文章增加"评论"资源

在 `src/comments/` 下新增完整的评论模块：

1. `CreateCommentDto`：含 `articleId`（正整数）、`content`（5~500 字符）、`authorId`（正整数）
2. `CommentResponseDto`：用 `OmitType` 派生，加上 `id` / `createdAt`
3. `CommentsController`：CRUD 接口，全部加 `@ApiTags('评论')` 与 `@ApiOperation`
4. 在 `main.ts` 的 `DocumentBuilder` 里 `.addTag('评论', '文章评论接口')`
5. 启动后到 Swagger UI 验证"评论"分组能否正常显示

### 练习 2：自定义错误响应 schema

当前所有 `@ApiNotFoundResponse` 只写 `description`，没指定 `type`。请：

1. 在 `src/common/` 下新增 `error-response.dto.ts`，定义 `{ code, message, details, timestamp, path }`
2. 把 `ArticlesController` 的所有 `@ApiNotFoundResponse` / `@ApiBadRequestResponse` 改成
   `@ApiResponse({ status: 404, type: ErrorResponseDto, description: '...' })`
3. 在 Swagger UI 验证 404 响应结构能正确显示 schema

> 提示：这其实就是呼应 Day10 的统一错误响应格式——让文档与过滤器输出对齐。

### 练习 3：用 IntersectionType 组合分页与排序

`QueryArticleDto` 目前用 `IntersectionType(PaginationDto, class { ... })` 内联定义过滤类。请：

1. 把过滤字段提取成独立的 `ArticleFilterDto`（含 `keyword` / `status`）
2. 把排序字段提取成独立的 `SortDto`（含 `sort` / `order`）
3. 把 `QueryArticleDto` 改成 `IntersectionType(PaginationDto, ArticleFilterDto, SortDto)`
   （`@nestjs/mapped-types` 的 `IntersectionType` 支持两个以上的类）
4. 验证 Swagger UI 是否仍能正确展示所有查询参数

---

## 本章代码结构

```
Day11 - DTO与Swagger文档/
├── Code/
│   ├── package.json                       # 含 @nestjs/swagger / mapped-types / class-validator / class-transformer
│   ├── tsconfig.json
│   ├── tsconfig.build.json
│   ├── nest-cli.json
│   └── src/
│       ├── main.ts                        # DocumentBuilder + SwaggerModule.setup 挂载 /api-docs
│       ├── app.module.ts                  # 根模块，导入 ArticlesModule / UsersModule
│       ├── common/
│       │   ├── pagination.dto.ts          # PaginationDto 基类（可被多个 QueryDto 复用）
│       │   └── api-response.dto.ts        # ApiResponseDto<T> 统一响应信封
│       ├── articles/
│       │   ├── articles.controller.ts     # 完整 CRUD + 发布接口，全部 Swagger 装饰器
│       │   ├── articles.service.ts        # 内存数据 + DTO ↔ Entity 转换
│       │   ├── articles.module.ts
│       │   └── dto/
│       │       ├── create-article.dto.ts  # 请求 DTO + @ApiProperty
│       │       ├── update-article.dto.ts  # PartialType(OmitType(CreateArticleDto, ['authorId']))
│       │       ├── query-article.dto.ts   # IntersectionType(PaginationDto, Filter)
│       │       └── article-response.dto.ts# OmitType(CreateArticleDto, ['authorId']) + 加 id/时间戳
│       └── users/
│           ├── users.controller.ts        # CRUD（请求含 password，响应不含）
│           ├── users.service.ts           # 响应剥离 password
│           ├── users.module.ts
│           └── dto/
│               ├── create-user.dto.ts     # 含 password（敏感）
│               └── user-response.dto.ts   # OmitType(CreateUserDto, ['password'])
└── README.md
```

### 运行方式

```bash
cd "Day11 - DTO与Swagger文档/Code"
npm install
npm run start:dev
```

启动后访问：

| URL | 内容 |
|-----|------|
| `http://localhost:3000/api-docs` | Swagger UI（交互式 API 文档） |
| `http://localhost:3000/api-docs-json` | OpenAPI 3 原始 JSON |
| `http://localhost:3000/api/v1/articles` | 文章列表接口 |

### 体验路径

| 请求 | 说明 | 验证点 |
|------|------|--------|
| `GET /api/v1/articles` | 分页查询 | 在 Swagger UI 看到所有查询参数（含枚举下拉框） |
| `POST /api/v1/articles` | 创建文章 | 请求体示例自动填充，422 校验失败时显示错误 |
| `GET /api/v1/articles/1` | 获取详情 | 404 响应 schema 正确显示 |
| `PATCH /api/v1/articles/1` | 部分更新 | UpdateArticleDto 字段全部可选 |
| `DELETE /api/v1/articles/1` | 删除 | 204 No Content |
| `POST /api/v1/users` | 创建用户 | **请求体含 password，响应体不含 password**（DTO 分离的核心示例） |
| 点击右上角 "Authorize" | Bearer 认证 | 输入任意字符串，所有接口自动带 `Authorization` 头 |
