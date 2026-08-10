import { Module } from '@nestjs/common';
import { ArticlesService } from './articles.service';
import { ArticlesController } from './articles.controller';

/**
 * Day12 Articles 模块
 *
 * 由于 ConfigModule 在根模块注册时设了 isGlobal: true，
 * 这里无需 import ConfigModule，ArticlesService 即可直接注入 ConfigService。
 *
 * 这也是 isGlobal 的主要价值：
 *   - 业务模块不依赖 ConfigModule，依赖关系更简洁
 *   - 任何地方读取配置都无需"穿透"模块边界
 */
@Module({
  controllers: [ArticlesController],
  providers: [ArticlesService],
  exports: [ArticlesService],
})
export class ArticlesModule {}
