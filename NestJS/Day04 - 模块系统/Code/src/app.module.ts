import { Module } from '@nestjs/common';
import { ConfigModule } from './config/config.module';
import { CommonModule } from './common/common.module';
import { ArticlesModule } from './articles/articles.module';
import { UsersModule } from './users/users.module';

/**
 * 根模块 AppModule
 *
 * 职责：装配应用，不写业务逻辑。
 * - ConfigModule.forRoot({ isGlobal: true })：动态模块，注册一次到处可用
 * - CommonModule：@Global 全局模块，LoggerService 全应用可见
 * - ArticlesModule / UsersModule：按业务领域划分的特性模块
 */
@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    CommonModule,
    ArticlesModule,
    UsersModule,
  ],
})
export class AppModule {}
