import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { getTypeOrmConfig } from './typeorm/typeorm.config';
import { PrismaModule } from './prisma/prisma.module';
import { ArticlesTypeormModule } from './typeorm/articles-typeorm/articles-typeorm.module';
import { ArticlesPrismaModule } from './prisma/articles-prisma/articles-prisma.module';

/**
 * 根模块
 *
 * 同时集成两套数据访问层，便于对比：
 *
 * 1. TypeORM
 *    - TypeOrmModule.forRootAsync 配合 ConfigService 异步读取 .env
 *    - 子模块用 forFeature([Entity]) 注入 Repository
 *
 * 2. Prisma
 *    - PrismaModule（@Global）封装 PrismaClient 单例
 *    - 子模块直接注入 PrismaService 调用 prisma.article / prisma.user
 */
@Module({
  imports: [
    // 配置模块：加载 .env，全局可用
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env', '.env.example'],
    }),

    // TypeORM：异步配置，从 .env 读取数据库连接参数
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService) =>
        getTypeOrmConfig(configService),
    }),

    // Prisma：全局模块，封装 PrismaClient
    PrismaModule,

    // 业务模块
    ArticlesTypeormModule,
    ArticlesPrismaModule,
  ],
})
export class AppModule {}
