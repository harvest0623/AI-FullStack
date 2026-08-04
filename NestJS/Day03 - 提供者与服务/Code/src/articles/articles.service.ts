// ============================================================
// ArticlesService：业务逻辑封装
// ------------------------------------------------------------
// 演示要点：
//   1. @Injectable 声明为 Provider
//   2. 构造函数注入 LoggerService（类作为 Token，无需 @Inject）
//   3. @Inject 注入字符串 Token 的 Provider（CONFIG_TOKEN / DATABASE_CONNECTION_TOKEN）
//   4. Service 之间的依赖：ArticlesService 依赖 LoggerService
// ============================================================

import { Inject, Injectable } from '@nestjs/common';
import { LoggerService } from '../common/logger.service';
import { AppConfig } from '../config/config.provider';
import {
  DatabaseConnection,
} from '../config/database.factory';
import {
  CONFIG_TOKEN,
  DATABASE_CONNECTION_TOKEN,
} from '../config/token.constants';

export interface Article {
  id: number;
  title: string;
  content: string;
}

@Injectable()
export class ArticlesService {
  // 内存存储，仅用于演示
  private articles: Article[] = [
    { id: 1, title: 'Provider 入门', content: 'Provider 是依赖注入的基本单元' },
    { id: 2, title: 'Service 模式', content: '业务逻辑下沉到 Service 中' },
  ];
  private nextId = 3;

  constructor(
    // 类作为 Token：构造函数注入即可，无需 @Inject
    private readonly logger: LoggerService,
    // 字符串 Token：必须使用 @Inject 显式指定 Token
    @Inject(CONFIG_TOKEN) private readonly config: AppConfig,
    // 工厂创建的 Provider：同样通过 Token 注入
    @Inject(DATABASE_CONNECTION_TOKEN)
    private readonly db: DatabaseConnection,
  ) {
    this.logger.log(
      `ArticlesService 初始化 | 环境=${config.environment} | DB=${db.host}:${db.port}`,
      'ArticlesService',
    );
  }

  findAll(): Article[] {
    this.logger.log('查询所有文章', 'ArticlesService');
    return this.articles;
  }

  findOne(id: number): Article | null {
    this.logger.log(`查询文章 id=${id}`, 'ArticlesService');
    return this.articles.find((a) => a.id === id) ?? null;
  }

  create(title: string, content: string): Article {
    const article: Article = { id: this.nextId++, title, content };
    this.articles.push(article);
    this.logger.log(
      `创建文章 id=${article.id} title=${title}`,
      'ArticlesService',
    );
    return article;
  }

  remove(id: number): boolean {
    const idx = this.articles.findIndex((a) => a.id === id);
    if (idx === -1) return false;
    this.articles.splice(idx, 1);
    this.logger.log(`删除文章 id=${id}`, 'ArticlesService');
    return true;
  }
}
