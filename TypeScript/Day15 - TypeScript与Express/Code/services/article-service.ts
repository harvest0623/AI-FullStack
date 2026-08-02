import type {
  Article,
  ArticleDTO,
  ArticleListQuery,
  CreateArticleDTO,
  IArticleService,
  PaginatedDTO,
  UpdateArticleDTO,
} from '../types';
import { NotFoundError, ValidationError } from '../types';

/**
 * 文章服务实现
 * --------------------------------------------------------
 * - implements IArticleService：强制实现所有契约方法，类型层保证不漏
 * - 用内存数组模拟数据存储，便于直接 npm start 跑起来
 * - 所有方法返回 Promise，未来切换到数据库时无需改 Controller
 *
 * 在 NestJS 中，此类会被标注 @Injectable()，
 * Controller 通过 constructor(private readonly articles: ArticleService) 注入。
 */
export class ArticleService implements IArticleService {
  // 模拟数据表
  private articles: Article[] = [
    {
      id: 1,
      title: 'TypeScript 与 Express 类型实战',
      content: '本文演示如何用 TS 重写 Express 应用，建立前后端类型链路。',
      authorId: '1',
      createdAt: '2025-01-10T08:00:00.000Z',
      updatedAt: '2025-01-10T08:00:00.000Z',
    },
    {
      id: 2,
      title: '从装饰器到 NestJS',
      content: '回顾 Day09 的装饰器与 DI 容器，理解 NestJS 的底层机制。',
      authorId: '1',
      createdAt: '2025-01-12T10:00:00.000Z',
      updatedAt: '2025-01-12T10:00:00.000Z',
    },
  ];
  private nextId = 3;

  async list(query: ArticleListQuery): Promise<PaginatedDTO<ArticleDTO>> {
    const page = Math.max(1, Number(query.page) || 1);
    const pageSize = Math.max(1, Number(query.pageSize) || 10);
    const keyword = query.keyword?.trim().toLowerCase();

    let filtered = this.articles;
    if (keyword) {
      filtered = this.articles.filter(
        (a) =>
          a.title.toLowerCase().includes(keyword) ||
          a.content.toLowerCase().includes(keyword),
      );
    }

    const start = (page - 1) * pageSize;
    const slice = filtered.slice(start, start + pageSize).map(this.toDTO);

    return {
      list: slice,
      total: filtered.length,
      page,
      pageSize,
    };
  }

  async getById(id: number): Promise<ArticleDTO> {
    const article = this.articles.find((a) => a.id === id);
    if (!article) throw new NotFoundError('文章', id);
    return this.toDTO(article);
  }

  async create(input: CreateArticleDTO, authorId: string): Promise<ArticleDTO> {
    // 运行时校验：TS 只能保证类型编译期正确，运行时仍需校验
    if (!input.title?.trim()) throw new ValidationError('title 不能为空');
    if (!input.content?.trim()) throw new ValidationError('content 不能为空');

    const now = new Date().toISOString();
    const article: Article = {
      id: this.nextId++,
      title: input.title.trim(),
      content: input.content.trim(),
      authorId,
      createdAt: now,
      updatedAt: now,
    };
    this.articles.push(article);
    return this.toDTO(article);
  }

  async update(id: number, input: UpdateArticleDTO): Promise<ArticleDTO> {
    const article = this.articles.find((a) => a.id === id);
    if (!article) throw new NotFoundError('文章', id);

    if (input.title !== undefined) {
      if (!input.title.trim()) throw new ValidationError('title 不能为空');
      article.title = input.title.trim();
    }
    if (input.content !== undefined) {
      if (!input.content.trim()) throw new ValidationError('content 不能为空');
      article.content = input.content.trim();
    }
    article.updatedAt = new Date().toISOString();
    return this.toDTO(article);
  }

  async remove(id: number): Promise<void> {
    const idx = this.articles.findIndex((a) => a.id === id);
    if (idx === -1) throw new NotFoundError('文章', id);
    this.articles.splice(idx, 1);
  }

  /** 领域模型 -> DTO，剥离内部字段 */
  private toDTO(a: Article): ArticleDTO {
    const { authorId: _authorId, ...dto } = a;
    return dto;
  }
}

// 单例导出，供路由直接使用（NestJS 中由 IoC 容器替代）
export const articleService = new ArticleService();
