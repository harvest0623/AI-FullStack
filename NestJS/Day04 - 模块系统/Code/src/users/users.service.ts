import { Injectable } from '@nestjs/common';
import { LoggerService } from '../common/logger.service';
import { ArticlesService } from '../articles/articles.service';

export interface User {
  id: number;
  name: string;
}

/**
 * UsersService
 *
 * 演示跨模块注入 ArticlesService：
 * - ArticlesService 通过 ArticlesModule 的 exports 暴露出来
 * - UsersModule 的 imports 引入了 ArticlesModule
 * - 因此这里可以在构造函数中直接注入 ArticlesService
 */
@Injectable()
export class UsersService {
  private readonly users: User[] = [
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' },
  ];

  constructor(
    private readonly logger: LoggerService,
    private readonly articlesService: ArticlesService, // 跨模块注入
  ) {}

  findAll(): User[] {
    this.logger.log('UsersService.findAll 被调用');
    return this.users;
  }

  /**
   * 返回某个用户及他的所有文章
   * 通过调用 ArticlesService 演示模块间协作
   */
  findUserWithArticles(userId: number) {
    const user = this.users.find((u) => u.id === userId);
    if (!user) {
      return { user: null, articles: [] };
    }
    const articles = this.articlesService.findByAuthorId(userId);
    this.logger.log(`查询到用户 ${user.name} 的 ${articles.length} 篇文章`);
    return { user, articles };
  }
}
