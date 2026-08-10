# Day15 - 日志、文件上传与生产部署

学完前 14 天的核心机制（控制器、依赖注入、中间件、管道、守卫、拦截器、过滤器、DTO、配置、数据库、JWT 认证），我们已经能写出一个"功能完整"的 NestJS 应用。但"功能完整"不等于"可以上线"。生产化是 NestJS 学习的最后一公里：日志、文件上传、定时任务、健康检查、容器化缺一不可。一个能跑在生产环境的应用，要能被运维、被监控、被回滚、被横向扩容——这些能力都来自本章的内容。

本章把"开发态"到"生产态"之间的所有常用基础设施一次性补齐：用 winston 替换默认日志、用 Multer 处理文件上传、用 @nestjs/schedule 跑后台任务、用 @nestjs/terminus 暴露健康检查、用 Docker 多阶段构建产出可移植镜像、用 Nginx 做反向代理。完成后，你的 NestJS 应用就具备了一个工业级后端服务的全部"外壳"。

---

## 学习目标

完成本章后，你应能：

- 用一句话讲清"生产级应用"与"Demo 应用"的差别，列出至少 5 项必备基础设施
- 区分 NestJS 内置 `Logger` 与自定义 `LoggerService`，知道何时该重写、何时该集成 winston
- 说出 5 个日志级别（log/error/warn/debug/verbose）的语义与典型使用场景
- 实现 winston 日志按日切割、按级别分文件、JSON 格式输出，便于 ELK 采集
- 用 `@UploadedFile()` + `FileInterceptor` 实现单文件上传，`@UploadedFiles()` + `FilesInterceptor` 实现多文件上传
- 区分 `diskStorage` 与 `memoryStorage`，知道何时用哪个
- 用 `ParseFilePipe` + `MaxFileSizeValidator` + `FileTypeValidator` 做文件校验
- 用 `@Cron` / `@Interval` / `@Timeout` 三种装饰器声明定时任务
- 用 `SchedulerRegistry` 在运行时动态添加/暂停/删除任务
- 用 `@nestjs/terminus` 暴露 `/health` 端点，组合多个 HealthIndicator
- 写出多阶段 Dockerfile，把镜像体积从 1GB 压到 200MB 以内
- 用 docker-compose 编排 app + mysql + redis + nginx
- 配置 Nginx 反向代理 + 限流 + gzip + 静态文件托管
- 说明 `enableShutdownHooks` 在容器化部署中的作用，描述优雅退出流程

---

## 理论知识讲解 - 日志体系

### 1. NestJS 内置 Logger

NestJS 自带一个轻量 `Logger` 类，开箱即用，无需任何依赖：

```typescript
import { Logger } from '@nestjs/common';

class UserService {
  private readonly logger = new Logger(UserService.name);

  findAll() {
    this.logger.log('查询用户列表');   // context 自动为 'UserService'
    this.logger.error('查询失败', err.stack);
  }
}
```

**三种实例化方式**：

1. **类内 `new Logger(ClassName)`**：最常见，`context` 字段即类名，便于日志中定位来源
2. **全局 `app.get(Logger)`**：拿到应用级 Logger 实例，常用于 bootstrap 阶段
3. **`@Injectable` 自定义 Logger**：实现 `LoggerService` 接口，通过 `app.useLogger()` 替换默认 Logger

### 2. 日志级别

| 方法 | 级别 | 典型场景 |
|------|------|---------|
| `log()` | info | 正常业务流程：用户登录、订单创建 |
| `error()` | error | 异常捕获、第三方调用失败 |
| `warn()` | warn | 可疑但可恢复：重试、降级、配额接近上限 |
| `debug()` | debug | 开发期排查细节：变量值、SQL 语句 |
| `verbose()` | trace | 极细粒度追踪：每一步函数进入/退出 |

通过 `app.useLogger` 设置 Logger 时，可控制全局最小输出级别（生产环境一般设为 `info` 或 `warn`，避免日志洪流）。

### 3. 自定义 Logger

#### 3.1 重写 ConsoleLogger

NestJS 10 提供 `ConsoleLogger` 作为可继承基类，方便在保留默认行为基础上扩展：

```typescript
import { ConsoleLogger, Injectable } from '@nestjs/common';

@Injectable()
class MyLogger extends ConsoleLogger {
  log(message: any, context?: string) {
    // 添加自定义前缀 / 上报监控平台
    super.log(`[MY-${context}] ${message}`);
  }
}
```

#### 3.2 集成 winston（推荐生产方案）

`winston` 是 Node.js 生态最成熟的日志库，支持多 transport（目的地）、按级别分文件、按日切割、JSON 格式。配合 `nest-winston` 或自己实现 `LoggerService` 接口即可接入 NestJS：

```typescript
@Injectable()
class MyLoggerService implements LoggerService {
  private readonly winston: winston.Logger;

  constructor(context?: string) {
    this.winston = winston.createLogger({
      level: 'debug',
      transports: [
        new winston.transports.Console({ format: ... }),
        new DailyRotateFile({ filename: 'app-%DATE%.log', ... }),
      ],
    });
  }

  log(message: any, context?: string) {
    this.winston.info(message, { context });
  }
  // error / warn / debug / verbose 同理
}
```

> 为什么不用 console.log？
> - 没有级别、没有时间戳、没有 context
> - 无法按文件落盘
> - 异步写入、缓冲、切割都缺失
> - JSON 结构化输出对 ELK / Loki / CloudWatch 不友好

### 4. 按模块输出：context 上下文字段

`Logger` 类第一个参数（或 `log(message, context)` 第二个参数）即"上下文"，本质是日志元数据中的一个字符串字段。在多模块应用中，给每个 Service 注入带 context 的 Logger，可在海量日志中快速过滤"某个模块的日志"：

```typescript
// 输出形如：
// 2026-07-26 10:23:11 [INFO] [UserService] 用户 admin 登录成功
// 2026-07-26 10:23:12 [INFO] [OrderService] 订单 #1001 创建
```

### 5. 结构化日志：JSON 格式

生产环境强烈建议输出 JSON 格式，便于 ELK（Elasticsearch + Logstash + Kibana）或 Loki 采集与检索：

```json
{
  "timestamp": "2026-07-26 10:23:11.234",
  "level": "info",
  "message": "用户 admin 登录成功",
  "context": "UserService",
  "service": "nest-day15",
  "pid": 12345,
  "userId": 1001,
  "ip": "192.168.1.10"
}
```

通过 `winston.format.combine(winston.format.timestamp(), winston.format.json())` 即可生成上述结构。

---

## 理论知识讲解 - 文件上传

### 1. @nestjs/platform-express + Multer

NestJS 默认基于 Express，集成 Multer 这个 Express 文件上传中间件。`@nestjs/platform-express` 已经内置 Multer 类型，无需额外安装类型：

```bash
npm i multer
npm i -D @types/multer
```

### 2. 单文件 vs 多文件

| 装饰器 | 拦截器 | 形参类型 | 用途 |
|--------|--------|---------|------|
| `@UploadedFile()` | `FileInterceptor(field, opts)` | `Express.Multer.File` | 单文件上传 |
| `@UploadedFiles()` | `FilesInterceptor(field, maxCount, opts)` | `Express.Multer.File[]` | 多文件上传（同字段名） |
| `@UploadedFiles()` | `FileFieldsInterceptor([{ name, maxCount }])` | `Record<string, File[]>` | 多字段多文件 |
| `@UploadedFile()` | `AnyFilesInterceptor(opts)` | `File[]` | 任意字段多文件 |

```typescript
@Post('single')
@UseInterceptors(FileInterceptor('file', { storage: diskStorage({...}) }))
uploadSingle(@UploadedFile() file: Express.Multer.File) {
  // file.originalname / file.filename / file.size / file.mimetype / file.path
}
```

### 3. 磁盘存储 diskStorage vs 内存存储 memoryStorage

| 存储方式 | 行为 | 适用场景 | 注意点 |
|---------|------|---------|-------|
| `diskStorage` | 直接写入磁盘 `destination/filename` | 大文件、永久保存、下载场景 | 占磁盘空间，需考虑清理策略 |
| `memoryStorage` | 文件留在内存 Buffer | 小文件需后续处理（压缩、转存 OSS） | 占内存，大文件易 OOM，需配合 `limits.fileSize` |

`diskStorage` 自定义文件名示例：

```typescript
storage: diskStorage({
  destination: './uploads',
  filename: (_req, file, cb) => {
    const ext = extname(file.originalname);
    cb(null, `${Date.now()}-${randomUUID()}${ext}`);
  },
})
```

### 4. 文件校验

NestJS 10 提供独立的 `ParseFilePipe`，可挂载多个内置 Validator：

```typescript
@UploadedFile(
  new ParseFilePipe({
    fileIsRequired: true,
    validators: [
      new MaxFileSizeValidator({ maxSize: 2 * 1024 * 1024 }),       // 2MB
      new FileTypeValidator({ fileType: /(jpg|jpeg|png)$/i }),      // 仅图片
      // 自定义：new CustomValidator implements FileValidator
    ],
  }),
)
file: Express.Multer.File
```

也可在拦截器 `limits` 字段做粗粒度限制（在 Multer 层就拒绝），避免大文件占用带宽：

```typescript
FileInterceptor('file', {
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB 上限
})
```

> 实战建议：在 Nginx 层 `client_max_body_size 20m` 做第一道防线，Multer `limits` 做第二道，`ParseFilePipe` 做业务级校验（类型/分辨率等）。

---

## 理论知识讲解 - 定时任务

### 1. @nestjs/schedule 入门

`@nestjs/schedule` 封装了 `node-cron` 与 `setInterval/setTimeout`，提供装饰器式声明：

```bash
npm i @nestjs/schedule
```

```typescript
// AppModule
import { ScheduleModule } from '@nestjs/schedule';

@Module({
  imports: [ScheduleModule.forRoot()], // 全局仅一次 forRoot
})
export class AppModule {}
```

### 2. 三种声明式调度

| 装饰器 | 用法 | 触发时机 |
|--------|------|---------|
| `@Cron('* * * * *')` | 标准 5 段 cron 表达式 | 每分钟第 0 秒 |
| `@Interval(5000)` | 毫秒数 | 每 5 秒一次 |
| `@Timeout(5000)` | 毫秒数 | 应用启动 5 秒后执行一次 |

**cron 表达式 5 段**：

```
┌──── minute (0-59)
│ ┌── hour (0-23)
│ │ ┌ day of month (1-31)
│ │ │ ┌ month (1-12)
│ │ │ │ ┌ day of week (0-7，0/7 都是周日)
│ │ │ │ │
* * * * *
```

`CronExpression` 枚举提供常用快捷宏：`EVERY_MINUTE` / `EVERY_HOUR` / `EVERY_DAY_AT_MIDNIGHT` / `EVERY_WEEKEND` 等。

### 3. 动态调度：SchedulerRegistry

需要在运行时增删任务时（如"用户开启某商品的定时上架"），注入 `SchedulerRegistry`：

```typescript
constructor(private readonly scheduler: SchedulerRegistry) {}

addJob(name: string, cron: string) {
  const job = new CronJob(cron, () => { /* ... */ });
  this.scheduler.addCronJob(name, job);
  job.start();
}

removeJob(name: string) {
  this.scheduler.deleteCronJob(name);
}
```

支持四类任务管理：`getCronJobs()` / `addInterval` / `addTimeout` / `addCronJob`。

> 分布式部署注意：多实例会重复执行同一 cron，需用分布式锁（Redis SETNX 或 BullMQ）保证幂等。

---

## 理论知识讲解 - 健康检查

### 1. @nestjs/terminus 入门

`@nestjs/terminus` 提供声明式健康检查能力，能组合多个 Indicator 并行探活，统一返回结构化结果：

```bash
npm i @nestjs/terminus
```

### 2. HealthController + @HealthCheck

```typescript
@Controller('health')
export class HealthController {
  constructor(
    private readonly health: HealthCheckService,
    private readonly db: TypeOrmHealthIndicator,
    private readonly memory: MemoryHealthIndicator,
  ) {}

  @Get()
  @HealthCheck()
  check() {
    return this.health.check([
      () => this.db.pingCheck('database'),
      () => this.memory.checkHeap('memory_heap', 300 * 1024 * 1024),
    ]);
  }
}
```

`@HealthCheck()` 装饰器把方法返回的 Promise 包装成统一结构：

```json
{
  "status": "ok",
  "info":  { "database": { "status": "up" }, "memory_heap": { "status": "up" } },
  "error": {},
  "details": { "database": { "status": "up" }, "memory_heap": { "status": "up" } }
}
```

任一 Indicator 失败，整体 `status` 变 `error`，HTTP 状态码返回 **503**。

### 3. 常用 HealthIndicator

| Indicator | 检查对象 | 用法 |
|-----------|---------|------|
| `HttpHealthIndicator` | 外部 HTTP 服务 | `pingCheck('api', 'https://...')` |
| `DNSHealthIndicator` | DNS 解析 | `pingCheck('dns', 'example.com')` |
| `TypeOrmHealthIndicator` | TypeORM 数据库 | `pingCheck('database')` |
| `PrismaHealthIndicator` | Prisma | `pingCheck('prisma')` |
| `MongooseHealthIndicator` | MongoDB | `pingCheck('mongo')` |
| `RedisHealthIndicator` | Redis | `pingCheck('redis')` |
| `MemoryHealthIndicator` | 进程内存 | `checkHeap('heap', 300MB)` / `checkRss('rss', 500MB)` |
| `DiskHealthIndicator` | 磁盘可用空间 | `checkStorage('disk', { path, threshold })` |
| `MicroserviceHealthIndicator` | RPC 服务 | `pingCheck('rpc', { transport, options })` |

### 4. /health 端点与 k8s 探针

生产环境通常拆成三套端点：

| 路径 | 用途 | 失败后果 |
|------|------|---------|
| `/health/live` | livenessProbe | 进程死掉 → 重启 Pod |
| `/health/ready` | readinessProbe | 依赖不可用 → 从负载均衡剔除 |
| `/health` | 完整检查 / startupProbe | 启动期探活 |

> livenessProbe 只检查"进程存活"，**不要**包含数据库/Redis 等依赖检查，否则依赖抖动会导致 Pod 反复重启。

---

## 理论知识讲解 - 生产部署

### 1. 安全加固

| 中间件 | 作用 | 安装 |
|--------|------|------|
| `helmet` | 设置安全 HTTP 头（HSTS / CSP / X-Frame-Options） | `npm i helmet` |
| `cors` | 跨域白名单（NestJS 内置 `app.enableCors()`） | 内置 |
| `@nestjs/throttler` | IP 级限流，超限返回 429 | `npm i @nestjs/throttler` |
| `compression` | gzip/deflate 压缩响应 | `npm i compression` |
| `ValidationPipe` | 全局参数校验，防 SQL/NoSQL 注入 | 内置 |

```typescript
// main.ts
app.use(helmet());
app.enableCors({ origin: ['https://app.example.com'], credentials: true });
app.use(compression({ threshold: 1024 }));
app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }));
```

### 2. Dockerfile 多阶段构建

多阶段构建把"构建环境"与"运行环境"分离，最终镜像不含 devDependencies、源码、构建工具，体积可压到 200MB 内：

```dockerfile
# 阶段 1：deps    安装全部依赖
FROM node:18-alpine AS deps
COPY package*.json ./
RUN npm ci

# 阶段 2：builder 编译 TS + 安装生产依赖
FROM node:18-alpine AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build && npm ci --only=production

# 阶段 3：runner  仅拷贝 dist + 生产 node_modules
FROM node:18-alpine AS runner
RUN apk add --no-cache dumb-init && adduser -S nestjs
COPY --from=builder --chown=nestjs /app/dist ./dist
COPY --from=builder --chown=nestjs /app/node_modules ./node_modules
USER nestjs
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main.js"]
```

**关键技巧**：
- `node:18-alpine` 比 `node:18` 小 8 倍
- `npm ci` 比 `npm install` 快且严格按 lock 文件
- `dumb-init` 作为 PID 1，正确转发 SIGTERM
- 非 root 用户运行（`USER nestjs`）
- `HEALTHCHECK` 指令让 Docker 自动探活

### 3. docker-compose 编排

```yaml
version: "3.9"
services:
  app:
    build: .
    ports: ["3000:3000"]
    env_file: [.env]
    depends_on:
      mysql: { condition: service_healthy }
    volumes:
      - app-uploads:/app/uploads
      - app-logs:/app/logs
  mysql:
    image: mysql:8.0
    environment: { MYSQL_ROOT_PASSWORD: 123456, MYSQL_DATABASE: nest_demo }
    volumes: [mysql-data:/var/lib/mysql]
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
  redis:
    image: redis:7-alpine
    volumes: [redis-data:/data]
  nginx:
    image: nginx:1.27-alpine
    ports: ["80:80"]
    volumes: ["./nginx.conf:/etc/nginx/conf.d/default.conf:ro"]
```

### 4. Nginx 反向代理配置

Nginx 在生产部署中承担四项职责：

1. **HTTPS 终止**：在 Nginx 层处理 TLS 证书，后端走 HTTP
2. **负载均衡**：`upstream` + `least_conn` / `round_robin` 分发到多个 app 实例
3. **限流**：`limit_req_zone` 防 CC 攻击
4. **静态文件**：托管前端构建产物（`@nestjs/serve-static` 也能做，但 Nginx 更高效）

```nginx
upstream nest_backend {
    least_conn;
    server app:3000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 80;
    client_max_body_size 20m;
    gzip on;

    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://nest_backend;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 5. 环境变量与 12-Factor

[12-Factor App](https://12factor.net/) 第三条 **Config** 要求：**配置存在环境变量中，代码不变**。NestJS 通过 `@nestjs/config` 落地：

```typescript
ConfigModule.forRoot({ isGlobal: true, envFilePath: ['.env'] });
const port = config.get<number>('PORT');
```

**配置层级**（从安全到易用）：
- k8s Secret / Vault（最敏感：DB 密码、JWT 密钥）
- `.env.production`（运维管理，不入 Git）
- `.env.example`（开发样例，入 Git）
- 代码内默认值（最后兜底）

### 6. 优雅退出：enableShutdownHooks

```typescript
app.enableShutdownHooks();
```

启用后，NestJS 会监听 `SIGTERM` / `SIGINT`，依次触发：
1. `onModuleDestroy()` —— 各模块清理（关闭数据库连接、释放句柄）
2. `beforeApplicationShutdown()` —— 应用级前置清理
3. `onApplicationShutdown()` —— 应用级后置清理（flush 日志、上报退出指标）
4. 进程退出

**容器化部署的关键链路**：

```
docker stop / kubectl delete pod
    ↓ (默认 grace period 30s)
容器向 PID 1 发送 SIGTERM
    ↓
dumb-init 转发给 node
    ↓
enableShutdownHooks 捕获
    ↓
onModuleDestroy / onApplicationShutdown 执行
    ↓
连接池关闭、日志 flush、定时任务停止
    ↓
进程退出
```

> 没有 `enableShutdownHooks` + `dumb-init`，Docker stop 时 Node 进程会被 SIGKILL 直接杀死，导致：日志丢失、连接泄漏、定时任务中断。

---

## NestJS 测试速览

### 1. 单元测试：@nestjs/testing

`@nestjs/testing` 提供 `Test.createTestingModule()` 构建测试用模块，可替换依赖为 mock：

```typescript
import { Test } from '@nestjs/testing';

describe('UserService', () => {
  let service: UserService;
  let repo: MockType<Repository<User>>;

  beforeEach(async () => {
    const moduleRef = await Test.createTestingModule({
      providers: [
        UserService,
        { provide: getRepositoryToken(User), useValue: mockRepo },
      ],
    }).compile();

    service = moduleRef.get(UserService);
    repo = moduleRef.get(getRepositoryToken(User));
  });

  it('findAll 应返回用户列表', async () => {
    repo.find.mockResolvedValue([{ id: 1, name: 'tom' }]);
    expect(await service.findAll()).toHaveLength(1);
  });
});
```

### 2. E2E 测试：supertest

E2E 测试启动整个 HTTP 应用，用 `supertest` 发起真实请求，验证完整链路（含中间件/守卫/拦截器）：

```typescript
import { Test } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';

describe('AppController (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();
    app = moduleRef.createNestApplication();
    await app.init();
  });

  it('/ (GET)', async () => {
    await request(app.getHttpServer())
      .get('/api/v1')
      .expect(200)
      .expect((res) => {
        expect(res.body.name).toBe('NestJS Day15');
      });
  });

  afterAll(() => app.close());
});
```

### 3. 测试金字塔

| 层级 | 数量 | 速度 | 隔离性 | 验证范围 |
|------|------|------|-------|---------|
| 单元测试 | 多 | 快 | 强 | 单个 Service / 函数 |
| 集成测试 | 中 | 中 | 中 | 模块内多个组件协作 |
| E2E 测试 | 少 | 慢 | 弱 | 完整业务流程 |

```bash
npm run test           # 单元
npm run test:cov       # 覆盖率
npm run test:e2e       # E2E
```

---

## 关键知识点总结

### 生产部署清单

```
✓ 日志：winston + 按级别分文件 + 按日切割 + JSON 格式
✓ 健康检查：/health/live /health/ready /health
✓ 安全：helmet + cors 白名单 + throttler 限流 + ValidationPipe
✓ 压缩：compression
✓ 配置：@nestjs/config + .env + 12-Factor
✓ 容器化：多阶段 Dockerfile + dumb-init + 非 root 用户
✓ 编排：docker-compose（app + db + redis + nginx）
✓ 反向代理：Nginx + HTTPS + 限流 + 静态托管
✓ 优雅退出：enableShutdownHooks + SIGTERM 处理
✓ 监控：日志采集到 ELK / 指标上报 Prometheus
✓ 备份：数据库定时备份 + Redis AOF
✓ CI/CD：GitHub Actions / GitLab CI 自动构建推送镜像
✓ 镜像管理：私有仓库 + 镜像签名 + 漏洞扫描
```

### Docker 命令速查

```bash
# 镜像构建与运行
docker build -t nest-day15:latest .
docker run --rm -p 3000:3000 --env-file .env nest-day15:latest
docker images                            # 查看镜像
docker rmi nest-day15:latest             # 删除镜像

# 容器编排（compose）
docker-compose up -d                     # 后台启动全部服务
docker-compose down                      # 停止并删除容器
docker-compose down -v                   # 同时删除数据卷
docker-compose logs -f app               # 跟踪 app 日志
docker-compose ps                        # 查看服务状态
docker-compose restart app               # 重启 app

# 进入容器调试
docker exec -it nest-day15-app sh
docker exec -it nest-day15-app node -e "console.log(process.versions)"

# 清理空间
docker system prune -a --volumes         # 清理无用镜像/容器/卷（谨慎）
docker stats                             # 实时资源占用
```

### 装饰器速查

| 装饰器 | 来源 | 用途 |
|--------|------|------|
| `@Cron('* * * * *')` | @nestjs/schedule | cron 表达式定时 |
| `@Interval(ms)` | @nestjs/schedule | 间隔执行 |
| `@Timeout(ms)` | @nestjs/schedule | 延迟执行一次 |
| `@UploadedFile()` | @nestjs/common | 单文件参数 |
| `@UploadedFiles()` | @nestjs/common | 多文件参数 |
| `@UseInterceptors(FileInterceptor)` | @nestjs/common | 单文件拦截 |
| `@HealthCheck()` | @nestjs/terminus | 健康检查方法 |
| `@Throttle({ default: { limit, ttl } })` | @nestjs/throttler | 细粒度限流 |
| `@SkipThrottle()` | @nestjs/throttler | 跳过限流 |

---

## 实战练习

### 练习 1：给上传文件添加类型白名单 Filter

需求：实现一个自定义 `ExceptionFilter`，专门捕获 Multer 抛出的 `LIMIT_FILE_SIZE` / `LIMIT_UNEXPECTED_FILE` 错误，返回统一格式：

```json
{ "code": "UPLOAD_SIZE_EXCEEDED", "message": "文件大小超过 10MB", "maxSize": 10485760 }
```

提示：
- Multer 错误类是 `MulterError`，`code` 字段为 `LIMIT_FILE_SIZE` 等
- 用 `@Catch(MulterError)` 限定捕获范围
- 注册到 UploadController 上（`@UseFilters(MulterExceptionFilter)`）

### 练习 2：实现一个"过期数据清理"定时任务

需求：每天凌晨 3 点扫描 `uploads/tmp/` 目录，删除 7 天前的临时文件。

提示：
- `@Cron('0 3 * * *')` 触发
- 用 `fs.readdir` + `fs.stat` 获取文件 `mtime`
- 用 `fs.unlink` 删除
- 在 `TasksService` 里新增方法，注意异常捕获避免任务崩溃

### 练习 3：扩展健康检查端点

需求：在 `HealthController` 中新增 `/health/db` 端点，模拟数据库 ping 检查（用 `setTimeout` 包装成异步）。

要求：
- 返回 terminus 标准格式 `{ status, info, error, details }`
- 模拟随机 10% 概率失败，测试 503 响应
- 在 Nginx `location = /health/db` 上配置 `access_log off` 减少探针日志噪音

提示：
- 自定义 Indicator 类继承 `HealthIndicator`，实现 `async pingCheck(key)`
- 用 `Math.random() < 0.1` 模拟失败，`throw new HealthCheckError(...)` 触发 503

---

**完成本章后，你已具备把 NestJS 应用部署到生产环境所需的全部基础知识。结合前 14 天的核心机制，你已经是一名合格的 NestJS 后端工程师。下一步可以把这套架构应用到 AI 应用后端（LLM 服务化、RAG 检索服务、Agent 编排）的实战中。**
