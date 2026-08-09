import { Module } from '@nestjs/common';
import { ArticlesController } from './articles.controller';
import { ArticlesService } from './articles.service';

/**
 * 文章模块
 *
 * 功能模块边界：
 *   - ArticlesController 负责路由与参数解析
 *   - ArticlesService 负责业务逻辑与异常抛出
 *   - 过滤器不放在功能模块里，而是统一在 AppModule 用 APP_FILTER 注册
 *     这样过滤器对所有模块生效，避免每个模块重复注册
 */
@Module({
  controllers: [ArticlesController],
  providers: [ArticlesService],
})
export class ArticlesModule {}
