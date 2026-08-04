import { Module } from '@nestjs/common';
import { ArticlesController } from './articles.controller';
import { ArticlesService } from './articles.service';

/**
 * 特性模块 ArticlesModule
 *
 * 按业务领域"文章"划分：
 * - controllers：注册 ArticlesController
 * - providers：内部注册 ArticlesService（私有）
 * - exports：把 ArticlesService 暴露给其他模块（UsersModule 会 import 它）
 */
@Module({
  controllers: [ArticlesController],
  providers: [ArticlesService],
  exports: [ArticlesService],
})
export class ArticlesModule {}
