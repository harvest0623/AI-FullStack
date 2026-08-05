import { NestFactory } from '@nestjs/core';
import { json, urlencoded } from 'express';
import { AppModule } from './app.module';

// ============================================================
// 应用启动入口
// ------------------------------------------------------------
// 演示要点：
//   1. app.use() 注册应用级中间件（函数形态，无法访问 DI）
//   2. app.enableCors() 启用 CORS（底层自动注册中间件）
//   3. 类中间件 + DI 通过 AppModule.configure() 注册，见 app.module.ts
// ============================================================

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // 统一加 /api 前缀，与 Day02-Day05 保持一致
  app.setGlobalPrefix('api');

  // 应用级中间件：Body 解析
  // NestJS 默认开启，这里显式写出是为了演示 app.use() 的用法
  app.use(json());
  app.use(urlencoded({ extended: true }));

  // 应用级中间件：CORS（封装形式，等价于 app.use(cors())）
  app.enableCors({
    origin: true,
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE',
    credentials: true,
  });

  await app.listen(3000);
  console.log('Application is running on: http://localhost:3000/api');
}

bootstrap();
