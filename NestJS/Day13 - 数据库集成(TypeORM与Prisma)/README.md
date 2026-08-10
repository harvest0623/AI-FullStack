# Day13 - 数据库集成（TypeORM 与 Prisma）

ORM（Object-Relational Mapping）把数据库表映射成 TypeScript 类，把行映射成对象，让 SQL 操作从字符串拼接变成类型安全的方法调用。NestJS 在官方文档里同时支持两套主流方案：TypeORM（装饰器驱动、传统 OOP 范式）与 Prisma（Schema 优先、生成式强类型 Client）。本章把两套方案在同一个 NestJS 项目里完整跑通，从连接配置、实体定义、关系映射，到 Repository 模式与 Prisma 查询，再到迁移命令，最后用一张对比表说清二者在范式、类型安全、迁移、生态上的差异，让你在不同业务场景下能做出合理选型。

---

## 学习目标

完成本章后，你应能：

- 用一句话讲清 ORM 在 NestJS 项目中解决了什么问题，以及它和原生 SQL、查询构建器的层级关系
- 区分 TypeORM 的 Active Record 与 Data Mapper 两种范式，知道 NestJS 默认推荐哪种
- 用 `TypeOrmModule.forRoot` / `forRootAsync` / `forFeature` 三种方法分别完成全局连接、异步配置、模块级仓库注册
- 用 `@Entity` / `@Column` / `@PrimaryGeneratedColumn` / `@CreateDateColumn` / `@UpdateDateColumn` 装饰器定义实体，并理解它们各自生成的 DDL
- 用 `@OneToOne` / `@OneToMany` / `@ManyToOne` / `@ManyToMany` + `@JoinColumn` 表达四种关系，知道外键落在哪一边
- 在 Service 里用 `@InjectRepository(Entity)` 注入 `Repository<Entity>`，调用 `find / findOne / save / update / remove` 等方法
- 走通 TypeORM 迁移三连命令：`migration:generate` / `migration:run` / `migration:revert`
- 用 `forRootAsync` 配合 `ConfigService` 从环境变量读取数据库连接参数，呼应 Day12 的配置体系
- 写出一份合法的 `schema.prisma`：`datasource` / `generator` / `model` 三块，并解释 Prisma 的 Schema 优先为什么能带来端到端类型安全
- 跑通 Prisma 三连命令：`prisma init` / `prisma generate` / `prisma migrate dev`
- 封装 `PrismaService extends PrismaClient` + `onModuleInit`，并把 `PrismaModule` 标记为 `@Global()` 让全应用共享
- 用 `include` / `select` / 嵌套 `where` 完成常见的 Prisma 关系查询
- 在新项目立项时，根据团队习惯、性能要求、迁移成本列出 TypeORM 与 Prisma 的取舍依据

---

## 理论知识讲解 - TypeORM 部分

### 1. TypeORM 简介

TypeORM 是 Node.js 生态里最老牌的 ORM 之一，最大特点是 **装饰器风格**：用 `@Entity` / `@Column` 这类装饰器把 TypeScript 类直接标注成表结构，借助 `emitDecoratorMetadata` 在运行时反射出字段类型，从而自动生成 DDL。

TypeORM 支持两种使用范式：

| 范式 | 基类 | 调用方式 | 优点 | 缺点 |
|------|------|---------|------|------|
| **Active Record** | `BaseEntity` | `User.find()` / `user.save()` 直接在实体上调用 | 简单、链式短 | 实体耦合数据访问，难做单元测试 |
| **Data Mapper** | 无 | 通过 `Repository<User>` 调用 `repo.find()` / `repo.save(user)` | 关注点分离，易测试 | 多一层注入，代码稍长 |

NestJS 官方文档默认演示的是 **Data Mapper** 范式，本章也采用这一范式，更贴合大型项目的工程实践。

### 2. @nestjs/typeorm 三个核心方法

`@nestjs/typeorm` 是 NestJS 对 TypeORM 的官方封装，提供三个方法：

#### 2.1 `TypeOrmModule.forRoot(options)`

在根模块 `AppModule` 里调用一次，建立全局数据库连接：

```typescript
import { TypeOrmModule } from '@nestjs/typeorm';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'sqlite',
      database: ':memory:',
      entities: [User, Article],
      synchronize: true, // 仅开发环境，自动建表
    }),
  ],
})
export class AppModule {}
```

#### 2.2 `TypeOrmModule.forRootAsync(options)`

异步版本，配合 `ConfigService` 读取环境变量。生产环境永远用这个版本：

```typescript
TypeOrmModule.forRootAsync({
  imports: [ConfigModule],
  inject: [ConfigService],
  useFactory: (config: ConfigService) => ({
    type: 'sqlite',
    database: config.get<string>('DB_DATABASE', ':memory:'),
    entities: [User, Article],
    synchronize: config.get<string>('NODE_ENV') !== 'production',
  }),
})
```

> 这是 Day12 配置体系在数据层的延续：所有连接参数都从 `.env` 读，不写死在代码里。

#### 2.3 `TypeOrmModule.forFeature([Entity1, Entity2])`

在子模块里调用，注册该模块需要用到的实体，并把对应的 `Repository<Entity>` 加入该模块的 DI 容器：

```typescript
@Module({
  imports: [TypeOrmModule.forFeature([Article])],
  providers: [ArticlesService],
  controllers: [ArticlesController],
})
export class ArticlesModule {}
```

只有 `forFeature` 过的实体，才能在 Service 里 `@InjectRepository(Article)` 注入。

### 3. 实体装饰器

#### 3.1 完整实体示例

```typescript
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';

@Entity('articles') // 表名 articles
export class Article {
  @PrimaryGeneratedColumn()          // 自增主键
  id: number;

  @Column({ length: 200 })           // varchar(200)
  title: string;

  @Column({ type: 'text', nullable: true })
  content: string | null;

  @Column({ default: 0 })
  viewCount: number;

  @CreateDateColumn()                // INSERT 时自动写入
  createdAt: Date;

  @UpdateDateColumn()                // UPDATE 时自动刷新
  updatedAt: Date;
}
```

#### 3.2 装饰器速查

| 装饰器 | 作用 | 对应 DDL |
|--------|------|---------|
| `@Entity(name)` | 把类标记为表 | `CREATE TABLE name` |
| `@PrimaryGeneratedColumn()` | 自增主键 | `id INTEGER PRIMARY KEY AUTOINCREMENT` |
| `@PrimaryGeneratedColumn('uuid')` | UUID 主键 | `id TEXT PRIMARY KEY` |
| `@Column(options)` | 普通列 | 根据 `type` 决定 |
| `@CreateDateColumn()` | 创建时间 | `createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `@UpdateDateColumn()` | 更新时间 | `updatedAt TIMESTAMP` 自动更新 |
| `@DeleteDateColumn()` | 软删除时间 | 配合 `softRemove` 实现 |
| `@VersionColumn()` | 乐观锁版本号 | 每次更新 +1 |

### 4. 关系映射

TypeORM 用四个装饰器表达实体间关系：

| 装饰器 | 数量关系 | 外键位置 |
|--------|---------|---------|
| `@OneToOne` | 1 ↔ 1 | 任意一方，用 `@JoinColumn` 指定 |
| `@OneToMany` | 1 ↔ N | 总是落在"多"的一方 |
| `@ManyToOne` | N ↔ 1 | 落在当前实体 |
| `@ManyToMany` | M ↔ N | 第三张中间表，用 `@JoinTable` 指定 |

#### 4.1 示例：User 1 ↔ N Article

```typescript
// user.entity.ts
@Entity('users')
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @OneToMany(() => Article, (article) => article.author)
  articles: Article[];
}

// article.entity.ts
@Entity('articles')
export class Article {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  title: string;

  @ManyToOne(() => User, (user) => user.articles)
  @JoinColumn({ name: 'author_id' }) // 显式指定外键列名
  author: User;
}
```

> **关键**：`@JoinColumn` 永远只写在一侧，它决定了外键列落在哪张表。`@OneToMany` 一侧不写 `@JoinColumn`，它只是反向引用。

#### 4.2 关系加载策略

- `eager: true`：自动 `JOIN` 加载，每次查 Article 都带出 author
- `eager: false`（默认）：需手动 `relations: ['author']`

```typescript
@ManyToOne(() => User, (user) => user.articles, { eager: false })
author: User;
```

### 5. Repository 模式

#### 5.1 注入 Repository

```typescript
@Injectable()
export class ArticlesService {
  constructor(
    @InjectRepository(Article)
    private readonly articleRepo: Repository<Article>,
  ) {}

  findAll() {
    return this.articleRepo.find({
      relations: ['author'],
      order: { createdAt: 'DESC' },
    });
  }

  findOne(id: number) {
    return this.articleRepo.findOne({
      where: { id },
      relations: ['author'],
    });
  }

  create(dto: CreateArticleDto) {
    const article = this.articleRepo.create(dto);
    return this.articleRepo.save(article);
  }

  async update(id: number, dto: UpdateArticleDto) {
    const article = await this.articleRepo.preload({ id, ...dto });
    if (!article) throw new NotFoundException(`Article ${id} not found`);
    return this.articleRepo.save(article);
  }

  async remove(id: number) {
    const result = await this.articleRepo.delete(id);
    if (result.affected === 0) throw new NotFoundException(`Article ${id} not found`);
  }
}
```

#### 5.2 Repository 常用方法

| 方法 | 作用 | 等价 SQL |
|------|------|---------|
| `find(options)` | 条件查询多条 | `SELECT ... WHERE ...` |
| `findOne(options)` | 查询单条 | `SELECT ... WHERE ... LIMIT 1` |
| `findBy({ field: value })` | 简化条件查询 | `SELECT ... WHERE field = value` |
| `create(dto)` | 创建实例（不入库） | 仅 `new` |
| `save(entity)` | 插入或更新 | `INSERT` / `UPDATE` |
| `preload(like)` | 根据 id 加载后合并字段 | `SELECT` + `UPDATE` |
| `update(id, dto)` | 直接更新 | `UPDATE` |
| `delete(id)` | 物理删除 | `DELETE` |
| `softDelete(id)` | 软删除 | `UPDATE deletedAt` |
| `count(options)` | 计数 | `SELECT COUNT(*)` |
| `createQueryBuilder()` | 链式查询 | 复杂 SQL |

### 6. 迁移 migrations

`synchronize: true` 只用于开发自动建表，生产必须用迁移。三步走：

#### 6.1 配置

```typescript
// data-source.ts（独立运行，不走 NestJS DI）
import { DataSource } from 'typeorm';

export default new DataSource({
  type: 'sqlite',
  database: './db.sqlite',
  entities: ['src/**/*.entity.ts'],
  migrations: ['src/migrations/*.ts'],
});
```

#### 6.2 三个命令

```bash
# 1. 对比 entities 与数据库差异，生成迁移文件
npx typeorm-ts-node-commonjs migration:generate src/migrations/Init

# 2. 执行未应用的迁移
npx typeorm-ts-node-commonjs migration:run

# 3. 回滚最近一次迁移
npx typeorm-ts-node-commonjs migration:revert
```

#### 6.3 迁移文件结构

```typescript
export class Init1700000000000 implements MigrationInterface {
  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(new Table({ /* ... */ }));
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('articles');
  }
}
```

> 迁移文件必须提交到 git，团队成员拉代码后 `migration:run` 即可同步表结构。

### 7. forRootAsync 配合 ConfigService

完整接线：

```typescript
// app.module.ts
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        type: 'sqlite',
        database: config.get<string>('DB_DATABASE', ':memory:'),
        entities: [__dirname + '/**/*.entity{.ts,.js}'],
        synchronize: config.get<string>('NODE_ENV') !== 'production',
      }),
    }),
  ],
})
export class AppModule {}
```

环境变量：

```bash
# .env
DB_DATABASE=:memory:
NODE_ENV=development
```

---

## 理论知识讲解 - Prisma 部分

### 1. Prisma 简介

Prisma 是新一代 ORM，三件套：

- **Prisma Schema**：用 `.prisma` 文件描述数据模型，单一真相源
- **Prisma Client**：根据 schema 自动生成的强类型查询客户端
- **Prisma Studio**：可视化数据浏览界面（`npx prisma studio`）

与 TypeORM 最大差异：**没有装饰器，没有反射**，所有类型在 `prisma generate` 阶段生成到 `node_modules/.prisma/client` 里。这带来两个好处：

1. **端到端类型安全**：schema 改了，client 立刻反映，TypeScript 编译期就能挡住错误
2. **查询自动补全**：IDE 能补全 `prisma.article.findMany({ where: { ... } })` 里所有字段

### 2. Prisma 三连命令

| 命令 | 作用 | 何时用 |
|------|------|--------|
| `npx prisma init` | 初始化 `prisma/schema.prisma` + `.env` | 新项目第一次 |
| `npx prisma generate` | 根据 schema 重新生成 Prisma Client | 改完 schema 必跑 |
| `npx prisma migrate dev --name xxx` | 生成迁移 + 应用到数据库 + 重新生成 client | 开发期改 schema |
| `npx prisma migrate deploy` | 仅执行迁移（生产） | CI/CD 部署 |
| `npx prisma db push` | 直接同步 schema 到数据库（不生成迁移） | 原型阶段快速迭代 |
| `npx prisma studio` | 浏览器可视化界面 | 手动看数据 |

### 3. schema.prisma 三块

```prisma
// 1. datasource：连什么数据库
datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

// 2. generator：生成什么 client
generator client {
  provider = "prisma-client-js"
}

// 3. model：表结构
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  articles  Article[]
  createdAt DateTime @default(now())
}

model Article {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  viewCount Int      @default(0)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

#### 3.1 关系表达

- `User.articles Article[]`：User 一侧声明"我有多条 Article"
- `Article.author User`：Article 一侧声明"我属于一个 User"
- `@relation(fields: [authorId], references: [id])`：外键列是 `authorId`，指向 `User.id`

> 与 TypeORM 不同：Prisma 的关系是**双向显式声明**，外键列必须单独定义为字段（`authorId Int`）。

### 4. PrismaService 封装

```typescript
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  async onModuleInit() {
    await this.$connect(); // 启动时连接数据库
  }

  async onModuleDestroy() {
    await this.$disconnect(); // 优雅关闭
  }
}
```

> 继承 `PrismaClient` 后，`this.article` / `this.user` 等代理直接可用，无需手动实例化。

### 5. PrismaModule 全局模块

```typescript
import { Global, Module } from '@nestjs/common';
import { PrismaService } from './prisma.service';

@Global()
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class PrismaModule {}
```

`@Global()` 让 `PrismaService` 在所有模块都可注入，不用每个子模块都 `imports: [PrismaModule]`。

### 6. 关系查询：include / select / nested

#### 6.1 include：把关联记录一起查出来

```typescript
// 查文章带作者
const articles = await this.prisma.article.findMany({
  include: { author: true },
});

// 嵌套：查作者，再查作者的所有文章
const users = await this.prisma.user.findMany({
  include: { articles: true },
});
```

#### 6.2 select：精挑细选字段（替代 SELECT 列）

```typescript
const articles = await this.prisma.article.findMany({
  select: {
    id: true,
    title: true,
    author: { select: { id: true, name: true } },
  },
});
```

#### 6.3 nested where：嵌套条件

```typescript
// 查邮箱为 alice@x.com 的用户写的所有文章
const articles = await this.prisma.article.findMany({
  where: { author: { email: 'alice@x.com' } },
  include: { author: true },
});
```

> 这条查询在 TypeORM 里要 `leftJoin` + 手写 `where author.email = :email`，Prisma 用对象嵌套表达，类型完全推导。

---

## TypeORM vs Prisma 对比表

| 维度 | TypeORM | Prisma |
|------|---------|--------|
| **范式** | 装饰器 + Active Record / Data Mapper | Schema 优先 + 生成式 Client |
| **类型安全** | 强（依赖 `emitDecoratorMetadata`），但运行时反射有边界 | 极强（编译期生成，零反射） |
| **学习曲线** | 陡（装饰器多、关系配置灵活但易错） | 平缓（schema 一目了然，文档友好） |
| **迁移** | `migration:generate` / `run` / `revert`，需独立 DataSource 配置 | `prisma migrate dev` 一条命令搞定，迁移文件自动生成 |
| **关系查询** | `relations` 字段 + `leftJoin`，复杂查询要 `QueryBuilder` | `include` / `select` / 嵌套 `where`，对象式表达 |
| **类型推导** | 需要手动声明 `Repository<Article>` 类型 | `prisma.article.findMany()` 返回类型自动推导 |
| **运行时依赖** | 装饰器元数据 + `class-transformer` 风格 | 生成独立 query engine 二进制（约 10MB） |
| **生态** | 老牌，NestJS 官方默认支持 | 新秀，社区增长快， NestJS 官方文档同等地位 |
| **性能** | 中等，复杂查询依赖 QueryBuilder | 较好，query engine 用 Rust 实现 |
| **可视化** | 无内置，需第三方工具 | 内置 `prisma studio` |
| **Schema 漂移检测** | 弱，需手动对比 | 强，`migrate dev` 自动检测漂移 |
| **多数据库切换** | 同一实体可换 driver，但 SQL 方言差异仍需注意 | 同上，但 schema 中 `provider` 需手动改 |

**选型经验**：

- 新项目、追求开发体验与类型安全 → **Prisma**
- 已有 TypeORM 代码库、团队熟悉装饰器范式 → **TypeORM**
- 需要复杂的多表 JOIN、CTE、窗口函数 → TypeORM 的 `QueryBuilder` 灵活度更高，Prisma 需要回退到 `$queryRaw`

---

## 两种方案完整实战：Articles CRUD

本章在同一个 NestJS 项目里同时挂载 TypeORM 与 Prisma 两套数据访问层，路由前缀分别为 `/api/v1/typeorm/articles` 与 `/api/v1/prisma/articles`，方便对比同样的业务在两种范式下的代码差异。

### 1. 数据模型

两套方案都建模 User 1 ↔ N Article：

- `User`：id、email、name、createdAt
- `Article`：id、title、content、viewCount、authorId、createdAt、updatedAt

### 2. 路由清单

| 方法 | 路径 | 作用 |
|------|------|------|
| `POST /api/v1/typeorm/articles` | 创建文章（带 authorId） |
| `GET /api/v1/typeorm/articles` | 列表（带 author 关系） |
| `GET /api/v1/typeorm/articles/:id` | 详情 |
| `PATCH /api/v1/typeorm/articles/:id` | 更新 |
| `DELETE /api/v1/typeorm/articles/:id` | 删除 |
| `POST /api/v1/prisma/articles` | 创建文章（带 authorId） |
| `GET /api/v1/prisma/articles` | 列表（带 author 关系） |
| `GET /api/v1/prisma/articles/:id` | 详情 |
| `PATCH /api/v1/prisma/articles/:id` | 更新 |
| `DELETE /api/v1/prisma/articles/:id` | 删除 |

### 3. 运行方式

```bash
cd "Day13 - 数据库集成(TypeORM与Prisma)/Code"

# 1. 安装依赖
npm install

# 2. 生成 Prisma Client（首次或 schema 变更后必跑）
npx prisma generate

# 3. 创建 SQLite 文件库 + 表结构（首次必跑）
npx prisma migrate dev --name init

# 4. 启动应用
npm run start:dev
```

### 4. 体验路径

```bash
# TypeORM 路径
curl -X POST http://localhost:3000/api/v1/typeorm/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"TypeORM 入门","content":"装饰器风格","authorId":1}'

curl http://localhost:3000/api/v1/typeorm/articles

# Prisma 路径
curl -X POST http://localhost:3000/api/v1/prisma/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"Prisma 入门","content":"Schema 优先","authorId":1}'

curl http://localhost:3000/api/v1/prisma/articles
```

> TypeORM 使用 `:memory:` SQLite，每次重启数据清空；Prisma 使用 `./prisma/dev.db` 文件库，数据持久。两者故意采用不同存储方式以演示两种场景。

---

## 关键知识点总结

### TypeORM 装饰器速查

| 装饰器 | 作用 |
|--------|------|
| `@Entity(name)` | 标记类为表 |
| `@PrimaryGeneratedColumn()` | 自增主键 |
| `@PrimaryGeneratedColumn('uuid')` | UUID 主键 |
| `@Column(options)` | 普通列 |
| `@CreateDateColumn()` | 创建时间自动填充 |
| `@UpdateDateColumn()` | 更新时间自动刷新 |
| `@DeleteDateColumn()` | 软删除时间 |
| `@VersionColumn()` | 乐观锁版本 |
| `@OneToOne(() => T, ...)` | 一对一 |
| `@OneToMany(() => T, ...)` | 一对多（反向） |
| `@ManyToOne(() => T, ...)` | 多对一 |
| `@ManyToMany(() => T, ...)` | 多对多 |
| `@JoinColumn({ name })` | 指定外键列 |
| `@JoinTable()` | 多对多中间表 |

### TypeORM 模块方法速查

| 方法 | 作用 | 调用位置 |
|------|------|---------|
| `forRoot(options)` | 同步建立全局连接 | AppModule |
| `forRootAsync({ useFactory })` | 异步建立全局连接（推荐） | AppModule |
| `forFeature([Entity])` | 注册实体 + 暴露 Repository | 子模块 |

### TypeORM 迁移命令速查

```bash
npx typeorm-ts-node-commonjs migration:generate src/migrations/Init
npx typeorm-ts-node-commonjs migration:run
npx typeorm-ts-node-commonjs migration:revert
```

### Prisma 命令速查

| 命令 | 作用 |
|------|------|
| `npx prisma init` | 初始化 schema.prisma + .env |
| `npx prisma generate` | 重新生成 Prisma Client |
| `npx prisma migrate dev --name xxx` | 生成 + 应用迁移（开发） |
| `npx prisma migrate deploy` | 仅应用迁移（生产） |
| `npx prisma migrate status` | 查看迁移状态 |
| `npx prisma migrate reset` | 重置数据库（删除重建） |
| `npx prisma db push` | 直接同步 schema（不生成迁移） |
| `npx prisma studio` | 可视化界面 |
| `npx prisma format` | 格式化 schema.prisma |

### Prisma 关系查询速查

| 操作 | 语法 |
|------|------|
| 加载关联 | `include: { author: true }` |
| 选择字段 | `select: { id: true, title: true }` |
| 嵌套加载 | `include: { author: { select: { name: true } } }` |
| 嵌套条件 | `where: { author: { email: 'x@x.com' } }` |
| 过滤关联 | `include: { articles: { where: { viewCount: { gt: 10 } } } }` |
| 排序关联 | `include: { articles: { orderBy: { createdAt: 'desc' } } }` |

### NestJS 集成三连问

1. **为什么 Prisma 不需要 `forRoot`？** Prisma Client 自带连接池，`PrismaService` 继承后 `$connect` 即用，不需要 NestJS 框架级封装。
2. **为什么 `PrismaModule` 要 `@Global()`？** 全应用共享单例，避免每个子模块重复 import；TypeORM 的 `forRoot` 也是全局的，逻辑等价。
3. **TypeORM `synchronize: true` 为什么不能上生产？** 它每次启动对比实体差异直接 ALTER 表，可能丢数据；生产必须用迁移可控地变更结构。

---

## 实战练习

### 练习 1：给 Article 增加软删除

TypeORM 侧：

1. 在 `Article` 实体上添加 `@DeleteDateColumn() deletedAt: Date | null;`
2. 把 service 的 `remove` 方法从 `delete` 改成 `softDelete`
3. 验证：删除后再 `find`，记录不再出现；查 `findWithDeleted` 能看到 `deletedAt` 被填充

Prisma 侧：

1. 在 schema.prisma 的 Article model 上加 `deletedAt DateTime?`
2. 跑 `npx prisma migrate dev --name add-soft-delete`
3. service 的 `remove` 改成 `update({ data: { deletedAt: new Date() } })`，`findAll` 加 `where: { deletedAt: null }`

### 练习 2：实现分页与排序

在两套方案的 `findAll` 上增加 `page` / `pageSize` / `orderBy` 三个查询参数：

- TypeORM：用 `skip` / `take` / `order`
- Prisma：用 `skip` / `take` / `orderBy`

返回结构：`{ data: Article[]; total: number; page: number; pageSize: number }`。验证 `GET /api/v1/typeorm/articles?page=2&pageSize=5&orderBy=createdAt:desc`。

### 练习 3：扩展多对多关系

新增 `Tag` 实体，Article 与 Tag 为多对多：

- TypeORM：用 `@ManyToMany` + `@JoinTable()`，编写接口 `POST /articles/:id/tags` 给文章打标签
- Prisma：在 schema 里加 `Tag` model 与隐式中间表 `ArticleTag`，编写接口给文章打标签

要求列表接口能通过 `?tagId=1` 过滤出带某标签的文章，对比两种方案的查询写法复杂度。

---

## 本章代码结构

```
Day13 - 数据库集成(TypeORM与Prisma)/
├── README.md                                       # 本文档
└── Code/
    ├── package.json                                # 含 @nestjs/typeorm / typeorm / @prisma/client / sqlite3
    ├── tsconfig.json
    ├── tsconfig.build.json
    ├── nest-cli.json
    ├── .env.example                                # 环境变量样例
    ├── prisma/
    │   └── schema.prisma                           # Prisma 模型定义（Article / User）
    └── src/
        ├── main.ts                                 # 启动入口
        ├── app.module.ts                           # 根模块：TypeOrmModule.forRootAsync + PrismaModule
        ├── typeorm/                                # typeorm-demo
        │   ├── typeorm.config.ts                   # forRootAsync 配合 ConfigService
        │   ├── entities/
        │   │   ├── article.entity.ts               # Article 实体 + ManyToOne(User)
        │   │   └── user.entity.ts                  # User 实体 + OneToMany(Article)
        │   └── articles-typeorm/
        │       ├── articles-typeorm.controller.ts  # CRUD
        │       ├── articles-typeorm.service.ts     # Repository 模式
        │       └── articles-typeorm.module.ts      # forFeature([Article])
        └── prisma/                                 # prisma-demo
            ├── prisma.service.ts                   # PrismaClient 封装 + onModuleInit
            ├── prisma.module.ts                    # @Global 模块
            └── articles-prisma/
                ├── articles-prisma.controller.ts   # CRUD
                ├── articles-prisma.service.ts      # Prisma 查询
                └── articles-prisma.module.ts
```
