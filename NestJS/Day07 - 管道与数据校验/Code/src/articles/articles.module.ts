import { Module } from '@nestjs/common';
import { ArticlesController } from './articles.controller';

/**
 * 文章模块
 *
 * Day07 聚焦管道与校验，暂不引入 Service 层（Day03/Day04 已覆盖）。
 * providers 为空数组，控制器依赖的全局 Pipe（ValidationPipe / TrimPipe）
 * 在 main.ts 与 app.module.ts 中统一注册。
 */
@Module({
  controllers: [ArticlesController],
  providers: [],
})
export class ArticlesModule {}
