import { Module } from '@nestjs/common';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { ArticlesModule } from '../articles/articles.module';

/**
 * 特性模块 UsersModule
 *
 * 演示跨模块注入：
 * - imports: [ArticlesModule]：因为 UsersService 需要注入 ArticlesService
 *   ArticlesModule 通过 exports 暴露了 ArticlesService，所以这里才能注入
 *
 * 若不写 imports，会报 "Nest can't resolve dependencies of UsersService (ArticlesService, ...)"
 */
@Module({
  imports: [ArticlesModule],
  controllers: [UsersController],
  providers: [UsersService],
})
export class UsersModule {}
