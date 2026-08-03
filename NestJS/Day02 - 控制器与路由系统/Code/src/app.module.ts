import { Module } from '@nestjs/common';
import { ArticlesModule } from './articles/articles.module';
import { UsersModule } from './users/users.module';

/**
 * 根模块：注册业务模块
 *
 * Day02 阶段只关注控制器与路由，
 * Service 层会在后续 Day 中逐步引入，
 * 因此 Module 的 providers 暂时为空数组。
 */
@Module({
  imports: [ArticlesModule, UsersModule],
})
export class AppModule {}
