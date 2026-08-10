import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Article } from '../entities/article.entity';
import { User } from '../entities/user.entity';
import { ArticlesTypeormController } from './articles-typeorm.controller';
import { ArticlesTypeormService } from './articles-typeorm.service';

/**
 * TypeORM 版 Articles 模块
 *
 * forFeature([Article, User])：
 *   - 把 Article 与 User 两个实体注册到当前模块的 DI 容器
 *   - 同时暴露 Repository<Article> 与 Repository<User> 供 Service 注入
 *
 * 仅本模块需要用 Article / User 的 Repository，故不导出。
 */
@Module({
  imports: [TypeOrmModule.forFeature([Article, User])],
  controllers: [ArticlesTypeormController],
  providers: [ArticlesTypeormService],
})
export class ArticlesTypeormModule {}
