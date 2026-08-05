import { Module } from '@nestjs/common';
import { ArticlesController } from './articles.controller';

// ============================================================
// Articles 业务模块
// ------------------------------------------------------------
// 控制器内部不直接挂中间件（NestJS 中间件没有 @Use() 装饰器）
// 所有路由级中间件在 AppModule.configure() 中通过 forRoutes 绑定
// ============================================================

@Module({
  controllers: [ArticlesController],
})
export class ArticlesModule {}
