import { Module } from '@nestjs/common';
import { ArticlesPrismaController } from './articles-prisma.controller';
import { ArticlesPrismaService } from './articles-prisma.service';

/**
 * Prisma 版 Articles 模块
 *
 * 注意：这里不需要 imports: [PrismaModule]，
 * 因为 PrismaModule 是 @Global()，PrismaService 在所有模块都可直接注入。
 *
 * 对比 TypeORM 版的 ArticlesTypeormModule，少了一行
 *   imports: [TypeOrmModule.forFeature([Article])]
 * 这是 Prisma 集成方式的简洁之处。
 */
@Module({
  controllers: [ArticlesPrismaController],
  providers: [ArticlesPrismaService],
})
export class ArticlesPrismaModule {}
