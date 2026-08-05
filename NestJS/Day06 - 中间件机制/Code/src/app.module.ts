import {
  Module,
  NestModule,
  MiddlewareConsumer,
  RequestMethod,
} from '@nestjs/common';
import { ArticlesModule } from './articles/articles.module';
import { LoggerMiddleware } from './middleware/logger.middleware';
import { AuthMiddleware, adminAuthMiddleware } from './middleware/auth.middleware';
import { RequestIdMiddleware } from './middleware/request-id.middleware';
import { TimerMiddleware } from './middleware/timer.middleware';
import { LoggerService } from './common/logger.service';

// ============================================================
// 根模块
// ------------------------------------------------------------
// 演示要点：
//   1. 实现 NestModule 接口的 configure(consumer) 方法
//   2. 链式调用 apply().forRoutes()，可对多组路由应用不同中间件
//   3. exclude() 排除特定路由
//   4. 中间件执行顺序按 apply 注册顺序：RequestId -> Timer -> Logger -> Auth
// ============================================================

@Module({
  imports: [ArticlesModule],
  providers: [LoggerService],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      // 全局生效：请求 ID 注入 + 计时 + 日志
      // 顺序很重要：RequestId 必须最先执行，后续中间件才能读到 req.requestId
      .apply(RequestIdMiddleware, TimerMiddleware, LoggerMiddleware)
      .forRoutes('*')
      // 仅对 /articles 生效的鉴权（排除 GET /articles/public 公开路由）
      .apply(AuthMiddleware)
      .exclude({ path: 'articles/public', method: RequestMethod.GET })
      .forRoutes('articles')
      // 函数中间件示例：仅 DELETE /articles/:id 要求 admin 角色
      // 这是对「函数中间件 vs 类中间件」的对比演示
      // 注意：NestJS 中间件没有 @Use() 装饰器，per-route 绑定只能这样做
      .apply(adminAuthMiddleware)
      .forRoutes({
        path: 'articles/:id',
        method: RequestMethod.DELETE,
      });
  }
}
