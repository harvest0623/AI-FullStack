import { Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import {
  ArticleNotFoundException,
  ArticleLockedException,
  UserNotFoundException,
  ValidationException,
} from '../exceptions/domain.exceptions';

/**
 * 文章服务
 *
 * 演示两种抛异常的方式：
 *   1. 抛自定义业务异常（推荐）—— 携带 errorCode，前端可精细分支处理
 *   2. 抛 NestJS 内置异常 —— 简单场景下快速返回标准 HTTP 状态码
 *
 * 选型建议：
 *   - 需要前端按业务码分支处理 → 业务异常
 *   - 纯粹的 HTTP 语义错误（404 资源不存在）→ 内置异常即可
 *   - 跨服务/跨领域的未知错误 → 让它自然抛出，由兜底过滤器处理
 */
@Injectable()
export class ArticlesService {
  // 内存数据，演示用
  private readonly articles = [
    { id: 1, title: 'NestJS 异常过滤器入门', authorId: 100, locked: false },
    { id: 2, title: '统一错误响应设计', authorId: 101, locked: true },
    { id: 3, title: '业务异常与 HTTP 异常的分工', authorId: 102, locked: false },
  ];

  /**
   * 演示：抛业务异常（ArticleNotFoundException）
   * 命中 BusinessExceptionFilter，返回 404 + code: ARTICLE_NOT_FOUND
   */
  findOne(id: number) {
    const article = this.articles.find((a) => a.id === id);
    if (!article) {
      throw new ArticleNotFoundException(id);
    }
    return article;
  }

  /**
   * 演示：抛业务异常（ArticleLockedException），映射到 HTTP 423 Locked
   * 先调用 findOne 复用"不存在"的校验。
   */
  update(id: number, dto: { title?: string }) {
    const article = this.findOne(id);
    if (article.locked) {
      throw new ArticleLockedException(id);
    }
    return { ...article, ...dto, updatedAt: new Date().toISOString() };
  }

  /**
   * 演示：抛多种业务异常
   *   - authorId 缺失 → ValidationException (400)
   *   - authorId 与文章作者不匹配 → UserNotFoundException (404)
   */
  publish(id: number, authorId: number) {
    if (!authorId) {
      throw new ValidationException('发布文章需要作者 ID', { field: 'authorId' });
    }
    const article = this.findOne(id);
    if (article.authorId !== authorId) {
      throw new UserNotFoundException(`authorId=${authorId}`);
    }
    return {
      published: true,
      articleId: id,
      publishedAt: new Date().toISOString(),
    };
  }

  /**
   * 演示：抛 NestJS 内置异常（NotFoundException）
   * 命中 HttpExceptionFilter，返回 404 + code: HTTP_404
   */
  findByTitle(title: string) {
    const article = this.articles.find((a) => a.title.includes(title));
    if (!article) {
      throw new NotFoundException(`没有标题包含 "${title}" 的文章`);
    }
    return article;
  }

  /**
   * 演示：抛内置 ForbiddenException
   * 命中 HttpExceptionFilter，返回 403 + code: HTTP_403
   */
  delete(id: number, role: string) {
    if (role !== 'admin') {
      throw new ForbiddenException('只有管理员可以删除文章');
    }
    return { deleted: true, id };
  }

  /**
   * 演示：抛非 HttpException、非 BusinessException 的原生 Error
   * 命中 AllExceptionsFilter 兜底，返回 500 + code: INTERNAL_ERROR
   *
   * 真实场景：数据库连接超时、第三方 SDK 抛错、JSON 解析失败等。
   */
  riskyOperation() {
    // 模拟数据库连接失败
    throw new Error('数据库连接超时: ECONNECTIONTIMEOUT');
  }
}
