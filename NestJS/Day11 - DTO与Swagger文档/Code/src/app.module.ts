import { Module } from '@nestjs/common';

import { ArticlesModule } from './articles/articles.module';
import { UsersModule } from './users/users.module';

/**
 * Day11 根模块
 *
 * 与 Day10 不同，本章不需要注册全局过滤器/拦截器/管道（管道在 main.ts 注册）。
 * 只需把 ArticlesModule 和 UsersModule 导入即可。
 *
 * Swagger 不需要在这里做任何配置——SwaggerModule.setup 是在 main.ts
 * 直接基于 app 实例挂载的，不依赖 DI 系统。
 */
@Module({
  imports: [ArticlesModule, UsersModule],
})
export class AppModule {}
