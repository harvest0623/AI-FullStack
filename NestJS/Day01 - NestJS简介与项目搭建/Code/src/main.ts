import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { AppModule } from './app.module';

/**
 * 应用启动入口
 *
 * NestJS 应用的入口约定为一个 async 函数（通常命名 bootstrap），
 * 内部调用 NestFactory.create(AppModule) 完成以下事情：
 *   1. 实例化根模块 AppModule，递归实例化所有 imports 的子模块
 *   2. 解析模块依赖图，构建 Provider → Token 映射表
 *   3. 装配 IoC 容器，准备按需注入
 *   4. 通过 @nestjs/platform-express 创建 Express 实例并绑定路由
 *
 * 之后 app 实例上可以挂载全局配置：前缀、CORS、管道、过滤器、拦截器等。
 */
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // 全局路由前缀：所有路由自动加上 /api
  // 例如 @Controller('users') + @Get('me') 实际路径为 /api/users/me
  // 优势：前端代理统一转发 /api/*，与静态资源分流清晰
  app.setGlobalPrefix('api');

  // 启用 CORS（跨域资源共享）
  // 开发阶段直接 enableCors() 允许所有来源
  // 生产环境应改为：
  //   app.enableCors({ origin: ['https://your-frontend.com'], credentials: true });
  app.enableCors();

  // 全局 ValidationPipe（后续 Day07 详解）
  // 作用：所有 @Body()、@Query()、@Param() 参数会按 DTO 类的 class-validator 装饰器校验
  // 此处先注册，为后续 Day 的 DTO 校验做铺垫；本 Day 没有 DTO 也不影响运行
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true, // 自动剔除 DTO 上未声明的属性（防止参数污染）
      forbidNonWhitelisted: true, // 出现未声明属性直接 400 Bad Request
      transform: true, // 把普通对象转为 DTO 类实例（启用后 @Body() 拿到的是 DTO 实例而非 plain object）
    }),
  );

  // 监听端口；第二个参数可传 callback，在监听成功后执行
  await app.listen(3000);

  const logger = new Logger('Bootstrap');
  logger.log('Nest application successfully started');
  logger.log('Listening on http://localhost:3000/api');
}

bootstrap();
