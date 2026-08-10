import { Injectable, NotFoundException, OnModuleInit, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Article } from '../entities/article.entity';
import { User } from '../entities/user.entity';

/**
 * 创建文章入参 DTO（内联，避免文件碎片）
 */
export interface CreateArticleDto {
  title: string;
  content?: string | null;
  authorId: number;
}

/**
 * 更新文章入参 DTO（所有字段可选）
 */
export interface UpdateArticleDto {
  title?: string;
  content?: string | null;
  viewCount?: number;
}

/**
 * TypeORM 版 Articles Service
 *
 * 演示 Repository 模式（Data Mapper）：
 *   - 通过 @InjectRepository(Article) 注入 Repository<Article>
 *   - 所有数据操作都走 repository 方法（find / findOne / save / update / delete）
 *
 * 同时注入 User 的 Repository 用于校验 authorId 是否存在。
 *
 * 为方便演示，OnModuleInit 时自动种入一个默认 User（id=1），
 * 这样调用方可以直接 POST authorId=1 的文章而无需先建用户。
 */
@Injectable()
export class ArticlesTypeormService implements OnModuleInit {
  private readonly logger = new Logger(ArticlesTypeormService.name);

  constructor(
    @InjectRepository(Article)
    private readonly articleRepo: Repository<Article>,
    @InjectRepository(User)
    private readonly userRepo: Repository<User>,
  ) {}

  async onModuleInit(): Promise<void> {
    // 内存库每次重启都会清空，种入一个默认 User 方便演示
    const existing = await this.userRepo.findOne({ where: { email: 'demo@day13.dev' } });
    if (!existing) {
      const user = this.userRepo.create({
        email: 'demo@day13.dev',
        name: 'Day13 Demo User',
      });
      const saved = await this.userRepo.save(user);
      this.logger.log(`已种入默认用户：id=${saved.id}, email=${saved.email}`);
    }
  }

  /** 创建文章 */
  async create(dto: CreateArticleDto): Promise<Article> {
    // 校验作者存在
    const author = await this.userRepo.findOne({ where: { id: dto.authorId } });
    if (!author) {
      throw new NotFoundException(`User ${dto.authorId} 不存在`);
    }

    const article = this.articleRepo.create({
      title: dto.title,
      content: dto.content ?? null,
      authorId: dto.authorId,
    });
    return this.articleRepo.save(article);
  }

  /** 文章列表（带 author 关系） */
  async findAll(): Promise<Article[]> {
    return this.articleRepo.find({
      relations: ['author'],
      order: { createdAt: 'DESC' },
    });
  }

  /** 文章详情（带 author 关系） */
  async findOne(id: number): Promise<Article> {
    const article = await this.articleRepo.findOne({
      where: { id },
      relations: ['author'],
    });
    if (!article) {
      throw new NotFoundException(`Article ${id} 不存在`);
    }
    return article;
  }

  /** 更新文章（部分字段） */
  async update(id: number, dto: UpdateArticleDto): Promise<Article> {
    // preload：先按 id 查出记录，再合并 dto 字段，返回新实例（不入库）
    const article = await this.articleRepo.preload({ id, ...dto });
    if (!article) {
      throw new NotFoundException(`Article ${id} 不存在`);
    }
    return this.articleRepo.save(article);
  }

  /** 删除文章 */
  async remove(id: number): Promise<{ id: number; deleted: boolean }> {
    const result = await this.articleRepo.delete(id);
    if (result.affected === 0) {
      throw new NotFoundException(`Article ${id} 不存在`);
    }
    return { id, deleted: true };
  }

  /** 浏览数 +1，演示 update 链式调用 */
  async incrementView(id: number): Promise<Article> {
    await this.articleRepo.increment({ id }, 'viewCount', 1);
    return this.findOne(id);
  }
}
