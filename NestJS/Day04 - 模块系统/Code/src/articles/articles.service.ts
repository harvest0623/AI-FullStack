import { Injectable } from '@nestjs/common';
import { LoggerService } from '../common/logger.service';
import { ConfigService } from '../config/config.service';

export interface Article {
  id: number;
  title: string;
  authorId: number;
}

/**
 * ArticlesService
 *
 * 演示两个跨模块/全局注入场景：
 * - LoggerService 来自 @Global 全局模块 CommonModule，无需在 ArticlesModule 显式 import
 * - ConfigService 来自动态模块 ConfigModule.forRoot({ isGlobal: true })
 */
@Injectable()
export class ArticlesService {
  private readonly articles: Article[] = [
    { id: 1, title: 'NestJS 模块系统入门', authorId: 1 },
    { id: 2, title: '动态模块实战', authorId: 2 },
    { id: 3, title: 'Provider 可见性原理', authorId: 1 },
  ];

  constructor(
    private readonly logger: LoggerService,
    private readonly config: ConfigService,
  ) {}

  findAll(): Article[] {
    this.logger.log(
      `ArticlesService.findAll 被调用，应用名称=${this.config.get('appName')}`,
    );
    return this.articles;
  }

  findByAuthorId(authorId: number): Article[] {
    return this.articles.filter((a) => a.authorId === authorId);
  }
}
