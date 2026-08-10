import { Injectable, NotFoundException, OnModuleInit, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma.service';

/**
 * 创建文章入参 DTO
 */
export interface CreateArticleDto {
  title: string;
  content?: string | null;
  authorId: number;
}

/**
 * 更新文章入参 DTO
 */
export interface UpdateArticleDto {
  title?: string;
  content?: string | null;
  viewCount?: number;
}

/**
 * Prisma 版 Articles Service
 *
 * 与 ArticlesTypeormService 对齐业务，但用 Prisma Client API 实现：
 *   - 不需要 @InjectRepository，直接注入 PrismaService
 *   - 通过 this.prisma.article.findMany / create / update / delete 操作
 *   - 关系查询用 include / select / 嵌套 where
 *
 * Prisma 不像 TypeORM 那样需要 synchronize 也不会在内存库里自动建表，
 * 因此 OnModuleInit 时若发现 users 表为空，种入一个默认 User 方便演示。
 */
@Injectable()
export class ArticlesPrismaService implements OnModuleInit {
  private readonly logger = new Logger(ArticlesPrismaService.name);

  constructor(private readonly prisma: PrismaService) {}

  async onModuleInit(): Promise<void> {
    const existing = await this.prisma.user.findUnique({
      where: { email: 'demo@day13.dev' },
    });
    if (!existing) {
      const user = await this.prisma.user.create({
        data: { email: 'demo@day13.dev', name: 'Day13 Demo User' },
      });
      this.logger.log(`已种入默认用户：id=${user.id}, email=${user.email}`);
    }
  }

  /** 创建文章：先校验作者存在，再写入 */
  async create(dto: CreateArticleDto) {
    const author = await this.prisma.user.findUnique({
      where: { id: dto.authorId },
    });
    if (!author) {
      throw new NotFoundException(`User ${dto.authorId} 不存在`);
    }

    return this.prisma.article.create({
      data: {
        title: dto.title,
        content: dto.content ?? null,
        authorId: dto.authorId,
      },
      include: { author: true },
    });
  }

  /** 文章列表（带 author 关系，按创建时间倒序） */
  async findAll() {
    return this.prisma.article.findMany({
      include: { author: true },
      orderBy: { createdAt: 'desc' },
    });
  }

  /** 文章详情（带 author 关系） */
  async findOne(id: number) {
    const article = await this.prisma.article.findUnique({
      where: { id },
      include: { author: true },
    });
    if (!article) {
      throw new NotFoundException(`Article ${id} 不存在`);
    }
    return article;
  }

  /** 更新文章 */
  async update(id: number, dto: UpdateArticleDto) {
    try {
      return await this.prisma.article.update({
        where: { id },
        data: dto,
        include: { author: true },
      });
    } catch {
      // Prisma 找不到记录时抛 PrismaClientKnownRequestError（code P2025）
      throw new NotFoundException(`Article ${id} 不存在`);
    }
  }

  /** 删除文章 */
  async remove(id: number): Promise<{ id: number; deleted: boolean }> {
    try {
      await this.prisma.article.delete({ where: { id } });
      return { id, deleted: true };
    } catch {
      throw new NotFoundException(`Article ${id} 不存在`);
    }
  }

  /** 浏览数 +1，演示 update + increment 字段 */
  async incrementView(id: number) {
    try {
      return await this.prisma.article.update({
        where: { id },
        data: { viewCount: { increment: 1 } },
        include: { author: true },
      });
    } catch {
      throw new NotFoundException(`Article ${id} 不存在`);
    }
  }

  /**
   * 嵌套条件查询示例：根据作者邮箱查文章
   * 演示 Prisma 嵌套 where 的写法（TypeORM 里要 leftJoin + 手写条件）
   */
  async findByAuthorEmail(email: string) {
    return this.prisma.article.findMany({
      where: { author: { email } },
      include: { author: true },
      orderBy: { createdAt: 'desc' },
    });
  }
}
