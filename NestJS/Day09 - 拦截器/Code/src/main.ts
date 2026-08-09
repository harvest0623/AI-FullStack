import { NestFactory } from '@nestjs/core';
import { Logger } from '@nestjs/common';
import { AppModule } from './app.module';
import { LoggingInterceptor } from './interceptors/logging.interceptor';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const logger = new Logger('Bootstrap');

  // 全局拦截器注册方式一：通过 useGlobalInterceptors 直接注册
  // 注意：这种方式注册的拦截器无法使用依赖注入（DI），
  // 因为它绕过了 Nest 容器，直接 new 一个实例。
  // 若拦截器内部需要注入 Service，请改用 APP_INTERCEPTOR（见 app.module.ts）
  app.useGlobalInterceptors(new LoggingInterceptor());

  await app.listen(3000);
  logger.log('🚀 应用已启动：http://localhost:3000');
  logger.log('📖 示例路由：');
  logger.log('   GET  /articles          （演示缓存 + 字段过滤）');
  logger.log('   GET  /articles/:id      （演示字段过滤）');
  logger.log('   GET  /articles/slow/:ms （演示超时控制）');
}
bootstrap();
