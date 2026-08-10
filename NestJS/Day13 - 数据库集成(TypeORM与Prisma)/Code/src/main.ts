import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { Logger } from '@nestjs/common';
import { AppModule } from './app.module';

/**
 * Day13 启动入口
 *
 * 同一应用同时挂载两套数据访问层：
 *   - TypeORM（SQLite :memory:）→ /api/v1/typeorm/articles
 *   - Prisma（SQLite 文件库）  → /api/v1/prisma/articles
 *
 * 启动前请确保：
 *   1. npm install
 *   2. npx prisma generate         # 生成 Prisma Client
 *   3. npx prisma migrate dev      # 创建 SQLite 文件库 + 表结构
 */
async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  app.setGlobalPrefix('api/v1');

  await app.listen(3000);
  logger.log('Day13 数据库集成 Demo 已启动：http://localhost:3000/api/v1');
  logger.log('TypeORM 路径（SQLite 内存库）：');
  logger.log('  POST   /api/v1/typeorm/articles              -> 创建文章');
  logger.log('  GET    /api/v1/typeorm/articles              -> 文章列表');
  logger.log('  GET    /api/v1/typeorm/articles/:id          -> 文章详情');
  logger.log('  PATCH  /api/v1/typeorm/articles/:id          -> 更新文章');
  logger.log('  DELETE /api/v1/typeorm/articles/:id          -> 删除文章');
  logger.log('Prisma 路径（SQLite 文件库）：');
  logger.log('  POST   /api/v1/prisma/articles               -> 创建文章');
  logger.log('  GET    /api/v1/prisma/articles               -> 文章列表');
  logger.log('  GET    /api/v1/prisma/articles/:id           -> 文章详情');
  logger.log('  PATCH  /api/v1/prisma/articles/:id           -> 更新文章');
  logger.log('  DELETE /api/v1/prisma/articles/:id           -> 删除文章');
  logger.log('提示：TypeORM 使用 :memory: 每次重启数据清空；Prisma 使用 ./prisma/dev.db 数据持久。');
}

bootstrap();
