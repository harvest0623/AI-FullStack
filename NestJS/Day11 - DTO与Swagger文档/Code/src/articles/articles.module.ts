import { Module } from '@nestjs/common';
import { ArticlesController } from './articles.controller';
import { ArticlesService } from './articles.service';

/**
 * 文章模块
 *
 * 把 ArticlesController 和 ArticlesService 注册在一起，
 * 由根模块 AppModule 导入后即可生效。
 */
@Module({
  controllers: [ArticlesController],
  providers: [ArticlesService],
})
export class ArticlesModule {}
