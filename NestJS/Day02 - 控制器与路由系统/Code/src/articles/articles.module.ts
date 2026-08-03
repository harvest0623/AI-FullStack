import { Module } from '@nestjs/common';
import { ArticlesController } from './articles.controller';

/**
 * 文章模块
 *
 * Day02 阶段还没有 Service 层，
 * providers 暂时为空数组。
 * Day04 引入 Provider 后会在这里注册 ArticlesService。
 */
@Module({
  controllers: [ArticlesController],
  providers: [],
})
export class ArticlesModule {}
