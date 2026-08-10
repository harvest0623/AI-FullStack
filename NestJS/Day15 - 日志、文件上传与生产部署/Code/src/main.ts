import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { Logger, ValidationPipe } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import helmet from 'helmet';
import compression from 'compression';
import { AppModule } from './app.module';
import { MyLoggerService } from './logger/my-logger.service';

/**
 * Day15 启动入口
 *
 * 本入口演示一个"生产级"应用的初始化清单：
 *   1. 自定义 Logger（集成 winston）替换默认 Logger
 *   2. helmet：安全 HTTP 头（防 XSS、点击劫持等）
 *   3. cors：跨域白名单
 *   4. compression：gzip 压缩响应
 *   5. ValidationPipe：全局参数校验
 *   6. 全局路由前缀
 *   7. enableShutdownHooks：监听 SIGTERM/SIGINT，触发 onModuleDestroy 等钩子
 *
 * 优雅退出流程：
 *   docker stop / kubectl delete pod
 *     -> 容器向 node 进程发送 SIGTERM
 *     -> enableShutdownHooks 捕获信号
 *     -> 依次执行各模块的 OnModuleDestroy / beforeApplicationShutdown / onApplicationShutdown
 *     -> 进程退出
 */
async function bootstrap() {
  // 使用自定义 Logger 作为应用级 Logger
  const app = await NestFactory.create(AppModule, {
    bufferLogs: true,
    // 关闭默认 logger，统一交给 winston
    autoFlushLogs: true,
  });

  // 1) 替换默认 Logger 为 winston-backed 自定义 Logger
  const customLogger = app.get(MyLoggerService);
  app.useLogger(customLogger);

  const config = app.get(ConfigService);
  const port = config.get<number>('PORT', 3000);
  const prefix = config.get<string>('API_PREFIX', 'api/v1');
  const corsOrigins = (config.get<string>('CORS_ORIGINS', '') || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  // 2) helmet：补一组安全响应头
  //    - X-Content-Type-Options: nosniff
  //    - X-Frame-Options: SAMEORIGIN
  //    - Strict-Transport-Security: 启用 HSTS
  //    - Content-Security-Policy: 默认限制资源加载来源
  app.use(helmet());

  // 3) cors：白名单模式，仅允许配置的源
  app.enableCors({
    origin: corsOrigins.length ? corsOrigins : true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    credentials: true,
    maxAge: 86400,
  });

  // 4) compression：对大于 1KB 的响应做 gzip/deflate 压缩
  app.use(compression({ threshold: 1024 }));

  // 5) 全局 ValidationPipe：开启 whitelist 自动剔除未声明字段
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  // 6) 全局路由前缀
  app.setGlobalPrefix(prefix);

  // 7) 优雅退出：注册 SIGTERM/SIGINT 钩子
  //    生产环境中 k8s/docker stop 会先发 SIGTERM 等待 grace period
  app.enableShutdownHooks();

  await app.listen(port);

  customLogger.log(
    `NestJS Day15 应用已启动：http://localhost:${port}/${prefix}`,
    'Bootstrap',
  );
  customLogger.log(`运行环境：${config.get<string>('NODE_ENV', 'development')}`, 'Bootstrap');
  customLogger.log('体验路径：', 'Bootstrap');
  customLogger.log('  GET    /api/v1                  -> 根路由', 'Bootstrap');
  customLogger.log('  GET    /api/v1/health           -> 健康检查', 'Bootstrap');
  customLogger.log('  POST   /api/v1/upload/single    -> 单文件上传 (form-data: file)', 'Bootstrap');
  customLogger.log('  POST   /api/v1/upload/multiple   -> 多文件上传 (form-data: files)', 'Bootstrap');
  customLogger.log('  POST   /api/v1/upload/avatar     -> 头像上传 (仅 jpg/png, <2MB)', 'Bootstrap');
  customLogger.log('  定时任务后台运行，查看 logs/ 目录', 'Bootstrap');
}

bootstrap().catch((err) => {
  // 启动失败兜底日志（此时 winston 可能尚未就绪）
  // eslint-disable-next-line no-console
  console.error('[Bootstrap] 启动失败：', err);
  process.exit(1);
});
