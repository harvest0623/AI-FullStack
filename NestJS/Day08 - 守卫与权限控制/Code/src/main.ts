import 'reflect-metadata';
import { NestFactory, Reflector } from '@nestjs/core';
import { Logger } from '@nestjs/common';
import { AppModule } from './app.module';
import { AuthGuard } from './guards/auth.guard';

/**
 * Day08 启动入口
 *
 * 本 Demo 的三个全局守卫通过 APP_GUARD 注册在 AppModule 中：
 *   AuthGuard → RolesGuard → PermissionGuard
 * 这里再演示 main.ts 中的「另一种注册方式」并解释两者差异，
 * 帮助理解 useGlobalGuards 与 APP_GUARD 的取舍。
 */
async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  // ---------- 方式一：useGlobalGuards（手动注册，不支持 DI） ----------
  //
  // app.useGlobalGuards(new AuthGuard(new Reflector()));
  //
  // 缺点：
  //   1. 守卫实例由我们手动 new，无法注入其他 Provider
  //   2. 不参与模块生命周期，无法使用 REQUEST 作用域 Provider
  //   3. 与 AppModule 的 APP_GUARD 重复时会执行两遍，需二选一
  //
  // 适用场景：极简脚本、不需要 DI 的纯函数式守卫
  //
  // const reflector = app.get(Reflector);
  // app.useGlobalGuards(new AuthGuard(reflector));

  // ---------- 方式二：APP_GUARD（推荐，已在 AppModule 中采用） ----------
  //
  // 在 AppModule 的 providers 写：
  //   { provide: APP_GUARD, useClass: AuthGuard }
  // Nest 会通过 DI 容器创建实例，自动注入 Reflector，
  // 支持作用域、依赖链、模块边界。生产项目一律用这种。
  //
  // 三个守卫已在 AppModule 注册，这里无需重复注册。

  await app.listen(3000);
  logger.log('Day08 守卫与权限控制 Demo 已启动：http://localhost:3000');
  logger.log('守卫执行顺序：AuthGuard → RolesGuard → PermissionGuard → 控制器');
  logger.log('可用路由：');
  logger.log('  GET    /articles/health              公开路由（@Public，无需 token）');
  logger.log('  GET    /articles/public-list          公开路由（@Public）');
  logger.log('  GET    /articles                      需登录（任意用户）');
  logger.log('  GET    /articles/:id                  需登录（任意用户）');
  logger.log('  GET    /articles/admin/dashboard     仅 admin 角色');
  logger.log('  GET    /articles/editor/workspace     admin 或 editor 角色');
  logger.log('  POST   /articles                      需 article:create 权限');
  logger.log('  DELETE /articles/:id                  需 article:delete 权限（仅 admin）');
  logger.log('');
  logger.log('可用 token（Authorization: Bearer <token>）：');
  logger.log('  token-admin     → admin 角色，全权限');
  logger.log('  token-editor    → editor 角色，read/create/update');
  logger.log('  token-visitor   → visitor 角色，仅 read');
  logger.log('');
  logger.log('测试示例：');
  logger.log('  curl http://localhost:3000/articles/health');
  logger.log('  curl -H "Authorization: Bearer token-admin" http://localhost:3000/articles');
  logger.log('  curl -H "Authorization: Bearer token-visitor" http://localhost:3000/articles/admin/dashboard  # 403');
}

bootstrap();
