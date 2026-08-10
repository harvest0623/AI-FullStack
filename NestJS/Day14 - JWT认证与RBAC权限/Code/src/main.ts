import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { AppModule } from './app.module';

/**
 * Day14 启动入口
 *
 * 本 Demo 把认证授权完整链路跑通：
 *   注册 → 登录（LocalStrategy） → 签发 JWT →
 *   受保护资源（JwtStrategy 解析 token） → 刷新 token → 登出（黑名单）
 *
 * 启动后通过 main.ts 中的日志即可看到完整的接口清单与测试 curl 示例。
 */
async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  // 全局 ValidationPipe：自动对 DTO 做 class-validator 校验
  // whitelist: true  → 自动剥离 DTO 未声明的字段
  // forbidNonWhitelisted: true → 出现未声明字段直接抛 400
  // transform: true → 把 query / param 字符串按 DTO 类型自动转换
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  );

  await app.listen(process.env.PORT ?? 3000);

  logger.log('Day14 JWT 认证与 RBAC 权限 Demo 已启动');
  logger.log(`HTTP 服务监听：http://localhost:${process.env.PORT ?? 3000}`);
  logger.log('');
  logger.log('可用路由：');
  logger.log('  POST   /auth/register    公开：注册新用户（密码使用 bcrypt 哈希）');
  logger.log('  POST   /auth/login       公开：用户名密码登录，签发 access + refresh token');
  logger.log('  GET    /auth/profile     需 JWT：返回当前登录用户信息');
  logger.log('  POST   /auth/refresh     需 JWT（refresh）：用 refresh token 换取新 access token');
  logger.log('  POST   /auth/logout      需 JWT：将当前 token 加入黑名单');
  logger.log('');
  logger.log('测试示例：');
  logger.log('  # 1. 注册（默认 admin 角色由 DTO 指定）');
  logger.log('  curl -X POST http://localhost:3000/auth/register \\');
  logger.log('       -H "Content-Type: application/json" \\');
  logger.log('       -d \'{"username":"alice","password":"Pass1234","roles":["admin"]}\'');
  logger.log('');
  logger.log('  # 2. 登录');
  logger.log('  curl -X POST http://localhost:3000/auth/login \\');
  logger.log('       -H "Content-Type: application/json" \\');
  logger.log('       -d \'{"username":"alice","password":"Pass1234"}\'');
  logger.log('');
  logger.log('  # 3. 访问受保护资源（替换 <ACCESS_TOKEN>）');
  logger.log('  curl -H "Authorization: Bearer <ACCESS_TOKEN>" http://localhost:3000/auth/profile');
}

bootstrap();
