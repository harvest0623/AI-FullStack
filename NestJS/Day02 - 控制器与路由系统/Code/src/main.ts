import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // 全局路由前缀：所有控制器路由都会带上 /api/v1
  // 例如 ArticlesController 的 'articles' 前缀最终会变成 /api/v1/articles
  app.setGlobalPrefix('api/v1');

  // 全局管道：开启 DTO 自动校验（class-validator 在 Day07 引入）
  // 提前注册 ValidationPipe，后续接入 DTO 校验无需修改业务代码
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  );

  // 启用 CORS：允许前端跨域访问
  app.enableCors();

  await app.listen(3000);

  const logger = new Logger('Bootstrap');
  logger.log('Day02 应用已启动：http://localhost:3000/api/v1');
  logger.log('文章接口：http://localhost:3000/api/v1/articles');
  logger.log('用户接口：http://localhost:3000/api/v1/users');
}
bootstrap();
