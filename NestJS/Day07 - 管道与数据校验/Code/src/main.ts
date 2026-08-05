import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { AppModule } from './app.module';

/**
 * 应用启动入口
 *
 * 本文件演示全局 Pipe 注册的第一种方式：app.useGlobalPipes()。
 * 这里注册了 ValidationPipe，对所有控制器的 @Body() / @Query() / @Param() 做 DTO 校验与类型转换。
 *
 * 另一种注册方式 APP_PIPE（支持依赖注入）在 app.module.ts 中演示，用于注册 TrimPipe。
 * 两种方式可以共存，详见 README.md "全局 Pipe 注册的两种方式"。
 */
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // 全局路由前缀：所有控制器路由都会带上 /api/v1
  app.setGlobalPrefix('api/v1');

  // 全局管道：ValidationPipe
  // - whitelist: true            剥离 DTO 上没有装饰器的多余字段
  // - forbidNonWhitelisted: true 多余字段直接抛 400，而不是静默剥离
  // - transform: true            开启类型转换：请求体转 DTO 实例，路径/查询参数按 TS 类型自动转换
  // - transformOptions.enableImplicitConversion: true
  //   基于 TypeScript 类型元数据自动转换（string -> number / boolean / Date）
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
  );

  // 启用 CORS：允许前端跨域访问
  app.enableCors();

  await app.listen(3000);

  const logger = new Logger('Bootstrap');
  logger.log('Day07 应用已启动：http://localhost:3000/api/v1');
  logger.log('文章接口：http://localhost:3000/api/v1/articles');
  logger.log('用户接口：http://localhost:3000/api/v1/users');
}
bootstrap();
