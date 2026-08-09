import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { Logger } from '@nestjs/common';
import { AppModule } from './app.module';
import { AllExceptionsFilter } from './filters/all-exceptions.filter';
import { HttpExceptionFilter } from './filters/http-exception.filter';
import { BusinessExceptionFilter } from './filters/business-exception.filter';

/**
 * Day10 启动入口
 *
 * 全局过滤器有两种注册方式，二选一即可（同时使用会重复注册）：
 *
 * 1) app.useGlobalFilters(...) —— 在 main.ts 注册，简单直接
 *    缺点：过滤器实例由我们手动 new，无法注入依赖
 *
 * 2) APP_FILTER 令牌 —— 在 AppModule 的 providers 里注册（本项目采用）
 *    优点：NestJS 容器实例化过滤器，支持 DI
 *
 * 本项目已在 AppModule 中通过 APP_FILTER 注册了三个过滤器，
 * 这里保留 useGlobalFilters 的写法作为对照（注释，避免重复注册）。
 */
async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  // 方式一：useGlobalFilters（与 AppModule 中的 APP_FILTER 二选一）
  // app.useGlobalFilters(
  //   new AllExceptionsFilter(),
  //   new HttpExceptionFilter(),
  //   new BusinessExceptionFilter(),
  // );

  app.setGlobalPrefix('api/v1');

  await app.listen(3000);
  logger.log('Day10 异常过滤器 Demo 已启动：http://localhost:3000/api/v1');
  logger.log('体验路径：');
  logger.log('  GET    /api/v1/articles/99                    -> BusinessException (ARTICLE_NOT_FOUND, 404)');
  logger.log('  PATCH  /api/v1/articles/2  {"title":"x"}      -> BusinessException (ARTICLE_LOCKED, 423)');
  logger.log('  POST   /api/v1/articles/1/publish {}          -> BusinessException (VALIDATION_FAILED, 400)');
  logger.log('  GET    /api/v1/articles/demo/search?title=不存在 -> HttpException (HTTP_404, 404)');
  logger.log('  DELETE /api/v1/articles/1                     -> HttpException (HTTP_403, 403)');
  logger.log('  GET    /api/v1/articles/demo/risky            -> AllExceptionsFilter (INTERNAL_ERROR, 500)');
  logger.log('  GET    /api/v1/articles/demo/method-filter    -> 方法级过滤器演示');
}

bootstrap();
