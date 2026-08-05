# Day07 - 管道与数据校验

## 本章简介

管道（Pipe）是 NestJS 请求生命周期中负责**数据转换**与**数据校验**的组件。当一次 HTTP 请求穿过中间件、守卫之后，真正进入控制器方法之前，管道会先对参数进行加工：把字符串形态的路径参数、查询参数转换成 `number` / `boolean` / `Date`，或者对请求体（DTO）逐字段做格式与范围校验。管道是类型安全请求体的核心保障——没有管道，控制器的 TypeScript 类型注解只是一份"君子协定"，运行时仍会收到未经校验的原始字符串。

NestJS 内置了覆盖常见场景的管道家族：`ValidationPipe` 基于 `class-validator` + `class-transformer` 对 DTO 做声明式校验；`ParseIntPipe` / `ParseFloatPipe` / `ParseBoolPipe` 负责基本类型转换；`ParseUUIDPipe` 与 `ParseEnumPipe` 保证特定格式与枚举值合法；`DefaultValuePipe` 为缺失参数兜底。当内置管道无法满足需求时，开发者只需实现 `PipeTransform` 接口的 `transform(value, metadata)` 方法即可编写自定义管道，本章会实战三个自定义管道：教学版 `ParseIntPipe`、字符串净化的 `TrimPipe`、分页参数转换的 `PaginationPipe`。

本章还将深入讲解管道的三个应用层级（参数级、方法级、全局级）与两种全局注册方式（`app.useGlobalPipes` 与 `APP_PIPE` Provider），并通过 `class-validator` 的全部常用装饰器、嵌套对象校验、自定义校验装饰器等实战内容，构建一套可直接用于生产环境的参数校验体系。

## 学习目标

- 理解管道在 NestJS 请求生命周期中的位置与两个核心职责：数据转换（transform）与数据校验（validate）。
- 掌握 `PipeTransform<T, R>` 接口与 `transform(value, metadata)` 方法的签名与执行机制。
- 熟练使用 NestJS 全部内置管道：`ValidationPipe`、`ParseIntPipe`、`ParseFloatPipe`、`ParseBoolPipe`、`ParseUUIDPipe`、`ParseEnumPipe`、`DefaultValuePipe`。
- 能够在参数级、方法级、全局级三个层级灵活挂载管道，并区分 `app.useGlobalPipes` 与 `APP_PIPE` 两种全局注册方式的差异。
- 掌握 `ValidationPipe` + `class-validator` + `class-transformer` 的完整工作流，能编写覆盖字符串、数字、邮箱、枚举、数组、嵌套对象的 DTO。
- 能够编写自定义 Pipe（`ParseIntPipe` 教学版、`TrimPipe`、`PaginationPipe`）与自定义校验装饰器（`@IsAfterNow`）。
- 清楚管道相对于守卫、拦截器的执行时机，避免把校验逻辑放错层级。

## 理论知识讲解

### 1. 管道 Pipe 的两个职责

管道做两件事，且这两件事在同一次 `transform` 调用中可以同时完成：

| 职责 | 说明 | 典型场景 | 失败行为 |
| --- | --- | --- | --- |
| **数据转换（transform）** | 把输入值转换成期望的类型或结构后返回。 | 路径参数 `"123"` → `number` `123`；查询参数 `"true"` → `boolean` `true`；分页参数 `{ page: "2", pageSize: "10" }` → `{ page: 2, pageSize: 10, skip: 10, take: 10 }` | 转换失败时抛 `BadRequestException` |
| **数据校验（validate）** | 检查输入值是否符合规则，不符合则抛异常。 | DTO 字段是否为邮箱、是否满足最小长度、是否在枚举范围内 | 校验失败时抛 `BadRequestException`，响应体包含错误详情 |

> 关键认知：转换与校验不是互斥的。`ValidationPipe` 在 `transform: true` 模式下会先做类型转换（借助 `class-transformer`），再做校验（借助 `class-validator`），两步合一。

### 2. PipeTransform 接口

所有管道都实现 `PipeTransform<T, R>` 接口，其中 `T` 是输入值类型，`R` 是输出值类型：

```ts
interface PipeTransform<T = any, R = any> {
  transform(value: T, metadata: ArgumentMetadata): R;
}

interface ArgumentMetadata {
  type: 'body' | 'query' | 'param' | 'custom';  // 参数来源
  metatype?: new (...args: any[]) => any;        // 参数的元类型（DTO 类）
  data?: string;                                  // 装饰器传入的 key，如 @Param('id') 中的 'id'
}
```

- `value`：当前参数的值。对于 `@Param('id')` 是路径参数字符串；对于 `@Body()` 是请求体对象；对于 `@Query()` 是查询参数对象。
- `metadata.type`：参数来源，决定管道是否需要处理该参数。例如 `TrimPipe` 可能只想处理 `body` 类型。
- `metadata.metatype`：参数的 TypeScript 类型对应的类。`@Body() body: CreateArticleDto` 的 metatype 是 `CreateArticleDto`；`@Param('id') id: string` 的 metatype 是 `String`。`ValidationPipe` 依赖此字段判断是否需要校验。
- `metadata.data`：装饰器传入的参数名。`@Param('id')` 的 data 是 `'id'`；`@Body()` 无参数时 data 是 `undefined`。

一个最小的自定义管道：

```ts
@Injectable()
export class UpperCasePipe implements PipeTransform<string, string> {
  transform(value: string, metadata: ArgumentMetadata): string {
    return value.toUpperCase();
  }
}
```

### 3. NestJS 内置 Pipe

NestJS 提供了七个开箱即用的管道，覆盖类型转换、格式校验、默认值兜底三类场景：

| 内置 Pipe | 职责 | 输入 → 输出 | 失败时 |
| --- | --- | --- | --- |
| `ValidationPipe` | 基于 DTO 做声明式校验与类型转换 | 普通对象 → DTO 类实例（`transform: true` 时） | 收集所有字段错误后一次性抛出 |
| `ParseIntPipe` | 把字符串转成整数 | `"123"` → `123` | `"abc"` → 400 |
| `ParseFloatPipe` | 把字符串转成浮点数 | `"3.14"` → `3.14` | `"abc"` → 400 |
| `ParseBoolPipe` | 把字符串转成布尔值 | `"true"` / `"1"` → `true`；`"false"` / `"0"` → `false` | `"yes"` → 400 |
| `ParseUUIDPipe` | 校验 UUID 格式（默认 v4） | `"550e8400-e29b-41d4-a716-446655440000"` → 原值 | `"abc"` → 400 |
| `ParseEnumPipe` | 校验值是否在指定枚举范围内 | `"admin"` → `UserRole.ADMIN` | `"superadmin"` → 400 |
| `DefaultValuePipe` | 当参数为 `undefined` 时返回默认值 | `undefined` → `'viewer'` | 不抛异常 |

使用方式分为两类：

**作为类传入装饰器**（NestJS 自动实例化，最常见）：

```ts
@Get(':id')
findOne(@Param('id', ParseIntPipe) id: number) { ... }
```

**传入实例**（需要配置选项时）：

```ts
@Get(':id')
findOne(
  @Param('id', new ParseIntPipe({ error: () => new NotFoundException('用户不存在') }))
  id: number,
) { ... }
```

### 4. Pipe 的三个应用层级

管道可以挂载在三个不同层级，作用范围从窄到宽：

#### 参数级（Param-level）

直接在参数装饰器中传入 Pipe，只对该参数生效：

```ts
@Get(':id')
findOne(
  @Param('id', ParseIntPipe) id: number,        // 仅 id 被转换
  @Query('page', ParseIntPipe) page: number,    // 仅 page 被转换
) { ... }
```

适用场景：只需要对个别参数做类型转换或格式校验。

#### 方法级（Method-level）

通过 `@UsePipes()` 装饰器挂在控制器方法上，对该方法的所有参数生效：

```ts
@Post()
@UsePipes(new ValidationPipe({ whitelist: true }))
create(@Body() body: CreateArticleDto, @Query() query: QueryDto) { ... }
```

适用场景：某个方法需要特殊校验规则，但又不想全局生效。

#### 全局级（Global-level）

注册一次，对所有控制器的所有方法的所有参数生效。有两种注册方式（见下一节）：

```ts
// 方式一：main.ts
app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));

// 方式二：AppModule
{ provide: APP_PIPE, useClass: ValidationPipe }
```

适用场景：`ValidationPipe` 几乎总是全局注册，保证所有 DTO 都被校验。

> 三个层级的执行顺序：全局 → 控制器级（`@UsePipes` 在控制器类上）→ 方法级 → 参数级。同层级内按声明顺序执行。

### 5. 全局 Pipe 注册的两种方式

| 对比项 | `app.useGlobalPipes()` | `APP_PIPE` Provider |
| --- | --- | --- |
| 注册位置 | `main.ts` | `AppModule` 的 `providers` |
| 依赖注入 | ❌ 不支持，Pipe 实例需手动 `new` | ✅ 支持，NestJS 通过 DI 容器实例化 |
| 可测试性 | 较弱，与 `main.ts` 耦合 | 强，可在测试模块中替换 |
| 配置灵活性 | 直接传实例，选项一目了然 | 需要 `useClass` / `useValue` / `useFactory` |
| 典型场景 | `ValidationPipe` 无外部依赖时 | Pipe 需要 `ConfigService` 等注入依赖时 |

**方式一：`app.useGlobalPipes`（本章 `main.ts` 采用）**

```ts
// main.ts
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
  }),
);
```

**方式二：`APP_PIPE` Provider（本章 `app.module.ts` 采用）**

```ts
// app.module.ts
import { APP_PIPE } from '@nestjs/core';

@Module({
  providers: [
    {
      provide: APP_PIPE,
      useClass: TrimPipe,  // NestJS 通过 DI 实例化，可注入其他 Provider
    },
  ],
})
export class AppModule {}
```

> 两种方式可以共存。本章在 `main.ts` 用 `useGlobalPipes` 注册 `ValidationPipe`，在 `app.module.ts` 用 `APP_PIPE` 注册 `TrimPipe`，同时演示两种方式。生产环境中如果只有一个全局 Pipe，任选其一即可；如果 Pipe 需要注入 `ConfigService` 等依赖，必须用 `APP_PIPE`。

## ValidationPipe + class-validator 详解

### 1. 安装依赖

```bash
npm install class-validator class-transformer
```

- `class-validator`：提供基于装饰器的校验规则（`@IsString`、`@IsEmail` 等），底层依赖 `validator.js`。
- `class-transformer`：负责把普通字面对象转换成 DTO 类实例，让 `class-validator` 的装饰器元数据生效。同时提供 `@Type()` 装饰器处理嵌套对象的类型转换。

两个库必须同时安装，缺一不可。`class-validator` 的装饰器只对类的实例生效，而 HTTP 请求体经过 `JSON.parse` 后只是普通对象，`class-transformer` 负责补上这一步实例化。

### 2. DTO 装饰器全览

以下是 `class-validator` 提供的常用装饰器，本章 `create-article.dto.ts` 会逐一演示：

| 装饰器 | 作用 | 示例 |
| --- | --- | --- |
| `@IsString()` | 必须是字符串 | `@IsString() title: string` |
| `@IsInt()` | 必须是整数 | `@IsInt() @Min(0) readTime: number` |
| `@IsEmail()` | 必须是合法邮箱 | `@IsEmail() authorEmail: string` |
| `@IsOptional()` | 字段可缺省 | `@IsOptional() @IsString() author?: string` |
| `@IsEnum(Enum)` | 必须是枚举成员 | `@IsEnum(ArticleStatus) status: ArticleStatus` |
| `@MinLength(n)` | 字符串最小长度 | `@MinLength(3) title: string` |
| `@MaxLength(n)` | 字符串最大长度 | `@MaxLength(100) title: string` |
| `@Min(n)` | 数字最小值 | `@Min(0) readTime: number` |
| `@Max(n)` | 数字最大值 | `@Max(1000) readTime: number` |
| `@IsArray()` | 必须是数组 | `@IsArray() tags: string[]` |
| `@IsString({ each: true })` | 数组每项都是字符串 | `@IsString({ each: true }) tags: string[]` |
| `@ValidateNested()` | 校验嵌套对象 | `@ValidateNested() @Type(() => MetaDto) meta: MetaDto` |
| `@IsDate()` | 必须是 Date 对象 | `@IsDate() publishAt: Date` |
| `@IsNotEmpty()` | 不能为空字符串 | `@IsNotEmpty() title: string` |

> 每个装饰器都接受 `validationOptions?` 参数，可自定义错误消息：`@MinLength(3, { message: '标题至少 3 个字符' })`。

### 3. ValidationPipe 选项

`ValidationPipe` 的构造函数接收一个 `ValidationPipeOptions` 对象，核心选项如下：

| 选项 | 类型 | 默认值 | 作用 |
| --- | --- | --- | --- |
| `whitelist` | `boolean` | `false` | 设为 `true` 后，DTO 上没有装饰器的字段会被自动剥离。防止传入未声明的多余字段。 |
| `forbidNonWhitelisted` | `boolean` | `false` | 设为 `true` 后，传入多余字段时直接抛 400 错误，而不是静默剥离。必须配合 `whitelist: true` 使用。 |
| `transform` | `boolean` | `false` | 设为 `true` 后，请求体会被转换成 DTO 类实例，路径/查询参数也会根据 TS 类型自动转换。 |
| `transformOptions` | `object` | `{}` | 传给 `class-transformer` 的选项。常用 `enableImplicitConversion: true` 开启基于 TS 类型的隐式转换。 |
| `disableErrorMessages` | `boolean` | `false` | 设为 `true` 后错误响应只返回字段名不返回消息，减少响应体体积。 |
| `validationError.target` | `boolean` | `true` | 是否在错误对象中包含 DTO 实例。生产环境建议设为 `false` 避免泄露敏感数据。 |
| `validationError.value` | `boolean` | `true` | 是否在错误对象中包含被校验的值。生产环境建议设为 `false`。 |

本章 `main.ts` 的推荐配置：

```ts
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,            // 剥离未声明字段
    forbidNonWhitelisted: true, // 多余字段直接报错
    transform: true,            // 开启类型转换
    transformOptions: {
      enableImplicitConversion: true,  // 基于 TS 类型自动转换
    },
  }),
);
```

### 4. 嵌套对象校验

当 DTO 包含嵌套对象或嵌套数组时，需要 `@ValidateNested()` + `@Type()` 配合使用：

```ts
import { ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';

class ArticleMetaDto {
  @IsString()
  @MinLength(1)
  key: string;

  @IsString()
  value: string;
}

class CreateArticleDto {
  // 单个嵌套对象
  @IsOptional()
  @ValidateNested()
  @Type(() => ArticleMetaDto)
  primaryMeta?: ArticleMetaDto;

  // 嵌套对象数组
  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => ArticleMetaDto)
  metadata?: ArticleMetaDto[];
}
```

> **必须同时加 `@Type(() => XxxDto)`**。`@ValidateNested()` 只负责触发嵌套校验，但 `class-transformer` 默认不会把普通对象转成嵌套 DTO 实例，没有 `@Type()` 的话嵌套对象的装饰器不会生效，校验形同虚设。这是最易踩的坑。

### 5. 自定义校验装饰器

当内置装饰器无法表达业务规则时，可以通过 `registerDecorator` 编写自定义校验装饰器。本章 `src/common/custom-validators.ts` 实现了两个：

**`@IsAfterNow`：校验日期必须晚于当前时间**

```ts
import { registerDecorator, ValidationOptions, ValidationArguments } from 'class-validator';

export function IsAfterNow(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'isAfterNow',
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      validator: {
        validate(value: any, args: ValidationArguments) {
          const date = value instanceof Date ? value : new Date(value);
          if (isNaN(date.getTime())) return false;
          return date.getTime() > Date.now();
        },
        defaultMessage(args: ValidationArguments) {
          return `${args.property} 必须晚于当前时间`;
        },
      },
    });
  };
}
```

**`@IsNotBlank`：校验字符串不能全是空白字符**

```ts
export function IsNotBlank(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'isNotBlank',
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      validator: {
        validate(value: any) {
          return typeof value === 'string' && value.trim().length > 0;
        },
        defaultMessage(args: ValidationArguments) {
          return `${args.property} 不能为空或纯空白字符`;
        },
      },
    });
  };
}
```

使用方式与内置装饰器一致：

```ts
@IsAfterNow({ message: '发布时间必须晚于当前时间' })
@Type(() => Date)
publishAt: Date;
```

## 自定义 Pipe 实战

### 1. 自定义 ParseIntPipe 实现（教学用）

内置 `ParseIntPipe` 的核心逻辑非常简单，自己实现一份有助于理解 `PipeTransform` 的工作机制：

```ts
// src/pipes/parse-int.pipe.ts
@Injectable()
export class CustomParseIntPipe implements PipeTransform<string, number> {
  transform(value: string, metadata: ArgumentMetadata): number {
    const val = parseInt(value, 10);
    if (isNaN(val)) {
      throw new BadRequestException(
        `参数 "${metadata.data}" 必须是整数，但收到: "${value}"`,
      );
    }
    return val;
  }
}
```

> 内置 `ParseIntPipe` 还处理了 `Infinity`、非字符串输入、自定义异常工厂等边界情况。这个教学版只保留核心逻辑，用于演示 `PipeTransform` 接口。使用方式见 `src/users/users.controller.ts` 的 `GET /users/custom/:id` 路由。

### 2. 自定义 TrimPipe：字符串去空格

`TrimPipe` 会递归遍历请求体中的所有字符串字段，去除两端空格。注册为全局 Pipe 后，所有控制器的 `@Body()` 都会自动净化：

```ts
// src/pipes/trim.pipe.ts
@Injectable()
export class TrimPipe implements PipeTransform {
  transform(value: any, metadata: ArgumentMetadata) {
    if (metadata.type !== 'body') return value;  // 只处理请求体
    if (value === null || value === undefined) return value;
    return this.trimDeep(value);
  }

  private trimDeep(value: any): any {
    if (typeof value === 'string') return value.trim();
    if (Array.isArray(value)) return value.map((item) => this.trimDeep(item));
    if (typeof value === 'object') {
      const result: Record<string, any> = {};
      for (const key of Object.keys(value)) {
        result[key] = this.trimDeep(value[key]);
      }
      return result;
    }
    return value;
  }
}
```

> 这个 Pipe 在本章通过 `APP_PIPE` 注册为全局管道（见 `app.module.ts`），演示了支持依赖注入的全局注册方式。注意：`TrimPipe` 只处理 `metadata.type === 'body'` 的参数，不会影响路径参数和查询参数。

### 3. 自定义 PaginationPipe：分页参数转换

`PaginationPipe` 把散落的 `page`、`pageSize` 查询参数转换成结构化的分页对象，同时计算 `skip`、`take` 供数据库查询直接使用：

```ts
// src/pipes/pagination.pipe.ts
export interface PaginationOptions {
  page: number;
  pageSize: number;
  skip: number;   // 数据库偏移量：(page - 1) * pageSize
  take: number;   // 数据库取数上限：pageSize
}

@Injectable()
export class PaginationPipe implements PipeTransform<any, PaginationOptions> {
  transform(value: any, metadata: ArgumentMetadata): PaginationOptions {
    if (metadata.type !== 'query') return value;
    const page = Math.max(1, parseInt(value?.page, 10) || 1);
    const pageSize = Math.min(100, Math.max(1, parseInt(value?.pageSize, 10) || 10));
    return { page, pageSize, skip: (page - 1) * pageSize, take: pageSize };
  }
}
```

使用方式见 `src/articles/articles.controller.ts` 的 `GET /articles/paginated` 路由，通过方法级 `@UsePipes(new PaginationPipe())` 挂载。

## 管道执行时机

管道在 NestJS 请求生命周期中的位置如下：

```
请求进入
  │
  ▼
中间件 (Middleware)
  │
  ▼
守卫 (Guard)          ← 鉴权，决定是否放行
  │
  ▼
管道 (Pipe)           ← 数据转换 + 数据校验  ★ 本章主角
  │
  ▼
拦截器前置 (Interceptor.before)
  │
  ▼
控制器方法 (Controller Method)
  │
  ▼
拦截器后置 (Interceptor.after)
  │
  ▼
异常过滤器 (Exception Filter)  ← 仅在以上任一环节抛异常时触发
  │
  ▼
响应返回
```

关键认知：

- **管道在守卫之后**：意味着未通过鉴权的请求不会触发管道校验，避免对非法请求做无用的 DTO 实例化。
- **管道在拦截器之前**：拦截器拿到的已经是校验通过、类型正确的数据，可以放心做日志、缓存、响应转换。
- **管道在控制器方法之前**：控制器方法体收到的参数一定是合法的，不需要再写 `if (!body.title) throw ...` 之类的手动校验。
- **异常过滤器在最外层**：管道抛出的 `BadRequestException` 会被异常过滤器捕获并格式化成统一的错误响应。

> 这个执行顺序解释了为什么校验逻辑应该放在管道而不是守卫或拦截器：守卫只负责鉴权（能不能访问），不应该关心数据格式；拦截器面向横切关注点（日志、缓存），做校验会污染职责。管道正是为数据加工而生的组件。

## 关键知识点总结

### 内置 Pipe 速查表

| Pipe | 用途 | 典型用法 | 失败状态码 |
| --- | --- | --- | --- |
| `ValidationPipe` | DTO 整体校验 + 类型转换 | 全局注册 `app.useGlobalPipes(new ValidationPipe(...))` | 400 |
| `ParseIntPipe` | 字符串 → 整数 | `@Param('id', ParseIntPipe) id: number` | 400 |
| `ParseFloatPipe` | 字符串 → 浮点数 | `@Param('score', ParseFloatPipe) score: number` | 400 |
| `ParseBoolPipe` | 字符串 → 布尔值 | `@Param('active', ParseBoolPipe) active: boolean` | 400 |
| `ParseUUIDPipe` | 校验 UUID 格式 | `@Param('uuid', ParseUUIDPipe) uuid: string` | 400 |
| `ParseEnumPipe` | 校验枚举值 | `@Param('role', new ParseEnumPipe(UserRole)) role: UserRole` | 400 |
| `DefaultValuePipe` | 缺省值兜底 | `@Query('page', new DefaultValuePipe(1)) page: number` | 不抛异常 |

### ValidationPipe 选项速查表

| 选项 | 作用 | 推荐值 |
| --- | --- | --- |
| `whitelist` | 剥离 DTO 未声明的字段 | `true` |
| `forbidNonWhitelisted` | 多余字段直接报错 | `true` |
| `transform` | 开启类型转换与 DTO 实例化 | `true` |
| `transformOptions.enableImplicitConversion` | 基于 TS 类型自动转换 | `true` |
| `disableErrorMessages` | 隐藏错误详情 | 生产环境 `true`，开发环境 `false` |
| `validationError.target` | 错误对象是否含 DTO 实例 | 生产环境 `false` |
| `validationError.value` | 错误对象是否含原始值 | 生产环境 `false` |

### 管道层级速查表

| 层级 | 注册方式 | 作用范围 | 适用场景 |
| --- | --- | --- | --- |
| 参数级 | `@Param('id', ParseIntPipe)` | 单个参数 | 单个路径/查询参数的类型转换 |
| 方法级 | `@UsePipes(new XxxPipe())` | 单个控制器方法 | 方法专属校验逻辑 |
| 控制器级 | `@UsePipes()` 在类上 | 控制器内所有方法 | 控制器级别的统一校验 |
| 全局级 | `app.useGlobalPipes()` 或 `APP_PIPE` | 全应用 | `ValidationPipe` 几乎总是全局注册 |

### 全局 Pipe 两种注册方式对比

| 维度 | `useGlobalPipes` | `APP_PIPE` |
| --- | --- | --- |
| 位置 | `main.ts` | `AppModule` providers |
| DI 支持 | ❌ | ✅ |
| 测试可替换性 | 弱 | 强 |
| 多 Pipe 共存 | 调用多次即可 | 多个 `APP_PIPE` Provider |
| 本章使用 | 注册 `ValidationPipe` | 注册 `TrimPipe` |

## 实战练习

### 练习 1：扩展 CreateArticleDto 的校验规则

在 `src/articles/dto/create-article.dto.ts` 中完成以下任务：

1. 新增 `slug` 字段，要求只包含小写字母、数字和连字符，使用 `@Matches(/^[a-z0-9-]+$/)` 装饰器。
2. 新增 `summary` 字段，可选，最大长度 200，使用 `@IsOptional()` + `@IsString()` + `@MaxLength(200)`。
3. 在 `tags` 数组上增加 `@ArrayMinSize(1)` 和 `@ArrayMaxSize(10)` 装饰器（需从 `class-validator` 导入），限制标签数量。
4. 用 curl 或 Postman 发送请求测试这些规则是否生效。

提示：`@Matches` 接收正则表达式作为第一个参数，`message` 选项可自定义错误提示。

### 练习 2：实现一个 PasswordStrengthPipe

在 `src/pipes/` 下新建 `password-strength.pipe.ts`，实现一个校验密码强度的管道：

- 要求：密码长度至少 8 位，必须同时包含大写字母、小写字母和数字。
- 当密码不满足要求时，抛出 `BadRequestException` 并说明具体缺少哪一项。
- 在 `UsersController` 中新增 `POST /users` 接口，`@Body()` 接收 `{ password: string; name: string }`，通过方法级 `@UsePipes(new PasswordStrengthPipe())` 挂载。
- 思考：这个管道只校验密码还是校验整个 body？如何通过 `metadata.data` 或字段名判断当前处理的是 `password` 字段？

### 练习 3：对比 useGlobalPipes 与 APP_PIPE 的执行顺序

通过实验验证两种全局注册方式的管道执行顺序：

1. 在 `main.ts` 的 `ValidationPipe` 之前再加一个 `app.useGlobalPipes(new TrimPipe())`。
2. 在 `app.module.ts` 中把 `APP_PIPE` 的 `useClass` 改成 `ValidationPipe`，注释掉 `main.ts` 中的 `useGlobalPipes`。
3. 分别启动应用，发送带多余空格和不合法字段的请求，观察 `TrimPipe` 是否在 `ValidationPipe` 之前执行（空格是否被先去除再校验）。
4. 记录两种配置下 `TrimPipe` 与 `ValidationPipe` 的相对执行顺序，并解释为什么生产环境通常把所有全局 Pipe 放在同一个注册位置。

---

## 运行示例代码

```bash
cd "Day07 - 管道与数据校验/Code"
npm install
npm run start:dev
```

预期输出：

- `ValidationPipe` 全局生效：发送不符合 DTO 规则的请求体会收到 400 错误，错误信息包含每个字段的校验详情。
- `TrimPipe` 全局生效：发送 `"  hello  "` 会在控制器中收到 `"hello"`。
- `ParseIntPipe` / `ParseUUIDPipe` / `ParseEnumPipe` 参数级生效：访问 `/users/abc` 会收到"必须是整数"的错误。
- `PaginationPipe` 方法级生效：访问 `/articles/paginated?page=2&pageSize=5` 会收到 `{ page: 2, pageSize: 5, skip: 5, take: 5 }`。
- 自定义校验装饰器 `@IsAfterNow` 生效：发送过去的日期作为 `publishAt` 会收到校验错误。

测试命令示例：

```bash
# 1. 创建文章（合法请求）
curl -X POST http://localhost:3000/api/v1/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"NestJS 管道详解","content":"管道负责数据转换与校验...","authorEmail":"author@example.com","status":"draft","tags":["nestjs","pipe"]}'

# 2. 创建文章（非法请求，触发 ValidationPipe）
curl -X POST http://localhost:3000/api/v1/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"ab","content":"短","authorEmail":"not-an-email"}'

# 3. 路径参数类型转换（触发 ParseIntPipe）
curl http://localhost:3000/api/v1/users/abc

# 4. UUID 格式校验（触发 ParseUUIDPipe）
curl http://localhost:3000/api/v1/users/uuid/not-a-uuid

# 5. 分页参数转换（触发方法级 PaginationPipe）
curl "http://localhost:3000/api/v1/articles/paginated?page=2&pageSize=5"

# 6. TrimPipe 测试（全局 APP_PIPE，去除 body 字符串两端空格）
curl -X POST http://localhost:3000/api/v1/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"  trimmed title  ","content":"content here","authorEmail":"a@b.com"}'
```
